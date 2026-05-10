#!/usr/bin/env bash
set -euo pipefail

# Genere un paquet .deb a partir du binaire Linux produit par PyInstaller.
# Usage:
#   scripts/build_deb.sh
# Variables d'environnement optionnelles:
#   APP_NAME=ConvertisseurUiPy
#   PACKAGE_NAME=convertisseur-ui-py
#   VERSION=1.0.0
#   MAINTAINER="Ton Nom <ton@email.com>"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

APP_NAME="${APP_NAME:-ConvertisseurUiPy}"
PACKAGE_NAME="${PACKAGE_NAME:-convertisseur-ui-py}"
VERSION="${VERSION:-1.0.0}"
MAINTAINER="${MAINTAINER:-Convertisseur UI PY <noreply@example.com>}"

# Verifie que les outils Debian necessaires sont disponibles.
if ! command -v dpkg-deb >/dev/null 2>&1; then
  echo "dpkg-deb est requis (installe le paquet dpkg)." >&2
  exit 1
fi

if ! command -v dpkg >/dev/null 2>&1; then
  echo "dpkg est requis pour detecter l'architecture." >&2
  exit 1
fi

# Si le binaire n'existe pas encore, on lance automatiquement le build Linux.
if [[ ! -x "dist/$APP_NAME/$APP_NAME" ]]; then
  echo "Binaire manquant: dist/$APP_NAME/$APP_NAME" >&2
  echo "Execution automatique du build binaire..."
  scripts/build_linux_binary.sh
fi

# Prepare l'arborescence Debian standard du paquet.
ARCH="$(dpkg --print-architecture)"
PKG_ROOT="dist/${PACKAGE_NAME}_${VERSION}_${ARCH}"
DEBIAN_DIR="$PKG_ROOT/DEBIAN"
OPT_DIR="$PKG_ROOT/opt/$PACKAGE_NAME"
BIN_DIR="$PKG_ROOT/usr/local/bin"
DESKTOP_DIR="$PKG_ROOT/usr/share/applications"
ICON_DIR="$PKG_ROOT/usr/share/icons/hicolor/256x256/apps"

rm -rf "$PKG_ROOT"
mkdir -p "$DEBIAN_DIR" "$OPT_DIR" "$BIN_DIR" "$DESKTOP_DIR" "$ICON_DIR"

# Copie le contenu de l'application dans /opt du paquet.
cp -r "dist/$APP_NAME/." "$OPT_DIR/"

# Cree le lanceur en ligne de commande utilise aussi par le .desktop.
cat > "$BIN_DIR/$PACKAGE_NAME" <<'SH'
#!/usr/bin/env sh
exec /opt/convertisseur-ui-py/ConvertisseurUiPy "$@"
SH
chmod +x "$BIN_DIR/$PACKAGE_NAME"

# Genere le fichier control depuis le template en injectant version, arch et mainteneur.
sed \
  -e "s|__VERSION__|$VERSION|g" \
  -e "s|__ARCH__|$ARCH|g" \
  -e "s|__MAINTAINER__|$MAINTAINER|g" \
  packaging/deb/control > "$DEBIAN_DIR/control"

# Installe l'entree de menu (desktop entry) dans le paquet.
cp packaging/deb/convertisseur-ui-py.desktop "$DESKTOP_DIR/$PACKAGE_NAME.desktop"

# Copie l'icone de l'application si elle existe.
if [[ -f "convertir.py.png" ]]; then
  cp "convertir.py.png" "$ICON_DIR/$PACKAGE_NAME.png"
fi

chmod 0644 "$DEBIAN_DIR/control" "$DESKTOP_DIR/$PACKAGE_NAME.desktop"

# Construit le paquet .deb final dans le dossier dist.
OUTPUT_DEB="dist/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
rm -f "$OUTPUT_DEB"
dpkg-deb --build "$PKG_ROOT" "$OUTPUT_DEB" >/dev/null

echo "Package Debian genere: $OUTPUT_DEB"
