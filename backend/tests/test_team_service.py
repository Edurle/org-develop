"""Unit tests for organization and team service layer.

Tests CRUD for organizations, teams, and team membership,
including slug uniqueness and membership constraints.
"""

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.models.team import Team
from app.models.user import TeamMember
from app.services.team import (
    create_organization,
    create_team,
    add_team_member,
    remove_team_member,
    update_team_member_role,
)
from app.services.user import create_user


# ────────────────────────────────────────────────────────────
# Organization
# ────────────────────────────────────────────────────────────

class TestOrganization:
    async def test_create_organization(self, db: AsyncSession):
        org = await create_organization(db, "Test Org", "test-org")
        assert org is not None
        assert org.name == "Test Org"
        assert org.slug == "test-org"

    async def test_create_organization_duplicate_slug(self, db: AsyncSession):
        await create_organization(db, "First Org", "dup-slug")
        with pytest.raises(ValueError, match="already exists"):
            await create_organization(db, "Second Org", "dup-slug")

    async def test_create_organization_different_slugs(self, db: AsyncSession):
        org1 = await create_organization(db, "Org One", "slug-one")
        org2 = await create_organization(db, "Org Two", "slug-two")
        assert org1.id != org2.id
        assert org1.slug != org2.slug


# ────────────────────────────────────────────────────────────
# Team
# ────────────────────────────────────────────────────────────

class TestTeam:
    async def test_create_team(self, db: AsyncSession):
        org = await create_organization(db, "Team Org", "team-org")
        team = await create_team(db, org.id, "Test Team", "test-team")
        assert team.org_id == org.id
        assert team.name == "Test Team"
        assert team.slug == "test-team"

    async def test_create_team_nonexistent_org(self, db: AsyncSession):
        with pytest.raises(ValueError, match="not found"):
            await create_team(db, "nonexistent-org-id", "Ghost Team", "ghost")

    async def test_create_multiple_teams_same_org(self, db: AsyncSession):
        org = await create_organization(db, "Multi Team Org", "multi-org")
        team1 = await create_team(db, org.id, "Team Alpha", "team-alpha")
        team2 = await create_team(db, org.id, "Team Beta", "team-beta")
        assert team1.org_id == team2.org_id == org.id
        assert team1.id != team2.id


# ────────────────────────────────────────────────────────────
# Team Member
# ────────────────────────────────────────────────────────────

class TestTeamMember:
    async def test_add_member(self, db: AsyncSession):
        org = await create_organization(db, "Member Org", "member-org")
        team = await create_team(db, org.id, "Member Team", "member-team")
        user = await create_user(
            db, "memberuser", "member@example.com", "password123"
        )
        member = await add_team_member(db, team.id, user.id, '["admin"]')
        assert member.team_id == team.id
        assert member.user_id == user.id
        assert member.roles == '["admin"]'

    async def test_add_member_default_roles(self, db: AsyncSession):
        org = await create_organization(db, "Role Org", "role-org")
        team = await create_team(db, org.id, "Role Team", "role-team")
        user = await create_user(
            db, "roleuser", "role@example.com", "password123"
        )
        member = await add_team_member(db, team.id, user.id, "developer")
        assert member.roles == "developer"

    async def test_add_member_duplicate_raises_value_error(self, db: AsyncSession):
        org = await create_organization(db, "Dup Org", "dup-org")
        team = await create_team(db, org.id, "Dup Team", "dup-team")
        user = await create_user(
            db, "dupuser", "dup@example.com", "password123"
        )
        await add_team_member(db, team.id, user.id, '["dev"]')
        with pytest.raises(ValueError, match="already a member"):
            await add_team_member(db, team.id, user.id, '["admin"]')

    async def test_add_member_nonexistent_team_raises_value_error(self, db: AsyncSession):
        user = await create_user(
            db, "noteamuser", "noteam@example.com", "password123"
        )
        with pytest.raises(ValueError, match="not found"):
            await add_team_member(db, "nonexistent-team", user.id, '["dev"]')

    async def test_add_multiple_members_to_team(self, db: AsyncSession):
        org = await create_organization(db, "Multi Org", "multi-member-org")
        team = await create_team(db, org.id, "Multi Team", "multi-member-team")
        user1 = await create_user(
            db, "multi1", "multi1@example.com", "password123"
        )
        user2 = await create_user(
            db, "multi2", "multi2@example.com", "password123"
        )
        m1 = await add_team_member(db, team.id, user1.id, '["admin"]')
        m2 = await add_team_member(db, team.id, user2.id, '["developer"]')
        assert m1.user_id != m2.user_id
        assert m1.team_id == m2.team_id == team.id


class TestRemoveTeamMember:
    async def test_remove_member(self, db: AsyncSession):
        org = await create_organization(db, "Remove Org", "remove-org")
        team = await create_team(db, org.id, "Remove Team", "remove-team")
        user = await create_user(
            db, "removeuser", "remove@example.com", "password123"
        )
        await add_team_member(db, team.id, user.id, "developer")
        await remove_team_member(db, team.id, user.id)
        result = await db.execute(
            select(TeamMember).where(
                TeamMember.team_id == team.id,
                TeamMember.user_id == user.id,
            )
        )
        assert result.scalars().first() is None

    async def test_remove_member_not_in_team(self, db: AsyncSession):
        with pytest.raises(ValueError, match="not a member"):
            await remove_team_member(db, "any-team", "any-user")

    async def test_remove_member_and_re_add(self, db: AsyncSession):
        org = await create_organization(db, "Readd Org", "readd-org")
        team = await create_team(db, org.id, "Readd Team", "readd-team")
        user = await create_user(
            db, "readduser", "readd@example.com", "password123"
        )
        await add_team_member(db, team.id, user.id, "developer")
        await remove_team_member(db, team.id, user.id)
        member = await add_team_member(db, team.id, user.id, "admin")
        assert member.roles == "admin"


class TestUpdateTeamMemberRole:
    async def test_update_member_role(self, db: AsyncSession):
        org = await create_organization(db, "UpdRole Org", "updrole-org")
        team = await create_team(db, org.id, "UpdRole Team", "updrole-team")
        user = await create_user(
            db, "updroleuser", "updrole@example.com", "password123"
        )
        await add_team_member(db, team.id, user.id, "developer")
        updated = await update_team_member_role(db, team.id, user.id, "admin")
        assert updated.roles == "admin"

    async def test_update_member_role_not_found(self, db: AsyncSession):
        with pytest.raises(ValueError, match="not a member"):
            await update_team_member_role(db, "any-team", "any-user", "admin")


class TestTeamMemberRoles:
    TEAM_ROLES = ["team_admin", "product_owner", "designer", "developer", "tester", "viewer"]

    async def test_add_member_with_each_role(self, db: AsyncSession):
        org = await create_organization(db, "Roles Org", "roles-org")
        team = await create_team(db, org.id, "Roles Team", "roles-team")
        for i, role in enumerate(self.TEAM_ROLES):
            user = await create_user(
                db, f"roleuser{i}", f"role{i}@example.com", "password123"
            )
            member = await add_team_member(db, team.id, user.id, role)
            assert member.roles == role

    async def test_update_to_each_role(self, db: AsyncSession):
        org = await create_organization(db, "UpdRoles Org", "updroles-org")
        team = await create_team(db, org.id, "UpdRoles Team", "updroles-team")
        user = await create_user(
            db, "updrolesuser", "updroles@example.com", "password123"
        )
        await add_team_member(db, team.id, user.id, "developer")
        for role in self.TEAM_ROLES:
            updated = await update_team_member_role(db, team.id, user.id, role)
            assert updated.roles == role

    async def test_mixed_roles_in_team(self, db: AsyncSession):
        org = await create_organization(db, "Mixed Org", "mixed-org")
        team = await create_team(db, org.id, "Mixed Team", "mixed-team")
        users_and_roles = [
            ("mixedadmin", "team_admin"),
            ("mixedpo", "product_owner"),
            ("mixeddesigner", "designer"),
            ("mixeddev", "developer"),
            ("mixedtester", "tester"),
            ("mixedviewer", "viewer"),
        ]
        for username, role in users_and_roles:
            user = await create_user(
                db, username, f"{username}@example.com", "password123"
            )
            member = await add_team_member(db, team.id, user.id, role)
            assert member.roles == role
