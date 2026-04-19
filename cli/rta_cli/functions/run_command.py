import subprocess
import os

def run_command(working_directory, command):
    abs_working_dir = os.path.abspath(working_directory)
    
    try:
        # We run the command via shell for flexibility, but within the working directory
        output = subprocess.run(command, shell=True, cwd=abs_working_dir, timeout=60, capture_output=True, text=True)

        final_string = (
            f"STDOUT : {output.stdout}\n"
            f"STDERR : {output.stderr}\n"
            f"RETURN CODE : {output.returncode}\n"
        )

        if not output.stdout and not output.stderr:
            final_string += "Process exited with no output\n"
        
        return final_string

    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 60 seconds."
    except Exception as e:
        return f"Error executing command : {e}"

schema_run_command = {
    "name": "run_command",
    "description": "Runs a general shell command in the working directory and returns the output",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "command": {
                "type": "STRING",
                "description": "The shell command to execute",
            },
        },
        "required": ["command"],
    },
}
