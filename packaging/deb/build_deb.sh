#!/usr/bin/env bash
set -euo pipefail

APP_ID="convertisseur-ui-py"
APP_NAME="Convertisseur UI Py"
VERSION="1.0.0"
ARCH="all"
MAINTAINER="Thomas <thomas@localhost>"
DESCRIPTION="Convertisseur Qt Designer .ui vers Python (PySide6)"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD_DIR="$PROJECT_DIR/dist/deb-build"
PKG_DIR="$BUILD_DIR/${APP_ID}_${VERSION}_${ARCH}"

rm -rf "$BUILD_DIR"
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/opt/$APP_ID"
mkdir -p "$PKG_DIR/usr/bin"
mkdir -p "$PKG_DIR/usr/share/applications"
mkdir -p "$PKG_DIR/usr/share/icons/hicolor/256x256/apps"

# Copie les fichiers applicatifs (sans le venv, caches et outils de packaging).
cp "$PROJECT_DIR/main.py" "$PKG_DIR/opt/$APP_ID/main.py"
cp -r "$PROJECT_DIR/logic" "$PKG_DIR/opt/$APP_ID/logic"
cp -r "$PROJECT_DIR/interface" "$PKG_DIR/opt/$APP_ID/interface"

find "$PKG_DIR/opt/$APP_ID" -type d -name "__pycache__" -prune -exec rm -rf {} +
find "$PKG_DIR/opt/$APP_ID" -type f -name "*.pyc" -delete

# Lanceur CLI global.
cat > "$PKG_DIR/usr/bin/$APP_ID" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
exec /usr/bin/python3 /opt/convertisseur-ui-py/main.py "$@"
EOF
chmod 0755 "$PKG_DIR/usr/bin/$APP_ID"

# Entrée menu desktop.
cat > "$PKG_DIR/usr/share/applications/$APP_ID.desktop" <<'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Convertisseur UI Py
Comment=Lance le convertisseur UI vers Python
Exec=convertisseur-ui-py
Icon=convertisseur-ui-py
Terminal=false
Categories=Development;
Keywords=Qt;PySide6;UI;Convertisseur;
StartupNotify=true
EOF

cp "$PROJECT_DIR/convertir.py.png" "$PKG_DIR/usr/share/icons/hicolor/256x256/apps/$APP_ID.png"

cat > "$PKG_DIR/DEBIAN/control" <<EOF
Package: $APP_ID
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Maintainer: $MAINTAINER
Depends: python3, python3-pyside6
Description: $DESCRIPTION
 Application de bureau PySide6 pour convertir des fichiers .ui Qt Designer
 en modules Python.
EOF

# Permissions Debian recommandées.
find "$PKG_DIR/opt/$APP_ID" -type d -exec chmod 0755 {} +
find "$PKG_DIR/opt/$APP_ID" -type f -exec chmod 0644 {} +
chmod 0755 "$PKG_DIR/opt/$APP_ID/main.py"
chmod 0644 "$PKG_DIR/usr/share/applications/$APP_ID.desktop"
chmod 0644 "$PKG_DIR/usr/share/icons/hicolor/256x256/apps/$APP_ID.png"
chmod 0644 "$PKG_DIR/DEBIAN/control"

OUT_DEB="$PROJECT_DIR/dist/${APP_ID}_${VERSION}_${ARCH}.deb"
mkdir -p "$PROJECT_DIR/dist"

dpkg-deb --build --root-owner-group "$PKG_DIR" "$OUT_DEB"

echo "Paquet cree: $OUT_DEB"
