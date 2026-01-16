"""
AgentAuth Python SDK

The authorization layer for AI agent purchases.
"""
from agentauth.client import AgentAuth, AsyncAgentAuth
from agentauth.models import (
    Consent,
    Authorization,
    Verification,
    ConsentProof,
)
from agentauth.exceptions import (
    AgentAuthError,
    AuthorizationDenied,
    InvalidToken,
    VerificationFailed,
)

# Framework integrations (optional dependencies)
from agentauth import integrations

__version__ = "0.2.0"
__all__ = [
    "AgentAuth",
    "AsyncAgentAuth",
    "Consent",
    "Authorization",
    "Verification",
    "ConsentProof",
    "AgentAuthError",
    "AuthorizationDenied",
    "InvalidToken",
    "VerificationFailed",
    "integrations",
]

