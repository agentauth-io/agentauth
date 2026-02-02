"""
AgentAuth Core Authorization Engine
====================================
PROPRIETARY AND CONFIDENTIAL

This module contains the core authorization algorithms and cryptographic
infrastructure for AgentAuth. This is the crown jewel of the company.

Architecture:
- crypto.py     : Cryptographic primitives and key management
- policy.py     : Policy evaluation engine
- engine.py     : Authorization decision engine
- tokens.py     : Token generation and verification
- audit.py      : Immutable audit logging
- risk.py       : Risk scoring and anomaly detection
- main.py       : Unified entry point

Security Model:
- All keys derived from master secret using HKDF
- Ed25519 for signatures (proven, fast, small)
- ChaCha20-Poly1305 for encryption (modern, secure)
- SHA-256/BLAKE2b for hashing
- Constant-time comparisons throughout

Copyright (c) 2024-2026 AgentAuth Inc. All rights reserved.

NOTICE: This code is proprietary and confidential. Unauthorized copying,
distribution, or use of this code, via any medium, is strictly prohibited.
"""

__version__ = "0.1.0"
__author__ = "AgentAuth Core Team"

# Public API
from .main import AgentAuthCore, create_spending_policy
from .engine import AuthorizationRequest, AuthorizationResponse, AuthorizationStatus
from .policy import Policy, PolicyBuilder, PolicyEffect
from .tokens import AuthorizationToken, TokenType
from .risk import RiskAssessment, RiskLevel
from .audit import AuditLog, AuditEventType

__all__ = [
    # Main entry point
    "AgentAuthCore",
    "create_spending_policy",
    
    # Authorization
    "AuthorizationRequest",
    "AuthorizationResponse",
    "AuthorizationStatus",
    
    # Policy
    "Policy",
    "PolicyBuilder",
    "PolicyEffect",
    
    # Tokens
    "AuthorizationToken",
    "TokenType",
    
    # Risk
    "RiskAssessment",
    "RiskLevel",
    
    # Audit
    "AuditLog",
    "AuditEventType",
]
