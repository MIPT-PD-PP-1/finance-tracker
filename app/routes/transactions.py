from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.utils import pagination_params, apply_filters
from app.database import get_db
from app.models import User, Group, Transaction
from app.schemas import (TransactionCreate, TransactionUpdate, TransactionResponse, Page,
                         TransactionFilters, get_transaction_filters)
from app.routes.users import get_current_user

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

@router.get("", response_model=Page[TransactionResponse],
            summary="Просмотр транзакций пользователя",
            description="Получить транзакции пользователя с фильтрацией")
async def get_transactions_by_user(
    pagination: dict = Depends(pagination_params),
    filters: TransactionFilters = Depends(get_transaction_filters),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):

    page = pagination["page"]
    size = pagination["size"]
    skip = (page - 1) * size

    query = select(Transaction).where(Transaction.user_id == current_user.id)
    query = apply_filters(query, filters)
    query = query.order_by(Transaction.transaction_datetime.desc()).offset(skip).limit(size)

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


@router.get("/group/{group_id}", response_model=Page[TransactionResponse],
            summary="Просмотр транзакций группы",
            description="Получить транзакции группы с фильтрацией по id")
async def get_transactions_by_group(
        group_id: int,
        pagination: dict = Depends(pagination_params),
        filters: TransactionFilters = Depends(get_transaction_filters),
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):

    group_result = await db.execute(
        select(Group).where(Group.id == group_id)
    )
    group = group_result.scalars().first()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Группа не найдена"
        )

    if current_user not in group.users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра этой группы"
        )

    page = pagination["page"]
    size = pagination["size"]
    skip = (page - 1) * size

    query = select(Transaction).join(Transaction.groups).where(Group.id == group_id)
    query = apply_filters(query, filters)
    query = query.order_by(Transaction.transaction_datetime.desc()).offset(skip).limit(size)

    result = await db.execute(query)
    transactions = result.scalars().all()

    count_query = select(func.count(Transaction.id)
                         ).join(Transaction.groups).where(Group.id == group_id)
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


@router.get("/group/{group_id}/stats",
            summary="Просмотр статистики группы",
            description="Получить статистику доходов/расходов группы, баланс группы по id")
async def get_group_transactions_stats(
        group_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):

    group_result = await db.execute(
        select(Group).where(Group.id == group_id)
    )
    group = group_result.scalars().first()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Группа не найдена"
        )

    if current_user not in group.users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра этой группы"
        )

    income_stats = await db.execute(
        select(func.sum(Transaction.amount)
               ).join(Transaction.groups).where(Group.id == group_id,
            Transaction.type == "income"
        )
    )
    total_income = income_stats.scalar() or 0

    expense_stats = await db.execute(
        select(func.sum(Transaction.amount)
               ).join(Transaction.groups).where(Group.id == group_id,
            Transaction.type == "expense"
        )
    )
    total_expense = expense_stats.scalar() or 0

    count_stats = await db.execute(
        select(func.count(Transaction.id)
               ).join(Transaction.groups).where(Group.id == group_id)
    )
    total_count = count_stats.scalar() or 0

    return {
        "group_id": group_id,
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": total_income - total_expense,
        "total_transactions": total_count
    }


@router.get("/{transaction_id}", response_model=TransactionResponse,
            summary="Просмотр транзакции",
            description="Получить транзакцию по id")
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


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED,
             summary="Создание новой транзакции",
             description="Записать транзакцию в БД")
async def create_transaction(
        transaction_data: TransactionCreate,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):

    groups = []

    if transaction_data.group_ids:

        groups_result = await db.execute(
            select(Group).where(Group.id.in_(transaction_data.group_ids))
            )
        groups = groups_result.scalars().all()

        for group in groups:
            if current_user not in group.users:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Недостаточно прав для добавления транзакции в группу {group.id}"
                )

    new_transaction = Transaction(
        **transaction_data.model_dump(exclude={"group_ids"}),
        user_id=current_user.id,
        groups=groups
    )

    db.add(new_transaction)
    await db.commit()
    await db.refresh(new_transaction)

    return new_transaction


@router.put("/{transaction_id}", response_model=TransactionResponse,
            summary="Обновление транзакции",
            description="Внести в БД изменения транзакции по ее id")
async def update_transaction(
        transaction_id: int,
        transaction_data: TransactionUpdate,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):

    result = await db.execute(
        select(Transaction).where(Transaction.id == transaction_id,
                                  Transaction.user_id == current_user.id)
    )
    transaction = result.scalars().first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Транзакция не найдена"
        )

    update_data = transaction_data.model_dump(exclude_unset=True)

    if 'group_ids' in update_data:
        group_ids = update_data.pop("group_ids")

        groups = []
        if group_ids:
            group_result = await db.execute(
            select(Group).where(Group.id.in_(group_ids))
            )
            groups = group_result.scalars().all()

            for group in groups:
                if current_user not in group.users:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Недостаточно прав для изменения транзакции в группе {group.id}"
                    )

        transaction.groups = groups

    for field, value in update_data.items():
        setattr(transaction, field, value)

    await db.commit()
    await db.refresh(transaction)

    return transaction

@router.delete("/{transaction_id}", status_code=status.HTTP_200_OK,
               summary="Удаление транзакции",
               description="Удалить из бд транзакцию по ее id")
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
