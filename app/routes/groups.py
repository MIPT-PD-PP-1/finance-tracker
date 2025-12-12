from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List
from app.database import get_db
from app.models import User, Group, Transaction, user_group_association
from app.schemas import GroupCreate, GroupUpdate, GroupResponse, UserResponse, TransactionFilters, get_transaction_filters, PeriodForGroupBy
from app.routes.users import get_current_user
from app.utils import apply_filters

router = APIRouter(prefix="/api/groups", tags=["groups"])


@router.get("", response_model=List[GroupResponse])
async def get_groups(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Group)
        .options(selectinload(Group.users))
        .join(Group.users)
        .where(User.id == current_user.id)
    )
    groups = result.scalars().all()
    return groups


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_data: GroupCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    new_group = Group(name=group_data.name, owner_id=current_user.id)
    new_group.users.append(current_user)

    db.add(new_group)
    await db.commit()
    await db.refresh(new_group)

    return new_group


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: int,
    group_data: GroupUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Group).options(selectinload(Group.users)).where(Group.id == group_id)
    )
    group = result.scalars().first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Группа не найдена"
        )
    if current_user not in group.users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для редактирования этой группы",
        )

    group.name = group_data.name
    await db.commit()
    await db.refresh(group)

    return group


@router.delete("/{group_id}", response_class=JSONResponse)
async def delete_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Group).options(selectinload(Group.users)).where(Group.id == group_id)
    )
    group = result.scalars().first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Группа не найдена"
        )
    if current_user not in group.users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для удаления этой группы",
        )

    await db.delete(group)
    await db.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"Группа с id {group_id} успешно удалена"},
    )


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Group).options(selectinload(Group.users)).where(Group.id == group_id)
    )
    group = result.scalars().first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Группа не найдена"
        )
    if current_user not in group.users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра этой группы",
        )

    return group


@router.post("/{group_id}/users/{user_id}", status_code=200)
async def add_user_to_group(
    group_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if current_user not in group.users:
        raise HTTPException(
            status_code=403, detail="Недостаточно прав для изменения группы"
        )

    if user not in group.users:
        group.users.append(user)
        await db.commit()

    return {
        "message": f"Пользователь с id {user_id} успешно добавлен в группу с id {group_id}"
    }


@router.delete("/{group_id}/users/{user_id}", status_code=200)
async def remove_user_from_group(
    group_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if current_user not in group.users:
        raise HTTPException(
            status_code=403, detail="Недостаточно прав для изменения группы"
        )

    if user in group.users:
        group.users.remove(user)
        await db.commit()
        return {
            "message": f"Пользователь с id {user_id} успешно удален из группы с id {group_id}"
        }

    return {"message": "Пользователь не состоит в группе"}


@router.get("/{group_id}/users", response_model=List[UserResponse])
async def get_group_users(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")

    if current_user not in group.users:
        raise HTTPException(
            status_code=403,
            detail="Недостаточно прав для просмотра пользователей группы",
        )

    return group.users


@router.get("/{group_id}/statistics")
async def get_group_statistics(
    group_id: int,
    period: PeriodForGroupBy = "month",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    filters: TransactionFilters = Depends(get_transaction_filters),
):
    target_group = await db.execute(
        select(Group).where(Group.id == group_id)
        )
    group = target_group.scalars().first()

    if not group:
        raise HTTPException(
            status_code=404,
            detail="Группа не найдена"
        )
    
    if current_user not in group.users:
        raise HTTPException(
            status_code=403,
            detail="Недостаточно прав для просмотра статистики группы"
        )

    group_name = group.name

    count_members_stats = await db.execute(
        select(func.count(Group.id)).join(Group.users).where(Group.id == group_id)
    )
    total_members = count_members_stats.scalar() or 0

    income_query = select(func.sum(Transaction.amount)).join(Transaction.groups).where(Group.id == group_id, 
        Transaction.type == "income")
    income_query = apply_filters(income_query, filters)
    income_stats = await db.execute(income_query)
    total_income = income_stats.scalar() or 0

    expense_query = select(func.sum(Transaction.amount)).join(Transaction.groups).where(Group.id == group_id, 
        Transaction.type == "expense")
    expense_query = apply_filters(expense_query, filters)
    expense_stats = await db.execute(expense_query)
    total_expense = expense_stats.scalar() or 0

    balance = total_income - total_expense

    count_query = select(func.count(Transaction.id)).join(Transaction.groups).where(Group.id == group_id)
    count_query = apply_filters(count_query, filters)
    count_stats = await db.execute(count_query)
    total_count = count_stats.scalar() or 0

    groupped_by_category_query = select(Transaction.category, 
        func.sum(Transaction.amount)).join(Transaction.groups).where(Group.id == group_id,
        Transaction.type == "expense")
    groupped_by_category_query = apply_filters(groupped_by_category_query, filters)
    groupped_by_category_query = groupped_by_category_query.group_by(Transaction.category)
    groupped_by_category_stats = await db.execute(groupped_by_category_query)
    groupped_by_category_expense = groupped_by_category_stats.scalars().all()

    period_truncated = func.date_trunc(period, Transaction.transaction_datetime).label("period")
    groupped_by_period_query = select(period_truncated, func.sum(Transaction.amount)).join(Transaction.groups).where(Group.id == group_id,
        Transaction.type == "expense")
    groupped_by_period_query = apply_filters(groupped_by_period_query, filters)
    groupped_by_period_query = groupped_by_period_query.group_by(period_truncated)
    groupped_by_period_stats = await db.execute(groupped_by_period_query)
    groupped_by_period_expense = groupped_by_period_stats.scalars().all()

    return {
        "Group's ID": group_id,
        "Name of group": group_name,
        "Total count of members": total_members,
        "Balance": balance,
        "Total income": total_income,
        "Total expense": total_expense,
        "Total count of transactions": total_count,
        "Groupped by category expense": groupped_by_category_expense,
        "Groupped by period expense": groupped_by_period_expense
    }

