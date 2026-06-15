"""JSON-lines pipe mode for IDE integration (--stdio flag)."""

import asyncio
import json
import logging
import sys
import threading
from typing import Any

from .events import (
    AgentEndEvent,
    ErrorEvent,
    InterruptedEvent,
    TextDeltaEvent,
    ToolApprovalEvent,
    ToolEndEvent,
    ToolStartEvent,
)
from .permissions import ApprovalResponse
from .runtime import ConversationRuntime
from .tools import DEFAULT_TOOLS, EXTRA_TOOLS, get_tools
from .version import VERSION

logger = logging.getLogger("kon.stdio")


def _write_response(obj: dict[str, Any]) -> None:
    """Write a single JSON line to stdout via raw fd and flush."""
    import os

    line = json.dumps(obj, ensure_ascii=False) + "\n"
    try:
        os.write(1, line.encode("utf-8"))
    except OSError:
        pass


def _stdin_reader(queue: asyncio.Queue[str | None], loop: asyncio.AbstractEventLoop) -> None:
    """Read lines from stdin via raw fd reads (bypasses pipe buffering)."""
    import os

    buf = b""
    _dbg = open(os.path.expanduser("~/.rta/stdio_debug.log"), "a")
    _dbg.write("stdin reader thread started, fd=0\n")
    _dbg.flush()
    while True:
        try:
            chunk = os.read(0, 4096)
            _dbg.write(f"stdin read: {len(chunk)} bytes\n")
            _dbg.flush()
            if not chunk:
                break
            buf += chunk
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                decoded = line.decode("utf-8", errors="replace").strip()
                if decoded:
                    _dbg.write(f"stdin line: {decoded[:200]}\n")
                    _dbg.flush()
                    loop.call_soon_threadsafe(queue.put_nowait, decoded)
        except (EOFError, OSError) as e:
            _dbg.write(f"stdin reader error: {e}\n")
            _dbg.flush()
            break
    _dbg.write("stdin reader thread exiting\n")
    _dbg.flush()
    loop.call_soon_threadsafe(queue.put_nowait, None)  # sentinel: stdin closed


async def run_stdio_mode(
    *,
    model: str | None,
    provider: str | None,
    api_key: str | None,
    base_url: str | None,
    openai_compat_auth_mode: Any,
    anthropic_compat_auth_mode: Any,
    extra_tools: list[str] | None,
    resume_session: str | None = None,
    continue_recent: bool = False,
) -> int:
    """Entry point for stdio JSON-lines mode."""
    import os
    import sys

    _dbg = open(os.path.expanduser("~/.rta/stdio_debug.log"), "a")
    _dbg.write("stdio: run_stdio_mode entered\n")
    _dbg.flush()

    from kon import config

    initial_model = model or config.llm.default_model
    initial_provider = (
        provider
        if provider is not None
        else (config.llm.default_provider if model is None else None)
    )
    base = base_url or config.llm.default_base_url or None
    thinking = config.llm.default_thinking_level
    openai_auth = openai_compat_auth_mode or config.llm.auth.openai_compat
    anthropic_auth = anthropic_compat_auth_mode or config.llm.auth.anthropic_compat

    _dbg.write(f"stdio: model={initial_model} provider={initial_provider}\n")
    _dbg.flush()

    merged = list(dict.fromkeys(config.tools.extra + (extra_tools or [])))
    extras = [n for n in merged if n in EXTRA_TOOLS]
    tools = get_tools(DEFAULT_TOOLS + extras)

    _dbg.write("stdio: creating runtime\n")
    _dbg.flush()

    runtime = ConversationRuntime(
        cwd=os.getcwd(),
        model=initial_model,
        model_provider=initial_provider,
        api_key=api_key,
        base_url=base,
        thinking_level=thinking,
        tools=tools,
        openai_compat_auth_mode=openai_auth,
        anthropic_compat_auth_mode=anthropic_auth,
    )

    _dbg.write("stdio: initializing runtime...\n")
    _dbg.flush()

    init = runtime.initialize(
        resume_session=resume_session, continue_recent=continue_recent
    )

    _dbg.write(f"stdio: runtime initialized, provider_error={init.provider_error}\n")
    _dbg.flush()

    if init.provider_error:
        _write_response({"type": "error", "message": init.provider_error})
        return 2

    agent = runtime.prepare_for_run()
    if agent is None or runtime.session is None:
        _write_response({"type": "error", "message": "Agent initialization failed"})
        return 2

    _dbg.write("stdio: agent ready, writing status_response\n")
    _dbg.flush()

    _write_response({
        "type": "status_response",
        "version": VERSION,
        "model": runtime.model,
        "session_id": runtime.session.id,
    })

    # Start background thread to read stdin lines
    line_queue: asyncio.Queue[str | None] = asyncio.Queue()
    loop = asyncio.get_running_loop()
    stdin_thread = threading.Thread(target=_stdin_reader, args=(line_queue, loop), daemon=True)
    stdin_thread.start()

    logger.info("stdio loop started, waiting for stdin")
    _dbg.write("stdio loop started, waiting for stdin\n")
    _dbg.flush()

    # Track pending approvals: approval_id -> Future
    pending_approvals: dict[str, asyncio.Future[ApprovalResponse]] = {}
    cancel_event = asyncio.Event()

    try:
        while True:
            raw_line = await line_queue.get()
            if raw_line is None:
                break  # stdin closed

            if not raw_line.strip():
                continue

            logger.info("stdin: %s", raw_line[:200])

            try:
                request = json.loads(raw_line)
            except json.JSONDecodeError as e:
                _write_response({"type": "error", "message": f"Invalid JSON: {e}"})
                continue

            req_type = request.get("type")

            _dbg.write(f"request type: {req_type}\n")
            _dbg.flush()

            if req_type == "chat":
                cancel_event.clear()
                message = request.get("message", "")
                session_id = request.get("session_id")

                _dbg.write(f"chat: session_id={session_id} runtime_session={runtime.session.id if runtime.session else None}\n")
                _dbg.flush()

                if session_id and runtime.session and session_id != runtime.session.id:
                    try:
                        runtime.load_session(session_id)
                        agent = runtime.prepare_for_run()
                    except Exception as e:
                        _write_response({"type": "error", "message": f"Session error: {e}"})
                        continue

                await _run_chat(agent, runtime, message, cancel_event, pending_approvals, dbg=_dbg)

            elif req_type == "cancel":
                cancel_event.set()

            elif req_type == "status":
                _write_response({
                    "type": "status_response",
                    "version": VERSION,
                    "model": runtime.model,
                    "session_id": runtime.session.id,
                })

            elif req_type == "tool_approved":
                approval_id = request.get("approval_id", "")
                future = pending_approvals.pop(approval_id, None)
                if future and not future.done():
                    future.set_result(ApprovalResponse.APPROVE)

            elif req_type == "tool_denied":
                approval_id = request.get("approval_id", "")
                future = pending_approvals.pop(approval_id, None)
                if future and not future.done():
                    future.set_result(ApprovalResponse.DENY)

            else:
                _write_response({"type": "error", "message": f"Unknown request type: {req_type}"})

    except asyncio.CancelledError:
        pass
    finally:
        cancel_event.set()
        for future in pending_approvals.values():
            if not future.done():
                future.set_result(ApprovalResponse.DENY)

    return 0


async def _run_chat(
    agent: Any,
    runtime: ConversationRuntime,
    query: str,
    cancel_event: asyncio.Event,
    pending_approvals: dict[str, asyncio.Future[ApprovalResponse]],
    dbg: Any = None,
) -> None:
    """Run a single chat turn and stream events as JSON-lines."""
    tokens_used = 0

    if dbg:
        dbg.write(f"_run_chat called, query={query[:100]}\n")
        dbg.flush()

    try:
        async for event in agent.run(query, cancel_event=cancel_event):
            if dbg:
                dbg.write(f"event: {type(event).__name__}\n")
                dbg.flush()

            match event:
                case TextDeltaEvent(delta=delta):
                    _write_response({"type": "text_delta", "content": delta})

                case ToolStartEvent(tool_name=name):
                    _write_response({"type": "tool_start", "tool": name})

                case ToolEndEvent(tool_name=name, display=display):
                    _write_response({"type": "tool_end", "tool": name, "display": display})

                case ToolApprovalEvent(tool_name=name, display=display, future=future):
                    if future is None:
                        continue

                    from kon import get_config

                    perm_cfg = get_config().permissions
                    if perm_cfg.mode == "auto":
                        future.set_result(ApprovalResponse.DENY)
                        _write_response({
                            "type": "tool_denied",
                            "tool": name,
                            "display": display,
                            "approval_id": "",
                        })
                        continue

                    import uuid

                    approval_id = uuid.uuid4().hex[:12]
                    pending_approvals[approval_id] = future
                    _write_response({
                        "type": "tool_approval",
                        "tool": name,
                        "display": display,
                        "approval_id": approval_id,
                    })

                case ErrorEvent(error=error):
                    _write_response({"type": "error", "message": error})

                case InterruptedEvent():
                    _write_response({"type": "error", "message": "Interrupted"})
                    return

                case AgentEndEvent(total_usage=usage):
                    if usage:
                        tokens_used = usage.input_tokens + usage.output_tokens
                    _write_response({
                        "type": "text_done",
                        "session_id": runtime.session.id if runtime.session else "",
                        "tokens_used": tokens_used,
                    })
    except Exception as e:
        if dbg:
            dbg.write(f"_run_chat error: {e}\n")
            dbg.flush()
        _write_response({"type": "error", "message": str(e)})
