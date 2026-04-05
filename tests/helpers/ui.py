"""
Playwright UI interaction wrapper for e2e tests.

Provides reusable methods for navigating, filling forms,
and asserting UI state in the org-dev frontend.
"""

from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:3000"


class UiHelper:
    """Wrapper around a Playwright Page with domain-specific helpers."""

    def __init__(self, page: Page, base_url: str = BASE_URL) -> None:
        self.page = page
        self.base_url = base_url

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def goto_login(self) -> None:
        self.page.goto(f"{self.base_url}/login")
        self.page.wait_for_load_state("networkidle")

    def goto_dashboard(self) -> None:
        self.page.goto(self.base_url)
        self.page.wait_for_load_state("networkidle")

    def goto_teams(self) -> None:
        self.page.goto(f"{self.base_url}/teams")
        self.page.wait_for_load_state("networkidle")

    def goto_projects(self) -> None:
        self.page.goto(f"{self.base_url}/projects")
        self.page.wait_for_load_state("networkidle")

    def goto_project(self, project_id: str) -> None:
        self.page.goto(f"{self.base_url}/projects/{project_id}")
        self.page.wait_for_load_state("networkidle")

    def goto_project_requirements(self, project_id: str) -> None:
        self.page.goto(f"{self.base_url}/projects/{project_id}/requirements")
        self.page.wait_for_load_state("networkidle")

    def goto_project_tasks(self, project_id: str) -> None:
        self.page.goto(f"{self.base_url}/projects/{project_id}/tasks")
        self.page.wait_for_load_state("networkidle")

    def goto_project_members(self, project_id: str) -> None:
        self.page.goto(f"{self.base_url}/projects/{project_id}/members")
        self.page.wait_for_load_state("networkidle")

    def goto_project_settings(self, project_id: str) -> None:
        self.page.goto(f"{self.base_url}/projects/{project_id}/settings")
        self.page.wait_for_load_state("networkidle")

    def goto_requirement(self, project_id: str, req_id: str) -> None:
        self.page.goto(
            f"{self.base_url}/projects/{project_id}/requirements/{req_id}"
        )
        self.page.wait_for_load_state("networkidle")

    def goto_specification(
        self, project_id: str, req_id: str, spec_id: str
    ) -> None:
        self.page.goto(
            f"{self.base_url}/projects/{project_id}/requirements/{req_id}/specs/{spec_id}"
        )
        self.page.wait_for_load_state("networkidle")

    def goto_coverage(self, project_id: str, req_id: str) -> None:
        self.page.goto(
            f"{self.base_url}/projects/{project_id}/requirements/{req_id}/coverage"
        )
        self.page.wait_for_load_state("networkidle")

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def login_via_ui(self, username: str, password: str) -> None:
        """Fill login form and submit."""
        self.goto_login()
        self.page.fill('input[id="username"]', username)
        self.page.fill('input[id="password"]', password)
        self.page.click('button[type="submit"]')
        self.page.wait_for_url("**/**", timeout=10000)

    def login_via_api(self, token: str) -> None:
        """Inject JWT token into localStorage and reload."""
        self.page.goto(self.base_url)
        self.page.evaluate(
            f'localStorage.setItem("token", "{token}")'
        )
        self.page.reload()
        self.page.wait_for_load_state("networkidle")

    def logout(self) -> None:
        self.page.click('button:has-text("Logout")')
        self.page.wait_for_url("**/login**", timeout=5000)

    # ------------------------------------------------------------------
    # Form helpers
    # ------------------------------------------------------------------

    def fill_input(self, field_id: str, value: str) -> None:
        self.page.fill(f'input[id="{field_id}"]', value)

    def fill_textarea(self, field_id: str, value: str) -> None:
        self.page.fill(f'textarea[id="{field_id}"]', value)

    def select_option(self, field_id: str, value: str) -> None:
        self.page.select_option(f'select[id="{field_id}"]', value)

    def click_button(self, text: str) -> None:
        self.page.click(f'button:has-text("{text}")')

    def click_link(self, text: str) -> None:
        self.page.click(f'a:has-text("{text}")')

    def click_element_with_title(self, title: str) -> None:
        self.page.click(f'[title="{title}"]')

    # ------------------------------------------------------------------
    # Assertions
    # ------------------------------------------------------------------

    def assert_text_visible(self, text: str) -> None:
        expect(self.page.locator(f"text={text}")).to_be_visible()

    def assert_input_value(self, field_id: str, expected: str) -> None:
        expect(self.page.locator(f'#{field_id}')).to_have_value(expected)

    def assert_url_contains(self, fragment: str) -> None:
        assert fragment in self.page.url, f"Expected '{fragment}' in {self.page.url}"

    def assert_status_badge(self, status: str) -> None:
        """Assert a StatusBadge with the given status text is visible."""
        expect(
            self.page.locator(f"span.badge-base:has-text('{status}')")
        ).to_be_visible()
