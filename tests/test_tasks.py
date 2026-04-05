"""
End-to-end tests for the tasks module.

Covers dev task CRUD, status transitions (open -> in_progress -> review -> done,
open -> in_progress -> blocked), test task CRUD, claim workflow, pre-condition
gates (spec must be locked), and UI interactions on the project tasks page.

Run:  python -m pytest tests/test_tasks.py -v -s
"""

import pytest

from helpers.api import ApiHelper
from helpers.ui import UiHelper


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_dev_task_via_seed(api: ApiHelper) -> dict:
    """Seed a locked spec and create a dev task; return all context."""
    data = api.seed_requirement_with_spec()
    rid = data["requirement"]["id"]
    pid = data["project"]["id"]
    iid = data["iteration"]["id"]
    vid = data["version"]["id"]

    resp = api.create_dev_task(
        requirement_id=rid,
        spec_version_id=vid,
        iteration_id=iid,
        title="Test Dev Task",
        estimate_hours=4.0,
    )
    assert resp.status_code == 201, f"create_dev_task: {resp.status_code} {resp.text}"
    task = resp.json()
    data["dev_task"] = task
    return data


# ===========================================================================
# API tests -- Dev Tasks
# ===========================================================================


class TestDevTaskAPI:
    """API-level tests for dev task CRUD and lifecycle."""

    # -- 1. Create dev task -------------------------------------------------

    def test_create_dev_task(self, api: ApiHelper, seed_data: dict):
        """Create a dev task on a locked spec; verify status=201 and fields."""
        data = api.seed_requirement_with_spec()
        rid = data["requirement"]["id"]
        iid = data["iteration"]["id"]
        vid = data["version"]["id"]

        resp = api.create_dev_task(
            requirement_id=rid,
            spec_version_id=vid,
            iteration_id=iid,
            title="Implement auth module",
            estimate_hours=8.0,
        )
        assert resp.status_code == 201

        task = resp.json()
        assert task["title"] == "Implement auth module"
        assert task["status"] == "open"
        assert task["spec_version_id"] == vid
        assert task["iteration_id"] == iid
        assert task["estimate_hours"] == 8.0
        assert "id" in task

    # -- 2. Create dev task before spec locked fails ------------------------

    def test_create_dev_task_before_spec_locked_fails(
        self, api: ApiHelper, seed_data: dict
    ):
        """Dev tasks cannot be created when requirement is still in draft."""
        pid = seed_data["project"]["id"]
        iid = seed_data["iteration"]["id"]

        req = api.create_requirement(project_id=pid, iteration_id=iid)
        rid = req["id"]

        # Advance to spec_writing, create a spec but do NOT lock it
        api.update_requirement_status(rid, "spec_writing").raise_for_status()
        spec = api.create_specification(requirement_id=rid)
        ver = api.create_spec_version(spec_id=spec["id"])

        resp = api.create_dev_task(
            requirement_id=rid,
            spec_version_id=ver["id"],
            iteration_id=iid,
            title="Should fail",
        )
        assert resp.status_code == 400

    # -- 3. List dev tasks --------------------------------------------------

    def test_list_dev_tasks(self, api: ApiHelper, seed_data: dict):
        """Create a dev task and verify it appears in the project listing."""
        data = _create_dev_task_via_seed(api)
        pid = data["project"]["id"]

        tasks = api.list_dev_tasks(project_id=pid)
        assert isinstance(tasks, list)
        assert len(tasks) >= 1

        task_ids = {t["id"] for t in tasks}
        assert data["dev_task"]["id"] in task_ids

    # -- 4. Claim dev task --------------------------------------------------

    def test_claim_dev_task(self, api: ApiHelper, seed_data: dict):
        """Claim an open dev task; verify status=in_progress and assignee set."""
        data = _create_dev_task_via_seed(api)
        task_id = data["dev_task"]["id"]

        resp = api.claim_dev_task(task_id)
        assert resp.status_code == 200

        claimed = resp.json()
        assert claimed["status"] == "in_progress"
        assert claimed["assignee_id"] == api.user_id

    # -- 5. Status open -> in_progress (via claim) --------------------------

    def test_dev_task_status_open_to_in_progress(
        self, api: ApiHelper, seed_data: dict
    ):
        """Claiming a dev task transitions status from open to in_progress."""
        data = _create_dev_task_via_seed(api)
        task_id = data["dev_task"]["id"]

        # Verify initial status
        assert data["dev_task"]["status"] == "open"

        resp = api.claim_dev_task(task_id)
        assert resp.status_code == 200

        updated = resp.json()
        assert updated["status"] == "in_progress"

    # -- 6. Status in_progress -> review ------------------------------------

    def test_dev_task_status_in_progress_to_review(
        self, api: ApiHelper, seed_data: dict
    ):
        """Chain: claim -> update to review."""
        data = _create_dev_task_via_seed(api)
        task_id = data["dev_task"]["id"]

        api.claim_dev_task(task_id).raise_for_status()

        resp = api.update_dev_task_status(task_id, "review")
        assert resp.status_code == 200

        updated = resp.json()
        assert updated["status"] == "review"

    # -- 7. Status review -> done -------------------------------------------

    def test_dev_task_status_review_to_done(
        self, api: ApiHelper, seed_data: dict
    ):
        """Full chain: claim -> review -> done."""
        data = _create_dev_task_via_seed(api)
        task_id = data["dev_task"]["id"]

        api.claim_dev_task(task_id).raise_for_status()
        api.update_dev_task_status(task_id, "review").raise_for_status()

        resp = api.update_dev_task_status(task_id, "done")
        assert resp.status_code == 200

        updated = resp.json()
        assert updated["status"] == "done"

    # -- 8. Status -> blocked -----------------------------------------------

    def test_dev_task_status_to_blocked(self, api: ApiHelper, seed_data: dict):
        """Chain: claim -> update to blocked."""
        data = _create_dev_task_via_seed(api)
        task_id = data["dev_task"]["id"]

        api.claim_dev_task(task_id).raise_for_status()

        resp = api.update_dev_task_status(task_id, "blocked")
        assert resp.status_code == 200

        updated = resp.json()
        assert updated["status"] == "blocked"


# ===========================================================================
# API tests -- Test Tasks
# ===========================================================================


class TestTestTaskAPI:
    """API-level tests for test task CRUD."""

    # -- 9. Create test task ------------------------------------------------

    def test_create_test_task(self, api: ApiHelper, seed_data: dict):
        """Create a test task and verify response fields."""
        pid = seed_data["project"]["id"]
        iid = seed_data["iteration"]["id"]

        req = api.create_requirement(project_id=pid, iteration_id=iid)
        rid = req["id"]

        resp = api.create_test_task(
            requirement_id=rid,
            iteration_id=iid,
            title="Run integration tests",
        )
        assert resp.status_code == 201

        task = resp.json()
        assert task["title"] == "Run integration tests"
        assert "id" in task
        assert task["iteration_id"] == iid

    # -- 10. List test tasks ------------------------------------------------

    def test_list_test_tasks(self, api: ApiHelper, seed_data: dict):
        """Create a test task and verify it appears in the project listing."""
        pid = seed_data["project"]["id"]
        iid = seed_data["iteration"]["id"]

        req = api.create_requirement(project_id=pid, iteration_id=iid)
        rid = req["id"]

        resp = api.create_test_task(
            requirement_id=rid,
            iteration_id=iid,
            title="Regression suite",
        )
        assert resp.status_code == 201
        created = resp.json()

        tasks = api.list_test_tasks(project_id=pid)
        assert isinstance(tasks, list)
        assert len(tasks) >= 1

        task_ids = {t["id"] for t in tasks}
        assert created["id"] in task_ids


# ===========================================================================
# UI tests
# ===========================================================================


class TestTaskUI:
    """UI workflow tests for the project tasks page."""

    # -- 11. Claim dev task via UI ------------------------------------------

    def test_project_tasks_claim(
        self, api: ApiHelper, seed_data: dict, ui: UiHelper
    ):
        """Create a dev task via API, navigate to tasks page, click Claim."""
        data = _create_dev_task_via_seed(api)
        pid = data["project"]["id"]
        task_title = data["dev_task"]["title"]

        ui.goto_project_tasks(pid)

        # Ensure we are on the Dev Tasks tab
        ui.click_button("Dev Tasks")
        ui.page.wait_for_timeout(500)

        # The task title should be visible
        ui.assert_text_visible(task_title)

        # Click the Claim button for this task
        ui.click_button("Claim")
        ui.page.wait_for_timeout(500)

        # After claiming, the status should reflect in_progress
        ui.assert_text_visible("in_progress")

        # Cross-check via API
        tasks = api.list_dev_tasks(project_id=pid)
        claimed = next(t for t in tasks if t["id"] == data["dev_task"]["id"])
        assert claimed["status"] == "in_progress"
        assert claimed["assignee_id"] == api.user_id

    # -- 12. Change dev task status via UI ----------------------------------

    def test_project_tasks_status_change(
        self, api: ApiHelper, seed_data: dict, ui: UiHelper
    ):
        """Create and claim a dev task via API, then change status via dropdown."""
        data = _create_dev_task_via_seed(api)
        pid = data["project"]["id"]
        task_id = data["dev_task"]["id"]

        # Claim the task via API so it is in_progress
        api.claim_dev_task(task_id).raise_for_status()

        ui.goto_project_tasks(pid)

        # Ensure we are on the Dev Tasks tab
        ui.click_button("Dev Tasks")
        ui.page.wait_for_timeout(500)

        # Use the status dropdown to change to review
        ui.select_option("task-status", "review")
        ui.page.wait_for_timeout(500)

        # Verify the status changed
        ui.assert_text_visible("review")

        # Cross-check via API
        tasks = api.list_dev_tasks(project_id=pid)
        updated = next(t for t in tasks if t["id"] == task_id)
        assert updated["status"] == "review"
