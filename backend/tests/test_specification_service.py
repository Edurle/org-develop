"""Unit tests for specification service layer.

Tests creating specifications, spec versions, and the
review/lock/reject lifecycle for spec versions.
"""

import pytest
import pytest_asyncio
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.requirement import Requirement
from app.models.specification import Specification, SpecVersion
from app.services.requirement import create_requirement, update_requirement_status
from app.services.specification import (
    create_specification,
    create_spec_version,
    submit_spec_for_review,
    lock_spec,
    reject_spec,
)


@pytest_asyncio.fixture
async def req_with_seed(db: AsyncSession, seed_data):
    """Create a requirement in draft status."""
    req = await create_requirement(
        db,
        iteration_id=seed_data["iteration"].id,
        title="User Login",
        priority="high",
        creator_id=seed_data["user"].id,
    )
    return {**seed_data, "requirement": req}


# ────────────────────────────────────────────────────────────
# Create Specification
# ────────────────────────────────────────────────────────────

class TestSpecificationService:

    async def test_create_specification(self, db, req_with_seed):
        req_id = req_with_seed["requirement"].id
        spec = await create_specification(db, req_id, "api", "Login API Spec")
        assert spec.spec_type == "api"
        assert spec.requirement_id == req_id
        assert spec.title == "Login API Spec"
        assert spec.current_version == 1

        # Verify auto-created first draft version
        result = await db.execute(
            select(SpecVersion).where(SpecVersion.spec_id == spec.id)
        )
        versions = list(result.scalars().all())
        assert len(versions) == 1
        assert versions[0].version == 1
        assert versions[0].status == "draft"
        assert versions[0].content == {}

    async def test_create_spec_invalid_type(self, db, req_with_seed):
        req_id = req_with_seed["requirement"].id
        with pytest.raises(ValueError, match="Invalid spec_type"):
            await create_specification(db, req_id, "invalid", "Spec")

    async def test_create_spec_nonexistent_req(self, db, req_with_seed):
        with pytest.raises(ValueError, match="not found"):
            await create_specification(db, "nonexistent-id", "api", "Spec")

    async def test_create_spec_all_valid_types(self, db, req_with_seed):
        req_id = req_with_seed["requirement"].id
        for spec_type in ("api", "data", "flow", "ui"):
            spec = await create_specification(db, req_id, spec_type, f"{spec_type} Spec")
            assert spec.spec_type == spec_type

    async def test_create_spec_rule_type(self, db, req_with_seed):
        req_id = req_with_seed["requirement"].id
        spec = await create_specification(db, req_id, "rule", "Business Rules Spec")
        assert spec.spec_type == "rule"

    async def test_create_spec_security_type(self, db, req_with_seed):
        req_id = req_with_seed["requirement"].id
        spec = await create_specification(db, req_id, "security", "Security Spec")
        assert spec.spec_type == "security"

    async def test_create_spec_event_type(self, db, req_with_seed):
        req_id = req_with_seed["requirement"].id
        spec = await create_specification(db, req_id, "event", "Event Spec")
        assert spec.spec_type == "event"

    async def test_create_spec_config_type(self, db, req_with_seed):
        req_id = req_with_seed["requirement"].id
        spec = await create_specification(db, req_id, "config", "Config Spec")
        assert spec.spec_type == "config"

    async def test_create_spec_all_eight_types(self, db, req_with_seed):
        req_id = req_with_seed["requirement"].id
        for spec_type in ("api", "data", "flow", "ui", "rule", "security", "event", "config"):
            spec = await create_specification(db, req_id, spec_type, f"{spec_type} Spec")
            assert spec.spec_type == spec_type

    async def test_create_spec_version(self, db, req_with_seed):
        req_id = req_with_seed["requirement"].id
        spec = await create_specification(db, req_id, "api", "API Spec")
        version = await create_spec_version(db, spec.id, {"endpoints": []})
        assert version.spec_id == spec.id
        # v1 is auto-created, so this becomes v2
        assert version.version == 2
        assert version.status == "draft"

        # Create another version (v3)
        v3 = await create_spec_version(db, spec.id, {"more": True})
        assert v3.version == 3
        assert v3.status == "draft"

        # Verify version auto-increment in DB
        result = await db.execute(
            select(func.max(SpecVersion.version)).where(SpecVersion.spec_id == spec.id)
        )
        assert result.scalar_one() == 3

        # Verify spec.current_version was updated
        result = await db.execute(
            select(Specification).where(Specification.id == spec.id)
        )
        updated_spec = result.scalars().first()
        assert updated_spec.current_version == 3

    async def test_create_version_nonexistent_spec(self, db, req_with_seed):
        with pytest.raises(ValueError, match="not found"):
            await create_spec_version(db, "nonexistent-id", {"more": True})

    async def test_submit_for_review(self, db, req_with_seed):
        req_id = req_with_seed["requirement"].id
        uid = req_with_seed["user"].id
        await update_requirement_status(db, req_id, "spec_writing", uid)
        spec = await create_specification(db, req_id, "api", "Login API Spec")
        version = await create_spec_version(db, spec.id, {"endpoints": []})
        reviewing = await submit_spec_for_review(db, version.id)
        assert reviewing.status == "reviewing"

    async def test_submit_for_review_non_draft_fails(self, db, req_with_seed):
        req_id = req_with_seed["requirement"].id
        uid = req_with_seed["user"].id
        await update_requirement_status(db, req_id, "spec_writing", uid)
        spec = await create_specification(db, req_id, "api", "Login API Spec")
        version = await create_spec_version(db, spec.id, {"endpoints": []})
        await submit_spec_for_review(db, version.id)
        # Already reviewing, cannot submit again
        with pytest.raises(ValueError, match="expected 'draft'"):
            await submit_spec_for_review(db, version.id)

    async def test_lock_spec(self, db, req_with_seed):
        req_id = req_with_seed["requirement"].id
        uid = req_with_seed["user"].id
        await update_requirement_status(db, req_id, "spec_writing", uid)
        spec = await create_specification(db, req_id, "api", "Login API Spec")
        version = await create_spec_version(db, spec.id, {"endpoints": []})
        await submit_spec_for_review(db, version.id)
        await update_requirement_status(db, req_id, "spec_review", uid)
        locked = await lock_spec(db, version.id, uid)
        assert locked.status == "locked"
        assert locked.locked_by == uid
        assert locked.locked_at is not None

    async def test_lock_non_reviewing_fails(self, db, req_with_seed):
        req_id = req_with_seed["requirement"].id
        uid = req_with_seed["user"].id
        await update_requirement_status(db, req_id, "spec_writing", uid)
        spec = await create_specification(db, req_id, "api", "Login API Spec")
        version = await create_spec_version(db, spec.id, {"endpoints": []})
        # Still draft, cannot lock
        with pytest.raises(ValueError, match="expected 'reviewing'"):
            await lock_spec(db, version.id, uid)

    async def test_reject_spec(self, db, req_with_seed):
        req_id = req_with_seed["requirement"].id
        uid = req_with_seed["user"].id
        await update_requirement_status(db, req_id, "spec_writing", uid)
        spec = await create_specification(db, req_id, "api", "Login API Spec")
        version = await create_spec_version(db, spec.id, {"endpoints": []})
        await submit_spec_for_review(db, version.id)
        await update_requirement_status(db, req_id, "spec_review", uid)
        rejected = await reject_spec(db, version.id)
        assert rejected.status == "draft"

    async def test_reject_locked_spec_fails(self, db, req_with_seed):
        req_id = req_with_seed["requirement"].id
        uid = req_with_seed["user"].id
        await update_requirement_status(db, req_id, "spec_writing", uid)
        spec = await create_specification(db, req_id, "api", "Login API Spec")
        version = await create_spec_version(db, spec.id, {"endpoints": []})
        await submit_spec_for_review(db, version.id)
        await update_requirement_status(db, req_id, "spec_review", uid)
        await lock_spec(db, version.id, uid)
        # Locked, cannot reject
        with pytest.raises(ValueError, match="expected 'reviewing'"):
            await reject_spec(db, version.id)

    async def test_reject_draft_spec_fails(self, db, req_with_seed):
        req_id = req_with_seed["requirement"].id
        uid = req_with_seed["user"].id
        await update_requirement_status(db, req_id, "spec_writing", uid)
        spec = await create_specification(db, req_id, "api", "Login API Spec")
        version = await create_spec_version(db, spec.id, {"endpoints": []})
        # Still draft, cannot reject
        with pytest.raises(ValueError, match="expected 'reviewing'"):
            await reject_spec(db, version.id)
