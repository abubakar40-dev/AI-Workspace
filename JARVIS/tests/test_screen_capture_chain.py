"""Tests for screen_capture's capture chain (portal -> grim -> ... -> X11).

Everything here is mocked: no portal dialog, no uinput, no real display.
The live behaviour was verified separately on GNOME 50 / Wayland (see the
measured-status table in screen_capture.py's module docstring).
"""

import inspect
import json
import sys
from pathlib import Path

import pytest
from PIL import Image

import screen_capture as sc


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def write_real(path, size=(80, 60)) -> None:
    """A colourful, definitely-not-blank PNG."""
    img = Image.new("RGB", size)
    px = img.load()
    for x in range(size[0]):
        for y in range(size[1]):
            px[x, y] = ((x * 7) % 256, (y * 5) % 256, (x + y) % 256)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "PNG")


def write_black(path, size=(80, 60)) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size).save(path, "PNG")


def portal_ok(uri):
    return {"ok": True, "method": "portal-silent", "uri": uri, "detail": "portal-silent: captured"}


def portal_fail(detail="portal-silent: portal response code 2"):
    return {"ok": False, "method": "portal-silent", "uri": None, "detail": detail}


@pytest.fixture
def real_capture(monkeypatch):
    """_copy_uri that writes a real frame (the portal hand-off)."""
    def fake_copy(uri, dest):
        if uri == "missing":
            return "Source not found: /nonexistent"
        write_real(dest)
        return None
    monkeypatch.setattr(sc, "_copy_uri", fake_copy)
    return fake_copy


# --------------------------------------------------------------------------
# signatures / contracts
# --------------------------------------------------------------------------
def test_capture_signature_supports_both_call_styles():
    sig = inspect.signature(sc.capture)
    assert sig.parameters["dest"].default is None
    assert sig.parameters["timeout"].default == 20.0
    # the wired caller does capture(str(path)); their test does capture()
    bound_str = sig.bind("/tmp/x.png")
    bound_none = sig.bind()
    bound_str.apply_defaults()
    bound_none.apply_defaults()
    assert bound_str.arguments["dest"] == "/tmp/x.png"
    assert bound_none.arguments["dest"] is None
    assert bound_str.arguments["timeout"] == 20.0


def test_public_api_present():
    for name in ("capture", "grab", "status", "capture_region", "run_portal", "reset"):
        assert hasattr(sc, name), name


def test_status_reports_key_facts():
    st = sc.status()
    for key in ("wayland", "scrot_available", "grim_available", "resolution",
                "portal_python", "last", "state"):
        assert key in st, key
    assert isinstance(st["wayland"], bool)


# --------------------------------------------------------------------------
# blank-frame rejection (the XWayland-black signature)
# --------------------------------------------------------------------------
def test_blank_detection_rejects_flat_frames(tmp_path):
    black = tmp_path / "black.png"
    write_black(black)
    assert sc._is_blank(black) is True


def test_blank_detection_accepts_real_frames(tmp_path):
    real = tmp_path / "real.png"
    write_real(real)
    assert sc._is_blank(real) is False


def test_blank_detection_missing_file_is_blank(tmp_path):
    assert sc._is_blank(tmp_path / "nope.png") is True


# --------------------------------------------------------------------------
# _copy_uri
# --------------------------------------------------------------------------
def test_copy_uri_moves_file(tmp_path):
    src = tmp_path / "portal output.png"
    write_real(src)
    dest = tmp_path / "final.png"
    assert sc._copy_uri(src.as_uri(), dest) is None
    assert dest.exists() and not src.exists()


def test_copy_uri_missing_source_is_reason(tmp_path):
    out = sc._copy_uri((tmp_path / "gone.png").as_uri(), tmp_path / "d.png")
    assert isinstance(out, str) and "Source not found" in out


# --------------------------------------------------------------------------
# the chain
# --------------------------------------------------------------------------
def test_silent_portal_success_short_circuits(monkeypatch, tmp_path, real_capture):
    calls = []

    def fake_run_portal(interactive=False, timeout=10, auto_confirm=True, heal=True):
        calls.append(interactive)
        return portal_ok("file:///whatever.png")

    monkeypatch.setattr(sc, "run_portal", fake_run_portal)
    ok, detail = sc.capture(tmp_path / "a.png")
    assert ok is True and "portal-silent" in detail
    assert calls == [False]                      # never escalated


def test_silent_denied_escalates_to_interactive(monkeypatch, tmp_path, real_capture):
    calls = []

    def fake_run_portal(interactive=False, timeout=10, auto_confirm=True, heal=True):
        calls.append((interactive, auto_confirm))
        if not interactive:
            return portal_fail()                 # denied: code 2
        return {"ok": True, "method": "portal-interactive", "uri": "file:///x.png",
                "detail": "portal-interactive: captured"}

    monkeypatch.setattr(sc, "run_portal", fake_run_portal)
    monkeypatch.setattr(sc.desktop_input, "active", lambda: True)
    ok, detail = sc.capture(tmp_path / "b.png")
    assert ok is True and "portal-interactive" in detail
    assert calls == [(False, True), (True, True)]


def test_interactive_skipped_without_backend(monkeypatch, tmp_path):
    monkeypatch.setattr(sc, "run_portal", lambda *a, **k: portal_fail())
    monkeypatch.setattr(sc.desktop_input, "active", lambda: False)
    monkeypatch.delenv("JARVIS_SCREENSHOT_MANUAL", raising=False)
    ok, detail = sc.capture(tmp_path / "c.png")
    assert ok is False
    assert "interactive portal: skipped" in detail


def test_manual_env_forces_interactive_without_auto_confirm(monkeypatch, tmp_path, real_capture):
    calls = []

    def fake_run_portal(interactive=False, timeout=10, auto_confirm=True, heal=True):
        calls.append((interactive, auto_confirm))
        if not interactive:
            return portal_fail()
        return {"ok": True, "method": "portal-interactive", "uri": "file:///x.png",
                "detail": "portal-interactive: captured"}

    monkeypatch.setattr(sc, "run_portal", fake_run_portal)
    monkeypatch.setattr(sc.desktop_input, "active", lambda: False)
    monkeypatch.setenv("JARVIS_SCREENSHOT_MANUAL", "1")
    ok, _detail = sc.capture(tmp_path / "d.png")
    assert ok is True
    assert calls == [(False, True), (True, False)]   # human clicks in manual mode


def test_blank_frame_is_rejected_and_chain_escalates(monkeypatch, tmp_path):
    state = {"n": 0}

    def fake_run_portal(interactive=False, timeout=10, auto_confirm=True, heal=True):
        state["n"] += 1
        if not interactive:
            return portal_ok("file:///black.png")
        return {"ok": True, "method": "portal-interactive", "uri": "file:///real.png",
                "detail": "portal-interactive: captured"}

    def fake_copy(uri, dest):
        if uri.endswith("black.png"):
            write_black(dest)                     # portal gave us a black frame
        else:
            write_real(dest)
        return None

    monkeypatch.setattr(sc, "run_portal", fake_run_portal)
    monkeypatch.setattr(sc, "_copy_uri", fake_copy)
    monkeypatch.setattr(sc.desktop_input, "active", lambda: True)

    ok, detail = sc.capture(tmp_path / "e.png")
    assert ok is True
    assert "portal-interactive" in detail         # silent's black frame escalated
    assert state["n"] == 2


def test_all_methods_fail_returns_reasons_without_raising(monkeypatch, tmp_path):
    monkeypatch.setattr(sc, "run_portal", lambda *a, **k: portal_fail())
    monkeypatch.setattr(sc.desktop_input, "active", lambda: True)
    monkeypatch.setattr(sc.shutil, "which", lambda name: None)
    monkeypatch.setattr(sc, "_is_wayland", lambda: True)   # skip X11 grab
    ok, detail = sc.capture(tmp_path / "f.png")
    assert ok is False
    assert isinstance(detail, str) and "portal-silent" in detail
    assert "grim: not installed" in detail
    assert "gnome-screenshot: not installed" in detail
    assert "rejected on Wayland" in detail
    assert not (tmp_path / "f.png").exists()      # no fake success file


def test_capture_never_raises(monkeypatch, tmp_path):
    def boom(*a, **k):
        raise RuntimeError("exploded")
    monkeypatch.setattr(sc, "run_portal", boom)
    monkeypatch.setattr(sc.desktop_input, "active", lambda: True)
    monkeypatch.setattr(sc.shutil, "which", lambda name: None)
    monkeypatch.setattr(sc, "_is_wayland", lambda: True)
    ok, detail = sc.capture(tmp_path / "g.png")
    assert ok is False and "exploded" in detail


# --------------------------------------------------------------------------
# portal client: JSON parsing, wedge healing, auto-Confirm
# --------------------------------------------------------------------------
def test_parse_client_reads_last_json_line():
    out = 'noise\n{"ok": true, "code": 0, "uri": "file:///x.png", "error": null}\n'
    res = sc._parse_client(out, "")
    assert res["ok"] is True and res["uri"] == "file:///x.png"


def test_parse_client_garbage_reports_stderr():
    res = sc._parse_client("not json at all", "Traceback: boom")
    assert res["ok"] is False
    assert res["error"] == "Traceback: boom"


@pytest.mark.parametrize("msg", [
    "portal did not answer in time (the capture UI may still be waiting)",
    "portal client hung (timed out)",
    "Request timed out",
])
def test_wedge_signatures_detected(msg):
    assert sc._looks_wedged(msg) is True


def test_permission_denied_is_not_a_wedge():
    assert sc._looks_wedged("Only the focused application can take screenshots") is False


def test_wedged_portal_is_healed_and_retried(monkeypatch):
    wedge = json.dumps({"ok": False, "code": None, "uri": None,
                        "error": "portal did not answer in time"})
    good = json.dumps({"ok": True, "code": 0, "uri": "file:///x.png", "error": None})
    outputs = [wedge, good]
    runs = []
    restarts = []

    monkeypatch.setattr(sc, "_get_py_path", lambda: "/usr/bin/python3")
    monkeypatch.setattr(sc, "_restart_portal",
                        lambda: (restarts.append(1), True)[1])

    def counting(cmd, hard, confirm):
        runs.append(tuple(cmd))
        return (0, outputs[len(runs) - 1], "")
    monkeypatch.setattr(sc, "_run_client", counting)

    res = sc.run_portal(False, timeout=5)
    assert res["ok"] is True
    assert len(restarts) == 1                    # healed exactly once
    assert len(runs) == 2                        # original + retry


def test_clean_failure_does_not_restart_portal(monkeypatch):
    bad = json.dumps({"ok": False, "code": 2, "uri": None,
                      "error": "Only the focused application can take screenshots"})
    runs = []
    restarts = []
    monkeypatch.setattr(sc, "_get_py_path", lambda: "/usr/bin/python3")
    monkeypatch.setattr(sc, "_restart_portal",
                        lambda: (restarts.append(1), True)[1])

    def counting(cmd, hard, confirm):
        runs.append(1)
        return (0, bad, "")
    monkeypatch.setattr(sc, "_run_client", counting)

    res = sc.run_portal(False, timeout=5)
    assert res["ok"] is False
    assert len(runs) == 1 and restarts == []


def test_auto_confirm_presses_enter_until_client_exits(monkeypatch):
    pressed = []
    killed = []

    class FakeProc:
        polls = 0

        def poll(self):
            FakeProc.polls += 1
            return None if FakeProc.polls < 4 else 0

        @property
        def returncode(self):
            return 0 if FakeProc.polls >= 4 else None

        def communicate(self, timeout=None):
            return ('{"ok": true, "code": 0, "uri": "file:///x.png", "error": null}', "")

        def kill(self):
            killed.append(1)

    monkeypatch.setattr(sc.subprocess, "Popen",
                        lambda *a, **k: FakeProc())
    monkeypatch.setattr(sc.desktop_input, "press",
                        lambda key: pressed.append(key))
    monkeypatch.setattr(sc.time, "sleep", lambda s: None)
    monkeypatch.setattr(sc, "_SETTLE", 0.0)
    monkeypatch.setattr(sc, "_PRESS_EVERY", 0.0)

    rc, out, err = sc._run_client(["portal-client"], 5.0, auto_confirm=True)
    assert rc == 0
    assert pressed and all(k == "enter" for k in pressed)
    assert killed == []                          # exited cleanly, never killed
    assert json.loads(out)["ok"] is True


def test_auto_confirm_disabled_uses_plain_run(monkeypatch):
    ran = []

    class R:
        returncode, stdout, stderr = 0, '{"ok": true}', ""

    def fake_run(cmd, capture_output=True, text=True, timeout=None):
        ran.append(tuple(cmd))
        return R()

    monkeypatch.setattr(sc.subprocess, "run", fake_run)
    rc, out, err = sc._run_client(["x"], 5.0, auto_confirm=False)
    assert rc == 0 and ran


def test_hard_timeout_kills_and_reports(monkeypatch):
    class HangingProc:
        def __init__(self):
            self._n = 0

        def poll(self):
            self._n += 1
            return None                           # never finishes

        def kill(self):
            self.killed = True

        def communicate(self, timeout=None):
            return ("", "portal client hung (killed)")

    monkeypatch.setattr(sc.subprocess, "Popen", lambda *a, **k: HangingProc())
    monkeypatch.setattr(sc, "_SETTLE", 99.0)      # never press Enter
    rc, out, err = sc._run_client(["x"], 0.05, auto_confirm=True)
    assert rc is None and "hung" in err


# --------------------------------------------------------------------------
# grab / capture_region
# --------------------------------------------------------------------------
def test_grab_returns_png_bytes(monkeypatch, tmp_path):
    def fake_capture(dest=None, timeout=20.0):
        write_real(dest)
        return (True, "ok")
    monkeypatch.setattr(sc, "capture", fake_capture)
    data = sc.grab()
    assert isinstance(data, bytes) and data[:8] == b"\x89PNG\r\n\x1a\n"


def test_grab_none_on_failure(monkeypatch):
    monkeypatch.setattr(sc, "capture", lambda dest=None, timeout=20.0: (False, "nope"))
    assert sc.grab() is None


def test_region_crops_full_frame(monkeypatch, tmp_path):
    def fake_capture(dest=None, timeout=20.0):
        write_real(dest, size=(400, 300))
        return (True, "ok")
    monkeypatch.setattr(sc, "capture", fake_capture)

    out = tmp_path / "region.png"
    ok, detail = sc.capture_region(10, 20, 100, 50, out)
    assert ok is True
    with Image.open(out) as img:
        assert img.size == (100, 50)


def test_region_clamps_to_screen(monkeypatch, tmp_path):
    def fake_capture(dest=None, timeout=20.0):
        write_real(dest, size=(400, 300))
        return (True, "ok")
    monkeypatch.setattr(sc, "capture", fake_capture)

    out = tmp_path / "region2.png"
    ok, _detail = sc.capture_region(390, 290, 100, 100, out)
    assert ok is True
    with Image.open(out) as img:
        assert img.size == (10, 10)               # clamped at the edge


def test_region_rejects_bad_size():
    ok, detail = sc.capture_region(0, 0, 0, 10)
    assert ok is False and "bad size" in detail


def test_region_failure_propagates(monkeypatch, tmp_path):
    monkeypatch.setattr(sc, "capture",
                        lambda dest=None, timeout=20.0: (False, "all methods failed"))
    ok, detail = sc.capture_region(0, 0, 10, 10, tmp_path / "r.png")
    assert ok is False and "all methods failed" in detail
