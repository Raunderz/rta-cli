import os
from google.genai import types

def write_file(working_directory,file_path,content):
    abs_working_dir = os.path.abspath(working_directory)
    abs_file_path = os.path.abspath(os.path.join(working_directory,file_path))
    if not abs_file_path.startswith(abs_working_dir):
        return f"Error : {file_path} is not in the working directory"

    parent_dir = os.path.dirname(abs_file_path)
    if not os.path.isdir(parent_dir):
        try:
            os.makedirs(parent_dir,exist_ok=True)
        except Exception as e:
            return f"Error : could not create parent directory {parent_dir} : {e}"

    try:
        with open(abs_file_path,"w") as f:
            f.write(content)
        return f"Successfully wrote to {file_path} ( {len(content)} characters written )"
    except Exception as e:
        return f"Failed to write the file {file_path} : {e}"

schema_write_file = types.FunctionDeclaration(
    name="write_file",
    description="Writes content to a specified file relative to the working directory. (and creates parent directories if needed), overwrites or writes to a new file if it doesn't exist.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="Path to the file to write to, relative to the working directory",
            ),
            "content": types.Schema(
                type=types.Type.STRING,
                description="Content to write to the file",
            ),
        },
    ),
)
