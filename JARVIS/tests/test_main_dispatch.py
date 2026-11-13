"""End-to-end tests: file_controller driven through the REAL tool dispatch.

These exercise `JarvisLive._execute_tool` — the exact code path Gemini Live
uses when the model returns a function call — instead of calling
`file_controller()` directly.  That proves the wiring (import, tool name,
argument dict, executor thread, UI callbacks, FunctionResponse shape) works,
not just the tool itself.

The live-session dependencies are stubbed:
  * `ui`            → recording stub (no Qt widgets)
  * `speak`         → no-op (no audio)
  * `_connect_tool_voice` → no-op (no LLM/network call)
so the suite stays offline and headless.
"""

import asyncio
from pathlib import Path

import pytest

main_module = pytest.importorskip("main", reason="main.py imports unavailable here")
from google.genai import types  # noqa: E402  (same types main.py returns)


class _StubUI:
    """Minimal stand-in for JarvisUI covering everything _execute_tool touches."""

    def __init__(self):
        self.muted = True          # skip LISTENING state churn
        self.current_file = ""
        self.states = []
        self.logs = []

    def set_state(self, state):
        self.states.append(state)

    def update_task_workspace(self, **kwargs):
        pass

    def finish_task_workspace(self, *args, **kwargs):
        pass

    def write_log(self, message):
        self.logs.append(message)


def _make_live():
    live = object.__new__(main_module.JarvisLive)
    live.ui = _StubUI()
    live.speak = lambda text=None: None
    live.speak_error = lambda name, error: None
    # avoid the LLM-backed voice-line generator entirely
    live._connect_tool_voice = lambda name, result: None
    return live


def run_named_tool(name: str, args: dict, call_id: str = "test-call"):
    """Runs one function call of any tool through the real dispatcher."""
    live = _make_live()
    fc = types.FunctionCall(id=call_id, name=name, args=args)
    return asyncio.run(live._execute_tool(fc))


def run_tool(args: dict, call_id: str = "test-call"):
    """Runs one file_controller function call through the real dispatcher."""
    return run_named_tool("file_controller", args, call_id)


def result_of(args: dict, call_id: str = "test-call") -> str:
    response = run_tool(args, call_id)
    assert isinstance(response, types.FunctionResponse)
    assert response.name == "file_controller"
    assert response.id == call_id
    payload = response.response
    assert isinstance(payload, dict) and "result" in payload
    return payload["result"]


# --------------------------------------------------------------- round trips

def test_write_then_read_through_dispatch(tmp_path):
    written = result_of({"action": "write", "path": str(tmp_path),
                         "name": "e2e.txt", "content": "hello dispatch"})
    assert written == "Written to: e2e.txt"

    read_back = result_of({"action": "read", "path": str(tmp_path), "name": "e2e.txt"})
    assert read_back == "hello dispatch"


def test_create_folder_then_list_through_dispatch(tmp_path):
    created = result_of({"action": "create_folder", "path": str(tmp_path),
                         "name": "dispatch_dir"})
    assert created.startswith("Folder created")

    listed = result_of({"action": "list", "path": str(tmp_path)})
    assert "dispatch_dir/" in listed


def test_find_through_dispatch(tmp_path):
    (tmp_path / "needle.pdf").write_text("x")
    (tmp_path / "hay.txt").write_text("x")

    found = result_of({"action": "find", "path": str(tmp_path), "extension": ".pdf"})
    assert "needle.pdf" in found

    found_by_pattern = result_of({"action": "find", "path": str(tmp_path),
                                  "pattern": "*.txt"})
    assert "hay.txt" in found_by_pattern


def test_info_through_dispatch(tmp_path):
    target = tmp_path / "meta.txt"
    target.write_text("payload")
    out = result_of({"action": "info", "path": str(target), "hash": True})
    assert "Owner" in out and "SHA-256" in out


def test_navigate_through_dispatch(tmp_path):
    child = tmp_path / "child"
    child.mkdir()

    out = result_of({"action": "cd", "path": str(child)})
    assert out.startswith(f"Now in: {child}")

    out = result_of({"action": "pwd"})
    assert str(child) in out

    out = result_of({"action": "up"})
    assert out.startswith(f"Now in: {tmp_path}")


def test_share_folder_through_dispatch(tmp_path):
    src = tmp_path / "packet.txt"
    src.write_text("shared payload")
    out_dir = tmp_path / "published"

    out = result_of({"action": "share", "path": str(src), "method": "folder",
                     "destination": str(out_dir)})
    assert "Shared copy" in out
    assert (out_dir / "packet.txt").read_text() == "shared payload"


def test_archive_and_extract_through_dispatch(tmp_path):
    source = tmp_path / "bundle"
    source.mkdir()
    (source / "inside.txt").write_text("zipped")

    out = result_of({"action": "archive", "path": str(source),
                     "destination": str(tmp_path)})
    assert "Archive created" in out
    assert (tmp_path / "bundle.zip").exists()

    out = result_of({"action": "extract", "path": str(tmp_path / "bundle.zip"),
                     "destination": str(tmp_path / "out")})
    assert "Extracted" in out
    assert (tmp_path / "out" / "bundle" / "inside.txt").exists()


def test_delete_permanent_through_dispatch(tmp_path):
    victim = tmp_path / "victim.txt"
    victim.write_text("bye")
    out = result_of({"action": "delete", "path": str(victim), "permanent": True})
    assert "deleted permanently" in out
    assert not victim.exists()


def test_permissions_through_dispatch(tmp_path):
    script = tmp_path / "run.sh"
    script.write_text("#!/bin/sh\n")

    out = result_of({"action": "chmod", "path": str(script), "permission": "755"})
    assert "Permissions of" in out
    assert oct(script.stat().st_mode & 0o777) == oct(0o755)

    out = result_of({"action": "permissions", "path": str(script)})
    assert "Executable: True" in out


def test_capabilities_through_dispatch():
    out = result_of({"action": "capabilities"})
    assert "Navigate" in out and "Share" in out


# ---------------------------------------------------------- legacy + errors

def test_legacy_planner_style_write_still_dispatches(tmp_path, monkeypatch):
    """The planner's classic 'write to desktop' parameters must keep working."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    (tmp_path / "Desktop").mkdir()

    out = result_of({"action": "write", "path": "desktop",
                     "name": "plan.txt", "content": "planned"})
    assert out == "Written to: plan.txt"
    assert (tmp_path / "Desktop" / "plan.txt").read_text() == "planned"


def test_bad_action_is_a_result_not_a_tool_failure():
    out = result_of({"action": "definitely_not_an_action"})
    assert out.startswith("Unknown action")
    assert "failed" not in out


def test_missing_file_reports_through_dispatch(tmp_path):
    out = result_of({"action": "read", "path": str(tmp_path / "ghost.txt")})
    assert out.startswith("File not found")


def test_args_are_not_mutated_by_dispatch():
    """The dispatcher must not modify the model's argument dict in place."""
    args = {"action": "capabilities"}
    snapshot = dict(args)
    run_tool(args)
    assert args == snapshot


def test_stuck_ui_state_returns_to_listening_when_unmuted(tmp_path):
    """With an unmuted UI the dispatcher must restore the LISTENING state."""
    live = _make_live()
    live.ui.muted = False
    fc = types.FunctionCall(id="state-check", name="file_controller",
                            args={"action": "pwd"})
    asyncio.run(live._execute_tool(fc))
    assert live.ui.states and live.ui.states[0] == "THINKING"
    assert live.ui.states[-1] == "LISTENING"


def test_unknown_tool_still_reports_unknown():
    response = run_named_tool("definitely_not_a_tool", {})
    assert response.response["result"] == "Unknown tool: definitely_not_a_tool"
