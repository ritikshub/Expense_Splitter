from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import crud
import schemas
from database import SessionLocal   
router = APIRouter()

# -> function that manages the database session, starts and closes it properly, we will use this function as 
# -> as a dependency function, where ever we need db session.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
def test_db(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "connected"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


@router.post("/groups", response_model=schemas.GroupResponse)
def create_group(group: schemas.GroupCreate, db: Session = Depends(get_db)):
    return crud.create_group(db, group)


@router.post("/groups/{group_id}/members", response_model=schemas.MemberAddResponse)
def add_members_to_group(group_id: str, request: schemas.MemberAddRequest, db: Session = Depends(get_db)):
    response = crud.add_members(db, group_id, request)
    if response is None:
        raise HTTPException(status_code=404, detail="Group not found")
    return response


@router.get("/groups/{group_id}/members")
def get_group_members(group_id: str, db: Session = Depends(get_db)):
    return crud.get_members_in_group(db, group_id)


@router.post("/groups/{group_id}/expenses", response_model=schemas.ExpenseResponse)
def add_expense(group_id: str, request: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    return crud.create_expense(db, group_id, request)


@router.get("/groups/{group_id}/balance", response_model=schemas.BalanceResponse)
def get_group_balance(group_id: str, db: Session = Depends(get_db)):
    return crud.get_group_balance(db, group_id)


@router.post("/groups/{group_id}/settle", response_model=schemas.SettlementResponse)
def settle_up(group_id: str, request: schemas.SettlementCreate, db: Session = Depends(get_db)):
    return crud.record_settlement(db, group_id, request)


@router.delete("/groups/{group_id}/expenses/{expense_id}", response_model=dict)
def delete_expense(group_id: str, expense_id: str, db: Session = Depends(get_db)):
    return crud.delete_expense(db, group_id, expense_id)


@router.get("/members/{user_id}/summary", response_model=schemas.MemberSummaryResponse)
def get_member_summary(user_id: str, db: Session = Depends(get_db)):
    result = crud.get_member_summary(db, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Member not found")
    return result

@router.get("/groups/{group_id}/analytics")
def group_analytics(group_id: str, db: Session = Depends(get_db)):
    return crud.get_group_analytics(db, group_id)

