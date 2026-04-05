"""Unit tests for project service layer.

Tests create, get, and list operations on projects,
including team validation and listing by team.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.project import create_project, get_project, list_projects


class TestCreateProject:
    async def test_create_project(self, db: AsyncSession, seed_data):
        proj = await create_project(
            db,
            team_id=seed_data["team"].id,
            name="Test Project",
            slug="test-project",
            description="A test project",
        )
        assert proj.slug == "test-project"
        assert proj.name == "Test Project"
        assert proj.description == "A test project"
        assert proj.team_id == seed_data["team"].id

    async def test_create_project_without_description(self, db: AsyncSession, seed_data):
        proj = await create_project(
            db,
            team_id=seed_data["team"].id,
            name="No Desc Project",
            slug="no-desc",
        )
        assert proj.description is None

    async def test_create_project_nonexistent_team(self, db: AsyncSession):
        with pytest.raises(ValueError, match="not found"):
            await create_project(
                db,
                team_id="nonexistent-team-id",
                name="Ghost Project",
                slug="ghost",
            )

    async def test_create_multiple_projects_same_team(self, db: AsyncSession, seed_data):
        proj1 = await create_project(
            db, seed_data["team"].id, "Project A", "proj-a"
        )
        proj2 = await create_project(
            db, seed_data["team"].id, "Project B", "proj-b"
        )
        assert proj1.id != proj2.id
        assert proj1.team_id == proj2.team_id


class TestGetProject:
    async def test_get_project(self, db: AsyncSession, seed_data):
        proj = await create_project(
            db, seed_data["team"].id, "Findable Project", "find-proj"
        )
        result = await get_project(db, proj.id)
        assert result is not None
        assert result.id == proj.id
        assert result.name == "Findable Project"

    async def test_get_project_nonexistent(self, db: AsyncSession):
        result = await get_project(db, "nonexistent-id")
        assert result is None


class TestListProjects:
    async def test_list_projects(self, db: AsyncSession, seed_data):
        await create_project(
            db, seed_data["team"].id, "Listed Project 1", "listed-1"
        )
        await create_project(
            db, seed_data["team"].id, "Listed Project 2", "listed-2"
        )
        result = await list_projects(db, seed_data["team"].id)
        # seed_data already has one project from conftest
        assert len(result) >= 2
        names = [p.name for p in result]
        assert "Listed Project 1" in names
        assert "Listed Project 2" in names

    async def test_list_projects_empty_for_team_without_projects(self, db: AsyncSession):
        from app.services.team import create_organization, create_team

        org = await create_organization(db, "Empty Org", "empty-org")
        team = await create_team(db, org.id, "Empty Team", "empty-team")
        result = await list_projects(db, team.id)
        assert result == []

    async def test_list_projects_filters_by_team(self, db: AsyncSession, seed_data):
        from app.services.team import create_organization, create_team

        # Create a second team with its own project
        org2 = await create_organization(db, "Other Org", "other-org")
        team2 = await create_team(db, org2.id, "Other Team", "other-team")
        await create_project(db, team2.id, "Other Project", "other-proj")

        # Original team's projects should not include the other team's project
        original_projects = await list_projects(db, seed_data["team"].id)
        names = [p.name for p in original_projects]
        assert "Other Project" not in names
