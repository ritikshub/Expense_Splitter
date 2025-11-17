from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Literal
from uuid import UUID
from pydantic import BaseModel, EmailStr,Field


class GroupCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str]


class GroupResponse(GroupCreate):
    id: UUID
    created_at: datetime


class UserCreate(BaseModel):
    name: str
    email: EmailStr


class UserResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr


class GroupMemberCreate(BaseModel):
    email: EmailStr  
    name: Optional[str] = None  


class MemberAddRequest(BaseModel):
    members: List[GroupMemberCreate]


class MemberAddedInfo(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    email: str


class MemberAddResponse(BaseModel):
    group_id: UUID
    members_added: List[MemberAddedInfo]


class GroupMemberInfo(BaseModel):
    group_member_id: UUID
    user_id: UUID
    name: str
    email: str


class SplitDetailInput(BaseModel):
    group_member_id: UUID
    amount: Optional[Decimal] = None
    percentage: Optional[Decimal] = None


class ExpenseCreate(BaseModel):
    description: str
    amount: Decimal
    paid_by: UUID  
    split_type: Literal["EQUAL", "EXACT", "PERCENTAGE"]
    split_details: List[SplitDetailInput] # so this is list of people among whom the money will be split


class SplitDetailResponse(BaseModel):
    member_id: UUID
    member_name: str
    amount: Decimal


class ExpenseResponse(BaseModel):
    id: UUID
    description: str
    amount: Decimal
    paid_by: dict
    split_details: List[SplitDetailResponse]


class SettlementCreate(BaseModel):
    from_group_member_id: UUID
    to_group_member_id: UUID
    amount: Decimal

    
class SettlementResponse(BaseModel):
    id: UUID
    from_: dict
    to: dict
    amount: Decimal
    settled_at: datetime


class BalanceSummary(BaseModel):
    member_id: UUID
    name: str
    total_paid: Decimal
    total_owed: Decimal
    balance: Decimal


class BalanceResponse(BaseModel):
    group_id: UUID
    group_name: str
    balances: List[dict]
    member_summaries: List[BalanceSummary]


class MemberGroupSummary(BaseModel):
    group_id: UUID
    group_name: str
    balance: Decimal
    status: str


class MemberSummaryResponse(BaseModel):
    member_id: UUID
    name: str
    overall_balance: Decimal
    groups: List[MemberGroupSummary]

