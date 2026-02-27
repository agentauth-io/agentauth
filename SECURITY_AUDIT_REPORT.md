# AgentAuth Security Audit Report

**Date:** February 27, 2026
**Auditor:** Senior Security Engineer
**Scope:** Full codebase security review
**Version:** 0.3.0

---

## Executive Summary

This security audit evaluates the AgentAuth authorization layer for AI agent purchases. The system demonstrates **strong foundational security practices** with several advanced features, but has **critical vulnerabilities** that require immediate attention before production deployment.

### Overall Security Rating: **6.5/10**

**Strengths:**
- Well-structured cryptographic primitives (Ed25519, ChaCha20-Poly1305, HKDF)
- Comprehensive security headers middleware
- Rate limiting with Redis fallback
- Idempotency protection for transactions
- JWT-based delegation tokens with embedded constraints
- In-memory caching for performance optimization

**Critical Issues:**
- Runtime secret generation in production (secrets lost on restart)
- Weak CSP policy (too restrictive, breaks legitimate features)
- Missing input validation on several endpoints
- Potential timing attack in fallback crypto implementation
- No API key rotation mechanism
- Insufficient audit trail for sensitive operations

---

## Critical Findings (Priority 1)

### 1. Runtime Secret Generation - CRITICAL

**Location:** `app/config.py:27-35`

**Issue:**
```python
_RUNTIME_SECRETS = {
    "secret_key": secrets.token_urlsafe(32),
    "admin_password": secrets.token_urlsafe(24),
    "admin_jwt_secret": secrets.token_urlsafe(32),
}
```

Secrets are generated at runtime and **persist only in memory**. On application restart:
- All existing JWT tokens become invalid
- Admin access is lost
- API keys cannot be verified
- Delegation tokens cannot be verified

**Impact:** Complete service disruption on restart. All authorizations fail.

**Recommendation:**
```python
# In production, require explicit secrets from environment
@field_validator("secret_key", "admin_password", "admin_jwt_secret")
@classmethod
def validate_secrets(cls, v: str, info) -> str:
    if not v:
        if settings.environment == "production":
            raise ValueError(
                f"{info.field_name} must be set via environment variable in production"
            )
        return _RUNTIME_SECRETS.get(info.field_name, secrets.token_urlsafe(32))
    return v
```

**Priority:** CRITICAL - Fix before production deployment

---

### 2. Overly Restrictive CSP Policy - HIGH

**Location:** `app/middleware/security_headers.py:23`

**Issue:**
```python
response.headers["Content-Security-Policy"] = "default-src 'self'"
```

This CSP policy:
- Blocks all inline scripts (even nonce-protected)
- Prevents loading from CDNs (fonts, analytics)
- Breaks webhooks that need to load external resources
- May break legitimate frontend features

**Impact:** Frontend functionality breaks; legitimate integrations fail.

**Recommendation:**
```python
# Production-ready CSP
csp_directives = [
    "default-src 'self'",
    "script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    "font-src 'self' https://fonts.gstatic.com",
    "img-src 'self' data: https:",
    "connect-src 'self' https://api.stripe.com",
    "frame-src 'self' https://js.stripe.com",
]
response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
```

**Priority:** HIGH - Affects user experience and integrations

---

### 3. Missing Input Validation - HIGH

**Location:** Multiple API endpoints

**Issues:**
- `app/api/authorize.py` - No validation on `transaction.amount` (could be negative, extremely large)
- `app/api/consents.py` - No validation on `constraints.max_amount`
- `app/api/limits.py` - No validation on limit values

**Impact:** DoS via extreme values, database corruption, logic bypass.

**Recommendation:**
```python
# Add Pydantic validators
class TransactionDetails(BaseModel):
    amount: float = Field(gt=0, le=1_000_000, description="Amount must be positive and <= $1M")
    currency: str = Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    merchant_id: str = Field(min_length=1, max_length=255)
    merchant_category: Optional[str] = Field(max_length=50)
```

**Priority:** HIGH - Prevents abuse and data corruption

---

### 4. Timing Attack in Fallback Crypto - MEDIUM

**Location:** `core/crypto.py:348-356`

**Issue:**
```python
def _encrypt_fallback(self, plaintext: bytes, nonce: bytes, aad: bytes) -> bytes:
    # Derive keystream
    keystream = b''
    for i in range((len(plaintext) + 31) // 32):
        keystream += hmac.new(
            self._key,
            nonce + struct.pack('>I', i),
            hashlib.sha256
        ).digest()
```

The fallback XOR encryption uses HMAC in a loop. The loop iteration count leaks plaintext length.

**Impact:** Side-channel attack reveals sensitive data length.

**Recommendation:**
```python
# Always pad to fixed block size before encryption
BLOCK_SIZE = 32
padded_len = ((len(plaintext) + BLOCK_SIZE - 1) // BLOCK_SIZE) * BLOCK_SIZE
padded = plaintext.ljust(padded_len, b'\x00')
# Then encrypt padded data
```

**Priority:** MEDIUM - Side-channel vulnerability

---

## High Priority Findings (Priority 2)

### 5. No API Key Rotation Mechanism - HIGH

**Location:** `app/middleware/api_keys.py`

**Issue:**
- API keys have no expiry by default
- No rotation endpoint
- No way to gracefully transition to new keys
- Compromised keys remain valid indefinitely

**Impact:** Long-term credential exposure risk.

**Recommendation:**
```python
# Add to ApiKey model
expires_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    default=lambda: datetime.now(timezone.utc) + timedelta(days=90)
)

# Add rotation endpoint
@router.post("/v1/api-keys/{key_id}/rotate")
async def rotate_api_key(key_id: str, db: AsyncSession = Depends(get_db)):
    # Create new key, mark old as expiring in 24 hours
    pass
```

**Priority:** HIGH - Credential management best practice

---

### 6. Insufficient Audit Logging - HIGH

**Location:** `app/services/auth_service.py`

**Issue:**
- Authorization decisions are logged but not all sensitive operations
- No audit trail for: consent creation, limit changes, rule modifications
- Audit logs not cryptographically signed for tamper evidence

**Impact:** Cannot investigate security incidents; potential tampering.

**Recommendation:**
```python
# Add comprehensive audit logging
async def audit_log(
    event_type: str,
    actor_id: str,
    action: str,
    resource_id: str,
    outcome: str,
    metadata: dict
):
    # Write to audit table with cryptographic signature
    entry = AuditEntry(
        event_type=event_type,
        actor_id=actor_id,
        action=action,
        resource_id=resource_id,
        outcome=outcome,
        metadata=metadata,
        signature=sign_audit_entry(...)
    )
    await db.add(entry)
```

**Priority:** HIGH - Compliance and incident response

---

### 7. Weak Password Requirements - MEDIUM

**Location:** `app/config.py:validate_production_config`

**Issue:**
```python
if not data.get("admin_password"):
    logger.warning("ADMIN_PASSWORD not set")
```

No minimum length or complexity requirements for admin password.

**Impact:** Weak passwords can be brute-forced.

**Recommendation:**
```python
@field_validator("admin_password")
@classmethod
def validate_admin_password(cls, v: str) -> str:
    if len(v) < 12:
        raise ValueError("ADMIN_PASSWORD must be at least 12 characters")
    if not any(c.isupper() for c in v):
        raise ValueError("ADMIN_PASSWORD must contain uppercase letters")
    if not any(c.isdigit() for c in v):
        raise ValueError("ADMIN_PASSWORD must contain digits")
    return v
```

**Priority:** MEDIUM - Password security

---

### 8. Missing Rate Limit on Critical Endpoints - MEDIUM

**Location:** `app/middleware/rate_limiter.py`

**Issue:**
Rate limiting is applied globally, but critical endpoints need stricter limits:
- `/v1/consents` - Should have per-user limits
- `/v1/authorize` - Should have per-agent limits

**Impact:** DoS on critical authorization path.

**Recommendation:**
```python
# Add endpoint-specific rate limits
CRITICAL_ENDPOINTS = {
    "/v1/consents": {"limit": 10, "window": 60, "key_type": "user"},
    "/v1/authorize": {"limit": 100, "window": 60, "key_type": "agent"},
}
```

**Priority:** MEDIUM - DoS prevention

---

## Medium Priority Findings (Priority 3)

### 9. In-Memory Cache Not Distributed - MEDIUM

**Location:** `app/services/auth_service.py:26-28`

**Issue:**
```python
_consent_cache: Dict[str, tuple[dict, datetime]] = {}
```

Consent cache is in-memory only. In multi-instance deployments:
- Cache is not shared
- Stale data across instances
- Inconsistent authorization decisions

**Impact:** Inconsistent behavior in production with multiple instances.

**Recommendation:**
Use Redis for distributed caching:
```python
async def _get_cached_consent(self, consent_id: str) -> Optional[dict]:
    cache = get_cache_service()
    cached = await cache.get(f"consent:{consent_id}")
    if cached:
        return json.loads(cached)
    return None
```

**Priority:** MEDIUM - Scalability concern

---

### 10. No Request Size Limits - MEDIUM

**Location:** `app/main.py`

**Issue:**
No middleware to limit request body size. Large payloads can:
- Exhaust memory
- Cause DoS
- Slow down processing

**Impact:** DoS via large payloads.

**Recommendation:**
```python
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# Add request size limiting
@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 10_000_000:  # 10MB
        raise HTTPException(status_code=413, detail="Payload too large")
    return await call_next(request)
```

**Priority:** MEDIUM - DoS prevention

---

### 11. Sensitive Data in Logs - LOW

**Location:** Multiple locations

**Issue:**
Some log statements may include sensitive data:
- Authorization codes
- API keys (partial)
- User IDs

**Impact:** Information leakage via logs.

**Recommendation:**
```python
# Use redaction helper
def redact_sensitive(data: str) -> str:
    if len(data) > 8:
        return data[:4] + "****" + data[-4:]
    return "****"

logger.info(f"Authorization {redact_sensitive(auth_code)} created")
```

**Priority:** LOW - Information leakage

---

### 12. Missing CORS Validation - LOW

**Location:** `app/main.py:157-165`

**Issue:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],  # Too permissive
)
```

`allow_headers=["*"]` allows any header, including sensitive ones.

**Impact:** Potential header injection attacks.

**Recommendation:**
```python
allow_headers=[
    "Content-Type",
    "Authorization",
    "X-API-Key",
    "Idempotency-Key",
    "X-Request-ID",
]
```

**Priority:** LOW - Defense in depth

---

## Positive Security Findings

### Strengths Identified

1. **Cryptographic Primitives** (`core/crypto.py`)
   - Uses modern algorithms (Ed25519, ChaCha20-Poly1305, HKDF)
   - Proper constant-time comparison
   - Secure random generation
   - Key derivation from master secret

2. **Security Headers** (`app/middleware/security_headers.py`)
   - Comprehensive header set
   - HSTS in production
   - Proper CSP, X-Frame-Options, etc.

3. **Rate Limiting** (`app/middleware/rate_limiter.py`)
   - Redis-backed with in-memory fallback
   - Token bucket algorithm
   - Per-IP and per-API-key limits
   - Stricter limits on auth endpoints

4. **Idempotency** (`app/middleware/idempotency.py`)
   - UUIDv4 keys (128-bit entropy)
   - 24-hour TTL
   - Distributed locking
   - Response caching

5. **JWT Token Design** (`app/services/token_service.py`)
   - Embedded constraints for offline verification
   - Proper issuer validation
   - Expiration handling
   - Single-use token support

6. **API Key Storage** (`app/middleware/api_keys.py`)
   - SHA-256 hashing (not plaintext)
   - In-memory LRU cache
   - Write-through caching
   - Last-used tracking

7. **Database Models** (`app/models/`)
   - Proper indexing
   - UUID primary keys
   - JSON metadata fields
   - Timestamp tracking

---

## Recommendations by Category

### Cryptography

| Priority | Recommendation | Effort |
|----------|----------------|--------|
| P1 | Fix timing attack in fallback crypto | Medium |
| P2 | Add key rotation support | High |
| P3 | Consider HSM integration for master secret | Very High |

### Authentication & Authorization

| Priority | Recommendation | Effort |
|----------|----------------|--------|
| P1 | Fix runtime secret generation | Low |
| P2 | Add API key expiry and rotation | Medium |
| P2 | Strengthen password requirements | Low |
| P3 | Add multi-factor auth for admin | High |

### API Security

| Priority | Recommendation | Effort |
|----------|----------------|--------|
| P1 | Add input validation to all endpoints | Medium |
| P2 | Add request size limits | Low |
| P2 | Add endpoint-specific rate limits | Medium |
| P3 | Tighten CORS headers | Low |

### Data Protection

| Priority | Recommendation | Effort |
|----------|----------------|--------|
| P1 | Fix CSP policy | Low |
| P2 | Add comprehensive audit logging | High |
| P3 | Redact sensitive data in logs | Low |

### Infrastructure

| Priority | Recommendation | Effort |
|----------|----------------|--------|
| P2 | Use Redis for distributed caching | Medium |
| P3 | Add monitoring and alerting | High |

---

## Testing Recommendations

### Security Tests to Add

1. **Fuzz Testing**
   - Test endpoints with malformed input
   - Test boundary conditions (max amounts, etc.)

2. **Penetration Testing**
   - Test for SQL injection
   - Test for XSS via webhook payloads
   - Test for CSRF on state-changing operations

3. **Load Testing**
   - Test rate limiting under load
   - Test cache eviction behavior
   - Test database connection pooling

4. **Security Regression Tests**
   ```python
   # Add to tests/test_security.py
   async def test_runtime_secrets_required_in_production():
       settings = get_settings()
       settings.environment = "production"
       with pytest.raises(ValueError):
           Settings()  # Should fail without explicit secrets

   async def test_csp_policy_allows_legitimate_resources():
       response = await client.get("/")
       csp = response.headers["content-security-policy"]
       assert "script-src 'self'" in csp
       assert "nonce-" in csp or "cdn.jsdelivr.net" in csp
   ```

---

## Compliance Checklist

| Requirement | Status | Notes |
|-------------|--------|-------|
| PCI DSS - Encryption | ✅ Partial | ChaCha20-Poly1305 used, but key rotation missing |
| PCI DSS - Access Control | ✅ Partial | API keys used, but no MFA |
| PCI DSS - Audit Logging | ⚠️ Incomplete | Basic logging, no tamper evidence |
| PCI DSS - Vulnerability Management | ⚠️ Pending | No regular scanning process |
| SOC 2 - Security | ⚠️ Partial | Good controls, missing some |
| SOC 2 - Availability | ✅ Good | Health checks, graceful degradation |
| GDPR - Data Protection | ✅ Good | No PII stored by default |
| GDPR - Right to Erasure | ⚠️ Pending | No user data deletion endpoint |

---

## Implementation Roadmap

### Phase 1: Critical Fixes (Week 1)
- [ ] Fix runtime secret generation
- [ ] Fix CSP policy
- [ ] Add input validation
- [ ] Fix timing attack in crypto

### Phase 2: High Priority (Week 2-3)
- [ ] Add API key rotation
- [ ] Add comprehensive audit logging
- [ ] Strengthen password requirements
- [ ] Add endpoint-specific rate limits

### Phase 3: Medium Priority (Week 4)
- [ ] Use Redis for distributed caching
- [ ] Add request size limits
- [ ] Tighten CORS headers
- [ ] Redact sensitive data in logs

### Phase 4: Advanced Features (Month 2)
- [ ] HSM integration
- [ ] Multi-factor auth
- [ ] Advanced monitoring
- [ ] Compliance automation

---

## Conclusion

AgentAuth has a **solid security foundation** with modern cryptographic practices and well-designed middleware. However, **critical issues** around secret management and input validation must be addressed before production deployment.

The system shows good security awareness in its design, but needs hardening in operational areas (secrets management, audit logging, credential lifecycle).

**Recommended Action:** Address all Priority 1 findings before production launch. Priority 2 findings should be addressed within the first month of operation.

---

## Appendix: Security Score Breakdown

| Category | Score | Weight | Weighted Score |
|----------|-------|--------|----------------|
| Cryptography | 8/10 | 25% | 2.0 |
| Authentication | 6/10 | 25% | 1.5 |
| API Security | 6/10 | 20% | 1.2 |
| Data Protection | 7/10 | 15% | 1.05 |
| Infrastructure |