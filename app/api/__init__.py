"""
AgentAuth API Package
"""
from app.api.consents import router as consents_router
from app.api.authorize import router as authorize_router
from app.api.verify import router as verify_router
from app.api.payments import router as payments_router
from app.api.dashboard import router as dashboard_router
from app.api.admin import router as admin_router
from app.api.limits import router as limits_router
from app.api.rules import router as rules_router
from app.api.analytics import router as analytics_router
from app.api.webhooks import router as webhooks_router

__all__ = [
    "consents_router", "authorize_router", "verify_router", 
    "payments_router", "dashboard_router", "admin_router",
    "limits_router", "rules_router", "analytics_router", "webhooks_router"
]


