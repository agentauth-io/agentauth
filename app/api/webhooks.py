"""
Webhooks API

API endpoints for managing webhook endpoints.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.webhooks import WEBHOOK_EVENTS
from app.services.webhooks import WebhooksService


router = APIRouter(prefix="/v1/webhooks", tags=["Webhooks"])


# Schemas

class WebhookCreate(BaseModel):
    """Request to create a webhook."""
    url: str = Field(..., description="Webhook endpoint URL")
    events: List[str] = Field(
        default=["authorization.approved", "authorization.denied"],
        description="Events to subscribe to"
    )
    description: Optional[str] = Field(None, description="Description of the webhook")


class WebhookUpdate(BaseModel):
    """Request to update a webhook."""
    url: Optional[str] = None
    events: Optional[List[str]] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class WebhookResponse(BaseModel):
    """Webhook response."""
    id: str
    url: str
    events: List[str]
    description: Optional[str]
    secret: str
    is_active: bool
    last_triggered_at: Optional[str]
    failure_count: int
    created_at: str


# Endpoints

@router.get("", response_model=List[WebhookResponse])
async def list_webhooks(
    user_id: str = "default",
    db: AsyncSession = Depends(get_db)
):
    """
    List all webhooks.
    
    Returns all active webhook endpoints for the user.
    """
    service = WebhooksService(db)
    webhooks = await service.list_webhooks(user_id)
    
    return [
        WebhookResponse(
            id=str(w.id),
            url=w.url,
            events=w.get_events_list(),
            description=w.description,
            secret=w.secret,
            is_active=w.is_active,
            last_triggered_at=w.last_triggered_at.isoformat() if w.last_triggered_at else None,
            failure_count=w.failure_count,
            created_at=w.created_at.isoformat()
        )
        for w in webhooks
    ]


@router.post("", response_model=WebhookResponse)
async def create_webhook(
    webhook: WebhookCreate,
    user_id: str = "default",
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new webhook.
    
    The secret returned should be saved securely - it's used to verify webhook signatures.
    """
    service = WebhooksService(db)
    w = await service.create_webhook(
        user_id=user_id,
        url=webhook.url,
        events=webhook.events,
        description=webhook.description
    )
    
    return WebhookResponse(
        id=str(w.id),
        url=w.url,
        events=w.get_events_list(),
        description=w.description,
        secret=w.secret,
        is_active=w.is_active,
        last_triggered_at=None,
        failure_count=0,
        created_at=w.created_at.isoformat()
    )


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: UUID,
    user_id: str = "default",
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific webhook.
    """
    service = WebhooksService(db)
    w = await service.get_webhook(webhook_id, user_id)
    
    if not w:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    return WebhookResponse(
        id=str(w.id),
        url=w.url,
        events=w.get_events_list(),
        description=w.description,
        secret=w.secret,
        is_active=w.is_active,
        last_triggered_at=w.last_triggered_at.isoformat() if w.last_triggered_at else None,
        failure_count=w.failure_count,
        created_at=w.created_at.isoformat()
    )


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: UUID,
    update: WebhookUpdate,
    user_id: str = "default",
    db: AsyncSession = Depends(get_db)
):
    """
    Update a webhook.
    """
    service = WebhooksService(db)
    w = await service.update_webhook(
        webhook_id=webhook_id,
        user_id=user_id,
        url=update.url,
        events=update.events,
        description=update.description,
        is_active=update.is_active
    )
    
    if not w:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    return WebhookResponse(
        id=str(w.id),
        url=w.url,
        events=w.get_events_list(),
        description=w.description,
        secret=w.secret,
        is_active=w.is_active,
        last_triggered_at=w.last_triggered_at.isoformat() if w.last_triggered_at else None,
        failure_count=w.failure_count,
        created_at=w.created_at.isoformat()
    )


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: UUID,
    user_id: str = "default",
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a webhook.
    """
    service = WebhooksService(db)
    deleted = await service.delete_webhook(webhook_id, user_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    return {"status": "success", "message": "Webhook deleted"}


@router.get("/events/available")
async def get_available_events():
    """
    Get list of available webhook events.
    """
    return {
        "events": [
            {"name": e, "description": _get_event_description(e)}
            for e in WEBHOOK_EVENTS
        ]
    }


def _get_event_description(event: str) -> str:
    """Get description for an event type."""
    descriptions = {
        "authorization.requested": "Fired when an agent requests authorization",
        "authorization.approved": "Fired when an authorization is approved",
        "authorization.denied": "Fired when an authorization is denied",
        "authorization.expired": "Fired when an authorization expires",
        "limit.exceeded": "Fired when a spending limit is exceeded",
        "rule.triggered": "Fired when a merchant/category rule is triggered",
    }
    return descriptions.get(event, "")
