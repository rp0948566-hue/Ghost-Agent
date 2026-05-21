"""Tests for BrowserExecutor — mocks Playwright."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from ghost_agent.core.executor import BrowserExecutor
from ghost_agent.utils.config import Config


def make_config(**kwargs):
    cfg = Config()
    cfg.openai_api_key = "sk-test"
    cfg.headless = True
    cfg.slow_mo = 0
    cfg.timeout = 5000
    cfg.screenshot_dir = "/tmp/ghost_test_screenshots"
    cfg.browser = "chromium"
    for k, v in kwargs.items():
        setattr(cfg, k, v)
    return cfg


@pytest.fixture
def mock_page():
    page = AsyncMock()
    page.goto = AsyncMock()
    page.locator = MagicMock(return_value=AsyncMock())
    page.get_by_text = MagicMock(return_value=AsyncMock())
    page.get_by_role = MagicMock(return_value=AsyncMock())
    page.evaluate = AsyncMock(return_value="extracted content here")
    page.keyboard = AsyncMock()
    page.screenshot = AsyncMock()
    page.go_back = AsyncMock()
    page.close = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.set_default_timeout = MagicMock()
    loc_mock = AsyncMock()
    loc_mock.count = AsyncMock(return_value=0)
    loc_mock.first = AsyncMock()
    loc_mock.first.click = AsyncMock()
    loc_mock.first.fill = AsyncMock()
    page.locator.return_value = loc_mock
    page.get_by_text.return_value = loc_mock
    page.get_by_role.return_value = loc_mock
    return page


@pytest.fixture
def executor_with_page(mock_page, tmp_path):
    cfg = make_config(screenshot_dir=str(tmp_path))
    executor = BrowserExecutor(cfg)
    executor._page = mock_page
    return executor, mock_page


@pytest.mark.asyncio
async def test_navigate_http(executor_with_page):
    executor, page = executor_with_page
    result = await executor.execute_step({
        "action": "navigate",
        "target": "https://example.com",
        "value": "",
        "description": "go to example",
    })
    page.goto.assert_called_once_with("https://example.com", wait_until="domcontentloaded")
    assert "navigated" in result


@pytest.mark.asyncio
async def test_navigate_without_scheme(executor_with_page):
    executor, page = executor_with_page
    result = await executor.execute_step({
        "action": "navigate",
        "target": "example.com",
        "value": "",
        "description": "go to example without https",
    })
    page.goto.assert_called_once_with("https://example.com", wait_until="domcontentloaded")
    assert "navigated" in result


@pytest.mark.asyncio
async def test_scroll_down(executor_with_page):
    executor, page = executor_with_page
    result = await executor.execute_step({
        "action": "scroll",
        "target": "",
        "value": "down",
        "description": "scroll down",
    })
    page.evaluate.assert_called()
    assert "scroll" in result


@pytest.mark.asyncio
async def test_scroll_up(executor_with_page):
    executor, page = executor_with_page
    result = await executor.execute_step({
        "action": "scroll",
        "target": "",
        "value": "up",
        "description": "scroll up",
    })
    assert "scroll" in result


@pytest.mark.asyncio
async def test_extract_returns_content(executor_with_page):
    executor, page = executor_with_page
    page.evaluate = AsyncMock(return_value="AI trending: LLMs, Agents, Multimodal")
    result = await executor.execute_step({
        "action": "extract",
        "target": "",
        "value": "trending topics",
        "description": "extract page content",
    })
    assert "AI trending" in result


@pytest.mark.asyncio
async def test_screenshot_saves_file(executor_with_page, tmp_path):
    executor, page = executor_with_page
    executor.config.screenshot_dir = str(tmp_path)
    result = await executor.execute_step({
        "action": "screenshot",
        "target": "",
        "value": "test_shot",
        "description": "take screenshot",
    })
    page.screenshot.assert_called_once()
    assert "screenshot" in result


@pytest.mark.asyncio
async def test_back_calls_go_back(executor_with_page):
    executor, page = executor_with_page
    result = await executor.execute_step({
        "action": "back",
        "target": "",
        "value": "",
        "description": "go back",
    })
    page.go_back.assert_called_once()
    assert "back" in result


@pytest.mark.asyncio
async def test_unknown_action_skipped(executor_with_page):
    executor, _ = executor_with_page
    result = await executor.execute_step({
        "action": "fly_to_moon",
        "target": "",
        "value": "",
        "description": "unknown",
    })
    assert "skipped" in result


@pytest.mark.asyncio
async def test_wait_ms(executor_with_page):
    executor, _ = executor_with_page
    result = await executor.execute_step({
        "action": "wait",
        "target": "",
        "value": "100",
        "description": "wait 100ms",
    })
    assert "wait" in result
