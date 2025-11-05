from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.models import User, Group
from app.schemas import GroupCreate, GroupUpdate, GroupResponse
from app.routes.users import get_current_user

router = APIRouter(prefix="/api/groups", tags=["groups"])

@router.get("", response_model=List[GroupResponse])
async def get_groups(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Group).where(Group.owner_id == current_user.id)
    )
    groups = result.scalars().all()
    return groups

@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_data: GroupCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    new_group = Group(
        name=group_data.name,
        owner_id=current_user.id
    )
    
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
        select(Group).where(Group.id == group_id)
    )
    group = result.scalars().first()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Группа не найдена"
        )
    
    if group.owner_id != current_user.id:
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
        select(Group).where(Group.id == group_id)
    )
    group = result.scalars().first()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Группа не найдена"
        )
    
    if group.owner_id != current_user.id:
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
        select(Group).where(Group.id == group_id)
    )
    group = result.scalars().first()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Группа не найдена"
        )
    
    if group.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра этой группы"
        )
    
    return group

