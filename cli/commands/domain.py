"""CLI domain command"""
import asyncio, sys
sys.path.insert(0, ".")

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich import box

console = Console()


def run(target: str, output: str = "terminal", threads: int = 10):
    """Entry point called by CLI."""
    console.print(Panel(f"[bold cyan]TARGET:[/] {target}  |  [bold cyan]MODULE:[/] DOMAIN OSINT", style="cyan"))
    asyncio.run(_run_async(target, output))


async def _run_async(target: str, output: str):
    import httpx
    console.print(f"\n[dim]Connecting to SP3CT3R engine...[/]")
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get("http://localhost:8000/health")
            if resp.status_code != 200:
                raise Exception("Engine not running")
    except Exception:
        console.print("[red]❌ SP3CT3R engine not running. Start it with: python backend/run.py[/]")
        return

    console.print("[green]✅ Engine connected[/]\n")
    # Start scan via API
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post("http://localhost:8000/api/v1/scans/start",
            json={"target": target, "module": "domain", "options": {}})
        if resp.status_code == 200:
            data = resp.json()
            console.print(f"[cyan]Scan ID:[/] {data['scan_id']}")
            console.print(f"[dim]WebSocket:[/] ws://localhost:8000{data['websocket_url']}")
            console.print("\n[yellow]Connect to WebSocket or poll /api/v1/scans/{scan_id} for results[/]")