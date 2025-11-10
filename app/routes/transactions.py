from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.utils import pagination_params, apply_filters
from app.database import get_db
from app.models import User, Group, UserGroup, Transaction
from app.schemas import TransactionCreate, TransactionUpdate, TransactionResponse, Page, TransactionFilters
from app.routes.users import get_current_user

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

@router.get("", response_model=Page[TransactionResponse])
async def get_transactions_by_user(
    pagination: dict = Depends(pagination_params),
    filters: TransactionFilters = Depends(TransactionFilters.dependence),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    page = pagination["page"]
    size = pagination["size"]
    skip = (page - 1) * size

    query = select(Transaction).where(Transaction.user_id == current_user.id)
    query = apply_filters(query, filters)
    query = query.order_by(Transaction.amount.desc()).offset(skip).limit(size)

    result = await db.execute(query)
    transactions = result.scalars().all()

    count_query = select(func.count(Transaction.id)).where(Transaction.user_id == current_user.id)
    count_query = apply_filters(count_query, filters)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return Page(
        items=transactions,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size if total > 0 else 0,
    )

@router.get("/group/{group_id}", response_model=Page[TransactionResponse])
async def get_transactions_by_group(
        group_id: int,
        pagination: dict = Depends(pagination_params),
        filters: TransactionFilters = Depends(TransactionFilters.dependence),
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    group_query = select(Group).where(Group.id == group_id)
    group_result = await db.execute(group_query)
    group = group_result.scalars().first()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Группа не найдена"
        )

    user_in_group = False
    if hasattr(group, 'users'):
        for user in group.users:
            if user.id == current_user.id:
                user_in_group = True
                break

    if not user_in_group:
        user_group_query = select(UserGroup).where(
            UserGroup.group_id == group_id,
            UserGroup.user_id == current_user.id
        )
        user_group_result = await db.execute(user_group_query)
        user_group = user_group_result.scalars().first()

        if not user_group:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет доступа к этой группе"
            )

    page = pagination["page"]
    size = pagination["size"]
    skip = (page - 1) * size

    query = select(Transaction).where(Transaction.group_id == group_id)
    query = apply_filters(query, filters)
    query = query.order_by(Transaction.amount.desc()).offset(skip).limit(size)

    result = await db.execute(query)
    transactions = result.scalars().all()

    count_query = select(func.count(Transaction.id)).where(Transaction.group_id == group_id)
    count_query = apply_filters(count_query, filters)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return Page(
        items=transactions,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size if total > 0 else 0,
    )


@router.get("/group/{group_id}/stats")
async def get_group_transactions_stats(
        group_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    group_query = select(Group).where(Group.id == group_id)
    group_result = await db.execute(group_query)
    group = group_result.scalars().first()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Группа не найдена"
        )

    user_in_group = False
    if hasattr(group, 'users'):
        for user in group.users:
            if user.id == current_user.id:
                user_in_group = True
                break

    if not user_in_group:
        user_group_query = select(UserGroup).where(
            UserGroup.group_id == group_id,
            UserGroup.user_id == current_user.id
        )
        user_group_result = await db.execute(user_group_query)
        user_group = user_group_result.scalars().first()

        if not user_group:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет доступа к этой группе"
            )

    income_stats = await db.execute(
        select(func.sum(Transaction.amount)).where(
            Transaction.group_id == group_id,
            Transaction.type == "income"
        )
    )
    total_income = income_stats.scalar() or 0

    expense_stats = await db.execute(
        select(func.sum(Transaction.amount)).where(
            Transaction.group_id == group_id,
            Transaction.type == "expense"
        )
    )
    total_expense = expense_stats.scalar() or 0

    count_stats = await db.execute(
        select(func.count(Transaction.id)).where(Transaction.group_id == group_id)
    )
    total_count = count_stats.scalar() or 0

    return {
        "group_id": group_id,
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": total_income - total_expense,
        "total_transactions": total_count
    }

@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id
        )
    )
    transaction = result.scalars().first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Транзакция не найдена"
        )

    return transaction

@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
        transaction_data: TransactionCreate,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    group_id = transaction_data.group_id

    if group_id:
        group_query = select(Group).where(Group.id == group_id)
        group_result = await db.execute(group_query)
        group = group_result.scalars().first()

        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Группа с ID {group_id} не найдена"
            )

        user_in_group = False
        if hasattr(group, 'users'):
            for user in group.users:
                if user.id == current_user.id:
                    user_in_group = True
                    break

        if not user_in_group:
            user_group_query = select(UserGroup).where(
                UserGroup.group_id == group_id,
                UserGroup.user_id == current_user.id
            )
            user_group_result = await db.execute(user_group_query)
            user_group = user_group_result.scalars().first()

            if not user_group:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Вы не состоите в этой группе"
                )

    new_transaction = Transaction(
        type=transaction_data.type,
        name=transaction_data.name,
        category=transaction_data.category,
        transaction_date=transaction_data.transaction_date,
        amount=transaction_data.amount,
        user_id=current_user.id,
        group_id=group_id
    )

    db.add(new_transaction)
    await db.commit()
    await db.refresh(new_transaction)

    return new_transaction


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
        transaction_id: int,
        transaction_data: TransactionUpdate,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id
        )
    )
    transaction = result.scalars().first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Транзакция не найдена"
        )

    update_data = transaction_data.dict(exclude_unset=True)

    if 'group_id' in update_data and update_data['group_id'] is not None:
        group_id = update_data['group_id']

        if group_id == 0:
            update_data['group_id'] = None
        else:
            group_query = select(Group).where(Group.id == group_id)
            group_result = await db.execute(group_query)
            group = group_result.scalars().first()

            if not group:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Группа с ID {group_id} не найдена"
                )

            user_in_group = False
            if hasattr(group, 'users'):
                for user in group.users:
                    if user.id == current_user.id:
                        user_in_group = True
                        break

            if not user_in_group:
                user_group_query = select(UserGroup).where(
                    UserGroup.group_id == group_id,
                    UserGroup.user_id == current_user.id
                )
                user_group_result = await db.execute(user_group_query)
                user_group = user_group_result.scalars().first()

                if not user_group:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Вы не состоите в этой группе"
                    )

    for field, value in update_data.items():
        setattr(transaction, field, value)

    await db.commit()
    await db.refresh(transaction)

    return transaction

@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id
        )
    )
    transaction = result.scalars().first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Транзакция не найдена"
        )

    await db.delete(transaction)
    await db.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"Транзакция с id {transaction_id} успешно удалена"}
    )

