import subprocess
import os
from rta_cli.safety import GitignoreFilter


def grep_search(working_directory, pattern, path=".", timeout=30, allow_ignored=False):
    abs_working_dir = os.path.abspath(working_directory)
    abs_path = os.path.abspath(os.path.join(abs_working_dir, path))
    gf = GitignoreFilter(abs_working_dir)

    if not abs_path.startswith(abs_working_dir):
        return f"Error: Path '{path}' is outside the working directory."

    if gf.is_ignored(abs_path, allow_ignored=allow_ignored):
        return f"Error : {path} is ignored by .gitignore. (PERMISSION_REQUIRED)"

    try:
        # Use grep -rn (recursive, line numbers)
        # We use a list for security, though we are in a controlled environment
        command = ["grep", "-rn", pattern, abs_path]

        # Add --exclude-dir for common ignored directories if not bypassing
        if not allow_ignored:
            for p in gf.patterns:
                if p.endswith("/"):
                    command.append(f"--exclude-dir={p[:-1]}")
                else:
                    command.append(f"--exclude={p}")

        output = subprocess.run(
            command, capture_output=True, text=True, timeout=timeout
        )
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
