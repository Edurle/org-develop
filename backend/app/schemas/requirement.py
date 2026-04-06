from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RequirementCreate(BaseModel):
    iteration_id: str
    title: str
    priority: str = "medium"
    status: str = "draft"
    creator_id: str | None = None
    assignee_id: str | None = None


class RequirementUpdate(BaseModel):
    title: str | None = None
    priority: str | None = None
    status: str | None = None
    assignee_id: str | None = None


class RequirementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    iteration_id: str
    title: str
    priority: str
    status: str
    creator_id: str
    assignee_id: str | None
    created_at: datetime
    updated_at: datetime
