from __future__ import annotations

from textual.containers import VerticalScroll

from .blocks import ContentBlock, ThinkingBlock, ToolBlock, UserBlock


class ChatLog(VerticalScroll):
    can_focus = False

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._current_thinking: ThinkingBlock | None = None
        self._current_content: ContentBlock | None = None
        self._tool_blocks: dict[str, ToolBlock] = {}

    def on_mount(self) -> None:
        self.anchor()

    def add_user_message(self, text: str) -> None:
        self.mount(UserBlock(text))
        self.scroll_end(animate=False)

    def start_thinking(self) -> ThinkingBlock:
        block = ThinkingBlock()
        self.mount(block)
        self._current_thinking = block
        self.scroll_end(animate=False)
        return block

    def start_content(self) -> ContentBlock:
        block = ContentBlock()
        self.mount(block)
        self._current_content = block
        self.scroll_end(animate=False)
        return block

    def start_tool(self, tool_call_id: str, name: str) -> ToolBlock:
        block = ToolBlock(tool_call_id=tool_call_id, name=name)
        self.mount(block)
        self._tool_blocks[tool_call_id] = block
        self.scroll_end(animate=False)
        return block

    def get_tool(self, tool_call_id: str) -> ToolBlock | None:
        return self._tool_blocks.get(tool_call_id)

    def finalize_thinking(self, collapse: bool = False) -> None:
        if self._current_thinking:
            self._current_thinking.finalize(collapse=collapse)
            self._current_thinking = None

    def finalize_content(self) -> None:
        if self._current_content:
            self._current_content.finalize()
            self._current_content = None

    def scroll_to_bottom(self) -> None:
        self.scroll_end(animate=False)
