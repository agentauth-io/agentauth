"""
Geo-Velocity and Location Risk Service

Provides location-based risk assessment:
- Geo-velocity checks (impossible travel detection)
- Country/region risk scoring
- Location anomaly detection
- Timezone-based risk

Impossible Travel: Detects if user could physically travel between
two locations in the observed time window.
"""

import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.config import get_settings

settings = get_settings()


class LocationRiskLevel(Enum):
    """Risk level based on location analysis."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Location:
    """Geographic location."""

    latitude: float
    longitude: float
    country: str = ""
    region: str = ""
    city: str = ""
    timezone: str = ""
    ip_address: str = ""
    is_vpn: bool = False
    is_proxy: bool = False

    def distance_to(self, other: "Location") -> float:
        """Calculate distance to another location in km (Haversine formula)."""
        R = 6371  # Earth's radius in km

        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(other.latitude), math.radians(other.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        return R * c


@dataclass
class TransactionLocation:
    """Location data for a transaction."""

    location: Location
    timestamp: float
    accuracy_km: float = 10.0  # GPS accuracy


@dataclass
class GeoVelocityResult:
    """Result of geo-velocity/impossible travel check."""

    is_impossible_travel: bool
    risk_score: float  # 0.0 - 1.0

    # Details
    previous_location: Location | None = None
    current_location: Location | None = None
    distance_km: float = 0.0
    time_difference_hours: float = 0.0
    required_speed_kmh: float = 0.0  # Speed needed to make the trip

    # Travel modes (what speed would be required)
    is_air_travel: bool = False
    is_ground_impossible: bool = False

    factors: dict[str, Any] = field(default_factory=dict)
    recommendation: str = "allow"  # "allow", "review", "block"


@dataclass
class LocationRiskResult:
    """Complete location risk assessment."""

    risk_level: LocationRiskLevel
    risk_score: float

    # Components
    geo_velocity: GeoVelocityResult | None = None
    country_risk: float = 0.0
    timezone_risk: float = 0.0

    # Details
    factors: dict[str, Any] = field(default_factory=dict)
    recommendation: str = "allow"


class GeoVelocityService:
    """
    Geo-velocity and location risk service.

    Detects:
    - Impossible travel (same user, distant locations, short time)
    - High-risk countries
    - Timezone anomalies
    - VPN/Proxy usage
    """

    # High-risk countries (simplified list)
    HIGH_RISK_COUNTRIES = {
        "XX",  # Unknown/Anonymous
    }

    # Medium-risk countries
    MEDIUM_RISK_COUNTRIES = {
        # Add countries as needed
    }

    # Country risk scores (0.0 - 1.0)
    COUNTRY_RISK_SCORES = {
        "US": 0.05,
        "GB": 0.05,
        "CA": 0.05,
        "DE": 0.05,
        "FR": 0.05,
        "JP": 0.05,
        "AU": 0.05,
        "XX": 0.9,  # Unknown
    }

    # Maximum realistic travel speeds (km/h)
    MAX_SPEEDS = {
        "walk": 7,  # Walking
        "car": 120,  # Highway driving
        "train": 320,  # High-speed train
        "plane": 900,  # Commercial flight (with takeoff/landing)
        "impossible": 9999,  # Beyond any realistic travel
    }

    def __init__(self):
        # Location history per user (last N locations)
        self._user_locations: dict[str, list[TransactionLocation]] = {}
        self._max_history = 10

        # Statistics
        self._stats = {
            "total_checks": 0,
            "impossible_travel_detected": 0,
            "high_risk_countries": 0,
            "vpn_detected": 0,
        }

    # ==================== Location Recording ====================

    def record_location(
        self,
        user_id: str,
        latitude: float,
        longitude: float,
        country: str = "",
        region: str = "",
        city: str = "",
        timezone: str = "",
        ip_address: str = "",
        is_vpn: bool = False,
        is_proxy: bool = False,
    ):
        """Record a location for a user."""
        location = Location(
            latitude=latitude,
            longitude=longitude,
            country=country,
            region=region,
            city=city,
            timezone=timezone,
            ip_address=ip_address,
            is_vpn=is_vpn,
            is_proxy=is_proxy,
        )

        txn_location = TransactionLocation(
            location=location,
            timestamp=time.time(),
        )

        if user_id not in self._user_locations:
            self._user_locations[user_id] = []

        self._user_locations[user_id].append(txn_location)

        # Limit history
        if len(self._user_locations[user_id]) > self._max_history:
            self._user_locations[user_id] = self._user_locations[user_id][
                -self._max_history :
            ]

    def get_last_location(self, user_id: str) -> TransactionLocation | None:
        """Get the last recorded location for a user."""
        locations = self._user_locations.get(user_id, [])
        return locations[-1] if locations else None

    def get_location_history(self, user_id: str) -> list[TransactionLocation]:
        """Get location history for a user."""
        return self._user_locations.get(user_id, [])

    # ==================== Geo-Velocity Check ====================

    def check_geo_velocity(
        self,
        user_id: str,
        current_location: Location,
    ) -> GeoVelocityResult:
        """
        Check for impossible travel.

        Compares current location to previous locations and
        calculates if travel is physically possible in the time elapsed.
        """
        self._stats["total_checks"] += 1

        history = self._user_locations.get(user_id, [])

        if not history:
            # No history - can't check impossible travel
            return GeoVelocityResult(
                is_impossible_travel=False,
                risk_score=0.0,
                current_location=current_location,
                factors={"reason": "no_history"},
            )

        # Check against last few locations
        previous_locations = history[-3:]  # Check last 3

        max_risk_score = 0.0
        result = None

        for prev_txn in previous_locations:
            prev_loc = prev_txn.location
            prev_time = prev_txn.timestamp
            current_time = time.time()

            # Calculate distance
            distance_km = prev_loc.distance_to(current_location)

            # Calculate time difference
            time_diff_hours = (current_time - prev_time) / 3600

            # Calculate required speed
            required_speed = distance_km / max(time_diff_hours, 0.001)

            # Determine if impossible
            is_impossible = False
            is_air = False
            is_ground_impossible = False

            if required_speed > self.MAX_SPEEDS["plane"]:
                is_impossible = True
                is_air = True
            elif required_speed > self.MAX_SPEEDS["car"]:
                is_impossible = True
                is_ground_impossible = True

            # Calculate risk score based on required speed
            risk_score = 0.0
            if required_speed > self.MAX_SPEEDS["plane"]:
                risk_score = 1.0  # Definitely impossible
            elif required_speed > self.MAX_SPEEDS["train"]:
                risk_score = 0.8  # Very unlikely
            elif required_speed > self.MAX_SPEEDS["car"]:
                risk_score = 0.6  # Unlikely but possible
            elif required_speed > self.MAX_SPEEDS["walk"]:
                risk_score = 0.3  # Somewhat suspicious

            if risk_score > max_risk_score:
                max_risk_score = risk_score
                result = GeoVelocityResult(
                    is_impossible_travel=is_impossible,
                    risk_score=risk_score,
                    previous_location=prev_loc,
                    current_location=current_location,
                    distance_km=distance_km,
                    time_difference_hours=time_diff_hours,
                    required_speed_kmh=required_speed,
                    is_air_travel=is_air,
                    is_ground_impossible=is_ground_impossible,
                    factors={
                        "checked_against": len(previous_locations),
                        "distance_km": round(distance_km, 2),
                        "time_hours": round(time_diff_hours, 2),
                    },
                )

        if result is None:
            result = GeoVelocityResult(
                is_impossible_travel=False,
                risk_score=0.0,
                current_location=current_location,
            )

        if result.is_impossible_travel:
            self._stats["impossible_travel_detected"] += 1

        return result

    # ==================== Country Risk ====================

    def assess_country_risk(self, country: str) -> float:
        """Get risk score for a country."""
        if country in self.HIGH_RISK_COUNTRIES:
            self._stats["high_risk_countries"] += 1
            return 0.8

        if country in self.MEDIUM_RISK_COUNTRIES:
            return 0.4

        return self.COUNTRY_RISK_SCORES.get(country, 0.2)

    # ==================== Timezone Risk ====================

    def assess_timezone_risk(
        self,
        user_timezone: str,
        transaction_timezone: str,
    ) -> float:
        """Assess risk based on timezone anomalies."""
        if not user_timezone or not transaction_timezone:
            return 0.0

        # Simple check - large timezone difference is suspicious
        # In production would use proper timezone handling

        # If exactly same timezone, low risk
        if user_timezone == transaction_timezone:
            return 0.0

        # Check if adjacent timezones (could be travel)
        return 0.2  # Medium risk for timezone change

    # ==================== Complete Assessment ====================

    def assess_location_risk(
        self,
        user_id: str,
        latitude: float,
        longitude: float,
        country: str = "",
        region: str = "",
        city: str = "",
        timezone: str = "",
        ip_address: str = "",
        is_vpn: bool = False,
        is_proxy: bool = False,
        user_timezone: str = "",
    ) -> LocationRiskResult:
        """
        Complete location risk assessment.

        Combines:
        - Geo-velocity (impossible travel)
        - Country risk
        - Timezone risk
        - VPN/Proxy detection
        """
        # Create current location
        current_location = Location(
            latitude=latitude,
            longitude=longitude,
            country=country,
            region=region,
            city=city,
            timezone=timezone,
            ip_address=ip_address,
            is_vpn=is_vpn,
            is_proxy=is_proxy,
        )

        # Record current location
        self.record_location(
            user_id=user_id,
            latitude=latitude,
            longitude=longitude,
            country=country,
            region=region,
            city=city,
            timezone=timezone,
            ip_address=ip_address,
            is_vpn=is_vpn,
            is_proxy=is_proxy,
        )

        # Check geo-velocity
        geo_velocity = self.check_geo_velocity(user_id, current_location)

        # Assess country risk
        country_risk = self.assess_country_risk(country)

        # Assess timezone risk
        timezone_risk = self.assess_timezone_risk(user_timezone, timezone)

        # Calculate combined risk
        scores = []
        weights = []

        if geo_velocity.risk_score > 0:
            scores.append(geo_velocity.risk_score)
            weights.append(0.5)  # Geo-velocity is most important

        if country_risk > 0:
            scores.append(country_risk)
            weights.append(0.2)

        if timezone_risk > 0:
            scores.append(timezone_risk)
            weights.append(0.1)

        # VPN/Proxy risk
        if is_vpn:
            scores.append(0.4)
            weights.append(0.1)
            self._stats["vpn_detected"] += 1

        if is_proxy:
            scores.append(0.5)
            weights.append(0.1)

        # Calculate weighted average
        if scores and weights:
            total_weight = sum(weights)
            combined_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
        else:
            combined_score = 0.0

        # Determine risk level
        if combined_score < 0.2:
            risk_level = LocationRiskLevel.LOW
            recommendation = "allow"
        elif combined_score < 0.5:
            risk_level = LocationRiskLevel.MEDIUM
            recommendation = "review"
        else:
            risk_level = LocationRiskLevel.HIGH
            recommendation = "block"

        # Build factors
        factors = {
            "country": country,
            "city": city,
            "is_vpn": is_vpn,
            "is_proxy": is_proxy,
            "country_risk": country_risk,
            "timezone_risk": timezone_risk,
        }

        if geo_velocity.is_impossible_travel:
            factors["impossible_travel"] = True
            factors["distance_km"] = geo_velocity.distance_km
            factors["required_speed_kmh"] = geo_velocity.required_speed_kmh

        return LocationRiskResult(
            risk_level=risk_level,
            risk_score=combined_score,
            geo_velocity=geo_velocity,
            country_risk=country_risk,
            timezone_risk=timezone_risk,
            factors=factors,
            recommendation=recommendation,
        )

    # ==================== Statistics ====================

    def get_stats(self) -> dict[str, Any]:
        """Get service statistics."""
        return {
            **self._stats,
            "users_tracked": len(self._user_locations),
        }


# Singleton instance
_geo_service: GeoVelocityService | None = None


def get_geo_service() -> GeoVelocityService:
    """Get singleton geo-velocity service."""
    global _geo_service
    if _geo_service is None:
        _geo_service = GeoVelocityService()
    return _geo_service


# Convenience functions
def assess_location_risk(
    user_id: str, latitude: float, longitude: float, **kwargs
) -> LocationRiskResult:
    """Assess location risk for a transaction."""
    service = get_geo_service()
    return service.assess_location_risk(user_id, latitude, longitude, **kwargs)


def record_location(user_id: str, latitude: float, longitude: float, **kwargs):
    """Record a user location."""
    service = get_geo_service()
    service.record_location(user_id, latitude, longitude, **kwargs)
