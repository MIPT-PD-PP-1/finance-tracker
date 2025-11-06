from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.utills import pagination_params, apply_filters
from app.database import get_db
from app.models import User, Group, Transaction
from app.schemas import TransactionCreate, TransactionUpdate, TransactionResponse, Page, TransactionFilters
from app.routes.users import get_current_user
from app.routes.groups import get_group

router = APIRouter(prefix="api/transactions", tags=["transactions"])

router.get("", response_model=Page[TransactionResponse])
async def get_transactions_user(
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
    query = query.order_by(Transaction.created_at.desc().offset(skip).limit(size))

    result = await db.execute(query)
    transactions = result.scalars().all()

    count_result = await db.execute(
        select(func.count(Transaction.id))
        .where(Transaction.user_id == current_user.id)
    )
    count_result = apply_filters(count_result, filters)
    total = count_result.scalar() or 0

    return Page(
        items=transactions,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size if total > 0 else 0,
    )

router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
        transaction_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Transaction).where(Transaction.id == transaction_id,
                                  Transaction.user_id == current_user.id)
    )
    transaction = result.scalars().first()

    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Транзакция не найдена")

    return transaction

@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
        transaction_data: TransactionCreate,
        current_user: User = Depends(get_current_user),
        current_group: Group = Depends(get_group),
        db: AsyncSession = Depends(get_db)
):
    new_transaction = Transaction(
        name=transaction_data.name,
        date=transaction_data.transaction_date,
        user_id=current_user.id
    )

    db.add(new_transaction)
    await db.commit()
    await db.refresh(new_transaction)

    return new_transaction

router.put("/{transaction_id}", response_model=TransactionResponse)
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Транзакция не найдена")


    transaction.name = transaction_data.name
    transaction.date = transaction_data.transaction_date
    transaction.user_id = current_user.id

    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)

    return transaction

router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
        transaction_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Transaction).where(Transaction.id == transaction_id,
                                  Transaction.user_id == current_user.id)
    )
    result = result.scalars().first()

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Транзакция не найдена")
    await db.delete(result)
    await db.commit()

    return JSONResponse(status_code=status.HTTP_200_OK,
                        content={"message": f"Транзакция с id {transaction_id} успешно удалена"})