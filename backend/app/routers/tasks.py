from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.iteration import Iteration
from app.models.task import DevTask, TestTask
from app.models.user import User
from app.schemas.task import (
    DevTaskCreate,
    DevTaskResponse,
    TestTaskCreate,
    TestTaskResponse,
)
from app.services import task as task_svc
from app.services.audit import log_action

router = APIRouter(prefix="/api", tags=["tasks"])


class StatusUpdate(BaseModel):
    status: str


# ---------------------------------------------------------------------------
# Dev Tasks
# ---------------------------------------------------------------------------


@router.post(
    "/requirements/{requirement_id}/dev-tasks",
    response_model=DevTaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_dev_task(
    requirement_id: str,
    body: DevTaskCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        t = await task_svc.create_dev_task(
            db,
            requirement_id=requirement_id,
            spec_version_id=body.spec_version_id,
            iteration_id=body.iteration_id,
            title=body.title,
            estimate_hours=body.estimate_hours,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    await log_action(
        db, user_id=user.id, action="task.dev.create",
        resource_type="dev_task", resource_id=t.id,
        detail=f"Created dev task '{body.title}'",
    )
    return DevTaskResponse.model_validate(t).model_dump()


@router.get("/projects/{project_id}/dev-tasks", response_model=list[DevTaskResponse])
async def list_dev_tasks(
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(DevTask)
        .join(Iteration, DevTask.iteration_id == Iteration.id)
        .where(Iteration.project_id == project_id)
        .order_by(DevTask.created_at)
    )
    return [DevTaskResponse.model_validate(t).model_dump() for t in result.scalars().all()]


@router.patch("/dev-tasks/{task_id}/claim", response_model=DevTaskResponse)
async def claim_dev_task(
    task_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        t = await task_svc.claim_dev_task(db, task_id=task_id, user_id=user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return DevTaskResponse.model_validate(t).model_dump()


@router.patch("/dev-tasks/{task_id}/status", response_model=DevTaskResponse)
async def update_dev_task_status(
    task_id: str,
    body: StatusUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        t = await task_svc.update_task_status(
            db, task_id=task_id, new_status=body.status
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    await log_action(
        db, user_id=user.id, action="task.dev.update_status",
        resource_type="dev_task", resource_id=t.id,
        detail=f"Dev task status changed to '{body.status}'",
    )
    return DevTaskResponse.model_validate(t).model_dump()


# ---------------------------------------------------------------------------
# Test Tasks
# ---------------------------------------------------------------------------


@router.post(
    "/requirements/{requirement_id}/test-tasks",
    response_model=TestTaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_test_task(
    requirement_id: str,
    body: TestTaskCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        t = await task_svc.create_test_task(
            db,
            requirement_id=requirement_id,
            iteration_id=body.iteration_id,
            title=body.title,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    await log_action(
        db, user_id=user.id, action="task.test.create",
        resource_type="test_task", resource_id=t.id,
        detail=f"Created test task '{body.title}'",
    )
    return TestTaskResponse.model_validate(t).model_dump()


@router.get(
    "/projects/{project_id}/test-tasks",
    response_model=list[TestTaskResponse],
)
async def list_test_tasks(
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(TestTask)
        .join(Iteration, TestTask.iteration_id == Iteration.id)
        .where(Iteration.project_id == project_id)
        .order_by(TestTask.created_at)
    )
    return [TestTaskResponse.model_validate(t).model_dump() for t in result.scalars().all()]
