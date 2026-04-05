from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# TestCase
# ---------------------------------------------------------------------------

class TestCaseCreate(BaseModel):
    test_task_id: str
    title: str
    preconditions: str | None = None
    steps: str
    expected_result: str
    actual_result: str | None = None
    status: str = "pending"


class TestCaseUpdate(BaseModel):
    title: str | None = None
    preconditions: str | None = None
    steps: str | None = None
    expected_result: str | None = None
    actual_result: str | None = None
    status: str | None = None


class TestCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    test_task_id: str
    title: str
    preconditions: str | None
    steps: str
    expected_result: str
    actual_result: str | None
    status: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# ClauseCoverage
# ---------------------------------------------------------------------------

class ClauseCoverageCreate(BaseModel):
    clause_id: str
    test_case_id: str


class ClauseCoverageUpdate(BaseModel):
    """ClauseCoverage has no updatable fields beyond identifiers, but
    we provide an empty schema for API consistency."""
    pass


class ClauseCoverageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    clause_id: str
    test_case_id: str
    created_at: datetime
