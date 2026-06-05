import asyncio
import os
from pydantic import BaseModel, Field

from ..core.types import ToolResult
from .base import BaseTool
from ..index.manager import BM25Indexer

class SemanticSearchParams(BaseModel):
    query: str = Field(..., description="The natural language query (e.g., 'how is authentication handled?')")
    limit: int = Field(5, description="Number of results to return (default 5)")

class SemanticSearchTool(BaseTool[SemanticSearchParams]):
    name = "semantic_search"
    params = SemanticSearchParams
    description = "Searches the codebase for relevant snippets using natural language semantic search. Useful when you don't know where a specific logic is located."
    mutating = False
    tool_icon = "🔎"

    async def execute(self, params: SemanticSearchParams, cancel_event: asyncio.Event | None = None) -> ToolResult:
        cwd = os.getcwd()
        try:
            indexer = BM25Indexer(cwd)
            # Background indexing/update
            await asyncio.to_thread(indexer.index_project)

            results = indexer.search(params.query, limit=params.limit)

            if not results:
                return ToolResult(success=True, result="No relevant code found for query.")

            formatted = []
            for res in results:
                formatted.append(
                    f"--- {res['file_path']} (lines {res['start_line']}-{res['end_line']}) ---\n"
                    f"{res['text']}\n"
                )

            res_text = "\n".join(formatted)
            return ToolResult(
                success=True,
                result=res_text,
                ui_summary=f"Found {len(results)} relevant snippets"
            )
        except Exception as e:
            return ToolResult(success=False, result=f"Error during semantic search: {e}")

    def format_call(self, params: SemanticSearchParams) -> str:
        return f"'{params.query}'"
