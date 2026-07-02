"""SP3CT3R CLI — 🖥  IP INTEL Command"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from rich.console import Console
from rich.panel import Panel
from cli.utils.streamer import check_engine, start_scan_api, stream_scan

console = Console()


def run(target: str, output: str = "terminal", *args):
    asyncio.run(_run_async(target, output))


async def _run_async(target: str, output: str):
    console.print()
    console.print(Panel(
        f"[bold cyan]TARGET[/] : [bold white]{target}[/]\n"
        f"[bold cyan]MODULE[/] : [bold white]🖥  IP INTEL[/]",
        border_style="cyan", padding=(0, 2)
    ))
    console.print()

    # Check engine
    console.print("[dim]Connecting to SP3CT3R engine...[/]")
    if not await check_engine():
        console.print("[bold red]❌ SP3CT3R engine not running.[/] Start with:\n  [cyan]python backend/run.py[/]")
        return
    console.print("[bold green]✅ Engine connected[/]\n")

    # Start scan
    try:
        data = await start_scan_api(target, "ip")
    except Exception as e:
        console.print(f"[bold red]❌ Failed to start scan: {e}[/]")
        return

    scan_id = data["scan_id"]
    console.print(f"[dim]Scan ID :[/] [cyan]{scan_id}[/]")
    console.print()

    # Stream results live
    await stream_scan(scan_id, target, "ip", output)
