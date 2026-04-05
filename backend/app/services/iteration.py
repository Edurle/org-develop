"""Service layer for iteration (sprint) management."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.iteration import Iteration
from app.models.project import Project


async def create_iteration(
    db: AsyncSession,
    project_id: str,
    name: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> Iteration:
    """Create a new iteration within a project."""
    # Verify project exists
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalars().first()
    if project is None:
        raise ValueError(f"Project '{project_id}' not found")

    iteration = Iteration(
        project_id=project_id,
        name=name,
        start_date=start_date,
        end_date=end_date,
    )
    db.add(iteration)
    await db.flush()
    return iteration


async def list_iterations(
    db: AsyncSession, project_id: str
) -> list[Iteration]:
    """List all iterations for a project."""
    result = await db.execute(
        select(Iteration)
        .where(Iteration.project_id == project_id)
        .order_by(Iteration.created_at)
    )
    return list(result.scalars().all())
