import subprocess
import os

def grep_search(working_directory, pattern, path=".", timeout=30):
    abs_working_dir = os.path.abspath(working_directory)
    abs_path = os.path.abspath(os.path.join(abs_working_dir, path))
    
    if not abs_path.startswith(abs_working_dir):
        return f"Error: Path '{path}' is outside the working directory."

    try:
        # Use grep -rn (recursive, line numbers)
        # We use a list for security, though we are in a controlled environment
        command = ["grep", "-rn", pattern, abs_path]
        output = subprocess.run(command, capture_output=True, text=True, timeout=timeout)

        if output.returncode == 0:
            return output.stdout
        elif output.returncode == 1:
            return "No matches found."
        else:
            return f"Error executing grep: {output.stderr}"

    except subprocess.TimeoutExpired:
        return "Error: Grep search timed out."
    except Exception as e:
        return f"Error: {e}"

schema_grep_search = {
    "name": "grep_search",
    "description": "Searches for a pattern in files within a specified path (recursive)",
    "parameters": {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "The regex or string pattern to search for",
            },
            "path": {
                "type": "string",
                "description": "The directory or file to search in, relative to the working directory (default is '.')",
            },
        },
        "required": ["pattern"],
    },
}
