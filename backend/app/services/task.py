"""Service layer for development and test task management."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.requirement import Requirement
from app.models.specification import SpecVersion
from app.models.task import DevTask, TestTask
from app.services.audit import log_action
from app.services.webhook import WebhookEvent, dispatch_event


async def _get_project_id_for_requirement(
    db: AsyncSession, requirement_id: str
) -> str | None:
    """Resolve project_id from requirement through iteration."""
    from app.models.iteration import Iteration

    result = await db.execute(
        select(Requirement).where(Requirement.id == requirement_id)
    )
    req = result.scalars().first()
    if req is None:
        return None
    iter_result = await db.execute(
        select(Iteration).where(Iteration.id == req.iteration_id)
    )
    iteration = iter_result.scalars().first()
    return iteration.project_id if iteration else None

# Dev task status transition map
_DEV_TASK_TRANSITIONS: dict[str, list[str]] = {
    "open": ["in_progress"],
    "in_progress": ["review", "blocked"],
    "review": ["done", "in_progress"],
    "blocked": ["in_progress"],
    "done": [],
}

# Requirement statuses that allow dev task creation
_VALID_REQ_STATUSES_FOR_DEV = {"spec_locked", "in_progress", "testing"}


async def create_dev_task(
    db: AsyncSession,
    requirement_id: str,
    spec_version_id: str,
    iteration_id: str,
    title: str,
    estimate_hours: float | None = None,
) -> DevTask:
    """Create a new development task linked to a requirement and spec version."""
    # Validate requirement status
    result = await db.execute(
        select(Requirement).where(Requirement.id == requirement_id)
    )
    requirement = result.scalars().first()
    if requirement is None:
        raise ValueError(f"Requirement '{requirement_id}' not found")

    if requirement.status not in _VALID_REQ_STATUSES_FOR_DEV:
        raise ValueError(
            f"Cannot create dev task: requirement status is "
            f"'{requirement.status}'. Must be one of: "
            f"{', '.join(sorted(_VALID_REQ_STATUSES_FOR_DEV))}"
        )

    # Validate spec version is locked
    result = await db.execute(
        select(SpecVersion).where(SpecVersion.id == spec_version_id)
    )
    spec_version = result.scalars().first()
    if spec_version is None:
        raise ValueError(f"SpecVersion '{spec_version_id}' not found")

    if spec_version.status != "locked":
        raise ValueError(
            f"Cannot create dev task: spec version status is "
            f"'{spec_version.status}', expected 'locked'"
        )

    task = DevTask(
        requirement_id=requirement_id,
        spec_version_id=spec_version_id,
        iteration_id=iteration_id,
        title=title,
        status="open",
        estimate_hours=estimate_hours,
    )
    db.add(task)
    await db.flush()
    return task


async def claim_dev_task(
    db: AsyncSession, task_id: str, user_id: str
) -> DevTask:
    """Claim an open dev task (open -> in_progress)."""
    result = await db.execute(
        select(DevTask).where(DevTask.id == task_id)
    )
    task = result.scalars().first()
    if task is None:
        raise ValueError(f"DevTask '{task_id}' not found")

    if task.status != "open":
        raise ValueError(
            f"Cannot claim task: status is '{task.status}', expected 'open'"
        )

    task.status = "in_progress"
    task.assignee_id = user_id
    await db.flush()
    await db.refresh(task)

    await log_action(
        db, user_id=user_id, action="task.dev.claim",
        resource_type="dev_task", resource_id=task.id,
        detail=f"Claimed dev task '{task.title}'",
    )

    # Dispatch webhook
    project_id = await _get_project_id_for_requirement(db, task.requirement_id)
    if project_id:
        await dispatch_event(
            db, project_id=project_id, event=WebhookEvent.TASK_CLAIMED,
            data={"task_id": task.id, "task_type": "dev", "assignee_id": user_id},
        )

    return task


async def update_task_status(
    db: AsyncSession, task_id: str, new_status: str
) -> DevTask:
    """Update a dev task's status with transition validation."""
    result = await db.execute(
        select(DevTask).where(DevTask.id == task_id)
    )
    task = result.scalars().first()
    if task is None:
        raise ValueError(f"DevTask '{task_id}' not found")

    if task.status == new_status:
        raise ValueError(f"Task is already in '{new_status}' status")

    allowed = _DEV_TASK_TRANSITIONS.get(task.status, [])
    if new_status not in allowed:
        raise ValueError(
            f"Invalid task status transition: '{task.status}' -> "
            f"'{new_status}'. Allowed from '{task.status}': {allowed}"
        )

    task.status = new_status
    await db.flush()
    await db.refresh(task)

    # Dispatch webhook
    project_id = await _get_project_id_for_requirement(db, task.requirement_id)
    if project_id:
        await dispatch_event(
            db, project_id=project_id, event=WebhookEvent.TASK_STATUS_CHANGED,
            data={"task_id": task.id, "task_type": "dev", "new_status": new_status},
        )

    return task


async def create_test_task(
    db: AsyncSession,
    requirement_id: str,
    iteration_id: str,
    title: str,
) -> TestTask:
    """Create a new test task for a requirement."""
    # Verify requirement exists
    result = await db.execute(
        select(Requirement).where(Requirement.id == requirement_id)
    )
    requirement = result.scalars().first()
    if requirement is None:
        raise ValueError(f"Requirement '{requirement_id}' not found")

    task = TestTask(
        requirement_id=requirement_id,
        iteration_id=iteration_id,
        title=title,
        status="open",
    )
    db.add(task)
    await db.flush()
    return task


async def update_dev_task(
    db: AsyncSession,
    task_id: str,
    title: str | None = None,
    estimate_hours: float | None = None,
    assignee_id: str | None = None,
) -> DevTask:
    """Update editable fields on a dev task."""
    result = await db.execute(
        select(DevTask).where(DevTask.id == task_id)
    )
    task = result.scalars().first()
    if task is None:
        raise ValueError(f"DevTask '{task_id}' not found")

    if title is not None:
        task.title = title
    if estimate_hours is not None:
        task.estimate_hours = estimate_hours
    if assignee_id is not None:
        task.assignee_id = assignee_id

    await db.flush()
    await db.refresh(task)
    return task


async def delete_dev_task(
    db: AsyncSession,
    task_id: str,
) -> None:
    """Delete a dev task that is still in 'open' status."""
    result = await db.execute(
        select(DevTask).where(DevTask.id == task_id)
    )
    task = result.scalars().first()
    if task is None:
        raise ValueError(f"DevTask '{task_id}' not found")

    if task.status != "open":
        raise ValueError(
            f"Cannot delete task: status is '{task.status}', expected 'open'"
        )

    await db.delete(task)
    await db.flush()
