import os

def write_file(working_directory, file_path, content, overwrite=True):
    abs_working_dir = os.path.abspath(working_directory)
    abs_file_path = os.path.abspath(os.path.join(working_directory, file_path))
    if not abs_file_path.startswith(abs_working_dir):
        return f"Error : {file_path} is not in the working directory"

    parent_dir = os.path.dirname(abs_file_path)
    if not os.path.isdir(parent_dir):
        try:
            os.makedirs(parent_dir, exist_ok=True)
        except Exception as e:
            return f"Error : could not create parent directory {parent_dir} : {e}"

    try:
        # Check if file exists and we are not allowed to overwrite
        if os.path.exists(abs_file_path) and not overwrite:
            return f"Error: File {file_path} already exists and overwrite is set to False."

        with open(abs_file_path, "w") as f:
            f.write(content)
        return f"Successfully wrote to {file_path} ( {len(content)} characters written )"
    except Exception as e:
        return f"Failed to write the file {file_path} : {e}"

schema_write_file = {
    "name": "write_file",
    "description": "Writes content to a specified file relative to the working directory. Overwrites by default.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to write to, relative to the working directory",
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file",
            },
            "overwrite": {
                "type": "boolean",
                "description": "Whether to overwrite the file if it exists. Defaults to true.",
            },
        },
        "required": ["file_path", "content"],
    },
}
