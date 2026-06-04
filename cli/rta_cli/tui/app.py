from __future__ import annotations

import asyncio
from typing import ClassVar

from textual.app import App, ComposeResult
from textual.containers import Vertical
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
from .widgets import InfoBar


class RtaApp(App):
    CSS = """
    Screen {
        background: $surface;
    }

    ChatLog {
        height: 1fr;
        border: none;
        background: $surface;
    }

    ChatLog > .user-block {
        padding: 0 1;
        margin: 0 0 0 0;
    }

    ChatLog > .thinking-block {
        padding: 0 1;
        margin: 0 0 0 0;
    }

    ChatLog > .content-block {
        padding: 0 1;
        margin: 0 0 0 0;
    }

    ChatLog > .tool-block {
        padding: 0 1;
        margin: 0 0 0 0;
    }

    Input {
        dock: bottom;
        margin: 0 1 1 1;
    }

    InfoBar {
        dock: bottom;
        height: 1;
        background: $panel;
    }
    """

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
        self._current_turn = 0
        self._pending_approval: ToolApprovalEvent | None = None

    def compose(self) -> ComposeResult:
        with Vertical():
            yield ChatLog(id="chat-log")
            yield Input(placeholder="Type a message...", id="input-box")
            yield InfoBar(cwd=self._cwd, model=self._model, id="info-bar")

    def on_mount(self) -> None:
        self.title = f"RTA — {self._cwd}"

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if self._agent_busy:
            return
        prompt = event.value.strip()
        if not prompt:
            return
        self.query_one("#input-box", Input).value = ""
        self.query_one("#input-box", Input).disabled = True
        self._agent_busy = True
        asyncio.create_task(self._run_turn(prompt))

    async def _run_turn(self, prompt: str) -> None:
        chat_log = self.query_one("#chat-log", ChatLog)
        info_bar = self.query_one("#info-bar", InfoBar)

        chat_log.add_user_message(prompt)

        self._cancel_event = asyncio.Event()
        self._pending_approval = None

        total_in = 0
        total_out = 0

        try:
            async for event in self._agent.run_turn(
                prompt, cancel_event=self._cancel_event
            ):
                self._handle_event(event, chat_log, info_bar)

                if isinstance(event, UsageEvent):
                    total_in = event.prompt_tokens
                    total_out = event.completion_tokens
                    info_bar.update_tokens(total_in, total_out)
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
