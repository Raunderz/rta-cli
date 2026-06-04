import json
from pathlib import Path
from typing import Any

PROJECT_INFO_FILE = ".rta_project.json"
CACHE_TTL_SECONDS = 300


def find_project_file(workspace: str, patterns: list[str]) -> str | None:
    """Find first matching file in workspace."""
    workspace_path = Path(workspace)
    for pattern in patterns:
        matches = list(workspace_path.glob(pattern))
        if matches:
            return str(matches[0])
    return None


def find_config_file(workspace: str, patterns: list[str]) -> list[str]:
    """Find all matching config files."""
    workspace_path = Path(workspace)
    files = []
    for pattern in patterns:
        matches = list(workspace_path.glob(pattern))
        files.extend(str(m) for m in matches if m.is_file())
    return files


def detect_language(workspace: str) -> tuple[str | None, str | None]:
    """Detect programming language and framework."""
    pyproject = find_project_file(workspace, ["pyproject.toml"])
    package_json = find_project_file(workspace, ["package.json"])
    cargo_toml = find_project_file(workspace, ["Cargo.toml"])
    go_mod = find_project_file(workspace, ["go.mod"])
    csproj = find_project_file(workspace, ["*.csproj"])

    if pyproject:
        try:
            with open(pyproject) as f:
                data = json.load(f)
            if "project" in data or "tool" in data:
                return "python", None
        except Exception:
            pass

    if package_json:
        try:
            with open(package_json) as f:
                data = json.load(f)
            deps = data.get("dependencies", {})
            dev_deps = data.get("devDependencies", {})
            all_deps = {**deps, **dev_deps}
            framework = None
            if "react" in all_deps:
                framework = "react"
            elif "vue" in all_deps:
                framework = "vue"
            elif "next" in all_deps:
                framework = "next"
            elif "svelte" in all_deps:
                framework = "svelte"
            language = "typescript" if "typescript" in all_deps else "javascript"
            return language, framework
        except Exception:
            return "javascript", None

    if cargo_toml:
        return "rust", None

    if go_mod:
        return "go", None

    if csproj:
        return "csharp", None

    if find_project_file(workspace, ["*.py"]):
        return "python", None

    if find_project_file(workspace, ["*.js", "*.ts"]):
        return "javascript", None

    return None, None


def detect_test_framework(workspace: str, language: str | None) -> str | None:
    """Detect test framework."""
    if language == "python":
        if find_project_file(workspace, ["pytest.ini", "conftest.py"]):
            return "pytest"
        if find_project_file(workspace, ["setup.cfg", "pyproject.toml"]):
            try:
                if find_project_file(workspace, ["pyproject.toml"]):
                    with open(find_project_file(workspace, ["pyproject.toml"])) as f:
                        data = json.load(f)
                    tool = data.get("tool", {}).get("pytest", {})
                    if tool:
                        return "pytest"
            except Exception:
                pass
        return None

    if language in ("javascript", "typescript"):
        if find_project_file(workspace, ["vitest.config.*", "jest.config.*"]):
            return (
                "vitest"
                if find_project_file(workspace, ["vitest.config.*"])
                else "jest"
            )
        return "vitest"

    if language == "rust":
        return "cargo test"

    if language == "go":
        return "go test"

    if language == "csharp":
        return "dotnet test"

    return None


def detect_linter(workspace: str, language: str | None) -> str | None:
    """Detect linter and type checker."""
    if language == "python":
        if find_project_file(workspace, ["ruff.toml", ".ruff.toml"]):
            return "ruff"
        if find_project_file(workspace, [".flake8", "setup.cfg"]):
            return "flake8"
        if find_project_file(workspace, ["mypy.ini", "mypy.ini"]):
            return "mypy"
        return None

    if language in ("javascript", "typescript"):
        if find_project_file(workspace, [".eslintrc*", "eslint.config.*"]):
            return "eslint"
        return None

    if language == "rust":
        return "cargo clippy"

    if language == "go":
        if find_project_file(workspace, [".golangci.yml", ".golangci.yaml"]):
            return "golangci-lint"
        return None

    return None


def detect_typechecker(workspace: str, language: str | None) -> str | None:
    """Detect type checker."""
    if language == "python":
        if find_project_file(workspace, ["mypy.ini", "pyproject.toml"]):
            return "mypy"
        return None

    if language in ("javascript", "typescript"):
        if find_project_file(workspace, ["tsconfig.json"]):
            return "tsc"
        return None

    if language == "rust":
        return "cargo check"

    if language == "go":
        return "go build"

    return None


def detect_build_command(workspace: str, language: str | None) -> str | None:
    """Detect build command."""
    if language in ("javascript", "typescript"):
        package_json = find_project_file(workspace, ["package.json"])
        if package_json:
            try:
                with open(package_json) as f:
                    data = json.load(f)
                scripts = data.get("scripts", {})
                if "build" in scripts:
                    return "npm run build"
                if "pack" in scripts:
                    return "npm run pack"
            except Exception:
                pass

    if language == "python":
        if find_project_file(workspace, ["setup.py", "setup.cfg"]):
            return "python -m build"

    if language == "rust":
        return "cargo build"

    if language == "go":
        return "go build"

    if language == "csharp":
        return "dotnet build"

    return None


def detect_package_manager(workspace: str) -> str | None:
    """Detect package manager."""
    if find_project_file(workspace, ["pnpm-lock.yaml"]):
        return "pnpm"
    if find_project_file(workspace, ["yarn.lock"]):
        return "yarn"
    if find_project_file(workspace, ["package-lock.json"]):
        return "npm"
    if find_project_file(workspace, ["poetry.lock"]):
        return "poetry"
    if find_project_file(workspace, ["Pipfile.lock"]):
        return "pipenv"
    if find_project_file(workspace, ["requirements*.txt"]):
        return "pip"
    return None


def detect_test_pattern(workspace: str, language: str | None) -> str | None:
    """Detect test file naming pattern."""
    if language == "python":
        patterns = ["test_*.py", "*_test.py", "tests/*.py"]
        for p in patterns:
            if find_project_file(workspace, [p]):
                return p
        return "test_*.py"

    if language in ("javascript", "typescript"):
        patterns = ["*.test.ts", "*.spec.ts", "*.test.js", "*.spec.js"]
        for p in patterns:
            if find_project_file(workspace, [p]):
                return p
        return "*.test.ts"

    if language == "rust":
        return "*_test.rs"

    if language == "go":
        return "*_test.go"

    return None


def detect_src_pattern(workspace: str, language: str | None) -> str | None:
    """Detect source file naming pattern."""
    if language == "python":
        return "*.py"

    if language == "javascript":
        return "*.js"

    if language == "typescript":
        return "*.ts"

    if language == "rust":
        return "src/**/*.rs"

    if language == "go":
        return "*.go"

    return ".*"


def get_project_info(workspace: str) -> dict[str, Any]:
    """Get all project information."""
    language, framework = detect_language(workspace)
    if not language:
        return {
            "language": None,
            "framework": None,
            "test_framework": None,
            "linter": None,
            "typechecker": None,
            "build_command": None,
            "test_pattern": None,
            "src_pattern": None,
            "package_manager": None,
        }

    test_framework = detect_test_framework(workspace, language)
    linter = detect_linter(workspace, language)
    typechecker = detect_typechecker(workspace, language)
    build_command = detect_build_command(workspace, language)
    test_pattern = detect_test_pattern(workspace, language)
    src_pattern = detect_src_pattern(workspace, language)
    package_manager = detect_package_manager(workspace)

    return {
        "language": language,
        "framework": framework,
        "test_framework": test_framework,
        "linter": linter,
        "typechecker": typechecker,
        "build_command": build_command,
        "test_pattern": test_pattern,
        "src_pattern": src_pattern,
        "package_manager": package_manager,
    }


def get_cached_info(workspace: str) -> dict[str, Any] | None:
    """Get cached project info if fresh."""
    cache_file = Path(workspace) / PROJECT_INFO_FILE
    if not cache_file.exists():
        return None

    try:
        stat = cache_file.stat()
        import time

        age = time.time() - stat.st_mtime
        if age > CACHE_TTL_SECONDS:
            return None
        with open(cache_file) as f:
            return json.load(f)
    except Exception:
        return None


def cache_project_info(workspace: str, info: dict[str, Any]) -> None:
    """Cache project info to file."""
    cache_file = Path(workspace) / PROJECT_INFO_FILE
    try:
        with open(cache_file, "w") as f:
            json.dump(info, f)
    except Exception:
        pass


def discover_project(workspace: str, use_cache: bool = True) -> dict[str, Any]:
    """Main entry point for project discovery."""
    if use_cache:
        cached = get_cached_info(workspace)
        if cached:
            return cached

    info = get_project_info(workspace)
    cache_project_info(workspace, info)
    return info


def get_test_command(project_info: dict[str, Any]) -> str | None:
    """Get appropriate test command."""
    test_framework = project_info.get("test_framework")
    language = project_info.get("language")
    package_manager = project_info.get("package_manager")

    if test_framework == "pytest":
        return "pytest"
    if test_framework == "vitest":
        return "npm test" if package_manager != "pnpm" else "pnpm test"
    if test_framework == "jest":
        return "npm test"
    if test_framework == "cargo test":
        return "cargo test"
    if test_framework == "go test":
        return "go test ./..."
    if test_framework == "dotnet test":
        return "dotnet test"

    return None


def get_lint_command(project_info: dict[str, Any]) -> str | None:
    """Get appropriate lint command."""
    linter = project_info.get("linter")
    language = project_info.get("language")
    package_manager = project_info.get("package_manager")

    if linter == "ruff":
        return "ruff check ."
    if linter == "flake8":
        return "flake8 ."
    if linter == "eslint":
        return "npm run lint" if package_manager != "pnpm" else "pnpm run lint"
    if linter == "golangci-lint":
        return "golangci-lint run ./..."
    if linter == "cargo clippy":
        return "cargo clippy -- -D warnings"

    if language == "python" and project_info.get("typechecker") == "mypy":
        return "mypy ."

    if (
        language in ("javascript", "typescript")
        and project_info.get("typechecker") == "tsc"
    ):
        return "npx tsc --noEmit"

    return None


def get_build_command(project_info: dict[str, Any]) -> str | None:
    """Get appropriate build command."""
    build = project_info.get("build_command")
    if build:
        return build

    language = project_info.get("language")
    package_manager = project_info.get("package_manager")

    if language in ("javascript", "typescript"):
        return "npm run build" if package_manager != "pnpm" else "pnpm build"
    if language == "rust":
        return "cargo build"
    if language == "go":
        return "go build"
    if language == "csharp":
        return "dotnet build"

    return None


schema_discovery = {
    "name": "discover_project",
    "description": "Automatically detect the project's language, framework, test framework, linter, type checker, and build configuration. Call this first to understand what commands to use for testing, linting, and building.",
    "parameters": {
        "type": "object",
        "properties": {
            "use_cache": {
                "type": "boolean",
                "description": "Whether to use cached project info (default true). Set to false to force re-detection.",
            },
        },
    },
}
