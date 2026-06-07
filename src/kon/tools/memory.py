import asyncio
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from ..core.types import ToolResult
from .base import BaseTool

MEMORY_PATH = Path.home() / ".rta" / "memory.json"


class MemorizeParams(BaseModel):
    key: str = Field(..., description="Unique key for this memory")
    value: str = Field(..., description="The content to remember")
    tags: str | None = Field(None, description="Comma-separated tags for retrieval")


class RecallParams(BaseModel):
    query: str = Field(..., description="Search term to find matching memories")


class ForgetParams(BaseModel):
    key: str = Field(..., description="Key of the memory to delete")


def _load() -> dict[str, Any]:
    if not MEMORY_PATH.exists():
        return {}
    try:
        with open(MEMORY_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict):
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MEMORY_PATH, "w") as f:
        json.dump(data, f, indent=2)


class MemorizeTool(BaseTool[MemorizeParams]):
    name = "memorize"
    params = MemorizeParams
    description = (
        "Store a fact persistently. Use for user preferences, project decisions, "
        "or any info you want to recall later."
    )
    mutating = True
    tool_icon = "🧠"

    async def execute(
        self, params: MemorizeParams, cancel_event: asyncio.Event | None = None
    ) -> ToolResult:
        data = _load()
        data[params.key] = {
            "value": params.value,
            "tags": params.tags.split(",") if params.tags else [],
        }
        _save(data)
        return ToolResult(
            success=True, result=f"Memorized: {params.key}", ui_summary=f"Memorized {params.key}"
        )

    def format_call(self, params: MemorizeParams) -> str:
        return f"{params.key}"


class RecallTool(BaseTool[RecallParams]):
    name = "recall"
    params = RecallParams
    description = (
        "Search stored memories by keyword. Only call this when you need "
        "to remember something from earlier."
    )
    mutating = False
    tool_icon = "🔍"

    async def execute(
        self, params: RecallParams, cancel_event: asyncio.Event | None = None
    ) -> ToolResult:
        data = _load()
        if not data:
            return ToolResult(success=True, result="No memories stored.")

        q = params.query.lower()
        matches = []
        for key, entry in data.items():
            if q in key.lower() or q in entry["value"].lower():
                matches.append((key, entry["value"]))
                continue
            for tag in entry.get("tags", []):
                if q in tag.lower():
                    matches.append((key, entry["value"]))
                    break

        if not matches:
            return ToolResult(success=True, result="No matching memories found.")

        result_text = "\n".join(f"- **{k}**: {v}" for k, v in matches[:10])
        return ToolResult(
            success=True, result=result_text, ui_summary=f"Found {len(matches)} matches"
        )

    def format_call(self, params: RecallParams) -> str:
        return f"'{params.query}'"


class ForgetTool(BaseTool[ForgetParams]):
    name = "forget"
    params = ForgetParams
    description = "Delete a specific memory by key."
    mutating = True
    tool_icon = "🗑️"

    async def execute(
        self, params: ForgetParams, cancel_event: asyncio.Event | None = None
    ) -> ToolResult:
        data = _load()
        if params.key in data:
            del data[params.key]
            _save(data)
            return ToolResult(
                success=True, result=f"Forgot: {params.key}", ui_summary=f"Forgot {params.key}"
            )
        return ToolResult(success=False, result=f"Key '{params.key}' not found.")

    def format_call(self, params: ForgetParams) -> str:
        return f"{params.key}"
