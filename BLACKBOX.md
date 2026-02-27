# AgentAuth — Project Context

## Project Overview

AgentAuth is **the authorization layer for AI agent purchases**. It provides cryptographic proof that a human authorized every AI agent transaction, enabling spending limits, purchase approvals, and chargeback defense for merchants.

**Core value proposition:** When an AI agent makes a purchase on behalf of a user, AgentAuth issues *delegation tokens* that cryptographically bind user consent to agent actions. Merchants verify these tokens to prove authorization, solving the $31B annual chargeback problem.

**Website:** [agentauth.in](https://agentauth.in)

---

## Architecture

This is a **polyglot monorepo** with the following major components:

| Component | Language/Framework | Location | Purpose |
|---|---|---|---|
| **API Server** | Python / FastAPI | `app/` | Core REST API — consents, authorization, verification |
| **Core Engine** | Python | `core/` | Authorization engine, policy, risk, crypto, audit |
| **AgentAuth Core** | Python | `agentauth_core/` | Agent registry, auth engine, policy engine, rate limiter |
| **Secure Core** | Rust | `secure-core/` | Memory-safe cryptographic primitives (Ed25519, ChaCha20, BLAKE3) |
| **WASM Policy Engine** | Rust → WASM | `wasm-policy/` | WebAssembly policy evaluation engine |
| **API Gateway** | Go (chi router) | `gateway/` | High-performance reverse proxy with auth, rate limiting |
| **Frontend / Dashboard** | React + Vite + Tailwind v4 | `frontend/` | Landing page, dashboard, demo store, admin panel |
| **Marketing Site** | Next.js + Tailwind | `agentauth-site/` | Public website with waitlist |
| **CLI** | TypeScript (Commander.js) | `cli/` | `@agentauth/cli` — terminal management tool |
| **MCP Server** | TypeScript | `mcp/` | Model Context Protocol server for AI agent tool integration |
| **Python SDK** | Python | `sdk/python/` | `agentauth-client` — pip-installable client library |
| **TypeScript SDK** | TypeScript | `sdk/typescript/` | TypeScript/JS client library |
| **AgentBuy** | Python + Next.js | `agentbuy/` | Voice-powered AI shopping agent demo (Jarvis) |

### Infrastructure & Deployment

| File/Dir | Purpose |
|---|---|
| `docker-compose.yml` | Local dev: API + PostgreSQL + Redis + OPA + Jaeger |
| `docker-compose.prod.yml` | Production Docker Compose |
| `docker-compose.advanced.yml` | Advanced deployment with all optional services |
| `Dockerfile` / `Dockerfile.prod` | Container images (Python 3.12-slim) |
| `helm/agentauth/` | Helm chart for Kubernetes deployment |
| `k8s/` | Raw Kubernetes manifests |
| `nginx.conf` / `nginx.dev.conf` | Reverse proxy configuration |
| `alembic/` | Database migrations (PostgreSQL) |
| `migrations/` | SQL migration scripts (Supabase RLS, billing tables) |
| `grafana/` | Grafana dashboard JSON |
| `prometheus.yml` | Prometheus monitoring config |

### Deployment Targets

Configured for: **Koyeb** (`koyeb.yaml`), **Railway** (`railway.toml`), **Render** (`render.yaml`), **Netlify** (`netlify.toml`), **Heroku** (`Procfile`).

---

## Core API Flow

```
1. POST /v1/consents     → User creates consent with spending limits → returns delegation_token
2. POST /v1/authorize    → Agent requests authorization for a transaction → returns ALLOW/DENY
3. POST /v1/verify       → Merchant verifies authorization code → returns cryptographic proof
```

### Additional API Routes

- `/v1/limits` — Spending limits (daily, monthly, per-transaction)
- `/v1/rules` — Merchant whitelists/blacklists, category controls
- `/v1/agents` — Agent registration and management
- `/v1/analytics` — Usage analytics
- `/v1/webhooks` — Webhook configuration
- `/v1/billing` — Stripe-based subscription billing
- `/v1/admin/*` — Admin panel endpoints
- `/v1/api-keys` — API key generation
- `/v1/connect` — Connected accounts (OAuth-style)
- `/health`, `/health/detailed` — Health checks
- `/metrics` — System metrics

**Authentication:** `X-API-Key` header or `Authorization: Bearer aa_live_xxx`

---

## Building and Running

### Backend API (Primary)

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# Edit .env with DATABASE_URL (PostgreSQL via Neon, Supabase, or local)

# Database migrations
alembic upgrade head

# Run development server
uvicorn app.main:app --reload

# Run production server
python production_server.py
# or
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

### Docker (Full Stack)

```bash
# Core services (API + PostgreSQL + Redis)
docker compose up -d

# With OPA policy engine
docker compose --profile with-opa up -d

# With distributed tracing (Jaeger)
docker compose --profile with-tracing up -d

# With Nginx reverse proxy
docker compose --profile with-nginx up -d
```

### Frontend Dashboard

```bash
cd frontend
npm install
npm run dev          # Vite dev server (localhost:5173)
npm run build        # Production build
```

### Marketing Site (Next.js)

```bash
cd agentauth-site
npm install
npm run dev          # Next.js dev server
npm run build        # Production build
```

### CLI

```bash
cd cli
npm install
npm run build        # TypeScript → dist/
npm start            # or: node dist/index.js
```

### MCP Server

```bash
cd mcp
npm install
npm run build
npm start
```

### Quickstart Script

```bash
./quickstart.sh      # Automated setup
```

---

## Testing

### Python Tests (pytest)

```bash
# Run all tests (uses in-memory SQLite — no external DB needed)
pytest

# With coverage
pytest --cov=app --cov-report=term-missing

# Specific test files
pytest tests/test_api_routes.py
pytest tests/test_middleware.py
pytest tests/test_security.py
```

**Test configuration:** `pyproject.toml` → `[tool.pytest.ini_options]`
- `asyncio_mode = "auto"`
- `testpaths = ["tests"]`
- Fixtures in `tests/conftest.py` — uses `aiosqlite` in-memory DB
- Custom markers: `@pytest.mark.db`, `@pytest.mark.slow`

### Standalone Test Scripts (root level)

```bash
python test_agentauth.py       # End-to-end API test
python test_auth_flow.py       # Authorization flow test
python test_core.py            # Core engine test
python test_security.py        # Security test
python test_transactions.py    # Transaction test
```

### CLI Tests

```bash
cd cli && npm test    # vitest
```

### Rust Tests

```bash
cd secure-core && cargo test
cd wasm-policy && cargo test
```

---

## Linting and Code Quality

```bash
# Python formatting
black app/ core/ tests/

# Python linting
ruff check app/ core/ tests/

# Type checking
mypy app/

# CLI linting
cd cli && npm run lint

# Rust
cd secure-core && cargo clippy
cd wasm-policy && cargo clippy
```

### Code Style Conventions

- **Python:** Black formatter (line-length 88), Ruff linter, target Python 3.10+
- **TypeScript:** Standard TypeScript strict mode
- **Rust:** Edition 2021, release profile with LTO enabled
- **Line length:** 88 characters (Python), default (TS/Rust)
- **Imports:** Ruff `isort`-compatible import sorting (`I` rule)

---

## Environment Variables

### Required (Production)

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (`postgresql+asyncpg://...`) |
| `SECRET_KEY` | JWT signing key (≥32 chars). Generate: `openssl rand -hex 32` |
| `ADMIN_PASSWORD` | Admin panel password (≥12 chars) |
| `ADMIN_JWT_SECRET` | Admin JWT signing secret |
| `ENVIRONMENT` | `development` / `staging` / `production` |

### Optional

| Variable | Description |
|---|---|
| `STRIPE_SECRET_KEY` | Stripe API key for billing |
| `REDIS_URL` | Redis for caching, rate limiting, idempotency |
| `SENTRY_DSN` | Sentry error tracking |
| `JWT_ALGORITHM` | `HS256` (default), `RS256`, or `EdDSA` |
| `TOKEN_EXPIRY_SECONDS` | Delegation token TTL (default: 3600) |
| `RATE_LIMIT_REQUESTS_PER_SECOND` | API rate limit (default: 100) |

See `.env.example` and `.env.production.example` for full list.

---

## Key Dependencies

### Python (Backend)

- **FastAPI** ≥0.109 — async web framework
- **SQLAlchemy** ≥2.0 (async) + **asyncpg** — PostgreSQL ORM
- **Pydantic** ≥2.5 + **pydantic-settings** — validation & config
- **PyJWT** ≥2.8 — JWT token handling
- **Alembic** ≥1.13 — database migrations
- **Stripe** ≥7.0 — payment processing
- **Redis** ≥5.0 — caching & rate limiting
- **OpenTelemetry** — distributed tracing
- **cryptography** ≥42.0 — Ed25519/RSA key operations
- **bcrypt** — password hashing
- **Sentry SDK** — error monitoring

### Frontend

- **React** 18.3 + **Vite** 6.x — SPA framework & bundler
- **Tailwind CSS** v4 — utility-first styling
- **Radix UI** — accessible component primitives (shadcn/ui pattern)
- **Recharts** — data visualization
- **React Router DOM** v7 — client-side routing
- **Motion** (Framer Motion) — animations
- **Supabase JS** — auth & database client
- **Lucide React** — icons

### Rust

- **ring**, **ed25519-dalek**, **chacha20poly1305**, **blake3** — cryptography
- **wasm-bindgen** — WASM interop
- **serde** / **serde_json** — serialization

### Go (Gateway)

- **chi** v5 — HTTP router
- **golang-jwt** v5 — JWT validation
- **go-redis** v9 — Redis client
- **zerolog** — structured logging
- **OpenTelemetry** — tracing

---

## Project Structure Summary

```
AgentAuth/
├── app/                    # FastAPI backend (main application)
│   ├── api/                #   Route handlers (consents, authorize, verify, etc.)
│   ├── middleware/          #   Rate limiting, API keys, security headers, idempotency
│   ├── models/             #   SQLAlchemy models (consent, audit, API keys, etc.)
│   ├── schemas/            #   Pydantic request/response schemas
│   ├── services/           #   Business logic (auth, billing, cache, webhooks, etc.)
│   ├── ml/                 #   ML modules (anomaly detection, fraud model)
│   ├── config.py           #   Settings (pydantic-settings, env validation)
│   └── main.py             #   FastAPI app entry point
├── core/                   # Python authorization engine & security
├── agentauth_core/         # Python agent registry & policy engine
├── secure-core/            # Rust cryptographic core (FFI/WASM)
├── wasm-policy/            # Rust → WASM policy engine
├── gateway/                # Go API gateway
├── frontend/               # React + Vite dashboard & landing page
├── agentauth-site/         # Next.js marketing website
├── cli/                    # TypeScript CLI tool
├── mcp/                    # MCP server for AI agent integration
├── sdk/python/             # Python SDK (agentauth-client)
├── sdk/typescript/         # TypeScript SDK
├── agentbuy/               # Voice AI shopping agent demo
├── tests/                  # pytest test suite
├── alembic/                # Database migrations
├── helm/                   # Kubernetes Helm chart
├── k8s/                    # Kubernetes manifests
├── deploy/                 # Deployment configs
├── docs/                   # API docs, production guide
├── demos/                  # Demo scripts (Stripe, shopping)
├── examples/               # Integration examples (LangChain)
├── scripts/                # Deployment scripts
├── grafana/                # Monitoring dashboards
├── docker-compose.yml      # Docker orchestration
├── pyproject.toml          # Python project config (build, lint, test)
├── requirements.txt        # Pinned production dependencies
├── openapi.yaml            # OpenAPI specification
└── BLACKBOX.md             # This file
```

---

## Important Notes

- **Database:** PostgreSQL is required for production. Tests use in-memory SQLite via `aiosqlite`.
- **Redis:** Optional but recommended — enables distributed rate limiting, caching, and idempotency. Falls back to in-memory when unavailable.
- **JWT Signing:** Supports HS256 (symmetric), RS256 (RSA), and EdDSA (Ed25519). Production should use asymmetric keys.
- **Production validation:** The `Settings` class enforces that `SECRET_KEY`, `ADMIN_PASSWORD`, `DATABASE_URL` (non-localhost) are set in production. Wildcard CORS is rejected.
- **API versioning:** All endpoints are under `/v1/`.
- **App entry point:** `app.main:app` (FastAPI ASGI application).
- **Middleware stack (order matters):** RequestID → SecurityHeaders → RateLimit → Idempotency → TenantContext → CORS.
