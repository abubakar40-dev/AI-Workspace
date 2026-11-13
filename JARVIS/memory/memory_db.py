# memory/memory_db.py
#
# SQLite-backed long-term personal memory for Jarvis.
#
# Replaces the old flat-JSON store (long_term.json), which had a hard
# MEMORY_MAX_CHARS=2200 cap that silently deleted the oldest facts once
# exceeded -- a real problem for someone who wants Jarvis to build up a
# genuinely deep, lifelong picture of them (dreams, past, present, future).
#
# The database itself is unbounded -- nothing is ever silently deleted.
# Only the prompt-context builder (format_memory_for_prompt) trims what
# gets sent to the LLM each turn, to keep the context budget sane; the
# full history always remains queryable in the database.

import hashlib
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from threading import Lock


def _get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR   = _get_base_dir()
CONFIG_DIR = BASE_DIR / "memory"
DB_FILE    = CONFIG_DIR / "personal_memory.sqlite3"

# Legacy JSON store, migrated automatically on first run if present.
LEGACY_JSON_PATH = CONFIG_DIR / "long_term.json"

VALID_CATEGORIES = {
    "identity",
    "past",
    "present",
    "future",
    "dreams",
    "relationships",
    "preferences",
    "personality",
    "projects",
    "notes",
}

_lock = Lock()


def _ensure_dir() -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)


class _ClosingConnection:
    """Wraps a sqlite3.Connection so 'with ...' both commits/rolls back and
    actually closes the connection afterward. (A bare sqlite3.Connection
    used as a context manager only handles the transaction, never closes
    the connection itself -- that bug elsewhere in this project caused a
    file-descriptor leak that crashed the whole app after enough calls.)"""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def __enter__(self) -> sqlite3.Connection:
        return self._conn

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type is None:
                self._conn.commit()
            else:
                self._conn.rollback()
        finally:
            self._conn.close()


def _connect():
    _ensure_dir()
    conn = sqlite3.connect(DB_FILE, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS memory_entries (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            category   TEXT    NOT NULL,
            key        TEXT    NOT NULL,
            value      TEXT    NOT NULL,
            source     TEXT    NOT NULL DEFAULT 'voice',
            created_at TEXT    NOT NULL,
            updated_at TEXT    NOT NULL
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_memory_cat_key
            ON memory_entries(category, key);
        CREATE INDEX IF NOT EXISTS idx_memory_category
            ON memory_entries(category);
        """
    )
    conn.commit()
    return conn


def _key_for(category: str, value: str, key: str | None) -> str:
    if key:
        return key.strip().lower().replace(" ", "_")[:80]
    # Narrative-style facts (past/present/future/dreams/personality/notes)
    # don't naturally have a short key -- derive a stable one from content
    # so re-saving the identical fact updates in place instead of
    # duplicating, but distinct facts in the same category coexist freely.
    digest = hashlib.sha1(value.strip().lower().encode("utf-8")).hexdigest()[:10]
    return f"{category}_{digest}"


def remember(category: str, value: str, key: str | None = None, source: str = "voice") -> str:
    category = category.strip().lower() if category else "notes"
    if category not in VALID_CATEGORIES:
        category = "notes"
    value = str(value).strip()
    if not value:
        return ""

    entry_key = _key_for(category, value, key)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with _lock:
        conn = _connect()
        with _ClosingConnection(conn) as c:
            c.execute(
                """
                INSERT INTO memory_entries (category, key, value, source, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(category, key) DO UPDATE SET
                    value = excluded.value,
                    source = excluded.source,
                    updated_at = excluded.updated_at
                """,
                (category, entry_key, value, source, now, now),
            )
    return entry_key


def forget(category: str, key: str) -> bool:
    with _lock:
        conn = _connect()
        with _ClosingConnection(conn) as c:
            cur = c.execute(
                "DELETE FROM memory_entries WHERE category = ? AND key = ?",
                (category, key),
            )
            return cur.rowcount > 0


def all_entries(category: str | None = None) -> list[dict]:
    with _lock:
        conn = _connect()
        with _ClosingConnection(conn) as c:
            if category:
                rows = c.execute(
                    "SELECT * FROM memory_entries WHERE category = ? ORDER BY updated_at DESC",
                    (category,),
                ).fetchall()
            else:
                rows = c.execute(
                    "SELECT * FROM memory_entries ORDER BY category, updated_at DESC"
                ).fetchall()
            return [dict(r) for r in rows]


def recent(category: str, limit: int = 12) -> list[dict]:
    with _lock:
        conn = _connect()
        with _ClosingConnection(conn) as c:
            rows = c.execute(
                "SELECT * FROM memory_entries WHERE category = ? ORDER BY updated_at DESC LIMIT ?",
                (category, limit),
            ).fetchall()
            return [dict(r) for r in rows]


def count() -> int:
    with _lock:
        conn = _connect()
        with _ClosingConnection(conn) as c:
            row = c.execute("SELECT COUNT(*) AS n FROM memory_entries").fetchone()
            return row["n"] if row else 0


def migrate_legacy_json() -> int:
    """One-time migration from the old long_term.json flat file, if present
    and not yet migrated. Returns the number of facts migrated."""
    if not LEGACY_JSON_PATH.exists():
        return 0

    marker = CONFIG_DIR / ".legacy_json_migrated"
    if marker.exists():
        return 0

    import json
    try:
        data = json.loads(LEGACY_JSON_PATH.read_text(encoding="utf-8"))
    except Exception:
        return 0

    migrated = 0
    # Old categories: identity, preferences, projects, relationships, wishes, notes
    category_map = {"wishes": "future"}  # closest new-schema fit
    for old_cat, items in (data or {}).items():
        if not isinstance(items, dict):
            continue
        new_cat = category_map.get(old_cat, old_cat)
        if new_cat not in VALID_CATEGORIES:
            new_cat = "notes"
        for k, entry in items.items():
            val = entry.get("value") if isinstance(entry, dict) else entry
            if val:
                remember(new_cat, str(val), key=k, source="migrated")
                migrated += 1

    marker.write_text(f"migrated {migrated} facts on {datetime.now().isoformat()}\n")
    return migrated


if __name__ == "__main__":
    n = migrate_legacy_json()
    if n:
        print(f"Migrated {n} facts from long_term.json")
    print(f"Total facts in personal_memory.sqlite3: {count()}")
    for row in all_entries():
        print(f"  [{row['category']}] {row['key']}: {row['value'][:80]}")
