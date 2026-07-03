"""
SP3CT3R CLI — Dark Web Intelligence Command
Streams breach, paste, and threat intel findings live to the terminal
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from cli.utils.streamer import check_engine, start_scan_api, stream_scan

console = Console()

SEVERITY_STYLES = {
    "critical": ("bold red",     "🔴"),
    "high":     ("red",          "🟠"),
    "medium":   ("bold yellow",  "🟡"),
    "low":      ("cyan",         "🔵"),
    "info":     ("dim",          "⚪"),
}


def run(target: str, output: str = "terminal", *args):
    asyncio.run(_run_async(target, output))


async def _run_async(target: str, output: str):
    console.print()
    console.print(Panel(
        f"[bold magenta]TARGET[/]  : [bold white]{target}[/]\n"
        f"[bold magenta]MODULE[/]  : [bold white]🕶  DARK WEB INTELLIGENCE[/]\n"
        f"[dim]Sources[/] : HIBP · psbdmp.ws · URLhaus · ThreatFox · VirusTotal · DeHashed",
        border_style="magenta", padding=(0, 2),
        title="[bold magenta]◈ DARK WEB MONITOR[/]",
    ))
    console.print()

    # ── Check Tor status ─────────────────────────────────────
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get("http://localhost:8000/api/v1/darkweb/tor-status")
            tor = r.json()
            if tor.get("tor_available"):
                console.print(f"[bold green]🧅 Tor: ACTIVE[/] — anonymized routing enabled")
            else:
                console.print(f"[yellow]🧅 Tor: OFFLINE[/] — scan proceeds on clearnet")
                console.print(f"  [dim]To enable: sudo apt install tor && sudo service tor start[/]")
    except Exception:
        console.print("[dim]Could not check Tor status[/]")

    console.print()

    # ── Check engine ─────────────────────────────────────────
    console.print("[dim]Connecting to SP3CT3R engine...[/]")
    if not await check_engine():
        console.print("[bold red]❌ SP3CT3R engine not running.[/] Start with:\n  [cyan]python backend/run.py[/]")
        return
    console.print("[bold green]✅ Engine connected[/]\n")

    # ── Start scan ───────────────────────────────────────────
    try:
        data = await start_scan_api(target, "darkweb")
    except Exception as e:
        console.print(f"[bold red]❌ Failed to start scan: {e}[/]")
        return

    scan_id = data["scan_id"]
    console.print(f"[dim]Scan ID :[/] [magenta]{scan_id}[/]")
    console.print()
    console.print(Rule(style="magenta"))

    # ── Stream live results ──────────────────────────────────
    await stream_scan(scan_id, target, "darkweb", output)



