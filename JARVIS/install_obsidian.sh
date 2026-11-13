#!/bin/bash
# install_obsidian.sh — Install Obsidian for JARVIS integration
# Run from the JARVIS project directory

set -e

echo "== Installing Obsidian for JARVIS =="
echo ""

VAULT_DIR="$HOME/.obsidian-vault"

# Check if vault exists
if [ ! -d "$VAULT_DIR" ]; then
    echo "ERROR: Vault not found at $VAULT_DIR"
    echo "Run the Obsidian integration first."
    exit 1
fi

echo "Vault found at $VAULT_DIR"
echo ""

# Try various installation methods
echo "Trying to install Obsidian..."
echo ""

# Method 1: Try pip (for obsidian-py or similar)
echo "[1/4] Trying pip install..."
pip install obsidian-api 2>/dev/null && echo "  ✓ Installed via pip" && exit 0 || echo "  ✗ pip install failed"

# Method 2: Try to download .deb from official GitHub releases
echo "[2/4] Trying GitHub download..."
curl -sL -o /tmp/obsidian.deb "https://github.com/obsidianmd/obsidian-releases/releases/download/v1.9.4/obsidian_1.9.4-16299_amd64.deb" 2>/dev/null
if [ -f /tmp/obsidian.deb ] && [ $(stat -c%s /tmp/obsidian.deb) -gt 1000000 ]; then
    echo "  ✓ Downloaded .deb ($(stat -c%s /tmp/obsidian.deb) bytes)"
    echo ""
    echo "To install, run:"
    echo "  sudo dpkg -i /tmp/obsidian.deb"
    exit 0
fi
echo "  ✗ GitHub download failed"

# Method 3: Try Flatpak
echo "[3/4] Trying Flatpak..."
flatpak install --user -y com.obsidianmd.Obsidian 2>/dev/null && echo "  ✓ Installed via Flatpak" && exit 0 || echo "  ✗ Flatpak install failed"

# Method 4: Try Snap
echo "[4/4] Trying Snap..."
sudo snap install obsidian 2>/dev/null && echo "  ✓ Installed via Snap" && exit 0 || echo "  ✗ Snap install failed"

echo ""
echo "All automatic methods failed."
echo ""
echo "Please install Obsidian manually from: https://obsidian.md"
echo "After installation, open the vault at: $VAULT_DIR"
echo ""
echo "Recommended plugins:"
echo "  - Local REST API (for programmatic access)"
echo "  - Templater (for auto-generating notes)"
echo "  - Data View (for querying notes)"
echo "  - Calendar (for browsing daily conversations)"
