#!/usr/bin/env bash
# Run once after: gh auth login
# Creates https://github.com/<you>/ComfyUI-VideoSlice and pushes main.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if ! command -v gh >/dev/null 2>&1; then
  echo "Install GitHub CLI: brew install gh" >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "Not logged in. In Terminal run:" >&2
  echo "  gh auth login" >&2
  echo "Then run this script again:" >&2
  echo "  bash $ROOT/create_github_repo.sh" >&2
  exit 1
fi

LOGIN="$(gh api user -q .login)"
echo "GitHub user: $LOGIN"

if git remote get-url origin >/dev/null 2>&1; then
  git remote remove origin
fi

# Create repo on GitHub from this folder and push (gh adds origin)
gh repo create ComfyUI-VideoSlice \
  --public \
  --source=. \
  --remote=origin \
  --description "ComfyUI custom node: ib video slicer — MP4/MOV to single IMAGE frame" \
  --push

echo "Done: https://github.com/${LOGIN}/ComfyUI-VideoSlice"
