#!/bin/bash
# install.sh — Install HELIX desktop app locally
set -euo pipefail

HELIX_DIR="$HOME/helix"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor"
BIN_DIR="$HOME/.local/bin"

echo "=== Installing HELIX desktop app ==="

# 1. Install launcher script
mkdir -p "$BIN_DIR"
cp "$HELIX_DIR/bridge/helix_desktop.py" "$BIN_DIR/helix-desktop"
chmod +x "$BIN_DIR/helix-desktop"
echo "[OK] Installed $BIN_DIR/helix-desktop"

# 2. Install .desktop file
mkdir -p "$DESKTOP_DIR"
cp "$HELIX_DIR/bridge/helix.desktop" "$DESKTOP_DIR/helix.desktop"
chmod +x "$DESKTOP_DIR/helix.desktop"
echo "[OK] Installed $DESKTOP_DIR/helix.desktop"

# 3. Install icons
for size in 16 32 48 64 128 256 512; do
    DIR="$ICON_DIR/${size}x${size}/apps"
    mkdir -p "$DIR"
    cp "$HELIX_DIR/tools/helix-icon.svg" "$DIR/helix.svg" 2>/dev/null || true
    # Use the pre-rendered PNG if it exists, otherwise render from the SVG.
    # (The old branch copied the destination onto itself, so `set -e` aborted.)
    if [ ! -f "$DIR/helix.png" ] && command -v convert >/dev/null 2>&1; then
        convert -background none -resize ${size}x${size} \
            "$HELIX_DIR/tools/helix-icon.svg" "$DIR/helix.png"
    fi
done
echo "[OK] Installed icons"

# 4. Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DESKTOP_DIR"
    echo "[OK] Ran update-desktop-database"
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    for size in 16 32 48 64 128 256 512; do
        gtk-update-icon-cache -t "$ICON_DIR/${size}x${size}" 2>/dev/null || true
    done
    echo "[OK] Ran gtk-update-icon-cache"
fi

echo ""
echo "=== Installation complete ==="
echo "Launch from app grid: HELIX AI Command Center"
echo "Or run: $BIN_DIR/helix-desktop"