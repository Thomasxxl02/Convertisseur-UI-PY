#!/usr/bin/env bash
set -euo pipefail

# Se place dans le dossier du projet, même en lancement par double-clic.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"

if [[ -x "$VENV_PYTHON" ]]; then
  exec "$VENV_PYTHON" "$SCRIPT_DIR/main.py"
fi

# Fallback si le venv n'existe pas.
exec python3 "$SCRIPT_DIR/main.py"
