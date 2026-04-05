from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.iteration import Iteration
from app.models.user import User
from app.schemas.iteration import IterationCreate, IterationResponse, IterationUpdate
from app.services import iteration as iteration_svc
from app.services.audit import log_action

router = APIRouter(prefix="/api", tags=["iterations"])


@router.post(
    "/projects/{project_id}/iterations",
    response_model=IterationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_iteration(
    project_id: str,
    body: IterationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        it = await iteration_svc.create_iteration(
            db,
            project_id=project_id,
            name=body.name,
            start_date=body.start_date,
            end_date=body.end_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    await log_action(
        db, user_id=user.id, action="iteration.create",
        resource_type="iteration", resource_id=it.id,
        detail=f"Created iteration '{body.name}'",
    )
    return IterationResponse.model_validate(it).model_dump()


@router.get(
    "/projects/{project_id}/iterations",
    response_model=list[IterationResponse],
)
async def list_iterations(
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    iterations = await iteration_svc.list_iterations(db, project_id)
    return [IterationResponse.model_validate(i).model_dump() for i in iterations]


@router.patch(
    "/projects/{project_id}/iterations/{iteration_id}",
    response_model=IterationResponse,
)
async def update_iteration(
    project_id: str,
    iteration_id: str,
    body: IterationUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(Iteration).where(
            Iteration.id == iteration_id,
            Iteration.project_id == project_id,
        )
    )
    it = result.scalars().first()
    if it is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Iteration not found")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(it, field, value)
    await db.flush()
    return IterationResponse.model_validate(it).model_dump()
