import os
import re
from typing import List, Dict, Optional
from rta_cli.utils import _rta_dir


def get_skills_dir() -> str:
    """Return the global skills directory."""
    d = os.path.join(_rta_dir(), "skills")
    os.makedirs(d, exist_ok=True)
    return d


def list_available_skills() -> List[Dict[str, str]]:
    """
    Scan ~/.rta/skills/ for skill directories and extract metadata.
    A skill directory must contain a SKILL.md.
    """
    skills_dir = get_skills_dir()
    skills = []

    if not os.path.exists(skills_dir):
        return []

    for item in os.listdir(skills_dir):
        item_path = os.path.join(skills_dir, item)
        if os.path.isdir(item_path):
            skill_md = os.path.join(item_path, "SKILL.md")
            if os.path.exists(skill_md):
                description = _extract_description(skill_md)
                skills.append(
                    {
                        "name": item,
                        "description": description or "No description provided.",
                    }
                )
    return sorted(skills, key=lambda x: x["name"])


def load_skill_content(name: str) -> Optional[str]:
    """Read the full content of a skill's SKILL.md."""
    skills_dir = get_skills_dir()
    skill_md = os.path.join(skills_dir, name, "SKILL.md")
    if os.path.exists(skill_md):
        with open(skill_md, "r") as f:
            return f.read()
    return None


def has_hidden_content(content: str) -> bool:
    """Detect HTML comments or other hidden content in Markdown."""
    # Matches <!-- any content -->
    return bool(re.search(r"<!--[\s\S]*?-->", content))


def _extract_description(path: str) -> Optional[str]:
    """
    Extract a short description from SKILL.md.
    Looks for the first non-header line or a specific 'Description:' line.
    """
    try:
        with open(path, "r") as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # Take first significant line, truncate if too long
                return line[:150] + "..." if len(line) > 150 else line
    except Exception:
        pass
    return None
