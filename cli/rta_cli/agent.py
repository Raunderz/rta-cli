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
    else:
        result = f"Error: function {name} not found"

    return {
        "functionResponse": {
            "name": name,
            "response": {"name": name, "content": result}
        }
    }

def stream_agent(prompt: str, workspace_dir: str, messages: list[dict], provider: str = "google", model_name: str = "gemini-2.5-flash-lite", max_iterations: int = 20, think: bool = False) -> Generator[dict, None, None]:
    load_dotenv()
    usage = {"prompt_tokens": 0, "candidate_tokens": 0, "total_tokens": 0, "start_time": time.time()}
    
    system_prompt = (
        "Respond in Caveman Lite mode (no filler/hedging, fragments OK, professional but tight).\n"
        "Work systematically: explore → read → reproduce → fix → verify.\n"
        "All paths are relative to the current workspace."
    )

    available_functions = [
        schema_get_files_info,
        schema_get_file_contents,
        schema_run_python_file,
        schema_write_file,
        schema_run_command,
        schema_grep_search,
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

    yield {"type": "error", "content": "Max iterations reached."}
    yield {"type": "usage", "content": usage}

def run_agent(prompt: str, workspace_dir: str, messages: list[dict], provider: str = "google", model_name: str = "gemini-2.5-flash-lite", max_iterations: int = 20, think: bool = False) -> tuple[str, dict]:
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
