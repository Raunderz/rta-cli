import asyncio
import re
import urllib.parse
import urllib.request

from pydantic import BaseModel, Field

from ..core.types import ToolResult
from .base import BaseTool


class ArXivParams(BaseModel):
    query: str = Field(..., description="The search query (e.g., 'large language model alignment')")
    max_results: int = Field(5, description="Maximum results to return (default: 5)")


class ArXivTool(BaseTool[ArXivParams]):
    name = "arxiv_search"
    params = ArXivParams
    description = "Search ArXiv for technical and scientific papers. Returns titles, summaries, and links. Ideal for deep technical research."
    mutating = False
    tool_icon = "📄"

    async def execute(self, params: ArXivParams, cwd: str, cancel_event: asyncio.Event | None = None) -> ToolResult:
        try:
            query_encoded = urllib.parse.urlencode(
                {"search_query": f"all:{params.query}", "start": 0, "max_results": params.max_results}
            )
            url = f"http://export.arxiv.org/api/query?{query_encoded}"

            # Use run_in_executor for blocking urllib call
            loop = asyncio.get_event_loop()

            def _fetch():
                with urllib.request.urlopen(url, timeout=10) as resp:
                    return resp.read().decode("utf-8")

            data = await loop.run_in_executor(None, _fetch)

            entries = re.findall(r"<entry>(.*?)</entry>", data, re.DOTALL)
            results = []
            for entry in entries[: params.max_results]:
                title_m = re.search(r"<title>(.*?)</title>", entry, re.DOTALL)
                summary_m = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)
                id_m = re.search(r"<id>(.*?)</id>", entry, re.DOTALL)

                title = self._strip_html(title_m.group(1)).strip() if title_m else "No Title"
                summary = self._strip_html(summary_m.group(1)).strip() if summary_m else "No Summary"
                link = id_m.group(1).strip() if id_m else ""

                results.append(
                    {"title": title, "url": link, "snippet": summary[:300] + ("..." if len(summary) > 300 else "")}
                )

            if not results:
                return ToolResult(success=True, result="No ArXiv results found.")

            output = f"ArXiv results for: {params.query}\n\n"
            for i, r in enumerate(results, 1):
                output += f"{i}. **{r['title']}**\n   {r['snippet']}\n   {r['url']}\n\n"

            return ToolResult(success=True, result=output.strip(), ui_summary=f"Found {len(results)} papers")
        except Exception as e:
            return ToolResult(success=False, result=f"Error searching ArXiv: {e}")

    def _strip_html(self, text: str) -> str:
        return re.sub(r"<[^>]+>", "", text)

    def format_call(self, params: ArXivParams) -> str:
        return f"'{params.query}'"
