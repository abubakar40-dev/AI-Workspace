"""Explicit, single-use confirmation for consequential actions.

Rules the audit requires, all enforced here rather than in the UI:

* A token is bound to the **exact** tool and arguments it was issued for. Change
  the file, the recipient or the target and the token no longer matches.
* A token is single-use. Replaying it fails.
* A token expires (default 5 minutes).
* Issuing is explicit; nothing issues one automatically.
* Everything is in-process only. Tokens are never written to disk, so a
  restart invalidates every outstanding approval.

This replaces the previous behaviour where ``confirm.request`` /
``confirm.response`` existed in the bridge protocol but gated nothing.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import threading
import time
from typing import Any, Dict, Mapping, Optional, Tuple

DEFAULT_TTL_SECONDS = 300
_MAX_OUTSTANDING = 256

_lock = threading.Lock()
_tokens: Dict[str, Dict[str, Any]] = {}


def _canonical(tool: str, params: Mapping[str, Any]) -> str:
    """Stable representation of the action being approved."""
    try:
        body = json.dumps(params or {}, sort_keys=True, ensure_ascii=False, default=str)
    except Exception:
        body = repr(sorted((params or {}).items()))
    return f"{tool}\x00{body}"


def _fingerprint(tool: str, params: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical(tool, params).encode("utf-8")).hexdigest()


def issue(tool: str, params: Optional[Mapping[str, Any]] = None,
          ttl: int = DEFAULT_TTL_SECONDS, reason: str = "") -> str:
    """Mint a confirmation token for exactly this tool call."""
    if not tool:
        raise ValueError("confirmation needs a tool name")
    now = time.time()
    token = secrets.token_urlsafe(24)
    with _lock:
        # drop expired entries so the store cannot grow without bound
        for key in [k for k, v in _tokens.items() if v["expires_at"] <= now]:
            _tokens.pop(key, None)
        if len(_tokens) >= _MAX_OUTSTANDING:
            oldest = min(_tokens, key=lambda k: _tokens[k]["issued_at"])
            _tokens.pop(oldest, None)
        _tokens[token] = {
            "tool": tool,
            "fingerprint": _fingerprint(tool, params or {}),
            "issued_at": now,
            "expires_at": now + max(1, int(ttl)),
            "reason": reason[:200],
            "used": False,
        }
    return token


def consume(token: str, tool: str, params: Optional[Mapping[str, Any]] = None) -> Tuple[bool, str]:
    """Validate and burn a token. Returns ``(ok, reason)``."""
    if not token:
        return False, "no token supplied"
    now = time.time()
    with _lock:
        entry = _tokens.get(token)
        if entry is None:
            return False, "unknown or already used token"
        if entry["used"]:
            return False, "token already used"
        if entry["expires_at"] <= now:
            _tokens.pop(token, None)
            return False, "token expired"
        if entry["tool"] != tool:
            return False, "token was issued for a different action"
        if entry["fingerprint"] != _fingerprint(tool, params or {}):
            return False, "the action changed after it was approved"
        entry["used"] = True
        _tokens.pop(token, None)
    return True, "ok"


def pending() -> int:
    """Number of live (unused, unexpired) tokens. Diagnostics only."""
    now = time.time()
    with _lock:
        return sum(1 for v in _tokens.values() if not v["used"] and v["expires_at"] > now)


def revoke_all() -> int:
    """Invalidate every outstanding approval. Returns how many were dropped."""
    with _lock:
        count = len(_tokens)
        _tokens.clear()
    return count
