from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.requirement import Requirement
from app.models.user import User
from app.schemas.requirement import (
    RequirementCreate,
    RequirementResponse,
    RequirementUpdate,
)
from app.services import requirement as requirement_svc

router = APIRouter(prefix="/api", tags=["requirements"])


@router.post(
    "/projects/{project_id}/requirements",
    response_model=RequirementResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_requirement(
    project_id: str,
    body: RequirementCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        req = await requirement_svc.create_requirement(
            db,
            iteration_id=body.iteration_id,
            title=body.title,
            priority=body.priority,
            creator_id=user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return RequirementResponse.model_validate(req).model_dump()


@router.get(
    "/projects/{project_id}/requirements",
    response_model=list[RequirementResponse],
)
async def list_requirements(
    project_id: str,
    iteration_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    _user: Annotated[User, Depends(get_current_user)] = None,
):
    stmt = select(Requirement).order_by(Requirement.created_at)
    if iteration_id is not None:
        stmt = stmt.where(Requirement.iteration_id == iteration_id)
    if status is not None:
        stmt = stmt.where(Requirement.status == status)
    result = await db.execute(stmt)
    return [RequirementResponse.model_validate(r).model_dump() for r in result.scalars().all()]


@router.get("/requirements/{requirement_id}", response_model=RequirementResponse)
async def get_requirement(
    requirement_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(Requirement).where(Requirement.id == requirement_id)
    )
    req = result.scalars().first()
    if req is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found"
        )
    return RequirementResponse.model_validate(req).model_dump()


@router.patch("/requirements/{requirement_id}", response_model=RequirementResponse)
async def update_requirement(
    requirement_id: str,
    body: RequirementUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    update_data = body.model_dump(exclude_unset=True)
    update_data.pop("status", None)
    update_data.pop("assignee_id", None)
    try:
        req = await requirement_svc.update_requirement(
            db,
            requirement_id=requirement_id,
            user_id=user.id,
            title=update_data.get("title"),
            priority=update_data.get("priority"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return RequirementResponse.model_validate(req).model_dump()


@router.patch(
    "/requirements/{requirement_id}/status",
    response_model=RequirementResponse,
)
async def transition_requirement_status(
    requirement_id: str,
    body: RequirementUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    if body.status is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="status field is required",
        )
    try:
        req = await requirement_svc.update_requirement_status(
            db,
            requirement_id=requirement_id,
            new_status=body.status,
            user_id=user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    # Eagerly validate while session is still open to avoid MissingGreenlet
    return RequirementResponse.model_validate(req).model_dump()


@router.delete(
    "/requirements/{requirement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_requirement(
    requirement_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        await requirement_svc.delete_requirement(
            db,
            requirement_id=requirement_id,
            user_id=user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
