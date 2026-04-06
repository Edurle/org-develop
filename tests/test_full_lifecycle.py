"""
End-to-end tests for the full requirement lifecycle.

Covers:
1. Happy path: register through done with full spec-driven workflow
2. Spec rejection: submit -> reject -> resubmit -> lock
3. Insufficient coverage blocks done
4. Cancelled requirement
5. Full lifecycle via UI (Playwright)

Run:  pytest tests/test_full_lifecycle.py -v -s
      (requires backend on localhost:8000, frontend on localhost:3000 for UI test)
"""

import pytest

from helpers.api import ApiHelper
from helpers.ui import UiHelper


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ok(resp, label: str = "") -> dict:
    """Assert 2xx and return parsed JSON."""
    assert 200 <= resp.status_code < 300, (
        f"{label}: expected 2xx, got {resp.status_code} -- {resp.text}"
    )
    return resp.json()


# ===========================================================================
# 1. Happy path -- full API-driven lifecycle
# ===========================================================================

class TestHappyPath:
    """Register -> org -> team -> project -> iteration -> requirement
    -> spec writing -> create spec/version/clauses -> spec review
    -> submit -> lock -> dev task -> claim -> review -> done
    -> test task -> test cases (linked to clauses) -> running -> passed
    -> coverage check -> requirement done.
    """

    def test_happy_path(self, api: ApiHelper):
        # ── Register ──
        reg = api.register()
        assert "access_token" in reg

        # ── Organization ──
        org = api.create_org()
        assert "id" in org

        # ── Team ──
        team = api.create_team(org_id=org["id"])
        assert "id" in team

        # ── Project ──
        project = api.create_project(team_id=team["id"])
        pid = project["id"]

        # ── Iteration ──
        iteration = api.create_iteration(project_id=pid)
        iid = iteration["id"]

        # ── Requirement (draft) ──
        req = api.create_requirement(
            project_id=pid,
            iteration_id=iid,
            title="User Authentication",
            priority="high",
        )
        rid = req["id"]
        assert req["status"] == "draft"

        # ── Transition to spec_writing ──
        resp = api.update_requirement_status(rid, "spec_writing")
        _ok(resp, "-> spec_writing")
        assert resp.json()["status"] == "spec_writing"

        # ── Create specification (api type) ──
        spec = api.create_specification(
            requirement_id=rid,
            spec_type="api",
            title="Auth API Specification",
        )
        spec_id = spec["id"]

        # ── Create spec version ──
        ver = api.create_spec_version(
            spec_id=spec_id,
            content={"endpoints": [{"path": "/auth/login", "method": "POST"}]},
        )
        ver_id = ver["id"]
        assert ver["version"] == 1
        assert ver["status"] == "draft"

        # ── Create clauses ──
        c_must = api.create_clause(
            version_id=ver_id,
            clause_id="FUNC-001",
            title="Login endpoint",
            description="POST /auth/login returns JWT token",
            category="functional",
            severity="must",
        )
        c_should = api.create_clause(
            version_id=ver_id,
            clause_id="SEC-001",
            title="Rate limiting",
            description="Max 5 login attempts per minute",
            category="security",
            severity="should",
        )
        assert c_must["severity"] == "must"
        assert c_should["severity"] == "should"

        # Verify both clauses are listed
        clauses = api.list_clauses(ver_id)
        assert len(clauses) == 2

        # ── Transition to spec_review ──
        resp = api.update_requirement_status(rid, "spec_review")
        _ok(resp, "-> spec_review")
        assert resp.json()["status"] == "spec_review"

        # ── Submit spec version ──
        resp = api.submit_spec_version(ver_id)
        _ok(resp, "submit spec version")
        assert resp.json()["status"] == "reviewing"

        # ── Lock spec version ──
        resp = api.lock_spec_version(ver_id)
        _ok(resp, "lock spec version")
        assert resp.json()["status"] == "locked"

        # ── Verify requirement auto-transitioned to spec_locked ──
        req_check = api.get_requirement(rid)
        assert req_check["status"] == "spec_locked"

        # ── Create dev task ──
        resp = api.create_dev_task(
            requirement_id=rid,
            spec_version_id=ver_id,
            iteration_id=iid,
            title="Implement user authentication",
            estimate_hours=8.0,
        )
        _ok(resp, "create dev task")
        dt = resp.json()
        dt_id = dt["id"]
        assert dt["status"] == "open"

        # ── Claim dev task ──
        resp = api.claim_dev_task(dt_id)
        _ok(resp, "claim dev task")
        assert resp.json()["status"] == "in_progress"

        # ── Dev task: review ──
        resp = api.update_dev_task_status(dt_id, "review")
        _ok(resp, "dev task -> review")
        assert resp.json()["status"] == "review"

        # ── Dev task: done ──
        resp = api.update_dev_task_status(dt_id, "done")
        _ok(resp, "dev task -> done")
        assert resp.json()["status"] == "done"

        # ── Requirement: spec_locked -> in_progress ──
        resp = api.update_requirement_status(rid, "in_progress")
        _ok(resp, "-> in_progress")
        assert resp.json()["status"] == "in_progress"

        # ── Requirement: in_progress -> testing ──
        resp = api.update_requirement_status(rid, "testing")
        _ok(resp, "-> testing")
        assert resp.json()["status"] == "testing"

        # ── Create test task ──
        resp = api.create_test_task(
            requirement_id=rid,
            iteration_id=iid,
            title="Test user authentication",
        )
        _ok(resp, "create test task")
        tt = resp.json()
        tt_id = tt["id"]

        # ── Create test cases linked to clauses ──
        resp = api.create_test_case(
            test_task_id=tt_id,
            title="Verify login returns JWT",
            steps="1. POST /auth/login with valid credentials\n2. Assert 200 with access_token",
            expected_result="200 OK with valid JWT in response body",
            clause_ids=[c_must["id"], c_should["id"]],
        )
        _ok(resp, "create test case")
        tc = resp.json()
        tc_id = tc["id"]
        assert tc["status"] == "pending"

        # ── Test case: running ──
        resp = api.update_test_case_status(tc_id, "running")
        _ok(resp, "test case -> running")
        assert resp.json()["status"] == "running"

        # ── Test case: passed ──
        resp = api.update_test_case_status(tc_id, "passed")
        _ok(resp, "test case -> passed")
        assert resp.json()["status"] == "passed"

        # ── Check coverage ──
        cov = api.get_coverage(rid)
        assert cov["total_clauses"] == 2
        assert cov["covered_clauses"] == 2
        assert cov["must_coverage_pct"] == 100.0

        check = api.check_coverage(rid)
        assert check["sufficient"] is True

        # ── Requirement: testing -> done ──
        resp = api.update_requirement_status(rid, "done")
        _ok(resp, "-> done")
        assert resp.json()["status"] == "done"

        # ── Final verification: fetch requirement and confirm status ──
        final = api.get_requirement(rid)
        assert final["status"] == "done"
        assert final["title"] == "User Authentication"

        # ── Verify tasks are visible at project level ──
        dev_tasks = api.list_dev_tasks(pid)
        assert any(t["id"] == dt_id for t in dev_tasks)

        test_tasks = api.list_test_tasks(pid)
        assert any(t["id"] == tt_id for t in test_tasks)


# ===========================================================================
# 2. Spec rejection flow
# ===========================================================================

class TestSpecRejectionFlow:
    """Create spec, submit, reject, verify version back to draft,
    resubmit and lock successfully."""

    def test_spec_rejection_flow(self, api: ApiHelper):
        data = api.seed()
        pid = data["project"]["id"]
        iid = data["iteration"]["id"]

        # Create requirement and push to spec_writing
        req = api.create_requirement(
            project_id=pid, iteration_id=iid,
            title="Spec Rejection Test", priority="medium",
        )
        rid = req["id"]

        api.update_requirement_status(rid, "spec_writing").raise_for_status()

        # Create spec + version + clause
        spec = api.create_specification(requirement_id=rid, title="Rejectable Spec")
        ver = api.create_spec_version(spec_id=spec["id"])
        api.create_clause(
            version_id=ver["id"], clause_id="R-001",
            title="Clause A", description="desc", severity="must",
        )

        # Move to spec_review and submit
        api.update_requirement_status(rid, "spec_review").raise_for_status()
        resp = api.submit_spec_version(ver["id"])
        _ok(resp, "submit for review")
        assert resp.json()["status"] == "reviewing"

        # ── Reject the spec version ──
        resp = api.reject_spec_version(ver["id"])
        _ok(resp, "reject spec version")
        # Version should go back to draft
        assert resp.json()["status"] == "draft"

        # ── Verify requirement is still in spec_review ──
        # (rejection does not auto-transition requirement status;
        #  the requirement stays at spec_review)
        req_state = api.get_requirement(rid)
        assert req_state["status"] in ("spec_review", "spec_rejected")

        # ── Transition requirement to spec_rejected if not already ──
        if req_state["status"] != "spec_rejected":
            resp = api.update_requirement_status(rid, "spec_rejected")
            _ok(resp, "-> spec_rejected")

        # ── Re-enter spec_writing from spec_rejected ──
        resp = api.update_requirement_status(rid, "spec_writing")
        _ok(resp, "spec_rejected -> spec_writing")
        assert resp.json()["status"] == "spec_writing"

        # ── Resubmit the fixed version ──
        # Move back to spec_review first
        api.update_requirement_status(rid, "spec_review").raise_for_status()

        resp = api.submit_spec_version(ver["id"])
        _ok(resp, "resubmit spec version")
        assert resp.json()["status"] == "reviewing"

        # ── Lock the version ──
        resp = api.lock_spec_version(ver["id"])
        _ok(resp, "lock spec version")
        assert resp.json()["status"] == "locked"

        # ── Verify requirement auto-transitioned to spec_locked ──
        final = api.get_requirement(rid)
        assert final["status"] == "spec_locked"


# ===========================================================================
# 3. Insufficient coverage blocks done
# ===========================================================================

class TestInsufficientCoverage:
    """Create a full chain with clauses but no test cases.
    Attempt to mark done -> expect 400."""

    def test_insufficient_coverage_blocks_done(self, api: ApiHelper):
        data = api.seed()
        pid = data["project"]["id"]
        iid = data["iteration"]["id"]

        # Create requirement and drive through spec workflow
        req = api.create_requirement(
            project_id=pid, iteration_id=iid,
            title="Coverage Gate Test", priority="high",
        )
        rid = req["id"]

        # spec_writing
        api.update_requirement_status(rid, "spec_writing").raise_for_status()

        # Create spec + version + must clause (no test cases will be created)
        spec = api.create_specification(requirement_id=rid)
        ver = api.create_spec_version(spec_id=spec["id"])
        api.create_clause(
            version_id=ver["id"], clause_id="M-001",
            title="Must have coverage", description="This needs a test",
            severity="must",
        )

        # spec_review -> submit -> lock
        api.update_requirement_status(rid, "spec_review").raise_for_status()
        api.submit_spec_version(ver["id"]).raise_for_status()
        api.lock_spec_version(ver["id"]).raise_for_status()

        # Verify spec_locked
        assert api.get_requirement(rid)["status"] == "spec_locked"

        # Drive to testing
        api.update_requirement_status(rid, "in_progress").raise_for_status()
        api.update_requirement_status(rid, "testing").raise_for_status()

        # ── Attempt to mark done WITHOUT test cases -> expect 400 ──
        resp = api.update_requirement_status(rid, "done")
        assert resp.status_code == 400, (
            f"Expected 400 (insufficient coverage), got {resp.status_code}: {resp.text}"
        )

        # Confirm coverage check reflects insufficient state
        check = api.check_coverage(rid)
        assert check["sufficient"] is False

        # Requirement should still be in testing
        req_state = api.get_requirement(rid)
        assert req_state["status"] == "testing"


# ===========================================================================
# 4. Cancelled requirement
# ===========================================================================

class TestCancelledRequirement:
    """Create a requirement, drive to spec_locked, then cancel it."""

    def test_cancelled_requirement(self, api: ApiHelper):
        data = api.seed_requirement_with_spec()
        rid = data["requirement"]["id"]

        # Verify starting state is spec_locked
        req = api.get_requirement(rid)
        assert req["status"] == "spec_locked"

        # ── Cancel the requirement ──
        resp = api.update_requirement_status(rid, "cancelled")
        _ok(resp, "-> cancelled")
        assert resp.json()["status"] == "cancelled"

        # ── Verify final state ──
        final = api.get_requirement(rid)
        assert final["status"] == "cancelled"

        # ── Verify cancelled requirement cannot transition further ──
        resp = api.update_requirement_status(rid, "in_progress")
        assert resp.status_code in (400, 422), (
            f"Cancelled requirement should not accept transitions, "
            f"got {resp.status_code}: {resp.text}"
        )

        # ── Also test cancelling from in_progress ──
        req2 = api.create_requirement(
            project_id=data["project"]["id"],
            iteration_id=data["iteration"]["id"],
            title="Cancel from in_progress",
            priority="low",
        )
        rid2 = req2["id"]

        # Drive through to in_progress via another spec chain
        api.update_requirement_status(rid2, "spec_writing").raise_for_status()
        spec2 = api.create_specification(requirement_id=rid2)
        ver2 = api.create_spec_version(spec_id=spec2["id"])
        api.create_clause(
            version_id=ver2["id"], clause_id="C-001",
            title="Clause", description="d", severity="must",
        )
        api.update_requirement_status(rid2, "spec_review").raise_for_status()
        api.submit_spec_version(ver2["id"]).raise_for_status()
        api.lock_spec_version(ver2["id"]).raise_for_status()
        api.update_requirement_status(rid2, "in_progress").raise_for_status()

        # Cancel from in_progress
        resp = api.update_requirement_status(rid2, "cancelled")
        _ok(resp, "in_progress -> cancelled")
        assert resp.json()["status"] == "cancelled"


# ===========================================================================
# 5. Full lifecycle via UI (Playwright)
# ===========================================================================

class TestFullLifecycleViaUI:
    """Walk through creating a requirement and transitioning statuses
    using the Playwright-driven UI.

    Uses API to pre-seed org/team/project/iteration, then uses UI
    for the requirement workflow.
    """

    def test_full_lifecycle_via_ui(self, api: ApiHelper, ui: UiHelper):
        # ── Seed hierarchy via API ──
        data = api.seed()
        pid = data["project"]["id"]
        iid = data["iteration"]["id"]

        # Use a unique title to avoid collision with leftover data from prior runs
        import uuid
        req_title = f"Lifecycle-{uuid.uuid4().hex[:8]}"

        # ── Navigate to project requirements page ──
        ui.goto_project_requirements(pid)
        ui.page.wait_for_selector('button:has-text("New Requirement")', state="visible")

        # ── Click "New Requirement" button to open modal ──
        ui.click_button("New Requirement")
        ui.page.wait_for_selector('input[id="req-title"]', state="visible")

        # ── Fill in requirement form ──
        ui.fill_input("req-title", req_title)

        # ── Submit the form via the modal's Create button ──
        ui.page.locator('.fixed button:has-text("Create")').click()

        # Wait for modal to close and row to appear
        ui.page.wait_for_selector('input[id="req-title"]', state="hidden", timeout=5000)
        ui.page.wait_for_selector(
            f'tr:has-text("{req_title}")', state="visible", timeout=5000
        )

        # ── Get requirement ID via API ──
        reqs = api.list_requirements(pid)
        rid = next((r["id"] for r in reqs if r["title"] == req_title), None)
        assert rid is not None, f"Requirement '{req_title}' not found"

        # ── Navigate directly to requirement detail page ──
        ui.goto_requirement(pid, rid)

        # ── Requirement starts in draft status ──
        # Verify the "Start Spec Writing" button is present (confirms draft status)
        assert ui.page.locator('button:has-text("Start Spec Writing")').is_visible()

        # ── Create spec + version + clause via API (while in draft) ──
        spec = api.create_specification(requirement_id=rid, title="Auth Spec")
        ver = api.create_spec_version(spec_id=spec["id"])
        c_must = api.create_clause(
            version_id=ver["id"],
            clause_id="FUNC-001",
            title="Login works",
            description="User can log in",
            severity="must",
        )

        # ── draft → spec_writing via UI ──
        ui.page.locator('button:has-text("Start Spec Writing")').first.click()
        # Wait for status to update (badge shows "Spec Writing", buttons change)
        ui.page.locator('button:has-text("Submit for Review")').wait_for(state="visible", timeout=5000)

        # ── spec_writing → spec_review via UI ──
        ui.page.locator('button:has-text("Submit for Review")').first.click()
        ui.page.locator('button:has-text("Lock")').wait_for(state="visible", timeout=5000)

        # ── Submit and lock spec version via API (auto-transitions req to spec_locked) ──
        api.submit_spec_version(ver["id"]).raise_for_status()
        api.lock_spec_version(ver["id"]).raise_for_status()

        # ── Reload to reflect auto-transition to spec_locked ──
        ui.page.reload()
        ui.page.wait_for_load_state("networkidle")
        ui.assert_status_badge("spec_locked")

        # ── spec_locked → in_progress via UI ──
        ui.page.locator('button:has-text("Start Development")').first.click()
        ui.assert_status_badge("in_progress")

        # ── Create and complete dev task via API ──
        resp = api.create_dev_task(
            requirement_id=rid,
            spec_version_id=ver["id"],
            iteration_id=iid,
            title="Implement feature",
        )
        resp.raise_for_status()
        dt = resp.json()
        api.claim_dev_task(dt["id"]).raise_for_status()
        api.update_dev_task_status(dt["id"], "review").raise_for_status()
        api.update_dev_task_status(dt["id"], "done").raise_for_status()

        # ── in_progress → testing via UI ──
        ui.page.locator('button:has-text("Start Testing")').first.click()
        ui.assert_status_badge("testing")

        # ── Create test task + test case + pass via API ──
        resp = api.create_test_task(
            requirement_id=rid,
            iteration_id=iid,
            title="Test feature",
        )
        resp.raise_for_status()
        tt = resp.json()
        resp = api.create_test_case(
            test_task_id=tt["id"],
            title="Verify login",
            steps="1. Submit form",
            expected_result="Success",
            clause_ids=[c_must["id"]],
        )
        resp.raise_for_status()
        tc = resp.json()
        api.update_test_case_status(tc["id"], "running").raise_for_status()
        api.update_test_case_status(tc["id"], "passed").raise_for_status()

        # ── Verify coverage is sufficient ──
        check = api.check_coverage(rid)
        assert check["sufficient"] is True

        # ── testing → done via UI ──
        ui.page.locator('button:has-text("Mark Done")').first.click()
        ui.assert_status_badge("done")
