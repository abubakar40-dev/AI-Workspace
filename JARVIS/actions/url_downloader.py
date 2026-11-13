# actions/url_downloader.py
# Generic URL downloader — videos, images, audio, documents, archives
# Uses yt-dlp for video/audio sites, requests for direct file URLs

import os
import re
import sys
import mimetypes
import subprocess
import shutil
import tempfile
from pathlib import Path
from urllib.parse import urlparse, unquote

import requests

# Ensure local imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import yt_dlp
    _YTDLP_OK = True
except ImportError:
    _YTDLP_OK = False

try:
    from config import get_os, is_windows, is_mac, is_linux
except Exception:
    def get_os(): return "linux"
    def is_windows(): return False
    def is_mac(): return False
    def is_linux(): return True

# ─── Constants ────────────────────────────────────────────────────────────────

# Video/audio sites that yt-dlp handles well
_YTDLP_DOMAINS = {
    "youtube.com", "youtu.be", "youtube-nocookie.com",
    "vimeo.com", "dailymotion.com", "twitch.tv",
    "twitter.com", "x.com", "instagram.com", "tiktok.com",
    "facebook.com", "fb.watch", "reddit.com",
    "soundcloud.com", "bandcamp.com", "mixcloud.com",
    "bilibili.com", "nicovideo.jp", " Rumble.com",
    "odysee.com", "lbry.tv", "peertube",
}

# Direct file extensions we can download with requests
_DIRECT_EXTS = {
    # Images
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg", ".ico", ".tiff", ".tif", ".heic", ".avif",
    # Audio
    ".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".opus", ".wma",
    # Video
    ".mp4", ".mkv", ".webm", ".mov", ".avi", ".flv", ".wmv", ".m4v", ".mpg", ".mpeg",
    # Documents
    ".pdf", ".doc", ".docx", ".txt", ".md", ".rtf", ".odt", ".xls", ".xlsx", ".csv", ".ppt", ".pptx",
    # Archives
    ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz",
    # Code/Data
    ".json", ".xml", ".yaml", ".yml", ".py", ".js", ".ts", ".html", ".css",
    # Fonts
    ".ttf", ".otf", ".woff", ".woff2",
}

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def _get_desktop() -> Path:
    return Path.home() / "Desktop"


def _safe_filename(url: str, content_type: str | None = None) -> str:
    """Generate a safe filename from URL and optional Content-Type."""
    parsed = urlparse(url)
    path = unquote(parsed.path)
    name = os.path.basename(path) or "download"

    # Sanitize
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    name = name[:200]  # reasonable limit

    # If no extension, try to guess from Content-Type
    if "." not in name and content_type:
        ext = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if ext:
            name += ext

    return name


def _is_ytdlp_url(url: str) -> bool:
    """Check if URL is from a site yt-dlp handles."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower().replace("www.", "")
    return any(d in domain for d in _YTDLP_DOMAINS)


def _is_direct_file_url(url: str) -> bool:
    """Check if URL looks like a direct file link (has file extension in path)."""
    parsed = urlparse(url)
    path = parsed.path.lower()
    return any(path.endswith(ext) for ext in _DIRECT_EXTS)


def _looks_like_file_url(url: str) -> bool:
    """Check if URL might serve a file (no video site domain)."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower().replace("www.", "")
    return not any(d in domain for d in _YTDLP_DOMAINS)


def _download_with_ytdlp(url: str, output_dir: Path, format_id: str | None = None) -> str:
    """Download video/audio using yt-dlp."""
    if not _YTDLP_OK:
        return "yt-dlp not installed. Run: pip install yt-dlp"

    output_dir.mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "merge_output_format": "mp4",
    }
    if format_id:
        ydl_opts["format"] = format_id

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return f"Downloaded: {filename}"
    except Exception as e:
        return f"yt-dlp download failed: {e}"


def _download_direct(url: str, output_dir: Path) -> str:
    """Download a direct file URL using requests."""
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Stream download to handle large files
        with requests.get(url, stream=True, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        }) as resp:
            resp.raise_for_status()

            content_type = resp.headers.get("Content-Type", "")
            filename = _safe_filename(url, content_type)
            filepath = output_dir / filename

            # Handle duplicate names
            counter = 1
            stem, suffix = filepath.stem, filepath.suffix
            while filepath.exists():
                filepath = output_dir / f"{stem}_{counter}{suffix}"
                counter += 1

            total_size = int(resp.headers.get("Content-Length", 0))
            downloaded = 0

            with open(filepath, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

            size_str = _format_size(filepath.stat().st_size)
            return f"Downloaded: {filepath.name} ({size_str})"

    except requests.RequestException as e:
        return f"Download failed: {e}"
    except Exception as e:
        return f"Download error: {e}"


def _format_size(bytes_size: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f} TB"


def _open_file(filepath: Path) -> None:
    """Open the downloaded file with default application."""
    try:
        if is_windows():
            subprocess.Popen(["cmd", "/c", "start", "", str(filepath)], shell=False)
        elif is_mac():
            subprocess.Popen(["open", str(filepath)])
        else:
            subprocess.Popen(["xdg-open", str(filepath)])
    except Exception as e:
        print(f"[URLDownloader] Could not open file: {e}")


# ─── Main Entry Point ─────────────────────────────────────────────────────────

def url_downloader(
    parameters: dict,
    response=None,
    player=None,
    session_memory=None,
) -> str:
    """
    Download a file from a URL. Handles:
    - Video/audio sites (YouTube, Vimeo, Twitter, etc.) via yt-dlp
    - Direct file URLs (images, documents, audio, video, archives) via requests

    parameters:
        url           : (required) The URL to download
        output_path   : (optional) Directory to save to (default: Desktop)
        format        : (optional) yt-dlp format selector (e.g. "bestaudio", "bestvideo+bestaudio/best")
        open_after    : (optional) Open file after download (default: true)
    """
    params = parameters or {}
    url = params.get("url", "").strip()
    output_path = params.get("output_path", "").strip()
    format_id = params.get("format", "").strip() or None
    open_after = str(params.get("open_after", "true")).lower() in ("true", "1", "yes", "y")

    if not url:
        return "Please provide a URL to download, sir."

    if not (url.startswith("http://") or url.startswith("https://")):
        return "Invalid URL — must start with http:// or https://, sir."

    # Resolve output directory
    if output_path:
        output_dir = Path(output_path).expanduser()
    else:
        output_dir = _get_desktop()

    print(f"[URLDownloader] ▶️ Downloading: {url}")
    if player:
        player.write_log(f"[url_downloader] {url}")

    try:
        # Check direct file URL FIRST (images, documents, etc.)
        if _is_direct_file_url(url):
            result = _download_direct(url, output_dir)
        elif _is_ytdlp_url(url):
            # Known video/audio site → yt-dlp
            result = _download_with_ytdlp(url, output_dir, format_id)
        elif _looks_like_file_url(url):
            # Not a video site — try direct download first
            result = _download_direct(url, output_dir)
            # If direct download fails (non-2xx, not a file), try yt-dlp as fallback
            if _YTDLP_OK and ("failed" in result.lower() or "error" in result.lower()):
                print("[URLDownloader] Direct download failed, trying yt-dlp...")
                result = _download_with_ytdlp(url, output_dir, format_id)
        else:
            # Unknown — try yt-dlp first (it supports 1000+ sites), then direct
            if _YTDLP_OK:
                print("[URLDownloader] Trying yt-dlp as generic extractor...")
                result = _download_with_ytdlp(url, output_dir, format_id)
                if "failed" in result.lower():
                    print("[URLDownloader] yt-dlp failed, trying direct download...")
                    result = _download_direct(url, output_dir)
            else:
                result = _download_direct(url, output_dir)

        # Try to extract filepath from result for open_after
        if open_after and "Downloaded:" in result:
            # Extract path from "Downloaded: /path/to/file"
            match = re.search(r"Downloaded:\s*(.+?)(?:\s*\(|\s*$)", result)
            if match:
                filepath_str = match.group(1).strip()
                filepath = Path(filepath_str)
                if not filepath.is_absolute():
                    filepath = output_dir / filepath_str
                if filepath.exists():
                    _open_file(filepath)

        return result

    except Exception as e:
        print(f"[URLDownloader] ❌ {e}")
        return f"Download failed, sir: {e}"