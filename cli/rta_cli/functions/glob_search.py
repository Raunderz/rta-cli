import os
import glob
from rta_cli.config import MAX_CHARS

def glob_search(working_directory, pattern):
    abs_working_dir = os.path.abspath(working_directory)
    try:
        # Use glob with root_dir if available (Python 3.10+), else fallback
        try:
            matches = glob.glob(pattern, root_dir=abs_working_dir, recursive=True)
        except TypeError:
            # Fallback for older Python versions
            abs_pattern = os.path.join(abs_working_dir, pattern)
            matches = glob.glob(abs_pattern, recursive=True)
            # Ensure matches are within the working directory
            matches = [m for m in matches if os.path.commonpath([m, abs_working_dir]) == abs_working_dir]
        
        # Convert to relative paths for cleaner output
        relative_matches = [os.path.relpath(m, abs_working_dir) for m in matches]
        # Sort for consistent output
        relative_matches.sort()
        result = "\n".join(relative_matches)
        if len(result) >= MAX_CHARS:
            result = result[:MAX_CHARS] + f"[...Result truncated at {MAX_CHARS} characters...]"
        return result
    except Exception as e:
        return f"Error : {e}"

schema_glob_search = {
    "name": "glob_search",
    "description": "Find files by glob patterns relative to the working directory",
    "parameters": {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Glob pattern to search for (e.g., '**/*.py')",
            },
        },
    },
}