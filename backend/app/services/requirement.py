"""Service layer for requirement management with status transition validation."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.requirement import Requirement
from app.services.audit import log_action
from app.services.coverage import check_coverage_sufficient
from app.services.webhook import WebhookEvent, dispatch_event

# Allowed forward transitions for the main workflow
_VALID_TRANSITIONS: dict[str, list[str]] = {
    "draft": ["spec_writing"],
    "spec_writing": ["spec_review"],
    "spec_review": ["spec_locked", "spec_rejected"],
    "spec_rejected": ["spec_writing"],
    "spec_locked": ["in_progress", "cancelled"],
    "in_progress": ["testing", "cancelled"],
    "testing": ["done", "cancelled"],
    "done": [],
    "cancelled": [],
}

# Statuses from which cancellation is allowed (supplementary check)
_CANCELLABLE_FROM = {"spec_locked", "in_progress", "testing"}


def _is_valid_transition(current: str, target: str) -> bool:
    """Check whether transitioning from current to target status is allowed."""
    allowed = _VALID_TRANSITIONS.get(current, [])
    return target in allowed


async def create_requirement(
    db: AsyncSession,
    iteration_id: str,
    title: str,
    priority: str = "medium",
    creator_id: str = "",
) -> Requirement:
    """Create a new requirement in draft status."""
    if priority not in ("low", "medium", "high", "critical"):
        raise ValueError(
            f"Invalid priority '{priority}'. "
            "Must be one of: low, medium, high, critical"
        )

    requirement = Requirement(
        iteration_id=iteration_id,
        title=title,
        priority=priority,
        status="draft",
        creator_id=creator_id,
    )
    db.add(requirement)
    await db.flush()
    await log_action(
        db, user_id=creator_id, action="requirement.create",
        resource_type="requirement", resource_id=requirement.id,
        detail=f"Created requirement '{title}' with priority '{priority}'",
    )
    return requirement


async def update_requirement(
    db: AsyncSession,
    requirement_id: str,
    user_id: str,
    title: str | None = None,
    priority: str | None = None,
) -> Requirement:
    """Update a requirement's title and/or priority."""
    result = await db.execute(
        select(Requirement).where(Requirement.id == requirement_id)
    )
    requirement = result.scalars().first()
    if requirement is None:
        raise ValueError(f"Requirement '{requirement_id}' not found")

    if title is not None:
        requirement.title = title

    if priority is not None:
        if priority not in ("low", "medium", "high", "critical"):
            raise ValueError(
                f"Invalid priority '{priority}'. "
                "Must be one of: low, medium, high, critical"
            )
        requirement.priority = priority

    await db.flush()
    await log_action(
        db, user_id=user_id, action="requirement.update",
        resource_type="requirement", resource_id=requirement.id,
        detail=f"Updated requirement '{requirement.title}'",
    )
    await db.refresh(requirement)
    return requirement


async def delete_requirement(
    db: AsyncSession,
    requirement_id: str,
    user_id: str,
) -> None:
    """Delete a requirement. Only allowed in draft or cancelled status."""
    result = await db.execute(
        select(Requirement).where(Requirement.id == requirement_id)
    )
    requirement = result.scalars().first()
    if requirement is None:
        raise ValueError(f"Requirement '{requirement_id}' not found")

    if requirement.status not in ("draft", "cancelled"):
        raise ValueError(
            f"Cannot delete requirement in '{requirement.status}' status. "
            "Only 'draft' or 'cancelled' requirements can be deleted."
        )

    await log_action(
        db, user_id=user_id, action="requirement.delete",
        resource_type="requirement", resource_id=requirement.id,
        detail=f"Deleted requirement '{requirement.title}'",
    )
    await db.delete(requirement)
    await db.flush()


async def update_requirement_status(
    db: AsyncSession,
    requirement_id: str,
    new_status: str,
    user_id: str,
) -> Requirement:
    """Transition a requirement to a new status with validation."""
    result = await db.execute(
        select(Requirement).where(Requirement.id == requirement_id)
    )
    requirement = result.scalars().first()
    if requirement is None:
        raise ValueError(f"Requirement '{requirement_id}' not found")

    current_status = requirement.status

    if current_status == new_status:
        raise ValueError(
            f"Requirement is already in '{new_status}' status"
        )

    if not _is_valid_transition(current_status, new_status):
        raise ValueError(
            f"Invalid status transition: '{current_status}' -> '{new_status}'. "
            f"Allowed transitions from '{current_status}': "
            f"{_VALID_TRANSITIONS.get(current_status, [])}"
        )

    # Coverage gate: testing -> done requires sufficient coverage
    if new_status == "done":
        sufficient = await check_coverage_sufficient(db, requirement_id)
        if not sufficient:
            raise ValueError(
                "Cannot mark requirement as done: test coverage insufficient. "
                "All 'must' clauses require 100% coverage, "
                "'should' clauses require >=80% coverage."
            )

    requirement.status = new_status
    requirement.assignee_id = user_id
    await db.flush()
    await log_action(
        db, user_id=user_id, action="requirement.status_change",
        resource_type="requirement", resource_id=requirement.id,
        detail=f"Status changed from '{current_status}' to '{new_status}'",
    )
    await db.refresh(requirement)

    # Dispatch webhook event
    await _dispatch_requirement_event(db, requirement, new_status)

    return requirement


async def _dispatch_requirement_event(
    db: AsyncSession,
    requirement: Requirement,
    new_status: str,
) -> None:
    """Dispatch webhook events for requirement status changes."""
    # Determine project_id through iteration
    from app.models.iteration import Iteration

    iter_result = await db.execute(
        select(Iteration).where(Iteration.id == requirement.iteration_id)
    )
    iteration = iter_result.scalars().first()
    if iteration is None:
        return

    event = WebhookEvent.REQUIREMENT_STATUS_CHANGED
    await dispatch_event(
        db,
        project_id=iteration.project_id,
        event=event,
        data={
            "requirement_id": requirement.id,
            "title": requirement.title,
            "old_status": requirement.status,
            "new_status": new_status,
        },
    )

    # Dispatch coverage-specific events
    if new_status == "testing":
        from app.services.coverage import check_coverage_sufficient

        sufficient = await check_coverage_sufficient(db, requirement.id)
        if not sufficient:
            await dispatch_event(
                db,
                project_id=iteration.project_id,
                event=WebhookEvent.COVERAGE_INSUFFICIENT,
                data={"requirement_id": requirement.id},
            )
