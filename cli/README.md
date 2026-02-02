<p align="center">
  <img src="https://agentauth.in/logo.png" alt="AgentAuth" width="120" />
</p>

<h1 align="center">AgentAuth CLI</h1>

<p align="center">
  <strong>Authorization Infrastructure for AI Agents</strong>
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/@agentauth/cli"><img src="https://img.shields.io/npm/v/@agentauth/cli.svg?style=flat-square" alt="npm version" /></a>
  <a href="https://www.npmjs.com/package/@agentauth/cli"><img src="https://img.shields.io/npm/dm/@agentauth/cli.svg?style=flat-square" alt="npm downloads" /></a>
  <a href="https://github.com/agentauth-io/agentauth/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square" alt="license" /></a>
</p>

<p align="center">
  <a href="https://docs.agentauth.in">Documentation</a> •
  <a href="https://app.agentauth.in">Dashboard</a> •
  <a href="https://agentauth.in">Website</a>
</p>

---

## What is AgentAuth?

AgentAuth is the **authorization layer for AI agents**. When AI agents need to make purchases, book services, or access resources on behalf of users, AgentAuth provides:

- 🔐 **User Consent Management** - Users set spending limits and approve actions
- ✅ **Real-time Authorization** - Verify every agent action before execution  
- 📊 **Audit Logging** - Complete visibility into what agents do
- 🛡️ **Policy Engine** - Define rules for agent behavior

## Installation

```bash
# Using npm
npm install -g @agentauth/cli

# Using yarn  
yarn global add @agentauth/cli

# Using pnpm
pnpm add -g @agentauth/cli
```

Verify installation:

```bash
agentauth --version
```

## Quick Start

### 1. Get Your API Key

Sign up at [app.agentauth.in](https://app.agentauth.in) and create an API key.

### 2. Authenticate

```bash
agentauth login
```

Enter your API key when prompted. Your credentials are stored securely.

### 3. Check Status

```bash
agentauth status
```

## Commands

### Authentication

```bash
agentauth login              # Interactive login
agentauth login -k <key>     # Login with API key
agentauth logout             # Clear credentials
agentauth status             # Check connection
```

### Consents

```bash
agentauth consents list                    # List all consents
agentauth consents get <id>                # View details
agentauth consents revoke <id>             # Revoke consent
```

### Authorization

```bash
agentauth authorize create                 # Create authorization
agentauth authorize verify <id>            # Verify authorization
```

### Agents

```bash
agentauth agents list                      # List agents
agentauth agents get <id>                  # View agent
```

### Policies

```bash
agentauth policies list                    # List policies
agentauth policies create                  # Create policy
```

### Monitoring

```bash
agentauth logs                             # View logs
agentauth logs --limit 50                  # Limit results
agentauth logs --type authorization        # Filter by type
```

### Configuration

```bash
agentauth config                           # View config
agentauth config --api-url <url>           # Set API URL
agentauth config --format json             # Set output format
```

## Output Formats

```bash
agentauth consents list                    # Table (default)
agentauth consents list --format json      # JSON
agentauth status --json                    # JSON
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `AGENTAUTH_API_KEY` | API key for authentication |
| `AGENTAUTH_API_URL` | API URL override |

## CI/CD Usage

```bash
export AGENTAUTH_API_KEY=aa_live_xxxxx
agentauth login --api-key $AGENTAUTH_API_KEY
agentauth consents list --format json
```

## Self-Hosted

```bash
agentauth config --api-url https://api.your-instance.com
agentauth login
```

## Requirements

- Node.js 18.0.0 or higher

## Support

- 📚 [Documentation](https://docs.agentauth.in)
- 📧 [support@agentauth.in](mailto:support@agentauth.in)
- 🐛 [GitHub Issues](https://github.com/agentauth-io/agentauth/issues)

## License

MIT License

---

<p align="center">
  Made with ❤️ by <a href="https://agentauth.in">AgentAuth</a>
</p>
