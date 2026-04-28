import os
import sys
import json
import httpx
import time
import re
from typing import Generator
from dotenv import load_dotenv

from rta_cli.functions.get_file_content import get_file_contents, schema_get_file_contents
from rta_cli.functions.get_files_info import get_files_info, schema_get_files_info
from rta_cli.functions.run_python_file import run_python_file, schema_run_python_file
from rta_cli.functions.write_file import write_file, schema_write_file
from rta_cli.functions.run_command import run_command, schema_run_command
from rta_cli.functions.grep_search import grep_search, schema_grep_search
from rta_cli.functions.glob_search import glob_search, schema_glob_search
from rta_cli.functions.edit_file import edit_file, schema_edit_file
from rta_cli.functions.delete_file import delete_file, schema_delete_file
from rta_cli.functions.create_dir import create_dir, schema_create_dir
from rta_cli.functions.list_directory import list_directory, schema_list_directory

def call_function(function_call, workspace_dir: str):
    name = function_call.get("name")
    args = function_call.get("args", {})
    if name == "get_files_info":
        result = get_files_info(workspace_dir, **args)
    elif name == "get_file_contents":
        result = get_file_contents(workspace_dir, **args)
    elif name == "run_python_file":
        result = run_python_file(workspace_dir, **args)
    elif name == "write_file":
        result = write_file(workspace_dir, **args)
    elif name == "run_command":
        result = run_command(workspace_dir, **args)
    elif name == "grep_search":
        result = grep_search(workspace_dir, **args)
    elif name == "glob_search":
        result = glob_search(workspace_dir, **args)
    elif name == "edit_file":
        result = edit_file(workspace_dir, **args)
    elif name == "delete_file":
        result = delete_file(workspace_dir, **args)
    elif name == "create_dir":
        result = create_dir(workspace_dir, **args)
    elif name == "list_directory":
        result = list_directory(workspace_dir, **args)
    else:
        result = f"Error: function {name} not found"

    return {
        "functionResponse": {
            "name": name,
            "response": {"name": name, "content": result}
        }
    }

def stream_agent(prompt: str, workspace_dir: str, messages: list[dict], provider: str = "openrouter", model_name: str = "nvidia/nemotron-3-super-120b-a12b:free", max_iterations: int = 20, think: bool = False) -> Generator[dict, None, None]:
    load_dotenv()
    usage = {"prompt_tokens": 0, "candidate_tokens": 0, "total_tokens": 0, "cached_tokens": 0, "start_time": time.time()}
    
    system_prompt = (
        "Role: Expert coder. Style: Caveman Lite (min tokens, professional). No filler.\n"
        "Workflow: explore → read → fix → verify. Paths relative to workspace.\n"
        "Note: Tool results older than 1 turn are truncated for efficiency."
    )

    available_functions = [
        schema_get_files_info,
        schema_get_file_contents,
        schema_run_python_file,
        schema_write_file,
        schema_run_command,
        schema_grep_search,
        schema_glob_search,
        schema_edit_file,
        schema_delete_file,
        schema_create_dir,
        schema_list_directory,
    ]

    ollama_tools = [{"type": "function", "function": f} for f in available_functions]

    if not any(m["role"] == "user" for m in messages):
        messages.append({"role": "user", "parts": [{"text": prompt}]})

    for i in range(max_iterations):
        if provider == "google":
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key: 
                yield {"type": "error", "content": "Error: GEMINI_API_KEY unset"}
                return
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            payload = {
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "contents": messages,
                "tools": [{"functionDeclarations": available_functions}]
            }

            data = None
            with httpx.Client(timeout=60.0) as client:
                for attempt in range(5):
                    try:
                        resp = client.post(url, json=payload)
                        if resp.status_code == 429:
                            time.sleep(2 ** attempt)
                            continue
                        resp.raise_for_status()
                        data = resp.json()
                        break
                    except httpx.HTTPStatusError as e:
                        if e.response.status_code == 429 and attempt < 4: continue
                        yield {"type": "error", "content": f"Google API Error: {e.response.status_code}"}
                        return
                    except Exception as e:
                        yield {"type": "error", "content": f"API Connection Error: {e}"}
                        return
                else:
                    yield {"type": "error", "content": "Rate limit exceeded."}
                    return

            usage_data = data.get("usageMetadata", {})
            u_p = usage_data.get("promptTokenCount", 0)
            u_c = usage_data.get("candidatesTokenCount", 0)
            usage["prompt_tokens"] += u_p
            usage["candidate_tokens"] += u_c
            usage["total_tokens"] += (u_p + u_c)
            usage["cached_tokens"] += usage_data.get("cachedContentTokenCount", 0)

            candidate = data.get("candidates", [{}])[0]
            content = candidate.get("content", {})
            if not content:
                yield {"type": "error", "content": "Empty response from model."}
                return

            messages.append(content)
            parts = content.get("parts", [])
            
            texts = [p["text"] for p in parts if "text" in p]
            if texts:
                full_text = "".join(texts)
                yield {"type": "text", "content": full_text}
            
            fcalls = [p["functionCall"] for p in parts if "functionCall" in p]
            if not fcalls:
                yield {"type": "usage", "content": usage}
                return

            fresps = []
            for fc in fcalls:
                yield {"type": "tool_start", "content": fc['name']}
                res = call_function(fc, workspace_dir)
                fresps.append(res)
            messages.append({"role": "function", "parts": fresps})

        elif provider == "ollama":
            url = "http://localhost:11434/api/chat"
            ollama_messages = [{"role": "system", "content": system_prompt}]
            for m in messages:
                role = "assistant" if m["role"] == "model" else m["role"]
                role = "tool" if m["role"] == "function" else role
                content = ""
                tcalls = []
                for p in m.get("parts", []):
                    if "text" in p: content += p["text"]
                    if "functionCall" in p:
                        fc = p["functionCall"]
                        tcalls.append({"type": "function", "function": {"name": fc["name"], "arguments": fc.get("args", {})}})
                    if "functionResponse" in p:
                        content = str(p["functionResponse"].get("response", {}).get("content", ""))
                
                msg = {"role": role, "content": content}
                if tcalls: msg["tool_calls"] = tcalls
                ollama_messages.append(msg)

            payload = {
                "model": model_name, "messages": ollama_messages, "stream": False, 
                "think": think, "tools": ollama_tools
            }
            
            data = None
            with httpx.Client(timeout=60.0) as client:
                try:
                    resp = client.post(url, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    yield {"type": "error", "content": f"Ollama Error: {e}"}
                    return

            u_p = data.get("prompt_eval_count", 0)
            u_c = data.get("eval_count", 0)
            usage["prompt_tokens"] += u_p
            usage["candidate_tokens"] += u_c
            usage["total_tokens"] += (u_p + u_c)

            msg_obj = data.get("message", {})
            thinking = msg_obj.get("thinking", "")
            if thinking:
                yield {"type": "thought", "content": thinking.strip()}
            
            text = msg_obj.get("content", "")
            if text:
                yield {"type": "text", "content": text}
            
            fcalls = msg_obj.get("tool_calls", [])
            
            parts = [{"text": text}] if text else []
            for tc in fcalls:
                fn = tc.get("function", {})
                parts.append({"functionCall": {"name": fn.get("name"), "args": fn.get("arguments", {})}})
            
            messages.append({"role": "model", "parts": parts})
            
            if not fcalls:
                yield {"type": "usage", "content": usage}
                return

            fresps = []
            for tc in fcalls:
                fn = tc.get("function", {})
                name = fn.get("name")
                yield {"type": "tool_start", "content": name}
                res = call_function({"name": name, "args": fn.get("arguments", {})}, workspace_dir)
                fresps.append(res)
            messages.append({"role": "function", "parts": fresps})

        elif provider == "cloudflare":
            api_key = os.environ.get("CF_AI_KEY")
            account_id = os.environ.get("CF_ACCOUNT_ID", "949e65768e0cfe07367790a75a98b98b")
            if not api_key:
                yield {"type": "error", "content": "Error: CF_AI_KEY unset in .env"}
                return
            
            current_model = model_name if "/" in model_name else f"@cf/meta/{model_name}"
            if model_name == "llama-3-8b-instruct":
                 current_model = "@cf/meta/llama-3-8b-instruct"

            url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{current_model}"
            headers = {"Authorization": f"Bearer {api_key}"}
            
            cf_messages = [{"role": "system", "content": system_prompt}]
            for m in messages:
                role = "assistant" if m["role"] == "model" else m["role"]
                role = "tool" if m["role"] == "function" else role
                content = ""
                for p in m.get("parts", []):
                    if "text" in p: content += p["text"]
                    if "functionResponse" in p:
                        content = str(p["functionResponse"].get("response", {}).get("content", ""))
                cf_messages.append({"role": role, "content": content})
            
            # CF Workers AI Tool support is limited/non-standard in basic run. 
            # We treat it as text-only for now unless it supports OpenAI-style tools.
            payload = {"messages": cf_messages}
            
            with httpx.Client(timeout=60.0) as client:
                try:
                    resp = client.post(url, json=payload, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    yield {"type": "error", "content": f"Cloudflare Error: {e}"}
                    return
            
            if not data.get("success"):
                errs = data.get("errors", [])
                err_msg = errs[0].get("message") if errs else "Unknown error"
                yield {"type": "error", "content": f"Cloudflare API Error: {err_msg}"}
                return
            
            result = data.get("result", {})
            text = result.get("response", "")
            if text:
                yield {"type": "text", "content": text}
                messages.append({"role": "model", "parts": [{"text": text}]})
            
            yield {"type": "usage", "content": usage}
            return

        elif provider == "openrouter":
            import uuid
            api_key = os.environ.get("OPENROUTER_API_KEY")
            if not api_key:
                yield {"type": "error", "content": "Error: OPENROUTER_API_KEY unset in .env"}
                return
            
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://github.com/schallten/Rta",
                "X-OpenRouter-Title": "Rta CLI",
                "X-Title": "Rta CLI"
            }
            
            # All models get tools; only legacy openrouter/free (no model path) is text-only
            supports_tools = model_name != "openrouter/free"
            
            # Build message list in strict OpenAI format
            openrouter_messages = [{"role": "system", "content": system_prompt}]
            for m in messages:
                if m["role"] == "function":
                    if not supports_tools:
                        # For no-tool models, flatten tool results as user messages
                        for p in m.get("parts", []):
                            if "functionResponse" in p:
                                fr = p["functionResponse"]
                                content = str(fr.get("response", {}).get("content", ""))
                                openrouter_messages.append({"role": "user", "content": f"[Tool result for {fr.get('name', '?')}]: {content}"})
                        continue
                    # Tool responses: each its own message with a valid tool_call_id
                    for p in m.get("parts", []):
                        if "functionResponse" in p:
                            fr = p["functionResponse"]
                            call_id = fr.get("call_id") or "call_unknown"
                            openrouter_messages.append({
                                "role": "tool",
                                "tool_call_id": call_id,
                                "name": fr.get("name", "unknown"),
                                "content": str(fr.get("response", {}).get("content", ""))
                            })
                    continue

                role = "assistant" if m["role"] == "model" else m["role"]
                content = ""
                tcalls = []
                for p in m.get("parts", []):
                    if "text" in p:
                        content += p["text"]
                    if "functionCall" in p and supports_tools:
                        fc = p["functionCall"]
                        # Robust ID handling: reuse existing ID, or generate and PERSIST it
                        call_id = fc.get("id")
                        if not call_id:
                            call_id = f"call_{uuid.uuid4().hex[:8]}"
                            fc["id"] = call_id
                        
                        tcalls.append({
                            "id": call_id,
                            "type": "function",
                            "function": {
                                "name": fc["name"],
                                "arguments": json.dumps(fc.get("args", {}))
                            }
                        })
                msg = {"role": role}
                if content or not tcalls:
                    msg["content"] = content
                if tcalls:
                    msg["tool_calls"] = tcalls
                openrouter_messages.append(msg)
            
            models_to_try = [model_name]
            fallbacks = ["nvidia/nemotron-3-super-120b-a12b:free", "openrouter/elephant-alpha", "google/gemma-4-26b-a4b-it:free", "z-ai/glm-4.5-air:free", "openai/gpt-oss-120b:free", "openrouter/free"]
            for f in fallbacks:
                if f not in models_to_try: models_to_try.append(f)

            payload = {"messages": openrouter_messages}
            if supports_tools:
                payload["tools"] = ollama_tools
                payload["tool_choice"] = "auto"
            
            data = None
            success = False
            with httpx.Client(timeout=60.0) as client:
                for current_m in models_to_try:
                    payload["model"] = current_m
                    # Re-check tool support for fallback models
                    if current_m == "openrouter/free":
                        if "tools" in payload: del payload["tools"]
                    elif "tools" not in payload and supports_tools:
                        payload["tools"] = ollama_tools

                    for attempt in range(2):
                        try:
                            resp = client.post(url, json=payload, headers=headers)
                            if resp.status_code == 429:
                                time.sleep(2 ** attempt)
                                continue
                            if resp.status_code == 400:
                                # If 400, might be model-specific payload issues, try next model
                                break 
                            resp.raise_for_status()
                            data = resp.json()
                            success = True
                            break
                        except Exception:
                            if attempt < 1: time.sleep(1)
                            continue
                    if success: break
                    yield {"type": "text", "content": f"*(Model `{current_m}` failed/busy, trying fallback...)*"}
                
                if not success:
                    yield {"type": "error", "content": "All OpenRouter models failed/busy."}
                    return
            
            usage_data = data.get("usage", {})
            u_p = usage_data.get("prompt_tokens", 0)
            u_c = usage_data.get("completion_tokens", 0)
            # OpenRouter / OpenAI format caching
            u_cached = usage_data.get("prompt_tokens_details", {}).get("cached_tokens", 0)
            # Some providers might use different fields in OpenRouter
            if not u_cached:
                u_cached = data.get("extra_fields", {}).get("native_tokens_prompt_cached", 0)

            usage["prompt_tokens"] += u_p
            usage["candidate_tokens"] += u_c
            usage["total_tokens"] += (u_p + u_c)
            usage["cached_tokens"] += u_cached

            choice = data.get("choices", [{}])[0]
            msg = choice.get("message", {})
            text = msg.get("content") or ""
            # Free models don't return structured tool_calls
            fcalls = msg.get("tool_calls") or [] if supports_tools else []
            
            parts = []
            if text:
                parts.append({"text": text})
                yield {"type": "text", "content": text}
            
            for tc in fcalls:
                fn = tc.get("function", {})
                name = fn.get("name")
                # Always guarantee a valid string ID
                call_id = tc.get("id") or f"call_{uuid.uuid4().hex[:8]}"
                args = {}
                try:
                    args = json.loads(fn.get("arguments", "{}"))
                except Exception:
                    pass
                parts.append({"functionCall": {"name": name, "args": args, "id": call_id}})
            
            messages.append({"role": "model", "parts": parts})
            
            if not fcalls:
                yield {"type": "usage", "content": usage}
                return

            fresps = []
            for tc in fcalls:
                fn = tc.get("function", {})
                name = fn.get("name")
                call_id = tc.get("id") or f"call_{uuid.uuid4().hex[:8]}"
                args = {}
                try:
                    args = json.loads(fn.get("arguments", "{}"))
                except Exception:
                    pass
                
                # Yield and call function
                yield {"type": "tool_start", "content": name}
                res = call_function({"name": name, "args": args}, workspace_dir)
                res["functionResponse"]["call_id"] = call_id
                
                # Sync the ID back to the 'model' message parts we just appended
                for p in parts:
                    if "functionCall" in p and p["functionCall"]["name"] == name and not p["functionCall"].get("id"):
                        p["functionCall"]["id"] = call_id
                
                fresps.append(res)
            messages.append({"role": "function", "parts": fresps})

    yield {"type": "error", "content": "Max iterations reached."}
    yield {"type": "usage", "content": usage}

def run_agent(prompt: str, workspace_dir: str, messages: list[dict], provider: str = "openrouter", model_name: str = "nvidia/nemotron-3-super-120b-a12b:free", max_iterations: int = 20, think: bool = False) -> tuple[str, dict]:
    # Compatibility wrapper
    final_text = ""
    last_usage = {}
    for event in stream_agent(prompt, workspace_dir, messages, provider, model_name, max_iterations, think):
        if event["type"] == "text":
            final_text += event["content"] + "\n\n"
        elif event["type"] == "tool_start":
            final_text += f"*(Executed tool: `{event['content']}`)*\n\n"
        elif event["type"] == "thought":
            final_text += f"> *{event['content']}*\n\n"
        elif event["type"] == "usage":
            last_usage = event["content"]
        elif event["type"] == "error":
            return f"Error: {event['content']}", {}
    
    return final_text.strip(), last_usage
