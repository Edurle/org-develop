from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserInfo(BaseModel):
    id: str
    username: str
    display_name: str | None = None


# ---------------------------------------------------------------------------
# DevTask
# ---------------------------------------------------------------------------

class DevTaskCreate(BaseModel):
    requirement_id: str | None = None
    spec_version_id: str | None = None
    iteration_id: str
    title: str
    status: str = "open"
    assignee_id: str | None = None
    estimate_hours: float | None = None


class DevTaskUpdate(BaseModel):
    title: str | None = None
    status: str | None = None
    assignee_id: str | None = None
    estimate_hours: float | None = None
    spec_version_id: str | None = None


class DevTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    requirement_id: str
    spec_version_id: str | None
    iteration_id: str
    title: str
    status: str
    assignee_id: str | None
    assignee: UserInfo | None = None
    estimate_hours: float | None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# TestTask
# ---------------------------------------------------------------------------

class TestTaskCreate(BaseModel):
    requirement_id: str | None = None
    iteration_id: str
    title: str
    status: str = "open"
    assignee_id: str | None = None


class TestTaskUpdate(BaseModel):
    title: str | None = None
    status: str | None = None
    assignee_id: str | None = None


class TestTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    requirement_id: str
    iteration_id: str
    title: str
    status: str
    assignee_id: str | None
    assignee: UserInfo | None = None
    created_at: datetime
    updated_at: datetime
