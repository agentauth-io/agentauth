# Changelog

All notable changes to AgentAuth are documented here.

## [Unreleased]

### Added - Infrastructure Roadmap (Jan 18-19, 2026)

#### Phase 1: Foundation
- Redis-backed caching service (`app/services/cache_service.py`)
- Token bucket rate limiting with Redis (`app/middleware/rate_limiter.py`)
- Idempotency middleware with 24h TTL (`app/middleware/idempotency.py`)
- Velocity fraud checks - 5 rules (`app/services/velocity_service.py`)

#### Phase 2: Security Hardening
- PostgreSQL Row-Level Security (`migrations/add_rls_policies.sql`)
- Tenant context middleware (`app/middleware/tenant_context.py`)
- OpenTelemetry distributed tracing (`app/tracing.py`)
- CloudEvents webhook streaming (`app/services/event_service.py`)

#### Phase 3: Advanced Security
- Biscuit token service with Ed25519 (`app/services/biscuit_service.py`)
- UCAN capability delegation (`app/services/ucan_service.py`)

#### Phase 4: AI/ML Intelligence
- Redis-backed ML feature store (`app/ml/feature_store.py`)
- DNN fraud detection model (`app/ml/fraud_model.py`)
- Anomaly detection ensemble (`app/ml/anomaly_detection.py`)

#### Phase 5: Enterprise
- Compliance audit logging (`app/services/audit_service.py`)
- OPA policy engine integration (`app/services/opa_service.py`)
- Docker Compose self-hosted deployment (`docker-compose.yml`)

### Fixed
- Netlify functions 404 error - deployed via CLI with explicit functions path
- Flaky integration tests - added `conftest.py` with DB connection reset

### Changed
- Simplified `netlify.toml` configuration
- Updated test fixtures for proper async isolation
