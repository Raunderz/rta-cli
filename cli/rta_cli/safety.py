import os

def confirm_destructive(action, path, force=False):
    return None

def is_dangerous_command(command):
    dangerous_patterns = [
        r"rm\s+-rf",
        r"del\s+/?[fqs]",
        r"rmdir\s+/s",
        r"format\s+",
        r"dd\s+.*of=",
    ]
    import re
    for pattern in dangerous_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False


def needs_confirmation(action):
    return {
        "delete_file": "This file will be permanently deleted.",
        "delete_dir": "This directory and all contents will be deleted.",
        "run_dangerous": "This command may modify or delete files.",
    }.get(action, None)