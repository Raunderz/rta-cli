from __future__ import annotations
import asyncio
from abc import ABC, abstractmethod
from typing import Type, Optional, Any, Dict
from pydantic import BaseModel
from .types import ToolResult


class BaseTool(ABC):
    name: str
    description: str
    parameters: Type[BaseModel]
    icon: str = "🔧"
    mutating: bool = True
    prompt_guidelines: tuple[str, ...] = ()

    @abstractmethod
    async def execute(
        self, params: Any, cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        """Execute the tool logic asynchronously."""
        pass

    def get_schema(self) -> Dict[str, Any]:
        """Return the OpenAI-compatible function schema."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters.model_json_schema(),
        }

    def format_call(self, params: Any) -> str:
        """Optional: Format the tool call for UI display."""
        return f"{self.name}({params})"

    def format_preview(self, params: Any) -> str | None:
        """Optional: Format a preview of what the tool will do (for approval UI)."""
        return None
