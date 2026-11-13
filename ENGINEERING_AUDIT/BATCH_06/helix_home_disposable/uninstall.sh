#!/bin/bash
# uninstall.sh — Remove HELIX desktop app
set -euo pipefail

HELIX_DIR="$HOME/helix"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor"
BIN_DIR="$HOME/.local/bin"

echo "=== Uninstalling HELIX desktop app ==="

# 1. Remove launcher
rm -f "$BIN_DIR/helix-desktop"
echo "[OK] Removed $BIN_DIR/helix-desktop"

# 2. Remove .desktop file
rm -f "$DESKTOP_DIR/helix.desktop"
echo "[OK] Removed $DESKTOP_DIR/helix.desktop"

# 3. Remove icons
for size in 16 32 48 64 128 256 512; do
    rm -f "$ICON_DIR/${size}x${size}/apps/helix.png" 2>/dev/null || true
    rm -f "$ICON_DIR/${size}x${size}/apps/helix.svg" 2>/dev/null || true
done
echo "[OK] Removed icons"

# 4. Remove desktop shortcut if it exists
rm -f "$HOME/Desktop/helix.desktop"
echo "[OK] Removed desktop shortcut (if present)"

# 5. Update caches
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
echo "=== Uninstall complete ==="