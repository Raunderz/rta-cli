import json
import os
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field

PROJECT_INFO_FILE = ".rta_project.json"
CACHE_TTL_SECONDS = 300

class ProjectInfo(BaseModel):
    language: str | None = None
    framework: str | None = None
    test_framework: str | None = None
    linter: str | None = None
    typechecker: str | None = None
    build_command: str | None = None
    test_pattern: str | None = None
    src_pattern: str | None = None
    package_manager: str | None = None

def find_project_file(workspace: str, patterns: list[str]) -> str | None:
    workspace_path = Path(workspace)
    for pattern in patterns:
        try:
            matches = list(workspace_path.glob(pattern))
            if matches:
                return str(matches[0])
        except Exception:
            continue
    return None

def detect_language(workspace: str) -> tuple[str | None, str | None]:
    pyproject = find_project_file(workspace, ["pyproject.toml"])
    package_json = find_project_file(workspace, ["package.json"])
    cargo_toml = find_project_file(workspace, ["Cargo.toml"])
    go_mod = find_project_file(workspace, ["go.mod"])
    csproj = find_project_file(workspace, ["*.csproj"])

    if pyproject:
        return "python", None

    if package_json:
        try:
            with open(package_json) as f:
                data = json.load(f)
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            framework = None
            if "react" in deps: framework = "react"
            elif "vue" in deps: framework = "vue"
            elif "next" in deps: framework = "next"
            language = "typescript" if "typescript" in deps else "javascript"
            return language, framework
        except Exception:
            return "javascript", None

    if cargo_toml: return "rust", None
    if go_mod: return "go", None
    if csproj: return "csharp", None
    if find_project_file(workspace, ["*.py"]): return "python", None
    if find_project_file(workspace, ["*.js", "*.ts"]): return "javascript", None
    return None, None

def discover_project(workspace: str) -> ProjectInfo:
    language, framework = detect_language(workspace)
    if not language:
        return ProjectInfo()

    # Simplified detection logic for kon
    info = ProjectInfo(language=language, framework=framework)
    
    if language == "python":
        info.test_framework = "pytest" if find_project_file(workspace, ["pytest.ini", "conftest.py", "tests/"]) else None
        info.linter = "ruff" if find_project_file(workspace, ["ruff.toml", ".ruff.toml"]) else "flake8"
        info.src_pattern = "*.py"
        info.test_pattern = "test_*.py"
    elif language in ("javascript", "typescript"):
        info.test_framework = "vitest" if find_project_file(workspace, ["vitest.config.*"]) else "jest"
        info.package_manager = "pnpm" if find_project_file(workspace, ["pnpm-lock.yaml"]) else "npm"
        info.src_pattern = "*.ts" if language == "typescript" else "*.js"
    
    return info
