import asyncio
import json
from typing import AsyncIterator, List, Optional, Dict, Any
from .types import (
    Message, UserMessage, AssistantMessage, ToolResultMessage, 
    ToolCall, FunctionCall, ToolResult, Usage
)
from .events import (
    Event, ThinkingStartEvent, ThinkingDeltaEvent, ThinkingEndEvent,
    TextStartEvent, TextDeltaEvent, TextEndEvent,
    ToolStartEvent, ToolArgsDeltaEvent, ToolEndEvent,
    ToolResultEvent, TurnEndEvent, ErrorEvent
)
from .provider import AsyncRtaProvider

from .tool_manager import ToolManager

from .session import SessionManager
from .context import ContextManager

class Agent:
    def __init__(
        self, 
        provider: AsyncRtaProvider, 
        system_prompt: str,
        tool_manager: ToolManager,
        session_manager: Optional[SessionManager] = None,
        context_manager: Optional[ContextManager] = None
    ):
        self.provider = provider
        self.system_prompt = system_prompt
        self.tool_manager = tool_manager
        self.session_manager = session_manager
        self.context_manager = context_manager
        
        # Initial message load
        self.messages: List[Message] = []
        if self.session_manager:
            self.messages = self.session_manager.load_messages()

    async def run_turn(
        self, 
        user_input: str, 
        cancel_event: Optional[asyncio.Event] = None,
        session_id: Optional[str] = None,
        model: Optional[str] = None
    ) -> AsyncIterator[Event]:
        # Switch model if provided (for Ollama)
        if model and hasattr(self.provider, "model"):
            self.provider.model = model

        # Switch session if provided
        if session_id and self.session_manager:
            if not hasattr(self, "_current_session_id") or self._current_session_id != session_id:
                self.messages = self.session_manager.load_messages(session_id=session_id)
                self._current_session_id = session_id

        # 0. Check for compaction before turn
        if self.context_manager and self.context_manager.should_compact(self.messages):
            summary = await self.context_manager.generate_summary(self.messages)
            self.messages = self.context_manager.compact(self.messages, summary)
            if self.session_manager:
                self.session_manager.append_compaction(summary)

        # 1. Setup user message
        user_msg = UserMessage(content=user_input)
        self.messages.append(user_msg)
        if self.session_manager:
            self.session_manager.append_message(user_msg)
        
        # 2. Start turn loop
        while True:
            current_assistant_content = ""
            current_thinking = ""
            current_tool_calls: List[ToolCall] = []
            
            async for event in self.provider.stream(
                messages=self.messages,
                system_prompt=self.system_prompt,
                tools=self.tool_manager.get_schemas()
            ):
                yield event
                
                if isinstance(event, ThinkingEndEvent):
                    current_thinking = event.thinking
                elif isinstance(event, TextEndEvent):
                    current_assistant_content = event.text
                elif isinstance(event, ToolEndEvent):
                    current_tool_calls.append(
                        ToolCall(
                            id=event.tool_call_id,
                            function=FunctionCall(name=event.name, arguments=event.arguments)
                        )
                    )
                elif isinstance(event, ErrorEvent):
                    return

            assistant_msg = AssistantMessage(
                content=current_assistant_content or None,
                thinking=current_thinking or None,
                tool_calls=current_tool_calls or None
            )
            self.messages.append(assistant_msg)
            if self.session_manager:
                self.session_manager.append_message(assistant_msg)

            if not current_tool_calls:
                yield TurnEndEvent(message=assistant_msg)
                return

            # 3. Execute tool calls
            for tc in current_tool_calls:
                result = await self.tool_manager.execute_call(tc, cancel_event=cancel_event)
                yield ToolResultEvent(tool_call_id=tc.id, result=result)
                
                tool_res_msg = ToolResultMessage(
                    tool_call_id=tc.id,
                    content=result.result
                )
                self.messages.append(tool_res_msg)
                if self.session_manager:
                    self.session_manager.append_message(tool_res_msg)
