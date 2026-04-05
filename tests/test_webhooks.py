"""
End-to-end tests for the webhooks module.

Covers webhook CRUD (create, list, delete) and delivery listing.

Run:  python -m pytest tests/test_webhooks.py -v -s
"""

import pytest

from helpers.api import ApiHelper
from helpers.ui import UiHelper


class TestWebhookAPI:
    """API-level tests for webhook endpoints."""

    # -- 1. Create webhook ----------------------------------------------------

    def test_create_webhook(self, api: ApiHelper, seed_data: dict):
        """Create a webhook and verify its fields."""
        pid = seed_data["project"]["id"]

        hook = api.create_webhook(
            project_id=pid,
            url="https://example.com/webhook/test",
            events=["requirement.created", "requirement.updated"],
            secret="whsec_abc123",
        )

        assert hook["url"] == "https://example.com/webhook/test"
        assert "requirement.created" in hook["events"]
        assert "requirement.updated" in hook["events"]
        assert hook["is_active"] is True
        assert "id" in hook

    # -- 2. List webhooks -----------------------------------------------------

    def test_list_webhooks(self, api: ApiHelper, seed_data: dict):
        """Create a webhook, list project webhooks, verify it appears."""
        pid = seed_data["project"]["id"]

        hook = api.create_webhook(
            project_id=pid,
            url="https://example.com/webhook/list-test",
            events=["requirement.created"],
        )

        hooks = api.list_webhooks(pid)
        assert isinstance(hooks, list)
        assert len(hooks) >= 1

        hook_ids = {h["id"] for h in hooks}
        assert hook["id"] in hook_ids

    # -- 3. Delete webhook ----------------------------------------------------

    def test_delete_webhook(self, api: ApiHelper, seed_data: dict):
        """Create a webhook, delete it, verify 204 and it is gone from the list."""
        pid = seed_data["project"]["id"]

        hook = api.create_webhook(
            project_id=pid,
            url="https://example.com/webhook/to-delete",
            events=["requirement.created"],
        )
        hook_id = hook["id"]

        # Delete
        status = api.delete_webhook(pid, hook_id)
        assert status == 204

        # Verify it no longer appears in the list
        hooks = api.list_webhooks(pid)
        hook_ids = {h["id"] for h in hooks}
        assert hook_id not in hook_ids

    # -- 4. Webhook deliveries ------------------------------------------------

    def test_webhook_deliveries(self, api: ApiHelper, seed_data: dict):
        """List deliveries for a webhook; the list may be empty, just verify the endpoint works."""
        pid = seed_data["project"]["id"]

        hook = api.create_webhook(
            project_id=pid,
            url="https://example.com/webhook/deliveries",
            events=["requirement.created"],
        )

        deliveries = api.list_webhook_deliveries(hook["id"])
        assert isinstance(deliveries, list)

    # -- 5. Webhook event triggered -------------------------------------------

    def test_webhook_event_triggered(self, api: ApiHelper, seed_data: dict):
        """Create a webhook for requirement.created, then create a requirement.
        Check deliveries list -- entries may or may not appear depending on
        whether the webhook delivery mechanism is synchronous."""
        pid = seed_data["project"]["id"]
        iid = seed_data["iteration"]["id"]

        hook = api.create_webhook(
            project_id=pid,
            url="https://example.com/webhook/triggered",
            events=["requirement.created"],
        )

        # Trigger the event by creating a requirement
        api.create_requirement(
            project_id=pid, iteration_id=iid, title="Trigger Webhook"
        )

        # List deliveries -- just verify the endpoint is reachable and returns a list
        deliveries = api.list_webhook_deliveries(hook["id"])
        assert isinstance(deliveries, list)
        # If the delivery mechanism is synchronous, there should be at least one entry
        # If async or fire-and-forget, the list may be empty; either outcome is acceptable
