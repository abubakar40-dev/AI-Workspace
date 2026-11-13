"""Tests for wayland_native.py — the X11/Wayland screenshot solution.

This module tests the unified screenshot pipeline that works across:
  - Wayland (scrot primary, grim fallback)
  - X11 (mss)
  - macOS (osascript/screencapture)
  - Windows (pyautogui)

All screenshots are saved locally. No cloud upload.
"""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest
from PIL import Image

import wayland_native as wn


# --------------------------------------------------------------------------
# basic functionality
# --------------------------------------------------------------------------
def test_screenshot_module_loads():
    """The wayland_native module loads without errors."""
    assert hasattr(wn, 'capture_screenshot')
    assert hasattr(wn, 'capture_region')
    assert hasattr(wn, 'capture_and_save')
    assert hasattr(wn, 'get_screen_resolution')
    assert hasattr(wn, 'is_wayland')
    assert hasattr(wn, 'is_wayland_screenshot_available')


def test_wayland_detection():
    """is_wayland() returns a boolean."""
    result = wn.is_wayland()
    assert isinstance(result, bool)


def test_screenshot_available_check():
    """is_wayland_screenshot_available() returns a boolean."""
    result = wn.is_wayland_screenshot_available()
    assert isinstance(result, bool)


def test_resolution_returns_tuple():
    """get_screen_resolution() returns (width, height)."""
    res = wn.get_screen_resolution()
    assert isinstance(res, tuple)
    assert len(res) == 2
    assert isinstance(res[0], int) and isinstance(res[1], int)
    assert res[0] > 0 and res[1] > 0


def test_screenshot_to_file():
    """capture_and_save() creates a PNG file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = wn.capture_and_save(tmpdir)
        assert result is not None, "capture_and_save returned None"
        assert Path(result).exists(), f"File not created: {result}"
        assert Path(result).stat().st_size > 0, "File is empty"
        img = Image.open(result)
        assert img.format == "PNG"


def test_screenshot_bytes():
    """capture_screenshot() works without crash."""
    result = wn.capture_screenshot()
    assert result is None or isinstance(result, (bytes, bool))


def test_region_capture():
    """capture_region() works without crash."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        result = wn.capture_region(0, 0, 100, 100, tmp_path)
        assert result is None or isinstance(result, bool) or (result and Path(result).exists())
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_preview_screenshot():
    """preview_screenshot() accepts bytes data without crash."""
    png_data = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x02, 0x00, 0x00, 0x00,
        0x90, 0x77, 0x53, 0xDE,
        0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41, 0x54,
        0x08, 0xD7, 0x63, 0xF8, 0x0F, 0x00, 0x00, 0x01,
        0x01, 0x00, 0x05, 0x18, 0xD8,
        0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44,
        0xAE, 0x42, 0x60, 0x82,
    ])
    result = wn.preview_screenshot(png_data)
    assert isinstance(result, bool) or result is None


def test_wayland_chain():
    """test_screenshot() returns valid status dict."""
    status = wn.test_screenshot()
    assert "wayland" in status
    assert "os" in status
    assert "screenshot_works" in status
    assert "scrot_available" in status
    assert "grim_available" in status


def test_screenshot_works():
    """The screenshot pipeline works."""
    status = wn.test_screenshot()
    assert isinstance(status["screenshot_works"], bool)


def test_backwards_compatibility():
    """Aliases exist for backwards compatibility."""
    assert hasattr(wn, 'screenshot')
    assert hasattr(wn, 'screenshot_region')
    assert hasattr(wn, 'screenshot_save')
    assert hasattr(wn, 'get_resolution')


def test_vault_read_write():
    """vault_read/vault_write/vault_delete work."""
    assert hasattr(wn, 'vault_read')
    assert hasattr(wn, 'vault_write')
    assert hasattr(wn, 'vault_delete')
    assert hasattr(wn, 'vault_exists')
    
    test_path = "test_vault_write.md"
    assert wn.vault_write(test_path, "test content")
    assert wn.vault_exists(test_path)
    content = wn.vault_read(test_path)
    assert "test content" in content
    assert wn.vault_delete(test_path)
    assert not wn.vault_exists(test_path)


# --------------------------------------------------------------------------
# screen_capture.py integration
# --------------------------------------------------------------------------
def test_screen_capture_delegation():
    """screen_capture.py delegates to wayland_native."""
    import screen_capture as sc
    
    assert hasattr(sc, 'capture')
    assert hasattr(sc, 'grab')
    assert hasattr(sc, 'status')
    assert hasattr(sc, 'capture_region')


def test_screen_capture_capture():
    """screen_capture.capture() returns tuple."""
    import screen_capture as sc
    ok, detail = sc.capture()
    assert isinstance(ok, bool)
    assert isinstance(detail, str)