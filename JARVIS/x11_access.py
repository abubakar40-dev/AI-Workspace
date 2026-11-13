# x11_access.py
#
# Permanent fix for the recurring "Can't connect to display :0:
# Authorization required, but no authorization protocol specified" error
# that broke pyautogui-based tools (computer_control, computer_settings,
# desktop) over and over across sessions.
#
# Root cause: pyautogui's mouseinfo dependency connects to X11 via
# python-xlib the moment it's imported. That connection needs X11
# authorization (an xhost grant), which the user was previously expected
# to set up themselves via `xhost +local:$USER` before every session --
# fragile, easy to forget, and apparently didn't reliably survive across
# terminals/sessions even when added to .bashrc.
#
# Permanent fix: Jarvis grants its own X11 access itself, in Python, at
# startup and before any pyautogui-dependent import -- no dependency on
# shell config timing at all. This module is the single shared place that
# does this; every action module that needs pyautogui imports
# `ensure_pyautogui()` from here instead of duplicating import-guard logic.

import os
import subprocess
import shutil

_pyautogui_module = None
_pyautogui_error: str | None = None
_x11_grant_attempted = False


def _grant_x11_access() -> None:
    """Runs `xhost +local:$USER` ourselves via subprocess, so X11 access
    is granted before pyautogui ever tries to connect -- regardless of
    whether the user's shell config did this already. Safe to call
    multiple times; xhost grants are idempotent. No-ops quietly if xhost
    isn't installed or there's no X server at all (e.g. a pure headless
    box), since pyautogui will simply stay unavailable in that case
    anyway and callers already handle that gracefully.
    """
    if not shutil.which("xhost"):
        return
    if not os.environ.get("DISPLAY"):
        return
    try:
        subprocess.run(
            ["xhost", f"+local:{os.environ.get('USER', '')}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3,
        )
    except Exception:
        pass  # best-effort -- pyautogui's own import will surface any real problem


def ensure_pyautogui():
    """Returns the pyautogui module if available, or None. Grants X11
    access first (idempotent, cheap), then imports/re-imports pyautogui.
    Safe to call repeatedly -- once successful, the result is cached; if
    it previously failed, each call retries (X11 auth can be fixed
    mid-session, e.g. by running xhost manually in another terminal, and
    this makes sure Jarvis notices without needing a restart)."""
    global _pyautogui_module, _pyautogui_error, _x11_grant_attempted

    if _pyautogui_module is not None:
        return _pyautogui_module

    if not _x11_grant_attempted:
        _grant_x11_access()
        _x11_grant_attempted = True

    try:
        import pyautogui as _pg
        _pg.FAILSAFE = True
        _pg.PAUSE = 0.05
        _pyautogui_module = _pg
        _pyautogui_error = None
        return _pyautogui_module
    except Exception as e:
        _pyautogui_error = str(e)
        # Re-attempt the X11 grant on the next call too, in case the
        # display wasn't ready the first time (e.g. very early in startup).
        _x11_grant_attempted = False
        return None


def pyautogui_error() -> str | None:
    """Human-readable reason pyautogui is unavailable, or None if it's
    working. Call ensure_pyautogui() first to get an up-to-date reason."""
    return _pyautogui_error


def require_pyautogui():
    """Returns the pyautogui module or raises RuntimeError with a clear
    explanation -- for call sites that want to fail loudly rather than
    check availability themselves."""
    pg = ensure_pyautogui()
    if pg is None:
        raise RuntimeError(
            f"PyAutoGUI unavailable"
            f"{f': {_pyautogui_error}' if _pyautogui_error else ''}. "
            f"Jarvis already tries to grant X11 access automatically (xhost) "
            f"at every attempt -- if this persists, there may be no X server "
            f"running, or you're on a display Jarvis can't reach."
        )
    return pg


if __name__ == "__main__":
    pg = ensure_pyautogui()
    if pg:
        print("pyautogui available:", pg.size())
    else:
        print("pyautogui NOT available:", pyautogui_error())
