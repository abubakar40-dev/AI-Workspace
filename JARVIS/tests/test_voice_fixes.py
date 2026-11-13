"""
Tests for the voice fixes.

Three separate faults, all of which made the assistant sound wrong:

* Playback went to the laptop's built-in codec while the desktop was actually
  playing to a Bluetooth headset, so the live voice was inaudible and only the
  Edge TTS briefing -- which goes through PipeWire's default sink -- was heard.
* The full executive briefing was spoken on every start, so weather,
  temperature and PC detail came unprompted every time.
* There was no greeting at all on a fresh start.
"""

from __future__ import annotations

import ast
import inspect
import textwrap

import pytest

import main as M


# ---------------------------------------------------------------------------
# 1. Playback must follow the desktop's real sink
# ---------------------------------------------------------------------------
def test_output_prefers_a_routing_node_not_concrete_hardware():
    """A Bluetooth headset was connected, so the default sink was bluez_*. A
    concrete alsa_output device played into the laptop speaker instead."""
    cands = M._audio_candidates("output")
    assert cands, "no output candidates"
    first = M._audio_devices()[cands[0]]["name"]
    assert M._is_aggregate(first), (
        f"playback chose {first!r}; it must follow the desktop's active sink")


def test_default_sink_is_read_from_the_desktop():
    src = inspect.getsource(M._default_sink_name)
    assert "pactl" in src and "get-default-sink" in src


def test_the_active_sink_is_tried_directly_too():
    src = inspect.getsource(M._audio_candidates)
    assert "_default_sink_name()" in src, \
        "the device that is the current sink must be a candidate"


def test_playback_never_selects_a_loopback():
    devs = M._audio_devices()
    for idx in M._audio_candidates("output"):
        assert devs[idx]["max_output_channels"] > 0
        assert not M._is_loopback(devs[idx]["name"])


def test_capture_still_never_selects_a_loopback():
    """The self-echo bug: a speaker monitor as the microphone."""
    devs = M._audio_devices()
    for idx in M._audio_candidates("input"):
        assert devs[idx]["max_input_channels"] > 0
        assert not M._is_loopback(devs[idx]["name"]), \
            f"microphone candidate {devs[idx]['name']!r} is a loopback"


def test_aggregate_names_are_recognised():
    for name in ("default", "pipewire", "sysdefault", "Default"):
        assert M._is_aggregate(name), name
    for name in ("alsa_output.pci-0000_00_1f.3.analog-stereo", "HDA Intel PCH: HDMI 0"):
        assert not M._is_aggregate(name), name


def test_both_directions_have_candidates():
    assert M._audio_candidates("input")
    assert M._audio_candidates("output")


def test_stream_opener_walks_the_ranking():
    src = inspect.getsource(M._open_stream)
    assert "_audio_candidates(direction)" in src
    assert "failures.append" in src, "rejections must be reported, not swallowed"
    assert "could not open any" in src


def test_output_stream_opener_is_used_for_playback():
    src = inspect.getsource(M.JarvisLive._play_audio)
    assert "_open_output_stream(" in src
    assert "sd.RawOutputStream(" not in src, \
        "playback must go through the ranking, not a hardcoded stream"


# ---------------------------------------------------------------------------
# 2. No unprompted briefing
# ---------------------------------------------------------------------------
def test_boot_speaks_the_greeting_not_the_briefing():
    src = inspect.getsource(M.main)
    boot = src[src.index("start_runner()\n    # A short"):] if \
        "start_runner()\n    # A short" in src else src
    assert "_speak_boot_greeting" in boot, "boot must greet"
    assert "_speak_daily_briefing" not in boot, \
        "the executive briefing must not be spoken on every start"


def test_the_greeting_is_short_and_carries_no_telemetry():
    text = M._boot_greeting()
    lowered = text.lower()
    for banned in ("cpu", "memory", "disk", "package", "°c", "uptime",
                   "weather", "overcast"):
        assert banned not in lowered, f"the greeting leaked {banned!r}: {text!r}"
    assert len(text) < 220, f"the greeting is too long: {text!r}"


def test_the_greeting_reports_the_real_agent_count():
    import agent_runtime as AR
    AR.start()
    total = AR.registry_stats()["total"]
    text = M._boot_greeting()
    assert f"{total} sub agent" in text, \
        f"expected the real count ({total}) in {text!r}"


def test_the_greeting_says_jarvis_is_online():
    text = M._boot_greeting().lower()
    assert "jarvis is online" in text
    assert "on duty" in text


def test_the_greeting_is_time_appropriate():
    text = M._boot_greeting()
    assert any(part in text for part in ("Good morning", "Good afternoon",
                                         "Good evening"))


def test_the_briefing_still_has_the_detail():
    """It is only *not* automatic any more."""
    text = M._executive_briefing_text()
    assert "CPU" in text and "memory" in text
    assert "System:" in text


def test_the_briefing_button_still_speaks_the_briefing():
    src = inspect.getsource(M.JarvisLive.__init__)
    block = src[src.index("on_briefing"):]
    block = block[:block.index("self._last_activity")]
    assert "_speak_daily_briefing" in block, \
        "the Executive Briefing button must still produce the full briefing"


def test_the_briefing_is_reachable_only_on_demand():
    """Exactly one caller: the button callback."""
    callers = [ln for ln in inspect.getsource(M).splitlines()
               if "_speak_daily_briefing" in ln and "def " not in ln]
    assert len(callers) == 1, f"the briefing is spoken from {len(callers)} places"


def test_the_prompt_forbids_volunteering_telemetry():
    prompt = (M.BASE_DIR / "core" / "prompt.txt").read_text(encoding="utf-8").lower()
    assert "only speak about weather" in prompt
    assert "do not volunteer system statistics" in prompt
    assert "executive briefing" in prompt


def test_greeting_and_briefing_are_distinct_functions():
    assert M._boot_greeting is not M._executive_briefing_text
    assert M._speak_boot_greeting is not M._speak_daily_briefing
    assert "_speak_boot_greeting" not in inspect.getsource(M._speak_daily_briefing)


def test_greeting_uses_a_local_datetime_import():
    """It raised NameError on datetime before the import was added."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(M._boot_greeting)))
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    imported = {a.name for n in ast.walk(tree)
                if isinstance(n, ast.ImportFrom) for a in n.names}
    assert "datetime" in imported, "datetime must be imported locally"


# ---------------------------------------------------------------------------
# 3. One writer on the live websocket
# ---------------------------------------------------------------------------
def test_every_session_write_goes_through_the_lock():
    """Concurrent websocket writes interleave frames and the server closes with
    1007 "invalid frame payload data". The audio task writes ~16 times a
    second, so a tool response landing mid-stream killed the session."""
    src = inspect.getsource(M)
    direct = [ln.strip() for ln in src.splitlines()
              if "self.session.send_" in ln and "_session_write" not in ln]
    assert not direct, f"unsynchronised session writes: {direct}"


def test_the_write_helper_takes_the_lock():
    src = inspect.getsource(M.JarvisLive._session_write)
    assert "async with self._ws_lock" in src
    assert "getattr(self.session, method)" in src


def test_the_lock_exists_before_the_session_does():
    src = inspect.getsource(M.JarvisLive.__init__)
    assert "_ws_lock" in src and "asyncio.Lock()" in src


def test_the_audio_writer_uses_the_lock():
    src = inspect.getsource(M.JarvisLive._send_realtime)
    assert '_session_write("send_realtime_input"' in src


def test_the_tool_responder_uses_the_lock():
    src = inspect.getsource(M.JarvisLive._receive_audio)
    assert '_session_write(\n                            "send_tool_response"' in src \
        or '"send_tool_response"' in src


def test_typed_commands_use_the_lock():
    src = inspect.getsource(M)
    assert src.count("_session_write(") >= 4, \
        "audio, tool responses and both text paths must all be locked"
