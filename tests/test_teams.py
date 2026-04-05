"""
End-to-end tests for the teams & organizations module.

Covers both API-level and UI-level workflows:
  1-6: API tests using the `api` / `seed_data` fixtures
  7-8: UI tests using the `ui` fixture (Playwright)

Run:  pytest tests/test_teams.py -v -s
"""

import pytest

from helpers.api import ApiHelper
from helpers.ui import UiHelper


# ===================================================================
# API tests
# ===================================================================


class TestOrganizationAPI:
    """API-level tests for organizations."""

    def test_create_organization(self, api: ApiHelper):
        """Create an org and verify all response fields are present."""
        org = api.create_org(name="Acme Corp", slug="acme-corp")

        assert "id" in org and org["id"], "Missing id"
        assert org["name"] == "Acme Corp"
        assert org["slug"] == "acme-corp"
        assert "created_at" in org, "Missing created_at"
        assert "updated_at" in org, "Missing updated_at"

    def test_list_organizations(self, api: ApiHelper):
        """Create an org, list orgs, and verify it appears in the list."""
        org = api.create_org(name="ListOrg", slug="list-org")

        orgs = api.list_orgs()
        assert isinstance(orgs, list)
        found = any(o["id"] == org["id"] for o in orgs)
        assert found, f"Created org {org['id']} not found in list"


class TestTeamAPI:
    """API-level tests for teams and team membership."""

    def test_create_team(self, api: ApiHelper):
        """Create a team under an org and verify response fields."""
        org = api.create_org(name="TeamOrg", slug="team-org")
        team = api.create_team(org_id=org["id"], name="Backend", slug="backend")

        assert "id" in team and team["id"], "Missing id"
        assert team["org_id"] == org["id"]
        assert team["name"] == "Backend"
        assert team["slug"] == "backend"

    def test_list_teams(self, api: ApiHelper):
        """Create a team, list teams, and verify it appears in the list."""
        org = api.create_org(name="ListTeamOrg", slug="list-team-org")
        team = api.create_team(org_id=org["id"], name="ListTeam", slug="list-team")

        teams = api.list_teams()
        assert isinstance(teams, list)
        found = any(t["id"] == team["id"] for t in teams)
        assert found, f"Created team {team['id']} not found in list"

    def test_add_team_member(self, api: ApiHelper):
        """Add a member to a team and verify the response."""
        org = api.create_org(name="MemberOrg", slug="member-org")
        team = api.create_team(org_id=org["id"], name="MemberTeam", slug="member-team")

        # Register a second user to add as a team member
        second = ApiHelper()
        second.register()

        member = api.add_team_member(
            team_id=team["id"],
            user_id=second.user_id,
            roles="developer",
        )

        assert "id" in member, "Missing member id"
        assert member["user_id"] == second.user_id
        assert member["roles"] == "developer"

    def test_list_team_members(self, api: ApiHelper):
        """Add a member, list members, and verify it appears in the list."""
        org = api.create_org(name="ListMemberOrg", slug="list-member-org")
        team = api.create_team(
            org_id=org["id"], name="ListMemberTeam", slug="list-member-team"
        )

        second = ApiHelper()
        second.register()

        api.add_team_member(
            team_id=team["id"],
            user_id=second.user_id,
            roles="developer",
        )

        members = api.list_team_members(team_id=team["id"])
        assert isinstance(members, list)
        found = any(m["user_id"] == second.user_id for m in members)
        assert found, f"Member {second.user_id} not found in team members list"


# ===================================================================
# UI tests
# ===================================================================


class TestTeamsUI:
    """Playwright-driven UI tests for the Teams & Organizations page."""

    def test_teams_page_create_org(self, ui: UiHelper):
        """Navigate to teams page, create an org via the modal, and verify."""
        ui.goto_teams()

        # Open the "New Organization" modal
        ui.click_button("New Organization")

        # Fill in the org form
        ui.fill_input("org-name", "UI Test Org")
        ui.fill_input("org-slug", "ui-test-org")

        # Submit
        ui.click_button("Create Organization")

        # The modal closes and the org name should appear on the page
        ui.assert_text_visible("UI Test Org")

    def test_teams_page_create_team(self, api: ApiHelper, ui: UiHelper):
        """Create an org via API, then use the UI to create a team in it."""
        org = api.create_org(name="UI Team Org", slug="ui-team-org")

        ui.goto_teams()

        # Click the "+ Team" button on the org card
        ui.click_button("+ Team")

        # Fill in the team modal
        ui.select_option("team-org", org["id"])
        ui.fill_input("team-name", "UI Test Team")
        ui.fill_input("team-slug", "ui-test-team")

        # Submit
        ui.click_button("Create Team")

        # The team name should now be visible under the org card
        ui.assert_text_visible("UI Test Team")
