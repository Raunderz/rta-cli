import sys
import tomllib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def _get_package_name() -> str:
    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    if pyproject_path.exists():
        try:
            data = tomllib.loads(pyproject_path.read_text())
            return data["project"]["name"]
        except Exception:
            pass
    return "rta-cli"


def _get_version_from_pyproject() -> str | None:
    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    if pyproject_path.exists():
        try:
            data = tomllib.loads(pyproject_path.read_text())
            return data["project"]["version"]
        except Exception:
            pass
    return None


PACKAGE_NAME = _get_package_name()

# Priority: bundled version file > installed metadata > pyproject.toml > hardcoded
if getattr(sys, "frozen", False):
    VERSION = "0.6.0"
else:
    try:
        VERSION = version(PACKAGE_NAME)
    except PackageNotFoundError:
        VERSION = _get_version_from_pyproject() or "0.0.0"
