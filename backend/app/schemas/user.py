from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    display_name: str | None = None


class UserUpdate(BaseModel):
    username: str | None = None
    email: str | None = None
    display_name: str | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    email: str
    display_name: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# TeamMember
# ---------------------------------------------------------------------------

class TeamMemberCreate(BaseModel):
    user_id: str
    team_id: str | None = None
    roles: str = "developer"


class TeamMemberUpdate(BaseModel):
    roles: str | None = None


class TeamMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    team_id: str
    roles: str
    joined_at: datetime
