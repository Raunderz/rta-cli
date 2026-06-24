import asyncio

from ddgs import DDGS
from pydantic import BaseModel, Field

from ..core.types import ToolResult
from ._tool_utils import ToolCancelledError, await_task_or_cancel
from .base import BaseTool


class WebSearchParams(BaseModel):
    query: str = Field(description="Search query")
    max_results: int = Field(description="Number of results to return (default 10)", default=10, ge=1, le=10)


class WebSearchTool(BaseTool):
    name = "web_search"
    tool_icon = "%"
    mutating = False
    params = WebSearchParams
    prompt_guidelines = (
        "Use web_search for any question about current/recent events, news, "
        "sports scores, weather, stock prices, or anything beyond your "
        "training data cutoff. Do NOT say you lack internet access — you "
        "have web_search and web_fetch tools. Use web_fetch to read full "
        "page content from a result URL.",
    )
    description = (
        "Search the web using DuckDuckGo. Returns titles, URLs, and snippets for each result. "
        "Use web_fetch to read full page content from a result URL."
    )

    def format_call(self, params: WebSearchParams) -> str:
        query = params.query.replace('"', '\\"')
        return f'"{query}"'

    async def execute(self, params: WebSearchParams, cwd: str, cancel_event: asyncio.Event | None = None) -> ToolResult:
        def _search() -> list[dict]:
            return list(DDGS().text(params.query, max_results=params.max_results))

        try:
            work = asyncio.create_task(asyncio.to_thread(_search))
            results = await await_task_or_cancel(work, cancel_event)
        except ToolCancelledError:
            return ToolResult(success=False, result="Search aborted")
        except Exception as e:
            return ToolResult(success=False, ui_summary=f"[red]Search failed: {e}[/red]")

        if not results:
            return ToolResult(success=True, result="No results found", ui_summary="[dim]No results found[/dim]")

        lines = []
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. {r.get('title', '(no title)')}")
            lines.append(f"   {r.get('href', '')}")
            lines.append(f"   {r.get('body', '')}")
            lines.append("")

        result_text = "\n".join(lines).strip()
        ui_summary = f"[dim]({len(results)} results)[/dim]"

        return ToolResult(success=True, result=result_text, ui_summary=ui_summary)


class DeepSearchParams(BaseModel):
    query: str = Field(..., description="The research query or topic to explore")
    max_results: int = Field(8, description="Maximum results to return after deduplication (default: 8)")
    num_queries: int = Field(3, description="Number of sub-queries to generate (default: 3, max: 5)")


class DeepSearchTool(BaseTool[DeepSearchParams]):
    name = "deep_search"
    params = DeepSearchParams
    description = "Deep research search: auto-generates multiple sub-queries from your query, runs all of them in parallel, and deduplicates results. Finds more comprehensive and diverse results than a single web_search call. Best for complex research topics."
    mutating = False
    tool_icon = "🔎"

    async def execute(self, params: DeepSearchParams, cwd: str, cancel_event: asyncio.Event | None = None) -> ToolResult:
        sub_queries = self._expand_queries(params.query, params.num_queries)
        seen_urls = set()
        all_results = []

        # We'll run them sequentially for simplicity and to respect DDG rate limits
        for sq in sub_queries:
            if cancel_event and cancel_event.is_set():
                break

            def _search(q: str) -> list[dict]:
                return list(DDGS().text(q, max_results=params.max_results))

            try:
                work = asyncio.create_task(asyncio.to_thread(_search, sq))
                results = await await_task_or_cancel(work, cancel_event)
                for r in results:
                    url = r.get("href", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_results.append(r)
            except Exception:
                continue

        all_results = all_results[: params.max_results]
        if not all_results:
            return ToolResult(success=True, result=f"No results found for: {params.query}")

        output = f"Deep search results for: {params.query}\n(Sub-queries: {', '.join(sub_queries)})\n\n"
        for i, r in enumerate(all_results, 1):
            output += f"{i}. **{r.get('title', '(no title)')}**\n   {r.get('body', '')}\n   {r.get('href', '')}\n\n"

        return ToolResult(
            success=True,
            result=output.strip(),
            ui_summary=f"({len(all_results)} results from {len(sub_queries)} queries)",
        )

    def _expand_queries(self, query: str, num_queries: int = 3) -> list[str]:
        queries = [query]
        stop_words = {
            "the",
            "a",
            "an",
            "in",
            "of",
            "for",
            "on",
            "and",
            "to",
            "is",
            "what",
            "how",
            "why",
            "does",
            "do",
            "are",
            "with",
            "at",
            "by",
            "from",
            "or",
            "as",
            "be",
            "this",
            "that",
        }
        words = query.split()
        content_words = [w for w in words if w.lower() not in stop_words]
        if len(words) > 2:
            queries.append(" ".join(words[1:]))
            queries.append(" ".join(words[:-1]))
        if content_words and len(content_words) > 1 and len(queries) < num_queries:
            queries.append(" ".join(content_words))

        seen = set()
        result = []
        for q in queries:
            key = q.lower().strip()
            if key and key not in seen:
                seen.add(key)
                result.append(q)
        return result[:num_queries]

    def format_call(self, params: DeepSearchParams) -> str:
        return f"'{params.query}'"
