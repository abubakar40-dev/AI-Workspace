"""Tests for actions/file_controller.py — the full-file-manager layer.

Covers: universal path resolution, CRUD, any-format reading, navigation,
search, permissions, archives, trash, sharing and system info.

Nothing here touches the network or the real recycle bin (the trash dir is
monkeypatched into tmp_path), so the suite is safe to run anywhere.
"""

import base64
import os
import zipfile
from pathlib import Path

import pytest

from actions import file_controller as fc
from actions.file_controller import (
    file_controller,
    _resolve_path,
    current_dir,
    navigate_to,
)


@pytest.fixture(autouse=True)
def _isolate_cwd(tmp_path, monkeypatch):
    """Keep the navigation state (cd/pwd) out of the real process state."""
    monkeypatch.setitem(fc._STATE, "cwd", tmp_path)
    monkeypatch.setitem(fc._STATE, "shares", {})
    yield


def call(**params):
    return file_controller(params, player=None)


# ------------------------------------------------------------ path resolution

@pytest.mark.parametrize("shortcut, expected", [
    ("desktop", Path.home() / "Desktop"),
    ("home", Path.home()),
    ("root", Path("/")),
    ("users", Path("/home")),
])
def test_shortcut_resolution(shortcut, expected):
    assert _resolve_path(shortcut) == expected


def test_shortcut_with_subpath():
    assert _resolve_path("desktop/projects/a.py") == Path.home() / "Desktop" / "projects" / "a.py"


def test_shortcut_is_case_insensitive():
    assert _resolve_path("Desktop") == Path.home() / "Desktop"


def test_absolute_path_anywhere_is_kept():
    assert _resolve_path("/etc/hosts") == Path("/etc/hosts")


def test_relative_path_uses_navigation_state(tmp_path):
    (tmp_path / "sub").mkdir()
    navigate_to(str(tmp_path))
    assert _resolve_path("sub/file.txt") == tmp_path / "sub" / "file.txt"


def test_env_var_and_user_expansion():
    assert _resolve_path("$HOME/expanded") == Path.home() / "expanded"
    assert _resolve_path("~") == Path.home()


def test_dot_dot_is_collapsed_without_touching_disk(tmp_path):
    navigate_to(str(tmp_path))
    assert _resolve_path("../sibling") == tmp_path.parent / "sibling"


# ------------------------------------------------------------------ CRUD

def test_create_read_append_roundtrip(tmp_path):
    assert "File created" in call(action="create_file", path=str(tmp_path),
                                  name="a.txt", content="hello")
    assert call(action="read", path=str(tmp_path), name="a.txt") == "hello"
    assert "Appended" in call(action="write", path=str(tmp_path), name="a.txt",
                              content=" world", append=True)
    assert call(action="read", path=str(tmp_path), name="a.txt") == "hello world"


def test_relative_write_lands_in_current_folder(tmp_path):
    call(action="create_file", path="rel.txt", content="x")
    assert (tmp_path / "rel.txt").exists()


def test_binary_write_via_base64(tmp_path):
    payload = bytes(range(64))
    result = call(action="write", path=str(tmp_path), name="b.bin",
                  content=base64.b64encode(payload).decode(), base64_encoded=True)
    assert "binary" in result
    assert (tmp_path / "b.bin").read_bytes() == payload


def test_create_folder_makes_parents(tmp_path):
    assert "Folder created" in call(action="create_folder",
                                    path=str(tmp_path), name="one/two")
    assert (tmp_path / "one" / "two").is_dir()


def test_move_copy_rename(tmp_path):
    src = tmp_path / "src.txt"
    src.write_text("data")
    target_dir = tmp_path / "dest"
    target_dir.mkdir()

    assert "Moved" in call(action="move", path=str(src), destination=str(target_dir))
    moved = target_dir / "src.txt"
    assert moved.exists() and not src.exists()

    assert "Copied" in call(action="copy", path=str(moved), destination=str(tmp_path))
    assert (tmp_path / "src.txt").exists() and moved.exists()

    assert "Renamed" in call(action="rename", path=str(tmp_path / "src.txt"),
                             new_name="final.txt")
    assert (tmp_path / "final.txt").exists()


def test_delete_permanent(tmp_path):
    victim = tmp_path / "victim.txt"
    victim.write_text("bye")
    result = call(action="delete", path=str(victim), permanent=True)
    assert "deleted permanently" in result
    assert not victim.exists()


def test_unknown_action_reports_cleanly():
    assert call(action="not_a_real_action").startswith("Unknown action")


# ------------------------------------------------------- any-format reading

def test_read_text_truncates_to_budget(tmp_path):
    big = tmp_path / "big.txt"
    big.write_text("x" * 10_000)
    out = call(action="read", path=str(big), max_chars=100)
    assert out.startswith("x" * 100) and "truncated" in out and "10000" in out


def test_read_image_reports_dimensions(tmp_path):
    pytest.importorskip("PIL")
    from PIL import Image
    Image.new("RGB", (40, 20)).save(tmp_path / "i.png")
    out = call(action="read", path=str(tmp_path), name="i.png")
    assert "Image:" in out and "40×20" in out


def test_read_docx_extracts_paragraphs(tmp_path):
    pytest.importorskip("docx")
    from docx import Document
    doc = Document()
    doc.add_paragraph("extraction marker")
    doc.save(tmp_path / "d.docx")
    assert "extraction marker" in call(action="read", path=str(tmp_path), name="d.docx")


def test_read_binary_returns_hex_dump(tmp_path):
    blob = tmp_path / "blob.bin"
    blob.write_bytes(b"\x00\x01\x02" + bytes(range(32)))
    out = call(action="read", path=str(blob))
    assert "binary file" in out.lower() and "hex" in out.lower() and "00000000" in out


def test_read_missing_file(tmp_path):
    assert call(action="read", path=str(tmp_path / "nope.txt")).startswith("File not found")


def test_read_folder_is_rejected(tmp_path):
    assert call(action="read", path=str(tmp_path)).startswith("Not a file")


# ------------------------------------------------------------- navigation

def test_cd_pwd_up_cycle(tmp_path):
    child = tmp_path / "child"
    child.mkdir()

    out = call(action="cd", path=str(child))
    assert out.startswith(f"Now in: {child}")
    assert str(child) in call(action="pwd")

    out = call(action="up")
    assert out.startswith(f"Now in: {tmp_path}")
    assert current_dir() == f"Current directory: {tmp_path}"


def test_list_reports_contents_and_hidden_count(tmp_path):
    (tmp_path / "visible.txt").write_text("1")
    (tmp_path / ".hidden").write_text("2")
    out = call(action="list", path=str(tmp_path))
    assert "visible.txt" in out and "hidden entries" in out
    out_hidden = call(action="list", path=str(tmp_path), show_hidden=True)
    assert ".hidden" in out_hidden


def test_list_of_huge_dir_is_paged(tmp_path):
    for index in range(30):
        (tmp_path / f"f{index:02d}.txt").write_text("x")
    out = call(action="list", path=str(tmp_path), limit=10)
    assert "of 30 items" in out and "more" in out


def test_tree_shows_structure(tmp_path):
    (tmp_path / "inner").mkdir()
    (tmp_path / "inner" / "leaf.txt").write_text("x")
    out = call(action="tree", path=str(tmp_path), depth=2)
    assert "inner/" in out and "leaf.txt" in out


# ------------------------------------------------------------------ search

def test_find_by_extension_and_pattern(tmp_path):
    (tmp_path / "report.pdf").write_text("x")
    (tmp_path / "clip.mp4").write_text("x")
    (tmp_path / "notes.txt").write_text("x")

    assert "report.pdf" in call(action="find", path=str(tmp_path), extension=".pdf")
    assert "clip.mp4" in call(action="find", path=str(tmp_path), pattern="*.mp4")
    assert "notes.txt" in call(action="find", path=str(tmp_path), name="note")


def test_find_respects_max_results(tmp_path):
    for index in range(15):
        (tmp_path / f"n{index}.txt").write_text("x")
    out = call(action="find", path=str(tmp_path), extension=".txt", max_results=4)
    assert out.count("📄") == 4


def test_find_from_filesystem_root_does_not_crash(tmp_path):
    out = call(action="find", path="root", pattern="*", max_results=3)
    assert isinstance(out, str) and "Search error" not in out


def test_find_across_all_user_homes():
    out = call(action="find", path="users", max_results=3, pattern="*")
    assert isinstance(out, str)


def test_largest_and_recent(tmp_path):
    (tmp_path / "big.bin").write_bytes(b"0" * 5000)
    (tmp_path / "small.txt").write_text("x")
    assert "big.bin" in call(action="largest", path=str(tmp_path), count=1)
    assert "most recent" in call(action="recent", path=str(tmp_path), days=1)


# -------------------------------------------------------------- permissions

def test_chmod_numeric_and_symbolic(tmp_path):
    script = tmp_path / "run.sh"
    script.write_text("#!/bin/sh\n")

    call(action="chmod", path=str(script), permission="755")
    assert oct(script.stat().st_mode & 0o777) == oct(0o755)

    call(action="chmod", path=str(script), permission="u+rwx,g-w,o+r")
    assert oct(script.stat().st_mode & 0o777) == oct(0o755)

    out = call(action="permissions", path=str(script))
    assert "Owner" in out and "Executable: True" in out


def test_chmod_rejects_garbage_mode(tmp_path):
    target = tmp_path / "f.txt"
    target.write_text("x")
    assert "Invalid permission string" in call(action="chmod", path=str(target),
                                               permission="banana")


def test_info_includes_owner_perms_and_hash(tmp_path):
    target = tmp_path / "f.txt"
    target.write_text("content")
    out = call(action="info", path=str(target), hash=True)
    for field in ("Owner:", "Permissions:", "SHA-256:", "Full path:"):
        assert field in out


# ------------------------------------------------------------------ trash

@pytest.fixture()
def fake_trash(tmp_path, monkeypatch):
    """Redirect recycle-bin operations into tmp_path so tests never bin real files."""
    trash = tmp_path / "Trash"
    (trash / "files").mkdir(parents=True)
    (trash / "info").mkdir(parents=True)
    monkeypatch.setattr(fc, "_trash_dir", lambda: trash)
    return trash


def test_trash_list_empty_restore(fake_trash):
    item = fake_trash / "files" / "kept.txt"
    item.write_text("keep me")
    (fake_trash / "info" / "kept.txt.trashinfo").write_text(
        "[Trash Info]\nPath=/tmp/original_location/kept.txt\nDeletionDate=2026-09-25T10:00:00\n")

    listed = call(action="trash", trash_action="list")
    assert "kept.txt" in listed

    restored = call(action="trash", trash_action="restore", trash_item="kept.txt")
    assert "Restored" in restored
    restored_at = Path("/tmp/original_location/kept.txt")
    assert restored_at.exists()
    restored_at.unlink()
    restored_at.parent.rmdir()

    empty = call(action="trash", trash_action="empty")
    assert "emptied" in empty


# ------------------------------------------------------------------- share

def test_share_to_folder(tmp_path):
    src = tmp_path / "gift.txt"
    src.write_text("for you")
    out_dir = tmp_path / "published"
    out = call(action="share", path=str(src), method="folder",
               destination=str(out_dir))
    assert "Shared copy" in out
    assert (out_dir / "gift.txt").read_text() == "for you"


def test_share_link_serves_then_stops(tmp_path):
    src = tmp_path / "payload.txt"
    src.write_text("downloadable content")

    out = call(action="share", path=str(src), method="link", duration=120)
    assert "http://" in out
    url = next(word.strip(".,") for word in out.split() if word.startswith("http://"))

    import urllib.request

    # fetch through loopback so the test does not depend on LAN routing
    parts = url.split("/")
    loopback = f"http://127.0.0.1:{parts[2].split(':')[1]}/{parts[3]}/{parts[4]}"
    with urllib.request.urlopen(loopback, timeout=5) as response:
        assert response.read() == b"downloadable content"

    assert "http://" in call(action="shares")
    assert "Stopped" in call(action="unshare")
    with pytest.raises(Exception):
        urllib.request.urlopen(loopback, timeout=2)


def test_share_unknown_method_is_reported(tmp_path):
    src = tmp_path / "x.txt"
    src.write_text("x")
    assert call(action="share", path=str(src), method="carrier-pigeon") \
        .startswith("Unknown share method")


# --------------------------------------------------------------- archives

def test_archive_and_extract(tmp_path):
    source = tmp_path / "payload"
    source.mkdir()
    (source / "inner.txt").write_text("archived")

    out = call(action="archive", path=str(source), destination=str(tmp_path))
    assert "Archive created" in out
    archive = tmp_path / "payload.zip"
    assert zipfile.is_zipfile(archive)

    dest = tmp_path / "unpacked"
    out = call(action="extract", path=str(archive), destination=str(dest))
    assert "Extracted" in out
    assert (dest / "payload" / "inner.txt").read_text() == "archived"


# ------------------------------------------------------- system information

def test_users_lists_homes():
    out = call(action="users")
    assert "Users on this machine" in out
    assert "uid" in out


def test_partitions_lists_mounts():
    out = call(action="partitions")
    assert "Mounted drives" in out
    assert "→ /" in out or "→ /home" in out


def test_disk_usage_for_root():
    out = call(action="disk_usage", path="root")
    assert "Disk usage for" in out and "Free" in out


def test_capabilities_lists_everything():
    out = call(action="capabilities")
    for word in ("Navigate", "Share", "permissions", "users", "archives"):
        assert word in out


# ------------------------------------------------- legacy behaviour intact

def test_legacy_desktop_shortcut_still_lists():
    out = call(action="list", path="desktop")
    assert out.startswith(("Contents of", "Directory is empty", "Path not found"))


def test_legacy_write_to_desktop_path(tmp_path, monkeypatch):
    """The planner's 'write to desktop' flow keeps producing the same message."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    (tmp_path / "Desktop").mkdir()
    out = call(action="write", path="desktop", name="plan.txt", content="notes")
    assert out == "Written to: plan.txt"
    assert (tmp_path / "Desktop" / "plan.txt").read_text() == "notes"


def test_organize_folder_by_type(tmp_path):
    (tmp_path / "photo.jpg").write_text("x")
    (tmp_path / "doc.pdf").write_text("x")
    out = call(action="organize_folder", path=str(tmp_path), mode="by_type")
    assert "organized" in out
    assert (tmp_path / "Images" / "photo.jpg").exists()
    assert (tmp_path / "Documents" / "doc.pdf").exists()


def test_action_aliases_are_accepted(tmp_path):
    (tmp_path / "alias.txt").write_text("hi")
    assert "alias.txt" in call(action="ls", path=str(tmp_path))
    assert call(action="cat", path=str(tmp_path), name="alias.txt") == "hi"
    assert call(action="cwd") == f"Current directory: {tmp_path}"
