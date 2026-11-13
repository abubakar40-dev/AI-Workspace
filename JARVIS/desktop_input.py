# desktop_input.py
"""
Wayland-capable mouse/keyboard injection for Jarvis.

Why this exists
---------------
On an X11 session pyautogui (XTEST) can drive the whole desktop. On
Wayland, XTEST only reaches XWayland clients: every native GTK/Qt/Firefox
window *and* GNOME Shell's own UI (including the screenshot UI) ignore it,
so clicks and keystrokes silently vanish. The only display-server-
independent injection point is the kernel's virtual input facility,
``/dev/uinput``. This module writes to it directly in pure Python -- no
compiled dependencies, no daemon -- and falls back to pyautogui whenever
uinput is unavailable.

Backend rule (so nothing that works today ever changes):

* X11 session            -> pyautogui, exactly as before, always.
* Wayland + uinput ready  -> uinput (controls everything, including the
                             Shell's screenshot UI).
* Wayland, no uinput      -> pyautogui (today's partial behaviour) plus a
                             ``status()`` hint explaining the one-time
                             setup (``setup_uinput.sh``).

Public API is action-only (no message strings -- callers format their own
messages, so existing user-facing text never changes):

    active()              True when input must go through uinput
    status()              human-readable backend/permission report
    type_text(text, interval)
    hotkey(*keys)
    press(key)
    click(x, y, button, clicks)
    move(x, y, duration)
    drag(x1, y1, x2, y2, duration)
    scroll(vertical, clicks)
"""

from __future__ import annotations

import fcntl
import os
import struct
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from x11_access import require_pyautogui  # noqa: E402

SETUP_HINT = (
    "Wayland needs write access to /dev/uinput for real mouse/keyboard control. "
    "One-time setup: run `pkexec bash setup_uinput.sh` (or `sudo bash setup_uinput.sh`)."
)

# --------------------------------------------------------------------------
# kernel uinput protocol (stable ABI, written by hand to avoid a dependency)
# --------------------------------------------------------------------------
UI_SET_EVBIT = 0x40045564   # _IOW('U', 100, int)
UI_SET_KEYBIT = 0x40045565  # _IOW('U', 101, int)
UI_SET_RELBIT = 0x40045566  # _IOW('U', 102, int)
UI_SET_ABSBIT = 0x40045567  # _IOW('U', 103, int)
UI_DEV_CREATE = 0x5501      # _IO('U', 1)
UI_DEV_DESTROY = 0x5502     # _IO('U', 2)

EV_SYN, EV_KEY, EV_REL, EV_ABS = 0x00, 0x01, 0x02, 0x03
SYN_REPORT = 0
REL_X, REL_Y, REL_HWHEEL, REL_WHEEL = 0, 1, 6, 8
ABS_X, ABS_Y = 0, 1
BTN_LEFT, BTN_RIGHT, BTN_MIDDLE = 0x110, 0x111, 0x112
BUS_VIRTUAL = 0x06

# struct uinput_user_dev: name[80], input_id{4xu16}, ff_effects_max{u32},
# absmax/absmin/absfuzz/absflat[64] each -- 1116 bytes, no padding.
UINPUT_USER_DEV_FMT = "=80sHHHHI" + "i" * 256
# struct input_event: timeval{2xlong} + type + code + value -> 24 bytes (64-bit)
_TIME_FMT = "qq" if struct.calcsize("=q") == 8 and sys.maxsize > 2 ** 32 else "ll"
INPUT_EVENT_FMT = f"={_TIME_FMT}HHi"

UINPUT_PATH = "/dev/uinput"

# --------------------------------------------------------------------------
# key maps (Linux input-event codes)
# --------------------------------------------------------------------------
_LETTER_ROWS = (("qwertyuiop", 16), ("asdfghjkl", 30), ("zxcvbnm", 44))
_DIGIT_BASE = {"1": 2, "2": 3, "3": 4, "4": 5, "5": 6,
               "6": 7, "7": 8, "8": 9, "9": 10, "0": 11}

_NAMED = {
    "esc": 1, "escape": 1, "backspace": 14, "tab": 15,
    "enter": 28, "return": 28, "space": 57, "capslock": 58,
    "numlock": 69, "scrolllock": 70, "printscreen": 99, "print": 99,
    "pause": 119, "break": 119, "menu": 127, "appmenu": 127,
    "insert": 110, "delete": 111, "del": 111,
    "home": 102, "end": 107, "pageup": 104, "pgup": 104,
    "pagedown": 109, "pgdn": 109,
    "up": 103, "down": 108, "left": 105, "right": 106,
    "ctrl": 29, "control": 29, "ctrlleft": 29, "ctrl_l": 29, "ctrlright": 97,
    "shift": 42, "shiftleft": 42, "shift_l": 42, "shiftright": 54,
    "alt": 56, "altleft": 56, "alt_l": 56, "altright": 100,
    "win": 125, "winleft": 125, "meta": 125, "super": 125, "cmd": 125,
    "command": 125, "winright": 126, "metaright": 126,
    "volumeup": 115, "volumedown": 114, "volumemute": 113,
    "nexttrack": 163, "playpause": 164, "prevtrack": 165,
}
for _n in range(1, 10):  # f1..f9 = 59..67
    _NAMED[f"f{_n}"] = 58 + _n
_NAMED["f10"] = 68
_NAMED["f11"] = 87
_NAMED["f12"] = 88
for _n in range(13, 25):  # f13..f24 = 183..194
    _NAMED[f"f{_n}"] = 170 + _n

_KEYS_BY_NAME: dict[str, int] = dict(_NAMED)
for _row, _base in _LETTER_ROWS:
    for _off, _ch in enumerate(_row):
        _KEYS_BY_NAME[_ch] = _base + _off
_KEYS_BY_NAME.update(_DIGIT_BASE)

# char -> (keycode, needs_shift); covers printable ASCII (US layout)
_CHAR_MAP: dict[str, tuple[int, bool]] = {}
for _row, _base in _LETTER_ROWS:
    for _off, _ch in enumerate(_row):
        _CHAR_MAP[_ch] = (_base + _off, False)
        _CHAR_MAP[_ch.upper()] = (_base + _off, True)
for _ch, _code in _DIGIT_BASE.items():
    _CHAR_MAP[_ch] = (_code, False)
for _ch, _code in zip("!@#$%^&*()", [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]):
    _CHAR_MAP[_ch] = (_code, True)
for _ch, _code, _shift in (
    ("-", 12, False), ("_", 12, True), ("=", 13, False), ("+", 13, True),
    ("[", 26, False), ("{", 26, True), ("]", 27, False), ("}", 27, True),
    ("\\", 43, False), ("|", 43, True), (";", 39, False), (":", 39, True),
    ("'", 40, False), ('"', 40, True), ("`", 41, False), ("~", 41, True),
    (",", 51, False), ("<", 51, True), (".", 52, False), (">", 52, True),
    ("/", 53, False), ("?", 53, True), (" ", 57, False),
    ("\n", 28, False), ("\r", 28, False), ("\t", 15, False),
):
    _CHAR_MAP[_ch] = (_code, _shift)

_KB_KEYS = sorted(set(_KEYS_BY_NAME.values()) | {v for v, _ in _CHAR_MAP.values()})
_MOUSE_KEYS = [BTN_LEFT, BTN_RIGHT, BTN_MIDDLE]

# --------------------------------------------------------------------------
# state
# --------------------------------------------------------------------------
_STATE = {
    "ready": None,          # None = untested, True/False = cached
    "retry_at": 0.0,
    "error": None,
    "kb": None,
    "mouse": None,
    "abs_works": None,      # set by mouse calibration
    "verified": None,       # pointer position verified after calibration
}


def reset() -> None:
    """Forget cached devices/decisions (used by tests and after setup)."""
    for dev in (_STATE["kb"], _STATE["mouse"]):
        try:
            if dev is not None:
                dev.close()
        except Exception:
            pass
    _STATE.update(ready=None, retry_at=0.0, error=None, kb=None, mouse=None,
                  abs_works=None, verified=None)


def is_wayland() -> bool:
    if os.environ.get("WAYLAND_DISPLAY"):
        return True
    return os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"


def uinput_writable() -> bool:
    try:
        return os.access(UINPUT_PATH, os.W_OK)
    except Exception:
        return False


# --------------------------------------------------------------------------
# kernel device wrapper
# --------------------------------------------------------------------------
class _KernelDevice:
    """One /dev/uinput virtual device."""

    def __init__(self, name: str, *, keys=(), rels=(), abs_max=()):
        self.fd = os.open(UINPUT_PATH, os.O_WRONLY | os.O_NONBLOCK)
        try:
            fcntl.ioctl(self.fd, UI_SET_EVBIT, EV_KEY)
            for code in keys:
                fcntl.ioctl(self.fd, UI_SET_KEYBIT, int(code))
            if rels:
                fcntl.ioctl(self.fd, UI_SET_EVBIT, EV_REL)
                for axis in rels:
                    fcntl.ioctl(self.fd, UI_SET_RELBIT, int(axis))
            if abs_max:
                fcntl.ioctl(self.fd, UI_SET_EVBIT, EV_ABS)
                for axis in range(len(abs_max)):
                    fcntl.ioctl(self.fd, UI_SET_ABSBIT, int(axis))
            n = 64
            maxes = list(abs_max) + [0] * (n - len(abs_max))
            mins = [0] * n
            fuzz = [0] * n
            flat = [0] * n
            payload = struct.pack(
                UINPUT_USER_DEV_FMT,
                name.encode()[:79], BUS_VIRTUAL, 0x1212, 0x0001, 1, 0,
                *maxes, *mins, *fuzz, *flat,
            )
            os.write(self.fd, payload)
            fcntl.ioctl(self.fd, UI_DEV_CREATE)
            time.sleep(0.15)  # let udev/libinput pick the device up
        except BaseException:
            try:
                os.close(self.fd)
            except Exception:
                pass
            raise
        self.closed = False

    # -- event writers ----------------------------------------------------
    def _write(self, etype: int, code: int, value: int) -> None:
        os.write(self.fd, struct.pack(INPUT_EVENT_FMT, 0, 0, etype, code, value))

    def key(self, code: int, down: bool) -> None:
        self._write(EV_KEY, code, 1 if down else 0)

    def rel(self, axis: int, value: int) -> None:
        self._write(EV_REL, axis, int(value))

    def abs(self, axis: int, value: int) -> None:
        self._write(EV_ABS, axis, int(value))

    def syn(self) -> None:
        self._write(EV_SYN, SYN_REPORT, 0)

    def close(self) -> None:
        if not self.closed:
            self.closed = True
            try:
                fcntl.ioctl(self.fd, UI_DEV_DESTROY)
            except Exception:
                pass
            try:
                os.close(self.fd)
            except Exception:
                pass


def _keyboard() -> _KernelDevice:
    dev = _STATE["kb"]
    if dev is None or dev.closed:
        dev = _KernelDevice("jarvis-keyboard", keys=_KB_KEYS)
        _STATE["kb"] = dev
    return dev


def _screen_size() -> tuple[int, int]:
    try:
        pg = require_pyautogui()
        w, h = pg.size()
        if w and h:
            return int(w), int(h)
    except Exception:
        pass
    try:
        out = subprocess.run(["xdotool", "getdisplaygeometry"],
                             capture_output=True, text=True, timeout=3)
        w, h = (int(v) for v in out.stdout.split())
        if w and h:
            return w, h
    except Exception:
        pass
    return 1920, 1080


def _mouse() -> _KernelDevice:
    dev = _STATE["mouse"]
    if dev is None or dev.closed:
        w, h = _screen_size()
        dev = _KernelDevice(
            "jarvis-mouse",
            keys=_MOUSE_KEYS,
            rels=(REL_X, REL_Y, REL_WHEEL, REL_HWHEEL),
            abs_max=(max(w - 1, 1), max(h - 1, 1)),
        )
        _STATE["mouse"] = dev
        _calibrate(dev)
    return dev


# --------------------------------------------------------------------------
# pointer position (XWayland mirrors the global pointer, so both readers
# agree on a Wayland session -- verified live on this machine)
# --------------------------------------------------------------------------
def pointer_pos() -> tuple[int, int] | None:
    try:
        out = subprocess.run(["xdotool", "getmouselocation"],
                             capture_output=True, text=True, timeout=3)
        if out.returncode == 0 and "x:" in out.stdout:
            part = out.stdout.split()
            x = int(part[0].split(":")[1])
            y = int(part[1].split(":")[1])
            return x, y
    except Exception:
        pass
    try:
        pg = require_pyautogui()
        p = pg.position()
        return int(p[0]), int(p[1])
    except Exception:
        return None


def _calibrate(dev: _KernelDevice) -> None:
    """Decide how to move the cursor: absolute coordinates (preferred, no
    position feedback needed) or relative deltas from the current pointer.

    Both paths are verified by moving ~60px and reading the pointer back;
    the cursor is restored afterwards, so the user barely sees anything.
    """
    p0 = pointer_pos()
    if p0 is None:
        # No position feedback at all: absolute warping is the only
        # mechanism that does not need to know where the cursor is.
        _STATE["abs_works"] = True
        _STATE["verified"] = False
        return

    w, _h = _screen_size()
    target_x = min(p0[0] + 60, w - 1)
    try:
        dev.abs(ABS_X, target_x)
        dev.abs(ABS_Y, p0[1])
        dev.syn()
        time.sleep(0.15)
        p1 = pointer_pos()
        if p1 is not None and abs(p1[0] - target_x) <= 4 and abs(p1[1] - p0[1]) <= 4:
            dev.abs(ABS_X, p0[0])
            dev.abs(ABS_Y, p0[1])
            dev.syn()
            time.sleep(0.1)
            _STATE["abs_works"] = True
            _STATE["verified"] = True
            return
    except Exception:
        pass

    try:
        dev.rel(REL_X, 60)
        dev.syn()
        time.sleep(0.15)
        p2 = pointer_pos()
        if p2 is not None and abs(p2[0] - (p0[0] + 60)) <= 4:
            dev.rel(REL_X, -60)
            dev.syn()
            time.sleep(0.1)
            _STATE["abs_works"] = False
            _STATE["verified"] = True
            return
    except Exception:
        pass

    # Neither mechanism confirmed (pointer reads on this session don't
    # respond). Fall back to absolute warping, which needs no feedback.
    _STATE["abs_works"] = True
    _STATE["verified"] = False


def _warp(dev: _KernelDevice, x: int, y: int) -> None:
    w, h = _screen_size()
    x = max(0, min(int(x), w - 1))
    y = max(0, min(int(y), h - 1))
    if _STATE["abs_works"] is not False:
        dev.abs(ABS_X, x)
        dev.abs(ABS_Y, y)
        dev.syn()
        return
    pos = pointer_pos() or (0, 0)
    dx, dy = x - pos[0], y - pos[1]
    while dx or dy:
        sx = max(-400, min(400, dx))
        sy = max(-400, min(400, dy))
        dev.rel(REL_X, sx)
        dev.rel(REL_Y, sy)
        dev.syn()
        dx -= sx
        dy -= sy
        time.sleep(0.01)


# --------------------------------------------------------------------------
# readiness / backend choice
# --------------------------------------------------------------------------
def _ensure_ready() -> bool:
    ready = _STATE["ready"]
    if ready is True:
        return True
    if ready is False and time.time() < _STATE["retry_at"]:
        return False

    if not is_wayland() or not uinput_writable():
        _STATE["ready"] = False
        _STATE["retry_at"] = time.time() + 30
        _STATE["error"] = ("/dev/uinput is not writable (run setup_uinput.sh)"
                           if is_wayland() else "X11 session (pyautogui by design)")
        return False
    try:
        _keyboard()   # throws if the kernel rejects the device
        _mouse()
        _STATE["ready"] = True
        _STATE["error"] = None
        return True
    except Exception as exc:  # permission, kernel, udev ...
        _STATE["ready"] = False
        _STATE["retry_at"] = time.time() + 30
        _STATE["error"] = str(exc)
        return False


def active() -> bool:
    """True when calls must be injected through uinput."""
    if not is_wayland():
        return False   # X11 keeps pyautogui, always
    return _ensure_ready()


def status() -> str:
    if not is_wayland():
        return "input backend: pyautogui (X11 session)"
    if active():
        verified = _STATE["verified"]
        extra = "" if verified else " (pointer position not verifiable)"
        return f"input backend: uinput (full Wayland control){extra}"
    reason = _STATE["error"] or "uinput unavailable"
    return f"input backend: pyautogui/X11-only — {reason}. {SETUP_HINT}"


# --------------------------------------------------------------------------
# injection (uinput)
# --------------------------------------------------------------------------
def _press(dev: _KernelDevice, code: int) -> None:
    dev.key(code, True)
    dev.syn()
    time.sleep(0.01)
    dev.key(code, False)
    dev.syn()


def _type_uinput(dev: _KernelDevice, text: str, interval: float) -> None:
    shift = 42
    shift_down = False
    for ch in text:
        entry = _CHAR_MAP.get(ch)
        if entry is None:
            continue
        code, needs_shift = entry
        if needs_shift and not shift_down:
            dev.key(shift, True)
            dev.syn()
            shift_down = True
        if not needs_shift and shift_down:
            dev.key(shift, False)
            dev.syn()
            shift_down = False
        dev.key(code, True)
        dev.syn()
        dev.key(code, False)
        dev.syn()
        if interval:
            time.sleep(interval)
    if shift_down:
        dev.key(shift, False)
        dev.syn()


def _hotkey_uinput(dev: _KernelDevice, codes: list[int]) -> None:
    for code in codes:
        dev.key(code, True)
        dev.syn()
    time.sleep(0.02)
    for code in reversed(codes):
        dev.key(code, False)
        dev.syn()


def resolve_key(name: str) -> int | None:
    """Key name (pyautogui-style) -> Linux keycode, or None."""
    if not name:
        return None
    key = str(name).strip().lower()
    if key in _KEYS_BY_NAME:
        return _KEYS_BY_NAME[key]
    if len(key) == 1:
        if key in _CHAR_MAP:
            return _CHAR_MAP[key][0]
        if key.upper() in _KEYS_BY_NAME:
            return _KEYS_BY_NAME[key.upper()]
    return None


def resolve_keys(keys) -> list[int]:
    codes = []
    for name in keys:
        code = resolve_key(name)
        if code is None:
            raise RuntimeError(f"unknown key: {name!r}")
        codes.append(code)
    return codes


def _buttons(button: str) -> int:
    return {"left": BTN_LEFT, "right": BTN_RIGHT,
            "middle": BTN_MIDDLE}.get(str(button).lower(), BTN_LEFT)


def _click_uinput(dev: _KernelDevice, x, y, button: str, clicks: int) -> None:
    if x is not None and y is not None:
        _warp(dev, x, y)
        time.sleep(0.05)
    btn = _buttons(button)
    for _ in range(max(1, int(clicks))):
        dev.key(btn, True)
        dev.syn()
        time.sleep(0.03)
        dev.key(btn, False)
        dev.syn()
        time.sleep(0.03)


def _move_uinput(dev: _KernelDevice, x: int, y: int, duration: float) -> None:
    duration = max(0.0, float(duration))
    if duration <= 0.01:
        _warp(dev, x, y)
        return
    start = pointer_pos() or (x, y)
    steps = max(1, int(duration / 0.03))
    for i in range(1, steps + 1):
        _warp(dev, start[0] + (x - start[0]) * i // steps,
              start[1] + (y - start[1]) * i // steps)
        time.sleep(duration / steps)


def _drag_uinput(dev: _KernelDevice, x1, y1, x2, y2, duration: float) -> None:
    _warp(dev, x1, y1)
    time.sleep(0.1)
    btn = BTN_LEFT
    dev.key(btn, True)
    dev.syn()
    time.sleep(0.05)
    _move_uinput(dev, x2, y2, duration)
    time.sleep(0.05)
    dev.key(btn, False)
    dev.syn()


def _scroll_uinput(dev: _KernelDevice, vertical: bool, clicks: int) -> None:
    dev.rel(REL_WHEEL if vertical else REL_HWHEEL, int(clicks))
    dev.syn()


# --------------------------------------------------------------------------
# public API -- action only; message formatting stays with the caller
# --------------------------------------------------------------------------
def type_text(text: str, interval: float = 0.03) -> None:
    if active():
        _type_uinput(_keyboard(), text, interval)
        return
    pg = require_pyautogui()
    pg.typewrite(text, interval=interval)


def hotkey(*keys) -> None:
    if active():
        _hotkey_uinput(_keyboard(), resolve_keys(keys))
        return
    pg = require_pyautogui()
    pg.hotkey(*keys)


def press(key: str) -> None:
    if active():
        code = resolve_key(key)
        if code is None:
            raise RuntimeError(f"unknown key: {key!r}")
        _press(_keyboard(), code)
        return
    pg = require_pyautogui()
    pg.press(key)


def click(x=None, y=None, button: str = "left", clicks: int = 1) -> None:
    if active():
        _click_uinput(_mouse(), x, y, button, clicks)
        return
    pg = require_pyautogui()
    if x is not None and y is not None:
        pg.click(x, y, button=button, clicks=clicks)
    else:
        pg.click(button=button, clicks=clicks)


def move(x: int, y: int, duration: float = 0.3) -> None:
    if active():
        _move_uinput(_mouse(), int(x), int(y), duration)
        return
    pg = require_pyautogui()
    pg.moveTo(int(x), int(y), duration=duration)


def drag(x1: int, y1: int, x2: int, y2: int, duration: float = 0.5) -> None:
    if active():
        dev = _mouse()
        _warp(dev, x1, y1)
        time.sleep(0.1)
        dev.key(BTN_LEFT, True)
        dev.syn()
        _move_uinput(dev, x2, y2, duration)
        dev.key(BTN_LEFT, False)
        dev.syn()
        return
    pg = require_pyautogui()
    pg.moveTo(int(x1), int(y1), duration=0.2)
    pg.dragTo(int(x2), int(y2), duration=duration, button="left")


def scroll(vertical: bool, clicks: int) -> None:
    if active():
        _scroll_uinput(_mouse(), vertical, clicks)
        return
    pg = require_pyautogui()
    if vertical:
        pg.scroll(clicks)
    else:
        pg.hscroll(clicks)


if __name__ == "__main__":
    print(status())
