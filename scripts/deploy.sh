#!/bin/bash
# =============================================================================
# AgentAuth Production Deployment Script
# =============================================================================
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration
NAMESPACE="agentauth"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-docker.io/agentauth}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

# =============================================================================
# Pre-flight checks
# =============================================================================
preflight_checks() {
    log_info "Running pre-flight checks..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl not found. Please install kubectl."
        exit 1
    fi
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster."
        exit 1
    fi
    
    # Check docker
    if ! command -v docker &> /dev/null; then
        log_error "docker not found. Please install Docker."
        exit 1
    fi
    
    log_success "Pre-flight checks passed."
}

# =============================================================================
# Build and push Docker image
# =============================================================================
build_and_push() {
    log_info "Building Docker image..."
    
    docker build \
        -f Dockerfile.prod \
        -t "${DOCKER_REGISTRY}/api:${IMAGE_TAG}" \
        -t "${DOCKER_REGISTRY}/api:latest" \
        .
    
    log_info "Pushing Docker image to registry..."
    docker push "${DOCKER_REGISTRY}/api:${IMAGE_TAG}"
    docker push "${DOCKER_REGISTRY}/api:latest"
    
    log_success "Docker image built and pushed: ${DOCKER_REGISTRY}/api:${IMAGE_TAG}"
}

# =============================================================================
# Deploy to Kubernetes
# =============================================================================
deploy_k8s() {
    log_info "Deploying to Kubernetes..."
    
    # Create namespace
    kubectl apply -f k8s/namespace.yaml
    
    # Check if secrets exist (don't override production secrets)
    if ! kubectl get secret agentauth-secrets -n ${NAMESPACE} &> /dev/null; then
        log_warn "Secrets not found. Applying template (CHANGE VALUES IN PRODUCTION)..."
        kubectl apply -f k8s/secrets.yaml
    else
        log_info "Using existing secrets."
    fi
    
    # Apply configs
    kubectl apply -f k8s/configmap.yaml
    
    # Deploy databases
    kubectl apply -f k8s/databases.yaml
    
    # Wait for databases
    log_info "Waiting for PostgreSQL to be ready..."
    kubectl rollout status statefulset/postgres -n ${NAMESPACE} --timeout=300s
    
    log_info "Waiting for Redis to be ready..."
    kubectl rollout status statefulset/redis -n ${NAMESPACE} --timeout=300s
    
    # Deploy API
    kubectl apply -f k8s/api-deployment.yaml
    
    # Wait for API
    log_info "Waiting for API deployment to be ready..."
    kubectl rollout status deployment/agentauth-api -n ${NAMESPACE} --timeout=300s
    
    # Apply networking
    kubectl apply -f k8s/ingress-network.yaml
    
    log_success "Deployment complete!"
}

# =============================================================================
# Health check
# =============================================================================
health_check() {
    log_info "Running health checks..."
    
    # Get a pod name
    POD=$(kubectl get pods -n ${NAMESPACE} -l app=agentauth-api -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    
    if [ -z "$POD" ]; then
        log_error "No API pods found."
        return 1
    fi
    
    # Check health endpoint
    HEALTH=$(kubectl exec -n ${NAMESPACE} ${POD} -- curl -s http://localhost:8000/health 2>/dev/null || echo "failed")
    
    if [[ "$HEALTH" == *"healthy"* ]]; then
        log_success "API health check passed."
    else
        log_warn "API health check failed or returned: $HEALTH"
    fi
    
    # Show pod status
    log_info "Pod status:"
    kubectl get pods -n ${NAMESPACE}
    
    # Show services
    log_info "Services:"
    kubectl get svc -n ${NAMESPACE}
    
    # Show ingress
    log_info "Ingress:"
    kubectl get ingress -n ${NAMESPACE}
}

# =============================================================================
# Rollback
# =============================================================================
rollback() {
    log_warn "Rolling back deployment..."
    kubectl rollout undo deployment/agentauth-api -n ${NAMESPACE}
    kubectl rollout status deployment/agentauth-api -n ${NAMESPACE} --timeout=300s
    log_success "Rollback complete."
}

# =============================================================================
# Logs
# =============================================================================
show_logs() {
    POD=$(kubectl get pods -n ${NAMESPACE} -l app=agentauth-api -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    
    if [ -z "$POD" ]; then
        log_error "No API pods found."
        return 1
    fi
    
    kubectl logs -n ${NAMESPACE} ${POD} --tail=100 -f
}

# =============================================================================
# Scale
# =============================================================================
scale() {
    REPLICAS=${1:-3}
    log_info "Scaling to ${REPLICAS} replicas..."
    kubectl scale deployment/agentauth-api -n ${NAMESPACE} --replicas=${REPLICAS}
    log_success "Scaled to ${REPLICAS} replicas."
}

# =============================================================================
# Local development with Docker Compose
# =============================================================================
local_up() {
    log_info "Starting local development environment..."
    docker compose -f docker-compose.prod.yml up -d
    log_success "Local environment started. API available at http://localhost:8000"
}

local_down() {
    log_info "Stopping local development environment..."
    docker compose -f docker-compose.prod.yml down
    log_success "Local environment stopped."
}

# =============================================================================
# Main
# =============================================================================
show_usage() {
    echo ""
    echo "AgentAuth Deployment Script"
    echo ""
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  preflight     Run pre-flight checks"
    echo "  build         Build and push Docker image"
    echo "  deploy        Deploy to Kubernetes"
    echo "  full          Run build + deploy"
    echo "  health        Run health checks"
    echo "  rollback      Rollback to previous deployment"
    echo "  logs          Show API logs"
    echo "  scale <n>     Scale to n replicas"
    echo "  local-up      Start local Docker Compose environment"
    echo "  local-down    Stop local Docker Compose environment"
    echo ""
    echo "Environment variables:"
    echo "  DOCKER_REGISTRY  Docker registry (default: docker.io/agentauth)"
    echo "  IMAGE_TAG        Image tag (default: latest)"
    echo ""
}

case "${1:-help}" in
    preflight)
        preflight_checks
        ;;
    build)
        preflight_checks
        build_and_push
        ;;
    deploy)
        preflight_checks
        deploy_k8s
        health_check
        ;;
    full)
        preflight_checks
        build_and_push
        deploy_k8s
        health_check
        ;;
    health)
        health_check
        ;;
    rollback)
        rollback
        ;;
    logs)
        show_logs
        ;;
    scale)
        scale "${2:-3}"
        ;;
    local-up)
        local_up
        ;;
    local-down)
        local_down
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        log_error "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac
