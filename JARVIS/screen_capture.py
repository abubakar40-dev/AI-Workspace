# screen_capture.py
#
# Local screen capture for JARVIS -- X11 *and* Wayland.
#
# Honest status of every method, measured live on this machine
# (GNOME 50 / Wayland, 1366x768, scale 1.0):
#
#   method                       result on this machine
#   ---------------------------  -------------------------------------------
#   XDG portal, silent           WORKS -- fast path (sub-second), the portal
#                                writes the PNG into ~/Pictures
#   XDG portal, interactive      WORKS -- opens the GNOME capture UI and
#                                auto-confirms it by injecting Enter through
#                                uinput (desktop_input); with
#                                JARVIS_SCREENSHOT_MANUAL=1 a human clicks
#                                the capture button instead
#   grim                         fails on GNOME (no wlr-screencopy protocol)
#   gnome-screenshot             denies or hangs -- always subprocess-bounded
#   scrot / mss / X11 grab       100% BLACK frame on Wayland: XWayland
#                                cannot read the compositor's desktop, so
#                                those frames are rejected as blank and are
#                                never reported as success
#   macOS screencapture /        used when running on those platforms
#   Windows ImageGrab
#
# Chain (first real, non-blank frame wins):
#
#   portal silent -> portal interactive (auto-Enter / manual) -> grim ->
#   gnome-screenshot -> X11 grab (X11 sessions only; always rejected on
#   Wayland) -> native macOS/Windows tool.
#
# If the portal stops answering (it can wedge after a crash), the user
# service is restarted once (systemctl --user restart xdg-desktop-portal)
# and the call retried once.
#
# capture() returns ``(ok, detail)`` and never raises for expected
# failures -- the caller formats the user-facing message.
#
# All screenshots are saved locally. No cloud upload.

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

import desktop_input  # noqa: E402
import wayland_native as _wn  # noqa: E402
from x11_access import require_pyautogui  # noqa: E402,F401 (compat import)

_CLIENT = Path(__file__).resolve().with_name("portal_shot_client.py")

# Auto-confirm choreography for the GNOME capture UI: let it appear, then
# press Enter a few times, stopping as soon as the client exits.
_SETTLE = 1.0        # seconds to wait before the first Enter
_PRESS_EVERY = 1.4   # seconds between Enter presses
_MAX_PRESS = 3       # never press more than three times

_STATE = {"py": None, "last": None}  # py: None=untested, ""=none, else path


def reset() -> None:
    """Forget cached decisions (tests)."""
    _STATE["py"] = None
    _STATE["last"] = None


def _is_wayland() -> bool:
    return desktop_input.is_wayland()


# ─── Public API ──────────────────────────────────────────────────

def capture(dest: str | Path | None = None, timeout: float = 20.0) -> tuple[bool, str]:
    """Capture the whole screen into *dest*; returns ``(ok, detail)``.

    *dest* defaults to ``~/Pictures/screenshot_<timestamp>.png``.
    *timeout* bounds each portal attempt.  Never raises for expected
    failures; a uniform (blank) frame is never counted as success.
    """
    target = Path(dest).expanduser() if dest else _default_dest()
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        ok, detail = _chain(target, float(timeout))
    except Exception as exc:  # a screenshot action must never blow up
        ok, detail = False, f"screenshot failed: {exc}"
    _STATE["last"] = detail
    return (ok, detail)


def grab() -> Optional[bytes]:
    """Capture the screen and return the PNG bytes (None on failure)."""
    tmp = Path(tempfile.mktemp(suffix=".png"))
    try:
        ok, _detail = capture(tmp, timeout=15.0)
        if not ok:
            return None
        return tmp.read_bytes()
    except Exception:
        return None
    finally:
        try:
            tmp.unlink()
        except OSError:
            pass


def capture_region(x: int, y: int, w: int, h: int,
                   dest: str | Path | None = None) -> tuple[bool, str]:
    """Capture a screen region; returns ``(ok, detail)``.

    The portal has no region mode, so a full frame is grabbed through the
    chain and then cropped locally (no cloud, no extra permissions).
    """
    if w <= 0 or h <= 0:
        return (False, f"Region capture failed: bad size {w}x{h}")
    tmp = Path(tempfile.mktemp(suffix=".png"))
    try:
        ok, detail = capture(tmp, timeout=20.0)
        if not ok:
            return (False, f"Region capture failed: {detail}")
        from PIL import Image
        with Image.open(tmp) as img:
            W, H = img.size
            x0, y0 = max(0, min(int(x), W - 1)), max(0, min(int(y), H - 1))
            x1 = max(x0 + 1, min(int(x) + int(w), W))
            y1 = max(y0 + 1, min(int(y) + int(h), H))
            region = img.crop((x0, y0, x1, y1))
            target = Path(dest).expanduser() if dest else _default_dest()
            target.parent.mkdir(parents=True, exist_ok=True)
            region.save(target, "PNG")
        return (True, f"Region captured: {x1 - x0}x{y1 - y0} at ({x0},{y0})")
    except Exception as exc:
        return (False, f"Region capture failed: {exc}")
    finally:
        try:
            tmp.unlink()
        except OSError:
            pass


def status() -> dict:
    """What is available here, and what happened last."""
    return {
        "wayland": _is_wayland(),
        "wayland_screenshot_available": _wn.is_wayland_screenshot_available(),
        "scrot_available": _is_scrot_available(),
        "grim_available": _is_grim_available(),
        "resolution": _wn.get_screen_resolution(),
        "portal_python": _get_py_path(),
        "desktop_input_active": desktop_input.active(),
        "state": dict(_STATE),
        "last": _STATE["last"],
    }


# ─── The chain ───────────────────────────────────────────────────

def _chain(target: Path, timeout: float) -> tuple[bool, str]:
    """Walk the capture chain; first real (non-blank) frame wins."""
    reasons: list[str] = []

    def win(detail: str) -> tuple[bool, str]:
        return (True, f"Screenshot saved: {target} ({detail})")

    if not sys.platform.startswith("linux"):
        reason = _capture_native(target)
        if reason is None:
            return win("native")
        return (False, reason)

    # 1) portal, silent -- no UI at all, the fast path
    res = run_portal(False, timeout=min(timeout, 12))
    reason = _adopt(res, target)
    if reason is None:
        return win(res.get("method", "portal-silent"))
    reasons.append(reason)

    # 2) portal, interactive -- GNOME capture UI, auto-confirmed with Enter
    #    over uinput; JARVIS_SCREENSHOT_MANUAL=1 = a human confirms instead.
    manual = os.environ.get("JARVIS_SCREENSHOT_MANUAL") == "1"
    if desktop_input.active() or manual:
        res = run_portal(True, timeout=timeout, auto_confirm=not manual)
        reason = _adopt(res, target)
        if reason is None:
            return win(res.get("method", "portal-interactive"))
        reasons.append(reason)
    else:
        reasons.append("interactive portal: skipped (no input backend; set "
                       "JARVIS_SCREENSHOT_MANUAL=1 to confirm by hand)")

    # 3) on X11 the grab is native and instant -- try it before the CLI tools
    if not _is_wayland():
        reason = _try_x11(target)
        if reason is None:
            return win("X11 grab")
        reasons.append(reason)
    else:
        reasons.append("X11 grab: rejected on Wayland (XWayland reads black)")

    # 4) grim -- wlroots compositors only (GNOME has no wlr-screencopy)
    if shutil.which("grim"):
        reason = _run_to_file(["grim", str(target)], 10, target)
        if reason is None:
            return win("grim")
        reasons.append(reason)
    else:
        reasons.append("grim: not installed")

    # 5) gnome-screenshot -- often hangs; bounded
    if shutil.which("gnome-screenshot"):
        reason = _run_to_file(["gnome-screenshot", "-f", str(target)], 8, target)
        if reason is None:
            return win("gnome-screenshot")
        reasons.append(reason)
    else:
        reasons.append("gnome-screenshot: not installed")

    return (False, "; ".join(reasons))


def _capture_native(target: Path) -> Optional[str]:
    """macOS/Windows built-ins. None = a real frame is at *target*."""
    try:
        if sys.platform == "darwin":
            reason = _run_to_file(["screencapture", "-x", str(target)], 10, target)
        elif sys.platform.startswith("win"):
            from PIL import ImageGrab
            ImageGrab.grab().save(target, "PNG")
            reason = "blank frame rejected" if _is_blank(target) else None
            if reason:
                _clean(target)
        else:
            reason = f"unsupported platform: {sys.platform}"
    except Exception as exc:
        reason = str(exc)
    if reason:
        _clean(target)
    return reason


def _try_x11(target: Path) -> Optional[str]:
    """PIL X11 grab, thread-bounded (an XWayland grab can block forever).

    None = a real frame is at *target*.
    """
    box: dict[str, str] = {}

    def worker() -> None:
        try:
            from PIL import ImageGrab
            ImageGrab.grab(xdisplay=os.environ.get("DISPLAY") or None).save(
                target, "PNG")
        except Exception as exc:
            box["error"] = str(exc)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(3.0)
    if thread.is_alive():
        return "X11 grab: hung"
    if "error" in box:
        return f"X11 grab: {box['error']}"
    if not target.exists():
        return "X11 grab: no output"
    if _is_blank(target):
        _clean(target)
        return "X11 grab: black frame rejected"
    return None


def _run_to_file(cmd: list[str], timeout: float, target: Path) -> Optional[str]:
    """Run an external capturer. None = a real frame is at *target*."""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout)
    except subprocess.TimeoutExpired:
        _clean(target)
        return f"{cmd[0]}: timed out after {timeout:.0f}s"
    except Exception as exc:
        _clean(target)
        return f"{cmd[0]}: {exc}"
    if proc.returncode != 0:
        _clean(target)
        lines = (proc.stderr or proc.stdout or "").strip().splitlines()
        return f"{cmd[0]}: {lines[-1] if lines else f'exit {proc.returncode}'}"
    if not target.exists():
        return f"{cmd[0]}: no output file"
    if _is_blank(target):
        _clean(target)
        return f"{cmd[0]}: blank frame rejected"
    return None


# ─── The XDG portal ──────────────────────────────────────────────

def run_portal(interactive: bool = False, timeout: int = 10,
               auto_confirm: bool = True, heal: bool = True) -> dict:
    """One XDG Screenshot portal attempt -> ``{"ok", "method", "uri", "detail"}``.

    *interactive=False* is the fast path (no UI).  *interactive=True* opens
    the GNOME capture UI; with *auto_confirm* and a live uinput backend,
    Enter is injected to press its capture button automatically.  A wedged
    portal is restarted once and the call retried once when *heal*.
    """
    method = "portal-interactive" if interactive else "portal-silent"
    py = _get_py_path()
    if not py:
        return {"ok": False, "method": method, "uri": None,
                "detail": f"{method}: no Python with PyGObject found"}
    cmd = [py, str(_CLIENT)]
    if interactive:
        cmd.append("--interactive")
    cmd += ["--timeout", str(max(1, int(timeout)))]
    confirm = bool(interactive and auto_confirm and desktop_input.active())
    hard = float(timeout) + 8.0

    _rc, out, err = _run_client(cmd, hard, confirm)
    res = _parse_client(out, err)

    if not res["ok"] and heal and _looks_wedged(res["error"] or ""):
        if _restart_portal():
            _rc, out, err = _run_client(cmd, hard, confirm)
            res = _parse_client(out, err)
            if not res["ok"]:
                res["error"] = (res["error"] or "portal failed") + \
                    " (still failing after portal restart)"

    if res["ok"] and res["uri"]:
        return {"ok": True, "method": method, "uri": res["uri"],
                "detail": f"{method}: captured"}
    reason = res["error"] or f"{method}: portal response code {res['code']}"
    return {"ok": False, "method": method, "uri": None,
            "detail": f"{method}: {reason}"}


def _run_client(cmd: list[str], hard_timeout: float,
                auto_confirm: bool) -> tuple[Optional[int], str, str]:
    """Run the portal client process; never hangs the caller.

    With *auto_confirm*, Enter is pressed while it runs (see choreography
    constants) until the client exits or *hard_timeout* elapses.
    Returns ``(returncode, stdout, stderr)``; returncode None = killed.
    """
    if not auto_confirm:
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=hard_timeout)
            return proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired:
            return None, "", "portal client hung (timed out)"
        except Exception as exc:
            return None, "", str(exc)

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True)
    except Exception as exc:
        return None, "", str(exc)

    deadline = time.monotonic() + hard_timeout
    presses, next_press = 0, time.monotonic() + _SETTLE
    while proc.poll() is None and time.monotonic() < deadline:
        if presses < _MAX_PRESS and time.monotonic() >= next_press:
            try:
                desktop_input.press("enter")
            except Exception:
                pass
            presses += 1
            next_press = time.monotonic() + _PRESS_EVERY
        time.sleep(0.15)

    try:
        if proc.poll() is None:
            proc.kill()
            out, err = proc.communicate(timeout=5)
            return None, out, (err or "portal client hung (killed)")
        out, err = proc.communicate(timeout=5)
        return proc.returncode, out, err
    except Exception as exc:
        return None, "", str(exc)


def _parse_client(out: str, err: str) -> dict:
    """Last JSON line of the portal client -> {"ok", "code", "uri", "error"}."""
    payload = None
    for line in reversed((out or "").strip().splitlines()):
        try:
            candidate = json.loads(line)
        except Exception:
            continue
        if isinstance(candidate, dict) and "ok" in candidate:
            payload = candidate
            break
    if payload is None:
        lines = (err or out or "portal client produced no output").strip().splitlines()
        return {"ok": False, "code": None, "uri": None,
                "error": lines[-1] if lines else "portal client produced no output"}
    return {"ok": bool(payload.get("ok")), "code": payload.get("code"),
            "uri": payload.get("uri"), "error": payload.get("error")}


def _adopt(res: dict, target: Path) -> Optional[str]:
    """Pull a portal URI into *target*.  None = real capture, str = reason."""
    if not res.get("ok") or not res.get("uri"):
        return res.get("detail") or "portal failed"
    reason = _copy_uri(res["uri"], target)
    if reason:
        return f"{res.get('method', 'portal')}: {reason}"
    if _is_blank(target):
        _clean(target)
        return f"{res.get('method', 'portal')}: blank frame rejected"
    return None


def _restart_portal() -> bool:
    """Kick a wedged xdg-desktop-portal back to life (per-user service)."""
    try:
        proc = subprocess.run(
            ["systemctl", "--user", "restart", "xdg-desktop-portal.service"],
            capture_output=True, timeout=20,
        )
        if proc.returncode == 0:
            time.sleep(1.0)
            return True
    except Exception:
        pass
    return False


def _get_py_path() -> Optional[str]:
    """Python interpreter that has PyGObject (the project venv does not)."""
    if _STATE["py"] is not None:
        return _STATE["py"] or None
    for cand in (sys.executable, "/usr/bin/python3", "/usr/bin/python", "python3"):
        try:
            probe = subprocess.run(
                [cand, "-c", "import gi; gi.require_version('Gio', '2.0')"],
                capture_output=True, timeout=8,
            )
            if probe.returncode == 0:
                _STATE["py"] = cand
                return cand
        except Exception:
            continue
    _STATE["py"] = ""
    return None


# ─── Helpers ─────────────────────────────────────────────────────

def _looks_wedged(error: str) -> bool:
    """Is this the signature of a portal that stopped answering?"""
    text = (error or "").lower()
    return any(p in text for p in (
        "portal client hung",
        "portal did not answer",
        "did not answer",
        "timed out",
        "hang",
    ))


def _copy_uri(uri: str, dest: Path) -> Optional[str]:
    """Move the portal's output file to *dest*.  None = success, str = reason."""
    try:
        from urllib.parse import unquote, urlparse
        src = Path(unquote(urlparse(uri).path))
        if not src.exists():
            return f"Source not found: {src}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src != dest:
            try:
                src.replace(dest)          # same filesystem: instant move
            except OSError:
                shutil.copy2(src, dest)    # cross-device fallback
                try:
                    src.unlink()
                except OSError:
                    pass
        return None
    except Exception as exc:
        return str(exc)


def _is_blank(path: Path) -> bool:
    """True when the image is uniform -- the XWayland-black signature.

    A real desktop frame carries thousands of colours; scrot/mss/X11 grabs
    on Wayland come back as one flat colour and are rejected here.
    """
    try:
        from PIL import Image
        with Image.open(path) as img:
            if img.size[0] < 4 or img.size[1] < 4:
                return True
            colors = img.convert("RGB").getcolors(maxcolors=64)
        return colors is not None and len(colors) <= 3
    except Exception:
        return True  # unreadable = unusable


def _clean(path: Path) -> None:
    """Drop a file this module just created for a failed attempt."""
    try:
        path.unlink()
    except OSError:
        pass


def _default_dest() -> Path:
    stamp = time.strftime("%Y%m%d_%H%M%S")
    directory = Path.home() / "Pictures"
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError:
        directory = Path(tempfile.gettempdir())
    return directory / f"screenshot_{stamp}.png"


# ─── Availability helpers (kept for compatibility) ───────────────

def _is_scrot_available() -> bool:
    return shutil.which("scrot") is not None


def _is_grim_available() -> bool:
    return shutil.which("grim") is not None


def _is_x11_available() -> bool:
    try:
        import mss  # noqa: F401
        return True
    except ImportError:
        return False
