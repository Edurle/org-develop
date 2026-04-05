"""
End-to-end tests for the coverage module.

Covers coverage reports, coverage checks (sufficient/insufficient),
edge cases with no clauses, coverage-gated done transitions,
and UI coverage page verification.

Run:  python -m pytest tests/test_coverage.py -v -s
"""

import pytest

from helpers.api import ApiHelper
from helpers.ui import UiHelper


def _seed_to_testing_with_clause(api: ApiHelper, severity: str = "must") -> dict:
    """Seed a requirement to testing status with one clause of given severity.

    Returns dict with requirement, project, iteration, version, and clauses.
    """
    data = api.seed_requirement_with_spec()
    rid = data["requirement"]["id"]
    iid = data["iteration"]["id"]
    vid = data["version"]["id"]

    # Clear default clause and create a custom one
    clauses = api.list_clauses(version_id=vid)

    # Add additional clause if needed
    api.create_clause(
        version_id=vid,
        clause_id=f"CL-{severity.upper()}",
        title=f"{severity.title()} clause",
        description=f"A clause with {severity} severity",
        severity=severity,
    )

    api.update_requirement_status(rid, "in_progress").raise_for_status()
    api.update_requirement_status(rid, "testing").raise_for_status()

    data["clauses"] = api.list_clauses(version_id=vid)
    return data


class TestCoverageAPI:
    """API-level tests for coverage reports and checks."""

    # -- 1. Get coverage report -----------------------------------------------

    def test_get_coverage_report(self, api: ApiHelper, seed_data: dict):
        """Create clause + test case + pass it, get report, verify numbers."""
        data = api.seed_requirement_with_spec()
        rid = data["requirement"]["id"]
        iid = data["iteration"]["id"]
        vid = data["version"]["id"]

        clauses = api.list_clauses(version_id=vid)
        assert len(clauses) >= 1
        clause_id = clauses[0]["id"]

        # Transition to testing
        api.update_requirement_status(rid, "in_progress").raise_for_status()
        api.update_requirement_status(rid, "testing").raise_for_status()

        # Create test task and test case covering the clause
        task_resp = api.create_test_task(
            requirement_id=rid, iteration_id=iid, title="Coverage Task"
        )
        assert task_resp.status_code == 201
        task = task_resp.json()

        tc_resp = api.create_test_case(
            test_task_id=task["id"],
            title="TC for coverage",
            steps="Execute feature",
            expected_result="Works",
            clause_ids=[clause_id],
        )
        assert tc_resp.status_code == 201
        tc = tc_resp.json()

        # Pass the test case
        api.update_test_case_status(tc["id"], "passed").raise_for_status()

        # Get coverage report
        report = api.get_coverage(rid)
        assert report["total_clauses"] >= 1
        assert report["covered_clauses"] >= 1
        assert report["must_coverage_pct"] == 100.0

    # -- 2. Coverage check sufficient -----------------------------------------

    def test_coverage_check_sufficient(self, api: ApiHelper, seed_data: dict):
        """must=100%, should>=80% should yield sufficient=True."""
        data = api.seed_requirement_with_spec()
        rid = data["requirement"]["id"]
        iid = data["iteration"]["id"]
        vid = data["version"]["id"]

        # The seed already creates a must clause; add a should clause
        should_clause = api.create_clause(
            version_id=vid,
            clause_id="CL-SH",
            title="Should clause",
            description="Recommended behavior",
            severity="should",
        )

        clauses = api.list_clauses(version_id=vid)
        all_clause_ids = [c["id"] for c in clauses]

        # Transition to testing
        api.update_requirement_status(rid, "in_progress").raise_for_status()
        api.update_requirement_status(rid, "testing").raise_for_status()

        # Create test task and cover all clauses with passed test cases
        task_resp = api.create_test_task(
            requirement_id=rid, iteration_id=iid, title="Sufficient Coverage Task"
        )
        assert task_resp.status_code == 201
        task = task_resp.json()

        tc_resp = api.create_test_case(
            test_task_id=task["id"],
            title="TC covers all",
            steps="Full coverage test",
            expected_result="All pass",
            clause_ids=all_clause_ids,
        )
        assert tc_resp.status_code == 201
        tc = tc_resp.json()

        api.update_test_case_status(tc["id"], "passed").raise_for_status()

        # Check coverage
        result = api.check_coverage(rid)
        assert result["sufficient"] is True

    # -- 3. Coverage check insufficient (must) --------------------------------

    def test_coverage_check_insufficient_must(self, api: ApiHelper, seed_data: dict):
        """A must clause with no covering test case -> sufficient=False."""
        data = api.seed_requirement_with_spec()
        rid = data["requirement"]["id"]

        # Transition to testing without creating any test cases
        api.update_requirement_status(rid, "in_progress").raise_for_status()
        api.update_requirement_status(rid, "testing").raise_for_status()

        result = api.check_coverage(rid)
        assert result["sufficient"] is False

    # -- 4. Coverage check insufficient (should) ------------------------------

    def test_coverage_check_insufficient_should(self, api: ApiHelper, seed_data: dict):
        """A should clause at 50% coverage (2 should clauses, only 1 covered) -> insufficient."""
        data = api.seed_requirement_with_spec()
        rid = data["requirement"]["id"]
        iid = data["iteration"]["id"]
        vid = data["version"]["id"]

        # Create two should clauses (in addition to the must clause from seed)
        should1 = api.create_clause(
            version_id=vid,
            clause_id="CL-SH1",
            title="Should clause 1",
            description="Recommended A",
            severity="should",
        )
        should2 = api.create_clause(
            version_id=vid,
            clause_id="CL-SH2",
            title="Should clause 2",
            description="Recommended B",
            severity="should",
        )

        # Transition to testing
        api.update_requirement_status(rid, "in_progress").raise_for_status()
        api.update_requirement_status(rid, "testing").raise_for_status()

        # Create test task, but only cover should1 (not should2)
        task_resp = api.create_test_task(
            requirement_id=rid, iteration_id=iid, title="Partial Should Task"
        )
        assert task_resp.status_code == 201
        task = task_resp.json()

        # Cover the must clause and only one of the two should clauses
        clauses = api.list_clauses(version_id=vid)
        must_clause = next(c for c in clauses if c["severity"] == "must")
        covered_ids = [must_clause["id"], should1["id"]]

        tc_resp = api.create_test_case(
            test_task_id=task["id"],
            title="TC partial should",
            steps="Partial test",
            expected_result="Partial pass",
            clause_ids=covered_ids,
        )
        assert tc_resp.status_code == 201
        tc = tc_resp.json()
        api.update_test_case_status(tc["id"], "passed").raise_for_status()

        # Should coverage = 1/2 = 50% < 80% -> insufficient
        result = api.check_coverage(rid)
        assert result["sufficient"] is False

    # -- 5. Coverage with no clauses ------------------------------------------

    def test_coverage_empty_no_clauses(self, api: ApiHelper, seed_data: dict):
        """A requirement with no clauses should report total_clauses=0."""
        pid = seed_data["project"]["id"]
        iid = seed_data["iteration"]["id"]

        # Create a requirement but do NOT add any clauses
        req = api.create_requirement(project_id=pid, iteration_id=iid, title="No Clauses")
        rid = req["id"]

        # Advance through the lifecycle (need a spec version even without clauses)
        api.update_requirement_status(rid, "spec_writing").raise_for_status()
        spec = api.create_specification(requirement_id=rid)
        ver = api.create_spec_version(spec_id=spec["id"])
        # No clauses added
        api.update_requirement_status(rid, "spec_review").raise_for_status()
        api.submit_spec_version(ver["id"]).raise_for_status()
        api.lock_spec_version(ver["id"]).raise_for_status()

        api.update_requirement_status(rid, "in_progress").raise_for_status()
        api.update_requirement_status(rid, "testing").raise_for_status()

        report = api.get_coverage(rid)
        assert report["total_clauses"] == 0
        assert report["covered_clauses"] == 0

    # -- 6. Cannot mark done without coverage ---------------------------------

    def test_cannot_mark_done_without_coverage(self, api: ApiHelper, seed_data: dict):
        """Attempt to move a requirement to done with 0% coverage, expect 400."""
        data = api.seed_requirement_with_spec()
        rid = data["requirement"]["id"]

        # Advance to testing without creating test cases
        api.update_requirement_status(rid, "in_progress").raise_for_status()
        api.update_requirement_status(rid, "testing").raise_for_status()

        # Attempt to move to done -- should fail due to insufficient coverage
        resp = api.update_requirement_status(rid, "done")
        assert resp.status_code == 400
        assert "coverage" in resp.json()["detail"].lower()

    # -- 7. Coverage report page (UI) -----------------------------------------

    def test_coverage_report_page(self, api: ApiHelper, seed_data: dict, ui: UiHelper):
        """Create coverage data via API, navigate to coverage page, verify percentages visible."""
        data = api.seed_requirement_with_spec()
        rid = data["requirement"]["id"]
        pid = data["project"]["id"]
        iid = data["iteration"]["id"]
        vid = data["version"]["id"]

        clauses = api.list_clauses(version_id=vid)
        clause_id = clauses[0]["id"]

        # Transition to testing
        api.update_requirement_status(rid, "in_progress").raise_for_status()
        api.update_requirement_status(rid, "testing").raise_for_status()

        # Create test task and passed test case
        task_resp = api.create_test_task(
            requirement_id=rid, iteration_id=iid, title="UI Coverage Task"
        )
        assert task_resp.status_code == 201
        task = task_resp.json()

        tc_resp = api.create_test_case(
            test_task_id=task["id"],
            title="TC UI coverage",
            steps="Test",
            expected_result="Pass",
            clause_ids=[clause_id],
        )
        assert tc_resp.status_code == 201
        tc = tc_resp.json()
        api.update_test_case_status(tc["id"], "passed").raise_for_status()

        # Navigate to the coverage page
        ui.goto_coverage(pid, rid)

        # Verify 100% is visible on the page
        ui.assert_text_visible("100%")
