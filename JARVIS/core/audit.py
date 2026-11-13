"""Append-only audit trail for consequential actions.

Design constraints taken from the audit:

* Never write a secret. Keys are matched case-insensitively and redacted;
  values are truncated so a pasted document cannot flood the log.
* Never rewrite history. One JSON object per line, opened in append mode.
* Never let logging failure break the action. A broken log is reported on
  stderr and the call proceeds.
* One file per month, under the user's data dir, mode 0600.

This is deliberately separate from ``error_logger`` (which records failures).
This records *actions*: who asked for what, what policy decided, and whether it
ran.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
from pathlib import Path
from typing import Any, Mapping, Optional

AUDIT_DIR = Path(os.path.expanduser("~")) / ".local" / "share" / "jarvis" / "audit"

_SECRET_HINTS = (
    "token", "password", "passwd", "secret", "api_key", "apikey", "authorization",
    "cookie", "session", "credential", "wstoken", "private_key",
)
_MAX_VALUE = 300


def _redact(key: str, value: Any) -> Any:
    lowered = (key or "").lower()
    if any(hint in lowered for hint in _SECRET_HINTS):
        return "[redacted]"
    if isinstance(value, str):
        return value if len(value) <= _MAX_VALUE else value[:_MAX_VALUE] + "…"
    if isinstance(value, Mapping):
        return {str(k): _redact(str(k), v) for k, v in list(value.items())[:40]}
    if isinstance(value, (list, tuple)):
        return [_redact("", v) for v in list(value)[:20]]
    return value


def _current_path() -> Path:
    stamp = _dt.datetime.now().strftime("%Y-%m")
    return AUDIT_DIR / f"actions-{stamp}.jsonl"


def record(
    tool: str,
    params: Optional[Mapping[str, Any]] = None,
    decision: Any = None,
    *,
    outcome: str = "",
    detail: str = "",
    source: str = "jarvis",
) -> Optional[str]:
    """Append one audit line. Returns the path written, or None on failure."""
    entry = {
        "at": _dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "tool": tool,
        "source": source,
        "action": "",
        "tier": getattr(decision, "tier", ""),
        "capability": getattr(decision, "capability", None),
        "policy": getattr(decision, "outcome", ""),
        "policy_reason": getattr(decision, "reason", ""),
        "outcome": outcome,
        "detail": detail[:500] if isinstance(detail, str) else "",
        "params": {str(k): _redact(str(k), v) for k, v in (params or {}).items()},
    }
    if isinstance(params, Mapping):
        for key in ("action", "command"):
            value = params.get(key)
            if isinstance(value, str):
                entry["action"] = value[:120]
                break

    try:
        path = _current_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        # Create with 0600 before writing so the mode is never wider.
        fd = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
        return str(path)
    except Exception as exc:  # logging must never break the caller
        print(f"[audit] could not write audit entry: {exc}", file=os.sys.stderr)
        return None


def read_recent(limit: int = 50) -> list[dict]:
    """Return the most recent audit entries (newest last). Test/debug helper."""
    path = _current_path()
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]
    out = []
    for line in lines:
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out
