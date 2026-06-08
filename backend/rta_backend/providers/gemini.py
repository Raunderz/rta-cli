import httpx
import json
from . import RateLimitError, ProviderDownError, ProviderTimeoutError, get_provider_client

def translate_messages(messages):
    gemini_contents = []
    system_instruction = ""
    
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")
        
        if role == "system":
            system_instruction += content + "\n\n"
            continue
            
        gemini_role = "user" if role == "user" else "model"
        gemini_contents.append({
            "role": gemini_role,
            "parts": [{"text": content}]
        })
        
    if system_instruction and gemini_contents:
        for entry in gemini_contents:
            if entry["role"] == "user":
                entry["parts"][0]["text"] = f"[SYSTEM]\n{system_instruction}[END SYSTEM]\n\n{entry['parts'][0]['text']}"
                break
            
    return gemini_contents

def translate_tools(openai_tools):
    if not openai_tools:
        return None
    
    function_declarations = []
    for tool in openai_tools:
        if tool.get("type") == "function":
            func = tool["function"]
            function_declarations.append({
                "name": func["name"],
                "description": func.get("description", ""),
                "parameters": func.get("parameters", {})
            })
            
    return [{"function_declarations": function_declarations}]

async def call_gemini(messages, model, tools, api_key, max_tokens) -> dict:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    gemini_contents = translate_messages(messages)
    gemini_tools = translate_tools(tools)
    
    payload = {
        "contents": gemini_contents,
        "generationConfig": {
            "maxOutputTokens": max_tokens,
        }
    }
    if gemini_tools:
        payload["tools"] = gemini_tools

    client = get_provider_client()
    try:
        response = await client.post(url, json=payload)
        
        if response.status_code == 429:
            raise RateLimitError("Gemini rate limit exceeded")
        elif response.status_code >= 500:
            raise ProviderDownError(f"Gemini server error: {response.status_code}")
            
        response.raise_for_status()
        data = response.json()
        
        if not data.get("candidates"):
            raise ProviderDownError("Gemini returned no candidates")

        candidate = data["candidates"][0]
        content = ""
        tool_calls = []
        
        parts = candidate.get("content", {}).get("parts", [])
        for part in parts:
            if "text" in part:
                content += part["text"]
            if "functionCall" in part:
                fc = part["functionCall"]
                tool_calls.append({
                    "id": f"call_{fc['name']}",
                    "type": "function",
                    "function": {
                        "name": fc["name"],
                        "arguments": json.dumps(fc.get("args", {}))
                    }
                })
        
        usage = data.get("usageMetadata", {})
        
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": content
                }
            }],
            "usage": {
                "prompt_tokens": usage.get("promptTokenCount", 0),
                "completion_tokens": usage.get("candidatesTokenCount", 0),
                "cached_tokens": 0
            },
            "model": model,
            "tool_calls_log": tool_calls
        }

    except httpx.TimeoutException:
        raise ProviderTimeoutError("Gemini request timed out")
    except httpx.HTTPStatusError as e:
        raise ProviderDownError(f"Gemini HTTP error: {e}")
    except Exception as e:
        if isinstance(e, RateLimitError):
            raise
        raise ProviderDownError(f"Gemini unexpected error: {e}")


async def call_gemini_stream(messages, model, tools, api_key, max_tokens):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?key={api_key}&alt=sse"
    
    gemini_contents = translate_messages(messages)
    gemini_tools = translate_tools(tools)
    
    payload = {
        "contents": gemini_contents,
        "generationConfig": {
            "maxOutputTokens": max_tokens,
        }
    }
    if gemini_tools:
        payload["tools"] = gemini_tools

    client = get_provider_client()
    try:
        async with client.stream("POST", url, json=payload) as resp:
            if resp.status_code == 429:
                raise RateLimitError("Gemini rate limit exceeded")
            elif resp.status_code >= 500:
                raise ProviderDownError(f"Gemini server error: {resp.status_code}")

            resp.raise_for_status()

            prev_text = ""
            current_tool_calls = {}
            usage = {}

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

                if "usageMetadata" in data and data["usageMetadata"]:
                    usage = data["usageMetadata"]

                candidates = data.get("candidates", [])
                if not candidates:
                    continue

                candidate = candidates[0]
                parts = candidate.get("content", {}).get("parts", [])

                current_text = ""
                for part in parts:
                    if "text" in part:
                        current_text += part["text"]
                    if "functionCall" in part:
                        fc = part["functionCall"]
                        idx = fc.get("name", "0")
                        current_tool_calls[idx] = {
                            "id": f"call_{fc['name']}",
                            "type": "function",
                            "function": {
                                "name": fc["name"],
                                "arguments": json.dumps(fc.get("args", {}))
                            }
                        }

                if current_text:
                    delta = current_text[len(prev_text):]
                    if delta:
                        yield {"type": "text", "content": delta}
                    prev_text = current_text

                finish_reason = candidate.get("finishReason")
                if finish_reason and finish_reason != "FINISH_REASON_UNSPECIFIED":
                    if current_tool_calls:
                        yield {"type": "tool_calls", "content": list(current_tool_calls.values())}
                        current_tool_calls = {}
                    if usage:
                        yield {"type": "usage", "content": {
                            "prompt_tokens": usage.get("promptTokenCount", 0),
                            "completion_tokens": usage.get("candidatesTokenCount", 0),
                            "cached_tokens": 0
                        }}

    except httpx.TimeoutException:
        raise ProviderTimeoutError("Gemini request timed out")
    except httpx.HTTPStatusError as e:
        raise ProviderDownError(f"Gemini HTTP error: {e}")
    except Exception as e:
        if isinstance(e, (RateLimitError, ProviderDownError, ProviderTimeoutError)):
            raise
        raise ProviderDownError(f"Gemini unexpected error: {e}")
