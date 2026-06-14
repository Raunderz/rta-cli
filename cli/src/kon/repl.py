"""Minimal REPL mode: type messages, see streaming text, run tools. No TUI."""

import asyncio
import signal
import sys

from kon import config, get_config

from .core.types import StopReason
from .events import (
    AgentEndEvent,
    CompactionEndEvent,
    CompactionStartEvent,
    ErrorEvent,
    InterruptedEvent,
    TextDeltaEvent,
    ToolApprovalEvent,
    ToolEndEvent,
    ToolResultEvent,
    ToolStartEvent,
    TurnEndEvent,
    WarningEvent,
)
from .llm import get_model
from .llm.base import AuthMode
from .permissions import ApprovalResponse
from .runtime import ConversationRuntime
from .tools import DEFAULT_TOOLS, EXTRA_TOOLS, get_tools
from .version import VERSION


class ReplState:
    """Tracks REPL session state for slash commands."""

    def __init__(self, runtime: ConversationRuntime) -> None:
        self.runtime = runtime
        self.agent = runtime.agent
        self.session = runtime.session


def _print_banner(model: str, cwd: str, session_id: str) -> None:
    short_id = session_id[:8]
    print(f"rta {VERSION} | {model} | {cwd}")
    print(f"Session: {short_id}")
    print()


def _print_exit(session_id: str) -> None:
    short_id = session_id[:8]
    print(f"\nSession saved. Resume with: rta --resume {short_id}")


def _handle_slash(line: str, state: ReplState) -> bool:
    """Handle slash commands. Returns True if handled."""
    parts = line.split(None, 1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else None

    if cmd == "/help":
        print("Commands:")
        print("  /help              Show this help")
        print("  /clear             Start a new session")
        print("  /model [name]      Show or switch model")
        print("  /compact           Compress context window")
        print("  /thinking [level]  Show or set thinking level")
        print("  /exit              Exit (same as Ctrl+D)")
        return True

    if cmd == "/clear":
        state.runtime.new_session(reload_context=True)
        state.agent = state.runtime.agent
        state.session = state.runtime.session
        print(f"New session: {state.session.id[:8]}")
        return True

    if cmd == "/model":
        if arg:
            target = arg.strip()
            model_info = get_model(target)
            if model_info is None:
                print(f"Unknown model: {target}")
                print("Use /model to see available models.")
                return True

            state.runtime.switch_model(model_info)
            state.agent = state.runtime.agent
            print(f"Switched to {target}")
        else:
            current = state.runtime.model
            print(f"Current model: {current}")
            print("Usage: /model <model-name>")
        return True

    if cmd == "/compact":
        try:
            result = asyncio.run(state.runtime.compact_now())
            print(f"Compacted ({result.tokens_before} tokens)")
        except Exception as e:
            print(f"Compaction failed: {e}")
        return True

    if cmd == "/thinking":
        if arg:
            level = arg.strip()
            state.runtime.set_thinking_level(level)
            print(f"Thinking level: {level}")
        else:
            print(f"Current thinking level: {state.runtime.thinking_level}")
            print("Usage: /thinking <none|brief|verbose>")
        return True

    if cmd == "/exit":
        return False

    print(f"Unknown command: {cmd}")
    print("Type /help for available commands.")
    return True


async def _run_turn(
    state: ReplState,
    query: str,
    cancel_event: asyncio.Event,
) -> StopReason:
    """Run a single user turn and consume events. Returns the stop reason."""
    stop = StopReason.STOP

    async for event in state.agent.run(query, cancel_event=cancel_event):
        match event:
            case TextDeltaEvent(delta=delta):
                print(delta, end="", flush=True)

            case ToolStartEvent(tool_name=name):
                print(f"\n  [{name}]", end="", flush=True)

            case ToolEndEvent(tool_name=name, display=display):
                if display:
                    print(f" {display[:80]}")

            case ToolResultEvent(tool_name=name, result=result):
                if result and result.is_error:
                    output = result.output[:200] if result.output else ""
                    print(f"  error: {output}")

            case ToolApprovalEvent(tool_name=name, display=display, future=future):
                if future is None:
                    continue
                # Check permission mode
                perm_cfg = get_config().permissions
                if perm_cfg.mode == "auto":
                    future.set_result(ApprovalResponse.DENY)
                    print(f"\n  [{name}] denied (auto mode)")
                    continue
                print(f"\n  [{name}] {display}")
                try:
                    resp = input("  Approve? [y/N]: ").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    future.set_result(ApprovalResponse.DENY)
                    print(" Denied")
                    continue
                if resp in ("y", "yes"):
                    future.set_result(ApprovalResponse.APPROVE)
                    print("  Approved")
                else:
                    future.set_result(ApprovalResponse.DENY)
                    print("  Denied")

            case TurnEndEvent():
                pass

            case CompactionStartEvent():
                print("\n  [compacting context...]", end="", flush=True)

            case CompactionEndEvent(tokens_before=tokens, aborted=aborted):
                if aborted:
                    print(" failed")
                else:
                    print(f" done ({tokens} tokens)")

            case ErrorEvent(error=error):
                print(f"\nError: {error}")

            case WarningEvent(warning=warning):
                print(f"\nWarning: {warning}")

            case InterruptedEvent():
                print("\nInterrupted.")
                return StopReason.INTERRUPTED

            case AgentEndEvent(stop_reason=sr):
                stop = sr

    return stop


async def _repl_loop(state: ReplState) -> None:
    """Main REPL loop: read input, run turns, handle commands."""
    cancel_event = asyncio.Event()

    def handle_sigint(sig, frame):
        if cancel_event.is_set():
            # Second Ctrl+C: exit
            _print_exit(state.session.id)
            sys.exit(0)
        cancel_event.set()

    original_sigint = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, handle_sigint)

    try:
        while True:
            cancel_event.clear()
            try:
                line = input("\033[1;36m>\033[0m ").strip()
            except EOFError:
                break
            except KeyboardInterrupt:
                print("\nInterrupted. Press Ctrl+D to exit.")
                continue

            if not line:
                continue

            if line.startswith("/"):
                if not _handle_slash(line, state):
                    break
                continue

            stop = await _run_turn(state, line, cancel_event)
            if stop == StopReason.INTERRUPTED:
                continue
    finally:
        signal.signal(signal.SIGINT, original_sigint)


def run_repl(
    *,
    model: str | None,
    provider: str | None,
    api_key: str | None,
    base_url: str | None,
    openai_compat_auth_mode: AuthMode | None,
    anthropic_compat_auth_mode: AuthMode | None,
    extra_tools: list[str] | None,
    resume_session: str | None = None,
    continue_recent: bool = False,
) -> int:
    """Entry point for REPL mode."""
    import os

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

    merged = list(dict.fromkeys(config.tools.extra + (extra_tools or [])))
    for name in merged:
        if name not in EXTRA_TOOLS:
            print(f"Warning: unknown extra tool: {name!r}", file=sys.stderr)
    extras = [n for n in merged if n in EXTRA_TOOLS]
    tools = get_tools(DEFAULT_TOOLS + extras)

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

    try:
        init = runtime.initialize(
            resume_session=resume_session, continue_recent=continue_recent
        )
        if init.provider_error:
            print(f"Error: {init.provider_error}", file=sys.stderr)
            return 2

        agent = runtime.prepare_for_run()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    if agent is None or runtime.session is None:
        print("Error: agent initialization failed", file=sys.stderr)
        return 2

    state = ReplState(runtime)
    _print_banner(runtime.model, os.getcwd(), runtime.session.id)

    try:
        asyncio.run(_repl_loop(state))
    except KeyboardInterrupt:
        pass
    finally:
        _print_exit(runtime.session.id)

    return 0
