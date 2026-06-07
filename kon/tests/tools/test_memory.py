import json

import pytest

from kon.tools.memory import (
    ForgetParams,
    ForgetTool,
    MemorizeParams,
    MemorizeTool,
    RecallParams,
    RecallTool,
)


@pytest.fixture
def mock_memory_path(tmp_path):
    path = tmp_path / "memory.json"
    from unittest.mock import patch

    with patch("kon.tools.memory.MEMORY_PATH", path):
        yield path


@pytest.mark.asyncio
async def test_memorize_and_recall(mock_memory_path):
    memo_tool = MemorizeTool()

    # Test Memorize
    params = MemorizeParams(key="color", value="blue", tags="ui,theme")
    result = await memo_tool.execute(params)
    assert result.success is True
    assert result.result is not None
    assert "Memorized: color" in result.result

    # Verify file content
    with open(mock_memory_path) as f:
        data = json.load(f)
        assert data["color"]["value"] == "blue"
        assert "ui" in data["color"]["tags"]

    # Test Recall
    recall_tool = RecallTool()
    recall_params = RecallParams(query="color")
    result = await recall_tool.execute(recall_params)
    assert result.success is True
    assert result.result is not None
    assert "blue" in result.result

    # Test Recall Miss
    recall_params = RecallParams(query="something_else")
    result = await recall_tool.execute(recall_params)
    assert result.result is not None
    assert "No matching memories" in result.result


@pytest.mark.asyncio
async def test_forget(mock_memory_path):
    memo_tool = MemorizeTool()
    forget_tool = ForgetTool()

    # Memorize
    await memo_tool.execute(MemorizeParams(key="temp", value="data", tags=None))

    # Forget
    result = await forget_tool.execute(ForgetParams(key="temp"))
    assert result.success is True

    # Verify gone
    with open(mock_memory_path) as f:
        data = json.load(f)
        assert "temp" not in data

    # Forget non-existent
    result = await forget_tool.execute(ForgetParams(key="temp"))
    assert result.success is False
