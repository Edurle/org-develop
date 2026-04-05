"""
API request wrapper for e2e tests.

Provides typed methods for all 58 backend endpoints.
Each ApiHelper instance carries its own auth token (isolated per test).
"""

import time
import uuid
from typing import Any

import requests


class ApiHelper:
    """Stateless HTTP client with auth for the org-dev backend."""

    BASE = "http://localhost:8000"

    def __init__(self) -> None:
        self.s = requests.Session()
        self._user_id: str | None = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _url(self, path: str) -> str:
        return f"{self.BASE}{path}"

    def _headers(self) -> dict[str, str]:
        token = self.s.headers.get("Authorization")
        if token:
            return {"Authorization": token}
        return {}

    def _set_token(self, access_token: str) -> None:
        self.s.headers["Authorization"] = f"Bearer {access_token}"

    @property
    def user_id(self) -> str:
        assert self._user_id, "Not authenticated"
        return self._user_id

    @staticmethod
    def _unique(prefix: str = "t") -> str:
        return f"{prefix}-{uuid.uuid4().hex[:8]}"

    @staticmethod
    def _ts() -> int:
        return int(time.time() * 1000)

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def register(
        self,
        username: str | None = None,
        email: str | None = None,
        password: str = "Test1234!",
        display_name: str | None = None,
    ) -> dict:
        ts = self._ts()
        body = {
            "username": username or f"user-{ts}",
            "email": email or f"user-{ts}@test.com",
            "password": password,
            "display_name": display_name,
        }
        r = self.s.post(self._url("/api/auth/register"), json=body)
        assert r.status_code == 201, f"register failed: {r.status_code} {r.text}"
        data = r.json()
        self._set_token(data["access_token"])
        # Decode JWT to get user_id (sub claim)
        import base64, json as _json

        payload = data["access_token"].split(".")[1]
        payload += "=" * (4 - len(payload) % 4)
        claims = _json.loads(base64.urlsafe_b64decode(payload))
        self._user_id = claims["sub"]
        return data

    def login(self, username: str, password: str) -> dict:
        r = self.s.post(
            self._url("/api/auth/login"),
            json={"username": username, "password": password},
        )
        r.raise_for_status()
        data = r.json()
        self._set_token(data["access_token"])
        return data

    def refresh_token(self, refresh_token: str) -> dict:
        r = self.s.post(
            self._url("/api/auth/refresh"),
            json={"refresh_token": refresh_token},
        )
        r.raise_for_status()
        data = r.json()
        self._set_token(data["access_token"])
        return data

    def create_api_key(self, name: str, scopes: list[str]) -> dict:
        r = self.s.post(
            self._url("/api/auth/api-keys"),
            json={"name": name, "scopes": scopes},
        )
        r.raise_for_status()
        return r.json()

    def delete_api_key(self, key_id: str) -> int:
        r = self.s.delete(self._url(f"/api/auth/api-keys/{key_id}"))
        return r.status_code

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def get_me(self) -> dict:
        r = self.s.get(self._url("/api/users/me"))
        r.raise_for_status()
        return r.json()

    def update_me(self, **fields) -> dict:
        r = self.s.patch(self._url("/api/users/me"), json=fields)
        r.raise_for_status()
        return r.json()

    def get_user(self, user_id: str) -> requests.Response:
        return self.s.get(self._url(f"/api/users/{user_id}"))

    # ------------------------------------------------------------------
    # Organizations
    # ------------------------------------------------------------------

    def create_org(self, name: str | None = None, slug: str | None = None) -> dict:
        ts = self._ts()
        n = name or f"Org{ts}"
        r = self.s.post(
            self._url("/api/organizations"),
            json={"name": n, "slug": slug or f"org-{ts}"},
        )
        assert r.status_code == 201, f"create_org: {r.status_code} {r.text}"
        return r.json()

    def list_orgs(self) -> list:
        r = self.s.get(self._url("/api/organizations"))
        r.raise_for_status()
        return r.json()

    # ------------------------------------------------------------------
    # Teams
    # ------------------------------------------------------------------

    def create_team(
        self, org_id: str, name: str | None = None, slug: str | None = None
    ) -> dict:
        ts = self._ts()
        n = name or f"Team{ts}"
        r = self.s.post(
            self._url("/api/teams"),
            json={"org_id": org_id, "name": n, "slug": slug or f"team-{ts}"},
        )
        assert r.status_code == 201, f"create_team: {r.status_code} {r.text}"
        return r.json()

    def list_teams(self) -> list:
        r = self.s.get(self._url("/api/teams"))
        r.raise_for_status()
        return r.json()

    def add_team_member(self, team_id: str, user_id: str, roles: str = "developer") -> dict:
        r = self.s.post(
            self._url(f"/api/teams/{team_id}/members"),
            json={"user_id": user_id, "roles": roles},
        )
        r.raise_for_status()
        return r.json()

    def list_team_members(self, team_id: str) -> list:
        r = self.s.get(self._url(f"/api/teams/{team_id}/members"))
        r.raise_for_status()
        return r.json()

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------

    def create_project(
        self,
        team_id: str,
        name: str | None = None,
        slug: str | None = None,
        description: str | None = None,
    ) -> dict:
        ts = self._ts()
        n = name or f"Proj{ts}"
        r = self.s.post(
            self._url("/api/projects"),
            json={
                "team_id": team_id,
                "name": n,
                "slug": slug or f"proj-{ts}",
                "description": description,
            },
        )
        assert r.status_code == 201, f"create_project: {r.status_code} {r.text}"
        return r.json()

    def list_projects(self, team_id: str | None = None) -> list:
        params = {}
        if team_id:
            params["team_id"] = team_id
        r = self.s.get(self._url("/api/projects"), params=params)
        r.raise_for_status()
        return r.json()

    def get_project(self, project_id: str) -> dict:
        r = self.s.get(self._url(f"/api/projects/{project_id}"))
        r.raise_for_status()
        return r.json()

    def update_project(self, project_id: str, **fields) -> dict:
        r = self.s.patch(self._url(f"/api/projects/{project_id}"), json=fields)
        r.raise_for_status()
        return r.json()

    def delete_project(self, project_id: str) -> int:
        r = self.s.delete(self._url(f"/api/projects/{project_id}"))
        return r.status_code

    # ------------------------------------------------------------------
    # Iterations
    # ------------------------------------------------------------------

    def create_iteration(
        self, project_id: str, name: str = "Sprint 1", **fields
    ) -> dict:
        body: dict[str, Any] = {"name": name}
        body.update(fields)
        r = self.s.post(
            self._url(f"/api/projects/{project_id}/iterations"), json=body
        )
        assert r.status_code == 201, f"create_iteration: {r.status_code} {r.text}"
        return r.json()

    def list_iterations(self, project_id: str) -> list:
        r = self.s.get(self._url(f"/api/projects/{project_id}/iterations"))
        r.raise_for_status()
        return r.json()

    def update_iteration(
        self, project_id: str, iteration_id: str, **fields
    ) -> dict:
        r = self.s.patch(
            self._url(f"/api/projects/{project_id}/iterations/{iteration_id}"),
            json=fields,
        )
        r.raise_for_status()
        return r.json()

    # ------------------------------------------------------------------
    # Requirements
    # ------------------------------------------------------------------

    def create_requirement(
        self,
        project_id: str,
        iteration_id: str,
        title: str = "Test Requirement",
        priority: str = "medium",
    ) -> dict:
        r = self.s.post(
            self._url(f"/api/projects/{project_id}/requirements"),
            json={"iteration_id": iteration_id, "title": title, "priority": priority},
        )
        assert r.status_code == 201, f"create_req: {r.status_code} {r.text}"
        return r.json()

    def list_requirements(self, project_id: str, **filters) -> list:
        r = self.s.get(
            self._url(f"/api/projects/{project_id}/requirements"), params=filters
        )
        r.raise_for_status()
        return r.json()

    def get_requirement(self, requirement_id: str) -> dict:
        r = self.s.get(self._url(f"/api/requirements/{requirement_id}"))
        r.raise_for_status()
        return r.json()

    def update_requirement(self, requirement_id: str, **fields) -> dict:
        r = self.s.patch(
            self._url(f"/api/requirements/{requirement_id}"), json=fields
        )
        r.raise_for_status()
        return r.json()

    def update_requirement_status(self, requirement_id: str, status: str) -> requests.Response:
        return self.s.patch(
            self._url(f"/api/requirements/{requirement_id}/status"),
            json={"status": status},
        )

    # ------------------------------------------------------------------
    # Specifications
    # ------------------------------------------------------------------

    def create_specification(
        self, requirement_id: str, spec_type: str = "api", title: str = "Test Spec"
    ) -> dict:
        r = self.s.post(
            self._url(f"/api/requirements/{requirement_id}/specifications"),
            json={"spec_type": spec_type, "title": title},
        )
        assert r.status_code == 201, f"create_spec: {r.status_code} {r.text}"
        return r.json()

    def list_specifications(self, requirement_id: str) -> list:
        r = self.s.get(
            self._url(f"/api/requirements/{requirement_id}/specifications")
        )
        r.raise_for_status()
        return r.json()

    def create_spec_version(
        self, spec_id: str, content: dict | None = None
    ) -> dict:
        r = self.s.post(
            self._url(f"/api/specifications/{spec_id}/versions"),
            json={"content": content or {}},
        )
        assert r.status_code == 201, f"create_ver: {r.status_code} {r.text}"
        return r.json()

    def list_spec_versions(self, spec_id: str) -> list:
        r = self.s.get(self._url(f"/api/specifications/{spec_id}/versions"))
        r.raise_for_status()
        return r.json()

    def submit_spec_version(self, version_id: str) -> requests.Response:
        return self.s.patch(self._url(f"/api/spec-versions/{version_id}/submit"))

    def lock_spec_version(self, version_id: str) -> requests.Response:
        return self.s.patch(self._url(f"/api/spec-versions/{version_id}/lock"))

    def reject_spec_version(self, version_id: str) -> requests.Response:
        return self.s.patch(self._url(f"/api/spec-versions/{version_id}/reject"))

    # ------------------------------------------------------------------
    # Clauses
    # ------------------------------------------------------------------

    def create_clause(
        self,
        version_id: str,
        clause_id: str,
        title: str,
        description: str,
        category: str = "functional",
        severity: str = "must",
    ) -> dict:
        r = self.s.post(
            self._url(f"/api/spec-versions/{version_id}/clauses"),
            json={
                "clause_id": clause_id,
                "title": title,
                "description": description,
                "category": category,
                "severity": severity,
            },
        )
        assert r.status_code == 201, f"create_clause: {r.status_code} {r.text}"
        return r.json()

    def list_clauses(self, version_id: str) -> list:
        r = self.s.get(self._url(f"/api/spec-versions/{version_id}/clauses"))
        r.raise_for_status()
        return r.json()

    # ------------------------------------------------------------------
    # Dev Tasks
    # ------------------------------------------------------------------

    def create_dev_task(
        self,
        requirement_id: str,
        spec_version_id: str,
        iteration_id: str,
        title: str = "Test Dev Task",
        estimate_hours: float | None = None,
    ) -> requests.Response:
        body: dict[str, Any] = {
            "spec_version_id": spec_version_id,
            "iteration_id": iteration_id,
            "title": title,
        }
        if estimate_hours is not None:
            body["estimate_hours"] = estimate_hours
        return self.s.post(
            self._url(f"/api/requirements/{requirement_id}/dev-tasks"), json=body
        )

    def list_dev_tasks(self, project_id: str) -> list:
        r = self.s.get(self._url(f"/api/projects/{project_id}/dev-tasks"))
        r.raise_for_status()
        return r.json()

    def claim_dev_task(self, task_id: str) -> requests.Response:
        return self.s.patch(self._url(f"/api/dev-tasks/{task_id}/claim"))

    def update_dev_task_status(self, task_id: str, status: str) -> requests.Response:
        return self.s.patch(
            self._url(f"/api/dev-tasks/{task_id}/status"), json={"status": status}
        )

    # ------------------------------------------------------------------
    # Test Tasks
    # ------------------------------------------------------------------

    def create_test_task(
        self,
        requirement_id: str,
        iteration_id: str,
        title: str = "Test Test Task",
    ) -> requests.Response:
        return self.s.post(
            self._url(f"/api/requirements/{requirement_id}/test-tasks"),
            json={"iteration_id": iteration_id, "title": title},
        )

    def list_test_tasks(self, project_id: str) -> list:
        r = self.s.get(self._url(f"/api/projects/{project_id}/test-tasks"))
        r.raise_for_status()
        return r.json()

    # ------------------------------------------------------------------
    # Test Cases
    # ------------------------------------------------------------------

    def create_test_case(
        self,
        test_task_id: str,
        title: str = "TC1",
        steps: str = "Step 1",
        expected_result: str = "Pass",
        clause_ids: list[str] | None = None,
    ) -> requests.Response:
        body: dict[str, Any] = {
            "title": title,
            "steps": steps,
            "expected_result": expected_result,
        }
        if clause_ids:
            body["clause_ids"] = clause_ids
        return self.s.post(
            self._url(f"/api/test-tasks/{test_task_id}/test-cases"), json=body
        )

    def list_test_cases(self, test_task_id: str) -> list:
        r = self.s.get(self._url(f"/api/test-tasks/{test_task_id}/test-cases"))
        r.raise_for_status()
        return r.json()

    def update_test_case_status(self, test_case_id: str, status: str) -> requests.Response:
        return self.s.patch(
            self._url(f"/api/test-cases/{test_case_id}/status"), json={"status": status}
        )

    # ------------------------------------------------------------------
    # Coverage
    # ------------------------------------------------------------------

    def get_coverage(self, requirement_id: str) -> dict:
        r = self.s.get(self._url(f"/api/requirements/{requirement_id}/coverage"))
        r.raise_for_status()
        return r.json()

    def check_coverage(self, requirement_id: str) -> dict:
        r = self.s.get(self._url(f"/api/requirements/{requirement_id}/coverage/check"))
        r.raise_for_status()
        return r.json()

    # ------------------------------------------------------------------
    # Webhooks
    # ------------------------------------------------------------------

    def create_webhook(
        self,
        project_id: str,
        url: str = "https://example.com/hook",
        events: list[str] | None = None,
        secret: str | None = None,
    ) -> dict:
        body: dict[str, Any] = {
            "url": url,
            "events": events or ["requirement.created"],
        }
        if secret:
            body["secret"] = secret
        r = self.s.post(
            self._url(f"/api/projects/{project_id}/webhooks"), json=body
        )
        assert r.status_code == 201, f"create_webhook: {r.status_code} {r.text}"
        return r.json()

    def list_webhooks(self, project_id: str) -> list:
        r = self.s.get(self._url(f"/api/projects/{project_id}/webhooks"))
        r.raise_for_status()
        return r.json()

    def delete_webhook(self, project_id: str, webhook_id: str) -> int:
        r = self.s.delete(
            self._url(f"/api/projects/{project_id}/webhooks/{webhook_id}")
        )
        return r.status_code

    def list_webhook_deliveries(self, webhook_id: str) -> list:
        r = self.s.get(self._url(f"/api/webhooks/{webhook_id}/deliveries"))
        r.raise_for_status()
        return r.json()

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------

    def list_audit_logs(self, **filters) -> dict:
        r = self.s.get(self._url("/api/audit/logs"), params=filters)
        r.raise_for_status()
        return r.json()

    def get_audit_log(self, log_id: str) -> requests.Response:
        return self.s.get(self._url(f"/api/audit/logs/{log_id}"))

    # ------------------------------------------------------------------
    # Convenience: seed full hierarchy
    # ------------------------------------------------------------------

    def seed(self) -> dict:
        """Create org → team → project → iteration and return all ids."""
        org = self.create_org()
        team = self.create_team(org_id=org["id"])
        project = self.create_project(team_id=team["id"])
        iteration = self.create_iteration(project_id=project["id"])
        return {
            "org": org,
            "team": team,
            "project": project,
            "iteration": iteration,
        }

    def seed_requirement_with_spec(self) -> dict:
        """Create a full requirement→spec→version→clause chain (locked)."""
        data = self.seed()
        pid = data["project"]["id"]
        iid = data["iteration"]["id"]

        req = self.create_requirement(project_id=pid, iteration_id=iid)
        rid = req["id"]
        self.update_requirement_status(rid, "spec_writing").raise_for_status()

        spec = self.create_specification(requirement_id=rid)
        ver = self.create_spec_version(spec_id=spec["id"])
        self.create_clause(
            version_id=ver["id"],
            clause_id="TC-001",
            title="Must clause",
            description="desc",
            severity="must",
        )
        self.update_requirement_status(rid, "spec_review").raise_for_status()
        self.submit_spec_version(ver["id"]).raise_for_status()
        self.lock_spec_version(ver["id"]).raise_for_status()
        # Requirement should auto-transition to spec_locked

        data["requirement"] = req
        data["spec"] = spec
        data["version"] = ver
        return data
