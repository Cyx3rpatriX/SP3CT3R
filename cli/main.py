# ── CLI ────────────────────────────────────
"""
SP3CT3R CLI — Command Line Interface
Usage: python cli/main.py [command] [target] [options]
"""
import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

BANNER = """
[bold cyan]        ███████╗██████╗ ██████╗  ██████╗████████╗██████╗ ██████╗[/]
[bold cyan]        ██╔════╝██╔══██╗╚════██╗██╔════╝╚══██╔══╝╚════██╗██╔══██╗[/]
[bold cyan]        ███████╗██████╔╝ █████╔╝██║        ██║    █████╔╝██████╔╝[/]
[dim cyan]        ╚════██║██╔═══╝  ╚═══██╗██║        ██║    ╚═══██╗██╔══██╗[/]
[bold cyan]        ███████║██║     ██████╔╝╚██████╗   ██║   ██████╔╝██║  ██║[/]
[dim cyan]        ╚══════╝╚═╝     ╚═════╝  ╚═════╝   ╚═╝   ╚═════╝ ╚═╝  ╚═╝[/]  [dim]v1.1.0[/]
[bold white]S.P.3.C.T.3.R. — Smart Profiling & Evidence Collection Tool for Enhanced Reconnaissance[/]
"""


@click.group()
@click.version_option("1.0.0", prog_name="sp3ct3r")
def cli():
    """S.P.E.C.T.E.R → Smart Profiling & Evidence Collection Tool for Enhanced Reconnaissance"""
    console.print(BANNER)


@cli.command()
@click.argument("target")
@click.option("--output", "-o", default="terminal", type=click.Choice(["terminal","json","csv","pdf"]))
@click.option("--threads", "-t", default=10, help="Concurrent threads")
def domain(target, output, threads):
    """Run domain OSINT scan."""
    from commands.domain import run
    run(target, output, threads)


@cli.command()
@click.argument("target")
@click.option("--output", "-o", default="terminal")
def email(target, output):
    """Run email OSINT scan."""
    from commands.email import run
    run(target, output)


@cli.command()
@click.argument("target")
@click.option("--output", "-o", default="terminal")
@click.option("--platforms", "-p", default="all", help="Comma-separated platforms or 'all'")
def username(target, output, platforms):
    """Run username search across platforms."""
    from commands.username import run
    run(target, output, platforms)


@cli.command()
@click.argument("target")
@click.option("--output", "-o", default="terminal")
def phone(target, output):
    """Run phone number OSINT."""
    from commands.phone import run
    run(target, output)


@cli.command()
@click.argument("target")
@click.option("--output", "-o", default="terminal")
@click.option("--ports", "-p", default="common", help="Port list: common|all|<port1,port2>")
def ip(target, output, ports):
    """Run IP intelligence scan."""
    from commands.ip import run
    run(target, output, ports)


@cli.command()
@click.argument("target")
@click.option("--output", "-o", default="terminal",                                         type=click.Choice(["terminal", "json", "csv"]))
def dark(target, output):
    """Dark Web Intel — breach databases, paste monitoring, threat feeds"""
    from commands.dark import run
    run(target, output)


@cli.command()
def gui():
    """Launch the GUI (opens browser)."""
    import webbrowser, subprocess, sys
    console.print("[cyan]Starting SP3CT3R GUI...[/]")
    subprocess.Popen([sys.executable, "backend/run.py"])
    webbrowser.open("http://localhost:5173")


if __name__ == "__main__":
    cli()
