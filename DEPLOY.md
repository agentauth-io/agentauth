# AgentAuth Production Deployment Guide

Deploy your AgentAuth backend so the CLI works for real users.

## Quick Deploy Options

### Option 1: Koyeb (Recommended - 5 minutes)

1. **Push to GitHub** (if not already):
   ```bash
   git add .
   git commit -m "Production ready"
   git push origin main
   ```

2. **Deploy on Koyeb**:
   - Go to [app.koyeb.com](https://app.koyeb.com)
   - Click **"Create App"** → **"GitHub"**
   - Select your `agentauth` repository
   - Choose **"Dockerfile"** as build method
   - Set the port to `8000`

3. **Add Environment Variables** (in Koyeb dashboard → Settings → Environment):
   ```
   DATABASE_URL=postgresql://user:pass@host:5432/agentauth
   REDIS_URL=redis://host:6379
   MASTER_SECRET=your-64-char-hex-secret
   SECRET_KEY=your-secure-secret-key-here
   STRIPE_SECRET_KEY=sk_live_xxx
   STRIPE_WEBHOOK_SECRET=whsec_xxx
   DEBUG=false
   CORS_ORIGINS=https://agentauth.in,https://www.agentauth.in
   ```

4. **Configure Health Check**:
   - Path: `/health`
   - Port: `8000`

5. **Add Custom Domain**:
   - Go to Settings → Domains
   - Add `api.agentauth.in`
   - Update DNS with Koyeb's CNAME

6. **Verify Deployment**:
   ```bash
   curl https://api.agentauth.in/health
   # Should return: {"status":"healthy","database":"connected","redis":"connected"}
   ```

### Option 2: Railway

1. Go to [railway.app](https://railway.app) → **"New Project"** → **"Deploy from GitHub repo"**
2. Select your `agentauth` repository
3. Railway auto-detects Python and deploys using `railway.toml`
4. Add environment variables (same as Koyeb above)
5. Add custom domain: `api.agentauth.in`

### Option 3: Render.com

1. Go to [render.com](https://render.com) → **New** → **Web Service**
2. Connect your GitHub repo
3. It will use `render.yaml` for configuration automatically
4. Add environment variables (same as above)
5. Add custom domain: `api.agentauth.in`

### Option 4: Docker (Any Cloud)

```bash
# Build
docker build -t agentauth-api .

# Run
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:pass@host:5432/agentauth" \
  -e REDIS_URL="redis://host:6379" \
  -e MASTER_SECRET="your-secret" \
  -e SECRET_KEY="your-secret" \
  agentauth-api
```

Deploy to:
- **Google Cloud Run**: `gcloud run deploy`
- **AWS ECS/Fargate**: Use ECR + ECS
- **DigitalOcean App Platform**: Connect GitHub

---

## Database Setup

### Neon (Recommended - Free tier with generous limits)

1. **Create account**: Go to [neon.tech](https://neon.tech) and sign up
2. **Create project**: Click "New Project" → Name it `agentauth`
3. **Get connection string**: Copy the connection string from the dashboard
4. **Convert for asyncpg**: Change the format:
   ```
   # From Neon (psycopg2 format):
   postgresql://user:password@ep-xxx.region.aws.neon.tech/agentauth
   
   # To asyncpg format (add +asyncpg):
   postgresql+asyncpg://user:password@ep-xxx.region.aws.neon.tech/agentauth?sslmode=require
   ```
5. **Set in Koyeb**: Add as `DATABASE_URL` environment variable

**Free tier includes:**
- 0.5 GB storage
- 3 GB data transfer/month
- Autoscaling compute
- Branching for dev/staging

### Supabase (Alternative)

1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Go to Settings → Database → Connection string
4. Use the "URI" format with `?sslmode=require`

### Run Migrations

After setting up the database:

```bash
# Run locally to apply migrations to production DB
DATABASE_URL="your-production-url" alembic upgrade head
```

---

## CLI Configuration

After deploying, update your CLI:

```bash
# Point CLI to production
agentauth config --api-url https://api.agentauth.in

# Or use environment variable
export AGENTAUTH_API_URL=https://api.agentauth.in

# Verify connection
agentauth doctor

# Login with your production API key
agentauth login
```

---

## npm Publishing (CLI)

Publish the CLI to npm for global installation:

```bash
cd cli
npm login
npm publish --access public
```

Users can then install with:
```bash
npm install -g @agentauth/cli
agentauth login
```

---

## Troubleshooting

### CLI can't connect
```bash
agentauth doctor --fix  # Auto-detect and fix API URL
```

### Check API health
```bash
curl https://api.agentauth.in/health
curl https://api.agentauth.in/docs  # OpenAPI docs
```

### Logs
- **Railway**: View logs in dashboard or `railway logs`
- **Render**: View logs in dashboard
- **Docker**: `docker logs <container_id>`

---

## Environment Variables Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://user:pass@host:5432/agentauth` |
| `SECRET_KEY` | JWT signing key (32+ chars) | Generate: `openssl rand -hex 32` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug mode |
| `ENVIRONMENT` | `development` | `development`, `staging`, or `production` |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection for caching/rate limiting |
| `ALLOWED_ORIGINS` | `http://localhost:3000,...` | Comma-separated CORS origins |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_JSON` | `false` | JSON format logs for production |

### Stripe Integration (for billing)

| Variable | Description |
|----------|-------------|
| `STRIPE_SECRET_KEY` | Stripe API secret key (`sk_live_xxx` or `sk_test_xxx`) |
| `STRIPE_PUBLISHABLE_KEY` | Stripe publishable key (`pk_live_xxx` or `pk_test_xxx`) |
| `STRIPE_WEBHOOK_SECRET` | Webhook signing secret (`whsec_xxx`) |
| `STRIPE_PRICE_PRO` | Stripe Price ID for Pro plan |
| `STRIPE_PRICE_ENTERPRISE` | Stripe Price ID for Enterprise plan |

### Admin Panel

| Variable | Default | Description |
|----------|---------|-------------|
| `ADMIN_PASSWORD` | Auto-generated | Admin dashboard password |
| `ADMIN_JWT_SECRET` | Auto-generated | Admin JWT signing key |
| `ADMIN_TOKEN_EXPIRY` | `3600` | Admin token expiry in seconds |

### Rate Limiting

| Variable | Default | Description |
|----------|---------|-------------|
| `RATE_LIMIT_REQUESTS_PER_SECOND` | `100` | Max requests per second |
| `RATE_LIMIT_BURST` | `200` | Burst allowance |

### Monitoring (Optional)

| Variable | Description |
|----------|-------------|
| `SENTRY_DSN` | Sentry error tracking DSN |

---

## Koyeb Environment Setup

To configure environment variables on Koyeb:

1. Go to [app.koyeb.com](https://app.koyeb.com)
2. Select your AgentAuth service
3. Click **Settings** → **Environment variables**
4. Add the following (at minimum):

```bash
# Required
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/agentauth
SECRET_KEY=<run: openssl rand -hex 32>

# Production settings
ENVIRONMENT=production
DEBUG=false
LOG_JSON=true

# Optional: Stripe for billing
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
```

5. Click **Apply** to redeploy with new settings

---

## Support

- Documentation: https://docs.agentauth.in
- Issues: https://github.com/agentauth-io/agentauth/issues
- Email: support@agentauth.in
