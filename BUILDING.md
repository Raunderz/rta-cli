# Building the `rta` Binary

This document records the steps, decisions, and pitfalls encountered when compiling
the `rta` CLI into a standalone Linux binary using **PyInstaller**.

---

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.13 | Managed via `.python-version` / `uv` |
| PyInstaller | latest in `.venv` | Installed inside the project venv |
| uv | any | Used to manage the venv |

Make sure the project virtual environment is set up:

```bash
cd cli/
uv sync
```

---

## Build Steps

### 1. Use `run.py` as the PyInstaller entry point

**Critical:** Do **not** point PyInstaller at `src/kon/cli.py` directly.  
`cli.py` uses relative imports (e.g. `from .llm import ...`), which fail with
`ImportError: attempted relative import with no known parent package` when the
script is executed as `__main__` inside a PyInstaller bundle.

Instead use `run.py` at the repo root, which uses an absolute import:

```python
# run.py
from kon.cli import main
main()
```

This file already exists in the project root and is the correct entry point for
PyInstaller.

### 2. Collect package data (`kon.defaults`)

The `config.toml` default config lives inside the `kon.defaults` sub-package.
PyInstaller will **not** automatically bundle non-Python files inside packages,
so we must tell it to collect all data files from `kon`:

```python
# rta.spec (excerpt)
from PyInstaller.utils.hooks import collect_data_files

datas = []
datas += collect_data_files('kon')   # picks up config.toml, sounds/, etc.
```

### 3. Add hidden imports

Sub-packages that are loaded dynamically (e.g. via `importlib`) must be declared
as hidden imports so PyInstaller includes them:

```
hiddenimports=[
    'kon.defaults',
    'kon.sounds',
    'kon.builtin_skills',
    'kon.builtin_skills.init',
    'kon.builtin_skills.review',
]
```

### 4. Run the build

```bash
cd cli/
.venv/bin/python -m PyInstaller --clean rta.spec
```

The binary lands at `cli/dist/rta`.

### 5. Verify

```bash
./dist/rta --version      # should print "rta <version>" with no errors
./dist/rta --help         # should print full help text
```

### 6. Deploy to website

```bash
cp dist/rta ../website/public/rta
chmod +x ../website/public/rta
```

---

## rta.spec (full reference)

```python
# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

datas = []
datas += collect_data_files('kon')

a = Analysis(
    ['run.py'],          # <-- MUST be run.py, not src/kon/cli.py
    pathex=['src'],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'kon.defaults',
        'kon.sounds',
        'kon.builtin_skills',
        'kon.builtin_skills.init',
        'kon.builtin_skills.review',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='rta',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

---

## Common Pitfalls & Fixes

### `ImportError: attempted relative import with no known parent package`

**Cause:** Entry point was `src/kon/cli.py` which uses `from .llm import ...`  
**Fix:** Switch entry point to `run.py` (uses absolute import `from kon.cli import main`)

### `FileNotFoundError` for `config.toml` at runtime

**Cause:** `kon.defaults` data files not bundled  
**Fix:** Add `datas += collect_data_files('kon')` and `'kon.defaults'` to `hiddenimports`

### Build produces binary but it crashes silently

**Cause:** Missing hidden imports for dynamically loaded submodules  
**Fix:** Add all `kon.builtin_skills.*` submodules to `hiddenimports`

---

## History

| Date | Action |
|------|--------|
| 2026-06-07 | Initial binary build setup; migrated from `kon/` → `cli/` |
| 2026-06-07 | Fixed entry-point bug (cli.py → run.py) resolving relative import error |
| 2026-06-07 | Deployed binary to `website/public/rta` |
