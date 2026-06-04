from __future__ import annotations

import asyncio
from typing import ClassVar

from textual.app import App, ComposeResult
from textual.widgets import Input

from ..core.events import (
    ErrorEvent,
    TextDeltaEvent,
    TextEndEvent,
    ThinkingDeltaEvent,
    ThinkingEndEvent,
    ThinkingStartEvent,
    ToolApprovalEvent,
    ToolArgsDeltaEvent,
    ToolEndEvent,
    ToolResultEvent,
    ToolStartEvent,
    TurnEndEvent,
    UsageEvent,
    WarningEvent,
)
from ..core.loop import Agent
from ..core.permissions import ApprovalResponse
from .chat import ChatLog
from .styles import get_styles
from .widgets import InfoBar


class RtaApp(App):
    CSS = get_styles()

    BINDINGS: ClassVar[list] = [
        ("ctrl+c", "handle_ctrl_c", "Interrupt/Exit"),
        ("ctrl+q", "quit", "Quit"),
        ("escape", "interrupt", "Interrupt"),
        ("y", "approve_tool", "Approve"),
        ("n", "deny_tool", "Deny"),
    ]

    def __init__(
        self,
        agent: Agent,
        cwd: str = "",
        model: str = "",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._agent = agent
        self._cwd = cwd
        self._model = model
        self._agent_busy = False
        self._cancel_event: asyncio.Event | None = None
        self._pending_approval: ToolApprovalEvent | None = None

    def compose(self) -> ComposeResult:
        yield ChatLog(id="chat-log")
        yield Input(placeholder="Type a message...", id="input-box")
        yield InfoBar(cwd=self._cwd, model=self._model, id="info-bar")

    def on_mount(self) -> None:
        self.title = f"RTA — {self._cwd}"

    def on_input_submitted(self, event: Input.Submitted) -> None:
        prompt = event.value.strip()
        if not prompt:
            return

        self.query_one("#input-box", Input).value = ""

        if prompt.startswith("/") and self._handle_command(prompt):
            return

        if self._agent_busy:
            return

        self.query_one("#input-box", Input).disabled = True
        self._agent_busy = True
        asyncio.create_task(self._run_turn(prompt))

    def _handle_command(self, text: str) -> bool:
        parts = text[1:].split(maxsplit=1)
        cmd = parts[0] if parts else ""
        args = parts[1] if len(parts) > 1 else ""

        chat_log = self.query_one("#chat-log", ChatLog)

        if cmd in ("exit", "quit", "q"):
            self.exit()
            return True

        if cmd == "help":
            self._show_help(chat_log)
            return True

        if cmd == "clear":
            self._clear_conversation(chat_log)
            return True

        if cmd == "theme":
            self._handle_theme_command(args, chat_log)
            return True

        if cmd == "model":
            chat_log.add_user_message(f"[System] Current model: {self._model}")
            chat_log.scroll_to_bottom()
            return True

        return False

    def _show_help(self, chat_log: ChatLog) -> None:
        help_text = (
            "Commands:\n"
            "  /help     Show this help\n"
            "  /clear    Clear conversation\n"
            "  /theme    List or switch themes\n"
            "  /model    Show current model\n"
            "  /exit     Exit the app\n"
            "\n"
            "Keybindings:\n"
            "  Ctrl+C    Interrupt/Exit\n"
            "  Ctrl+Q    Quit\n"
            "  Escape    Interrupt\n"
            "  y/n       Approve/Deny tool"
        )
        chat_log.add_user_message(f"[System]\n{help_text}")
        chat_log.scroll_to_bottom()

    def _clear_conversation(self, chat_log: ChatLog) -> None:
        chat_log.clear()
        self._agent.messages = []
        chat_log.add_user_message("[System] Conversation cleared")
        chat_log.scroll_to_bottom()

    def _handle_theme_command(self, args: str, chat_log: ChatLog) -> None:
        from .themes import get_current_theme_id, get_theme_options, set_theme

        if args:
            try:
                set_theme(args)
                type(self).CSS = get_styles()
                self.refresh_css()
                chat_log.add_user_message(f"[System] Theme: {args}")
            except ValueError:
                chat_log.add_user_message(f"[System] Unknown theme: {args}")
        else:
            lines = ["Themes:"]
            for tid, label in get_theme_options():
                marker = "●" if tid == get_current_theme_id() else " "
                lines.append(f"  {marker} {tid} - {label}")
            lines.append("\nUsage: /theme <id>")
            chat_log.add_user_message("\n".join(lines))
        chat_log.scroll_to_bottom()

    async def _run_turn(self, prompt: str) -> None:
        chat_log = self.query_one("#chat-log", ChatLog)
        info_bar = self.query_one("#info-bar", InfoBar)

        chat_log.add_user_message(prompt)

        self._cancel_event = asyncio.Event()
        self._pending_approval = None

        try:
            async for event in self._agent.run_turn(
                prompt, cancel_event=self._cancel_event
            ):
                self._handle_event(event, chat_log, info_bar)

                if isinstance(event, UsageEvent):
                    info_bar.update_tokens(event.prompt_tokens, event.completion_tokens)
                elif isinstance(event, TurnEndEvent):
                    if event.usage:
                        info_bar.update_tokens(
                            event.usage.input_tokens, event.usage.output_tokens
                        )
                    chat_log.finalize_thinking()
                    chat_log.finalize_content()
        except Exception as e:
            chat_log.mount(_error_block(f"Error: {e}"))
        finally:
            self._agent_busy = False
            self._cancel_event = None
            self._pending_approval = None
            self.query_one("#input-box", Input).disabled = False
            self.query_one("#input-box", Input).focus()
            chat_log.scroll_to_bottom()

    def _handle_event(self, event, chat_log: ChatLog, info_bar: InfoBar) -> None:
        if isinstance(event, ThinkingStartEvent):
            chat_log.start_thinking()

        elif isinstance(event, ThinkingDeltaEvent):
            if chat_log._current_thinking:
                asyncio.ensure_future(chat_log._current_thinking.append(event.delta))

        elif isinstance(event, ThinkingEndEvent):
            chat_log.finalize_thinking()

        elif isinstance(event, TextDeltaEvent):
            if not chat_log._current_content:
                chat_log.start_content()
            if chat_log._current_content:
                asyncio.ensure_future(chat_log._current_content.append(event.delta))

        elif isinstance(event, TextEndEvent):
            chat_log.finalize_content()

        elif isinstance(event, ToolStartEvent):
            chat_log.start_tool(event.tool_call_id, event.name)

        elif isinstance(event, ToolApprovalEvent):
            self._pending_approval = event
            tool = chat_log.get_tool(event.tool_call_id)
            if tool:
                tool.show_approval(event.display)

        elif isinstance(event, ToolArgsDeltaEvent):
            tool = chat_log.get_tool(event.tool_call_id)
            if tool:
                tool.set_args(event.delta)

        elif isinstance(event, ToolEndEvent):
            tool = chat_log.get_tool(event.tool_call_id)
            if tool:
                tool.set_args(event.arguments)

        elif isinstance(event, ToolResultEvent):
            tool = chat_log.get_tool(event.tool_call_id)
            if tool:
                result_text = event.result.result if event.result else ""
                success = event.result.success if event.result else True
                tool.set_result(result_text, success)

        elif isinstance(event, WarningEvent):
            chat_log.mount(_warning_block(event.warning))

        elif isinstance(event, ErrorEvent):
            chat_log.mount(_error_block(f"{event.message}: {event.details or ''}"))

    def action_handle_ctrl_c(self) -> None:
        if self._agent_busy and self._cancel_event:
            self._cancel_event.set()
        else:
            self.exit()

    def action_interrupt(self) -> None:
        if self._agent_busy and self._cancel_event:
            self._cancel_event.set()

    def action_quit(self) -> None:
        self.exit()

    def action_approve_tool(self) -> None:
        if self._pending_approval:
            future = self._pending_approval.get_future()
            if future and not future.done():
                future.set_result(ApprovalResponse.APPROVE)
            self._pending_approval = None

    def action_deny_tool(self) -> None:
        if self._pending_approval:
            future = self._pending_approval.get_future()
            if future and not future.done():
                future.set_result(ApprovalResponse.DENY)
            self._pending_approval = None


def _warning_block(text: str):
    from .blocks import UserBlock

    return UserBlock(content=f"⚠ {text}")


def _error_block(text: str):
    from .blocks import UserBlock

    return UserBlock(content=f"✗ {text}")
