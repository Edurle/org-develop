"""
End-to-end tests for the auth module.

Covers registration, login, token refresh, API key CRUD, and login page UI.

Run:  python -m pytest tests/test_auth.py -v -s
"""

import pytest
import requests

from helpers.api import ApiHelper

API = "http://localhost:8000"
BASE = "http://localhost:3000"


# ===========================================================================
# 1. Registration tests
# ===========================================================================


class TestRegister:
    def test_register_success(self):
        """Register a new user and verify tokens are returned."""
        api = ApiHelper()
        data = api.register()

        assert "access_token" in data
        assert "refresh_token" in data
        assert isinstance(data["access_token"], str)
        assert isinstance(data["refresh_token"], str)
        assert len(data["access_token"]) > 0
        assert len(data["refresh_token"]) > 0

    def test_register_duplicate_username(self):
        """Registering the same username twice should return 409."""
        api = ApiHelper()
        username = ApiHelper._unique("dup")
        api.register(username=username, email=f"{username}@test.com")

        # Second registration with the same username via raw request
        r = requests.post(
            f"{API}/api/auth/register",
            json={
                "username": username,
                "email": f"{username}-alt@test.com",
                "password": "Test1234!",
            },
        )
        assert r.status_code == 409


# ===========================================================================
# 2. Login tests
# ===========================================================================


class TestLogin:
    def test_login_success(self):
        """Login with valid credentials returns access and refresh tokens."""
        api = ApiHelper()
        password = "Test1234!"
        username = ApiHelper._unique("login")
        api.register(username=username, password=password)

        # Use a fresh session to avoid cached auth
        fresh = ApiHelper()
        data = fresh.login(username, password)

        assert "access_token" in data
        assert "refresh_token" in data
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0

    def test_login_wrong_password(self):
        """Login with wrong password returns 401."""
        api = ApiHelper()
        username = ApiHelper._unique("badpw")
        api.register(username=username)

        r = requests.post(
            f"{API}/api/auth/login",
            json={"username": username, "password": "WrongPassword!1"},
        )
        assert r.status_code == 401


# ===========================================================================
# 3. Token refresh tests
# ===========================================================================


class TestRefreshToken:
    def test_refresh_token(self):
        """Use a refresh token to obtain new tokens."""
        api = ApiHelper()
        data = api.register()
        old_refresh = data["refresh_token"]

        fresh = ApiHelper()
        new_data = fresh.refresh_token(old_refresh)

        assert "access_token" in new_data
        assert "refresh_token" in new_data
        # The new tokens should be non-empty strings
        assert isinstance(new_data["access_token"], str)
        assert isinstance(new_data["refresh_token"], str)
        assert len(new_data["access_token"]) > 0


# ===========================================================================
# 4. API key tests
# ===========================================================================


class TestApiKeys:
    def test_create_api_key(self, api: ApiHelper):
        """Create an API key and verify its structure."""
        scopes = ["requirements:read", "tasks:write"]
        data = api.create_api_key(name="test-key", scopes=scopes)

        assert data["key"].startswith("odk_")
        assert data["scopes"] == scopes
        assert data["name"] == "test-key"
        assert data["is_active"] is True
        assert "id" in data
        assert "key_prefix" in data

    def test_delete_api_key(self, api: ApiHelper):
        """Create then delete an API key; expect 204."""
        scopes = ["requirements:read"]
        data = api.create_api_key(name="delete-me", scopes=scopes)
        key_id = data["id"]

        status_code = api.delete_api_key(key_id)
        assert status_code == 204


# ===========================================================================
# 5. Login page UI tests (Playwright)
# ===========================================================================


class TestLoginPageUI:
    def test_login_page_ui(self, page):
        """
        Full login page UI flow:
        1. Load login page
        2. Fill wrong credentials, submit, see error message
        3. Fill correct credentials, submit, redirect to dashboard
        """
        # Register a user via API so we have known credentials
        api = ApiHelper()
        password = "Test1234!"
        username = ApiHelper._unique("ui")
        api.register(username=username, password=password)

        # Step 1: Load the login page
        page.goto(f"{BASE}/login")
        page.wait_for_load_state("networkidle")

        # Verify form is visible
        assert page.locator('input[id="username"]').is_visible()
        assert page.locator('input[id="password"]').is_visible()
        assert page.locator('button[type="submit"]').is_visible()

        # Step 2: Fill wrong credentials and submit
        page.fill('input[id="username"]', username)
        page.fill('input[id="password"]', "WrongPassword!1")
        page.click('button[type="submit"]')

        # Wait for error message to appear
        error_div = page.locator("div.bg-red-500\\/10")
        error_div.wait_for(state="visible", timeout=10000)

        # Verify we are still on the login page
        assert "/login" in page.url

        # Step 3: Fill correct credentials and submit
        page.fill('input[id="username"]', username)
        page.fill('input[id="password"]', password)
        page.click('button[type="submit"]')

        # Wait for redirect away from login page
        page.wait_for_url("**/dashboard**", timeout=10000)
        assert "/login" not in page.url
