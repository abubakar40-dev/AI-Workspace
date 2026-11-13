"""Tests for actions/computer_control.py — Task 4 wiring.

Two contracts are locked down here:

1. **Nothing user-visible changed.** Every action still returns the exact
   message it returned before the Wayland work (``Screenshot saved: …``,
   ``Clicked (10, 20) [left]``, ``Hotkey: ctrl+c``, …), the dispatcher still
   formats failures as ``computer_control '<action>' failed: …``, and
   screenshot paths are still confined to the home directory.
2. **The new backends are actually wired in.** Input actions must go
   through ``desktop_input`` (uinput on Wayland, pyautogui passthrough on
   X11) and ``screenshot`` must go through the ``screen_capture`` chain —
   never straight to ``pyautogui.screenshot()``, which hangs forever on
   this machine.

Injection is faked at the ``desktop_input`` boundary, so no real mouse,
keyboard, or display is touched.
"""

import pytest

import desktop_input
import screen_capture
from actions import computer_control as cc


@pytest.fixture(autouse=True)
def no_real_input(monkeypatch):
    """Record every injection instead of performing it, and never sleep."""
    calls = []

    def record(name):
        def fn(*args, **kwargs):
            calls.append((name, args, kwargs))
        return fn

    for name in ("type_text", "hotkey", "press", "click", "move",
                 "drag", "scroll"):
        monkeypatch.setattr(desktop_input, name, record(name))
    # active()==True keeps _require_input() off the pyautogui path
    monkeypatch.setattr(desktop_input, "active", lambda: True)
    monkeypatch.setattr(cc.time, "sleep", lambda s: None)
    yield calls


def inj(calls, name):
    """All recorded calls to one backend function."""
    return [c for c in calls if c[0] == name]


# --------------------------------------------------------------------------
# input actions route through desktop_input and keep their messages
# --------------------------------------------------------------------------
def test_type_routes_through_backend_and_keeps_message(no_real_input):
    assert cc._type("hello") == "Typed: hello"
    assert inj(no_real_input, "type_text") == [("type_text", ("hello", 0.03), {})]


def test_type_truncates_long_text_like_before(no_real_input):
    msg = cc._type("x" * 100)
    assert msg.startswith("Typed: " + "x" * 60) and msg.endswith("…")


def test_smart_type_uses_backend_for_paste_and_type(no_real_input):
    msg = cc._smart_type("short", clear_first=False)
    assert msg == "Smart-typed: short"
    assert inj(no_real_input, "type_text")
    assert not inj(no_real_input, "hotkey")     # short text skips clipboard


def test_click_messages_are_byte_identical(no_real_input):
    assert cc._click(10, 20) == "Clicked (10, 20) [left]"
    assert cc._click(10, 20, "left", 2) == "Double-clicked (10, 20) [left]"
    assert cc._click(3, 4, "right") == "Clicked (3, 4) [right]"
    assert cc._click() == "Clicked at current position [left]"
    assert inj(no_real_input, "click")[0][1] == (10, 20, "left", 1)
    assert inj(no_real_input, "click")[-1][1] == (None, None, "left", 1)


def test_hotkey_press_messages_kept(no_real_input):
    assert cc._hotkey("ctrl", "c") == "Hotkey: ctrl+c"
    assert cc._press("enter") == "Pressed: enter"
    assert inj(no_real_input, "hotkey")[0][1] == ("ctrl", "c")
    assert inj(no_real_input, "press")[0][1] == ("enter",)


def test_scroll_direction_polarity_preserved(no_real_input):
    assert cc._scroll("up", 5) == "Scrolled up ×5"
    assert cc._scroll("down", 3) == "Scrolled down ×3"
    # vertical flag + signed clicks must match the old pyautogui logic
    assert inj(no_real_input, "scroll") == [
        ("scroll", (True, 5), {}),
        ("scroll", (True, -3), {}),
    ]


def test_move_and_drag_messages_kept(no_real_input):
    assert cc._move(5, 6) == "Mouse → (5, 6)"
    assert cc._drag(1, 2, 3, 4) == "Dragged (1,2) → (3,4)"
    assert inj(no_real_input, "move")[0][1] == (5, 6, 0.3)
    assert inj(no_real_input, "drag")[0][1] == (1, 2, 3, 4, 0.5)


def test_clear_field_keeps_message_and_uses_backend(no_real_input):
    assert cc._clear_field() == "Field cleared"
    assert inj(no_real_input, "hotkey")[0][1] == ("ctrl", "a")
    assert inj(no_real_input, "press")[0][1] == ("delete",)


# --------------------------------------------------------------------------
# pyautogui is still required exactly when uinput is NOT available
# --------------------------------------------------------------------------
def test_pyautogui_required_only_without_uinput(monkeypatch, no_real_input):
    required = []
    monkeypatch.setattr(cc, "_require_pyautogui",
                        lambda: required.append(1))
    monkeypatch.setattr(desktop_input, "active", lambda: True)
    cc._type("hi")
    assert required == []                 # uinput path needs no X11

    monkeypatch.setattr(desktop_input, "active", lambda: False)
    cc._press("enter")
    assert required == [1]                # X11/fallback still checks pyautogui


def test_backend_error_is_reported_through_the_dispatcher(monkeypatch):
    def explode(*a, **k):
        raise RuntimeError("uinput device went away")

    monkeypatch.setattr(desktop_input, "click", explode)
    monkeypatch.setattr(desktop_input, "active", lambda: True)
    monkeypatch.setattr(cc.time, "sleep", lambda s: None)

    out = cc.computer_control({"action": "click", "x": 1, "y": 2})
    assert out == "computer_control 'click' failed: uinput device went away"


# --------------------------------------------------------------------------
# screenshot goes through the capture chain, not pyautogui
# --------------------------------------------------------------------------
def test_screenshot_success_message_uses_chain(monkeypatch, tmp_path):
    dest = tmp_path / "shot.png"
    monkeypatch.setattr(cc, "_safe_screenshot_path", lambda p=None: dest)
    seen = {}

    def fake_capture(path, timeout=20.0):
        seen["path"] = path
        return True, "portal+confirm"

    monkeypatch.setattr(screen_capture, "capture", fake_capture)
    msg = cc._screenshot()
    assert msg == f"Screenshot saved: {dest}"
    assert seen["path"] == str(dest)


def test_screenshot_failure_is_honest(monkeypatch, tmp_path):
    dest = tmp_path / "shot.png"
    monkeypatch.setattr(cc, "_safe_screenshot_path", lambda p=None: dest)
    monkeypatch.setattr(screen_capture, "capture",
                        lambda path, timeout=20.0: (False, "grim: no protocol"))
    msg = cc._screenshot()
    assert msg == "Screenshot failed: grim: no protocol"
    assert not dest.exists()               # nothing was captured


def test_screenshot_still_confined_to_home_dir(tmp_path):
    outside = tmp_path / "elsewhere.png"
    got = cc._safe_screenshot_path(str(outside))
    assert str(got).startswith(str(cc.Path.home()))
    assert got.name == "elsewhere.png"     # filename kept, location replaced


def test_screenshot_default_path_pattern_unchanged():
    got = cc._safe_screenshot_path(None)
    assert got.parent == cc.Path.home() / "Desktop"
    assert got.name.startswith("screenshot_") and got.name.endswith(".png")


def test_dispatch_screenshot_action_uses_chain(monkeypatch, tmp_path):
    dest = tmp_path / "d.png"
    monkeypatch.setattr(cc, "_safe_screenshot_path", lambda p=None: dest)
    monkeypatch.setattr(screen_capture, "capture",
                        lambda path, timeout=20.0: (True, "grim"))
    out = cc.computer_control({"action": "screenshot"})
    assert out == f"Screenshot saved: {dest}"


def test_dispatch_unknown_action_message_unchanged():
    assert cc.computer_control({"action": "teleport"}) == \
        "Unknown action: 'teleport'"
    assert cc.computer_control({}) == \
        "No action specified for computer_control."
