import atexit
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any

log = logging.getLogger("kon.mcp")


def _rta_dir() -> str:
    import platform

    if platform.system() == "Windows":
        base = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    else:
        base = os.path.expanduser("~")
    return os.path.join(base, ".rta")


MCP_CONFIG_PATH = Path(_rta_dir()) / "mcp_config.json"


def load_mcp_config() -> dict[str, Any]:
    if not MCP_CONFIG_PATH.exists():
        template = {
            "mcpServers": {
                "search": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-duckduckgo"],
                    "env": {},
                }
            }
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


_PROCESS_CACHE: dict[str, subprocess.Popen] = {}


def cleanup_mcp_servers():
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
    if server_name in _PROCESS_CACHE:
        proc = _PROCESS_CACHE[server_name]
        if proc.poll() is None:
            return proc
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
            bufsize=1,
        )
        _PROCESS_CACHE[server_name] = proc
        return proc
    except Exception as e:
        log.error("Failed to start MCP server '%s': %s", server_name, e)
        return None


def _send_rpc_stdio(server_name: str, sc: dict, request: dict, _retry: bool = True) -> Any:
    proc = _get_cached_process(server_name, sc)
    if not proc:
        return {"error": f"Could not start MCP server '{server_name}'"}

    try:
        proc.stdin.write(json.dumps(request) + "\n")
        proc.stdin.flush()

        while True:
            line = proc.stdout.readline()
            if not line:
                _PROCESS_CACHE.pop(server_name, None)
                if _retry:
                    return _send_rpc_stdio(server_name, sc, request, _retry=False)
                break
            try:
                data = json.loads(line)
                if "result" in data or "error" in data:
                    return data.get("result") or data.get("error")
            except json.JSONDecodeError:
                continue
    except Exception as e:
        _PROCESS_CACHE.pop(server_name, None)
        if _retry:
            return _send_rpc_stdio(server_name, sc, request, _retry=False)
        return {"error": f"RPC Error: {e}"}
    return None


def _send_rpc_http(sc: dict, request: dict) -> Any:
    try:
        import httpx

        with httpx.Client() as client:
            resp = client.post(
                sc["url"], json=request, headers=sc.get("headers", {}), timeout=30.0
            )
            resp.raise_for_status()
            return resp.json().get("result") or resp.json().get("error")
    except Exception as e:
        return {"error": f"HTTP RPC Error: {e}"}


def list_mcp_tools(server_name: str) -> list[dict[str, Any]]:
    config = load_mcp_config()
    server_configs = config.get("mcpServers", {})
    if server_name not in server_configs:
        return []
    sc = server_configs[server_name]
    request = {"jsonrpc": "2.0", "id": "list-tools", "method": "tools/list", "params": {}}
    if "command" in sc:
        res = _send_rpc_stdio(server_name, sc, request)
    elif "url" in sc:
        res = _send_rpc_http(sc, request)
    else:
        return []
    return res.get("tools", []) if isinstance(res, dict) else []


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
    return {"error": f"No transport config for server '{server_name}'"}
