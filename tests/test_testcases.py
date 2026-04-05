"""
End-to-end tests for the test cases module.

Covers test case CRUD, clause linking, status transitions
(pending -> running -> passed/failed/blocked), and listing.

Run:  python -m pytest tests/test_testcases.py -v -s
"""

import pytest

from helpers.api import ApiHelper
from helpers.ui import UiHelper


def _seed_requirement_in_testing(api: ApiHelper) -> dict:
    """Create a full chain and advance the requirement to testing status.

    Returns dict with requirement, project, iteration, version, and clauses.
    """
    data = api.seed_requirement_with_spec()
    rid = data["requirement"]["id"]

    api.update_requirement_status(rid, "in_progress").raise_for_status()
    api.update_requirement_status(rid, "testing").raise_for_status()

    clauses = api.list_clauses(version_id=data["version"]["id"])
    data["clauses"] = clauses
    return data


class TestTestCaseAPI:
    """API-level tests for test case CRUD and lifecycle."""

    # -- 1. Create test case -------------------------------------------------

    def test_create_test_case(self, api: ApiHelper, seed_data: dict):
        """Move requirement to testing, create test task + test case, verify 201 and fields."""
        data = _seed_requirement_in_testing(api)
        rid = data["requirement"]["id"]
        iid = data["iteration"]["id"]

        # Create a test task
        task_resp = api.create_test_task(
            requirement_id=rid, iteration_id=iid, title="Test Task Alpha"
        )
        assert task_resp.status_code == 201
        task = task_resp.json()

        # Create a test case
        tc_resp = api.create_test_case(
            test_task_id=task["id"],
            title="Verify login works",
            steps="1. Open login page\n2. Enter credentials\n3. Click submit",
            expected_result="User is redirected to dashboard",
        )
        assert tc_resp.status_code == 201

        tc = tc_resp.json()
        assert tc["title"] == "Verify login works"
        assert tc["steps"] == "1. Open login page\n2. Enter credentials\n3. Click submit"
        assert tc["expected_result"] == "User is redirected to dashboard"
        assert tc["status"] == "pending"
        assert "id" in tc

    # -- 2. Create test case with clause_ids ---------------------------------

    def test_create_test_case_with_clause_ids(self, api: ApiHelper, seed_data: dict):
        """Create a clause first, then create a test case linked to it."""
        data = _seed_requirement_in_testing(api)
        rid = data["requirement"]["id"]
        iid = data["iteration"]["id"]
        clauses = data["clauses"]
        assert len(clauses) >= 1, "Expected at least one clause from seed"
        clause_id = clauses[0]["id"]

        # Create test task
        task_resp = api.create_test_task(
            requirement_id=rid, iteration_id=iid, title="Clause-Linked Task"
        )
        assert task_resp.status_code == 201
        task = task_resp.json()

        # Create test case linked to the clause
        tc_resp = api.create_test_case(
            test_task_id=task["id"],
            title="TC with clause link",
            steps="Execute the feature described in clause",
            expected_result="Clause requirement is satisfied",
            clause_ids=[clause_id],
        )
        assert tc_resp.status_code == 201

        tc = tc_resp.json()
        assert tc["title"] == "TC with clause link"
        assert clause_id in tc.get("clause_ids", [clause_id])

    # -- 3. List test cases --------------------------------------------------

    def test_list_test_cases(self, api: ApiHelper, seed_data: dict):
        """Create 2 test cases on the same test task, list, verify both appear."""
        data = _seed_requirement_in_testing(api)
        rid = data["requirement"]["id"]
        iid = data["iteration"]["id"]

        task_resp = api.create_test_task(
            requirement_id=rid, iteration_id=iid, title="List Task"
        )
        assert task_resp.status_code == 201
        task = task_resp.json()

        tc1_resp = api.create_test_case(
            test_task_id=task["id"],
            title="TC-List-001",
            steps="Step A",
            expected_result="Result A",
        )
        assert tc1_resp.status_code == 201

        tc2_resp = api.create_test_case(
            test_task_id=task["id"],
            title="TC-List-002",
            steps="Step B",
            expected_result="Result B",
        )
        assert tc2_resp.status_code == 201

        cases = api.list_test_cases(task["id"])
        assert isinstance(cases, list)
        assert len(cases) >= 2

        titles = {c["title"] for c in cases}
        assert "TC-List-001" in titles
        assert "TC-List-002" in titles

    # -- 4. Update test case to passed ---------------------------------------

    def test_update_test_case_passed(self, api: ApiHelper, seed_data: dict):
        """Create a test case, transition pending -> running -> passed."""
        data = _seed_requirement_in_testing(api)
        rid = data["requirement"]["id"]
        iid = data["iteration"]["id"]

        task_resp = api.create_test_task(
            requirement_id=rid, iteration_id=iid, title="Pass Task"
        )
        assert task_resp.status_code == 201
        task = task_resp.json()

        tc_resp = api.create_test_case(
            test_task_id=task["id"],
            title="TC-Pass",
            steps="Run test",
            expected_result="Passes",
        )
        assert tc_resp.status_code == 201
        tc = tc_resp.json()

        # Transition to running
        run_resp = api.update_test_case_status(tc["id"], "running")
        assert run_resp.status_code == 200
        assert run_resp.json()["status"] == "running"

        # Transition to passed
        pass_resp = api.update_test_case_status(tc["id"], "passed")
        assert pass_resp.status_code == 200
        assert pass_resp.json()["status"] == "passed"

    # -- 5. Update test case to failed ---------------------------------------

    def test_update_test_case_failed(self, api: ApiHelper, seed_data: dict):
        """Create a test case, transition pending -> running -> failed."""
        data = _seed_requirement_in_testing(api)
        rid = data["requirement"]["id"]
        iid = data["iteration"]["id"]

        task_resp = api.create_test_task(
            requirement_id=rid, iteration_id=iid, title="Fail Task"
        )
        assert task_resp.status_code == 201
        task = task_resp.json()

        tc_resp = api.create_test_case(
            test_task_id=task["id"],
            title="TC-Fail",
            steps="Execute failing scenario",
            expected_result="Should not happen",
        )
        assert tc_resp.status_code == 201
        tc = tc_resp.json()

        # Transition to running
        run_resp = api.update_test_case_status(tc["id"], "running")
        assert run_resp.status_code == 200
        assert run_resp.json()["status"] == "running"

        # Transition to failed
        fail_resp = api.update_test_case_status(tc["id"], "failed")
        assert fail_resp.status_code == 200
        assert fail_resp.json()["status"] == "failed"

    # -- 6. Update test case to blocked --------------------------------------

    def test_update_test_case_blocked(self, api: ApiHelper, seed_data: dict):
        """Create a test case, transition pending -> running -> blocked."""
        data = _seed_requirement_in_testing(api)
        rid = data["requirement"]["id"]
        iid = data["iteration"]["id"]

        task_resp = api.create_test_task(
            requirement_id=rid, iteration_id=iid, title="Blocked Task"
        )
        assert task_resp.status_code == 201
        task = task_resp.json()

        tc_resp = api.create_test_case(
            test_task_id=task["id"],
            title="TC-Blocked",
            steps="Attempt to test",
            expected_result="Cannot proceed",
        )
        assert tc_resp.status_code == 201
        tc = tc_resp.json()

        # Transition to running
        run_resp = api.update_test_case_status(tc["id"], "running")
        assert run_resp.status_code == 200
        assert run_resp.json()["status"] == "running"

        # Transition to blocked
        block_resp = api.update_test_case_status(tc["id"], "blocked")
        assert block_resp.status_code == 200
        assert block_resp.json()["status"] == "blocked"
