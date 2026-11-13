#!/usr/bin/env python3
"""Gemini Live voice proxy for Helix.

Why this exists: the Gemini API key must never be reachable from a browser, but
Live is a bidirectional WebSocket, so something has to sit in the middle. This
process holds the key and relays audio between the Voice Core page and Gemini
Live. It binds to 127.0.0.1 only.

This file is a TRANSPORT. It is not a second voice core: the model, voice,
persona, wake words, sample rates and key lookup are all imported from
``JARVIS/core/voice.py``, which is the one place those are defined. If that
module cannot be found the service refuses to start rather than silently
drifting back into its own copy of the persona.

Protocol, browser <-> here:
    binary  mic audio in   (PCM16 mono 16 kHz)
    binary  model audio out (PCM16 mono 24 kHz)
    text    JSON control: {"type": ready|state|transcript|reply|interrupted|error, ...}

Barge-in is handled by Gemini, not by us. The old Jarvis muted the mic for a
fixed window after TTS and discarded any transcript resembling the reply, which
is precisely why it could not be interrupted. Nothing here does that: mic audio
keeps flowing while the model speaks, and Google decides when to stop talking.
"""
import asyncio, json, os, re, sys

from google import genai
from google.genai import types
from websockets.asyncio.server import serve

# --- shared voice contract ---------------------------------------------------
# JARVIS owns the voice core. Set JARVIS_ROOT when HELIX is deployed without a
# sibling JARVIS checkout; there is deliberately no local copy of these values.
_JARVIS_ROOT = os.path.abspath(os.environ.get(
    "JARVIS_ROOT",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "JARVIS"),
))
sys.path.insert(0, _JARVIS_ROOT)
try:
    from core.voice import (  # noqa: E402
        LIVE_MODEL as MODEL,
        LIVE_VOICE as VOICE,
        SEND_SAMPLE_RATE as RATE,
        read_gemini_key,
        system_prompt,
    )
except Exception as exc:  # deployment guard, not a fallback
    raise SystemExit(
        f"HELIX requires the shared JARVIS voice core at "
        f"{_JARVIS_ROOT}/core/voice.py ({exc}). Set JARVIS_ROOT to the JARVIS checkout."
    )

HOST, PORT = "127.0.0.1", int(os.environ.get("HELIX_LIVE_PORT", "8788"))
ENV = os.path.expanduser("~/.hermes/.env")

# HELIX-specific rider only. Identity, tone, barge-in and wake-word policy all
# come from the shared contract, so the two assistants cannot diverge there.
HELIX_RIDER = (
    "You are HELIX, the voice interface to a local multi-agent system on this "
    "machine. You can dispatch work to specialist agents (research, documents, "
    "system control, development, vision, messaging, career); for anything long, "
    "say you are starting it rather than reading the whole result aloud. Your "
    "activation cues are 'helix', 'hey helix' and 'hi helix'."
)
SYSTEM = system_prompt(HELIX_RIDER)


def read_key():
    """Read GEMINI_API_KEY through the shared contract. Never logged."""
    return read_gemini_key(ENV)


async def handle(ws):
    key = read_key()
    if not key:
        await ws.send(json.dumps({"type": "error",
                                  "error": "GEMINI_API_KEY not set"}))
        await ws.close()
        return

    await ws.send(json.dumps({"type": "ready", "model": MODEL, "voice": VOICE}))
    # Per-connection counters. Without these the proxy is silent and a dead
    # audio path is indistinguishable from a quiet model.
    stats = {"in_frames": 0, "in_bytes": 0, "out_frames": 0, "out_bytes": 0}
    client = genai.Client(api_key=key, http_options={"api_version": "v1beta"})
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        input_audio_transcription={},
        output_audio_transcription={},
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=VOICE))),
        system_instruction=SYSTEM,
    )

    try:
        async with client.aio.live.connect(model=MODEL, config=config) as session:
            await ws.send(json.dumps({"type": "state", "state": "connected"}))

            async def to_gemini():
                """Browser -> Gemini. Audio frames go straight through."""
                async for msg in ws:
                    if isinstance(msg, bytes):
                        stats["in_frames"] += 1
                        stats["in_bytes"] += len(msg)
                        if len(msg) < 2:
                            continue
                        try:
                            await session.send_realtime_input(
                                audio=types.Blob(
                                    data=msg, mime_type=f"audio/pcm;rate={RATE}"))
                        except Exception:                 # session ended
                            return
                    elif isinstance(msg, str) and msg:
                        try:
                            await session.send_client_content(
                                    turns=[types.Content(
                                        role="user",
                                        parts=[types.Part(text=msg)])],
                                    turn_complete=True)
                        except Exception:
                            return

            async def to_browser():
                """Gemini -> browser. Audio out as binary, everything else as JSON.

                `session.receive()` is a one-shot generator that ends after ONE model
                turn, so it must be re-entered per turn. Treating its end as "the
                conversation is over" tore the session down after the first reply.
                """
                while True:
                    try:
                        async for msg in session.receive():
                            sc = msg.server_content
                            if msg.data:
                                # Count BEFORE sending. These counters were
                                # briefly missing while shape-logging was added,
                                # and they reported 0 while a raw client was
                                # demonstrably receiving audio - i.e. the
                                # instrumentation lied and nearly sent me
                                # hunting a bug that was not in this file.
                                stats["out_frames"] += 1
                                stats["out_bytes"] += len(msg.data)
                                await ws.send(msg.data)
                            if sc is None:
                                continue
                            interim = getattr(sc, "interim_input_transcription", None)
                            if interim and interim.text:
                                await ws.send(json.dumps(
                                    {"type": "transcript", "final": False,
                                     "text": interim.text}))
                            it = getattr(sc, "input_transcription", None)
                            if it and it.text:
                                await ws.send(json.dumps(
                                    {"type": "transcript", "final": True,
                                     "text": it.text}))
                            ot = getattr(sc, "output_transcription", None)
                            if ot and ot.text:
                                await ws.send(json.dumps(
                                    {"type": "reply", "text": ot.text}))
                            if getattr(sc, "interrupted", False):
                                # Google's own signal that we were cut off mid-sentence.
                                await ws.send(json.dumps({"type": "interrupted"}))
                            if getattr(sc, "turn_complete", False):
                                await ws.send(json.dumps({"type": "state",
                                                          "state": "listening"}))
                    except asyncio.CancelledError:
                        raise
                    except Exception:
                        return
            # Tear down only when the BROWSER goes away. The reader is long-lived and
            # must not be allowed to end the conversation, or the session dies right
            # after the first reply.
            reader = asyncio.create_task(to_browser())

            async def report():
                """Progress while the session is OPEN. The end-of-session counter
                alone was useless: a live conversation never prints it, so a
                silent audio path looked identical to a working one."""
                while True:
                    await asyncio.sleep(5)
                    print(f"[live] out {stats['out_frames']}f/{stats['out_bytes']:,}B "
                          f"({stats['out_bytes']/48000:.1f}s) | in "
                          f"{stats['in_frames']}f/{stats['in_bytes']:,}B", flush=True)

            tick = asyncio.create_task(report())
            try:
                await to_gemini()          # returns when the browser disconnects
            finally:
                tick.cancel()
                reader.cancel()
                secs = max(1, round(stats["in_bytes"] / 32000))
                print(f"[live] {stats['out_frames']} audio frames / {stats['out_bytes']:,} B "
                      f"out ({stats['out_bytes']/48000:.1f}s @24k mono) | "
                      f"{stats['in_frames']} frames / {stats['in_bytes']:,} B in ~{secs}s", flush=True)
    except Exception as e:
        try:
            await ws.send(json.dumps({"type": "error", "error": str(e)[:200]}))
        except Exception:
            pass
    finally:
        try:
            await ws.close()
        except Exception:
            pass


async def main():
    if not read_key():
        print("FATAL: GEMINI_API_KEY not found", file=sys.stderr)
        return 1
    async with serve(handle, HOST, PORT, max_size=None):
        print(f"Gemini Live proxy on ws://{HOST}:{PORT}  model={MODEL} voice={VOICE}")
        await asyncio.Future()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
