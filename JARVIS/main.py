from collections import deque
import asyncio
import threading
import json
import re
import shutil
import socket
import subprocess
import sys
import time
import random
import traceback
import os
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    import numpy as _np
except Exception:                                    # pragma: no cover
    _np = None
try:
    import sounddevice as sd
except Exception:                                    # pragma: no cover
    sd = None


# ---------------------------------------------------------------------------
# Audio device resolution
# ---------------------------------------------------------------------------
# PortAudio device *indices* are not stable under PipeWire: the same number
# can be the microphone on one boot and a speaker monitor on the next, and
# PipeWire will happily hand back a loopback node. Pinning the microphone to
# a fixed index therefore captured our own speaker output, which is a
# guaranteed self-echo -- Jarvis heard his own voice, replied, and then
# tidied the operator's files with nobody speaking.
#
# So resolve by role, and never accept a loopback.
def _audio_devices() -> list:
    try:
        return list(sd.query_devices())
    except Exception:
        return []


def _is_loopback(name: str) -> bool:
    """True only for a device that plays back what it captures.

    A monitor is the danger: capturing one feeds the assistant its own voice.
    Only the "monitor"/"loopback" naming marks one -- a plain
    ``alsa_output.pci-...analog-stereo`` is a real speaker and must stay in the
    output ranking, and it is already excluded from input because it reports no
    capture channels at all.
    """
    n = (name or "").lower()
    return "monitor" in n or "loopback" in n or "loopback" in n.replace("-", "")


def _looks_like_input(name: str) -> bool:
    n = (name or "").lower()
    return n.startswith("alsa_input") or n.startswith("hw:") or "input" in n


def _looks_like_output(name: str) -> bool:
    """A *specific* speaker, not an aggregate node.

    "Default Sink" and friends are routing nodes: PipeWire may renegotiate
    the format underneath them, which crashed PortAudio at the C level. So
    only a concrete alsa_output/hw device counts as hardware here.
    """
    n = (name or "").lower()
    # PortAudio renders hardware nodes either as "hw:0,0" or, when the codec
    # name is known, as "HDA Intel PCH: ... (hw:0,3)".
    return (n.startswith("alsa_output") or n.startswith("hw:")
            or "(hw:" in n)


def _is_aggregate(name: str) -> bool:
    """A PipeWire/Pulse routing node rather than a concrete device.

    These follow whatever sink or source the system is actually using, which
    is why playback has to go through one: with a Bluetooth headset connected,
    a concrete hardware device plays into the laptop's built-in speaker and the
    user hears nothing.
    """
    return (name or "").strip().lower() in ("default", "pipewire", "sysdefault")


def _default_sink_name() -> str:
    """The sink the desktop is really playing to, if we can ask."""
    try:
        import subprocess
        out = subprocess.run(["pactl", "get-default-sink"], capture_output=True,
                             text=True, timeout=1.5)
        name = (out.stdout or "").strip()
        return name if out.returncode == 0 else ""
    except Exception:
        return ""


def _audio_candidates(direction: str) -> list:
    """Ordered device candidates for 'input' or 'output'.

    Playback prefers a routing node so it follows the active sink (Bluetooth
    headsets included) and only then falls back to concrete hardware. Capture
    never accepts a monitor, which is what made Jarvis hear his own voice.
    """
    devs = _audio_devices()
    if not devs:
        return []
    want = ("max_input_channels" if direction == "input"
            else "max_output_channels")
    usable = [(i, d) for i, d in enumerate(devs) if d.get(want, 0) > 0]
    if not usable:
        return []

    def out_names():
        return [d["name"] for i, d in usable
                if _looks_like_output(d["name"]) and not _is_loopback(d["name"])]

    ordered: list = []
    env = os.environ.get("JARVIS_MIC_DEVICE" if direction == "input"
                         else "JARVIS_SPEAKER_DEVICE", "").strip()
    if env:
        try:
            idx = int(env)
            if 0 <= idx < len(devs):
                key = ("max_input_channels" if direction == "input"
                       else "max_output_channels")
                if (devs[idx].get(key, 0) > 0
                        and not (direction == "input"
                                 and _is_loopback(devs[idx]["name"]))):
                    ordered.append(idx)
        except (TypeError, ValueError):
            print(f"[JARVIS] bad {direction} device override {env!r}")

    if direction == "output":
        # 1. the routing node, so audio follows the desktop's real sink.
        #    "default" is the Pulse/PipeWire default and is preferred over
        #    "sysdefault"/"pipewire", which are equivalent but ordered by name.
        for wanted in ("default", "pipewire", "sysdefault"):
            for i, d in usable:
                if d["name"].strip().lower() == wanted:
                    ordered.append(i)
        # 2. the device that *is* the current default sink
        sink = _default_sink_name()
        if sink:
            for i, d in usable:
                if d["name"].strip() == sink:
                    ordered.append(i)
        # 3. concrete hardware
        ordered += [i for i, d in usable
                    if _looks_like_output(d["name"])
                    and not _is_loopback(d["name"])]
    else:
        # 1. PortAudio's own default input, never a monitor
        try:
            default_idx = sd.default.device[0]
        except Exception:
            default_idx = None
        for i, d in usable:
            if i == default_idx and not _is_loopback(d["name"]):
                ordered.append(i)
        # 2. a concrete hardware microphone
        predicate = _looks_like_input
        ordered += [i for i, d in usable
                    if predicate(d["name"]) and not _is_loopback(d["name"])]
        # 3. a routing node, which follows the default source
        for wanted in ("default", "pipewire", "sysdefault"):
            ordered += [i for i, d in usable
                        if d["name"].strip().lower() == wanted]

    # 4. anything left that is not a monitor
    ordered += [i for i, d in usable if not _is_loopback(d["name"])]

    seen, out = set(), []
    for i in ordered:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def _resolve_audio_device(direction: str):
    """The preferred device for a direction, or None to let PortAudio choose."""
    candidates = _audio_candidates(direction)
    return candidates[0] if candidates else None


def _describe_audio_devices() -> None:
    """Log the real choice and the ranking, so a wrong device is obvious."""
    devs = _audio_devices()
    if not devs:
        return
    for direction, env in (("input", "JARVIS_MIC_DEVICE"),
                           ("output", "JARVIS_SPEAKER_DEVICE")):
        chosen = _resolve_audio_device(direction)
        name = (devs[chosen]["name"]
                if chosen is not None and 0 <= chosen < len(devs) else "auto")
        try:
            rate = _native_rate(chosen)
        except Exception:
            rate = 0
        print(f"[JARVIS] AUDIO {direction:6s} -> {chosen} ({name}) @{rate or '?'} Hz")
    try:
        print(f"[JARVIS] AUDIO desktop sink: {_default_sink_name() or 'unknown'}")
    except Exception:
        pass
    print("[JARVIS] AUDIO override with JARVIS_MIC_DEVICE / JARVIS_SPEAKER_DEVICE")


_MIC_DEVICE = _resolve_audio_device("input") if sd is not None else None
def _native_rate(idx) -> int:
    """Sample rate a device natively supports, else 0."""
    try:
        devs = _audio_devices()
        if idx is not None and 0 <= idx < len(devs):
            return int(devs[idx].get("default_samplerate") or 0)
    except Exception:
        pass
    return 0


def _resample_pcm16(block, src_rate: int, dst_rate: int) -> bytes:
    """Resample mono int16 PCM.

    Hardware runs at its own rate (44.1/48 kHz) while Gemini wants 16 kHz in
    and 24 kHz out. Handing PortAudio a rate the codec refuses fails the
    stream, and routing through the aggregate PipeWire node to get
    resampling is what made the "microphone" resolve to a speaker monitor.
    So we do the conversion ourselves and always talk to real hardware.

    ``block`` may be bytes, a memoryview or the numpy array PortAudio hands
    the callback, so emptiness is checked by size and never by truthiness --
    ``not array`` raises for a multi-element array, which killed the callback
    on every single block.
    """
    if block is None or src_rate <= 0 or dst_rate <= 0 or src_rate == dst_rate:
        return b"" if block is None else bytes(block)
    if _np is not None and isinstance(block, _np.ndarray):
        arr = block.reshape(-1).astype(_np.int16, copy=False)
    else:
        arr = _np.frombuffer(bytes(block), dtype=_np.int16)
    if arr.size == 0:
        return b""
    if src_rate == dst_rate:
        return arr.tobytes()
    n_out = max(1, int(round(arr.size * dst_rate / src_rate)))
    x_old = _np.arange(arr.size, dtype=_np.float64)
    x_new = _np.linspace(0.0, arr.size - 1.0, n_out, dtype=_np.float64)
    out = _np.interp(x_new, x_old, arr.astype(_np.float64))
    return out.astype(_np.int16).tobytes()


def _audio_rms(block) -> float:
    """Normalised RMS of an int16 block, 0.0 to 1.0.

    Runs on PortAudio's real-time callback, so it stays cheap: numpy when
    available, otherwise a strided sample. A full Python loop over every
    1024-sample block was avoidable work on the one thread that must never be
    late. Module level so it can be tested and reused outside the callback.
    """
    if block is None:
        return 0.0
    try:
        if _np is not None:
            if isinstance(block, _np.ndarray):
                arr = block.reshape(-1).astype(_np.int16, copy=False)
            else:
                arr = _np.frombuffer(bytes(block), dtype=_np.int16)
            if arr.size:
                return float(_np.sqrt(_np.mean(arr.astype(_np.float64) ** 2))
                             / 32768.0)
            return 0.0
        total = 0
        n = 0
        for v in memoryview(block).cast("h")[::4]:       # strided
            total += v * v
            n += 1
        return (total / n) ** 0.5 / 32768.0 if n else 0.0
    except Exception:
        return 0.0


def _open_stream(kind: str, samplerate: int, channels: int, dtype: str,
                 blocksize: int, callback=None):
    """Open audio, walking the ranked device candidates until one works.

    Which device is usable changes with whatever PipeWire and Bluetooth are
    doing that minute, and a codec that refuses the requested rate fails the
    stream outright, so this tries each candidate at its own native rate and
    then at the rate we want. Every rejection is reported, because a silent
    "could not open" is impossible to diagnose.
    """
    if sd is None:
        raise RuntimeError("sounddevice is unavailable")
    direction = "input" if kind == "input" else "output"
    devs = _audio_devices()
    attempts: list[tuple] = []
    for dev in _audio_candidates(direction):
        rate = int(devs[dev].get("default_samplerate") or 0) if 0 <= dev < len(devs) else 0
        if rate > 0:
            attempts.append((dev, rate))
        attempts.append((dev, samplerate))
    attempts.append((None, samplerate))

    seen, failures = set(), []
    for dev, rate in attempts:
        if rate <= 0 or (dev, rate) in seen:
            continue
        seen.add((dev, rate))
        name = ("auto" if dev is None
                else devs[dev]["name"] if 0 <= dev < len(devs) else f"dev {dev}")
        try:
            if kind == "input":
                st = sd.InputStream(device=dev, samplerate=rate, channels=channels,
                                    dtype=dtype, blocksize=blocksize,
                                    callback=callback)
            else:
                st = sd.RawOutputStream(device=dev, samplerate=rate,
                                        channels=channels, dtype=dtype,
                                        blocksize=blocksize)
            return st, rate, name
        except Exception as exc:
            failures.append(f"{name} @ {rate}: {exc}")
    raise RuntimeError(f"could not open any {kind} -- " + " | ".join(failures[:4]))


def _open_input_stream(samplerate: int, channels: int, dtype: str,
                       blocksize: int, callback=None):
    stream, rate, _name = _open_stream("input", samplerate, channels, dtype,
                                      blocksize, callback)
    return stream, rate


def _open_output_stream(samplerate: int, channels: int, dtype: str,
                        blocksize: int):
    stream, rate, _name = _open_stream("output", samplerate, channels, dtype,
                                       blocksize)
    return stream, rate


def _audio_rms(block) -> float:
    """Normalised RMS of an int16 block, 0.0 to 1.0.

    Runs on PortAudio's real-time callback, so it stays cheap: numpy when
    available, otherwise a strided sample. A full Python loop over every
    1024-sample block was avoidable work on the one thread that must never be
    late. Module level so it can be tested and reused outside the callback.
    """
    if block is None:
        return 0.0
    try:
        if _np is not None:
            if isinstance(block, _np.ndarray):
                arr = block.reshape(-1).astype(_np.int16, copy=False)
            else:
                arr = _np.frombuffer(bytes(block), dtype=_np.int16)
            if arr.size:
                return float(_np.sqrt(_np.mean(arr.astype(_np.float64) ** 2))
                             / 32768.0)
            return 0.0
        total = 0
        n = 0
        for v in memoryview(block).cast("h")[::4]:       # strided
            total += v * v
            n += 1
        return (total / n) ** 0.5 / 32768.0 if n else 0.0
    except Exception:
        return 0.0


def _open_input_stream(samplerate: int, channels: int, dtype: str,
                       blocksize: int, callback=None):
    """Open the microphone, trying real candidates until one actually works.

    A codec that refuses the requested rate fails the stream outright, and
    which device is usable varies with whatever PipeWire and Bluetooth are
    doing that minute, so this walks a list instead of trusting one choice:
    the resolved device at its native rate, then at the rate we want, then
    PortAudio's own default, then any other non-loopback input as a last
    resort. Every rejection is printed, because a silent "could not open"
    is impossible to diagnose.
    """
    attempts: list[tuple] = []
    native = _native_rate(_MIC_DEVICE)
    if _MIC_DEVICE is not None and native:
        attempts.append((_MIC_DEVICE, native))
    if _MIC_DEVICE is not None:
        attempts.append((_MIC_DEVICE, samplerate))
    attempts.append((None, samplerate))

    # Last resort: anything with inputs that is not a monitor.
    devs = _audio_devices()
    for i, d in enumerate(devs):
        if d.get("max_input_channels", 0) > 0 and not _is_loopback(d["name"]):
            attempts.append((i, samplerate))
            rate = int(d.get("default_samplerate") or 0)
            if rate > 0:
                attempts.append((i, rate))

    seen = set()
    failures = []
    for dev, rate in attempts:
        if rate <= 0 or (dev, rate) in seen:
            continue
        seen.add((dev, rate))
        name = ("auto" if dev is None
                else devs[dev]["name"] if 0 <= dev < len(devs) else f"dev {dev}")
        try:
            st = sd.InputStream(device=dev, samplerate=rate, channels=channels,
                                dtype=dtype, blocksize=blocksize,
                                callback=callback)
            return st, rate
        except Exception as exc:
            failures.append(f"{name} @ {rate}: {exc}")
    raise RuntimeError("could not open any microphone input -- "
                       + " | ".join(failures[:4]))


def _open_output_stream(samplerate: int, channels: int, dtype: str, blocksize: int):
    """Open the speaker, same strategy as the microphone."""
    attempts = []
    native = _native_rate(_SPEAKER_DEVICE)
    if _SPEAKER_DEVICE is not None and native:
        attempts.append((_SPEAKER_DEVICE, native))
    if _SPEAKER_DEVICE is not None:
        attempts.append((_SPEAKER_DEVICE, samplerate))
    attempts.append((None, samplerate))
    attempts.append((_SPEAKER_DEVICE, samplerate))
    seen = set()
    for dev, rate in attempts:
        if rate <= 0 or (dev, rate) in seen:
            continue
        seen.add((dev, rate))
        try:
            st = sd.RawOutputStream(device=dev, samplerate=rate, channels=channels,
                                    dtype=dtype, blocksize=blocksize)
            return st, rate
        except Exception:
            continue
    raise RuntimeError("could not open any audio output")


_SPEAKER_DEVICE = _resolve_audio_device("output") if sd is not None else None

from google import genai
from google.genai import types
from ui import JarvisUI
from memory.memory_manager import (
    load_memory, update_memory, format_memory_for_prompt,
    should_extract_memory, extract_memory
)

from actions.file_processor import file_processor
from actions.flight_finder     import flight_finder
from actions.open_app          import open_app
from actions.weather_report    import weather_action
from actions.send_message      import send_message
from actions.reminder          import reminder
from actions.computer_settings import computer_settings

from actions.meeting_assistant import MeetingAssistant
from actions.youtube_video     import youtube_video
from actions.desktop           import desktop_control
from actions.browser_control   import browser_control
from actions.file_controller   import file_controller
from actions.website_builder   import website_builder
from actions.office_builder     import create_presentation, create_spreadsheet
from actions.docx_tools        import word_document
from actions.pdf_tools         import create_pdf
from PyQt6.QtCore import QTimer
from actions.web_search        import web_search as web_search_action
from actions.computer_control  import computer_control
from actions.game_updater      import game_updater
from actions.url_downloader    import url_downloader
from actions.attention_monitor import AttentionMonitor, speak_native, stop_native_speech, handle_call_action, read_event_preview
# from actions.daily_briefing import compile_daily_briefing
from or_client import client as openrouter_client
from ollama_client import client as ollama_client, OllamaUnavailable
from groq_client import client as groq_client
import nrouter_client
from connectivity import is_online
from workspace_store import store as workspace_store
from plugin_manager import PluginManager

try:
    from dashboard.server import DashboardServer
except Exception:
    DashboardServer = None


def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


BASE_DIR        = get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"
PROMPT_PATH     = BASE_DIR / "core" / "prompt.txt"
STARTUP_LOG     = Path(os.environ.get("LOCALAPPDATA", str(BASE_DIR))) / "Jarvis" / "startup.log"
LIVE_MODEL          = "gemini-3.1-flash-live-preview"
CHANNELS            = 1
SEND_SAMPLE_RATE    = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE          = 1024

# Local voice-activity floor, as a fraction of full-scale int16. Audio quieter
# than this never reaches the model. Without it, room noise was transcribed as
# turns and Jarvis answered requests nobody made -- searching the web, writing
# invented memories, tidying Desktop and Downloads.
#
# Measured cutoffs: room tone tops out near 0.0009, real speech starts around
# 0.004. The default sits between them. If Jarvis ever seems deaf, lower it:
#     JARVIS_RMS_FLOOR=0.0015 python main.py
try:
    _RMS_FLOOR = float(os.environ.get("JARVIS_RMS_FLOOR", "0.0025"))
except (TypeError, ValueError):
    _RMS_FLOOR = 0.0025
_RMS_FLOOR = max(0.0, min(0.5, _RMS_FLOOR))
# How far above the tracked noise floor a block must sit to be forwarded.
_RMS_MARGIN = 1.6

# How long the microphone stays closed after playback stops, so the tail of
# our own voice is never transcribed back in as the user.
_ECHO_GUARD_MS = 700

# The live API needs the sample rate in the mime type. Plain "audio/pcm" is
# rejected with 1007 "Request contains an invalid argument" -- which stayed
# hidden while the microphone never opened and no audio was ever sent.
_INPUT_MIME = f"audio/pcm;rate={SEND_SAMPLE_RATE}"
LIVE_CONNECT_TIMEOUT = 12

class _GoAwaySignal(Exception):
    """Raised when Gemini Live sends a GoAway; triggers a clean, non-penalized reconnect."""
    pass


def _get_api_key() -> str:
    with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["gemini_api_key"]


def _is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex((host, port)) == 0


def _startup_log(message: str) -> None:
    try:
        STARTUP_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(STARTUP_LOG, "a", encoding="utf-8") as f:
            f.write(message + "\n")
    except Exception:
        pass


def _ensure_desktop_shortcut() -> None:
    if os.name != "nt":
        return

    marker_path = BASE_DIR / "config" / ".desktop_shortcut_created"
    if marker_path.exists():
        return

    try:
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
            desktop_raw, _ = winreg.QueryValueEx(key, "Desktop")
            winreg.CloseKey(key)
            desktop_dir = Path(os.path.expandvars(desktop_raw))
        except Exception:
            desktop_dir = Path(os.path.expanduser("~")) / "Desktop"
            
        desktop_dir.mkdir(parents=True, exist_ok=True)
        shortcut_path = desktop_dir / "Jarvis.lnk"
        script_path = BASE_DIR / "main.py"
        icon_path = BASE_DIR / "assets" / "Jarvis_Logo.ico"

        if not icon_path.exists():
            icon_path = None

        python_exe = sys.executable
        if not python_exe:
            python_exe = shutil.which("python") or shutil.which("py") or "python"

        shortcut_target = python_exe
        shortcut_args = f'"{script_path}"'
        if getattr(sys, "frozen", False):
            shortcut_target = python_exe
            shortcut_args = ""

        powershell_exe = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell_exe is None:
            raise RuntimeError("PowerShell is not available")

        def _ps_escape(value: str) -> str:
            return value.replace("'", "''")

        icon_value = str(icon_path) if icon_path and icon_path.exists() else ""
        ps1_path = BASE_DIR / "config" / "create_desktop_shortcut.ps1"
        ps1_script = "\n".join([
            "$WshShell = New-Object -ComObject WScript.Shell",
            f"$Shortcut = $WshShell.CreateShortcut('{_ps_escape(str(shortcut_path))}')",
            f"$Shortcut.TargetPath = '{_ps_escape(shortcut_target)}'",
            f"$Shortcut.Arguments = '{_ps_escape(shortcut_args)}'",
            f"$Shortcut.WorkingDirectory = '{_ps_escape(str(BASE_DIR))}'",
            "$Shortcut.WindowStyle = 7",
            "$Shortcut.Description = 'Launch Jarvis'",
            f"if ('{_ps_escape(icon_value)}') {{ $Shortcut.IconLocation = '{_ps_escape(icon_value)},0' }}",
            "$Shortcut.Save()",
        ])
        ps1_path.write_text(ps1_script, encoding="utf-8")

        subprocess.run(
            [powershell_exe, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        marker_path.write_text("created", encoding="utf-8")
        _startup_log(f"desktop shortcut created at {shortcut_path}")
    except Exception as exc:
        _startup_log(f"desktop shortcut creation skipped: {exc}")


def _load_system_prompt() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except Exception:
        return (
            "You are Jarvis, a calm, direct, and professional AI assistant. "
            "Be concise, direct, and always use the provided tools to complete tasks. "
            "Never simulate or guess results — always call the appropriate tool. "
            "If the user asks to create, build, launch, or open a website, always use the selected workspace folder."
        )


def _executive_briefing_text() -> str:
    """Compose the briefing from real state. No network, so it is instant."""
    from datetime import datetime
    import command_panels as CP
    now = datetime.now()
    lines = [f"Good {('morning' if now.hour < 12 else 'afternoon' if now.hour < 17 else 'evening')}, "
             f"{now.strftime('%A %d %B')}."]
    try:
        host = (CP._sensors().get("host_summary") or {})
        bits = []
        if host.get("cpu_pct") is not None:
            bits.append(f"CPU {host['cpu_pct']:.0f}%")
        mem = host.get("mem") or {}
        if mem.get("percent") is not None:
            bits.append(f"memory {mem['percent']:.0f}%")
        disk = host.get("disk") or {}
        if disk.get("percent") is not None:
            bits.append(f"disk {disk['percent']:.0f}%")
        temp = (host.get("temp") or {}).get("celsius")
        if temp is not None:
            bits.append(f"package {temp}°C")
        if bits:
            lines.append("System: " + ", ".join(bits) + ".")
        if host.get("uptime"):
            lines.append(f"Up {host['uptime']}.")
    except Exception:
        pass
    try:
        rem = CP._reminders()
        lines.append(f"Reminders: {len(rem)} scheduled."
                     + (" Next: " + rem[0]["text"] if rem else ""))
    except Exception:
        pass
    try:
        facts = CP._memory_facts()
        lines.append(f"Memory: {sum(facts.values())} facts across "
                     f"{len(facts)} categories.")
    except Exception:
        pass
    try:
        convs = CP._conversations()
        if convs:
            lines.append(f"Last conversation: {convs[0].get('title', 'untitled')}.")
    except Exception:
        pass
    return " ".join(lines)


def _boot_greeting() -> str:
    """The short line spoken when JARVIS comes online.

    Deliberately *not* the executive briefing: weather, temperature and PC
    detail are only ever given when the operator asks for them or presses
    Executive Briefing. This says the system is up and who is on duty, using
    the real agent count rather than a fixed number.
    """
    from datetime import datetime

    try:
        import agent_runtime as AR
        AR.start()
        total = AR.registry_stats().get("total", 0)
    except Exception:
        total = 0

    hour = datetime.now().hour
    part = ("Good morning, sir." if hour < 12 else
            "Good afternoon, sir." if hour < 17 else
            "Good evening, sir.")
    if total:
        team = (f"{total} sub agents are on duty and waiting for your commands."
                if total > 1 else
                "1 sub agent is on duty and waiting for your commands.")
    else:
        team = "The agent team is not available right now."
    return f"{part} Jarvis is online. {team} How may I help?"


def _speak_boot_greeting(ui=None) -> None:
    """Announce that the system is up -- and nothing else."""
    try:
        text = _boot_greeting()
    except Exception as exc:
        text = f"Jarvis is online. Greeting unavailable: {exc}"
    if ui is not None:
        try:
            ui.push_feed(text, "System", "live", "ONLINE")
        except Exception:
            pass
    print(f"[Greeting] {text}")
    try:
        from actions.attention_monitor import speak_native
        threading.Thread(target=speak_native, args=(text,), daemon=True,
                         name="boot-greeting").start()
    except Exception:
        pass


def _speak_daily_briefing(ui=None) -> None:
    """Show the executive briefing in every surface that can carry it."""
    try:
        text = _executive_briefing_text()
    except Exception as exc:
        text = f"Could not assemble the briefing: {exc}"
    if ui is not None:
        for method, arg in (("push_feed", None), ("write_log", None)):
            try:
                if method == "push_feed":
                    ui.push_feed(text, "Executive briefing", "live", "BRIEF")
                else:
                    ui.write_log(f"Jarvis: {text}")
            except Exception:
                pass
        try:
            ui._to_chat("jarvis", text)
        except Exception:
            pass
    print(f"[Briefing] {text}")
    try:
        from actions.attention_monitor import speak_native
        threading.Thread(target=speak_native, args=(text,), daemon=True).start()
    except Exception:
        pass
    
def _extract_gemini_text(response) -> str:
    text_parts: list[str] = []
    try:
        for candidate in getattr(response, "candidates", []) or []:
            content = getattr(candidate, "content", None)
            if not content:
                continue
            for part in getattr(content, "parts", []) or []:
                part_text = getattr(part, "text", None)
                if part_text:
                    text_parts.append(part_text)
    except Exception:
        pass

    text = "".join(text_parts).strip()
    if text:
        return text

    try:
        return (getattr(response, "text", "") or "").strip()
    except Exception:
        return ""


def _gemini_text_reply(prompt: str) -> str:
    client = genai.Client(
        api_key=_get_api_key(),
        http_options={"api_version": "v1beta"},
    )
    system_prompt = (
        "You are Jarvis, a concise, helpful desktop assistant. "
        "Reply naturally and briefly. Do not mention internal implementation details."
    )
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=f"{system_prompt}\n\nUser: {prompt}",
        config={"temperature": 0.6, "max_output_tokens": 768},
    )
    return _extract_gemini_text(response)


def _looks_like_code_request(text: str) -> bool:
    low = (text or "").lower()
    code_words = (
        "build", "create", "write", "implement", "code", "python", "app",
        "module", "function", "class", "project", "script", "api",
        "ui", "webpage", "bot", "server", "service"
    )
    return any(word in low for word in code_words)


def _looks_like_website_request(text: str) -> bool:
    low = (text or "").lower()
    website_words = (
        "website",
        "web site",
        "landing page",
        "homepage",
        "home page",
        "portfolio",
        "product site",
        "business site",
        "marketing site",
        "web app",
        "frontend",
        "site",
    )
    return any(word in low for word in website_words)


def _is_gemini_limit_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(token in msg for token in (
        "429",
        "resource_exhausted",
        "quota",
        "rate limit",
        "too many requests",
        "exceeded",
        "1008",
        "access denied",
        "permission denied",
    ))


def _looks_like_screen_request(text: str) -> bool:
    t = (text or "").lower()
    if not t:
        return False
    direct_phrases = (
        "what's on my screen",
        "whats on my screen",
        "what is on my screen",
        "check my screen",
        "look at my screen",
        "analyze my screen",
        "analyse my screen",
        "tell me what's on my screen",
        "tell me what is on my screen",
        "read my screen",
        "what does my screen say",
    )
    if any(p in t for p in direct_phrases):
        return True
    screen_words = ("screen", "display", "monitor", "window")
    request_words = ("what", "check", "look", "analy", "analyse", "analyze", "read", "tell", "answer", "see")
    return any(sw in t for sw in screen_words) and any(rw in t for rw in request_words)


def _wakeword_detected(text: str) -> bool:
    t = re.sub(r"[^a-z0-9\s]+", " ", (text or "").lower())
    words = [w for w in t.split() if w]
    if not words:
        return False
    phrases = (
        "jarvis",
        "hey jarvis",
        "hi jarvis",
        "hello jarvis",
        "hey",
        "hi",
        "hello",
    )
    compact = " ".join(words)
    if compact in phrases or any(p in compact for p in phrases):
        return True
    return any(word in {"jarvis", "hey", "hi", "hello"} for word in words)


def _build_task_plan(text: str) -> list[str]:
    t = (text or "").lower()
    if any(word in t for word in ("presentation", "ppt", "slides", "deck")):
        return [
            "Understand the topic and goal",
            "Build a slide structure",
            "Generate and format the deck",
            "Open the finished presentation",
        ]
    if any(word in t for word in ("spreadsheet", "excel", "sheet", "table", "tracker", "budget")):
        return [
            "Read the data request",
            "Lay out sheets and columns",
            "Apply formulas and formatting",
            "Open the workbook",
        ]
    if any(word in t for word in ("word", "docx", "document", "report", "letter")):
        return [
            "Understand the document type",
            "Draft the structure and content",
            "Preserve formatting and polish",
            "Save the editable file",
        ]
    if any(word in t for word in ("website", "web site", "landing page", "saaS", "saas", "dashboard", "app")):
        return [
            "Interpret the brief",
            "Generate frontend and backend files",
            "Launch the local preview",
            "Debug and fix launch issues if needed",
        ]
    if any(word in t for word in ("browser", "website", "google", "search", "open url", "navigate")):
        return [
            "Open the browser",
            "Navigate to the target page",
            "Collect the needed information",
            "Return the result",
        ]
    if any(word in t for word in ("screen", "camera", "meeting", "call", "analyze", "analyse", "analyze")):
        return [
            "Capture the live screen or camera",
            "Inspect what is visible",
            "Answer with the important details",
            "Keep listening for follow-up commands",
        ]
    if any(word in t for word in ("fan", "light", "plug", "kasa", "atomberg", "smart home", "home device", "room", "bedroom", "living room", "kitchen", "office", "bathroom", "balcony")):
        return [
            "Identify the smart-home device or room",
            "Choose the correct action",
            "Send the command to the connected provider",
            "Confirm the result back to the user",
        ]
    return [
        "Understand the command",
        "Choose the right tool",
        "Execute the task",
        "Return the result",
    ]


_last_memory_input = ""

def _update_memory_async(user_text: str, brahma_text: str) -> None:
    global _last_memory_input

    user_text   = (user_text   or "").strip()
    brahma_text = (brahma_text or "").strip()

    if len(user_text) < 5 or user_text == _last_memory_input:
        return
    _last_memory_input = user_text

    try:
        api_key = _get_api_key()
        if not should_extract_memory(user_text, brahma_text, api_key):
            return
        data = extract_memory(user_text, brahma_text, api_key)
        if data:
            update_memory(data)
            print(f"[Memory] ✅ {list(data.keys())}")
    except Exception as e:
        if "429" not in str(e):
            print(f"[Memory] ⚠️ {e}")

def _memory_context_for_request(text: str) -> str:
    try:
        return workspace_store().memory_context(text, limit=5)
    except Exception:
        return ""


TOOL_DECLARATIONS = [
    {
        "name": "open_app",
        "description": (
            "Opens any application on the Windows computer. "
            "Use this whenever the user asks to open, launch, or start any app, "
            "website, or program. Always call this tool — never just say you opened it."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "app_name": {
                    "type": "STRING",
                    "description": "Exact name of the application (e.g. 'WhatsApp', 'Chrome', 'Spotify')"
                }
            },
            "required": ["app_name"]
        }
    },
    {
        "name": "web_search",
        "description": "Searches the web for any information.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query":  {"type": "STRING", "description": "Search query"},
                "mode":   {"type": "STRING", "description": "search (default) or compare"},
                "items":  {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Items to compare"},
                "aspect": {"type": "STRING", "description": "price | specs | reviews"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "weather_report",
        "description": "Gives the weather report to user",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "city": {"type": "STRING", "description": "City name"}
            },
            "required": ["city"]
        }
    },
    {
        "name": "send_message",
        "description": "Sends a text message via WhatsApp, Telegram, Instagram DMs, or other messaging platform. Can also upload media to Instagram when mode=upload and media_path is supplied.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "receiver":     {"type": "STRING", "description": "Recipient contact name for DMs"},
                "message_text": {"type": "STRING", "description": "The message to send or Instagram caption"},
                "platform":     {"type": "STRING", "description": "Platform: WhatsApp, Telegram, Instagram, etc."},
                "mode":         {"type": "STRING", "description": "dm | upload (Instagram only; default: dm)"},
                "media_path":   {"type": "STRING", "description": "Optional image/video path for Instagram uploads"}
            },
            "required": ["platform"]
        }
    },
    {
        "name": "reminder",
        "description": "Sets a timed reminder using Windows Task Scheduler.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "date":    {"type": "STRING", "description": "Date in YYYY-MM-DD format"},
                "time":    {"type": "STRING", "description": "Time in HH:MM format (24h)"},
                "message": {"type": "STRING", "description": "Reminder message text"}
            },
            "required": ["date", "time", "message"]
        }
    },
    {
        "name": "youtube_video",
        "description": (
            "Controls YouTube. Use for: playing videos, summarizing a video's content, "
            "getting video info, showing trending videos, or downloading videos/audio. "
            "Use action='download' to download a video using yt-dlp."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":    {"type": "STRING", "description": "play | summarize | get_info | trending | download (default: play)"},
                "query":     {"type": "STRING", "description": "Search query for play action"},
                "save":      {"type": "BOOLEAN", "description": "Save summary to Notepad (summarize only)"},
                "region":    {"type": "STRING", "description": "Country code for trending e.g. TR, US"},
                "url":       {"type": "STRING", "description": "Video URL for get_info or download action"},
                "output_path": {"type": "STRING", "description": "Directory to save downloaded file (default: Desktop)"},
                "format":    {"type": "STRING", "description": "Download format e.g. bestvideo+bestaudio/best, bestaudio, bestvideo"},
            },
            "required": []
        }
    },
    {
        "name": "url_downloader",
        "description": (
            "Downloads any file from a URL. Handles videos/audio from sites like YouTube, Vimeo, Twitter, "
            "Instagram, TikTok, Reddit, SoundCloud (via yt-dlp), AND direct file links for images, "
            "documents, audio, video, archives, code, fonts. Use when user pastes a link and wants to download it."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "url":         {"type": "STRING", "description": "The URL to download (required)"},
                "output_path": {"type": "STRING", "description": "Directory to save file (default: Desktop)"},
                "format":      {"type": "STRING", "description": "yt-dlp format selector (e.g. bestvideo+bestaudio/best, bestaudio)"},
                "open_after":  {"type": "BOOLEAN", "description": "Open file after download (default: true)"}
            },
            "required": ["url"]
        }
    },
    {
        "name": "computer_settings",
        "description": (
            "Controls the computer: volume, brightness, window management, keyboard shortcuts, "
            "typing text on screen, closing apps, fullscreen, dark mode, WiFi, restart, shutdown, "
            "scrolling, tab management, zoom, screenshots, lock screen, refresh/reload page. "
            "Use for ANY single computer control command. NEVER route to agent_task."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":      {"type": "STRING", "description": "The action to perform"},
                "description": {"type": "STRING", "description": "Natural language description of what to do"},
                "value":       {"type": "STRING", "description": "Optional value: volume level, text to type, etc."}
            },
            "required": []
        }
    },
    {
        "name": "browser_control",
        "description": (
            "Controls the web browser. Use for: opening websites, searching the web, "
            "navigating pages, clicking elements, filling forms, scrolling, tabs, back/forward, "
            "refreshing, and any web-based task."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":      {"type": "STRING", "description": "go_to | navigate | search | click | type | scroll | fill_form | smart_click | smart_type | get_text | press | back | forward | refresh | open_tab | new_tab | switch_tab | list_tabs | close"},
                "url":         {"type": "STRING", "description": "URL for go_to action"},
                "query":       {"type": "STRING", "description": "Search query for search action"},
                "selector":    {"type": "STRING", "description": "CSS selector for click/type"},
                "text":        {"type": "STRING", "description": "Text to click or type"},
                "description": {"type": "STRING", "description": "Element description for smart_click/smart_type"},
                "direction":   {"type": "STRING", "description": "up or down for scroll"},
                "key":         {"type": "STRING", "description": "Key name for press action"},
                "tab":         {"type": "INTEGER", "description": "1-based tab index for switch_tab"},
                "incognito":   {"type": "BOOLEAN", "description": "Open in private/incognito mode"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "file_controller",
        "description": (
            "Full file manager for the entire computer: navigate folders (cd/pwd/up/tree), "
            "list, create, read, write, delete, move, copy, rename, find/search, share, open, "
            "permissions, archives and system info. Works on ANY path — every drive, every "
            "user's home folder, /root, hidden and system folders — and escalates when the OS "
            "asks for permission. Reads any format (text, code, JSON, CSV, PDF, DOCX, PPTX, "
            "XLSX, images, audio/video, archives, binary hex)."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":      {"type": "STRING", "description": "list | tree | cd | pwd | up | create_file | create_folder | delete | move | copy | rename | read | write | find | largest | recent | disk_usage | organize_desktop | organize_folder | info | open | open_with | reveal | share | shares | unshare | permissions | chmod | chown | users | partitions | trash | archive | extract | describe | capabilities"},
                "path":        {"type": "STRING", "description": "File/folder path — absolute anywhere on the system, or a shortcut: desktop, downloads, documents, pictures, music, videos, home, root, users, tmp, trash, shared, cwd (also supports ~user and $VARS)"},
                "name":        {"type": "STRING", "description": "File/folder name inside path (create, read, write, delete, open...)"},
                "destination": {"type": "STRING", "description": "Destination path for move/copy/extract/archive/share to folder"},
                "new_name":    {"type": "STRING", "description": "New name for rename"},
                "content":     {"type": "STRING", "description": "Content for create_file/write (base64 when base64_encoded=true)"},
                "extension":   {"type": "STRING", "description": "File extension to search (e.g. .pdf)"},
                "pattern":     {"type": "STRING", "description": "Glob pattern for find (e.g. *.mp4)"},
                "count":       {"type": "INTEGER", "description": "Max results for largest/recent"},
                "max_results": {"type": "INTEGER", "description": "Max results for find (default 20)"},
                "mode":        {"type": "STRING", "description": "by_type/by_date for organize, or permission mode for chmod (755, u+rwx), or list/empty/restore for trash"},
                "permission":  {"type": "STRING", "description": "Permission mode for chmod: 755, 644, u+rwx,g-w,o+r"},
                "owner":       {"type": "STRING", "description": "Owner for chown: user, user:group, :group"},
                "show_hidden": {"type": "BOOLEAN", "description": "Include dotfiles in list/find/recent (default false)"},
                "hidden":      {"type": "BOOLEAN", "description": "Alias of show_hidden for find/largest/recent"},
                "permanent":   {"type": "BOOLEAN", "description": "delete only: skip the recycle bin and delete permanently (default false)"},
                "elevated":    {"type": "BOOLEAN", "description": "Ask the OS for root permission when a path is blocked (default true for writes/deletes)"},
                "append":      {"type": "BOOLEAN", "description": "write: append instead of overwrite"},
                "base64_encoded": {"type": "BOOLEAN", "description": "write: content is base64-encoded binary data"},
                "max_chars":   {"type": "INTEGER", "description": "read: character budget (default 3000)"},
                "recursive":   {"type": "BOOLEAN", "description": "Descend into subfolders (find/largest) or apply to a whole tree (chmod/chown)"},
                "kind":        {"type": "STRING", "description": "find: file | dir | any"},
                "max_depth":   {"type": "INTEGER", "description": "find: how deep to descend"},
                "min_size":    {"type": "STRING", "description": "find: minimum size (e.g. 10MB)"},
                "max_size":    {"type": "STRING", "description": "find: maximum size (e.g. 2GB)"},
                "limit":       {"type": "INTEGER", "description": "list: max entries per page (default 500)"},
                "offset":      {"type": "INTEGER", "description": "list: paging offset"},
                "levels":      {"type": "INTEGER", "description": "up: how many parent folders to go up (default 1)"},
                "depth":       {"type": "INTEGER", "description": "tree: depth levels (default 3)"},
                "max_entries": {"type": "INTEGER", "description": "tree: max entries (default 300)"},
                "app":         {"type": "STRING", "description": "open/open_with: application to open the file with"},
                "method":      {"type": "STRING", "description": "share: auto | device | link | folder | email"},
                "device":      {"type": "STRING", "description": "share: paired device name to send the file to"},
                "duration":    {"type": "INTEGER", "description": "share link lifetime in seconds (default 1800)"},
                "token":       {"type": "STRING", "description": "unshare: share token or URL to stop"},
                "trash_action": {"type": "STRING", "description": "trash: list | empty | restore"},
                "trash_item":  {"type": "STRING", "description": "trash restore: item name in the recycle bin"},
                "format":      {"type": "STRING", "description": "archive: zip | tar.gz"},
                "days":        {"type": "INTEGER", "description": "recent: only files changed within N days (default 7)"},
                "hash":        {"type": "BOOLEAN", "description": "info: include SHA-256 checksum"},
                "instruction": {"type": "STRING", "description": "describe: what to analyze about the file"},
                "target":      {"type": "STRING", "description": "Alias for destination/device/trash_item"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "desktop_control",
        "description": "Controls the desktop: wallpaper, organize, clean, list, stats.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "wallpaper | wallpaper_url | organize | clean | list | stats | task"},
                "path":   {"type": "STRING", "description": "Image path for wallpaper"},
                "url":    {"type": "STRING", "description": "Image URL for wallpaper_url"},
                "mode":   {"type": "STRING", "description": "by_type or by_date for organize"},
                "task":   {"type": "STRING", "description": "Natural language desktop task"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "agent_task",
        "description": (
            "DELEGATE a high-level objective to the agent team. Use this for work "
            "that needs several different specialists: research plus documents, "
            "or code plus files. The orchestrator breaks the objective into "
            "steps, assigns each to the right agent (Research, Document, Code), "
            "runs them in dependency order, shares their results, and reports "
            "when the whole objective is verified. "
            "Example: 'research Forex trading, write a PDF and a PowerPoint with "
            "images, save both to my Desktop'. "
            "DO NOT use for single commands — do those yourself."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "goal":     {"type": "STRING", "description": "The complete objective, including every deliverable and where it must be saved"},
            "objective": {"type": "STRING", "description": "Optional concise objective; defaults to goal"},
            "priority": {"type": "STRING", "description": "low | normal | high (default: normal)"},
            "context": {"type": "OBJECT", "description": "Relevant authorized context only"},
            "requirements": {"type": "ARRAY", "items": {"type": "STRING"}},
            "constraints": {"type": "ARRAY", "items": {"type": "STRING"}},
            "expected_output": {"type": "STRING"},
            "references": {"type": "ARRAY", "items": {"type": "STRING"}},
            "request_id": {"type": "STRING", "description": "Stable id for safe retry and deduplication"}
            },
            "required": ["goal"]
        }
    },
    {
        "name": "agent_status",
        "description": (
            "Report what the agent team is doing right now: which agents are "
            "working, the current objective and the steps completed so far. "
            "Use this when the user asks what you are doing or how a delegated "
            "task is progressing."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "detail": {"type": "BOOLEAN", "description": "Include the full step list (default: false)"}
            }
        }
    },
    {
        "name": "agent_cancel",
        "description": "Cancel an active HELIX task by its task_id.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "task_id": {"type": "STRING", "description": "HELIX task id from the acceptance receipt"}
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "computer_control",
        "description": "Direct computer control: type, click, hotkeys, scroll, move mouse, screenshots, find elements on screen.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":      {"type": "STRING", "description": "type | smart_type | click | double_click | right_click | hotkey | press | scroll | move | copy | paste | screenshot | wait | clear_field | focus_window | screen_find | screen_click | random_data | user_data"},
                "text":        {"type": "STRING", "description": "Text to type or paste"},
                "x":           {"type": "INTEGER", "description": "X coordinate"},
                "y":           {"type": "INTEGER", "description": "Y coordinate"},
                "keys":        {"type": "STRING", "description": "Key combination e.g. 'ctrl+c'"},
                "key":         {"type": "STRING", "description": "Single key e.g. 'enter'"},
                "direction":   {"type": "STRING", "description": "up | down | left | right"},
                "amount":      {"type": "INTEGER", "description": "Scroll amount (default: 3)"},
                "seconds":     {"type": "NUMBER",  "description": "Seconds to wait"},
                "title":       {"type": "STRING",  "description": "Window title for focus_window"},
                "description": {"type": "STRING",  "description": "Element description for screen_find/screen_click"},
                "type":        {"type": "STRING",  "description": "Data type for random_data"},
                "field":       {"type": "STRING",  "description": "Field for user_data: name|email|city"},
                "clear_first": {"type": "BOOLEAN", "description": "Clear field before typing (default: true)"},
                "path":        {"type": "STRING",  "description": "Save path for screenshot"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "game_updater",
        "description": (
            "THE ONLY tool for ANY Steam or Epic Games request. "
            "Use for: installing, downloading, updating games, listing installed games, "
            "checking download status, scheduling updates. "
            "ALWAYS call directly for any Steam/Epic/game request. "
            "NEVER use agent_task, browser_control, or web_search for Steam/Epic."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":    {"type": "STRING",  "description": "update | install | list | download_status | schedule | cancel_schedule | schedule_status (default: update)"},
                "platform":  {"type": "STRING",  "description": "steam | epic | both (default: both)"},
                "game_name": {"type": "STRING",  "description": "Game name (partial match supported)"},
                "app_id":    {"type": "STRING",  "description": "Steam AppID for install (optional)"},
                "hour":      {"type": "INTEGER", "description": "Hour for scheduled update 0-23 (default: 3)"},
                "minute":    {"type": "INTEGER", "description": "Minute for scheduled update 0-59 (default: 0)"},
                "shutdown_when_done": {"type": "BOOLEAN", "description": "Shut down PC when download finishes"},
            },
            "required": []
        }
    },
    {
        "name": "flight_finder",
        "description": "Searches Google Flights and speaks the best options.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "origin":      {"type": "STRING",  "description": "Departure city or airport code"},
                "destination": {"type": "STRING",  "description": "Arrival city or airport code"},
                "date":        {"type": "STRING",  "description": "Departure date (any format)"},
                "return_date": {"type": "STRING",  "description": "Return date for round trips"},
                "passengers":  {"type": "INTEGER", "description": "Number of passengers (default: 1)"},
                "cabin":       {"type": "STRING",  "description": "economy | premium | business | first"},
                "save":        {"type": "BOOLEAN", "description": "Save results to Notepad"},
            },
            "required": ["origin", "destination", "date"]
        }
    },
    {
        "name": "file_processor",
        "description": (
            "Processes any file that the user has uploaded or dropped onto the interface. "
        "Use this when the user refers to an uploaded file and wants an action on it. "
        "Supports: images (describe/ocr/resize/compress/convert), "
        "PDFs (summarize/extract_text/to_word), "
            "text files (summarize/fix/reformat/translate), "
        "CSV/Excel (analyze/stats/filter/sort/convert), "
        "JSON/XML (validate/format/analyze), "
        "code files (explain/review/fix/optimize/run/document/test), "
        "audio (transcribe/trim/convert/info), "
        "video (trim/extract_audio/extract_frame/compress/transcribe/info), "
        "archives (list/extract), "
        "presentations (summarize/extract_text). "
            "ALWAYS call this tool when a non-Word file has been uploaded and the user gives a command about it. "
        "If the user's command is ambiguous, pick the most logical action for that file type."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "file_path": {
                "type": "STRING",
                "description": "Full path to the uploaded file. Leave empty to use the currently uploaded file."
            },
            "action": {
                "type": "STRING",
                "description": (
                    "What to do with the file. Examples by type:\n"
                    "image: describe | ocr | resize | compress | convert | info\n"
                    "pdf: summarize | extract_text | to_word | info\n"
                    "docx via word_document; txt: summarize | fix | reformat | translate_hint | word_count | to_bullet\n"
                    "csv/excel: analyze | stats | filter | sort | convert | info\n"
                    "json: validate | format | analyze | to_csv\n"
                    "code: explain | review | fix | optimize | run | document | test\n"
                    "audio: transcribe | trim | convert | info\n"
                    "video: trim | extract_audio | extract_frame | compress | transcribe | info | convert\n"
                    "archive: list | extract\n"
                    "pptx: summarize | extract_text | analyze"
                )
            },
            "instruction": {
                "type": "STRING",
                "description": "Free-form instruction if action doesn't cover it. E.g. 'translate this to Turkish', 'find all email addresses'"
            },
            "format": {
                "type": "STRING",
                "description": "Target format for conversion. E.g. 'mp3', 'pdf', 'csv', 'png'"
            },
            "width":     {"type": "INTEGER", "description": "Target width for image resize"},
            "height":    {"type": "INTEGER", "description": "Target height for image resize"},
            "scale":     {"type": "NUMBER",  "description": "Scale factor for image resize (e.g. 0.5)"},
            "quality":   {"type": "INTEGER", "description": "Quality 1-100 for image/video compress"},
            "start":     {"type": "STRING",  "description": "Start time for trim: seconds or HH:MM:SS"},
            "end":       {"type": "STRING",  "description": "End time for trim: seconds or HH:MM:SS"},
            "timestamp": {"type": "STRING",  "description": "Timestamp for video frame extraction HH:MM:SS"},
            "column":    {"type": "STRING",  "description": "Column name for CSV filter/sort"},
            "value":     {"type": "STRING",  "description": "Filter value for CSV filter"},
            "condition": {"type": "STRING",  "description": "Filter condition: equals|contains|gt|lt"},
            "ascending": {"type": "BOOLEAN", "description": "Sort order for CSV sort (default: true)"},
            "save":      {"type": "BOOLEAN", "description": "Save result to file (default: true)"},
            "destination": {"type": "STRING", "description": "Output folder for archive extract"},
        },
        "required": []
        }
    },
    {
        "name": "presentation_builder",
        "description": (
            "Creates editable PowerPoint presentations (.pptx) from a structured slide outline. "
            "Jarvis automatically infers the best visual style from the topic, searches for a matching online template when available, "
            "reuses cached templates, and falls back to the built-in designer if no suitable template is found. "
            "Use when the user asks for a deck, slideshow, presentation, pitch deck, or report slides."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "title": {"type": "STRING", "description": "Presentation title"},
                "subtitle": {"type": "STRING", "description": "Optional subtitle or audience line"},
                "theme": {
                    "type": "STRING",
                    "description": "Optional presentation theme or visual direction such as neon, corporate, luxury, academic, sunset, or creative. If omitted, Jarvis infers the best style automatically."
                },
                "outline": {
                    "type": "STRING",
                    "description": "Slide-by-slide outline. Use blank lines to separate slides if slides array is omitted."
                },
                "slides": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "title": {"type": "STRING", "description": "Slide title"},
                            "kicker": {"type": "STRING", "description": "Short all-caps kicker"},
                            "bullets": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"},
                                "description": "Bullet points for the slide"
                            },
                            "notes": {"type": "STRING", "description": "Optional speaker note or footnote"}
                        },
                        "required": ["title"]
                    },
                    "description": "Structured slides. Preferred when the model can format the deck directly."
                },
                "output_path": {"type": "STRING", "description": "Optional output path for the .pptx"},
                "auto_open": {"type": "BOOLEAN", "description": "Open the file after creating it (default: true)"},
            },
            "required": ["title"]
        }
    },
    {
        "name": "spreadsheet_builder",
        "description": (
            "Creates editable Excel workbooks (.xlsx) from structured sheet data. "
            "Use for trackers, tables, analysis workbooks, budgets, planners, and other spreadsheet requests."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "title": {"type": "STRING", "description": "Workbook title"},
                "worksheets": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "name": {"type": "STRING", "description": "Worksheet name"},
                            "title": {"type": "STRING", "description": "Optional sheet title row"},
                            "headers": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"},
                                "description": "Column headers"
                            },
                            "rows": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "ARRAY",
                                    "items": {"type": "STRING"},
                                },
                                "description": "Data rows"
                            },
                            "chart": {
                                "type": "OBJECT",
                                "properties": {
                                    "type": {"type": "STRING", "description": "bar | line | pie"},
                                    "title": {"type": "STRING", "description": "Chart title"},
                                    "anchor": {"type": "STRING", "description": "Cell anchor such as E2"},
                                    "x_axis": {"type": "STRING", "description": "Optional x-axis title"},
                                    "y_axis": {"type": "STRING", "description": "Optional y-axis title"},
                                }
                            }
                        },
                        "required": ["name"]
                    },
                    "description": "One or more worksheets to create."
                },
                "output_path": {"type": "STRING", "description": "Optional output path for the .xlsx"},
                "auto_open": {"type": "BOOLEAN", "description": "Open the file after creating it (default: true)"},
            },
            "required": ["title"]
        }
    },
    {
        "name": "word_document",
        "description": (
            "Creates, edits, reads, summarizes, extracts text from, and opens editable Word documents (.docx). "
            "Use for Word document requests, letters, reports, headings, bullets, formatting edits, and preserving existing formatting."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING",
                    "description": "create | create_letter | create_report | read | summarize | extract_text | append | replace_text | add_heading | add_bullets | reformat | open"
                },
                "file_path": {"type": "STRING", "description": "Existing .docx file path for read/edit/open actions"},
                "output_path": {"type": "STRING", "description": "Optional output path for the saved .docx"},
                "title": {"type": "STRING", "description": "Document title"},
                "doc_type": {"type": "STRING", "description": "letter | report | generic"},
                "content": {"type": "STRING", "description": "Main body content or text to append"},
                "body": {"type": "STRING", "description": "Body text for letter/report creation"},
                "paragraphs": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Paragraphs to add"},
                "bullets": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Bullet items to add"},
                "numbered": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Numbered items to add"},
                "sections": {"type": "ARRAY", "items": {"type": "OBJECT"}, "description": "Structured sections with heading/body/bullets"},
                "replacements": {"type": "OBJECT", "description": "Find/replace mapping for formatting-preserving edits"},
                "find": {"type": "STRING", "description": "Text to find for simple replace_text edits"},
                "replace": {"type": "STRING", "description": "Replacement text for simple replace_text edits"},
                "heading": {"type": "STRING", "description": "Heading text to append"},
                "level": {"type": "INTEGER", "description": "Heading level 1-3"},
                "recipient": {"type": "STRING", "description": "Letter recipient"},
                "salutation": {"type": "STRING", "description": "Custom letter salutation"},
                "closing": {"type": "STRING", "description": "Custom letter closing"},
                "date": {"type": "STRING", "description": "Letter date"},
                "author": {"type": "STRING", "description": "Document author"},
                "subject": {"type": "STRING", "description": "Document subject"},
                "open_after": {"type": "BOOLEAN", "description": "Open the saved document after writing (default: true)"},
                "save": {"type": "BOOLEAN", "description": "Save large generated summaries to a text file"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "pdf_document",
        "description": (
            "Creates editable-style PDF documents (.pdf) from structured content or converts DOCX / text files into PDFs. "
            "Use for PDF creation, PDF exports, and PDF generation requests that need a direct file output."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING",
                    "description": "create | create_report | create_letter | convert"
                },
                "file_path": {"type": "STRING", "description": "Existing file to convert, typically .docx or .txt"},
                "output_path": {"type": "STRING", "description": "Optional output path for the saved .pdf"},
                "title": {"type": "STRING", "description": "PDF title"},
                "subtitle": {"type": "STRING", "description": "Optional subtitle"},
                "content": {"type": "STRING", "description": "Main body content"},
                "body": {"type": "STRING", "description": "Main body content"},
                "paragraphs": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Paragraphs to add"},
                "bullets": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Bullet items to add"},
                "numbered": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Numbered items to add"},
                "sections": {"type": "ARRAY", "items": {"type": "OBJECT"}, "description": "Structured sections with heading/body/bullets"},
                "recipient": {"type": "STRING", "description": "Letter recipient"},
                "salutation": {"type": "STRING", "description": "Custom letter salutation"},
                "closing": {"type": "STRING", "description": "Custom letter closing"},
                "date": {"type": "STRING", "description": "Letter date"},
                "author": {"type": "STRING", "description": "Document author"},
                "subject": {"type": "STRING", "description": "Document subject"},
                "auto_open": {"type": "BOOLEAN", "description": "Open the file after creating it (default: true)"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "shutdown_jarvis",
        "description": (
            "Shuts down the assistant completely. "
        "Call this when the user expresses intent to end the conversation, "
        "close the assistant, say goodbye, or stop Jarvis. "
        "The user can say this in ANY language."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {},
    }
    },
    {
        "name": "save_memory",
        "description": (
            "Save an important personal fact about the user to long-term memory. "
            "Call this silently whenever the user reveals something worth remembering: "
            "name, age, city, job, preferences, hobbies, relationships, projects, or future plans. "
            "Do NOT call for: weather, reminders, searches, or one-time commands. "
            "Do NOT announce that you are saving — just call it silently. "
            "Values must be in English regardless of the conversation language."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "category": {
                    "type": "STRING",
                    "description": (
                        "identity — name, age, birthday, city, job, language, nationality | "
                        "past — life history, background, past events, career history | "
                        "present — current projects, current situation, current challenges | "
                        "future — goals, plans, things they want to do, upcoming events | "
                        "dreams — deeper aspirations, what they care about long-term | "
                        "preferences — favorite food/color/music/film/game/sport, hobbies | "
                        "personality — patterns in how they think, work, communicate | "
                        "projects — active projects, goals, things being built | "
                        "relationships — friends, family, partner, colleagues | "
                        "notes — habits, schedule, anything else worth remembering"
                    )
                },
                "key":   {"type": "STRING", "description": "Short snake_case key (e.g. name, favorite_food, sister_name)"},
                "value": {"type": "STRING", "description": "Concise value in English (e.g. Suryaansh, pizza, older sister)"},
            },
            "required": ["category", "key", "value"]
        }
    },
    {
        "name": "recall_chat_history",
        "description": (
            "Recall something from a past conversation with the user — a full day's "
            "conversation log, or a search for a specific topic/word across all past days. "
            "Use this when the user asks things like 'what did we talk about yesterday', "
            "'do you remember when I asked about X', 'what did I say about Y last week'."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "mode": {
                    "type": "STRING",
                    "description": "'search' to find mentions of a topic across all days, or 'day' to recall a specific date's full conversation."
                },
                "query": {
                    "type": "STRING",
                    "description": "For mode=search: the topic/word to look for. Not needed for mode=day."
                },
                "date": {
                    "type": "STRING",
                    "description": "For mode=day: a date as YYYY-MM-DD, or the words 'today'/'yesterday'."
                },
            },
            "required": ["mode"]
        }
    },
]


class JarvisLive:

    def __init__(self, ui: JarvisUI, dashboard=None, dashboard_started: bool = False, enable_dashboard: bool = True):
        self.ui             = ui
        self.session        = None
        self.audio_in_queue = None
        self.out_queue      = None
        # One writer at a time on the live websocket; see _session_write.
        self._ws_lock       = asyncio.Lock()
        self._loop          = None
        self._is_speaking   = False
        # Echo guard. A plain boolean is racy: turn_complete can land before
        # the last audio chunks finish playing, and the playback queue can be
        # momentarily empty between chunks. Either window un-gates the mic
        # while our own voice is still in the room, the server transcribes it
        # as the user, and Jarvis starts answering himself. So the gate is a
        # deadline that every bit of playback pushes forward.
        self._speaking_until = 0.0
        self._echo_guard_ms  = _ECHO_GUARD_MS
        self._recent_jarvis_speech: deque[str] = deque(maxlen=6)
        self._echo_drops = 0
        self._watchdog_started = False
        # Jarvis may only act on something the operator actually asked for.
        # Without this the model invented turns with nobody speaking and went
        # on to save fabricated memories and reorganise Desktop/Downloads.
        self._user_turn_active = False
        self._last_user_text = ""
        self._mic_down = False
        self._blocked_tool_calls = 0
        self._speaking_lock = threading.Lock()
        self._use_openrouter_first = False
        self._pending_attention: dict | None = None
        self._pending_reply_event: dict | None = None
        self._reply_mode = False
        self._attention_lock = threading.Lock()
        self._attention_monitor = AttentionMonitor(on_event=self._on_external_notification)
        self._meeting_lock = threading.Lock()
        self._meeting_active = False
        self._meeting_event: dict | None = None
        self._meeting_assistant = MeetingAssistant(
            on_update=self._on_meeting_update,
            on_state=self._on_meeting_state,
        )
        self._phone_active = False
        self._local_voice_mode = False  # True = local (offline) pipeline, False = Gemini Live
        self._dashboard = dashboard if dashboard is not None else (DashboardServer() if (enable_dashboard and DashboardServer is not None) else None)
        self.ui_bridge = None
        self._dashboard_started = bool(dashboard_started and self._dashboard is not None)
        self.ui.on_text_command = self._on_text_command
        self.ui.on_attention_action = self._on_attention_action
        self.ui.on_remote_clicked = self._make_remote_key
        # The Executive Briefing button composes the briefing off the GUI
        # thread and hands the text to every surface.
        self.ui.on_briefing = lambda: threading.Thread(
            target=_speak_daily_briefing, args=(self.ui,),
            daemon=True, name="briefing").start()
        self._last_activity = time.monotonic()
        self._idle_prompts = [
            "Hey, you there?",
            "Yo, get alive.",
            "How may I help, bro?",
            "Need anything?",
            "I'm here if you want me.",
        ]
        # Idle chatter ("Hey, you there?") used to fire every 4-5 minutes with
        # no request from the user, which is indistinguishable from Jarvis
        # talking to itself. It is now opt-in and off by default.
        self._idle_speech_thread = threading.Thread(target=self._idle_speech_loop, daemon=True)
        self._idle_speech_thread.start()

    def _reset_idle_activity(self):
        self._last_activity = time.monotonic()
        self._obsidian_logged = False
        self._obsidian_user_text = ""
        self._obsidian_jarvis_text = ""

    def _should_announce_idle(self) -> bool:
        # Opt-in only: unprompted speech is a bug, not a feature. Enable with
        # settings key "idle_chatter_enabled".
        try:
            ui_settings = self.ui._load_app_settings()
        except Exception:
            ui_settings = {}
        if not bool(ui_settings.get("idle_chatter_enabled", False)):
            return False
        if self.ui.muted:
            return False
        if self._is_speaking:
            return False
        if self._meeting_active:
            return False
        if self._pending_attention:
            return False
        if time.monotonic() - self._last_activity < 240:
            return False
        return True

    def _idle_speech_loop(self):
        while True:
            time.sleep(random.uniform(240.0, 300.0))
            try:
                if self._should_announce_idle():
                    message = random.choice(self._idle_prompts)
                    self.ui.write_log(f"SYS: {message}")
                    threading.Thread(target=speak_native, args=(message,), daemon=True).start()
                    self._reset_idle_activity()
            except Exception:
                pass

    def _make_remote_key(self):
        if self._dashboard is None:
            self.ui.write_log("ERR: Mobile Connect unavailable. Install fastapi, uvicorn, cryptography, and qrcode[pil].")
            return None
        key = self._dashboard.new_key()
        url = self._dashboard.get_url()
        manual = self._dashboard.get_manual_url()
        return url, key, f"{url}/auto-login?key={key}", manual

    def _on_phone_connected(self):
        try:
            self.ui.notify_phone_connected()
        except Exception:
            pass

    def _on_text_command(self, text: str, source: str = "local"):
        self._reset_idle_activity()
        text = (text or "").strip()
        if not text:
            return
        # A typed / mobile / Discord request is a real user turn, so the tool
        # gate must open for it exactly as it does for a voice transcript.
        self._mark_user_turn(text)
        try:
            stop_native_speech()
        except Exception:
            pass
        # allow plugins to handle the incoming text command first
        try:
            pm = getattr(self, "plugin_manager", None)
            if pm is not None:
                handled = pm.dispatch("on_text_command", text, source)
                if handled:
                    return
        except Exception:
            pass
        if self._reply_mode:
            if self._handle_pending_reply(text):
                return
            # Still in reply mode but no pending reply event means reset and continue
            self._reply_mode = False

        # Log conversation to Obsidian vault (online + offline)
        try:
            from obsidian_integration import save_conversation
            save_conversation(text, "")  # Will be updated after response
            self._obsidian_logged = True
            self._obsidian_user_text = text
        except Exception:
            self._obsidian_logged = False

        developer_settings = self.ui._load_app_settings() if hasattr(self.ui, "_load_app_settings") else {}
        developer_enabled = bool(developer_settings.get("developer_mode_enabled", False))
        developer_workspace = str(developer_settings.get("developer_mode_workspace", "")).strip()
        website_request = _looks_like_website_request(text)
        if website_request and not (developer_enabled and developer_workspace):
            message = "Website builds need developer mode enabled and a workspace folder selected first."
            self.ui.write_log(f"ERR: {message}")
            self.speak(message)
            return

        if website_request and developer_enabled and developer_workspace:
            try:
                if hasattr(self.ui, "_developer_status_lbl"):
                    self.ui._developer_status_lbl.setText("Building website with Gemini in the selected workspace")
                    self.ui._developer_card.show()
                    self.ui._developer_card.raise_()
                result = website_builder(
                    parameters={
                        "action": "create",
                        "description": text,
                        "title": text,
                        "output_dir": developer_workspace,
                        "auto_open": True,
                    },
                    player=self.ui,
                )
                self.ui.write_log(f"[WebsiteBuilder] {result[:400]}")
                self.speak(result[:800])
                return
            except Exception as exc:
                self.ui.write_log(f"ERR: Website build failed: {exc}")

        memory_ctx = _memory_context_for_request(text)
        routed_text = f"{memory_ctx}\n\nCurrent User Request:\n{text}" if memory_ctx else text
        if text.lower() in {"stop meeting mode", "end meeting mode", "close meeting mode"}:
            self._stop_meeting_mode("Meeting mode closed.")
            return

        # Local voice mode switching
        if text.lower() in {"switch to offline mode", "switch to local mode", "go offline", "use local voice"}:
            self._enable_local_voice_mode()
            return
        if text.lower() in {"switch to online mode", "switch to cloud mode", "go online", "use gemini live"}:
            self._disable_local_voice_mode()
            return

        if self._handle_attention_response(text):
            return
        try:
            self.ui.begin_task_workspace(text, _build_task_plan(text), source=source or "local")
        except Exception:
            pass
        if _looks_like_screen_request(text):
            print("[Main] Screen analysis request received (vision removed)")
            try:
                self.ui.update_task_workspace(
                    status="Screen analysis unavailable",
                    output="Screen and camera vision are disabled on this installation.",
                    percent=0,
                )
            except Exception:
                pass
            return
        if self._local_voice_mode:
            # Local voice mode: use Ollama + local TTS
            threading.Thread(target=self._run_local_voice_pipeline, args=(text,), daemon=True).start()
            return
        if self._use_openrouter_first or not self._loop or not self.session:
            threading.Thread(target=self._fallback_reply, args=(text, memory_ctx), daemon=True).start()
            return
        asyncio.run_coroutine_threadsafe(
            self._session_write(
                "send_client_content",
                turns={"parts": [{"text": routed_text}]},
                turn_complete=True,
            ),
            self._loop
        )


    def _extract_launch_app_name(self, text: str) -> str:
        normalized = re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s%]", " ", text.lower())).strip()
        if not normalized:
            return ""

        prefixes = (
            "launch app ",
            "open app ",
            "start app ",
            "open the app ",
            "launch the app ",
            "start the app ",
            "open ",
            "launch ",
            "start ",
            "run ",
            "bring up ",
        )

        candidate = normalized
        for prefix in prefixes:
            if candidate.startswith(prefix):
                candidate = candidate[len(prefix):]
                break

        candidate = re.sub(r"\s+(?:on|in|to)\s+(?:my\s+)?(?:phone|mobile|tablet|android|device)\b.*$", "", candidate).strip()
        candidate = re.sub(r"\b(?:app|application|please|the)\b", " ", candidate).strip()
        candidate = re.sub(r"\s+", " ", candidate)
        return candidate

    def _attention_message(self, event: dict) -> str:
        app = (event.get("app") or "an app").strip()
        kind = (event.get("kind") or "message").strip().lower()
        if kind == "call":
            return f"Incoming call detected on {app}. Should I pick it up, ignore it, or cut the call?"
        title = (event.get("title") or "").strip()
        preview = (event.get("preview") or "").strip()
        if title:
            return f"You received a message on {app} from {title}. It says: {preview}"
        return f"You received a message on {app}. It says: {preview}"

    def _announce_attention(self, event: dict):
        msg = self._attention_message(event)
        self.ui.write_log(f"SYS: {msg}")
        threading.Thread(target=speak_native, args=(msg,), daemon=True).start()
        self.ui.show_attention_alert(event)

    def _on_external_notification(self, event: dict):
        if not isinstance(event, dict):
            return
        kind = (event.get("kind") or "message").strip().lower()
        app = (event.get("app") or "App").strip()
        preview = (event.get("preview") or "").strip()
        settings = {}
        try:
            settings = self.ui._load_app_settings()
        except Exception:
            settings = {}

        if kind == "call" and not bool(settings.get("attention_call_prompts", True)):
            return
        if kind == "message" and not bool(settings.get("attention_message_prompts", True)):
            return

        with self._attention_lock:
            current = self._pending_attention
            if current:
                same_app = (current.get("app") or "").strip().lower() == app.lower()
                same_kind = (current.get("kind") or "").strip().lower() == kind
                if same_app and same_kind:
                    return
            self._pending_attention = dict(event)

        self._announce_attention(event)
        if preview:
            self.ui.write_log(f"[Attention] {app}: {preview}")
        if kind == "call" and app.lower() in {"zoom", "teams", "whatsapp"}:
            self._start_meeting_mode(event)

    def _start_meeting_mode(self, event: dict):
        event = dict(event or {})
        app = (event.get("app") or "Meeting").strip()
        title = event.get("title") or f"{app} meeting"
        summary = f"Watching {app} for questions and answers."
        with self._meeting_lock:
            self._meeting_active = True
            self._meeting_event = event
        self.ui.set_meeting_mode(True, title, summary, "Listening for questions on screen...", self._meeting_assistant.latest_speech())
        self._meeting_assistant.start(title=title, context=summary)
        self.ui.write_log(f"SYS: Meeting mode enabled for {app}.")

    def _stop_meeting_mode(self, reason: str = "Meeting mode stopped."):
        with self._meeting_lock:
            was_active = self._meeting_active
            self._meeting_active = False
            self._meeting_event = None
        if was_active:
            self._meeting_assistant.stop()
            self.ui.set_meeting_mode(False, "", "", "")
            self.ui.write_log(f"SYS: {reason}")

    def _enable_local_voice_mode(self):
        """Switch to fully local/offline voice pipeline (faster-whisper -> Ollama -> Piper/espeak-ng)."""
        if self._local_voice_mode:
            self.speak("Already in offline mode, sir.")
            return
        self._local_voice_mode = True
        # Close Gemini Live session if active
        if self.session:
            try:
                self.session.close()
            except Exception:
                pass
            self.session = None
        self.ui.write_log("SYS: Switched to LOCAL voice mode (offline).")
        self.speak("Switched to offline mode. All voice processing now runs locally on your machine.")

    def _disable_local_voice_mode(self):
        """Switch back to Gemini Live (cloud) voice pipeline."""
        if not self._local_voice_mode:
            self.speak("Already in online mode, sir.")
            return
        self._local_voice_mode = False
        self.ui.write_log("SYS: Switched to ONLINE voice mode (Gemini Live).")
        self.speak("Switched to online mode. Voice processing now uses Gemini Live.")
        # The next voice command will trigger a new Gemini Live connection

    def _run_local_voice_pipeline(self, text: str):
        """Process a text command through the local voice pipeline (Ollama -> local TTS)."""
        try:
            from ollama_client import client as ollama_client, OllamaUnavailable
        except ImportError:
            self.speak("Local voice pipeline not available — Ollama client missing.")
            return

        SYSTEM_PROMPT = (
            "You are Jarvis, running in fully offline/local mode. "
            "Be concise, helpful, and natural — this reply will be "
            "spoken aloud, so keep it short and conversational."
        )

        try:
            reply = ollama_client.chat(text, system=SYSTEM_PROMPT)
        except OllamaUnavailable as e:
            reply = f"Local model unavailable: {e}"

        self.ui.write_log(f"Jarvis (local): {reply}")
        if not self.ui.muted:
            self.speak(reply)

    def _on_meeting_update(self, payload: dict):
        if not isinstance(payload, dict):
            return
        active = bool(payload.get("active"))
        title = payload.get("title") or "Meeting mode"
        summary = payload.get("summary") or ""
        answer = payload.get("answer") or ""
        speech = payload.get("speech") or ""
        self.ui.set_meeting_mode(active, title, summary, answer, speech)
        if summary:
            self.ui.write_log(f"[Meeting] {summary}")
        if answer:
            self.ui.write_log(f"Jarvis: {answer}")

    def _on_meeting_state(self, state: str):
        if state == "LISTENING":
            self.ui.set_state("LISTENING")
        elif state == "MEETING":
            self.ui.set_state("THINKING")

    def _attention_matches(self, text: str, words: tuple[str, ...]) -> bool:
        t = (text or "").lower()
        return any(word in t for word in words)

    def _prompt_message_reply(self, event: dict) -> bool:
        if not isinstance(event, dict):
            return False
        with self._attention_lock:
            self._pending_reply_event = dict(event)
            self._pending_attention = None
            self._reply_mode = True

        message = "What would you like to say in reply?"
        self.ui.write_log(f"SYS: {message}")
        threading.Thread(target=speak_native, args=(message,), daemon=True).start()
        try:
            self.ui.begin_task_workspace(
                "Replying to message",
                [
                    "Type your response",
                    "I will reword it naturally",
                    f"Send via {event.get('app', 'the app')}",
                ],
                source="reply",
            )
            self.ui.update_task_workspace(
                status="Awaiting your reply",
                output="Type the message you want to send, and I will make it sound natural before sending it as you.",
                percent=10,
            )
        except Exception:
            pass
        return True

    def _handle_pending_reply(self, text: str) -> bool:
        with self._attention_lock:
            event = dict(self._pending_reply_event or {})
            self._pending_reply_event = None
        if not event:
            return False

        lower = (text or "").lower()
        if self._attention_matches(lower, ("cancel", "never mind", "skip", "do not send", "don't send")):
            self._reply_mode = False
            self.ui.write_log("SYS: Reply cancelled.")
            try:
                self.ui.finish_task_workspace("Reply cancelled.", "Cancelled", 100)
            except Exception:
                pass
            return True

        self.ui.write_log(f"SYS: Drafting reply to {event.get('title') or event.get('app')}.")
        threading.Thread(target=self._draft_and_send_reply, args=(event, text), daemon=True).start()
        return True

    def _rewrite_reply_text(self, user_text: str, event: dict) -> str:
        prompt = (
            "You are a friendly assistant helping a user rewrite their draft reply for a chat message. "
            "Keep the same meaning and intent, expand the wording slightly, and make it sound natural and human. "
            "Do not mention the notification, app, or any internal system details. "
            "Return only the rewritten reply text.\n\n"
            "Notification context:\n"
            f"App: {event.get('app', '')}\n"
            f"Sender: {event.get('title', '')}\n"
            f"Preview: {event.get('preview', '')}\n\n"
            "User draft reply:\n"
            f"{user_text}\n\n"
            "Reply text:"
        )
        rewrite_system = "You are a friendly assistant. Rewrite the reply naturally and humanely."

        if not is_online():
            try:
                return ollama_client.chat(prompt, system=rewrite_system)
            except OllamaUnavailable:
                return user_text

        try:
            return _gemini_text_reply(prompt) or user_text
        except Exception:
            pass
        try:
            return openrouter_client.chat(prompt, system=rewrite_system)
        except Exception:
            pass
        try:
            return groq_client.chat(prompt, system=rewrite_system)
        except Exception:
            pass
        try:
            return nrouter_client.chat(prompt, system=rewrite_system)
        except Exception:
            pass
        try:
            return ollama_client.chat(prompt, system=rewrite_system)
        except OllamaUnavailable:
            return user_text

    def _draft_and_send_reply(self, event: dict, text: str):
        try:
            reply_text = self._rewrite_reply_text(text, event)
            if not reply_text:
                reply_text = text
            self.ui.update_task_workspace(
                status="Sending reply",
                output="Sending your expanded reply now...",
                percent=70,
            )
            receiver = (event.get("title") or "").strip()
            platform = (event.get("app") or "whatsapp").strip()
            if not receiver:
                self.ui.write_log("ERR: Could not determine recipient for reply.")
                try:
                    self.ui.finish_task_workspace("Reply failed: recipient not found.", "Reply failed", 100)
                except Exception:
                    pass
                return
            result = send_message(
                parameters={
                    "receiver": receiver,
                    "message_text": reply_text,
                    "platform": platform,
                },
                player=self.ui,
            )
            self._reply_mode = False
            self.ui.write_log(f"SYS: {result}")
            try:
                self.ui.finish_task_workspace(reply_text, "Reply delivered.", 100)
            except Exception:
                pass
        except Exception as e:
            self._reply_mode = False
            self.ui.write_log(f"ERR: Reply failed: {e}")
            try:
                self.ui.finish_task_workspace(f"Reply failed: {e}", "Reply failed", 100)
            except Exception:
                pass
        finally:
            if not self.ui.muted:
                self.ui.set_state("LISTENING")

    def _handle_attention_response(self, text: str) -> bool:
        with self._attention_lock:
            event = dict(self._pending_attention or {})
        if not event:
            return False

        kind = (event.get("kind") or "message").strip().lower()
        lower = (text or "").lower()

        if kind == "message":
            if self._attention_matches(lower, ("reply", "respond", "answer", "write back", "send reply", "send a reply")):
                return self._prompt_message_reply(event)
            if self._attention_matches(lower, ("hear", "read", "what is it", "tell me", "show it", "open it")):
                preview = read_event_preview(event)
                self.ui.write_log(f"Jarvis: {preview}")
                threading.Thread(target=speak_native, args=(preview,), daemon=True).start()
                with self._attention_lock:
                    self._pending_attention = None
                return True
            if self._attention_matches(lower, ("ignore", "dismiss", "skip", "no", "not now")):
                self.ui.write_log("SYS: Message alert dismissed.")
                with self._attention_lock:
                    self._pending_attention = None
                return True
            return False

        if kind == "call":
            if self._attention_matches(lower, ("pick up", "answer", "accept", "take it", "join")):
                result = handle_call_action(event, "accept")
                self.ui.write_log(f"SYS: {result}")
                threading.Thread(target=speak_native, args=(result,), daemon=True).start()
                with self._attention_lock:
                    self._pending_attention = None
                return True
            if self._attention_matches(lower, ("ignore", "decline", "reject", "cut", "hang up", "end")):
                result = handle_call_action(event, "decline")
                self.ui.write_log(f"SYS: {result}")
                threading.Thread(target=speak_native, args=(result,), daemon=True).start()
                with self._attention_lock:
                    self._pending_attention = None
                return True
            if self._attention_matches(lower, ("x", "nothing", "do nothing", "close")):
                self.ui.write_log("SYS: Call alert dismissed.")
                with self._attention_lock:
                    self._pending_attention = None
                return True
            return False

        return False

    def _on_attention_action(self, event: dict, decision: str):
        if not isinstance(event, dict):
            return
        kind = (event.get("kind") or "message").strip().lower()
        decision = (decision or "").strip().lower()

        if kind == "meeting":
            if decision == "stop":
                self._stop_meeting_mode()
            return

        if kind == "message":
            if decision == "hear":
                preview = read_event_preview(event)
                self.ui.write_log(f"Jarvis: {preview}")
                threading.Thread(target=speak_native, args=(preview,), daemon=True).start()
            elif decision == "reply":
                self._prompt_message_reply(event)
                return
            else:
                self.ui.write_log("SYS: Message alert dismissed.")
            with self._attention_lock:
                self._pending_attention = None
            return

        if kind == "call":
            if decision in {"accept", "answer", "pick_up"}:
                result = handle_call_action(event, "accept")
                self.ui.write_log(f"SYS: {result}")
                threading.Thread(target=speak_native, args=(result,), daemon=True).start()
            elif decision in {"noop", "x", "none"}:
                self.ui.write_log("SYS: Call alert dismissed.")
            else:
                result = handle_call_action(event, "decline")
                self.ui.write_log(f"SYS: {result}")
                threading.Thread(target=speak_native, args=(result,), daemon=True).start()
            with self._attention_lock:
                self._pending_attention = None


    def _fallback_reply(self, text: str, memory_ctx: str = ""):
        try:
            self.ui.set_state("THINKING")
            try:
                self.ui.update_task_workspace(
                    status="Thinking",
                    output="Jarvis is drafting a direct reply.",
                    percent=35,
                )
            except Exception:
                pass
            reply = ""
            gemini_first = not self._use_openrouter_first
            request_text = f"{memory_ctx}\n\nCurrent User Request:\n{text}" if memory_ctx else text

            SYSTEM_PROMPT = (
                "You are Jarvis, a concise, helpful desktop assistant. "
                "Reply naturally and briefly. Do not mention internal implementation details."
            )

            online = is_online()
            if not online:
                print("[JARVIS] 📴 Offline — skipping cloud providers, using local Qwen directly.")
                try:
                    reply = ollama_client.chat(request_text, system=SYSTEM_PROMPT)
                except OllamaUnavailable as e:
                    print(f"[JARVIS] ⚠️ Offline and local Qwen unavailable: {e}")

            if online and gemini_first:
                try:
                    reply = _gemini_text_reply(request_text)
                except Exception as e:
                    print(f"[JARVIS] ⚠️ Gemini fallback failed: {e}")
                    if _is_gemini_limit_error(e):
                        self._use_openrouter_first = True

            # Requested fallback order: Gemini, OpenRouter, Groq, nRouter, Ollama.
            if online and not reply:
                try:
                    reply = openrouter_client.chat(
                        request_text,
                        system=SYSTEM_PROMPT,
                    )
                except Exception as e:
                    print(f"[JARVIS] ⚠️ OpenRouter fallback failed: {e}")
                    if gemini_first and not self._use_openrouter_first and _is_gemini_limit_error(e):
                        self._use_openrouter_first = True

            if online and not reply:
                try:
                    reply = groq_client.chat(request_text, system=SYSTEM_PROMPT)
                except Exception as e:
                    print(f"[JARVIS] ⚠️ Groq fallback failed: {e}")

            if online and not reply:
                try:
                    reply = nrouter_client.chat(request_text, system=SYSTEM_PROMPT)
                except Exception as e:
                    print(f"[JARVIS] ⚠️ nRouter fallback failed: {e}")

            # Last resort: local Qwen (Ollama).
            if online and not reply:
                try:
                    reply = ollama_client.chat(
                        request_text,
                        system=(
                            "You are Jarvis, a concise, helpful desktop assistant. "
                            "Reply naturally and briefly. Do not mention internal implementation details."
                        ),
                    )
                except OllamaUnavailable as e:
                    print(f"[JARVIS] ⚠️ Local Qwen also unavailable: {e}")
            reply = (reply or "").strip()
            if not reply:
                reply = "I'm ready, sir."
            self.ui.write_log(f"Jarvis: {reply}")
            
            # Save full conversation to Obsidian
            if getattr(self, '_obsidian_logged', False) and getattr(self, '_obsidian_user_text', ''):
                try:
                    from obsidian_integration import save_conversation
                    save_conversation(self._obsidian_user_text, reply)
                except Exception:
                    pass

            try:
                self.ui.finish_task_workspace(reply, "Reply delivered.", 100)
            except Exception:
                pass
            if not self.ui.muted:
                self.ui.set_state("LISTENING")
            return reply
        except Exception as e:
            msg = f"Fallback reply failed: {e}"
            print(f"[JARVIS] ⚠️ {msg}")
            self.ui.write_log(f"ERR: {msg}")
            try:
                self.ui.finish_task_workspace(msg, "Reply failed.", 100)
            except Exception:
                pass
            return msg
            if not self.ui.muted:
                self.ui.set_state("LISTENING")

    def set_speaking(self, value: bool, force: bool = False):
        """Set the mic gate.

        Turning it on arms a short tail, and turning it off only *re-arms*
        that tail -- the release itself is the watchdog's job. Hard-clearing
        on turn_complete was the bug: the room is still ringing after the
        last chunk is written, and listening then transcribes our own voice
        as the user. Pass force=True only when playback was aborted.
        """
        with self._speaking_lock:
            if value:
                self._is_speaking = True
                self._speaking_until = time.monotonic() + (self._echo_guard_ms / 1000.0)
            elif force:
                self._is_speaking = False
                self._speaking_until = 0.0
            elif self._is_speaking:
                # keep waiting for the tail to lapse
                self._speaking_until = time.monotonic() + (self._echo_guard_ms / 1000.0)
        if value:
            self.ui.set_state("SPEAKING")
        elif not self._is_speaking_now() and not self.ui.muted:
            self.ui.set_state("LISTENING")

    def _is_speaking_now(self) -> bool:
        with self._speaking_lock:
            return self._is_speaking

    def note_audio_played(self) -> None:
        """Called for every chunk written to the speaker. Keeps the echo gate
        closed for as long as our voice is actually in the air."""
        with self._speaking_lock:
            self._is_speaking = True
            self._speaking_until = time.monotonic() + (self._echo_guard_ms / 1000.0)

    def _expire_speaking_gate(self) -> None:
        """Watchdog: release the mic once the tail has elapsed."""
        with self._speaking_lock:
            if not self._is_speaking:
                return
            if time.monotonic() < self._speaking_until:
                return
            if getattr(self, "audio_in_queue", None) and not self.audio_in_queue.empty():
                self._speaking_until = time.monotonic() + 0.25
                return
            self._is_speaking = False
        if not self.ui.muted:
            self.ui.set_state("LISTENING")

    def _mark_user_turn(self, text: str) -> None:
        """Record a genuine user turn and open the tool gate for it."""
        text = (text or "").strip()
        if not text:
            return
        self._last_user_text = text
        self._user_turn_active = True

    def _close_user_turn(self) -> None:
        self._user_turn_active = False

    def _tool_gate_open(self) -> bool:
        return bool(self._user_turn_active and self._last_user_text.strip())

    def _looks_like_echo(self, text: str) -> bool:
        """True when the "user" transcript is really our own voice.

        Two independent triggers, both observed in the wild:
          * the tail of our own playback bleeding into the mic, and
          * Edge TTS alerts (speak_native) playing over an open mic, which
            never went through set_speaking at all.
        Comparing against what we just said catches the residue either way.
        """
        if self._is_speaking_now():
            return True
        norm = " ".join((text or "").lower().split())
        if len(norm) < 8:
            return False
        for said in self._recent_jarvis_speech:
            other = " ".join(said.lower().split())
            if not other:
                continue
            if norm in other or other in norm:
                return True
            a, b = set(norm.split()), set(other.split())
            if a and b and len(a & b) / len(a) > 0.7:
                return True
        return False

    def speak(self, text: str):
        if not self._loop or not self.session:
            return
        asyncio.run_coroutine_threadsafe(
            self._session_write(
                "send_client_content",
                turns={"parts": [{"text": text}]},
                turn_complete=True,
            ),
            self._loop
        )

    def speak_error(self, tool_name: str, error: str):
        short = str(error)[:120]
        self.ui.write_log(f"ERR: {tool_name} — {short}")
        self.speak(f"Sir, {tool_name} encountered an error. {short}")

    def _build_config(self) -> types.LiveConnectConfig:
        from datetime import datetime

        memory     = load_memory()
        mem_str    = format_memory_for_prompt(memory)
        sys_prompt = _load_system_prompt()

        now      = datetime.now()
        time_str = now.strftime("%A, %B %d, %Y — %I:%M %p")
        time_ctx = (
            f"[CURRENT DATE & TIME]\n"
            f"Right now it is: {time_str}\n"
            f"Use this to calculate exact times for reminders.\n\n"
        )

        parts = [time_ctx]
        if mem_str:
            parts.append(mem_str)
        parts.append(sys_prompt)
        parts.append(
            "Wake-word mode: if the microphone is muted, still listen for the words 'Jarvis', 'hey', 'hi', and 'hello'. "
            "When you hear one of these activation cues, keep the session friendly and concise, "
            "and wait for the user's next command."
        )

        return types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            output_audio_transcription={},
            input_audio_transcription={},
            system_instruction="\n".join(parts),
            tools=[{"function_declarations": TOOL_DECLARATIONS}],
            session_resumption=types.SessionResumptionConfig(),
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Charon"
                    )
                )
            ),
        )

    async def _session_write(self, method: str, **kwargs):
        """Every websocket write goes through one lock.

        The `websockets` library cannot handle concurrent ``send()`` from more
        than one task: frames interleave and the server closes the connection
        with 1007 "invalid frame payload data". The audio task writes about
        sixteen times a second, so a tool response or a typed command landing
        mid-stream was corrupting the connection and killing the session --
        which is why the assistant went quiet right after running a tool.
        """
        async with self._ws_lock:
            return await getattr(self.session, method)(**kwargs)

    async def _execute_tool(self, fc) -> types.FunctionResponse:
        name = fc.name
        args = dict(fc.args or {})

        print(f"[JARVIS] 🔧 {name}  {args}")
        self.ui.set_state("THINKING")
        try:
            self.ui.update_task_workspace(
                title=f"Running {name}",
                status=f"Executing {name}",
                output="Waiting for the tool to finish.",
                percent=45,
            )
        except Exception:
            pass
        if name == "save_memory":
            category = args.get("category", "notes")
            key      = args.get("key", "")
            value    = args.get("value", "")
            if key and value:
                update_memory({category: {key: {"value": value}}})
                print(f"[Memory] 💾 save_memory: {category}/{key} = {value}")
                try:
                    self.ui.finish_task_workspace("Memory saved.", "Memory updated.", 100)
                except Exception:
                    pass
            if not self.ui.muted:
                self.ui.set_state("LISTENING")
            return types.FunctionResponse(
                id=fc.id, name=name,
                response={"result": "ok", "silent": True}
            )

        if name == "recall_chat_history":
            mode = str(args.get("mode", "search")).lower()
            try:
                from chat_history_manager import search, get_day, get_relative_day, summarize_matches
                if mode == "day":
                    date_arg = str(args.get("date", "today")).strip().lower()
                    if date_arg == "today":
                        _, content = get_relative_day(0)
                    elif date_arg == "yesterday":
                        _, content = get_relative_day(1)
                    else:
                        content = get_day(date_arg)
                    result_text = content if content else f"I don't have any conversation history logged for {date_arg}."
                else:
                    query = args.get("query", "")
                    result_text = summarize_matches(query) if query else "I need a topic to search for."
            except Exception as e:
                result_text = f"Couldn't access chat history: {e}"

            try:
                self.ui.finish_task_workspace(result_text, "Recall complete.", 100)
            except Exception:
                pass
            if not self.ui.muted:
                self.ui.set_state("LISTENING")
            print(f"[JARVIS] 📤 {name} → {str(result_text)[:80]}")
            return types.FunctionResponse(
                id=fc.id, name=name,
                response={"result": result_text}
            )

        loop   = asyncio.get_event_loop()
        result = "Done."

        try:
            if name == "open_app":
                r = await loop.run_in_executor(None, lambda: open_app(parameters=args, response=None, player=self.ui))
                result = r or f"Opened {args.get('app_name')}."

            elif name == "weather_report":
                r = await loop.run_in_executor(None, lambda: weather_action(parameters=args, player=self.ui))
                result = r or "Weather delivered."
                # Feed the Command Center's bottom bar from the real report
                # instead of leaving the shipped placeholder text there.
                try:
                    city = str(args.get("city") or "").strip()
                    if city:
                        self.ui.set_location(city)
                    detail = args.get("result") or args.get("data") or {}
                    if isinstance(detail, dict):
                        temp = detail.get("temp") or detail.get("temperature")
                        desc = (detail.get("description") or detail.get("condition")
                                or detail.get("summary") or "")
                        if temp is not None or desc:
                            self.ui.set_weather(str(desc), temp)
                except Exception:
                    pass
                # Feed the Command Center's bottom bar from the real report
                # instead of leaving the shipped placeholder text there.
                try:
                    city = str(args.get("city") or "").strip()
                    if city:
                        self.ui.set_location(city)
                    detail = args.get("result") or args.get("data") or {}
                    if isinstance(detail, dict):
                        temp = detail.get("temp") or detail.get("temperature")
                        desc = (detail.get("description") or detail.get("condition")
                                or detail.get("summary") or "")
                        if temp is not None or desc:
                            self.ui.set_weather(str(desc), temp)
                except Exception:
                    pass

            elif name == "browser_control":
                r = await loop.run_in_executor(None, lambda: browser_control(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "file_controller":
                r = await loop.run_in_executor(None, lambda: file_controller(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "send_message":
                r = await loop.run_in_executor(None, lambda: send_message(parameters=args, response=None, player=self.ui, session_memory=None))
                result = r or f"Message sent to {args.get('receiver')}."

            elif name == "reminder":
                r = await loop.run_in_executor(None, lambda: reminder(parameters=args, response=None, player=self.ui))
                result = r or "Reminder set."

            elif name == "youtube_video":
                r = await loop.run_in_executor(None, lambda: youtube_video(parameters=args, response=None, player=self.ui))
                result = r or "Done."
            elif name == "file_processor":
                if not args.get("file_path") and self.ui.current_file:
                    args["file_path"] = self.ui.current_file
                r = await loop.run_in_executor(
                    None,
                    lambda: file_processor(parameters=args, player=self.ui, speak=self.speak)
                )
                result = r or "Done."

            elif name == "presentation_builder":
                r = await loop.run_in_executor(
                    None,
                    lambda: create_presentation(parameters=args, player=self.ui)
                )
                result = r or "Presentation created."

            elif name == "spreadsheet_builder":
                r = await loop.run_in_executor(
                    None,
                    lambda: create_spreadsheet(parameters=args, player=self.ui)
                )
                result = r or "Spreadsheet created."


            elif name == "word_document":
                if not args.get("file_path") and self.ui.current_file:
                    current_file = Path(self.ui.current_file)
                    if current_file.suffix.lower() == ".docx":
                        args["file_path"] = self.ui.current_file
                r = await loop.run_in_executor(
                    None,
                    lambda: word_document(parameters=args, player=self.ui, speak=self.speak)
                )
                result = r or "Word document handled."

            elif name == "pdf_document":
                r = await loop.run_in_executor(
                    None,
                    lambda: create_pdf(parameters=args, player=self.ui)
                )
                result = r or "PDF created."


            elif name == "computer_settings":
                r = await loop.run_in_executor(None, lambda: computer_settings(parameters=args, response=None, player=self.ui))
                result = r or "Done."

            elif name == "desktop_control":
                r = await loop.run_in_executor(None, lambda: desktop_control(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "agent_task":
                # Delegate to the orchestrator, which decomposes the objective
                # and runs the right specialists in dependency order. The old
                # path submitted to a TaskQueue whose worker was never started,
                # so objectives sat in a queue and were never carried out.
                import agent_runtime as _ar
                receipt = _ar.submit(
                    args.get("goal", ""),
                    objective=args.get("objective"),
                    context=args.get("context"),
                    priority=args.get("priority", "normal"),
                    request_id=args.get("request_id"),
                    requirements=args.get("requirements"),
                    constraints=args.get("constraints"),
                    expected_output=args.get("expected_output", ""),
                    references=args.get("references"),
                )
                if not receipt.get("ok"):
                    result = f"Could not delegate: {receipt.get('error')}"
                else:
                    result = receipt["message"]
                    try:
                        self.ui.begin_task_workspace(
                            args.get("goal", ""),
                            ["Decompose the objective",
                             "Research Agent gathers what is needed",
                             "Document Agent produces the deliverables",
                             "Verify the files exist and are valid",
                             "Report back"],
                            source="delegate")
                    except Exception:
                        pass

            elif name == "agent_status":
                import agent_runtime as _ar
                if args.get("detail"):
                    info = _ar.progress()
                    steps = "\n".join(f"  {i + 1}. {s['text']}"
                                      for i, s in enumerate(info["steps"]))
                    result = (_ar.status_text()
                              + (f"\nObjective: {info['goal']}" if info["goal"] else "")
                              + (f"\nCompleted steps:\n{steps}" if steps else ""))
                else:
                    result = _ar.status_text()

            elif name == "agent_cancel":
                import agent_runtime as _ar
                task_id = str(args.get("task_id") or "").strip()
                result = (
                    f"HELIX task {task_id} cancelled."
                    if task_id and _ar.cancel(task_id)
                    else f"Could not cancel HELIX task {task_id or '(missing id)'}."
                )

            elif name == "web_search":
                r = await loop.run_in_executor(None, lambda: web_search_action(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "computer_control":
                r = await loop.run_in_executor(None, lambda: computer_control(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "game_updater":
                r = await loop.run_in_executor(None, lambda: game_updater(parameters=args, player=self.ui, speak=self.speak))
                result = r or "Done."

            elif name == "flight_finder":
                r = await loop.run_in_executor(None, lambda: flight_finder(parameters=args, player=self.ui))
                result = r or "Done."
            elif name == "shutdown_jarvis":
                self.ui.write_log("SYS: Shutdown requested.")
                self.speak("Goodbye, sir.")

                def _shutdown():
                    import time, sys, os
                    time.sleep(1)
                    os._exit(0)

                threading.Thread(target=_shutdown, daemon=True).start()
            else:
                result = f"Unknown tool: {name}"

        except Exception as e:
            result = f"Tool '{name}' failed: {e}"
            traceback.print_exc()
            self.speak_error(name, e)

        try:
            self.ui.finish_task_workspace(result, "Task completed.", 100)
        except Exception:
            pass

        tool_voice = None
        try:
            tool_voice = None  # Brahma Connect removed (see CLEANUP_PLAN.md)
        except Exception:
            traceback.print_exc()
        if tool_voice:
            try:
                self.ui.write_log(f"Jarvis: {tool_voice}")
            except Exception:
                pass
            try:
                self.speak(tool_voice)
            except Exception:
                pass

        if not self.ui.muted:
            self.ui.set_state("LISTENING")

        print(f"[JARVIS] 📤 {name} → {str(result)[:80]}")

        return types.FunctionResponse(
            id=fc.id, name=name,
            response={"result": result}
        )

    async def _open_ui_html(self):
        await asyncio.sleep(2)
        try:
            import os
            path = "/home/abubakargcx/Desktop/UI_Logic/jarvis-ui-logic/jarvis-ui.html"
            env = os.environ.copy()
            if env.get("WAYLAND_DISPLAY") and env.get("DISPLAY") and not env.get("QT_QPA_PLATFORM"):
                env["QT_QPA_PLATFORM"] = "xcb"
            subprocess.Popen(
                [sys.executable, str(BASE_DIR / "desktop_ui.py"), path, "ws://127.0.0.1:8875"],
                cwd=str(BASE_DIR),
                env=env,
                start_new_session=True,
            )
        except Exception as e:
            self.ui.write_log(f"Could not open new UI: {e}")

    async def _serve_ui_bridge(self):
        try:
            import bridge_ws
            async def handle_web_command(text, source="web"):
                if self._loop and self.session and not self._local_voice_mode:
                    self._on_text_command(text, source=source)
                    return "Gemini Live is processing your request."
                return await asyncio.to_thread(self._fallback_reply, text)
            bridge_ws.set_command_handler(handle_web_command)
            self.ui.write_log("UI bridge listening on ws://127.0.0.1:8875")
            await bridge_ws.main(8875)
        except Exception as e:
            self.ui.write_log(f"UI bridge error: {e}")

    async def _serve_dashboard(self):
        if self._dashboard is None:
            self.ui.write_log("ERR: Mobile Connect disabled because dashboard dependencies are missing.")
            return
        try:
            self._dashboard.set_connect_callback(self._on_phone_connected)
            self._dashboard.set_wake_callback(lambda: None)
            await self._dashboard.serve()
        except Exception as e:
            self.ui.write_log(f"ERR: Mobile Connect server failed: {e}")
            traceback.print_exc()

    async def _consume_remote_commands(self):
        if self._dashboard is None:
            return
        while True:
            text = await self._dashboard._command_queue.get()
            if text:
                try:
                    self.ui.submit_external_command(text, source="mobile")
                except Exception:
                    self._on_text_command(text, source="mobile")

    async def _relay_phone_audio(self):
        if self._dashboard is None:
            return
        while True:
            frame = await self._dashboard._phone_audio_queue.get()
            if not self.out_queue:
                continue
            self._phone_active = True
            try:
                await self.out_queue.put(frame)
            finally:
                await asyncio.sleep(0.08)
                if self._dashboard._phone_audio_queue.empty():
                    self._phone_active = False

    def _announce_audio(self) -> None:
        try:
            _describe_audio_devices()
        except Exception:
            pass

    def _start_speaking_watchdog(self) -> None:
        """Poll the echo gate so it is always released eventually."""
        if self._watchdog_started:
            return
        self._watchdog_started = True

        def _loop() -> None:
            while True:
                time.sleep(0.15)
                try:
                    self._expire_speaking_gate()
                except Exception:
                    pass

        threading.Thread(target=_loop, daemon=True, name="echo-gate").start()

    async def _send_realtime(self):
        while True:
            msg = await self.out_queue.get()
            # The current Live API expects realtime PCM in the typed audio
            # field; passing the callback's dict directly is not sufficient.
            await self._session_write(
                "send_realtime_input",
                audio=types.Blob(data=msg["data"], mime_type=msg["mime_type"]),
            )

    async def _listen_audio(self):
        print("[JARVIS] 🎤 Mic started")
        loop = asyncio.get_event_loop()

        def _safe_enqueue(item):
            # Real-time audio: if the send side falls behind (slow network,
            # brief API hiccup) it's better to drop a chunk than to spam
            # QueueFull exceptions through asyncio's unhandled-callback-error
            # path -- that was burning enough event-loop time under load to
            # help trigger the "keepalive ping timeout" disconnects seen
            # after long queue-full storms.
            try:
                self.out_queue.put_nowait(item)
            except asyncio.QueueFull:
                try:
                    self.out_queue.get_nowait()  # drop oldest, keep audio fresh
                    self.out_queue.put_nowait(item)
                except Exception:
                    pass

        # Local energy gate. Without it, room tone, a fan, a keyboard or a
        # cough reached the server, the server's VAD "heard" a turn, and the
        # model answered a hallucinated request -- which is how Jarvis ended
        # up searching the web and tidying files with nobody speaking.
        noise_floor = _RMS_FLOOR

        def callback(indata, frames, time_info, status):
            nonlocal noise_floor
            # hw_rate is bound just below, before the stream starts
            with self._speaking_lock:
                brahma_speaking = self._is_speaking
            if self._phone_active:
                return
            if brahma_speaking or (self.ui.muted and
                                    not getattr(self.ui, "_wakeword_listening", False)):
                return

            level = _audio_rms(indata)
            # Drive the Command Center's waveform from the real signal. The
            # UI throttles this, so the audio callback stays cheap.
            try:
                self.ui.set_audio_level(min(1.0, level / 0.06))
            except Exception:
                pass
            if level <= noise_floor * 2.2:
                # slow enough to track the room rather than the speech
                noise_floor = 0.99 * noise_floor + 0.01 * level

            if level < max(noise_floor * _RMS_MARGIN, _RMS_FLOOR):
                return
            data = _resample_pcm16(indata, hw_rate, SEND_SAMPLE_RATE)
            loop.call_soon_threadsafe(
                _safe_enqueue,
                {"data": data, "mime_type": _INPUT_MIME}
            )

        try:
            # resolved by role at import, never a fixed index: a pinned index
            # resolved to a speaker monitor under PipeWire, so the
            # "microphone" was capturing our own playback
            stream, hw_rate = _open_input_stream(SEND_SAMPLE_RATE, CHANNELS,
                                                "int16", CHUNK_SIZE,
                                                callback=callback)
            with stream:
                print(f"[JARVIS] AUDIO mic live at {hw_rate} Hz"
                      + ("" if hw_rate == SEND_SAMPLE_RATE
                         else f" -> {SEND_SAMPLE_RATE} Hz for the model"))
                while True:
                    await asyncio.sleep(0.1)
        except Exception as e:
            # A missing or busy microphone must not take the whole session
            # down: text, GUI and tool use all still work, and plugging a
            # mic back in recovers without a restart. Previously this raised
            # and killed the TaskGroup, ending the assistant entirely.
            print(f"[JARVIS] mic unavailable ({e}) -- "
                  f"running without voice; retrying in 20s")
            self._mic_down = True
            for attempt in range(30):          # ~10 min of retrying
                await asyncio.sleep(20)
                if self._phone_active:
                    continue
                try:
                    st, hw_rate = _open_input_stream(
                        SEND_SAMPLE_RATE, CHANNELS, "int16", CHUNK_SIZE,
                        callback=callback)
                except Exception as exc:
                    print(f"[JARVIS] mic retry: {exc}")
                    continue
                try:
                    st.start()
                    self._mic_down = False
                    print("[JARVIS] microphone recovered")
                    with st:
                        while True:
                            await asyncio.sleep(0.1)
                except Exception as e2:
                    print(f"[JARVIS] mic retry failed: {e2}")
                    continue
            return

    async def _receive_audio(self):
        print("[JARVIS] 👂 Recv started")
        out_buf, in_buf = [], []

        try:
            while True:
                async for response in self.session.receive():

                    if getattr(response, "go_away", None):
                        time_left = getattr(response.go_away, "time_left", None)
                        print(f"[JARVIS] ⚠️ GoAway received (time_left={time_left}) — reconnecting proactively.")
                        raise _GoAwaySignal()

                    if response.data:
                        self.audio_in_queue.put_nowait(response.data)

                    if response.server_content:
                        sc = response.server_content

                        if sc.output_transcription and sc.output_transcription.text:
                            self.set_speaking(True)
                            txt = sc.output_transcription.text.strip()
                            if txt:
                                out_buf.append(txt)
                                self._recent_jarvis_speech.append(txt)

                        if sc.input_transcription and sc.input_transcription.text:
                            txt = sc.input_transcription.text.strip()
                            if txt and self._looks_like_echo(txt):
                                # Our own voice coming back through the mic.
                                # Treating it as a user turn is what made
                                # Jarvis answer himself, save memories about
                                # his own reasoning, and reorganise the
                                # Desktop with nobody speaking.
                                self._echo_drops += 1
                                if self._echo_drops <= 3 or self._echo_drops % 25 == 0:
                                    print(f"[JARVIS] \U0001f7e1 dropped self-echo "
                                          f"({self._echo_drops}): {txt[:60]!r}")
                                txt = ""
                            if txt:
                                try:
                                    from actions.attention_monitor import stop_native_speech
                                    stop_native_speech()
                                except Exception:
                                    pass
                                in_buf.append(txt)
                                if self.ui.muted and _wakeword_detected(txt):
                                    try:
                                        self.ui.set_muted_state(False, wakeword=True)
                                        self.ui.write_log("SYS: Wake word detected. Mic active.")
                                    except Exception:
                                        pass

                        if sc.turn_complete:
                            self.set_speaking(False)

                            full_in = " ".join(in_buf).strip()
                            if full_in:
                                self._mark_user_turn(full_in)
                                self.ui.write_log(f"You: {full_in}")
                            else:
                                self._close_user_turn()
                            in_buf = []

                            full_out = " ".join(out_buf).strip()
                            if full_out:
                                self.ui.write_log(f"Jarvis: {full_out}")
                                try:
                                    import bridge_ws
                                    bridge_ws.broadcast({
                                        "type": "chat", "role": "jarvis", "agent": "jarvis",
                                        "text": full_out,
                                    })
                                except Exception:
                                    pass
                            out_buf = []

                            if full_in or full_out:
                                try:
                                    from chat_history_manager import log_turn
                                    log_turn(full_in, full_out, source="voice")
                                except Exception as e:
                                    print(f"[ChatHistory] ⚠️ log_turn failed: {e}")

                            if full_in and len(full_in) > 5:
                                threading.Thread(
                                    target=_update_memory_async,
                                    args=(full_in, full_out),
                                    daemon=True
                                ).start()

                    if response.tool_call:
                        fn_responses = []
                        for fc in response.tool_call.function_calls:
                            if not self._tool_gate_open():
                                # No genuine user turn behind this call. The
                                # model sometimes opens a turn by itself, and
                                # acting on that meant saving invented
                                # memories and tidying the operator's files
                                # with nobody speaking.
                                self._blocked_tool_calls += 1
                                if (self._blocked_tool_calls <= 3
                                        or self._blocked_tool_calls % 25 == 0):
                                    print(f"[JARVIS] refused {fc.name} -- no "
                                          f"user turn "
                                          f"({self._blocked_tool_calls})")
                                fn_responses.append(types.FunctionResponse(
                                    id=fc.id,
                                    name=fc.name,
                                    response={
                                        "ok": False,
                                        "error": "No user request is active, so "
                                                 "this action was not performed.",
                                    },
                                ))
                                continue
                            print(f"[JARVIS] CALL {fc.name}")
                            fr = await self._execute_tool(fc)
                            fn_responses.append(fr)
                        await self._session_write(
                            "send_tool_response",
                            function_responses=fn_responses,
                        )

        except Exception as e:
            print(f"[JARVIS] ❌ Recv: {e}")
            traceback.print_exc()
            raise

    async def _play_audio(self):
        print("[JARVIS] 🔊 Play started")
        loop = asyncio.get_event_loop()

        stream, out_rate = _open_output_stream(RECEIVE_SAMPLE_RATE, CHANNELS,
                                              "int16", CHUNK_SIZE)
        print(f"[JARVIS] AUDIO speaker live at {out_rate} Hz"
              + ("" if out_rate == RECEIVE_SAMPLE_RATE
                 else f" <- {RECEIVE_SAMPLE_RATE} Hz from the model"))
        stream.start()
        try:
            while True:
                chunk = await self.audio_in_queue.get()
                # Arm the gate before the blocking write, then push the
                # deadline out again per chunk. The queue can drain for an
                # instant between network chunks; clearing the flag there
                # let the room echo back in as "user speech".
                self.note_audio_played()
                pcm = _resample_pcm16(chunk, RECEIVE_SAMPLE_RATE, out_rate)
                await asyncio.to_thread(stream.write, pcm)
                self.note_audio_played()
                if self.audio_in_queue.empty():
                    # the watchdog releases the gate once the tail expires
                    self._expire_speaking_gate()
        except Exception as e:
            print(f"[JARVIS] ❌ Play: {e}")
            raise
        finally:
            self.set_speaking(False)
            stream.stop()
            stream.close()

    async def run(self):
        # announce boot steps to UI overlay (thread-safe wrappers)
        try:
            self.ui.boot_add_step("Load configuration")
            self.ui.boot_add_step("Start attention monitor")
            self.ui.boot_add_step("Start dashboard server")
            self.ui.boot_add_step("Initialize audio")
            self.ui.boot_add_step("Connect AI backend")
            self.ui.boot_add_step("Finalize startup")
            self.ui.boot_set_progress(3, "Preparing startup...")
        except Exception:
            pass

        self._attention_monitor.start()
        try:
            self.ui.boot_set_step_status("Start attention monitor", "done")
            self.ui.boot_set_progress(12, "Attention monitor online")
        except Exception:
            pass
        if self._dashboard is not None:
            if not self._dashboard_started:
                self._dashboard_started = True
                asyncio.create_task(self._serve_dashboard())
                try:
                    self.ui.boot_set_step_status("Start dashboard server", "done")
                    self.ui.boot_set_progress(22, "Mobile connect server running")
                except Exception:
                    pass
            asyncio.create_task(self._consume_remote_commands())
            asyncio.create_task(self._relay_phone_audio())
        asyncio.create_task(self._serve_ui_bridge())
        asyncio.create_task(self._open_ui_html())
        try:
            self.ui.boot_set_progress(36, "Initializing AI client")
        except Exception:
            pass

        client = genai.Client(
            api_key=_get_api_key(),
            http_options={"api_version": "v1beta"}
        )

        # Consecutive-failure tracking for capped exponential backoff. A fixed
        # 5s-forever retry loop hammers Google's servers uselessly if the
        # underlying problem is persistent (e.g. Live API quota/access, not a
        # transient blip) — this backs off up to 60s and prints a clear
        # warning after repeated identical failures instead of retrying
        # silently forever.
        reconnect_attempt = 0
        last_error_text = None

        while True:
            try:
                print("[JARVIS] 🔌 Connecting...")
                self.ui.set_state("THINKING")
                config = self._build_config()

                connect_cm = client.aio.live.connect(model=LIVE_MODEL, config=config)
                session = await asyncio.wait_for(connect_cm.__aenter__(), timeout=LIVE_CONNECT_TIMEOUT)
                try:
                    async with asyncio.TaskGroup() as tg:
                        self.session        = session
                        self._loop          = asyncio.get_event_loop()
                        self.audio_in_queue = asyncio.Queue()
                        self.out_queue      = asyncio.Queue(maxsize=50)

                        print("[JARVIS] ✅ Connected.")
                        reconnect_attempt = 0
                        last_error_text = None
                        try:
                            self.ui.boot_set_step_status("Connect AI backend", "done")
                            self.ui.boot_set_progress(75, "AI backend connected")
                        except Exception:
                            pass
                        self.ui.set_state("LISTENING")
                        self.ui.write_log("SYS: Jarvis online.")

                        tg.create_task(self._send_realtime())
                        self._start_speaking_watchdog()
                        tg.create_task(self._listen_audio())
                        tg.create_task(self._relay_phone_audio())
                        tg.create_task(self._receive_audio())
                        tg.create_task(self._play_audio())
                        try:
                            self.ui.boot_set_step_status("Initialize audio", "done")
                            self.ui.boot_set_progress(92, "Audio subsystems online")
                        except Exception:
                            pass
                        # finalize
                        try:
                            self.ui.boot_set_step_status("Finalize startup", "done")
                            self.ui.boot_set_progress(100, "Startup complete")
                        except Exception:
                            pass
                finally:
                    try:
                        await connect_cm.__aexit__(None, None, None)
                    except Exception:
                        pass
                    
            except Exception as e:
                # GoAway is Gemini Live's expected "close and reconnect now"
                # signal, not a real error -- asyncio.TaskGroup wraps it in an
                # ExceptionGroup since it's raised inside a child task. Handle
                # it as a clean, silent, non-penalized reconnect: no traceback
                # spam, no backoff, no "failed N times" warning.
                is_goaway_only = (
                    isinstance(e, BaseExceptionGroup)
                    and all(isinstance(sub, _GoAwaySignal) for sub in e.exceptions)
                )
                if is_goaway_only:
                    print("[JARVIS] 🔄 GoAway — reconnecting immediately (expected Live API session rotation).")
                    self.session = None
                    self._loop = None
                    reconnect_attempt = 0
                    last_error_text = None
                    continue

                print(f"[JARVIS] ⚠️ {e}")
                traceback.print_exc()
                if _is_gemini_limit_error(e):
                    self._use_openrouter_first = True
                self.session = None
                self._loop = None

                error_text = str(e)
                if error_text == last_error_text:
                    reconnect_attempt += 1
                else:
                    reconnect_attempt = 1
                    last_error_text = error_text

                if reconnect_attempt == 4:
                    print(
                        "[JARVIS] ⚠️ Live API has failed the same way "
                        f"{reconnect_attempt} times in a row: {error_text[:150]}\n"
                        "[JARVIS] ⚠️ This usually means a persistent problem, not a "
                        "network blip — check your Gemini API key's Live API "
                        "quota/access at https://aistudio.google.com. Jarvis will "
                        "keep retrying in the background (text replies via "
                        "OpenRouter/local Qwen still work)."
                    )
            else:
                reconnect_attempt = 0
                last_error_text = None

            self.set_speaking(False)
            self.ui.set_state("LISTENING")
            backoff = min(5 * (2 ** max(0, reconnect_attempt - 1)), 60)
            print(f"[JARVIS] 🔄 Reconnecting in {backoff}s...")
            await asyncio.sleep(backoff)

def _acquire_single_instance_lock():
    """Guarantee one Jarvis per machine.

    Two live instances both open the microphone and both answer, which
    sounds like Jarvis talking to itself.

    A unix socket file survives a crash (the kernel does not delete the
    path), so a plain ``bind()`` would report "already running" forever
    after a hard kill. We therefore probe the existing path first: if
    nothing answers on it, it is stale and safe to replace.
    """
    import hashlib as _hashlib
    import socket as _socket

    name = f"/tmp/jarvis_{os.getuid()}_{_hashlib.sha256(str(BASE_DIR).encode()).hexdigest()[:12]}"

    def _someone_is_listening() -> bool:
        probe = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
        probe.settimeout(0.4)
        try:
            probe.connect(name)
            return True
        except OSError:
            return False
        finally:
            probe.close()

    if os.path.exists(name):
        if _someone_is_listening():
            return None, name          # a real instance owns it
        try:
            os.unlink(name)             # stale leftover — clear it
        except OSError:
            pass

    sock = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
    try:
        sock.bind(name)
    except OSError:
        sock.close()
        return None, name
    try:
        sock.listen(1)
    except Exception:
        pass
    return sock, name


def main():
    _startup_log("main entered")

    _lock_sock, _lock_name = _acquire_single_instance_lock()
    if _lock_sock is None:
        _startup_log(f"another instance already running ({_lock_name})")
        print("[JARVIS] Another Jarvis instance is already running. "
              "Close it first, otherwise two microphones answer at once.")
        return

    _ensure_desktop_shortcut()
    # The Desktop Command Deck is the only visible UI. The Qt object remains
    # hidden as a compatibility adapter for existing backend status methods.
    ui = JarvisUI(str(BASE_DIR / "assets" / "Jarvis_Logo.png"), show_immediately=False)
    dashboard = None
    dashboard_enabled = DashboardServer is not None and not _is_port_in_use(8000)
    if DashboardServer is not None and not dashboard_enabled:
        _startup_log("dashboard disabled: port 8000 already in use")
        try:
            ui.write_log("SYS: Mobile Connect is already running in another Jarvis instance.")
        except Exception:
            pass
    if dashboard_enabled:
        dashboard = DashboardServer()

    if dashboard is not None:
        def _start_dashboard_server():
            try:
                _startup_log("dashboard thread started")
                asyncio.run(dashboard.serve())
            except Exception as exc:
                _startup_log(f"dashboard thread error: {exc}")
                try:
                    ui.write_log(f"ERR: Mobile Connect server failed: {exc}")
                except Exception:
                    pass

        threading.Thread(target=_start_dashboard_server, daemon=True).start()
        _startup_log("dashboard thread spawned")

    _startup_log("legacy Qt UI suppressed; Desktop Command Deck is primary UI")

    # Initialize plugin manager and load any plugins from ./plugins
    try:
        plugin_manager = PluginManager(BASE_DIR)
        plugin_manager.load_plugins()
    except Exception:
        plugin_manager = None

    def runner():
        _startup_log("runner waiting api key")
        ui.wait_for_api_key()
        _startup_log("runner api key ready")

        # Bring up the agent team. Without this nothing started the
        # orchestrator, so `agent_task` had nowhere to delegate to and the
        # Command Center had no live agents to show.
        try:
            import agent_runtime as _agent_runtime
            _agent_runtime.start()

            def _on_agent_event(event: str, data: dict) -> None:
                """Principle 9: JARVIS knows what its agents are doing."""
                if event == "submitted":
                    ui.push_feed(f"Objective delegated: {data.get('goal', '')}"[:160],
                                 "Agent team", "live", "DELEGATE")
                elif event == "progress":
                    ui.push_feed(data.get("message", "")[:160],
                                 data.get("agent", "Agent"), "tip", "AGENT")
                elif event == "complete":
                    ui.push_feed(data.get("headline", "Objective finished"),
                                 "Agent team", "live", "DONE")
                    try:
                        ui.finish_task_workspace(
                            data.get("headline", "Objective finished"),
                            "Verified" if data.get("ok") else "Finished with issues",
                            100)
                    except Exception:
                        pass

            _agent_runtime.subscribe(_on_agent_event)
        except Exception as exc:
            print(f"[JARVIS] agent system unavailable: {exc}")

        jarvis_assistant = JarvisLive(
            ui,
            dashboard=dashboard,
            dashboard_started=dashboard is not None,
            enable_dashboard=dashboard_enabled,
        )
        # Close the mic while Edge TTS plays and remember what we said, so an
        # alert can never be transcribed back in as the user speaking.
        try:
            from actions.attention_monitor import set_speech_hooks

            def _on_tts_speaking(on: bool):
                if on:
                    jarvis_assistant.note_audio_played()
                else:
                    jarvis_assistant.set_speaking(False)

            def _on_tts_spoke(text: str):
                if text:
                    jarvis_assistant._recent_jarvis_speech.append(text.strip())

            set_speech_hooks(_on_tts_speaking, _on_tts_spoke)
        except Exception as _e:
            print(f"[JARVIS] ⚠️ speech hooks not registered: {_e}")

        # Wire the holographic dashboard's isSpeaking() query to JarvisLive's
        # speaking state, so the orb/globe pulse sync with TTS playback.
        try:
            jarvis_assistant.ui.bridge.set_speaking_getter(
                lambda: jarvis_assistant._is_speaking_now()
            )
        except Exception:
            pass

        try:
            if plugin_manager is not None:
                jarvis_assistant.plugin_manager = plugin_manager
                plugin_manager.register_brahma(jarvis_assistant)
                # allow plugins to run a startup hook
                try:
                    plugin_manager.dispatch("on_startup", jarvis_assistant)
                except Exception:
                    pass
        except Exception:
            pass
        try:
            asyncio.run(jarvis_assistant.run())
        except KeyboardInterrupt:
            print("\n🔴 Shutting down...")

    # Exactly one live AI session per process. Two sessions meant two
    # overlapping microphones and two voices answering at once, because a
    # failure in play_boot_sequence() used to fall through to the except
    # branch below and call start_runner() a second time.
    _runner_lock = threading.Lock()
    _runner_started = False

    def start_runner():
        nonlocal _runner_started
        with _runner_lock:
            if _runner_started:
                return
            _runner_started = True
        threading.Thread(target=runner, daemon=True).start()

    start_runner()
    try:
        ui.play_boot_sequence(
            finished_callback=None
        )
    except Exception:
        start_runner()
    ui.root.mainloop()


if __name__ == "__main__":
    import traceback
    try:
        main()
    except Exception as e:
        with open("FATAL_CRASH.log", "w") as f:
            traceback.print_exc(file=f)
        raise
