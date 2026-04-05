"""Service layer for project management."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.team import Team


async def create_project(
    db: AsyncSession,
    team_id: str,
    name: str,
    slug: str,
    description: str | None = None,
) -> Project:
    """Create a new project within a team."""
    # Verify team exists
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalars().first()
    if team is None:
        raise ValueError(f"Team '{team_id}' not found")

    project = Project(
        team_id=team_id, name=name, slug=slug, description=description
    )
    db.add(project)
    await db.flush()
    return project


async def get_project(
    db: AsyncSession, project_id: str
) -> Project | None:
    """Retrieve a project by ID."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    return result.scalars().first()


async def list_projects(
    db: AsyncSession, team_id: str
) -> list[Project]:
    """List all projects belonging to a team."""
    result = await db.execute(
        select(Project)
        .where(Project.team_id == team_id)
        .order_by(Project.created_at)
    )
    return list(result.scalars().all())
