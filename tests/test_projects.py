"""
End-to-end tests for the projects module.

Covers API CRUD operations and UI workflows for project management.

Run:  python -m pytest tests/test_projects.py -v -s
"""

import pytest

from helpers.api import ApiHelper
from helpers.ui import UiHelper


# ===========================================================================
# API tests
# ===========================================================================


class TestProjectAPI:
    """CRUD tests for the /api/projects endpoints."""

    def test_create_project(self, api: ApiHelper, seed_data: dict):
        team_id = seed_data["team"]["id"]
        project = api.create_project(
            team_id=team_id,
            name="My Project",
            slug="my-project",
            description="A test project",
        )
        assert project["name"] == "My Project"
        assert project["slug"] == "my-project"
        assert project["description"] == "A test project"
        assert project["team_id"] == team_id
        assert "id" in project

    def test_list_projects(self, api: ApiHelper, seed_data: dict):
        # seed_data already created one project; add a second one
        team_id = seed_data["team"]["id"]
        api.create_project(team_id=team_id, name="Second Project")

        projects = api.list_projects()
        assert isinstance(projects, list)
        assert len(projects) >= 2

    def test_list_projects_filter_by_team(self, api: ApiHelper, seed_data: dict):
        # Create a second org+team to verify filtering
        team_id = seed_data["team"]["id"]
        other_org = api.create_org()
        other_team = api.create_team(org_id=other_org["id"])
        api.create_project(team_id=other_team["id"], name="Other Team Project")

        # Filter by original team
        projects = api.list_projects(team_id=team_id)
        assert all(p["team_id"] == team_id for p in projects)
        assert len(projects) >= 1

        # Filter by other team
        other_projects = api.list_projects(team_id=other_team["id"])
        assert all(p["team_id"] == other_team["id"] for p in other_projects)
        assert len(other_projects) >= 1

    def test_get_project(self, api: ApiHelper, seed_data: dict):
        created = seed_data["project"]
        fetched = api.get_project(created["id"])
        assert fetched["id"] == created["id"]
        assert fetched["name"] == created["name"]
        assert fetched["slug"] == created["slug"]
        assert fetched["team_id"] == created["team_id"]

    def test_update_project(self, api: ApiHelper, seed_data: dict):
        project_id = seed_data["project"]["id"]
        updated = api.update_project(
            project_id,
            name="Renamed Project",
            description="Updated description",
        )
        assert updated["name"] == "Renamed Project"
        assert updated["description"] == "Updated description"

        # Verify via GET
        fetched = api.get_project(project_id)
        assert fetched["name"] == "Renamed Project"
        assert fetched["description"] == "Updated description"

    def test_delete_project(self, api: ApiHelper, seed_data: dict):
        team_id = seed_data["team"]["id"]
        project = api.create_project(
            team_id=team_id,
            name="To Be Deleted",
            slug="to-be-deleted",
        )
        project_id = project["id"]

        status_code = api.delete_project(project_id)
        assert status_code == 204

        # Verify the project is gone
        response = api.s.get(api._url(f"/api/projects/{project_id}"))
        assert response.status_code == 404


# ===========================================================================
# UI tests
# ===========================================================================


class TestProjectUI:
    """UI workflow tests for project pages."""

    def test_projects_page_create(self, api: ApiHelper, ui: UiHelper):
        """Create a project via the Projects page modal."""
        # Need an org + team first (created via API)
        org = api.create_org()
        team = api.create_team(org_id=org["id"])

        # Navigate to projects page
        ui.goto_projects()

        # Open the create modal
        ui.click_button("+ New Project")

        # Fill in the form
        ui.fill_input("proj-name", "UI Created Project")
        ui.fill_input("proj-slug", "ui-created-project")
        ui.fill_textarea("proj-desc", "Created via the UI")
        ui.select_option("proj-team", team["id"])

        # Submit
        ui.click_button("Create Project")

        # Verify the project appears on the page
        ui.assert_text_visible("UI Created Project")

        # Verify via API as well
        projects = api.list_projects(team_id=team["id"])
        names = [p["name"] for p in projects]
        assert "UI Created Project" in names

    def test_project_overview_inline_edit(self, api: ApiHelper, seed_data: dict, ui: UiHelper):
        """Edit the project name inline on the overview page."""
        project_id = seed_data["project"]["id"]

        # Navigate to project overview and wait for the edit button
        ui.goto_project(project_id)
        ui.page.wait_for_selector('[title="Edit name"]', state="visible")
        ui.page.wait_for_timeout(500)

        # Click the pencil icon to start editing
        ui.click_element_with_title("Edit name")

        # Wait for the inline input to appear (Vue reactivity)
        save_btn = ui.page.locator('button:has-text("Save")').first
        save_btn.wait_for(state="visible")

        # Fill the input using fill() which properly triggers Vue v-model
        edit_input = ui.page.locator('input[type="text"].input-glass').first
        edit_input.fill("Inline Edited Name")

        # Click Save
        save_btn.click()

        # Wait for API update to complete
        ui.page.wait_for_timeout(1000)

        # Verify the new name is visible
        ui.assert_text_visible("Inline Edited Name")

        # Verify via API
        fetched = api.get_project(project_id)
        assert fetched["name"] == "Inline Edited Name"

    def test_project_settings_edit(self, api: ApiHelper, seed_data: dict, ui: UiHelper):
        """Edit project details via the settings page."""
        project_id = seed_data["project"]["id"]

        # Navigate to settings
        ui.goto_project_settings(project_id)

        # Wait for form to be populated
        ui.page.wait_for_selector('input[id="settings-name"]', state="visible")
        ui.page.wait_for_timeout(500)

        # Update fields
        ui.fill_input("settings-name", "Settings Updated Name")
        ui.fill_input("settings-slug", "settings-updated-slug")
        ui.fill_textarea("settings-desc", "Updated via settings page")

        # Save
        ui.click_button("Save Changes")
        ui.page.wait_for_timeout(2000)

        # Verify via API
        fetched = api.get_project(project_id)
        assert fetched["name"] == "Settings Updated Name"
        assert fetched["slug"] == "settings-updated-slug"
        assert fetched["description"] == "Updated via settings page"

    def test_project_settings_delete(self, api: ApiHelper, seed_data: dict, ui: UiHelper):
        """Delete a project via the settings page confirmation modal."""
        # Create a dedicated project for this test
        team_id = seed_data["team"]["id"]
        project = api.create_project(
            team_id=team_id,
            name="Delete Me",
            slug="delete-me",
        )
        project_id = project["id"]
        project_name = project["name"]

        # Navigate to settings and wait for the form to load
        ui.goto_project_settings(project_id)
        ui.page.wait_for_selector('input[id="settings-name"]', state="visible")
        ui.page.wait_for_timeout(500)

        # Click the danger zone "Delete Project" button to open the modal
        # (before modal opens, there is only one such button on the page)
        ui.click_button("Delete Project")

        # Wait for the confirmation modal to appear
        ui.page.wait_for_selector('input[id="delete-confirm"]', state="visible")

        # Type the project name to confirm deletion
        ui.fill_input("delete-confirm", project_name)

        # Click the modal's confirm button (inside the .fixed Teleport'd modal)
        # Playwright auto-waits for the button to become enabled
        ui.page.locator('.fixed button:has-text("Delete Project")').click()

        # Should be redirected away from the project page
        ui.page.wait_for_timeout(2000)
        assert f"/projects/{project_id}" not in ui.page.url

        # Verify via API that the project is gone
        response = api.s.get(api._url(f"/api/projects/{project_id}"))
        assert response.status_code == 404

    def test_project_members_add(self, api: ApiHelper, seed_data: dict, ui: UiHelper):
        """Add a member to a project via the members page."""
        project_id = seed_data["project"]["id"]
        team_id = seed_data["team"]["id"]

        # Create a second user to add as member
        other = ApiHelper()
        other.register()

        # Navigate to members page
        ui.goto_project_members(project_id)
        ui.page.wait_for_timeout(1000)

        # Open add-member modal (before modal opens, only one "Add Member" button)
        ui.click_button("Add Member")

        # Wait for the modal to appear
        ui.page.wait_for_selector('input[id="member-user-id"]', state="visible")

        # Fill in the member details
        ui.fill_input("member-user-id", other.user_id)
        ui.select_option("member-role", "member")

        # Submit via the modal's "Add Member" button (inside the .fixed Teleport'd modal)
        ui.page.locator('.fixed button:has-text("Add Member")').click()

        # Wait for the member to appear in the list
        ui.page.wait_for_timeout(1000)

        # Verify the new member is listed
        ui.assert_text_visible(other.user_id)

        # Verify via API
        members = api.list_team_members(team_id)
        member_ids = [m["user_id"] for m in members]
        assert other.user_id in member_ids

    def test_project_navigation(self, api: ApiHelper, seed_data: dict, ui: UiHelper):
        """Navigate between project tabs and verify each loads correctly."""
        project_id = seed_data["project"]["id"]
        project_name = seed_data["project"]["name"]

        # Start at the overview page
        ui.goto_project(project_id)
        ui.page.wait_for_selector(f'text="{project_name}"', state="visible")

        # Navigate to Requirements tab — wait for page content before moving on
        ui.click_link("Requirements")
        ui.page.wait_for_url(f"**/projects/{project_id}/requirements", timeout=5000)
        ui.page.wait_for_selector('button:has-text("New Requirement")', state="visible")
        ui.assert_url_contains(f"/projects/{project_id}/requirements")

        # Navigate to Tasks tab
        ui.click_link("Tasks")
        ui.page.wait_for_url(f"**/projects/{project_id}/tasks", timeout=5000)
        ui.page.wait_for_timeout(500)
        ui.assert_url_contains(f"/projects/{project_id}/tasks")

        # Navigate to Members tab
        ui.click_link("Members")
        ui.page.wait_for_url(f"**/projects/{project_id}/members", timeout=5000)
        ui.page.wait_for_selector('button:has-text("Add Member")', state="visible")
        ui.assert_url_contains(f"/projects/{project_id}/members")

        # Navigate to Settings tab
        ui.click_link("Settings")
        ui.page.wait_for_url(f"**/projects/{project_id}/settings", timeout=5000)
        ui.page.wait_for_selector('input[id="settings-name"]', state="visible")
        ui.assert_url_contains(f"/projects/{project_id}/settings")

        # Verify settings page has the expected form
        assert ui.page.locator('input[id="settings-name"]').is_visible()
        assert ui.page.locator('button:has-text("Save Changes")').is_visible()
