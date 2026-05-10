import httpx
import json
from . import RateLimitError, ProviderDownError, ProviderTimeoutError

async def call_sambanova(messages, model, tools, api_key, max_tokens) -> dict:
    url = "https://api.sambanova.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "messages": messages,
        "model": model,
        "max_tokens": max_tokens
    }
    if tools:
        payload["tools"] = tools

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                raise RateLimitError("SambaNova rate limit exceeded", retry_after=retry_after)
            elif response.status_code >= 500:
                raise ProviderDownError(f"SambaNova server error: {response.status_code}")
            
            response.raise_for_status()
            data = response.json()
            
            tool_calls = []
            if data.get("choices") and data["choices"][0].get("message", {}).get("tool_calls"):
                tool_calls = data["choices"][0]["message"]["tool_calls"]

            return {
                "choices": data.get("choices", []),
                "usage": data.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "cached_tokens": 0}),
                "model": data.get("model", model),
                "tool_calls_log": tool_calls
            }

        except httpx.TimeoutException:
            raise ProviderTimeoutError("SambaNova request timed out")
        except httpx.HTTPStatusError as e:
            raise ProviderDownError(f"SambaNova HTTP error: {e}")
        except Exception as e:
            if isinstance(e, RateLimitError):
                raise
            raise ProviderDownError(f"SambaNova unexpected error: {e}")


async def call_sambanova_stream(messages, model, tools, api_key, max_tokens):
    url = "https://api.sambanova.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "messages": messages,
        "model": model,
        "max_tokens": max_tokens,
        "stream": True,
        "stream_options": {"include_usage": True}
    }
    if tools:
        payload["tools"] = tools

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                if resp.status_code == 429:
                    retry_after = resp.headers.get("Retry-After")
                    raise RateLimitError("SambaNova rate limit exceeded", retry_after=retry_after)
                elif resp.status_code >= 500:
                    raise ProviderDownError(f"SambaNova server error: {resp.status_code}")

                resp.raise_for_status()

                current_tool_calls = {}
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    choices = data.get("choices", [])
                    if not choices:
                        if "usage" in data and data["usage"]:
                            yield {"type": "usage", "content": data["usage"]}
                        continue

                    delta = choices[0].get("delta", {})

                    if "content" in delta and delta["content"]:
                        yield {"type": "text", "content": delta["content"]}

                    if "tool_calls" in delta:
                        for tc in delta["tool_calls"]:
                            idx = tc.get("index", 0)
                            if idx not in current_tool_calls:
                                current_tool_calls[idx] = {
                                    "id": tc.get("id", ""),
                                    "type": "function",
                                    "function": {"name": "", "arguments": ""}
                                }
                            if tc.get("id"):
                                current_tool_calls[idx]["id"] = tc["id"]
                            if tc.get("function", {}).get("name"):
                                current_tool_calls[idx]["function"]["name"] = tc["function"]["name"]
                            if tc.get("function", {}).get("arguments"):
                                current_tool_calls[idx]["function"]["arguments"] += tc["function"]["arguments"]

                    finish_reason = choices[0].get("finish_reason")
                    if finish_reason and current_tool_calls:
                        yield {"type": "tool_calls", "content": list(current_tool_calls.values())}
                        current_tool_calls = {}

        except httpx.TimeoutException:
            raise ProviderTimeoutError("SambaNova request timed out")
        except httpx.HTTPStatusError as e:
            raise ProviderDownError(f"SambaNova HTTP error: {e}")
        except Exception as e:
            if isinstance(e, (RateLimitError, ProviderDownError, ProviderTimeoutError)):
                raise
            raise ProviderDownError(f"SambaNova unexpected error: {e}")
