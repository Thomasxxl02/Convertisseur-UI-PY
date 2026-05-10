#!/usr/bin/env bash
set -euo pipefail

APP_ID="convertisseur-ui-py"
APP_NAME="Convertisseur UI Py"
APP_COMMENT="Lance le convertisseur UI vers Python"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAUNCHER_PATH="$PROJECT_DIR/executer_ubuntu.sh"
ICON_PATH="$PROJECT_DIR/convertir.py.png"

DESKTOP_DIR="$HOME/.local/share/applications"
BIN_DIR="$HOME/.local/bin"
DESKTOP_PATH="$DESKTOP_DIR/${APP_ID}.desktop"
BIN_PATH="$BIN_DIR/${APP_ID}"

if [[ ! -x "$LAUNCHER_PATH" ]]; then
  echo "Erreur: lanceur introuvable ou non exécutable: $LAUNCHER_PATH" >&2
  echo "Astuce: exécute d'abord: chmod +x \"$LAUNCHER_PATH\"" >&2
  exit 1
fi

mkdir -p "$DESKTOP_DIR" "$BIN_DIR"

# Installe une entrée d'application conforme pour le menu Ubuntu.
cat > "$DESKTOP_PATH" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=$APP_NAME
Comment=$APP_COMMENT
Exec=$LAUNCHER_PATH
Path=$PROJECT_DIR
Icon=$ICON_PATH
Terminal=false
Categories=Development;
Keywords=Qt;PySide6;UI;Convertisseur;
StartupNotify=true
EOF

chmod +x "$DESKTOP_PATH"

# Ajoute une commande terminal simple: convertisseur-ui-py
cat > "$BIN_PATH" <<EOF
#!/usr/bin/env bash
exec \"$LAUNCHER_PATH\" \"\$@\"
EOF

chmod +x "$BIN_PATH"

if command -v desktop-file-validate >/dev/null 2>&1; then
  desktop-file-validate "$DESKTOP_PATH"
fi

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$DESKTOP_DIR" || true
fi

if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
  echo "Note: $BIN_DIR n'est pas dans PATH pour ce shell."
  echo "Ajoute cette ligne a ~/.profile puis reconnecte-toi:"
  echo "export PATH=\"$BIN_DIR:\$PATH\""
fi

echo "Installation terminee."
echo "- Menu Ubuntu: $APP_NAME"
echo "- Commande terminal: $APP_ID"
echo "- Fichier desktop: $DESKTOP_PATH"
