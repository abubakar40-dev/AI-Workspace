#!/usr/bin/env python3
"""Helix WebSocket Bridge — speaks the UI's WebSocket protocol on ws://127.0.0.1:8765.

Reads real Hermes/Kanban state from ~/.hermes/kanban.db and ~/.hermes/state.db.
Forwards UI commands to Hermes via `hermes kanban create` / CLI.
No external deps — stdlib only (asyncio, base64, hashlib, hmac, json, os, re,
sqlite3, struct, subprocess, time, urllib).

Protocol (see src/js/00_core.js BRIDGE PROTOCOL):
  SERVER→UI: hello, agent.status, task.upsert, task.remove, interact, tool.call,
    verify, chat, voice.state, voice.level, think, model, ctx, confirm.request,
    alert, headline, lms.data, lms.update, download, kill, resume, skills.list,
    souls, soul.saved
  UI→SERVER: command, confirm.response, kill, resume, voice.start/stop/interrupt,
    download, soul.update, gesture
  Deliberately rejected (no real backing): settings, skill.install, memory.add,
    memory.delete, vision.source, vision.frame.
"""
import argparse
import asyncio
import base64
import hashlib
import json
import mimetypes
import os
import re
import sqlite3
import struct
import shutil
import tempfile
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

UI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ui")
UI_FILE = os.path.join(UI_DIR, "helix-ui.html")

HERMES_HOME = os.path.expanduser("~/.hermes")
KANBAN_DB = os.path.join(HERMES_HOME, "kanban.db")
STATE_DB = os.path.join(HERMES_HOME, "state.db")
HERMES_BIN = "/home/abubakargcx/.local/bin/hermes"

# Logs live in the XDG state dir, not next to the binary.
LOG_DIR = os.path.expanduser("~/.local/state/helix/logs")


# ── speech (live-tts → edge-tts → piper → espeak-ng) ────────────────────────
TTS_DIR = os.path.expanduser("~/.local/share/helix-tts")
EDGE_TTS = os.path.expanduser("~/.local/share/helix-tts-venv/bin/edge-tts")
# Gemini Live lives in its own venv; argv is a LIST so _render does not exec a
# space-joined path as one filename.
LIVE_TTS = [os.path.expanduser("~/.local/share/helix-live-venv/bin/python"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "tools", "live_tts.py")]
PIPER = os.path.join(TTS_DIR, "piper", "piper")
PIPER_LIB = os.path.join(TTS_DIR, "piper")
PIPER_MODEL = os.path.join(TTS_DIR, "voices", "en_GB-alan-medium.onnx")
ESPEAK = "espeak-ng"
# Male voices throughout, per the human's preference for a deep voice.
TTS_VOICES = {
    "edge":   {"en": "en-GB-ThomasNeural", "ur": "ur-PK-AsadNeural"},
    "piper":  {"en": "en_GB-alan-medium",  "ur": None},
    "espeak": {"en": "en-gb",              "ur": "ur"},
}


def _voice(engine, lang):
    return TTS_VOICES[engine].get(lang) or TTS_VOICES[engine]["en"]


def _render(label, build, ext, mime, stdin=None, env=None, timeout=60):
    """Run a TTS binary to a temp file and return (bytes, mime, error).

    A tier that produces no audio is a FAILURE, never a silent success —
    that is the bug class this keeps getting bitten by.
    """
    out = tempfile.mktemp(suffix=ext)
    try:
        p = subprocess.run(build(out), input=stdin, capture_output=True,
                           text=bool(stdin), timeout=timeout, env=env)
        if p.returncode != 0 or not os.path.isfile(out) or os.path.getsize(out) < 512:
            err = p.stderr if isinstance(p.stderr, str) else \
                (p.stderr or b"").decode(errors="replace")
            return None, mime, f"{label}: " + ((err or "").strip()[-120:] or "no audio")
        with open(out, "rb") as f:
            return f.read(), mime, None
    except subprocess.TimeoutExpired:
        return None, mime, f"{label} timed out"
    except OSError as e:
        return None, mime, f"{label}: {e}"
    finally:
        if os.path.exists(out):
            os.unlink(out)


def _tts_live(text, lang):
    """Tier 0: Gemini Live, one text turn -> one WAV. Stateless; shells out
    because google-genai lives in its own venv."""
    return _render("live-tts",
                   lambda o: [*LIVE_TTS, "--lang", lang, "--out", o],
                   ".wav", "audio/wav", stdin=text, timeout=12)


def _tts_edge(text, lang):
    if not os.path.isfile(EDGE_TTS):
        return None, None, "edge-tts not installed"
    return _render("edge-tts",
                   lambda o: [EDGE_TTS, "--voice", _voice("edge", lang), "--text", text,
                              "--write-media", o],
                   ".mp3", "audio/mpeg", timeout=10)


def _tts_piper(text, lang):
    if not (os.path.isfile(PIPER) and os.path.isfile(PIPER_MODEL)):
        return None, None, "piper not installed"
    if not TTS_VOICES["piper"].get(lang):
        return None, None, f"no piper voice for '{lang}'"
    return _render("piper",
                   lambda o: [PIPER, "--model", PIPER_MODEL, "--output_file", o],
                   ".wav", "audio/wav", stdin=text,
                   env=dict(os.environ, LD_LIBRARY_PATH=PIPER_LIB), timeout=15)


def _tts_espeak(text, lang):
    return _render("espeak",
                   lambda o: [ESPEAK, "-v", _voice("espeak", lang), "-s", "165", "-w", o, text],
                   ".wav", "audio/wav", timeout=20)


def tts(text, lang="en", engine="auto"):
    """Online-first TTS with a local fallback. Returns (audio, mime, engine, error).

    Chain: live-tts (Gemini Live) → edge-tts → piper → espeak-ng. A tier that
    produces no audio is a failure, never a silent success.

    WebKit2GTK usually ships NO speech-dispatcher voices, so the browser's
    speechSynthesis is silent in the desktop app. The bridge chain is what
    actually speaks.
    """
    text = (text or "").strip()
    if not text:
        return None, None, None, "empty text"
    if len(text) > 2000:
        return None, None, None, "text too long"
    if not re.fullmatch(r"[a-z]{2,3}(-[a-z]{2,4})?", lang or ""):
        return None, None, None, "bad lang"
    lang = lang.split("-")[0]

    order = {
        "auto":  [_tts_live, _tts_edge, _tts_piper, _tts_espeak],
        "live":  [_tts_live, _tts_edge, _tts_piper, _tts_espeak],
        "edge":  [_tts_edge, _tts_piper, _tts_espeak],
        "piper": [_tts_piper, _tts_espeak],
        "espeak": [_tts_espeak],
    }.get(engine or "auto")
    if not order:
        return None, None, None, "bad engine"

    tried, skipped = [], []
    for fn in order:
        audio, mime, err = fn(text, lang)
        if audio:
            name = fn.__name__.replace("_tts_", "")
            return audio, mime, name, None
        reason = (err or "no audio").replace("\n", " ")[:90]
        tried.append(reason)
        skipped.append(f"{fn.__name__}={reason}")
    return None, None, None, "; ".join(tried)[:300]


def _play_host_audio(audio_bytes, mime="audio/wav"):
    """Play audio directly on the host's default audio sink (PulseAudio/PipeWire).

    Mirrors Jarvis's audio output: routes to the active sink (including Bluetooth
    headsets) and eliminates WebKit2GTK audio routing failures and autoplay stalls.
    """
    if not audio_bytes:
        return

    def _worker():
        ext = ".wav" if "wav" in (mime or "") else ".mp3"
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=ext)
        try:
            with os.fdopen(tmp_fd, "wb") as f:
                f.write(audio_bytes)
            players = [
                ["pw-play", tmp_path],
                ["paplay", tmp_path],
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", tmp_path],
            ]
            if ext == ".wav":
                players.insert(2, ["aplay", "-q", tmp_path])
            for cmd in players:
                bin_path = shutil.which(cmd[0])
                if bin_path:
                    try:
                        res = subprocess.run([bin_path] + cmd[1:], capture_output=True, timeout=30)
                        if res.returncode == 0:
                            return
                    except Exception:
                        pass
            _log("host audio: all playback backends failed")
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except OSError:
                pass

    t = threading.Thread(target=_worker, daemon=True, name="helix-host-audio")
    t.start()



# ── real data for the snapshot ───────────────────────────────────────────────

# Keyless public RSS. Al Jazeera is deliberately absent - unreachable here.
FEEDS = [
    ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("NPR", "https://feeds.npr.org/1001/rss.xml"),
    ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/index"),
    ("Hacker News", "https://hnrss.org/frontpage"),
]
HEADLINE_TTL = 300
_headline_cache = {"at": 0, "data": None}


def _one_feed(name, url, limit=12):
    """Fetch + parse one RSS feed. Never raises - a dead feed is not a dead endpoint."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Helix/1.0 (local)"})
        with urllib.request.urlopen(req, timeout=12) as r:
            root = ET.fromstring(r.read(2_000_000))
    except Exception as e:
        return {"source": name, "error": str(e)[:120], "items": []}
    items = []
    for it in root.iter("item"):
        t = (it.findtext("title") or "").strip()
        if not t:
            continue
        items.append({"title": t, "link": (it.findtext("link") or "").strip(),
                      "date": (it.findtext("pubDate") or "").strip()})
        if len(items) >= limit:
            break
    return {"source": name, "error": None, "items": items}


def headlines():
    """RSS headlines for the World Monitor, cached briefly. stdlib only.

    Fetches run in parallel: four sequential 12s-timeout requests blocked the
    event loop for 18 seconds, which stalled every other event (including the
    agent snapshot) behind them.
    """
    if _headline_cache["data"] and time.time() - _headline_cache["at"] < HEADLINE_TTL:
        return _headline_cache["data"]
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=len(FEEDS)) as ex:
        feeds = list(ex.map(lambda f: _one_feed(*f), FEEDS))
    data = {"feeds": feeds, "total": sum(len(f["items"]) for f in feeds)}
    _headline_cache.update(at=time.time(), data=data)
    return data


def skills_items():
    """Real skills installed in the Hermes skills directory."""
    sdir = os.path.join(HERMES_HOME, "skills")
    out = []
    if not os.path.isdir(sdir):
        return out
    for name in sorted(os.listdir(sdir)):
        p = os.path.join(sdir, name)
        if not os.path.isdir(p):
            continue
        desc = ""
        for cand in ("SKILL.md", "README.md", "skill.md"):
            cp = os.path.join(p, cand)
            if os.path.isfile(cp):
                try:
                    desc = " ".join(open(cp, encoding="utf-8",
                                         errors="replace").read().split())[:180]
                except OSError:
                    pass
                break
        out.append({"id": name, "name": name, "desc": desc,
                    "installed": True, "enabled": True})
    return out


def runtime_info():
    """Model actually in use + live context usage, for the status bar."""
    info = {"model": "", "ctx": 0, "ctx_max": 200000}
    try:
        import yaml
        cfg = os.path.join(HERMES_HOME, "config.yaml")
        if os.path.exists(cfg):
            with open(cfg, "r", encoding="utf-8") as f:
                info["model"] = (yaml.safe_load(f) or {}).get("model", {}).get("default", "")
    except Exception:
        pass
    try:
        db = os.path.join(HERMES_HOME, "state.db")
        if os.path.exists(db):
            c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
            try:
                best = 0
                for (ej,) in c.execute("SELECT entry_json FROM gateway_routing "
                                       "ORDER BY updated_at DESC LIMIT 25"):
                    try:
                        best = max(best, int(json.loads(ej).get("last_prompt_tokens") or 0))
                    except (TypeError, ValueError):
                        continue
                info["ctx"] = best
            finally:
                c.close()
    except Exception:
        pass
    return info


def lms_snapshot():
    """Real LMS data for the panel, or None if the portal is unreachable."""
    try:
        tools_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools")
        if tools_dir not in sys.path:
            sys.path.insert(0, tools_dir)
        from lms_client import state, client
        base = state()
        courses = []
        items = []
        for c in base.get("courses", []):
            try:
                detail = client().course(c["id"])
            except Exception:
                detail = {}
            present = total = 0
            for att in detail.get("attendance", []):
                m = re.match(r"(\d+)\s*/\s*(\d+)", str(att.get("points") or ""))
                if m:
                    present += int(m.group(1))
                    total += int(m.group(2))
            courses.append({"code": str(c.get("id", "")), "name": c.get("name", ""),
                            "present": present, "total": total,
                            "percentage": round(present * 100 / total) if total else None})
            for a in detail.get("assignments", []):
                due = a.get("due")
                try:
                    due = int(datetime.fromisoformat(due).timestamp() * 1000) if due else 0
                except (TypeError, ValueError):
                    due = 0
                items.append({
                    "id": "lms-assign-" + str(a.get("id")), "kind": "assignment",
                    "title": a.get("title", ""), "course": c.get("name", ""),
                    "lecture": detail.get("name", ""),
                    "assignment_id": a.get("id"),
                    "status": "submitted" if a.get("submitted") else "pending",
                    "due": due,
                    "submission_status": a.get("submission_status", ""),
                })
        return {"synced": int(time.time() * 1000), "courses": courses,
                "items": items, "live": True}
    except Exception as e:
        _log(f"lms snapshot failed: {str(e)[:120]}")
        return None


def _log(msg):
    """Append a timestamped line to the bridge log."""
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(os.path.join(LOG_DIR, "bridge.log"), "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except Exception:
        pass


# ── local speech-to-text (whisper.cpp) ───────────────────────────────────────
STT_DIR = os.path.expanduser("~/.local/share/helix-stt")
WHISPER = os.path.join(STT_DIR, "whisper-cli")
WHISPER_MODEL = os.path.join(STT_DIR, "models", "ggml-base.bin")
# ponytail: 2 threads, NOT nproc. This box is 4 cores at load ~9. Same 30s clip
# measured through /stt: -t 4 -> 100.0s (0.30x realtime), -t 2 -> 21.5s
# (1.40x). Oversubscribing the cores is ~5x SLOWER. Re-measure before changing.
STT_THREADS = "2"


def stt(audio: bytes, lang: str = ""):
    """Transcribe locally with whisper.cpp. No audio leaves the machine.

    WebKit2GTK has no SpeechRecognition API (that is Chrome-only), so the UI
    records audio and posts it here. ggml-base is the model; ggml-tiny was
    tried first and mis-detects Urdu audio as English.
    """
    if not (os.path.isfile(WHISPER) and os.path.isfile(WHISPER_MODEL)):
        return {"ok": False, "error": "whisper.cpp not installed"}
    if not audio:
        return {"ok": False, "error": "no audio"}
    if lang and not re.fullmatch(r"[a-z]{2}(-[a-z]+)?", lang or ""):
        return {"ok": False, "error": "bad lang"}

    tmp = tempfile.mkdtemp(prefix="helix-stt-")
    src, wav = os.path.join(tmp, "in"), os.path.join(tmp, "out.wav")
    try:
        with open(src, "wb") as f:
            f.write(audio)
        # ffmpeg probes the content, so the extension does not matter.
        p = subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", src,
             "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", wav],
            capture_output=True, timeout=60)
        if p.returncode != 0 or not os.path.isfile(wav):
            return {"ok": False, "error": "ffmpeg: " + p.stderr.decode()[:160]}

        cmd = [WHISPER, "-m", WHISPER_MODEL, "-nt", "-t", STT_THREADS, "-f", wav]
        if lang:
            cmd[1:1] = ["-l", lang]
        t0 = time.time()
        w = subprocess.run(cmd, capture_output=True, timeout=180)
        if w.returncode != 0:
            return {"ok": False, "error": w.stderr.decode()[:160]}
        text = " ".join(l.strip() for l in
                        w.stdout.decode(errors="replace").splitlines() if l.strip())
        return {"ok": True, "text": text, "lang": lang or "auto",
                "ms": int((time.time() - t0) * 1000)}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "whisper timed out"}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

HOST = "127.0.0.1"
PORT = 8765
WS_MAGIC = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

AGENT_IDS = ["helix", "research", "files", "pc", "vision", "dev", "career", "comms", "sysmon", "lms"]
AGENT_ROLES = {
    "helix": "CEO / Orchestrator",
    "research": "Research",
    "files": "File / Documents",
    "pc": "PC Control",
    "vision": "Vision",
    "dev": "Development",
    "career": "Career",
    "comms": "Communication",
    "sysmon": "System Monitor",
    "lms": "LMS / Study",
}

# Hermes profile id -> the id the UI knows the agent by. The UI's H.AGENTS uses
# "helix"/"files"/"comms"; Hermes calls them "default"/"document"/"comm".
# Without this the chat showed the sender as "undefined" for every message
# from the CEO, because H.agent('default') finds nothing.
UI_AGENT_ID = {"default": "helix", "document": "files", "comm": "comms"}


def ui_agent(profile_id):
    return UI_AGENT_ID.get(profile_id or "", profile_id or "helix")

# UI agent id -> Hermes profile directory. "helix" is the default profile at
# the root ~/.hermes/SOUL.md; the rest live under profiles/<id>/SOUL.md.
SOUL_PROFILE = {
    "helix": "default", "research": "research", "files": "document",
    "pc": "pc", "vision": "vision", "dev": "dev", "career": "career",
    "comms": "comm", "sysmon": "sysmon",
}


def soul_path(agent):
    pid = SOUL_PROFILE.get(agent)
    if not pid:
        return None
    if pid == "default":
        return os.path.join(HERMES_HOME, "SOUL.md")
    return os.path.join(HERMES_HOME, "profiles", pid, "SOUL.md")


def souls_snapshot():
    """Real persona files, keyed by the UI's agent id."""
    out = {}
    for agent in SOUL_PROFILE:
        try:
            with open(soul_path(agent), encoding="utf-8", errors="replace") as f:
                out[agent] = f.read()
        except OSError:
            out[agent] = ""
    return out

# ── WebSocket helpers ────────────────────────────────────────────────────────

def ws_accept(key: str) -> str:
    return base64.b64encode(hashlib.sha1((key + WS_MAGIC).encode()).digest()).decode()

def ws_frame(payload: bytes, opcode: int = 1) -> bytes:
    """Encode a WebSocket data frame."""
    b1 = 0x80 | opcode  # FIN + opcode
    n = len(payload)
    if n < 126:
        header = struct.pack("!BB", b1, n)
    elif n < 65536:
        header = struct.pack("!BBH", b1, 126, n)
    else:
        header = struct.pack("!BBQ", b1, 127, n)
    return header + payload

def ws_close(code: int = 1000, reason: str = "") -> bytes:
    payload = struct.pack("!H", code) + reason.encode()
    return ws_frame(payload, opcode=8)

def ws_ping() -> bytes:
    return ws_frame(b"", opcode=9)

def ws_pong(payload: bytes = b"") -> bytes:
    return ws_frame(payload, opcode=10)

def ws_decode_frame(data: bytes):
    """Decode a WebSocket frame. Returns (opcode, payload) or (None, None)."""
    if len(data) < 2:
        return None, None
    b1, b2 = data[0], data[1]
    opcode = b1 & 0x0F
    masked = b2 & 0x80
    length = b2 & 0x7F
    offset = 2
    if length == 126:
        length = struct.unpack("!H", data[offset:offset + 2])[0]
        offset += 2
    elif length == 127:
        length = struct.unpack("!Q", data[offset:offset + 8])[0]
        offset += 8
    if masked:
        mask = data[offset:offset + 4]
        offset += 4
        payload = bytes(b ^ mask[i % 4] for i, b in enumerate(data[offset:offset + length]))
    else:
        payload = data[offset:offset + length]
    return opcode, payload

# ── Kanban DB access ─────────────────────────────────────────────────────────

def kanban_connect():
    return sqlite3.connect(f"file:{KANBAN_DB}?mode=ro", uri=True, timeout=2)

def profile_state(conn, pid):
    """Return (status, task_dict_or_None) for a profile."""
    busy = conn.execute(
        "SELECT id,title,status,last_heartbeat_at,current_run_id,result "
        "FROM tasks WHERE assignee=? AND status='running' "
        "ORDER BY started_at DESC LIMIT 1", (pid,)).fetchone()
    if busy:
        event = conn.execute(
            "SELECT kind,payload,created_at FROM task_events "
            "WHERE task_id=? ORDER BY id DESC LIMIT 1", (busy[0],)).fetchone()
        progress = _task_progress(busy, event)
        return "working", progress

    stuck = conn.execute(
        "SELECT id,title,status,last_heartbeat_at,current_run_id,result "
        "FROM tasks WHERE assignee=? AND status='blocked' "
        "ORDER BY created_at DESC LIMIT 1", (pid,)).fetchone()
    if stuck:
        event = conn.execute(
            "SELECT kind,payload,created_at FROM task_events "
            "WHERE task_id=? ORDER BY id DESC LIMIT 1", (stuck[0],)).fetchone()
        progress = _task_progress(stuck, event)
        return "blocked", progress

    return "idle", None

def _task_progress(task_row, event_row=None):
    task_id, title, status, heartbeat, run_id, result = task_row
    progress = {
        "id": task_id, "title": title, "status": status,
        "run_id": run_id, "last_heartbeat_at": heartbeat,
        "result": (result or "").strip()[:1200],
    }
    if event_row:
        kind, payload, created_at = event_row
        progress["last_event"] = {"kind": kind, "detail": payload or "", "at": created_at}
        if not progress["result"] and kind == "completed":
            try:
                import json as _json
                progress["result"] = (_json.loads(payload or "{}").get("summary") or "")[:1200]
            except Exception:
                pass
    return progress

def snapshot():
    """Full UI snapshot for ui.ready response."""
    out = {"ts": int(time.time()), "profiles": [], "tasks": [], "events": []}
    conn = kanban_connect()
    try:
        for pid in AGENT_IDS:
            status, task = profile_state(conn, pid)
            out["profiles"].append({
                "id": pid, "name": pid, "role": AGENT_ROLES.get(pid, pid),
                "status": status, "task": task,
            })
        out["events"] = [
            {"task": r[0], "kind": r[1], "detail": r[2] or "", "at": r[3]}
            for r in conn.execute(
                "SELECT e.task_id, e.kind, COALESCE(e.payload,''), e.created_at "
                "FROM task_events e JOIN tasks t ON t.id = e.task_id "
                "ORDER BY e.id DESC LIMIT 25")
        ]
        rows = conn.execute(
            "SELECT id,title,assignee,status,result,created_at,completed_at,"
            "last_heartbeat_at,current_run_id FROM tasks WHERE status != 'archived' "
            "ORDER BY created_at DESC LIMIT 100").fetchall()
        for row in rows:
            tid, title, assignee, status, result, created_at, completed_at, heartbeat, run_id = row
            latest = conn.execute(
                "SELECT kind,payload,created_at FROM task_events "
                "WHERE task_id=? ORDER BY id DESC LIMIT 1", (tid,)).fetchone()
            detail = ""; event_at = None
            if latest:
                kind, payload, event_at = latest
                if kind in ("completed", "failed", "blocked", "heartbeat"):
                    detail = payload or ""
                if kind == "completed" and not result:
                    try:
                        import json as _json
                        detail = (_json.loads(payload or "{}").get("summary") or detail)
                    except Exception:
                        pass
            out["tasks"].append({
                "id": tid, "title": title, "assignee": assignee or "default",
                "status": status, "summary": (result or detail or "").strip()[:1200],
                "created_at": created_at, "completed_at": completed_at,
                "last_heartbeat_at": heartbeat, "run_id": run_id,
                "last_event_at": event_at,
            })
    finally:
        conn.close()
    return out

# ── Hermes CLI integration ───────────────────────────────────────────────────

def hermes_kanban_create(title: str, body: str, assignee: str = "default"):
    """Create a Kanban task via hermes CLI. Returns task id or None."""
    try:
        out = subprocess.run(
            [HERMES_BIN, "kanban", "create", title[:120],
             "--body-file", "-", "--assignee", assignee, "--workspace", "scratch"],
            input=body, capture_output=True, text=True, timeout=120)
        if out.returncode != 0:
            return None
        m = re.search(r"\b(t_[0-9a-f]{4,32})\b", out.stdout)
        return m.group(1) if m else None
    except Exception:
        return None

def hermes_run_command(text: str, assignee: str = "default"):
    """Create a task and return its id."""
    return hermes_kanban_create(text[:120] or "voice task", text, assignee)

def _board_watcher():
    """Watch the Kanban board and broadcast live changes to every client.

    Without this the agent worked on the task and its answer never
    reached the UI: the bridge created the card, said "Task accepted",
    and then went silent. The chat looked dead even though Hermes was
    busy for a minute. This polls the board, pushes agent.status so the
    Agent Town actors actually walk to their desks, and delivers the
    agent's final answer as a chat message.
    """
    last_tasks = {}
    last_agents = {}
    announced = set()
    while True:
        time.sleep(1.5)
        with _CLIENT_LOCK:
            if not CLIENTS:
                continue
        try:
            snap = snapshot()
        except Exception:
            continue

        # --- agent status changes -> Agent Town movement ---
        for p in snap["profiles"]:
            key = p["id"]
            sig = (p["status"], (p["task"] or {}).get("id"))
            if last_agents.get(key) != sig:
                last_agents[key] = sig
                t = p["task"] or {}
                broadcast({"type": "agent.status", "agent": ui_agent(key),
                           "status": p["status"], "task": t.get("id"),
                           "progress": 0, "note": (t.get("result") or "")[:200],
                           "where": "desk"})

        # --- task changes ---
        for t in snap["tasks"]:
            tid = t["id"]
            status = t["status"]
            summary = (t.get("summary") or "").strip()
            if last_tasks.get(tid) != status:
                last_tasks[tid] = status
                broadcast({"type": "task.upsert", "task": {
                    "id": tid, "title": t["title"], "assignee": ui_agent(t["assignee"]),
                    "status": status, "progress": 1 if status == "done" else 0,
                    "summary": summary[:800], "deps": [], "parent": None}})

            # --- a finished task delivers the agent's answer to the chat ---
            if status == "done" and tid not in announced and summary:
                announced.add(tid)
                broadcast({"type": "chat", "role": "agent",
                           "agent": ui_agent(t["assignee"]), "text": summary[:1500]})
                broadcast({"type": "voice.state", "state": "idle"})


def _start_board_watcher():
    t = threading.Thread(target=_board_watcher, daemon=True)
    t.start()


# ── WebSocket handler ────────────────────────────────────────────────────────

# Every connected UI. The board watcher broadcasts to all of them, so agent
# activity reaches the window that asked for it AND any other open one.
CLIENTS = set()
_CLIENT_LOCK = threading.Lock()


def broadcast(obj):
    """Send an event to every connected client."""
    payload = json.dumps(obj, separators=(",", ":")).encode()
    with _CLIENT_LOCK:
        targets = list(CLIENTS)
    for h in targets:
        try:
            h.send_bytes(payload)
        except Exception:
            pass


class BridgeHandler:
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer
        self.connected = False
        self.handshaked = False
        self.outbox = []

    async def handshake(self):
        line = await self.reader.readline()
        if not line:
            return False
        method, path, _ = line.decode().split(" ", 2)
        key = None
        while True:
            l = await self.reader.readline()
            if not l or l in (b"\r\n", b"\n"):
                break
            l = l.decode().strip()
            if l.lower().startswith("sec-websocket-key:"):
                key = l.split(":", 1)[1].strip()
        if not key:
            self.writer.write(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            await self.writer.drain()
            return False
        accept = ws_accept(key)
        resp = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
        )
        self.writer.write(resp.encode())
        await self.writer.drain()
        self.handshaked = True
        return True

    async def recv_frame(self):
        """Read exactly one complete WebSocket frame.

        The header alone is not enough: the payload follows it, and a client
        frame is always masked (4 mask bytes) with the payload after that.
        Reading only 2 bytes and handing them to the decoder produced an
        EMPTY payload for every message the UI sent — the handshake worked,
        the connection looked live, and not one command ever reached the
        backend. That is why the UI sat on "BRIDGE LIVE" and nothing happened.
        """
        head = await self.reader.readexactly(2)
        b1, b2 = head[0], head[1]
        opcode = b1 & 0x0F
        masked = b2 & 0x80
        length = b2 & 0x7F
        if length == 126:
            length = int.from_bytes(await self.reader.readexactly(2), "big")
        elif length == 127:
            length = int.from_bytes(await self.reader.readexactly(8), "big")
        mask = await self.reader.readexactly(4) if masked else b""
        payload = await self.reader.readexactly(length) if length else b""
        if masked:
            payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        return opcode, payload

    async def send_frame(self, opcode, payload: bytes):
        self.writer.write(ws_frame(payload, opcode))
        await self.writer.drain()

    async def send_json(self, obj: dict):
        payload = json.dumps(obj, separators=(",", ":")).encode()
        await self.send_frame(1, payload)

    def send_bytes(self, payload: bytes):
        """Queue a frame for sending from another thread."""
        self.outbox.append(payload)

    async def flush_outbox(self):
        """Drain frames queued by the board watcher thread."""
        while self.outbox:
            payload = self.outbox.pop(0)
            try:
                await self.send_frame(1, payload)
            except Exception:
                return

    async def send_snapshot(self):
        snap = snapshot()
        # Captured once, on the loop's own thread. The worker threads below
        # use it to hand their results back.
        self.loop = asyncio.get_running_loop()
        _log(f"snapshot: {len(snap['profiles'])} profiles, {len(snap['tasks'])} tasks")
        rt = runtime_info()
        await self.send_json({"type": "hello",
                              "model": rt.get("model") or "nvidia/nemotron-3.5-lightning:free",
                              "agents": AGENT_IDS})
        await self.send_json({"type": "model",
                              "name": rt.get("model") or "nvidia/nemotron-3.5-lightning:free",
                              "chain": [rt.get("model") or "nvidia/nemotron-3.5-lightning:free",
                                        "openrouter/free"]})
        await self.send_json({"type": "ctx", "used": rt.get("ctx", 0),
                              "max": rt.get("ctx_max", 200000)})
        await self.send_json({"type": "souls", "souls": souls_snapshot()})
        for p in snap["profiles"]:
            # _task_progress() returns id/title/status/run_id/last_heartbeat_at/
            # result/last_event — it has NO "progress", "note" or "where" keys.
            # Indexing them raised KeyError and killed the whole snapshot
            # mid-stream, so the UI received 4 agents and zero tasks.
            t = p["task"] or {}
            await self.send_json({
                "type": "agent.status", "agent": ui_agent(p["id"]), "status": p["status"],
                "task": t.get("id"), "progress": t.get("progress", 0),
                "note": (t.get("result") or t.get("note") or "")[:200],
                "where": t.get("where", "desk"),
            })
        for t in snap["tasks"]:
            await self.send_json({"type": "task.upsert", "task": {
                "id": t["id"], "title": t["title"], "assignee": ui_agent(t["assignee"]),
                "status": t["status"], "progress": t.get("progress", 0),
                "summary": t.get("summary", ""), "deps": [], "parent": None}})

        # Real installed skills (not the seeded defaults the demo shipped).
        skl = skills_items()
        await self.send_json({"type": "skills.list", "items": skl})
        _log(f"snapshot: {len(skl)} skills")

        # Real task activity for the AGENT tab. The snapshot carries the
        # tasks; these events are what the tool-card feed renders.
        for ev in snap.get("events", [])[:25]:
            task_id = ev.get("task", "")
            assignee = "helix"
            for t in snap["tasks"]:
                if t["id"] == task_id:
                    assignee = t["assignee"]
                    break
            await self.send_json({"type": "tool.call", "agent": ui_agent(assignee),
                                  "tool": ev.get("kind", "event"),
                                  "input": (ev.get("detail") or "")[:800],
                                  "output": {"task": task_id},
                                  "ms": 0,
                                  "ok": ev.get("kind") == "completed"})

        # Real headlines for the World Monitor panel. Also off the event loop —
        # the RSS fetches are network calls and must not stall agent events.
        def _headlines_worker():
            try:
                hd = headlines()
                items = []
                for f in hd.get("feeds", []):
                    for it in f.get("items", []):
                        items.append({"title": it["title"], "source": f["source"],
                                      "url": it.get("link", ""), "ts": 0})

                async def _push():
                    for h in items[:20]:
                        await self.send_json({"type": "headline", **h})
                asyncio.run_coroutine_threadsafe(_push(), self.loop)
                _log(f"snapshot: {len(items)} headlines")
            except Exception as e:
                _log(f"headlines failed: {str(e)[:100]}")

        threading.Thread(target=_headlines_worker, daemon=True).start()

        # Real LMS data for the LMS panel. Fetching 10 courses from Moodle takes
        # many seconds — doing it inline blocked the whole snapshot, so it runs
        # in a thread and the result is pushed when it arrives.
        def _lms_worker():
            lms = lms_snapshot()
            if not lms:
                lms = {"synced": int(time.time() * 1000), "courses": [], "items": [],
                       "live": False, "error": "LMS unreachable"}
            try:
                # The loop must be captured from the coroutine's own thread.
                # asyncio.get_event_loop() raises inside a plain thread on
                # Python 3.14, and the send silently never happened.
                asyncio.run_coroutine_threadsafe(self.send_json(
                    {"type": "lms.data", "lms": lms}), self.loop)
            except Exception as e:
                _log(f"lms send failed: {str(e)[:120]}")
            _log(f"snapshot: lms {len(lms.get('courses', []))} courses, "
                 f"{len(lms.get('items', []))} items")

        threading.Thread(target=_lms_worker, daemon=True).start()

    async def handle_message(self, obj: dict):
        mtype = obj.get("type")
        _log(f"recv {mtype}")
        if mtype == "command":
            text = obj.get("text", "")
            assignee = obj.get("assignee", "default")
            await self.send_json({"type": "voice.state", "state": "thinking"})
            await self.send_json({"type": "think", "text": f"parse request ({len(text.split())} words)"})
            await asyncio.sleep(0.7)
            tid = hermes_kanban_create(text[:120] or "voice task", text, assignee)
            if tid:
                await self.send_json({"type": "task.upsert", "task": {
                    "id": tid, "title": text[:120], "assignee": ui_agent(assignee),
                    "status": "ready", "progress": 0, "summary": "Task accepted by CEO"}})
                await self.send_json({"type": "chat", "role": "helix", "agent": "helix",
                    "text": f"Task accepted by HELIX. I am working on: {text}"})
                await self.send_json({"type": "voice.state", "state": "idle"})
            else:
                await self.send_json({"type": "chat", "role": "sys",
                    "text": "Failed to create task — hermes unavailable"})
        elif mtype == "kill":
            await self.send_json({"type": "kill"})
            await self.send_json({"type": "voice.state", "state": "idle"})
        elif mtype == "resume":
            await self.send_json({"type": "resume"})
        elif mtype == "confirm.response":
            await self.send_json({"type": "chat", "role": "sys",
                "text": f"{'✓ Approved' if obj.get('approve') else '✗ Denied'}: {obj.get('id','')}"})
        elif mtype == "voice.start":
            await self.send_json({"type": "voice.state", "state": "listening"})
        elif mtype == "voice.stop":
            await self.send_json({"type": "voice.state", "state": "idle"})
        elif mtype == "voice.interrupt":
            await self.send_json({"type": "voice.state", "state": "idle"})
        elif mtype == "download":
            url = (obj.get("url") or "").strip()
            if not re.match(r"^https?://", url):
                await self.send_json({"type": "chat", "role": "sys",
                    "text": "Download needs a full http(s) link."})
                return
            body = (
                f"Download this link: {url}\n\n"
                "Use yt-dlp for video/audio and direct fetch for plain files. "
                "Save under ~/Downloads/helix, verify the file exists and is "
                "non-zero, and report the exact path. Do not claim success "
                "without checking.\n"
            )
            tid = await asyncio.to_thread(
                hermes_kanban_create, f"Download {url[:100]}", body, "pc")
            if tid:
                await self.send_json({"type": "download", "id": tid, "url": url,
                    "status": "queued", "pct": 0})
                await self.send_json({"type": "chat", "role": "sys",
                    "text": f"Download queued for pc as {tid}."})
            else:
                await self.send_json({"type": "download", "id": "dl-error", "url": url,
                    "status": "error", "pct": 0})
                await self.send_json({"type": "chat", "role": "sys",
                    "text": "Download could not be queued — hermes unavailable."})
        elif mtype == "soul.update":
            agent = obj.get("agent") or ""
            text = obj.get("text") or ""
            path = soul_path(agent)
            if not path:
                await self.send_json({"type": "soul.saved", "agent": agent,
                    "ok": False, "error": "unknown agent"})
            elif not text.strip():
                await self.send_json({"type": "soul.saved", "agent": agent,
                    "ok": False, "error": "SOUL.md cannot be empty"})
            elif len(text) > 65536:
                await self.send_json({"type": "soul.saved", "agent": agent,
                    "ok": False, "error": "SOUL.md too large (64 KB max)"})
            else:
                try:
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    tmp = path + ".tmp"
                    with open(tmp, "w", encoding="utf-8") as f:
                        f.write(text)
                    try:
                        os.chmod(tmp, os.stat(path).st_mode & 0o777)
                    except OSError:
                        os.chmod(tmp, 0o600)
                    os.replace(tmp, path)
                    _log(f"soul updated: {agent} -> {path} ({len(text)} chars)")
                    await self.send_json({"type": "soul.saved", "agent": agent,
                        "ok": True, "path": path})
                except OSError as e:
                    await self.send_json({"type": "soul.saved", "agent": agent,
                        "ok": False, "error": str(e)[:200]})
        elif mtype in ("settings", "skill.install", "memory.add",
                       "memory.delete", "vision.source", "vision.frame"):
            await self.send_json({"type": "chat", "role": "sys",
                "text": f"{mtype} is not wired in this bridge."})
        elif mtype == "gesture":
            await self.send_json({"type": "chat", "role": "sys",
                "text": f"gesture → {obj.get('name','')}"})
        elif mtype == "ui.ready":
            await self.send_snapshot()
        elif mtype == "diag":
            # The page reporting its own state. A webview that failed
            # silently is indistinguishable from a working one, and there
            # is no devtools console to read in a packaged desktop app.
            _log("page state: " + json.dumps(obj.get("state") or {}))
        elif mtype == "hello":
            # The UI's handshake. Falling through to the generic
            # "Unknown message type" branch put that text into the chat
            # log on every single connect.
            _log("client hello")
        else:
            await self.send_json({"type": "chat", "role": "sys",
                "text": f"Unknown message type: {mtype}"})

    async def run(self):
        with _CLIENT_LOCK:
            CLIENTS.add(self)
        try:
            while True:
                await self.flush_outbox()
                # A short timeout so the outbox (fed by the board watcher
                # thread) keeps draining even while the client is quiet.
                try:
                    opcode, payload = await asyncio.wait_for(
                        self.recv_frame(), timeout=0.25)
                except asyncio.TimeoutError:
                    continue
                if opcode is None:
                    break
                if opcode == 8:  # close
                    break
                if opcode == 9:  # ping
                    await self.send_frame(10, payload or b"")
                    continue
                if opcode == 1:  # text
                    try:
                        obj = json.loads(payload.decode())
                    except Exception:
                        continue
                    await self.handle_message(obj)
        except Exception:
            pass
        finally:
            with _CLIENT_LOCK:
                CLIENTS.discard(self)
            try:
                self.writer.close()
            except Exception:
                pass

# ── Main ─────────────────────────────────────────────────────────────────────

async def handle_client(reader, writer):
    """Dispatch a connection: WebSocket upgrade, or a plain HTTP GET for the UI.

    Reads the HTTP request line and headers BYTE-EXACTLY (readline), so no
    frame bytes that follow the handshake can be swallowed. A blanket
    read(256) could consume the start of the client's first WebSocket frame
    and silently discard it.
    """
    try:
        line = await reader.readline()
        if not line:
            writer.close()
            return
        parts = line.decode("latin1").split(" ", 2)
        method = parts[0] if parts else ""
        path = parts[1] if len(parts) > 1 else "/"
        headers = {}
        while True:
            hl = await reader.readline()
            if not hl or hl in (b"\r\n", b"\n"):
                break
            k, _, v = hl.decode("latin1").partition(":")
            headers[k.strip().lower()] = v.strip()

        if headers.get("upgrade", "").lower() == "websocket":
            key = headers.get("sec-websocket-key", "")
            if not key:
                writer.close()
                return
            accept = ws_accept(key)
            resp = (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
            )
            writer.write(resp.encode())
            await writer.drain()
            h = BridgeHandler(reader, writer)
            h.handshaked = True
            await h.run()
            return

        if method == "POST":
            await http_post(reader, writer, path, headers)
            return

        await http_serve(writer, method, path)
    except (asyncio.IncompleteReadError, ConnectionResetError, BrokenPipeError):
        pass
    except Exception:
        pass
    finally:
        try:
            writer.close()
        except Exception:
            pass


async def http_post(reader, writer, path, headers):
    """Handle POST requests. /stt (audio in) and /tts (audio out)."""
    path = path.split("?", 1)[0]

    if path == "/tts":
        length = int(headers.get("content-length") or 0)
        if length <= 0:
            await _json_response(writer, {"ok": False, "error": "empty body"}, 400)
            return
        if length > 64_000:
            await _json_response(writer, {"ok": False, "error": "body too large"}, 413)
            return
        try:
            payload = json.loads(await reader.readexactly(length) or b"{}")
        except ValueError:
            await _json_response(writer, {"ok": False, "error": "bad json"}, 400)
            return
        audio, mime, used, err = tts(payload.get("text", ""),
                                     payload.get("lang") or "en",
                                     payload.get("engine") or "auto")
        if err:
            _log(f"tts error: {err[:100]}")
            await _json_response(writer, {"ok": False, "error": err}, 400)
            return
        _log(f"tts ok engine={used} bytes={len(audio)}")
        play_on_host = payload.get("play", True)
        if play_on_host:
            _play_host_audio(audio, mime)
        resp = (
            f"HTTP/1.1 200 OK\r\n"
            f"Content-Type: {mime}\r\n"
            f"Content-Length: {len(audio)}\r\n"
            f"X-Helix-TTS-Engine: {used}\r\n"
            f"X-Helix-Host-Played: {'1' if play_on_host else '0'}\r\n"
            f"Cache-Control: no-store\r\n"
            f"\r\n"
        ).encode()
        writer.write(resp + audio)
        await writer.drain()
        return

    if path != "/stt":
        await _json_response(writer, {"ok": False, "error": "not found"}, 404)
        return

    length = int(headers.get("content-length") or 0)
    if length <= 0:
        await _json_response(writer, {"ok": False, "error": "empty body"}, 400)
        return
    if length > 12 * 1024 * 1024:      # ~12MB, roughly 3 minutes of opus
        await _json_response(writer, {"ok": False, "error": "audio too large"}, 413)
        return

    body = await reader.readexactly(length)
    ctype = headers.get("content-type", "")
    lang = ""
    audio = body

    if ctype.startswith("multipart/form-data"):
        # The UI posts the recording as multipart (MediaRecorder blob + fields).
        audio, lang = _multipart_audio(body, ctype)

    result = stt(audio, lang)
    _log(f"stt -> {str(result.get('text') or result.get('error'))[:80]}")
    await _json_response(writer, result, 200 if result.get("ok") else 400)


def _multipart_audio(body: bytes, ctype: str):
    """Pull the audio part and the lang field out of a multipart body."""
    m = re.search(r'boundary="?([^";]+)"?', ctype)
    if not m:
        return body, ""
    dash = b"--" + m.group(1).encode()
    audio, lang = b"", ""
    for part in body.split(dash):
        if b"\r\n\r\n" not in part:
            continue
        head, _, data = part.partition(b"\r\n\r\n")
        head_s = head.decode("latin1", "replace")
        data = data.rstrip(b"\r\n")
        name_m = re.search(r'name="([^"]*)"', head_s)
        if not name_m:
            continue
        name = name_m.group(1)
        if name == "lang":
            lang = data.decode("utf-8", "replace").strip()
        elif name in ("audio", "file", "blob"):
            audio = data
    return audio, lang


async def _json_response(writer, obj, code=200):
    payload = json.dumps(obj).encode()
    resp = (
        f"HTTP/1.1 {code} {'OK' if code == 200 else 'Error'}\r\n"
        f"Content-Type: application/json\r\n"
        f"Content-Length: {len(payload)}\r\n"
        f"Cache-Control: no-store\r\n"
        f"\r\n"
    ).encode()
    writer.write(resp + payload)
    await writer.drain()


async def http_serve(writer, method, path):
    """Serve the UI file over plain HTTP (same origin as the WebSocket)."""
    if method != "GET":
        writer.write(b"HTTP/1.1 405 Method Not Allowed\r\nContent-Length: 0\r\n\r\n")
        await writer.drain()
        return
    path = path.split("?", 1)[0]
    if path in ("/", ""):
        path = "/helix-ui.html"
    file_path = os.path.join(UI_DIR, path.lstrip("/"))
    real_path = os.path.realpath(file_path)
    real_ui = os.path.realpath(UI_DIR)
    if not (real_path == real_ui or real_path.startswith(real_ui + os.sep)):
        writer.write(b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n")
        await writer.drain()
        return
    if not os.path.isfile(real_path):
        writer.write(b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n")
        await writer.drain()
        return
    try:
        with open(real_path, "rb") as f:
            body = f.read()
    except OSError:
        writer.write(b"HTTP/1.1 500 Internal Server Error\r\nContent-Length: 0\r\n\r\n")
        await writer.drain()
        return
    ctype, _ = mimetypes.guess_type(real_path)
    ctype = ctype or "application/octet-stream"
    resp = (
        f"HTTP/1.1 200 OK\r\n"
        f"Content-Type: {ctype}\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"Cache-Control: no-store, no-cache, must-revalidate\r\n"
        f"Access-Control-Allow-Origin: *\n"
        f"\r\n"
    ).encode()
    writer.write(resp + body)
    await writer.drain()


def _watch_parent():
    """Exit when the parent process dies.

    PR_SET_PDEATHSIG covers the common case, but it is not available on
    every kernel/ABI combination and it does not fire if the parent is
    re-parented. Polling getppid() catches every case: SIGKILL, a crash,
    a session logout, anything. Without this the bridge outlives the app
    and keeps holding its port.
    """
    start_ppid = os.getppid()
    while True:
        time.sleep(1.0)
        if os.getppid() != start_ppid:
            os._exit(0)


def _start_parent_watch():
    try:
        t = threading.Thread(target=_watch_parent, daemon=True)
        t.start()
    except Exception:
        pass


def _selftest():
    """Check the status-derivation rules against a throwaway DB. No Hermes involved."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        c = sqlite3.connect(path)
        c.execute(
            "CREATE TABLE tasks (id TEXT,title TEXT,assignee TEXT,status TEXT,"
            "created_at INTEGER,started_at INTEGER,last_heartbeat_at INTEGER,"
            "current_run_id INTEGER,result TEXT)"
        )
        c.execute(
            "CREATE TABLE task_events (id INTEGER PRIMARY KEY,task_id TEXT,"
            "kind TEXT,payload TEXT,created_at INTEGER)"
        )
        c.executemany("INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?)", [
            ("t1", "running task", "pc", "running", 1, 1, 1, 1, ""),
            ("t2", "old stuck", "research", "blocked", 1, None, 1, None, ""),
            ("t3", "finished", "helix", "done", 1, None, None, None, ""),
        ])
        c.commit()
        c.close()

        def state(pid):
            global KANBAN_DB
            old, KANBAN_DB = KANBAN_DB, path
            conn = kanban_connect()
            try:
                return profile_state(conn, pid)
            finally:
                conn.close()
                KANBAN_DB = old

        assert state("pc")[0] == "working", state("pc")
        assert state("pc")[1]["id"] == "t1"
        assert state("research")[0] == "blocked", state("research")
        assert state("nobody")[0] == "idle", state("nobody")
        assert state("pc")[0] != "blocked"
        print("selftest OK: working / blocked / idle all derive correctly")
    finally:
        os.unlink(path)


# ── Main ─────────────────────────────────────────────────────────────────────

async def main(port=None):
    port = port or PORT
    _start_parent_watch()
    _start_board_watcher()
    server = await asyncio.start_server(handle_client, HOST, port)
    print(f"helix bridge on ws://{HOST}:{port}  (ctrl-c to stop)", flush=True)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Helix WebSocket bridge")
    ap.add_argument("--port", type=int, default=PORT,
                    help="TCP port on 127.0.0.1 (loopback only)")
    ap.add_argument("--selftest", action="store_true",
                    help="check the status rules against a throwaway DB and exit")
    args = ap.parse_args()
    if args.selftest:
        _selftest()
        sys.exit(0)
    try:
        asyncio.run(main(args.port))
    except KeyboardInterrupt:
        print("\nstopped")
