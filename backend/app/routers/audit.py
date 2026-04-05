from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogResponse
from app.schemas.common import PaginatedResponse, PaginationParams, paginate
from app.services import audit as audit_svc

router = APIRouter(prefix="/api", tags=["audit"])


@router.get("/audit/logs", response_model=PaginatedResponse[AuditLogResponse])
async def list_audit_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
    resource_type: str | None = Query(default=None),
    resource_id: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    action: str | None = Query(default=None),
    pagination: PaginationParams = Depends(),
):
    logs, total = await audit_svc.query_audit_logs(
        db,
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user_id,
        action=action,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    items = [AuditLogResponse.model_validate(log).model_dump() for log in logs]
    return paginate(items, total, pagination)


@router.get("/audit/logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(select(AuditLog).where(AuditLog.id == log_id))
    log = result.scalars().first()
    if log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit log not found")
    return AuditLogResponse.model_validate(log).model_dump()
