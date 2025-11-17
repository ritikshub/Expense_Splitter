import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Numeric,
    DECIMAL,
)

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)

    memberships = relationship("GroupMember", back_populates="user", cascade="all, delete-orphan")


class Group(Base):
    __tablename__ = "groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="group", cascade="all, delete-orphan")


class GroupMember(Base):
    __tablename__ = "group_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    group = relationship("Group", back_populates="members")
    user = relationship("User", back_populates="memberships")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    description = Column(String)
    amount = Column(DECIMAL(10, 2), nullable=False)
    paid_by = Column(UUID(as_uuid=True), ForeignKey("group_members.id"))
    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id"))
    split_type = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    group = relationship("Group", back_populates="expenses")
    splits = relationship("SplitDetail", back_populates="expense")


class SplitDetail(Base):
    __tablename__ = "split_details"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expense_id = Column(UUID(as_uuid=True), ForeignKey("expenses.id"))
    member_id = Column(UUID(as_uuid=True), ForeignKey("group_members.id"))
    amount = Column(DECIMAL(10, 2), nullable=True)
    percentage = Column(DECIMAL(5, 2), nullable=True)

    expense = relationship("Expense", back_populates="splits")


class Settlement(Base):
    __tablename__ = "settlements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id"), nullable=False)
    from_member_id = Column(UUID(as_uuid=True), ForeignKey("group_members.id"), nullable=False)
    to_member_id = Column(UUID(as_uuid=True), ForeignKey("group_members.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    settled_at = Column(DateTime, default=datetime.utcnow)