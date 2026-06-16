import asyncio
import gzip
import json
import urllib.parse
import urllib.request

from pydantic import BaseModel, Field

from ..core.types import ToolResult
from .base import BaseTool


class StackOverflowParams(BaseModel):
    query: str = Field(..., description="The programming-related search query")
    max_results: int = Field(5, description="Maximum results to return (default: 5)")


class StackOverflowTool(BaseTool[StackOverflowParams]):
    name = "so_search"
    params = StackOverflowParams
    description = "Search Stack Overflow for programming-related questions and answers. Returns titles, tags, and links. Use for troubleshooting specific code issues."
    mutating = False
    tool_icon = "📚"

    async def execute(
        self, params: StackOverflowParams, cwd: str, cancel_event: asyncio.Event | None = None
    ) -> ToolResult:
        try:
            query_encoded = urllib.parse.urlencode(
                {"order": "desc", "sort": "relevance", "q": params.query, "site": "stackoverflow"}
            )
            url = f"https://api.stackexchange.com/2.3/search/advanced?{query_encoded}"

            loop = asyncio.get_event_loop()

            def _fetch():
                req = urllib.request.Request(url, headers={"Accept-Encoding": "gzip", "User-Agent": "kon-agent"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    content = resp.read()
                    if resp.info().get("Content-Encoding") == "gzip":
                        content = gzip.decompress(content)
                    return json.loads(content.decode("utf-8"))

            data = await loop.run_in_executor(None, _fetch)

            results = []
            for item in data.get("items", [])[: params.max_results]:
                title = item.get("title", "").replace("&quot;", '"').replace("&#39;", "'").replace("&amp;", "&")
                link = item.get("link", "")
                tags = ", ".join(item.get("tags", []))
                score = item.get("score", 0)
                is_answered = " [Answered]" if item.get("is_answered") else ""

                results.append(
                    {
                        "title": f"{title}{is_answered}",
                        "url": link,
                        "snippet": f"Tags: {tags}. Score: {score}. Views: {item.get('view_count', 0)}",
                    }
                )

            if not results:
                return ToolResult(success=True, result="No Stack Overflow results found.")

            output = f"Stack Overflow results for: {params.query}\n\n"
            for i, r in enumerate(results, 1):
                output += f"{i}. **{r['title']}**\n   {r['snippet']}\n   {r['url']}\n\n"

            return ToolResult(success=True, result=output.strip(), ui_summary=f"Found {len(results)} results")
        except Exception as e:
            return ToolResult(success=False, result=f"Error searching Stack Overflow: {e}")

    def format_call(self, params: StackOverflowParams) -> str:
        return f"'{params.query}'"
