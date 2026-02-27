"""
Session Management Service

Manages user sessions with advanced security features:
- Session creation and lifecycle
- Risk-based session scoring
- Continuous authentication
- Session anomaly detection
- Concurrent session management
- Token rotation

Features:
- JWT-based sessions with refresh tokens
- Risk scoring per session
- Automatic session invalidation on suspicious activity
- Session monitoring and analytics
"""
import secrets
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.config import get_settings

settings = get_settings()


class SessionStatus(Enum):
    """Session status."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"


class SessionRiskLevel(Enum):
    """Session risk level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Session:
    """User session."""
    session_id: str
    user_id: str
    
    # Token info
    access_token: str
    refresh_token: str
    token_version: int = 1
    
    # Context
    device_fingerprint: str | None = None
    ip_address: str = ""
    user_agent: str = ""
    location_country: str = ""
    location_city: str = ""
    
    # Timing
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    expires_at: float = 0.0
    refresh_expires_at: float = 0.0
    
    # Risk
    risk_level: SessionRiskLevel = SessionRiskLevel.LOW
    risk_score: float = 0.0
    
    # Status
    status: SessionStatus = SessionStatus.ACTIVE
    
    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionAssessment:
    """Session risk assessment."""
    session_id: str
    risk_level: SessionRiskLevel
    risk_score: float
    
    # Checks
    is_new_device: bool = False
    is_new_location: bool = False
    is_anomalous_activity: bool = False
    is_idle_session: bool = False
    is_concurrent: bool = False
    
    # Factors
    factors: dict[str, Any] = field(default_factory=dict)
    
    # Recommendation
    recommendation: str = "allow"  # "allow", "review", "revoke"
    message: str = ""


class SessionManager:
    """
    Session Management Service.
    
    Handles:
    - Session creation and validation
    - Risk-based access control
    - Token rotation
    - Concurrent session limits
    - Session monitoring
    """
    
    # Configuration
    ACCESS_TOKEN_TTL = 3600        # 1 hour
    REFRESH_TOKEN_TTL = 604800    # 7 days
    IDLE_TIMEOUT = 1800            # 30 minutes idle
    MAX_CONCURRENT_SESSIONS = 5
    
    def __init__(self):
        # Active sessions
        self._sessions: dict[str, Session] = {}
        
        # User sessions (user_id -> set of session_ids)
        self._user_sessions: dict[str, set[str]] = {}
        
        # Token to session mapping
        self._token_sessions: dict[str, str] = {}  # token -> session_id
        
        # Statistics
        self._stats = {
            "total_sessions": 0,
            "active_sessions": 0,
            "expired_sessions": 0,
            "revoked_sessions": 0,
            "concurrent_violations": 0,
            "risk_blocks": 0,
        }

    # ==================== Session Creation ====================
    
    def create_session(
        self,
        user_id: str,
        ip_address: str = "",
        user_agent: str = "",
        device_fingerprint: str | None = None,
        location_country: str = "",
        location_city: str = "",
        metadata: dict | None = None,
    ) -> Session:
        """
        Create a new session.
        
        Returns:
            Session with tokens
        """
        # Check concurrent session limit
        self._enforce_concurrent_limit(user_id)
        
        # Generate session ID
        session_id = f"ses_{secrets.token_urlsafe(16)}"
        
        # Generate tokens
        access_token = self._generate_token()
        refresh_token = self._generate_token()
        
        # Calculate expiry
        now = time.time()
        expires_at = now + self.ACCESS_TOKEN_TTL
        refresh_expires_at = now + self.REFRESH_TOKEN_TTL
        
        session = Session(
            session_id=session_id,
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            device_fingerprint=device_fingerprint,
            ip_address=ip_address,
            user_agent=user_agent,
            location_country=location_country,
            location_city=location_city,
            created_at=now,
            last_activity=now,
            expires_at=expires_at,
            refresh_expires_at=refresh_expires_at,
            metadata=metadata or {},
        )
        
        # Store session
        self._sessions[session_id] = session
        
        # Track user sessions
        if user_id not in self._user_sessions:
            self._user_sessions[user_id] = set()
        self._user_sessions[user_id].add(session_id)
        
        # Token mapping
        self._token_sessions[access_token] = session_id
        self._token_sessions[refresh_token] = session_id
        
        self._stats["total_sessions"] += 1
        self._stats["active_sessions"] += 1
        
        return session

    def _generate_token(self) -> str:
        """Generate a secure token."""
        return f"{secrets.token_urlsafe(32)}"

    def _enforce_concurrent_limit(self, user_id: str):
        """Enforce maximum concurrent sessions per user."""
        if user_id not in self._user_sessions:
            return
        
        # Get active sessions
        active = [
            sid for sid in self._user_sessions[user_id]
            if self._sessions.get(sid, Session("", "")).status == SessionStatus.ACTIVE
        ]
        
        # If over limit, revoke oldest
        if len(active) >= self.MAX_CONCURRENT_SESSIONS:
            # Sort by created_at
            sorted_sessions = sorted(
                active,
                key=lambda sid: self._sessions[sid].created_at
            )
            
            # Revoke oldest
            oldest_id = sorted_sessions[0]
            self.revoke_session(oldest_id, reason="concurrent_limit")
            self._stats["concurrent_violations"] += 1

    # ==================== Session Validation ====================
    
    def validate_access_token(self, access_token: str) -> Session | None:
        """Validate access token and return session."""
        session_id = self._token_sessions.get(access_token)
        if not session_id:
            return None
        
        session = self._sessions.get(session_id)
        if not session:
            return None
        
        # Check if expired
        if session.status != SessionStatus.ACTIVE:
            return None
        
        if time.time() > session.expires_at:
            self._expire_session(session_id)
            return None
        
        # Update last activity
        session.last_activity = time.time()
        
        return session

    def validate_refresh_token(self, refresh_token: str) -> Session | None:
        """Validate refresh token."""
        session_id = self._token_sessions.get(refresh_token)
        if not session_id:
            return None
        
        session = self._sessions.get(session_id)
        if not session:
            return None
        
        # Check if refresh token expired
        if time.time() > session.refresh_expires_at:
            return None
        
        return session

    # ==================== Token Rotation ====================
    
    def refresh_session(self, refresh_token: str) -> Session | None:
        """
        Refresh session tokens.
        
        Returns new session with rotated tokens.
        """
        session = self.validate_refresh_token(refresh_token)
        if not session:
            return None
        
        # Check risk before refresh
        assessment = self.assess_session(session.session_id)
        if assessment.recommendation == "revoke":
            self._stats["risk_blocks"] += 1
            return None
        
        # Revoke old tokens
        old_session_id = session.session_id
        old_access = session.access_token
        old_refresh = session.refresh_token
        
        # Create new session
        new_session = self.create_session(
            user_id=session.user_id,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            device_fingerprint=session.device_fingerprint,
            location_country=session.location_country,
            location_city=session.location_city,
            metadata=session.metadata,
        )
        
        # Revoke old session
        self.revoke_session(old_session_id, reason="token_refresh")
        
        return new_session

    # ==================== Session Assessment ====================
    
    def assess_session(self, session_id: str) -> SessionAssessment:
        """
        Assess session risk.
        
        Checks for anomalies and suspicious activity.
        """
        session = self._sessions.get(session_id)
        if not session:
            return SessionAssessment(
                session_id=session_id,
                risk_level=SessionRiskLevel.HIGH,
                risk_score=1.0,
                recommendation="revoke",
                message="Session not found",
            )
        
        factors = {}
        risk_score = 0.0
        
        # Check 1: Idle session
        idle_seconds = time.time() - session.last_activity
        if idle_seconds > self.IDLE_TIMEOUT:
            factors["idle_seconds"] = idle_seconds
            risk_score += 0.3
        
        # Check 2: Token age
        token_age = time.time() - session.created_at
        if token_age > 3600:  # Over 1 hour
            factors["token_age_hours"] = token_age / 3600
            risk_score += 0.1
        
        # Check 3: New device (would need device history - simplified)
        if session.device_fingerprint is None:
            factors["no_device_fingerprint"] = True
            risk_score += 0.2
        
        # Check 4: Concurrent sessions
        if session.user_id in self._user_sessions:
            active_count = len([
                sid for sid in self._user_sessions[session.user_id]
                if sid != session_id and self._sessions.get(sid, Session("", "")).status == SessionStatus.ACTIVE
            ])
            if active_count > 2:
                factors["many_concurrent_sessions"] = active_count
                risk_score += 0.2
        
        # Check 5: Risk level from creation
        if session.risk_level == SessionRiskLevel.HIGH:
            risk_score += 0.3
        elif session.risk_level == SessionRiskLevel.CRITICAL:
            risk_score += 0.5
        
        # Clamp
        risk_score = min(1.0, risk_score)
        
        # Determine level
        if risk_score >= 0.7:
            risk_level = SessionRiskLevel.CRITICAL
            recommendation = "revoke"
        elif risk_score >= 0.5:
            risk_level = SessionRiskLevel.HIGH
            recommendation = "revoke"
        elif risk_score >= 0.3:
            risk_level = SessionRiskLevel.MEDIUM
            recommendation = "review"
        else:
            risk_level = SessionRiskLevel.LOW
            recommendation = "allow"
        
        return SessionAssessment(
            session_id=session_id,
            risk_level=risk_level,
            risk_score=risk_score,
            is_idle_session=idle_seconds > self.IDLE_TIMEOUT,
            is_concurrent=factors.get("many_concurrent_sessions", 0) > 2,
            factors=factors,
            recommendation=recommendation,
            message=self._get_assessment_message(recommendation, factors),
        )

    def _get_assessment_message(self, recommendation: str, factors: dict) -> str:
        """Get human-readable assessment message."""
        if recommendation == "revoke":
            if "idle_seconds" in factors:
                return "Session expired due to inactivity"
            if "many_concurrent_sessions" in factors:
                return "Session revoked: too many concurrent sessions"
            return "Session revoked due to suspicious activity"
        if recommendation == "review":
            return "Session flagged for review"
        return "Session authorized"

    # ==================== Session Management ====================
    
    def revoke_session(self, session_id: str, reason: str = ""):
        """Revoke a session."""
        session = self._sessions.get(session_id)
        if not session:
            return
        
        # Remove token mappings
        if session.access_token in self._token_sessions:
            del self._token_sessions[session.access_token]
        if session.refresh_token in self._token_sessions:
            del self._token_sessions[session.refresh_token]
        
        # Update status
        session.status = SessionStatus.REVOKED
        
        # Remove from user sessions
        if session.user_id in self._user_sessions:
            self._user_sessions[session.user_id].discard(session_id)
        
        self._stats["active_sessions"] -= 1
        self._stats["revoked_sessions"] += 1

    def _expire_session(self, session_id: str):
        """Mark session as expired."""
        session = self._sessions.get(session_id)
        if not session:
            return
        
        session.status = SessionStatus.EXPIRED
        
        if session.user_id in self._user_sessions:
            self._user_sessions[session.user_id].discard(session_id)
        
        self._stats["active_sessions"] -= 1
        self._stats["expired_sessions"] += 1

    def revoke_all_user_sessions(self, user_id: str, reason: str = ""):
        """Revoke all sessions for a user."""
        if user_id not in self._user_sessions:
            return
        
        session_ids = list(self._user_sessions[user_id])
        for sid in session_ids:
            self.revoke_session(sid, reason)

    def get_user_sessions(self, user_id: str) -> list[Session]:
        """Get all active sessions for a user."""
        if user_id not in self._user_sessions:
            return []
        
        sessions = []
        for sid in self._user_sessions[user_id]:
            session = self._sessions.get(sid)
            if session and session.status == SessionStatus.ACTIVE:
                sessions.append(session)
        
        return sessions

    def get_session(self, session_id: str) -> Session | None:
        """Get session by ID."""
        return self._sessions.get(session_id)

    # ==================== Statistics ====================
    
    def get_stats(self) -> dict[str, Any]:
        """Get service statistics."""
        return {
            **self._stats,
            "total_sessions": len(self._sessions),
        }


# Singleton instance
_session_manager: SessionManager | None = None


def get_session_manager() -> SessionManager:
    """Get singleton session manager."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


# Convenience functions
def create_session(user_id: str, **kwargs) -> Session:
    """Create a new session."""
    manager = get_session_manager()
    return manager.create_session(user_id, **kwargs)


def validate_token(token: str) -> Session | None:
    """Validate an access token."""
    manager = get_session_manager()
    return manager.validate_access_token(token)


def refresh_session(refresh_token: str) -> Session | None:
    """Refresh session tokens."""
    manager = get_session_manager()
    return manager.refresh_session(refresh_token)
