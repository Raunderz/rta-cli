# Releasing Rta CLI to the Open-Source Repo

This doc describes how to push CLI releases to `https://github.com/Raunderz/rta-cli`.

## Overview

The CLI code lives in `cli/` inside the main monorepo. The open-source repo (`Raunderz/rta-cli`) only gets stable releases — not every WIP commit.

## One-Time Setup

```bash
# Add the open-source repo as a remote
git remote add rta-cli git@github.com:Raunderz/rta-cli.git

# Do the initial push (preserves git history)
git subtree split -P cli -b cli-only
git push rta-cli cli-only:main
```

## Release Process

### 1. Prepare the release

Make sure all changes are committed in the monorepo, tests pass, and CHANGELOG is updated.

### 2. Tag the release

```bash
git tag v0.7.0
git push origin v0.7.0
```

### 3. Push to the open-source repo

```bash
./scripts/release-cli.sh v0.7.0
```

Or manually:

```bash
git subtree split -P cli -b cli-only
git push rta-cli cli-only:main --force
```

The `--force` is expected — the open-source repo only ever contains the CLI snapshot.

### 4. Create a GitHub Release

Go to `https://github.com/Raunderz/rta-cli/releases` and create a new release from the tag with release notes from `CHANGELOG.md`.

## What Gets Pushed

- `cli/` source code only (no `backend/`, `app/`, etc.)
- `pyproject.toml`, `README.md`, `LICENSE`, `CHANGELOG.md`
- Full git history of the `cli/` directory

## What Stays Private

- Backend, mobile_backend, app, extensions, scripts
- Supabase config, API keys, deployment details
- Internal architecture docs
