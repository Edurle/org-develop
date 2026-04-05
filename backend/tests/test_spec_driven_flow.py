"""End-to-end tests for the spec-driven development flow.

Tests the core enforcement rules:
1. Requirement status gate (spec_locked before dev tasks)
2. Spec version immutability after lock
3. Coverage enforcement (must 100%, should >=80%)
4. Full workflow: requirement -> spec -> lock -> dev task -> test task -> coverage -> done
"""

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.requirement import Requirement
from app.models.specification import Specification, SpecVersion, SpecClause
from app.models.task import DevTask, TestTask
from app.models.testcase import TestCase, ClauseCoverage
from app.services.requirement import create_requirement, update_requirement_status
from app.services.specification import (
    create_specification,
    create_spec_version,
    submit_spec_for_review,
    lock_spec,
    reject_spec,
)
from app.services.clause import create_clause
from app.services.task import (
    create_dev_task,
    claim_dev_task,
    update_task_status,
    create_test_task,
)
from app.services.testcase import create_test_case
from app.services.coverage import get_requirement_coverage, check_coverage_sufficient


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
# 1. Requirement Status Transition Tests
# ────────────────────────────────────────────────────────────

class TestRequirementStatusTransitions:
    async def test_draft_to_spec_writing(self, db, req_with_seed):
        req = req_with_seed["requirement"]
        uid = req_with_seed["user"].id
        updated = await update_requirement_status(db, req.id, "spec_writing", uid)
        assert updated.status == "spec_writing"

    async def test_cannot_skip_to_in_progress(self, db, req_with_seed):
        req = req_with_seed["requirement"]
        uid = req_with_seed["user"].id
        with pytest.raises(ValueError, match="Invalid status transition"):
            await update_requirement_status(db, req.id, "in_progress", uid)

    async def test_cannot_create_dev_task_before_spec_locked(self, db, req_with_seed):
        req = req_with_seed["requirement"]
        uid = req_with_seed["user"].id
        await update_requirement_status(db, req.id, "spec_writing", uid)
        with pytest.raises(ValueError, match="Cannot create dev task"):
            await create_dev_task(
                db, req.id, "fake-version-id", req_with_seed["iteration"].id, "Task 1"
            )

    async def test_full_forward_flow(self, db, req_with_seed):
        req = req_with_seed["requirement"]
        uid = req_with_seed["user"].id
        for status in ["spec_writing", "spec_review", "spec_locked", "in_progress", "testing"]:
            req = await update_requirement_status(db, req.id, status, uid)
            assert req.status == status


# ────────────────────────────────────────────────────────────
# 2. Spec Version Immutability Tests
# ────────────────────────────────────────────────────────────

class TestSpecVersionImmutability:
    async def _setup_locked_spec(self, db, req_with_seed):
        req = req_with_seed["requirement"]
        uid = req_with_seed["user"].id
        await update_requirement_status(db, req.id, "spec_writing", uid)
        spec = await create_specification(db, req.id, "api", "Login API Spec")
        version = await create_spec_version(db, spec.id, {"endpoints": []})
        await create_clause(db, version.id, "API-001", "Create endpoint", "POST /login", "functional", "must")
        await update_requirement_status(db, req.id, "spec_review", uid)
        await submit_spec_for_review(db, version.id)
        await lock_spec(db, version.id, uid)
        return spec, version

    async def test_locked_version_rejects_new_clauses(self, db, req_with_seed):
        spec, version = await self._setup_locked_spec(db, req_with_seed)
        with pytest.raises(ValueError, match="Cannot add clauses to a locked"):
            await create_clause(db, version.id, "API-002", "New", "Desc", "functional", "must")

    async def test_can_create_new_version(self, db, req_with_seed):
        spec, version = await self._setup_locked_spec(db, req_with_seed)
        v2 = await create_spec_version(db, spec.id, {"endpoints": [{"path": "/v2"}]})
        assert v2.version == 2
        assert v2.status == "draft"

    async def test_locked_version_status_is_immutable(self, db, req_with_seed):
        spec, version = await self._setup_locked_spec(db, req_with_seed)
        with pytest.raises(ValueError, match="expected 'draft'"):
            await submit_spec_for_review(db, version.id)
        with pytest.raises(ValueError, match="expected 'reviewing'"):
            await lock_spec(db, version.id, req_with_seed["user"].id)


# ────────────────────────────────────────────────────────────
# 3. Coverage Enforcement Tests
# ────────────────────────────────────────────────────────────

class TestCoverageEnforcement:
    async def _setup_with_clauses(self, db, req_with_seed, clauses):
        req = req_with_seed["requirement"]
        uid = req_with_seed["user"].id
        await update_requirement_status(db, req.id, "spec_writing", uid)
        spec = await create_specification(db, req.id, "api", "Test Spec")
        version = await create_spec_version(db, spec.id, {})
        clause_objs = []
        for c in clauses:
            cl = await create_clause(
                db, version.id, c["clause_id"], c["title"],
                c["description"], c["category"], c["severity"],
            )
            clause_objs.append(cl)
        await update_requirement_status(db, req.id, "spec_review", uid)
        await submit_spec_for_review(db, version.id)
        await lock_spec(db, version.id, uid)
        return spec, version, clause_objs

    async def test_coverage_zero_when_no_test_cases(self, db, req_with_seed):
        await self._setup_with_clauses(
            db, req_with_seed,
            [{"clause_id": "F-001", "title": "A", "description": "d", "category": "functional", "severity": "must"}],
        )
        coverage = await get_requirement_coverage(db, req_with_seed["requirement"].id)
        assert coverage["must_coverage_pct"] == 0.0
        assert coverage["covered_clauses"] == 0

    async def test_coverage_insufficient_blocks_done(self, db, req_with_seed):
        await self._setup_with_clauses(
            db, req_with_seed,
            [{"clause_id": "F-001", "title": "A", "description": "d", "category": "functional", "severity": "must"}],
        )
        req = req_with_seed["requirement"]
        uid = req_with_seed["user"].id
        # _setup_with_clauses auto-transitioned to spec_locked
        result = await db.execute(select(Requirement).where(Requirement.id == req.id))
        fresh_req = result.scalars().first()
        assert fresh_req.status == "spec_locked"

        await update_requirement_status(db, req.id, "in_progress", uid)
        await update_requirement_status(db, req.id, "testing", uid)
        with pytest.raises(ValueError, match="test coverage insufficient"):
            await update_requirement_status(db, req.id, "done", uid)

    async def test_must_100_percent_enforcement(self, db, req_with_seed):
        _, _, clauses = await self._setup_with_clauses(
            db, req_with_seed,
            [
                {"clause_id": "F-001", "title": "A", "description": "d", "category": "functional", "severity": "must"},
                {"clause_id": "F-002", "title": "B", "description": "d", "category": "functional", "severity": "must"},
            ],
        )
        req = req_with_seed["requirement"]
        iter_id = req_with_seed["iteration"].id
        test_task = await create_test_task(db, req.id, iter_id, "Test")
        await create_test_case(
            db, test_task.id, "Test A", None, "Step 1", "Result 1",
            clause_ids=[clauses[0].id],
        )
        sufficient = await check_coverage_sufficient(db, req.id)
        assert sufficient is False  # 50% must

    async def test_should_80_percent_enforcement(self, db, req_with_seed):
        _, _, clauses = await self._setup_with_clauses(
            db, req_with_seed,
            [
                {"clause_id": "S-001", "title": "S1", "description": "d", "category": "performance", "severity": "should"},
                {"clause_id": "S-002", "title": "S2", "description": "d", "category": "performance", "severity": "should"},
            ],
        )
        req = req_with_seed["requirement"]
        iter_id = req_with_seed["iteration"].id
        test_task = await create_test_task(db, req.id, iter_id, "Test")
        await create_test_case(
            db, test_task.id, "Test S1", None, "Step", "Result",
            clause_ids=[clauses[0].id],
        )
        sufficient = await check_coverage_sufficient(db, req.id)
        assert sufficient is False  # 50% < 80%

    async def test_may_not_enforced(self, db, req_with_seed):
        _, _, clauses = await self._setup_with_clauses(
            db, req_with_seed,
            [
                {"clause_id": "F-001", "title": "Must A", "description": "d", "category": "functional", "severity": "must"},
                {"clause_id": "M-001", "title": "May A", "description": "d", "category": "functional", "severity": "may"},
            ],
        )
        req = req_with_seed["requirement"]
        iter_id = req_with_seed["iteration"].id
        test_task = await create_test_task(db, req.id, iter_id, "Test")
        await create_test_case(
            db, test_task.id, "Test Must", None, "Step", "Result",
            clause_ids=[clauses[0].id],
        )
        sufficient = await check_coverage_sufficient(db, req.id)
        assert sufficient is True  # must=100%, may not enforced

    async def test_full_coverage_allows_done(self, db, req_with_seed):
        _, _, clauses = await self._setup_with_clauses(
            db, req_with_seed,
            [
                {"clause_id": "F-001", "title": "Must A", "description": "d", "category": "functional", "severity": "must"},
                {"clause_id": "S-001", "title": "Should A", "description": "d", "category": "performance", "severity": "should"},
            ],
        )
        req = req_with_seed["requirement"]
        uid = req_with_seed["user"].id
        iter_id = req_with_seed["iteration"].id

        test_task = await create_test_task(db, req.id, iter_id, "Test All")
        await create_test_case(
            db, test_task.id, "Test All", None, "Steps", "Results",
            clause_ids=[c.id for c in clauses],
        )
        await update_requirement_status(db, req.id, "in_progress", uid)
        await update_requirement_status(db, req.id, "testing", uid)
        done_req = await update_requirement_status(db, req.id, "done", uid)
        assert done_req.status == "done"


# ────────────────────────────────────────────────────────────
# 4. End-to-End Complete Flow
# ────────────────────────────────────────────────────────────

class TestEndToEndFlow:
    async def test_complete_spec_driven_flow(self, db, req_with_seed):
        req = req_with_seed["requirement"]
        uid = req_with_seed["user"].id
        iter_id = req_with_seed["iteration"].id

        # Step 1-2: spec_writing
        assert req.status == "draft"
        await update_requirement_status(db, req.id, "spec_writing", uid)

        # Step 3: Create 4 specs
        specs = {}
        for stype in ("api", "data", "flow", "ui"):
            specs[stype] = await create_specification(db, req.id, stype, f"Login {stype}")

        # Step 4: Create versions with clauses
        api_ver = await create_spec_version(db, specs["api"].id, {"endpoints": []})
        await create_clause(db, api_ver.id, "API-001", "Login endpoint", "POST /login", "functional", "must")

        data_ver = await create_spec_version(db, specs["data"].id, {"tables": []})
        await create_clause(db, data_ver.id, "DATA-001", "User table", "Schema", "functional", "must")

        flow_ver = await create_spec_version(db, specs["flow"].id, {"flows": []})
        await create_clause(db, flow_ver.id, "FLOW-001", "Login flow", "Transitions", "functional", "should")

        ui_ver = await create_spec_version(db, specs["ui"].id, {
            "views": [{"route": "/login", "elements": [
                {"role": "interactive", "description": "Login btn", "locator": {"type": "data-testid", "value": "login-submit-btn"}}
            ]}]
        })
        await create_clause(db, ui_ver.id, "UI-001", "Login button", "Exists", "ui_element", "must")

        # Step 5: Review and lock all
        await update_requirement_status(db, req.id, "spec_review", uid)
        for ver in [api_ver, data_ver, flow_ver, ui_ver]:
            await submit_spec_for_review(db, ver.id)
            await lock_spec(db, ver.id, uid)

        # Step 6: Auto-transitioned to spec_locked
        result = await db.execute(select(Requirement).where(Requirement.id == req.id))
        assert result.scalars().first().status == "spec_locked"

        # Step 7: Dev task
        dev_task = await create_dev_task(db, req.id, api_ver.id, iter_id, "Impl login", estimate_hours=4.0)
        assert dev_task.status == "open"

        # Step 8: Complete dev task
        dev_task = await claim_dev_task(db, dev_task.id, uid)
        dev_task = await update_task_status(db, dev_task.id, "review")
        dev_task = await update_task_status(db, dev_task.id, "done")

        # Step 9: Test task covering all clauses
        test_task = await create_test_task(db, req.id, iter_id, "Test Login")
        all_clauses = (await db.execute(select(SpecClause))).scalars().all()
        await create_test_case(
            db, test_task.id, "Verify login", "User exists",
            "1. POST /login\n2. Check response", "200 OK",
            clause_ids=[c.id for c in all_clauses],
        )

        # Step 10: Done
        await update_requirement_status(db, req.id, "in_progress", uid)
        await update_requirement_status(db, req.id, "testing", uid)

        coverage = await get_requirement_coverage(db, req.id)
        assert coverage["must_coverage_pct"] == 100.0

        done = await update_requirement_status(db, req.id, "done", uid)
        assert done.status == "done"


# ────────────────────────────────────────────────────────────
# 5. Dev Task Gate
# ────────────────────────────────────────────────────────────

class TestDevTaskGate:
    async def test_dev_task_requires_locked_version(self, db, req_with_seed):
        req = req_with_seed["requirement"]
        uid = req_with_seed["user"].id
        iter_id = req_with_seed["iteration"].id

        await update_requirement_status(db, req.id, "spec_writing", uid)
        spec = await create_specification(db, req.id, "api", "Spec")
        version = await create_spec_version(db, spec.id, {})
        await update_requirement_status(db, req.id, "spec_review", uid)
        await submit_spec_for_review(db, version.id)
        # version is reviewing, not locked

        with pytest.raises(ValueError, match="Cannot create dev task"):
            await create_dev_task(db, req.id, version.id, iter_id, "Task")

    async def test_dev_task_works_with_locked(self, db, req_with_seed):
        req = req_with_seed["requirement"]
        uid = req_with_seed["user"].id
        iter_id = req_with_seed["iteration"].id

        await update_requirement_status(db, req.id, "spec_writing", uid)
        spec = await create_specification(db, req.id, "api", "Spec")
        version = await create_spec_version(db, spec.id, {})
        await update_requirement_status(db, req.id, "spec_review", uid)
        await submit_spec_for_review(db, version.id)
        await lock_spec(db, version.id, uid)

        task = await create_dev_task(db, req.id, version.id, iter_id, "Implement")
        assert task.status == "open"


# ────────────────────────────────────────────────────────────
# 6. Test Case Clause Link
# ────────────────────────────────────────────────────────────

class TestTestCaseClauseLink:
    async def test_create_with_valid_clauses(self, db, req_with_seed):
        req = req_with_seed["requirement"]
        uid = req_with_seed["user"].id
        iter_id = req_with_seed["iteration"].id

        await update_requirement_status(db, req.id, "spec_writing", uid)
        spec = await create_specification(db, req.id, "api", "Spec")
        ver = await create_spec_version(db, spec.id, {})
        clause = await create_clause(db, ver.id, "T-001", "Test", "Desc", "functional", "must")

        test_task = await create_test_task(db, req.id, iter_id, "Test Task")
        tc = await create_test_case(
            db, test_task.id, "TC1", None, "Steps", "Expected",
            clause_ids=[clause.id],
        )
        assert tc.status == "pending"

        result = await db.execute(
            select(ClauseCoverage).where(ClauseCoverage.test_case_id == tc.id)
        )
        coverages = list(result.scalars().all())
        assert len(coverages) == 1
        assert coverages[0].clause_id == clause.id

    async def test_create_with_invalid_clause_fails(self, db, req_with_seed):
        req = req_with_seed["requirement"]
        iter_id = req_with_seed["iteration"].id
        test_task = await create_test_task(db, req.id, iter_id, "Test Task")
        with pytest.raises(ValueError, match="clause IDs do not exist"):
            await create_test_case(
                db, test_task.id, "TC1", None, "Steps", "Expected",
                clause_ids=["nonexistent-id"],
            )
