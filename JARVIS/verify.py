"""
verify.py — post-action verification layer ("never assume success").

Audit Phase 2 item #3: *"Add verification wrapper — Decorator to verify
action results (file exists, process running, etc.)"*.

The problem it solves: an action returns a **string it wrote itself**.
`write_file()` can print ``Written to: notes.txt`` while the disk never
changed (full filesystem, race with another process, a silent sudo failure,
a bug).  Anything downstream — Jarvis's reply, the planner, a later step —
then reasons about a world that does not exist.

So after a mutating action runs, this module re-reads the *actual* system
state and compares it with what the action claimed:

  * claim succeeded  -> reality must match, or the result gets an explicit
    ``⚠️ VERIFICATION FAILED: ...`` line appended,
  * claim failed     -> for `delete`, reality must agree the item is still
    there (a "failed" delete that actually removed something is reported too),
  * nothing to check (read/list/find/info/...) -> the result passes through
    byte-for-byte untouched.

Successful verifications add NO text, so every existing message, test and
voice line stays exactly as it was.

Disable entirely with ``JARVIS_VERIFY=0`` (also: off/false/no/disabled).
The wrapper never raises — a broken verifier degrades to "no verification"
rather than breaking the action it was watching.

Usage:
    from verify import verify_action

    @verify_action("file_controller")
    def file_controller(parameters, response=None, player=None, ...):
        ...
"""

from __future__ import annotations

import functools
import os
import re
from pathlib import Path

# Words that mean "the action did NOT do the thing".  Kept deliberately
# conservative: these are matched against Jarvis's own action messages, not
# against file contents (read-only actions are never verified anyway).
FAILURE_MARKERS = (
    "could not",
    "cannot",
    "can't",
    "unable",
    "failed",
    "failure",
    "permission denied",
    "not found",
    "no such",
    "does not exist",
    "already exists",
    "unknown action",
    "unsupported",
    "unavailable",
    "not available",
    "not installed",
    "invalid",
    "refused",
    "no file path",
    "nothing to",
    "no matches",
    "no entries",
    "not a file",
    "not a directory",
    "error:",
    "exception",
)

FAIL_PREFIX = "⚠️ VERIFICATION FAILED: "


def is_enabled() -> bool:
    """Verification can be turned off with JARVIS_VERIFY=0."""
    flag = os.environ.get("JARVIS_VERIFY", "1")
    return str(flag).strip().lower() not in {"0", "off", "false", "no", "disabled"}


def looks_like_failure(result) -> bool:
    """True when an action message reports that it did NOT succeed."""
    text = str(result or "").strip().lower()
    if not text:
        return True
    return any(marker in text for marker in FAILURE_MARKERS)


def process_running(name: str) -> bool:
    """Best-effort 'is this process alive?' check for action verifiers."""
    needle = str(name or "").strip().lower()
    if not needle:
        return False
    try:
        import subprocess
        out = subprocess.run(
            ["ps", "-A", "-o", "comm="],
            capture_output=True, text=True, timeout=10,
        )
        procs = [line.strip().lower() for line in (out.stdout or "").splitlines()]
    except Exception:
        return False
    base = needle.rsplit("/", 1)[-1]
    return any(proc == base or proc == needle or proc.endswith("/" + base)
               for proc in procs)


# ---------------------------------------------------------------------------
#  file_controller verifier
# ---------------------------------------------------------------------------

def _target(params: dict, resolve) -> Path:
    """Same path the dispatcher hands to the action (path + name)."""
    path = str(params.get("path") or "desktop")
    name = str(params.get("name") or "")
    base = resolve(path)
    return base / name if name else base


def _has(params: dict, *keys) -> bool:
    for key in keys:
        value = params.get(key)
        if value is None:
            continue
        if isinstance(value, bool):
            if value:
                return True
            continue
        if str(value).strip().lower() in {"1", "true", "yes", "on"}:
            return True
    return False


def _content_length(params: dict):
    """Bytes the action should have written, or None if not knowable."""
    content = params.get("content")
    if content in (None, ""):
        return 0
    if _has(params, "base64_encoded", "base64"):
        import base64
        try:
            return len(base64.b64decode(str(content), validate=False))
        except Exception:
            return None
    try:
        return len(str(content).encode("utf-8"))
    except Exception:
        return None


def _move_destination(src: Path, params: dict, resolve) -> Path | None:
    raw = params.get("destination") or params.get("target") or ""
    if not raw:
        return None
    return resolve(str(raw))


def check_file_action(params: dict, action: str, result: str):
    """
    Verify one file_controller action against the real filesystem.

    Returns ``(ok, reason)`` where ``ok`` is True (verified), False (the
    claim does not match reality — ``reason`` explains why) or None (nothing
    to verify / verification inconclusive).
    """
    from actions.file_controller import _ACTION_ALIASES, _STATE, _resolve_path

    params = params or {}
    action = str(action or params.get("action") or params.get("command")
                 or "").lower().strip()
    action = _ACTION_ALIASES.get(action, action)
    text = str(result or "")
    failed = looks_like_failure(text)

    def target() -> Path:
        return _target(params, _resolve_path)

    # ------------------------------------------------- create / write / append
    if action in ("create_file", "write", "append"):
        if failed:
            return None, ""
        t = target()
        if not t.exists() or not t.is_file():
            return False, f"'{action}' reported success but {t} does not exist"
        if os.name == "posix":
            expected = _content_length(params)
            if expected is not None and expected > 0:
                actual = t.stat().st_size
                appending = action == "append" or _has(params, "append")
                if appending:
                    if actual < expected:
                        return False, (
                            f"{t} is {actual} bytes but {expected} were appended"
                        )
                elif actual != expected:
                    return False, (
                        f"{t} is {actual} bytes but {expected} were written"
                    )
        return True, ""

    # ---------------------------------------------------------- create_folder
    if action == "create_folder":
        if failed:
            return None, ""
        t = target()
        if not t.exists():
            return False, f"'create_folder' reported success but {t} does not exist"
        if not t.is_dir():
            return False, f"{t} exists but is not a folder"
        return True, ""

    # ------------------------------------------------------------------ delete
    if action == "delete":
        t = target()
        present = t.exists() or t.is_symlink()
        if failed:
            # The action said it could not delete: the item must still be there.
            if not present:
                return False, f"'delete' reported failure but {t} is gone"
            return None, ""
        if present:
            return False, f"'delete' reported success but {t} is still present"
        return True, ""

    # ------------------------------------------------------------ move / copy
    if action in ("move", "copy"):
        if failed:
            return None, ""
        src = target()
        dst = _move_destination(src, params, _resolve_path)
        if dst is None:
            return None, ""
        landed = dst / src.name if (dst / src.name).exists() else None
        if landed is None and dst.exists() and not dst.is_dir():
            landed = dst
        if landed is None:
            return False, f"'{action}' reported success but {dst} does not exist"
        if action == "move" and (src.exists() or src.is_symlink()):
            return False, f"'move' reported success but the source is still at {src}"
        return True, ""

    # ----------------------------------------------------------------- rename
    if action == "rename":
        if failed:
            return None, ""
        src = target()
        new_name = str(params.get("new_name") or "")
        if not new_name:
            return None, ""
        new_path = (Path(new_name) if str(new_name).startswith("/")
                    else src.parent / new_name)
        if not new_path.exists():
            return False, f"'rename' reported success but {new_path} does not exist"
        if src.exists() or src.is_symlink():
            return False, f"'rename' reported success but {src} is still present"
        return True, ""

    # ------------------------------------------------------------------ chmod
    if action == "chmod":
        if failed:
            return None, ""
        t = target()
        if not t.exists():
            return False, f"'chmod' reported success but {t} does not exist"
        spec = str(params.get("permission") or params.get("mode") or "").strip()
        if re.fullmatch(r"[0-7]{3,4}", spec):
            try:
                want = int(spec, 8) & 0o777
                have = t.stat().st_mode & 0o777
            except OSError:
                return None, ""
            if have != want:
                return False, f"{t} is {oct(have)} but {oct(want)} was requested"
        return True, ""

    # ---------------------------------------------------------------- archive
    if action == "archive":
        if failed:
            return None, ""
        match = re.match(r"Archive created:\s*(.+?)\s*\(", text.strip())
        if not match:
            return None, ""
        out = Path(match.group(1).strip())
        if not out.exists():
            return False, f"'archive' reported {out} but it does not exist"
        return True, ""

    # ---------------------------------------------------------------- extract
    if action == "extract":
        if failed:
            return None, ""
        if "→" in text:
            dest = text.rsplit("→", 1)[-1].strip()
            if not Path(dest).exists():
                return False, f"'extract' reported {dest} but it does not exist"
            return True, ""
        return None, ""

    # ------------------------------------------------------------------ share
    if action == "share":
        if failed:
            return None, ""
        method = str(params.get("method") or "auto").lower()
        if method == "folder" and "→" in text:
            dest = text.rsplit("→", 1)[-1].strip()
            if not Path(dest).exists():
                return False, f"'share' reported {dest} but it does not exist"
            return True, ""
        if method == "link":
            shares = _STATE.get("shares") or {}
            if shares and any(token in text for token in shares):
                return True, ""
        return None, ""

    # ------------------------------------------------------------ navigation
    if action == "cd":
        if failed:
            return None, ""
        match = re.search(r"Now in:\s*(.+)\s*$", text)
        if not match:
            return None, ""
        claimed = match.group(1).strip()
        cwd = os.path.normpath(str(_STATE.get("cwd") or ""))
        if cwd != os.path.normpath(claimed):
            return False, (
                f"navigation state is '{cwd}' but the result claims '{claimed}'"
            )
        return True, ""

    # Anything else (read, find, list, info, users, partitions, trash, open...)
    # is either read-only or too stateful to check honestly — leave it alone.
    return None, ""


# ---------------------------------------------------------------------------
#  generic entry points
# ---------------------------------------------------------------------------

_VERIFIERS = {
    "file_controller": check_file_action,
}


def verify(tool: str, params: dict, result: str):
    """Run the verifier registered for ``tool``. Never raises."""
    if not is_enabled():
        return None, ""
    verifier = _VERIFIERS.get(tool)
    if verifier is None:
        return None, ""
    try:
        params = params or {}
        action = str(params.get("action") or params.get("command") or "")
        ok, reason = verifier(params, action, result)
    except Exception as exc:  # a broken verifier must not break the action
        print(f"[Verify] verifier error ({tool}): {exc}")
        return None, ""
    return ok, reason


def verify_action(tool: str):
    """
    Decorator: check an action's returned message against real system state.

    On a verified success the result is returned unchanged.  On a
    contradiction a ``⚠️ VERIFICATION FAILED: ...`` line is appended so the
    caller (and the LLM) can never act on a success that did not happen.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            try:
                params = kwargs.get("parameters")
                if params is None and args and isinstance(args[0], dict):
                    params = args[0]
                if not isinstance(params, dict):
                    params = {}
                ok, reason = verify(tool, params,
                                    result if isinstance(result, str) else "")
            except Exception as exc:
                print(f"[Verify] could not verify {tool}: {exc}")
                ok, reason = None, ""
            if ok is False and reason and isinstance(result, str):
                print(f"[Verify] {tool}: {reason}")
                return f"{result}\n{FAIL_PREFIX}{reason}"
            return result

        wrapper.__verified_by__ = tool
        return wrapper

    return decorator
