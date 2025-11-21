#!/usr/bin/env bash
set -euo pipefail

workspace="${PWD}"

detect_editor_flavor() {
  # Allow manual override
  if [[ "${EDITOR_FLAVOR:-}" =~ ^(vscode|cursor)$ ]]; then
    echo "${EDITOR_FLAVOR}"
    return
  fi

  # VS Code/ Cursor remote server folder hint
  if [[ -n "${VSCODE_AGENT_FOLDER:-}" ]]; then
    if [[ "${VSCODE_AGENT_FOLDER}" == *".cursor-server"* ]]; then
      echo "cursor"; return
    fi
    if [[ "${VSCODE_AGENT_FOLDER}" == *".vscode-server"* ]]; then
      echo "vscode"; return
    fi
  fi

  # Server installation directories
  if [[ -d "${HOME}/.cursor-server" ]]; then
    echo "cursor"; return
  fi
  if [[ -d "${HOME}/.vscode-server" ]]; then
    echo "vscode"; return
  fi

  # Terminal program hint
  case "${TERM_PROGRAM:-}" in
    cursor|*Cursor*) echo "cursor"; return ;;
    vscode|*VSCode*) echo "vscode"; return ;;
  esac

  # Default
  echo "vscode"
}

flavor="$(detect_editor_flavor)"
echo "[devcontainer] Detected editor flavor: ${flavor}"

mkdir -p "${workspace}/.vscode"

pushd "${workspace}/.vscode" >/dev/null

# Link editor-specific settings (avoid broken symlinks)
if [[ -f "settings.${flavor}.json" ]]; then
  ln -sf "settings.${flavor}.json" "settings.json"
elif [[ -f "settings.vscode.json" ]]; then
  ln -sf "settings.vscode.json" "settings.json"
else
  echo "[devcontainer] Warning: No settings JSON found for flavor '${flavor}' or vscode fallback; skipping link"
fi

# Link editor-specific extension recommendations (avoid broken symlinks)
if [[ -f "extensions.${flavor}.json" ]]; then
  ln -sf "extensions.${flavor}.json" "extensions.json"
elif [[ -f "extensions.vscode.json" ]]; then
  ln -sf "extensions.vscode.json" "extensions.json"
else
  echo "[devcontainer] Warning: No extensions JSON found for flavor '${flavor}' or vscode fallback; skipping link"
fi

popd >/dev/null

# Ensure venv exists and install dev deps
if [[ ! -d "${workspace}/.venv" ]]; then
  echo "[devcontainer] Creating Python venv with uv..."
  uv venv "${workspace}/.venv"
  # shellcheck disable=SC1091
  source "${workspace}/.venv/bin/activate"
  if ! uv pip install -e "${workspace}.[dev]"; then
    echo "[devcontainer] Warning: Failed to install development dependencies"
  fi
fi

# Validate JSON files if jq is available
if command -v jq >/dev/null 2>&1; then
  for f in "${workspace}/.vscode/settings.json" "${workspace}/.vscode/extensions.json"; do
    if [[ -f "$f" ]]; then
      if ! jq empty "$f" 2>/dev/null; then
        echo "[devcontainer] Warning: Invalid JSON detected in $f"
      fi
    fi
  done
fi

echo "[devcontainer] Editor-specific settings linked: ${flavor}"

