"""
SP3CT3R CLI — Shared WebSocket Streamer
All CLI modules use this to stream live results to the terminal
"""
import asyncio
import json
import time
import httpx
import websockets
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.rule import Rule
from rich import box

console = Console()

STATUS_COLORS = {
    "found": "bold green", "live": "bold green",
    "exposed": "bold red", "partial": "bold yellow",
    "not_found": "dim", "offline": "dim", "masked": "yellow",
}
RISK_COLORS = {
    "critical": "bold red", "high": "red",
    "medium": "yellow", "low": "cyan", "info": "dim white",
}
LOG_COLORS = {
    "INFO": "cyan", "OK": "green",
    "WARN": "yellow", "ERROR": "bold red", "DATA": "magenta",
}


async def check_engine() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get("http://localhost:8000/health")
            return r.status_code == 200
    except Exception:
        return False


async def start_scan_api(target: str, module: str, options: dict = {}) -> dict:
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(
            "http://localhost:8000/api/v1/scans/start",
            json={"target": target, "module": module, "options": options}
        )
        r.raise_for_status()
        return r.json()


async def stream_scan(scan_id: str, target: str, module: str, output: str):
    """
    Connect to WS, print live logs + results as they stream in,
    then print final summary table on completion.
    """
    results  = []
    start_ts = time.time()
    ws_url   = f"ws://localhost:8000/ws/{scan_id}"

    try:
        async with websockets.connect(ws_url, ping_interval=20, open_timeout=10) as ws:
            await ws.send(json.dumps({"type": "subscribe", "scan_id": scan_id}))
            console.print(f"  [cyan]◈[/] Streaming [bold]{module.upper()}[/] results for [bold]{target}[/]...\n")

            async for raw in ws:
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                mtype = msg.get("type")
                mdata = msg.get("data", {})

                if mtype == "log":
                    _print_log(mdata, time.time() - start_ts)

                elif mtype == "result":
                    results.append(mdata)
                    _print_result_inline(mdata)

                elif mtype == "progress":
                    _print_progress(mdata)

                elif mtype == "complete":
                    console.print()
                    _print_summary_table(results, target, module, time.time() - start_ts, output)
                    break

                elif mtype == "error":
                    console.print(f"\n[bold red]❌ {mdata.get('message', 'Scan error')}[/]")
                    break

    except (websockets.exceptions.ConnectionClosed, OSError):
        console.print("\n[yellow]⚠ Connection closed — polling for final results...[/]")
        await _poll_fallback(scan_id, target, module, time.time() - start_ts, output)
    except Exception as e:
        console.print(f"\n[bold red]WebSocket error: {e}[/]")


def _print_log(mdata: dict, elapsed: float):
    level   = mdata.get("level", "INFO")
    message = mdata.get("message", "")
    color   = LOG_COLORS.get(level, "white")
    ts      = f"{int(elapsed):>3d}s"
    console.print(f"  [dim]{ts}[/]  [{color}][{level:5}][/{color}]  {message}")


def _print_result_inline(r: dict):
    cat      = (r.get("category") or "")[:10]
    platform = (r.get("platform") or "")[:28]
    data_val = str(r.get("data") or "")[:60]
    status   = r.get("status", "found")
    scol     = STATUS_COLORS.get(status, "white")
    console.print(
        f"  [dim cyan]{cat:10}[/]  [white]{platform:28}[/]  "
        f"[dim]{data_val}[/]  [{scol}]{status.upper()}[/{scol}]"
    )


def _print_progress(mdata: dict):
    progress = mdata.get("progress", 0)
    found    = mdata.get("found", 0)
    total    = mdata.get("total", 0)
    bars     = int(progress / 5)
    bar      = "█" * bars + "░" * (20 - bars)
    # Overwrite the same line
    console.print(
        f"\r  [cyan]{bar}[/] [bold white]{progress:5.1f}%[/]  "
        f"[green]{found}[/]/[dim]{total}[/]",
        end="", highlight=False
    )


def _print_summary_table(results, target, module, elapsed, output):
    console.print(Rule("[bold cyan]SCAN COMPLETE[/]", style="cyan"))
    console.print()

    found_c   = sum(1 for r in results if r.get("status") in ("found", "live"))
    exposed_c = sum(1 for r in results if r.get("status") == "exposed")
    high_c    = sum(1 for r in results if r.get("risk_level") in ("high", "critical"))
    mins, secs = divmod(int(elapsed), 60)

    console.print(Panel(
        f"  [cyan]Target  [/]: [bold white]{target}[/]\n"
        f"  [cyan]Module  [/]: [bold white]{module.upper()}[/]\n"
        f"  [cyan]Total   [/]: [bold white]{len(results)}[/] findings\n"
        f"  [cyan]Found   [/]: [green]{found_c}[/]  "
        f"[cyan]Exposed[/]: [red]{exposed_c}[/]  "
        f"[cyan]High Risk[/]: [yellow]{high_c}[/]\n"
        f"  [cyan]Elapsed [/]: {mins:02d}m {secs:02d}s",
        title="[bold cyan]◈ Intelligence Summary[/]",
        border_style="cyan",
        padding=(0, 2),
    ))
    console.print()

    if not results:
        console.print("[dim]  No findings.[/]")
        return

    # Group by category
    cats = {}
    for r in results:
        cats.setdefault(r.get("category", "general"), []).append(r)

    for cat, items in cats.items():
        t = Table(
            title=f"[bold cyan]{cat.upper().replace('_',' ')}[/]",
            box=box.SIMPLE_HEAVY, border_style="cyan",
            header_style="bold cyan", show_lines=False, expand=True,
        )
        t.add_column("Platform",  style="white",     min_width=22)
        t.add_column("Data",      style="dim white", ratio=1)
        t.add_column("Status",    width=12)
        t.add_column("Risk",      width=10)

        for r in items:
            s = r.get("status", "found")
            k = r.get("risk_level", "info")
            t.add_row(
                str(r.get("platform", ""))[:30],
                str(r.get("data", ""))[:80],
                f"[{STATUS_COLORS.get(s,'white')}]{s.upper()}[/]",
                f"[{RISK_COLORS.get(k,'dim white')}]{k}[/]",
            )
        console.print(t)
        console.print()

    # Export
    if output in ("json", "csv"):
        _export_results(results, target, output)


def _export_results(results, target, fmt):
    import os
    from datetime import datetime
    os.makedirs("reports/output", exist_ok=True)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"reports/output/sp3ct3r_{target.replace('.','_')}_{ts}.{fmt}"

    if fmt == "json":
        import json as _json
        with open(name, "w") as f:
            _json.dump({"target": target, "results": results}, f, indent=2)
    elif fmt == "csv":
        import csv
        with open(name, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["category","platform","data","status","risk_level"])
            w.writeheader()
            for r in results:
                w.writerow({k: r.get(k,"") for k in ["category","platform","data","status","risk_level"]})

    console.print(f"\n[green]✅ Exported:[/] [cyan]{name}[/]")


async def _poll_fallback(scan_id, target, module, elapsed, output):
    """Fallback polling if WS drops before completion."""
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            for _ in range(60):
                r = await c.get(f"http://localhost:8000/api/v1/scans/{scan_id}")
                d = r.json()
                if d.get("status") in ("completed", "failed"):
                    console.print(f"[cyan]Final status:[/] {d['status']} | Found: [green]{d.get('total_found',0)}[/]")
                    break
                await asyncio.sleep(2)
    except Exception as e:
        console.print(f"[red]Polling failed: {e}[/]")
