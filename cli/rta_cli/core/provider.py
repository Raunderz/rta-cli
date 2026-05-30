import json
import httpx
import asyncio
from typing import AsyncIterator, List, Optional, Union
from .types import Message, TextContent, AssistantMessage, ToolCall, FunctionCall, Usage
from .events import (
    Event, ThinkingStartEvent, ThinkingDeltaEvent, ThinkingEndEvent,
    TextStartEvent, TextDeltaEvent, TextEndEvent,
    ToolStartEvent, ToolArgsDeltaEvent, ToolEndEvent,
    UsageEvent, ErrorEvent
)
from rta_cli.utils import load_credential, get_device_id, get_server_url

class AsyncRtaProvider:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or load_credential("rta_api_key")
        self.server_url = get_server_url()
        self.device_id = get_device_id()

    async def stream(
        self, 
        messages: List[Message], 
        system_prompt: Optional[str] = None,
        tools: Optional[List[dict]] = None
    ) -> AsyncIterator[Event]:
        headers = {
            "X-API-KEY": self.api_key,
            "X-Device-ID": self.device_id,
            "X-CLI-Version": "0.5.0",
            "Content-Type": "application/json",
            "User-Agent": "rta-cli/1.0",
            "ngrok-skip-browser-warning": "69420"
        }

        from .types import AssistantMessage
        clean_messages = [
            m for m in messages
            if not (isinstance(m, AssistantMessage) and m.content is None and m.tool_calls is None)
        ]

        payload = {
            "messages": [m.model_dump() for m in clean_messages],
            "model": "auto",
            "provider": "auto",
            "stream": True,
            "max_tokens": 2000,
        }
        if tools:
            payload["tools"] = tools

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST", 
                    f"{self.server_url}/v1/chat", 
                    json=payload, 
                    headers=headers
                ) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        yield ErrorEvent(message=f"API Error {response.status_code}", details=error_text.decode())
                        return

                    # State for reconstructing the response
                    current_thinking = ""
                    current_text = ""
                    tool_calls_data: dict[int, dict] = {}

                    thinking_started = False
                    text_started = False

                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue

                        data_str = line[6:].strip()
                        if not data_str or data_str == "[DONE]":
                            break

                        try:
                            event = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue

                        event_type = event.get("type", "")
                        content = event.get("content", "")

                        if event_type == "text" and content:
                            if thinking_started:
                                yield ThinkingEndEvent(thinking=current_thinking)
                                thinking_started = False
                            if not text_started:
                                yield TextStartEvent()
                                text_started = True
                            yield TextDeltaEvent(delta=content)
                            current_text += content

                        elif event_type == "thought" and content:
                            if not thinking_started:
                                yield ThinkingStartEvent()
                                thinking_started = True
                            yield ThinkingDeltaEvent(delta=content)
                            current_thinking += content

                        elif event_type == "tool_calls":
                            for tc in content:
                                tc_id = tc.get("id", "")
                                fn = tc.get("function", {})
                                name = fn.get("name", "")
                                args = fn.get("arguments", "")
                                if tc_id:
                                    yield ToolStartEvent(tool_call_id=tc_id, name=name)
                                    if args:
                                        yield ToolArgsDeltaEvent(tool_call_id=tc_id, delta=args)
                                    yield ToolEndEvent(tool_call_id=tc_id, name=name, arguments=args)

                        elif event_type == "error":
                            yield ErrorEvent(message=content or "Unknown error")
                            return

                        elif event_type == "usage" and isinstance(content, dict):
                            yield UsageEvent(
                                prompt_tokens=content.get("prompt_tokens", 0),
                                completion_tokens=content.get("completion_tokens", 0),
                                total_tokens=content.get("total_tokens", 0),
                            )
                        elif event_type == "provider" or event_type == "meta":
                            continue

                    # Finalize events
                    if thinking_started:
                        yield ThinkingEndEvent(thinking=current_thinking)
                    if text_started:
                        yield TextEndEvent(text=current_text)

        except asyncio.CancelledError:
            # Re-raise to let the caller handle it
            raise
        except Exception as e:
            yield ErrorEvent(message="Connection Error", details=str(e))
