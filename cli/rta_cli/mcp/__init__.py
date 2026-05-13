"""MCP (Model Context Protocol) client for Rta CLI."""
import json
import os
import subprocess
import urllib.request
from pathlib import Path
from typing import Any

MCP_CONFIG_PATH = Path.home() / ".rta" / "mcp_config.json"


def load_mcp_config() -> dict[str, Any]:
    if not MCP_CONFIG_PATH.exists():
        return {}
    with open(MCP_CONFIG_PATH) as f:
        return json.load(f)


def save_mcp_config(config: dict[str, Any]) -> None:
    MCP_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MCP_CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def call_mcp_tool(server_name: str, tool_name: str, arguments: dict[str, Any]) -> Any:
    config = load_mcp_config()
    server_configs = config.get("mcpServers", {})
    if server_name not in server_configs:
        return {"error": f"MCP server '{server_name}' not configured"}

    sc = server_configs[server_name]

    if "command" in sc:
        return _call_stdio(sc, tool_name, arguments)
    elif "url" in sc:
        return _call_http(sc, tool_name, arguments)
    else:
        return {"error": f"No transport config for server '{server_name}'"}


def _call_stdio(sc: dict, tool_name: str, arguments: dict) -> Any:
    full_env = os.environ.copy()
    full_env.update(sc.get("env", {}))

    proc = subprocess.Popen(
        [sc["command"], *sc.get("args", [])],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=full_env,
        text=True,
    )

    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }

    proc.stdin.write(json.dumps(request) + "\n")
    proc.stdin.flush()
    response_line = proc.stdout.readline()
    proc.terminate()
    return json.loads(response_line).get("result")


def _call_http(sc: dict, tool_name: str, arguments: dict) -> Any:
    import httpx

    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }

    with httpx.Client() as client:
        resp = client.post(
            sc["url"],
            json=request,
            headers=sc.get("headers", {}),
        )
        resp.raise_for_status()
        return resp.json().get("result")
