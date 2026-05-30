import json
import httpx
from typing import AsyncIterator, List, Optional, Union
from .types import Message, TextContent, AssistantMessage, ToolCall, FunctionCall, Usage
from .events import (
    Event, ThinkingStartEvent, ThinkingDeltaEvent, ThinkingEndEvent,
    TextStartEvent, TextDeltaEvent, TextEndEvent,
    ToolStartEvent, ToolArgsDeltaEvent, ToolEndEvent,
    ErrorEvent
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
            "User-Agent": "rta-cli/1.0"
        }

        payload = {
            "messages": [m.model_dump() for m in messages],
            "stream": True
        }
        if system_prompt:
            payload["system_prompt"] = system_prompt
        if tools:
            payload["tools"] = tools

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST", 
                    f"{self.server_url}/v1/chat/completions", 
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
                    tool_calls_data = {} # id -> {name, args}

                    thinking_started = False
                    text_started = False

                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})

                            # 1. Handle Thinking (Reasoning)
                            reasoning = delta.get("reasoning_content") or delta.get("thinking")
                            if reasoning:
                                if not thinking_started:
                                    yield ThinkingStartEvent()
                                    thinking_started = True
                                yield ThinkingDeltaEvent(delta=reasoning)
                                current_thinking += reasoning

                            # 2. Handle Text Content
                            content = delta.get("content")
                            if content:
                                if not text_started:
                                    # If thinking was happening, end it
                                    if thinking_started:
                                        yield ThinkingEndEvent(thinking=current_thinking)
                                        thinking_started = False
                                    yield TextStartEvent()
                                    text_started = True
                                yield TextDeltaEvent(delta=content)
                                current_text += content

                            # 3. Handle Tool Calls
                            tool_deltas = delta.get("tool_calls", [])
                            for td in tool_deltas:
                                index = td.get("index", 0)
                                tc_id = td.get("id")
                                fn_delta = td.get("function", {})
                                
                                if tc_id: # Start of a tool call
                                    name = fn_delta.get("name")
                                    tool_calls_data[index] = {"id": tc_id, "name": name, "args": ""}
                                    yield ToolStartEvent(tool_call_id=tc_id, name=name)
                                
                                args_delta = fn_delta.get("arguments")
                                if args_delta and index in tool_calls_data:
                                    tool_calls_data[index]["args"] += args_delta
                                    yield ToolArgsDeltaEvent(
                                        tool_call_id=tool_calls_data[index]["id"], 
                                        delta=args_delta
                                    )

                        except json.JSONDecodeError:
                            continue

                    # Finalize events
                    if thinking_started:
                        yield ThinkingEndEvent(thinking=current_thinking)
                    if text_started:
                        yield TextEndEvent(text=current_text)
                    
                    for index, data in tool_calls_data.items():
                        yield ToolEndEvent(
                            tool_call_id=data["id"], 
                            name=data["name"], 
                            arguments=data["args"]
                        )

        except Exception as e:
            yield ErrorEvent(message="Connection Error", details=str(e))
