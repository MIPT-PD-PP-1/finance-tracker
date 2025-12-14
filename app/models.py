from sqlalchemy import (Column, Integer, String, Numeric, DateTime, ForeignKey, Enum as SQLEnum,
                        Table, text, Boolean)
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class TransactionType(str, enum.Enum):
    income = "income"
    expense = "expense"

user_group_association = Table(
    'user_group_association',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True)
)

transaction_group_association = Table(
    'transaction_group_association',
    Base.metadata,
    Column('transaction_id', Integer, ForeignKey('transactions.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    login = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)

    groups = relationship(
        "Group",
        secondary=user_group_association,
        back_populates="users"
    )
    transactions = relationship("Transaction", back_populates="user")
    owned_groups = relationship("Group", back_populates="owner")

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    users = relationship(
        "User",
        secondary=user_group_association,
        back_populates="groups",
        lazy="selectin"
    )
    owner = relationship("User", back_populates="owned_groups")
    transactions = relationship("Transaction",
                                secondary=transaction_group_association,
                                back_populates="groups",
                                lazy="selectin"
                                )

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(SQLEnum(TransactionType), nullable=False)
    category = Column(String, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    transaction_datetime = Column(DateTime(timezone=True), nullable=False,
                                  server_default=text("CURRENT_TIMESTAMP"))
    description = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    is_recurring = Column(Boolean, nullable=False, default=False)
    recurring_period_days = Column(Integer, nullable=True)
    next_run = Column(DateTime(timezone=True), nullable=True, server_default=text("CURRENT_TIMESTAMP"))
    user = relationship("User", back_populates="transactions")
    groups = relationship("Group",
                          secondary=transaction_group_association,
                          back_populates="transactions",
                          lazy="selectin"
                          )

