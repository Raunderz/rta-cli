import os
from rta_cli.config import MAX_CHARS
from rta_cli.safety import GitignoreFilter

def get_file_contents(working_directory,file_path, allow_ignored=False):
    abs_working_dir = os.path.abspath(working_directory)
    abs_file_path = os.path.abspath(os.path.join(working_directory,file_path))
    gf = GitignoreFilter(abs_working_dir)

    if not abs_file_path.startswith(abs_working_dir):
        return f"Error : {file_path} is not in the working directory"

    if gf.is_ignored(abs_file_path, allow_ignored=allow_ignored):
        return f"Error : {file_path} is ignored by .gitignore. (PERMISSION_REQUIRED)"

    if not os.path.isfile(abs_file_path):        return f"Error : {file_path} is not a file"
...

    try:
        with open(abs_file_path,"r") as f:
            file_content_string = f.read(MAX_CHARS)
            if len(file_content_string) >= MAX_CHARS:
                file_content_string += f"[...File {file_path} truncated at {MAX_CHARS} characters...]"

        return file_content_string
    except Exception as e:
        return f"Error : {e}"

schema_get_file_contents = {
    "name": "get_file_contents",
    "description": "Reads the contents of a specified file relative to the working directory",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to read, relative to the working directory",
            },
        },
    },
}