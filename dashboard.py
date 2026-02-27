#!/usr/bin/env python3
"""
AgentAuth Terminal Dashboard

A real-time monitoring dashboard for AgentAuth consents and authorizations.
Uses Rich for beautiful terminal UI.

Usage:
    python dashboard.py
    python dashboard.py --url https://api.agentauth.in --key aa_live_xxx

Requirements:
    pip install rich httpx
"""
import argparse
import os
import asyncio
from datetime import datetime
from typing import Optional

try:
    from rich.console import Console
    from rich.table import Table
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.live import Live
    from rich.text import Text
    from rich.align import Align
    import httpx
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.run(["pip", "install", "rich", "httpx", "-q"], check=True)
    from rich.console import Console
    from rich.table import Table
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.live import Live
    from rich.text import Text
    from rich.align import Align
    import httpx


# Configuration
DEFAULT_API_URL = os.environ.get(
    "AGENTAUTH_API_URL", "https://agentauth-production.up.railway.app"
)
REFRESH_INTERVAL = 2  # seconds
MAX_RETRIES = 3

console = Console()


class Dashboard:
    """AgentAuth monitoring dashboard."""

    def __init__(self, api_url: str = DEFAULT_API_URL, api_key: Optional[str] = None):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key or os.environ.get("AGENTAUTH_API_KEY")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        self.client = httpx.AsyncClient(timeout=10, headers=headers)
        self.consents = []
        self.recent_auths = []
        self.stats = {
            "total_consents": 0,
            "total_authorizations": 0,
            "allowed": 0,
            "denied": 0,
            "api_status": "Connecting...",
            "version": "",
        }
        self.last_update = None
        self.error = None
        self._consecutive_errors = 0

    async def fetch_health(self) -> bool:
        """Check API health."""
        try:
            resp = await self.client.get(f"{self.api_url}/health")
            if resp.status_code == 200:
                self.stats["api_status"] = "🟢 Healthy"
                self._consecutive_errors = 0
            else:
                self.stats["api_status"] = f"🟡 HTTP {resp.status_code}"
            return resp.status_code == 200
        except httpx.ConnectError:
            self._consecutive_errors += 1
            self.stats["api_status"] = f"🔴 Unreachable ({self._consecutive_errors})"
            return False
        except Exception as e:
            self._consecutive_errors += 1
            self.stats["api_status"] = f"🔴 {str(e)[:25]}"
            return False

    async def fetch_data(self):
        """Fetch latest data from API with graceful error handling."""
        try:
            healthy = await self.fetch_health()
            if not healthy:
                self.last_update = datetime.now()
                return

            # Get API info
            try:
                info_resp = await self.client.get(f"{self.api_url}/")
                if info_resp.status_code == 200:
                    self.stats["version"] = info_resp.json().get("version", "")
            except Exception:
                pass

            # Fetch consents
            try:
                resp = await self.client.get(
                    f"{self.api_url}/v1/consents", params={"limit": 15}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    self.consents = (
                        data if isinstance(data, list) else data.get("consents", [])
                    )
                    self.stats["total_consents"] = (
                        data.get("total", len(self.consents))
                        if isinstance(data, dict)
                        else len(self.consents)
                    )
            except Exception:
                pass

            self.last_update = datetime.now()
            self.error = None
        except Exception as e:
            self.error = str(e)
            self.last_update = datetime.now()

    def make_header(self) -> Panel:
        """Create the header panel."""
        header_text = Text()
        header_text.append("⚡ AgentAuth Dashboard ", style="bold cyan")
        header_text.append(f"| API: {self.stats['api_status']} ", style="white")
        if self.stats["version"]:
            header_text.append(f"| v{self.stats['version']} ", style="dim")
        header_text.append(
            f"| Updated: {self.last_update.strftime('%H:%M:%S') if self.last_update else 'Never'}",
            style="dim",
        )
        auth_status = "🔑 Authenticated" if self.api_key else "🔓 No API Key"
        header_text.append(f" | {auth_status}", style="dim")

        return Panel(Align.center(header_text), style="blue", height=3)

    def make_stats(self) -> Panel:
        """Create the stats panel."""
        stats_text = Text()
        stats_text.append(
            f"📋 Consents: {self.stats['total_consents']}  ", style="cyan"
        )
        stats_text.append(
            f"✅ Allowed: {self.stats['allowed']}  ", style="green"
        )
        stats_text.append(
            f"❌ Denied: {self.stats['denied']}  ", style="red"
        )
        stats_text.append(f"🔗 {self.api_url}", style="dim")

        return Panel(Align.center(stats_text), title="📊 Statistics", height=5)

    def make_consents_table(self) -> Panel:
        """Create the consents table."""
        table = Table(title="Recent Consents", expand=True)
        table.add_column("Consent ID", style="cyan", no_wrap=True, max_width=24)
        table.add_column("User", style="green", max_width=15)
        table.add_column("Intent", max_width=30)
        table.add_column("Max Amount", justify="right", style="magenta")
        table.add_column("Active", justify="center")
        table.add_column("Created", style="dim")

        if self.consents:
            for consent in self.consents[:12]:
                consent_id = consent.get("consent_id", consent.get("id", "N/A"))
                constraints = consent.get("constraints", {})
                max_amount = constraints.get("max_amount", 0) if isinstance(constraints, dict) else 0
                table.add_row(
                    str(consent_id)[:22],
                    consent.get("user_id", "N/A"),
                    consent.get("intent_description", "")[:28],
                    f"${max_amount:,.2f}",
                    "✓" if consent.get("is_active", True) else "✗",
                    str(consent.get("created_at", ""))[:19],
                )
        else:
            table.add_row("-", "No consents yet", "-", "-", "-", "-")

        return Panel(table, title="📋 Live Consents", border_style="cyan")

    def make_activity_panel(self) -> Panel:
        """Create the activity panel."""
        if self.error:
            content = Text(f"⚠️  Error: {self.error}\n", style="red")
            content.append("Retrying automatically...", style="dim")
        elif self._consecutive_errors > 0:
            content = Text()
            content.append(
                f"⚠️  Connection issues ({self._consecutive_errors} failures). Retrying...\n",
                style="yellow",
            )
            content.append("Press Ctrl+C to exit", style="dim")
        else:
            content = Text()
            content.append("Monitoring AgentAuth activity...\n", style="dim")
            content.append("Press ", style="dim")
            content.append("Ctrl+C", style="bold red")
            content.append(" to exit", style="dim")

        return Panel(content, title="📡 Activity", border_style="green")

    def make_layout(self) -> Layout:
        """Create the full layout."""
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="stats", size=5),
            Layout(name="main"),
            Layout(name="footer", size=6),
        )

        layout["header"].update(self.make_header())
        layout["stats"].update(self.make_stats())
        layout["main"].update(self.make_consents_table())
        layout["footer"].update(self.make_activity_panel())

        return layout

    async def run(self):
        """Run the dashboard with auto-reconnect."""
        console.clear()

        with Live(
            self.make_layout(), refresh_per_second=1, console=console
        ) as live:
            while True:
                await self.fetch_data()
                live.update(self.make_layout())
                # Back off if experiencing errors
                delay = (
                    min(REFRESH_INTERVAL * (2 ** self._consecutive_errors), 30)
                    if self._consecutive_errors > 0
                    else REFRESH_INTERVAL
                )
                await asyncio.sleep(delay)

    async def close(self):
        """Close the client."""
        await self.client.aclose()


def parse_args():
    parser = argparse.ArgumentParser(
        description="AgentAuth Terminal Dashboard"
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_API_URL,
        help=f"API URL (default: {DEFAULT_API_URL})",
    )
    parser.add_argument("--key", default=None, help="API key for authenticated requests")
    parser.add_argument(
        "--interval",
        type=int,
        default=REFRESH_INTERVAL,
        help=f"Refresh interval in seconds (default: {REFRESH_INTERVAL})",
    )
    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_args()
    dashboard = Dashboard(api_url=args.url, api_key=args.key)

    global REFRESH_INTERVAL
    REFRESH_INTERVAL = args.interval

    console.print("\n[bold cyan]⚡ AgentAuth Dashboard[/bold cyan]")
    console.print(f"[dim]Connecting to {args.url}...[/dim]")
    if args.key:
        console.print(f"[dim]Using API key: {args.key[:15]}...[/dim]")
    console.print()

    try:
        await dashboard.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped.[/yellow]")
    finally:
        await dashboard.close()


if __name__ == "__main__":
    asyncio.run(main())
