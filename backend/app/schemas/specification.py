from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Specification
# ---------------------------------------------------------------------------

class SpecificationCreate(BaseModel):
    requirement_id: str | None = None
    spec_type: str  # api, data, flow, ui
    title: str
    current_version: int = 0


class SpecificationUpdate(BaseModel):
    spec_type: str | None = None
    title: str | None = None
    current_version: int | None = None


class SpecificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    requirement_id: str
    spec_type: str
    title: str
    current_version: int
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# SpecVersion
# ---------------------------------------------------------------------------

class SpecVersionCreate(BaseModel):
    spec_id: str | None = None
    version: int | None = None
    status: str = "draft"
    content: dict = {}
    locked_by: str | None = None


class SpecVersionUpdate(BaseModel):
    status: str | None = None
    content: dict | None = None
    locked_by: str | None = None


class SpecVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    spec_id: str
    version: int
    status: str
    content: dict
    locked_at: datetime | None
    locked_by: str | None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# SpecClause
# ---------------------------------------------------------------------------

class SpecClauseCreate(BaseModel):
    spec_version_id: str | None = None
    clause_id: str  # auto-generated, e.g. "API-001"
    title: str
    description: str
    category: str  # functional, validation, security, performance, ui_element
    severity: str = "must"  # must, should, may


class SpecClauseUpdate(BaseModel):
    clause_id: str | None = None
    title: str | None = None
    description: str | None = None
    category: str | None = None
    severity: str | None = None


class SpecClauseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    spec_version_id: str
    clause_id: str
    title: str
    description: str
    category: str
    severity: str
    created_at: datetime
