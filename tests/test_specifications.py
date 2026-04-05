"""
End-to-end tests for the specifications module.

Covers specification CRUD, version lifecycle (draft -> reviewing -> locked),
clause management, and UI workflows for spec detail pages.

Run:  python -m pytest tests/test_specifications.py -v -s
"""

import pytest

from helpers.api import ApiHelper
from helpers.ui import UiHelper


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_requirement_ready_for_spec(api: ApiHelper, seed_data: dict) -> dict:
    """Create a requirement in spec_writing status and return {req, project_id}."""
    pid = seed_data["project"]["id"]
    iid = seed_data["iteration"]["id"]
    req = api.create_requirement(project_id=pid, iteration_id=iid)
    api.update_requirement_status(req["id"], "spec_writing").raise_for_status()
    return {"requirement": req, "project_id": pid, "iteration_id": iid}


# ===========================================================================
# API tests
# ===========================================================================


class TestSpecificationAPI:
    """API tests for specification and version endpoints."""

    # -- 1. Create specification (api type) ------------------------------

    def test_create_specification_api_type(self, api: ApiHelper, seed_data: dict):
        ctx = _create_requirement_ready_for_spec(api, seed_data)
        rid = ctx["requirement"]["id"]

        spec = api.create_specification(
            requirement_id=rid, spec_type="api", title="API Spec"
        )
        assert spec["spec_type"] == "api"
        assert spec["title"] == "API Spec"
        assert spec["requirement_id"] == rid
        assert "id" in spec

    # -- 2. Create specification (data type) -----------------------------

    def test_create_specification_data_type(self, api: ApiHelper, seed_data: dict):
        ctx = _create_requirement_ready_for_spec(api, seed_data)
        rid = ctx["requirement"]["id"]

        spec = api.create_specification(
            requirement_id=rid, spec_type="data", title="Data Spec"
        )
        assert spec["spec_type"] == "data"
        assert spec["title"] == "Data Spec"
        assert spec["requirement_id"] == rid
        assert "id" in spec

    # -- 3. Create specification (flow type) -----------------------------

    def test_create_specification_flow_type(self, api: ApiHelper, seed_data: dict):
        ctx = _create_requirement_ready_for_spec(api, seed_data)
        rid = ctx["requirement"]["id"]

        spec = api.create_specification(
            requirement_id=rid, spec_type="flow", title="Flow Spec"
        )
        assert spec["spec_type"] == "flow"
        assert spec["title"] == "Flow Spec"
        assert spec["requirement_id"] == rid
        assert "id" in spec

    # -- 4. Create specification (ui type) -------------------------------

    def test_create_specification_ui_type(self, api: ApiHelper, seed_data: dict):
        ctx = _create_requirement_ready_for_spec(api, seed_data)
        rid = ctx["requirement"]["id"]

        spec = api.create_specification(
            requirement_id=rid, spec_type="ui", title="UI Spec"
        )
        assert spec["spec_type"] == "ui"
        assert spec["title"] == "UI Spec"
        assert spec["requirement_id"] == rid
        assert "id" in spec

    # -- 5. List specifications ------------------------------------------

    def test_list_specifications(self, api: ApiHelper, seed_data: dict):
        ctx = _create_requirement_ready_for_spec(api, seed_data)
        rid = ctx["requirement"]["id"]

        # Create multiple specifications of different types
        s1 = api.create_specification(rid, "api", "API Spec")
        s2 = api.create_specification(rid, "data", "Data Spec")
        s3 = api.create_specification(rid, "flow", "Flow Spec")

        specs = api.list_specifications(rid)
        assert isinstance(specs, list)
        assert len(specs) >= 3

        returned_ids = {s["id"] for s in specs}
        assert s1["id"] in returned_ids
        assert s2["id"] in returned_ids
        assert s3["id"] in returned_ids

    # -- 6. Create spec version ------------------------------------------

    def test_create_spec_version(self, api: ApiHelper, seed_data: dict):
        ctx = _create_requirement_ready_for_spec(api, seed_data)
        rid = ctx["requirement"]["id"]
        spec = api.create_specification(rid, "api", "Versioned Spec")

        version = api.create_spec_version(spec_id=spec["id"])
        assert version["spec_id"] == spec["id"]
        assert version["version"] == 1
        assert version["status"] == "draft"
        assert "id" in version

    # -- 7. List spec versions -------------------------------------------

    def test_list_spec_versions(self, api: ApiHelper, seed_data: dict):
        ctx = _create_requirement_ready_for_spec(api, seed_data)
        rid = ctx["requirement"]["id"]
        spec = api.create_specification(rid, "api", "Multi-Version Spec")

        v1 = api.create_spec_version(spec_id=spec["id"])
        v2 = api.create_spec_version(spec_id=spec["id"])

        versions = api.list_spec_versions(spec_id=spec["id"])
        assert isinstance(versions, list)
        assert len(versions) == 2

        version_numbers = {v["version"] for v in versions}
        assert 1 in version_numbers
        assert 2 in version_numbers

        version_ids = {v["id"] for v in versions}
        assert v1["id"] in version_ids
        assert v2["id"] in version_ids

    # -- 8. Submit spec version (draft -> reviewing) ---------------------

    def test_submit_spec_version(self, api: ApiHelper, seed_data: dict):
        ctx = _create_requirement_ready_for_spec(api, seed_data)
        rid = ctx["requirement"]["id"]
        spec = api.create_specification(rid, "api", "Submit Test")
        version = api.create_spec_version(spec_id=spec["id"])

        resp = api.submit_spec_version(version["id"])
        assert resp.status_code == 200

        # Verify status changed to reviewing
        versions = api.list_spec_versions(spec_id=spec["id"])
        submitted = next(v for v in versions if v["id"] == version["id"])
        assert submitted["status"] == "reviewing"

    # -- 9. Lock spec version (reviewing -> locked) ----------------------

    def test_lock_spec_version(self, api: ApiHelper, seed_data: dict):
        ctx = _create_requirement_ready_for_spec(api, seed_data)
        rid = ctx["requirement"]["id"]
        spec = api.create_specification(rid, "api", "Lock Test")
        version = api.create_spec_version(spec_id=spec["id"])

        # Must submit before locking
        api.submit_spec_version(version["id"]).raise_for_status()

        resp = api.lock_spec_version(version["id"])
        assert resp.status_code == 200

        # Verify status changed to locked
        versions = api.list_spec_versions(spec_id=spec["id"])
        locked = next(v for v in versions if v["id"] == version["id"])
        assert locked["status"] == "locked"

    # -- 10. Reject spec version (reviewing -> draft, re-submit) ---------

    def test_reject_spec_version(self, api: ApiHelper, seed_data: dict):
        ctx = _create_requirement_ready_for_spec(api, seed_data)
        rid = ctx["requirement"]["id"]
        spec = api.create_specification(rid, "api", "Reject Test")
        version = api.create_spec_version(spec_id=spec["id"])

        # Submit first, then reject
        api.submit_spec_version(version["id"]).raise_for_status()

        resp = api.reject_spec_version(version["id"])
        assert resp.status_code == 200

        # Verify status back to draft
        versions = api.list_spec_versions(spec_id=spec["id"])
        rejected = next(v for v in versions if v["id"] == version["id"])
        assert rejected["status"] == "draft"

        # Verify can submit again after rejection
        resp2 = api.submit_spec_version(version["id"])
        assert resp2.status_code == 200

        versions2 = api.list_spec_versions(spec_id=spec["id"])
        resubmitted = next(v for v in versions2 if v["id"] == version["id"])
        assert resubmitted["status"] == "reviewing"

    # -- 11. Create clause -----------------------------------------------

    def test_create_clause(self, api: ApiHelper, seed_data: dict):
        ctx = _create_requirement_ready_for_spec(api, seed_data)
        rid = ctx["requirement"]["id"]
        spec = api.create_specification(rid, "api", "Clause Test")
        version = api.create_spec_version(spec_id=spec["id"])

        clause = api.create_clause(
            version_id=version["id"],
            clause_id="CL-001",
            title="User authentication",
            description="The system must authenticate users via JWT tokens.",
            category="security",
            severity="must",
        )
        assert clause["clause_id"] == "CL-001"
        assert clause["title"] == "User authentication"
        assert clause["description"] == "The system must authenticate users via JWT tokens."
        assert clause["category"] == "security"
        assert clause["severity"] == "must"
        assert "id" in clause

    # -- 12. List clauses ------------------------------------------------

    def test_list_clauses(self, api: ApiHelper, seed_data: dict):
        ctx = _create_requirement_ready_for_spec(api, seed_data)
        rid = ctx["requirement"]["id"]
        spec = api.create_specification(rid, "api", "Clause List Test")
        version = api.create_spec_version(spec_id=spec["id"])

        c1 = api.create_clause(version["id"], "CL-001", "First", "Desc 1", "functional", "must")
        c2 = api.create_clause(version["id"], "CL-002", "Second", "Desc 2", "validation", "should")

        clauses = api.list_clauses(version["id"])
        assert isinstance(clauses, list)
        assert len(clauses) == 2

        clause_ids = {c["id"] for c in clauses}
        assert c1["id"] in clause_ids
        assert c2["id"] in clause_ids

    # -- 13. Clause severity must/should/may -----------------------------

    def test_clause_severity_must_should_may(self, api: ApiHelper, seed_data: dict):
        ctx = _create_requirement_ready_for_spec(api, seed_data)
        rid = ctx["requirement"]["id"]
        spec = api.create_specification(rid, "api", "Severity Test")
        version = api.create_spec_version(spec_id=spec["id"])

        api.create_clause(version["id"], "CL-M1", "Must clause", "Required", "functional", "must")
        api.create_clause(version["id"], "CL-S1", "Should clause", "Recommended", "functional", "should")
        api.create_clause(version["id"], "CL-Y1", "May clause", "Optional", "functional", "may")

        clauses = api.list_clauses(version["id"])
        assert len(clauses) == 3

        severities = {c["severity"] for c in clauses}
        assert severities == {"must", "should", "may"}

        # Verify each clause has the correct severity
        by_clause_id = {c["clause_id"]: c for c in clauses}
        assert by_clause_id["CL-M1"]["severity"] == "must"
        assert by_clause_id["CL-S1"]["severity"] == "should"
        assert by_clause_id["CL-Y1"]["severity"] == "may"

    # -- 14. Spec locked immutable ----------------------------------------

    def test_spec_locked_immutable(self, api: ApiHelper, seed_data: dict):
        ctx = _create_requirement_ready_for_spec(api, seed_data)
        rid = ctx["requirement"]["id"]
        spec = api.create_specification(rid, "api", "Immutable Test")
        version = api.create_spec_version(spec_id=spec["id"])

        # Submit and lock
        api.submit_spec_version(version["id"]).raise_for_status()
        api.lock_spec_version(version["id"]).raise_for_status()

        # Trying to submit a locked version should fail with 400
        resp = api.submit_spec_version(version["id"])
        assert resp.status_code == 400


# ===========================================================================
# UI tests
# ===========================================================================


class TestSpecificationUI:
    """UI workflow tests for specification detail pages."""

    def _seed_spec_for_ui(
        self, api: ApiHelper, seed_data: dict
    ) -> dict:
        """Create a requirement + specification ready for UI interaction."""
        ctx = _create_requirement_ready_for_spec(api, seed_data)
        rid = ctx["requirement"]["id"]
        pid = ctx["project_id"]
        spec = api.create_specification(rid, "api", "UI Test Spec")
        return {
            "requirement_id": rid,
            "project_id": pid,
            "spec": spec,
            "iteration_id": ctx["iteration_id"],
        }

    # -- 15. Create version via UI ----------------------------------------

    def test_spec_detail_create_version(
        self, api: ApiHelper, seed_data: dict, ui: UiHelper
    ):
        ctx = self._seed_spec_for_ui(api, seed_data)
        pid = ctx["project_id"]
        rid = ctx["requirement_id"]
        spec_id = ctx["spec"]["id"]

        # Navigate to the specification detail page
        ui.goto_specification(pid, rid, spec_id)

        # Edit content in the textarea
        ui.fill_textarea("spec-content", '{"endpoints": ["/api/test"]}')

        # Save as a new version
        ui.click_button("Save as New Version")

        # Verify the new version is visible
        ui.assert_text_visible("draft")

        # Cross-check via API
        versions = api.list_spec_versions(spec_id)
        assert len(versions) >= 1
        assert any(v["status"] == "draft" for v in versions)

    # -- 16. Add clause via modal -----------------------------------------

    def test_spec_detail_add_clause(
        self, api: ApiHelper, seed_data: dict, ui: UiHelper
    ):
        ctx = self._seed_spec_for_ui(api, seed_data)
        pid = ctx["project_id"]
        rid = ctx["requirement_id"]
        spec_id = ctx["spec"]["id"]

        # Create a version first (clauses belong to versions)
        version = api.create_spec_version(spec_id=spec_id)

        # Navigate to spec detail
        ui.goto_specification(pid, rid, spec_id)

        # Open the add-clause modal
        ui.click_button("Add Clause")

        # Fill in the clause form
        ui.fill_input("clause-id", "CL-UI-001")
        ui.fill_input("clause-title", "UI Added Clause")
        ui.fill_textarea("clause-description", "Clause created via the UI modal")
        ui.select_option("clause-category", "functional")
        ui.select_option("clause-severity", "must")

        # Submit the modal form
        ui.click_button("Save Clause")

        # Verify the clause is visible on the page
        ui.assert_text_visible("UI Added Clause")

        # Cross-check via API
        clauses = api.list_clauses(version["id"])
        assert any(c["title"] == "UI Added Clause" for c in clauses)

    # -- 17. Submit and lock via UI ---------------------------------------

    def test_spec_detail_submit_and_lock(
        self, api: ApiHelper, seed_data: dict, ui: UiHelper
    ):
        ctx = self._seed_spec_for_ui(api, seed_data)
        pid = ctx["project_id"]
        rid = ctx["requirement_id"]
        spec_id = ctx["spec"]["id"]

        # Create a version via API
        version = api.create_spec_version(spec_id=spec_id)

        # Navigate to spec detail
        ui.goto_specification(pid, rid, spec_id)

        # Click submit to transition draft -> reviewing
        ui.click_button("Submit for Review")
        ui.assert_text_visible("reviewing")

        # Click lock to transition reviewing -> locked
        ui.click_button("Lock Version")
        ui.assert_text_visible("locked")

        # Cross-check via API
        versions = api.list_spec_versions(spec_id)
        locked = next(v for v in versions if v["id"] == version["id"])
        assert locked["status"] == "locked"
