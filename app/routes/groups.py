from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from app.database import get_db
from app.models import User, Group
from app.schemas import GroupCreate, GroupUpdate, GroupResponse, UserResponse
from app.routes.users import get_current_user

router = APIRouter(prefix="/api/groups", tags=["groups"])

@router.get("", response_model=List[GroupResponse])
async def get_groups(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Group).options(selectinload(Group.users)).join(Group.users).where(User.id == current_user.id)
    )
    groups = result.scalars().all()
    return groups

@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_data: GroupCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    new_group = Group(name=group_data.name,
                      owner_id=current_user.id)
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
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Group).options(selectinload(Group.users)).where(Group.id == group_id)
    )
    group = result.scalars().first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Группа не найдена"
        )
    if current_user not in group.users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для редактирования этой группы"
        )

    group.name = group_data.name
    await db.commit()
    await db.refresh(group)

    return group

@router.delete("/{group_id}", response_class=JSONResponse)
async def delete_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Group).options(selectinload(Group.users)).where(Group.id == group_id)
    )
    group = result.scalars().first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Группа не найдена"
        )
    if current_user not in group.users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для удаления этой группы"
        )

    await db.delete(group)
    await db.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"Группа с id {group_id} успешно удалена"}
    )

@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Group).options(selectinload(Group.users)).where(Group.id == group_id)
    )
    group = result.scalars().first()
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

    return group

@router.post("/{group_id}/users/{user_id}", status_code=200)
async def add_user_to_group(
    group_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if current_user not in group.users:
        raise HTTPException(status_code=403, detail="Недостаточно прав для изменения группы")

    if user not in group.users:
        group.users.append(user)
        await db.commit()
    
    return {"message": f"Пользователь с id {user_id} успешно добавлен в группу с id {group_id}"}

@router.delete("/{group_id}/users/{user_id}", status_code=200)
async def remove_user_from_group(
    group_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if current_user not in group.users:
        raise HTTPException(status_code=403, detail="Недостаточно прав для изменения группы")

    if user in group.users:
        group.users.remove(user)
        await db.commit()
        return {"message": f"Пользователь с id {user_id} успешно удален из группы с id {group_id}"}

    return {"message": "Пользователь не состоит в группе"}

@router.get("/{group_id}/users", response_model=List[UserResponse])
async def get_group_users(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")

    if current_user not in group.users:
        raise HTTPException(status_code=403, detail="Недостаточно прав для просмотра пользователей группы")

    return group.users

