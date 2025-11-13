from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from app.schemas import TransactionFilters
from app.models import Transaction, Group
from fastapi import Query
import os

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set")

if len(SECRET_KEY) < 32:
    raise ValueError("SECRET_KEY must be at least 32 characters long")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()

    if "sub" in to_encode and isinstance(to_encode["sub"], int):
        to_encode["sub"] = str(to_encode["sub"])

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None

        return {"user_id": int(user_id)}
    except JWTError:
        return None


def pagination_params(
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(20, ge=1, le=100, description="Размер страницы")
):
    return {"page": page, "size": size}

def apply_filters(query: Query, filters: TransactionFilters) -> Query:
    if filters.name:
        query = query.where(Transaction.name == filters.name)
    if filters.type:
        query = query.where(Transaction.type == filters.type)
    if filters.category:
        query = query.where(Transaction.category == filters.category)
    if filters.amount:
        query = query.where(Transaction.amount >= filters.amount)
    if filters.transaction_datetime:
        query = query.where(Transaction.transaction_datetime >= filters.transaction_datetime)
    if filters.user_id:
        query = query.where(Transaction.user_id == filters.user_id)
    if filters.group_ids:
        query = query.join(Transaction.groups).where(Group.id.in_(group_filters)).distinct()

    return query

