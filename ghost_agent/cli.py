import asyncio
import json
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax

from ghost_agent.core.agent import GhostAgent
from ghost_agent.utils.config import Config
from ghost_agent.utils.logger import get_logger

app = typer.Typer(
    name="ghost",
    help="👻 Ghost-Agent — AI-powered browser automation in plain English.",
    rich_markup_mode="rich",
    add_completion=False,
)
console = Console()
logger = get_logger("cli")

BANNER = r"""
  ____  _              _            _                   _
 / ___|| |__   ___  ___| |_      /\ | | ____ _  __ _  __| |_
| |  _ | '_ \ / _ \/ __| __|    /  \| |/ / _` |/ _` |/ _` (_)
| |_| || | | | (_) \__ \ |_    / /\ \   < (_| | (_| | (_| |_
 \____||_| |_|\___/|___/\__|  /_/  \_\_|\_\__,_|\__, |\__,_(_)
                                                 |___/
          Your AI Browser Co-pilot 👻
"""

def _get_config(
    headless: bool,
    browser: str,
    model: str,
    slow_mo: int,
) -> Config:
    cfg = Config()
    cfg.headless = headless
    cfg.browser = browser
    cfg.openai_model = model
    cfg.slow_mo = slow_mo
    cfg.validate()
    return cfg


@app.command("run")
def run_command(
    prompt: str = typer.Argument(..., help="Natural language task for Ghost-Agent to perform."),
    headless: bool = typer.Option(True, "--headless/--no-headless", help="Run browser in headless mode."),
    browser: str = typer.Option("chromium", "--browser", "-b", help="Browser engine: chromium | firefox | webkit"),
    model: str = typer.Option("gpt-4o", "--model", "-m", help="OpenAI model to use for planning."),
    slow_mo: int = typer.Option(0, "--slow-mo", help="Slow down actions by N ms (useful for demos)."),
    output_json: bool = typer.Option(False, "--json", help="Output results as JSON."),
    screenshot: bool = typer.Option(False, "--screenshot", "-s", help="Take a screenshot after task completion."),
):
    """
    Run a browser automation task from a natural language prompt.

    Examples:

      ghost run "Go to Hacker News and find the top AI stories"

      ghost run "Search GitHub for trending Python repos" --no-headless

      ghost run "Go to x.com and list trending topics" --slow-mo 500 --screenshot
    """
    console.print(BANNER, style="bold cyan")

    try:
        cfg = _get_config(headless, browser, model, slow_mo)
    except ValueError as e:
        console.print(f"[bold red]Configuration error:[/bold red] {e}")
        raise typer.Exit(1)

    if screenshot:
        final_prompt = prompt + ". Take a screenshot at the end."
    else:
        final_prompt = prompt

    try:
        result = asyncio.run(_run_agent(final_prompt, cfg))
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user.[/yellow]")
        raise typer.Exit(0)
    except Exception as e:
        console.print(f"[bold red]Fatal error:[/bold red] {e}")
        logger.exception("Unhandled error during run")
        raise typer.Exit(1)

    if output_json:
        syntax = Syntax(json.dumps(result, indent=2), "json", theme="monokai")
        console.print(syntax)

    raise typer.Exit(0 if result.get("success") else 1)


async def _run_agent(prompt: str, config: Config) -> dict:
    agent = GhostAgent(config)
    return await agent.run(prompt)


@app.command("tasks")
def list_tasks():
    """List all registered built-in task templates."""
    from ghost_agent.tasks.registry import TaskRegistry
    tasks = TaskRegistry.list_tasks()
    if not tasks:
        console.print("[dim]No built-in tasks registered.[/dim]")
        return
    table = Table(title="Built-in Tasks", border_style="cyan")
    table.add_column("Name", style="bold yellow")
    table.add_column("Description")
    for name, desc in tasks.items():
        table.add_row(name, desc or "—")
    console.print(table)


@app.command("version")
def version_command():
    """Show Ghost-Agent version."""
    from ghost_agent import __version__
    console.print(f"[bold cyan]Ghost-Agent[/bold cyan] v{__version__}")


@app.command("interactive")
def interactive_mode(
    headless: bool = typer.Option(True, "--headless/--no-headless"),
    browser: str = typer.Option("chromium", "--browser", "-b"),
    model: str = typer.Option("gpt-4o", "--model", "-m"),
    slow_mo: int = typer.Option(0, "--slow-mo"),
):
    """
    Start an interactive Ghost-Agent session. Type prompts and run tasks one-by-one.
    Type 'exit' or 'quit' to stop.
    """
    console.print(BANNER, style="bold cyan")
    console.print("[bold green]Interactive mode[/bold green] — type your task and press Enter. ('exit' to quit)\n")

    try:
        cfg = _get_config(headless, browser, model, slow_mo)
    except ValueError as e:
        console.print(f"[bold red]Configuration error:[/bold red] {e}")
        raise typer.Exit(1)

    while True:
        try:
            prompt = console.input("[bold cyan]ghost>[/bold cyan] ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not prompt:
            continue
        if prompt.lower() in ("exit", "quit", "q"):
            console.print("[dim]Goodbye! 👻[/dim]")
            break

        try:
            asyncio.run(_run_agent(prompt, cfg))
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")


def main():
    app()


if __name__ == "__main__":
    main()
