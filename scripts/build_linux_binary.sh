#!/usr/bin/env bash
set -euo pipefail

# Genere un binaire GUI Linux avec PyInstaller (format onedir, plus fiable avec Qt).
# Usage:
#   scripts/build_linux_binary.sh
# Variables d'environnement optionnelles:
#   PYTHON_BIN=.venv/bin/python APP_NAME=ConvertisseurUiPy ICON_PATH=convertir.py.png

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

PYTHON_BIN="${PYTHON_BIN:-$PROJECT_ROOT/.venv/bin/python}"
APP_NAME="${APP_NAME:-ConvertisseurUiPy}"
ICON_PATH="${ICON_PATH:-$PROJECT_ROOT/convertir.py.png}"

# Verifie la presence d'un interpreteur Python executable.
if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python introuvable: $PYTHON_BIN" >&2
  echo "Astuce: active ton venv puis relance, ou passe PYTHON_BIN=/chemin/python" >&2
  exit 1
fi

# Installe/actualise les dependances minimales de build.
"$PYTHON_BIN" -m pip install --upgrade pip >/dev/null
"$PYTHON_BIN" -m pip install -r requirements-runtime.txt pyinstaller

# Nettoie les anciens artefacts pour un build propre.
rm -rf build dist

# Arguments PyInstaller de base pour une app desktop Qt.
PYINSTALLER_ARGS=(
  --name "$APP_NAME"
  --windowed
  --onedir
  --collect-all PySide6
  main.py
)

# Ajoute l'icone seulement si le fichier existe.
if [[ -f "$ICON_PATH" ]]; then
  PYINSTALLER_ARGS=(--icon "$ICON_PATH" "${PYINSTALLER_ARGS[@]}")
fi

# Lance la generation du binaire.
"$PYTHON_BIN" -m PyInstaller "${PYINSTALLER_ARGS[@]}"

echo
# Verifie que le binaire attendu est bien produit.
if [[ -x "dist/$APP_NAME/$APP_NAME" ]]; then
  echo "Build OK: dist/$APP_NAME/$APP_NAME"
else
  echo "Build termine, mais binaire non trouve: dist/$APP_NAME/$APP_NAME" >&2
  exit 1
fi
