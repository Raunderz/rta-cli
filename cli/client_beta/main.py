import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types
from functions.get_file_content import schema_get_file_contents
from functions.get_files_info import schema_get_files_info
from functions.run_python_file import schema_run_python_file
from functions.write_file import schema_write_file
from call_function import call_function

def main():
    load_dotenv()
    api_key =  os.environ.get("GEMINI_API_KEY")

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

    if len(sys.argv) < 2:
        print("Usage: python main.py <prompt>")
        return

    if len(sys.argv) == 3 and sys.argv[2] == "--verbose":
        verbose_flag = True
    else:
        verbose_flag = False
        

    prompt = sys.argv[1]

    messages = [types.Content(role="user",parts=[types.Part(text=prompt)]),]

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

    for i in range(20):
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=messages,
            config=config,
        )

        if response is None or response.candidates is None or not response.candidates:
            print("response is malformed")
            return

        # Add the model's primary response to conversation history
        messages.append(response.candidates[0].content)

        if response.function_calls:
            function_responses = []
            for function_call in response.function_calls:
                tool_content = call_function(function_call, verbose_flag)
                function_responses.extend(tool_content.parts)
            
            # Add all function responses as a single "tool" role message
            messages.append(types.Content(role="tool", parts=function_responses))
        else:
            print(f"Final response:\n{response.text}")
            return

    print("Error: Maximum iterations reached without a final response.")
    sys.exit(1)

main()