import httpx
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
