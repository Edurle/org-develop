"""Unit tests for test case service layer.

Tests creating test cases with clause coverage, status transitions,
and validation of invalid clause IDs.
"""

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.testcase import TestCase, ClauseCoverage
from app.services.requirement import create_requirement, update_requirement_status
from app.services.specification import (
    create_specification,
    create_spec_version,
)
from app.services.clause import create_clause
from app.services.task import create_test_task
from app.services.testcase import create_test_case, update_test_case_status


@pytest_asyncio.fixture
async def req_with_seed(db: AsyncSession, seed_data):
    """Create a requirement in draft status."""
    req = await create_requirement(
        db,
        iteration_id=seed_data["iteration"].id,
        title="TestCase Test Req",
        priority="medium",
        creator_id=seed_data["user"].id,
    )
    return {**seed_data, "requirement": req}


class TestTestCaseService:

    async def _setup_test_task_with_clauses(self, db, req_with_seed):
        """Create a requirement with a spec, clause, and test task for testing."""
        req_id = req_with_seed["requirement"].id
        uid = req_with_seed["user"].id
        iter_id = req_with_seed["iteration"].id

        await update_requirement_status(db, req_id, "spec_writing", uid)
        spec = await create_specification(db, req_id, "api", "Test Spec")
        version = await create_spec_version(db, spec.id, {"endpoints": []})
        clause = await create_clause(
            db, version.id, "FN-001", "Test Clause",
            "A functional clause", "functional", "must",
        )
        test_task = await create_test_task(db, req_id, iter_id, "Test Task")
        return test_task, clause

    async def test_create_test_case(self, db, req_with_seed):
        test_task, clause = await self._setup_test_task_with_clauses(db, req_with_seed)
        tc = await create_test_case(
            db, test_task.id, "Verify Login", "User exists",
            "1. POST /login\n2. Check response", "200 OK",
            clause_ids=[clause.id],
        )
        assert tc.status == "pending"
        assert tc.title == "Verify Login"
        assert tc.preconditions == "User exists"
        assert tc.steps == "1. POST /login\n2. Check response"
        assert tc.expected_result == "200 OK"

        # Verify ClauseCoverage link
        result = await db.execute(
            select(ClauseCoverage).where(ClauseCoverage.test_case_id == tc.id)
        )
        coverages = list(result.scalars().all())
        assert len(coverages) == 1
        assert coverages[0].clause_id == clause.id

    async def test_create_test_case_invalid_clause(self, db, req_with_seed):
        test_task, _ = await self._setup_test_task_with_clauses(db, req_with_seed)
        with pytest.raises(ValueError, match="clause IDs do not exist"):
            await create_test_case(
                db, test_task.id, "Test", None, "Steps", "Result",
                clause_ids=["nonexistent-id"],
            )

    async def test_create_test_case_no_clauses(self, db, req_with_seed):
        test_task, _ = await self._setup_test_task_with_clauses(db, req_with_seed)
        tc = await create_test_case(
            db, test_task.id, "Test", None, "Steps", "Result",
            clause_ids=[],
        )
        assert tc.status == "pending"
        assert tc.title == "Test"

    async def test_update_test_case_status_transitions(self, db, req_with_seed):
        test_task, _ = await self._setup_test_task_with_clauses(db, req_with_seed)
        tc = await create_test_case(
            db, test_task.id, "Test", None, "Steps", "Result",
            clause_ids=[],
        )
        # pending -> running
        tc = await update_test_case_status(db, tc.id, "running")
        assert tc.status == "running"

        # running -> passed
        tc = await update_test_case_status(db, tc.id, "passed")
        assert tc.status == "passed"

    async def test_update_test_case_status_failed_path(self, db, req_with_seed):
        test_task, _ = await self._setup_test_task_with_clauses(db, req_with_seed)
        tc = await create_test_case(
            db, test_task.id, "Test", None, "Steps", "Result",
            clause_ids=[],
        )
        tc = await update_test_case_status(db, tc.id, "running")
        # running -> failed
        tc = await update_test_case_status(db, tc.id, "failed")
        assert tc.status == "failed"
        # failed -> running (retry)
        tc = await update_test_case_status(db, tc.id, "running")
        assert tc.status == "running"

    async def test_update_test_case_status_blocked_path(self, db, req_with_seed):
        test_task, _ = await self._setup_test_task_with_clauses(db, req_with_seed)
        tc = await create_test_case(
            db, test_task.id, "Test", None, "Steps", "Result",
            clause_ids=[],
        )
        tc = await update_test_case_status(db, tc.id, "running")
        # running -> blocked
        tc = await update_test_case_status(db, tc.id, "blocked")
        assert tc.status == "blocked"
        # blocked -> running
        tc = await update_test_case_status(db, tc.id, "running")
        assert tc.status == "running"

    async def test_update_test_case_invalid_status(self, db, req_with_seed):
        test_task, _ = await self._setup_test_task_with_clauses(db, req_with_seed)
        tc = await create_test_case(
            db, test_task.id, "Test", None, "Steps", "Result",
            clause_ids=[],
        )
        with pytest.raises(ValueError, match="Invalid test case status"):
            await update_test_case_status(db, tc.id, "invalid_status")

    async def test_update_test_case_same_status(self, db, req_with_seed):
        test_task, _ = await self._setup_test_task_with_clauses(db, req_with_seed)
        tc = await create_test_case(
            db, test_task.id, "Test", None, "Steps", "Result",
            clause_ids=[],
        )
        with pytest.raises(ValueError, match="already in"):
            await update_test_case_status(db, tc.id, "pending")

    async def test_update_test_case_invalid_transition_from_pending(self, db, req_with_seed):
        test_task, _ = await self._setup_test_task_with_clauses(db, req_with_seed)
        tc = await create_test_case(
            db, test_task.id, "Test", None, "Steps", "Result",
            clause_ids=[],
        )
        # Cannot go pending -> passed (must go through running first)
        with pytest.raises(ValueError, match="Invalid test case status transition"):
            await update_test_case_status(db, tc.id, "passed")

    async def test_update_passed_cannot_transition(self, db, req_with_seed):
        test_task, _ = await self._setup_test_task_with_clauses(db, req_with_seed)
        tc = await create_test_case(
            db, test_task.id, "Test", None, "Steps", "Result",
            clause_ids=[],
        )
        tc = await update_test_case_status(db, tc.id, "running")
        tc = await update_test_case_status(db, tc.id, "passed")
        # Passed is a terminal state
        with pytest.raises(ValueError, match="Invalid test case status transition"):
            await update_test_case_status(db, tc.id, "running")

    async def test_create_test_case_nonexistent_task(self, db, req_with_seed):
        with pytest.raises(ValueError, match="not found"):
            await create_test_case(
                db, "nonexistent-id", "Test", None, "Steps", "Result",
                clause_ids=[],
            )
