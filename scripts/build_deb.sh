#!/usr/bin/env bash
# Build script for ClipDen Debian package (.deb)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

VERSION="1.0.0"
PACKAGE_NAME="ClipDen"
ARCH="amd64"
DEB_FILENAME="${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
OUTPUT_DIR="$PROJECT_ROOT/dist/packages"
STAGING_DIR="$PROJECT_ROOT/build/deb_staging"

echo "=== Building ClipDen v${VERSION} Debian Package ==="
cd "$PROJECT_ROOT"

# 1. Clean previous build directories
echo "[1/5] Cleaning previous build artifacts..."
rm -rf "$STAGING_DIR"
mkdir -p "$OUTPUT_DIR"
mkdir -p "$STAGING_DIR"

# 2. Build PyInstaller bundle
echo "[2/5] Running PyInstaller..."
"$PROJECT_ROOT/.venv/bin/pyinstaller" --noconfirm --clean "$PROJECT_ROOT/packaging/clipden.spec"

# 3. Create Debian file hierarchy in staging
echo "[3/5] Setting up Debian file structure..."
INSTALL_OPT_DIR="$STAGING_DIR/opt/clipden"
BIN_DIR="$STAGING_DIR/usr/bin"
DESKTOP_DIR="$STAGING_DIR/usr/share/applications"
ICON_SCALABLE_DIR="$STAGING_DIR/usr/share/icons/hicolor/scalable/apps"
ICON_128_DIR="$STAGING_DIR/usr/share/icons/hicolor/128x128/apps"
DEBIAN_DIR="$STAGING_DIR/DEBIAN"

mkdir -p "$INSTALL_OPT_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$DESKTOP_DIR"
mkdir -p "$ICON_SCALABLE_DIR"
mkdir -p "$ICON_128_DIR"
mkdir -p "$DEBIAN_DIR"

# Copy application files (PyInstaller onedir output)
cp -a "$PROJECT_ROOT/dist/clipden/." "$INSTALL_OPT_DIR/"

# Remove any accidental environment files from bundled payload
rm -f "$INSTALL_OPT_DIR/.env" "$INSTALL_OPT_DIR/.env.*"

# Install launcher binary wrapper
install -m 755 "$PROJECT_ROOT/packaging/debian/clipden-launcher" "$BIN_DIR/clipden"

# Install desktop entry
install -m 644 "$PROJECT_ROOT/packaging/debian/clipden.desktop" "$DESKTOP_DIR/clipden.desktop"

# Install icons
if [ -f "$PROJECT_ROOT/assets/clipden.svg" ]; then
    install -m 644 "$PROJECT_ROOT/assets/clipden.svg" "$ICON_SCALABLE_DIR/clipden.svg"
fi
if [ -f "$PROJECT_ROOT/assets/clipden.png" ]; then
    install -m 644 "$PROJECT_ROOT/assets/clipden.png" "$ICON_128_DIR/clipden.png"
fi

# Copy Debian control files
install -m 644 "$PROJECT_ROOT/packaging/debian/control" "$DEBIAN_DIR/control"
install -m 755 "$PROJECT_ROOT/packaging/debian/postinst" "$DEBIAN_DIR/postinst"
install -m 755 "$PROJECT_ROOT/packaging/debian/postrm" "$DEBIAN_DIR/postrm"

# 4. Calculate Installed-Size
INSTALLED_SIZE=$(du -sk "$STAGING_DIR" | cut -f1)
sed -i "/^Architecture:/a Installed-Size: ${INSTALLED_SIZE}" "$DEBIAN_DIR/control"

# 5. Build Debian package using dpkg-deb
echo "[4/5] Building .deb package with dpkg-deb..."
dpkg-deb --root-owner-group --build "$STAGING_DIR" "$OUTPUT_DIR/$DEB_FILENAME"

echo "[5/5] Package successfully created:"
ls -lh "$OUTPUT_DIR/$DEB_FILENAME"

echo "=== Build Complete ==="
