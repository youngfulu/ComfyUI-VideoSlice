#!/usr/bin/env bash
# Install OpenCV into the same Python environment ComfyUI uses (local or RunPod).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQ="${ROOT}/requirements.txt"

run_pip() {
  local pip_exe="$1"
  echo "Using: ${pip_exe}"
  "${pip_exe}" install -r "${REQ}"
}

# 1) Explicit override (recommended on RunPod if auto-detect fails)
if [[ -n "${COMFYUI_PIP:-}" && -x "${COMFYUI_PIP}" ]]; then
  run_pip "${COMFYUI_PIP}"
  exit 0
fi

# 2) Common RunPod / cloud ComfyUI venv locations (try first match)
for candidate in \
  "/workspace/ComfyUI/venv/bin/pip" \
  "/workspace/comfyui/venv/bin/pip" \
  "/opt/ComfyUI/venv/bin/pip" \
  "${HOME}/ComfyUI/venv/bin/pip"
do
  if [[ -x "${candidate}" ]]; then
    run_pip "${candidate}"
    exit 0
  fi
done

# 3) Fallback: whatever `pip` is on PATH (works if you activated Comfy's venv first)
if command -v pip >/dev/null 2>&1; then
  run_pip "$(command -v pip)"
  exit 0
fi

echo "No pip found. On RunPod: open a terminal, find Comfy's venv pip, then run:" >&2
echo "  export COMFYUI_PIP=/path/to/ComfyUI/venv/bin/pip" >&2
echo "  bash ${ROOT}/install_deps.sh" >&2
exit 1
