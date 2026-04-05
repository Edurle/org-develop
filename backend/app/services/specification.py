"""Service layer for specification and spec version management."""

from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.requirement import Requirement
from app.models.specification import Specification, SpecVersion
from app.models.iteration import Iteration
from app.services.audit import log_action
from app.services.spec_validation import validate_ui_spec_content
from app.services.webhook import WebhookEvent, dispatch_event


async def _check_all_specs_locked_for_requirement(
    db: AsyncSession, requirement_id: str
) -> bool:
    """Check if all specifications for a requirement have at least one locked version."""
    result = await db.execute(
        select(Specification).where(Specification.requirement_id == requirement_id)
    )
    specs = list(result.scalars().all())
    if not specs:
        return False

    for spec in specs:
        # Each spec must have at least one locked version
        ver_result = await db.execute(
            select(SpecVersion).where(
                SpecVersion.spec_id == spec.id,
                SpecVersion.status == "locked",
            )
        )
        if ver_result.scalars().first() is None:
            return False
    return True


async def create_specification(
    db: AsyncSession,
    requirement_id: str,
    spec_type: str,
    title: str,
) -> Specification:
    """Create a new specification for a requirement."""
    if spec_type not in ("api", "data", "flow", "ui"):
        raise ValueError(
            f"Invalid spec_type '{spec_type}'. "
            "Must be one of: api, data, flow, ui"
        )

    # Verify requirement exists
    result = await db.execute(
        select(Requirement).where(Requirement.id == requirement_id)
    )
    if result.scalars().first() is None:
        raise ValueError(f"Requirement '{requirement_id}' not found")

    spec = Specification(
        requirement_id=requirement_id,
        spec_type=spec_type,
        title=title,
        current_version=0,
    )
    db.add(spec)
    await db.flush()
    return spec


async def create_spec_version(
    db: AsyncSession,
    spec_id: str,
    content: dict,
) -> SpecVersion:
    """Create a new version of a specification with auto-incremented version number."""
    # Fetch the specification
    result = await db.execute(
        select(Specification).where(Specification.id == spec_id)
    )
    spec = result.scalars().first()
    if spec is None:
        raise ValueError(f"Specification '{spec_id}' not found")

    # Determine the next version number
    result = await db.execute(
        select(func.coalesce(func.max(SpecVersion.version), 0)).where(
            SpecVersion.spec_id == spec_id
        )
    )
    max_version = result.scalar_one()
    next_version = max_version + 1

    version = SpecVersion(
        spec_id=spec_id,
        version=next_version,
        status="draft",
        content=content,
    )
    db.add(version)

    # Update the specification's current_version pointer
    spec.current_version = next_version
    await db.flush()
    return version


async def submit_spec_for_review(
    db: AsyncSession,
    version_id: str,
) -> SpecVersion:
    """Submit a spec version for review (draft -> reviewing)."""
    result = await db.execute(
        select(SpecVersion).where(SpecVersion.id == version_id)
    )
    version = result.scalars().first()
    if version is None:
        raise ValueError(f"SpecVersion '{version_id}' not found")

    if version.status != "draft":
        raise ValueError(
            f"Cannot submit for review: version status is '{version.status}', "
            "expected 'draft'"
        )

    # Validate UI spec content before submitting for review
    spec_result = await db.execute(
        select(Specification).where(Specification.id == version.spec_id)
    )
    spec = spec_result.scalars().first()
    if spec is not None and spec.spec_type == "ui":
        errors = validate_ui_spec_content(version.content or {})
        if errors:
            raise ValueError(
                "UI spec validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            )

    version.status = "reviewing"
    await db.flush()
    return version


async def lock_spec(
    db: AsyncSession,
    version_id: str,
    user_id: str,
) -> SpecVersion:
    """Lock a spec version after review (reviewing -> locked)."""
    result = await db.execute(
        select(SpecVersion).where(SpecVersion.id == version_id)
    )
    version = result.scalars().first()
    if version is None:
        raise ValueError(f"SpecVersion '{version_id}' not found")

    if version.status != "reviewing":
        raise ValueError(
            f"Cannot lock: version status is '{version.status}', "
            "expected 'reviewing'"
        )

    version.status = "locked"
    version.locked_at = datetime.now(timezone.utc)
    version.locked_by = user_id
    await db.flush()

    await log_action(
        db, user_id=user_id, action="specification.lock",
        resource_type="spec_version", resource_id=version.id,
        detail=f"Locked spec version v{version.version}",
    )

    # Check if all specs for this requirement are now locked
    # and auto-transition requirement status
    spec_result = await db.execute(
        select(Specification).where(Specification.id == version.spec_id)
    )
    spec = spec_result.scalars().first()
    if spec is not None:
        req_result = await db.execute(
            select(Requirement).where(Requirement.id == spec.requirement_id)
        )
        requirement = req_result.scalars().first()
        if requirement and requirement.status == "spec_review":
            all_locked = await _check_all_specs_locked_for_requirement(
                db, requirement.id
            )
            if all_locked:
                requirement.status = "spec_locked"
                await db.flush()

    # Dispatch webhook event
    if spec is not None:
        req_result2 = await db.execute(
            select(Requirement).where(Requirement.id == spec.requirement_id)
        )
        req = req_result2.scalars().first()
        if req is not None:
            iter_result = await db.execute(
                select(Iteration).where(Iteration.id == req.iteration_id)
            )
            iteration = iter_result.scalars().first()
            if iteration is not None:
                await dispatch_event(
                    db,
                    project_id=iteration.project_id,
                    event=WebhookEvent.SPEC_LOCKED,
                    data={
                        "spec_id": spec.id,
                        "version_id": version.id,
                        "spec_type": spec.spec_type,
                        "requirement_id": spec.requirement_id,
                    },
                )

    return version


async def reject_spec(
    db: AsyncSession,
    version_id: str,
) -> SpecVersion:
    """Reject a spec version, sending it back to draft (reviewing -> draft)."""
    result = await db.execute(
        select(SpecVersion).where(SpecVersion.id == version_id)
    )
    version = result.scalars().first()
    if version is None:
        raise ValueError(f"SpecVersion '{version_id}' not found")

    if version.status != "reviewing":
        raise ValueError(
            f"Cannot reject: version status is '{version.status}', "
            "expected 'reviewing'"
        )

    version.status = "draft"
    await db.flush()

    # Dispatch webhook event for rejection
    spec_result = await db.execute(
        select(Specification).where(Specification.id == version.spec_id)
    )
    spec = spec_result.scalars().first()
    if spec is not None:
        req_result = await db.execute(
            select(Requirement).where(Requirement.id == spec.requirement_id)
        )
        req = req_result.scalars().first()
        if req is not None:
            iter_result = await db.execute(
                select(Iteration).where(Iteration.id == req.iteration_id)
            )
            iteration = iter_result.scalars().first()
            if iteration is not None:
                await dispatch_event(
                    db,
                    project_id=iteration.project_id,
                    event=WebhookEvent.SPEC_REJECTED,
                    data={
                        "spec_id": spec.id,
                        "version_id": version.id,
                        "spec_type": spec.spec_type,
                        "requirement_id": spec.requirement_id,
                    },
                )

    return version
