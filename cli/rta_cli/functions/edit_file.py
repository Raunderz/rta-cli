import os


def edit_file(working_directory, file_path, old_string, new_string):
    abs_working_dir = os.path.abspath(working_directory)
    abs_file_path = os.path.abspath(os.path.join(working_directory, file_path))
    if not abs_file_path.startswith(abs_working_dir):
        return f"Error: {file_path} is not in the working directory"
    if not os.path.isfile(abs_file_path):
        return f"Error: {file_path} is not a file"

    try:
        with open(abs_file_path, "r") as f:
            content = f.read()

        if old_string not in content:
            return f"Error: old_string not found in {file_path}"

        new_content = content.replace(old_string, new_string, 1)

        with open(abs_file_path, "w") as f:
            f.write(new_content)

        return f"Successfully edited {file_path}"
    except Exception as e:
        return f"Failed to edit {file_path}: {e}"


schema_edit_file = {
    "name": "edit_file",
    "description": "Replaces a specific string in a file with new content. Only replaces the first occurrence.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to edit, relative to the working directory",
            },
            "old_string": {
                "type": "string",
                "description": "The string to find and replace",
            },
            "new_string": {
                "type": "string",
                "description": "The new string to replace it with",
            },
        },
    },
}
