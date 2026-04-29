"""Agent: routes all AI calls through Rta backend middleware."""
import sys
from typing import Generator

import httpx

from rta_cli.utils import load_credential, get_device_id, get_server_url
from rta_cli.functions.get_file_content import get_file_contents, schema_get_file_contents
from rta_cli.functions.get_files_info import get_files_info, schema_get_files_info
from rta_cli.functions.run_python_file import run_python_file, schema_run_python_file
from rta_cli.functions.write_file import write_file, schema_write_file
from rta_cli.functions.run_command import run_command, schema_run_command
from rta_cli.functions.grep_search import grep_search, schema_grep_search
from rta_cli.functions.glob_search import glob_search, schema_glob_search
from rta_cli.functions.edit_file import edit_file, schema_edit_file
from rta_cli.functions.delete_file import delete_file, schema_delete_file
from rta_cli.functions.create_dir import create_dir, schema_create_dir
from rta_cli.functions.list_directory import list_directory, schema_list_directory

CLI_VERSION = "2.0.0"

AVAILABLE_TOOLS = [
    {"type": "function", "function": f}
    for f in [
        schema_get_files_info,
        schema_get_file_contents,
        schema_run_python_file,
        schema_write_file,
        schema_run_command,
        schema_grep_search,
        schema_glob_search,
        schema_edit_file,
        schema_delete_file,
        schema_create_dir,
        schema_list_directory,
    ]
]

ERROR_MESSAGES = {
    401: "Invalid or expired API key. Run: rta login",
    429: "Daily limit reached. Upgrade at https://rta-three.vercel.app/#/pricing",
    502: "Rta service temporarily unavailable. Check https://rta-three.vercel.app",
    503: "Rta service unavailable. Check https://rta-three.vercel.app",
}


def _require_key() -> str:
    key = load_credential("rta_api_key")
    if not key:
        print(
            "\nNo API key found. Get one at https://rta-three.vercel.app/dashboard.html and run: rta login",
            file=sys.stderr,
        )
        sys.exit(1)
    return key


def _request_headers(api_key: str) -> dict:
    return {
        "X-API-KEY": api_key,
        "X-Device-ID": get_device_id(),
        "X-CLI-Version": CLI_VERSION,
        "ngrok-skip-browser-warning": "69420",
        "User-Agent": f"rta-cli/1.0",
    }


def call_function(function_call: dict, workspace_dir: str) -> dict:
    name = function_call.get("name")
    args = function_call.get("args", {})

    dispatch = {
        "get_files_info":   lambda: get_files_info(workspace_dir, **args),
        "get_file_contents": lambda: get_file_contents(workspace_dir, **args),
        "run_python_file":  lambda: run_python_file(workspace_dir, **args),
        "write_file":       lambda: write_file(workspace_dir, **args),
        "run_command":      lambda: run_command(workspace_dir, **args),
        "grep_search":      lambda: grep_search(workspace_dir, **args),
        "glob_search":      lambda: glob_search(workspace_dir, **args),
        "edit_file":        lambda: edit_file(workspace_dir, **args),
        "delete_file":      lambda: delete_file(workspace_dir, **args),
        "create_dir":       lambda: create_dir(workspace_dir, **args),
        "list_directory":   lambda: list_directory(workspace_dir, **args),
    }

    fn = dispatch.get(name)
    result = fn() if fn else f"Error: function '{name}' not found"

    return {
        "functionResponse": {
            "name": name,
            "response": {"name": name, "content": result},
        }
    }


def _call_backend(
    messages: list[dict],
    tools: list[dict],
    workspace_path: str,
    api_key: str,
    max_tokens: int = 2000,
) -> dict:
    """Single POST to /v1/chat. Returns parsed JSON or raises."""
    server_url = get_server_url()

    try:
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(
                f"{server_url}/v1/chat",
                headers=_request_headers(api_key),
                json={
                    "messages": messages,
                    "model": "auto",
                    "provider": "auto",
                    "tools": tools,
                    "stream": False,
                    "workspace_path": workspace_path,
                    "max_tokens": max_tokens,
                },
            )
    except httpx.ConnectError:
        raise RuntimeError("Cannot reach Rta server. Check your connection.")
    except httpx.TimeoutException:
        raise RuntimeError("Request timed out. Try again.")
    except Exception as e:
        raise RuntimeError(f"Network error: {e}")

    if resp.status_code in ERROR_MESSAGES:
        raise RuntimeError(ERROR_MESSAGES[resp.status_code])
    if resp.status_code != 200:
        raise RuntimeError(f"Server error ({resp.status_code}): {resp.text[:200]}")

    return resp.json()


def stream_agent(
    prompt: str,
    workspace_dir: str,
    messages: list[dict],
    provider: str = "rta",   # kept for compat but ignored; always uses backend
    model_name: str = "auto",
    max_iterations: int = 20,
    think: bool = False,
) -> Generator[dict, None, None]:
    """
    Agentic loop. Each iteration:
      1. POST /v1/chat with current messages + tools
      2. Parse response: text + tool_calls
      3. Execute tool_calls locally, append results
      4. Repeat until no tool_calls or max_iterations
    """
    api_key = _require_key()

    usage = {
        "prompt_tokens": 0,
        "candidate_tokens": 0,
        "total_tokens": 0,
        "cached_tokens": 0,
    }

    # Normalise incoming messages to flat OpenAI format for backend
    if not messages:
        messages = []
    if not any(m.get("role") == "user" for m in messages):
        messages.append({"role": "user", "content": prompt})

    for _ in range(max_iterations):
        try:
            data = _call_backend(
                messages=messages,
                tools=AVAILABLE_TOOLS,
                workspace_path=workspace_dir,
                api_key=api_key,
            )
        except RuntimeError as e:
            yield {"type": "error", "content": str(e)}
            return

        # Accumulate usage
        u = data.get("usage", {})
        usage["prompt_tokens"]    += u.get("prompt_tokens", 0)
        usage["candidate_tokens"] += u.get("completion_tokens", 0)
        usage["total_tokens"]     += u.get("prompt_tokens", 0) + u.get("completion_tokens", 0)
        usage["cached_tokens"]    += u.get("cached_tokens", 0)

        choices = data.get("choices", [])
        if not choices:
            yield {"type": "error", "content": "Empty response from backend."}
            return

        msg = choices[0].get("message", {})
        text = msg.get("content") or ""
        tool_calls = msg.get("tool_calls") or []

        if text:
            yield {"type": "text", "content": text}

        # Append assistant turn
        assistant_msg: dict = {"role": "assistant"}
        if text:
            assistant_msg["content"] = text
        if tool_calls:
            assistant_msg["tool_calls"] = tool_calls
        messages.append(assistant_msg)

        if not tool_calls:
            yield {"type": "usage", "content": usage}
            return

        # Execute tools, build tool result messages
        for tc in tool_calls:
            fn = tc.get("function", {})
            name = fn.get("name")
            call_id = tc.get("id", "call_unknown")

            import json as _json
            args = {}
            try:
                args = _json.loads(fn.get("arguments", "{}"))
            except Exception:
                pass

            yield {"type": "tool_start", "content": name}
            result = call_function({"name": name, "args": args}, workspace_dir)
            content = str(result["functionResponse"]["response"]["content"])

            messages.append({
                "role": "tool",
                "tool_call_id": call_id,
                "name": name,
                "content": content,
            })

    yield {"type": "error", "content": "Max iterations reached."}
    yield {"type": "usage", "content": usage}


def run_agent(
    prompt: str,
    workspace_dir: str,
    messages: list[dict],
    provider: str = "rta",
    model_name: str = "auto",
    max_iterations: int = 20,
    think: bool = False,
) -> tuple[str, dict]:
    """Compatibility wrapper: collects stream_agent events → (text, usage)."""
    final_text = ""
    last_usage: dict = {}

    for event in stream_agent(prompt, workspace_dir, messages, provider, model_name, max_iterations, think):
        if event["type"] == "text":
            final_text += event["content"] + "\n\n"
        elif event["type"] == "tool_start":
            final_text += f"*(Executed tool: `{event['content']}`)*\n\n"
        elif event["type"] == "thought":
            final_text += f"> *{event['content']}*\n\n"
        elif event["type"] == "usage":
            last_usage = event["content"]
        elif event["type"] == "error":
            return f"Error: {event['content']}", {}

    return final_text.strip(), last_usage
