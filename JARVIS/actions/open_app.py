# actions/open_app.py
# Jarvis - Cross-Platform App Launcher

import time
import subprocess
import platform
import shutil
import shlex
from pathlib import Path

try:
    import psutil
    _PSUTIL = True
except ImportError:
    _PSUTIL = False

_APP_ALIASES = {
    "whatsapp":           {"Windows": "WhatsApp",               "Darwin": "WhatsApp",            "Linux": "whatsapp"},
    "chrome":             {"Windows": "chrome",                 "Darwin": "Google Chrome",       "Linux": "google-chrome"},
    "google chrome":      {"Windows": "chrome",                 "Darwin": "Google Chrome",       "Linux": "google-chrome"},
    "firefox":            {"Windows": "firefox",                "Darwin": "Firefox",             "Linux": "firefox"},
    "spotify":            {"Windows": "Spotify",                "Darwin": "Spotify",             "Linux": "spotify"},
    "vscode":             {"Windows": "code",                   "Darwin": "Visual Studio Code",  "Linux": "code"},
    "visual studio code": {"Windows": "code",                   "Darwin": "Visual Studio Code",  "Linux": "code"},
    "discord":            {"Windows": "Discord",                "Darwin": "Discord",             "Linux": "discord"},
    "telegram":           {"Windows": "Telegram",               "Darwin": "Telegram",            "Linux": "telegram"},
    "instagram":          {"Windows": "Instagram",              "Darwin": "Instagram",           "Linux": "instagram"},
    "tiktok":             {"Windows": "TikTok",                 "Darwin": "TikTok",              "Linux": "tiktok"},
    "notepad":            {"Windows": "notepad.exe",            "Darwin": "TextEdit",            "Linux": "gedit"},
    "calculator":         {"Windows": "calc.exe",               "Darwin": "Calculator",          "Linux": "gnome-calculator"},
    "terminal":           {"Windows": "cmd.exe",                "Darwin": "Terminal",            "Linux": "gnome-terminal"},
    "cmd":                {"Windows": "cmd.exe",                "Darwin": "Terminal",            "Linux": "bash"},
    "explorer":           {"Windows": "explorer.exe",           "Darwin": "Finder",              "Linux": "nautilus"},
    "file explorer":      {"Windows": "explorer.exe",           "Darwin": "Finder",              "Linux": "nautilus"},
    "paint":              {"Windows": "mspaint.exe",            "Darwin": "Preview",             "Linux": "gimp"},
    "word":               {"Windows": "winword",                "Darwin": "Microsoft Word",      "Linux": "libreoffice --writer"},
    "excel":              {"Windows": "excel",                  "Darwin": "Microsoft Excel",     "Linux": "libreoffice --calc"},
    "powerpoint":         {"Windows": "powerpnt",               "Darwin": "Microsoft PowerPoint","Linux": "libreoffice --impress"},
    "vlc":                {"Windows": "vlc",                    "Darwin": "VLC",                 "Linux": "vlc"},
    "zoom":               {"Windows": "Zoom",                   "Darwin": "zoom.us",             "Linux": "zoom"},
    "slack":              {"Windows": "Slack",                  "Darwin": "Slack",               "Linux": "slack"},
    "steam":              {"Windows": "steam",                  "Darwin": "Steam",               "Linux": "steam"},
    "task manager":       {"Windows": "taskmgr.exe",            "Darwin": "Activity Monitor",    "Linux": "gnome-system-monitor"},
    "settings":           {"Windows": "ms-settings:",           "Darwin": "System Preferences",  "Linux": "gnome-control-center"},
    "powershell":         {"Windows": "powershell.exe",         "Darwin": "Terminal",            "Linux": "bash"},
    "edge":               {"Windows": "msedge",                 "Darwin": "Microsoft Edge",      "Linux": "microsoft-edge"},
    "brave":              {"Windows": "brave",                  "Darwin": "Brave Browser",       "Linux": "brave-browser"},
    "obsidian":           {"Windows": "Obsidian",               "Darwin": "Obsidian",            "Linux": "obsidian"},
    "notion":             {"Windows": "Notion",                 "Darwin": "Notion",              "Linux": "notion"},
    "blender":            {"Windows": "blender",                "Darwin": "Blender",             "Linux": "blender"},
    "capcut":             {"Windows": "CapCut",                 "Darwin": "CapCut",              "Linux": "capcut"},
    "postman":            {"Windows": "Postman",                "Darwin": "Postman",             "Linux": "postman"},
    "figma":              {"Windows": "Figma",                  "Darwin": "Figma",               "Linux": "figma"},
}


def _normalize(raw: str) -> str:
    system = platform.system()
    key    = raw.lower().strip()
    if key in _APP_ALIASES:
        return _APP_ALIASES[key].get(system, raw)
    for alias_key, os_map in _APP_ALIASES.items():
        if alias_key in key or key in alias_key:
            return os_map.get(system, raw)
    return raw


def _is_running(app_name: str) -> bool:
    if not _PSUTIL:
        return True
    app_lower = app_name.lower().replace(" ", "").replace(".exe", "")
    try:
        for proc in psutil.process_iter(["name"]):
            try:
                proc_name = proc.info["name"].lower().replace(" ", "").replace(".exe", "")
                if app_lower in proc_name or proc_name in app_lower:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception:
        pass
    return False


def _launch_windows(app_name: str) -> bool:
    try:
        import pyautogui
        pyautogui.PAUSE = 0.1
        pyautogui.press("win")
        time.sleep(0.6)
        pyautogui.write(app_name, interval=0.05)
        time.sleep(0.8)
        pyautogui.press("enter")
        time.sleep(3.0)
        return True
    except Exception as e:
        print(f"[open_app] ⚠️ Windows launch failed: {e}")
        return False

def _launch_macos(app_name: str) -> bool:
    try:
        result = subprocess.run(["open", "-a", app_name], capture_output=True, timeout=8)
        if result.returncode == 0:
            time.sleep(1.0)
            return True
    except Exception:
        pass

    try:
        result = subprocess.run(["open", "-a", f"{app_name}.app"], capture_output=True, timeout=8)
        if result.returncode == 0:
            time.sleep(1.0)
            return True
    except Exception:
        pass

    try:
        import pyautogui
        pyautogui.hotkey("command", "space")
        time.sleep(0.6)
        pyautogui.write(app_name, interval=0.05)
        time.sleep(0.8)
        pyautogui.press("enter")
        time.sleep(1.5)
        return True
    except Exception as e:
        print(f"[open_app] ⚠️ macOS Spotlight failed: {e}")
        return False



def _launch_linux(app_name: str) -> bool:
    binary = (
        shutil.which(app_name) or
        shutil.which(app_name.lower()) or
        shutil.which(app_name.lower().replace(" ", "-"))
    )
    if binary:
        try:
            proc = subprocess.Popen([binary], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1.0)
            exit_code = proc.poll()
            # Still running after 1s -> genuinely launched. Some apps
            # legitimately fork a real window and exit 0 quickly, so treat
            # a clean exit as success too -- only a *nonzero* exit shortly
            # after launch means it actually failed.
            if exit_code is None or exit_code == 0:
                return True
            print(f"[open_app] ⚠️ {binary} exited immediately with code {exit_code}")
        except Exception as e:
            print(f"[open_app] ⚠️ Popen failed for {binary}: {e}")

    # Resolve graphical applications by their desktop-entry metadata when the
    # executable name differs from the human-facing application name.
    needle = app_name.casefold().replace("-", " ")
    desktop_dirs = (
        Path.home() / ".local/share/applications",
        Path("/usr/local/share/applications"),
        Path("/usr/share/applications"),
    )
    for directory in desktop_dirs:
        if not directory.is_dir():
            continue
        for desktop_file in directory.glob("*.desktop"):
            try:
                fields = {}
                for line in desktop_file.read_text(errors="replace").splitlines():
                    if "=" in line and not line.startswith("#"):
                        key, value = line.split("=", 1)
                        fields[key] = value.strip()
                names = " ".join((fields.get("Name", ""), fields.get("GenericName", "")))
                if needle not in names.casefold().replace("-", " "):
                    continue
                try:
                    result = subprocess.run(
                        ["gtk-launch", desktop_file.stem],
                        capture_output=True,
                        timeout=8,
                    )
                    if result.returncode == 0:
                        return True
                except (OSError, subprocess.SubprocessError):
                    pass
                command = fields.get("Exec", "")
                if command:
                    argv = [
                        token for token in shlex.split(command)
                        if not token.startswith("%")
                    ]
                    if argv:
                        proc = subprocess.Popen(
                            argv,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        time.sleep(1.0)
                        if proc.poll() in (None, 0):
                            return True
            except (OSError, subprocess.SubprocessError):
                continue

    # xdg-open is meant for opening files/URLs by MIME association, not
    # launching an app by name -- it will usually fail for a bare app
    # name, but the previous code returned True unconditionally here
    # regardless of whether it actually worked. Check the real exit code.
    try:
        result = subprocess.run(["xdg-open", app_name], capture_output=True, timeout=5)
        if result.returncode == 0:
            return True
        print(f"[open_app] ⚠️ xdg-open {app_name!r} failed (exit {result.returncode}): "
              f"{result.stderr.decode(errors='replace')[:200]}")
    except Exception as e:
        print(f"[open_app] ⚠️ xdg-open failed: {e}")

    try:
        desktop_name = app_name.lower().replace(" ", "-")
        result = subprocess.run(["gtk-launch", desktop_name], capture_output=True, timeout=5)
        if result.returncode == 0:
            return True
        print(f"[open_app] ⚠️ gtk-launch {desktop_name!r} failed (exit {result.returncode})")
    except Exception as e:
        print(f"[open_app] ⚠️ gtk-launch failed: {e}")

    return False


_OS_LAUNCHERS = {
    "Windows": _launch_windows,
    "Darwin":  _launch_macos,
    "Linux":   _launch_linux,
}


def open_app(
    parameters=None,
    response=None,
    player=None,
    session_memory=None,
) -> str:
    app_name = (parameters or {}).get("app_name", "").strip()

    if not app_name:
        return "Please specify which application to open, sir."

    system   = platform.system()
    launcher = _OS_LAUNCHERS.get(system)

    if launcher is None:
        return f"Unsupported OS: {system}"

    normalized = _normalize(app_name)
    print(f"[open_app] 🚀 Launching: {app_name} → {normalized} ({system})")

    if player:
        player.write_log(f"[open_app] {app_name}")

    try:
        success = launcher(normalized)

        if success:
            return f"Opened {app_name} successfully, sir."

        if normalized != app_name:
            success = launcher(app_name)
            if success:
                return f"Opened {app_name} successfully, sir."

        return (
            f"I tried to open {app_name}, sir, but couldn't confirm it launched. "
            f"It may still be loading or might not be installed."
        )

    except Exception as e:
        print(f"[open_app] ❌ {e}")
        return f"Failed to open {app_name}, sir: {e}"