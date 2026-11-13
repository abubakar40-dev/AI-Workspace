#!/usr/bin/env python3
"""HELIX Desktop Application — standalone GTK3 + WebKit2GTK desktop app.

Self-contained: starts the WebSocket bridge as a managed child process and
loads the Helix UI in an embedded WebKit2GTK WebView. No Chrome dependency,
no browser cache issues — the UI is served by the bridge on 127.0.0.1 and
loaded over that same origin, so the WebSocket is same-origin too.

Note on GTK versions: the WebKit2GTK 4.1 typelib on this machine is built
against GTK 3, and importing it pulls Gtk-3.0 in automatically. Requiring
Gtk 4.0 first therefore fails with "Gtk version '3.0' is already loaded".
So: GTK 3.0 + WebKit2 4.1.
"""
import os
import sys
import subprocess
import time
import signal
import atexit
import socket

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.1")

from gi.repository import Gtk, WebKit2, GLib, Gdk, Gio

HELIX_DIR = os.path.expanduser("~/JARVIS")
BRIDGE_SCRIPT = os.path.join(HELIX_DIR, "bridge_ws.py")
APP_ID = "jarvis"
RUNTIME_DIR = os.path.expanduser(os.environ.get("XDG_RUNTIME_DIR", "/tmp"))
LOCK_FILE = os.path.join(RUNTIME_DIR, "jarvis.lock")
LOG_DIR = os.path.expanduser("~/.local/state/jarvis/logs")


def log(msg):
    """Timestamped line into the XDG state log dir."""
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(os.path.join(LOG_DIR, "app.log"), "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except Exception:
        pass


def find_free_port():
    """Pick a free TCP port on 127.0.0.1."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def is_app_running():
    """True if another Helix instance holds the lock."""
    if not os.path.exists(LOCK_FILE):
        return False
    try:
        with open(LOCK_FILE, "r") as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        try:
            os.unlink(LOCK_FILE)
        except OSError:
            pass
        return False


def write_lock(pid):
    with open(LOCK_FILE, "w") as f:
        f.write(str(pid))


def clear_lock():
    try:
        os.unlink(LOCK_FILE)
    except OSError:
        pass


def _child_preexec():
    """Make the bridge child die with this process.

    Without PR_SET_PDEATHSIG the bridge is orphaned whenever the app dies
    in a way GTK does not route through do_shutdown (SIGKILL, session
    logout, a crash). It then keeps holding its port forever.
    """
    try:
        import ctypes
        PR_SET_PDEATHSIG = 1
        ctypes.CDLL("libc.so.6", use_errno=True).prctl(
            PR_SET_PDEATHSIG, signal.SIGTERM)
    except Exception:
        pass
    os.setpgrp()


class HelixWindow(Gtk.ApplicationWindow):
    def __init__(self, app, port):
        super().__init__(application=app, title="HELIX — AI Command Center")
        self.set_default_size(1400, 900)
        self.set_position(Gtk.WindowPosition.CENTER)
        # GTK3 has no set_widget_name (that is GTK4). set_name() is the GTK3
        # equivalent and is what the desktop file's StartupWMClass is matched
        # against once the window is realized.
        self.set_name("jarvis")

        icon_path = os.path.join(HELIX_DIR, "assets", "Jarvis_Logo.png")
        if os.path.exists(icon_path):
            try:
                self.set_icon_from_file(icon_path)
            except Exception:
                pass

        self.webview = WebKit2.WebView()
        self.set_hexpand(True)
        self.set_vexpand(True)

        # Load the UI FROM THE BRIDGE over HTTP — same origin as the WebSocket.
        # A file:// page has an opaque origin, and WebKit then refuses or
        # mis-handles the ws:// connection, so the UI sat on BRIDGE OFFLINE.
        # ?demo=0 guarantees the demo backend never starts in this session.
        uri = f"http://127.0.0.1:{port}/?demo=0&bridge=ws://127.0.0.1:{port}"
        self.webview.load_uri(uri)

        self.add(self.webview)
        self.webview.connect("load-changed", self._on_load_changed)
        self.connect("destroy", Gtk.main_quit)
        self.show_all()
        # Pin the WM_CLASS so the GNOME dock groups the window under the
        # jarvis icon instead of a generic "python3" entry. StartupWMClass in
        # the .desktop file must equal the first component ("jarvis").
        self.connect("realize", self._set_wmclass)
        # WebKit does not show Chrome's per-site camera/mic prompt, so the
        # page's getUserMedia() just rejects with NotAllowedError. Granting
        # here is what makes the Voice Core mic and the Media Link camera
        # work at all. Only microphone/camera requests are auto-allowed;
        # anything else is denied.
        try:
            self.webview.connect("permission-request", self._on_permission)
        except Exception:
            log("permission-request signal unavailable")

    def _on_permission(self, _webview, request):
        try:
            if isinstance(request, WebKit2.UserMediaPermissionRequest):
                request.allow()
                log("granted user-media permission (mic/camera)")
                return True
        except Exception:
            pass
        try:
            request.deny()
        except Exception:
            pass
        return False

    def _set_wmclass(self, _w):
        try:
            gdk_window = self.get_window()
            if gdk_window:
                gdk_window.set_wmclass("jarvis", "Jarvis")
        except Exception:
            pass

    def _on_load_changed(self, webview, event):
        if event == WebKit2.LoadEvent.FINISHED:
            print("[OK] HELIX UI loaded", flush=True)
            log("UI loaded")
            GLib.timeout_add(7000, lambda: (self._diagnose(webview), False)[1])
        elif event == WebKit2.LoadEvent.STARTED:
            print("[..] loading HELIX UI…", flush=True)
            log("loading UI")

    def _diagnose(self, webview):
        """Ask the page what it thinks its state is, and log the answer.

        A webview that silently failed looks identical to one that is
        working. Reading the page's own state is the only way to tell.
        """
        js = """(function(){
            try {
              var H = window.H || {}, S = H.state || {};
              return JSON.stringify({
                mode: S.mode,
                souls: S.souls ? Object.keys(S.souls).length : 0,
                bridgeConnected: !!(H.bridge && H.bridge.connected),
                bridgeUrl: H.bridge ? H.bridge.url : null,
                agents: S.agents ? Object.keys(S.agents).length : 0,
                tasks: S.tasks ? Object.keys(S.tasks).length : 0,
                chat: S.chat ? S.chat.length : 0,
                headlines: S.headlines ? S.headlines.length : 0,
                lms: !!S.lms,
                memory: S.memory ? S.memory.length : 0,
                skills: S.skills ? S.skills.length : 0,
                model: S.model,
                ctxUsed: S.ctx ? S.ctx.used : null,
                voice: S.voice,
                orbAlive: !!(window.H && H.orb && !H.orb.dead),
                errors: (window.__jarvisErrors || []).slice(0, 8)
              });
            } catch (e) { return JSON.stringify({fatal: String(e)}); }
        })()"""
        try:
            webview.run_javascript(js, None, self._diagnose_done, None)
        except Exception as e:
            log(f"diagnose failed: {e}")

    def _diagnose_done(self, webview, result, _user_data):
        # run_javascript is the ASYNC evaluator; the value comes out of
        # run_javascript_finish, and reading it as a plain string is what
        # produced "Must be string, not Task".
        try:
            jsv = webview.run_javascript_finish(result)
            value = jsv.get_js_value()
            log(f"page state: {value.to_string()}")
        except Exception as e:
            log(f"diagnose read failed: {e}")

    def snapshot_to_file(self, path):
        """Render the webview to a PNG. Lets the UI be inspected without a
        screenshot tool (Wayland compositors refuse gnome-screenshot/grim)."""
        try:
            self.webview.get_snapshot(
                WebKit2.SnapshotRegion.VISIBLE, WebKit2.SnapshotOptions.NONE,
                None, self._snapshot_done, path)
            return path
        except Exception as e:
            log(f"snapshot failed: {e}")
            return None

    def _snapshot_done(self, webview, result, path):
        try:
            surface = webview.get_snapshot_finish(result)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            surface.write_to_png(path)
            log(f"snapshot written: {path} ({os.path.getsize(path)} bytes)")
        except Exception as e:
            log(f"snapshot write failed: {e}")


class HelixApp(Gtk.Application):
    def __init__(self):
        # A D-Bus application id must contain a dot — "jarvis" is rejected by
        # g_application_set_application_id and the WM_CLASS then never gets
        # set. "jarvis.desktop" is valid and yields the class "jarvis".
        super().__init__(application_id="jarvis.desktop",
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.bridge_proc = None
        self.bridge_port = None
        self.window = None

    def do_startup(self):
        Gtk.Application.do_startup(self)

        if is_app_running():
            print("HELIX is already running.", file=sys.stderr)
            sys.exit(0)

        self.bridge_port = find_free_port()
        env = dict(os.environ)
        env["HELIX_BRIDGE_PORT"] = str(self.bridge_port)
        self.bridge_proc = subprocess.Popen(
            [sys.executable, BRIDGE_SCRIPT, "--port", str(self.bridge_port)],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            cwd=HELIX_DIR, env=env, preexec_fn=_child_preexec)

        ready = False
        for _ in range(120):
            if is_port_in_use(self.bridge_port):
                ready = True
                break
            time.sleep(0.05)

        if not ready:
            print("ERROR: bridge did not start on port", self.bridge_port,
                  file=sys.stderr)
            self.bridge_proc.kill()
            self.bridge_proc = None
            clear_lock()
        else:
            print(f"[OK] Bridge on 127.0.0.1:{self.bridge_port}", flush=True)
            log(f"bridge up on 127.0.0.1:{self.bridge_port} pid={self.bridge_proc.pid}")

        write_lock(os.getpid())

    def do_activate(self):
        if self.window is not None:
            self.window.present()
            return
        self.window = HelixWindow(self, self.bridge_port)
        # A rendered snapshot lands in the log dir. It is the only way to see
        # the UI on a Wayland box where gnome-screenshot and grim are refused.
        GLib.timeout_add(9000, self._snapshot_once)

    def _snapshot_once(self):
        if self.window:
            self.window.snapshot_to_file(
                os.path.join(LOG_DIR, "ui-snapshot.png"))
        return False

    def _snapshot_now(self):
        """SIGHUP: capture the UI on demand (also useful to the user)."""
        if self.window:
            self.window.snapshot_to_file(
                os.path.join(LOG_DIR, "ui-snapshot.png"))
        return False

    def do_shutdown(self):
        log("shutting down")
        if self.bridge_proc and self.bridge_proc.poll() is None:
            self.bridge_proc.terminate()
            try:
                self.bridge_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.bridge_proc.kill()
        clear_lock()


def main():
    app = HelixApp()

    # GLib's unix-signal callbacks receive exactly ONE argument (the user
    # data), not the usual (signum, frame). A two-argument handler raises
    # TypeError inside the C callback, which GLib swallows — so the signal
    # was received and then silently ignored, and the app never quit.
    def _make_handler(sig):
        def _on_signal(_user_data=None):
            print(f"[..] signal {sig} — shutting down", flush=True)
            GLib.idle_add(app.quit)
            return False
        return _on_signal

    def _on_hup(_user_data=None):
        # SIGHUP captures the UI instead of quitting: on Wayland there is no
        # screenshot tool, so this is the only way to see what the window
        # currently shows.
        if app.window:
            GLib.idle_add(app._snapshot_now)
        return False

    try:
        from gi.repository import GLibUnix
        for sig in (signal.SIGTERM, signal.SIGINT):
            GLibUnix.signal_add(GLib.PRIORITY_HIGH, sig, _make_handler(sig))
        # SIGHUP captures the UI instead of quitting.
        GLibUnix.signal_add(GLib.PRIORITY_HIGH, signal.SIGHUP, _on_hup)
    except Exception:
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                GLib.unix_signal_add(GLib.PRIORITY_HIGH, sig,
                                      _make_handler(sig))
            except Exception:
                pass
        try:
            GLib.unix_signal_add(GLib.PRIORITY_HIGH, signal.SIGHUP, _on_hup)
        except Exception:
            pass

    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())