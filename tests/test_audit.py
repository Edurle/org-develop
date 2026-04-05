"""
End-to-end tests for the audit log module.

Covers listing audit logs with pagination, filtering by resource_type
and action, and retrieving individual log entries.

Run:  python -m pytest tests/test_audit.py -v -s
"""

import pytest

from helpers.api import ApiHelper
from helpers.ui import UiHelper


class TestAuditAPI:
    """API-level tests for audit log endpoints."""

    # -- 1. List audit logs ---------------------------------------------------

    def test_list_audit_logs(self, api: ApiHelper, seed_data: dict):
        """Create a requirement (triggers audit), list logs, verify pagination format."""
        pid = seed_data["project"]["id"]
        iid = seed_data["iteration"]["id"]

        # Create a requirement to generate an audit log entry
        api.create_requirement(project_id=pid, iteration_id=iid, title="Audit Test Req")

        # List all audit logs
        result = api.list_audit_logs()

        # Verify pagination envelope
        assert "items" in result
        assert "total" in result
        assert "page" in result
        assert "page_size" in result
        assert "total_pages" in result
        assert isinstance(result["items"], list)
        assert result["total"] >= 1

    # -- 2. Filter audit logs by resource_type --------------------------------

    def test_filter_audit_by_resource_type(self, api: ApiHelper, seed_data: dict):
        """Create a requirement, filter logs by resource_type=requirement, verify."""
        pid = seed_data["project"]["id"]
        iid = seed_data["iteration"]["id"]

        api.create_requirement(
            project_id=pid, iteration_id=iid, title="Filter by Type Req"
        )

        result = api.list_audit_logs(resource_type="requirement")

        assert isinstance(result["items"], list)
        assert result["total"] >= 1

        # Every item should be for a requirement resource
        for item in result["items"]:
            assert item["resource_type"] == "requirement"

    # -- 3. Filter audit logs by action ---------------------------------------

    def test_filter_audit_by_action(self, api: ApiHelper, seed_data: dict):
        """Filter logs by action=requirement.create, verify all entries match."""
        pid = seed_data["project"]["id"]
        iid = seed_data["iteration"]["id"]

        api.create_requirement(
            project_id=pid, iteration_id=iid, title="Filter by Action Req"
        )

        result = api.list_audit_logs(action="requirement.create")

        assert isinstance(result["items"], list)
        assert result["total"] >= 1

        # Every item should have action requirement.create
        for item in result["items"]:
            assert item["action"] == "requirement.create"

    # -- 4. Get individual audit log ------------------------------------------

    def test_get_audit_log(self, api: ApiHelper, seed_data: dict):
        """Get a specific log by ID from the list, verify its fields."""
        pid = seed_data["project"]["id"]
        iid = seed_data["iteration"]["id"]

        api.create_requirement(
            project_id=pid, iteration_id=iid, title="Get Log Req"
        )

        # Find the log entry for this creation
        result = api.list_audit_logs(action="requirement.create")
        assert result["total"] >= 1
        log_entry = result["items"][-1]
        log_id = log_entry["id"]

        # Fetch the individual log
        resp = api.get_audit_log(log_id)
        assert resp.status_code == 200

        log = resp.json()
        assert log["id"] == log_id
        assert log["action"] == "requirement.create"
        assert log["resource_type"] == "requirement"
        assert "resource_id" in log
        assert "user_id" in log
        assert "created_at" in log
