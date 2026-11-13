"""
Tests for the interactive layer: clickable controls, real views, the chat
channel, and the microphone fix.

The command center is only useful if pressing things does something. These
tests pin that contract at three levels: the binding script must route every
visible control somewhere, every view must return real content rather than
placeholders, and the drawer/chat plumbing must actually fire.
"""

from __future__ import annotations

import asyncio
import inspect
import re
import sys
import textwrap

import pytest

pytest.importorskip("PyQt6")

import command_bridge as CB
import command_center as CC
import command_panels as CP

MARKUP = CC.COMMAND_CENTER_HTML.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Every visible control is wired
# ---------------------------------------------------------------------------
# (label, the selector the design uses, the view/verb it must route to)
CONTROLS = [
    ("nav Command Center", "nav a", "command center"),
    ("nav AI Core", "nav a", "ai core"),
    ("nav Agents", "nav a", "agents"),
    ("nav Tasks", "nav a", "tasks"),
    ("nav Calendar", "nav a", "calendar"),
    ("nav Memory", "nav a", "memory"),
    ("nav Conversations", "nav a", "conversations"),
    ("nav Knowledge Base", "nav a", "knowledge base"),
    ("nav Tools & Skills", "nav a", "tools"),
    ("nav Workflows", "nav a", "workflows"),
    ("top icon 1", ".icon-btn", "icon"),
    ("top icon 2", ".icon-btn", "icon"),
    ("top icon 3", ".icon-btn", "icon"),
    ("FOCUS MODE", ".focus-btn", "focus mode"),
    ("Executive Briefing", ".brief-btn", "executive briefing"),
    ("TALK TO JARVIS", ".talk-btn", "talk to jarvis"),
    ("orb", ".orb", "orb"),
    ("search", ".search", "search"),
    ("avatar", ".avatar", "avatar"),
    ("status pill", ".status-pill", "status pill"),
    ("brand", ".brand", "brand"),
    ("voice card header", ".voice-card .label", "voice"),
]


def test_every_visible_control_exists_in_the_page():
    for label, sel, _ in CONTROLS:
        base = sel.split()[0]
        assert base.lstrip(".") in MARKUP or f'class="{base.lstrip(".")}' in MARKUP, \
            f"{label}: {sel} is not in the page"


def test_every_control_has_a_handler_in_the_binding():
    js = CB.BINDING_JS
    for label, sel, _ in CONTROLS:
        base = sel.split()[0]
        assert base in js, f"{label}: no handler references {base}"


def test_nav_labels_are_read_without_the_icon_glyph():
    """The anchor's textContent is "◉AI Core", not "AI Core"."""
    assert "navLabel" in CB.BINDING_JS
    assert "nodeType === 3" in CB.BINDING_JS, \
        "nav text must come from text nodes only, or the glyph breaks the lookup"


def test_nav_view_map_covers_every_nav_entry():
    block = CB.BINDING_JS
    start = block.index("var NAV_VIEWS")
    end = block.index("};", start)
    entries = dict(re.findall(r"'([^']+)':\s*(null|'[^']+')", block[start:end]))
    for label in ("command center", "ai core", "agents", "tasks", "calendar",
                  "memory", "conversations", "knowledge base", "workflows"):
        assert label in entries, f"nav entry {label!r} is not routed anywhere"
    assert entries["tools"] == "'tools'"


def test_cards_use_delegation_so_rebuilt_nodes_stay_clickable():
    """The pollers replace feed items and cards; a per-node listener dies."""
    assert "document.addEventListener('click'" in CB.BINDING_JS
    assert "t.closest('.feed-item')" in CB.BINDING_JS
    assert "t.closest('.agent-card')" in CB.BINDING_JS


def test_bridge_exposes_every_slot_the_page_calls():
    for slot in ("sendCommand", "setMuted", "mutedState", "navClicked",
                 "iconClicked", "requestView", "openChat", "runBriefing",
                 "setFocusState"):
        assert hasattr(CB.CommandCenterBridge, slot), f"missing bridge slot {slot}"


def test_bridge_signals_exist_for_each_request():
    for sig in ("command_received", "mute_requested", "view_requested",
                "chat_requested", "briefing_requested", "focus_state"):
        assert hasattr(CB.CommandCenterBridge, sig), f"missing signal {sig}"


def test_binding_never_assumes_a_window_pybridge_global():
    """QWebChannel publishes channel.objects, not a global. An early version
    read window.pybridge and silently no control did anything."""
    assert "window.pybridge = c.objects.pybridge" in \
        inspect.getsource(CC.CommandCenter._on_page_loaded)
    assert "window.__jarvisChannel && window.__jarvisChannel.objects" in CB.BINDING_JS


# ---------------------------------------------------------------------------
# 2. Every view returns real content
# ---------------------------------------------------------------------------
VIEWS = ["ai_core", "agents", "tasks", "calendar", "conversations", "memory",
         "knowledge", "tools", "workflows", "monitor", "notifications",
         "providers", "settings", "profile", "schedule", "events",
         "new_task", "chatday"]


@pytest.mark.parametrize("view", VIEWS)
def test_view_builds_without_error(view):
    title, sub, html = CP.build_view(view, {"feed": [], "task": None})
    assert title and title != "ERROR"
    assert "Could not build" not in html
    assert len(html) > 40, f"{view} returned almost nothing"


@pytest.mark.parametrize("view", VIEWS)
def test_view_has_no_placeholder_data(view):
    """A panel full of em-dashes is a dead panel."""
    title, sub, html = CP.build_view(view, {"feed": [], "task": None})
    # A prose em-dash is fine; a *value cell* that is only an em-dash is the
    # placeholder a broken data source produces.
    empty_cells = re.findall(r"<td[^>]*>\s*—\s*</td>", html)
    if view in ("tasks", "notifications", "events", "calendar", "schedule"):
        return                      # legitimately empty when nothing is stored
    assert not empty_cells, f"{view} has {len(empty_cells)} placeholder cells"


def test_monitor_view_uses_the_real_sensor_keys():
    """host_summary() reports cpu_pct/mem/disk/temp, not cpu_percent."""
    title, sub, html = CP.build_view("monitor", {})
    text = re.sub(r"<[^>]+>", " ", html)
    assert "Package temp" in text
    assert "Adapter" in text
    assert "Uptime" in text


def test_gauge_views_differ_per_metric():
    seen = set()
    for label in ("CPU", "RAM", "Disk"):
        _, _, html = CP.build_view(f"gauge?{label}", {})
        seen.add(re.sub(r"<[^>]+>", " ", html))
    assert len(seen) == 3, "all three gauges rendered the same content"


def test_core_item_routes_to_the_right_view():
    for row, expected in (("Memory", "MEMORY"), ("LLMs", "PROVIDERS"),
                          ("System", "SYSTEM MONITOR"), ("Agents", "AGENTS"),
                          ("Voice", "SETTINGS"), ("AI Core", "AI CORE")):
        title, _, _ = CP.build_view(f"core?{row}", {})
        assert title == expected, f"core row {row} opened {title}"


def test_panels_use_tables_not_flexbox():
    """Qt's rich-text engine has no flexbox; flex rows collapsed."""
    for view in ("monitor", "memory", "knowledge", "providers"):
        _, _, html = CP.build_view(view, {})
        assert "display:flex" not in html, f"{view} still uses flexbox"


def test_unknown_view_degrades_gracefully():
    title, sub, html = CP.build_view("nope", {})
    assert title and "Traceback" not in html


def test_views_escape_untrusted_text():
    _, _, html = CP.build_view("gauge?<script>x</script>", {})
    assert "<script>" not in html


# ---------------------------------------------------------------------------
# 3. The drawer and chat actually fire
# ---------------------------------------------------------------------------
def _bare_host() -> CC.CommandCenter:
    """A host without the web view.

    PyQt refuses *any* attribute assignment on a QWidget whose ``__init__``
    never ran, so every field the code under test touches has to exist here.
    """
    import collections
    ui = CC.CommandCenter.__new__(CC.CommandCenter)
    ui._task = None
    ui._timeline = []
    ui._states_sent = "IDLE"
    ui._mic_down = False
    ui._turns = 0
    ui._feed_queue = collections.deque(maxlen=200)
    ui._feed_seen = collections.deque(maxlen=60)
    ui._chat_queue = collections.deque(maxlen=200)
    ui._recent_feed = collections.deque(maxlen=60)
    ui._attention_log = []

    class _Log:
        def __init__(self):
            self.cleared = 0
        def clear(self):
            self.cleared += 1

    class _Chat:
        def __init__(self):
            self.log = _Log()
        def isVisible(self):
            return False
        def close_panel(self):
            pass
        def append(self, *_a, **_k):
            pass

    ui.chat = _Chat()
    ui.drawer = _Chat()
    return ui


def test_view_context_is_buildable():
    ctx = _bare_host()._view_context()
    assert set(ctx) == {"state", "mic_down", "task", "feed", "attention"}
    CP.build_view("ai_core", ctx)          # must not raise


def test_write_log_mirrors_conversation_into_the_chat_queue():
    ui = _bare_host()
    ui.write_log("You: what is the weather")
    ui.write_log("Jarvis: it is overcast")
    assert [w for w, _ in ui._chat_queue] == ["you", "jarvis"]
    assert ui._chat_queue[0][1] == "what is the weather"


def test_chat_ignores_blank_input():
    ui = _bare_host()
    seen = []
    ui.on_text_command = lambda *a, **k: seen.append(a)
    ui._on_chat_submitted("   ")
    assert seen == []


def test_chat_clear_command_empties_the_log():
    ui = _bare_host()
    ui.write_log("You: hello")
    seen = []
    ui.on_text_command = lambda *a, **k: seen.append(a)
    ui._on_chat_submitted("/clear")
    assert ui.chat.log.cleared == 1
    assert seen == [], "/clear must not reach the assistant"


def test_briefing_falls_back_when_no_handler_is_attached():
    ui = _bare_host()
    ui.on_briefing = None
    ui.run_briefing()                    # must not raise
    assert ui._feed_queue, "expected a feed entry about the missing handler"


def test_briefing_is_composed_from_real_state():
    import main as M
    text = M._executive_briefing_text()
    assert "System:" in text
    assert re.search(r"CPU \d+%", text)
    assert re.search(r"memory \d+%", text)
    assert "Memory:" in text


def test_briefing_text_builder_is_not_a_stub():
    import main as M
    src = inspect.getsource(M._speak_daily_briefing)
    assert "disabled" not in src.lower(), "the briefing is disabled again"
    assert "pass" not in src.split("\n")[-3:][0] if src else True


# ---------------------------------------------------------------------------
# 4. The microphone
# ---------------------------------------------------------------------------
def test_open_input_stream_takes_a_callback():
    """It referenced a bare `callback` that was not a parameter; every attempt
    raised NameError, the bare except swallowed it, and the microphone always
    reported 'could not open any microphone input'."""
    import main as M
    sig = inspect.signature(M._open_input_stream)
    assert "callback" in sig.parameters
    assert sig.parameters["callback"].default is None


def test_microphone_resolution_never_returns_a_loopback():
    import main as M
    devs = M._audio_devices()
    if M._MIC_DEVICE is not None and 0 <= M._MIC_DEVICE < len(devs):
        name = devs[M._MIC_DEVICE]["name"]
        assert not M._is_loopback(name), f"microphone resolved to {name}"


def test_microphone_reports_why_it_failed():
    import main as M
    src = inspect.getsource(M._open_input_stream)
    assert "failures" in src, "rejections must be recorded, not swallowed"
    assert "except Exception:\\n            continue" not in src.replace(" ", " ") \
        or "failures.append" in src


def test_input_stream_attempts_several_devices():
    """A pinned device is a coin flip under PipeWire; the opener must walk a
    list of candidates."""
    import main as M
    src = inspect.getsource(M._open_input_stream)
    assert "attempts" in src
    assert "Last resort" in src or "_is_loopback" in src


def test_retry_path_passes_the_callback_too():
    import main as M
    src = inspect.getsource(M.JarvisLive._listen_audio)
    assert src.count("callback=callback") >= 2, "the retry path dropped the callback"


# ---------------------------------------------------------------------------
# 5. The live-audio payload
# ---------------------------------------------------------------------------
def test_input_mime_declares_the_sample_rate():
    """Plain "audio/pcm" is rejected by the live API with 1007 "Request
    contains an invalid argument". It went unnoticed because the microphone
    never opened, so no audio was ever sent."""
    import main as M
    assert M._INPUT_MIME == f"audio/pcm;rate={M.SEND_SAMPLE_RATE}"


def test_the_callback_sends_the_declared_mime():
    import main as M
    src = inspect.getsource(M.JarvisLive._listen_audio)
    assert '"mime_type": "audio/pcm"' not in src, "hardcoded mime without a rate"
    assert "_INPUT_MIME" in src


def test_resampler_accepts_the_array_portaudio_hands_over():
    """The callback receives a 2-D numpy array; `not array` raises, which
    killed the callback on every block."""
    import numpy as np
    import main as M
    block = np.zeros((1024, 1), dtype=np.int16)
    out = M._resample_pcm16(block, 44100, 16000)
    assert isinstance(out, bytes)
    assert 0 < len(out) // 2 < 1024


def test_resampler_handles_degenerate_inputs():
    import numpy as np
    import main as M
    assert M._resample_pcm16(None, 44100, 16000) == b""
    assert M._resample_pcm16(np.array([], dtype=np.int16), 44100, 16000) == b""
    block = np.zeros((256, 1), dtype=np.int16)
    assert M._resample_pcm16(block, 44100, 44100) == block.tobytes()


def test_audio_rms_is_module_level_and_handles_the_callback_array():
    import numpy as np
    import main as M
    assert hasattr(M, "_audio_rms"), "the level meter must be testable"
    assert M._audio_rms(None) == 0.0
    assert M._audio_rms(np.zeros((1024, 1), dtype=np.int16)) == 0.0
    loud = (np.sin(np.arange(1024) / 10) * 20000).astype(np.int16).reshape(-1, 1)
    assert 0.3 < M._audio_rms(loud) < 0.7


def test_listen_audio_calls_the_level_meter_that_exists():
    """Lifting _rms to module level replaced the *first* call site, which was
    the in-flight local-voice function, leaving _listen_audio calling a
    closure that no longer existed. The mic callback then died with a NameError
    on every block -- so the function body is checked by name, not by eye."""
    import ast
    import main as M
    src = inspect.getsource(M.JarvisLive._listen_audio)
    tree = ast.parse(textwrap.dedent(src))
    called = {n.func.id for n in ast.walk(tree)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert "_audio_rms" in called, "_listen_audio does not call _audio_rms"
    assert "_rms" not in called, "_listen_audio still calls the removed _rms"
    assert hasattr(M, "_rms") is False, "_rms should no longer exist at all"
