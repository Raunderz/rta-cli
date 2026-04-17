import os
from google.genai import types

def get_files_info(working_directory,directory=None):
    abs_working_dir = os.path.abspath(working_directory)
    
    abs_directory = ""
    if directory is None:
        abs_directory = abs_working_dir
    else:
        abs_directory = os.path.abspath(os.path.join(abs_working_dir, directory))
    
    if not abs_directory.startswith(abs_working_dir):
        return f'Error: "{directory}" is not in the working directory'

    try:
        final_response = ""
        contents = os.listdir(abs_directory)
        for content in contents:
            content_path = os.path.join(abs_directory,content)
            is_dir = os.path.isdir(content_path)
            size = os.path.getsize(content_path)
            final_response += f" - {content} : file_size = {size} bytes, is_dir={is_dir}\n"
        
        return final_response
    except Exception as e:
        return f"Error: {e}"

schema_get_files_info = types.FunctionDeclaration(
    name="get_files_info",
    description="Lists files in a specified directory relative to the working directory, providing file size and directory status",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "directory": types.Schema(
                type=types.Type.STRING,
                description="Directory path to list files from, relative to the working directory (default is the working directory itself)",
            ),
        },
    ),
)