"""
Real content for the Command Center's clickable surfaces.

Every visible control in ``assets/command_center/index.html`` is wired to one
of the views here. The page is not modified: a click travels
``element -> pybridge.viewRequested(id, payload) -> open_view()`` and the
resulting panel is drawn in a native Qt drawer floating *over* the web view.
That keeps the operator's design byte-for-byte intact while giving every
button, card, gauge, badge and nav link something real behind it.

Nothing in here is mocked. Counts come from the memory database, the
conversation store, the Obsidian vault, the plugin manager and
``hud_sensors``; navigation and tool lists come from the live declarations in
``main.py``.
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path

from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSizePolicy,
    QTextBrowser, QVBoxLayout, QWidget,
)

BASE_DIR = Path(__file__).resolve().parent

# Matches the page's own palette so the drawers read as part of the design
# rather than as a foreign window pasted on top of it.
PANEL_CSS = """
QFrame#drawer{ background:#0d1526; border-left:1px solid #1c2c45; }
QLabel#title{ color:#eafcff; font:700 13px 'Rajdhani'; letter-spacing:2px; }
QLabel#sub{ color:#5f7691; font:11px 'Rajdhani'; }
QPushButton#close{ background:#0f1a2c; border:1px solid #1c2c45; border-radius:8px;
                   color:#cfe8f2; font:700 12px 'Rajdhani'; padding:2px 10px; }
QPushButton#close:hover{ border-color:#22e6ff; color:#22e6ff; }
QTextBrowser{ background:transparent; border:none; color:#cfe8f2;
              font:12.5px 'Rajdhani'; }
QLineEdit{ background:#0d1626; border:1px solid #1c2c45; border-radius:8px;
           color:#cfe8f2; padding:9px 12px; font:13px 'Rajdhani'; }
QLineEdit:focus{ border-color:#22e6ff; }
QPushButton#send{ background:#0f1a2c; border:1px solid #22e6ff; border-radius:8px;
                  color:#22e6ff; font:700 11px 'Rajdhani'; letter-spacing:1px;
                  padding:9px 18px; }
QPushButton#send:hover{ background:#22e6ff; color:#071018; }
QPushButton#side{ background:#0a1424; border:1px solid #1c2c45; border-radius:8px;
                  color:#cfe8f2; font:600 11px 'Rajdhani'; padding:6px 12px; }
QPushButton#side:hover{ border-color:#22e6ff; color:#22e6ff; }
QScrollBar:vertical{ background:transparent; width:8px; margin:0; }
QScrollBar::handle:vertical{ background:#1c2c45; border-radius:4px; min-height:24px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical{ height:0; }
"""


def human(n) -> str:
    try:
        n = float(n or 0)
    except (TypeError, ValueError):
        return "?"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024.0:
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024.0
    return f"{n:.1f}PB"


def _pair(label: str, value: str, label_colour: str = "#cfe8f2",
          value_colour: str | None = None) -> str:
    """One label/value line.

    Qt's rich-text engine has no flexbox, so a display:flex row collapses and
    the label runs straight into the value. A two-cell table is the reliable
    way to get the same look inside QTextBrowser.
    """
    colour = value_colour or label_colour
    return (f'<tr><td style="color:{label_colour};padding:4px 16px 4px 0;'
            f'vertical-align:top;">{_esc(label)}</td>'
            f'<td style="color:{colour};padding:4px 0;'
            f'vertical-align:top;">{_esc(value)}</td></tr>')


def _esc(text) -> str:
    return (str(text if text is not None else "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _row(label: str, value: str) -> str:
    return (f'<tr><td style="color:#5f7691;padding:3px 14px 3px 0;'
            f'vertical-align:top;white-space:nowrap;">{_esc(label)}</td>'
            f'<td style="padding:3px 0;">{value}</td></tr>')


def _link(view: str, payload: str, text: str) -> str:
    return (f'<a href="jarvis://{_esc(view)}?{_esc(payload)}" '
            f'style="color:#22e6ff;text-decoration:none;">{_esc(text)}</a>')


def _command(text: str) -> str:
    return (f'<a href="jarvis://say?{_esc(text)}" '
            f'style="color:#22e6ff;text-decoration:none;">{_esc(text)}</a>')


def _open_path(path: str) -> str:
    return (f'<a href="jarvis://open?{_esc(path)}" '
            f'style="color:#22e6ff;text-decoration:none;">{_esc(path)}</a>')


# ---------------------------------------------------------------------------
# Real data collectors
# ---------------------------------------------------------------------------
def _memory_facts() -> dict:
    try:
        from memory.memory_manager import load_memory
        data = load_memory() or {}
        if isinstance(data, dict):
            out = {}
            for cat, items in data.items():
                out[cat] = len(items) if isinstance(items, (list, dict, set)) else 1
            return out
    except Exception:
        pass
    return {}


def _conversations() -> list[dict]:
    try:
        from workspace_store import workspace_store
        return workspace_store().list_conversations() or []
    except Exception:
        return []


def _vault_files() -> list[dict]:
    try:
        import obsidian_integration as obs
        return obs.obsidian_list_files() or []
    except Exception:
        return []


def _plugins() -> list:
    try:
        from plugin_manager import PluginManager
        return list(getattr(PluginManager(BASE_DIR), "plugins", []) or [])
    except Exception:
        return []


def _tool_names() -> list[str]:
    """The tools the live session actually advertises.

    ``TOOL_DECLARATIONS`` is a *list* of dicts, so reading it as a mapping
    returned nothing and the Tools panel showed an empty list.
    """
    try:
        import main
        decls = getattr(main, "TOOL_DECLARATIONS", None) or []
        names = [d["name"] for d in decls
                 if isinstance(d, dict) and d.get("name")]
        if names:
            return names
    except Exception:
        pass
    try:
        import ast
        tree = ast.parse((BASE_DIR / "main.py").read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and any(
                    getattr(t, "id", "") == "TOOL_DECLARATIONS"
                    for t in node.targets):
                out = []
                for element in getattr(node.value, "elts", []) or []:
                    try:
                        decl = ast.literal_eval(element)
                        if isinstance(decl, dict) and decl.get("name"):
                            out.append(decl["name"])
                    except Exception:
                        continue
                if out:
                    return out
    except Exception:
        pass
    return []


def _action_modules() -> list[str]:
    actions = BASE_DIR / "actions"
    if not actions.is_dir():
        return []
    return sorted(p.stem for p in actions.glob("*.py")
                  if not p.stem.startswith("_"))


def _reminders() -> list[dict]:
    """Reminders Jarvis has set, plus anything queued with ``at``."""
    items: list[dict] = []
    store = BASE_DIR / "config" / "reminders.json"
    try:
        if store.is_file():
            for row in json.loads(store.read_text(encoding="utf-8")):
                items.append({"when": row.get("when", ""), "text": row.get("text", ""),
                              "source": "Jarvis"})
    except Exception:
        pass
    try:
        out = subprocess.run(["atq"], capture_output=True, text=True, timeout=2)
        for line in (out.stdout or "").splitlines():
            line = line.strip()
            if line:
                items.append({"when": line.split()[0], "text": " ".join(line.split()[1:]),
                              "source": "at"})
    except Exception:
        pass
    return items


def _attention_log() -> list[dict]:
    path = BASE_DIR / "config" / "attention_log.json"
    try:
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))[-60:]
    except Exception:
        pass
    return []


def _sensors() -> dict:
    out: dict = {}
    try:
        import hud_sensors as S
        for name in ("host_summary", "temperatures", "net_mbps", "ip_address",
                     "active_adapter", "uptime_human", "battery", "load_average"):
            try:
                out[name] = getattr(S, name)()
            except Exception:
                pass
    except Exception:
        pass
    return out


# ---------------------------------------------------------------------------
# The drawer
# ---------------------------------------------------------------------------
class PanelDrawer(QFrame):
    """A right-hand overlay. Floats above the web view; the page is untouched."""

    closed = pyqtSignal()
    action = pyqtSignal(str, str)          # kind, payload

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("drawer")
        self.setStyleSheet(PANEL_CSS)
        self.setFixedWidth(520)

        head = QHBoxLayout()
        head.setContentsMargins(16, 14, 12, 8)
        self._title = QLabel("JARVIS")
        self._title.setObjectName("title")
        self._sub = QLabel("")
        self._sub.setObjectName("sub")
        close = QPushButton("✕")
        close.setObjectName("close")
        close.clicked.connect(self.close_panel)
        head.addWidget(self._title)
        head.addStretch(1)
        head.addWidget(close)

        self.body = QTextBrowser()
        self.body.setOpenLinks(False)
        self.body.setOpenExternalLinks(False)
        self.body.anchorClicked.connect(self._on_anchor)
        self.body.setSizePolicy(QSizePolicy.Policy.Expanding,
                                QSizePolicy.Policy.Expanding)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addLayout(head)
        lay.addWidget(self._sub)
        lay.addWidget(self.body, 1)
        self.hide()

    # -- navigation ----------------------------------------------------
    def _on_anchor(self, url: QUrl) -> None:
        """Handle jarvis://view?payload links inside the panel."""
        raw = url.toString()
        if not raw.startswith("jarvis://"):
            return
        rest = raw[len("jarvis://"):]
        view, _, payload = rest.partition("?")
        if view == "say":
            self.action.emit("say", payload)
        elif view == "open":
            self.action.emit("open", payload)
        else:
            self.action.emit("view", f"{view}?{payload}" if payload else view)

    def show_view(self, title: str, sub: str, html: str) -> None:
        self._title.setText(title)
        self._sub.setText(f"  {sub}" if sub else "")
        self.body.setHtml(html)
        self.show()
        self.raise_()
        parent = self.parentWidget()
        if parent is not None:
            self.setFixedHeight(parent.height())
            self.move(parent.width() - self.width(), 0)

    def close_panel(self) -> None:
        self.hide()
        self.closed.emit()


class ChatDrawer(QFrame):
    """A text channel to Jarvis, docked over the page so the design is intact."""

    submitted = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("drawer")
        self.setStyleSheet(PANEL_CSS)
        self.setFixedWidth(520)

        head = QHBoxLayout()
        head.setContentsMargins(16, 14, 12, 8)
        title = QLabel("CHAT WITH JARVIS")
        title.setObjectName("title")
        hint = QLabel("  Enter sends · Shift+Enter newline")
        hint.setObjectName("sub")
        close = QPushButton("✕")
        close.setObjectName("close")
        close.clicked.connect(self.close_panel)
        head.addWidget(title)
        head.addWidget(hint)
        head.addStretch(1)
        head.addWidget(close)

        self.log = QTextBrowser()
        self.log.setOpenLinks(False)

        row = QHBoxLayout()
        row.setContentsMargins(16, 6, 16, 14)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Type a message or a command…")
        self.input.returnPressed.connect(self._send)
        send = QPushButton("SEND")
        send.setObjectName("send")
        send.clicked.connect(self._send)
        row.addWidget(self.input, 1)
        row.addWidget(send)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addLayout(head)
        lay.addWidget(self.log, 1)
        lay.addLayout(row)
        self.hide()

    def _send(self) -> None:
        text = self.input.text().strip()
        if not text:
            return
        self.input.clear()
        self.append("you", text)
        self.submitted.emit(text)

    def append(self, who: str, text: str) -> None:
        colour = {"you": "#22e6ff", "jarvis": "#cfe8f2",
                  "sys": "#ffb020", "err": "#ff4d6d"}.get(who, "#cfe8f2")
        label = {"you": "You", "jarvis": "Jarvis", "sys": "System",
                 "err": "Error"}.get(who, who)
        stamp = datetime.now().strftime("%H:%M")
        self.log.append(
            f'<div style="margin:2px 0;"><span style="color:#5f7691;">{stamp}</span> '
            f'<span style="color:{colour};font-weight:700;">{label}</span><br>'
            f'<span style="color:{colour};">{_esc(text)}</span></div>')
        sb = self.log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def show_panel(self) -> None:
        self.show()
        self.raise_()
        parent = self.parentWidget()
        if parent is not None:
            self.setFixedHeight(parent.height())
            self.move(parent.width() - self.width(), 0)
        self.input.setFocus()

    def close_panel(self) -> None:
        self.hide()


# ---------------------------------------------------------------------------
# View builders
# ---------------------------------------------------------------------------
# Each returns (title, subtitle, html). ``view_id`` is the string the page
# sends, optionally "name?payload".
def _v_ai_core(ctx) -> tuple:
    s = _sensors()
    host = s.get("host_summary") or {}
    keys = _api_keys_present()
    uptime = host.get("uptime") or "—"
    load = host.get("load")
    load_s = " · ".join(f"{v:.2f}" for v in load) if load else "—"
    rows = [
        _row("Version", "8.0.0"),
        _row("State", _esc(ctx.get("state", "IDLE"))),
        _row("Host", _esc(f"{host.get('host','—')} · {host.get('user','—')}")),
        _row("Uptime", _esc(uptime)),
        _row("Load average", _esc(load_s)),
        _row("CPU", _esc(f"{(host.get('cpu_mhz') or 0) / 1000:.1f} GHz · "
                         f"{host.get('cpu_pct', '—')}%")),
        _row("GPU", _esc((host.get("gpu") or {}).get("name", "—"))),
        _row("Voice", "online" if not ctx.get("mic_down") else "listening for mic"),
        _row("Memory facts", f"{sum(_memory_facts().values())} across "
                             f"{len(_memory_facts())} categories"),
        _row("Conversations", str(len(_conversations()))),
        _row("Vault files", str(len(_vault_files()))),
    ]
    if s.get("battery"):
        b = s["battery"]
        rows.append(_row("Battery", _esc(f"{b.get('percent','—')}% "
                                         f"{'charging' if b.get('charging') else ''}")))
    providers = "".join(
        f'<span style="color:{"#39ffb0" if v else "#5f7691"};">'
        f'{_esc(k.replace("_api_key","").replace("_token","").replace("_key",""))}</span>  '
        for k, v in keys.items())
    html = (f'<p style="color:#5f7691;margin:0 0 10px;">Providers with a key configured</p>'
            f'<div style="line-height:1.9;">{providers}</div>'
            f'<hr style="border:none;border-top:1px solid #142238;margin:14px 0;">'
            f'<table cellspacing="0" cellpadding="0">{"".join(rows)}</table>')
    return "AI CORE", "live session detail", html


def _api_keys_present() -> dict:
    out = {}
    try:
        path = BASE_DIR / "config" / "api_keys.json"
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            for k, v in data.items():
                if isinstance(v, str) and v.strip():
                    out[k] = True
    except Exception:
        pass
    return out


def _v_agents(ctx) -> tuple:
    """The real agent registry, with live status -- not a static list."""
    import command_bridge as CB
    rows = CB.build_agent_rows()
    real = [r for r in rows if r.get("real")]
    if not real:
        return "AGENTS", "agent system not running", (
            '<p style="color:#5f7691;">The agent system is not running. '
            'Start JARVIS to bring up the Research, Document and Code agents.</p>')

    try:
        import agent_runtime as AR
        stats = AR.registry_stats()
        live = AR.registry()
        goal = AR.progress().get("goal", "")
    except Exception:
        stats, live, goal = {}, [], ""

    cards = []
    for row in rows:
        if row.get("active"):
            colour, label = "#39ffb0", row.get("status", "Working")
        elif row.get("real"):
            colour, label = "#5f7691", row.get("status", "Standby")
        else:
            colour, label = "#ffb020", "not registered"
        note = str(row.get("task") or row.get("detail") or "")[:70]
        # A table, because Qt's rich-text engine ignores div borders and
        # padding; the name links through to the agent's own page.
        cards.append(
            f'<tr><td style="color:{colour};padding:4px 16px 4px 0;'
            f'vertical-align:top;">{_link("agent", row["name"], row["name"])}'
            f' &nbsp;<span style="font-size:10px;">{_esc(label)}</span></td>'
            f'<td style="color:#5f7691;padding:4px 0;">{_esc(note)}</td></tr>')

    head = ""
    if goal:
        head = (f'<p style="color:#22e6ff;font-weight:700;">'
                f'Working on: {_esc(goal[:120])}</p>')
    working = sum(1 for a in live if a.get("status") in ("running", "starting"))
    summary = (f'<p style="color:#5f7691;">'
               f'{stats.get("total", 0)} registered · {working} working · '
               f'{_link("agent_status", "", "ask what they are doing")}</p>')
    return "AGENTS", f"{len(real)} agents registered", (
        head + "<table cellspacing=0 cellpadding=0 width='100%'>"
        + "".join(cards) + "</table>" + summary)


def _v_agent(ctx, payload) -> tuple:
    """One agent's live detail from the registry."""
    import command_bridge as CB
    row = next((a for a in CB.build_agent_rows() if a["name"] == payload), None)
    if not row:
        return "AGENT", "", '<p style="color:#5f7691;">Unknown agent.</p>'

    detail = ""
    try:
        import agent_runtime as AR
        wanted = payload.split()[0].lower()          # "Research" -> "research"
        live = next((a for a in AR.registry()
                     if a.get("type", "").startswith(wanted[:6])), None)
        if live:
            detail = (f'{_row("Class", _esc(live["name"]))}'
                      f'{_row("Type", _esc(live["type"]))}'
                      f'{_row("Status", _esc(live["status"]))}'
                      f'{_row("Current task", _esc(str(live.get("current_task") or "—")))}')
    except Exception:
        pass

    if not detail:
        detail = _row("Status", _esc(row.get("status", "Standby")))
        if not row.get("real"):
            detail += _row("Note", "not registered")

    return row["name"], row.get("status", ""), (
        f'<table cellspacing="0" cellpadding="0">{detail}</table>'
        f'<p style="margin-top:16px;">'
        f'{_command(f"delegate a task to the {payload}")}</p>')


def _v_tasks(ctx) -> tuple:
    task = ctx.get("task")
    items = []
    if task:
        steps = task.get("steps") or []
        for i, s in enumerate(steps):
            items.append(f'<li>{_esc(s)}</li>')
        body = (f'<p style="color:#22e6ff;font-weight:700;">{_esc(task.get("command",""))}</p>'
                f'<p style="color:#5f7691;">{_esc(task.get("status",""))} · '
                f'{task.get("percent",0)}%</p><ol style="color:#cfe8f2;">'
                f'{"".join(items)}</ol>')
    else:
        body = '<p style="color:#5f7691;">No task running.</p>'
    rem = _reminders()
    rem_html = "".join(
        f'<div style="border-bottom:1px solid #142238;padding:6px 0;">'
        f'<b style="color:#22e6ff;">{_esc(r["when"])}</b> {_esc(r["text"])}</div>'
        for r in rem) or '<p style="color:#5f7691;">No reminders set.</p>'
    return "TASKS", "active work and reminders", (
        body + '<hr style="border:none;border-top:1px solid #142238;margin:14px 0;">'
        f'<p style="color:#5f7691;">REMINDERS</p>{rem_html}'
        f'<p style="margin-top:16px;">'
        f'{_link("new_task", "", "＋ Start a new task")} &nbsp; '
        f'{_command("what reminders do I have?")}</p>')


def _v_calendar(ctx) -> tuple:
    rem = _reminders()
    now = datetime.now()
    rows = [("Today", now.strftime("%A, %d %B %Y")),
            ("Tomorrow", (now + timedelta(days=1)).strftime("%A, %d %B %Y"))]
    cal = "".join(f'{_row(k, _esc(v))}' for k, v in rows)
    items = "".join(
        f'<div style="border-bottom:1px solid #142238;padding:7px 0;">'
        f'<b style="color:#22e6ff;">{_esc(r["when"])}</b> {esc_str(r["text"])}</div>'
        for r in rem) or '<p style="color:#5f7691;">Nothing scheduled.</p>'
    return "CALENDAR", now.strftime("%H:%M"), (
        f'<table cellspacing="0" cellpadding="0">{cal}</table>'
        f'<hr style="border:none;border-top:1px solid #142238;margin:14px 0;">'
        f'<p style="color:#5f7691;">SCHEDULED</p>{items}'
        f'<p style="margin-top:16px;">{_command("remind me to stretch in 20 minutes")}'
        f' &nbsp; {_link("schedule", "", "Full schedule")}</p>')


def esc_str(text) -> str:
    return _esc(text)


def _v_conversations(ctx) -> tuple:
    convs = _conversations()
    if convs:
        rows = []
        for c in convs[:60]:
            title = c.get("title") or "(untitled)"
            when = (c.get("updated_at") or c.get("created_at") or "")[:16]
            rows.append(
                f'<div style="border-bottom:1px solid #142238;padding:8px 0;">'
                f'{_link("conversation", str(c.get("id", "")), title)}'
                f'<div style="color:#5f7691;font-size:11px;">{_esc(when)} · '
                f'{c.get("message_count", "?")} messages</div></div>')
        return "CONVERSATIONS", f"{len(convs)} stored", "".join(rows)

    # The conversation store can be empty on a fresh install while the
    # markdown history already holds every session, so fall back to it rather
    # than showing an empty panel.
    try:
        from chat_history_manager import list_days
        days = list_days()
    except Exception:
        days = []
    if not days:
        return "CONVERSATIONS", "none stored", \
            '<p style="color:#5f7691;">No conversations yet.</p>'
    rows = "".join(
        f'<div style="border-bottom:1px solid #142238;padding:8px 0;">'
        f'{_link("chatday", d, d)}'
        f'<div style="color:#5f7691;font-size:11px;">'
        f'{_esc(chat_day_title(d))}</div></div>' for d in days)
    return "CONVERSATIONS", f"{len(days)} logged days", rows


def chat_day_title(day: str) -> str:
    try:
        from chat_history_manager import get_day
        first = (get_day(day) or "").strip().splitlines()
        return (first[0].lstrip("# ").strip() if first else day)[:60]
    except Exception:
        return day


def _v_chatday(ctx, payload) -> tuple:
    try:
        from chat_history_manager import get_day
        body = get_day(payload) or ""
    except Exception:
        body = ""
    if not body.strip():
        return "CONVERSATION", payload, \
            '<p style="color:#5f7691;">Nothing logged for that day.</p>'
    out = []
    for line in body.splitlines():
        line = line.rstrip()
        if line.startswith("**You:**"):
            out.append(f'<div style="margin:7px 0;">'
                       f'<b style="color:#22e6ff;">You</b><br>'
                       f'{_esc(line[9:].strip())}</div>')
        elif line.startswith("**Jarvis:**"):
            out.append(f'<div style="margin:7px 0;">'
                       f'<b style="color:#cfe8f2;">Jarvis</b><br>'
                       f'{_esc(line[11:].strip())}</div>')
        elif line.startswith("## "):
            out.append(f'<p style="color:#5f7691;margin:10px 0 2px;">'
                       f'{_esc(line[3:].strip())}</p>')
    return "CONVERSATION", payload, "".join(out) or \
        '<p style="color:#5f7691;">Nothing logged for that day.</p>'


def _v_conversation(ctx, payload) -> tuple:
    conv = next((c for c in _conversations() if str(c.get("id")) == payload), None)
    if not conv:
        return _v_chatday(ctx, payload)
    parts = [f'<p style="color:#22e6ff;font-weight:700;">'
             f'{_esc(conv.get("title") or "(untitled)")}</p>']
    for msg in (conv.get("messages") or [])[-60:]:
        role = msg.get("role", "?")
        colour = "#22e6ff" if role in ("user", "You") else "#cfe8f2"
        parts.append(f'<div style="margin:6px 0;"><b style="color:{colour};">'
                     f'{_esc(role)}</b><br>{_esc(msg.get("content", ""))}</div>')
    if len(parts) == 1:
        parts.append('<p style="color:#5f7691;">No messages recorded.</p>')
    return "CONVERSATION", (conv.get("title") or "")[:40], "".join(parts)


def _v_memory(ctx) -> tuple:
    facts = _memory_facts()
    if not facts:
        return "MEMORY", "empty", '<p style="color:#5f7691;">No memories stored.</p>'
    total = sum(facts.values())
    rows = "<table cellspacing=0 cellpadding=0 width='100%'>" + "".join(
        _pair(cat, n, "#7c5cff", "#5f7691")
        for cat, n in sorted(facts.items(), key=lambda kv: -kv[1])) + "</table>"
    return "MEMORY", f"{total} facts in {len(facts)} categories", (
        f'<p style="color:#5f7691;">Largest categories</p>{rows}'
        f'<p style="margin-top:16px;">{_command("what do you remember about me?")}'
        f' &nbsp; {_link("knowledge", "", "Knowledge base")}</p>')


def _v_knowledge(ctx) -> tuple:
    files = _vault_files()
    if not files:
        return "KNOWLEDGE BASE", "vault not found", \
            '<p style="color:#5f7691;">No Obsidian vault found.</p>'
    groups: dict[str, int] = {}
    for f in files:
        folder = (f.get("folder") or "/").strip("/").split("/")[0] or "root"
        groups[folder] = groups.get(folder, 0) + 1
    rows = "<table cellspacing=0 cellpadding=0 width='100%'>" + "".join(
        _pair(name, n, "#22e6ff", "#5f7691")
        for name, n in sorted(groups.items(), key=lambda kv: -kv[1])) + "</table>"
    recent = "".join(
        f'<div style="border-bottom:1px solid #142238;padding:6px 0;">'
        f'{_esc(f.get("name") or f.get("path"))}</div>'
        for f in sorted(files, key=lambda f: str(f.get("modified", "")),
                        reverse=True)[:15])
    vault = Path.home() / ".obsidian-vault"
    return "KNOWLEDGE BASE", f"{len(files)} notes", (
        f'<p style="color:#5f7691;">By folder</p>{rows}'
        f'<hr style="border:none;border-top:1px solid #142238;margin:12px 0;">'
        f'<p style="color:#5f7691;">RECENTLY MODIFIED</p>{recent}'
        f'<p style="margin-top:16px;">{_open_path(str(vault))}</p>')


def _v_tools(ctx) -> tuple:
    tools = _tool_names()
    mods = _action_modules()
    t_rows = "".join(
        f'<div style="border-bottom:1px solid #142238;padding:5px 0;">'
        f'<span style="color:#22e6ff;">{_esc(t)}</span></div>' for t in tools)
    m_rows = "".join(
        f'<div style="border-bottom:1px solid #142238;padding:5px 0;">'
        f'{_link("workflow", m, m)}</div>' for m in mods)
    return "TOOLS & SKILLS", f"{len(tools)} tools · {len(mods)} skills", (
        f'<p style="color:#5f7691;">TOOLS THE ASSISTANT CAN CALL</p>{t_rows}'
        f'<hr style="border:none;border-top:1px solid #142238;margin:12px 0;">'
        f'<p style="color:#5f7691;">SKILL MODULES — CLICK TO RUN</p>{m_rows}')


def _v_workflow(ctx, payload) -> tuple:
    mod = (payload or "").strip()
    path = BASE_DIR / "actions" / f"{mod}.py"
    doc = ""
    if path.is_file():
        try:
            import ast
            tree = ast.parse(path.read_text(encoding="utf-8"))
            doc = (ast.get_docstring(tree) or "").strip()
        except Exception:
            doc = ""
    fns = []
    if path.is_file():
        try:
            import ast
            tree = ast.parse(path.read_text(encoding="utf-8"))
            fns = [n.name for n in tree.body
                   if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                   and not n.name.startswith("_")][:20]
        except Exception:
            fns = []
    body = f'<p style="color:#cfe8f2;">{_esc(doc[:600])}</p>' if doc else \
        '<p style="color:#5f7691;">No module documentation.</p>'
    fn_list = "".join(f'<li style="color:#7c8ea3;">{_esc(f)}</li>' for f in fns)
    return f"SKILL · {mod.upper()}", path.name, (
        f'{body}<ul style="color:#7c8ea3;">{fn_list}</ul>'
        f'<p style="margin-top:16px;">'
        f'{_command(f"use the {mod} skill")}</p>')


def _v_workflows(ctx) -> tuple:
    mods = _action_modules()
    rows = "".join(
        f'<div style="border-bottom:1px solid #142238;padding:6px 0;">'
        f'{_link("workflow", m, m)}</div>' for m in mods)
    return "WORKFLOWS", f"{len(mods)} skills you can chain", (
        f'<p style="color:#5f7691;">Pick a skill to inspect or run it through Jarvis.</p>'
        f'{rows}')


def _v_monitor(ctx) -> tuple:
    s = _sensors()
    host = s.get("host_summary") or {}
    temps = s.get("temperatures") or []
    t_rows = "".join(
        _pair(t.get("label", t.get("chip", "sensor")),
              f'{t.get("celsius", "—")}°C', "#cfe8f2",
              "#ff4d6d" if (t.get("celsius") or 0) > 80 else "#22e6ff")
        for t in temps)
    net = s.get("net_mbps")
    mem = host.get("mem") or {}
    disk = host.get("disk") or {}
    gpu = host.get("gpu") or {}
    cpu_temp = (host.get("temp") or {}).get("celsius")
    rows = [
        _row("Host", _esc(host.get("host", "—"))),
        _row("User", _esc(host.get("user", "—"))),
        _row("CPU", _esc(f"{(host.get('cpu_mhz') or 0) / 1000:.2f} GHz")),
        _row("CPU load", _esc(f"{host.get('cpu_pct', '—')}%")),
        _row("Package temp", _esc(f"{cpu_temp}°C" if cpu_temp is not None else "—")),
        _row("Memory", _esc(f"{mem.get('percent', '—')}%  "
                            f"({human(mem.get('used'))} / {human(mem.get('total'))})")),
        _row("Disk", _esc(f"{disk.get('percent', '—')}%  "
                          f"({human(disk.get('used'))} / {human(disk.get('total'))})")),
        _row("GPU", _esc(f"{gpu.get('name', '—')}"
                         + (f" · {gpu['util']}%" if gpu.get("util") is not None else ""))),
        _row("Address", _esc(host.get("ip", "—"))),
        _row("Adapter", _esc(host.get("adapter", "—"))),
        _row("Throughput", _esc(f"{net} Mb/s" if net is not None else "—")),
        _row("Uptime", _esc(host.get("uptime", "—"))),
    ]
    return "SYSTEM MONITOR", "live telemetry", (
        f'<table cellspacing="0" cellpadding="0">{"".join(rows)}</table>'
        f'<hr style="border:none;border-top:1px solid #142238;margin:12px 0;">'
        f'<p style="color:#5f7691;">TEMPERATURES</p>{t_rows or "<p>No sensors.</p>"}')


def _v_notifications(ctx) -> tuple:
    log = ctx.get("attention") or _attention_log()
    if not log:
        return "NOTIFICATIONS", "none yet", (
            '<p style="color:#5f7691;">No notifications have arrived yet.</p>'
            f'<p style="margin-top:12px;">'
            f'{_command("what are my current notifications")}</p>')
    rows = "".join(
        f'<div style="border-bottom:1px solid #142238;padding:6px 0;">'
        f'<span style="color:#ffb020;">{_esc(e.get("app", "app"))}</span> '
        f'{_esc(e.get("title", ""))}'
        f'<div style="color:#5f7691;font-size:11px;">{_esc(e.get("preview", ""))}</div>'
        f'</div>' for e in reversed(log))
    return "NOTIFICATIONS", f"{len(log)} received", rows


def _v_providers(ctx) -> tuple:
    import command_bridge as CB
    rows = CB.build_llm_rows(_api_keys_present())
    body = ["<table cellspacing=0 cellpadding=0 width='100%'>"]
    for r in rows:
        colour = "#39ffb0" if r["on"] else "#5f7691"
        body.append(_pair(r["name"], r["state"], "#eafcff", colour))
    keys_path = BASE_DIR / "config" / "api_keys.json"
    body.append("</table>")
    return "PROVIDERS", f"{sum(1 for r in rows if r['on'])} of {len(rows)} connected", (
        "".join(body)
        + f'<p style="margin-top:16px;">Keys live in '
          f'{_open_path(str(keys_path))}</p>'
          f'<p style="color:#5f7691;">Add a key there and restart; the panel '
          f'picks it up on the next poll.</p>')


def _v_settings(ctx) -> tuple:
    import main as M
    rows = [
        _row("Mic", _esc(f"device {M._MIC_DEVICE}")),
        _row("Speaker", _esc(f"device {M._SPEAKER_DEVICE}")),
        _row("Sample floor", _esc(str(getattr(M, "_RMS_FLOOR", "—")))),
        _row("Echo guard", _esc(f"{getattr(M, '_ECHO_GUARD_MS', '—')} ms tail")),
        _row("Command center", _open_path(str(BASE_DIR / "assets" /
                                             "command_center" / "index.html"))),
        _row("Vault", _open_path(str(Path.home() / ".obsidian-vault"))),
    ]
    override = os.environ.get("JARVIS_MIC_DEVICE", "")
    if override:
        rows.append(_row("Mic override", _esc(override)))
    return "SETTINGS", "audio and files", (
        f'<table cellspacing="0" cellpadding="0">{"".join(rows)}</table>'
        f'<p style="margin-top:16px;">{_command("open developer mode")}</p>')


def _v_profile(ctx) -> tuple:
    s = _sensors()
    try:
        import getpass
        user = getpass.getuser()
    except Exception:
        user = "operator"
    return "OPERATOR", user, (
        f'<table cellspacing="0" cellpadding="0">'
        f'{_row("User", _esc(user))}'
        f'{_row("Host", _esc((s.get("host_summary") or {}).get("host", "—")))}'
        f'{_row("Conversations", str(len(_conversations())))}'
        f'{_row("Memories", str(sum(_memory_facts().values())))}'
        f'{_row("Vault notes", str(len(_vault_files())))}'
        f'{_row("Reminders", str(len(_reminders())))}'
        f'</table>')


def _v_schedule(ctx) -> tuple:
    rem = _reminders()
    convs = _conversations()[:10]
    rem_html = "".join(
        f'<div style="border-bottom:1px solid #142238;padding:6px 0;">'
        f'<b style="color:#22e6ff;">{_esc(r["when"])}</b> {esc_str(r["text"])}</div>'
        for r in rem) or '<p style="color:#5f7691;">No reminders.</p>'
    conv_html = "".join(
        f'<div style="border-bottom:1px solid #142238;padding:6px 0;">'
        f'{_link("conversation", str(c.get("id","")), c.get("title") or "(untitled)")}'
        f'</div>' for c in convs)
    return "SCHEDULE", "everything scheduled", (
        f'<p style="color:#5f7691;">REMINDERS</p>{rem_html}'
        f'<hr style="border:none;border-top:1px solid #142238;margin:12px 0;">'
        f'<p style="color:#5f7691;">RECENT CONVERSATIONS</p>{conv_html}')


def _v_events(ctx) -> tuple:
    feed = ctx.get("feed") or []
    if not feed:
        return "ACTIVITY", "nothing yet", '<p style="color:#5f7691;">No activity yet.</p>'
    rows = "".join(
        f'<div style="border-bottom:1px solid #142238;padding:6px 0;">'
        f'{_esc(i.get("title",""))}'
        f'<div style="color:#5f7691;font-size:11px;">'
        f'{_esc(i.get("tagText",""))} · {_esc(i.get("meta",""))}</div></div>'
        for i in feed)
    return "ACTIVITY", f"{len(feed)} entries", rows


def _v_gauge(ctx, payload) -> tuple:
    import command_bridge as CB
    s = _sensors()
    host = s.get("host_summary") or {}
    label = (payload or "").strip() or "CPU"
    mem = host.get("mem") or {}
    disk = host.get("disk") or {}
    temp = (host.get("temp") or {}).get("celsius")
    if label.upper() == "RAM":
        detail = _row("Used", _esc(f"{mem.get('percent','—')}%"))
        extra = _row("Of", _esc(f"{human(mem.get('used'))} / {human(mem.get('total'))}"))
    elif label.upper() == "DISK":
        detail = _row("Used", _esc(f"{disk.get('percent','—')}%"))
        extra = _row("Of", _esc(f"{human(disk.get('used'))} / {human(disk.get('total'))}"))
    else:
        detail = _row("Load", _esc(f"{host.get('cpu_pct','—')}%"))
        extra = _row("Speed", _esc(f"{(host.get('cpu_mhz') or 0) / 1000:.2f} GHz"))
        if temp is not None:
            extra += _row("Package", _esc(f"{temp}°C"))
    return f"{label.upper()} · live", "system monitor", (
        f'<table cellspacing="0" cellpadding="0">{detail}{extra}</table>'
        f'<p style="margin-top:16px;">{_command(f"report the {label.lower()} usage")}</p>')


def _v_llm(ctx, payload) -> tuple:
    import command_bridge as CB
    row = next((r for r in CB.build_llm_rows(_api_keys_present())
                if r["name"] == payload), None)
    if not row:
        return "PROVIDER", "", '<p style="color:#5f7691;">Unknown provider.</p>'
    return row["name"], row["state"], (
        f'<table cellspacing="0" cellpadding="0">'
        f'{_row("Status", _esc(row["state"]))}'
        f'{_row("Role", "answer when the primary provider is unavailable")}'
        f'</table>'
        f'<p style="margin-top:16px;">'
        f'{_link("providers", "", "Manage providers")}</p>')


def _v_core_item(ctx, payload) -> tuple:
    name = (payload or "").strip()
    routes = {
        "AI Core": "ai_core", "Memory": "memory", "Voice": "settings",
        "Agents": "agents", "LLMs": "providers", "System": "monitor",
    }
    return build_view(routes.get(name, "ai_core"), ctx)


def _v_new_task(ctx) -> tuple:
    return "NEW TASK", "describe what you want done", (
        f'<p style="color:#cfe8f2;">Type the task below and press Enter. Jarvis '
        f'will plan it and run the steps.</p>'
        f'<p style="margin-top:14px;">'
        f'<a href="jarvis://newtask?prompt" '
        f'style="color:#22e6ff;">＋ Start typing a task…</a></p>'
        f'<p style="color:#5f7691;margin-top:16px;">Or just ask in the chat box — '
        f'every message becomes a task automatically.</p>')


def _v_agent_status(ctx) -> tuple:
    """What the team is doing right now -- Principle 9, on demand."""
    try:
        import agent_runtime as AR
    except Exception as exc:
        return "AGENT STATUS", "", f'<p style="color:#ff4d6d;">{_esc(exc)}</p>'
    AR.start()
    info = AR.progress()
    stats = info.get("stats") or {}
    rows = [
        _row("State", _esc(AR.status_text())),
        _row("Objective", _esc(info.get("goal") or "—")),
        _row("Registered", str(stats.get("total", 0))),
    ]
    for label, key in (("By status", "by_status"), ("By type", "by_type")):
        bucket = stats.get(key) or {}
        if bucket:
            rows.append(_row(label, _esc(", ".join(
                f"{k}: {v}" for k, v in sorted(bucket.items())))))
    body = f'<table cellspacing="0" cellpadding="0">{"".join(rows)}</table>'
    steps = info.get("steps") or []
    if steps:
        body += ('<hr style="border:none;border-top:1px solid #142238;margin:12px 0;">'
                 '<p style="color:#5f7691;">COMPLETED STEPS</p>'
                 '<ol style="color:#cfe8f2;">'
                 + "".join(f'<li>{_esc(s["text"])}</li>' for s in steps) + "</ol>")
    else:
        body += '<p style="color:#5f7691;">No steps have run yet.</p>'
    return "AGENT STATUS", "live team state", body


VIEWS = {
    "ai_core": _v_ai_core,
    "agents": _v_agents,
    "tasks": _v_tasks,
    "calendar": _v_calendar,
    "conversations": _v_conversations,
    "memory": _v_memory,
    "knowledge": _v_knowledge,
    "tools": _v_tools,
    "workflows": _v_workflows,
    "monitor": _v_monitor,
    "notifications": _v_notifications,
    "providers": _v_providers,
    "settings": _v_settings,
    "profile": _v_profile,
    "schedule": _v_schedule,
    "events": _v_events,
    "agent": _v_agent,
    "conversation": _v_conversation,
    "chatday": _v_chatday,
    "workflow": _v_workflow,
    "gauge": _v_gauge,
    "llm": _v_llm,
    "core": _v_core_item,
    "new_task": _v_new_task,
    "agent_status": _v_agent_status,
}


def build_view(request: str, ctx: dict) -> tuple:
    """Turn "name?payload" into (title, subtitle, html)."""
    view, _, payload = (request or "").partition("?")
    view = view.strip() or "ai_core"
    fn = VIEWS.get(view)
    if fn is None:
        return view.upper().replace("_", " "), "", \
            '<p style="color:#5f7691;">Nothing to show here yet.</p>'
    try:
        if fn.__code__.co_argcount == 2:
            return fn(ctx, payload)
        return fn(ctx)
    except Exception as exc:
        return view.upper(), "error", \
            f'<p style="color:#ff4d6d;">Could not build this view: {_esc(exc)}</p>'
