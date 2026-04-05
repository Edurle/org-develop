import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.webhook import WebhookConfig, WebhookDelivery

router = APIRouter(prefix="/api", tags=["webhooks"])


class WebhookCreate(BaseModel):
    url: str
    events: list[str]
    secret: str | None = None


class WebhookResponse(BaseModel):
    id: str
    project_id: str
    url: str
    events: list[str]
    secret: str | None
    is_active: bool
    created_at: str | None

    class Config:
        from_attributes = True


class DeliveryResponse(BaseModel):
    id: str
    event: str
    status: str
    status_code: int | None
    attempts: int
    last_attempt_at: str | None
    created_at: str | None

    class Config:
        from_attributes = True


def _webhook_to_response(wh: WebhookConfig) -> WebhookResponse:
    return WebhookResponse(
        id=wh.id,
        project_id=wh.project_id,
        url=wh.url,
        events=json.loads(wh.events),
        secret=wh.secret,
        is_active=wh.is_active,
        created_at=wh.created_at.isoformat() if wh.created_at else None,
    )


def _delivery_to_response(d: WebhookDelivery) -> DeliveryResponse:
    return DeliveryResponse(
        id=d.id,
        event=d.event,
        status=d.status,
        status_code=d.status_code,
        attempts=d.attempts,
        last_attempt_at=d.last_attempt_at.isoformat() if d.last_attempt_at else None,
        created_at=d.created_at.isoformat() if d.created_at else None,
    )


@router.post(
    "/projects/{project_id}/webhooks",
    response_model=WebhookResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_webhook(
    project_id: str,
    body: WebhookCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    wh = WebhookConfig(
        project_id=project_id,
        url=body.url,
        events=json.dumps(body.events),
        secret=body.secret,
        is_active=True,
    )
    db.add(wh)
    await db.flush()
    return _webhook_to_response(wh)


@router.get(
    "/projects/{project_id}/webhooks",
    response_model=list[WebhookResponse],
)
async def list_webhooks(
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(WebhookConfig)
        .where(WebhookConfig.project_id == project_id)
        .order_by(WebhookConfig.created_at)
    )
    return [_webhook_to_response(wh) for wh in result.scalars().all()]


@router.delete(
    "/projects/{project_id}/webhooks/{webhook_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_webhook(
    project_id: str,
    webhook_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(WebhookConfig).where(
            WebhookConfig.id == webhook_id,
            WebhookConfig.project_id == project_id,
        )
    )
    wh = result.scalars().first()
    if wh is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found"
        )
    await db.delete(wh)
    await db.flush()


@router.get(
    "/webhooks/{webhook_id}/deliveries",
    response_model=list[DeliveryResponse],
)
async def list_deliveries(
    webhook_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    """List recent delivery attempts for a webhook."""
    result = await db.execute(
        select(WebhookDelivery)
        .where(WebhookDelivery.webhook_id == webhook_id)
        .order_by(WebhookDelivery.created_at.desc())
        .limit(50)
    )
    return [_delivery_to_response(d) for d in result.scalars().all()]
