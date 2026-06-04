"""Clone command - clone a git repository."""

import sys


def clone(args):
    import subprocess

    repo_url = args[0]
    dest = args[1] if len(args) > 1 else None

    print(f"Cloning {repo_url}...")
    cmd = ["git", "clone", repo_url]
    if dest:
        cmd.append(dest)

    try:
        subprocess.run(cmd, check=True)
        print(f"Successfully cloned into {dest or 'current directory'}")
    except subprocess.CalledProcessError:
        print("error: git clone failed", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
