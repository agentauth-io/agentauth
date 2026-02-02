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

### Neon (Recommended - Free tier)

1. Go to [neon.tech](https://neon.tech)
2. Create a new project
3. Copy the connection string
4. Set as `DATABASE_URL` in your deployment

### Supabase

1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Go to Settings → Database → Connection string
4. Use the "URI" format

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

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `SECRET_KEY` | Yes | JWT signing key (generate with `openssl rand -hex 32`) |
| `DEBUG` | No | Set to `false` in production |
| `CORS_ORIGINS` | No | Comma-separated allowed origins |
| `PORT` | No | Server port (usually auto-set) |

---

## Support

- Documentation: https://docs.agentauth.in
- Issues: https://github.com/agentauth-io/agentauth/issues
- Email: support@agentauth.in
