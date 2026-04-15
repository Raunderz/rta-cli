import os

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
        return f"Sucessfully wrote to {file_path} ( {len(content)} characters written )"
    except Exception as e:
        return f"Failed to write the file {file_path} : {e}"