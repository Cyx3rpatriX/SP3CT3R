# CLI formatter
"""SP3CT3R CLI Rich formatting helpers"""
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

STATUS_COLORS = {
    "found": "green", "not_found": "dim", "partial": "yellow",
    "exposed": "bold red", "live": "green",
}
RISK_COLORS = {
    "critical": "bold red", "high": "red", "medium": "yellow",
    "low": "cyan", "info": "dim white",
}


def results_table(results: list, title: str = "Results") -> Table:
    table = Table(title=title, box=box.SIMPLE_HEAVY, border_style="cyan",
                  header_style="bold cyan", show_lines=False)
    table.add_column("Category", style="dim", width=12)
    table.add_column("Platform", style="white", width=20)
    table.add_column("Data", style="white", ratio=1)
    table.add_column("Status", width=10)
    table.add_column("Risk", width=8)

    for r in results:
        status = r.get("status", "")
        risk = r.get("risk_level", "info")
        table.add_row(
            r.get("category", ""),
            r.get("platform", ""),
            r.get("data", "")[:80],
            f"[{STATUS_COLORS.get(status, 'white')}]{status}[/]",
            f"[{RISK_COLORS.get(risk, 'white')}]{risk}[/]",
        )
    return table


def log_line(level: str, message: str):
    colors = {"INFO": "cyan", "OK": "green", "WARN": "yellow", "ERROR": "red", "DATA": "magenta"}
    color = colors.get(level, "white")
    console.print(f"[dim]{__import__('datetime').datetime.now().strftime('%H:%M:%S')}[/] [{color}][{level}][/] {message}")

