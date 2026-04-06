"""Comprehensive tests for edit and delete service methods.

Covers: requirement update/delete, clause update/delete,
dev task update/delete, and test case update/delete.
"""

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.requirement import Requirement
from app.models.specification import SpecClause
from app.models.task import DevTask
from app.models.testcase import TestCase
from app.services.requirement import (
    create_requirement,
    update_requirement,
    delete_requirement,
    update_requirement_status,
)
from app.services.specification import (
    create_specification,
    create_spec_version,
    submit_spec_for_review,
    lock_spec,
)
from app.services.clause import (
    create_clause,
    update_clause,
    delete_clause,
)
from app.services.task import (
    create_dev_task,
    update_dev_task,
    delete_dev_task,
    create_test_task,
    claim_dev_task,
)
from app.services.testcase import (
    create_test_case,
    update_test_case,
    delete_test_case,
    update_test_case_status,
)


@pytest_asyncio.fixture
async def req_with_seed(db: AsyncSession, seed_data):
    """Create a requirement in draft status."""
    req = await create_requirement(
        db,
        iteration_id=seed_data["iteration"].id,
        title="Edit Test Req",
        priority="medium",
        creator_id=seed_data["user"].id,
    )
    return {**seed_data, "requirement": req}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _setup_locked_spec(db, req_with_seed):
    """Walk requirement through to spec_locked with a locked spec version."""
    req_id = req_with_seed["requirement"].id
    uid = req_with_seed["user"].id

    await update_requirement_status(db, req_id, "spec_writing", uid)
    spec = await create_specification(db, req_id, "api", "Login API Spec")
    version = await create_spec_version(db, spec.id, {"endpoints": []})
    await update_requirement_status(db, req_id, "spec_review", uid)
    await submit_spec_for_review(db, version.id)
    await lock_spec(db, version.id, uid)
    return version


async def _setup_clause_on_draft_version(db, req_with_seed):
    """Create a requirement -> spec -> draft version -> clause."""
    req_id = req_with_seed["requirement"].id
    uid = req_with_seed["user"].id

    await update_requirement_status(db, req_id, "spec_writing", uid)
    spec = await create_specification(db, req_id, "api", "Clause Edit Spec")
    version = await create_spec_version(db, spec.id, {"endpoints": []})
    clause = await create_clause(
        db, version.id, "FN-001", "Original Clause",
        "A functional clause", "functional", "must",
    )
    return version, clause


async def _setup_test_task_with_clauses(db, req_with_seed):
    """Create a requirement with spec, clause, and test task."""
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


# ===================================================================
# TestRequirementEdit
# ===================================================================

class TestRequirementEdit:

    async def test_update_title(self, db, req_with_seed):
        req = req_with_seed["requirement"]
        uid = req_with_seed["user"].id
        updated = await update_requirement(db, req.id, uid, title="New Title")
        assert updated.title == "New Title"
        assert updated.priority == "medium"  # unchanged

    async def test_update_priority(self, db, req_with_seed):
        req = req_with_seed["requirement"]
        uid = req_with_seed["user"].id
        updated = await update_requirement(db, req.id, uid, priority="high")
        assert updated.priority == "high"
        assert updated.title == "Edit Test Req"  # unchanged

    async def test_update_both_fields(self, db, req_with_seed):
        req = req_with_seed["requirement"]
        uid = req_with_seed["user"].id
        updated = await update_requirement(
            db, req.id, uid, title="Brand New Title", priority="critical",
        )
        assert updated.title == "Brand New Title"
        assert updated.priority == "critical"

    async def test_update_invalid_priority(self, db, req_with_seed):
        req = req_with_seed["requirement"]
        uid = req_with_seed["user"].id
        with pytest.raises(ValueError, match="Invalid priority"):
            await update_requirement(db, req.id, uid, priority="urgent")

    async def test_update_nonexistent(self, db, req_with_seed):
        uid = req_with_seed["user"].id
        with pytest.raises(ValueError, match="not found"):
            await update_requirement(db, "nonexistent-id", uid, title="X")

    async def test_delete_draft(self, db, req_with_seed):
        req = req_with_seed["requirement"]
        uid = req_with_seed["user"].id
        assert req.status == "draft"
        await delete_requirement(db, req.id, uid)
        # Verify it's gone
        result = await db.execute(
            select(Requirement).where(Requirement.id == req.id)
        )
        assert result.scalars().first() is None

    async def test_delete_non_draft_rejected(self, db, req_with_seed):
        req = req_with_seed["requirement"]
        uid = req_with_seed["user"].id
        # Move out of draft
        await update_requirement_status(db, req.id, "spec_writing", uid)
        with pytest.raises(ValueError, match="Cannot delete requirement"):
            await delete_requirement(db, req.id, uid)

    async def test_delete_cancelled(self, db, req_with_seed):
        req = req_with_seed["requirement"]
        uid = req_with_seed["user"].id
        # Move to spec_locked (lock_spec auto-transitions requirement), then cancel
        await update_requirement_status(db, req.id, "spec_writing", uid)
        spec = await create_specification(db, req.id, "api", "Spec")
        version = await create_spec_version(db, spec.id, {"endpoints": []})
        await update_requirement_status(db, req.id, "spec_review", uid)
        await submit_spec_for_review(db, version.id)
        await lock_spec(db, version.id, uid)  # auto-transitions req to spec_locked
        # Now cancel
        await update_requirement_status(db, req.id, "cancelled", uid)
        # Delete should succeed
        await delete_requirement(db, req.id, uid)
        result = await db.execute(
            select(Requirement).where(Requirement.id == req.id)
        )
        assert result.scalars().first() is None


# ===================================================================
# TestClauseEdit
# ===================================================================

class TestClauseEdit:

    async def test_update_clause_title(self, db, req_with_seed):
        _version, clause = await _setup_clause_on_draft_version(db, req_with_seed)
        updated = await update_clause(db, clause.id, title="Updated Title")
        assert updated.title == "Updated Title"
        assert updated.category == "functional"  # unchanged
        assert updated.severity == "must"  # unchanged

    async def test_update_clause_severity(self, db, req_with_seed):
        _version, clause = await _setup_clause_on_draft_version(db, req_with_seed)
        updated = await update_clause(db, clause.id, severity="should")
        assert updated.severity == "should"
        assert updated.title == "Original Clause"  # unchanged

    async def test_update_clause_all_fields(self, db, req_with_seed):
        _version, clause = await _setup_clause_on_draft_version(db, req_with_seed)
        updated = await update_clause(
            db, clause.id,
            clause_id_str="VD-001",
            title="All Fields Updated",
            description="New description",
            category="validation",
            severity="may",
        )
        assert updated.clause_id == "VD-001"
        assert updated.title == "All Fields Updated"
        assert updated.description == "New description"
        assert updated.category == "validation"
        assert updated.severity == "may"

    async def test_update_clause_locked_version_rejected(self, db, req_with_seed):
        version, clause = await _setup_clause_on_draft_version(db, req_with_seed)
        uid = req_with_seed["user"].id
        # Lock the version
        await update_requirement_status(
            db, req_with_seed["requirement"].id, "spec_review", uid,
        )
        await submit_spec_for_review(db, version.id)
        await lock_spec(db, version.id, uid)
        with pytest.raises(ValueError, match="non-draft"):
            await update_clause(db, clause.id, title="Should Fail")

    async def test_delete_clause_draft(self, db, req_with_seed):
        _version, clause = await _setup_clause_on_draft_version(db, req_with_seed)
        await delete_clause(db, clause.id)
        # Verify it's gone
        result = await db.execute(
            select(SpecClause).where(SpecClause.id == clause.id)
        )
        assert result.scalars().first() is None

    async def test_delete_clause_locked_version_rejected(self, db, req_with_seed):
        version, clause = await _setup_clause_on_draft_version(db, req_with_seed)
        uid = req_with_seed["user"].id
        # Lock the version
        await update_requirement_status(
            db, req_with_seed["requirement"].id, "spec_review", uid,
        )
        await submit_spec_for_review(db, version.id)
        await lock_spec(db, version.id, uid)
        with pytest.raises(ValueError, match="non-draft"):
            await delete_clause(db, clause.id)


# ===================================================================
# TestDevTaskEdit
# ===================================================================

class TestDevTaskEdit:

    async def test_update_dev_task_title(self, db, req_with_seed):
        version = await _setup_locked_spec(db, req_with_seed)
        task = await create_dev_task(
            db, req_with_seed["requirement"].id, version.id,
            req_with_seed["iteration"].id, "Original Task", 4.0,
        )
        updated = await update_dev_task(db, task.id, title="New Task Title")
        assert updated.title == "New Task Title"
        assert updated.estimate_hours == 4.0  # unchanged

    async def test_update_dev_task_estimate(self, db, req_with_seed):
        version = await _setup_locked_spec(db, req_with_seed)
        task = await create_dev_task(
            db, req_with_seed["requirement"].id, version.id,
            req_with_seed["iteration"].id, "Task", 2.0,
        )
        updated = await update_dev_task(db, task.id, estimate_hours=8.0)
        assert updated.estimate_hours == 8.0
        assert updated.title == "Task"  # unchanged

    async def test_delete_open_task(self, db, req_with_seed):
        version = await _setup_locked_spec(db, req_with_seed)
        task = await create_dev_task(
            db, req_with_seed["requirement"].id, version.id,
            req_with_seed["iteration"].id, "To Delete",
        )
        assert task.status == "open"
        await delete_dev_task(db, task.id)
        # Verify it's gone
        result = await db.execute(
            select(DevTask).where(DevTask.id == task.id)
        )
        assert result.scalars().first() is None

    async def test_delete_non_open_task_rejected(self, db, req_with_seed):
        version = await _setup_locked_spec(db, req_with_seed)
        uid = req_with_seed["user"].id
        task = await create_dev_task(
            db, req_with_seed["requirement"].id, version.id,
            req_with_seed["iteration"].id, "Claimed Task",
        )
        # Claim the task to move it out of 'open'
        await claim_dev_task(db, task.id, uid)
        assert task.status == "in_progress"
        with pytest.raises(ValueError, match="Cannot delete task"):
            await delete_dev_task(db, task.id)


# ===================================================================
# TestTestCaseEdit
# ===================================================================

class TestTestCaseEdit:

    async def test_update_test_case_title(self, db, req_with_seed):
        test_task, _clause = await _setup_test_task_with_clauses(db, req_with_seed)
        tc = await create_test_case(
            db, test_task.id, "Original Title", "Pre", "Steps", "Expected",
            clause_ids=[],
        )
        updated = await update_test_case(db, tc.id, title="Updated Title")
        assert updated.title == "Updated Title"
        assert updated.preconditions == "Pre"  # unchanged

    async def test_update_test_case_fields(self, db, req_with_seed):
        test_task, _clause = await _setup_test_task_with_clauses(db, req_with_seed)
        tc = await create_test_case(
            db, test_task.id, "TC", "Pre", "Steps", "Expected",
            clause_ids=[],
        )
        updated = await update_test_case(
            db, tc.id,
            preconditions="New Pre",
            steps="New Steps",
            expected_result="New Expected",
            actual_result="New Actual",
        )
        assert updated.preconditions == "New Pre"
        assert updated.steps == "New Steps"
        assert updated.expected_result == "New Expected"
        assert updated.actual_result == "New Actual"
        assert updated.title == "TC"  # unchanged

    async def test_delete_pending_test_case(self, db, req_with_seed):
        test_task, _clause = await _setup_test_task_with_clauses(db, req_with_seed)
        tc = await create_test_case(
            db, test_task.id, "To Delete", None, "Steps", "Result",
            clause_ids=[],
        )
        assert tc.status == "pending"
        await delete_test_case(db, tc.id)
        # Verify it's gone
        result = await db.execute(
            select(TestCase).where(TestCase.id == tc.id)
        )
        assert result.scalars().first() is None

    async def test_delete_non_pending_test_case_rejected(self, db, req_with_seed):
        test_task, _clause = await _setup_test_task_with_clauses(db, req_with_seed)
        tc = await create_test_case(
            db, test_task.id, "Running TC", None, "Steps", "Result",
            clause_ids=[],
        )
        # Move to running so it's no longer pending
        await update_test_case_status(db, tc.id, "running")
        with pytest.raises(ValueError, match="Cannot delete test case"):
            await delete_test_case(db, tc.id)
