"""Init command - scaffold a new project."""

import os
import sys


def init(args):
    import json

    project_name = args[0]

    if os.path.exists(project_name):
        print(f"error: '{project_name}' already exists", file=sys.stderr)
        sys.exit(1)

    try:
        os.makedirs(project_name, exist_ok=True)
        # Create a basic .rta_project.json so the CLI recognizes it as a project
        project_info = {
            "name": project_name,
            "version": "0.1.0",
            "created_at": os.path.getctime(project_name)
            if hasattr(os.path, "getctime")
            else 0,
        }
        with open(os.path.join(project_name, ".rta_project.json"), "w") as f:
            json.dump(project_info, f, indent=2)

        print(f"Initialized project '{project_name}'")
        print(f"Run: cd {project_name} && rta chat")
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
