"""Unit tests for iteration service layer.

Tests create and list operations on iterations,
including project validation and iteration listing by project.
"""

import pytest
import pytest_asyncio
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.iteration import create_iteration, list_iterations


class TestCreateIteration:
    async def test_create_iteration(self, db: AsyncSession, seed_data):
        it = await create_iteration(
            db, seed_data["project"].id, "Sprint 2"
        )
        assert it.project_id == seed_data["project"].id
        assert it.name == "Sprint 2"
        assert it.status == "planning"

    async def test_create_iteration_with_dates(self, db: AsyncSession, seed_data):
        start = date(2026, 4, 1)
        end = date(2026, 4, 14)
        it = await create_iteration(
            db, seed_data["project"].id, "Timed Sprint",
            start_date=start, end_date=end,
        )
        assert it.start_date == start
        assert it.end_date == end

    async def test_create_iteration_nonexistent_project(self, db: AsyncSession):
        with pytest.raises(ValueError, match="not found"):
            await create_iteration(db, "nonexistent-id", "Ghost Sprint")

    async def test_create_multiple_iterations(self, db: AsyncSession, seed_data):
        it1 = await create_iteration(db, seed_data["project"].id, "Sprint A")
        it2 = await create_iteration(db, seed_data["project"].id, "Sprint B")
        assert it1.id != it2.id
        assert it1.project_id == it2.project_id


class TestListIterations:
    async def test_list_iterations(self, db: AsyncSession, seed_data):
        await create_iteration(db, seed_data["project"].id, "List Sprint 1")
        await create_iteration(db, seed_data["project"].id, "List Sprint 2")
        result = await list_iterations(db, seed_data["project"].id)
        # seed_data already has one iteration from conftest ("Sprint 1")
        assert len(result) >= 2
        names = [it.name for it in result]
        assert "List Sprint 1" in names
        assert "List Sprint 2" in names

    async def test_list_iterations_empty_for_project_without_iterations(
        self, db: AsyncSession, seed_data
    ):
        from app.services.project import create_project

        proj = await create_project(
            db, seed_data["team"].id, "Iter Empty Project", "iter-empty"
        )
        result = await list_iterations(db, proj.id)
        assert result == []

    async def test_list_iterations_filters_by_project(self, db: AsyncSession, seed_data):
        from app.services.project import create_project

        proj2 = await create_project(
            db, seed_data["team"].id, "Other Iter Project", "other-iter"
        )
        await create_iteration(db, proj2.id, "Exclusive Sprint")
        original_iterations = await list_iterations(db, seed_data["project"].id)
        names = [it.name for it in original_iterations]
        assert "Exclusive Sprint" not in names
