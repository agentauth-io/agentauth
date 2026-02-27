# AgentAuth MCP Server

Model Context Protocol server for AgentAuth — lets AI agents (Claude, GPT, etc.)
authorize purchases and manage policies through standard MCP tools.

## Quick Start

```bash
cd mcp
npm install
npm run build
```

## Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "agentauth": {
      "command": "node",
      "args": ["/path/to/agentauth/mcp/dist/index.js"],
      "env": {
        "AGENTAUTH_API_KEY": "aa_live_xxx",
        "AGENTAUTH_API_URL": "https://agentauth-api.koyeb.app"
      }
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `authorize` | Authorize an AI agent action against configured policies |
| `create_consent` | Create a user spending consent with budget limits |
| `check_budget` | Check remaining daily/monthly budget for a user |
| `list_policies` | List all configured authorization policies |
| `evaluate_policy` | Test policies against a context in the sandbox |
| `create_policy` | Create a new authorization policy |

## Resources

| URI | Description |
|-----|-------------|
| `agentauth://policies` | Current policy list (JSON) |
| `agentauth://health` | API health status |
| `agentauth://openapi` | OpenAPI spec reference |

## Environment Variables

- `AGENTAUTH_API_KEY` — API key for authenticated endpoints
- `AGENTAUTH_API_URL` — Base URL (default: `https://agentauth-api.koyeb.app`)
