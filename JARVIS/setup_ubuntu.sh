#!/usr/bin/env bash
# setup_ubuntu.sh — one-time Linux setup for Jarvis (ported from Brahma Echo).
# Run this from inside the JARVIS project folder: bash setup_ubuntu.sh
set -e

echo "== Jarvis Ubuntu setup =="

echo "-- Installing system packages (apt) --"
sudo apt-get update
sudo apt-get install -y \
    python3-venv python3-pip \
    ffmpeg \
    xdotool wmctrl \
    at \
    scrot gnome-screenshot \
    espeak-ng \
    libxcb-cursor0 libxkbcommon-x11-0 \
    portaudio19-dev \
    xclip xsel

# Ubuntu 26.04 ships PipeWire (wpctl) by default; pulseaudio-utils (pactl) is
# only needed if you're on a classic PulseAudio setup. Install whichever applies:
if ! command -v wpctl >/dev/null 2>&1 && ! command -v pactl >/dev/null 2>&1; then
    sudo apt-get install -y pulseaudio-utils
fi

ENV_DIR="${JARVIS_ENV_DIR:-venv}"
echo "-- Creating Python virtual environment ($ENV_DIR) --"
python3 -m venv "$ENV_DIR"
source "$ENV_DIR/bin/activate"

echo "-- Installing Python dependencies --"
pip install --upgrade pip
pip install -r requirements-linux.txt

echo "-- Installing Playwright browsers --"
python -m playwright install chromium

echo "-- Installing the Jarvis terminal command --"
mkdir -p "$HOME/.local/bin"
ln -sfn "$PWD/bin/Jarvis" "$HOME/.local/bin/Jarvis"

echo
echo "== Setup complete =="
echo "Next steps:"
echo "  1. Edit config/api_keys.json and paste in your real API keys."
echo "  2. Ensure \$HOME/.local/bin is in PATH, then run: Jarvis"
