"""
Regression tests for the self-echo loop.

Jarvis was answering himself: the microphone picked up his own playback, the
server transcribed it as a user turn, and he replied again. In a live run
that escalated into saving memories about his own reasoning, searching the
web for the operator's location, and reorganising Desktop and Downloads with
nobody speaking.

The guards are:

  * the mic gate is a deadline, not a boolean, so it survives turn_complete
    arriving before the last audio chunk and momentary gaps in the queue;
  * every chunk written to the speaker pushes that deadline forward;
  * Edge TTS (a second audio path that never touched the flag) brackets its
    own playback with the same gate;
  * input transcription that matches our recent output is discarded.
"""

from __future__ import annotations

import asyncio
import threading
import time

import pytest

pytest.importorskip("PyQt6")

import main as jarvis_main
import ui as jarvis_ui


def _bare_assistant():
    """A JarvisLive built without running __init__.

    Every method exercised here is pure bookkeeping over _is_speaking,
    _speaking_until and the recent-speech buffer, so the real constructor --
    which owns audio devices, a tray icon and threads -- would only make
    these tests slow and hang-prone.
    """
    a = jarvis_main.JarvisLive.__new__(jarvis_main.JarvisLive)
    a._speaking_lock = threading.Lock()
    a._is_speaking = False
    a._speaking_until = 0.0
    a._echo_guard_ms = 700
    a._recent_jarvis_speech = jarvis_main.deque(maxlen=6)
    a._echo_drops = 0
    a._watchdog_started = False
    a._user_turn_active = False
    a._last_user_text = ""
    a._blocked_tool_calls = 0
    a.audio_in_queue = asyncio.Queue()

    class _NullUI:
        muted = False

        def set_state(self, *_a, **_k):
            pass

    a.ui = _NullUI()
    return a


@pytest.fixture()
def assistant():
    return _bare_assistant()


# ---------------------------------------------------------------- echo text
def test_own_speech_is_recognised_as_echo(assistant):
    assistant._recent_jarvis_speech.append(
        "the weather in Rawalpindi today is sunny and warm"
    )
    assert assistant._looks_like_echo(
        "the weather in Rawalpindi today is sunny and warm"
    )


def test_partial_overlap_of_own_speech_is_echo(assistant):
    assistant._recent_jarvis_speech.append(
        "sure sir, opening the weather report for rawalpindi right now"
    )
    assert assistant._looks_like_echo(
        "opening the weather report for rawalpindi"
    )


def test_real_user_request_is_not_treated_as_echo(assistant):
    assistant._recent_jarvis_speech.append(
        "the weather in Rawalpindi today is sunny and warm"
    )
    assert not assistant._looks_like_echo("please download this youtube video")


def test_transcript_arriving_while_speaking_is_echo(assistant):
    assistant.set_speaking(True)
    assert assistant._looks_like_echo("anything at all")
    assistant.set_speaking(False, force=True)


def test_short_fillers_are_never_echo(assistant):
    # a one-word fragment matching nothing must not be swallowed
    assistant._recent_jarvis_speech.append("okay")
    assert not assistant._looks_like_echo("yes")


# ------------------------------------------------------------------ mic gate
def test_gate_survives_turn_complete_with_audio_queued(assistant):
    """turn_complete used to hard-clear the flag mid-playback."""
    assistant.set_speaking(True)
    assistant.audio_in_queue.put_nowait(b"chunk")
    assistant.set_speaking(False)              # turn_complete
    assert assistant._is_speaking_now()


def test_gate_survives_the_tail_after_the_last_chunk(assistant):
    assistant.set_speaking(True)
    assistant.audio_in_queue.put_nowait(b"chunk")
    assistant.set_speaking(False)
    assistant.audio_in_queue.get_nowait()       # audio finished writing
    assistant.set_speaking(False)
    assistant._expire_speaking_gate()
    assert assistant._is_speaking_now(), "released before the room went quiet"


def test_gate_is_held_across_individual_chunks(assistant):
    assistant.set_speaking(True)
    for _ in range(5):
        assistant.note_audio_played()
    assistant._expire_speaking_gate()
    assert assistant._is_speaking_now()


def test_gate_eventually_releases(assistant):
    assistant.set_speaking(True)
    assistant._speaking_until = time.monotonic() - 1.0
    assistant._expire_speaking_gate()
    assert not assistant._is_speaking_now()


def test_gate_holds_while_more_audio_arrives(assistant):
    assistant.set_speaking(True)
    assistant._speaking_until = time.monotonic() - 1.0     # pretend tail lapsed
    assistant.audio_in_queue.put_nowait(b"more")           # but audio remains
    assistant._expire_speaking_gate()
    assert assistant._is_speaking_now()


def test_force_releases_immediately(assistant):
    """Aborting playback must not wait out the tail."""
    assistant.set_speaking(True)
    assistant.set_speaking(False, force=True)
    assert not assistant._is_speaking_now()


def test_note_audio_played_rearms_the_gate(assistant):
    assistant.set_speaking(True)
    assistant._speaking_until = time.monotonic() - 1.0
    assistant.note_audio_played()
    assistant._expire_speaking_gate()
    assert assistant._is_speaking_now()


# ------------------------------------------------------------ Edge TTS hooks
def test_speech_hooks_are_installed():
    from actions.attention_monitor import (
        set_speech_hooks, _speaking_hook, _just_spoke_hook,
    )
    events = []
    try:
        set_speech_hooks(lambda on: events.append(("gate", on)),
                         lambda t: events.append(("spoke", t)))
        from actions import attention_monitor as am
        assert am._speaking_hook is not None
        assert am._just_spoke_hook is not None
    finally:
        set_speech_hooks(None, None)


# --------------------------------------------------------------- tool gate
# Jarvis must only act on something the operator actually asked for. The live
# model sometimes opens a turn by itself, and acting on that produced invented
# memories plus unsolicited file tidying.
def test_tool_gate_closed_without_a_user_turn(assistant):
    assert not assistant._tool_gate_open()


def test_tool_gate_opens_on_a_real_request(assistant):
    assistant._mark_user_turn("download this video")
    assert assistant._tool_gate_open()


def test_tool_gate_closes_when_the_turn_ends(assistant):
    assistant._mark_user_turn("hello")
    assistant._close_user_turn()
    assert not assistant._tool_gate_open()


def test_blank_input_does_not_open_the_tool_gate(assistant):
    assistant._mark_user_turn("   \n  ")
    assert not assistant._tool_gate_open()


def test_tool_gate_reopens_for_a_later_request(assistant):
    assistant._mark_user_turn("first")
    assistant._close_user_turn()
    assistant._mark_user_turn("second")
    assert assistant._tool_gate_open()
    assert assistant._last_user_text == "second"
