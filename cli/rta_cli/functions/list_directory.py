import os

def list_directory(working_directory, dir_path=""):
    abs_working_dir = os.path.abspath(working_directory)
    abs_dir_path = os.path.abspath(os.path.join(working_directory, dir_path))
    if not abs_dir_path.startswith(abs_working_dir):
        return f"Error: {dir_path} is not in the working directory"
    if not os.path.isdir(abs_dir_path):
        return f"Error: {dir_path} is not a directory"

    try:
        entries = os.listdir(abs_dir_path)
        result = []
        for entry in sorted(entries):
            entry_path = os.path.join(abs_dir_path, entry)
            if os.path.isdir(entry_path):
                result.append(f"{entry}/")
            else:
                size = os.path.getsize(entry_path)
                result.append(f"{entry} ({size})")
        return "\n".join(result)
    except Exception as e:
        return f"Failed to list directory {dir_path}: {e}"

schema_list_directory = {
    "name": "list_directory",
    "description": "Lists files and directories in a specified directory, showing directories with trailing / and files with their sizes.",
    "parameters": {
        "type": "object",
        "properties": {
            "dir_path": {
                "type": "string",
                "description": "Path to the directory to list, relative to the working directory (empty for root)",
            },
        },
    },
}