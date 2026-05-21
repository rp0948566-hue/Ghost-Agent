"""Tests for Ghost-Agent CLI."""
import pytest
from typer.testing import CliRunner
from unittest.mock import AsyncMock, patch
from ghost_agent.cli import app

runner = CliRunner()

MOCK_RESULT = {
    "goal": "Test goal",
    "steps": [{"action": "navigate", "target": "https://example.com", "value": "", "description": "test"}],
    "results": [{"step": 1, "action": "navigate", "result": "navigated", "ok": True}],
    "success": True,
}


def test_version_command():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "Ghost-Agent" in result.output


def test_run_missing_prompt():
    result = runner.invoke(app, ["run"])
    assert result.exit_code != 0


def test_run_no_api_key():
    with patch.dict("os.environ", {}, clear=True):
        result = runner.invoke(app, ["run", "test task"])
    assert result.exit_code != 0


def test_run_success():
    with patch("ghost_agent.cli._run_agent", new=AsyncMock(return_value=MOCK_RESULT)):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
            result = runner.invoke(app, ["run", "Go to example.com"])
    assert result.exit_code == 0


def test_run_with_json_output():
    with patch("ghost_agent.cli._run_agent", new=AsyncMock(return_value=MOCK_RESULT)):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
            result = runner.invoke(app, ["run", "Go to example.com", "--json"])
    assert result.exit_code == 0
    assert "goal" in result.output


def test_run_failure_exit_code():
    failed_result = {**MOCK_RESULT, "success": False}
    with patch("ghost_agent.cli._run_agent", new=AsyncMock(return_value=failed_result)):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
            result = runner.invoke(app, ["run", "Go to example.com"])
    assert result.exit_code == 1


def test_tasks_command():
    result = runner.invoke(app, ["tasks"])
    assert result.exit_code == 0
