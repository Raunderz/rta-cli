import httpx
import json
from . import RateLimitError, ProviderDownError, ProviderTimeoutError

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
        # Find first user message and prepend system instruction
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

    async with httpx.AsyncClient(timeout=30.0) as client:
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
