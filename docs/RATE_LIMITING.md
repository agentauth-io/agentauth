# AgentAuth Rate Limiting System

## Overview

AgentAuth implements a multi-tiered rate limiting system designed to protect the API from abuse while ensuring legitimate traffic flows smoothly. The system supports both in-memory (fallback) and Redis-backed (production) rate limiting with distributed coordination.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Rate Limiting Architecture                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐      │
│  │   Client    │────▶│   WAF/CDN   │────▶│   Ingress   │      │
│  │             │     │ (Cloudflare)│     │   (nginx)   │      │
│  └─────────────┘     └─────────────┘     └──────┬──────┘      │
│                                                  │              │
│  ┌───────────────────────────────────────────────┘              │
│  │                                                              │
│  │  ┌─────────────────────────────────────────────────────┐    │
│  │  │              RateLimitMiddleware                      │    │
│  │  │  ┌───────────────────────────────────────────────┐  │    │
│  │  │  │              Path Classification                │  │    │
│  │  │  │  ┌─────────┐ ┌─────────┐ ┌─────────────────┐ │  │    │
│  │  │  │  │ Exempt  │ │ Standard│ │     Strict      │ │  │    │
│  │  │  │  │/health  │ │ /v1/*   │ │ /v1/admin/*     │ │  │    │
│  │  │  │  │/docs    │ │         │ │ /v1/auth/*      │ │  │    │
│  │  │  │  └────┬────┘ └────┬────┘ └────────┬────────┘ │  │    │
│  │  │  │       │           │               │            │  │    │
│  │  │  │       └───────────┴───────────────┘            │  │    │
│  │  │  │                   │                             │  │    │
│  │  │  │                   ▼                             │  │    │
│  │  │  │  ┌─────────────────────────────────────────┐   │  │    │
│  │  │  │  │         Rate Limit Check                │   │  │    │
│  │  │  │  │                                         │   │  │    │
│  │  │  │  │  ┌─────────────┐    ┌─────────────┐   │   │  │    │
│  │  │  │  │  │    Redis    │◄──►│   Fallback  │   │   │  │    │
│  │  │  │  │  │  (Primary)  │    │  (In-Memory)│   │   │  │    │
│  │  │  │  │  └─────────────┘    └─────────────┘   │   │  │    │
│  │  │  │  └─────────────────────────────────────────┘   │  │    │
│  │  │  └──────────────────────────────────────────────────┘  │    │
│  │  └────────────────────────────────────────────────────────┘    │
│  └──────────────────────────────────────────────────────────────────┘
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Response Headers                          ││
│  │  X-RateLimit-Limit: 100                                     ││
│  │  X-RateLimit-Remaining: 87                                  ││
│  │  X-RateLimit-Reset: 47                                      ││
│  │  Retry-After: 47 (on 429)                                   ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Rate Limit Tiers

| Tier | Requests/Second | Requests/Minute | Burst | Use Case |
|------|-----------------|-----------------|-------|----------|
| **Exempt** | ∞ | ∞ | ∞ | Health checks, docs, metrics |
| **Strict** | - | 10 | 5 | Auth endpoints (brute force protection) |
| **Standard (IP)** | - | 100 | 20 | Unauthenticated requests |
| **Standard (API Key)** | 100 | 6000 | 150 | Authenticated requests |
| **Enterprise** | 1000 | 60000 | 500 | Custom enterprise tier |

## Implementation Details

### Path Classification

```python
# Exempt paths - no rate limiting
EXEMPT_PATHS = {
    "/health", "/docs", "/redoc", "/openapi.json", "/", "/metrics"
}

# Strict paths - lower limits for security
STRICT_PATHS = {
    "/v1/admin/login",
    "/v1/auth/login",
    "/v1/auth/register",
    "/v1/auth/otp",
    "/v1/auth/verify-otp",
}
STRICT_LIMIT = 10  # requests per minute
```

### Rate Limit Key Selection

```python
def get_rate_limit_key(request):
    """Determine rate limit key based on request characteristics."""
    
    # 1. API Key (highest priority)
    api_key = extract_api_key(request)
    if api_key and api_key.startswith("aa_"):
        return f"apikey:{api_key[:20]}"
    
    # 2. IP Address (fallback)
    client_ip = request.client.host if request.client else "unknown"
    return f"ip:{client_ip}"
```

### Sliding Window Algorithm

```python
def is_rate_limited(key, max_requests, window_seconds):
    """
    Sliding window rate limiting algorithm.
    
    1. Remove requests outside the current window
    2. Count remaining requests
    3. If count >= max_requests: reject
    4. Otherwise: record request and accept
    """
    now = time.time()
    window_start = now - window_seconds
    
    # Clean old requests
    requests[key] = [ts for ts in requests[key] if ts > window_start]
    
    current_count = len(requests[key])
    
    if current_count >= max_requests:
        # Rate limited
        oldest = min(requests[key])
        reset_in = int(oldest + window_seconds - now)
        return True, 0, reset_in
    
    # Allow request
    requests[key].append(now)
    remaining = max_requests - current_count - 1
    return False, remaining, window_seconds
```

## Response Headers

All API responses include rate limit headers:

| Header | Description | Example |
|--------|-------------|---------|
| `X-RateLimit-Limit` | Maximum requests allowed | `100` |
| `X-RateLimit-Remaining` | Remaining requests in window | `87` |
| `X-RateLimit-Reset` | Seconds until window resets | `47` |
| `Retry-After` | Seconds to wait (on 429) | `47` |

## Error Response (429)

When rate limit is exceeded:

```json
{
  "error": "rate_limit_exceeded",
  "detail": "Rate limit exceeded. Try again in 47 seconds.",
  "retry_after": 47
}
```

With headers:
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 47
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 47
```

## Redis vs In-Memory

| Feature | In-Memory | Redis |
|---------|-----------|-------|
| **Persistence** | ❌ Lost on restart | ✅ Persistent |
| **Distributed** | ❌ Per-instance | ✅ Shared across instances |
| **Performance** | ✅ <1ms latency | ~2-5ms latency |
| **Memory** | Limited by pod | Scales independently |
| **Failover** | ❌ None | ✅ Redis Sentinel/Cluster |

## Testing

Run the comprehensive rate limit test suite:

```bash
# All rate limit tests
pytest tests/test_rate_limit_load.py -v

# Specific test categories
pytest tests/test_rate_limit_load.py::TestConcurrentRateLimiting -v
pytest tests/test_rate_limit_load.py::TestRateLimitPerformance -v
pytest tests/test_rate_limit_load.py::TestStress -v

# With coverage
pytest tests/test_rate_limit_load.py --cov=app.middleware.rate_limiter
```

## Best Practices

1. **Use API Keys**: API keys have higher limits than IP-based limiting
2. **Handle 429s**: Implement exponential backoff when rate limited
3. **Cache Responses**: Don't repeat identical requests
4. **Batch Operations**: Use bulk endpoints when available
5. **Monitor Headers**: Track `X-RateLimit-Remaining` to anticipate limits

## Configuration

Environment variables for rate limiting:

| Variable | Default | Description |
|----------|---------|-------------|
| `RATE_LIMIT_REQUESTS_PER_SECOND` | `100` | API key rate limit (req/sec) |
| `RATE_LIMIT_IP_PER_MINUTE` | `100` | IP-based rate limit (req/min) |
| `RATE_LIMIT_STRICT_PER_MINUTE` | `10` | Auth endpoint limit (req/min) |
| `REDIS_URL` | - | Redis connection for distributed limiting |

---

*Last updated: February 27, 2026*
