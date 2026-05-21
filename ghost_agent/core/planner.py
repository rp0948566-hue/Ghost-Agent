import json
from typing import Any
from openai import AsyncOpenAI
from ghost_agent.utils.logger import get_logger

logger = get_logger("planner")

SYSTEM_PROMPT = """You are Ghost-Agent's task planner. Given a natural language user request,
decompose it into a structured list of browser automation steps.

Output ONLY valid JSON in this exact format:
{
  "goal": "<short description of the overall goal>",
  "steps": [
    {
      "action": "<one of: navigate, click, type, scroll, wait, screenshot, extract, search, back, close>",
      "target": "<CSS selector, URL, or descriptive target>",
      "value": "<optional: text to type, scroll amount, wait ms, or extraction query>",
      "description": "<human-readable description of this step>"
    }
  ]
}

Action glossary:
- navigate: Go to a URL (target = URL)
- click: Click an element (target = selector or description)
- type: Type text (target = input selector, value = text)
- scroll: Scroll the page (value = "down" | "up" | number of pixels)
- wait: Wait for element or milliseconds (target = selector or value = ms)
- screenshot: Take a screenshot (value = optional filename)
- extract: Extract visible text/data from page (value = what to look for)
- search: Type into a search box and submit (target = search box, value = query)
- back: Navigate browser back
- close: Close current tab

Keep steps atomic. Do not skip steps. If a URL isn't known, use an appropriate search engine.
"""

class TaskPlanner:
    def __init__(self, model: str, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def plan(self, user_prompt: str) -> dict[str, Any]:
        logger.info(f"Planning task: [bold cyan]{user_prompt}[/bold cyan]", extra={"markup": True})
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        raw = response.choices[0].message.content
        plan = json.loads(raw)
        logger.info(f"Plan generated: [bold green]{plan.get('goal')}[/bold green] — {len(plan.get('steps', []))} steps", extra={"markup": True})
        return plan
