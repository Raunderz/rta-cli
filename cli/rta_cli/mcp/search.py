"""
Multi-engine web search using free/no-API-key backends.
Tries engines in priority order: DuckDuckGo, SearXNG, Wikipedia.
"""

import json
import re
import urllib.parse
import urllib.request
import gzip
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


MAX_FETCH_SIZE = 512 * 1024  # 512KB max download


def _strip_prompt_injection(text: str) -> str:
    """Remove common prompt injection patterns from fetched content."""
    patterns = [
        # "Ignore all previous instructions" and variants
        r"(?i)(ignore|disregard|forget|override)\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|commands?|directives?|prompts?|context)",
        # "You are now..." / "From now on, you are..." / "Act as..."
        r"(?i)(from now on|starting now|henceforth|you are now|act as|you will now)\s+.*?(assistant|system|agent|bot|gpt|ai)",
        # Fake system role blocks in markdown
        r"(?i)```(system|assistant|user|instruction)\s*\n.*?```",
        # Explicit "System:" or "[System]" lines
        r"(?im)^(?:\[system\]|system:)\s+.*$",
        # "Say/start with/output..." instructions
        r"(?i)(say|start|begin|output|respond|reply)\s+(with|by)\s+['\"].*?['\"]",
        # Hidden base64-encoded instructions embedded in text
        r"(?i)(?:your\s+)?(?:first\s+)?(?:task|mission|goal|purpose|instruction)\s+(?:is|:)\s+[a-z0-9+/]{40,}={0,2}(?:\s|$)",
    ]
    for pat in patterns:
        text = re.sub(pat, " [redacted] ", text)
    return text


def fetch_url(url: str) -> str:
    """Download a URL and return its readable text content."""
    if not url.startswith(("http://", "https://")):
        return "Error: URL must start with http:// or https://"

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; Rta-CLI/0.5.0)"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if "text" not in content_type and "html" not in content_type and "json" not in content_type:
                return f"Error: Unsupported content type: {content_type}"
            raw = resp.read(MAX_FETCH_SIZE)
            # Try UTF-8, fall back to latin-1
            try:
                html = raw.decode("utf-8")
            except UnicodeDecodeError:
                html = raw.decode("latin-1")

    except Exception as e:
        return f"Error fetching URL: {e}"

    title = ""
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if m:
        title = strip_html(m.group(1)).strip()

    # Remove HTML comments (<!-- ... -->) before any other processing
    cleaned = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
    # Remove script/style tags and their contents
    cleaned = re.sub(r"<(script|style|nav|footer|header)[^>]*>.*?</\1>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
    # Remove all HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    # Decode HTML entities
    cleaned = cleaned.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    cleaned = cleaned.replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
    cleaned = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), cleaned)
    cleaned = re.sub(r"&#[xX]([0-9a-fA-F]+);", lambda m: chr(int(m.group(1), 16)), cleaned)
    cleaned = re.sub(r"&[a-zA-Z]+;", " ", cleaned)
    # Collapse whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Strip prompt injection patterns
    cleaned = _strip_prompt_injection(cleaned)

    # Truncate to keep response manageable
    MAX_TEXT = 100 * 1024  # 100KB of text
    if len(cleaned) > MAX_TEXT:
        cleaned = cleaned[:MAX_TEXT] + "\n\n[truncated...]"

    if title:
        return f"Title: {title}\n\n{cleaned}"
    return cleaned


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


schema_fetch_url = {
    "name": "fetch_url",
    "description": "Download a URL and return its readable text content (title + body). Strips HTML, scripts, and styling. Max 100KB of text, 512KB download limit. Use after web_search to read interesting pages.",
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The full URL to fetch (must start with http:// or https://)",
            },
        },
        "required": ["url"],
    },
}


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


def arxiv_search(query: str, max_results: int = 5) -> str:
    """Search ArXiv for technical and scientific papers."""
    try:
        params = urllib.parse.urlencode({
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
        })
        url = f"http://export.arxiv.org/api/query?{params}"
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = resp.read().decode("utf-8")
            
            entries = re.findall(r"<entry>(.*?)</entry>", data, re.DOTALL)
            results = []
            for entry in entries[:max_results]:
                title_m = re.search(r"<title>(.*?)</title>", entry, re.DOTALL)
                summary_m = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)
                id_m = re.search(r"<id>(.*?)</id>", entry, re.DOTALL)
                
                title = strip_html(title_m.group(1)).strip() if title_m else "No Title"
                summary = strip_html(summary_m.group(1)).strip() if summary_m else "No Summary"
                link = id_m.group(1).strip() if id_m else ""
                
                results.append({
                    "title": title,
                    "url": link,
                    "snippet": summary[:300] + ("..." if len(summary) > 300 else ""),
                })
            
            if not results:
                return "No ArXiv results found."
                
            output = f"ArXiv results for: {query}\n\n"
            for i, r in enumerate(results, 1):
                output += f"{i}. **{r['title']}**\n   {r['snippet']}\n   {r['url']}\n\n"
            return output.strip()
    except Exception as e:
        return f"Error searching ArXiv: {e}"


def so_search(query: str, max_results: int = 5) -> str:
    """Search Stack Overflow for programming questions."""
    try:
        params = urllib.parse.urlencode({
            "order": "desc",
            "sort": "relevance",
            "q": query,
            "site": "stackoverflow",
        })
        url = f"https://api.stackexchange.com/2.3/search/advanced?{params}"
        req = urllib.request.Request(url, headers={"Accept-Encoding": "gzip", "User-Agent": "Rta-CLI"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read()
            if resp.info().get("Content-Encoding") == "gzip":
                content = gzip.decompress(content)
            
            data = json.loads(content.decode("utf-8"))
            results = []
            for item in data.get("items", [])[:max_results]:
                title = item.get("title", "").replace("&quot;", '"').replace("&#39;", "'").replace("&amp;", "&")
                link = item.get("link", "")
                tags = ", ".join(item.get("tags", []))
                score = item.get("score", 0)
                is_answered = " [Answered]" if item.get("is_answered") else ""
                
                results.append({
                    "title": f"{title}{is_answered}",
                    "url": link,
                    "snippet": f"Tags: {tags}. Score: {score}. Views: {item.get('view_count', 0)}",
                })
            
            if not results:
                return "No Stack Overflow results found."
                
            output = f"Stack Overflow results for: {query}\n\n"
            for i, r in enumerate(results, 1):
                output += f"{i}. **{r['title']}**\n   {r['snippet']}\n   {r['url']}\n\n"
            return output.strip()
    except Exception as e:
        return f"Error searching Stack Overflow: {e}"


schema_arxiv_search = {
    "name": "arxiv_search",
    "description": "Search ArXiv for technical and scientific papers. Returns titles, summaries, and links. Ideal for deep technical research.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query (e.g., 'large language model alignment')",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum results to return (default: 5)",
                "default": 5,
            },
        },
        "required": ["query"],
    },
}

schema_so_search = {
    "name": "so_search",
    "description": "Search Stack Overflow for programming-related questions and answers. Returns titles, tags, and links. Use for troubleshooting specific code issues.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The programming-related search query",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum results to return (default: 5)",
                "default": 5,
            },
        },
        "required": ["query"],
    },
}
