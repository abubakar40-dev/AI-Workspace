#!/usr/bin/env bash
# One-time setup: let this user inject keyboard/mouse events on Wayland.
#
# Wayland compositors ignore X11 (XTEST) input for native windows, so the
# only way for Jarvis -- or any background tool -- to control the desktop
# (including GNOME's screenshot UI) is the kernel's /dev/uinput device.
# This script installs a udev rule so the permission survives reboots and
# applies it immediately for the current boot. Safe to re-run.
#
# Run as root:
#     pkexec bash setup_uinput.sh        (GUI password prompt)
#  or sudo bash setup_uinput.sh
#
# Security note: MODE="0666" lets *any* local process inject input. That
# is the usual trade-off for desktop automation tools (ydotool/dotool use
# the same rule) and is normal on a single-user personal machine. Change
# MODE to "0660" and add yourself to the "input" group instead if you
# prefer group-restricted access (takes effect after re-login).
set -euo pipefail

RULE=/etc/udev/rules.d/99-jarvis-uinput.rules

if [ "$(id -u)" -ne 0 ]; then
    echo "This script must run as root: pkexec bash $0  (or sudo bash $0)" >&2
    exit 1
fi

echo 'KERNEL=="uinput", MODE="0666"' > "$RULE"
echo "Installed $RULE"

udevadm control --reload-rules 2>/dev/null || true
# uinput is a misc-class device; re-trigger it so the rule applies now
# instead of waiting for the next reboot.
udevadm trigger --subsystem-match=misc --action=change 2>/dev/null || true
udevadm trigger 2>/dev/null || true

# Current boot, belt and braces:
chmod 0666 /dev/uinput 2>/dev/null || true

if [ -w /dev/uinput ]; then
    echo "OK: /dev/uinput is now writable — Wayland mouse/keyboard control enabled."
    ls -l /dev/uinput
else
    echo "FAILED: /dev/uinput is still not writable." >&2
    exit 2
fi
