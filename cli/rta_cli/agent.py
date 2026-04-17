import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

from rta_cli.functions.get_file_content import get_file_contents, schema_get_file_contents
from rta_cli.functions.get_files_info import get_files_info, schema_get_files_info
from rta_cli.functions.run_python_file import run_python_file, schema_run_python_file
from rta_cli.functions.write_file import write_file, schema_write_file

def call_function(function_call_part, workspace_dir: str):
    if function_call_part.name == "get_files_info":
        result = get_files_info(workspace_dir, **function_call_part.args)
    elif function_call_part.name == "get_file_contents":
        result = get_file_contents(workspace_dir, **function_call_part.args)
    elif function_call_part.name == "run_python_file":
        result = run_python_file(workspace_dir, **function_call_part.args)
    elif function_call_part.name == "write_file":
        result = write_file(workspace_dir, **function_call_part.args)
    else:
        result = f"Error: function {function_call_part.name} not found"

    return types.Content(
        role="tool",
        parts=[
            types.Part.from_function_response(
                name=function_call_part.name,
                response={"result": result},
            )
        ],
    )

def run_agent(prompt: str, workspace_dir: str, max_iterations: int = 15) -> str:
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    system_prompt = (
        """
        You are an expert AI software engineer.
        When a user asks a question or makes a request, work systematically:
        1. Explore the current directory to understand the project structure and find relevant files.
        2. Read and understand the contents of those files.
        3. Reproduce the bug or issue.
        4. Implement a fix.
        5. Verify the fix by running relevant code or tests.

        You can perform the following operations:
        - List files and directories: get_files_info(directory="path")
        - Read the contents of a file: get_file_contents(file_path="path")
        - Run a Python file: run_python_file(file_path="path", args=["arg1", "arg2"])
        - Write content to a file: write_file(file_path="path", content="content")

        All paths you provide should be relative to the current working directory.
        """
    )

    messages = [types.Content(role="user", parts=[types.Part(text=prompt)])]

    available_functions = types.Tool(
        function_declarations=[
            schema_get_files_info,
            schema_get_file_contents,
            schema_run_python_file,
            schema_write_file,
        ]
    )

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=[available_functions],
    )

    for i in range(max_iterations):
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=messages,
            config=config,
        )

        if response is None or response.candidates is None or not response.candidates:
            return "response is malformed or empty"

        messages.append(response.candidates[0].content)

        if response.function_calls:
            function_responses = []
            for function_call in response.function_calls:
                tool_content = call_function(function_call, workspace_dir)
                function_responses.extend(tool_content.parts)
            
            messages.append(types.Content(role="tool", parts=function_responses))
        else:
            return response.text

    return "Error: Maximum iterations reached without a final response."
