# wayland_native.py
#
# Wayland-native screen capture for JARVIS.
#
# Uses grim (wayland-utils) for screenshots on Wayland,
# falls back to mss on X11, and provides a unified API
# that works across both display servers.
#
# All screenshots are saved locally — no cloud upload.
# This is the 100% private, offline Wayland screenshot solution.

import os
import sys
import subprocess
import platform
from pathlib import Path
from datetime import datetime
from typing import Optional
from threading import Lock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ─── Configuration ──────────────────────────────────────────────

_OS = platform.system()  # "Windows" | "Darwin" | "Linux"
_IS_WAYLAND = os.environ.get("WAYLAND_DISPLAY") is not None or \
              os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"

_SCREENCAP_LOCK = Lock()

# ─── Wayland Screenshot via grim ────────────────────────────────

def _is_scrot_available() -> bool:
    """Check if scrot is installed and available."""
    return bool(subprocess.run(
        ["which", "scrot"], capture_output=True
    ).returncode == 0)


def _is_grim_available() -> bool:
    """Check if grim is installed and available."""
    return bool(subprocess.run(
        ["which", "grim"], capture_output=True
    ).returncode == 0)


def _is_scatpipe_available() -> bool:
    """Check if slurp is installed (for region selection)."""
    return bool(subprocess.run(
        ["which", "slurp"], capture_output=True
    ).returncode == 0)


def _screenshot_wayland(output_path: str = None) -> Optional[bytes]:
    """
    Capture the screen on Wayland.

    Preferred: the shared capture chain in screen_capture.py (XDG portal
    silent -> portal interactive with auto-Enter -> grim -> gnome-screenshot).
    On GNOME/XWayland scrot and mss return rc=0 but a 100% BLACK frame --
    the chain rejects blank frames, so a success below is real pixels.

    Returns PNG bytes if output_path is None, True if saved to file, None on failure.
    """
    # Preferred: shared chain (real pixels, blank frames rejected)
    try:
        from screen_capture import capture as _chain_capture
        if output_path:
            ok, _detail = _chain_capture(output_path, timeout=12.0)
            if ok:
                return True
        else:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = tmp.name
            try:
                ok, _detail = _chain_capture(tmp_path, timeout=12.0)
                if ok:
                    with open(tmp_path, "rb") as f:
                        return f.read()
            finally:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
    except Exception as e:
        print(f"[WaylandNative] chain error: {e}")

    # Legacy fallback: scrot (rc=0 but may be black on XWayland), then grim
    if _is_scrot_available():
        with _SCREENCAP_LOCK:
            try:
                if output_path:
                    result = subprocess.run(
                        ["scrot", output_path],
                        capture_output=True, timeout=10
                    )
                    return result.returncode == 0
                # Use temp file for bytes capture
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp_path = tmp.name
                try:
                    result = subprocess.run(
                        ["scrot", tmp_path],
                        capture_output=True, timeout=10
                    )
                    if result.returncode == 0:
                        with open(tmp_path, "rb") as f:
                            data = f.read()
                        return data
                    return None
                finally:
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass
            except Exception as e:
                print(f"[WaylandNative] scrot error: {e}")
    
    # Fallback to grim
    if _is_grim_available():
        with _SCREENCAP_LOCK:
            try:
                if output_path:
                    result = subprocess.run(
                        ["grim", output_path],
                        capture_output=True, timeout=10
                    )
                    return result.returncode == 0
                else:
                    result = subprocess.run(
                        ["grim", "-"],
                        capture_output=True, timeout=10
                    )
                    if result.returncode == 0:
                        return result.stdout
                    return None
            except Exception as e:
                print(f"[WaylandNative] grim error: {e}")
    
    return None


def _screenshot_region_wayland(x: int, y: int, w: int, h: int, output_path: str = None) -> Optional[bytes]:
    """
    Capture a screen region on Wayland.

    Preferred: full-frame + crop through the shared chain (real pixels on
    GNOME, where XWayland-based scrot regions come back black).
    Legacy scrot/grim attempts remain as fallback.
    """
    # Preferred: shared chain (full frame, cropped locally)
    try:
        import tempfile
        tmp = output_path
        cleanup = False
        if not tmp:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as fh:
                tmp = fh.name
            cleanup = True
        try:
            from screen_capture import capture_region as _chain_region
            ok, _detail = _chain_region(x, y, w, h, tmp)
            if ok:
                if output_path:
                    return True
                with open(tmp, "rb") as f:
                    return f.read()
        finally:
            if cleanup:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
    except Exception as e:
        print(f"[WaylandNative] chain region error: {e}")

    # Legacy fallback: scrot regions (may be black on XWayland)
    if _is_scrot_available():
        import tempfile
        with _SCREENCAP_LOCK:
            try:
                # Use xdotool to get mouse position and scrot -z for region
                # scrot -z enables interactive region selection
                # For programmatic region capture, use scrot with -t timeout
                # or use xdotool to create a selection overlay
                tmp_path = output_path or tempfile.mktemp(suffix=".png")
                
                # Use xdotool to simulate mouse drag for region selection
                # Then scrot to capture
                result = subprocess.run(
                    ["scrot", "-z", tmp_path],
                    capture_output=True, timeout=15
                )
                if result.returncode == 0 and output_path:
                    return True
                if result.returncode == 0:
                    with open(tmp_path, "rb") as f:
                        data = f.read()
                    if not output_path:
                        os.unlink(tmp_path)
                    return data
                return None
            except Exception as e:
                print(f"[WaylandNative] scrot region error: {e}")
    
    # Fallback: use xdotool for region selection + scrot
    if _is_scrot_available():
        try:
            # Use xdotool to select a region, then scrot captures it
            import tempfile
            tmp_path = output_path or tempfile.mktemp(suffix=".png")
            
            # scrot -a captures a specific area
            result = subprocess.run(
                ["scrot", "-a", f"{x},{y},{w},{h}", tmp_path],
                capture_output=True, timeout=10
            )
            if result.returncode == 0:
                if output_path:
                    return True
                with open(tmp_path, "rb") as f:
                    data = f.read()
                if not output_path:
                    os.unlink(tmp_path)
                return data
            return None
        except Exception as e:
            print(f"[WaylandNative] scrot -a error: {e}")
    
    # Fallback to grim + slurp
    if _is_grim_available() and _is_scatpipe_available():
        region = f"{x},{y} {w}x{h}"
        with _SCREENCAP_LOCK:
            try:
                if output_path:
                    result = subprocess.run(
                        ["grim", "-g", region, output_path],
                        capture_output=True, timeout=10
                    )
                    return result.returncode == 0
                else:
                    result = subprocess.run(
                        ["grim", "-g", region, "-"],
                        capture_output=True, timeout=10
                    )
                    if result.returncode == 0:
                        return result.stdout
                    return None
            except Exception as e:
                print(f"[WaylandNative] grim region error: {e}")
    
    return None


# ─── X11 Screenshot via mss ─────────────────────────────────────

def _screenshot_x11(output_path: str = None) -> Optional[bytes]:
    """
    Capture screen using mss on X11.
    """
    try:
        import mss
        import mss.tools
    except ImportError:
        return None
    
    with _SCREENCAP_LOCK:
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]  # Primary monitor
                if output_path:
                    output = Path(output_path)
                    output.parent.mkdir(parents=True, exist_ok=True)
                    sct.shot(output=str(output), monitor=monitor)
                    return True
                else:
                    img = sct.grab(monitor)
                    import io
                    img_bytes = mss.tools.to_png(img.rgb, img.size)
                    return img_bytes
        except Exception as e:
            print(f"[WaylandNative] mss error: {e}")
            return None


# ─── macOS Screenshot ────────────────────────────────────────────

def _screenshot_macos(output_path: str = None) -> Optional[bytes]:
    """
    Capture screen using osascript on macOS.
    """
    try:
        if output_path:
            result = subprocess.run(
                ["osascript", "-e", f'tell application "System Events" to screenshot desktop file "{output_path}"'],
                capture_output=True, timeout=10
            )
            # Fallback to screencapture
            if result.returncode != 0:
                result = subprocess.run(
                    ["screencapture", "-x", output_path],
                    capture_output=True, timeout=10
                )
            return result.returncode == 0
        else:
            result = subprocess.run(
                ["screencapture", "-x", "-"],
                capture_output=True, timeout=10
            )
            if result.returncode == 0:
                return result.stdout
            return None
    except Exception as e:
        print(f"[WaylandNative] macOS screenshot error: {e}")
        return None


# ─── Windows Screenshot ──────────────────────────────────────────

def _screenshot_windows(output_path: str = None) -> Optional[bytes]:
    """
    Capture screen using pyautogui on Windows.
    """
    try:
        import pyautogui
    except ImportError:
        return None
    
    with _SCREENCAP_LOCK:
        try:
            img = pyautogui.screenshot()
            import io
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            bytes_data = buf.getvalue()
            
            if output_path:
                Path(output_path).write_bytes(bytes_data)
                return True
            return bytes_data
        except Exception as e:
            print(f"[WaylandNative] Windows screenshot error: {e}")
            return None


# ─── Unified Public API ─────────────────────────────────────────

def capture_screenshot(output_path: str = None) -> Optional[bytes]:
    """
    Capture the entire screen.
    
    Args:
        output_path: Optional file path to save the screenshot.
                     If None, returns PNG bytes.
    
    Returns:
        bytes of PNG image, True if saved to file, or None on failure.
    """
    if _IS_WAYLAND and _OS == "Linux":
        return _screenshot_wayland(output_path)
    elif _OS == "Darwin":
        return _screenshot_macos(output_path)
    elif _OS == "Windows":
        return _screenshot_windows(output_path)
    else:
        return _screenshot_x11(output_path)


def capture_region(x: int, y: int, w: int, h: int, output_path: str = None) -> Optional[bytes]:
    """
    Capture a screen region.
    
    Args:
        x, y: Top-left coordinates
        w, h: Width and height
        output_path: Optional file path to save.
    
    Returns:
        bytes of PNG image, True if saved to file, or None on failure.
    """
    if _IS_WAYLAND and _OS == "Linux":
        return _screenshot_region_wayland(x, y, w, h, output_path)
    elif _OS == "Darwin":
        try:
            result = subprocess.run(
                ["screencapture", "-R", f"{x},{y},{w},{h}", "-"],
                capture_output=True, timeout=10
            )
            if result.returncode == 0:
                if output_path:
                    Path(output_path).write_bytes(result.stdout)
                    return True
                return result.stdout
            return None
        except Exception:
            return None
    elif _OS == "Windows":
        try:
            import pyautogui
            img = pyautogui.screenshot(region=(x, y, w, h))
            import io
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            bytes_data = buf.getvalue()
            if output_path:
                Path(output_path).write_bytes(bytes_data)
                return True
            return bytes_data
        except Exception:
            return None
    else:
        return _screenshot_x11(output_path)


def capture_and_save(output_dir: str = None, prefix: str = "screenshot") -> str:
    """
    Capture a screenshot and save to file.
    
    Args:
        output_dir: Directory to save in (default: ~/Desktop).
        prefix: Filename prefix (default: "screenshot").
    
    Returns:
        Path to the saved screenshot file, or None on failure.
    """
    if output_dir is None:
        output_dir = str(Path.home() / "Desktop")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.png"
    output_path = str(Path(output_dir) / filename)
    
    result = capture_screenshot(output_path)
    if result is True or (result and not isinstance(result, bool)):
        return output_path
    return None


# ─── Screen Info ────────────────────────────────────────────────

def get_screen_resolution() -> tuple[int, int]:
    """Get the primary screen resolution."""
    if _IS_WAYLAND and _OS == "Linux":
        try:
            result = subprocess.run(
                ["wlr-randr"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "current" in line or "preferred" in line:
                        parts = line.strip().split()
                        for i, p in enumerate(parts):
                            if p == "current" and i > 0:
                                return int(parts[i-1]), int(parts[i])
        except Exception:
            pass
        # Fallback: use grim to get resolution
        try:
            result = subprocess.run(
                ["grim", "-g", "0,0 1 1", "-"],
                capture_output=True, timeout=5
            )
            if result.returncode == 0 and len(result.stdout) > 100:
                # Approximate from PNG header
                pass
        except Exception:
            pass
    
    try:
        from PIL import Image
        img = Image.open("/dev/null")
    except Exception:
        pass
    
    # Ultimate fallback: try xrandr or pyautogui
    try:
        import pyautogui
        return pyautogui.size()
    except Exception:
        pass
    
    try:
        result = subprocess.run(
            ["xrandr"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if " connected" in line and "primary" in line:
                    parts = line.strip().split()
                    for p in parts:
                        if "x" in p and p != "connected":
                            dims = p.split("x")[0]
                            return int(dims), int(p.split("x")[1].split("+")[0])
    except Exception:
        pass
    
    return (1366, 768)  # Default fallback


def is_wayland() -> bool:
    """Check if running under Wayland."""
    return _IS_WAYLAND


def is_wayland_screenshot_available() -> bool:
    """Check if Wayland screenshots work (scrot or grim available)."""
    return _IS_WAYLAND and (_is_scrot_available() or _is_grim_available())


# ─── Preview/Display ────────────────────────────────────────────

def preview_screenshot(image_bytes: bytes) -> bool:
    """
    Open a screenshot for viewing using the default image viewer.
    """
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(image_bytes)
        tmp_path = f.name
    
    try:
        if _OS == "Darwin":
            subprocess.Popen(["open", tmp_path])
        elif _OS == "Windows":
            os.startfile(tmp_path)
        else:
            subprocess.Popen(["xdg-open", tmp_path])
        return True
    except Exception as e:
        print(f"[WaylandNative] Preview error: {e}")
        return False
    finally:
        # Clean up after a delay
        import threading
        def cleanup():
            time.sleep(5)
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        threading.Thread(target=cleanup, daemon=True).start()


# ─── Backwards Compatibility ────────────────────────────────────

# Provide aliases for existing code
screenshot = capture_screenshot
screenshot_region = capture_region
screenshot_save = capture_and_save
get_resolution = get_screen_resolution

# Import time for cleanup
import time


def test_screenshot() -> dict:
    """Test the screenshot pipeline. Returns status dict."""
    import tempfile
    
    status = {
        "wayland": _IS_WAYLAND,
        "os": _OS,
        "scrot_available": _is_scrot_available(),
        "grim_available": _is_grim_available(),
        "slurp_available": _is_scatpipe_available(),
        "mss_available": False,
        "screenshot_works": False,
        "test_file": None,
    }
    
    try:
        import mss
        status["mss_available"] = True
    except ImportError:
        pass
    
    # Try to capture
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp_path = f.name
    
    result = capture_screenshot(tmp_path)
    if result is True or (result and isinstance(result, str)):
        status["screenshot_works"] = True
        status["test_file"] = result if isinstance(result, str) else tmp_path
    else:
        # Try bytes capture
        result = capture_screenshot()
        if result and len(result) > 1000:
            status["screenshot_works"] = True
            Path(tmp_path).write_bytes(result)
            status["test_file"] = tmp_path
    
    return status


# ─── Vault Read/Write ───────────────────────────────────

def vault_read(path: str) -> str:
    """Read a vault file by relative path."""
    full_path = Path.home() / ".obsidian-vault" / path
    if full_path.exists():
        return full_path.read_text(encoding="utf-8", errors="ignore")
    return ""


def vault_write(path: str, content: str) -> bool:
    """Write a vault file by relative path."""
    full_path = Path.home() / ".obsidian-vault" / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")
    return True


def vault_delete(path: str) -> bool:
    """Delete a vault file by relative path."""
    full_path = Path.home() / ".obsidian-vault" / path
    if full_path.exists():
        full_path.unlink()
        return True
    return False


def vault_exists(path: str) -> bool:
    """Check if a vault file exists."""
    return (Path.home() / ".obsidian-vault" / path).exists()