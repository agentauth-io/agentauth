# AgentAuth Helm Chart

## Quick Start

```bash
# Add repo (if published)
helm repo add agentauth https://charts.agentauth.io
helm repo update

# Install with default values (development)
helm install agentauth ./helm/agentauth \
  --namespace agentauth \
  --create-namespace \
  --set secrets.masterSecret=$(openssl rand -hex 32) \
  --set postgresql.auth.password=$(openssl rand -base64 16) \
  --set redis.auth.password=$(openssl rand -base64 16)

# Install for production with external database
helm install agentauth ./helm/agentauth \
  --namespace agentauth \
  --create-namespace \
  --set postgresql.enabled=false \
  --set redis.enabled=false \
  --set secrets.masterSecret=$MASTER_SECRET \
  --set secrets.databaseUrl=$DATABASE_URL \
  --set secrets.redisUrl=$REDIS_URL \
  --values production-values.yaml
```

## Configuration

See [values.yaml](values.yaml) for all configuration options.

### Key Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of API replicas | `3` |
| `image.repository` | Docker image | `agentauth/api` |
| `image.tag` | Image tag | `latest` |
| `ingress.enabled` | Enable ingress | `true` |
| `ingress.hosts[0].host` | API hostname | `api.agentauth.io` |
| `autoscaling.enabled` | Enable HPA | `true` |
| `autoscaling.minReplicas` | Min replicas | `3` |
| `autoscaling.maxReplicas` | Max replicas | `50` |
| `postgresql.enabled` | Deploy PostgreSQL | `true` |
| `redis.enabled` | Deploy Redis | `true` |

### Production Recommendations

1. **Use external managed databases** (RDS, Cloud SQL, ElastiCache)
2. **Use External Secrets Operator** for secrets management
3. **Enable network policies**
4. **Set appropriate resource limits**

## Upgrading

```bash
helm upgrade agentauth ./helm/agentauth \
  --namespace agentauth \
  --reuse-values \
  --set image.tag=v1.2.0
```

## Uninstalling

```bash
helm uninstall agentauth --namespace agentauth
kubectl delete namespace agentauth
```
