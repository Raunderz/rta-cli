from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.widgets import Label, Static


class UserBlock(Static):
    ALLOW_SELECT = True
    can_focus = False

    def __init__(self, content: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._content = content
        self.add_class("user-block")

    def compose(self) -> ComposeResult:
        text = Text()
        text.append("You  ", style="bold green")
        text.append(self._content)
        yield Label(text, id="user-text", markup=False)


class _StreamingMixin:
    _pending: str
    _completed: str
    _content: str
    _finalized: bool

    def _init_streaming(self) -> None:
        self._pending = ""
        self._completed = ""
        self._content = ""

    def _append_streaming(self, text: str) -> None:
        self._content += text
        self._pending += text
        last_nl = self._pending.rfind("\n")
        if last_nl != -1:
            self._completed += self._pending[: last_nl + 1]
            self._pending = self._pending[last_nl + 1 :]
        self._schedule_streaming_update()

    def _schedule_streaming_update(self) -> None:
        self.call_after_refresh(self._flush_streaming_update)

    def _flush_streaming_update(self) -> None:
        display = self._render_streaming_display()
        self._streaming_update_label(display)

    def _render_streaming_display(self) -> Text:
        display = Text()
        if self._completed:
            display.append(self._completed)
        if self._pending:
            if self._completed:
                display.append("\n")
            display.append(self._pending, style="italic")
        return display

    def _streaming_update_label(self, display: Text) -> None:
        raise NotImplementedError


class ThinkingBlock(_StreamingMixin, Static):
    ALLOW_SELECT = True
    can_focus = False

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._init_streaming()
        self._label: Label | None = None
        self.add_class("thinking-block")

    def compose(self) -> ComposeResult:
        header = Text()
        header.append("  🤔", style="bold yellow")
        header.append(" Thinking...", style="italic dim")
        yield Label(header, id="thinking-header", markup=False)
        yield Label("", id="thinking-content", markup=False)

    @property
    def _label_widget(self) -> Label:
        if self._label is None:
            self._label = self.query_one("#thinking-content", Label)
        return self._label

    def _streaming_update_label(self, display: Text) -> None:
        self._label_widget.update(display)

    async def append(self, text: str) -> None:
        self._append_streaming(text)

    def finalize(self, collapse: bool = False) -> None:
        self._finalized = True
        display = Text()
        if self._content:
            lines = self._content.strip().split("\n")
            visible = lines[:5] if collapse else lines
            for i, line in enumerate(visible):
                if i > 0:
                    display.append("\n")
                display.append(line.strip(), style="italic dim")
            remaining = len(lines) - len(visible)
            if remaining > 0 and collapse:
                display.append(f" ... ({remaining} more lines)", style="italic dim")
        self._label_widget.update(display)


class ContentBlock(_StreamingMixin, Static):
    ALLOW_SELECT = True
    can_focus = False

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._init_streaming()
        self._label: Label | None = None
        self.add_class("content-block")

    def compose(self) -> ComposeResult:
        header = Text()
        header.append("  ✦", style="bold cyan")
        yield Label(header, id="content-header", markup=False)
        yield Label("", id="content-text", markup=False)

    @property
    def _label_widget(self) -> Label:
        if self._label is None:
            self._label = self.query_one("#content-text", Label)
        return self._label

    def _streaming_update_label(self, display: Text) -> None:
        self._label_widget.update(display)

    async def append(self, text: str) -> None:
        self._append_streaming(text)

    def finalize(self) -> None:
        self._finalized = True
        if self._content:
            self._label_widget.update(self._content)


class ToolBlock(Static):
    ALLOW_SELECT = True
    can_focus = False

    def __init__(self, tool_call_id: str, name: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._tool_call_id = tool_call_id
        self._name = name
        self._args_text = ""
        self._result_text = ""
        self._success: bool | None = None
        self._header: Label | None = None
        self._body: Label | None = None
        self.add_class("tool-block")

    def compose(self) -> ComposeResult:
        header = Text()
        header.append("  → ", style="bold")
        header.append(self._name, style="bold blue")
        header.append("  ...", style="dim")
        yield Label(header, id=f"tool-header-{self._tool_call_id}", markup=False)
        yield Label("", id=f"tool-body-{self._tool_call_id}", markup=False)

    def _get_header(self) -> Label:
        if self._header is None:
            self._header = self.query_one(f"#tool-header-{self._tool_call_id}", Label)
        return self._header

    def _get_body(self) -> Label:
        if self._body is None:
            self._body = self.query_one(f"#tool-body-{self._tool_call_id}", Label)
        return self._body

    def show_approval(self, preview: str | None = None) -> None:
        header = Text()
        header.append("  △ ", style="bold yellow")
        header.append(self._name, style="bold blue")
        header.append("  Permission required [y/n]", style="bold yellow")
        self._get_header().update(header)
        if preview:
            self._get_body().update(preview[:300])

    def set_args(self, text: str) -> None:
        self._args_text = text

    def set_result(self, result: str, success: bool) -> None:
        self._success = success
        self._result_text = result
        header = Text()
        header.append("  → ", style="bold")
        header.append(self._name, style="bold blue")
        status = " ✓" if success else " ✗"
        status_style = "bold green" if success else "bold red"
        header.append(status, style=status_style)
        self._get_header().update(header)
        if result:
            body = Text()
            body.append(result[:500])
            if len(result) > 500:
                body.append(f"\n... ({len(result) - 500} more chars)")
            self._get_body().update(body)
