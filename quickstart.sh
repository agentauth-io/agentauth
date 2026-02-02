#!/bin/bash
#
# AgentAuth Quick Start Script
# Run this to start the server and test the API
#

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}"
echo "============================================================"
echo "           AgentAuth Quick Start"
echo "============================================================"
echo -e "${NC}"

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

# Kill any existing server on port 8000
if lsof -i :8000 &>/dev/null; then
    echo -e "${YELLOW}Stopping existing server on port 8000...${NC}"
    pkill -f "production_server.py" 2>/dev/null || true
    sleep 2
fi

# Start Redis if not running (via Docker)
if ! redis-cli ping &>/dev/null; then
    echo -e "${YELLOW}Starting Redis...${NC}"
    if command -v docker &>/dev/null; then
        docker run -d --name agentauth-redis -p 6379:6379 redis:alpine 2>/dev/null || true
        sleep 2
    else
        echo -e "${RED}Redis not running. Install Docker or Redis locally.${NC}"
    fi
fi

# Start the server
echo -e "${GREEN}Starting AgentAuth server...${NC}"
export DEBUG=true
python production_server.py &
SERVER_PID=$!

# Wait for server to start
echo -e "${YELLOW}Waiting for server to start...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8000/health &>/dev/null; then
        break
    fi
    sleep 1
done

# Test the API
echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}                    API Test Results${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Health check
echo -e "${GREEN}1. Health Check:${NC}"
curl -s http://localhost:8000/health | python -m json.tool
echo ""

# Create API Key
echo -e "${GREEN}2. Create API Key:${NC}"
API_RESPONSE=$(curl -s -X POST "http://localhost:8000/v1/api-key/create?owner=demo_user" \
  -H "X-API-Key: bootstrap" \
  -H "Content-Type: application/json")
echo "$API_RESPONSE" | python -m json.tool
API_KEY=$(echo "$API_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['key'])" 2>/dev/null || echo "")

if [ -z "$API_KEY" ]; then
    echo -e "${RED}Failed to create API key${NC}"
    exit 1
fi
echo ""

# Authorize a transaction
echo -e "${GREEN}3. Authorize Transaction (\$150 at Amazon):${NC}"
curl -s -X POST http://localhost:8000/v1/authorize \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "shopping_agent",
    "user_id": "user_123",
    "amount": 150.00,
    "currency": "USD",
    "merchant_id": "amazon",
    "merchant_name": "Amazon",
    "description": "Wireless Headphones"
  }' | python -m json.tool
echo ""

# Authorize over-limit transaction
echo -e "${GREEN}4. Authorize Over-Limit Transaction (\$50,000):${NC}"
curl -s -X POST http://localhost:8000/v1/authorize \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "shopping_agent",
    "user_id": "user_123",
    "amount": 50000.00,
    "currency": "USD",
    "merchant_id": "luxury",
    "merchant_name": "Luxury Store",
    "description": "Diamond Ring"
  }' | python -m json.tool
echo ""

# Rate limit status
echo -e "${GREEN}5. Rate Limit Status:${NC}"
curl -s http://localhost:8000/v1/rate-limits/status \
  -H "X-API-Key: $API_KEY" | python -m json.tool
echo ""

echo -e "${BLUE}============================================================${NC}"
echo -e "${GREEN}✅ AgentAuth is running!${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""
echo -e "Server:      ${GREEN}http://localhost:8000${NC}"
echo -e "API Docs:    ${GREEN}http://localhost:8000/docs${NC}"
echo -e "Health:      ${GREEN}http://localhost:8000/health${NC}"
echo -e "API Key:     ${GREEN}${API_KEY:0:40}...${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Keep running
wait $SERVER_PID
