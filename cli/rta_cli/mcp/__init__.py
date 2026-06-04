"""MCP (Model Context Protocol) client for Rta CLI."""

import json
import logging
import os
import subprocess
import urllib.request
from pathlib import Path
from typing import Any

log = logging.getLogger("rta.mcp")

MCP_CONFIG_PATH = Path.home() / ".rta" / "mcp_config.json"


def load_mcp_config() -> dict[str, Any]:
    if not MCP_CONFIG_PATH.exists():
        # Create a documented template for new users
        template = {
            "mcpServers": {
                "search": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-duckduckgo"],
                    "env": {},
                    "_comment": "Search the web using DuckDuckGo (No API key needed)",
                },
                "github": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-github"],
                    "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "REPLACE_WITH_YOUR_TOKEN"},
                    "_comment": "Manage GitHub issues and PRs. Requires a Personal Access Token.",
                },
            },
            "_instructions": "Add your MCP servers here. Supports 'command' (stdio) or 'url' (http-sse) transports. Namespaced as mcp_{server_name}_{tool_name}.",
        }
        save_mcp_config(template)
        return template

    with open(MCP_CONFIG_PATH) as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def save_mcp_config(config: dict[str, Any]) -> None:
    MCP_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MCP_CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


import atexit

_PROCESS_CACHE: dict[str, subprocess.Popen] = {}


def cleanup_mcp_servers():
    """Terminate all cached MCP server processes."""
    for server_name, proc in _PROCESS_CACHE.items():
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    _PROCESS_CACHE.clear()


atexit.register(cleanup_mcp_servers)


def _get_cached_process(server_name: str, sc: dict) -> subprocess.Popen | None:
    """Get or create a persistent process for an MCP server."""
    if server_name in _PROCESS_CACHE:
        proc = _PROCESS_CACHE[server_name]
        if proc.poll() is None:  # Process is still running
            return proc
        # Process died, remove it
        log.warning("MCP server '%s' process died, restarting...", server_name)
        del _PROCESS_CACHE[server_name]

    full_env = os.environ.copy()
    full_env.update(sc.get("env", {}))

    try:
        proc = subprocess.Popen(
            [sc["command"], *sc.get("args", [])],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=full_env,
            text=True,
            bufsize=1,  # Line buffered
        )
        _PROCESS_CACHE[server_name] = proc
        return proc
    except Exception as e:
        log.error("Failed to start MCP server '%s': %s", server_name, e)
        return None


def list_mcp_tools(server_name: str) -> list[dict[str, Any]]:
    """Fetch tool definitions from an MCP server."""
    config = load_mcp_config()
    server_configs = config.get("mcpServers", {})
    if server_name not in server_configs:
        return []

    sc = server_configs[server_name]
    request = {
        "jsonrpc": "2.0",
        "id": "list-tools",
        "method": "tools/list",
        "params": {},
    }

    try:
        if "command" in sc:
            response = _send_rpc_stdio(server_name, sc, request)
        elif "url" in sc:
            response = _send_rpc_http(sc, request)
        else:
            return []

        return response.get("tools", []) if response else []
    except Exception:
        return []


def map_mcp_to_openai_schema(
    server_name: str, mcp_tool: dict[str, Any]
) -> dict[str, Any]:
    """Convert MCP tool definition to OpenAI/Gemini function schema."""
    name = mcp_tool.get("name", "unknown")
    # Namespace to avoid collisions: mcp_{server}_{tool}
    namespaced_name = f"mcp_{server_name}_{name}"

    return {
        "name": namespaced_name,
        "description": mcp_tool.get("description", ""),
        "parameters": mcp_tool.get(
            "inputSchema",
            {
                "type": "object",
                "properties": {},
            },
        ),
    }


def _send_rpc_stdio(
    server_name: str, sc: dict, request: dict, _retry: bool = True
) -> Any:
    proc = _get_cached_process(server_name, sc)
    if not proc:
        return {"error": f"Could not start MCP server '{server_name}'"}

    try:
        proc.stdin.write(json.dumps(request) + "\n")
        proc.stdin.flush()

        # Read until we get a valid JSON-RPC response
        while True:
            line = proc.stdout.readline()
            if not line:
                # Process likely died — retry once with a fresh process
                if server_name in _PROCESS_CACHE:
                    del _PROCESS_CACHE[server_name]
                if _retry:
                    log.warning(
                        "MCP server '%s' died mid-RPC, retrying...", server_name
                    )
                    return _send_rpc_stdio(server_name, sc, request, _retry=False)
                break
            try:
                data = json.loads(line)
                if "result" in data or "error" in data:
                    return data.get("result")
            except json.JSONDecodeError:
                continue
    except Exception as e:
        if server_name in _PROCESS_CACHE:
            del _PROCESS_CACHE[server_name]
        if _retry:
            log.warning("MCP RPC error for '%s': %s, retrying...", server_name, e)
            return _send_rpc_stdio(server_name, sc, request, _retry=False)
        return {"error": f"RPC Error: {e}"}
    return None


def _send_rpc_http(sc: dict, request: dict) -> Any:
    # Use urllib.request to avoid httpx dependency if possible (as per plan 12)
    try:
        import httpx

        with httpx.Client() as client:
            resp = client.post(
                sc["url"], json=request, headers=sc.get("headers", {}), timeout=30.0
            )
            resp.raise_for_status()
            return resp.json().get("result")
    except (ImportError, Exception):
        # Fallback to urllib
        try:
            req = urllib.request.Request(
                sc["url"],
                data=json.dumps(request).encode("utf-8"),
                headers={"Content-Type": "application/json", **sc.get("headers", {})},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8")).get("result")
        except Exception as e:
            return {"error": f"HTTP RPC Error: {e}"}


def call_mcp_tool(server_name: str, tool_name: str, arguments: dict[str, Any]) -> Any:
    config = load_mcp_config()
    server_configs = config.get("mcpServers", {})
    if server_name not in server_configs:
        return {"error": f"MCP server '{server_name}' not configured"}

    sc = server_configs[server_name]
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }

    if "command" in sc:
        return _send_rpc_stdio(server_name, sc, request)
    elif "url" in sc:
        return _send_rpc_http(sc, request)
    else:
        return {"error": f"No transport config for server '{server_name}'"}
