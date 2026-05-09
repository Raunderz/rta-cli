import subprocess
import os
from rta_cli.discovery import discover_project, get_test_command, get_lint_command

def run_command(working_directory, command, timeout=120, force=False):
    abs_working_dir = os.path.abspath(working_directory)
    
    cmd_lower = command.lower().strip()
    if cmd_lower in ("run tests", "test"):
        info = discover_project(abs_working_dir)
        discovered = get_test_command(info)
        if discovered:
            command = discovered
            print(f"Auto-discovered test command: {command}")
    elif cmd_lower in ("run lint", "lint"):
        info = discover_project(abs_working_dir)
        discovered = get_lint_command(info)
        if discovered:
            command = discovered
            print(f"Auto-discovered lint command: {command}")

    try:
        output = subprocess.run(command, shell=True, cwd=abs_working_dir, timeout=timeout, capture_output=True, text=True)

        final_string = (
            f"STDOUT : {output.stdout}\n"
            f"STDERR : {output.stderr}\n"
            f"RETURN CODE : {output.returncode}\n"
        )

        if not output.stdout and not output.stderr:
            final_string += "Process exited with no output\n"
        
        return final_string

    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds."
    except Exception as e:
        return f"Error executing command : {e}"

schema_run_command = {
    "name": "run_command",
    "description": "Runs a general shell command in the working directory and returns the output",
    "parameters": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute",
            },
        },
        "required": ["command"],
    },
}
