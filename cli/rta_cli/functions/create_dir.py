import os

def create_dir(working_directory, dir_path):
    abs_working_dir = os.path.abspath(working_directory)
    abs_dir_path = os.path.abspath(os.path.join(working_directory, dir_path))
    if not abs_dir_path.startswith(abs_working_dir):
        return f"Error: {dir_path} is not in the working directory"

    try:
        os.makedirs(abs_dir_path, exist_ok=True)
        return f"Successfully created directory {dir_path}"
    except Exception as e:
        return f"Failed to create directory {dir_path}: {e}"

schema_create_dir = {
    "name": "create_dir",
    "description": "Creates a directory (and parent directories if needed) relative to the working directory.",
    "parameters": {
        "type": "object",
        "properties": {
            "dir_path": {
                "type": "string",
                "description": "Path to the directory to create, relative to the working directory",
            },
        },
    },
}