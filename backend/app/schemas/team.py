from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Organization
# ---------------------------------------------------------------------------

class OrganizationCreate(BaseModel):
    name: str
    slug: str


class OrganizationUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Team
# ---------------------------------------------------------------------------

class TeamCreate(BaseModel):
    org_id: str
    name: str
    slug: str


class TeamUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None


class TeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    org_id: str
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime
