#!/usr/bin/env python3
"""
AgentAuth Terminal Dashboard

A real-time monitoring dashboard for AgentAuth consents and authorizations.
Uses Rich for beautiful terminal UI.

Usage:
    python dashboard.py

Requirements:
    pip install rich httpx
"""
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
    os.system("pip install rich httpx -q")
    from rich.console import Console
    from rich.table import Table
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.live import Live
    from rich.text import Text
    from rich.align import Align
    import httpx


# Configuration
API_URL = os.environ.get("AGENTAUTH_API_URL", "https://agentauth-production.up.railway.app")
REFRESH_INTERVAL = 2  # seconds

console = Console()


class Dashboard:
    """AgentAuth monitoring dashboard."""
    
    def __init__(self, api_url: str = API_URL):
        self.api_url = api_url
        self.client = httpx.AsyncClient(timeout=10)
        self.consents = []
        self.authorizations = []
        self.stats = {
            "total_consents": 0,
            "total_authorizations": 0,
            "allowed": 0,
            "denied": 0,
            "api_status": "Unknown",
        }
        self.last_update = None
        self.error = None
    
    async def fetch_health(self) -> bool:
        """Check API health."""
        try:
            resp = await self.client.get(f"{self.api_url}/health")
            self.stats["api_status"] = "🟢 Healthy" if resp.status_code == 200 else "🔴 Unhealthy"
            return resp.status_code == 200
        except Exception as e:
            self.stats["api_status"] = f"🔴 Error: {str(e)[:30]}"
            return False
    
    async def fetch_data(self):
        """Fetch latest data from API."""
        try:
            await self.fetch_health()
            
            # Try to get consents (if endpoint exists)
            try:
                resp = await self.client.get(f"{self.api_url}/v1/consents")
                if resp.status_code == 200:
                    data = resp.json()
                    self.consents = data if isinstance(data, list) else data.get("consents", [])
                    self.stats["total_consents"] = len(self.consents)
            except:
                pass  # Endpoint may not exist yet
            
            self.last_update = datetime.now()
            self.error = None
        except Exception as e:
            self.error = str(e)
    
    def make_header(self) -> Panel:
        """Create the header panel."""
        header_text = Text()
        header_text.append("⚡ AgentAuth Dashboard ", style="bold cyan")
        header_text.append(f"| API: {self.stats['api_status']} ", style="white")
        header_text.append(f"| Updated: {self.last_update.strftime('%H:%M:%S') if self.last_update else 'Never'}", style="dim")
        
        return Panel(
            Align.center(header_text),
            style="blue",
            height=3,
        )
    
    def make_stats(self) -> Panel:
        """Create the stats panel."""
        stats_text = Text()
        stats_text.append(f"📋 Consents: {self.stats['total_consents']}  ", style="cyan")
        stats_text.append(f"✅ Allowed: {self.stats['allowed']}  ", style="green")
        stats_text.append(f"❌ Denied: {self.stats['denied']}  ", style="red")
        stats_text.append(f"🔗 {self.api_url}", style="dim")
        
        return Panel(
            Align.center(stats_text),
            title="📊 Statistics",
            height=5,
        )
    
    def make_consents_table(self) -> Panel:
        """Create the consents table."""
        table = Table(title="Recent Consents", expand=True)
        table.add_column("ID", style="cyan", no_wrap=True, max_width=20)
        table.add_column("User", style="green")
        table.add_column("Agent", style="yellow")
        table.add_column("Max Amount", justify="right", style="magenta")
        table.add_column("Created", style="dim")
        
        if self.consents:
            for consent in self.consents[-10:]:  # Last 10
                table.add_row(
                    consent.get("id", "N/A")[:18] + "...",
                    consent.get("user_id", "N/A"),
                    consent.get("agent_id", "N/A"),
                    f"${consent.get('constraints', {}).get('max_amount', 0):.2f}",
                    consent.get("created_at", "N/A")[:19] if consent.get("created_at") else "N/A",
                )
        else:
            table.add_row("-", "No consents yet", "-", "-", "-")
        
        return Panel(table, title="📋 Live Consents", border_style="cyan")
    
    def make_activity_panel(self) -> Panel:
        """Create the activity panel."""
        if self.error:
            content = Text(f"⚠️ Error: {self.error}", style="red")
        else:
            content = Text()
            content.append("Monitoring AgentAuth activity...\n\n", style="dim")
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
        """Run the dashboard."""
        console.clear()
        
        with Live(self.make_layout(), refresh_per_second=1, console=console) as live:
            while True:
                await self.fetch_data()
                live.update(self.make_layout())
                await asyncio.sleep(REFRESH_INTERVAL)
    
    async def close(self):
        """Close the client."""
        await self.client.aclose()


async def main():
    """Main entry point."""
    dashboard = Dashboard()
    
    console.print("\n[bold cyan]⚡ AgentAuth Dashboard[/bold cyan]")
    console.print(f"[dim]Connecting to {API_URL}...[/dim]\n")
    
    try:
        await dashboard.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped.[/yellow]")
    finally:
        await dashboard.close()


if __name__ == "__main__":
    asyncio.run(main())
