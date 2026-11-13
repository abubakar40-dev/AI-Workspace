#!/usr/bin/env bash
# ============================================================
# JARVIS — FULL RE-AUDIT (post-Linux-port, current state check)
# ============================================================
set -u

PROJECT="/run/media/abubakargcx/My Drive/JARVIS_linux_port/JARVIS"

echo "============================================================"
echo "                 JARVIS RE-AUDIT"
echo "============================================================"

if [ ! -d "$PROJECT" ]; then
    echo "ERROR: JARVIS project was not found at:"
    echo "$PROJECT"
    exit 1
fi

cd "$PROJECT"

echo
echo "========== LOCATION =========="
pwd

echo
echo "========== PROJECT SIZE =========="
du -sh .

echo
echo "========== GIT STATUS (uncommitted changes / patches applied) =========="
git status 2>/dev/null || echo "Not a git repo / git not initialized here."
git diff --stat 2>/dev/null

echo
echo "========== BACKUP FILES PRESENT (from prior patches) =========="
find . -maxdepth 2 -name "*.bak" -not -path './.git/*'

echo
echo "========== VENV STATUS =========="
if [ -d ".venv" ]; then
    echo ".venv exists"
    ls -la .venv/bin/python* 2>/dev/null
    echo "--- shebang check on key entrypoints (should point INTO this .venv) ---"
    for f in pip pip3 playwright; do
        if [ -f ".venv/bin/$f" ]; then
            echo "--- $f ---"
            head -n1 ".venv/bin/$f"
        fi
    done
else
    echo ".venv NOT FOUND"
fi

echo
echo "========== PYTHON / KEY PACKAGE VERSIONS =========="
if [ -f ".venv/bin/python3" ]; then
    PY=".venv/bin/python3"
else
    PY="python3"
fi
$PY --version
$PY -m pip --version 2>/dev/null
echo "--- installed packages relevant to JARVIS ---"
$PY -m pip list 2>/dev/null | grep -iE \
    "google-genai|google-generativeai|groq|tavily|sounddevice|PyQt6|playwright|openpyxl|python-pptx|python-docx|reportlab|discord|fastapi|uvicorn|cryptography|qrcode|edge-tts|mediapipe|opencv|websockets|mss|psutil|pyaudio"

echo
echo "========== API KEYS FILE PRESENT? (not printing contents) =========="
if [ -f "config/api_keys.json" ]; then
    echo "config/api_keys.json exists"
    python3 -c "
import json
try:
    d = json.load(open('config/api_keys.json'))
    for k in d:
        v = d[k]
        print(f'{k}: {\"SET\" if v else \"EMPTY\"} (len={len(v) if isinstance(v,str) else \"n/a\"})')
except Exception as e:
    print('Could not parse api_keys.json:', e)
"
else
    echo "config/api_keys.json MISSING"
fi

echo
echo "========== AUDIO DEVICE SETUP (current pin) =========="
grep -n "device=" main.py | grep -i "InputStream\|device=10\|device=0" 
grep -n -B2 -A8 "sd.InputStream(" main.py

echo
echo "========== SEND / RECEIVE SAMPLE RATE CONSTANTS =========="
grep -n "SEND_SAMPLE_RATE\s*=\|RECEIVE_SAMPLE_RATE\s*=\|CHANNELS\s*=\|CHUNK_SIZE\s*=\|LIVE_MODEL\s*=" main.py

echo
echo "========== GEMINI LIVE SESSION / RECONNECT LOGIC =========="
grep -n "go_away\|GoAway\|LIVE_CONNECT_TIMEOUT\|reconnect_attempt\|async with asyncio.TaskGroup" main.py

echo
echo "========== KNOWN OUTSTANDING ITEMS (per project backlog) =========="
for f in CLAUDE.md FEATURE_BACKLOG.md; do
    if [ -f "$f" ]; then
        echo "--- $f ---"
        cat "$f"
        echo
    else
        echo "$f NOT FOUND"
    fi
done

echo
echo "========== google.generativeai DEPRECATION FOOTPRINT =========="
grep -rln "import google.generativeai" --include="*.py" . | grep -v ".venv"

echo
echo "========== BRAHMA_CONNECT / MDNS INTEGRITY CHECK (must remain unchanged) =========="
grep -rn "_BRAHMA._tcp.local." --include="*.py" . | grep -v ".venv"
find . -maxdepth 1 -type d -name "brahma_connect"

echo
echo "========== STALE PATH REFERENCES (old ~/Projects/JARVIS or old drive path) =========="
grep -rln "Projects/JARVIS\|/home/abubakargcx/JARVIS_linux_port" --include="*.py" --include="*.json" --include="*.sh" . 2>/dev/null | grep -v ".venv"

echo
echo "========== SYSTEM AUDIO / DEVICE TOOLS AVAILABLE =========="
for app in ffplay paplay pactl wpctl xdotool wmctrl bluetoothctl; do
    command -v "$app" >/dev/null 2>&1 && echo "[OK] $app -> $(command -v $app)" || echo "[MISSING] $app"
done

echo
echo "========== CURRENT DEFAULT AUDIO SOURCE =========="
pactl get-default-source 2>/dev/null
pactl list short sources 2>/dev/null

echo
echo "========== BLUETOOTH DEVICES (relevant to mic drift theory) =========="
bluetoothctl devices 2>/dev/null

echo
echo "========== LAST CRASH-RELEVANT PYTHON FILES MODIFIED (last 3 days) =========="
find . -maxdepth 2 -name "*.py" -mtime -3 -not -path './.git/*' -not -path './.venv/*' -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -20

echo
echo "============================================================"
echo "                 RE-AUDIT COMPLETE"
echo "============================================================"
echo "No project files were modified by this audit."
