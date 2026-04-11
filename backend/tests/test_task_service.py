"""Unit tests for task service layer.

Tests creating dev tasks, test tasks, claiming tasks, status transitions,
and requirement/spec-version gates for dev task creation.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.requirement import create_requirement, update_requirement_status
from app.services.specification import (
    create_specification,
    create_spec_version,
    submit_spec_for_review,
    lock_spec,
)
from app.services.task import (
    create_dev_task,
    claim_dev_task,
    update_task_status,
    create_test_task,
)


@pytest_asyncio.fixture
async def req_with_seed(db: AsyncSession, seed_data):
    """Create a requirement in draft status."""
    req = await create_requirement(
        db,
        iteration_id=seed_data["iteration"].id,
        title="Task Test Req",
        priority="high",
        creator_id=seed_data["user"].id,
    )
    return {**seed_data, "requirement": req}


class TestDevTaskService:

    async def _setup_locked_spec(self, db, req_with_seed):
        """Helper: set up requirement -> spec -> locked version for dev task creation."""
        req_id = req_with_seed["requirement"].id
        uid = req_with_seed["user"].id

        await update_requirement_status(db, req_id, "spec_writing", uid)
        spec = await create_specification(db, req_id, "api", "Login API Spec")
        version = await create_spec_version(db, spec.id, {"endpoints": []})
        await submit_spec_for_review(db, version.id)
        await update_requirement_status(db, req_id, "spec_review", uid)
        await lock_spec(db, version.id, uid)
        return version

    async def test_create_dev_task(self, db, req_with_seed):
        version = await self._setup_locked_spec(db, req_with_seed)
        task = await create_dev_task(
            db, req_with_seed["requirement"].id, version.id,
            req_with_seed["iteration"].id, "Impl Login", 4.0,
        )
        assert task.status == "open"
        assert task.spec_version_id == version.id
        assert task.estimate_hours == 4.0
        assert task.title == "Impl Login"

    async def test_create_dev_task_not_locked(self, db, req_with_seed):
        req_id = req_with_seed["requirement"].id
        uid = req_with_seed["user"].id
        await update_requirement_status(db, req_id, "spec_writing", uid)
        spec = await create_specification(db, req_id, "api", "Login API Spec")
        version = await create_spec_version(db, spec.id, {"endpoints": []})
        await submit_spec_for_review(db, version.id)
        await update_requirement_status(db, req_id, "spec_review", uid)
        # Version is reviewing, not locked
        with pytest.raises(ValueError, match="Cannot create dev task"):
            await create_dev_task(
                db, req_id, version.id, req_with_seed["iteration"].id, "Task",
            )

    async def test_claim_dev_task(self, db, req_with_seed):
        version = await self._setup_locked_spec(db, req_with_seed)
        uid = req_with_seed["user"].id
        task = await create_dev_task(
            db, req_with_seed["requirement"].id, version.id,
            req_with_seed["iteration"].id, "Task",
        )
        assert task.status == "open"
        claimed = await claim_dev_task(db, task.id, uid)
        assert claimed.status == "in_progress"
        assert claimed.assignee_id == uid

    async def test_claim_dev_task_not_open(self, db, req_with_seed):
        version = await self._setup_locked_spec(db, req_with_seed)
        uid = req_with_seed["user"].id
        task = await create_dev_task(
            db, req_with_seed["requirement"].id, version.id,
            req_with_seed["iteration"].id, "Task",
        )
        await claim_dev_task(db, task.id, uid)
        # Already in_progress, cannot claim again
        with pytest.raises(ValueError, match="Cannot claim"):
            await claim_dev_task(db, task.id, uid)

    async def test_update_task_status_transitions(self, db, req_with_seed):
        version = await self._setup_locked_spec(db, req_with_seed)
        uid = req_with_seed["user"].id
        task = await create_dev_task(
            db, req_with_seed["requirement"].id, version.id,
            req_with_seed["iteration"].id, "Task",
        )
        await claim_dev_task(db, task.id, uid)
        assert task.status == "in_progress"

        # in_progress -> review
        task = await update_task_status(db, task.id, "review")
        assert task.status == "review"

        # review -> done
        task = await update_task_status(db, task.id, "done")
        assert task.status == "done"

    async def test_update_task_status_blocked_and_back(self, db, req_with_seed):
        version = await self._setup_locked_spec(db, req_with_seed)
        uid = req_with_seed["user"].id
        task = await create_dev_task(
            db, req_with_seed["requirement"].id, version.id,
            req_with_seed["iteration"].id, "Task",
        )
        await claim_dev_task(db, task.id, uid)
        # in_progress -> blocked
        task = await update_task_status(db, task.id, "blocked")
        assert task.status == "blocked"
        # blocked -> in_progress
        task = await update_task_status(db, task.id, "in_progress")
        assert task.status == "in_progress"

    async def test_update_task_status_invalid_transition(self, db, req_with_seed):
        version = await self._setup_locked_spec(db, req_with_seed)
        task = await create_dev_task(
            db, req_with_seed["requirement"].id, version.id,
            req_with_seed["iteration"].id, "Task",
        )
        # open cannot go directly to done
        with pytest.raises(ValueError, match="Invalid task status transition"):
            await update_task_status(db, task.id, "done")

    async def test_update_task_status_same_status(self, db, req_with_seed):
        version = await self._setup_locked_spec(db, req_with_seed)
        task = await create_dev_task(
            db, req_with_seed["requirement"].id, version.id,
            req_with_seed["iteration"].id, "Task",
        )
        with pytest.raises(ValueError, match="already in"):
            await update_task_status(db, task.id, "open")

    async def test_create_test_task(self, db, req_with_seed):
        req_id = req_with_seed["requirement"].id
        iter_id = req_with_seed["iteration"].id
        task = await create_test_task(db, req_id, iter_id, "Test Login")
        assert task.status == "open"
        assert task.title == "Test Login"
        assert task.requirement_id == req_id
        assert task.iteration_id == iter_id

    async def test_create_test_task_nonexistent_req(self, db, req_with_seed):
        with pytest.raises(ValueError, match="not found"):
            await create_test_task(
                db, "nonexistent-id", req_with_seed["iteration"].id, "Test",
            )

    async def test_create_dev_task_nonexistent_req(self, db, req_with_seed):
        version = await self._setup_locked_spec(db, req_with_seed)
        with pytest.raises(ValueError, match="not found"):
            await create_dev_task(
                db, "nonexistent-id", version.id,
                req_with_seed["iteration"].id, "Task",
            )
