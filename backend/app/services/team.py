"""Service layer for organization and team management."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.models.team import Team
from app.models.user import TeamMember


async def create_organization(
    db: AsyncSession, name: str, slug: str
) -> Organization:
    """Create a new organization."""
    # Check slug uniqueness
    result = await db.execute(
        select(Organization).where(Organization.slug == slug)
    )
    if result.scalars().first() is not None:
        raise ValueError(f"Organization slug '{slug}' already exists")

    org = Organization(name=name, slug=slug)
    db.add(org)
    await db.flush()
    return org


async def create_team(
    db: AsyncSession, org_id: str, name: str, slug: str
) -> Team:
    """Create a new team within an organization."""
    # Verify organization exists
    result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    org = result.scalars().first()
    if org is None:
        raise ValueError(f"Organization '{org_id}' not found")

    team = Team(org_id=org_id, name=name, slug=slug)
    db.add(team)
    await db.flush()
    return team


async def add_team_member(
    db: AsyncSession, team_id: str, user_id: str, roles: str
) -> TeamMember:
    """Add a member to a team with specified roles."""
    # Verify team exists
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalars().first()
    if team is None:
        raise ValueError(f"Team '{team_id}' not found")

    # Check for duplicate membership
    result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id,
        )
    )
    if result.scalars().first() is not None:
        raise ValueError(
            f"User '{user_id}' is already a member of team '{team_id}'"
        )

    member = TeamMember(team_id=team_id, user_id=user_id, roles=roles)
    db.add(member)
    await db.flush()
    return member


async def remove_team_member(
    db: AsyncSession, team_id: str, user_id: str
) -> None:
    result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id,
        )
    )
    member = result.scalars().first()
    if member is None:
        raise ValueError(f"User '{user_id}' is not a member of team '{team_id}'")
    await db.delete(member)
    await db.flush()


async def update_team_member_role(
    db: AsyncSession, team_id: str, user_id: str, roles: str
) -> TeamMember:
    result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id,
        )
    )
    member = result.scalars().first()
    if member is None:
        raise ValueError(f"User '{user_id}' is not a member of team '{team_id}'")
    member.roles = roles
    await db.flush()
    return member
