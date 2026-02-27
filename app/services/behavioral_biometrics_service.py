"""
Behavioral Biometrics Service

Provides continuous authentication through behavioral analysis:
- Typing patterns (keystroke dynamics)
- Mouse movement patterns
- Touch gestures
- Navigation patterns
- Session behavior

Creates a behavioral profile for each user and detects anomalies
that may indicate account takeover or fraud.
"""
import math
import secrets
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.config import get_settings

settings = get_settings()


class BiometricRiskLevel(Enum):
    """Risk level based on behavioral biometrics."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TypingMetrics:
    """Keystroke dynamics metrics."""
    # Timing
    avg_keypress_duration_ms: float = 0.0    # Key down to up
    avg_key_interval_ms: float = 0.0          # Time between keys
    avg_digraph_ms: float = 0.0               # Time for 2-key combinations
    avg_trigraph_ms: float = 0.0              # Time for 3-key combinations
    
    # Variance
    keypress_variance: float = 0.0
    key_interval_variance: float = 0.0
    
    # Patterns
    backspace_ratio: float = 0.0              # Backspaces per character
    correction_ratio: float = 0.0              # Corrections per character
    delete_key_ratio: float = 0.0
    
    # Speed
    typing_speed_wpm: float = 0.0             # Words per minute
    
    # Counters
    total_keypresses: int = 0
    total_characters: int = 0


@dataclass
class MouseMetrics:
    """Mouse/touch movement metrics."""
    # Movement
    avg_movement_speed: float = 0.0          # Pixels per second
    avg_click_duration_ms: float = 0.0        # Click hold time
    
    # Patterns
    avg_path_directness: float = 0.0         # Straightness of movement
    avg_pause_duration_ms: float = 0.0        # Pause between movements
    
    # Clicks
    avg_clicks_per_minute: float = 0.0
    right_click_ratio: float = 0.0
    double_click_ratio: float = 0.0
    
    # Scroll
    avg_scroll_distance: float = 0.0
    scroll_frequency: float = 0.0
    
    # Counters
    total_movements: int = 0
    total_clicks: int = 0


@dataclass
class BehavioralProfile:
    """User's behavioral profile."""
    user_id: str
    
    # Typing profile
    typing: TypingMetrics
    
    # Mouse profile
    mouse: MouseMetrics
    
    # Metadata
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    sample_count: int = 0
    confidence: float = 0.0  # How confident we are in the profile


@dataclass
class BehavioralAssessment:
    """Behavioral biometrics assessment."""
    risk_level: BiometricRiskLevel
    risk_score: float  # 0.0 - 1.0
    
    # Component scores
    typing_score: float = 0.0  # How similar to profile (0 = different, 1 = same)
    mouse_score: float = 0.0
    
    # Analysis
    is_typing_anomaly: bool = False
    is_mouse_anomaly: bool = False
    
    # Factors
    factors: dict[str, Any] = field(default_factory=dict)
    
    # Recommendation
    recommendation: str = "allow"  # "allow", "review", "block"


class BehavioralBiometricsService:
    """
    Behavioral Biometrics Service.
    
    Analyzes user behavior patterns to detect:
    - Account takeover (different person using account)
    - Bot automation
    - Session hijacking
    - Fraudulent transactions
    """
    
    # Thresholds
    MIN_SAMPLES_FOR_PROFILE = 5  # Samples needed before profiling
    ANOMALY_THRESHOLD = 0.3     # Score below this = anomaly
    
    def __init__(self):
        # User profiles
        self._profiles: dict[str, BehavioralProfile] = {}
        
        # Raw samples (for training)
        self._samples: dict[str, list[dict]] = {}
        
        # Statistics
        self._stats = {
            "total_assessments": 0,
            "anomalies_detected": 0,
            "profiles_created": 0,
            "profiles_updated": 0,
        }

    # ==================== Profile Management ====================
    
    def get_or_create_profile(self, user_id: str) -> BehavioralProfile:
        """Get existing profile or create new one."""
        if user_id in self._profiles:
            return self._profiles[user_id]
        
        # Create new profile with default metrics
        profile = BehavioralProfile(
            user_id=user_id,
            typing=TypingMetrics(),
            mouse=MouseMetrics(),
        )
        self._profiles[user_id] = profile
        self._samples[user_id] = []
        
        return profile

    def add_typing_sample(
        self,
        user_id: str,
        keypress_durations: list[float],     # ms
        key_intervals: list[float],          # ms between key presses
        total_characters: int,
        backspace_count: int = 0,
        correction_count: int = 0,
    ):
        """Add typing sample to build profile."""
        if user_id not in self._samples:
            self._samples[user_id] = []
        
        sample = {
            "type": "typing",
            "keypress_durations": keypress_durations,
            "key_intervals": key_intervals,
            "total_characters": total_characters,
            "backspace_count": backspace_count,
            "correction_count": correction_count,
            "timestamp": time.time(),
        }
        
        self._samples[user_id].append(sample)
        
        # Update profile if enough samples
        if len(self._samples[user_id]) >= self.MIN_SAMPLES_FOR_PROFILE:
            self._update_profile(user_id)

    def add_mouse_sample(
        self,
        user_id: str,
        movements: list[dict],      # [{"dx": float, "dy": float, "duration_ms": float}]
        clicks: list[dict],        # [{"type": "left"|"right"|"double", "duration_ms": float}]
        scrolls: list[dict],       # [{"distance": float}]
    ):
        """Add mouse sample to build profile."""
        if user_id not in self._samples:
            self._samples[user_id] = []
        
        sample = {
            "type": "mouse",
            "movements": movements,
            "clicks": clicks,
            "scrolls": scrolls,
            "timestamp": time.time(),
        }
        
        self._samples[user_id].append(sample)
        
        # Update profile if enough samples
        if len(self._samples[user_id]) >= self.MIN_SAMPLES_FOR_PROFILE:
            self._update_profile(user_id)

    def _update_profile(self, user_id: str):
        """Update behavioral profile from samples."""
        samples = self._samples.get(user_id, [])
        typing_samples = [s for s in samples if s["type"] == "typing"]
        mouse_samples = [s for s in samples if s["type"] == "mouse"]
        
        profile = self.get_or_create_profile(user_id)
        
        # Update typing profile
        if typing_samples:
            self._update_typing_profile(profile, typing_samples)
        
        # Update mouse profile
        if mouse_samples:
            self._update_mouse_profile(profile, mouse_samples)
        
        # Update metadata
        profile.sample_count = len(samples)
        profile.last_updated = time.time()
        
        # Calculate confidence based on sample count
        profile.confidence = min(1.0, len(samples) / 20)
        
        if profile.sample_count == self.MIN_SAMPLES_FOR_PROFILE:
            self._stats["profiles_created"] += 1
        else:
            self._stats["profiles_updated"] += 1

    def _update_typing_profile(self, profile: BehavioralProfile, samples: list[dict]):
        """Update typing metrics from samples."""
        all_durations = []
        all_intervals = []
        total_chars = 0
        total_backspaces = 0
        total_corrections = 0
        
        for s in samples:
            all_durations.extend(s.get("keypress_durations", []))
            all_intervals.extend(s.get("key_intervals", []))
            total_chars += s.get("total_characters", 0)
            total_backspaces += s.get("backspace_count", 0)
            total_corrections += s.get("correction_count", 0)
        
        typing = profile.typing
        
        if all_durations:
            typing.avg_keypress_duration_ms = sum(all_durations) / len(all_durations)
            typing.keypress_variance = self._variance(all_durations)
        
        if all_intervals:
            typing.avg_key_interval_ms = sum(all_intervals) / len(all_intervals)
            typing.key_interval_variance = self._variance(all_intervals)
        
        if total_chars > 0:
            typing.backspace_ratio = total_backspaces / total_chars
            typing.correction_ratio = total_corrections / total_chars
        
        # Calculate WPM (assume average word = 5 chars)
        if all_intervals and total_chars > 0:
            total_time_ms = sum(all_intervals) + sum(all_durations)
            if total_time_ms > 0:
                words = total_chars / 5
                minutes = total_time_ms / 60000
                typing.typing_speed_wpm = words / minutes if minutes > 0 else 0
        
        typing.total_keypresses = len(all_durations)
        typing.total_characters = total_chars

    def _update_mouse_profile(self, profile: BehavioralProfile, samples: list[dict]):
        """Update mouse metrics from samples."""
        all_movements = []
        all_clicks = []
        all_scrolls = []
        
        for s in samples:
            all_movements.extend(s.get("movements", []))
            all_clicks.extend(s.get("clicks", []))
            all_scrolls.extend(s.get("scrolls", []))
        
        mouse = profile.mouse
        
        # Movement speed
        if all_movements:
            speeds = []
            
            for m in all_movements:
                dx = m.get("dx", 0)
                dy = m.get("dy", 0)
                duration = m.get("duration_ms", 1)
                
                distance = math.sqrt(dx**2 + dy**2)
                speed = distance / max(duration, 1) * 1000  # px/s
                speeds.append(speed)
            
            if speeds:
                mouse.avg_movement_speed = sum(speeds) / len(speeds)
                mouse.total_movements = len(all_movements)
        
        # Click patterns
        if all_clicks:
            left = sum(1 for c in all_clicks if c.get("type") == "left")
            right = sum(1 for c in all_clicks if c.get("type") == "right")
            double = sum(1 for c in all_clicks if c.get("type") == "double")
            
            total = left + right + double
            if total > 0:
                mouse.right_click_ratio = right / total
                mouse.double_click_ratio = double / total
            
            click_durations = [c.get("duration_ms", 0) for c in all_clicks]
            if click_durations:
                mouse.avg_click_duration_ms = sum(click_durations) / len(click_durations)
            
            mouse.total_clicks = total

    def _variance(self, values: list[float]) -> float:
        """Calculate variance."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)

    # ==================== Assessment ====================
    
    def assess(
        self,
        user_id: str,
        typing_sample: dict | None = None,
        mouse_sample: dict | None = None,
    ) -> BehavioralAssessment:
        """
        Assess behavioral biometrics.
        
        Compares current behavior to stored profile.
        """
        self._stats["total_assessments"] += 1
        
        profile = self.get_or_create_profile(user_id)
        
        # If no profile yet, can't detect anomaly
        if profile.sample_count < self.MIN_SAMPLES_FOR_PROFILE:
            return BehavioralAssessment(
                risk_level=BiometricRiskLevel.LOW,
                risk_score=0.0,
                recommendation="allow",
                factors={"reason": "insufficient_data"},
            )
        
        typing_score = 1.0
        mouse_score = 1.0
        factors = {}
        
        # Compare typing
        if typing_sample:
            typing_score = self._compare_typing(profile, typing_sample)
            factors["typing_score"] = typing_score
        
        # Compare mouse
        if mouse_sample:
            mouse_score = self._compare_mouse(profile, mouse_sample)
            factors["mouse_score"] = mouse_score
        
        # Combined score
        scores = []
        weights = []
        
        if typing_sample:
            scores.append(typing_score)
            weights.append(0.6)  # Typing is more distinctive
        
        if mouse_sample:
            scores.append(mouse_score)
            weights.append(0.4)
        
        if scores:
            combined = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        else:
            combined = 1.0
        
        # Convert similarity to anomaly score (inverse)
        anomaly_score = 1.0 - combined
        
        # Determine if anomaly
        is_anomaly = anomaly_score > (1.0 - self.ANOMALY_THRESHOLD)
        
        if is_anomaly:
            self._stats["anomalies_detected"] += 1
        
        # Risk level
        if anomaly_score >= 0.7:
            risk_level = BiometricRiskLevel.CRITICAL
            recommendation = "block"
        elif anomaly_score >= 0.5:
            risk_level = BiometricRiskLevel.HIGH
            recommendation = "block"
        elif anomaly_score >= 0.3:
            risk_level = BiometricRiskLevel.MEDIUM
            recommendation = "review"
        else:
            risk_level = BiometricRiskLevel.LOW
            recommendation = "allow"
        
        return BehavioralAssessment(
            risk_level=risk_level,
            risk_score=anomaly_score,
            typing_score=typing_score,
            mouse_score=mouse_score,
            is_typing_anomaly=typing_sample is not None and typing_score < self.ANOMALY_THRESHOLD,
            is_mouse_anomaly=mouse_sample is not None and mouse_score < self.ANOMALY_THRESHOLD,
            factors=factors,
            recommendation=recommendation,
        )

    def _compare_typing(self, profile: BehavioralProfile, sample: dict) -> float:
        """Compare typing sample to profile. Returns 0-1 (1 = identical)."""
        typing = profile.typing
        
        # Get sample metrics
        keypress_durations = sample.get("keypress_durations", [])
        key_intervals = sample.get("key_intervals", [])
        
        if not keypress_durations and not key_intervals:
            return 1.0
        
        scores = []
        
        # Compare keypress duration
        if keypress_durations and typing.avg_keypress_duration_ms > 0:
            sample_avg = sum(keypress_durations) / len(keypress_durations)
            diff = abs(sample_avg - typing.avg_keypress_duration_ms)
            # Allow 30% variance
            score = max(0, 1 - (diff / typing.avg_keypress_duration_ms))
            scores.append(score)
        
        # Compare key interval
        if key_intervals and typing.avg_key_interval_ms > 0:
            sample_avg = sum(key_intervals) / len(key_intervals)
            diff = abs(sample_avg - typing.avg_key_interval_ms)
            score = max(0, 1 - (diff / typing.avg_key_interval_ms))
            scores.append(score)
        
        return sum(scores) / len(scores) if scores else 1.0

    def _compare_mouse(self, profile: BehavioralProfile, sample: dict) -> float:
        """Compare mouse sample to profile. Returns 0-1 (1 = identical)."""
        mouse = profile.mouse
        
        movements = sample.get("movements", [])
        
        if not movements:
            return 1.0
        
        scores = []
        
        # Compare movement speed
        if movements and mouse.avg_movement_speed > 0:
            speeds = []
            for m in movements:
                dx = m.get("dx", 0)
                dy = m.get("dy", 0)
                duration = m.get("duration_ms", 1)
                distance = math.sqrt(dx**2 + dy**2)
                speed = distance / max(duration, 1) * 1000
                speeds.append(speed)
            
            if speeds:
                sample_avg = sum(speeds) / len(speeds)
                diff = abs(sample_avg - mouse.avg_movement_speed)
                score = max(0, 1 - (diff / mouse.avg_movement_speed))
                scores.append(score)
        
        return sum(scores) / len(scores) if scores else 1.0

    # ==================== Statistics ====================
    
    def get_stats(self) -> dict[str, Any]:
        """Get service statistics."""
        return {
            **self._stats,
            "profiles_count": len(self._profiles),
        }


# Singleton instance
_biometric_service: BehavioralBiometricsService | None = None


def get_biometric_service() -> BehavioralBiometricsService:
    """Get singleton biometric service."""
    global _biometric_service
    if _biometric_service is None:
        _biometric_service = BehavioralBiometricsService()
    return _biometric_service


# Convenience functions
def assess_behavior(user_id: str, **kwargs) -> BehavioralAssessment:
    """Assess behavioral biometrics."""
    service = get_biometric_service()
    return service.assess(user_id, **kwargs)
