from sqlalchemy import Column, Integer, String, Numeric, Date, ForeignKey, Enum as SQLEnum, Table, UniqueConstraint
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
    user_groups = relationship("UserGroup", back_populates="user")

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
    user_groups = relationship("UserGroup", back_populates="group")
    transactions = relationship("Transaction", back_populates="group")

class UserGroup(Base):
    __tablename__ = "user_groups"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, default="member")
    joined_at = Column(Date, nullable=False)

    user = relationship("User", back_populates="user_groups")
    group = relationship("Group", back_populates="user_groups")

    __table_args__ = (
        UniqueConstraint('user_id', 'group_id', name='uq_user_group'),
    )

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(SQLEnum(TransactionType), nullable=False)
    category = Column(String, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    transaction_date = Column(Date, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=True)

    user = relationship("User", back_populates="transactions")
    group = relationship("Group", back_populates="transactions")

