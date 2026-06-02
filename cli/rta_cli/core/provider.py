import json
import httpx
import asyncio
import time
from typing import AsyncIterator, List, Optional, Union
from .types import Message, TextContent, AssistantMessage, ToolCall, FunctionCall, Usage
from .events import (
    Event, ThinkingStartEvent, ThinkingDeltaEvent, ThinkingEndEvent,
    TextStartEvent, TextDeltaEvent, TextEndEvent,
    ToolStartEvent, ToolArgsDeltaEvent, ToolEndEvent,
    UsageEvent, ErrorEvent
)
from rta_cli.utils import load_credential, get_device_id, get_server_url

class OllamaProvider:
    def __init__(self, model: str = "deepseek-r1", base_url: str = "http://localhost:11434", think: bool = False):
        self.model = model
        self.base_url = base_url
        self.think = think

    async def list_models(self) -> List[str]:
        """Fetch list of local models from Ollama."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    return [m["name"] for m in data.get("models", [])]
        except:
            pass
        return []

    async def stream(
        self, 
        messages: List[Message], 
        system_prompt: Optional[str] = None,
        tools: Optional[List[dict]] = None
    ) -> AsyncIterator[Event]:
        # ... (logic remains same, but use self.think)
        ollama_messages = []
        if system_prompt:
            ollama_messages.append({"role": "system", "content": system_prompt})
        
        for m in messages:
            msg_dict = m.model_dump()
            if msg_dict.get("content") is None: msg_dict["content"] = ""
            ollama_messages.append(msg_dict)

        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": True,
            "think": self.think, # Explicitly pass think mode
            "options": {
                "num_ctx": 32000,
            }
        }
        if tools:
            payload["tools"] = tools

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST", 
                    f"{self.base_url}/api/chat", 
                    json=payload
                ) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        yield ErrorEvent(message=f"Ollama Error {response.status_code}", details=error_text.decode())
                        return

                    thinking_started = False
                    text_started = False
                    current_thinking = ""
                    current_text = ""

                    emitted_tool_ids = set()

                    async for line in response.aiter_lines():
                        if not line: continue
                        try:
                            chunk = json.loads(line)
                        except json.JSONDecodeError: continue

                        if chunk.get("done"):
                            # ... usage logic ...
                            if "prompt_eval_count" in chunk:
                                yield UsageEvent(
                                    prompt_tokens=chunk.get("prompt_eval_count", 0),
                                    completion_tokens=chunk.get("eval_count", 0),
                                    total_tokens=chunk.get("prompt_eval_count", 0) + chunk.get("eval_count", 0)
                                )
                            break

                        msg = chunk.get("message", {})
                        
                        # Handle Thinking/Reasoning
                        thought = msg.get("thinking") or msg.get("reasoning_content")
                        if thought:
                            if not thinking_started:
                                yield ThinkingStartEvent()
                                thinking_started = True
                            yield ThinkingDeltaEvent(delta=thought)
                            current_thinking += thought
                        
                        # Handle Content
                        content = msg.get("content", "")
                        if content:
                            if thinking_started:
                                yield ThinkingEndEvent(thinking=current_thinking)
                                thinking_started = False
                            if not text_started:
                                yield TextStartEvent()
                                text_started = True
                            yield TextDeltaEvent(delta=content)
                            current_text += content

                        # Handle Tool Calls
                        tool_calls = msg.get("tool_calls")
                        if tool_calls:
                            # Ollama sometimes repeats tool_calls in chunks, or appends them
                            for i, tc in enumerate(tool_calls):
                                # Small models hallucinate tool calls. 
                                # Verification: check if tool name exists in registered tools
                                fn = tc.get("function", {})
                                name = fn.get("name", "")
                                if tools and not any(t["function"]["name"] == name for t in tools):
                                    # Hallucination or invalid tool
                                    continue

                                tc_id = f"ollama_{i}" # Stable ID for this turn
                                if tc_id not in emitted_tool_ids:
                                    args = json.dumps(fn.get("arguments", {}))
                                    yield ToolStartEvent(tool_call_id=tc_id, name=name)
                                    yield ToolArgsDeltaEvent(tool_call_id=tc_id, delta=args)
                                    yield ToolEndEvent(tool_call_id=tc_id, name=name, arguments=args)
                                    emitted_tool_ids.add(tc_id)

                    if thinking_started:
                        yield ThinkingEndEvent(thinking=current_thinking)
                    if text_started:
                        yield TextEndEvent(text=current_text)

        except Exception as e:
            yield ErrorEvent(message="Ollama Connection Error", details=str(e))

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
