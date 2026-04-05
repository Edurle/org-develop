"""Unit tests for clause service layer.

Tests creating clauses with valid/invalid categories and severities,
listing clauses, and locked-version protection.
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
from app.services.clause import create_clause, list_clauses


@pytest_asyncio.fixture
async def req_with_seed(db: AsyncSession, seed_data):
    """Create a requirement in draft status."""
    req = await create_requirement(
        db,
        iteration_id=seed_data["iteration"].id,
        title="Clause Test Req",
        priority="medium",
        creator_id=seed_data["user"].id,
    )
    return {**seed_data, "requirement": req}


class TestClauseService:

    async def test_create_clause(self, db, req_with_seed):
        req_id = req_with_seed["requirement"].id
        uid = req_with_seed["user"].id
        await update_requirement_status(db, req_id, "spec_writing", uid)
        spec = await create_specification(db, req_id, "api", "Login API Spec")
        version = await create_spec_version(db, spec.id, {"endpoints": []})
        clause = await create_clause(
            db, version.id, "FN-001", "Test Clause", "A test functional clause",
            "functional", "must",
        )
        assert clause is not None
        assert clause.clause_id == "FN-001"
        assert clause.title == "Test Clause"
        assert clause.category == "functional"
        assert clause.severity == "must"
        assert clause.spec_version_id == version.id

    async def test_create_clause_invalid_category(self, db, req_with_seed):
        req_id = req_with_seed["requirement"].id
        uid = req_with_seed["user"].id
        await update_requirement_status(db, req_id, "spec_writing", uid)
        spec = await create_specification(db, req_id, "api", "Spec")
        version = await create_spec_version(db, spec.id, {"endpoints": []})
        with pytest.raises(ValueError, match="Invalid category"):
            await create_clause(
                db, version.id, "FN-002", "Bad Cat", "Invalid category",
                "invalid_category", "must",
            )

    async def test_create_clause_invalid_severity(self, db, req_with_seed):
        req_id = req_with_seed["requirement"].id
        uid = req_with_seed["user"].id
        await update_requirement_status(db, req_id, "spec_writing", uid)
        spec = await create_specification(db, req_id, "api", "Spec")
        version = await create_spec_version(db, spec.id, {"endpoints": []})
        with pytest.raises(ValueError, match="Invalid severity"):
            await create_clause(
                db, version.id, "FN-003", "Bad Sev", "Invalid severity",
                "functional", "invalid_severity",
            )

    async def test_create_clause_locked_version_rejected(self, db, req_with_seed):
        """Cannot add clauses to a locked version."""
        req_id = req_with_seed["requirement"].id
        uid = req_with_seed["user"].id
        await update_requirement_status(db, req_id, "spec_writing", uid)
        spec = await create_specification(db, req_id, "api", "Spec")
        version = await create_spec_version(db, spec.id, {"endpoints": []})
        await update_requirement_status(db, req_id, "spec_review", uid)
        await submit_spec_for_review(db, version.id)
        await lock_spec(db, version.id, uid)
        with pytest.raises(ValueError, match="Cannot add clauses to a locked"):
            await create_clause(
                db, version.id, "FN-010", "Locked Clause", "Should fail",
                "functional", "must",
            )

    async def test_list_clauses(self, db, req_with_seed):
        req_id = req_with_seed["requirement"].id
        uid = req_with_seed["user"].id
        await update_requirement_status(db, req_id, "spec_writing", uid)
        spec = await create_specification(db, req_id, "api", "Spec")
        version = await create_spec_version(db, spec.id, {"endpoints": []})
        await create_clause(
            db, version.id, "FN-001", "Clause A", "Desc A", "functional", "must",
        )
        await create_clause(
            db, version.id, "VD-001", "Clause B", "Desc B", "validation", "should",
        )
        await create_clause(
            db, version.id, "SC-001", "Clause C", "Desc C", "security", "may",
        )
        clauses = await list_clauses(db, version.id)
        assert len(clauses) == 3
        # Ordered by clause_id
        assert clauses[0].clause_id == "FN-001"
        assert clauses[1].clause_id == "SC-001"
        assert clauses[2].clause_id == "VD-001"

    async def test_list_clauses_empty(self, db, req_with_seed):
        req_id = req_with_seed["requirement"].id
        uid = req_with_seed["user"].id
        await update_requirement_status(db, req_id, "spec_writing", uid)
        spec = await create_specification(db, req_id, "api", "Spec")
        version = await create_spec_version(db, spec.id, {})
        clauses = await list_clauses(db, version.id)
        assert len(clauses) == 0

    async def test_create_clause_nonexistent_version(self, db, req_with_seed):
        with pytest.raises(ValueError, match="not found"):
            await create_clause(
                db, "nonexistent-id", "FN-001", "Title", "Desc",
                "functional", "must",
            )

    async def test_create_clause_all_valid_categories(self, db, req_with_seed):
        req_id = req_with_seed["requirement"].id
        uid = req_with_seed["user"].id
        await update_requirement_status(db, req_id, "spec_writing", uid)
        spec = await create_specification(db, req_id, "api", "Spec")
        version = await create_spec_version(db, spec.id, {})
        categories = ["functional", "validation", "security", "performance", "ui_element"]
        for i, cat in enumerate(categories):
            clause = await create_clause(
                db, version.id, f"CL-{i:03d}", f"Clause {cat}", f"Desc {cat}",
                cat, "must",
            )
            assert clause.category == cat

    async def test_create_clause_all_valid_severities(self, db, req_with_seed):
        req_id = req_with_seed["requirement"].id
        uid = req_with_seed["user"].id
        await update_requirement_status(db, req_id, "spec_writing", uid)
        spec = await create_specification(db, req_id, "api", "Spec")
        version = await create_spec_version(db, spec.id, {})
        for i, sev in enumerate(["must", "should", "may"]):
            clause = await create_clause(
                db, version.id, f"SV-{i:03d}", f"Clause {sev}", f"Desc {sev}",
                "functional", sev,
            )
            assert clause.severity == sev
