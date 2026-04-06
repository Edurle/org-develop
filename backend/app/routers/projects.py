from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services import project as project_svc
from app.services.audit import log_action

router = APIRouter(prefix="/api", tags=["projects"])


@router.post(
    "/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    body: ProjectCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        proj = await project_svc.create_project(
            db,
            team_id=body.team_id,
            name=body.name,
            slug=body.slug,
            description=body.description,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    await log_action(
        db, user_id=user.id, action="project.create",
        resource_type="project", resource_id=proj.id,
        detail=f"Created project '{body.name}'",
    )
    return ProjectResponse.model_validate(proj).model_dump()


@router.get("/projects", response_model=list[ProjectResponse])
async def list_projects(
    team_id: str | None = Query(default=None),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    _user: Annotated[User, Depends(get_current_user)] = None,
):
    stmt = select(Project).order_by(Project.created_at)
    if team_id is not None:
        stmt = stmt.where(Project.team_id == team_id)
    result = await db.execute(stmt)
    return [ProjectResponse.model_validate(p).model_dump() for p in result.scalars().all()]


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    proj = await project_svc.get_project(db, project_id)
    if proj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return ProjectResponse.model_validate(proj).model_dump()


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    body: ProjectUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    proj = result.scalars().first()
    if proj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(proj, field, value)
    await db.flush()
    await db.refresh(proj)
    await log_action(
        db, user_id=user.id, action="project.update",
        resource_type="project", resource_id=proj.id,
        detail=f"Updated project fields: {', '.join(update_data.keys())}",
    )
    return ProjectResponse.model_validate(proj).model_dump()


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    proj = result.scalars().first()
    if proj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    await log_action(
        db, user_id=user.id, action="project.delete",
        resource_type="project", resource_id=proj.id,
        detail=f"Deleted project '{proj.name}'",
    )
    await db.delete(proj)
    await db.flush()
