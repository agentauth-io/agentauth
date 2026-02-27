"""
Device Fingerprinting Service

Provides device identification and risk assessment based on:
- Browser fingerprints
- Device characteristics
- Behavioral patterns
- Historical device trust scores

Used for fraud detection and account takeover prevention.
"""

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.config import get_settings

settings = get_settings()


class DeviceRiskLevel(Enum):
    """Risk level based on device characteristics."""

    TRUSTED = "trusted"  # Known, trusted device
    NEW = "new"  # New device, needs verification
    SUSPICIOUS = "suspicious"  # Known suspicious patterns
    COMPROMISED = "compromised"  # Known compromised


@dataclass
class DeviceFingerprint:
    """Device fingerprint data."""

    fingerprint_id: str

    # Device characteristics
    user_agent: str
    platform: str
    browser: str
    device_type: str  # "desktop", "mobile", "tablet", "bot"

    # Hardware identifiers (hashed)
    screen_resolution: str
    timezone: str
    language: str
    color_depth: int

    # Canvas/WebGL fingerprint (hashed)
    canvas_hash: str | None = None
    webgl_hash: str | None = None

    # Behavioral
    touch_support: bool = False
    max_touch_points: int = 0

    # Metadata
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    seen_count: int = 1


@dataclass
class DeviceAssessment:
    """Assessment of a device for a transaction."""

    fingerprint_id: str
    risk_level: DeviceRiskLevel
    risk_score: float  # 0.0 - 1.0

    # Assessment details
    is_known_device: bool
    is_new_device: bool
    is_emulator: bool
    is_bot: bool
    is_vpn: bool
    is_proxy: bool

    # Factors
    factors: dict[str, Any] = field(default_factory=dict)

    # Trust history
    transaction_count: int = 0
    last_transaction_days_ago: int = 0
    trust_score: float = 0.5  # 0.0 - 1.0

    # Recommendation
    recommendation: str = "allow"  # "allow", "review", "block"


class DeviceFingerprintService:
    """
    Device fingerprinting service.

    Identifies devices and assesses risk based on:
    - Fingerprint matching
    - Known device history
    - Anomaly detection
    - Threat intelligence
    """

    # Known bot user agents
    BOT_PATTERNS = [
        "bot",
        "crawler",
        "spider",
        "curl",
        "wget",
        "headless",
        "phantom",
        "selenium",
        "playwright",
        "puppeteer",
    ]

    # Suspicious indicators
    SUSPICIOUS_INDICATORS = [
        "emulator",
        "genymotion",
        "bluestacks",
        "nox",
        "virtualbox",
        "vmware",
        "qemu",
    ]

    def __init__(self):
        # Device fingerprint storage
        self._devices: dict[str, DeviceFingerprint] = {}

        # Device-to-user mapping
        self._device_users: dict[str, set[str]] = {}  # fingerprint_id -> user_ids

        # Trust scores (device_id -> score)
        self._trust_scores: dict[str, float] = {}

        # Transaction history per device
        self._device_transactions: dict[str, list[dict]] = {}

        # Statistics
        self._stats = {
            "total_fingerprints": 0,
            "new_devices": 0,
            "trusted_devices": 0,
            "suspicious_devices": 0,
            "blocked_devices": 0,
        }

    # ==================== Fingerprint Generation ====================

    def create_fingerprint(
        self,
        user_agent: str,
        platform: str,
        screen_resolution: str,
        timezone: str,
        language: str,
        color_depth: int = 24,
        canvas_hash: str | None = None,
        webgl_hash: str | None = None,
        touch_support: bool = False,
        max_touch_points: int = 0,
    ) -> str:
        """
        Create a device fingerprint.

        Returns:
            fingerprint_id (hash-based identifier)
        """
        # Build fingerprint data
        fp_data = f"{user_agent}:{platform}:{screen_resolution}:{timezone}:{language}:{color_depth}"
        if canvas_hash:
            fp_data += f":{canvas_hash}"
        if webgl_hash:
            fp_data += f":{webgl_hash}"

        # Generate stable ID from fingerprint data
        fingerprint_id = hashlib.sha256(fp_data.encode()).hexdigest()[:32]

        # Determine device type
        device_type = self._detect_device_type(user_agent, platform)

        # Determine browser
        browser = self._detect_browser(user_agent)

        # Store or update fingerprint
        if fingerprint_id not in self._devices:
            self._devices[fingerprint_id] = DeviceFingerprint(
                fingerprint_id=fingerprint_id,
                user_agent=user_agent,
                platform=platform,
                browser=browser,
                device_type=device_type,
                screen_resolution=screen_resolution,
                timezone=timezone,
                language=language,
                color_depth=color_depth,
                canvas_hash=canvas_hash,
                webgl_hash=webgl_hash,
                touch_support=touch_support,
                max_touch_points=max_touch_points,
            )
            self._stats["total_fingerprints"] += 1
            self._stats["new_devices"] += 1
        else:
            # Update existing
            fp = self._devices[fingerprint_id]
            fp.last_seen = time.time()
            fp.seen_count += 1

        return fingerprint_id

    def _detect_device_type(self, user_agent: str, platform: str) -> str:
        """Detect device type from user agent."""
        ua_lower = user_agent.lower()

        # Check for mobile
        if any(p in ua_lower for p in ["mobile", "android", "iphone", "ipad", "ipod"]):
            return "mobile"

        # Check for tablet
        if "tablet" in ua_lower or "ipad" in ua_lower:
            return "tablet"

        # Check for bot
        if any(bot in ua_lower for bot in self.BOT_PATTERNS):
            return "bot"

        return "desktop"

    def _detect_browser(self, user_agent: str) -> str:
        """Detect browser from user agent."""
        ua_lower = user_agent.lower()

        if "chrome" in ua_lower and "edg" not in ua_lower:
            return "chrome"
        elif "firefox" in ua_lower:
            return "firefox"
        elif "safari" in ua_lower and "chrome" not in ua_lower:
            return "safari"
        elif "edg" in ua_lower:
            return "edge"
        elif "opera" in ua_lower or "opr" in ua_lower:
            return "opera"

        return "unknown"

    # ==================== Device Assessment ====================

    def assess_device(
        self,
        fingerprint_id: str,
        user_id: str,
    ) -> DeviceAssessment:
        """
        Assess device risk for a transaction.

        Returns:
            DeviceAssessment with risk evaluation
        """
        # Check if device exists
        if fingerprint_id not in self._devices:
            # Unknown device
            return DeviceAssessment(
                fingerprint_id=fingerprint_id,
                risk_level=DeviceRiskLevel.NEW,
                risk_score=0.5,
                is_known_device=False,
                is_new_device=True,
                is_emulator=False,
                is_bot=False,
                is_vpn=False,
                is_proxy=False,
                factors={"reason": "unknown_device"},
                recommendation="review",
            )

        fp = self._devices[fingerprint_id]

        # Track user-device association
        if fingerprint_id not in self._device_users:
            self._device_users[fingerprint_id] = set()
        self._device_users[fingerprint_id].add(user_id)

        # Check if known for this user
        is_known_device = user_id in self._device_users.get(fingerprint_id, set())

        # Calculate risk factors
        factors = {}
        risk_score = 0.0

        # Factor: Device type
        if fp.device_type == "bot":
            factors["bot_detected"] = True
            risk_score += 0.9
        elif fp.device_type in ["mobile", "tablet"]:
            factors["mobile_device"] = True
            risk_score += 0.1

        # Factor: Known device
        if not is_known_device:
            factors["new_user_device"] = True
            risk_score += 0.3

        # Factor: Device age (newly seen)
        device_age_days = (time.time() - fp.first_seen) / 86400
        if device_age_days < 1:
            factors["recent_device"] = True
            risk_score += 0.2
        elif device_age_days > 30:
            factors["old_device"] = True
            risk_score -= 0.1  # Lower risk for established devices

        # Factor: Usage frequency
        if fp.seen_count < 3:
            factors["low_usage"] = True
            risk_score += 0.15

        # Factor: User agent analysis
        if any(ind in fp.user_agent.lower() for ind in self.SUSPICIOUS_INDICATORS):
            factors["emulator_detected"] = True
            risk_score += 0.5

        # Factor: VPN/Proxy (simplified check - in production would use external service)
        # For demo, assume some patterns indicate VPN
        if "vpn" in fp.user_agent.lower() or "proxy" in fp.user_agent.lower():
            factors["vpn_detected"] = True
            risk_score += 0.3

        # Get trust score
        trust_score = self._trust_scores.get(fingerprint_id, 0.5)

        # Adjust risk based on trust
        risk_score = risk_score * (1 - trust_score * 0.5)

        # Clamp risk score
        risk_score = max(0.0, min(1.0, risk_score))

        # Determine risk level
        if risk_score < 0.2:
            risk_level = DeviceRiskLevel.TRUSTED
            recommendation = "allow"
            self._stats["trusted_devices"] += 1
        elif risk_score < 0.5:
            risk_level = DeviceRiskLevel.NEW
            recommendation = "review"
        else:
            risk_level = DeviceRiskLevel.SUSPICIOUS
            recommendation = "block"
            self._stats["suspicious_devices"] += 1

        # Get transaction history
        txn_history = self._device_transactions.get(fingerprint_id, [])
        last_txn_days = 0
        if txn_history:
            last_txn_days = int((time.time() - txn_history[-1]["timestamp"]) / 86400)

        return DeviceAssessment(
            fingerprint_id=fingerprint_id,
            risk_level=risk_level,
            risk_score=risk_score,
            is_known_device=is_known_device,
            is_new_device=not is_known_device or device_age_days < 7,
            is_emulator=factors.get("emulator_detected", False),
            is_bot=fp.device_type == "bot",
            is_vpn=factors.get("vpn_detected", False),
            is_proxy=False,
            factors=factors,
            transaction_count=fp.seen_count,
            last_transaction_days_ago=last_txn_days,
            trust_score=trust_score,
            recommendation=recommendation,
        )

    # ==================== Trust Management ====================

    def record_successful_transaction(
        self,
        fingerprint_id: str,
        user_id: str,
        amount: float,
    ):
        """Record a successful transaction to build trust."""
        # Update trust score
        current = self._trust_scores.get(fingerprint_id, 0.5)
        # Increase trust slightly for successful transactions
        self._trust_scores[fingerprint_id] = min(1.0, current + 0.05)

        # Record transaction
        if fingerprint_id not in self._device_transactions:
            self._device_transactions[fingerprint_id] = []

        self._device_transactions[fingerprint_id].append(
            {
                "user_id": user_id,
                "amount": amount,
                "timestamp": time.time(),
                "success": True,
            }
        )

        # Limit history
        if len(self._device_transactions[fingerprint_id]) > 100:
            self._device_transactions[fingerprint_id] = self._device_transactions[
                fingerprint_id
            ][-100:]

    def record_failed_transaction(
        self,
        fingerprint_id: str,
        user_id: str,
        amount: float,
        reason: str,
    ):
        """Record a failed transaction (fraud attempt)."""
        # Decrease trust
        current = self._trust_scores.get(fingerprint_id, 0.5)
        self._trust_scores[fingerprint_id] = max(0.0, current - 0.2)

        # Check if should block
        if current < 0.2:
            self._stats["blocked_devices"] += 1

        # Record transaction
        if fingerprint_id not in self._device_transactions:
            self._device_transactions[fingerprint_id] = []

        self._device_transactions[fingerprint_id].append(
            {
                "user_id": user_id,
                "amount": amount,
                "timestamp": time.time(),
                "success": False,
                "reason": reason,
            }
        )

    def trust_device(self, fingerprint_id: str):
        """Explicitly trust a device (e.g., after 2FA)."""
        self._trust_scores[fingerprint_id] = 1.0

    def block_device(self, fingerprint_id: str):
        """Explicitly block a device."""
        self._trust_scores[fingerprint_id] = 0.0
        self._stats["blocked_devices"] += 1

    # ==================== Query ====================

    def get_device(self, fingerprint_id: str) -> DeviceFingerprint | None:
        """Get device fingerprint."""
        return self._devices.get(fingerprint_id)

    def get_user_devices(self, user_id: str) -> list[DeviceFingerprint]:
        """Get all devices associated with a user."""
        devices = []
        for fp_id, users in self._device_users.items():
            if user_id in users:
                fp = self._devices.get(fp_id)
                if fp:
                    devices.append(fp)
        return devices

    def get_trust_score(self, fingerprint_id: str) -> float:
        """Get trust score for a device."""
        return self._trust_scores.get(fingerprint_id, 0.5)

    # ==================== Statistics ====================

    def get_stats(self) -> dict[str, Any]:
        """Get service statistics."""
        return {
            **self._stats,
            "total_devices": len(self._devices),
            "active_devices": len(self._trust_scores),
        }


# Singleton instance
_device_service: DeviceFingerprintService | None = None


def get_device_service() -> DeviceFingerprintService:
    """Get singleton device fingerprint service."""
    global _device_service
    if _device_service is None:
        _device_service = DeviceFingerprintService()
    return _device_service


# Convenience functions
def create_fingerprint(**kwargs) -> str:
    """Create a device fingerprint."""
    service = get_device_service()
    return service.create_fingerprint(**kwargs)


def assess_device(fingerprint_id: str, user_id: str) -> DeviceAssessment:
    """Assess device risk."""
    service = get_device_service()
    return service.assess_device(fingerprint_id, user_id)


def record_transaction(
    fingerprint_id: str, user_id: str, amount: float, success: bool = True
):
    """Record transaction for device trust."""
    service = get_device_service()
    if success:
        service.record_successful_transaction(fingerprint_id, user_id, amount)
    else:
        service.record_failed_transaction(fingerprint_id, user_id, amount, "failed")
