from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from app.database import get_db
from app.models import User, Transaction
from app.schemas import UserCreate, UserResponse, UserLogin, Token, ChangePassword, TransactionFilters, get_transaction_filters, PeriodForGroupBy
from app.utils import hash_password, verify_password, create_access_token, decode_access_token, apply_filters

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    
    token_data = decode_access_token(token)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    result = await db.execute(select(User).where(User.id == token_data["user_id"]))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    return user

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.login == user_data.login))
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким логином уже существует"
        )
    
    hashed_password = hash_password(user_data.password)
    new_user = User(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        login=user_data.login,
        password=hashed_password
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.login == credentials.login))
    user = result.scalars().first()
    
    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильный логин или пароль"
        )
    
    access_token = create_access_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id
    }

@router.put("/change-password")
async def change_password(
    password_data: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not verify_password(password_data.old_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильный текущий пароль"
        )
    
    current_user.password = hash_password(password_data.new_password)
    await db.commit()
    
    return {"message": "Пароль успешно изменён"}

@router.post("/refresh-token", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_user)
):
    new_access_token = create_access_token(data={"sub": current_user.id})
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "user_id": current_user.id
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/me/statistics")
async def get_group_statistics(
    period: PeriodForGroupBy = "month",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    filters: TransactionFilters = Depends(get_transaction_filters),
):
    income_query = select(func.sum(Transaction.amount)).where(Transaction.user_id == current_user.id, 
        Transaction.type == "income")
    income_query = apply_filters(income_query, filters)
    income_stats = await db.execute(income_query)
    total_income = income_stats.scalar() or 0

    expense_query = select(func.sum(Transaction.amount)).where(Transaction.user_id == current_user.id, 
        Transaction.type == "expense")
    expense_query = apply_filters(expense_query, filters)
    expense_stats = await db.execute(expense_query)
    total_expense = expense_stats.scalar() or 0

    balance = total_income - total_expense

    count_query = select(func.count(Transaction.id)).where(Transaction.user_id == current_user.id)
    count_query = apply_filters(count_query, filters)
    count_stats = await db.execute(count_query)
    total_count = count_stats.scalar() or 0

    grouped_by_category_query = select(Transaction.category,
        func.sum(Transaction.amount).label("amount")).where(Transaction.user_id == current_user.id,
        Transaction.type == "expense")
    grouped_by_category_query = apply_filters(grouped_by_category_query, filters)
    grouped_by_category_query = grouped_by_category_query.group_by(Transaction.category)
    grouped_by_category_stats = await db.execute(grouped_by_category_query)
    grouped_by_category_expense = [
        {"category": row.category, "amount": float(row.amount)}
        for row in grouped_by_category_stats.all()
    ]

    period_truncated = func.date_trunc(period, Transaction.transaction_datetime).label("period")
    grouped_by_period_query = select(period_truncated, func.sum(Transaction.amount).label("amount")).where(Transaction.user_id == current_user.id,
        Transaction.type == "expense")
    grouped_by_period_query = apply_filters(grouped_by_period_query, filters)
    grouped_by_period_query = grouped_by_period_query.group_by(period_truncated)
    grouped_by_period_stats = await db.execute(grouped_by_period_query)
    grouped_by_period_expense = [
        {"period": row.period.isoformat() if row.period else None, "amount": float(row.amount)}
        for row in grouped_by_period_stats.all()
    ]

    return {
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "user_id": current_user.id,
        "balance": balance,
        "total_income": total_income,
        "total_expense": total_expense,
        "total_count_of_transactions": total_count,
        "grouped_by_category_expense": grouped_by_category_expense,
        "grouped_by_period_expense": grouped_by_period_expense
    }

