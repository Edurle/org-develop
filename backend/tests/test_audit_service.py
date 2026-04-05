"""Unit tests for audit service layer.

Tests logging actions and querying audit logs with filters.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.audit import log_action, query_audit_logs


class TestAuditService:

    async def test_log_action(self, db):
        entry = await log_action(
            db, user_id="user-123", action="requirement.create",
            resource_type="requirement", resource_id="req-456",
            detail="Created requirement 'Login'",
        )
        assert entry.action == "requirement.create"
        assert entry.resource_type == "requirement"
        assert entry.resource_id == "req-456"
        assert entry.user_id == "user-123"
        assert entry.detail == "Created requirement 'Login'"

    async def test_query_audit_logs(self, db):
        await log_action(
            db, user_id="user-123", action="requirement.create",
            resource_type="requirement", resource_id="req-456",
            detail="Created requirement 'Login'",
        )
        logs, total = await query_audit_logs(db, resource_type="requirement")
        assert total == 1
        assert len(logs) == 1
        assert logs[0].action == "requirement.create"

    async def test_query_audit_logs_filtering(self, db):
        # Add two log entries with different resource types
        await log_action(
            db, user_id="user-123", action="requirement.create",
            resource_type="requirement", resource_id="req-456",
            detail="Created requirement 'Login'",
        )
        await log_action(
            db, user_id="user-456", action="spec.locked",
            resource_type="spec_version", resource_id="ver-789",
            detail="Locked spec version",
        )

        # Query all
        logs, total = await query_audit_logs(db)
        assert total == 2

        # Filter by resource_type
        logs, total = await query_audit_logs(db, resource_type="spec_version")
        assert total == 1
        assert logs[0].action == "spec.locked"

        # Filter by nonexistent resource_type
        logs, total = await query_audit_logs(db, resource_type="nonexistent")
        assert total == 0

        # Filter by action
        logs, total = await query_audit_logs(db, action="requirement.create")
        assert total == 1
        assert logs[0].resource_type == "requirement"

        # Filter by nonexistent action
        logs, total = await query_audit_logs(db, action="nonexistent")
        assert total == 0

    async def test_query_audit_logs_by_user_id(self, db):
        await log_action(
            db, user_id="user-aaa", action="task.create",
            resource_type="dev_task", resource_id="task-001",
            detail="Created task",
        )
        await log_action(
            db, user_id="user-bbb", action="task.claim",
            resource_type="dev_task", resource_id="task-002",
            detail="Claimed task",
        )

        logs, total = await query_audit_logs(db, user_id="user-aaa")
        assert total == 1
        assert logs[0].action == "task.create"

        logs, total = await query_audit_logs(db, user_id="user-bbb")
        assert total == 1
        assert logs[0].action == "task.claim"
