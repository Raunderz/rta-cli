#!/usr/bin/env bash
set -euo pipefail

# Release Rta CLI to the open-source repo (Raunderz/rta-cli)
# Usage: ./scripts/release-cli.sh [version]
#
# If no version is given, uses the version from cli/pyproject.toml

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
CLI_DIR="$REPO_ROOT/cli"
REMOTE="rta-cli"
BRANCH="cli-only"

# Extract version from pyproject.toml if not provided
if [ $# -ge 1 ]; then
    VERSION="$1"
else
    VERSION=$(grep '^version' "$CLI_DIR/pyproject.toml" | head -1 | sed 's/.*"\(.*\)".*/\1/')
fi

echo "==> Releasing rta-cli v${VERSION}"
echo "    Source: $CLI_DIR"
echo "    Remote: $REMOTE"
echo ""

# Ensure we're in the repo root
cd "$REPO_ROOT"

# Ensure the remote exists
if ! git remote get-url "$REMOTE" &>/dev/null; then
    echo "Adding remote '$REMOTE'..."
    git remote add "$REMOTE" git@github.com:Raunderz/rta-cli.git
fi

# Tag if version argument was given
if [ $# -ge 1 ]; then
    echo "Tagging v${VERSION}..."
    git tag "v${VERSION}" 2>/dev/null || echo "Tag v${VERSION} already exists, skipping."
fi

# Split and push
echo "Splitting cli/ history..."
git subtree split -P cli -b "$BRANCH"

echo "Pushing to $REMOTE..."
git push "$REMOTE" "$BRANCH:main" --force

echo ""
echo "==> Done! v${VERSION} pushed to https://github.com/Raunderz/rta-cli"
echo "    Create a release at: https://github.com/Raunderz/rta-cli/releases/new"
