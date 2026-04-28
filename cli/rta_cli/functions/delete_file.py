import os
import shutil

def delete_file(working_directory, file_path):
    abs_working_dir = os.path.abspath(working_directory)
    abs_file_path = os.path.abspath(os.path.join(working_directory, file_path))
    if not abs_file_path.startswith(abs_working_dir):
        return f"Error: {file_path} is not in the working directory"
    if not os.path.isfile(abs_file_path):
        return f"Error: {file_path} is not a file"

    try:
        os.remove(abs_file_path)
        return f"Successfully deleted {file_path}"
    except Exception as e:
        return f"Failed to delete {file_path}: {e}"

schema_delete_file = {
    "name": "delete_file",
    "description": "Deletes a specified file from the working directory.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to delete, relative to the working directory",
            },
        },
    },
}