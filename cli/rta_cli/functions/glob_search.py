import os
import glob
from rta_cli.config import MAX_CHARS
from rta_cli.safety import GitignoreFilter

def glob_search(working_directory, pattern, allow_ignored=False):
    abs_working_dir = os.path.abspath(working_directory)
    gf = GitignoreFilter(abs_working_dir)
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
            # Convert to relative for filtering
            matches = [os.path.relpath(m, abs_working_dir) for m in matches]
        
        # Filter ignored paths
        matches = [m for m in matches if not gf.is_ignored(os.path.join(abs_working_dir, m), allow_ignored=allow_ignored)]
        
        # Convert to relative paths for cleaner output
        relative_matches = [m if not os.path.isabs(m) else os.path.relpath(m, abs_working_dir) for m in matches]
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