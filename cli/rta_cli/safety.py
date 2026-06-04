import os
import fnmatch
from typing import List, Optional


class GitignoreFilter:
    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)
        self.patterns: List[str] = []
        self._load_gitignore()

    def _load_gitignore(self):
        # Default patterns to always ignore
        self.patterns = [".git/", ".rta/", "__pycache__/", "*.pyc"]

        gitignore_path = os.path.join(self.root_dir, ".gitignore")
        if os.path.exists(gitignore_path):
            with open(gitignore_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Normalize pattern for fnmatch
                        self.patterns.append(line)

    def is_ignored(self, path: str, allow_ignored: bool = False) -> bool:
        """
        Check if a path is ignored by .gitignore patterns.
        'path' should be relative to self.root_dir or absolute.
        """
        if allow_ignored:
            return False

        if os.path.isabs(path):
            rel_path = os.path.relpath(path, self.root_dir)
        else:
            rel_path = path

        # Normalize path separators
        rel_path = rel_path.replace(os.sep, "/")

        parts = rel_path.split("/")

        for i in range(len(parts)):
            subpath = "/".join(parts[: i + 1])
            is_dir = (i < len(parts) - 1) or os.path.isdir(
                os.path.join(self.root_dir, rel_path)
            )

            for pattern in self.patterns:
                # Handle directory-only patterns (ending with /)
                if pattern.endswith("/"):
                    if not is_dir:
                        continue
                    clean_pattern = pattern[:-1]
                else:
                    clean_pattern = pattern

                # Check if the subpath or just the current part matches the pattern
                if (
                    fnmatch.fnmatch(subpath, clean_pattern)
                    or fnmatch.fnmatch(parts[i], clean_pattern)
                    or fnmatch.fnmatch(subpath, f"*/{clean_pattern}")
                ):
                    return True
        return False

    def filter_paths(
        self, paths: List[str], base_dir: Optional[str] = None
    ) -> List[str]:
        """Filter a list of paths (relative to base_dir or root_dir)."""
        filtered = []
        for p in paths:
            full_path = p
            if base_dir:
                full_path = os.path.join(base_dir, p)
            if not self.is_ignored(full_path):
                filtered.append(p)
        return filtered
