"""
End-to-end integration tests for the org-dev platform.

Tests the full spec-driven workflow via API + basic UI smoke tests.

Run:  python -m pytest tests/test_integration.py -v -s
"""

import time

import pytest
import requests

API = "http://localhost:8000"
BASE = "http://localhost:3000"
LOGIN = {"username": "admin", "password": "admin123"}


def ok(status: int, label: str = ""):
    assert 200 <= status < 300, f"{label}: expected 2xx, got {status}"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def auth_headers():
    r = requests.post(f"{API}/api/auth/login", json=LOGIN)
    ok(r.status_code, "login")
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def seeded(auth_headers):
    """Create org → team → project → iteration."""
    ts = int(time.time() * 1000)
    h = auth_headers

    r = requests.post(f"{API}/api/organizations",
        json={"name": f"TOrg{ts}", "slug": f"t-org-{ts}"}, headers=h)
    ok(r.status_code, "org")
    org = r.json()

    r = requests.post(f"{API}/api/teams",
        json={"org_id": org["id"], "name": f"TTeam{ts}", "slug": f"t-team-{ts}"}, headers=h)
    ok(r.status_code, "team")
    team = r.json()

    r = requests.post(f"{API}/api/projects",
        json={"team_id": team["id"], "name": f"TProj{ts}", "slug": f"t-proj-{ts}"}, headers=h)
    ok(r.status_code, "project")
    project = r.json()

    r = requests.post(f"{API}/api/projects/{project['id']}/iterations",
        json={"project_id": project["id"], "name": "Sprint 1"}, headers=h)
    ok(r.status_code, "iteration")

    return {
        "h": h,
        "org": org, "team": team, "project": project,
        "iteration": r.json(),
    }


# ===========================================================================
# 1. Full API workflow
# ===========================================================================

class TestFullAPIWorkflow:
    def test_complete_flow(self, seeded):
        h = seeded["h"]
        pid = seeded["project"]["id"]
        iid = seeded["iteration"]["id"]
        uid = "00000000-0000-0000-0000-000000000001"  # creator_id placeholder

        # ── Requirement (draft) ──
        r = requests.post(f"{API}/api/projects/{pid}/requirements",
            json={"iteration_id": iid, "title": "User Login", "priority": "high",
                  "creator_id": uid},
            headers=h)
        ok(r.status_code, "create req")
        req = r.json()
        rid = req["id"]
        assert req["status"] == "draft"

        # ── Spec Writing ──
        r = requests.patch(f"{API}/api/requirements/{rid}/status",
            json={"status": "spec_writing"}, headers=h)
        ok(r.status_code, "→ spec_writing")

        # Specification
        r = requests.post(f"{API}/api/requirements/{rid}/specifications",
            json={"requirement_id": rid, "spec_type": "api", "title": "Login API"}, headers=h)
        ok(r.status_code, "create spec")
        spec = r.json()

        # Version
        r = requests.post(f"{API}/api/specifications/{spec['id']}/versions",
            json={"spec_id": spec["id"], "version": 1, "content": {"endpoints": [{"path": "/login", "method": "POST"}]}},
            headers=h)
        ok(r.status_code, "create version")
        ver = r.json()
        assert ver["version"] == 1
        assert ver["status"] == "draft"

        # Clauses
        r = requests.post(f"{API}/api/spec-versions/{ver['id']}/clauses", json={
            "spec_version_id": ver["id"], "clause_id": "API-001",
            "title": "Login endpoint", "description": "POST /login returns JWT",
            "category": "functional", "severity": "must",
        }, headers=h)
        ok(r.status_code, "clause must")
        c_must = r.json()

        r = requests.post(f"{API}/api/spec-versions/{ver['id']}/clauses", json={
            "spec_version_id": ver["id"], "clause_id": "API-002",
            "title": "Rate limiting", "description": "Max 5 attempts/min",
            "category": "security", "severity": "should",
        }, headers=h)
        ok(r.status_code, "clause should")
        c_should = r.json()

        # List clauses
        r = requests.get(f"{API}/api/spec-versions/{ver['id']}/clauses", headers=h)
        ok(r.status_code, "list clauses")
        assert len(r.json()) == 2

        # ── Spec Review → Lock ──
        r = requests.patch(f"{API}/api/requirements/{rid}/status",
            json={"status": "spec_review"}, headers=h)
        ok(r.status_code, "→ spec_review")

        r = requests.patch(f"{API}/api/spec-versions/{ver['id']}/submit", headers=h)
        ok(r.status_code, "submit")
        assert r.json()["status"] == "reviewing"

        r = requests.patch(f"{API}/api/spec-versions/{ver['id']}/lock", headers=h)
        ok(r.status_code, "lock")
        assert r.json()["status"] == "locked"

        # Verify requirement auto-transitioned to spec_locked
        r = requests.get(f"{API}/api/requirements/{rid}", headers=h)
        assert r.json()["status"] == "spec_locked"

        # ── Dev Task ──
        r = requests.post(f"{API}/api/requirements/{rid}/dev-tasks", json={
            "requirement_id": rid, "spec_version_id": ver["id"],
            "iteration_id": iid, "title": "Implement login", "estimate_hours": 4.0,
        }, headers=h)
        ok(r.status_code, "create dev task")
        dt = r.json()
        assert dt["status"] == "open"

        r = requests.patch(f"{API}/api/dev-tasks/{dt['id']}/claim", headers=h)
        ok(r.status_code, "claim")
        assert r.json()["status"] == "in_progress"

        r = requests.patch(f"{API}/api/dev-tasks/{dt['id']}/status",
            json={"status": "review"}, headers=h)
        ok(r.status_code, "→ review")

        r = requests.patch(f"{API}/api/dev-tasks/{dt['id']}/status",
            json={"status": "done"}, headers=h)
        ok(r.status_code, "→ done")

        # ── Test Task + Test Case ──
        r = requests.post(f"{API}/api/requirements/{rid}/test-tasks", json={
            "requirement_id": rid, "iteration_id": iid, "title": "Test login",
        }, headers=h)
        ok(r.status_code, "create test task")
        tt = r.json()

        r = requests.post(f"{API}/api/test-tasks/{tt['id']}/test-cases", json={
            "title": "Verify login + rate limit",
            "steps": "1. POST /login\n2. Check rate limit",
            "expected_result": "200 OK + 429 after 5 tries",
            "clause_ids": [c_must["id"], c_should["id"]],
        }, headers=h)
        ok(r.status_code, "create test case")
        tc = r.json()
        assert tc["status"] == "pending"

        # Run test case
        r = requests.patch(f"{API}/api/test-cases/{tc['id']}/status",
            json={"status": "running"}, headers=h)
        ok(r.status_code, "tc → running")

        r = requests.patch(f"{API}/api/test-cases/{tc['id']}/status",
            json={"status": "passed"}, headers=h)
        ok(r.status_code, "tc → passed")

        # ── Coverage ──
        r = requests.get(f"{API}/api/requirements/{rid}/coverage", headers=h)
        ok(r.status_code, "coverage")
        cov = r.json()
        assert cov["total_clauses"] == 2
        assert cov["covered_clauses"] == 2
        assert cov["must_coverage_pct"] == 100.0

        r = requests.get(f"{API}/api/requirements/{rid}/coverage/check", headers=h)
        ok(r.status_code, "coverage check")
        assert r.json()["sufficient"] is True

        # ── Complete workflow ──
        r = requests.patch(f"{API}/api/requirements/{rid}/status",
            json={"status": "in_progress"}, headers=h)
        ok(r.status_code, "→ in_progress")

        r = requests.patch(f"{API}/api/requirements/{rid}/status",
            json={"status": "testing"}, headers=h)
        ok(r.status_code, "→ testing")

        r = requests.patch(f"{API}/api/requirements/{rid}/status",
            json={"status": "done"}, headers=h)
        ok(r.status_code, "→ done")
        assert r.json()["status"] == "done"

        # ── Verify lists ──
        r = requests.get(f"{API}/api/projects/{pid}/dev-tasks", headers=h)
        ok(r.status_code, "list dev tasks")
        assert len(r.json()) >= 1

        r = requests.get(f"{API}/api/projects/{pid}/test-tasks", headers=h)
        ok(r.status_code, "list test tasks")
        assert len(r.json()) >= 1

        print("\n✅ Full workflow: draft → spec_writing → spec_review → spec_locked → in_progress → testing → done")

    def test_coverage_gate_blocks_done(self, seeded):
        """Insufficient coverage prevents done."""
        h = seeded["h"]
        pid = seeded["project"]["id"]
        iid = seeded["iteration"]["id"]
        uid = "00000000-0000-0000-0000-000000000001"

        # Quick setup: req → spec → lock → testing
        r = requests.post(f"{API}/api/projects/{pid}/requirements",
            json={"iteration_id": iid, "title": "Blocked", "priority": "medium",
                  "creator_id": uid}, headers=h)
        rid = r.json()["id"]

        requests.patch(f"{API}/api/requirements/{rid}/status",
            json={"status": "spec_writing"}, headers=h)
        r = requests.post(f"{API}/api/requirements/{rid}/specifications",
            json={"requirement_id": rid, "spec_type": "api", "title": "S"}, headers=h)
        spec = r.json()
        r = requests.post(f"{API}/api/specifications/{spec['id']}/versions",
            json={"spec_id": spec["id"], "content": {}}, headers=h)
        ver = r.json()
        requests.post(f"{API}/api/spec-versions/{ver['id']}/clauses", json={
            "spec_version_id": ver["id"], "clause_id": "X-001",
            "title": "Must", "description": "d", "category": "functional", "severity": "must",
        }, headers=h)

        requests.patch(f"{API}/api/requirements/{rid}/status",
            json={"status": "spec_review"}, headers=h)
        requests.patch(f"{API}/api/spec-versions/{ver['id']}/submit", headers=h)
        requests.patch(f"{API}/api/spec-versions/{ver['id']}/lock", headers=h)
        requests.patch(f"{API}/api/requirements/{rid}/status",
            json={"status": "in_progress"}, headers=h)
        requests.patch(f"{API}/api/requirements/{rid}/status",
            json={"status": "testing"}, headers=h)

        # No test cases → should fail
        r = requests.patch(f"{API}/api/requirements/{rid}/status",
            json={"status": "done"}, headers=h)
        assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text}"

        print("\n✅ Coverage gate: done blocked when must=0%")

    def test_dev_task_requires_locked_spec(self, seeded):
        """Dev task creation fails without locked spec."""
        h = seeded["h"]
        pid = seeded["project"]["id"]
        iid = seeded["iteration"]["id"]
        uid = "00000000-0000-0000-0000-000000000001"

        r = requests.post(f"{API}/api/projects/{pid}/requirements",
            json={"iteration_id": iid, "title": "NoLock", "priority": "medium",
                  "creator_id": uid}, headers=h)
        rid = r.json()["id"]

        # Still draft → dev task should fail
        r = requests.post(f"{API}/api/requirements/{rid}/dev-tasks", json={
            "requirement_id": rid, "spec_version_id": "fake-id",
            "iteration_id": iid, "title": "Should fail",
        }, headers=h)
        assert r.status_code in (400, 403, 422), f"Expected error, got {r.status_code}"

        print("\n✅ Dev task gate: blocked without locked spec")


# ===========================================================================
# 2. UI Smoke Tests (Playwright)
# ===========================================================================

@pytest.fixture(scope="session")
def browser_context(playwright):
    browser = playwright.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1280, "height": 720})
    yield ctx
    ctx.close()
    browser.close()


@pytest.fixture()
def page(browser_context):
    p = browser_context.new_page()
    yield p
    p.close()


def _login(page):
    page.goto(f"{BASE}/login")
    page.fill('input[id="username"]', "admin")
    page.fill('input[id="password"]', "admin123")
    page.click('button[type="submit"]')
    page.wait_for_url("**/**", timeout=10000)


class TestUISmoke:
    def test_login_page_loads(self, page):
        page.goto(f"{BASE}/login")
        page.wait_for_load_state("networkidle")
        assert page.locator('input[id="username"]').is_visible()
        assert page.locator('button[type="submit"]').is_visible()
        print("✅ Login page loads")

    def test_login_success(self, page):
        # Register a user via API first so we have known credentials
        from helpers.api import ApiHelper
        api = ApiHelper()
        password = "Test1234!"
        username = ApiHelper._unique("smoke")
        api.register(username=username, password=password)

        page.goto(f"{BASE}/login")
        page.wait_for_load_state("networkidle")
        page.fill('input[id="username"]', username)
        page.fill('input[id="password"]', password)
        page.click('button[type="submit"]')
        page.wait_for_url(lambda url: "/login" not in url, timeout=10000)
        assert "/login" not in page.url
        print("✅ Login → dashboard")

    def test_login_failure(self, page):
        page.goto(f"{BASE}/login")
        page.fill('input[id="username"]', "wrong")
        page.fill('input[id="password"]', "wrong")
        page.click('button[type="submit"]')
        page.wait_for_timeout(2000)
        assert page.locator("text=Invalid").is_visible() or page.locator(".bg-red-50").is_visible()
        assert "/login" in page.url
        print("✅ Login failure shows error")

    def test_dashboard_nav(self, page):
        _login(page)
        page.wait_for_load_state("networkidle")
        assert page.locator('a:has-text("Dashboard")').is_visible()
        assert page.locator('a:has-text("Projects")').is_visible()
        assert page.locator('a:has-text("Teams")').is_visible()
        print("✅ Dashboard nav visible")

    def test_projects_page(self, page):
        _login(page)
        page.click('a:has-text("Projects")')
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        assert "Project" in page.locator("body").inner_text()
        print("✅ Projects page loads")

    def test_logout(self, page):
        _login(page)
        page.click('button:has-text("Logout")')
        page.wait_for_timeout(2000)
        assert "/login" in page.url
        print("✅ Logout → login page")
