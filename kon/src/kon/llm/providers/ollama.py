import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from ...core.types import (
    AssistantMessage,
    ImageContent,
    Message,
    StopReason,
    StreamDone,
    StreamError,
    StreamPart,
    TextContent,
    TextPart,
    ThinkingContent,
    ThinkPart,
    ToolCall,
    ToolCallDelta,
    ToolCallStart,
    ToolDefinition,
    ToolResultMessage,
    Usage,
    UserMessage,
)
from ..base import BaseProvider, LLMStream, ProviderConfig


class OllamaProvider(BaseProvider):
    name = "ollama"

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = config.base_url or "http://localhost:11434"
        self.model = config.model or "deepseek-r1"

    async def _stream_impl(
        self,
        messages: list[Message],
        *,
        system_prompt: str | None = None,
        tools: list[ToolDefinition] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMStream:
        ollama_messages = self._convert_messages(messages, system_prompt)

        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": True,
            "think": self.config.thinking_level != "none",
            "options": {"num_ctx": 32000},
        }
        if temperature is not None:
            payload["options"]["temperature"] = temperature
        if max_tokens is not None:
            payload["options"]["num_predict"] = max_tokens

        if tools:
            payload["tools"] = self._convert_tools(tools)

        llm_stream = LLMStream()
        llm_stream.set_iterator(self._process_stream(payload, llm_stream))
        return llm_stream

    async def _process_stream(
        self, payload: dict[str, Any], llm_stream: LLMStream
    ) -> AsyncIterator[StreamPart]:
        try:
            async with (
                httpx.AsyncClient(timeout=120.0) as client,
                client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response,
            ):
                if response.status_code != 200:
                    error_text = await response.aread()
                    yield StreamError(
                        error=f"Ollama Error {response.status_code}: {error_text.decode()}"
                    )
                    return

                emitted_tool_ids = set()

                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if chunk.get("done"):
                        if "prompt_eval_count" in chunk:
                            llm_stream._usage = Usage(
                                input_tokens=chunk.get("prompt_eval_count", 0),
                                output_tokens=chunk.get("eval_count", 0),
                            )
                        break

                    msg = chunk.get("message", {})

                    # Handle Thinking/Reasoning
                    thought = msg.get("thinking") or msg.get("reasoning_content")
                    if thought:
                        yield ThinkPart(think=thought)

                    # Handle Content
                    content = msg.get("content", "")
                    if content:
                        yield TextPart(text=content)

                    # Handle Tool Calls
                    tool_calls = msg.get("tool_calls")
                    if tool_calls:
                        for i, tc in enumerate(tool_calls):
                            tc_id = f"ollama_{i}"
                            fn = tc.get("function", {})
                            name = fn.get("name", "")
                            if tc_id not in emitted_tool_ids:
                                args = json.dumps(fn.get("arguments", {}))
                                yield ToolCallStart(id=tc_id, name=name, index=i)
                                yield ToolCallDelta(index=i, arguments_delta=args)
                                emitted_tool_ids.add(tc_id)

            yield StreamDone(stop_reason=StopReason.STOP)

        except Exception as e:
            yield StreamError(error=f"Ollama Connection Error: {e!s}")

    def _convert_messages(
        self, messages: list[Message], system_prompt: str | None
    ) -> list[dict[str, Any]]:
        result = []
        if system_prompt:
            result.append({"role": "system", "content": system_prompt})

        for msg in messages:
            if isinstance(msg, UserMessage):
                if isinstance(msg.content, str):
                    result.append({"role": "user", "content": msg.content})
                else:
                    parts = []
                    for item in msg.content:
                        if isinstance(item, TextContent):
                            parts.append({"type": "text", "text": item.text})
                        elif isinstance(item, ImageContent):
                            # Ollama might not support images in this format directly via chat API
                            # but we'll pass it if they do.
                            pass
                    result.append({"role": "user", "content": parts})
            elif isinstance(msg, AssistantMessage):
                content_parts = []
                tool_calls = []
                for item in msg.content:
                    if isinstance(item, TextContent):
                        content_parts.append(item.text)
                    elif isinstance(item, ThinkingContent):
                        # Ollama supports thinking in the response, but does it support it in messages?
                        # Usually it's just text.
                        content_parts.append(item.thinking)
                    elif isinstance(item, ToolCall):
                        tool_calls.append(
                            {
                                "type": "function",
                                "function": {"name": item.name, "arguments": item.arguments},
                            }
                        )

                res_msg = {
                    "role": "assistant",
                    "content": "".join(content_parts) if content_parts else None,
                }
                if tool_calls:
                    res_msg["tool_calls"] = tool_calls
                result.append(res_msg)
            elif isinstance(msg, ToolResultMessage):
                text_parts = [item.text for item in msg.content if isinstance(item, TextContent)]
                result.append(
                    {"role": "tool", "content": "\n".join(text_parts) if text_parts else ""}
                )
        return result

    def _convert_tools(self, tools: list[ToolDefinition]) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]

    def should_retry_for_error(self, error: Exception) -> bool:
        return False
