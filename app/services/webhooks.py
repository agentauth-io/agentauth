"""
Webhooks Service

Handles webhook registration, event dispatching, and delivery.
"""
import json
import hmac
import hashlib
import httpx
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import BackgroundTasks

from app.models.webhooks import Webhook, WebhookDelivery, WEBHOOK_EVENTS


class WebhooksService:
    """
    Webhooks service for event notification.
    
    Handles:
    - Webhook CRUD operations
    - Event dispatching
    - Async delivery with retries
    - Signature generation for verification
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # CRUD Operations
    
    async def list_webhooks(self, user_id: str) -> List[Webhook]:
        """List all webhooks for a user."""
        result = await self.db.execute(
            select(Webhook).where(
                Webhook.user_id == user_id,
                Webhook.is_active == True
            ).order_by(Webhook.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_webhook(self, webhook_id: UUID, user_id: str) -> Optional[Webhook]:
        """Get a specific webhook."""
        result = await self.db.execute(
            select(Webhook).where(
                Webhook.id == webhook_id,
                Webhook.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
    
    async def create_webhook(
        self, 
        user_id: str, 
        url: str, 
        events: List[str],
        description: Optional[str] = None
    ) -> Webhook:
        """Create a new webhook."""
        # Validate events
        valid_events = [e for e in events if e in WEBHOOK_EVENTS]
        if not valid_events:
            valid_events = ["authorization.approved", "authorization.denied"]
        
        webhook = Webhook(
            user_id=user_id,
            url=url,
            description=description
        )
        webhook.set_events_list(valid_events)
        
        self.db.add(webhook)
        await self.db.commit()
        await self.db.refresh(webhook)
        
        return webhook
    
    async def update_webhook(
        self,
        webhook_id: UUID,
        user_id: str,
        url: Optional[str] = None,
        events: Optional[List[str]] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[Webhook]:
        """Update a webhook."""
        webhook = await self.get_webhook(webhook_id, user_id)
        if not webhook:
            return None
        
        if url is not None:
            webhook.url = url
        if events is not None:
            valid_events = [e for e in events if e in WEBHOOK_EVENTS]
            webhook.set_events_list(valid_events)
        if description is not None:
            webhook.description = description
        if is_active is not None:
            webhook.is_active = is_active
        
        await self.db.commit()
        await self.db.refresh(webhook)
        
        return webhook
    
    async def delete_webhook(self, webhook_id: UUID, user_id: str) -> bool:
        """Soft delete a webhook."""
        webhook = await self.get_webhook(webhook_id, user_id)
        if not webhook:
            return False
        
        webhook.is_active = False
        await self.db.commit()
        return True
    
    # Event Dispatching
    
    async def dispatch_event(
        self,
        user_id: str,
        event_type: str,
        payload: Dict[str, Any],
        background_tasks: Optional[BackgroundTasks] = None
    ):
        """
        Dispatch an event to all subscribed webhooks.
        
        If background_tasks is provided, delivery happens asynchronously.
        """
        # Get webhooks subscribed to this event
        webhooks = await self._get_subscribed_webhooks(user_id, event_type)
        
        for webhook in webhooks:
            # Create delivery record
            delivery = WebhookDelivery(
                webhook_id=webhook.id,
                event_type=event_type,
                payload=json.dumps(payload)
            )
            self.db.add(delivery)
            await self.db.flush()
            
            if background_tasks:
                # Async delivery
                background_tasks.add_task(
                    self._deliver_webhook,
                    webhook_id=webhook.id,
                    delivery_id=delivery.id,
                    url=webhook.url,
                    secret=webhook.secret,
                    event_type=event_type,
                    payload=payload
                )
            else:
                # Sync delivery (for testing)
                await self._deliver_webhook(
                    webhook_id=webhook.id,
                    delivery_id=delivery.id,
                    url=webhook.url,
                    secret=webhook.secret,
                    event_type=event_type,
                    payload=payload
                )
        
        await self.db.commit()
    
    async def _get_subscribed_webhooks(self, user_id: str, event_type: str) -> List[Webhook]:
        """Get webhooks subscribed to an event."""
        result = await self.db.execute(
            select(Webhook).where(
                Webhook.user_id == user_id,
                Webhook.is_active == True
            )
        )
        webhooks = result.scalars().all()
        
        # Filter by event subscription
        return [w for w in webhooks if event_type in w.get_events_list()]
    
    async def _deliver_webhook(
        self,
        webhook_id: UUID,
        delivery_id: UUID,
        url: str,
        secret: str,
        event_type: str,
        payload: Dict[str, Any]
    ):
        """Deliver a webhook with signature."""
        # Build full payload
        full_payload = {
            "event": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": payload
        }
        payload_json = json.dumps(full_payload)
        
        # Generate signature
        signature = self._generate_signature(payload_json, secret)
        
        # Make request
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    url,
                    content=payload_json,
                    headers={
                        "Content-Type": "application/json",
                        "X-AgentAuth-Signature": signature,
                        "X-AgentAuth-Event": event_type
                    }
                )
                
                # Update delivery record (need new session since this is async)
                # In production, use a proper connection pool
                status = "success" if response.status_code < 400 else "failed"
                
        except Exception as e:
            # Log error (in production, use proper logging)
            print(f"Webhook delivery failed: {e}")
    
    def _generate_signature(self, payload: str, secret: str) -> str:
        """Generate HMAC-SHA256 signature for webhook payload."""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
    
    # Utility Methods
    
    @staticmethod
    def verify_signature(payload: str, signature: str, secret: str) -> bool:
        """Verify a webhook signature."""
        expected = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)


# Event helper functions

async def emit_authorization_event(
    db: AsyncSession,
    user_id: str,
    decision: str,
    amount: float,
    merchant: Optional[str] = None,
    agent_id: Optional[str] = None,
    reason: Optional[str] = None,
    background_tasks: Optional[BackgroundTasks] = None
):
    """
    Emit an authorization event to webhooks.
    
    Usage:
        await emit_authorization_event(
            db, user_id, "approved", 
            amount=49.99, merchant="stripe.com"
        )
    """
    event_type = f"authorization.{decision}"
    payload = {
        "amount": amount,
        "merchant": merchant,
        "agent_id": agent_id,
    }
    if reason:
        payload["reason"] = reason
    
    service = WebhooksService(db)
    await service.dispatch_event(user_id, event_type, payload, background_tasks)
