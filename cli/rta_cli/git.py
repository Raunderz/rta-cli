import os
import re
import subprocess

SECRET_PATTERNS = [
    r"API_KEY\s*=\s*['\"][^'\"\s]+",
    r"api_key\s*=\s*['\"][^'\"\s]+",
    r"password\s*=\s*['\"][^'\"\s]+",
    r"secret\s*=\s*['\"][^'\"\s]+",
    r"token\s*=\s*['\"][^'\"\s]{10,}",
    r"ghp_\w+",
    r"sk-[a-zA-Z0-9]{20,}",
    r"sk-proj-[a-zA-Z0-9_-]{20,}",
    r"amzn\.aws[A-Z0-9+/=]{20,}",
    r"AKIA[A-Z0-9]{16}",
    r"-----BEGIN.*PRIVATE KEY-----",
    r"xoxb-[a-zA-Z0-9-]{50,}",
    r"sq0[a-z]{3}-[a-zA-Z0-9-]{22}",
]

SECRET_FILES = [
    ".env",
    "credentials.json",
    ".credentials",
    "*.key",
    "*.pem",
    "id_rsa",
    "id_ed25519",
    ".netrc",
]

schema_git_status = {
    "name": "git_status",
    "description": "Show the working tree status of the git repository",
    "parameters": {"type": "object", "properties": {}},
}

schema_git_diff = {
    "name": "git_diff",
    "description": "Show staged and unstaged changes in the git repository",
    "parameters": {
        "type": "object",
        "properties": {
            "staged": {"type": "boolean", "description": "Show only staged changes"},
        },
    },
}

schema_git_log = {
    "name": "git_log",
    "description": "Show recent commit history",
    "parameters": {
        "type": "object",
        "properties": {
            "n": {"type": "integer", "description": "Number of commits to show", "default": 10},
        },
    },
}

schema_git_commit = {
    "name": "git_commit",
    "description": "Create a git commit with safety checks for secrets",
    "parameters": {
        "type": "object",
        "properties": {
            "message": {"type": "string", "description": "Commit message"},
            "auto_add": {"type": "boolean", "description": "Run git add -A before commit", "default": True},
        },
        "required": ["message"],
    },
}

schema_git_create_pr = {
    "name": "git_create_pr",
    "description": "Create a GitHub pull request using the gh CLI",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "PR title"},
            "body": {"type": "string", "description": "PR description"},
            "base": {"type": "string", "description": "Target branch", "default": "main"},
        },
        "required": ["title"],
    },
}

schema_git_branch = {
    "name": "git_branch",
    "description": "List, create, or delete branches",
    "parameters": {
        "type": "object",
        "properties": {
            "list": {"type": "boolean", "description": "List all branches"},
            "create": {"type": "string", "description": "Create a new branch"},
            "delete": {"type": "string", "description": "Delete a branch"},
        },
    },
}


def _run_git(working_directory, *args, check=True):
    result = subprocess.run(
        ["git"] + list(args),
        cwd=working_directory,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        return f"Error: {result.stderr.strip()}"
    return result.stdout.strip()


def _scan_file_for_secrets(filepath):
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            for pattern in SECRET_PATTERNS:
                if re.search(pattern, content):
                    return True
            return False
    except Exception:
        return False


def _scan_for_secrets(working_directory, files):
    affected = []
    for f in files:
        filepath = os.path.join(working_directory, f)
        if _scan_file_for_secrets(filepath):
            affected.append(f)
    return affected


def git_status(working_directory):
    if not os.path.isdir(os.path.join(working_directory, ".git")):
        return "Error: Not a git repository"
    return _run_git(working_directory, "status", "-s")


def git_diff(working_directory, staged=False):
    if not os.path.isdir(os.path.join(working_directory, ".git")):
        return "Error: Not a git repository"
    if staged:
        return _run_git(working_directory, "diff", "--cached")
    return _run_git(working_directory, "diff")


def git_log(working_directory, n=10):
    if not os.path.isdir(os.path.join(working_directory, ".git")):
        return "Error: Not a git repository"
    return _run_git(working_directory, "log", f"-{n}", "--oneline")


def git_commit(working_directory, message=None, auto_add=True, force=False):
    if not message:
        return "Error: Commit message is required"
    if not os.path.isdir(os.path.join(working_directory, ".git")):
        return "Error: Not a git repository"
    
    if auto_add and not force:
        staged = _run_git(working_directory, "diff", "--cached", "--name-only", check=False)
        unstaged = _run_git(working_directory, "diff", "--name-only", check=False)
        untracked = _run_git(working_directory, "ls-files", "--others", "--exclude-standard", check=False)
        
        all_files = []
        if staged:
            all_files.extend(staged.split("\n"))
        if unstaged:
            all_files.extend(unstaged.split("\n"))
        if untracked:
            all_files.extend(untracked.split("\n"))
        all_files = [f for f in set(all_files) if f]
        
        secret_files = _scan_for_secrets(working_directory, all_files)
        if secret_files:
            return f"Warning: Potential secrets detected in: {', '.join(secret_files)}\nUse --force to commit anyway."
    
    if auto_add:
        _run_git(working_directory, "add", "-A", check=False)
    
    return _run_git(working_directory, "commit", "-m", message)


def git_create_pr(working_directory, title=None, body="", base="main"):
    if not title:
        return "Error: PR title is required"
    if not os.path.isdir(os.path.join(working_directory, ".git")):
        return "Error: Not a git repository"
    
    result = subprocess.run(
        ["gh", "pr", "create", "-t", title, "-b", body or title, "-B", base],
        cwd=working_directory,
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        return f"Error creating PR: {result.stderr.strip()}"
    return result.stdout.strip()


def git_branch(working_directory, list=False, create=None, delete=None):
    if not os.path.isdir(os.path.join(working_directory, ".git")):
        return "Error: Not a git repository"
    
    if create:
        _run_git(working_directory, "checkout", "-b", create)
        return f"Created and switched to branch: {create}"
    
    if delete:
        result = _run_git(working_directory, "branch", "-d", delete, check=False)
        if "error" in result.lower():
            return result
        return f"Deleted branch: {delete}"
    
    if list:
        current = _run_git(working_directory, "branch", "--show-current")
        branches = _run_git(working_directory, "branch", "-a")
        output = [f"Current: {current}", "", branches]
        return "\n".join(output)
    
    return _run_git(working_directory, "branch", "--show-current")