import asyncio
from typing import Any

from pydantic import BaseModel, Field

from ..core.types import ToolResult
from ..session import current_session_id
from .base import BaseTool

# Global store indexed by session_id
_thinking_state: dict[str, dict[str, Any]] = {}


class ThinkingParams(BaseModel):
    thought: str = Field(..., description="Your current thought or reasoning step")
    thought_number: int = Field(
        ..., description="Current thought number (starts at 1, increments)"
    )
    total_thoughts: int = Field(..., description="Estimated total thoughts needed")
    next_thought_needed: bool = Field(..., description="Whether another thought step follows")
    is_revision: bool = Field(False, description="Whether this revises a previous thought")
    revises_thought: int | None = Field(None, description="Which thought number to revise")
    branch_from_thought: int | None = Field(
        None, description="Branch a new line of reasoning from this thought"
    )
    branch_id: str | None = Field(None, description="Unique ID for this reasoning branch")
    needs_more_thoughts: bool = Field(
        True, description="Whether more thoughts are still needed to reach a conclusion"
    )


class SequentialThinkingTool(BaseTool[ThinkingParams]):
    name = "sequential_thinking"
    params = ThinkingParams
    description = "A tool for dynamic, structured, and reflective problem-solving. Use this when you need to work through a complex problem step by step, revise previous reasoning, or explore branching lines of thought."
    mutating = False
    tool_icon = "💭"

    async def execute(
        self, params: ThinkingParams, cancel_event: asyncio.Event | None = None
    ) -> ToolResult:
        session_id = current_session_id.get() or "default"

        if session_id not in _thinking_state:
            _thinking_state[session_id] = {
                "thoughts": [],
                "branches": {},
                "current_branch": "main",
            }

        state = _thinking_state[session_id]
        branch = state["current_branch"]

        if params.branch_from_thought is not None and params.branch_id:
            if params.branch_id not in state["branches"]:
                state["branches"][params.branch_id] = []
            branch = params.branch_id
            state["current_branch"] = branch

        entry = {
            "number": params.thought_number,
            "content": params.thought,
            "is_revision": params.is_revision,
            "revises": params.revises_thought,
            "branch": branch,
        }

        target = state["branches"].get(branch, state["thoughts"])

        if params.is_revision and params.revises_thought is not None:
            for i, t in enumerate(target):
                if t["number"] == params.revises_thought:
                    target[i] = entry
                    break
            else:
                target.append(entry)
        else:
            target.append(entry)

        history_lines = []
        for t in state["thoughts"]:
            label = f"Thought {t['number']}"
            if t["is_revision"]:
                label += f" (revised {t['revises']})"
            history_lines.append(f"{label}: {t['content']}")

        for bid, thoughts in state["branches"].items():
            if bid == "main":
                continue
            for t in thoughts:
                history_lines.append(f"Branch[{bid}] Thought {t['number']}: {t['content']}")

        result_text = (
            f"Thought {params.thought_number}/{params.total_thoughts} recorded.\n"
            f"Next thought needed: {params.next_thought_needed}\n\n"
            f"Full chain:\n" + "\n".join(history_lines)
        )

        if not params.next_thought_needed or not params.needs_more_thoughts:
            result_text += "\n\n**Thought chain complete.**"
            # Cleanup state for this session
            _thinking_state.pop(session_id, None)

        return ToolResult(
            success=True,
            result=result_text,
            ui_summary=f"Thought {params.thought_number}/{params.total_thoughts}",
        )

    def format_call(self, params: ThinkingParams) -> str:
        return f"{params.thought_number}/{params.total_thoughts}"
