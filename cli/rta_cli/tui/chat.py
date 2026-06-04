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
        self._anchor_released = False

    def on_mount(self) -> None:
        self.anchor()

    def add_user_message(self, text: str) -> UserBlock:
        block = UserBlock(text)
        self.mount(block)
        self._anchor_released = False
        self.scroll_end(animate=False)
        return block

    def start_thinking(self) -> ThinkingBlock:
        block = ThinkingBlock()
        self.mount(block)
        self._current_thinking = block
        self._scroll_if_anchored()
        return block

    def start_content(self) -> ContentBlock:
        block = ContentBlock()
        self.mount(block)
        self._current_content = block
        self._scroll_if_anchored()
        return block

    def start_tool(self, tool_call_id: str, name: str) -> ToolBlock:
        block = ToolBlock(tool_call_id=tool_call_id, name=name)
        self.mount(block)
        self._tool_blocks[tool_call_id] = block
        self._scroll_if_anchored()
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

    def _scroll_if_anchored(self) -> None:
        if not self._anchor_released:
            self.scroll_end(animate=False)

    def scroll_to_bottom(self) -> None:
        self.scroll_end(animate=False)

    def clear(self) -> None:
        for child in list(self.children):
            child.remove()
        self._current_thinking = None
        self._current_content = None
        self._tool_blocks.clear()
