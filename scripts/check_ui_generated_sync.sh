#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON:-python3}"

"${PYTHON_BIN}" logic/convert_ui_to_py.py --sync-default-ui --timeout 30

if ! git diff --quiet -- interface/convertisseur.py; then
  echo "Le fichier généré interface/convertisseur.py n'était pas synchronisé avec interface/convertisseur.ui." >&2
  echo "Le hook l'a régénéré. Lance: git add interface/convertisseur.py puis recommence le commit." >&2
  exit 1
fi
