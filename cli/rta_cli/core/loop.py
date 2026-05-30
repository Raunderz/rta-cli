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

class Agent:
    def __init__(
        self, 
        provider: AsyncRtaProvider, 
        system_prompt: str,
        tools: List[Dict[str, Any]]
    ):
        self.provider = provider
        self.system_prompt = system_prompt
        self.tools = tools
        self.messages: List[Message] = []

    async def run_turn(self, user_input: str) -> AsyncIterator[Event]:
        # 1. Setup user message
        self.messages.append(UserMessage(content=user_input))
        
        # 2. Start turn loop (to handle multiple tool cycles if needed)
        while True:
            current_assistant_content = ""
            current_thinking = ""
            current_tool_calls: List[ToolCall] = []
            
            # Stream from provider
            async for event in self.provider.stream(
                messages=self.messages,
                system_prompt=self.system_prompt,
                tools=self.tools
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
                    return # Stop on error

            # Create the assistant message
            assistant_msg = AssistantMessage(
                content=current_assistant_content or None,
                thinking=current_thinking or None,
                tool_calls=current_tool_calls or None
            )
            self.messages.append(assistant_msg)

            # 3. If no tool calls, turn is done
            if not current_tool_calls:
                yield TurnEndEvent(message=assistant_msg)
                return

            # 4. Execute tool calls (Placeholder for Phase 2 Tool Manager)
            # For now, we yield dummy results to keep the loop valid
            for tc in current_tool_calls:
                # TODO: Implement ToolManager.execute(tc)
                dummy_result = ToolResult(
                    success=False, 
                    result=f"Tool '{tc.function.name}' execution not yet implemented in Phase 1."
                )
                
                yield ToolResultEvent(tool_call_id=tc.id, result=dummy_result)
                
                self.messages.append(
                    ToolResultMessage(
                        tool_call_id=tc.id,
                        content=dummy_result.result
                    )
                )

            # Continue the loop for the model to see tool results
