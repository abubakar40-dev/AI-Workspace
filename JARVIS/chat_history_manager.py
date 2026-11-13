# chat_history_manager.py
#
# Stores every Jarvis conversation turn as human-readable markdown, one
# file per calendar day, in a top-level chat_history/ folder. This is
# separate from memory/personal_memory.sqlite3 (which stores extracted
# facts about the person) -- this stores the raw conversation itself, so
# Jarvis can recall "what did we talk about last Tuesday" or search for a
# specific past exchange, not just the facts distilled from it.
#
# Files look like:  chat_history/2026-08-26.md
#
#   ## 14:32
#   **You:** remind me to call the bank tomorrow
#   **Jarvis:** Reminder set for tomorrow at 9 AM.
#
# No extra dependencies -- plain text files, plain substring search.

import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock


def _get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


BASE_DIR    = _get_base_dir()
HISTORY_DIR = BASE_DIR / "chat_history"
_lock       = Lock()


def _ensure_dir() -> None:
    os.makedirs(HISTORY_DIR, exist_ok=True)


def _day_path(dt: datetime | None = None) -> Path:
    dt = dt or datetime.now()
    return HISTORY_DIR / f"{dt.strftime('%Y-%m-%d')}.md"


def log_turn(user_text: str, jarvis_text: str, source: str = "voice") -> None:
    """Appends one conversation turn to today's markdown file."""
    user_text = (user_text or "").strip()
    jarvis_text = (jarvis_text or "").strip()
    if not user_text and not jarvis_text:
        return

    _ensure_dir()
    now = datetime.now()
    path = _day_path(now)

    with _lock:
        is_new_file = not path.exists()
        with open(path, "a", encoding="utf-8") as f:
            if is_new_file:
                f.write(f"# Jarvis conversation log — {now.strftime('%A, %B %d, %Y')}\n\n")
            f.write(f"## {now.strftime('%H:%M')}")
            if source != "voice":
                f.write(f" ({source})")
            f.write("\n")
            if user_text:
                f.write(f"**You:** {user_text}\n")
            if jarvis_text:
                f.write(f"**Jarvis:** {jarvis_text}\n")
            f.write("\n")


def list_days() -> list[str]:
    """Returns available dates (YYYY-MM-DD) with logged history, newest first."""
    _ensure_dir()
    days = [p.stem for p in HISTORY_DIR.glob("*.md")]
    return sorted(days, reverse=True)


def get_day(date_str: str) -> str:
    """Returns the full markdown content for a specific date (YYYY-MM-DD),
    or an empty string if nothing was logged that day."""
    path = HISTORY_DIR / f"{date_str}.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def get_relative_day(days_ago: int) -> tuple[str, str]:
    """Convenience for 'yesterday' (days_ago=1), 'today' (0), etc.
    Returns (date_str, content)."""
    dt = datetime.now() - timedelta(days=days_ago)
    date_str = dt.strftime("%Y-%m-%d")
    return date_str, get_day(date_str)


def search(query: str, limit: int = 15) -> list[dict]:
    """Plain substring search (case-insensitive) across all logged days.
    Returns matches with their date and the matching line, most recent
    days first."""
    query = (query or "").strip().lower()
    if not query:
        return []

    _ensure_dir()
    results = []
    for date_str in list_days():
        path = HISTORY_DIR / f"{date_str}.md"
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines):
            if query in line.lower():
                # include a little context: the timestamp heading above it
                heading = ""
                for j in range(i, -1, -1):
                    if lines[j].startswith("## "):
                        heading = lines[j].lstrip("#").strip()
                        break
                results.append({"date": date_str, "time": heading, "line": line.strip()})
                if len(results) >= limit:
                    return results
    return results


def summarize_matches(query: str, limit: int = 8) -> str:
    """Human-readable summary of search results, for Jarvis to speak/read
    back directly."""
    matches = search(query, limit=limit)
    if not matches:
        return f"I couldn't find anything about '{query}' in our conversation history."

    lines = [f"Found {len(matches)} mention(s) of '{query}':"]
    for m in matches:
        clean = re.sub(r"\*\*(You|Jarvis):\*\*\s*", "", m["line"])
        lines.append(f"- {m['date']} at {m['time']}: {clean}")
    return "\n".join(lines)


if __name__ == "__main__":
    print("Chat history days available:", list_days())
    if len(sys.argv) > 1:
        print(summarize_matches(" ".join(sys.argv[1:])))
