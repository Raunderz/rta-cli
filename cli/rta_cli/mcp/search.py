"""
Multi-engine web search using free/no-API-key backends.
Tries engines in priority order: DuckDuckGo, SearXNG, Wikipedia.
"""

import json
import urllib.parse
import urllib.request
from ddgs import DDGS

SEARXNG_INSTANCES = [
    "https://searx.be",
    "https://search.sapti.me",
    "https://search.mdosch.de",
]


def _search_ddgs(query: str, max_results: int = 5) -> list[dict]:
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                    "engine": "duckduckgo",
                })
    except Exception:
        pass
    return results


def _search_searxng(query: str, max_results: int = 5) -> list[dict]:
    results = []
    params = urllib.parse.urlencode({"q": query, "format": "json", "language": "en-US"})
    for instance in SEARXNG_INSTANCES:
        try:
            url = f"{instance}/search?{params}"
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                for r in data.get("results", [])[:max_results]:
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "snippet": r.get("content", ""),
                        "engine": "searxng",
                    })
                if results:
                    break
        except Exception:
            continue
    return results


def _search_wikipedia(query: str, max_results: int = 5) -> list[dict]:
    results = []
    try:
        params = urllib.parse.urlencode({
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": max_results,
        })
        url = f"https://en.wikipedia.org/w/api.php?{params}"
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            for r in data.get("query", {}).get("search", []):
                title = r.get("title", "")
                results.append({
                    "title": title,
                    "url": f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}",
                    "snippet": r.get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", ""),
                    "engine": "wikipedia",
                })
    except Exception:
        pass
    return results


SEARCH_ENGINES = [
    ("duckduckgo", _search_ddgs),
    ("searxng", _search_searxng),
    ("wikipedia", _search_wikipedia),
]


def web_search(query: str, max_results: int = 8) -> str:
    seen_urls = set()
    all_results = []
    errors = []

    for name, engine_fn in SEARCH_ENGINES:
        try:
            results = engine_fn(query, max_results)
            for r in results:
                url = r.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_results.append(r)
                    if len(all_results) >= max_results:
                        break
        except Exception as e:
            errors.append(f"{name}: {e}")
        if len(all_results) >= max_results:
            break

    if not all_results:
        err_msg = "; ".join(errors) if errors else "All engines returned empty."
        return f"No results found. Errors: {err_msg}"

    output = f"Search results for: {query}\n\n"
    for i, r in enumerate(all_results[:max_results], 1):
        output += f"{i}. **{r['title']}** ({r['engine']})\n   {r['snippet']}\n   {r['url']}\n\n"
    return output.strip()


schema_web_search = {
    "name": "web_search",
    "description": "Search the web using multiple free search engines (DuckDuckGo, SearXNG, Wikipedia). No API key required. Returns titles, snippets, and URLs.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query string",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return (default: 8)",
                "default": 8,
            },
        },
        "required": ["query"],
    },
}
