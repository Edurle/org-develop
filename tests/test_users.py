"""
End-to-end tests for the users module.

Covers GET /api/users/me, PATCH /api/users/me, GET /api/users/{user_id}.

Run:  python -m pytest tests/test_users.py -v -s
"""

import uuid

import pytest

from helpers.api import ApiHelper


class TestUsers:
    """E2E tests for user endpoints."""

    def test_get_me(self, api: ApiHelper):
        """GET /api/users/me returns the authenticated user's info."""
        me = api.get_me()

        # Verify required fields are present
        assert "id" in me
        assert "username" in me
        assert "email" in me
        assert "is_active" in me
        assert "created_at" in me
        assert "updated_at" in me

        # Values should be non-empty
        assert me["id"]
        assert me["username"]
        assert me["email"]

        # id should match the one decoded from JWT during registration
        assert me["id"] == api.user_id

    def test_update_me(self, api: ApiHelper):
        """PATCH /api/users/me updates display_name and email."""
        new_name = "Updated Display Name"
        new_email = f"updated-{uuid.uuid4().hex[:8]}@test.com"

        updated = api.update_me(display_name=new_name, email=new_email)

        assert updated["display_name"] == new_name
        assert updated["email"] == new_email

        # Verify persistence via GET /me
        me = api.get_me()
        assert me["display_name"] == new_name
        assert me["email"] == new_email

    def test_get_user_by_id(self, api: ApiHelper):
        """GET /api/users/{user_id} returns the correct user."""
        me = api.get_me()
        user_id = me["id"]

        resp = api.get_user(user_id)
        assert resp.status_code == 200

        user = resp.json()
        assert user["id"] == me["id"]
        assert user["username"] == me["username"]
        assert user["email"] == me["email"]

    def test_get_user_not_found(self, api: ApiHelper):
        """GET /api/users/{user_id} returns 404 for a non-existent UUID."""
        fake_id = str(uuid.uuid4())
        resp = api.get_user(fake_id)
        assert resp.status_code == 404
