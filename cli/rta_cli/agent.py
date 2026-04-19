import os
import sys
import json
import httpx
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

def run_agent(prompt: str, workspace_dir: str, messages: list[dict], max_iterations: int = 20) -> str:
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY environment variable not set."

    messages.append({
        "role": "user",
        "parts": [{"text": prompt}]
    })

    system_prompt = (
        "You are an expert AI software engineer.\n"
        "When a user asks a question or makes a request, work systematically:\n"
        "1. Explore the current directory to understand the project structure and find relevant files.\n"
        "2. Read and understand the contents of those files.\n"
        "3. Reproduce the bug or issue.\n"
        "4. Implement a fix.\n"
        "5. Verify the fix by running relevant code or tests.\n\n"
        "You can perform the following operations:\n"
        "- List files and directories: get_files_info(directory=\"path\")\n"
        "- Read the contents of a file: get_file_contents(file_path=\"path\")\n"
        "- Run a Python file: run_python_file(file_path=\"path\", args=[\"arg1\", \"arg2\"])\n"
        "- Write content to a file: write_file(file_path=\"path\", content=\"content\")\n\n"
        "All paths you provide should be relative to the current working directory."
    )

    available_functions = [
        schema_get_files_info,
        schema_get_file_contents,
        schema_run_python_file,
        schema_write_file,
    ]

    if hasattr(sys, '_MEIPASS'):
        config_path = os.path.join(sys._MEIPASS, 'rta_cli', 'config.json')
    else:
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    
    model_name = "gemini-2.5-flash"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            model_name = json.load(f).get("model", model_name)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    for i in range(max_iterations):
        payload = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": messages,
            "tools": [{"functionDeclarations": available_functions}]
        }

        with httpx.Client(timeout=60.0) as client:
            try:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPError as e:
                return f"HTTP error during Gemini API call: {e}"
            except json.JSONDecodeError:
                return "Failed to parse JSON response from Gemini API"

        candidates = data.get("candidates", [])
        if not candidates:
            return "response is malformed or empty"

        content = candidates[0].get("content", {})
        messages.append(content)

        parts = content.get("parts", [])
        
        function_calls = [p["functionCall"] for p in parts if "functionCall" in p]
        
        if function_calls:
            function_responses = []
            for function_call in function_calls:
                tool_part = call_function(function_call, workspace_dir)
                function_responses.append(tool_part)
            
            messages.append({
                "role": "function",
                "parts": function_responses
            })
        else:
            texts = [p["text"] for p in parts if "text" in p]
            return "".join(texts)

    return "Error: Maximum iterations reached without a final response."
