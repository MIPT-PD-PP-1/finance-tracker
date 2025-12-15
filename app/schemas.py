from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Generic, TypeVar, Literal
from app.models import TransactionType
from fastapi import Query

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
    users: List[UserResponse] = []
    model_config = ConfigDict(from_attributes=True)

class TransactionBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=100, description="Название транзакции")
    type: TransactionType = Field(TransactionType.expense, description="Тип транзакции пополнение/расход")
    category: str = Field(..., min_length=1, max_length=50, description="Категория")
    amount: Decimal = Field(..., gt=0, description="Сумма транзакции")
    description: Optional[str] = Field(None, description="Описание")
    is_recurring: bool = False
    recurring_period_days: Optional[int] = None

class TransactionCreate(TransactionBase):
    group_ids: List[int] = Field(default=[], description="Список ID групп")

class TransactionUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Название транзакции")
    type: Optional[TransactionType] = None
    category: Optional[str] = Field(None, min_length=1, max_length=50, description="Категория")
    amount: Optional[Decimal] = Field(None, gt=0, description="Сумма транзакции")
    transaction_datetime: Optional[datetime] = Field(None, description="Дата и время транзакции")
    description: Optional[str] = Field(None, description="Описание")
    group_ids: Optional[List[int]] = Field(None, description="Список ID групп")
    is_recurring: Optional[bool] = None
    recurring_period_days: Optional[int] = None

class TransactionResponse(TransactionBase):
    id: int = Field(..., description="ID транзакции")
    transaction_datetime: datetime = Field(..., description="Дата и время транзакции")
    user_id: int = Field(..., description="ID пользователя")
    groups: List[GroupResponse] = Field(default=[], description="Информация о группах")

class TransactionFilters(BaseModel):
    name: Optional[str] = None
    type: Optional[TransactionType] = None
    category: Optional[str] = None
    amount: Optional[Decimal] = None
    transaction_datetime: Optional[datetime] = None
    user_id: Optional[int] = None
    group_ids: Optional[List[int]] = None

    model_config = ConfigDict(from_attributes=True)

async def get_transaction_filters(
    name: Optional[str] = Query(None),
    type: Optional[TransactionType] = Query(None),
    category: Optional[str] = Query(None),
    amount: Optional[Decimal] = Query(None),
    transaction_datetime: Optional[datetime] = Query(None),
    group_ids: Optional[List[int]] = Query(None)
) -> TransactionFilters:
    return TransactionFilters(
        name=name,
        type=type,
        category=category,
        amount=amount,
        transaction_datetime=transaction_datetime,
        group_ids=group_ids
    )

T = TypeVar("T")

class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int

class PeriodForGroupBy(BaseModel):
    period: Literal["year", "month", "day"]
