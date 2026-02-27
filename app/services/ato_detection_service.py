"""
Account Takeover (ATO) Detection Service

Detects account takeover attempts through:
- Credential stuffing detection
- Password spraying detection
- Bruteforce detection
- Login anomaly detection
- New device/location patterns
- Behavioral changes

Features:
- Real-time threat detection
- Risk scoring per login attempt
- Automatic account locking
- Alert generation
"""
import secrets
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.config import get_settings

settings = get_settings()


class AtoRiskLevel(Enum):
    """Account takeover risk level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class LoginAttempt:
    """A login attempt record."""
    attempt_id: str
    user_id: str
    timestamp: float

    # Context
    ip_address: str
    user_agent: str
    device_fingerprint: str | None
    location_country: str
    location_city: str

    # Result
    success: bool
    failure_reason: str | None = None

    # Risk indicators
    is_new_device: bool = False
    is_new_location: bool = False
    is_vpn: bool = False
    is_proxy: bool = False


@dataclass
class AtoAssessment:
    """Account takeover risk assessment."""
    risk_level: AtoRiskLevel
    risk_score: float  # 0.0 - 1.0

    # Detection signals
    is_credential_stuffing: bool = False
    is_password_spraying: bool = False
    is_bruteforce: bool = False
    is_new_device_attack: bool = False
    is_new_location_attack: bool = False
    is_behavioral_anomaly: bool = False

    # Details
    failed_attempts_count: int = 0
    unique_ips: int = 0
    time_window_hours: float = 0.0

    # Factors
    factors: dict[str, Any] = field(default_factory=dict)

    # Recommendation
    recommendation: str = "allow"  # "allow", "review", "block", "lock"
    message: str = ""


class AtoDetectionService:
    """
    Account Takeover Detection Service.
    
    Monitors login patterns and detects:
    - Credential stuffing (same credentials across many accounts)
    - Password spraying (common passwords tried across many users)
    - Bruteforce (many attempts for single account)
    - Anomalous login patterns
    """

    # Thresholds
    MAX_FAILED_ATTEMPTS_PER_HOUR = 5
    MAX_UNIQUE_IPS_PER_HOUR = 3
    CREDENTIAL_STUFFING_THRESHOLD = 10  # Same credentials across N users
    PASSWORD_SPRAYING_THRESHOLD = 20    # Same password tried across N users

    def __init__(self):
        # Login history per user
        self._user_login_history: dict[str, list[LoginAttempt]] = {}

        # IP-based tracking (for credential stuffing/spraying)
        self._ip_attempts: dict[str, list[dict]] = {}  # ip -> attempts
        self._credential_attempts: dict[str, set[str]] = {}  # hashed_credential -> user_ids

        # Statistics
        self._stats = {
            "total_attempts": 0,
            "blocked_attempts": 0,
            "locked_accounts": 0,
            "credential_stuffing_detected": 0,
            "password_spraying_detected": 0,  # nosec: B105 - Dictionary key name, not a password
            "bruteforce_detected": 0,
        }

        # Locked accounts
        self._locked_accounts: dict[str, float] = {}  # user_id -> unlock_time

    # ==================== Record Login Attempt ====================

    def record_attempt(
        self,
        user_id: str,
        ip_address: str,
        user_agent: str,
        device_fingerprint: str | None,
        success: bool,
        failure_reason: str | None = None,
        location_country: str = "",
        location_city: str = "",
        is_vpn: bool = False,
        is_proxy: bool = False,
    ) -> LoginAttempt:
        """Record a login attempt."""
        attempt_id = secrets.token_urlsafe(8)

        attempt = LoginAttempt(
            attempt_id=attempt_id,
            user_id=user_id,
            timestamp=time.time(),
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            location_country=location_country,
            location_city=location_city,
            success=success,
            failure_reason=failure_reason,
            is_vpn=is_vpn,
            is_proxy=is_proxy,
        )

        # Store in user history
        if user_id not in self._user_login_history:
            self._user_login_history[user_id] = []
        self._user_login_history[user_id].append(attempt)

        # Keep only last 100 attempts
        if len(self._user_login_history[user_id]) > 100:
            self._user_login_history[user_id] = self._user_login_history[user_id][-100:]

        # Store in IP history
        if ip_address not in self._ip_attempts:
            self._ip_attempts[ip_address] = []
        self._ip_attempts[ip_address].append({
            "user_id": user_id,
            "success": success,
            "timestamp": time.time(),
        })

        # Clean old IP attempts (keep last hour)
        self._clean_ip_history()

        self._stats["total_attempts"] += 1

        if not success:
            self._stats["blocked_attempts"] += 1

        return attempt

    def _clean_ip_history(self):
        """Clean old IP attempts (older than 1 hour)."""
        cutoff = time.time() - 3600
        for ip in list(self._ip_attempts.keys()):
            self._ip_attempts[ip] = [
                a for a in self._ip_attempts[ip]
                if a["timestamp"] > cutoff
            ]
            if not self._ip_attempts[ip]:
                del self._ip_attempts[ip]

    # ==================== Detect Attacks ====================

    def detect_credential_stuffing(
        self,
        user_id: str,
        ip_address: str,
    ) -> bool:
        """
        Detect credential stuffing attack.
        
        Credential stuffing = same IP trying many different user accounts.
        """
        if ip_address not in self._ip_attempts:
            return False

        attempts = self._ip_attempts[ip_address]

        # Count unique users from this IP in last hour
        unique_users = set(a["user_id"] for a in attempts)

        if len(unique_users) >= self.CREDENTIAL_STUFFING_THRESHOLD:
            self._stats["credential_stuffing_detected"] += 1
            return True

        return False

    def detect_password_spraying(
        self,
        user_id: str,
        password_hash: str,
    ) -> bool:
        """
        Detect password spraying attack.
        
        Password spraying = same password tried across many user accounts.
        """
        # Track hashed password attempts
        if password_hash not in self._credential_attempts:
            self._credential_attempts[password_hash] = set()

        self._credential_attempts[password_hash].add(user_id)

        # Check if exceeded threshold
        if len(self._credential_attempts[password_hash]) >= self.PASSWORD_SPRAYING_THRESHOLD:
            self._stats["password_spraying_detected"] += 1
            return True

        return False

    def detect_bruteforce(self, user_id: str) -> tuple[bool, int]:
        """
        Detect bruteforce attack.
        
        Bruteforce = many failed attempts for single account.
        
        Returns:
            (is_bruteforce, failed_count)
        """
        if user_id not in self._user_login_history:
            return (False, 0)

        # Get attempts from last hour
        cutoff = time.time() - 3600
        recent_attempts = [
            a for a in self._user_login_history[user_id]
            if a.timestamp > cutoff
        ]

        # Count failed attempts
        failed_count = sum(1 for a in recent_attempts if not a.success)

        if failed_count >= self.MAX_FAILED_ATTEMPTS_PER_HOUR:
            self._stats["bruteforce_detected"] += 1
            return (True, failed_count)

        return (False, failed_count)

    # ==================== Assess ATO Risk ====================

    def assess_risk(
        self,
        user_id: str,
        ip_address: str,
        user_agent: str,
        device_fingerprint: str | None,
        success: bool,
        location_country: str = "",
        location_city: str = "",
        is_vpn: bool = False,
        is_proxy: bool = False,
    ) -> AtoAssessment:
        """
        Assess account takeover risk for a login attempt.
        """
        # Check if account is locked
        if user_id in self._locked_accounts:
            if time.time() < self._locked_accounts[user_id]:
                return AtoAssessment(
                    risk_level=AtoRiskLevel.CRITICAL,
                    risk_score=1.0,
                    recommendation="block",
                    message="Account is temporarily locked due to suspicious activity",
                )
            else:
                # Unlock expired
                del self._locked_accounts[user_id]

        # Get recent login history
        history = self._user_login_history.get(user_id, [])

        # Get attempts from last hour
        cutoff = time.time() - 3600
        recent = [a for a in history if a.timestamp > cutoff]

        # Calculate factors
        factors = {}
        risk_score = 0.0

        # Factor 1: Failed attempts
        failed_count = sum(1 for a in recent if not a.success)
        if failed_count > 0:
            factors["failed_attempts_1h"] = failed_count
            risk_score += min(0.4, failed_count * 0.1)

        # Factor 2: Bruteforce detection
        is_bruteforce, _ = self.detect_bruteforce(user_id)
        if is_bruteforce:
            factors["bruteforce_detected"] = True
            risk_score += 0.5

        # Factor 3: Credential stuffing
        is_stuffing = self.detect_credential_stuffing(user_id, ip_address)
        if is_stuffing:
            factors["credential_stuffing_detected"] = True
            risk_score += 0.6

        # Factor 4: New device
        if device_fingerprint:
            known_devices = self._get_known_devices(user_id)
            if device_fingerprint not in known_devices:
                factors["new_device"] = True
                risk_score += 0.2

        # Factor 5: New location
        known_locations = self._get_known_locations(user_id)
        current_location = f"{location_country}/{location_city}"
        if current_location not in known_locations and location_country:
            factors["new_location"] = True
            risk_score += 0.15

        # Factor 6: VPN/Proxy
        if is_vpn:
            factors["vpn_detected"] = True
            risk_score += 0.25
        if is_proxy:
            factors["proxy_detected"] = True
            risk_score += 0.3

        # Factor 7: Time-based anomaly (login at unusual hour)
        hour = time.localtime().tm_hour
        if hour < 6 or hour > 22:  # Late night/early morning
            factors["unusual_hour"] = True
            risk_score += 0.1

        # Determine risk level
        if risk_score >= 0.7:
            risk_level = AtoRiskLevel.CRITICAL
            recommendation = "lock"
        elif risk_score >= 0.5:
            risk_level = AtoRiskLevel.HIGH
            recommendation = "block"
        elif risk_score >= 0.3:
            risk_level = AtoRiskLevel.MEDIUM
            recommendation = "review"
        else:
            risk_level = AtoRiskLevel.LOW
            recommendation = "allow"

        # Count unique IPs
        unique_ips = len(set(a.ip_address for a in recent))

        # Lock account if critical
        if recommendation == "lock":
            self._lock_account(user_id)

        return AtoAssessment(
            risk_level=risk_level,
            risk_score=min(1.0, risk_score),
            is_bruteforce=is_bruteforce,
            is_credential_stuffing=is_stuffing,
            failed_attempts_count=failed_count,
            unique_ips=unique_ips,
            time_window_hours=1.0,
            factors=factors,
            recommendation=recommendation,
            message=self._get_message(recommendation, factors),
        )

    def _get_known_devices(self, user_id: str) -> set[str]:
        """Get known device fingerprints for user."""
        devices = set()
        history = self._user_login_history.get(user_id, [])
        for attempt in history:
            if attempt.device_fingerprint:
                devices.add(attempt.device_fingerprint)
        return devices

    def _get_known_locations(self, user_id: str) -> set[str]:
        """Get known locations for user."""
        locations = set()
        history = self._user_login_history.get(user_id, [])
        for attempt in history:
            if attempt.location_country:
                locations.add(f"{attempt.location_country}/{attempt.location_city}")
        return locations

    def _get_message(self, recommendation: str, factors: dict) -> str:
        """Get human-readable message."""
        if recommendation == "lock":
            return "Account temporarily locked due to suspicious activity"
        if recommendation == "block":
            if factors.get("bruteforce_detected"):
                return "Login blocked: too many failed attempts"
            if factors.get("credential_stuffing_detected"):
                return "Login blocked: suspicious activity detected"
            return "Login blocked due to high risk"
        if recommendation == "review":
            return "Login flagged for review"
        return "Login allowed"

    # ==================== Account Locking ====================

    def _lock_account(self, user_id: str, duration_seconds: int = 1800):
        """Lock an account (30 minutes default)."""
        self._locked_accounts[user_id] = time.time() + duration_seconds
        self._stats["locked_accounts"] += 1

    def unlock_account(self, user_id: str):
        """Manually unlock an account."""
        if user_id in self._locked_accounts:
            del self._locked_accounts[user_id]

    def is_locked(self, user_id: str) -> bool:
        """Check if account is locked."""
        if user_id not in self._locked_accounts:
            return False
        if time.time() > self._locked_accounts[user_id]:
            del self._locked_accounts[user_id]
            return False
        return True

    # ==================== Statistics ====================

    def get_stats(self) -> dict[str, Any]:
        """Get service statistics."""
        return {
            **self._stats,
            "locked_accounts": len(self._locked_accounts),
        }


# Singleton instance
_ato_service: AtoDetectionService | None = None


def get_ato_service() -> AtoDetectionService:
    """Get singleton ATO detection service."""
    global _ato_service
    if _ato_service is None:
        _ato_service = AtoDetectionService()
    return _ato_service


# Convenience functions
def assess_ato_risk(user_id: str, ip_address: str, **kwargs) -> AtoAssessment:
    """Assess account takeover risk."""
    service = get_ato_service()
    return service.assess_risk(user_id, ip_address, **kwargs)


def record_login_attempt(user_id: str, ip_address: str, **kwargs) -> LoginAttempt:
    """Record a login attempt."""
    service = get_ato_service()
    return service.record_attempt(user_id, ip_address, **kwargs)
