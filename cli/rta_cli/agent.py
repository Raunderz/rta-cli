import os
import sys
import json
import httpx
import time

import re
from dotenv import load_dotenv

from rta_cli.functions.get_file_content import get_file_contents, schema_get_file_contents
from rta_cli.functions.get_files_info import get_files_info, schema_get_files_info
from rta_cli.functions.run_python_file import run_python_file, schema_run_python_file
from rta_cli.functions.write_file import write_file, schema_write_file

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
    else:
        result = f"Error: function {name} not found"


    return {
        "functionResponse": {
            "name": name,
            "response": {"name": name, "content": result}
        }
    }

def run_agent(prompt: str, workspace_dir: str, messages: list[dict], provider: str = "google", model_name: str = "gemini-2.5-flash-lite", max_iterations: int = 20, think: bool = False) -> tuple[str, dict]:
    load_dotenv()
    usage = {"prompt_tokens": 0, "candidate_tokens": 0, "total_tokens": 0, "start_time": time.time()}
    final_output = ""
    
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
    ]

    ollama_tools = [{"type": "function", "function": f} for f in available_functions]

    # Add initial user prompt to messages if empty
    if not any(m["role"] == "user" for m in messages):
        messages.append({"role": "user", "parts": [{"text": prompt}]})

    for i in range(max_iterations):
        if provider == "google":
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key: return "Error: GEMINI_API_KEY unset", usage
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            payload = {
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "contents": messages,
                "tools": [{"functionDeclarations": available_functions}]
            }

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
                        return f"Google API Error: {e.response.status_code} - Resource exhausted or rate limited.", usage
                    except Exception as e:
                        return f"API Connection Error. Check your internet or API Key.", usage
                else:
                    return "Rate limit exceeded after multiple retries. Slow down!", usage


            usage_data = data.get("usageMetadata", {})
            usage["prompt_tokens"] += usage_data.get("promptTokenCount", 0)
            usage["candidate_tokens"] += usage_data.get("candidatesTokenCount", 0)
            usage["total_tokens"] += usage_data.get("totalTokenCount", 0)

            candidate = data.get("candidates", [{}])[0]
            reason = candidate.get("finishReason")
            if reason in ["SAFETY", "BLOCKed", "OTHER"]:
                return f"Response blocked by safety filters (Reason: {reason})", usage
            
            content = candidate.get("content", {})
            if not content: 
                if final_output.strip(): return final_output.strip(), usage
                return "The model returned an empty response.", usage


            messages.append(content)
            parts = content.get("parts", [])
            
            texts = [p["text"] for p in parts if "text" in p]
            if texts: final_output += "".join(texts) + "\n\n"
            
            fcalls = [p["functionCall"] for p in parts if "functionCall" in p]
            if not fcalls: 
                if not final_output.strip():
                    return "Model responded with no text or actions.", usage
                return final_output.strip(), usage

            
            fresps = []
            for fc in fcalls:
                final_output += f"*(Executed tool: `{fc['name']}`)*\n\n"
                fresps.append(call_function(fc, workspace_dir))
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
            
            with httpx.Client(timeout=60.0) as client:
                for attempt in range(3):
                    try:
                        resp = client.post(url, json=payload)
                        if resp.status_code == 429:
                            time.sleep(2 ** attempt)
                            continue
                        resp.raise_for_status()
                        data = resp.json()
                        break
                    except Exception as e:
                        if attempt < 2: continue
                        return "Ollama Error: Could not connect to local server.", usage
                else:
                    return "Ollama is too busy or rate limited.", usage


            usage["prompt_tokens"] += data.get("prompt_eval_count", 0)
            usage["candidate_tokens"] += data.get("eval_count", 0)
            usage["total_tokens"] += usage["prompt_tokens"] + usage["candidate_tokens"]

            msg_obj = data.get("message", {})
            thinking = msg_obj.get("thinking", "")
            if thinking: final_output += f"> *{thinking.strip()}*\n\n"
            
            text = msg_obj.get("content", "")
            if text: final_output += text + "\n\n"
            
            fcalls = msg_obj.get("tool_calls", [])
            
            # --- Regex Fallback for "stupid" models ---
            if not fcalls and text:
                pattern = r"(\w+)\((.*?)\)"
                matches = re.findall(pattern, text)
                for name, args_str in matches:
                    if name in [f["name"] for f in available_functions]:
                        try:
                            # Try to parse as JSON or simple dict
                            args_str = args_str.replace("'", '"')
                            args = json.loads(f"{{{args_str}}}") if ":" in args_str else {}
                            fcalls.append({"function": {"name": name, "arguments": args}})
                        except: pass
            
            parts = [{"text": text}] if text else []
            for tc in fcalls:
                fn = tc.get("function", {})
                parts.append({"functionCall": {"name": fn.get("name"), "args": fn.get("arguments", {})}})
            
            messages.append({"role": "model", "parts": parts})
            if not fcalls: 
                if not final_output.strip():
                    return "Ollama returned no text or tool calls.", usage
                return final_output.strip(), usage

            
            fresps = []
            for tc in fcalls:
                fn = tc.get("function", {})
                name = fn.get("name")
                final_output += f"*(Executed tool: `{name}`)*\n\n"
                fresps.append(call_function({"name": name, "args": fn.get("arguments", {})}, workspace_dir))
            messages.append({"role": "function", "parts": fresps})

    return final_output.strip() + "\nError: Max iterations.", usage
