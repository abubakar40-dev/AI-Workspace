# actions/file_controller.py
# Full file-manager access for Jarvis — navigate, create, read, write,
# delete, move, copy, rename, share, find, chmod/chown, plus system info
# (users, drives) and archives.
#
# Scope: EVERY path on the machine is addressable — any drive, any user's
# home (/home/*, C:\Users\*), /root, system folders, hidden files.  The only
# limits are the OS's own permissions, and when those block an operation
# Jarvis escalates through `sudo -n` / `pkexec` (the system asks the user
# for a password — Jarvis never stores or guesses one).

import base64
import fnmatch
import mimetypes
import os
import re
import shlex
import shutil
import socket
import stat as stat_module
import subprocess
import tarfile
import tempfile
import threading
import time
import zipfile
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlparse
from uuid import uuid4

try:
    import send2trash
except Exception:  # optional — delete falls back to permanent removal
    send2trash = None

# Verification layer: after any mutation, re-read the filesystem and check the
# action's claim actually happened (verify.py at the repo root, same import
# style as x11_access used by the other action modules).
try:
    from verify import verify_action
except ImportError:  # repo root not on sys.path (odd invocation style)
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from verify import verify_action

_FILE_TYPE_MAP = {
    "Images":    [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico"],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx", ".ppt", ".pptx", ".csv"],
    "Videos":    [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"],
    "Music":     [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma"],
    "Archives":  [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Code":      [".py", ".js", ".html", ".css", ".json", ".xml", ".ts", ".cpp", ".java"],
}

# Virtual filesystems are never useful to list/search and are skipped.
_SYSTEM_SKIP = ("/proc", "/sys", "/dev", "/run")

# Navigation state: where relative paths and `cd` currently point, plus the
# temporary LAN share servers started by the `share` action.
_STATE_LOCK = threading.Lock()
_STATE = {"cwd": Path.cwd(), "shares": {}}

_ELEVATION_TIMEOUT = 60


def _get_desktop() -> Path:
    """Returns desktop path — works on Windows, Mac, Linux."""
    return Path.home() / "Desktop"


def _get_downloads() -> Path:
    return Path.home() / "Downloads"


def _trash_dir() -> Path:
    """Recycle-bin location (freedesktop XDG trash on Linux)."""
    if os.name == "nt":
        return Path.home() / "AppData" / "Local" / "Microsoft" / "Windows" / "Recycle Bin"
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return base / "Trash"


def _shortcut_paths() -> dict:
    """Named locations Jarvis can jump to by word instead of a full path."""
    home = Path.home()
    if os.name == "nt":
        users_root = Path("C:/Users")
        root = Path("C:/")
    else:
        users_root = Path("/home")
        root = Path("/")
    return {
        "desktop":   home / "Desktop",
        "downloads": home / "Downloads",
        "documents": home / "Documents",
        "pictures":  home / "Pictures",
        "music":     home / "Music",
        "videos":    home / "Videos",
        "home":      home,
        "root":      root,
        "system":    root,
        "users":     users_root,
        "all_users": users_root,
        "tmp":       Path(tempfile.gettempdir()),
        "cwd":       Path(_STATE["cwd"]),
        "trash":     _trash_dir(),
        "shared":    home / "Shared",
    }


def _resolve_path(raw: str, base: Path | None = None) -> Path:
    """
    Resolves any path from user/model input.

    Supports: shortcuts ('desktop', 'downloads', 'documents', 'pictures',
    'music', 'videos', 'home', 'root'/'system' for the filesystem root,
    'users' for all user homes, 'tmp', 'trash', 'shared', 'cwd') including
    sub-paths ('desktop/projects/x.py'), '~' and '~otheruser', $VARS,
    absolute paths anywhere on the system, and relative paths (resolved
    against the current navigation directory).
    """
    raw = "" if raw is None else str(raw).strip()
    if not raw:
        return Path(_STATE["cwd"])

    raw = os.path.expandvars(os.path.expanduser(raw))
    working = Path(base) if base is not None else Path(_STATE["cwd"])

    normalized = raw.replace("\\", "/") if os.name == "nt" else raw
    head, _, rest = normalized.partition("/")
    shortcut = _shortcut_paths().get(head.lower())
    if shortcut is not None:
        target = shortcut / rest if rest else shortcut
        return Path(os.path.normpath(str(target)))

    path = Path(raw)
    if not path.is_absolute():
        path = working / path
    return Path(os.path.normpath(str(path)))


def _format_size(bytes_size: int) -> str:
    """Converts bytes to human readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f} TB"


def _permission_denied(target) -> str:
    """Actionable message when the OS blocks a path (Jarvis can escalate)."""
    return (
        f"Permission denied: {target}. "
        f"Re-run with elevated=true and the system will ask you to authorize it."
    )


def _wants_elevation(parameters: dict, default_mutation: bool) -> bool:
    """
    Whether to escalate a permission-blocked operation.

    Explicit `elevated` parameter wins; otherwise mutations (write/delete/
    move/chmod) escalate automatically, reads stay silent unless asked.
    """
    if "elevated" not in (parameters or {}):
        return default_mutation
    value = (parameters or {}).get("elevated")
    if isinstance(value, str):
        return value.strip().lower() not in ("false", "0", "no", "off", "never")
    return bool(value)


def _elevate(argv, stdin_text: str | None = None, interactive: bool = True,
             timeout: int = _ELEVATION_TIMEOUT):
    """
    Runs `argv` with root privileges. Tries passwordless `sudo -n` first
    (silent, instant), then `pkexec` (GUI password prompt) when interactive.

    Returns (ok: bool, output: str).
    """
    if os.name == "nt":
        return False, "Elevation is not supported on this platform."

    attempts = []
    if shutil.which("sudo"):
        attempts.append(["sudo", "-n", "--"] + list(argv))
    if interactive and shutil.which("pkexec"):
        attempts.append(["pkexec"] + list(argv))

    last = ""
    for cmd in attempts:
        try:
            proc = subprocess.run(cmd, input=stdin_text, capture_output=True,
                                  text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            last = "authorization timed out"
            continue
        except Exception as exc:
            last = str(exc)
            continue
        if proc.returncode == 0:
            return True, proc.stdout
        last = (proc.stderr or proc.stdout or "").strip() or f"exit code {proc.returncode}"
    return False, last or "no elevation method available"


def _elevate_shell(script: str, stdin_text: str | None = None,
                   interactive: bool = True, timeout: int = _ELEVATION_TIMEOUT):
    """Runs a shell script as root (paths must already be shlex-quoted)."""
    return _elevate(["/bin/sh", "-c", script], stdin_text=stdin_text,
                    interactive=interactive, timeout=timeout)


def _q(path) -> str:
    return shlex.quote(str(path))


def list_files(path: str = "desktop", show_hidden: bool = False,
               limit: int = 500, offset: int = 0) -> str:
    """Lists files and folders in a directory (any directory on the system)."""
    try:
        target = _resolve_path(path)
        if not target.exists():
            return f"Path not found: {target}"
        if not target.is_dir():
            return f"Not a directory: {target}"

        items = []
        hidden_skipped = 0
        try:
            entries = sorted(target.iterdir(), key=lambda i: (not i.is_dir(), i.name.lower()))
        except PermissionError:
            return _permission_denied(target)

        for item in entries:
            if not show_hidden and item.name.startswith("."):
                hidden_skipped += 1
                continue
            try:
                if item.is_dir():
                    items.append(f"📁 {item.name}/")
                else:
                    size = _format_size(item.stat().st_size)
                    items.append(f"📄 {item.name} ({size})")
            except OSError:
                items.append(f"🔒 {item.name} (inaccessible)")

        total = len(items)
        page = items[offset:offset + limit] if limit else items[offset:]

        if not page:
            note = f" ({hidden_skipped} hidden entries)" if (hidden_skipped and not show_hidden) else ""
            return f"Directory is empty: {target}{note}"

        header = f"Contents of {target.name}/ ({len(page)} items):"
        if offset:
            header = f"Contents of {target.name}/ (items {offset + 1}-{offset + len(page)} of {total}):"
        elif total > len(page):
            header = f"Contents of {target.name}/ ({len(page)} of {total} items):"

        body = "\n".join(page)
        if total > offset + len(page):
            body += f"\n... {total - offset - len(page)} more (raise 'offset' to see them)"
        if hidden_skipped and not show_hidden:
            body += f"\n({hidden_skipped} hidden entries — pass show_hidden=true to include)"

        return header + "\n" + body

    except PermissionError:
        return _permission_denied(path)
    except Exception as e:
        return f"Error listing files: {e}"


def create_file(path: str, content: str = "", parameters: dict | None = None) -> str:
    """Creates a new file with optional content (any location on the system)."""
    try:
        target = _resolve_path(path)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return f"File created: {target.name}"
        except PermissionError:
            if not _wants_elevation(parameters, default_mutation=True):
                return _permission_denied(target)
            script = (
                f"mkdir -p {_q(target.parent)} && "
                f"printf %s {_q(content)} > {_q(target)}"
            )
            ok, out = _elevate_shell(script, interactive=True, timeout=45)
            if ok:
                return f"File created (elevated): {target.name}"
            return f"Could not create file: permission denied ({out.strip()[:200]})"
    except Exception as e:
        return f"Could not create file: {e}"


def create_folder(path: str, parameters: dict | None = None) -> str:
    """Creates a new folder (and parent folders if needed) anywhere on the system."""
    try:
        target = _resolve_path(path)
        try:
            target.mkdir(parents=True, exist_ok=True)
            return f"Folder created: {target}"
        except PermissionError:
            if not _wants_elevation(parameters, default_mutation=True):
                return _permission_denied(target)
            ok, out = _elevate_shell(f"mkdir -p {_q(target)}", interactive=True, timeout=45)
            if ok:
                return f"Folder created (elevated): {target}"
            return f"Could not create folder: permission denied ({out.strip()[:200]})"
    except Exception as e:
        return f"Could not create folder: {e}"


def _elevated_trash(target: Path) -> tuple[bool, str]:
    """
    Root-level move to the recycle bin: copies the item into the *user's*
    trash (files/ + info/*.trashinfo) so it stays restorable, then removes
    the original with elevated privileges.
    """
    trash = _trash_dir()
    files_dir = trash / "files"
    info_dir = trash / "info"
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    name = target.name
    dest = files_dir / name
    if dest.exists() or (info_dir / f"{name}.trashinfo").exists():
        name = f"{target.stem}_{stamp}{target.suffix}"
        dest = files_dir / name
    info_file = info_dir / f"{name}.trashinfo"
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    script = (
        "set -e; mkdir -p {files} {info}; "
        "mv -- {src} {dest}; "
        "printf '[Trash Info]\\nPath=%s\\nDeletionDate=%s\\n' {abs} {when} > {info_file}"
    ).format(
        files=_q(files_dir), info=_q(info_dir),
        src=_q(target), dest=_q(dest),
        abs=_q(str(target.resolve())), when=_q(now),
        info_file=_q(info_file),
    )
    return _elevate_shell(script, interactive=True, timeout=_ELEVATION_TIMEOUT)


def delete_file(path: str, confirm: bool = True, permanent: bool = False,
                parameters: dict | None = None) -> str:
    """
    Deletes a file or folder — anything on the system.

    Default: moves to the Recycle Bin (restorable). `permanent=True` removes
    it for good. Permission-blocked targets escalate automatically.
    """
    try:
        target = _resolve_path(path)
        if not target.exists() and not target.is_symlink():
            return f"Not found: {path}"

        interactive = _wants_elevation(parameters, default_mutation=True)

        # 1. Recycle bin (default) — works for the current user.
        if not permanent and send2trash is not None:
            try:
                send2trash.send2trash(str(target))
                return f"Moved to Recycle Bin: {target.name}"
            except Exception as trash_err:
                # 2. Blocked → move it into the user's bin as root (restorable).
                ok, out = _elevated_trash(target)
                if ok:
                    return f"Moved to Recycle Bin (elevated): {target.name}"
                return (
                    f"Could not move to Recycle Bin: {trash_err}. "
                    f"Retry with permanent=true to delete it permanently."
                )

        # 3. Permanent delete.
        try:
            is_folder = target.is_dir() and not target.is_symlink()
            if is_folder:
                shutil.rmtree(target)
            else:
                target.unlink()
            return f"{'Folder' if is_folder else 'File'} deleted permanently: {target.name}"
        except PermissionError:
            if not _wants_elevation(parameters, default_mutation=True):
                return _permission_denied(target)
            ok, out = _elevate_shell(f"rm -rf -- {_q(target)}", interactive=interactive)
            if ok:
                return f"Deleted permanently (elevated): {target.name}"
            return f"Could not delete: permission denied ({out.strip()[:200]})"

    except PermissionError:
        return _permission_denied(path)
    except Exception as e:
        return f"Could not delete: {e}"


def move_file(source: str, destination: str, parameters: dict | None = None) -> str:
    """Moves a file or folder to a new location (cut & paste)."""
    try:
        src = _resolve_path(source)
        dst = _resolve_path(destination)

        if not src.exists() and not src.is_symlink():
            return f"Source not found: {source}"

        if dst.is_dir() and dst != src:
            dst = dst / src.name

        interactive = _wants_elevation(parameters, default_mutation=True)
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            return f"Moved: {src.name} → {dst.parent.name}/"
        except PermissionError:
            if not interactive and not os.access(dst.parent, os.W_OK):
                return _permission_denied(dst.parent)
            ok, out = _elevate_shell(
                f"mkdir -p {_q(dst.parent)} && mv -- {_q(src)} {_q(dst)}",
                interactive=interactive)
            if ok:
                return f"Moved (elevated): {src.name} → {dst.parent.name}/"
            return f"Could not move: permission denied ({out.strip()[:200]})"

    except Exception as e:
        return f"Could not move: {e}"


def copy_file(source: str, destination: str, parameters: dict | None = None) -> str:
    """Copies a file or folder (leaves the original in place)."""
    try:
        src = _resolve_path(source)
        dst = _resolve_path(destination)

        if not src.exists() and not src.is_symlink():
            return f"Source not found: {source}"

        if dst.is_dir() and dst != src:
            dst = dst / src.name

        interactive = _wants_elevation(parameters, default_mutation=True)
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                shutil.copytree(str(src), str(dst), dirs_exist_ok=True)
            else:
                shutil.copy2(str(src), str(dst))
            return f"Copied: {src.name} → {dst.parent.name}/"
        except PermissionError:
            ok, out = _elevate_shell(
                f"mkdir -p {_q(dst.parent)} && cp -a -- {_q(src)} {_q(dst)}",
                interactive=interactive)
            if ok:
                return f"Copied (elevated): {src.name} → {dst.parent.name}/"
            return f"Could not copy: permission denied ({out.strip()[:200]})"

    except Exception as e:
        return f"Could not copy: {e}"


def rename_file(path: str, new_name: str) -> str:
    """Renames a file or folder (can also move it if new_name has a path)."""
    try:
        target = _resolve_path(path)
        new_path = (target.parent / new_name) if not str(new_name).startswith("/") \
            else _resolve_path(new_name)

        if not target.exists() and not target.is_symlink():
            return f"Not found: {path}"
        if new_path.exists():
            return f"A file named '{new_name}' already exists."

        new_path.parent.mkdir(parents=True, exist_ok=True)
        target.rename(new_path)
        return f"Renamed: {target.name} → {new_path.name}"

    except PermissionError:
        return _permission_denied(path)
    except Exception as e:
        return f"Could not rename: {e}"


def _hexdump(data: bytes, limit: int = 256) -> str:
    lines = []
    for offset in range(0, min(len(data), limit), 16):
        chunk = data[offset:offset + 16]
        hex_part = " ".join(f"{byte:02x}" for byte in chunk)
        ascii_part = "".join(chr(byte) if 32 <= byte < 127 else "." for byte in chunk)
        lines.append(f"{offset:08x}  {hex_part:<47}  {ascii_part}")
    return "\n".join(lines)


def _truncate(text: str, max_chars: int) -> str:
    if len(text) > max_chars:
        return text[:max_chars] + f"\n\n... (truncated, {len(text)} total chars)"
    return text


def _sniff_binary(sample: bytes) -> bool:
    if not sample:
        return False
    if b"\x00" in sample:
        return True
    try:
        sample.decode("utf-8")
        return False
    except UnicodeDecodeError:
        # High-byte-only content that is not valid UTF-8 counts as binary.
        return True


def _read_pdf(target: Path, max_chars: int) -> str | None:
    """PDF → extracted text (pdftotext, then PyPDF2/pypdf)."""
    tool = shutil.which("pdftotext")
    if tool:
        try:
            proc = subprocess.run([tool, "-layout", "-q", str(target), "-"],
                                  capture_output=True, text=True, timeout=60)
            if proc.returncode == 0 and proc.stdout.strip():
                return _truncate(proc.stdout, max_chars)
        except Exception:
            pass
    for module_name in ("pypdf", "PyPDF2"):
        try:
            module = __import__(module_name)
            reader = module.PdfReader(str(target))
            pages = "\n\n".join((page.extract_text() or "") for page in reader.pages)
            if pages.strip():
                return _truncate(pages, max_chars)
        except Exception:
            continue
    return f"PDF opened but no text could be extracted ({target.name})."


def _read_docx(target: Path, max_chars: int) -> str | None:
    from docx import Document
    document = Document(str(target))
    parts = [p.text for p in document.paragraphs if p.text.strip()]
    for table in document.tables:
        for row in table.rows:
            parts.append(" | ".join(cell.text.strip() for cell in row.cells))
    return _truncate("\n".join(parts), max_chars)


def _read_pptx(target: Path, max_chars: int) -> str | None:
    from pptx import Presentation
    presentation = Presentation(str(target))
    parts = []
    for index, slide in enumerate(presentation.slides, start=1):
        parts.append(f"--- Slide {index} ---")
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                parts.append(shape.text)
    return _truncate("\n".join(parts), max_chars)


def _read_xlsx(target: Path, max_chars: int) -> str | None:
    import openpyxl
    workbook = openpyxl.load_workbook(str(target), read_only=True, data_only=True)
    parts = []
    for sheet in workbook.worksheets:
        parts.append(f"--- Sheet: {sheet.title} ---")
        for row_number, row in enumerate(sheet.iter_rows(values_only=True), start=1):
            if row_number > 200:
                parts.append("... (more rows)")
                break
            values = ["" if value is None else str(value) for value in row]
            if any(values):
                parts.append("\t".join(values))
    return _truncate("\n".join(parts), max_chars)


def _read_image(target: Path, max_chars: int) -> str | None:
    from PIL import Image, ExifTags
    with Image.open(target) as image:
        details = [
            f"Image: {image.format} {image.width}×{image.height}, mode={image.mode}",
            f"File size: {_format_size(target.stat().st_size)}",
        ]
        try:
            exif = image.getexif()
            if exif:
                tagged = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
                for key in ("Make", "Model", "DateTime", "Orientation", "Software"):
                    if key in tagged:
                        details.append(f"{key}: {tagged[key]}")
        except Exception:
            pass
        details.append("Use action=describe for an AI description of the image.")
        return "\n".join(details)


def _read_media(target: Path, max_chars: int) -> str | None:
    """Audio/Video → duration + stream metadata (ffprobe, then PyAV)."""
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        try:
            proc = subprocess.run(
                [ffprobe, "-v", "quiet", "-print_format", "json",
                 "-show_format", "-show_streams", str(target)],
                capture_output=True, text=True, timeout=60)
            if proc.returncode == 0 and proc.stdout.strip():
                import json
                data = json.loads(proc.stdout)
                lines = []
                fmt = data.get("format", {})
                if fmt.get("format_name"):
                    lines.append(f"Container: {fmt['format_name']}")
                if fmt.get("duration"):
                    lines.append(f"Duration: {float(fmt['duration']):.1f}s")
                if fmt.get("bit_rate"):
                    lines.append(f"Bitrate: {int(fmt['bit_rate']) // 1000} kbps")
                for stream in data.get("streams", []):
                    kind = stream.get("codec_type", "?")
                    label = stream.get("codec_name", "?")
                    if kind == "video":
                        lines.append(f"Video: {label} {stream.get('width')}×{stream.get('height')}"
                                     f" @ {stream.get('avg_frame_rate')} fps")
                    elif kind == "audio":
                        lines.append(f"Audio: {label} {stream.get('sample_rate')}Hz "
                                     f"ch={stream.get('channels')}")
                lines.append(f"File size: {_format_size(target.stat().st_size)}")
                return "\n".join(lines)
        except Exception:
            pass
    try:
        import av
        with av.open(str(target)) as container:
            duration = float(container.duration or 0) / av.time_base if container.duration else 0
            lines = [f"Duration: {duration:.1f}s",
                     f"File size: {_format_size(target.stat().st_size)}"]
            for stream in container.streams:
                lines.append(f"{stream.type} stream: {stream.codec_context.name}")
            return "\n".join(lines)
    except Exception:
        return None


def _read_archive(target: Path, max_chars: int) -> str | None:
    entries = []
    if zipfile.is_zipfile(target):
        with zipfile.ZipFile(target) as archive:
            total = 0
            for info in archive.infolist()[:500]:
                total += info.file_size
                entries.append(f"  📦 {info.filename} ({_format_size(info.file_size)})")
            entries.append(f"{len(archive.infolist())} entries, {_format_size(total)} uncompressed")
    elif tarfile.is_tarfile(target):
        with tarfile.open(target) as archive:
            members = archive.getmembers()[:500]
            total = sum(member.size for member in members)
            for member in members:
                entries.append(f"  📦 {member.name} ({_format_size(member.size)})")
            entries.append(f"{len(archive.getmembers())} entries, {_format_size(total)} uncompressed")
    else:
        for tool in ("7z", "7zz"):
            binary = shutil.which(tool)
            if binary:
                proc = subprocess.run([binary, "l", str(target)], capture_output=True,
                                      text=True, timeout=60)
                if proc.returncode == 0:
                    return _truncate(proc.stdout, max_chars)
                break
        return None
    header = f"Archive: {target.name} ({target.suffix.lstrip('.').upper()})\n"
    return _truncate(header + "\n".join(entries), max_chars)


_PDF_EXTS = {".pdf"}
_DOCX_EXTS = {".docx"}
_PPTX_EXTS = {".pptx"}
_XLSX_EXTS = {".xlsx", ".xlsm", ".ods"}
_XLS_NOTE_EXTS = {".xls"}
_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico",
               ".tiff", ".tif", ".heic", ".raw"}
_MEDIA_EXTS = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a", ".opus",
               ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".3gp"}
_ARCHIVE_EXTS = {".zip", ".rar", ".7z", ".tar", ".gz", ".tgz", ".bz2", ".xz"}


def _read_structured(target: Path, max_chars: int) -> str | None:
    """Extracts readable content from a non-text format, else None."""
    ext = target.suffix.lower()
    handlers = (
        (_PDF_EXTS, _read_pdf),
        (_DOCX_EXTS, _read_docx),
        (_PPTX_EXTS, _read_pptx),
        (_XLSX_EXTS, _read_xlsx),
        (_IMAGE_EXTS, _read_image),
        (_MEDIA_EXTS, _read_media),
        (_ARCHIVE_EXTS, _read_archive),
    )
    for extensions, handler in handlers:
        if ext in extensions:
            try:
                return handler(target, max_chars)
            except Exception as exc:
                return f"Could not read {ext} file ({target.name}): {exc}"
    if ext in _XLS_NOTE_EXTS:
        return (f"Legacy .xls binary workbook — use file_processor with action "
                f"extract_text, or ask me to convert it to .xlsx.")
    return None


def read_file(path: str, max_chars: int = 3000, parameters: dict | None = None) -> str:
    """
    Reads ANY file type: text, code, JSON, CSV, PDF, DOCX, PPTX, XLSX,
    images, audio/video, archives, and raw binaries (shown as a hex dump).
    Works on any path on the system, escalating if the OS blocks it.
    """
    try:
        target = _resolve_path(path)
        if not target.exists() and not target.is_symlink():
            return f"File not found: {path}"
        if not target.is_file():
            return f"Not a file: {path}"

        structured = _read_structured(target, max_chars)
        if structured is not None:
            return structured

        try:
            data = target.read_bytes()
        except PermissionError:
            ok, out = _elevate_shell(f"cat {_q(target)}", interactive=False, timeout=45)
            if ok:
                text = out if isinstance(out, str) else out.decode("utf-8", "ignore")
                return _truncate(text, max_chars)
            if not _wants_elevation(parameters, default_mutation=False):
                ok, out = _elevate_shell(f"cat {_q(target)}", interactive=True, timeout=45)
                if ok:
                    return _truncate(out, max_chars)
            return _permission_denied(target)

        if not data:
            return f"File is empty: {target.name}"

        if _sniff_binary(data[:8192]):
            head = data[:16]
            kind = "executable" if head.startswith(b"\x7fELF") or head[:2] == b"MZ" else "binary"
            mime = mimetypes.guess_type(str(target))[0] or "unknown"
            return (
                f"{kind.capitalize()} file: {target.name}\n"
                f"Type: {mime} | Size: {_format_size(len(data))}\n"
                f"First {_format_size(min(len(data), 256))} (hex):\n"
                f"{_hexdump(data)}"
            )

        content = data.decode("utf-8", errors="ignore")
        return _truncate(content, max_chars)

    except PermissionError:
        return _permission_denied(path)
    except Exception as e:
        return f"Could not read file: {e}"


def write_file(path: str, content: str = "", append: bool = False,
               base64_encoded: bool = False, parameters: dict | None = None) -> str:
    """
    Writes or appends content to a file — text by default, or binary when
    `base64_encoded=true` (content is base64). Creates parent folders.
    """
    try:
        target = _resolve_path(path)
        mode = ("ab" if append else "wb") if base64_encoded else ("a" if append else "w")
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            if base64_encoded:
                payload = base64.b64decode(content, validate=False)
                with open(target, mode) as f:
                    f.write(payload)
            else:
                with open(target, mode, encoding="utf-8") as f:
                    f.write(content)
            action = "Appended to" if append else "Written to"
            suffix = " (binary)" if base64_encoded else ""
            return f"{action}: {target.name}{suffix}"
        except PermissionError:
            if not _wants_elevation(parameters, default_mutation=True):
                return _permission_denied(target)
            if base64_encoded:
                raw = base64.b64encode(content.encode("utf-8")).decode("ascii")
                script = (f"mkdir -p {_q(target.parent)} && printf %s {_q(raw)} | "
                          f"base64 -d > {'>>' if append else '>'} {_q(target)}")
            else:
                script = (f"mkdir -p {_q(target.parent)} && printf %s {_q(content)} "
                          f"{'>>' if append else '>'} {_q(target)}")
            ok, out = _elevate_shell(script, interactive=True, timeout=45)
            if ok:
                action = "Appended to" if append else "Written to"
                return f"{action} (elevated): {target.name}"
            return f"Could not write file: permission denied ({out.strip()[:200]})"
    except Exception as e:
        return f"Could not write file: {e}"


def _walk(root: Path, hidden: bool = False):
    """
    Depth-first walk over any directory tree — never dies on permission
    errors, symlinks or virtual filesystems (/proc, /sys, /dev, /run).
    Yields (dirpath, dirnames, filenames).
    """
    root_str = str(root)

    def _on_error(_error):
        return None

    for dirpath, dirnames, filenames in os.walk(root_str, onerror=_on_error,
                                                followlinks=False):
        if dirpath.startswith(os.sep):
            pruned = []
            for entry in dirnames:
                full = os.path.join(dirpath, entry)
                if any(full == skip or full.startswith(skip + os.sep)
                       for skip in _SYSTEM_SKIP):
                    continue
                if not hidden and entry.startswith("."):
                    continue
                pruned.append(entry)
            dirnames[:] = pruned
        elif not hidden:
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        yield dirpath, dirnames, filenames


def find_files(name: str = "", extension: str = "", path: str = "home",
               max_results: int = 20, hidden: bool = False,
               recursive: bool = True, kind: str = "any",
               pattern: str = "", max_depth: int | None = None,
               min_size: int | None = None, max_size: int | None = None) -> str:
    """
    Searches for files by name, extension or glob pattern anywhere on the
    system — including other users' homes and system folders.

    Examples: find_files(extension=".pdf", path="documents")
              find_files(pattern="*.mp4", path="users", max_results=50)
    """
    try:
        search_path = _resolve_path(path)
        if not search_path.exists():
            return f"Search path not found: {path}"

        if extension and not extension.startswith("."):
            extension = "." + extension
        extension = extension.lower()
        kind = (kind or "any").lower()

        results = []
        base_depth = len(search_path.parts)

        def _matches(item_name: str, item: Path) -> bool:
            lowered = item_name.lower()
            if extension and not lowered.endswith(extension):
                return False
            if name and name.lower() not in lowered:
                return False
            if pattern and not fnmatch.fnmatch(item_name, pattern):
                return False
            if kind == "file" and not item.is_file():
                return False
            if kind == "dir" and not item.is_dir():
                return False
            if kind == "any" and not item.is_file():
                return False
            if min_size is not None or max_size is not None:
                try:
                    size = item.stat().st_size
                except OSError:
                    return False
                if min_size is not None and size < min_size:
                    return False
                if max_size is not None and size > max_size:
                    return False
            return True

        if search_path.is_dir():
            for dirpath, dirnames, filenames in _walk(search_path, hidden=hidden):
                depth = len(Path(dirpath).parts) - base_depth
                if not recursive:
                    dirnames[:] = []
                elif max_depth is not None and depth >= max_depth:
                    dirnames[:] = []
                entries = list(dirnames) if kind == "dir" else list(filenames)
                for entry in entries:
                    item = Path(dirpath) / entry
                    if _matches(entry, item):
                        try:
                            size = _format_size(item.stat().st_size) if item.is_file() else "-"
                        except OSError:
                            size = "?"
                        marker = "📁" if item.is_dir() else "📄"
                        results.append(f"{marker} {item.name} ({size}) — {item.parent}")
                        if len(results) >= max_results:
                            break
                if len(results) >= max_results:
                    break
        elif _matches(search_path.name, search_path):
            results.append(f"📄 {search_path.name} ({_format_size(search_path.stat().st_size)}) — {search_path.parent}")

        if not results:
            query = name or extension or pattern or "files"
            return f"No {query} found in {search_path.name}/"

        header = f"Found {len(results)} file(s):" if kind != "dir" else f"Found {len(results)} folder(s):"
        return header + "\n" + "\n".join(results)

    except PermissionError:
        return _permission_denied(path)
    except Exception as e:
        return f"Search error: {e}"


def get_largest_files(path: str = "home", count: int = 10,
                      hidden: bool = False, recursive: bool = True) -> str:
    """Returns the largest files in a directory (or an entire drive)."""
    try:
        search_path = _resolve_path(path)
        if not search_path.exists():
            return f"Path not found: {path}"

        files = []
        if search_path.is_file():
            files.append((search_path.stat().st_size, search_path))
        else:
            for dirpath, dirnames, filenames in _walk(search_path, hidden=hidden):
                if not recursive:
                    dirnames[:] = []
                for filename in filenames:
                    item = Path(dirpath) / filename
                    try:
                        files.append((item.stat().st_size, item))
                    except OSError:
                        continue

        files.sort(key=lambda pair: pair[0], reverse=True)
        top = files[:count]

        if not top:
            return "No files found."

        lines = [f"Top {len(top)} largest files in {search_path.name}/:\n"]
        for size, f in top:
            lines.append(f"  {_format_size(size):>10}  {f.name}  ({f.parent})")

        return "\n".join(lines)

    except PermissionError:
        return _permission_denied(path)
    except Exception as e:
        return f"Error: {e}"


def get_disk_usage(path: str = "home") -> str:
    """Returns disk usage information for the drive holding `path`."""
    try:
        target = _resolve_path(path)
        while not target.exists() and target != target.parent:
            target = target.parent
        usage  = shutil.disk_usage(target)
        total  = _format_size(usage.total)
        used   = _format_size(usage.used)
        free   = _format_size(usage.free)
        pct    = usage.used / usage.total * 100 if usage.total else 0

        return (
            f"Disk usage for {target}:\n"
            f"  Total : {total}\n"
            f"  Used  : {used} ({pct:.1f}%)\n"
            f"  Free  : {free}"
        )
    except Exception as e:
        return f"Could not get disk usage: {e}"


def organize_desktop() -> str:
    """
    Organizes the desktop by grouping files into folders by type.
    Creates folders: Images, Documents, Videos, Music, Archives, Others
    """
    try:
        desktop = _get_desktop()
        type_map = {
            "Images":    [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico"],
            "Documents": [".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx", ".ppt", ".pptx", ".csv"],
            "Videos":    [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"],
            "Music":     [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma"],
            "Archives":  [".zip", ".rar", ".7z", ".tar", ".gz"],
            "Code":      [".py", ".js", ".html", ".css", ".json", ".xml", ".ts", ".cpp", ".java"],
        }

        moved    = []
        skipped  = []

        for item in desktop.iterdir():

            if item.is_dir() or item.name.startswith("."):
                continue

            ext        = item.suffix.lower()
            target_dir = None

            for folder, extensions in type_map.items():
                if ext in extensions:
                    target_dir = desktop / folder
                    break

            if target_dir is None:
                target_dir = desktop / "Others"

            target_dir.mkdir(exist_ok=True)
            new_path = target_dir / item.name

            if new_path.exists():
                skipped.append(item.name)
                continue

            shutil.move(str(item), str(new_path))
            moved.append(f"{item.name} → {target_dir.name}/")

        result = f"Desktop organized. {len(moved)} files moved."
        if moved:
            result += "\n" + "\n".join(moved[:10])
            if len(moved) > 10:
                result += f"\n... and {len(moved)-10} more."
        if skipped:
            result += f"\n{len(skipped)} files skipped (already exist)."

        return result

    except Exception as e:
        return f"Could not organize desktop: {e}"


def _organize_directory(target_path: str, mode: str = "by_type") -> str:
    """Organizes files in a directory by type or by date."""
    try:
        target_dir = _resolve_path(target_path)
        if not target_dir.exists():
            return f"Path not found: {target_dir}"
        if not target_dir.is_dir():
            return f"Not a directory: {target_dir}"

        moved = []
        skipped = []

        for item in sorted(target_dir.iterdir()):
            if item.is_dir() or item.name.startswith("."):
                continue

            if mode == "by_date":
                folder_name = datetime.fromtimestamp(item.stat().st_mtime).strftime("%Y-%m")
            else:
                ext = item.suffix.lower()
                folder_name = "Others"
                for folder, extensions in _FILE_TYPE_MAP.items():
                    if ext in extensions:
                        folder_name = folder
                        break

            dest_dir = target_dir / folder_name
            dest_dir.mkdir(exist_ok=True)
            new_path = dest_dir / item.name

            if new_path.exists():
                skipped.append(item.name)
                continue

            shutil.move(str(item), str(new_path))
            moved.append(f"{item.name} -> {dest_dir.name}/")

        label = "Desktop" if target_dir == _get_desktop() else target_dir.name
        if not moved and not skipped:
            return f"{label} scanned ({mode}). No files to organize."

        result = f"{label} organized ({mode}). {len(moved)} file(s) moved."
        if moved:
            result += "\n" + "\n".join(moved[:10])
            if len(moved) > 10:
                result += f"\n... and {len(moved) - 10} more."
        if skipped:
            result += f"\n{len(skipped)} file(s) skipped because a same-named file already exists."

        return result

    except Exception as e:
        return f"Could not organize folder: {e}"


def organize_desktop() -> str:
    return _organize_directory(str(_get_desktop()), mode="by_type")


def organize_folder(path: str, mode: str = "by_type") -> str:
    return _organize_directory(path, mode=mode)


def get_file_info(path: str, compute_hash: bool = False) -> str:
    """Returns detailed information about a file or folder."""
    try:
        target = _resolve_path(path)
        if not target.exists() and not target.is_symlink():
            return f"Not found: {path}"

        try:
            stat = target.lstat() if target.is_symlink() else target.stat()
        except PermissionError:
            return _permission_denied(target)

        is_link = target.is_symlink()
        info = {
            "Name":     target.name,
            "Type":     ("Symlink" if is_link else "Folder") if (is_link or target.is_dir()) else "File",
            "Size":     _format_size(stat.st_size),
            "Location": str(target.parent),
            "Full path": str(target),
            "Created":  datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M"),
            "Modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
            "Extension": target.suffix or "None",
            "Permissions": f"{stat_module.filemode(stat.st_mode)} ({oct(stat.st_mode & 0o7777)})",
            "Owner": _owner_label(stat.st_uid),
            "MIME type": mimetypes.guess_type(str(target))[0] or "unknown",
        }
        if is_link:
            try:
                info["Link target"] = os.readlink(target)
            except OSError:
                pass
        if target.is_dir():
            try:
                info["Items"] = str(sum(1 for _ in target.iterdir()))
            except OSError:
                info["Items"] = "unknown (permission denied)"

        if compute_hash and target.is_file() and stat.st_size <= 64 * 1024 * 1024:
            import hashlib
            digest = hashlib.sha256()
            with open(target, "rb") as handle:
                for block in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(block)
            info["SHA-256"] = digest.hexdigest()

        return "\n".join(f"  {k}: {v}" for k, v in info.items())

    except PermissionError:
        return _permission_denied(path)
    except Exception as e:
        return f"Could not get file info: {e}"

def _owner_label(uid: int) -> str:
    if os.name == "nt":
        return "n/a (Windows)"
    try:
        import pwd
        return f"{pwd.getpwuid(uid).pw_name} (uid {uid})"
    except Exception:
        return f"uid {uid}"


# ---------------------------------------------------------------- navigation

def navigate_to(path: str = "home") -> str:
    """Changes the current folder (cd) and lists what is inside it."""
    target = _resolve_path(path)
    if not target.exists():
        return f"Path not found: {target}"
    if not target.is_dir():
        return f"Not a directory: {target}"
    with _STATE_LOCK:
        _STATE["cwd"] = target
    return f"Now in: {target}\n" + list_files(str(target), limit=100)


def current_dir() -> str:
    """Reports the folder relative paths are resolved against (pwd)."""
    with _STATE_LOCK:
        cwd = Path(_STATE["cwd"])
    return f"Current directory: {cwd}"


def go_up(levels: int = 1) -> str:
    """Moves to the parent folder (..), `levels` times."""
    with _STATE_LOCK:
        cwd = Path(_STATE["cwd"])
    for _ in range(max(1, int(levels or 1))):
        cwd = cwd.parent if cwd.parent != cwd else cwd
    return navigate_to(str(cwd))


def folder_tree(path: str = "home", depth: int = 3, max_entries: int = 300) -> str:
    """Shows a folder structure like a file manager's tree view."""
    target = _resolve_path(path)
    if not target.exists():
        return f"Path not found: {target}"
    if not target.is_dir():
        return f"Not a directory: {target}"

    lines = [f"{target}/"]
    state = {"count": 0, "stopped": False}
    depth = max(1, int(depth or 3))
    max_entries = max(1, int(max_entries or 300))

    def _build(directory: Path, prefix: str, level: int) -> None:
        if state["stopped"] or level > depth:
            return
        try:
            children = sorted((c for c in directory.iterdir() if not c.name.startswith(".")),
                              key=lambda i: (not i.is_dir(), i.name.lower()))
        except PermissionError:
            lines.append(prefix + "🔒 permission denied")
            return
        for index, child in enumerate(children):
            if state["count"] >= max_entries:
                state["stopped"] = True
                lines.append(prefix + "... (entry limit reached)")
                return
            last = index == len(children) - 1
            branch = "└── " if last else "├── "
            state["count"] += 1
            if child.is_dir():
                lines.append(f"{prefix}{branch}📁 {child.name}/")
                _build(child, prefix + ("    " if last else "│   "), level + 1)
            else:
                try:
                    size = _format_size(child.stat().st_size)
                except OSError:
                    size = "?"
                lines.append(f"{prefix}{branch}📄 {child.name} ({size})")

    _build(target, "", 1)
    return "\n".join(lines)


# ------------------------------------------------------- open / show in app

def open_path(path: str, app: str = "") -> str:
    """Opens a file with its default application, or a specific one."""
    target = _resolve_path(path)
    if not target.exists() and not target.is_symlink():
        return f"Not found: {path}"

    try:
        if os.name == "nt":
            if app:
                argv = [app, str(target)]
            else:
                os.startfile(str(target))  # type: ignore[attr-defined]
                return f"Opened: {target.name}"
        else:
            if app:
                binary = shutil.which(app) or (app if os.path.exists(app) else None)
                if not binary:
                    return f"Application not found: {app}"
                argv = [binary, str(target)]
            else:
                binary = shutil.which("xdg-open") or shutil.which("open")
                if not binary:
                    return "No system opener found (xdg-open missing)."
                argv = [binary, str(target)]

        subprocess.Popen(argv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         stdin=subprocess.DEVNULL, start_new_session=True)
        return f"Opened {target.name} with {app or 'the default application'}"
    except Exception as e:
        return f"Could not open: {e}"


def reveal_path(path: str) -> str:
    """Shows the file in the system file manager (highlighted)."""
    target = _resolve_path(path)
    if not target.exists() and not target.is_symlink():
        return f"Not found: {path}"
    folder = target if target.is_dir() else target.parent

    try:
        if os.name == "nt":
            subprocess.Popen(["explorer", "/select,", str(target)],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Revealed in Explorer: {target.name}"

        for name in ("nautilus", "dolphin", "thunar", "nemo"):
            binary = shutil.which(name)
            if not binary:
                continue
            argv = [binary, "--select", str(target)] if name in ("nautilus", "dolphin", "nemo") \
                else [binary, str(folder)]
            subprocess.Popen(argv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             start_new_session=True)
            return f"Revealed in {name}: {target.name}"
    except Exception:
        pass
    return open_path(str(folder))


# ------------------------------------------------------------------- sharing

def _lan_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
    except Exception:
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            ip = "127.0.0.1"
    finally:
        sock.close()
    if ip.startswith("127."):
        try:
            resolved = socket.gethostbyname(socket.gethostname())
            if not resolved.startswith("127."):
                ip = resolved
        except Exception:
            pass
    return ip


def _make_share_handler(token: str, file_path: Path, display_name: str):
    class _ShareHandler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802 (stdlib naming)
            parts = unquote(urlparse(self.path).path).split("/")
            if len(parts) < 3 or parts[1] != token:
                self.send_error(404, "Unknown share")
                return
            try:
                size = file_path.stat().st_size
                with open(file_path, "rb") as handle:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/octet-stream")
                    self.send_header("Content-Disposition",
                                     f'attachment; filename="{display_name}"')
                    self.send_header("Content-Length", str(size))
                    self.end_headers()
                    shutil.copyfileobj(handle, self.wfile)
            except OSError:
                pass

        def log_message(self, fmt, *args):  # keep the console quiet
            return

    return _ShareHandler


def _start_link_share(target: Path, duration: int = 0, player=None) -> str:
    working = target
    temp_dir = None
    if target.is_dir():
        # Folders are zipped first so a link is still a single download.
        temp_dir = Path(tempfile.mkdtemp(prefix="jarvis_share_"))
        working = temp_dir / f"{target.name}.zip"
        with zipfile.ZipFile(working, "w", zipfile.ZIP_DEFLATED) as archive:
            for dirpath, _dirnames, filenames in os.walk(target):
                for filename in filenames:
                    item = Path(dirpath) / filename
                    try:
                        archive.write(item, item.relative_to(target.parent))
                    except OSError:
                        continue

    token = uuid4().hex[:12]
    seconds = int(duration or 0) or 1800
    handler = _make_share_handler(token, working, working.name)
    try:
        server = ThreadingHTTPServer(("0.0.0.0", 0), handler)
    except Exception as exc:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)
        return f"Could not start share link: {exc}"

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    url = f"http://{_lan_ip()}:{port}/{token}/{quote(target.name + ('.zip' if target.is_dir() else ''))}"

    with _STATE_LOCK:
        _STATE["shares"][token] = {
            "server": server, "thread": thread, "path": str(target),
            "url": url, "created": time.time(), "expires": seconds,
            "temp_dir": str(temp_dir) if temp_dir else None,
        }
    if player:
        player.write_log(f"[share] {url}")
    return (f"Share link ready: {url}\n"
            f"Anyone on your local network can download '{target.name}' "
            f"for {seconds // 60} minute(s). Use action=unshare to stop it.")


def list_shares() -> str:
    now = time.time()
    with _STATE_LOCK:
        records = dict(_STATE["shares"])
    if not records:
        return "No active shares."
    lines = [f"Active shares ({len(records)}):"]
    for token, record in records.items():
        remaining = int(record["expires"] - (now - record["created"]))
        lines.append(f"  {record['url']}  ({max(remaining, 0)}s left, {record['path']})")
    return "\n".join(lines)


def stop_share(token: str = "") -> str:
    """Stops one share link (by token or full URL) or all of them."""
    with _STATE_LOCK:
        records = dict(_STATE["shares"])
        if token:
            wanted = [t for t in records if token in t or token in records[t]["url"]]
        else:
            wanted = list(records)
        stopped = []
        for key in wanted:
            record = _STATE["shares"].pop(key, None)
            if record:
                stopped.append(record)
                try:
                    record["server"].shutdown()
                    record["server"].server_close()
                except Exception:
                    pass
                if record.get("temp_dir"):
                    shutil.rmtree(record["temp_dir"], ignore_errors=True)
    if not stopped:
        return "No matching share to stop."
    return "Stopped: " + ", ".join(record["url"] for record in stopped)


def share_file(path: str, method: str = "auto", device: str = "",
               destination: str = "", duration: int = 0,
               parameters: dict | None = None, player=None) -> str:
    """
    Shares a file or folder with anything, using the method that fits:
      link    → temporary download link for your local network
      folder  → copy into a shared folder (default ~/Shared)
      email   → attach it in your mail client
    """
    target = _resolve_path(path)
    if not target.exists() and not target.is_symlink():
        return f"Not found: {path}"

    method = (method or "auto").lower().strip()
    if method == "auto":
        if destination:
            method = "folder"
        elif target.is_dir():
            method = "folder"
        else:
            method = "link"

    if method in ("folder", "local", "copy"):
        dest_dir = _resolve_path(destination) if destination else _shortcut_paths()["shared"]
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / target.name
            if dest.exists():
                dest = dest_dir / f"{target.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{target.suffix}"
            if target.is_dir():
                shutil.copytree(target, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(target, dest)
            return f"Shared copy of {target.name} → {dest}"
        except PermissionError:
            return _permission_denied(dest_dir)
        except Exception as exc:
            return f"Could not create shared copy: {exc}"

    if method in ("email", "mail"):
        if os.name == "nt":
            try:
                os.startfile(f"mailto:?attachment={target}")  # type: ignore[attr-defined]
                return f"Mail client opened with {target.name} attached."
            except Exception as exc:
                return f"Could not open mail client: {exc}"
        binary = shutil.which("xdg-email")
        if not binary:
            return "No email client integration found (xdg-email missing)."
        try:
            subprocess.Popen([binary, f"--attach={target}"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             start_new_session=True)
            return f"Mail client opened with {target.name} attached."
        except Exception as exc:
            return f"Could not open mail client: {exc}"

    if method in ("link", "url", "http", "lan", "web"):
        return _start_link_share(target, duration, player)

    return f"Unknown share method: {method} (use link | folder | email)"


# ------------------------------------------------------- permissions / users

def _parse_mode(spec: str, current: int) -> int:
    """Turns '755' or 'u+rwx,g-w,o+r' into an octal mode."""
    spec = (spec or "").strip()
    if re.fullmatch(r"[0-7]{3,4}", spec):
        return int(spec, 8)

    mode = current & 0o7777
    shifts = {"u": 6, "g": 3, "o": 0}
    for part in spec.split(","):
        match = re.fullmatch(r"([ugoa]*)([=+-])([rwxstX]*)", part.strip())
        if not match:
            raise ValueError(f"Invalid permission string: '{part}'")
        who, operator, perms = match.groups()
        who = who or "a"
        targets = list("ugo") if "a" in who else list(dict.fromkeys(who))

        rbits = (4 if "r" in perms else 0) + (2 if "w" in perms else 0) + (1 if "x" in perms else 0)
        for target_who in targets:
            bits = rbits << shifts[target_who]
            if "s" in perms:
                if target_who == "u":
                    bits |= 0o4000
                elif target_who == "g":
                    bits |= 0o2000
            if "t" in perms:
                bits |= 0o1000
            rmask = (4 + 2 + 1) << shifts[target_who]
            smask = 0
            if "s" in perms and target_who in ("u", "g"):
                smask |= 0o4000 if target_who == "u" else 0o2000
            if "t" in perms:
                smask |= 0o1000
            clear = rmask | smask
            if operator == "=":
                mode = (mode & ~clear) | bits
            elif operator == "+":
                mode |= bits
            else:
                mode &= ~bits
    return mode & 0o7777


def chmod_path(path: str, permission: str, recursive: bool = False,
               parameters: dict | None = None) -> str:
    """Changes permissions: numeric (755, 644) or symbolic (u+rwx,g-w)."""
    target = _resolve_path(path)
    if not target.exists():
        return f"Not found: {path}"
    permission = (permission or "").strip()
    if not permission:
        return "No permission mode given (examples: 755, 644, u+rwx,g-w,o+r)."

    try:
        if recursive and target.is_dir():
            touched = 0
            for dirpath, dirnames, filenames in os.walk(target):
                for entry in list(dirnames) + list(filenames):
                    item = Path(dirpath) / entry
                    try:
                        os.chmod(item, _parse_mode(permission, item.stat().st_mode))
                        touched += 1
                    except OSError:
                        continue
            os.chmod(target, _parse_mode(permission, target.stat().st_mode))
            return f"Permissions of {touched + 1} item(s) under {target.name}/ set to {permission}"
        os.chmod(target, _parse_mode(permission, target.stat().st_mode))
        return f"Permissions of {target.name} → {permission} ({stat_module.filemode(target.stat().st_mode)})"
    except ValueError as exc:
        return str(exc)
    except PermissionError:
        if not _wants_elevation(parameters, default_mutation=True):
            return _permission_denied(target)
        flags = "-R " if recursive else ""
        ok, out = _elevate_shell(f"chmod {flags}{_q(permission)} {_q(target)}",
                                 interactive=True, timeout=45)
        if ok:
            return f"Permissions of {target.name} → {permission} (elevated)"
        return f"Could not change permissions: {out.strip()[:200]}"
    except Exception as e:
        return f"Could not change permissions: {e}"


def chown_path(path: str, owner: str, recursive: bool = False,
               parameters: dict | None = None) -> str:
    """Changes ownership: 'user', 'user:group' or ':group' (needs root)."""
    target = _resolve_path(path)
    if not target.exists():
        return f"Not found: {path}"
    owner = (owner or "").strip()
    if not owner:
        return "No owner given (examples: 'abubakar', 'abubakar:staff', ':staff')."

    flags = "-R " if recursive else ""
    interactive = _wants_elevation(parameters, default_mutation=True)
    ok, out = _elevate_shell(f"chown {flags}{_q(owner)} {_q(target)}", interactive=interactive)
    if ok:
        return f"Owner of {target.name} → {owner} (elevated)"
    if not interactive:
        return _permission_denied(target)
    return f"Could not change owner: {out.strip()[:200]}"


def get_permissions(path: str) -> str:
    """Shows permissions, owner and access rights for a file or folder."""
    target = _resolve_path(path)
    if not target.exists() and not target.is_symlink():
        return f"Not found: {path}"
    try:
        stat = target.stat()
        group = f"gid {stat.st_gid}"
        if os.name != "nt":
            try:
                import grp
                group = f"{grp.getgrgid(stat.st_gid).gr_name} (gid {stat.st_gid})"
            except Exception:
                pass
        return (
            f"Permissions for {target}:\n"
            f"  Mode      : {oct(stat.st_mode & 0o7777)} ({stat_module.filemode(stat.st_mode)})\n"
            f"  Owner     : {_owner_label(stat.st_uid)}\n"
            f"  Group     : {group}\n"
            f"  Readable  : {os.access(target, os.R_OK)}\n"
            f"  Writable  : {os.access(target, os.W_OK)}\n"
            f"  Executable: {os.access(target, os.X_OK)}"
        )
    except PermissionError:
        return _permission_denied(target)
    except Exception as e:
        return f"Could not read permissions: {e}"


def list_users(max_entries: int = 300) -> str:
    """Lists every user account on this machine (with home folders)."""
    try:
        if os.name == "nt":
            proc = subprocess.run(["net", "user"], capture_output=True, text=True, timeout=20)
            if proc.returncode != 0:
                return f"Could not list users: {proc.stderr.strip()[:200]}"
            lines, capture = [], False
            names = []
            for line in proc.stdout.splitlines():
                if line.strip().startswith("---"):
                    capture = not capture
                    continue
                if capture:
                    names.extend(line.split())
            return f"Users on this machine ({len(names)}):\n" + \
                   "\n".join(f"  {name}" for name in names[:max_entries])

        import pwd
        entries = sorted(pwd.getpwall(), key=lambda e: (e.pw_uid < 1000, e.pw_uid))
        try:
            current = pwd.getpwuid(os.getuid()).pw_name
        except Exception:
            current = ""
        rows = []
        for entry in entries[:max_entries]:
            kind = "system" if entry.pw_uid < 1000 else "user"
            marker = " ← current" if entry.pw_name == current else ""
            rows.append(f"  {entry.pw_name} (uid {entry.pw_uid}) → {entry.pw_dir} "
                        f"[{kind}] shell={entry.pw_shell or '-'}{marker}")
        return f"Users on this machine ({len(entries)}):\n" + "\n".join(rows)
    except Exception as e:
        return f"Could not list users: {e}"


def list_partitions() -> str:
    """Lists every mounted drive/partition with size and free space."""
    try:
        import psutil
        parts = psutil.disk_partitions(all=True)
        if not parts:
            return "No partitions reported by the system."
        lines = [f"Mounted drives ({len(parts)}):"]
        for part in parts:
            try:
                usage = psutil.disk_usage(part.mountpoint)
                size = (f"{_format_size(usage.total)} total, "
                        f"{_format_size(usage.free)} free ({usage.percent}% used)")
            except Exception as exc:
                size = f"n/a ({exc.__class__.__name__})"
            lines.append(f"  {part.device} → {part.mountpoint} [{part.fstype or '?'}] {size}")
        return "\n".join(lines)
    except Exception as e:
        return f"Could not list drives: {e}"


# -------------------------------------------------------------------- trash

def trash_action(mode: str = "list", path: str = "") -> str:
    """Recycle Bin control: list (default), empty, or restore an item."""
    if os.name == "nt":
        return "Recycle Bin management is Linux-only here; use delete/permanent instead."
    trash = _trash_dir()
    files_dir = trash / "files"
    info_dir = trash / "info"
    mode = (mode or "list").lower().strip()

    if mode in ("empty", "clear", "purge"):
        if not files_dir.exists():
            return "Recycle Bin is already empty."
        count = sum(1 for _ in files_dir.iterdir())
        shutil.rmtree(files_dir, ignore_errors=True)
        shutil.rmtree(info_dir, ignore_errors=True)
        files_dir.mkdir(parents=True, exist_ok=True)
        info_dir.mkdir(parents=True, exist_ok=True)
        return f"Recycle Bin emptied — {count} item(s) permanently removed."

    if mode in ("restore", "put_back", "undelete"):
        if not path:
            return "Restore needs the name of an item in the Recycle Bin."
        name = Path(path).name
        item = files_dir / name
        if not item.exists():
            return f"Not in the Recycle Bin: {name}"
        original = None
        info_file = info_dir / f"{name}.trashinfo"
        if info_file.exists():
            for line in info_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                if line.startswith("Path="):
                    original = Path(line[5:].strip())
        if original is None:
            return f"Cannot restore {name}: original location unknown."
        try:
            original.parent.mkdir(parents=True, exist_ok=True)
            final = original
            if final.exists():
                final = original.with_name(f"{original.name} (restored)")
            shutil.move(str(item), str(final))
            info_file.unlink(missing_ok=True)
            return f"Restored {name} → {final}"
        except Exception as exc:
            return f"Could not restore {name}: {exc}"

    # list
    if not files_dir.exists():
        return "Recycle Bin is empty."
    entries = []
    for item in files_dir.iterdir():
        try:
            entries.append((item.stat().st_mtime, item))
        except OSError:
            continue
    entries.sort(key=lambda pair: pair[0], reverse=True)
    if not entries:
        return "Recycle Bin is empty."
    lines = [f"Recycle Bin ({len(entries)} items):"]
    for mtime, item in entries[:100]:
        marker = "📁" if item.is_dir() else "📄"
        lines.append(f"  {marker} {item.name} — removed "
                     f"{datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')}")
    if len(entries) > 100:
        lines.append(f"  ... {len(entries) - 100} more")
    return "\n".join(lines)


# ----------------------------------------------------------------- archives

def create_archive(source: str, target: str = "", fmt: str = "") -> str:
    """Compresses a file or folder into a .zip / .tar.gz archive."""
    src = _resolve_path(source)
    if not src.exists():
        return f"Not found: {source}"

    fmt = (fmt or "").lower().lstrip(".")
    if not fmt:
        fmt = "zip"
    use_tar = fmt in ("tar", "tgz", "tar.gz", "gz")

    if target:
        out = _resolve_path(target)
        if out.is_dir():
            out = out / f"{src.name}.{ 'tar.gz' if use_tar else 'zip' }"
    else:
        out = src.parent / f"{src.name}.{ 'tar.gz' if use_tar else 'zip' }"

    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        if use_tar:
            mode = "w:gz" if fmt in ("tgz", "tar.gz", "gz") else "w"
            with tarfile.open(out, mode) as archive:
                archive.add(src, arcname=src.name)
        else:
            if out.suffix.lower() != ".zip":
                out = out.with_suffix(".zip")
            with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
                if src.is_dir():
                    for dirpath, _dirnames, filenames in os.walk(src):
                        for filename in filenames:
                            item = Path(dirpath) / filename
                            try:
                                archive.write(item, item.relative_to(src.parent))
                            except OSError:
                                continue
                else:
                    archive.write(src, src.name)
        return f"Archive created: {out} ({_format_size(out.stat().st_size)})"
    except PermissionError:
        return _permission_denied(out.parent)
    except Exception as e:
        return f"Could not create archive: {e}"


def extract_archive(path: str, destination: str = "") -> str:
    """Extracts a .zip / .tar / .tar.gz / .7z archive anywhere on the system."""
    src = _resolve_path(path)
    if not src.exists():
        return f"Not found: {path}"
    dest = _resolve_path(destination) if destination else src.parent

    try:
        dest.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        return _permission_denied(dest)

    try:
        if zipfile.is_zipfile(src):
            with zipfile.ZipFile(src) as archive:
                archive.extractall(dest)
        elif tarfile.is_tarfile(src):
            with tarfile.open(src) as archive:
                try:
                    archive.extractall(dest, filter="data")
                except TypeError:
                    archive.extractall(dest)
        else:
            for tool in ("7z", "7zz"):
                binary = shutil.which(tool)
                if binary:
                    proc = subprocess.run([binary, "x", "-y", f"-o{dest}", str(src)],
                                          capture_output=True, text=True, timeout=300)
                    if proc.returncode == 0:
                        return f"Extracted {src.name} → {dest}"
            return f"Unsupported archive format: {src.suffix or 'unknown'} (install p7zip for .7z/.rar)"
        return f"Extracted {src.name} → {dest}"
    except PermissionError:
        return _permission_denied(dest)
    except Exception as e:
        return f"Could not extract: {e}"


# ------------------------------------------------------------------- recent

def recent_files(path: str = "home", count: int = 20, days: int = 7,
                 hidden: bool = False) -> str:
    """Lists files changed recently (default: last 7 days)."""
    root = _resolve_path(path)
    if not root.exists():
        return f"Path not found: {path}"
    count = max(1, int(count or 20))
    days = max(1, int(days or 7))
    cutoff = time.time() - days * 86400

    matches = []
    for dirpath, _dirnames, filenames in _walk(root, hidden=hidden):
        for filename in filenames:
            item = Path(dirpath) / filename
            try:
                mtime = item.stat().st_mtime
            except OSError:
                continue
            if mtime >= cutoff:
                matches.append((mtime, item))

    matches.sort(key=lambda pair: pair[0], reverse=True)
    top = matches[:count]
    if not top:
        return f"No files modified in the last {days} day(s) under {root.name}/"

    lines = [f"{len(top)} most recent file(s) (last {days} day(s)) in {root.name}/:"]
    for mtime, item in top:
        try:
            size = _format_size(item.stat().st_size)
        except OSError:
            size = "?"
        stamp = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        lines.append(f"📄 {item.name} ({size}) — {stamp} — {item.parent}")
    return "\n".join(lines)


def describe_file(path: str, instruction: str = "", player=None) -> str:
    """Describes/analyzes ANY file type (image, PDF, audio, video, code...)."""
    target = _resolve_path(path)
    if not target.exists():
        return f"Not found: {path}"
    if not target.is_file():
        return f"Not a file: {path} — use list or tree for folders."
    try:
        from actions.file_processor import file_processor
    except Exception as exc:
        return f"File analyzer unavailable: {exc}"
    try:
        return file_processor(
            parameters={"file_path": str(target),
                        "instruction": instruction or "Describe what this file contains."},
            player=player) or "Done."
    except Exception as exc:
        return f"Could not analyze {target.name}: {exc}"


def capabilities_text() -> str:
    return (
        "Jarvis file manager capabilities:\n"
        "  Navigate : cd/navigate, pwd, up, tree, list (show_hidden, limit, offset)\n"
        "  Read     : read (text, code, JSON, CSV, PDF, DOCX, PPTX, XLSX, images,\n"
        "             audio/video metadata, archives, binary hex), describe\n"
        "  Write    : write (append, base64 binary), create_file, create_folder\n"
        "  Delete   : delete (recycle bin or permanent=true), trash (list/empty/restore)\n"
        "  Organize : move, copy, rename, organize_folder, organize_desktop\n"
        "  Find     : find (name, extension, pattern, hidden, system-wide), recent, largest\n"
        "  Share    : share (link | folder | email), shares, unshare\n"
        "  Open     : open (default app or app=...), reveal (show in file manager)\n"
        "  Security : info (owner, permissions, hash), permissions, chmod, chown\n"
        "  System   : users, partitions, disk_usage\n"
        "  Archive  : archive, extract\n"
        "Paths: absolute anywhere, shortcuts (desktop, downloads, documents, pictures,\n"
        "music, videos, home, root, users, tmp, trash, shared, cwd), ~user, $VARS,\n"
        "or relative to the current folder. Permission-blocked paths escalate with\n"
        "elevated=true (the OS asks you to authorize)."
    )


_ACTION_ALIASES = {
    "ls": "list", "dir": "list", "show": "list", "show_files": "list",
    "new_file": "create_file", "touch": "create_file", "make_file": "create_file",
    "new_folder": "create_folder", "mkdir": "create_folder", "make_folder": "create_folder",
    "delete_file": "delete", "remove": "delete", "rm": "delete", "erase": "delete",
    "mv": "move", "cut": "move",
    "cp": "copy", "duplicate": "copy",
    "cat": "read", "type": "read", "view": "read", "show_content": "read",
    "edit": "write", "save": "write",
    "search": "find", "locate": "find", "glob": "find",
    "du": "disk_usage", "size": "disk_usage",
    "navigate": "cd", "chdir": "cd",
    "cwd": "pwd",
    "parent": "up", "back": "up",
    "stat": "info", "file_info": "info", "properties": "info",
    "show_in_folder": "reveal", "reveal_in_folder": "reveal", "open_folder": "reveal",
    "zip": "archive", "compress": "archive",
    "unzip": "extract", "unpack": "extract",
    "list_users": "users", "drives": "partitions", "mounts": "partitions",
    "recycle_bin": "trash", "list_trash": "trash",
    "analyze": "describe", "summarize": "describe",
    "help": "capabilities", "capability": "capabilities",
    "stop_share": "unshare", "stop_sharing": "unshare",
    "active_shares": "shares",
    "perm": "permissions", "ownership": "permissions",
}


def _as_bool(value, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in ("true", "1", "yes", "on", "y")


def _as_int(value, default: int) -> int:
    try:
        if isinstance(value, str):
            value = value.strip().replace(",", "")
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _parse_size(value) -> int | None:
    """Accepts 1048576, '10MB', '500 kb', '2G' …"""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return int(value)
    match = re.fullmatch(r"\s*([\d.]+)\s*([kmgtp]?i?b?)\s*", str(value), re.IGNORECASE)
    if not match:
        return None
    number = float(match.group(1))
    unit = (match.group(2) or "b").lower()
    factors = {"b": 1, "kb": 1024, "k": 1024, "mb": 1024 ** 2, "m": 1024 ** 2,
               "gb": 1024 ** 3, "g": 1024 ** 3, "tb": 1024 ** 4, "t": 1024 ** 4,
               "pb": 1024 ** 5, "p": 1024 ** 5}
    return int(number * factors.get(unit, 1))


@verify_action("file_controller")
def file_controller(
    parameters: dict,
    response=None,
    player=None,
    session_memory=None
) -> str:
    params = dict(parameters or {})
    action = str(params.get("action") or params.get("command") or "").lower().strip()
    action = _ACTION_ALIASES.get(action, action)
    path    = params.get("path") or "desktop"
    name    = params.get("name") or ""
    content = params.get("content") or ""

    def _full_path(p: str, n: str) -> str:
        base = _resolve_path(p)
        if n:
            return str(base / n)
        return str(base)

    def _target() -> str:
        return _full_path(path, name)

    result = "Unknown action."

    try:
        if action == "list":
            result = list_files(path,
                                show_hidden=_as_bool(params.get("show_hidden"), False),
                                limit=_as_int(params.get("limit"), 500),
                                offset=_as_int(params.get("offset"), 0))

        elif action == "create_file":
            result = create_file(_target(), content=content, parameters=params)

        elif action == "create_folder":
            result = create_folder(_target(), parameters=params)

        elif action == "delete":
            result = delete_file(_target(),
                                 permanent=_as_bool(params.get("permanent"), False),
                                 parameters=params)

        elif action == "move":
            result = move_file(_target(),
                               params.get("destination") or params.get("target") or "",
                               parameters=params)

        elif action == "copy":
            result = copy_file(_target(),
                               params.get("destination") or params.get("target") or "",
                               parameters=params)

        elif action == "rename":
            result = rename_file(_target(), params.get("new_name") or name)

        elif action == "read":
            result = read_file(_target(),
                               max_chars=_as_int(params.get("max_chars"), 3000),
                               parameters=params)

        elif action in ("write", "append"):
            append = action == "append" or _as_bool(params.get("append"), False)
            result = write_file(_target(), content=content, append=append,
                                base64_encoded=_as_bool(
                                    params.get("base64_encoded", params.get("base64")), False),
                                parameters=params)

        elif action == "find":
            result = find_files(
                name=name,
                extension=params.get("extension") or "",
                path=path,
                max_results=_as_int(params.get("max_results", params.get("count")), 20),
                hidden=_as_bool(params.get("show_hidden", params.get("hidden")), False),
                recursive=_as_bool(params.get("recursive"), True),
                kind=params.get("kind") or "any",
                pattern=params.get("pattern") or "",
                max_depth=(None if params.get("max_depth") in (None, "")
                           else _as_int(params.get("max_depth"), 10)),
                min_size=_parse_size(params.get("min_size")),
                max_size=_parse_size(params.get("max_size")),
            )

        elif action == "largest":
            result = get_largest_files(
                path=path,
                count=_as_int(params.get("count"), 10),
                hidden=_as_bool(params.get("show_hidden", params.get("hidden")), False),
                recursive=_as_bool(params.get("recursive"), True),
            )

        elif action == "disk_usage":
            result = get_disk_usage(path)

        elif action == "organize_desktop":
            result = organize_desktop()

        elif action == "organize_folder":
            result = organize_folder(path=path, mode=params.get("mode") or "by_type")

        elif action == "info":
            result = get_file_info(
                _target(),
                compute_hash=_as_bool(params.get("hash", params.get("sha256")), False))

        # ---- navigation -------------------------------------------------
        elif action == "cd":
            result = navigate_to(path)

        elif action == "pwd":
            result = current_dir()

        elif action == "up":
            result = go_up(_as_int(params.get("levels"), 1))

        elif action == "tree":
            result = folder_tree(path,
                                 depth=_as_int(params.get("depth"), 3),
                                 max_entries=_as_int(params.get("max_entries"), 300))

        # ---- open / reveal ---------------------------------------------
        elif action == "open":
            result = open_path(_target(), app=params.get("app") or "")

        elif action == "open_with":
            result = open_path(_target(), app=params.get("app") or "")

        elif action == "reveal":
            result = reveal_path(_target())

        # ---- sharing ----------------------------------------------------
        elif action == "share":
            result = share_file(
                _target(),
                method=params.get("method") or "auto",
                device=params.get("device") or params.get("target") or "",
                destination=params.get("destination") or "",
                duration=_as_int(params.get("duration"), 0),
                parameters=params,
                player=player,
            )

        elif action == "shares":
            result = list_shares()

        elif action == "unshare":
            result = stop_share(params.get("token") or params.get("url") or "")

        # ---- permissions ------------------------------------------------
        elif action == "chmod":
            result = chmod_path(_target(),
                                params.get("permission") or params.get("mode") or "",
                                recursive=_as_bool(params.get("recursive"), False),
                                parameters=params)

        elif action == "chown":
            result = chown_path(_target(),
                                params.get("owner") or params.get("user") or "",
                                recursive=_as_bool(params.get("recursive"), False),
                                parameters=params)

        elif action == "permissions":
            result = get_permissions(_target())

        # ---- system -----------------------------------------------------
        elif action == "users":
            result = list_users()

        elif action == "partitions":
            result = list_partitions()

        elif action == "trash":
            result = trash_action(
                mode=params.get("trash_action") or params.get("mode") or "list",
                path=params.get("trash_item") or params.get("target") or name)

        # ---- archives / recent / analyze -------------------------------
        elif action == "archive":
            result = create_archive(_target(),
                                    target=params.get("destination") or params.get("target") or "",
                                    fmt=params.get("format") or "")

        elif action == "extract":
            result = extract_archive(_target(),
                                     destination=params.get("destination") or "")

        elif action == "recent":
            result = recent_files(path,
                                  count=_as_int(params.get("count"), 20),
                                  days=_as_int(params.get("days"), 7),
                                  hidden=_as_bool(params.get("show_hidden", params.get("hidden")), False))

        elif action == "describe":
            result = describe_file(_target(),
                                   instruction=params.get("instruction") or content,
                                   player=player)

        elif action in ("capabilities", "help"):
            result = capabilities_text()

        else:
            result = f"Unknown action: '{action}'"

    except Exception as e:
        result = f"File controller error: {e}"

    if player:
        try:
            player.write_log(f"[file] {result[:60]}")
        except Exception:
            pass

    return result
