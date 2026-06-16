import pytest

from kon.session import current_session_id
from kon.tools.thinking import SequentialThinkingTool, ThinkingParams, _thinking_state


@pytest.fixture(autouse=True)
def cleanup_state():
    _thinking_state.clear()
    yield
    _thinking_state.clear()


@pytest.mark.asyncio
async def test_sequential_thinking_basic():
    tool = SequentialThinkingTool()
    current_session_id.set("session-1")

    # Thought 1
    params = ThinkingParams(
        thought="First step",
        thought_number=1,
        total_thoughts=3,
        next_thought_needed=True,
        is_revision=False,
        revises_thought=None,
        branch_from_thought=None,
        branch_id=None,
        needs_more_thoughts=True,
    )
    result = await tool.execute(params, cwd="/tmp")
    assert result.success is True
    assert result.result is not None
    assert "Thought 1/3" in result.result
    assert "First step" in result.result

    # Thought 2
    params = ThinkingParams(
        thought="Second step",
        thought_number=2,
        total_thoughts=3,
        next_thought_needed=True,
        is_revision=False,
        revises_thought=None,
        branch_from_thought=None,
        branch_id=None,
        needs_more_thoughts=True,
    )
    result = await tool.execute(params, cwd="/tmp")
    assert result.result is not None
    assert "Second step" in result.result

    # Thought 3 (Complete)
    params = ThinkingParams(
        thought="Final step",
        thought_number=3,
        total_thoughts=3,
        next_thought_needed=False,
        is_revision=False,
        revises_thought=None,
        branch_from_thought=None,
        branch_id=None,
        needs_more_thoughts=False,
    )
    result = await tool.execute(params, cwd="/tmp")
    assert result.result is not None
    assert "Final step" in result.result
    assert "Thought chain complete" in result.result
    assert "session-1" not in _thinking_state


@pytest.mark.asyncio
async def test_sequential_thinking_revision():
    tool = SequentialThinkingTool()
    current_session_id.set("session-2")

    # Original thought
    await tool.execute(
        ThinkingParams(
            thought="Original thought",
            thought_number=1,
            total_thoughts=2,
            next_thought_needed=True,
            is_revision=False,
            revises_thought=None,
            branch_from_thought=None,
            branch_id=None,
            needs_more_thoughts=True,
        ),
        cwd="/tmp",
    )

    # Revision
    params = ThinkingParams(
        thought="Revised thought",
        thought_number=1,
        total_thoughts=2,
        next_thought_needed=True,
        is_revision=True,
        revises_thought=1,
        branch_from_thought=None,
        branch_id=None,
        needs_more_thoughts=True,
    )
    result = await tool.execute(params, cwd="/tmp")
    assert result.result is not None
    assert "Revised thought" in result.result
    assert "Original thought" not in result.result
