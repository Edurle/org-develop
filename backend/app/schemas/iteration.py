from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class IterationCreate(BaseModel):
    project_id: str
    name: str
    status: str = "planning"
    start_date: date | None = None
    end_date: date | None = None


class IterationUpdate(BaseModel):
    name: str | None = None
    status: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class IterationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    name: str
    status: str
    start_date: date | None
    end_date: date | None
    created_at: datetime
    updated_at: datetime
