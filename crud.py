from fastapi import HTTPException
from sqlalchemy.orm import Session
import models, schemas
from uuid import uuid4, UUID
from collections import defaultdict


# this will handle the error response if something goes wrong:
def error_response(code: str, message: str, details: dict, status_code: int):
    raise HTTPException(
        status_code=status_code,
        detail={
            "error": {
                "code": code,
                "message": message,
                "details": details
            }
        }
    )

# -> this function creates a new group and commit it to the daatbase
def create_group(db: Session, group: schemas.GroupCreate):
    new_group = models.Group(**group.dict())
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    return new_group

# this adds member into the group
def add_members(db: Session, group_id: str, members: schemas.MemberAddRequest) -> schemas.MemberAddResponse:
    group = db.query(models.Group).filter_by(id=group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    added = []
    for m in members.members:
        # Check if a member with the same name already exists in the group
        name_conflict = (
            db.query(models.GroupMember)
            .join(models.User)
            .filter(
                models.GroupMember.group_id == group_id,
                models.User.name == m.name
            )
            .first()
        )
        if name_conflict:
            error_response(
                code="DUPLICATE RESOURCE",
                message="Member already exists",
                details={
                    "name": m.name
                },
                status_code=409
            )

        # Create or fetch user
        user = db.query(models.User).filter_by(email=m.email).first()
        if not user:
            user = models.User(name=m.name, email=m.email)
            db.add(user)
            db.commit()
            db.refresh(user)

        # Check if this user is already in the group
        existing = db.query(models.GroupMember).filter_by(group_id=group_id, user_id=user.id).first()
        if existing:
            continue

        group_member = models.GroupMember(group_id=group_id, user_id=user.id)
        db.add(group_member)
        db.commit()
        db.refresh(group_member)

        added.append(
            schemas.MemberAddedInfo(
                id=group_member.id,
                user_id=user.id,
                name=user.name,
                email=user.email
            )
        )

    return schemas.MemberAddResponse(group_id=group.id, members_added=added)

# this query the db and gives all the members in the group based on split type
def get_members_in_group(db: Session, group_id: str):
    members = (
        db.query(models.GroupMember)
        .join(models.User)
        .filter(models.GroupMember.group_id == group_id)
        .all()
    )

    return [
        {
            "group_member_id": member.id,
            "user_id": member.user.id,
            "name": member.user.name,
            "email": member.user.email
        }
        for member in members
    ]

# this handles the expense and split it among members:
def create_expense(db: Session, group_id: str, data: schemas.ExpenseCreate):
    # Validating the group
    group = db.query(models.Group).filter_by(id=group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Validating the payer in the group
    payer = db.query(models.GroupMember).filter_by(id=data.paid_by, group_id=group_id).first()
    if not payer:
        raise HTTPException(status_code=404, detail="Payer not found in group")

    # Validating the member amount which the amount will be splitted.
    member_ids = [d.group_member_id for d in data.split_details]
    valid_members = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.id.in_(member_ids)
    ).all()

    if len(valid_members) != len(member_ids):
        raise HTTPException(status_code=400, detail="One or more group_member_ids are invalid or not in the group")

    # Map member_id to user name
    member_map = {m.id: m.user.name for m in valid_members}

    # putting the expens into the database.
    expense = models.Expense(
        id=uuid4(),
        description=data.description,
        amount=data.amount,
        paid_by=data.paid_by,
        group_id=group_id,
        split_type=data.split_type
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)

    # Create splits
    splits = []
    if data.split_type == "EQUAL":
        per_head = data.amount / len(data.split_details)
        for detail in data.split_details:
            splits.append(models.SplitDetail(
                id=uuid4(),
                expense_id=expense.id,
                member_id=detail.group_member_id,
                amount=per_head
            ))

    elif data.split_type == "EXACT":
        total = sum(d.amount for d in data.split_details)
        if total != data.amount:
            raise HTTPException(status_code=400, detail="Split amounts do not match total")
        for detail in data.split_details:
            splits.append(models.SplitDetail(
                id=uuid4(),
                expense_id=expense.id,
                member_id=detail.group_member_id,
                amount=detail.amount
            ))

    elif data.split_type == "PERCENTAGE":
        total = sum(d.percentage for d in data.split_details)
        if total != 100:
            raise HTTPException(status_code=400, detail="Split percentages must total 100")
        for detail in data.split_details:
            splits.append(models.SplitDetail(
                id=uuid4(),
                expense_id=expense.id,
                member_id=detail.group_member_id,
                amount=(data.amount * detail.percentage / 100),
                percentage=detail.percentage
            ))

    db.add_all(splits)
    db.commit()

    return schemas.ExpenseResponse(
        id=expense.id,
        description=expense.description,
        amount=expense.amount,
        paid_by={
            "id": payer.id,
            "name": payer.user.name
        },
        split_details=[
            {
                "member_id": s.member_id,
                "member_name": member_map.get(s.member_id),
                "amount": s.amount
            } for s in splits
        ]
    )

# this fetches the groups expenses and uses the debt simplfication methods.
def get_group_balance(db: Session, group_id: str):
    group = db.query(models.Group).filter_by(id=group_id).first()
    if not group:
        error_response(
            code="GROUP NOT FOUND",
            message="Please enter correct group id",
            details={
                "group" : group_id
            },
            status_code=404
        )

    members = db.query(models.GroupMember).filter_by(group_id=group_id).all()


    member_map = {m.id: m.user.name for m in members}
   # this will return all the expenses by the group_id, this will return list of expenses
    expenses = db.query(models.Expense).filter_by(group_id=group_id).all()

    splits = (
        db.query(models.SplitDetail)
        .join(models.Expense)
        .filter(models.Expense.group_id == group_id)
        .all()
    )

    # Track totals
    paid = defaultdict(float)
    owed = defaultdict(float)

    for expense in expenses:
        paid[expense.paid_by] += float(expense.amount)

    for split in splits:
        owed[split.member_id] += float(split.amount)

    # Member summaries
    member_summaries = []
    for member in members:
        total_paid = paid[member.id]
        total_owed = owed[member.id]
        balance = total_paid - total_owed
        member_summaries.append({
            "member_id": str(member.id),
            "name": member.user.name,
            "total_paid": round(total_paid, 2),
            "total_owed": round(total_owed, 2),
            "balance": round(balance, 2)
        })

    # Simplified balances
    net_balances = {m["member_id"]: m["balance"] for m in member_summaries}
    debtors = {k: v for k, v in net_balances.items() if v < 0}
    creditors = {k: v for k, v in net_balances.items() if v > 0}


    # this is core-debt simplification algorithm
    balances = []
    for debtor_id, debt in debtors.items():
        for creditor_id, credit in creditors.items():
            if debt == 0:
                break
            transfer = min(-debt, credit)
            if transfer > 0:
                balances.append({
                    "from": {
                        "id": debtor_id,
                        "name": member_map[UUID(debtor_id)]
                    },
                    "to": {
                        "id": creditor_id,
                        "name": member_map[UUID(creditor_id)]
                    },
                    "amount": round(transfer, 2)
                })
                net_balances[debtor_id] += transfer
                net_balances[creditor_id] -= transfer
                debtors[debtor_id] += transfer
                creditors[creditor_id] -= transfer

    return {
        "group_id": str(group.id),
        "group_name": group.name,
        "balances": balances,
        "member_summaries": member_summaries
    }

# this keeps the records of settlement of the amount between the members of the group
def record_settlement(db: Session, group_id: str, data: schemas.SettlementCreate) -> schemas.SettlementResponse:
    group = db.query(models.Group).filter_by(id=group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    from_member = db.query(models.GroupMember).filter_by(id=data.from_group_member_id, group_id=group_id).first()
    to_member = db.query(models.GroupMember).filter_by(id=data.to_group_member_id, group_id=group_id).first()

    if not from_member or not to_member:
        raise HTTPException(status_code=404, detail="Both members must exist in the group")

    # fetching the amount and then validating if amount is not more than the settlement amount

    group_balance = get_group_balance(db, group_id)
    from_summary = next((m for m in group_balance["member_summaries"] if m["member_id"] == str(from_member.id)), None)

    if not from_summary:
        raise HTTPException(status_code=400, detail="Could not retrieve balance for payer")

    max_settle_amount = abs(from_summary["balance"])
    if data.amount > max_settle_amount:
        raise HTTPException(
            status_code=400,
            detail=f"Settlement amount ₹{data.amount} exceeds owed amount ₹{max_settle_amount}"
        )

    # If everything goes fine, we are recording the transactions

    settlement = models.Settlement(
        group_id=group_id,
        from_member_id=data.from_group_member_id,
        to_member_id=data.to_group_member_id,
        amount=data.amount
    )
    db.add(settlement)
    db.commit()
    db.refresh(settlement)

    return schemas.SettlementResponse(
        id=settlement.id,
        from_={
            "id": from_member.id,
            "name": from_member.user.name
        },
        to={
            "id": to_member.id,
            "name": to_member.user.name
        },
        amount=settlement.amount,
        settled_at=settlement.settled_at
    )

# this gives a user summary that how many group he/she is in and how much he/she owes.
def get_member_summary(db: Session, user_id: str):
    user = db.query(models.User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    memberships = db.query(models.GroupMember).filter_by(user_id=user_id).all()

    group_summaries = []
    overall_balance = 0.0

    for membership in memberships:
        group = db.query(models.Group).filter_by(id=membership.group_id).first()
        expenses = db.query(models.Expense).filter_by(group_id=group.id).all()
        splits = db.query(models.SplitDetail).join(models.Expense).filter(models.Expense.group_id == group.id).all()

        total_paid = sum(float(e.amount) for e in expenses if e.paid_by == membership.id)
        total_owed = sum(float(s.amount) for s in splits if s.member_id == membership.id)
        balance = round(total_paid - total_owed, 2)
        overall_balance += balance

        group_summaries.append({
            "group_id": str(group.id),
            "group_name": group.name,
            "balance": balance,
            "status": "gets_back" if balance > 0 else "owes" if balance < 0 else "settled"
        })

    return {
        "member_id": str(user.id),
        "name": user.name,
        "overall_balance": round(overall_balance, 2),
        "groups": group_summaries
    }

# this just delete an expense using the expense id
def delete_expense(db: Session, group_id: str, expense_id: str):
    expense = db.query(models.Expense).filter_by(id=expense_id, group_id=group_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found in group")

    # Delete associated split details first
    db.query(models.SplitDetail).filter_by(expense_id=expense_id).delete()

    # Delete the expense
    db.delete(expense)
    db.commit()

    return {"message": "Expense deleted successfully"}

# this give info about the group, payment timing, amount, transaction...
def get_group_analytics(db: Session, group_id: str) -> dict:
    expenses = db.query(models.Expense).filter_by(group_id=group_id).all()
    splits = (
        db.query(models.SplitDetail)
        .join(models.Expense)
        .filter(models.Expense.group_id == group_id)
        .all()
    )

    # Totals
    paid = defaultdict(float)
    owed = defaultdict(float)

    for e in expenses:
        paid[e.paid_by] += float(e.amount)

    for s in splits:
        owed[s.member_id] += float(s.amount)

    # Member summaries
    members = db.query(models.GroupMember).filter_by(group_id=group_id).all()
    summaries = []
    for m in members:
        summaries.append({
            "name": m.user.name,
            "total_paid": round(paid[m.id], 2),
            "total_owed": round(owed[m.id], 2),
            "net_balance": round(paid[m.id] - owed[m.id], 2)
        })

    # Timeline
    timeline_raw = sorted([(e.created_at.date(), float(e.amount)) for e in expenses])
    timeline = []
    cumulative = 0.0
    for dt, amt in timeline_raw:
        cumulative += amt
        timeline.append({
            "date": dt.isoformat(),
            "cumulative_amount": round(cumulative, 2)
        })

    return {
        "members": summaries,
        "timeline": timeline
    }
