"""Tests for desktop_input.py — Wayland/X11 input injection backend.

Three layers are covered:

1. **Key maps** — every name/character resolves to the right Linux input
   keycode (verified against the kernel's evdev table), and shift handling
   for uppercase/symbols is correct.
2. **Event streams** — with a recording sink we assert the exact sequence
   of key/syn events for typing, hotkeys and clicks, so the uinput path is
   provable without /dev/uinput access.
3. **Backend selection** — X11 must always stay on pyautogui (nothing that
   works today may change), Wayland falls back to pyautogui when uinput is
   not set up, and only Wayland + writable uinput activates injection.

Plus the mouse calibration logic (absolute vs relative) that decides how
the cursor gets moved at runtime.
"""

import struct

import pytest

import desktop_input as di


class Sink:
    """Records injected events instead of writing them to the kernel."""

    def __init__(self):
        self.events = []
        self.closed = False

    def key(self, code, down):
        self.events.append(("key", code, bool(down)))

    def rel(self, axis, value):
        self.events.append(("rel", axis, value))

    def abs(self, axis, value):
        self.events.append(("abs", axis, value))

    def syn(self):
        self.events.append(("syn",))

    def close(self):
        self.closed = True


@pytest.fixture(autouse=True)
def _fresh_state():
    di.reset()
    yield
    di.reset()


# --------------------------------------------------------------------------
# kernel protocol constants
# --------------------------------------------------------------------------
def test_uinput_struct_sizes_match_kernel_abi():
    # struct uinput_user_dev: name[80] + input_id{4xu16} + ff(u32) + 4x64 s32
    assert struct.calcsize(di.UINPUT_USER_DEV_FMT) == 1116
    # struct input_event: timeval{2x long} + type + code + value (64-bit)
    assert struct.calcsize(di.INPUT_EVENT_FMT) == 24


def test_ioctl_numbers_are_the_documented_uinput_ones():
    assert di.UI_SET_EVBIT == 0x40045564
    assert di.UI_SET_KEYBIT == 0x40045565
    assert di.UI_DEV_CREATE == 0x5501
    assert di.UI_DEV_DESTROY == 0x5502


# --------------------------------------------------------------------------
# key maps
# --------------------------------------------------------------------------
@pytest.mark.parametrize("name,expected", [
    ("q", 16), ("w", 17), ("p", 25),      # top row, base 16
    ("a", 30), ("l", 38), ("s", 31),      # home row, base 30
    ("z", 44), ("b", 48), ("m", 50),      # bottom row, base 44
    ("1", 2), ("0", 11), ("5", 6),        # digits
])
def test_letter_and_digit_keycodes(name, expected):
    assert di.resolve_key(name) == expected


@pytest.mark.parametrize("name,expected", [
    ("enter", 28), ("return", 28), ("esc", 1), ("escape", 1),
    ("space", 57), ("tab", 15), ("backspace", 14), ("delete", 111),
    ("ctrl", 29), ("control", 29), ("shift", 42), ("alt", 56),
    ("win", 125), ("meta", 125), ("up", 103), ("down", 108),
    ("left", 105), ("right", 106), ("home", 102), ("end", 107),
    ("pageup", 104), ("pagedown", 109), ("insert", 110),
    ("f1", 59), ("f5", 63), ("f10", 68), ("f11", 87), ("f12", 88),
    ("f13", 183), ("capslock", 58), ("printscreen", 99),
])
def test_named_keys(name, expected):
    assert di.resolve_key(name) == expected


def test_unknown_key_resolves_to_none_and_raises_on_use():
    assert di.resolve_key("hyper") is None
    assert di.resolve_key("") is None
    with pytest.raises(RuntimeError):
        di.resolve_keys(["ctrl", "hyper"])


@pytest.mark.parametrize("ch,code,shift", [
    ("a", 30, False), ("A", 30, True),
    ("z", 44, False), ("Z", 44, True),
    ("1", 2, False), ("!", 2, True),
    ("@", 3, True), ("9", 10, False), ("(", 10, True),
    ("-", 12, False), ("_", 12, True),
    ("=", 13, False), ("+", 13, True),
    ("[", 26, False), ("{", 26, True),
    (";", 39, False), (":", 39, True),
    ("'", 40, False), ('"', 40, True),
    ("`", 41, False), ("~", 41, True),
    (",", 51, False), ("<", 51, True),
    (".", 52, False), (">", 52, True),
    ("/", 53, False), ("?", 53, True),
    (" ", 57, False), ("\n", 28, False), ("\t", 15, False),
])
def test_char_map_covers_printable_ascii_with_shift(ch, code, shift):
    assert di._CHAR_MAP[ch] == (code, shift)


def test_shift_is_latched_only_while_needed():
    """Typing "Ab!" must press shift for 'A', release it for 'b', and
    press it again for '!' — no stray shift-down left at the end."""
    dev = Sink()
    di._type_uinput(dev, "Ab!", 0)
    shift_values = [e[2] for e in dev.events
                    if e[0] == "key" and e[1] == 42]
    assert shift_values == [True, False, True, False]
    # the very last key event must be shift release (then a final syn)
    assert [e for e in dev.events if e[0] == "key"][-1] == ("key", 42, False)


def test_typing_event_stream_is_exact():
    dev = Sink()
    di._type_uinput(dev, "A", 0)
    assert dev.events == [
        ("key", 42, True), ("syn",),
        ("key", 30, True), ("syn",),
        ("key", 30, False), ("syn",),
        ("key", 42, False), ("syn",),
    ]


def test_unmapped_characters_are_skipped_not_crashed():
    dev = Sink()
    di._type_uinput(dev, "héllo", 0)   # 'é' has no US-layout keycode
    # 'h','l','l','o' still typed: 4 characters * 2 key events each
    downs = [e for e in dev.events if e[0] == "key" and e[2]]
    assert len(downs) == 4


def test_hotkey_presses_down_in_order_and_releases_in_reverse():
    dev = Sink()
    di._hotkey_uinput(dev, di.resolve_keys(["ctrl", "shift", "t"]))
    downs = [e[1] for e in dev.events if e[0] == "key" and e[2]]
    ups = [e[1] for e in dev.events if e[0] == "key" and not e[2]]
    assert downs == [29, 42, 20]          # ctrl, shift, t
    assert ups == [20, 42, 29]            # exactly reversed
    assert all(e == ("syn",) for e in dev.events if e[0] == "syn")


# --------------------------------------------------------------------------
# backend selection — the "don't break X11" contract
# --------------------------------------------------------------------------
def test_x11_session_never_uses_uinput(monkeypatch):
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    assert di.active() is False
    assert "pyautogui (X11 session)" in di.status()


def test_wayland_without_uinput_falls_back_with_actionable_hint(monkeypatch):
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.setattr(di, "uinput_writable", lambda: False)
    assert di.active() is False
    status = di.status()
    assert "setup_uinput.sh" in status
    assert "pyautogui" in status


def test_wayland_with_writable_uinput_activates_full_control(monkeypatch):
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.setattr(di, "uinput_writable", lambda: True)
    monkeypatch.setattr(di, "_keyboard", lambda: Sink())
    monkeypatch.setattr(di, "_mouse", lambda: Sink())
    assert di.active() is True
    assert "full Wayland control" in di.status()


def test_uinput_error_is_reported_not_swallowed(monkeypatch):
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.setattr(di, "uinput_writable", lambda: True)

    def boom():
        raise PermissionError("[Errno 13] Permission denied: '/dev/uinput'")

    monkeypatch.setattr(di, "_keyboard", boom)
    assert di.active() is False
    assert "Permission denied" in di.status()


def test_readiness_is_cached_and_can_be_reset(monkeypatch):
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.setattr(di, "uinput_writable", lambda: False)
    assert di.active() is False
    assert di._STATE["ready"] is False
    di.reset()
    assert di._STATE["ready"] is None


# --------------------------------------------------------------------------
# pyautogui passthrough must stay byte-identical to the old behaviour
# --------------------------------------------------------------------------
class FakePG:
    def __init__(self):
        self.calls = []

    def typewrite(self, text, interval=0.0):
        self.calls.append(("typewrite", text, interval))

    def hotkey(self, *keys):
        self.calls.append(("hotkey",) + keys)

    def press(self, key):
        self.calls.append(("press", key))

    def click(self, *args, **kwargs):
        self.calls.append(("click", args, kwargs))

    def moveTo(self, x, y, duration=0.0):
        self.calls.append(("moveTo", x, y, duration))

    def dragTo(self, x, y, duration=0.0, button="left"):
        self.calls.append(("dragTo", x, y, duration, button))

    def scroll(self, clicks):
        self.calls.append(("scroll", clicks))

    def hscroll(self, clicks):
        self.calls.append(("hscroll", clicks))


@pytest.fixture
def fake_pg(monkeypatch):
    pg = FakePG()
    monkeypatch.setattr(di, "active", lambda: False)
    monkeypatch.setattr(di, "require_pyautogui", lambda: pg)
    return pg


def test_click_passthrough_arguments_unchanged(fake_pg):
    di.click(10, 20, "left", 2)
    di.click()
    assert fake_pg.calls == [
        ("click", (10, 20), {"button": "left", "clicks": 2}),
        ("click", (), {"button": "left", "clicks": 1}),
    ]


def test_type_press_hotkey_move_drag_scroll_passthrough(fake_pg):
    di.type_text("hi", 0.05)
    di.press("enter")
    di.hotkey("ctrl", "c")
    di.move(1, 2, 0.3)
    di.drag(0, 0, 5, 5, 0.5)
    di.scroll(True, -3)
    di.scroll(False, 2)
    assert fake_pg.calls == [
        ("typewrite", "hi", 0.05),
        ("press", "enter"),
        ("hotkey", "ctrl", "c"),
        ("moveTo", 1, 2, 0.3),
        ("moveTo", 0, 0, 0.2),
        ("dragTo", 5, 5, 0.5, "left"),
        ("scroll", -3),
        ("hscroll", 2),
    ]


# --------------------------------------------------------------------------
# uinput injection paths (active backend)
# --------------------------------------------------------------------------
def test_uinput_click_warps_then_clicks_the_right_button(monkeypatch):
    sink = Sink()
    monkeypatch.setattr(di, "active", lambda: True)
    monkeypatch.setattr(di, "_mouse", lambda: sink)
    di.click(5, 6, "right", 2)
    assert ("abs", di.ABS_X, 5) in sink.events
    assert ("abs", di.ABS_Y, 6) in sink.events
    downs = [e for e in sink.events if e[0] == "key" and e[2]]
    assert all(e[1] == di.BTN_RIGHT for e in downs)      # right button used
    assert len(downs) == 2                               # clicked twice


def test_uinput_press_resolves_key(monkeypatch):
    sink = Sink()
    monkeypatch.setattr(di, "active", lambda: True)
    monkeypatch.setattr(di, "_keyboard", lambda: sink)
    di.press("enter")
    assert ("key", 28, True) in sink.events
    assert ("key", 28, False) in sink.events


def test_uinput_unknown_press_raises(monkeypatch):
    monkeypatch.setattr(di, "active", lambda: True)
    monkeypatch.setattr(di, "_keyboard", lambda: Sink())
    with pytest.raises(RuntimeError):
        di.press("hyper")


def test_scroll_maps_to_wheel_axes(monkeypatch):
    sink = Sink()
    monkeypatch.setattr(di, "active", lambda: True)
    monkeypatch.setattr(di, "_mouse", lambda: sink)
    di.scroll(True, -3)
    di.scroll(False, 2)
    assert ("rel", di.REL_WHEEL, -3) in sink.events
    assert ("rel", di.REL_HWHEEL, 2) in sink.events


def test_warp_clamps_to_screen_bounds(monkeypatch):
    sink = Sink()
    monkeypatch.setattr(di, "_screen_size", lambda: (100, 80))
    di._STATE["abs_works"] = True
    di._warp(sink, 5000, -20)
    assert ("abs", di.ABS_X, 99) in sink.events
    assert ("abs", di.ABS_Y, 0) in sink.events


# --------------------------------------------------------------------------
# mouse calibration (absolute preferred, relative fallback, honest unknown)
# --------------------------------------------------------------------------
def test_calibration_prefers_absolute_and_restores_cursor(monkeypatch):
    dev = Sink()
    positions = iter([(100, 50), (160, 50)])
    monkeypatch.setattr(di, "pointer_pos", lambda: next(positions))
    monkeypatch.setattr(di, "_screen_size", lambda: (1366, 768))
    di._calibrate(dev)
    assert di._STATE["abs_works"] is True
    assert di._STATE["verified"] is True
    abs_writes = [e[2] for e in dev.events if e[0] == "abs" and e[1] == di.ABS_X]
    assert abs_writes[0] == 160        # probe: p0 + 60
    assert abs_writes[-1] == 100       # restored to the original position


def test_calibration_falls_back_to_relative_when_abs_ignored(monkeypatch):
    dev = Sink()
    # pointer never responds to the absolute probe, but follows the
    # relative one -> relative mode
    positions = iter([(100, 50), (100, 50), (160, 50)])
    monkeypatch.setattr(di, "pointer_pos", lambda: next(positions))
    monkeypatch.setattr(di, "_screen_size", lambda: (1366, 768))
    di._calibrate(dev)
    assert di._STATE["abs_works"] is False
    assert di._STATE["verified"] is True
    rel_moves = [e[2] for e in dev.events if e[0] == "rel" and e[1] == di.REL_X]
    assert rel_moves[0] == 60 and rel_moves[-1] == -60   # probe then restore


def test_calibration_without_position_feedback_uses_absolute(monkeypatch):
    dev = Sink()
    monkeypatch.setattr(di, "pointer_pos", lambda: None)
    di._calibrate(dev)
    assert di._STATE["abs_works"] is True
    assert di._STATE["verified"] is False   # honest: could not verify


def test_calibration_unverifiable_reports_not_verified(monkeypatch):
    dev = Sink()
    positions = iter([(100, 50), (100, 50), (100, 50)])  # nothing ever moves
    monkeypatch.setattr(di, "pointer_pos", lambda: next(positions))
    monkeypatch.setattr(di, "_screen_size", lambda: (1366, 768))
    di._calibrate(dev)
    assert di._STATE["verified"] is False
