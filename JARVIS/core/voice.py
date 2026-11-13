"""The one shared voice contract.

JARVIS owns the voice core. HELIX must not keep a second, independent audio
pipeline: it consumes this module for the things that made the two diverge —
model id, voice id, wake words, persona/system prompt, API-key lookup and the
sample rates — and keeps only its own *transport* (a WebSocket proxy, a desktop
speaker, a phone bridge).

What belongs here
-----------------
Configuration and policy that must be identical in both front-ends: which model
speaks, which voice, what the assistant is told about itself, how it is woken,
and how audio is framed.

What does **not** belong here
-----------------------------
Any capture or playback implementation. Those stay behind a transport adapter
so JARVIS's Gemini Live session and HELIX's proxy can differ mechanically while
behaving the same.

Kept import-free on purpose: ``bridge_ws.py`` and the HELIX tools load this from
outside the JARVIS package, so it must not pull in the application.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

# --- audio framing ---------------------------------------------------------
SEND_SAMPLE_RATE = 16000     # microphone -> model, PCM16 mono
RECEIVE_SAMPLE_RATE = 24000  # model -> speaker, PCM16 mono
CHANNELS = 1
SAMPLE_WIDTH_BYTES = 2

# --- model and voice -------------------------------------------------------
# JARVIS is the authoritative voice core, so these defaults are JARVIS's own
# values (main.py's LIVE_MODEL), not the ones HELIX used to carry separately.
LIVE_MODEL = os.environ.get("JARVIS_LIVE_MODEL", "gemini-3.1-flash-live-preview")
LIVE_VOICE = os.environ.get("JARVIS_LIVE_VOICE", "Charon")

# --- activation ------------------------------------------------------------
# Both spellings are accepted; the model is told to acknowledge rather than
# answer them, because the microphone is muted until the wake word arrives.
WAKE_PHRASES = ("jarvis", "hey jarvis", "wake up jarvis", "helix", "hey helix")

# --- persona ---------------------------------------------------------------
IDENTITY_PROMPT = (
    "You are JARVIS, a personal AI assistant running on the user's own machine. "
    "You are concise and direct: answer in one or two short sentences unless "
    "detail is asked for. Address the user as 'sir'. "
    "You may speak English and Urdu. "
)

WAKE_PROMPT = (
    "Wake-word mode: the microphone is muted by default. When you hear one of "
    f"{', '.join(repr(w) for w in WAKE_PHRASES)} on its own, do not answer it — "
    "acknowledge briefly that you are listening and wait for the actual command."
)

BARGE_IN_PROMPT = (
    "If the user talks over you, stop immediately and listen. Never mute the "
    "microphone while speaking: being interruptible matters more than finishing."
)

LONG_RESULT_PROMPT = (
    "For work that takes a while, say that you are starting it rather than "
    "reading the whole result aloud."
)

SYSTEM_PROMPT = " ".join(
    (IDENTITY_PROMPT, LONG_RESULT_PROMPT, BARGE_IN_PROMPT, WAKE_PROMPT)
)


def system_prompt(extra: str = "") -> str:
    """The shared persona, optionally extended by a transport-specific rider."""
    extra = (extra or "").strip()
    return f"{SYSTEM_PROMPT} {extra}".strip() if extra else SYSTEM_PROMPT


# --- credentials -----------------------------------------------------------
_ENV_CANDIDATES = (
    Path(os.path.expanduser("~")) / ".hermes" / ".env",
    Path(os.path.expanduser("~")) / ".config" / "jarvis" / "voice.env",
)
_KEY_RE = re.compile(r"^\s*GEMINI_API_KEY\s*=\s*(\S+)\s*$")


def read_gemini_key(env_path: Optional[str] = None) -> str:
    """Return the Gemini key from the environment, else a private env file.

    Never logs or returns the key anywhere but the caller. Accepts a bare key
    file or a ``KEY=value`` line so the machine can hold the key on its own.
    """
    candidates = []
    if env_path:
        candidates.append(Path(os.path.expanduser(env_path)))
    candidates.extend(_ENV_CANDIDATES)
    for path in candidates:
        try:
            if not path.is_file():
                continue
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                match = _KEY_RE.match(line)
                if match:
                    return match.group(1).strip().strip("\"'")
                if "=" not in line and len(line) > 20:
                    return line.strip("\"'")
        except OSError:
            continue
    return os.environ.get("GEMINI_API_KEY", "").strip()


def frames_for(seconds: float, rate: int = SEND_SAMPLE_RATE) -> int:
    """How many 20 ms frames a duration is worth — used by diagnostics."""
    return max(1, round(seconds * rate / (rate * 0.02)))
