from pydantic import BaseModel, ConfigDict
from datetime import date
from decimal import Decimal
from typing import Optional, List, Generic, TypeVar
from app.models import TransactionType

class UserBase(BaseModel):
    first_name: str
    last_name: str
    login: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    login: str
    password: str

class ChangePassword(BaseModel):
    old_password: str
    new_password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int

class GroupBase(BaseModel):
    name: str

class GroupCreate(GroupBase):
    pass

class GroupUpdate(BaseModel):
    name: str

class GroupResponse(GroupBase):
    id: int
    owner_id: int
    model_config = ConfigDict(from_attributes=True)

class TransactionBase(BaseModel):
    name: str
    type: TransactionType
    category: str
    amount: Decimal
    transaction_date: date

class TransactionCreate(TransactionBase):
    user_id: int
    group_id: Optional[int] = None

class TransactionUpdate(TransactionBase):
    user_id: int
    group_id: Optional[int] = None
    name: Optional[str] = None
    category: Optional[str] = None
    amount: Optional[Decimal] = None
    transaction_date: Optional[date] = None

class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    group_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)

class TransactionFilters(BaseModel):
    name: Optional[str] = None
    type: Optional[TransactionType] = "expense"
    category: Optional[str] = None
    amount: Optional[Decimal] = None
    transaction_date: Optional[date] = None
    user_id: Optional[int] = None
    group_id: Optional[int] = None

    @classmethod
    def dependence(
            cls,
            name: Optional[str] = None,
            type: Optional[TransactionType] = "expense",
            category: Optional[str] = None,
            amount: Optional[Decimal] = None,
            transaction_date: Optional[date] = None,
            user_id: Optional[int] = None,
            group_id: Optional[int] = None,
    ):
        return cls(
            name=name,
            type=type,
            category=category,
            amount=amount,
            transaction_date=transaction_date,
            user_id=user_id,
            group_id=group_id
        )

T = TypeVar("T")

class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int


