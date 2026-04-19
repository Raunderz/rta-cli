import os
import sys
import json
import httpx
import toons
import time
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

    if name in ["get_files_info"]:
        result = toons.dumps(result)
        
    return {
        "functionResponse": {
            "name": name,
            "response": {"name": name, "content": result}
        }
    }

def run_agent(prompt: str, workspace_dir: str, messages: list[dict], provider: str = "google", model_name: str = "gemini-2.5-flash-lite", max_iterations: int = 20) -> tuple[str, dict]:
    load_dotenv()
    usage = {"prompt_tokens": 0, "candidate_tokens": 0, "total_tokens": 0, "start_time": time.time()}
    final_output = ""
    
    system_prompt = (
        "You are an expert AI software engineer. Respond in Caveman Lite mode (no filler/hedging, fragments OK, professional but tight).\n"
        "All data communication uses TOON format for efficiency.\n\n"
        "## TOON Rules:\n"
        "- Objects: key: value (no braces, 2-space indent for nesting)\n"
        "- Arrays: tags[3]: admin,ops,dev (always declare length [N])\n"
        "- Array of objects: users[2]{id,name}: 1,Alice \\n 2,Bob\n"
        "- Escape: \\\\, \\\", \\n, \\r, \\t\n\n"
        "Work systematically: explore → read → reproduce → fix → verify.\n"
        "Operations:\n"
        "- get_files_info(directory=\"path\")\n"
        "- get_file_contents(file_path=\"path\")\n"
        "- run_python_file(file_path=\"path\", args=[\"arg1\", \"arg2\"])\n"
        "- write_file(file_path=\"path\", content=\"content\")\n\n"
        "All paths relative to CWD."
    )

    available_functions = [
        schema_get_files_info,
        schema_get_file_contents,
        schema_run_python_file,
        schema_write_file,
    ]

    for i in range(max_iterations):
        if provider == "google":
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key: return "Error: GEMINI_API_KEY unset", usage
            
            if not any(m["role"] == "user" and m["parts"][0].get("text") == prompt for m in messages[-2:]):
                messages.append({"role": "user", "parts": [{"text": prompt}]})

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            payload = {
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "contents": messages,
                "tools": [{"functionDeclarations": available_functions}]
            }

            with httpx.Client(timeout=60.0) as client:
                try:
                    resp = client.post(url, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e: return f"Google API Error: {e}", usage

            usage_data = data.get("usageMetadata", {})
            usage["prompt_tokens"] += usage_data.get("promptTokenCount", 0)
            usage["candidate_tokens"] += usage_data.get("candidatesTokenCount", 0)
            usage["total_tokens"] += usage_data.get("totalTokenCount", 0)

            candidate = data.get("candidates", [{}])[0]
            content = candidate.get("content", {})
            messages.append(content)
            parts = content.get("parts", [])
            
            texts = [p["text"] for p in parts if "text" in p]
            if texts: final_output += "".join(texts) + "\n\n"
            
            fcalls = [p["functionCall"] for p in parts if "functionCall" in p]
            if not fcalls: return final_output.strip(), usage
            
            fresps = []
            for fc in fcalls:
                final_output += f"*(Executed tool: `{fc['name']}`)*\n\n"
                fresps.append(call_function(fc, workspace_dir))
            messages.append({"role": "function", "parts": fresps})

        elif provider == "ollama":
            url = "http://localhost:11434/api/chat"
            # Map Gemini messages to Ollama format
            ollama_messages = [{"role": "system", "content": system_prompt}]
            for m in messages:
                role = "assistant" if m["role"] == "model" else m["role"]
                # Simplify parts to string for basic Ollama compatibility
                content = ""
                for p in m.get("parts", []):
                    if "text" in p: content += p["text"]
                ollama_messages.append({"role": role, "content": content})
            
            # Add current prompt if not in history
            ollama_messages.append({"role": "user", "content": prompt})

            payload = {"model": model_name, "messages": ollama_messages, "stream": False}
            
            with httpx.Client(timeout=60.0) as client:
                try:
                    resp = client.post(url, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e: return f"Ollama Error: {e}", usage

            usage["prompt_tokens"] += data.get("prompt_eval_count", 0)
            usage["candidate_tokens"] += data.get("eval_count", 0)
            usage["total_tokens"] += usage["prompt_tokens"] + usage["candidate_tokens"]

            res_text = data.get("message", {}).get("content", "")
            final_output += res_text
            # Tool calling not yet mapped for Ollama in this simplified version
            return final_output.strip(), usage

    return final_output.strip() + "\nError: Max iterations.", usage
