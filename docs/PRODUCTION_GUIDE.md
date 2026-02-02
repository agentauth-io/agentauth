# AgentAuth Enterprise Production Guide

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRODUCTION ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐   ┌─────────────────────────────────────────────────────┐ │
│  │   Clients   │   │                   Cloud Provider                    │ │
│  │ (SDKs/APIs) │   │  ┌───────────────────────────────────────────────┐  │ │
│  └──────┬──────┘   │  │              Kubernetes Cluster               │  │ │
│         │          │  │                                               │  │ │
│         ▼          │  │  ┌─────────────────────────────────────────┐  │  │ │
│  ┌──────────────┐  │  │  │           Ingress Controller            │  │  │ │
│  │  Cloudflare  │──┼──┼─▶│   (nginx + TLS + Rate Limiting + WAF)   │  │  │ │
│  │   WAF/CDN    │  │  │  └────────────────────┬────────────────────┘  │  │ │
│  └──────────────┘  │  │                       │                       │  │ │
│                    │  │                       ▼                       │  │ │
│                    │  │  ┌─────────────────────────────────────────┐  │  │ │
│                    │  │  │           AgentAuth API Pods            │  │  │ │
│                    │  │  │         (3-50 replicas, HPA)            │  │  │ │
│                    │  │  │                                         │  │  │ │
│                    │  │  │  ┌─────────┐ ┌─────────┐ ┌─────────┐    │  │  │ │
│                    │  │  │  │  Pod 1  │ │  Pod 2  │ │  Pod 3  │    │  │  │ │
│                    │  │  │  │ FastAPI │ │ FastAPI │ │ FastAPI │    │  │  │ │
│                    │  │  │  └────┬────┘ └────┬────┘ └────┬────┘    │  │  │ │
│                    │  │  └───────┼───────────┼───────────┼─────────┘  │  │ │
│                    │  │          │           │           │            │  │ │
│                    │  │          └───────────┼───────────┘            │  │ │
│                    │  │                      ▼                        │  │ │
│                    │  │  ┌─────────────────────────────────────────┐  │  │ │
│                    │  │  │              Data Layer                 │  │  │ │
│                    │  │  │  ┌─────────────┐  ┌─────────────────┐   │  │  │ │
│                    │  │  │  │ PostgreSQL  │  │     Redis       │   │  │  │ │
│                    │  │  │  │  (Primary)  │  │ (Cache/Session) │   │  │  │ │
│                    │  │  │  └─────────────┘  └─────────────────┘   │  │  │ │
│                    │  │  └─────────────────────────────────────────┘  │  │ │
│                    │  │                                               │  │ │
│                    │  │  ┌─────────────────────────────────────────┐  │  │ │
│                    │  │  │            Observability                │  │  │ │
│                    │  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ │  │  │ │
│                    │  │  │  │Prometheus│ │ Grafana  │ │  Jaeger  │ │  │  │ │
│                    │  │  │  │ Metrics  │ │  Dash    │ │  Traces  │ │  │  │ │
│                    │  │  │  └──────────┘ └──────────┘ └──────────┘ │  │  │ │
│                    │  │  └─────────────────────────────────────────┘  │  │ │
│                    │  │                                               │  │ │
│                    │  └───────────────────────────────────────────────┘  │ │
│                    └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🚀 Deployment Options

### Option 1: Docker Compose (Development/Staging)

```bash
# Start local production-like environment
./scripts/deploy.sh local-up

# Stop
./scripts/deploy.sh local-down
```

### Option 2: Kubernetes (Production)

```bash
# Full deployment pipeline
./scripts/deploy.sh full

# Or step by step:
./scripts/deploy.sh preflight   # Check prerequisites
./scripts/deploy.sh build       # Build and push Docker image
./scripts/deploy.sh deploy      # Deploy to Kubernetes
./scripts/deploy.sh health      # Run health checks
```

### Option 3: Managed Cloud Services

| Component | AWS | GCP | Azure |
|-----------|-----|-----|-------|
| **Kubernetes** | EKS | GKE | AKS |
| **PostgreSQL** | RDS for PostgreSQL | Cloud SQL | Azure Database for PostgreSQL |
| **Redis** | ElastiCache | Memorystore | Azure Cache for Redis |
| **Load Balancer** | ALB/NLB | Cloud Load Balancing | Azure Load Balancer |
| **Secrets** | Secrets Manager | Secret Manager | Key Vault |
| **Monitoring** | CloudWatch | Cloud Monitoring | Azure Monitor |

---

## 📋 Pre-Production Checklist

### Security

- [ ] **Generate new secrets** - Never use example values
  ```bash
  # Master secret (32 bytes)
  openssl rand -hex 32
  
  # API keys
  openssl rand -base64 32
  
  # Database password
  openssl rand -base64 24
  ```

- [ ] **Configure TLS certificates** via cert-manager or load them manually

- [ ] **Enable network policies** in your cluster

- [ ] **Set up WAF** (Cloudflare, AWS WAF, etc.)

- [ ] **Review RBAC** - Limit service account permissions

### Database

- [ ] **Use managed PostgreSQL** for production (RDS, Cloud SQL)
  - Enable automated backups
  - Configure point-in-time recovery
  - Set up read replicas for scaling reads

- [ ] **Use managed Redis** for production (ElastiCache, Memorystore)
  - Enable cluster mode for HA
  - Configure persistence

### Observability

- [ ] **Set up Prometheus/Grafana** for metrics
- [ ] **Configure alerting** for critical thresholds
- [ ] **Enable distributed tracing** (Jaeger/Tempo)
- [ ] **Set up log aggregation** (ELK/Loki)

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | ✅ |
| `REDIS_URL` | Redis connection string | ✅ |
| `MASTER_SECRET` | 32-byte hex secret for crypto | ✅ |
| `API_KEY_INTERNAL` | Internal service API key | ✅ |
| `ENVIRONMENT` | `production`, `staging`, `development` | ✅ |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | ❌ |
| `API_WORKERS` | Number of uvicorn workers | ❌ |

### Kubernetes Secrets (Production)

```bash
# Create secrets from file
kubectl create secret generic agentauth-secrets \
  --namespace agentauth \
  --from-literal=MASTER_SECRET="$(openssl rand -hex 32)" \
  --from-literal=POSTGRES_PASSWORD="$(openssl rand -base64 24)" \
  --from-literal=REDIS_PASSWORD="$(openssl rand -base64 24)" \
  --from-literal=API_KEY_INTERNAL="$(openssl rand -base64 32)"
```

### Using External Secrets Operator (Recommended)

```yaml
# With HashiCorp Vault
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: agentauth-secrets
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: vault-backend
  target:
    name: agentauth-secrets
  data:
    - secretKey: MASTER_SECRET
      remoteRef:
        key: secret/agentauth/production
        property: master_secret
```

---

## 📊 Performance Tuning

### API Server

```yaml
# Optimal resource allocation per pod
resources:
  requests:
    cpu: "500m"
    memory: "1Gi"
  limits:
    cpu: "2000m"
    memory: "4Gi"
```

### PostgreSQL

```sql
-- Recommended settings for authorization workload
-- (High read, medium write)

-- Connection pooling
max_connections = 200
shared_buffers = 4GB
effective_cache_size = 12GB

-- Write performance
wal_buffers = 64MB
checkpoint_completion_target = 0.9
max_wal_size = 4GB

-- Read performance
random_page_cost = 1.1  -- SSD
effective_io_concurrency = 200

-- Parallelism
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
```

### Redis

```conf
# Redis configuration for session/cache
maxmemory 4gb
maxmemory-policy allkeys-lru
activedefrag yes
lazyfree-lazy-eviction yes
```

---

## 🔄 Operations

### Scaling

```bash
# Manual scaling
./scripts/deploy.sh scale 10

# Or via kubectl
kubectl scale deployment/agentauth-api -n agentauth --replicas=10

# HPA handles automatic scaling based on:
# - CPU > 70%
# - Memory > 80%
```

### Rolling Updates

```bash
# Update image (zero downtime)
kubectl set image deployment/agentauth-api \
  api=agentauth/api:v1.2.0 \
  -n agentauth

# Watch rollout
kubectl rollout status deployment/agentauth-api -n agentauth

# Rollback if issues
./scripts/deploy.sh rollback
```

### Database Migrations

```bash
# Run migrations
kubectl exec -n agentauth deployment/agentauth-api -- \
  alembic upgrade head

# Create new migration
kubectl exec -n agentauth deployment/agentauth-api -- \
  alembic revision --autogenerate -m "description"
```

---

## 📈 Monitoring & Alerting

### Key Metrics to Monitor

| Metric | Warning | Critical |
|--------|---------|----------|
| Request latency (p99) | > 200ms | > 500ms |
| Error rate | > 1% | > 5% |
| CPU usage | > 70% | > 90% |
| Memory usage | > 80% | > 95% |
| Authorization denials/min | > 100 | > 500 |
| Audit log size | > 80% capacity | > 95% capacity |

### Grafana Dashboard

Import the provided dashboard from `monitoring/grafana-dashboard.json`

Key panels:
- Authorization decisions (approved/denied)
- Request latency histogram
- Risk score distribution
- Active tokens
- Audit log throughput

### Alerting Rules

```yaml
# Prometheus alerting rules
groups:
  - name: agentauth
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High error rate on AgentAuth API
          
      - alert: HighLatency
        expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High latency on AgentAuth API
```

---

## 🔐 Security Hardening

### Network Security

1. **Use private subnets** for databases
2. **Enable VPC peering** for cross-service communication
3. **Configure security groups** to limit traffic
4. **Use service mesh** (Istio/Linkerd) for mTLS

### Application Security

1. **Rotate secrets regularly**
   ```bash
   # Rotate master secret (requires token invalidation)
   kubectl create secret generic agentauth-secrets-new \
     --from-literal=MASTER_SECRET="$(openssl rand -hex 32)" \
     ...
   ```

2. **Enable audit logging** for all authorization decisions

3. **Implement IP allowlisting** for admin endpoints

4. **Use rate limiting** at multiple levels (Cloudflare, Ingress, App)

### Compliance

For SOC 2, PCI-DSS, and financial regulations:

- ✅ All data encrypted at rest and in transit
- ✅ Comprehensive audit logging with hash chain
- ✅ Role-based access control
- ✅ Automatic session expiration
- ✅ Multi-factor authentication support (via integration)

---

## 🆘 Troubleshooting

### Common Issues

**Pods not starting:**
```bash
kubectl describe pod -n agentauth -l app=agentauth-api
kubectl logs -n agentauth -l app=agentauth-api --previous
```

**Database connection issues:**
```bash
kubectl exec -n agentauth deployment/agentauth-api -- \
  python -c "import asyncpg; print('OK')"
```

**High latency:**
1. Check database connection pool
2. Review Redis cache hit rate
3. Analyze slow query logs
4. Check network policies

### Support

- **Documentation**: https://docs.agentauth.io
- **Status Page**: https://status.agentauth.io
- **Enterprise Support**: support@agentauth.io

---

## 📝 File Reference

```
k8s/
├── namespace.yaml       # Kubernetes namespace
├── secrets.yaml         # Secrets (template - replace values!)
├── configmap.yaml       # Application configuration
├── api-deployment.yaml  # API deployment, service, HPA, PDB
├── databases.yaml       # PostgreSQL and Redis StatefulSets
└── ingress-network.yaml # Ingress and network policies

scripts/
└── deploy.sh            # Deployment automation script

docker-compose.prod.yml  # Local production environment
Dockerfile.prod          # Production container image
nginx.conf               # Nginx load balancer config
prometheus.yml           # Prometheus scrape config
.env.production.example  # Environment variable template
```
