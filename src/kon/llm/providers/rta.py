import asyncio
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
# Heartbeat — keeps the RTA backend process alive on Render/HF Spaces
# by pinging GET /v1/heartbeat every 20s while the CLI is active.
# ──────────────────────────────────────────────────────────────────────────────

_heartbeat_task: asyncio.Task | None = None


async def _heartbeat_loop(server_url: str, api_key: str) -> None:
    client = httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0, read=5.0))
    try:
        while True:
            await asyncio.sleep(20)
            try:
                await client.get(
                    f"{server_url}/v1/heartbeat",
                    headers={"X-API-KEY": api_key},
                )
            except Exception:
                pass
    finally:
        await client.aclose()


def _ensure_heartbeat(server_url: str, api_key: str) -> None:
    global _heartbeat_task
    if _heartbeat_task is None:
        _heartbeat_task = asyncio.create_task(_heartbeat_loop(server_url, api_key))


async def stop_heartbeat() -> None:
    global _heartbeat_task
    if _heartbeat_task is not None:
        _heartbeat_task.cancel()
        try:
            await _heartbeat_task
        except asyncio.CancelledError:
            pass
        _heartbeat_task = None


# ──────────────────────────────────────────────────────────────────────────────
# Provider Implementation
# ──────────────────────────────────────────────────────────────────────────────


class RtaProvider(BaseProvider):
    name = "rta"
    thinking_levels: list[str] = []  # RTA provider doesn't support reasoning/thinking

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = (
            config.api_key or kon_config.rta.api_key or kon_auth.load_credential("rta_api_key")
        )
        self.server_url = config.base_url or kon_config.rta.server_url
        self.device_id = kon_config.rta.device_id or kon_auth.get_device_id()

    async def get_metadata(self) -> dict[str, Any]:
        if not self.api_key:
            return {}
        
        headers = {"X-API-KEY": self.api_key}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.server_url}/v1/usage", headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    tier = data.get("tier", "free").lower()
                    
                    # Context windows per tier (aligned with backend TIER_CAPS)
                    context_windows = {
                        "free": 2000,
                        "basic": 4000,
                        "pro": 10000,
                        "enterprise": 32000
                    }
                    
                    window = context_windows.get(tier, 2000)
                    
                    return {
                        "context_window": window,
                        "tier": tier,
                        "usage": data
                    }
        except Exception:
            pass
        return {}

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

        _ensure_heartbeat(self.server_url, self.api_key)

        llm_stream = LLMStream()
        llm_stream.set_iterator(self._process_stream(payload, headers, llm_stream))
        return llm_stream

    async def _process_stream(
        self, payload: dict[str, Any], headers: dict[str, str], llm_stream: LLMStream
    ) -> AsyncIterator[StreamPart]:
        try:
            # 1. Enqueue job
            async with httpx.AsyncClient(timeout=30.0) as client:
                print(f"DEBUG: Connecting to {self.server_url}/v1/chat/async")
                response = await client.post(
                    f"{self.server_url}/v1/chat/async", json=payload, headers=headers
                )
                if response.status_code not in (200, 202):
                    error_text = await response.aread()
                    raise httpx.HTTPStatusError(
                        f"API Error {response.status_code}: {error_text.decode()}",
                        request=response.request,
                        response=response,
                    )
                
                job_data = response.json()
                job_id = job_data["job_id"]
                print(f"\n[~] Enqueued job: {job_id}")

            # 2. Poll for chunks
            next_index = 0
            consecutive_errors = 0
            while True:
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        poll_url = f"{self.server_url}/v1/chat/job/{job_id}?after_index={next_index}"
                        # print(f"DEBUG: Polling {poll_url}")
                        poll_resp = await client.get(poll_url, headers=headers)
                        
                        if poll_resp.status_code != 200:
                            consecutive_errors += 1
                            err_body = await poll_resp.aread()
                            print(f"DEBUG: Polling failed ({poll_resp.status_code}): {err_body.decode()}")
                            if consecutive_errors > 5:
                                yield StreamError(error=f"Polling failed: {poll_resp.status_code}")
                                return
                            await asyncio.sleep(1)
                            continue
                        
                        consecutive_errors = 0
                        status_data = poll_resp.json()
                        
                        # Process chunks
                        for event in status_data.get("chunks", []):
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

                        next_index = status_data.get("next_index", next_index)

                        if status_data.get("done"):
                            if status_data.get("status") == "failed":
                                yield StreamError(error=status_data.get("error", "Job failed"))
                            break
                        
                        # Wait before next poll
                        await asyncio.sleep(0.5)

                except Exception as e:
                    consecutive_errors += 1
                    if consecutive_errors > 10:
                        yield StreamError(error=f"Connection Error during polling: {e}")
                        return
                    await asyncio.sleep(1)

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
