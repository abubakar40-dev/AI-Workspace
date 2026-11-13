"""
Tests for audio device resolution.

The microphone used to be pinned to PortAudio index 10. Under PipeWire the
index table is rebuilt on every session, so index 10 could be the microphone
on one boot and a speaker monitor on the next. When it landed on a monitor,
the "microphone" captured Jarvis's own speaker output: a guaranteed echo
loop that made him answer himself, invent memories and reorganise the
operator's Desktop and Downloads with nobody speaking.

These tests pin the resolution rules against synthetic device tables so the
behaviour does not depend on the machine they run on.
"""

from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")

import main as jarvis_main


def _dev(name: str, inp: int = 0, out: int = 0, rate: int = 48000) -> dict:
    return {
        "name": name,
        "max_input_channels": inp,
        "max_output_channels": out,
        "default_samplerate": rate,
    }


# A table shaped like a real PipeWire machine: speakers, their monitors,
# the internal mic, and the aggregate nodes.
TABLE = [
    _dev("HDA Intel PCH: ALC3246 Analog (hw:0,0)", inp=2),
    _dev("HDA Intel PCH: HDMI 0 (hw:0,3)", out=8),
    _dev("sysdefault", inp=128),
    _dev("pipewire", inp=128, out=128),
    _dev("default", inp=128, out=128),
    _dev("Default Sink", out=32),
    _dev("Default Source", inp=32),
    _dev("alsa_output.pci-0000_00_1f.3.analog-stereo", out=2),
    _dev("alsa_output.pci-0000_00_1f.3.analog-stereo.monitor", inp=2),
    _dev("alsa_input.pci-0000_00_1f.3.analog-stereo", inp=2),
]


@pytest.fixture()
def table(monkeypatch):
    monkeypatch.setattr(jarvis_main, "_audio_devices", lambda: list(TABLE))
    monkeypatch.setattr(jarvis_main.os, "environ", dict(jarvis_main.os.environ))
    return TABLE


# ------------------------------------------------------------------ loopback
def test_speaker_monitor_is_recognised_as_a_loopback():
    assert jarvis_main._is_loopback(
        "alsa_output.pci-0000_00_1f.3.analog-stereo.monitor")


def test_only_monitors_are_loopbacks():
    """An earlier version treated every ``alsa_output*`` name as a loopback,
    which quietly removed the real analog speaker from the output fallback."""
    assert jarvis_main._is_loopback(
        "alsa_output.pci-0000_00_1f.3.analog-stereo.monitor")
    assert jarvis_main._is_loopback(
        "bluez_output.41:42:FF:0D:11:00.monitor")
    assert not jarvis_main._is_loopback(
        "alsa_output.pci-0000_00_1f.3.analog-stereo")
    assert not jarvis_main._is_loopback("bluez_output.41:42:FF:0D:11:00")
    # and a speaker reports no capture channels, so it can never be the mic
    table_speaker = _dev("alsa_output.pci-0000_00_1f.3.analog-stereo", out=2)
    assert table_speaker["max_input_channels"] == 0


def test_a_real_microphone_is_not_a_loopback():
    assert not jarvis_main._is_loopback(
        "alsa_input.pci-0000_00_1f.3.analog-stereo")
    assert not jarvis_main._is_loopback("HDA Intel PCH: ALC3246 Analog (hw:0,0)")


def test_aggregate_nodes_are_not_loopbacks():
    assert not jarvis_main._is_loopback("default")
    assert not jarvis_main._is_loopback("pipewire")
    assert not jarvis_main._is_loopback("sysdefault")


# ---------------------------------------------------------------- mic choice
def test_microphone_is_never_a_speaker(table, monkeypatch):
    chosen = jarvis_main._resolve_audio_device("input")
    assert chosen is not None
    name = table[chosen]["name"]
    assert table[chosen]["max_input_channels"] > 0
    assert not jarvis_main._is_loopback(name), f"chose a loopback: {name}"


def test_microphone_is_not_the_old_pinned_index_when_that_is_a_speaker(table):
    """The historical failure: index 10 was a 0-input speaker."""
    speaker = next(i for i, d in enumerate(table)
                   if d["name"].startswith("alsa_output.pci") and ".monitor" not in d["name"])
    assert table[speaker]["max_input_channels"] == 0
    assert jarvis_main._resolve_audio_device("input") != speaker


def test_microphone_prefers_a_real_input_node(table, monkeypatch):
    # no usable system default, so the hardware input must win
    monkeypatch.setattr(jarvis_main.sd, "default", type(
        "D", (), {"device": (None, None)}))
    chosen = jarvis_main._resolve_audio_device("input")
    assert chosen is not None
    assert not jarvis_main._is_loopback(table[chosen]["name"])


def test_system_default_microphone_is_accepted(table, monkeypatch):
    default_in = next(i for i, d in enumerate(table) if d["name"] == "default")
    monkeypatch.setattr(jarvis_main.sd, "default", type(
        "D", (), {"device": (default_in, default_in)}))
    assert jarvis_main._resolve_audio_device("input") == default_in


def test_monitor_is_rejected_even_when_it_is_the_default(table, monkeypatch):
    monitor = next(i for i, d in enumerate(table) if ".monitor" in d["name"])
    monkeypatch.setattr(jarvis_main.sd, "default", type(
        "D", (), {"device": (monitor, None)}))
    chosen = jarvis_main._resolve_audio_device("input")
    assert chosen != monitor, "a speaker monitor was accepted as a microphone"


# ------------------------------------------------------------ speaker choice
def test_speaker_is_never_an_input_only_node(table):
    chosen = jarvis_main._resolve_audio_device("output")
    assert chosen is not None
    assert table[chosen]["max_output_channels"] > 0


def test_speaker_prefers_a_routing_node_over_hardware(table, monkeypatch):
    """Playback must follow the desktop's active sink.

    This used to prefer a concrete device, on the theory that riding an
    aggregate node let PipeWire renegotiate the format. That is exactly what
    made the live voice inaudible: with a Bluetooth headset connected the
    default sink was bluez_output..., and a concrete alsa_output device played
    into the laptop's built-in speaker instead. A routing node follows the
    active sink, so it has to come first.
    """
    monkeypatch.setattr(jarvis_main.sd, "default", type(
        "D", (), {"device": (None, None)}))
    chosen = jarvis_main._resolve_audio_device("output")
    assert chosen is not None
    name = table[chosen]["name"]
    assert jarvis_main._is_aggregate(name), \
        f"playback chose {name!r}; it must follow the active sink"
    assert name == "default", "the Pulse/PipeWire default is preferred"


def test_hardware_is_still_reachable_as_a_fallback(table, monkeypatch):
    """The concrete device must stay in the ranking, just not first."""
    cands = jarvis_main._audio_candidates("output")
    names = [table[i]["name"] for i in cands]
    assert any(jarvis_main._looks_like_output(n) for n in names), \
        "no concrete output device left in the fallback list"
    assert "alsa_output.pci-0000_00_1f.3.analog-stereo" in names


def test_the_active_sink_is_ranked_before_hardware(table, monkeypatch):
    monkeypatch.setattr(jarvis_main, "_default_sink_name",
                        lambda: "bluez_output.41:42:FF:0D:11:00")
    table.append(_dev("bluez_output.41:42:FF:0D:11:00", out=2))
    cands = jarvis_main._audio_candidates("output")
    names = [table[i]["name"] for i in cands]
    bt = names.index("bluez_output.41:42:FF:0D:11:00")
    hw = names.index("alsa_output.pci-0000_00_1f.3.analog-stereo")
    assert bt < hw, "the device the desktop is playing to must be tried first"


def test_no_devices_yields_none(monkeypatch):
    monkeypatch.setattr(jarvis_main, "_audio_devices", lambda: [])
    assert jarvis_main._resolve_audio_device("input") is None
    assert jarvis_main._resolve_audio_device("output") is None


def test_no_input_devices_yields_none(monkeypatch):
    monkeypatch.setattr(jarvis_main, "_audio_devices",
                        lambda: [_dev("headphones", out=2)])
    assert jarvis_main._resolve_audio_device("input") is None
