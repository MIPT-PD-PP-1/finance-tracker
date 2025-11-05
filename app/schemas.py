from pydantic import BaseModel, ConfigDict
from datetime import date
from decimal import Decimal
from typing import Optional
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

class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    group_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)

