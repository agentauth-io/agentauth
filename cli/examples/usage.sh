#!/bin/bash
# AgentAuth CLI Usage Examples

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== AgentAuth CLI Examples ===${NC}\n"

# 1. Login
echo -e "${GREEN}1. Login to AgentAuth${NC}"
echo "agentauth login"
echo ""

# 2. Check status
echo -e "${GREEN}2. Check connection status${NC}"
echo "agentauth status"
echo ""

# 3. View dashboard
echo -e "${GREEN}3. View dashboard metrics${NC}"
echo "agentauth dashboard"
echo ""

# 4. List agents
echo -e "${GREEN}4. List all agents${NC}"
echo "agentauth agents list"
echo ""

# 5. Register new agent
echo -e "${GREEN}5. Register a new agent${NC}"
echo "agentauth agents register --name shopping-agent"
echo ""

# 6. Create authorization
echo -e "${GREEN}6. Create an authorization${NC}"
echo "agentauth authorize create --agent shopping-agent --intent 'Purchase electronics' --amount 500"
echo ""

# 7. Verify authorization
echo -e "${GREEN}7. Verify an authorization${NC}"
echo "agentauth authorize verify <authorization_id>"
echo ""

# 8. Create spending limit policy
echo -e "${GREEN}8. Create a spending limit policy${NC}"
echo "agentauth policies create --interactive"
echo ""

# 9. View logs
echo -e "${GREEN}9. View recent authorization logs${NC}"
echo "agentauth logs --type authorization --limit 20"
echo ""

# 10. Run integration tests
echo -e "${GREEN}10. Run integration tests${NC}"
echo "agentauth test --verbose"
echo ""

# 11. Export data as JSON
echo -e "${GREEN}11. Export agents as JSON${NC}"
echo "agentauth agents list --format json"
echo ""

# 12. CI/CD usage
echo -e "${GREEN}12. CI/CD non-interactive login${NC}"
echo "agentauth login --api-key \$AGENTAUTH_API_KEY --api-url https://api.agentauth.in"
echo ""
