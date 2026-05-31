"""Agent: routes all AI calls through Rta backend middleware."""
import sys
import json as _json
from concurrent.futures import ThreadPoolExecutor
from typing import Generator

import httpx

from rta_cli.utils import load_credential, get_device_id, get_server_url
from rta_cli.functions.get_file_content import get_file_contents, schema_get_file_contents
from rta_cli.functions.get_files_info import get_files_info, schema_get_files_info
from rta_cli.functions.write_file import write_file, schema_write_file
from rta_cli.functions.run_command import run_command, schema_run_command
from rta_cli.functions.grep_search import grep_search, schema_grep_search
from rta_cli.functions.glob_search import glob_search, schema_glob_search
from rta_cli.functions.edit_file import edit_file, schema_edit_file
from rta_cli.functions.edit_file_ast import edit_file_ast, schema_edit_file_ast
from rta_cli.functions.apply_diff import apply_diff, schema_apply_diff
from rta_cli.functions.delete_file import delete_file, schema_delete_file
from rta_cli.functions.create_dir import create_dir, schema_create_dir
from rta_cli.functions.list_directory import list_directory, schema_list_directory
from rta_cli.functions.list_skills import list_skills, schema_list_skills
from rta_cli.functions.semantic_search import semantic_search, schema_semantic_search
from rta_cli.functions.get_repo_skeleton import get_repo_skeleton, schema_get_repo_skeleton
from rta_cli.functions.lsp_tools import get_diagnostics, go_to_definition, schema_get_diagnostics, schema_go_to_definition
from rta_cli.mcp.search import web_search, schema_web_search, fetch_url, schema_fetch_url
from rta_cli.mcp.sequential_thinking import sequential_thinking, schema_sequential_thinking
from rta_cli.mcp.memory import memorize, recall, forget, schema_memorize, schema_recall, schema_forget
from rta_cli.mcp import call_mcp_tool, list_mcp_tools, map_mcp_to_openai_schema, load_mcp_config
from rta_cli.discovery import discover_project, get_test_command, get_lint_command, get_build_command, schema_discovery
from rta_cli.questions import ask_question, schema_question
from rta_cli.git import (
    git_status, git_diff, git_log, git_commit, git_create_pr, git_branch,
    schema_git_status, schema_git_diff, schema_git_log, schema_git_commit,
    schema_git_create_pr, schema_git_branch,
)

CLI_VERSION = "0.5.0"

_NATIVE_TOOLS = [
    schema_discovery,
    schema_get_files_info,
    schema_get_file_contents,
    schema_write_file,
    schema_run_command,
    schema_grep_search,
    schema_glob_search,
    schema_edit_file,
    schema_edit_file_ast,
    schema_apply_diff,
    schema_delete_file,
    schema_list_directory,
    schema_list_skills,
    schema_semantic_search,
    schema_get_repo_skeleton,
    schema_get_diagnostics,
    schema_go_to_definition,
    schema_question,
    schema_git_status,
    schema_git_diff,
    schema_git_log,
    schema_git_commit,
    schema_git_create_pr,
    schema_git_branch,
    schema_web_search,
    schema_fetch_url,
    schema_sequential_thinking,
    schema_memorize,
    schema_recall,
    schema_forget,
]

def get_available_tools() -> list[dict]:
    """Combine native tools with dynamic MCP tools."""
    tools = [{"type": "function", "function": f} for f in _NATIVE_TOOLS]
    
    # Load dynamic MCP tools from config
    config = load_mcp_config()
    for server_name in config.get("mcpServers", {}):
        mcp_tools = list_mcp_tools(server_name)
        for tool in mcp_tools:
            openai_schema = map_mcp_to_openai_schema(server_name, tool)
            tools.append({"type": "function", "function": openai_schema})
            
    return tools

AVAILABLE_TOOLS = get_available_tools()

READ_ONLY_TOOLS = {
    "get_files_info", "get_file_contents", "grep_search", "glob_search",
    "list_directory", "discover_project", "get_repo_skeleton", "semantic_search",
    "get_diagnostics", "go_to_definition",
    "web_search", "fetch_url", "sequential_thinking", "recall",
    "git_status", "git_diff", "git_log",
    "question",
}

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


def explain_error(tool: str, error: str, args: dict) -> str:
    """Enhanced error messages for the agent."""
    if not error.lower().startswith("error"):
        return error

    if tool == "run_command":
        if "not found" in error or "no such file" in error.lower():
            cmd = args.get("command", "").split()[0] if args.get("command") else "command"
            return f"{error} - Suggestion: Check if '{cmd}' is installed or use full path."
    
    if tool == "edit_file":
        if "old_string not found" in error:
            return f"{error} - Hint: whitespace/indentation must match exactly. Use get_file_contents to verify content first."
    
    if tool == "get_file_contents":
        if "not found" in error or "no such file" in error.lower():
            return f"{error} - Hint: Check path with list_directory or get_files_info."

    return error


def _run_auto_lint(workspace_dir: str) -> str | None:
    """Detect and run linter, return output if it fails."""
    try:
        info = discover_project(workspace_dir)
        cmd = get_lint_command(info)
        if not cmd:
            return None
        
        # Run linter via run_command logic but quietly
        from rta_cli.functions.run_command import run_command
        res = run_command(workspace_dir, cmd, timeout=30)
        
        # If return code is non-zero, it failed
        if "RETURN CODE : 0" not in res:
            return res
        return None
    except Exception:
        return None


def call_function(function_call: dict, workspace_dir: str, default_timeout: int = 120, force: bool = False, read_only: bool = False) -> dict:
    name = function_call.get("name")
    args = function_call.get("args", {})

    # Check read-only permission (including dynamic MCP tools)
    is_mcp = name.startswith("mcp_")
    if read_only:
        allowed = name in READ_ONLY_TOOLS
        # By default, dynamic MCP tools are BLOCKED in review mode unless we white-list them.
        # For now, block all unless specifically in READ_ONLY_TOOLS.
        if not allowed:
            return {
                "functionResponse": {
                    "name": name,
                    "response": {"name": name, "content": f"Blocked: '{name}' is not available in review mode. Only read-only tools are allowed."},
                }
            }

    # Plan 2.3: Per-tool timeouts
    TIMEOUTS = {
        "get_file_contents": 10,
        "run_command": default_timeout,
        "glob_search": 10,
        "grep_search": 30,
        "edit_file": 10,
        "write_file": 10,
        "delete_file": 10,
        "create_dir": 10,
        "list_directory": 10,
        "discover_project": 10,
        "get_files_info": 20,
        "question": 60,
        "git_status": 10,
        "git_diff": 30,
        "git_log": 10,
        "git_commit": 60,
        "git_create_pr": 120,
        "git_branch": 10,
        "web_search": 30,
        "fetch_url": 20,
        "sequential_thinking": 30,
        "memorize": 10,
        "recall": 10,
        "forget": 10,
    }
    
    timeout = TIMEOUTS.get(name, 10)

    # Pass timeout to tools that support it
    if name in ["run_command", "grep_search"]:
        args["timeout"] = timeout

    # Handle Dynamic MCP tools
    if is_mcp:
        # Format: mcp_{server}_{tool}
        parts = name.split("_")
        if len(parts) >= 3:
            server_name = parts[1]
            real_tool_name = "_".join(parts[2:])
            result = call_mcp_tool(server_name, real_tool_name, args)
            # Normalize MCP results (can be complex objects)
            if isinstance(result, dict) and "content" in result:
                # Often MCP returns {"content": [{"type": "text", "text": "..."}]}
                content_items = result["content"]
                if isinstance(content_items, list):
                    text_parts = []
                    for item in content_items:
                        if item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                    result = "\n".join(text_parts)
        else:
            result = f"Error: Invalid MCP tool name format '{name}'"
    else:
        funcs = {
            "discover_project":   discover_project,
            "get_files_info":     get_files_info,
            "get_file_contents":  get_file_contents,
            "write_file":         write_file,
            "run_command":        run_command,
            "grep_search":        grep_search,
            "glob_search":        glob_search,
            "edit_file":          edit_file,
            "edit_file_ast":      edit_file_ast,
            "apply_diff":         apply_diff,
            "delete_file":        delete_file,
            "create_dir":         create_dir,
            "list_directory":     list_directory,
            "list_skills":        list_skills,
            "semantic_search":    semantic_search,
            "get_repo_skeleton":  get_repo_skeleton,
            "get_diagnostics":    get_diagnostics,
            "go_to_definition":   go_to_definition,
            "question":           ask_question,
            "git_status":         git_status,
            "git_diff":           git_diff,
            "git_log":            git_log,
            "git_commit":         git_commit,
            "git_create_pr":      git_create_pr,
            "git_branch":         git_branch,
            "web_search":         web_search,
            "fetch_url":          fetch_url,
            "sequential_thinking": sequential_thinking,
            "memorize":           memorize,
            "recall":             recall,
            "forget":             forget,
        }
        target_fn = funcs.get(name)
        if target_fn:
            import inspect
            try:
                sig = inspect.signature(target_fn)
                has_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
                if not has_kwargs:
                    args = {k: v for k, v in args.items() if k in sig.parameters}
            except Exception:
                pass

        dispatch = {
            "discover_project":   lambda: discover_project(workspace_dir),
            "get_files_info":     lambda: get_files_info(workspace_dir, **args),
            "get_file_contents":  lambda: get_file_contents(workspace_dir, **args),
            "write_file":         lambda: write_file(workspace_dir, **args),
            "run_command":        lambda: run_command(workspace_dir, **args, force=force),
            "grep_search":        lambda: grep_search(workspace_dir, **args),
            "glob_search":        lambda: glob_search(workspace_dir, **args),
            "edit_file":          lambda: edit_file(workspace_dir, **args),
            "edit_file_ast":      lambda: edit_file_ast(workspace_dir, **args),
            "apply_diff":         lambda: apply_diff(workspace_dir, **args),
            "delete_file":        lambda: delete_file(workspace_dir, **args, force=force),
            "create_dir":         lambda: create_dir(workspace_dir, **args),
            "list_directory":     lambda: list_directory(workspace_dir, **args),
            "list_skills":        lambda: list_skills(workspace_dir),
            "semantic_search":    lambda: semantic_search(workspace_dir, **args),
            "get_repo_skeleton":  lambda: get_repo_skeleton(workspace_dir),
            "get_diagnostics":    lambda: get_diagnostics(workspace_dir, **args),
            "go_to_definition":   lambda: go_to_definition(workspace_dir, **args),
            "question":           lambda: ask_question(workspace_dir, **args),
            "git_status":         lambda: git_status(workspace_dir),
            "git_diff":           lambda: git_diff(workspace_dir, **args),
            "git_log":            lambda: git_log(workspace_dir, **args),
            "git_commit":         lambda: git_commit(workspace_dir, **args, force=force),
            "git_create_pr":      lambda: git_create_pr(workspace_dir, **args),
            "git_branch":         lambda: git_branch(workspace_dir, **args),
            "web_search":         lambda: web_search(**args),
            "fetch_url":          lambda: fetch_url(**args),
            "sequential_thinking": lambda: sequential_thinking(**args),
            "memorize":           lambda: memorize(**args),
            "recall":             lambda: recall(**args),
            "forget":             lambda: forget(**args),
        }
        fn = dispatch.get(name)
        result = fn() if fn else f"Error: function '{name}' not found"

    # Plan 6.2: Auto-lint after mutating edits
    MUTATING_TOOLS = ["write_file", "edit_file", "edit_file_ast", "apply_diff"]
    if name in MUTATING_TOOLS and isinstance(result, str) and result.startswith("Successfully"):
        lint_error = _run_auto_lint(workspace_dir)
        if lint_error:
            result += f"\n\n[AUTO-LINT] Found issues after edit:\n{lint_error}\nPlease fix these issues."

    # Apply error explanation
    if isinstance(result, str) and result.startswith("Error:"):
        result = explain_error(name, result, args)

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
    session_id: str = "",
    turn_index: int = 0,
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
                    "session_id": session_id,
                    "turn_index": turn_index,
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


def _call_backend_stream(
    messages: list[dict],
    tools: list[dict],
    workspace_path: str,
    api_key: str,
    session_id: str = "",
    turn_index: int = 0,
    timeout: int = 120,
) -> Generator[dict, None, None]:
    """Streaming POST to /v1/chat. Yields SSE events as dicts."""
    server_url = get_server_url()

    try:
        with httpx.Client(timeout=timeout) as client:
            with client.stream("POST", f"{server_url}/v1/chat",
                headers=_request_headers(api_key),
                json={
                    "messages": messages,
                    "model": "auto",
                    "provider": "auto",
                    "tools": tools,
                    "stream": True,
                    "workspace_path": workspace_path,
                    "max_tokens": 2000,
                    "session_id": session_id,
                    "turn_index": turn_index,
                },
            ) as resp:
                if resp.status_code in ERROR_MESSAGES:
                    yield {"type": "error", "content": ERROR_MESSAGES[resp.status_code]}
                    return
                if resp.status_code != 200:
                    yield {"type": "error", "content": f"Server error ({resp.status_code})"}
                    return

                for line in resp.iter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if not data_str or data_str == "[DONE]":
                            continue
                        try:
                            event = _json.loads(data_str)
                            yield event
                        except _json.JSONDecodeError:
                            continue

    except httpx.ConnectError:
        yield {"type": "error", "content": "Cannot reach Rta server. Check your connection."}
    except httpx.TimeoutException:
        yield {"type": "error", "content": "Request timed out. Try again."}
    except Exception as e:
        yield {"type": "error", "content": f"Network error: {e}"}


def stream_agent(
    prompt: str,
    workspace_dir: str,
    messages: list[dict],
    provider: str = "rta",
    model_name: str = "auto",
    max_iterations: int = 20,
    think: bool = False,
    session_id: str = "",
    turn_index: int = 0,
    timeout: int = 120,
    force: bool = False,
    read_only: bool = False,
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
    if messages is None:
        messages = []
    
    # Ensure the new prompt is added if it's not already the most recent user message
    if prompt and (not messages or messages[-1].get("role") != "user" or messages[-1].get("content") != prompt):
        messages.append({"role": "user", "content": prompt})

    current_turn = turn_index
    for i in range(max_iterations):
        # Determine how many telemetry rows backend will insert
        last_msg = messages[-1] if messages else {}
        if last_msg.get("role") == "user":
            num_new_rows = 2
        else:
            num_tools = 0
            for m in reversed(messages):
                if m.get("role") == "tool":
                    num_tools += 1
                elif m.get("role") == "assistant":
                    break
            num_new_rows = num_tools + 1

        # Stream the LLM call
        text_buffer = ""
        tool_calls = None
        stream_usage = {}
        stream_error = None

        tools = [t for t in AVAILABLE_TOOLS if not read_only or t["function"]["name"] in READ_ONLY_TOOLS]
        for event in _call_backend_stream(
            messages=messages,
            tools=tools,
            workspace_path=workspace_dir,
            api_key=api_key,
            session_id=session_id,
            turn_index=current_turn,
            timeout=timeout,
        ):
            if event["type"] == "text":
                yield {"type": "text_chunk", "content": event["content"]}
                text_buffer += event["content"]
            elif event["type"] == "tool_calls":
                tool_calls = event["content"]
            elif event["type"] == "usage":
                stream_usage = event["content"]
            elif event["type"] == "provider":
                yield event
            elif event["type"] == "thought":
                yield event
            elif event["type"] == "error":
                stream_error = event["content"]
                yield {"type": "error", "content": stream_error}
                break
            elif event["type"] == "done":
                break

        if stream_error:
            return

        if not text_buffer and not tool_calls and not stream_usage:
            yield {"type": "error", "content": "Empty response from server (streaming not supported?)."}
            return

        current_turn += num_new_rows

        # Accumulate usage
        usage["prompt_tokens"]    += stream_usage.get("prompt_tokens", 0)
        usage["candidate_tokens"] += stream_usage.get("completion_tokens", 0)
        usage["total_tokens"]     += stream_usage.get("prompt_tokens", 0) + stream_usage.get("completion_tokens", 0)
        usage["cached_tokens"]    += stream_usage.get("cached_tokens", 0)

        # Yield full text for backward compatibility
        if text_buffer:
            yield {"type": "text", "content": text_buffer}

        # Append assistant turn
        assistant_msg: dict = {"role": "assistant"}
        if text_buffer:
            assistant_msg["content"] = text_buffer
        if tool_calls:
            assistant_msg["tool_calls"] = tool_calls
        messages.append(assistant_msg)

        if not tool_calls:
            yield {"type": "usage", "content": usage, "turn_index": current_turn}
            return

        # Execute tools, build tool result messages
        INDEPENDENT_TOOLS = {
            "get_files_info",
            "get_file_contents",
            "grep_search",
            "glob_search",
            "list_directory",
            "discover_project",
        }

        # Group tool calls: contiguous independent tools can run in parallel
        groups = []
        current_group = []
        for tc in tool_calls:
            name = tc.get("function", {}).get("name")
            if name in INDEPENDENT_TOOLS:
                current_group.append(tc)
            else:
                if current_group:
                    groups.append(("parallel", current_group))
                    current_group = []
                groups.append(("sequential", [tc]))
        if current_group:
            groups.append(("parallel", current_group))

        def execute_one(tc, force_flag=False, read_only_flag=False):
            fn = tc.get("function", {})
            name = fn.get("name")
            call_id = tc.get("id", "call_unknown")

            args = {}
            try:
                args = _json.loads(fn.get("arguments", "{}"))
            except Exception:
                pass

            import time as _time
            from rta_cli.ui import Console
            console = Console()
            
            max_retries = 2
            allow_ignored = False
            allow_hidden = False
            
            for attempt in range(max_retries + 1):
                # Pass flags if they've been granted
                if allow_ignored:
                    args["allow_ignored"] = True
                if allow_hidden:
                    args["allow_hidden"] = True

                result = call_function({"name": name, "args": args}, workspace_dir, default_timeout=timeout, force=force_flag, read_only=read_only_flag)
                content = str(result["functionResponse"]["response"]["content"])
                
                # Check for permission requirement
                if "(PERMISSION_REQUIRED)" in content and not force_flag:
                    path_match = content.split("Error : ")[1].split(" is ignored")[0] if "Error : " in content else "this path"
                    console.print(f"\n[bold yellow][?] The agent wants to access ignored path: {path_match}[/bold yellow]")
                    choice = console.input("[bold]Allow access? (y/N): [/bold]").strip().lower()
                    if choice == 'y':
                        allow_ignored = True
                        continue # Retry
                    else:
                        return {
                            "role": "tool",
                            "tool_call_id": call_id,
                            "name": name,
                            "content": f"Error: Permission denied by user to access ignored path: {path_match}",
                        }

                if "(HIDDEN_CONTENT_PERMISSION_REQUIRED)" in content and not force_flag:
                    skill_name = content.split("Skill '")[1].split("' contains")[0] if "Skill '" in content else "this skill"
                    console.print(f"\n[bold red][!] SECURITY WARNING: Skill '{skill_name}' contains hidden HTML comments.[/bold red]")
                    console.print("[dim]Hidden content can be used for malicious prompt injection.[/dim]")
                    choice = console.input("[bold]Activate anyway? (y/N): [/bold]").strip().lower()
                    if choice == 'y':
                        allow_hidden = True
                        continue # Retry
                    else:
                        return {
                            "role": "tool",
                            "tool_call_id": call_id,
                            "name": name,
                            "content": f"Error: Activation denied by user for skill '{skill_name}' due to hidden content.",
                        }

                # Check for transient failure (timeout)
                is_transient = "timed out" in content.lower()
                
                if is_transient and attempt < max_retries:
                    # Exponential backoff: 1s, 2s
                    _time.sleep(2**attempt)
                    continue
                break

            return {
                "role": "tool",
                "tool_call_id": call_id,
                "name": name,
                "content": content,
            }

        for mode, group_tcs in groups:
            if mode == "parallel" and len(group_tcs) > 1:
                for tc in group_tcs:
                    name = tc.get("function", {}).get("name")
                    args = tc.get("function", {}).get("arguments", "{}")
                    yield {"type": "tool_start", "content": name, "arguments": args}
                
                with ThreadPoolExecutor(max_workers=min(len(group_tcs), 10)) as executor:
                    results = list(executor.map(lambda tc: execute_one(tc, force, read_only), group_tcs))
                    messages.extend(results)
            else:
                for tc in group_tcs:
                    name = tc.get("function", {}).get("name")
                    args = tc.get("function", {}).get("arguments", "{}")
                    yield {"type": "tool_start", "content": name, "arguments": args}
                    res = execute_one(tc, force, read_only)
                    messages.append(res)

    yield {"type": "error", "content": "Max iterations reached."}
    yield {"type": "usage", "content": usage, "turn_index": current_turn}


def run_agent(
    prompt: str,
    workspace_dir: str,
    messages: list[dict],
    provider: str = "rta",
    model_name: str = "auto",
    max_iterations: int = 20,
    think: bool = False,
    session_id: str = "",
    turn_index: int = 0,
    timeout: int = 120,
    force: bool = False,
) -> tuple[str, dict, int]:
    """Compatibility wrapper: collects stream_agent events → (text, usage, turn_index)."""
    final_text = ""
    last_usage: dict = {}
    last_turn = turn_index

    for event in stream_agent(prompt, workspace_dir, messages, provider, model_name, max_iterations, think, session_id, turn_index, timeout=timeout, force=force):
        if event["type"] == "text":
            final_text += event["content"] + "\n\n"
        elif event["type"] == "tool_start":
            args = event.get("arguments", "")
            if args and args != "{}":
                final_text += f"*(Executed tool: `{event['content']}` with args: `{args}`)*\n\n"
            else:
                final_text += f"*(Executed tool: `{event['content']}`)*\n\n"
        elif event["type"] == "thought":
            final_text += f"> *{event['content']}*\n\n"
        elif event["type"] == "usage":
            last_usage = event["content"]
            last_turn = event.get("turn_index", last_turn)
        elif event["type"] == "error":
            return f"Error: {event['content']}", {}, last_turn

    return final_text.strip(), last_usage, last_turn
