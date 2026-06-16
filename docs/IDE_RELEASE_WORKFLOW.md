# Releasing RTA Desktop to the Open-Source Repo

This doc describes how to push RTA Desktop releases to `https://github.com/Raunderz/rta-desktop`.

## Overview

The desktop IDE code lives in `rta-desktop/` inside the main monorepo. The open-source repo (`Raunderz/rta-desktop`) only gets stable releases — not every WIP commit.

## One-Time Setup

```bash
# Add the open-source repo as a remote
git remote add rta-desktop git@github.com:Raunderz/rta-desktop.git

# Do the initial push (preserves git history)
git subtree split -P rta-desktop -b rta-desktop-only
git push rta-desktop rta-desktop-only:main
```

## Release Process

### 1. Prepare the release

Make sure all changes are committed in the monorepo, tests pass (`lua rta-desktop/tests/run.lua`), and the README is up to date.

### 2. Tag the release

```bash
git tag v-desktop-1.0.0
git push origin v-desktop-1.0.0
```

### 3. Push to the open-source repo

```bash
git subtree split -P rta-desktop -b rta-desktop-only
git push rta-desktop rta-desktop-only:main --force
```

The `--force` is expected — the open-source repo only ever contains the desktop IDE snapshot.

### 4. Create a GitHub Release

Go to `https://github.com/Raunderz/rta-desktop/releases` and create a new release from the tag with release notes.

## What Gets Pushed

- `src/` — Lite XL C source code
- `data/` — Lua core, plugins (including `rta_chat.lua`), themes
- `scripts/` — Build scripts
- `tests/` — Test suite
- `subprojects/` — Meson wraps for dependencies
- `resources/` — Icons, cross-compilation files
- `meson.build`, `meson_options.txt`, `BUILD.md`, `README.md`, `LICENSE`

## What Stays Private

- `bin/` — Built CLI binary (gitignored anyway)
- `build/` — Build output (gitignored)
- Backend, mobile_backend, app, extensions, scripts (monorepo-level)
- Supabase config, API keys, deployment details
- Internal architecture docs

## Building the External Repo

Users clone and build:

```bash
git clone https://github.com/Raunderz/rta-desktop.git
cd rta-desktop
meson setup build --wrap-mode=forcefallback
meson compile -C build
ln -sf ../../data build/src/data
./build/src/rta-desktop
```

The `rta` CLI binary must be placed in `bin/` or in the user's PATH separately.
