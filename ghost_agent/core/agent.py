import asyncio
from typing import AsyncIterator
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from ghost_agent.core.planner import TaskPlanner
from ghost_agent.core.executor import BrowserExecutor
from ghost_agent.utils.config import Config
from ghost_agent.utils.logger import get_logger

logger = get_logger("ghost-agent")
console = Console()


class GhostAgent:
    """Orchestrates planning and execution of browser automation tasks."""

    def __init__(self, config: Config | None = None):
        self.config = config or Config()
        self.planner = TaskPlanner(
            model=self.config.openai_model,
            api_key=self.config.openai_api_key,
        )

    async def run(self, prompt: str) -> dict:
        console.print(Panel.fit(
            f"[bold ghost_agent]👻 Ghost-Agent[/bold ghost_agent]\n[dim]{prompt}[/dim]",
            border_style="cyan",
        ))

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
            console=console,
        ) as progress:
            task_id = progress.add_task("Thinking...", total=None)
            plan = await self.planner.plan(prompt)
            progress.update(task_id, description="Plan ready. Launching browser...")

        steps = plan.get("steps", [])
        if not steps:
            logger.warning("Planner returned no steps.")
            return {"goal": plan.get("goal"), "results": [], "success": False}

        results = []
        async with BrowserExecutor(self.config) as executor:
            for i, step in enumerate(steps[: self.config.max_steps], 1):
                desc = step.get("description", step.get("action"))
                console.print(f"[dim cyan][{i}/{len(steps)}][/dim cyan] {desc}")
                try:
                    result = await executor.execute_step(step)
                    results.append({"step": i, "action": step.get("action"), "result": result, "ok": True})
                except Exception as exc:
                    logger.error(f"Step {i} failed: {exc}")
                    results.append({"step": i, "action": step.get("action"), "result": str(exc), "ok": False})

        success = all(r["ok"] for r in results)
        console.print(Panel.fit(
            f"[bold {'green' if success else 'yellow'}]{'✅ Task complete!' if success else '⚠️  Task completed with errors'}[/bold {'green' if success else 'yellow'}]\n"
            f"[dim]{sum(r['ok'] for r in results)}/{len(results)} steps succeeded[/dim]",
            border_style="green" if success else "yellow",
        ))
        return {"goal": plan.get("goal"), "steps": steps, "results": results, "success": success}

    async def stream(self, prompt: str) -> AsyncIterator[dict]:
        """Yield step-by-step events for integrations that need streaming output."""
        plan = await self.planner.plan(prompt)
        yield {"event": "plan", "data": plan}

        steps = plan.get("steps", [])
        async with BrowserExecutor(self.config) as executor:
            for i, step in enumerate(steps[: self.config.max_steps], 1):
                try:
                    result = await executor.execute_step(step)
                    yield {"event": "step", "step": i, "action": step.get("action"), "result": result, "ok": True}
                except Exception as exc:
                    yield {"event": "step", "step": i, "action": step.get("action"), "result": str(exc), "ok": False}

        yield {"event": "done"}
