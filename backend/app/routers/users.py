from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.services import user as user_svc

router = APIRouter(prefix="/api", tags=["users"])


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    search: str | None = None,
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
    _user: Annotated[User, Depends(get_current_user)] = Depends(get_current_user),
):
    users = await user_svc.list_users(db, search=search)
    return [UserResponse.model_validate(u).model_dump() for u in users]


@router.get("/users/me", response_model=UserResponse)
async def get_current_user_info(
    user: Annotated[User, Depends(get_current_user)],
):
    return UserResponse.model_validate(user).model_dump()


@router.patch("/users/me", response_model=UserResponse)
async def update_current_user(
    body: UserUpdate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        updated = await user_svc.update_user(
            db,
            user_id=user.id,
            display_name=body.display_name,
            email=body.email,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return UserResponse.model_validate(updated).model_dump()


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalars().first()
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.model_validate(target).model_dump()
