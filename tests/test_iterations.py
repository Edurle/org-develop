"""
End-to-end tests for the iterations module.

Covers CRUD operations and status transitions for project iterations.

Run:  python -m pytest tests/test_iterations.py -v -s
"""

import pytest

from helpers.api import ApiHelper


class TestIterationAPI:
    """Tests for the /api/projects/{project_id}/iterations endpoints."""

    def test_create_iteration(self, api: ApiHelper, seed_data: dict):
        project_id = seed_data["project"]["id"]
        iteration = api.create_iteration(project_id=project_id, name="Sprint Alpha")

        assert "id" in iteration
        assert iteration["name"] == "Sprint Alpha"
        assert iteration["status"] == "planning"
        assert iteration["project_id"] == project_id

    def test_list_iterations(self, api: ApiHelper, seed_data: dict):
        project_id = seed_data["project"]["id"]
        # seed_data already created one iteration via seed()
        api.create_iteration(project_id=project_id, name="Second Iteration")

        iterations = api.list_iterations(project_id)
        assert isinstance(iterations, list)
        assert len(iterations) >= 2

        names = [it["name"] for it in iterations]
        assert "Second Iteration" in names

    def test_update_iteration(self, api: ApiHelper, seed_data: dict):
        project_id = seed_data["project"]["id"]
        iteration = seed_data["iteration"]
        iteration_id = iteration["id"]

        updated = api.update_iteration(
            project_id,
            iteration_id,
            name="Renamed Sprint",
            start_date="2026-04-01",
            end_date="2026-04-30",
        )
        assert updated["name"] == "Renamed Sprint"
        assert updated["start_date"] == "2026-04-01"
        assert updated["end_date"] == "2026-04-30"

    def test_iteration_status_planning_to_active(self, api: ApiHelper, seed_data: dict):
        project_id = seed_data["project"]["id"]
        iteration = api.create_iteration(project_id=project_id, name="Status Test Sprint")
        assert iteration["status"] == "planning"

        updated = api.update_iteration(
            project_id, iteration["id"], status="active"
        )
        assert updated["status"] == "active"

    def test_iteration_status_active_to_completed(self, api: ApiHelper, seed_data: dict):
        project_id = seed_data["project"]["id"]
        iteration = api.create_iteration(project_id=project_id, name="Completion Sprint")

        # Transition planning -> active -> completed
        api.update_iteration(project_id, iteration["id"], status="active")
        updated = api.update_iteration(
            project_id, iteration["id"], status="completed"
        )
        assert updated["status"] == "completed"
