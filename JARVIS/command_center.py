"""
The JARVIS Command Center host.

Replaces the previous Qt cockpit GUI. The interface itself is
``assets/command_center/index.html`` -- the operator's design, shipped
byte-for-byte and never edited. This module is the room it lives in: it owns
the web view, the QWebChannel transport, the telemetry pollers that keep every
panel honest, and the public API that ``main.py`` and the action modules
already call.

Threading
---------
``main.py`` calls into the UI from audio, tool and screen-processing threads.
Everything that touches Qt or the page is marshalled onto the GUI thread via
``_Invoke``, so no worker ever reaches a widget. ``write_log`` and
``set_audio_level`` are the two genuinely hot paths and are queue/throttle
based instead, because a signal per log line would flood the event loop.
"""

from __future__ import annotations

import json
import os
import platform
import sys
import time
from collections import deque
from pathlib import Path

from PyQt6.QtCore import QObject, QThread, QTimer, QUrl, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QApplication, QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

# Chromium's Qt bindings require this attribute to be set *before* the
# QCoreApplication exists; otherwise importing QtWebEngineWidgets aborts the
# process with "QWidget: Must construct a QApplication before a QWidget".
# main.py imports this module before it builds an application, so setting it
# here is early enough.
QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)

try:
    from PyQt6.QtWebChannel import QWebChannel
    from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineScript
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEB_ENGINE_AVAILABLE = True
except Exception as exc:                                # pragma: no cover
    print(f"[CommandCenter] QtWebEngine unavailable: {exc}")
    WEB_ENGINE_AVAILABLE = False

from command_bridge import (
    BINDING_JS, COMMAND_CENTER_HTML, QWEBCHANNEL_JS, CommandCenterBridge,
    build_agent_rows, build_llm_rows, gauge_colour, human_bytes,
)
from command_panels import ChatDrawer, PanelDrawer, build_view

BASE_DIR = Path(__file__).resolve().parent
APP_VERSION = "8.0.0"

#: The holographic dashboard — a self-contained HTML file with inlined Three.js
#: that renders a 3D animated core (molten sphere + wireframe shells + particles).
HOLOGRAPHIC_HTML = BASE_DIR / "gui" / "assets" / "jarvis.html"


# ---------------------------------------------------------------------------
# Cross-thread invocation
# ---------------------------------------------------------------------------
class _Invoke(QObject):
    """Runs a callable on the GUI thread, whatever thread calls it."""

    _call = pyqtSignal(object, object, object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._call.connect(self._run, Qt.ConnectionType.QueuedConnection)

    def _run(self, fn, args, kwargs) -> None:
        try:
            fn(*args, **kwargs)
        except Exception as exc:                         # pragma: no cover
            print(f"[CommandCenter] marshalled call failed: {exc}")

    def post(self, fn, *args, **kwargs) -> None:
        self._call.emit(fn, args, kwargs)


class _Page(QWebEnginePage):
    """Surfaces page-side errors instead of swallowing them."""

    def javaScriptConsoleMessage(self, level, message, line, source):  # noqa: N802
        low = str(message).lower()
        if "error" in low or "uncaught" in low:
            print(f"[CommandCenter] page error: {message} (line {line})")


# ---------------------------------------------------------------------------
# API key prompt (only shown when nothing is configured)
# ---------------------------------------------------------------------------
def _api_keys_path() -> Path:
    return BASE_DIR / "config" / "api_keys.json"


def _read_api_keys() -> dict:
    try:
        with open(_api_keys_path(), "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_api_keys(data: dict) -> None:
    path = _api_keys_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass


#: Keeps the application alive. Without a module-level reference the object
#: created inside ensure_application() loses its last Python reference the
#: moment that function returns, is destroyed, and the next QWidget aborts with
#: "Must construct a QApplication before a QWidget".
_APP: QApplication | None = None


def ensure_application() -> QApplication:
    """Return the QApplication, creating it if the caller has not.

    ``main.py`` constructs the UI before it builds an application, exactly as
    it did with the previous GUI, so the window has to be able to stand this up
    for itself.
    """
    global _APP
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv[:1])
        app.setApplicationName("JARVIS")
        app.setApplicationDisplayName("JARVIS Command Center")
    _APP = app
    return app


# ---------------------------------------------------------------------------
# The command center
# ---------------------------------------------------------------------------
class CommandCenter(QWidget):
    """The window ``main.py`` drives. Public names match the previous GUI."""

    def __init__(self, logo_path: str | None = None,
                 show_immediately: bool = True, parent=None) -> None:
        ensure_application()
        super().__init__(parent)
        self.logo_path = logo_path

        # -- state the rest of the app reads and writes --------------------
        self.muted = False
        self.current_file = ""
        self.states: list[str] = []
        self._wakeword_listening = False

        # -- callbacks main.py assigns --------------------------------------
        self.on_text_command = None
        self.on_attention_action = None
        self.on_remote_clicked = None
        self.on_briefing = None
        self._brahma_connect_service = None
        self._focus = False
        self._chat_greeted = False
        self._attention_log: list[dict] = []
        self._recent_feed: deque = deque(maxlen=60)

        # -- internals ------------------------------------------------------
        self._invoke = _Invoke(self)
        self._page_ready = False
        self._level = 0.0
        self._level_sent = 0.0
        self._states_sent = "IDLE"
        self._feed_queue: deque = deque(maxlen=200)
        self._chat_queue: deque = deque(maxlen=200)
        self._feed_seen: deque = deque(maxlen=60)
        self._memory_history: deque = deque(maxlen=24)
        self._memory_seeded = False
        self._turns = 0
        self._cost = 0.0
        self._mic_down = False
        self._last_cpu = [0.0, 0.0]
        self._prev_net = (0, 0)
        self._settings: dict = {}
        self._task: dict | None = None
        self._timeline: list[dict] = []
        self._boot_steps: list[dict] = []
        self._boot_percent = 0
        self._location = ""
        self._weather = ""
        self._temp = "--"
        self._weather_icon = "☀"
        self._network: str | None = None

        self.setWindowTitle("JARVIS Command Center")
        self.resize(1440, 900)
        self.setMinimumSize(1024, 640)

        self._build()
        self._start_pollers()

        if show_immediately:
            self.show_main()

    # ------------------------------------------------------------------ build
    def _build(self) -> None:
        if not WEB_ENGINE_AVAILABLE:
            self._build_fallback()
            return

        # -- tab widget: Command Center + Holographic Dashboard ------------
        self.tabs = QTabWidget(self)
        self.tabs.setStyleSheet(
            "QTabWidget::pane{border:none;}"
            "QTabBar{background:#0a0705;border:none;}"
            "QTabBar::tab{background:#0a0705;color:#9a8163;padding:8px 20px;"
            "font:600 12px 'Rajdhani';letter-spacing:1px;border:none;}"
            "QTabBar::tab:selected{color:#ffdb96;background:#130d08;"
            "border-bottom:2px solid #ffb020;}"
            "QTabBar::tab:hover{color:#ffdb96;}"
        )

        # -- Tab 1: Command Center (existing web view) ----------------------
        self.view = QWebEngineView()
        page = _Page(self.view)
        self.view.setPage(page)
        # Scrollbars stay on. The design is taller than a laptop viewport at
        # narrow widths, and hiding them made the System Monitor, Memory
        # Insights and LLM Status panels unreachable with no way to scroll.

        self.bridge = CommandCenterBridge(self)
        self.channel = QWebChannel(page)
        self.channel.registerObject("pybridge", self.bridge)
        page.setWebChannel(self.channel)

        self.bridge.command_received.connect(self._on_page_command)
        self.bridge.mute_requested.connect(self._on_page_mute)
        self.bridge.nav_requested.connect(self._on_page_nav)
        self.bridge.icon_requested.connect(self._on_page_icon)
        self.bridge.view_requested.connect(self.open_view)
        self.bridge.chat_requested.connect(self._on_chat_request)
        self.bridge.briefing_requested.connect(self.run_briefing)
        self.bridge.focus_state.connect(self._on_focus_state)

        self.tabs.addTab(self.view, "Command Center")

        # -- Tab 2: Holographic Dashboard (new web view) --------------------
        self.holo_view = QWebEngineView()
        holo_page = _Page(self.holo_view)
        self.holo_view.setPage(holo_page)
        self.tabs.addTab(self.holo_view, "Holographic Dashboard")

        # -- layout ----------------------------------------------------------
        # The tab widget must actually fill the window. Without this it keeps
        # Qt's default 100x30 and the operator sees a postage stamp.
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.tabs)

        # Panels float above the page, so the operator's design is untouched.
        self.drawer = PanelDrawer(self)
        self.chat = ChatDrawer(self)
        self.drawer.action.connect(self._on_panel_action)
        self.chat.submitted.connect(self._on_chat_submitted)

        self._build_developer_card()

        page.loadFinished.connect(self._on_page_loaded)
        # The base URL is the project's own directory so the page's Google
        # Fonts <link> and any relative asset resolve; the file itself is
        # untouched.
        self.view.load(QUrl.fromLocalFile(str(COMMAND_CENTER_HTML)))
        self.holo_view.load(QUrl.fromLocalFile(str(HOLOGRAPHIC_HTML)))
        # Share the same QWebChannel (with pybridge registered) between both tabs
        self.holo_view.page().setWebChannel(self.channel)

        # Inject the same stub on the holographic view so its inline scripts
        # don't crash before the bridge connects either.
        _stub_holo = (
            "if(!window.JarvisUI){window.JarvisUI={apply:function(){},pushFeed:function(){},"
            "setState:function(){},setMuted:function(){},setLevel:function(){},"
            "setCore:function(){},setFooter:function(){},setUser:function(){},"
            "setTimeline:function(){},setTask:function(){},setBadges:function(){},"
            "setNavActive:function(){},setFocus:function(){},ready:false};}"
        )
        _stub_holo_script = QWebEngineScript()
        _stub_holo_script.setSourceCode(_stub_holo)
        _stub_holo_script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        _stub_holo_script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        _stub_holo_script.setName("jarvis-ui-stub-holo")
        self.holo_view.page().scripts().insert(_stub_holo_script)

    def _build_fallback(self) -> None:
        """If QtWebEngine is missing, say so instead of showing a blank window."""
        box = QLabel(
            "The Command Center needs PyQt6-WebEngine.\n\n"
            "    pip install PyQt6-WebEngine\n\n"
            f"(page expected at {COMMAND_CENTER_HTML})"
        )
        box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        box.setStyleSheet("color:#cfe8f2;background:#070c16;font:14px sans-serif;")
        lay = QVBoxLayout(self)
        lay.addWidget(box)

    def _build_developer_card(self) -> None:
        """``main.py`` shows this with .show()/.raise_() while Gemini builds."""
        self._developer_card = QFrame(self)
        self._developer_card.setStyleSheet(
            "QFrame{background:#0d1526;border:1px solid #1c2c45;border-radius:12px;}"
        )
        lay = QVBoxLayout(self._developer_card)
        lay.setContentsMargins(16, 14, 16, 14)
        title = QLabel("DEVELOPER MODE")
        title.setStyleSheet("color:#22e6ff;font:600 11px 'Rajdhani';letter-spacing:2px;")
        self._developer_status_lbl = QLabel("Working…")
        self._developer_status_lbl.setWordWrap(True)
        self._developer_status_lbl.setStyleSheet(
            "color:#cfe8f2;font:13px 'Rajdhani';")
        close = QPushButton("Close")
        close.clicked.connect(self._developer_card.hide)
        close.setStyleSheet(
            "QPushButton{background:#0f1a2c;border:1px solid #1c2c45;border-radius:8px;"
            "color:#cfe8f2;padding:6px 14px;font:600 11px 'Rajdhani';letter-spacing:1px;}"
            "QPushButton:hover{border-color:#22e6ff;color:#22e6ff;}"
        )
        lay.addWidget(title)
        lay.addWidget(self._developer_status_lbl)
        lay.addWidget(close)
        self._developer_card.resize(380, 160)
        self._developer_card.move(40, 120)
        self._developer_card.hide()

    # ------------------------------------------------------------------ page
    def _on_page_loaded(self, ok: bool) -> None:
        if not ok:
            print(f"[CommandCenter] page failed to load: {COMMAND_CENTER_HTML}")
            return
        self._page_ready = True
        # Pull in qwebchannel.js from Qt's own resource, then bind. Doing this
        # from JS means the operator's HTML needs no <script> tag from us.
        boot = (
            "(function(){"
            "  var s=document.createElement('script');"
            f" s.src='{QWEBCHANNEL_JS}';"
            "  s.onload=function(){"
            "    try{ new QWebChannel(qt.webChannelTransport, function(c){"
            "      window.__jarvisChannel=c; window.__jarvisBound=false;"
            # QWebChannel exposes objects on channel.objects; it does not
            # create a window.pybridge global. Without this line every click
            # in the page silently did nothing.
            "      window.pybridge = c.objects.pybridge;"
            f"      {BINDING_JS}"
            "    }); }catch(e){ console.error('bridge: '+e); }"
            "  };"
            "  s.onerror=function(){ console.error('qwebchannel.js unavailable'); };"
            "  document.head.appendChild(s);"
            "})();"
        )
        self._js(boot)
        # The page's own clock and placeholder panels are already live; feed
        # the first real snapshot as soon as the binding exists.
        QTimer.singleShot(600, self._push_full_snapshot)

    def _js(self, code: str) -> None:
        """Run page JS, hopping to the GUI thread when necessary.

        main.py drives the UI from the audio, tool, screen and runner threads.
        ``QWebEnginePage.runJavaScript`` is not thread-safe, so every page call
        funnels through here and is marshalled when it did not originate on the
        GUI thread.
        """
        if not (WEB_ENGINE_AVAILABLE and self._page_ready):
            return
        if QThread.currentThread() is self.thread():
            self._run_js(code)
        else:
            self._invoke.post(self._run_js, code)

    def _run_js(self, code: str) -> None:
        try:
            self.view.page().runJavaScript(code)
        except Exception as exc:                         # pragma: no cover
            print(f"[CommandCenter] JS failed: {exc}")

    def _broadcast_js(self, js: str) -> None:
        """Run JavaScript on both the Command Center view and the Holographic Dashboard view."""
        if not (WEB_ENGINE_AVAILABLE and self._page_ready):
            return
        if QThread.currentThread() is self.thread():
            self._run_broadcast_js(js)
        else:
            self._invoke.post(self._run_broadcast_js, js)

    def _run_broadcast_js(self, js: str) -> None:
        """Internal method to run JS on both views - must be called on GUI thread."""
        for v in (self.view, getattr(self, "holo_view", None)):
            if v is not None:
                try:
                    v.page().runJavaScript(js)
                except Exception:
                    pass

    def _call(self, fn: str, *args) -> None:
        """Call a ``window.JarvisUI`` method from Python."""
        payload = json.dumps(list(args), default=str)
        self._broadcast_js(
            f"if(window.JarvisUI && typeof window.JarvisUI['{fn}']==='function')"
            f"{{window.JarvisUI['{fn}'].apply(null,{payload});}}")

    def _apply(self, snapshot: dict) -> None:
        self._broadcast_js(
            "if(window.JarvisUI && typeof window.JarvisUI.apply==='function')"
            "{window.JarvisUI.apply(" + json.dumps(snapshot, default=str) + ");}")

    # ------------------------------------------------------------- page events
    def _on_page_command(self, text: str) -> None:
        if self.on_text_command:
            try:
                self.on_text_command(text, source="gui")
            except TypeError:
                self.on_text_command(text)
        else:
            self.write_log(f"SYS: (no handler) {text}")

    def _on_page_mute(self, muted: bool) -> None:
        self.muted = bool(muted)
        if self.on_text_command and muted:
            # keep the assistant's own echo guard in step with the GUI
            pass
        self.push_feed("Microphone " + ("muted" if muted else "unmuted"),
                       "Command Center", "info", "SYS")

    def _on_page_nav(self, label: str) -> None:
        # The nav is a single-page design: honour the click and route the
        # request rather than pretending there are separate screens.
        self._call("setNavActive", label)
        self.push_feed(f"Opened {label}", "Navigation", "info", "NAV")

    def _on_page_icon(self, index: int) -> None:
        actions = {
            0: "show me the system monitor",
            1: "what are my current notifications",
            2: "open settings",
        }
        cmd = actions.get(index, "show me the dashboard")
        if self.on_text_command:
            self._on_page_command(cmd)

    # ---------------------------------------------------------------- views
    def open_view(self, view: str, payload: str = "") -> None:
        """Show a real panel for anything the operator clicks."""
        request = f"{view}?{payload}" if payload else str(view or "")
        try:
            title, sub, html = build_view(request, self._view_context())
        except Exception as exc:                         # pragma: no cover
            title, sub, html = ("ERROR", str(exc),
                                '<p style="color:#ff4d6d;">Could not open this '
                                'view.</p>')
        if self.chat.isVisible():
            self.chat.close_panel()
        self.drawer.show_view(title, sub, html)

    def _view_context(self) -> dict:
        return {
            "state": self._states_sent,
            "mic_down": self._mic_down,
            "task": self._task,
            "feed": list(self._recent_feed)[-40:],
            "attention": self._attention_log,
        }

    def _on_panel_action(self, kind: str, payload: str) -> None:
        if kind == "say":
            self._on_page_command(payload)
        elif kind == "open":
            from PyQt6.QtGui import QDesktopServices
            path = Path(str(payload or "")).expanduser()
            if path.exists():
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve())))
            else:
                self.push_feed(f"Cannot open {path.name}", "Panel", "warn", "FILE")
        elif kind == "view":
            view, _, rest = str(payload or "").partition("?")
            self.open_view(view, rest)

    def _on_focus_state(self, on: bool) -> None:
        self._focus = bool(on)
        if self._focus:
            self.drawer.close_panel()
            self.chat.close_panel()

    # ----------------------------------------------------------------- chat
    def _on_chat_request(self, open_it: bool) -> None:
        if open_it:
            if self.drawer.isVisible():
                self.drawer.close_panel()
            self._chat_greeting()
            self.chat.show_panel()
        else:
            self.chat.close_panel()

    def _chat_greeting(self) -> None:
        if self._chat_greeted:
            return
        self._chat_greeted = True
        self.chat.append("sys", "Text channel open. Anything typed here is "
                                "handled exactly like a spoken command.")
        if self.muted:
            self.chat.append("sys", "The microphone is muted; the text channel "
                                    "works regardless.")

    def _on_chat_submitted(self, text: str) -> None:
        text = str(text or "").strip()
        if not text:
            return
        if text.lower() in ("/clear", "clear"):
            self.chat.log.clear()
            return
        if self.on_text_command:
            self._on_page_command(text)
        else:
            self.chat.append("err", "No command handler is attached yet.")

    def show_chat(self) -> None:
        """Open the text channel from Python as well."""
        self._on_chat_request(True)

    def run_briefing(self) -> None:
        """Executive Briefing, from the button or from the boot sequence."""
        if self.on_briefing:
            try:
                self.on_briefing()
                return
            except Exception as exc:                     # pragma: no cover
                print(f"[CommandCenter] briefing handler failed: {exc}")
        self.push_feed("No briefing handler attached", "Command Center",
                       "warn", "BRIEF")

    def resizeEvent(self, event):                        # noqa: N802
        super().resizeEvent(event)
        for panel in (getattr(self, "drawer", None), getattr(self, "chat", None)):
            if panel is not None and panel.isVisible():
                panel.setFixedHeight(self.height())
                panel.move(self.width() - panel.width(), 0)

    # =====================================================================
    # Public API -- the names main.py and the action modules already use
    # =====================================================================
    @property
    def root(self) -> "CommandCenter":
        """``main.py`` ends with ``ui.root.mainloop()``."""
        return self

    def mainloop(self) -> int:
        app = QApplication.instance()
        return app.exec() if app else 0

    # -- state ---------------------------------------------------------
    def set_state(self, state: str) -> None:
        state = str(state or "IDLE").upper()
        self.states.append(state)
        if len(self.states) > 200:
            del self.states[:-200]
        if state != self._states_sent:
            self._states_sent = state
            self._call("setState", state)

    def set_muted_state(self, muted: bool, wakeword: bool = False) -> None:
        self.muted = bool(muted)
        self._wakeword_listening = bool(wakeword) and bool(muted)
        self._call("setMuted", self.muted)

    def set_scanning(self, scanning: bool, label: str = "") -> None:
        self._call("setState", "SCANNING" if scanning else "IDLE")
        if scanning and label:
            self.push_feed(label, "Screen analysis", "live", "SCAN")

    def set_meeting_mode(self, active: bool, title: str = "",
                         summary: str = "", answer: str = "", speech: str = "") -> None:
        if active:
            self._call("setState", "MEETING")
            self.push_feed(title or "Meeting started", summary or "Meeting assistant",
                           "live", "MEET")
        else:
            self._call("setState", "LISTENING")
            if answer or speech:
                self.push_feed(answer or speech, title or "Meeting",
                               "tip", "ANSWER")

    # -- logging and the intelligence feed -------------------------------
    def write_log(self, text: str) -> None:
        """Queue a log line. Called from every worker thread, so it must not
        touch Qt. The pollers drain the queue on the GUI thread."""
        text = str(text or "").strip()
        if not text:
            return
        if text.startswith("You:"):
            self._turns += 1
            body = text[4:].strip()
            item = {"title": body, "meta": "Spoken command",
                    "tag": "live", "tagText": "YOU"}
            self._to_chat("you", body)
        elif text.startswith("SYS:"):
            body = text[4:].strip()
            item = {"title": body, "meta": "System",
                    "tag": "info", "tagText": "SYS"}
        elif text.startswith("Jarvis:"):
            body = text[7:].strip()
            item = {"title": body, "meta": "Response",
                    "tag": "tip", "tagText": "JARVIS"}
            self._to_chat("jarvis", body)
        else:
            item = {"title": text, "meta": "Log", "tag": "info",
                    "tagText": "LOG"}
        if not item["title"]:
            return
        # Collapse an immediately repeated line so a retry loop cannot flood
        # the panel.
        if self._feed_seen and self._feed_seen[-1] == item["title"]:
            return
        self._feed_seen.append(item["title"])
        self._feed_queue.append(item)
        self._recent_feed.append(item)

    def _to_chat(self, who: str, text: str) -> None:
        """Mirror a conversation turn into the text channel.

        Called from worker threads, so it only queues; the GUI thread drains it
        alongside the feed.
        """
        try:
            self._chat_queue.append((who, text[:1500]))
        except Exception:
            pass

    def add_system_message(self, text: str) -> None:
        self.write_log(f"SYS: {text}")

    def push_feed(self, title: str, meta: str = "", tag: str = "info",
                  tag_text: str = "") -> None:
        title = str(title or "").strip()
        if not title:
            return
        self._feed_queue.append({"title": title, "meta": str(meta or ""),
                                 "tag": tag, "tagText": tag_text or tag.upper()})

    def _drain_feed(self) -> None:
        while self._chat_queue:
            who, text = self._chat_queue.popleft()
            try:
                self.chat.append(who, text)
            except Exception:
                pass
        if not self._feed_queue:
            return
        while self._feed_queue:
            item = self._feed_queue.popleft()
            self._broadcast_js("window.JarvisUI && window.JarvisUI.pushFeed("
                     f"{json.dumps(item, default=str)});")

    # -- audio level ---------------------------------------------------
    def set_audio_level(self, level: float) -> None:
        """Real microphone level, 0..1. Throttled: the mic callback fires far
        faster than the eye can use.

        Called from PortAudio's real-time thread, so it must never raise into
        the audio path no matter what state the window is in.
        """
        try:
            self._level = max(0.0, min(1.0, float(level or 0.0)))
            now = time.monotonic()
            if now - self._level_sent < 0.08 and self._level < 0.2:
                return
            self._level_sent = now
            self._call("setLevel", round(self._level, 3))
        except Exception:
            pass

    # -- task workspace (Mission Timeline doubles as the task view) ------
    def begin_task_workspace(self, command: str, plan=None, source: str = "local") -> None:
        steps = [str(s) for s in (plan or []) if str(s).strip()]
        self._task = {
            "command": str(command or ""),
            "source": source,
            "steps": steps,
            "index": 0,
            "active": True,
            "percent": 0,
        }
        self._timeline = [
            {"time": f"{i + 1:02d}", "title": s, "eta": "Pending", "done": False}
            for i, s in enumerate(steps[:5])
        ] or [{"time": "01", "title": str(command or "Working"), "eta": "Pending",
               "done": False}]
        self._call("setTimeline", self._timeline)
        self._call("setTask", {"sub": str(command or "Working")[:48],
                               "percent": 0, "active": True})
        self.push_feed(str(command or "Task started"),
                       f"{len(steps)} step(s) · {source}", "live", "TASK")

    def update_task_workspace(self, status: str = "", output: str = "",
                              percent=None, **kwargs) -> None:
        status = status or kwargs.get("state", "") or ""
        percent = percent if percent is not None else kwargs.get("progress")
        if self._task is None:
            # Still forward the text so the operator sees what is happening.
            if output:
                self.push_feed(output[:120], status or "Update", "info", "TASK")
            return
        self._task["status"] = status
        if percent is not None:
            try:
                self._task["percent"] = max(0, min(100, float(percent)))
            except (TypeError, ValueError):
                pass
        # Advance the highlighted step as progress crosses each quarter.
        idx = self._task["index"]
        if idx < len(self._task["steps"]) and percent is not None:
            try:
                want = min(len(self._task["steps"]) - 1,
                           int(float(percent) / 100 * len(self._task["steps"])))
            except (TypeError, ValueError):
                want = idx
            for j in range(self._task["index"], want):
                self._timeline[j] = {**self._timeline[j], "eta": "Done", "done": True}
            self._task["index"] = want
        if self._timeline:
            cur = dict(self._timeline[self._task["index"]])
            cur["eta"] = status or cur.get("eta") or "Working"
            self._timeline[self._task["index"]] = cur
        self._call("setTimeline", self._timeline)
        self._call("setTask", {"sub": (status or output or "")[:48],
                               "percent": self._task.get("percent"),
                               "active": True})

    def finish_task_workspace(self, reply: str = "", status: str = "",
                              percent: int = 100) -> None:
        if self._task is not None:
            for j in range(len(self._timeline)):
                self._timeline[j] = {**self._timeline[j],
                                     "eta": status or "Done", "done": True}
            self._call("setTimeline", self._timeline)
            self._task = None
        self._call("setState", "LISTENING")
        if reply:
            self.push_feed(str(reply)[:180], status or "Result", "tip", "DONE")

    # -- attention -----------------------------------------------------
    def show_attention_alert(self, event: dict) -> None:
        event = event or {}
        app = event.get("app") or "Notification"
        title = event.get("title") or app
        preview = event.get("preview") or event.get("body") or ""
        self._attention_log.append(dict(event))
        del self._attention_log[:-60]
        try:
            self._attention_log_file()
        except Exception:
            pass
        self.push_feed(f"{title}", f"{app} · {preview}"[:80] if preview else str(app),
                       "warn", "ALERT")
        try:
            self._to_chat("sys", f"[{app}] {title} {preview}".strip())
        except Exception:
            pass
        self._call("setState", "LISTENING")
        if self.on_attention_action:
            try:
                self.on_attention_action(event)
            except Exception:
                pass

    def _attention_log_file(self) -> None:
        """Keep the notification history so the panel survives a restart."""
        path = BASE_DIR / "config" / "attention_log.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self._attention_log[-60:], fh, indent=1, default=str)

    def notify_phone_connected(self) -> None:
        self.push_feed("Mobile control connected", "Command Center", "live", "LINK")
        self._call("setState", "LISTENING")

    def submit_external_command(self, text: str, source: str = "mobile") -> None:
        text = str(text or "").strip()
        if not text:
            return
        if self.on_text_command:
            try:
                self.on_text_command(text, source=source)
            except TypeError:
                self.on_text_command(text)

    def set_brahma_connect_service(self, service) -> None:
        self._brahma_connect_service = service

    # -- boot sequence -------------------------------------------------
    # The design has no splash screen, and inventing one would change it. Boot
    # progress is therefore reported through components that already exist:
    # the status pill, the core's subtitle, the Mission Timeline and the feed.
    def boot_add_step(self, label: str) -> None:
        label = str(label or "").strip()
        if not label:
            return
        self._boot_steps.append({"label": label, "status": "pending"})
        self._render_boot_timeline()

    def boot_set_step_status(self, label: str, status: str = "done") -> None:
        label = str(label or "").strip()
        status = str(status or "done").lower()
        for step in self._boot_steps:
            if step["label"] == label:
                step["status"] = "done" if status == "done" else status
                break
        self._render_boot_timeline()

    def _render_boot_timeline(self) -> None:
        if self._task is not None:
            return                       # a running task owns the timeline
        rows = []
        for i, step in enumerate(self._boot_steps[:5]):
            done = step["status"] == "done"
            rows.append({
                "time": f"{i + 1:02d}",
                "title": step["label"],
                "eta": "Ready" if done else "Starting…",
                "done": done,
            })
        if rows:
            self._timeline = rows
            self._call("setTimeline", rows)

    def boot_set_progress(self, percent: int = 0, status: str = "") -> None:
        try:
            pct = max(0, min(100, int(percent)))
        except (TypeError, ValueError):
            pct = 0
        self._boot_percent = pct
        self._js(
            "window.JarvisUI && (function(){"
            f"  var p=document.querySelector('.status-pill');"
            f"  if(p){{ for(var i=0;i<p.childNodes.length;i++){{"
            f"    if(p.childNodes[i].nodeType===3){{"
            f"      p.childNodes[i].nodeValue='SYSTEM STATUS · BOOT {pct}%'; break; }} }} }}"
            f"  var s=document.querySelector('.core-label .sub');"
            f"  if(s){{ s.textContent={json.dumps(str(status or 'BOOTING')[:24].upper())}; }}"
            "})();"
        )

    def play_boot_sequence(self, finished_callback=None, *args, **kwargs) -> None:
        """Announce the end of boot, then run main.py's callback.

        Called as ``play_boot_sequence(finished_callback=...)``; the positional
        and keyword forms are both accepted so no caller can break it.
        """
        if finished_callback is None and args:
            finished_callback = args[0]
        if finished_callback is None:
            finished_callback = kwargs.get("on_finished") or kwargs.get("callback")

        self.boot_set_progress(100, "READY")
        self.push_feed("All systems online", "Command Center", "live", "BOOT")

        def _finish() -> None:
            if finished_callback is None:
                return
            try:
                finished_callback()
            except Exception as exc:                     # pragma: no cover
                print(f"[CommandCenter] boot callback failed: {exc}")

        # A beat of delay keeps main.py's sequencing intact: the runner and the
        # daily-briefing thread start after the interface is visibly up.
        QTimer.singleShot(900, _finish)

    # -- misc ----------------------------------------------------------
    def capture_screen_bytes(self):
        """Bytes of a screenshot, or None. Used by the vision path."""
        try:
            import tempfile
            from screen_capture import capture
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                dest = tmp.name
            ok, detail = capture(dest=dest)
            if not ok:
                return None
            return Path(dest).read_bytes()
        except Exception as exc:
            print(f"[CommandCenter] screen capture failed: {exc}")
            return None

    def _load_app_settings(self) -> dict:
        path = BASE_DIR / "config" / "app_settings.json"
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            self._settings = data if isinstance(data, dict) else {}
        except Exception:
            self._settings = {}
        return self._settings

    def wait_for_api_key(self) -> bool:
        """Block until a Gemini key is available.

        Returns immediately when ``config/api_keys.json`` already has one, so
        the prompt only ever appears on a genuinely unconfigured machine.
        """
        keys = _read_api_keys()
        if str(keys.get("gemini_api_key") or keys.get("google_api_key") or "").strip():
            return True
        if not self._page_ready and not WEB_ENGINE_AVAILABLE:
            return False

        dlg = QDialog(self)
        dlg.setWindowTitle("JARVIS · API key")
        dlg.setStyleSheet(
            "QDialog{background:#0d1526;}"
            "QLabel{color:#cfe8f2;font:13px 'Rajdhani';}"
            "QLineEdit{background:#0d1626;border:1px solid #1c2c45;border-radius:8px;"
            "color:#cfe8f2;padding:8px;font:13px monospace;}"
            "QPushButton{background:#0f1a2c;border:1px solid #22e6ff;border-radius:8px;"
            "color:#22e6ff;padding:8px 18px;font:700 11px 'Rajdhani';letter-spacing:1px;}"
        )
        lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel("Gemini API key — stored in config/api_keys.json"))
        edit = QLineEdit()
        edit.setEchoMode(QLineEdit.EchoMode.Password)
        lay.addWidget(edit)
        row = QHBoxLayout()
        row.addStretch(1)
        ok_btn = QPushButton("SAVE")
        cancel = QPushButton("CANCEL")
        row.addWidget(cancel)
        row.addWidget(ok_btn)
        lay.addLayout(row)
        ok_btn.clicked.connect(dlg.accept)
        cancel.clicked.connect(dlg.reject)
        dlg.setModal(True)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return False
        key = edit.text().strip()
        if not key:
            return False
        keys["gemini_api_key"] = key
        try:
            _write_api_keys(keys)
        except Exception as exc:
            QMessageBox.warning(self, "JARVIS", f"Could not save the key: {exc}")
            return False
        return True

    def show_main(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    def hide_main(self) -> None:
        self.hide()

    def show_holographic_dashboard(self) -> None:
        """Switch to the Holographic Dashboard tab."""
        if hasattr(self, "tabs") and self.tabs.count() > 1:
            self.tabs.setCurrentIndex(1)

    def show_command_center(self) -> None:
        """Switch to the Command Center tab."""
        if hasattr(self, "tabs") and self.tabs.count() > 0:
            self.tabs.setCurrentIndex(0)

    # =====================================================================
    # Telemetry -- every panel is driven by real readings, never mock values
    # =====================================================================
    def _start_pollers(self) -> None:
        self._feed_timer = QTimer(self)
        self._feed_timer.timeout.connect(self._drain_feed)
        self._feed_timer.start(250)

        self._fast_timer = QTimer(self)
        self._fast_timer.timeout.connect(self._poll_fast)
        self._fast_timer.start(1000)

        self._slow_timer = QTimer(self)
        self._slow_timer.timeout.connect(self._poll_slow)
        self._slow_timer.start(2500)

        # Agent status has to be quick: an operator watching the Active Agents
        # panel must see an agent light up when it starts and go dark when it
        # finishes, not up to a minute later.
        self._agent_timer = QTimer(self)
        self._agent_timer.timeout.connect(self._poll_agents)
        self._agent_timer.start(1200)

    def _poll_agents(self) -> None:
        """Live agent registry -> the Active Agents panel and the core row."""
        try:
            import agent_runtime as AR
            rows = AR.agent_rows()
        except Exception:
            return
        if not any(r.get("real") for r in rows):
            return
        self._agent_rows = rows
        self._apply({"agents": rows})
        working = sum(1 for r in rows if r.get("active"))
        real = sum(1 for r in rows if r.get("real"))
        self._apply({"core": {"agents": (f"{working} of {real} Working"
                                          if working else f"{real} Ready")}})
        self._agent_goal = AR.progress().get("goal", "")

    def _poll_fast(self) -> None:
        """Gauges, network and the core's System row: the numbers that move."""
        try:
            import hud_sensors as S
        except Exception:
            S = None

        cpu = ram = disk = None
        net_mbps = None
        if S is not None:
            try:
                cpu = S.cpu_percent()
            except Exception:
                cpu = None
            try:
                ram = S.mem_percent()
            except Exception:
                ram = None
            try:
                disk = S.disk_percent("/")
            except Exception:
                disk = None
            try:
                net_mbps = S.net_mbps()
            except Exception:
                net_mbps = None

        if cpu is not None and 0 <= cpu <= 100:
            self._last_cpu[0] = cpu
        if ram is not None and 0 <= ram <= 100:
            self._last_cpu[1] = ram

        gauges = [
            {"label": "CPU",  "val": round(self._last_cpu[0], 1), "color": gauge_colour(self._last_cpu[0])},
            {"label": "RAM",  "val": round(self._last_cpu[1], 1), "color": gauge_colour(self._last_cpu[1])},
            {"label": "Disk", "val": round(disk or 0, 1),      "color": gauge_colour(disk or 0)},
        ]
        self._apply({"gauges": gauges})

        if self._task is None:
            system = "Optimal"
            if cpu is not None and cpu >= 85:
                system = "Under Load"
            elif cpu is None:
                system = "Unknown"
            self._apply({"core": {"system": system}})

        if net_mbps is not None:
            self._network = ("Excellent" if net_mbps >= 50 else
                             "Good" if net_mbps >= 8 else
                             "Fair" if net_mbps >= 1 else "Idle")
        elif self._network is None:
            self._network = "Unknown"
        self._apply({"footer": {"network": self._network or "Unknown"}})

    def _poll_slow(self) -> None:
        """Everything slower than a gauge: memory, providers, agents, place."""
        self._push_full_snapshot()

    # -- individual panels ---------------------------------------------
    def _memory_count(self) -> int:
        try:
            from memory.memory_manager import load_memory
            data = load_memory() or {}
            if isinstance(data, dict):
                return sum(len(v) for v in data.values()
                           if isinstance(v, (list, dict, set)))
            if isinstance(data, (list, set)):
                return len(data)
        except Exception:
            pass
        return 0

    def _turn_count(self) -> int:
        """Real session turns, counted from today's conversation log."""
        try:
            from datetime import datetime
            from chat_history_manager import get_day
            body = get_day(datetime.now().strftime("%Y-%m-%d")) or ""
            return body.count("**You:**")
        except Exception:
            return 0

    def _conversation_count(self) -> int:
        try:
            from chat_history_manager import list_days
            return len(list_days())
        except Exception:
            return 0

    def _memory_history_series(self) -> list[int]:
        """Real memories *added per day* for the last 24 days.

        The Memory Insights chart plots additions rather than the cumulative
        total, because a cumulative line barely moves between saves and reads
        as a dead chart. Today's figure is refreshed on every poll, so the last
        point stays live while the history behind it is genuine.
        """
        if not self._memory_seeded:
            self._memory_seeded = True
            try:
                import sqlite3
                from datetime import date, timedelta
                db = BASE_DIR / "memory" / "personal_memory.sqlite3"
                if db.exists():
                    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
                    rows = dict(con.execute(
                        "SELECT substr(created_at,1,10), COUNT(*) "
                        "FROM memory_entries GROUP BY 1").fetchall())
                    con.close()
                    today = date.today()
                    series = []
                    for back in range(23, -1, -1):
                        day = (today - timedelta(days=back)).isoformat()
                        series.append(int(rows.get(day, 0)))
                    self._memory_history = deque(series, maxlen=24)
            except Exception as exc:
                print(f"[CommandCenter] memory history unavailable: {exc}")

        # Keep today's live value as the final point.
        try:
            import sqlite3
            from datetime import date
            db = BASE_DIR / "memory" / "personal_memory.sqlite3"
            if db.exists():
                con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
                n = con.execute(
                    "SELECT COUNT(*) FROM memory_entries "
                    "WHERE substr(created_at,1,10)=?", (date.today().isoformat(),)
                ).fetchone()[0]
                con.close()
                if self._memory_history:
                    self._memory_history[-1] = int(n)
        except Exception:
            pass
        return list(self._memory_history)

    def _push_full_snapshot(self) -> None:
        if not self._page_ready:
            return
        mem = self._memory_count()
        history = self._memory_history_series()

        keys = _read_api_keys()
        llms = build_llm_rows(keys)
        connected = sum(1 for r in llms if r["on"])
        agents = build_agent_rows()
        running = sum(1 for a in agents if a["active"])

        voice = ("Muted" if self.muted else
                 "Offline" if self._mic_down else
                 "Online")

        try:
            import hud_sensors as S
            user = S.username()
        except Exception:
            import getpass
            user = getpass.getuser()

        initials = "".join(part[0] for part in str(user).split()[:2]).upper() or "OP"
        self._call("setUser", initials, str(user))

        snapshot = {
            "core": {
                "version": APP_VERSION,
                "sub": self._core_sub(),
                "memory": f"{mem:,} Stored",
                "voice": voice,
                "agents": f"{running} Running",
                "llms": f"{connected} Connected",
                "system": self._system_word(),
            },
            "memory": {
                "memories": f"{mem:,}",
                "turns": self._turn_count(),
                "cost": f"${self._cost:.2f}",
                "history": history,
            },
            "llms": llms,
            "agents": agents,
            "badges": {
                "tasks": len(self._timeline),
                "conversations": self._conversation_count(),
                "tools": len(llms) + 1,
            },
            "footer": {
                # Only a real reading is sent. Until the weather tool has
                # reported, the design's own placeholder text is left alone
                # rather than being overwritten with a hostname.
                "location": self._location,
                "weather": self._weather,
                "temp": self._temp if self._weather else None,
                "icon": self._weather_icon if self._weather else None,
                "network": self._network or "Unknown",
            },
            "level": round(self._level, 3),
        }
        self._apply(snapshot)

    def _core_sub(self) -> str:
        if self._task is not None:
            return str(self._task.get("status") or self._task.get("command") or "WORKING")[:24].upper()
        return self._states_sent if self._states_sent != "IDLE" else "AI CORE"

    def _system_word(self) -> str:
        cpu = self._last_cpu[0]
        return "Optimal" if cpu < 75 else "Busy" if cpu < 90 else "Under Load"

    # -- setters used by the assistant ---------------------------------
    def set_location(self, location: str) -> None:
        self._location = str(location or "")

    def set_weather(self, description: str, temp=None, icon: str = "☀") -> None:
        self._weather = str(description or "")
        self._temp = "--" if temp is None else str(temp)
        self._weather_icon = icon or "☀"

    def set_network(self, label: str) -> None:
        self._network = str(label or "Unknown")

    def add_cost(self, amount: float) -> None:
        try:
            self._cost += float(amount or 0.0)
        except (TypeError, ValueError):
            pass


# ---------------------------------------------------------------------------
# Backwards-compatible name used across the app
# ---------------------------------------------------------------------------
class JarvisUI(CommandCenter):
    """Same object as before; the name ``main.py`` imports."""
