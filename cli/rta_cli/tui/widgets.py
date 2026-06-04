from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Label


class InfoBar(Horizontal):
    can_focus = False

    def __init__(
        self,
        cwd: str = "",
        model: str = "",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._cwd = cwd
        self._model = model
        self._input_tokens = 0
        self._output_tokens = 0
        self._label: Label | None = None

    def compose(self) -> ComposeResult:
        yield Label(self._render_text(), id="info-text", markup=False)

    def _get_label(self) -> Label:
        if self._label is None:
            self._label = self.query_one("#info-text", Label)
        return self._label

    def _render_text(self) -> Text:
        text = Text()
        text.append(f" {self._cwd}", style="dim")
        if self._model:
            text.append(" | model: ", style="dim")
            text.append(self._model, style="bold cyan")
        if self._input_tokens or self._output_tokens:
            text.append(" | in: ", style="dim")
            text.append(str(self._input_tokens), style="green")
            text.append(" out: ", style="dim")
            text.append(str(self._output_tokens), style="yellow")
        return text

    def update_tokens(self, input_tokens: int, output_tokens: int) -> None:
        self._input_tokens = input_tokens
        self._output_tokens = output_tokens
        self._get_label().update(self._render_text())

    def update_model(self, model: str) -> None:
        self._model = model
        self._get_label().update(self._render_text())
