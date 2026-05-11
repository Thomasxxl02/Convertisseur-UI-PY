#!/usr/bin/env bash
set -euo pipefail

# Genere un binaire GUI Linux avec PyInstaller (format onedir, plus fiable avec Qt).
# Usage:
#   scripts/build_linux_binary.sh
# Variables d'environnement optionnelles:
#   PYTHON_BIN=.venv/bin/python APP_NAME=ConvertisseurUiPy ICON_PATH=convertir.py.png
#   CLEAN_BUILD=1 UPGRADE_PIP=0 INSTALL_DEPS=1 PYINSTALLER_EXTRA_ARGS="--log-level=WARN"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

PYTHON_BIN="${PYTHON_BIN:-$PROJECT_ROOT/.venv/bin/python}"
APP_NAME="${APP_NAME:-ConvertisseurUiPy}"
ICON_PATH="${ICON_PATH:-$PROJECT_ROOT/convertir.py.png}"
CLEAN_BUILD="${CLEAN_BUILD:-1}"
UPGRADE_PIP="${UPGRADE_PIP:-0}"
INSTALL_DEPS="${INSTALL_DEPS:-1}"
PYINSTALLER_EXTRA_ARGS="${PYINSTALLER_EXTRA_ARGS:-}"

log_info() {
  echo "[INFO] $*"
}

log_error() {
  echo "[ERREUR] $*" >&2
}

# Verifie la presence d'un interpreteur Python executable.
if [[ ! -x "$PYTHON_BIN" ]]; then
  log_error "Python introuvable: $PYTHON_BIN"
  log_error "Astuce: active ton venv puis relance, ou passe PYTHON_BIN=/chemin/python"
  exit 1
fi

# Ce script cible un packaging Linux.
if [[ "${OSTYPE:-}" != linux* ]]; then
  log_error "Ce script est prevu pour Linux (OSTYPE actuel: ${OSTYPE:-inconnu})."
  exit 1
fi

if [[ ! -f "main.py" ]]; then
  log_error "Fichier introuvable: $PROJECT_ROOT/main.py"
  exit 1
fi

if [[ ! -f "requirements-runtime.txt" ]]; then
  log_error "Fichier introuvable: $PROJECT_ROOT/requirements-runtime.txt"
  exit 1
fi

# Installe/actualise les dependances minimales de build.
if [[ "$INSTALL_DEPS" == "1" ]]; then
  if [[ "$UPGRADE_PIP" == "1" ]]; then
    log_info "Mise a jour de pip..."
    "$PYTHON_BIN" -m pip install --upgrade pip >/dev/null
  fi
  log_info "Installation des dependances runtime + PyInstaller..."
  "$PYTHON_BIN" -m pip install -r requirements-runtime.txt pyinstaller
else
  log_info "INSTALL_DEPS=0: installation des dependances ignoree."
fi

# Nettoie les anciens artefacts pour un build propre.
if [[ "$CLEAN_BUILD" == "1" ]]; then
  log_info "Nettoyage des anciens artefacts (build/, dist/)..."
  rm -rf build dist
fi

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

if [[ -n "$PYINSTALLER_EXTRA_ARGS" ]]; then
  # shellcheck disable=SC2206
  EXTRA_ARGS=($PYINSTALLER_EXTRA_ARGS)
  PYINSTALLER_ARGS=("${EXTRA_ARGS[@]}" "${PYINSTALLER_ARGS[@]}")
fi

# Lance la generation du binaire.
log_info "Generation du binaire PyInstaller..."
"$PYTHON_BIN" -m PyInstaller "${PYINSTALLER_ARGS[@]}"

echo
# Verifie que le binaire attendu est bien produit.
if [[ -x "dist/$APP_NAME/$APP_NAME" ]]; then
  log_info "Build OK: dist/$APP_NAME/$APP_NAME"
  log_info "Execution: ./dist/$APP_NAME/$APP_NAME"
else
  log_error "Build termine, mais binaire non trouve: dist/$APP_NAME/$APP_NAME"
  exit 1
fi
