import subprocess
import os

def run_python_file(working_directory,file_path,args=[]):
    abs_working_dir = os.path.abspath(working_directory)
    abs_file_path = os.path.abspath(os.path.join(working_directory,file_path))
    if not abs_file_path.startswith(abs_working_dir):
        return f"Error : {file_path} is not in the working directory"
    if not os.path.isfile(abs_file_path):
        return f"Error : {file_path} is not a file"

    if not file_path.endswith(".py"):
        return f'Error : {file_path} is not a python file'

    try:
        final_args = ["python3",file_path]
        final_args.extend(args)
        output = subprocess.run(final_args, cwd=abs_working_dir, timeout=30, capture_output=True, text=True)

        final_string = (
            f"STDOUT : {output.stdout}\n"
            f"STDERR : {output.stderr}\n"
            f"RETURN CODE : {output.returncode}\n"
        )

        if not output.stdout and not output.stderr:
            final_string += "Process exited with no output\n"
        
        return final_string

    except Exception as e:
        return f"Error executing python file : {e}"

schema_run_python_file = {
    "name": "run_python_file",
    "description": "Runs a Python file with optional arguments,using python3 interpreter, relative to the working directory",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the Python file to run, relative to the working directory",
            },
            "args": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Arguments to pass to the Python file",
            },
        },
    },
}