"""Webhook event dispatching and delivery service.

Provides:
- Event type definitions
- HMAC-SHA256 payload signing
- Async HTTP delivery with retry
- Delivery tracking
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone
from enum import StrEnum

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.webhook import WebhookConfig, WebhookDelivery

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAYS = [1, 5, 15]  # seconds
DELIVERY_TIMEOUT = 10  # seconds


class WebhookEvent(StrEnum):
    """All supported webhook events."""

    # Requirement lifecycle
    REQUIREMENT_CREATED = "requirement.created"
    REQUIREMENT_STATUS_CHANGED = "requirement.status_changed"

    # Specification lifecycle
    SPEC_CREATED = "spec.created"
    SPEC_SUBMITTED = "spec.submitted"
    SPEC_LOCKED = "spec.locked"
    SPEC_REJECTED = "spec.rejected"

    # Task lifecycle
    TASK_CREATED = "task.created"
    TASK_CLAIMED = "task.claimed"
    TASK_STATUS_CHANGED = "task.status_changed"

    # Test lifecycle
    TEST_CASE_CREATED = "test_case.created"
    TEST_CASE_STATUS_CHANGED = "test_case.status_changed"

    # Coverage
    COVERAGE_INSUFFICIENT = "coverage.insufficient"
    COVERAGE_SUFFICIENT = "coverage.sufficient"


def sign_payload(payload: str, secret: str) -> str:
    """Generate HMAC-SHA256 signature for a webhook payload."""
    return hmac.new(
        secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()


async def dispatch_event(
    db: AsyncSession,
    project_id: str,
    event: WebhookEvent,
    data: dict,
) -> list[str]:
    """
    Dispatch a webhook event to all matching webhook configs for a project.

    Returns list of delivery IDs.
    """
    result = await db.execute(
        select(WebhookConfig).where(
            WebhookConfig.project_id == project_id,
            WebhookConfig.is_active == True,
        )
    )
    configs = list(result.scalars().all())

    if not configs:
        return []

    payload = json.dumps(
        {
            "event": event,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "project_id": project_id,
            "data": data,
        },
        ensure_ascii=False,
    )

    delivery_ids: list[str] = []
    for config in configs:
        # Check if this config is subscribed to this event
        subscribed_events = json.loads(config.events)
        if not _event_matches(event, subscribed_events):
            continue

        delivery = WebhookDelivery(
            webhook_id=config.id,
            event=event,
            payload=payload,
            status="pending",
            attempts=0,
        )
        db.add(delivery)
        await db.flush()

        delivery_ids.append(delivery.id)

        # Fire and forget — actual delivery happens in background
        # For now we await; in production this would go to a task queue
        await _deliver(db, delivery, config, payload)

    return delivery_ids


async def _deliver(
    db: AsyncSession,
    delivery: WebhookDelivery,
    config: WebhookConfig,
    payload: str,
) -> None:
    """Attempt to deliver a webhook with retries."""
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Event": delivery.event,
        "X-Webhook-Delivery": delivery.id,
    }

    if config.secret:
        signature = sign_payload(payload, config.secret)
        headers["X-Webhook-Signature"] = f"sha256={signature}"

    last_error: str | None = None
    for attempt in range(MAX_RETRIES):
        delivery.attempts = attempt + 1
        delivery.last_attempt_at = datetime.now(timezone.utc)

        try:
            async with httpx.AsyncClient(timeout=DELIVERY_TIMEOUT) as client:
                resp = await client.post(config.url, content=payload, headers=headers)

            delivery.status_code = resp.status_code
            delivery.response_body = resp.text[:2000]

            if 200 <= resp.status_code < 300:
                delivery.status = "success"
                await db.flush()
                logger.info(
                    "Webhook delivered: %s -> %s (delivery=%s)",
                    delivery.event,
                    config.url,
                    delivery.id,
                )
                return
            else:
                last_error = f"HTTP {resp.status_code}"

        except httpx.HTTPError as exc:
            last_error = str(exc)
            logger.warning(
                "Webhook delivery attempt %d failed: %s (delivery=%s)",
                attempt + 1,
                exc,
                delivery.id,
            )

        # Mark as retrying if more attempts remain
        if attempt < MAX_RETRIES - 1:
            delivery.status = "retrying"
            await db.flush()
            # In production, would use task queue with delay
            # import asyncio; await asyncio.sleep(RETRY_DELAYS[attempt])
        else:
            delivery.status = "failed"
            await db.flush()
            logger.error(
                "Webhook delivery failed after %d attempts: %s (delivery=%s)",
                MAX_RETRIES,
                last_error,
                delivery.id,
            )


def _event_matches(event: WebhookEvent, subscribed: list[str]) -> bool:
    """Check if an event matches any subscription pattern.

    Supports exact match and wildcard patterns:
    - "requirement.created" matches exactly
    - "requirement.*" matches all requirement events
    - "*" matches everything
    """
    event_str = str(event)
    for pattern in subscribed:
        if pattern == "*":
            return True
        if pattern == event_str:
            return True
        if pattern.endswith(".*"):
            prefix = pattern[:-1]  # "requirement."
            if event_str.startswith(prefix):
                return True
    return False
