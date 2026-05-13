"""
MCP (Model Context Protocol) client for Rta CLI.
Supports stdio and HTTP-SSE transport modes.
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Any

MCP_CONFIG_PATH = Path.home() / ".rta" / "mcp_config.json"


def load_mcp_config() -> dict[str, Any]:
    """Load MCP server configuration."""
    if not MCP_CONFIG_PATH.exists():
        return {}
    with open(MCP_CONFIG_PATH) as f:
        return json.load(f)


def save_mcp_config(config: dict[str, Any]) -> None:
    """Save MCP server configuration."""
    MCP_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MCP_CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


class MCPServer:
    """Base class for MCP servers."""

    def __init__(self, name: str, config: dict[str, Any]):
        self.name = name
        self.config = config

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool on this MCP server."""
        raise NotImplementedError


class STDIO(MCPServer):
    """MCP server running as a subprocess (stdio transport)."""

    def __init__(self, name: str, config: dict[str, Any]):
        super().__init__(name, config)
        self.command = config.get("command")
        self.args = config.get("args", [])
        self.env = config.get("env", {})
        self._process: subprocess.Popen | None = None

    def _ensure_running(self):
        """Start the subprocess if not running."""
        if self._process is not None:
            return

        full_env = os.environ.copy()
        full_env.update(self.env)

        self._process = subprocess.Popen(
            [self.command, *self.args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=full_env,
            text=True,
        )

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Send JSON-RPC request to the MCP server."""
        self._ensure_running()

        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
        }

        self._process.stdin.write(json.dumps(request) + "\n")
        self._process.stdin.flush()

        # Read response (simplified - real impl would handle streaming)
        response_line = self._process.stdout.readline()
        return json.loads(response_line).get("result")


class HTTPMCPServer(MCPServer):
    """MCP server accessed via HTTP-SSE."""

    def __init__(self, name: str, config: dict[str, Any]):
        super().__init__(name, config)
        self.url = config.get("url")
        self.headers = config.get("headers", {})

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Send JSON-RPC request via HTTP."""
        import httpx

        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
        }

        with httpx.Client() as client:
            resp = client.post(self.url, json=request, headers=self.headers)
            resp.raise_for_status()
            return resp.json().get("result")


def get_mcp_server(name: str) -> MCPServer | None:
    """Get an MCP server by name."""
    config = load_mcp_config()
    server_configs = config.get("mcpServers", {})
    if name not in server_configs:
        return None

    server_config = server_configs[name]

    if "command" in server_config:
        return STDIO(name, server_config)
    elif "url" in server_config:
        return HTTPMCPServer(name, server_config)

    return None