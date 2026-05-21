import asyncio
import os
from pathlib import Path
from typing import Any
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from ghost_agent.utils.logger import get_logger
from ghost_agent.utils.config import Config

logger = get_logger("executor")


class BrowserExecutor:
    def __init__(self, config: Config):
        self.config = config
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        Path(config.screenshot_dir).mkdir(parents=True, exist_ok=True)

    async def __aenter__(self):
        self._playwright = await async_playwright().start()
        launcher = getattr(self._playwright, self.config.browser)
        self._browser = await launcher.launch(
            headless=self.config.headless,
            slow_mo=self.config.slow_mo,
        )
        self._context = await self._browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        self._page = await self._context.new_page()
        self._page.set_default_timeout(self.config.timeout)
        return self

    async def __aexit__(self, *_):
        if self._page:
            await self._page.close()
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def execute_step(self, step: dict[str, Any]) -> str:
        action = step.get("action", "").lower()
        target = step.get("target", "")
        value = step.get("value", "")
        description = step.get("description", action)

        logger.info(f"  [dim]→[/dim] [yellow]{action}[/yellow]: {description}", extra={"markup": True})

        handlers = {
            "navigate": self._navigate,
            "click": self._click,
            "type": self._type,
            "scroll": self._scroll,
            "wait": self._wait,
            "screenshot": self._screenshot,
            "extract": self._extract,
            "search": self._search,
            "back": self._back,
            "close": self._close_tab,
        }

        handler = handlers.get(action)
        if not handler:
            logger.warning(f"Unknown action '{action}', skipping.")
            return f"skipped: unknown action {action}"

        return await handler(target=target, value=value)

    async def _navigate(self, target: str, **_) -> str:
        url = target if target.startswith("http") else f"https://{target}"
        await self._page.goto(url, wait_until="domcontentloaded")
        return f"navigated to {url}"

    async def _click(self, target: str, **_) -> str:
        try:
            locator = self._page.get_by_text(target, exact=False).first
            if await locator.count() > 0:
                await locator.click()
            else:
                await self._page.locator(target).first.click()
        except Exception:
            await self._page.locator(target).first.click()
        return f"clicked {target}"

    async def _type(self, target: str, value: str, **_) -> str:
        try:
            await self._page.locator(target).first.fill(value)
        except Exception:
            await self._page.get_by_role("textbox").first.fill(value)
        return f"typed '{value}' into {target}"

    async def _scroll(self, value: str, **_) -> str:
        if value == "down":
            await self._page.evaluate("window.scrollBy(0, window.innerHeight)")
        elif value == "up":
            await self._page.evaluate("window.scrollBy(0, -window.innerHeight)")
        else:
            try:
                px = int(value)
                await self._page.evaluate(f"window.scrollBy(0, {px})")
            except (ValueError, TypeError):
                await self._page.evaluate("window.scrollBy(0, 600)")
        return "scrolled"

    async def _wait(self, target: str, value: str, **_) -> str:
        if value and value.isdigit():
            await asyncio.sleep(int(value) / 1000)
            return f"waited {value}ms"
        if target:
            await self._page.wait_for_selector(target, timeout=self.config.timeout)
            return f"waited for {target}"
        await asyncio.sleep(1)
        return "waited 1s"

    async def _screenshot(self, value: str, **_) -> str:
        filename = value or "screenshot"
        if not filename.endswith(".png"):
            filename += ".png"
        path = os.path.join(self.config.screenshot_dir, filename)
        await self._page.screenshot(path=path, full_page=False)
        logger.info(f"  [dim]📸 Screenshot saved:[/dim] [blue]{path}[/blue]", extra={"markup": True})
        return f"screenshot saved to {path}"

    async def _extract(self, value: str, **_) -> str:
        text = await self._page.evaluate(
            """() => {
                const els = document.querySelectorAll(
                    'h1, h2, h3, h4, p, li, span, div[class*="trend"], '
                    + 'article, [class*="title"], [class*="headline"]'
                );
                return Array.from(els)
                    .map(e => e.innerText?.trim())
                    .filter(t => t && t.length > 5 && t.length < 500)
                    .slice(0, 50)
                    .join('\\n');
            }"""
        )
        snippet = text[:2000] if text else "(nothing extracted)"
        logger.info(f"\n[bold white]── Extracted Content ──[/bold white]\n{snippet}\n", extra={"markup": True})
        return snippet

    async def _search(self, target: str, value: str, **_) -> str:
        try:
            if target:
                box = self._page.locator(target).first
            else:
                box = self._page.get_by_role("searchbox").first
                if await box.count() == 0:
                    box = self._page.locator("input[type='search'], input[name='q'], input[name='query']").first
            await box.fill(value)
            await box.press("Enter")
        except Exception as e:
            logger.warning(f"Search fallback triggered: {e}")
            await self._page.keyboard.type(value)
            await self._page.keyboard.press("Enter")
        return f"searched for '{value}'"

    async def _back(self, **_) -> str:
        await self._page.go_back()
        return "navigated back"

    async def _close_tab(self, **_) -> str:
        await self._page.close()
        return "tab closed"
