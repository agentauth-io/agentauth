#!/usr/bin/env python3
"""
AgentAuth CLI — Developer command-line interface.

Usage:
    python -m cli.agentauth_cli status
    python -m cli.agentauth_cli consent create --user user_123 --intent "Buy flight" --amount 500
    python -m cli.agentauth_cli authorize --token <TOKEN> --amount 347
    python -m cli.agentauth_cli verify --code <AUTH_CODE> --amount 347
    python -m cli.agentauth_cli agents list
    python -m cli.agentauth_cli configure --url https://api.agentauth.in --key aa_live_xxx

Configuration is stored in ~/.agentauth/config.json
"""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

import httpx

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text

    HAS_RICH = True
except ImportError:
    HAS_RICH = False

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CONFIG_DIR = Path.home() / ".agentauth"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_URL = "http://localhost:8000"


def _load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def _save_config(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


def _get_url(args) -> str:
    if getattr(args, "url", None):
        return args.url
    cfg = _load_config()
    return cfg.get("api_url", os.environ.get("AGENTAUTH_API_URL", DEFAULT_URL))


def _get_key(args) -> Optional[str]:
    if getattr(args, "key", None):
        return args.key
    cfg = _load_config()
    return cfg.get("api_key", os.environ.get("AGENTAUTH_API_KEY"))


def _headers(args) -> dict:
    headers = {"Content-Type": "application/json"}
    key = _get_key(args)
    if key:
        headers["X-API-Key"] = key
    return headers


def _client(args) -> httpx.Client:
    return httpx.Client(base_url=_get_url(args), headers=_headers(args), timeout=15)


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

if HAS_RICH:
    console = Console()
else:
    class _FallbackConsole:
        def print(self, msg="", **kwargs):
            print(msg)
    console = _FallbackConsole()


def _print_json(data, use_json: bool = False):
    if use_json:
        print(json.dumps(data, indent=2, default=str))
    elif HAS_RICH:
        console.print_json(json.dumps(data, default=str))
    else:
        print(json.dumps(data, indent=2, default=str))


def _error(msg: str):
    if HAS_RICH:
        console.print(f"[bold red]Error:[/bold red] {msg}")
    else:
        print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def _success(msg: str):
    if HAS_RICH:
        console.print(f"[bold green]✓[/bold green] {msg}")
    else:
        print(f"✓ {msg}")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_configure(args):
    """Save API URL and key to ~/.agentauth/config.json."""
    cfg = _load_config()
    if args.url:
        cfg["api_url"] = args.url.rstrip("/")
    if args.key:
        cfg["api_key"] = args.key
    _save_config(cfg)
    _success(f"Configuration saved to {CONFIG_FILE}")
    if args.url:
        console.print(f"  API URL: {cfg.get('api_url')}")
    if args.key:
        console.print(f"  API Key: {cfg.get('api_key', '')[:20]}...")


def cmd_status(args):
    """Check API health and display status."""
    url = _get_url(args)
    try:
        with _client(args) as c:
            # Health
            resp = c.get("/health")
            health = resp.json()

            # Root info
            info_resp = c.get("/")
            info = info_resp.json()

        if args.json:
            _print_json({"health": health, "info": info}, use_json=True)
            return

        if HAS_RICH:
            table = Table(title="AgentAuth Status")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            table.add_row("API URL", url)
            table.add_row("Status", health.get("status", "unknown"))
            table.add_row("Name", info.get("name", ""))
            table.add_row("Version", info.get("version", ""))
            console.print(table)
        else:
            print(f"API URL:  {url}")
            print(f"Status:   {health.get('status')}")
            print(f"Version:  {info.get('version')}")
    except httpx.ConnectError:
        _error(f"Cannot connect to {url}")
    except Exception as e:
        _error(str(e))


def cmd_consent_create(args):
    """Create a new consent."""
    payload = {
        "user_id": args.user,
        "intent": {"description": args.intent},
        "constraints": {"max_amount": args.amount, "currency": args.currency},
        "options": {"expires_in_seconds": args.expires, "single_use": not args.multi_use},
        "signature": "cli_generated",
        "public_key": "cli_key",
    }
    if args.merchants:
        payload["constraints"]["allowed_merchants"] = args.merchants.split(",")

    try:
        with _client(args) as c:
            resp = c.post("/v1/consents", json=payload)

        if resp.status_code == 201:
            data = resp.json()
            if args.json:
                _print_json(data, use_json=True)
            else:
                _success("Consent created")
                console.print(f"  Consent ID: [cyan]{data['consent_id']}[/cyan]")
                console.print(f"  Token:      [dim]{data['delegation_token'][:40]}...[/dim]")
                console.print(f"  Expires:    {data['expires_at']}")
        else:
            _error(f"HTTP {resp.status_code}: {resp.text}")
    except httpx.ConnectError:
        _error(f"Cannot connect to {_get_url(args)}")


def cmd_consent_list(args):
    """List consents."""
    try:
        with _client(args) as c:
            resp = c.get("/v1/consents", params={"limit": args.limit})

        if resp.status_code != 200:
            _error(f"HTTP {resp.status_code}: {resp.text}")

        data = resp.json()
        if args.json:
            _print_json(data, use_json=True)
            return

        consents = data.get("consents", [])
        if not consents:
            console.print("[dim]No consents found.[/dim]")
            return

        if HAS_RICH:
            table = Table(title=f"Consents ({data.get('total', len(consents))} total)")
            table.add_column("Consent ID", style="cyan", max_width=24)
            table.add_column("User", style="green")
            table.add_column("Intent", max_width=30)
            table.add_column("Active", justify="center")
            table.add_column("Created", style="dim")
            for c in consents:
                table.add_row(
                    c.get("consent_id", "")[:22],
                    c.get("user_id", ""),
                    c.get("intent_description", ""),
                    "✓" if c.get("is_active") else "✗",
                    str(c.get("created_at", ""))[:19],
                )
            console.print(table)
    except httpx.ConnectError:
        _error(f"Cannot connect to {_get_url(args)}")


def cmd_authorize(args):
    """Authorize a transaction."""
    payload = {
        "delegation_token": args.token,
        "action": "payment",
        "transaction": {
            "amount": args.amount,
            "currency": args.currency,
            "merchant_id": args.merchant,
        },
    }
    try:
        with _client(args) as c:
            resp = c.post("/v1/authorize", json=payload)

        data = resp.json()
        if args.json:
            _print_json(data, use_json=True)
            return

        decision = data.get("decision", "UNKNOWN")
        if decision == "ALLOW":
            _success(f"AUTHORIZED — code: {data.get('authorization_code')}")
        elif decision == "DENY":
            _error(f"DENIED — {data.get('reason')}: {data.get('message', '')}")
        else:
            console.print(f"[yellow]Decision: {decision}[/yellow]")
            _print_json(data)
    except httpx.ConnectError:
        _error(f"Cannot connect to {_get_url(args)}")


def cmd_verify(args):
    """Verify an authorization code."""
    payload = {
        "authorization_code": args.code,
        "transaction": {"amount": args.amount, "currency": args.currency},
    }
    if args.merchant:
        payload["merchant_id"] = args.merchant

    try:
        with _client(args) as c:
            resp = c.post("/v1/verify", json=payload)

        data = resp.json()
        if args.json:
            _print_json(data, use_json=True)
            return

        if data.get("valid"):
            _success("VALID — Authorization verified")
            proof = data.get("consent_proof", {})
            if proof:
                console.print(f"  User intent:  {proof.get('user_intent')}")
                console.print(f"  Max amount:   ${proof.get('max_authorized_amount')}")
                console.print(f"  Actual:       ${proof.get('actual_amount')}")
        else:
            _error(f"INVALID — {data.get('error', 'Unknown error')}")
    except httpx.ConnectError:
        _error(f"Cannot connect to {_get_url(args)}")


def cmd_agents_list(args):
    """List agents."""
    try:
        with _client(args) as c:
            resp = c.get("/v1/agents")

        data = resp.json()
        if args.json:
            _print_json(data, use_json=True)
            return

        agents = data.get("agents", [])
        if not agents:
            console.print("[dim]No agents registered.[/dim]")
            return

        if HAS_RICH:
            table = Table(title="Registered Agents")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Status")
            table.add_column("Created", style="dim")
            for a in agents:
                table.add_row(a["id"], a["name"], a["status"], a.get("created_at", "")[:19])
            console.print(table)
    except httpx.ConnectError:
        _error(f"Cannot connect to {_get_url(args)}")


def cmd_agents_create(args):
    """Create an agent."""
    payload = {"name": args.name}
    if args.description:
        payload["description"] = args.description

    try:
        with _client(args) as c:
            resp = c.post("/v1/agents", json=payload)

        data = resp.json()
        if args.json:
            _print_json(data, use_json=True)
        else:
            _success(f"Agent created: {data.get('id')} ({data.get('name')})")
    except httpx.ConnectError:
        _error(f"Cannot connect to {_get_url(args)}")


def cmd_agents_delete(args):
    """Delete an agent."""
    try:
        with _client(args) as c:
            resp = c.delete(f"/v1/agents/{args.agent_id}")

        if resp.status_code in (200, 204):
            _success(f"Agent {args.agent_id} deleted")
        else:
            _error(f"HTTP {resp.status_code}: {resp.text}")
    except httpx.ConnectError:
        _error(f"Cannot connect to {_get_url(args)}")


# ---------------------------------------------------------------------------
# CLI parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentauth",
        description="AgentAuth CLI — Authorization layer for AI agent purchases",
    )
    parser.add_argument("--url", help="API base URL (overrides config)")
    parser.add_argument("--key", help="API key (overrides config)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")

    sub = parser.add_subparsers(dest="command", help="Command to run")

    # configure
    cfg_parser = sub.add_parser("configure", help="Save API URL and key")
    cfg_parser.add_argument("--url", dest="cfg_url", help="API URL")
    cfg_parser.add_argument("--key", dest="cfg_key", help="API key")

    # status
    sub.add_parser("status", help="Check API health")

    # consent
    consent_parser = sub.add_parser("consent", help="Consent management")
    consent_sub = consent_parser.add_subparsers(dest="consent_cmd")

    create_p = consent_sub.add_parser("create", help="Create a consent")
    create_p.add_argument("--user", required=True, help="User ID")
    create_p.add_argument("--intent", required=True, help="Intent description")
    create_p.add_argument("--amount", type=float, required=True, help="Max amount")
    create_p.add_argument("--currency", default="USD", help="Currency (default: USD)")
    create_p.add_argument("--expires", type=int, default=3600, help="Expiry in seconds")
    create_p.add_argument("--merchants", help="Comma-separated merchant IDs")
    create_p.add_argument("--multi-use", action="store_true", help="Allow multiple uses")

    consent_sub.add_parser("list", help="List consents").add_argument(
        "--limit", type=int, default=20
    )

    # authorize
    auth_parser = sub.add_parser("authorize", help="Authorize a transaction")
    auth_parser.add_argument("--token", required=True, help="Delegation token")
    auth_parser.add_argument("--amount", type=float, required=True, help="Transaction amount")
    auth_parser.add_argument("--currency", default="USD", help="Currency")
    auth_parser.add_argument("--merchant", help="Merchant ID")

    # verify
    ver_parser = sub.add_parser("verify", help="Verify authorization code")
    ver_parser.add_argument("--code", required=True, help="Authorization code")
    ver_parser.add_argument("--amount", type=float, required=True, help="Transaction amount")
    ver_parser.add_argument("--currency", default="USD", help="Currency")
    ver_parser.add_argument("--merchant", help="Merchant ID")

    # agents
    agents_parser = sub.add_parser("agents", help="Agent management")
    agents_sub = agents_parser.add_subparsers(dest="agents_cmd")
    agents_sub.add_parser("list", help="List agents")
    ac = agents_sub.add_parser("create", help="Create an agent")
    ac.add_argument("--name", required=True, help="Agent name")
    ac.add_argument("--description", help="Agent description")
    ad = agents_sub.add_parser("delete", help="Delete an agent")
    ad.add_argument("--agent-id", required=True, help="Agent ID to delete")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Route to configure (special: uses cfg_url/cfg_key)
    if args.command == "configure":
        args.url = getattr(args, "cfg_url", None)
        args.key = getattr(args, "cfg_key", None)
        cmd_configure(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "consent":
        if args.consent_cmd == "create":
            cmd_consent_create(args)
        elif args.consent_cmd == "list":
            cmd_consent_list(args)
        else:
            console.print("[dim]Usage: agentauth consent [create|list][/dim]")
    elif args.command == "authorize":
        cmd_authorize(args)
    elif args.command == "verify":
        cmd_verify(args)
    elif args.command == "agents":
        if args.agents_cmd == "list":
            cmd_agents_list(args)
        elif args.agents_cmd == "create":
            cmd_agents_create(args)
        elif args.agents_cmd == "delete":
            cmd_agents_delete(args)
        else:
            console.print("[dim]Usage: agentauth agents [list|create|delete][/dim]")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
