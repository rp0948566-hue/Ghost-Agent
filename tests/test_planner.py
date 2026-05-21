"""Tests for TaskPlanner — mocks the OpenAI client."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from ghost_agent.core.planner import TaskPlanner


MOCK_PLAN = {
    "goal": "Find trending topics on X",
    "steps": [
        {"action": "navigate", "target": "https://x.com/explore", "value": "", "description": "Go to X explore page"},
        {"action": "extract", "target": "", "value": "trending topics", "description": "Extract trending topics"},
        {"action": "screenshot", "target": "", "value": "x_trending", "description": "Screenshot result"},
    ],
}


def _make_mock_response(plan: dict):
    choice = MagicMock()
    choice.message.content = json.dumps(plan)
    response = MagicMock()
    response.choices = [choice]
    return response


@pytest.fixture
def planner():
    return TaskPlanner(model="gpt-4o", api_key="sk-test-key")


@pytest.mark.asyncio
async def test_plan_returns_dict(planner):
    mock_response = _make_mock_response(MOCK_PLAN)
    with patch.object(planner.client.chat.completions, "create", new=AsyncMock(return_value=mock_response)):
        result = await planner.plan("Find trending topics on X.com")
    assert isinstance(result, dict)
    assert "goal" in result
    assert "steps" in result


@pytest.mark.asyncio
async def test_plan_has_steps(planner):
    mock_response = _make_mock_response(MOCK_PLAN)
    with patch.object(planner.client.chat.completions, "create", new=AsyncMock(return_value=mock_response)):
        result = await planner.plan("Find trending topics on X.com")
    assert len(result["steps"]) == 3


@pytest.mark.asyncio
async def test_plan_step_schema(planner):
    mock_response = _make_mock_response(MOCK_PLAN)
    with patch.object(planner.client.chat.completions, "create", new=AsyncMock(return_value=mock_response)):
        result = await planner.plan("Find trending topics on X.com")
    for step in result["steps"]:
        assert "action" in step
        assert "description" in step


@pytest.mark.asyncio
async def test_plan_goal_matches(planner):
    mock_response = _make_mock_response(MOCK_PLAN)
    with patch.object(planner.client.chat.completions, "create", new=AsyncMock(return_value=mock_response)):
        result = await planner.plan("anything")
    assert result["goal"] == "Find trending topics on X"


@pytest.mark.asyncio
async def test_plan_uses_correct_model(planner):
    mock_response = _make_mock_response(MOCK_PLAN)
    mock_create = AsyncMock(return_value=mock_response)
    with patch.object(planner.client.chat.completions, "create", new=mock_create):
        await planner.plan("test prompt")
    call_kwargs = mock_create.call_args.kwargs
    assert call_kwargs["model"] == "gpt-4o"


@pytest.mark.asyncio
async def test_plan_sends_user_prompt(planner):
    mock_response = _make_mock_response(MOCK_PLAN)
    mock_create = AsyncMock(return_value=mock_response)
    with patch.object(planner.client.chat.completions, "create", new=mock_create):
        await planner.plan("custom user prompt here")
    messages = mock_create.call_args.kwargs["messages"]
    user_messages = [m for m in messages if m["role"] == "user"]
    assert any("custom user prompt here" in m["content"] for m in user_messages)
