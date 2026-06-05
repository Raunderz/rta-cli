import asyncio
import json
import urllib.parse
import urllib.request
from typing import Literal

from pydantic import BaseModel, Field

from ..core.types import ToolResult
from .base import BaseTool


class GitHubSearchParams(BaseModel):
    query: str = Field(
        ...,
        description="The search query (e.g., 'machine learning rust', 'user:torvalds repo:linux')",
    )
    search_type: Literal["repositories", "code", "issues"] = Field(
        "repositories", description="What to search: 'repositories', 'code', or 'issues'"
    )
    max_results: int = Field(5, description="Maximum results to return (default: 5)")


class GitHubSearchTool(BaseTool[GitHubSearchParams]):
    name = "github_search"
    params = GitHubSearchParams
    description = "Search GitHub for repositories, code, or issues. Rate-limited to 60 requests/hour without authentication. Use for finding open-source projects, example code, or tracking issues."
    mutating = False
    tool_icon = "🐙"

    async def execute(
        self, params: GitHubSearchParams, cancel_event: asyncio.Event | None = None
    ) -> ToolResult:
        try:
            params_v = {
                "q": params.query,
                "per_page": params.max_results,
                "sort": "stars" if params.search_type == "repositories" else None,
            }
            query_encoded = urllib.parse.urlencode({k: v for k, v in params_v.items() if v})
            url = f"https://api.github.com/search/{params.search_type}?{query_encoded}"

            loop = asyncio.get_event_loop()

            def _fetch():
                req = urllib.request.Request(
                    url,
                    headers={
                        "Accept": "application/vnd.github.v3+json",
                        "User-Agent": "kon-agent",
                    },
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    return json.loads(resp.read().decode("utf-8"))

            data = await loop.run_in_executor(None, _fetch)

            items = data.get("items", [])[: params.max_results]
            if not items:
                return ToolResult(
                    success=True, result=f"No GitHub {params.search_type} results found."
                )

            output = f"GitHub {params.search_type.capitalize()} results for: {params.query}\n\n"
            for i, item in enumerate(items, 1):
                if params.search_type == "repositories":
                    name = item.get("full_name", "")
                    desc = item.get("description") or "No description"
                    stars = item.get("stargazers_count", 0)
                    lang = item.get("language") or "Unknown"
                    url_link = item.get("html_url", "")
                    output += f"{i}. **{name}** ({lang}, ⭐{stars})\n   {desc}\n   {url_link}\n\n"
                elif params.search_type == "code":
                    name = item.get("name", "")
                    path = item.get("path", "")
                    repo = item.get("repository", {}).get("full_name", "")
                    url_link = item.get("html_url", "")
                    output += f"{i}. **{name}** in {repo}\n   {path}\n   {url_link}\n\n"
                elif params.search_type == "issues":
                    title = item.get("title", "")
                    state = item.get("state", "")
                    repo_url = item.get("repository_url", "")
                    repo = repo_url.split("/repos/")[-1] if "/repos/" in repo_url else ""
                    comments = item.get("comments", 0)
                    url_link = item.get("html_url", "")
                    output += f"{i}. **{title}** ({state}, {comments} comments)\n   Repo: {repo}\n   {url_link}\n\n"

            return ToolResult(
                success=True,
                result=output.strip(),
                ui_summary=f"Found {len(items)} {params.search_type}",
            )
        except urllib.error.HTTPError as e:
            if e.code == 403:
                return ToolResult(
                    success=False, result="GitHub API rate limit exceeded. Try again later."
                )
            return ToolResult(success=False, result=f"Error searching GitHub: HTTP {e.code}")
        except Exception as e:
            return ToolResult(success=False, result=f"Error searching GitHub: {e}")

    def format_call(self, params: GitHubSearchParams) -> str:
        return f"{params.search_type}: '{params.query}'"
