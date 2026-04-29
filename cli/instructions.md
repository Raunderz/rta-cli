# CLI Build Instructions

This document provides instructions for building standalone executables of the RTA CLI for Linux and Windows using PyInstaller.

## Prerequisites

- Python 3.12+
- PyInstaller
- Project dependencies installed

## General Setup

1. Ensure you have Python 3.12 or later installed.
2. Install PyInstaller: `pip install pyinstaller`
3. Install project dependencies: `cd cli && pip install -e .`

## Linux Build (using Docker)

To build on Linux without installing dependencies locally, use Docker:

```bash
# Build using Docker
docker run --rm -v $(pwd):/workspace -w /workspace \
  python:3.12-slim \
  bash -c "
    apt-get update && apt-get install -y git
    cd cli
    pip install -e .
    pip install pyinstaller
    pyinstaller rta.spec
  "
```

The executable will be created at `cli/dist/rta` (Linux executable).

## Windows Build

On a Windows machine (using uv - recommended):

1. Open PowerShell
2. Navigate to the project directory
3. Install dependencies and build:

```powershell
cd cli
uv pip install -e .
uv add --dev pyinstaller
uv run pyinstaller rta.spec --clean
```

Alternatively, using standard pip:

```batch
cd cli
pip install -e .
pip install pyinstaller
pyinstaller rta.spec --clean
```

The executable will be created at `cli\dist\rta.exe`.

**Note:** The build uses `rta_cli_main.py` as the entry point and bundles `config.json` via the `rta.spec` file.

## Notes

- The build process uses the existing `rta.spec` file for PyInstaller configuration
- The resulting executable is standalone and includes all dependencies
- On Linux, the executable will be at `cli/dist/rta`
- On Windows, it will be at `cli\dist\rta.exe`
- You may need to adjust paths if your project structure differs
- For GUI applications (if applicable), modify the spec file accordingly