"""Service layer for specification clause management."""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.specification import SpecVersion, SpecClause

# Category prefix mapping for auto-generated clause IDs
_CATEGORY_PREFIXES = {
    "functional": "FN",
    "validation": "VD",
    "security": "SC",
    "performance": "PF",
    "ui_element": "UI",
}


async def _next_clause_number(db: AsyncSession, spec_version_id: str) -> int:
    """Get the next clause number for a spec version."""
    result = await db.execute(
        select(func.coalesce(func.count(SpecClause.id), 0)).where(
            SpecClause.spec_version_id == spec_version_id
        )
    )
    return result.scalar_one() + 1


async def create_clause(
    db: AsyncSession,
    spec_version_id: str,
    clause_id: str,
    title: str,
    description: str,
    category: str,
    severity: str = "must",
) -> SpecClause:
    """Create a new clause under a spec version."""
    # Verify spec version exists
    result = await db.execute(
        select(SpecVersion).where(SpecVersion.id == spec_version_id)
    )
    version = result.scalars().first()
    if version is None:
        raise ValueError(f"SpecVersion '{spec_version_id}' not found")

    # LOCKED versions cannot be modified
    if version.status == "locked":
        raise ValueError(
            "Cannot add clauses to a locked spec version"
        )

    # Validate category
    valid_categories = (
        "functional", "validation", "security", "performance", "ui_element",
    )
    if category not in valid_categories:
        raise ValueError(
            f"Invalid category '{category}'. "
            f"Must be one of: {', '.join(valid_categories)}"
        )

    # Validate severity
    if severity not in ("must", "should", "may"):
        raise ValueError(
            f"Invalid severity '{severity}'. Must be one of: must, should, may"
        )

    clause = SpecClause(
        spec_version_id=spec_version_id,
        clause_id=clause_id,
        title=title,
        description=description,
        category=category,
        severity=severity,
    )
    db.add(clause)
    await db.flush()
    return clause


async def list_clauses(
    db: AsyncSession, spec_version_id: str
) -> list[SpecClause]:
    """List all clauses for a spec version."""
    result = await db.execute(
        select(SpecClause)
        .where(SpecClause.spec_version_id == spec_version_id)
        .order_by(SpecClause.clause_id)
    )
    return list(result.scalars().all())
