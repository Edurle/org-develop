"""Audit log service for recording and querying CUD operations."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


async def log_action(
    db: AsyncSession,
    user_id: str | None,
    action: str,
    resource_type: str,
    resource_id: str,
    detail: str | None = None,
) -> AuditLog:
    """Record an audit log entry. Flushes within the current transaction."""
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        detail=detail,
    )
    db.add(entry)
    await db.flush()
    return entry


async def query_audit_logs(
    db: AsyncSession,
    resource_type: str | None = None,
    resource_id: str | None = None,
    user_id: str | None = None,
    action: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[AuditLog], int]:
    """Query audit logs with optional filters. Returns (logs, total_count)."""
    stmt = select(AuditLog)
    count_stmt = select(func.count(AuditLog.id))

    if resource_type is not None:
        stmt = stmt.where(AuditLog.resource_type == resource_type)
        count_stmt = count_stmt.where(AuditLog.resource_type == resource_type)
    if resource_id is not None:
        stmt = stmt.where(AuditLog.resource_id == resource_id)
        count_stmt = count_stmt.where(AuditLog.resource_id == resource_id)
    if user_id is not None:
        stmt = stmt.where(AuditLog.user_id == user_id)
        count_stmt = count_stmt.where(AuditLog.user_id == user_id)
    if action is not None:
        stmt = stmt.where(AuditLog.action == action)
        count_stmt = count_stmt.where(AuditLog.action == action)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()
    offset = (page - 1) * page_size
    stmt = stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    logs = list(result.scalars().all())
    return logs, total
