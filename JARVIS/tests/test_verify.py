"""Tests for verify.py — the post-action verification layer.

Two kinds of coverage:

1. **Honest actions** — a real write/delete/move/chmod must come back
   byte-for-byte unchanged (verification is silent when reality agrees).
2. **Lying actions** — the action function is monkeypatched to return a
   success message without doing the work; the wrapper must append
   ``⚠️ VERIFICATION FAILED: ...`` so no caller can act on it.

Plus the safety properties: disabled by env var, and a broken verifier can
never break the action it is watching.
"""

import os
import stat
from pathlib import Path

import pytest

import verify as verify_module
from actions import file_controller as fc_module
from actions.file_controller import file_controller


@pytest.fixture(autouse=True)
def _isolate_cwd(monkeypatch):
    """Navigation tests must not leak the module's working directory."""
    monkeypatch.setitem(fc_module._STATE, "cwd", Path.cwd())


def call(params: dict) -> str:
    return file_controller(parameters=params)


# ------------------------------------------------------------- wiring checks

def test_file_controller_is_wrapped_by_the_verifier():
    assert getattr(file_controller, "__verified_by__", None) == "file_controller"


def test_wrapper_preserves_the_callable_signature():
    import inspect
    params = list(inspect.signature(file_controller).parameters)
    assert params == ["parameters", "response", "player", "session_memory"]


def test_wrapper_preserves_name_and_doc():
    assert file_controller.__name__ == "file_controller"
    assert file_controller.__doc__ is None or isinstance(file_controller.__doc__, str)


# ------------------------------------------------- honest actions stay silent

def test_real_write_is_returned_unchanged(tmp_path):
    out = call({"action": "write", "path": str(tmp_path), "name": "a.txt",
                "content": "hello"})
    assert out == "Written to: a.txt"
    assert "VERIFICATION" not in out


def test_real_create_folder_is_returned_unchanged(tmp_path):
    out = call({"action": "create_folder", "path": str(tmp_path), "name": "sub"})
    assert out.startswith("Folder created")
    assert "VERIFICATION" not in out


def test_real_delete_is_returned_unchanged(tmp_path):
    target = tmp_path / "gone.txt"
    target.write_text("x")
    out = call({"action": "delete", "path": str(target), "permanent": True})
    assert "deleted permanently" in out
    assert "VERIFICATION" not in out
    assert not target.exists()


def test_real_move_and_copy_are_returned_unchanged(tmp_path):
    src = tmp_path / "src.txt"
    src.write_text("payload")
    dest_dir = tmp_path / "out"
    dest_dir.mkdir()

    copied = call({"action": "copy", "path": str(src), "destination": str(dest_dir)})
    assert copied.startswith("Copied:")
    assert "VERIFICATION" not in copied
    assert (dest_dir / "src.txt").read_text() == "payload"

    moved = call({"action": "move", "path": str(src), "destination": str(dest_dir)})
    assert moved.startswith("Moved:")
    assert "VERIFICATION" not in moved
    assert not src.exists()


def test_real_rename_is_returned_unchanged(tmp_path):
    target = tmp_path / "old.txt"
    target.write_text("x")
    out = call({"action": "rename", "path": str(target), "new_name": "new.txt"})
    assert out.startswith("Renamed:")
    assert "VERIFICATION" not in out
    assert (tmp_path / "new.txt").exists()


def test_real_chmod_is_returned_unchanged(tmp_path):
    script = tmp_path / "run.sh"
    script.write_text("#!/bin/sh\n")
    out = call({"action": "chmod", "path": str(script), "permission": "755"})
    assert out.startswith("Permissions of")
    assert "VERIFICATION" not in out
    assert stat.S_IMODE(script.stat().st_mode) == 0o755


def test_read_and_find_results_pass_through_untouched(tmp_path):
    target = tmp_path / "note.txt"
    target.write_text("content that mentions failure, error, denied")

    read = call({"action": "read", "path": str(target)})
    assert read == "content that mentions failure, error, denied"
    assert "VERIFICATION" not in read

    found = call({"action": "find", "path": str(tmp_path), "extension": ".txt"})
    assert "note.txt" in found
    assert "VERIFICATION" not in found


def test_unknown_action_is_not_annotated():
    out = call({"action": "definitely_not_an_action"})
    assert out.startswith("Unknown action")
    assert "VERIFICATION" not in out


def test_capabilities_text_is_not_annotated():
    out = call({"action": "capabilities"})
    assert "Navigate" in out
    assert "VERIFICATION" not in out


# ------------------------------------------------- lying actions get caught

def test_write_claiming_success_without_writing_is_caught(tmp_path, monkeypatch):
    def lying_write(path, content="", append=False, base64_encoded=False,
                    parameters=None):
        return f"Written to: {Path(path).name}"

    monkeypatch.setattr(fc_module, "write_file", lying_write)

    out = call({"action": "write", "path": str(tmp_path), "name": "phantom.txt",
                "content": "some content"})

    assert out.startswith("Written to: phantom.txt")
    assert "⚠️ VERIFICATION FAILED" in out
    assert "phantom.txt" in out
    assert not (tmp_path / "phantom.txt").exists()


def test_partial_write_is_caught(tmp_path, monkeypatch):
    def short_write(path, content="", append=False, base64_encoded=False,
                    parameters=None):
        Path(path).write_text(content[:3], encoding="utf-8")
        return f"Written to: {Path(path).name}"

    monkeypatch.setattr(fc_module, "write_file", short_write)

    out = call({"action": "write", "path": str(tmp_path), "name": "short.txt",
                "content": "0123456789"})

    assert "⚠️ VERIFICATION FAILED" in out
    assert "10 were written" in out
    assert (tmp_path / "short.txt").stat().st_size == 3


def test_create_file_claiming_success_without_creating_is_caught(tmp_path,
                                                                  monkeypatch):
    monkeypatch.setattr(
        fc_module, "create_file",
        lambda path, content="", parameters=None: f"File created: {Path(path).name}"
    )
    out = call({"action": "create_file", "path": str(tmp_path),
                "name": "missing.txt", "content": "x"})
    assert "⚠️ VERIFICATION FAILED" in out
    assert not (tmp_path / "missing.txt").exists()


def test_delete_claiming_success_but_leaving_the_file_is_caught(tmp_path,
                                                                monkeypatch):
    monkeypatch.setattr(
        fc_module, "delete_file",
        lambda path, confirm=True, permanent=False, parameters=None:
            f"Moved to Recycle Bin: {Path(path).name}"
    )
    target = tmp_path / "still_here.txt"
    target.write_text("x")

    out = call({"action": "delete", "path": str(target), "permanent": True})
    assert "⚠️ VERIFICATION FAILED" in out
    assert "still present" in out


def test_delete_claiming_failure_but_deleting_anyway_is_caught(tmp_path,
                                                               monkeypatch):
    def lying_failure(path, confirm=True, permanent=False, parameters=None):
        Path(path).unlink()          # really deletes it...
        return "Could not delete: permission denied"

    monkeypatch.setattr(fc_module, "delete_file", lying_failure)
    target = tmp_path / "vanished.txt"
    target.write_text("x")

    out = call({"action": "delete", "path": str(target), "permanent": True})
    assert "⚠️ VERIFICATION FAILED" in out
    assert "is gone" in out


def test_move_claiming_success_without_moving_is_caught(tmp_path, monkeypatch):
    monkeypatch.setattr(
        fc_module, "move_file",
        lambda source, destination, parameters=None:
            f"Copied over: {Path(source).name}"
    )
    src = tmp_path / "not_moved.txt"
    src.write_text("x")
    dest = tmp_path / "elsewhere.txt"

    out = call({"action": "move", "path": str(src), "destination": str(dest)})
    assert "⚠️ VERIFICATION FAILED" in out
    assert "does not exist" in out


def test_chmod_claiming_success_without_changing_mode_is_caught(tmp_path,
                                                                monkeypatch):
    monkeypatch.setattr(
        fc_module, "chmod_path",
        lambda path, permission, recursive=False, parameters=None:
            f"Permissions of {Path(path).name} → {permission}"
    )
    script = tmp_path / "nope.sh"
    script.write_text("#!/bin/sh\n")
    original_mode = oct(stat.S_IMODE(script.stat().st_mode))

    out = call({"action": "chmod", "path": str(script), "permission": "755"})
    assert "⚠️ VERIFICATION FAILED" in out
    assert "0o755" in out          # the mode that was requested
    assert original_mode in out    # the mode it actually still has


def test_create_folder_claiming_success_without_mkdir_is_caught(tmp_path,
                                                                monkeypatch):
    monkeypatch.setattr(
        fc_module, "create_folder",
        lambda path, parameters=None: f"Folder created: {path}"
    )
    out = call({"action": "create_folder", "path": str(tmp_path), "name": "nope"})
    assert "⚠️ VERIFICATION FAILED" in out
    assert not (tmp_path / "nope").exists()


def test_navigating_to_the_wrong_directory_is_caught(tmp_path, monkeypatch):
    monkeypatch.setattr(fc_module, "navigate_to",
                        lambda path="home": "Now in: /definitely/not/there")
    out = call({"action": "cd", "path": str(tmp_path)})
    assert "⚠️ VERIFICATION FAILED" in out
    assert "navigation state" in out


def test_honest_cd_passes(tmp_path, monkeypatch):
    seen = {}

    def honest_navigate(path="home"):
        resolved = fc_module._resolve_path(str(path))
        fc_module._STATE["cwd"] = resolved
        seen["path"] = resolved
        return f"Now in: {resolved}"

    monkeypatch.setattr(fc_module, "navigate_to", honest_navigate)
    out = call({"action": "cd", "path": str(tmp_path)})
    assert out.startswith(f"Now in: {tmp_path}")
    assert "VERIFICATION" not in out


# ------------------------------------------------------- safety / switches

def test_verification_can_be_switched_off(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_VERIFY", "0")
    monkeypatch.setattr(
        fc_module, "write_file",
        lambda path, content="", append=False, base64_encoded=False,
        parameters=None: f"Written to: {Path(path).name}"
    )
    out = call({"action": "write", "path": str(tmp_path), "name": "ghost.txt",
                "content": "x"})
    assert out == "Written to: ghost.txt"
    assert "VERIFICATION" not in out


@pytest.mark.parametrize("flag", ["0", "off", "false", "no", "disabled"])
def test_disabled_flag_spellings(monkeypatch, flag):
    monkeypatch.setenv("JARVIS_VERIFY", flag)
    assert verify_module.is_enabled() is False


def test_enabled_by_default(monkeypatch):
    monkeypatch.delenv("JARVIS_VERIFY", raising=False)
    assert verify_module.is_enabled() is True


def test_a_broken_verifier_never_breaks_the_action(tmp_path, monkeypatch):
    def explode(params, action, result):
        raise RuntimeError("verifier bug")

    monkeypatch.setitem(verify_module._VERIFIERS, "file_controller", explode)

    out = call({"action": "write", "path": str(tmp_path), "name": "safe.txt",
                "content": "still works"})
    assert out == "Written to: safe.txt"
    assert (tmp_path / "safe.txt").exists()


def test_unregistering_the_verifier_leaves_results_alone(tmp_path, monkeypatch):
    monkeypatch.delitem(verify_module._VERIFIERS, "file_controller")
    monkeypatch.setattr(
        fc_module, "write_file",
        lambda path, content="", append=False, base64_encoded=False,
        parameters=None: f"Written to: {Path(path).name}"
    )
    out = call({"action": "write", "path": str(tmp_path), "name": "raw.txt",
                "content": "x"})
    assert out == "Written to: raw.txt"


# -------------------------------------------------------------- primitives

@pytest.mark.parametrize("message,expect_failure", [
    ("Written to: notes.txt", False),
    ("File created (elevated): notes.txt", False),
    ("Moved to Recycle Bin: notes.txt", False),
    ("Copied: a.txt → out/", False),
    ("Renamed: a.txt → b.txt", False),
    ("Could not create file: no space left", True),
    ("Permission denied: /root/x. Re-run with elevated=true", True),
    ("Not found: /tmp/ghost", True),
    ("Source not found: /tmp/ghost", True),
    ("A file named 'x' already exists.", True),
    ("", True),
    ("Unknown action: 'nope'", True),
    ("Unsupported file type: xyz", True),
])
def test_failure_marker_detection(message, expect_failure):
    assert verify_module.looks_like_failure(message) is expect_failure


def test_process_running_detects_a_real_process():
    assert verify_module.process_running("python") is True
    assert verify_module.process_running("/usr/bin/python3") is True
    assert verify_module.process_running("definitely-not-a-real-process-xyz") is False
    assert verify_module.process_running("") is False


def test_check_file_action_reports_unverifiable_actions_as_none(tmp_path):
    ok, reason = verify_module.check_file_action(
        {"path": str(tmp_path)}, "info", "Owner: me")
    assert ok is None and reason == ""
