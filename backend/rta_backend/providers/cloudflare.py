import httpx
import json
from . import RateLimitError, ProviderDownError, ProviderTimeoutError, get_provider_client, reset_provider_client

async def call_cloudflare(messages, model, tools, api_key, max_tokens, account_id) -> dict:
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "messages": messages,
    }
    if tools:
        payload["tools"] = tools

    client = get_provider_client()
    try:
        response = await client.post(url, headers=headers, json=payload)

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError("Cloudflare rate limit exceeded", retry_after=retry_after)
        elif response.status_code >= 500:
            raise ProviderDownError(f"Cloudflare server error: {response.status_code}")
        elif response.status_code == 400:
            raise ProviderDownError(f"Cloudflare bad request: {response.text[:200]}")

        response.raise_for_status()
        data = response.json()

        if not data.get("success"):
            errors = data.get("errors", [])
            error_msg = errors[0].get("message", "Unknown error") if errors else "Unknown error"
            if "rate" in error_msg.lower():
                raise RateLimitError("Cloudflare rate limit exceeded")
            raise ProviderDownError(f"Cloudflare API error: {error_msg}")

        result = data.get("result", {})
        choices = result.get("choices", [])

        tool_calls = []
        if choices and choices[0].get("message", {}).get("tool_calls"):
            tool_calls = choices[0]["message"]["tool_calls"]

        return {
            "choices": choices,
            "usage": result.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "cached_tokens": 0}),
            "model": result.get("model", model),
            "tool_calls_log": tool_calls
        }

    except httpx.TimeoutException:
        raise ProviderTimeoutError("Cloudflare request timed out")
    except httpx.HTTPStatusError as e:
        raise ProviderDownError(f"Cloudflare HTTP error: {e}")
    except Exception as e:
        if isinstance(e, RateLimitError):
            raise
        if isinstance(e, (httpx.ConnectError, httpx.RemoteProtocolError, httpx.LocalProtocolError, httpx.ReadError, httpx.WriteError)):
            await reset_provider_client()
        raise ProviderDownError(f"Cloudflare unexpected error: {e}")


async def call_cloudflare_stream(messages, model, tools, api_key, max_tokens, account_id):
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "messages": messages,
        "stream": True,
    }
    if tools:
        payload["tools"] = tools

    client = get_provider_client()
    try:
        async with client.stream("POST", url, headers=headers, json=payload) as resp:
            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After")
                raise RateLimitError("Cloudflare rate limit exceeded", retry_after=retry_after)
            elif resp.status_code >= 500:
                raise ProviderDownError(f"Cloudflare server error: {resp.status_code}")
            elif resp.status_code == 400:
                body = await resp.aread()
                raise ProviderDownError(f"Cloudflare bad request: {body.decode()[:200]}")

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
        raise ProviderTimeoutError("Cloudflare request timed out")
    except httpx.HTTPStatusError as e:
        raise ProviderDownError(f"Cloudflare HTTP error: {e}")
    except Exception as e:
        if isinstance(e, (RateLimitError, ProviderDownError, ProviderTimeoutError)):
            raise
        if isinstance(e, (httpx.ConnectError, httpx.RemoteProtocolError, httpx.LocalProtocolError, httpx.ReadError, httpx.WriteError)):
            await reset_provider_client()
        raise ProviderDownError(f"Cloudflare unexpected error: {e}")
