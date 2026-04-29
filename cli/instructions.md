# CLI Build Instructions

This document provides instructions for building standalone executables of the RTA CLI for Linux and Windows.

## Prerequisites

- Python 3.12
- PyInstaller
- Project dependencies installed

## Linux Build (Recommended - Using Docker)

The simplest and most reproducible way to build the Linux binary:

```bash
# Build the binary
docker build -t rta-cli -f ../Dockerfile ..

# Extract the binary from the container
docker run --rm rta-cli cat /rta > cli/dist/rta
chmod +x cli/dist/rta
```

Or build and copy directly:

```bash
docker build -t rta-cli -f ../Dockerfile ..
docker create --name rta-build rta-cli
docker cp rta-build:/rta ./website/public/rta
docker rm rta-build
chmod +x website/public/rta
```

The executable will be created at `website/public/rta`.

## Linux Build (Without Docker)

If you have Python 3.12 locally:

```bash
cd cli
pip install -e .
pip install pyinstaller
pyinstaller --onefile --name rta rta_cli/__init__.py
cp dist/rta ../website/public/rta
chmod +x ../website/public/rta
```

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

## Notes

- The build process uses PyInstaller to create a standalone executable
- The resulting executable includes all Python dependencies bundled in
- On Linux, the executable will be at `website/public/rta`
- On Windows, it will be at `cli\dist\rta.exe`
- For GUI applications (if applicable), modify the spec file accordingly