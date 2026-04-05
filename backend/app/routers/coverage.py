from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.services import coverage as coverage_svc

router = APIRouter(prefix="/api", tags=["coverage"])


class CoverageResponse(BaseModel):
    total_clauses: int
    covered_clauses: int
    must_coverage_pct: float
    should_coverage_pct: float
    may_coverage_pct: float
    uncovered_clauses: list[dict]


class CoverageCheckResponse(BaseModel):
    sufficient: bool


@router.get(
    "/requirements/{requirement_id}/coverage",
    response_model=CoverageResponse,
)
async def get_coverage_report(
    requirement_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    try:
        report = await coverage_svc.get_requirement_coverage(db, requirement_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return CoverageResponse(**report)


@router.get(
    "/requirements/{requirement_id}/coverage/check",
    response_model=CoverageCheckResponse,
)
async def check_coverage_sufficient(
    requirement_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    try:
        sufficient = await coverage_svc.check_coverage_sufficient(db, requirement_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return CoverageCheckResponse(sufficient=sufficient)
