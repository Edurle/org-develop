from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.organization import Organization
from app.models.team import Team
from app.models.user import TeamMember, User
from app.schemas.team import (
    OrganizationCreate,
    OrganizationResponse,
    TeamCreate,
    TeamResponse,
)
from app.schemas.user import TeamMemberCreate, TeamMemberResponse
from app.services import team as team_svc
from app.services.audit import log_action

router = APIRouter(prefix="/api", tags=["teams"])


# ---------------------------------------------------------------------------
# Organizations
# ---------------------------------------------------------------------------


@router.post(
    "/organizations",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_organization(
    body: OrganizationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        org = await team_svc.create_organization(db, name=body.name, slug=body.slug)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    await log_action(
        db, user_id=user.id, action="organization.create",
        resource_type="organization", resource_id=org.id,
        detail=f"Created organization '{body.name}'",
    )
    return OrganizationResponse.model_validate(org).model_dump()


@router.get("/organizations", response_model=list[OrganizationResponse])
async def list_organizations(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(Organization).order_by(Organization.created_at)
    )
    return [OrganizationResponse.model_validate(o).model_dump() for o in result.scalars().all()]


# ---------------------------------------------------------------------------
# Teams
# ---------------------------------------------------------------------------


@router.post(
    "/teams",
    response_model=TeamResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_team(
    body: TeamCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        t = await team_svc.create_team(
            db, org_id=body.org_id, name=body.name, slug=body.slug
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    await log_action(
        db, user_id=user.id, action="team.create",
        resource_type="team", resource_id=t.id,
        detail=f"Created team '{body.name}'",
    )
    return TeamResponse.model_validate(t).model_dump()


@router.get("/teams", response_model=list[TeamResponse])
async def list_teams(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(select(Team).order_by(Team.created_at))
    return [TeamResponse.model_validate(t).model_dump() for t in result.scalars().all()]


# ---------------------------------------------------------------------------
# Team Members
# ---------------------------------------------------------------------------


@router.post(
    "/teams/{team_id}/members",
    response_model=TeamMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_team_member(
    team_id: str,
    body: TeamMemberCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        member = await team_svc.add_team_member(
            db, team_id=team_id, user_id=body.user_id, roles=body.roles
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    await log_action(
        db, user_id=user.id, action="team.member.add",
        resource_type="team_member", resource_id=member.id,
        detail=f"Added user '{body.user_id}' to team '{team_id}' with roles '{body.roles}'",
    )
    return TeamMemberResponse.model_validate(member).model_dump()


@router.get("/teams/{team_id}/members", response_model=list[TeamMemberResponse])
async def list_team_members(
    team_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(TeamMember)
        .where(TeamMember.team_id == team_id)
        .order_by(TeamMember.joined_at)
    )
    return [TeamMemberResponse.model_validate(m).model_dump() for m in result.scalars().all()]
