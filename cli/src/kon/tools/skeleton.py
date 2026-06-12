import asyncio
import os

from pydantic import BaseModel

from ..core.types import ToolResult
from ..index.manager import BM25Indexer
from .base import BaseTool


class SkeletonParams(BaseModel):
    pass


class SkeletonTool(BaseTool[SkeletonParams]):
    name = "get_repo_skeleton"
    params = SkeletonParams
    description = "Returns a high-level overview of the project's classes and functions. Call this first to get oriented in a new codebase."
    mutating = False
    tool_icon = "💀"

    async def execute(
        self, params: SkeletonParams, cwd: str, cancel_event: asyncio.Event | None = None
    ) -> ToolResult:
        try:
            indexer = BM25Indexer(cwd)
            # Ensure index exists
            if not indexer.corpus:
                await asyncio.to_thread(indexer.index_project)

            skeleton = indexer.get_skeleton()
            return ToolResult(
                success=True, result=skeleton, ui_summary="Retrieved project skeleton"
            )
        except Exception as e:
            return ToolResult(success=False, result=f"Error getting skeleton: {e}")

    def format_call(self, params: SkeletonParams) -> str:
        return ""
