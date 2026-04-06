"""
End-to-end tests for the requirements module.

Covers API CRUD, status transitions, coverage-gated done flow,
and UI workflows for requirement list and detail pages.

Run:  python -m pytest tests/test_requirements.py -v -s
"""

import pytest

from helpers.api import ApiHelper
from helpers.ui import UiHelper


# ===========================================================================
# API tests
# ===========================================================================


class TestRequirementAPI:
    """API-level tests for requirement CRUD and lifecycle."""

    # -- Creation -----------------------------------------------------------

    def test_create_requirement(self, api: ApiHelper, seed_data: dict):
        """Create a requirement with defaults; verify status=draft, priority=medium."""
        pid = seed_data["project"]["id"]
        iid = seed_data["iteration"]["id"]

        req = api.create_requirement(
            project_id=pid, iteration_id=iid, title="Basic Requirement"
        )

        assert req["title"] == "Basic Requirement"
        assert req["status"] == "draft"
        assert req["priority"] == "medium"
        assert req["iteration_id"] == iid
        assert "id" in req
        assert req["creator_id"] == api.user_id

    def test_create_requirement_high_priority(self, api: ApiHelper, seed_data: dict):
        """Create a requirement with priority=high and verify it is stored."""
        pid = seed_data["project"]["id"]
        iid = seed_data["iteration"]["id"]

        req = api.create_requirement(
            project_id=pid,
            iteration_id=iid,
            title="High Priority Req",
            priority="high",
        )

        assert req["priority"] == "high"
        assert req["title"] == "High Priority Req"

    # -- Listing / filtering ------------------------------------------------

    def test_list_requirements(self, api: ApiHelper, seed_data: dict):
        """Create several requirements and verify the list count."""
        pid = seed_data["project"]["id"]
        iid = seed_data["iteration"]["id"]

        # seed_data already implies no existing requirements for this project
        api.create_requirement(project_id=pid, iteration_id=iid, title="R1")
        api.create_requirement(project_id=pid, iteration_id=iid, title="R2")
        api.create_requirement(project_id=pid, iteration_id=iid, title="R3")

        reqs = api.list_requirements(project_id=pid)
        assert len(reqs) >= 3

    def test_list_requirements_filter_by_status(self, api: ApiHelper, seed_data: dict):
        """Filter requirements by status=draft returns only draft items."""
        pid = seed_data["project"]["id"]
        iid = seed_data["iteration"]["id"]

        api.create_requirement(project_id=pid, iteration_id=iid, title="Draft A")
        api.create_requirement(project_id=pid, iteration_id=iid, title="Draft B")

        # Transition a third requirement out of draft
        req_c = api.create_requirement(
            project_id=pid, iteration_id=iid, title="Moved On"
        )
        api.update_requirement_status(req_c["id"], "spec_writing").raise_for_status()

        drafts = api.list_requirements(project_id=pid, status="draft")
        assert all(r["status"] == "draft" for r in drafts)
        assert len(drafts) >= 2

        # The moved requirement should not appear in drafts
        draft_ids = {r["id"] for r in drafts}
        assert req_c["id"] not in draft_ids

    def test_list_requirements_filter_by_iteration(self, api: ApiHelper, seed_data: dict):
        """Filter requirements by iteration_id returns only items in that iteration."""
        pid = seed_data["project"]["id"]
        iid = seed_data["iteration"]["id"]

        api.create_requirement(project_id=pid, iteration_id=iid, title="In Sprint")

        # Create a second iteration and a requirement in it
        other_iter = api.create_iteration(project_id=pid, name="Sprint 2")
        api.create_requirement(
            project_id=pid, iteration_id=other_iter["id"], title="Other Sprint"
        )

        reqs = api.list_requirements(project_id=pid, iteration_id=iid)
        assert all(r["iteration_id"] == iid for r in reqs)
        assert len(reqs) >= 1

        other_reqs = api.list_requirements(
            project_id=pid, iteration_id=other_iter["id"]
        )
        assert all(r["iteration_id"] == other_iter["id"] for r in other_reqs)
        assert len(other_reqs) >= 1

    # -- Retrieval / update -------------------------------------------------

    def test_get_requirement(self, api: ApiHelper, seed_data: dict):
        """GET a single requirement by id and verify all fields."""
        pid = seed_data["project"]["id"]
        iid = seed_data["iteration"]["id"]

        created = api.create_requirement(
            project_id=pid, iteration_id=iid, title="Fetch Me"
        )
        fetched = api.get_requirement(created["id"])

        assert fetched["id"] == created["id"]
        assert fetched["title"] == "Fetch Me"
        assert fetched["status"] == "draft"
        assert fetched["priority"] == "medium"
        assert fetched["iteration_id"] == iid
        assert fetched["creator_id"] == api.user_id

    def test_update_requirement(self, api: ApiHelper, seed_data: dict):
        """PATCH a requirement's title and verify the change persists."""
        pid = seed_data["project"]["id"]
        iid = seed_data["iteration"]["id"]

        created = api.create_requirement(
            project_id=pid, iteration_id=iid, title="Original Title"
        )
        updated = api.update_requirement(created["id"], title="Updated Title")

        assert updated["title"] == "Updated Title"

        # Verify via GET
        fetched = api.get_requirement(created["id"])
        assert fetched["title"] == "Updated Title"

    # -- Status transitions -------------------------------------------------

    def test_status_draft_to_spec_writing(self, api: ApiHelper, seed_data: dict):
        """Transition draft -> spec_writing."""
        pid = seed_data["project"]["id"]
        iid = seed_data["iteration"]["id"]

        req = api.create_requirement(
            project_id=pid, iteration_id=iid, title="Transition Test"
        )

        resp = api.update_requirement_status(req["id"], "spec_writing")
        assert resp.status_code == 200

        updated = resp.json()
        assert updated["status"] == "spec_writing"

    def test_status_spec_writing_to_spec_review(self, api: ApiHelper, seed_data: dict):
        """Transition draft -> spec_writing -> spec_review."""
        pid = seed_data["project"]["id"]
        iid = seed_data["iteration"]["id"]

        req = api.create_requirement(
            project_id=pid, iteration_id=iid, title="Multi-step Transition"
        )

        api.update_requirement_status(req["id"], "spec_writing").raise_for_status()
        resp = api.update_requirement_status(req["id"], "spec_review")
        assert resp.status_code == 200

        updated = resp.json()
        assert updated["status"] == "spec_review"

    def test_status_spec_review_to_spec_locked(self, api: ApiHelper, seed_data: dict):
        """Create spec + version + clauses, submit & lock -> auto-transition to spec_locked."""
        pid = seed_data["project"]["id"]
        iid = seed_data["iteration"]["id"]

        req = api.create_requirement(
            project_id=pid, iteration_id=iid, title="Spec Lock Flow"
        )
        rid = req["id"]

        # Advance to spec_writing
        api.update_requirement_status(rid, "spec_writing").raise_for_status()

        # Create specification and version with clause
        spec = api.create_specification(requirement_id=rid)
        ver = api.create_spec_version(spec_id=spec["id"])
        api.create_clause(
            version_id=ver["id"],
            clause_id="C-001",
            title="Must clause",
            description="System must do X",
            severity="must",
        )

        # Advance to spec_review, then submit and lock the version
        api.update_requirement_status(rid, "spec_review").raise_for_status()
        api.submit_spec_version(ver["id"]).raise_for_status()
        api.lock_spec_version(ver["id"]).raise_for_status()

        # The requirement should now be spec_locked
        fetched = api.get_requirement(rid)
        assert fetched["status"] == "spec_locked"

    def test_status_spec_locked_to_in_progress(self, api: ApiHelper, seed_data: dict):
        """Transition spec_locked -> in_progress."""
        data = api.seed_requirement_with_spec()
        rid = data["requirement"]["id"]

        resp = api.update_requirement_status(rid, "in_progress")
        assert resp.status_code == 200

        updated = resp.json()
        assert updated["status"] == "in_progress"

    def test_status_in_progress_to_testing(self, api: ApiHelper, seed_data: dict):
        """Transition spec_locked -> in_progress -> testing."""
        data = api.seed_requirement_with_spec()
        rid = data["requirement"]["id"]

        api.update_requirement_status(rid, "in_progress").raise_for_status()
        resp = api.update_requirement_status(rid, "testing")
        assert resp.status_code == 200

        updated = resp.json()
        assert updated["status"] == "testing"

    def test_status_testing_to_done_with_coverage(self, api: ApiHelper, seed_data: dict):
        """Full lifecycle: create spec + clause, lock, progress, create test task +
        test case covering the clause, then transition to done."""
        data = api.seed_requirement_with_spec()
        rid = data["requirement"]["id"]
        pid = data["project"]["id"]
        iid = data["iteration"]["id"]
        clause = data["version"]  # we need the clause id; retrieve it

        # Fetch clause id via the clauses listing endpoint
        clauses = api.list_clauses(version_id=data["version"]["id"])
        assert len(clauses) >= 1
        clause_id = clauses[0]["id"]

        # Transition to in_progress then testing
        api.update_requirement_status(rid, "in_progress").raise_for_status()
        api.update_requirement_status(rid, "testing").raise_for_status()

        # Create a test task and a test case that covers the must clause
        test_task_resp = api.create_test_task(
            requirement_id=rid, iteration_id=iid, title="Integration Test Task"
        )
        assert test_task_resp.status_code == 201
        test_task = test_task_resp.json()

        tc_resp = api.create_test_case(
            test_task_id=test_task["id"],
            title="TC covers must clause",
            steps="Execute the feature",
            expected_result="Feature works correctly",
            clause_ids=[clause_id],
        )
        assert tc_resp.status_code == 201
        test_case = tc_resp.json()

        # Mark the test case as passed so coverage is satisfied
        api.update_test_case_status(test_case["id"], "running").raise_for_status()
        api.update_test_case_status(test_case["id"], "passed").raise_for_status()

        # Now the transition to done should succeed
        resp = api.update_requirement_status(rid, "done")
        assert resp.status_code == 200

        updated = resp.json()
        assert updated["status"] == "done"

    def test_status_invalid_transition(self, api: ApiHelper, seed_data: dict):
        """Attempting draft -> done directly should return 400."""
        pid = seed_data["project"]["id"]
        iid = seed_data["iteration"]["id"]

        req = api.create_requirement(
            project_id=pid, iteration_id=iid, title="Bad Transition"
        )

        resp = api.update_requirement_status(req["id"], "done")
        assert resp.status_code == 400
        assert "Invalid status transition" in resp.json()["detail"]


# ===========================================================================
# UI tests
# ===========================================================================


class TestRequirementUI:
    """UI workflow tests for requirement list and detail pages."""

    def test_requirements_page_create(self, api: ApiHelper, seed_data: dict, ui: UiHelper):
        """Create a requirement via the New Requirement modal on the list page."""
        pid = seed_data["project"]["id"]
        iid = seed_data["iteration"]["id"]

        ui.goto_project_requirements(pid)

        # Open the create modal
        ui.click_button("New Requirement")

        # Fill the form
        ui.fill_input("req-title", "UI Created Requirement")
        ui.select_option("req-priority", "high")
        ui.select_option("req-iteration", iid)

        # Submit
        ui.click_button("Create")

        # Verify the requirement title appears on the page
        ui.assert_text_visible("UI Created Requirement")

        # Cross-check via API
        reqs = api.list_requirements(project_id=pid)
        titles = [r["title"] for r in reqs]
        assert "UI Created Requirement" in titles

    def test_requirements_page_filter(self, api: ApiHelper, seed_data: dict, ui: UiHelper):
        """Create requirements with different statuses via API, then use filter dropdowns."""
        pid = seed_data["project"]["id"]
        iid = seed_data["iteration"]["id"]

        # Create two requirements in draft
        api.create_requirement(project_id=pid, iteration_id=iid, title="Filter Draft A")
        api.create_requirement(project_id=pid, iteration_id=iid, title="Filter Draft B")

        # Create one and move it to spec_writing
        moved = api.create_requirement(
            project_id=pid, iteration_id=iid, title="Filter Writing"
        )
        api.update_requirement_status(moved["id"], "spec_writing").raise_for_status()

        ui.goto_project_requirements(pid)

        # All three should be visible initially
        ui.assert_text_visible("Filter Draft A")
        ui.assert_text_visible("Filter Writing")

        # Apply status filter to show only draft
        ui.select_option("filter-status", "draft")
        ui.page.wait_for_timeout(500)

        # Draft items should still be visible
        ui.assert_text_visible("Filter Draft A")

        # Reset filter
        ui.select_option("filter-status", "")
        ui.page.wait_for_timeout(500)

        # Everything should be visible again
        ui.assert_text_visible("Filter Writing")

    def test_requirement_detail_status_transitions(
        self, api: ApiHelper, seed_data: dict, ui: UiHelper
    ):
        """Navigate to requirement detail and click status transition buttons."""
        pid = seed_data["project"]["id"]
        iid = seed_data["iteration"]["id"]

        req = api.create_requirement(
            project_id=pid, iteration_id=iid, title="Detail Transition"
        )
        rid = req["id"]

        ui.goto_requirement(pid, rid)

        # Initial status should be draft
        ui.assert_status_badge("draft")

        # Click "Start Spec Writing"
        ui.click_button("Start Spec Writing")
        ui.page.wait_for_timeout(500)
        ui.assert_status_badge("spec_writing")

        # Verify via API
        fetched = api.get_requirement(rid)
        assert fetched["status"] == "spec_writing"
