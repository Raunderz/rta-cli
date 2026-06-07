import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from kon import auth as kon_auth
from kon import config as kon_config

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

# ──────────────────────────────────────────────────────────────────────────────
# Provider Implementation
# ──────────────────────────────────────────────────────────────────────────────


class RtaProvider(BaseProvider):
    name = "rta"

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = (
            config.api_key or kon_config.rta.api_key or kon_auth.load_credential("rta_api_key")
        )
        self.server_url = config.base_url or kon_config.rta.server_url
        self.device_id = kon_config.rta.device_id or kon_auth.get_device_id()

    async def _stream_impl(
        self,
        messages: list[Message],
        *,
        system_prompt: str | None = None,
        tools: list[ToolDefinition] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMStream:
        headers = {
            "X-API-KEY": self.api_key or "",
            "X-Device-ID": self.device_id,
            "X-CLI-Version": "0.6.0-kon",
            "Content-Type": "application/json",
            "User-Agent": "rta-kon/1.0",
        }

        payload = {
            "messages": self._convert_messages(messages, system_prompt),
            "model": self.config.model or "auto",
            "provider": "auto",
            "stream": True,
            "max_tokens": max_tokens or self.config.max_tokens or 2000,
        }
        if tools:
            payload["tools"] = self._convert_tools(tools)

        llm_stream = LLMStream()
        llm_stream.set_iterator(self._process_stream(payload, headers, llm_stream))
        return llm_stream

    async def _process_stream(
        self, payload: dict[str, Any], headers: dict[str, str], llm_stream: LLMStream
    ) -> AsyncIterator[StreamPart]:
        try:
            async with (
                httpx.AsyncClient(timeout=60.0) as client,
                client.stream(
                    "POST", f"{self.server_url}/v1/chat", json=payload, headers=headers
                ) as response,
            ):
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise httpx.HTTPStatusError(
                        f"API Error {response.status_code}: {error_text.decode()}",
                        request=response.request,
                        response=response,
                    )

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
                        yield TextPart(text=content)
                    elif event_type == "thought" and content:
                        yield ThinkPart(think=content)
                    elif event_type == "tool_calls":
                        for i, tc in enumerate(content):
                            tc_id = tc.get("id", "")
                            fn = tc.get("function", {})
                            name = fn.get("name", "")
                            args = fn.get("arguments", "")
                            if tc_id:
                                yield ToolCallStart(id=tc_id, name=name, index=i)
                                if args:
                                    yield ToolCallDelta(index=i, arguments_delta=args)
                    elif event_type == "error":
                        yield StreamError(error=content or "Unknown error")
                        return
                    elif event_type == "usage" and isinstance(content, dict):
                        llm_stream._usage = Usage(
                            input_tokens=content.get("prompt_tokens", 0),
                            output_tokens=content.get("completion_tokens", 0),
                        )
                    elif event_type == "meta" and isinstance(content, dict) and "id" in content:
                        llm_stream._id = content["id"]

            yield StreamDone(stop_reason=StopReason.STOP)

        except httpx.HTTPStatusError as e:
            if e.response.status_code >= 500:
                raise
            yield StreamError(error=str(e))
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout):
            raise
        except Exception as e:
            yield StreamError(error=f"Connection Error: {e!s}")

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
                            parts.append(
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{item.mime_type};base64,{item.data}"
                                    },
                                }
                            )
                    result.append({"role": "user", "content": parts})
            elif isinstance(msg, AssistantMessage):
                content_parts = []
                tool_calls = []
                for item in msg.content:
                    if isinstance(item, TextContent):
                        content_parts.append(item.text)
                    elif isinstance(item, ThinkingContent):
                        # Rta backend might not expect thinking content back in the same way,
                        # but we include it if needed.
                        pass
                    elif isinstance(item, ToolCall):
                        tool_calls.append(
                            {
                                "id": item.id,
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
                    {
                        "role": "tool",
                        "tool_call_id": msg.tool_call_id,
                        "content": "\n".join(text_parts) if text_parts else "",
                    }
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
        retryable = (
            httpx.ConnectError,
            httpx.ConnectTimeout,
            httpx.ReadTimeout,
            httpx.WriteTimeout,
        )
        return isinstance(error, retryable) or (
            isinstance(error, httpx.HTTPStatusError) and error.response.status_code >= 500
        )
