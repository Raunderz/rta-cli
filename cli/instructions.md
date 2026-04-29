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

On a Windows machine:

1. Open Command Prompt or PowerShell as Administrator
2. Navigate to the project directory
3. Install dependencies and build:

```batch
cd cli
pip install -e .
pip install pyinstaller
pyinstaller rta.spec
```

The executable will be created at `cli\dist\rta.exe`.

## Notes

- The build process uses the existing `rta.spec` file for PyInstaller configuration
- The resulting executable is standalone and includes all dependencies
- On Linux, the executable will be at `cli/dist/rta`
- On Windows, it will be at `cli\dist\rta.exe`
- You may need to adjust paths if your project structure differs
- For GUI applications (if applicable), modify the spec file accordingly