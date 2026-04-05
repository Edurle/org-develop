"""
Shared fixtures for e2e tests.

Every test gets its own:
- ApiHelper (registered user with fresh JWT)
- seed_data (org → team → project → iteration hierarchy)
- Playwright page (logged in via API token injection)
"""

import pytest
import requests
from playwright.sync_api import Page

from helpers.api import ApiHelper
from helpers.ui import UiHelper

API = "http://localhost:8000"
BASE_URL = "http://localhost:3000"


# ------------------------------------------------------------------
# API fixtures
# ------------------------------------------------------------------


@pytest.fixture()
def api() -> ApiHelper:
    """Fresh ApiHelper with a newly registered user."""
    helper = ApiHelper()
    helper.register()
    return helper


@pytest.fixture()
def seed_data(api: ApiHelper) -> dict:
    """Pre-built org → team → project → iteration hierarchy."""
    return api.seed()


# ------------------------------------------------------------------
# Playwright / UI fixtures
# ------------------------------------------------------------------


@pytest.fixture()
def logged_in_page(page: Page, api: ApiHelper) -> Page:
    """Playwright page with authenticated session (via localStorage token)."""
    # Register + get token
    token = api.s.headers.get("Authorization", "").replace("Bearer ", "")
    # Navigate to frontend and inject token
    page.goto(f"{BASE_URL}/login")
    page.evaluate(f'localStorage.setItem("token", "{token}")')
    page.evaluate(
        'localStorage.setItem("user", JSON.stringify({{"username": "test"}}))'
    )
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    return page


@pytest.fixture()
def ui(logged_in_page: Page) -> UiHelper:
    """UiHelper wrapping an authenticated Playwright page."""
    return UiHelper(logged_in_page)


# ------------------------------------------------------------------
# Health-check (skip all tests if backend/frontend not running)
# ------------------------------------------------------------------


def pytest_collection_modifyitems(config, items):
    """Skip all tests if backend is not reachable."""
    try:
        r = requests.get(f"{API}/docs", timeout=2)
        r.raise_for_status()
    except Exception:
        pytest.skip("Backend not running on localhost:8000", allow_module_level=True)
