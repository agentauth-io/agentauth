"""
AgentAuth Rate Limiter
Adaptive rate limiting with token bucket and sliding window algorithms
"""

import time
import threading
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import hashlib


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    requests_per_second: float = 10.0
    requests_per_minute: float = 100.0
    requests_per_hour: float = 1000.0
    burst_size: int = 20
    cooldown_seconds: float = 60.0


@dataclass
class TokenBucket:
    """Token bucket for rate limiting"""
    tokens: float
    last_update: float
    max_tokens: float
    refill_rate: float  # tokens per second


class AdaptiveRateLimiter:
    """
    Adaptive rate limiter with multiple algorithms:
    - Token bucket for burst handling
    - Sliding window for sustained rate
    - Exponential backoff for abusers
    - Per-agent and per-user limits
    """
    
    def __init__(self, default_config: Optional[RateLimitConfig] = None):
        self._default_config = default_config or RateLimitConfig()
        self._buckets: Dict[str, TokenBucket] = {}
        self._sliding_windows: Dict[str, list] = defaultdict(list)
        self._blocked: Dict[str, float] = {}
        self._violation_counts: Dict[str, int] = defaultdict(int)
        self._custom_configs: Dict[str, RateLimitConfig] = {}
        self._lock = threading.RLock()
    
    def set_config(self, key: str, config: RateLimitConfig) -> None:
        """Set custom rate limit config for a specific key"""
        with self._lock:
            self._custom_configs[key] = config
    
    def check_rate_limit(
        self,
        key: str,
        cost: float = 1.0
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Check if request is within rate limits
        
        Args:
            key: Identifier (agent_id, user_id, IP, etc.)
            cost: Request cost (default 1.0)
        
        Returns:
            Tuple of (allowed, metadata)
        """
        with self._lock:
            now = time.time()
            
            # Check if blocked
            if key in self._blocked:
                unblock_time = self._blocked[key]
                if now < unblock_time:
                    return False, {
                        "reason": "RATE_LIMITED",
                        "retry_after": unblock_time - now,
                        "blocked": True
                    }
                else:
                    del self._blocked[key]
            
            config = self._custom_configs.get(key, self._default_config)
            
            # Token bucket check
            bucket_allowed = self._check_token_bucket(key, cost, config, now)
            
            # Sliding window check
            window_allowed = self._check_sliding_window(key, config, now)
            
            if not bucket_allowed or not window_allowed:
                self._record_violation(key, config, now)
                return False, {
                    "reason": "RATE_LIMITED",
                    "retry_after": self._calculate_retry_after(key, config),
                    "blocked": False
                }
            
            # Consume tokens
            self._consume_tokens(key, cost)
            
            # Record request in sliding window
            self._sliding_windows[key].append(now)
            
            return True, {
                "remaining_tokens": self._buckets[key].tokens if key in self._buckets else config.burst_size,
                "reset_at": now + (1.0 / config.refill_rate if hasattr(config, 'refill_rate') else 1.0)
            }
    
    def _check_token_bucket(
        self,
        key: str,
        cost: float,
        config: RateLimitConfig,
        now: float
    ) -> bool:
        """Check token bucket algorithm"""
        if key not in self._buckets:
            self._buckets[key] = TokenBucket(
                tokens=config.burst_size,
                last_update=now,
                max_tokens=config.burst_size,
                refill_rate=config.requests_per_second
            )
        
        bucket = self._buckets[key]
        
        # Refill tokens
        time_passed = now - bucket.last_update
        tokens_to_add = time_passed * bucket.refill_rate
        bucket.tokens = min(bucket.max_tokens, bucket.tokens + tokens_to_add)
        bucket.last_update = now
        
        return bucket.tokens >= cost
    
    def _consume_tokens(self, key: str, cost: float) -> None:
        """Consume tokens from bucket"""
        if key in self._buckets:
            self._buckets[key].tokens -= cost
    
    def _check_sliding_window(
        self,
        key: str,
        config: RateLimitConfig,
        now: float
    ) -> bool:
        """Check sliding window rate limit"""
        window = self._sliding_windows[key]
        
        # Clean old entries
        minute_ago = now - 60
        hour_ago = now - 3600
        
        self._sliding_windows[key] = [t for t in window if t > hour_ago]
        window = self._sliding_windows[key]
        
        # Check minute limit
        minute_count = sum(1 for t in window if t > minute_ago)
        if minute_count >= config.requests_per_minute:
            return False
        
        # Check hour limit
        if len(window) >= config.requests_per_hour:
            return False
        
        return True
    
    def _record_violation(
        self,
        key: str,
        config: RateLimitConfig,
        now: float
    ) -> None:
        """Record rate limit violation and potentially block"""
        self._violation_counts[key] += 1
        
        # Exponential backoff for repeat offenders
        violations = self._violation_counts[key]
        if violations >= 3:
            block_duration = config.cooldown_seconds * (2 ** (violations - 3))
            block_duration = min(block_duration, 3600)  # Max 1 hour
            self._blocked[key] = now + block_duration
    
    def _calculate_retry_after(self, key: str, config: RateLimitConfig) -> float:
        """Calculate when client can retry"""
        if key in self._blocked:
            return self._blocked[key] - time.time()
        
        if key in self._buckets:
            bucket = self._buckets[key]
            if bucket.tokens < 1:
                return (1 - bucket.tokens) / bucket.refill_rate
        
        return 1.0
    
    def reset(self, key: str) -> None:
        """Reset rate limit state for a key"""
        with self._lock:
            if key in self._buckets:
                del self._buckets[key]
            if key in self._sliding_windows:
                del self._sliding_windows[key]
            if key in self._blocked:
                del self._blocked[key]
            if key in self._violation_counts:
                del self._violation_counts[key]
    
    def get_status(self, key: str) -> Dict[str, any]:
        """Get current rate limit status for a key"""
        with self._lock:
            config = self._custom_configs.get(key, self._default_config)
            now = time.time()
            
            status = {
                "key": key,
                "blocked": key in self._blocked,
                "violations": self._violation_counts.get(key, 0),
                "config": {
                    "requests_per_second": config.requests_per_second,
                    "requests_per_minute": config.requests_per_minute,
                    "requests_per_hour": config.requests_per_hour,
                    "burst_size": config.burst_size
                }
            }
            
            if key in self._blocked:
                status["unblock_at"] = self._blocked[key]
                status["blocked_remaining"] = max(0, self._blocked[key] - now)
            
            if key in self._buckets:
                bucket = self._buckets[key]
                status["tokens_remaining"] = bucket.tokens
                status["max_tokens"] = bucket.max_tokens
            
            window = self._sliding_windows.get(key, [])
            minute_ago = now - 60
            hour_ago = now - 3600
            
            status["requests_last_minute"] = sum(1 for t in window if t > minute_ago)
            status["requests_last_hour"] = sum(1 for t in window if t > hour_ago)
            
            return status
