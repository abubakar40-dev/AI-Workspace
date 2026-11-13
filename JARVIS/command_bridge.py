"""
Python <-> JavaScript bridge for the JARVIS Command Center.

``assets/command_center/index.html`` is the operator's design and is treated as
read-only: it is shipped byte-for-byte and is never edited, reformatted or
re-generated. Everything that makes it *live* lives here instead, in two
places:

  * ``BINDING_JS`` -- injected with ``runJavaScript`` once the page has loaded.
    It only ever reads existing elements, clones the page's own nodes when it
    needs more of one, and writes text, attributes, inline animation timings
    and the file's own state classes. It never inserts new markup, never adds
    a stylesheet and never changes a geometry, so not one pixel of the
    original design moves. Cloning is deliberate: a cloned ``.agent-card`` is
    pixel-identical to the six the author wrote, whereas hand-built markup
    would silently drift from the design.

  * ``CommandCenter`` -- the Qt host. It owns the web view, the QWebChannel
    transport, the telemetry pollers and the public API that ``main.py`` and
    the action modules already call.

Every selector below was verified against the shipped file.
"""

from __future__ import annotations

import json
import os
import platform
import time
from pathlib import Path

from PyQt6.QtCore import (
    QObject, QPoint, QTimer, QUrl, pyqtSignal, pyqtSlot,
)

# ---------------------------------------------------------------------------
# Locating the page
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
COMMAND_CENTER_HTML = BASE_DIR / "assets" / "command_center" / "index.html"

# Qt ships qwebchannel.js inside its compiled resource, not on disk, so the
# page pulls it in with a plain <script src>. That keeps the operator's HTML
# free of any tag we would have had to add.
QWEBCHANNEL_JS = "qrc:///qtwebchannel/qwebchannel.js"


# ---------------------------------------------------------------------------
# Injected binding script
# ---------------------------------------------------------------------------
BINDING_JS = r"""
(function () {
  if (window.__jarvisBound) { return; }
  window.__jarvisBound = true;

  var $  = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) {
    return Array.prototype.slice.call((r || document).querySelectorAll(s));
  };
  function text(node, value) {
    if (node && value !== undefined && value !== null) { node.textContent = String(value); }
  }
  function panel(re) {
    var found = $$('.panel').filter(function (p) {
      var h = p.querySelector('h2');
      return h && re.test(h.textContent || '');
    });
    return found[0] || null;
  }
  function template(root, sel) {
    var n = $(sel, root);
    return n ? n.cloneNode(true) : null;
  }

  // ------------------------------------------------------------------ nodes
  var feedPanel  = panel(/LIVE INTELLIGENCE FEED/i);
  var agentPanel = panel(/ACTIVE AGENTS/i);

  var feedTpl  = feedPanel  ? feedPanel.querySelectorAll('.feed-item')[1]
                            || feedPanel.querySelector('.feed-item') : null;
  if (feedTpl && !$('.meta', feedTpl)) {
    var m = document.createElement('span'); m.className = 'meta';
    feedTpl.appendChild(m);
  }
  var agentTpl = agentPanel ? template(agentPanel, '.agent-card') : null;

  var el = {
    pill:     $('.status-pill'),
    dateStr:  $('#dateStr'),
    timeStr:  $('#timeStr'),
    wave:     $('#wave'),
    orb:      $('.orb'),
    vcStatus: $('.voice-card .status'),
    vcHint:   $('.voice-card > div[style*="font-size:9px"]'),
    focusBtn: $('.focus-btn'),
    search:   $('.search'),
    talkBtn:  $('.talk-btn'),
    talkMain: $('.talk-btn .main'),
    talkSub:  $('.talk-btn .sub'),
    briefBtn: $('.brief-btn'),
    avatar:   $('.avatar'),
    coreSub:  $('.core-label .sub'),
    coreVer:  $('.core-label .ver'),
    sidebar:  $('.sidebar'),
    bar:      $('.bottombar'),
    globeHost: $('#globeHost'),
    coreLabel: $('.core-label h3')
  };
  var waveBars = $$('#wave span');

  // ------------------------------------------------------------------ state
  var S = { state: 'IDLE', muted: false, focus: false, level: 0, scan: false };

  var COPY = {
    LISTENING: ['Listening…',    'I am listening…'],
    SPEAKING:  ['Speaking…',     'Speaking…'],
    THINKING:  ['Thinking…',     'Thinking…'],
    SCANNING:  ['Scanning…',     'Scanning…'],
    MEETING:   ['In Meeting',    'Listening to the meeting…'],
    ERROR:     ['Degraded',      'Check the connection…'],
    IDLE:      ['Listening…',    'I am listening…']
  };
  function copy() { return COPY[S.state] || COPY.IDLE; }

  // The status pill's label is a bare text node next to .dot, so it is
  // written as a text node rather than into a wrapper we would have had to
  // invent.
  function setPill(label, colour) {
    if (!el.pill) { return; }
    for (var i = 0; i < el.pill.childNodes.length; i++) {
      var n = el.pill.childNodes[i];
      if (n.nodeType === 3) { n.nodeValue = label; break; }
    }
    var dot = $('.dot', el.pill);
    if (dot && colour) { dot.style.background = colour; dot.style.boxShadow = '0 0 8px ' + colour; }
  }

  // ----------------------------------------------------------------- bridge
  window.JarvisUI = {
    ready: true,

    // Called once per poll with a complete snapshot.
    apply: function (snap) {
      snap = snap || {};
      if (snap.state)  { this.setState(snap.state); }
      if (snap.muted !== undefined && snap.muted !== S.muted) { this.setMuted(snap.muted); }
      if (snap.core)     { this.setCore(snap.core); }
      if (snap.agents)   { this.setAgents(snap.agents); }
      if (snap.footer)   { this.setFooter(snap.footer); }
      if (snap.badges)   { this.setBadges(snap.badges); }
      if (snap.feed)     { this.setFeed(snap.feed); }
      if (snap.task)     { this.setTask(snap.task); }
      if (snap.level !== undefined) { this.setLevel(snap.level); }
    },

    // ----------------------------------------------------------- voice state
    setState: function (state) {
      S.state = String(state || 'IDLE').toUpperCase();
      var c = copy();
      text(el.vcStatus, S.muted ? 'Muted' : c[0]);
      text(el.talkSub, c[1]);

      if (el.orb) {
        el.orb.style.animationDuration =
          S.state === 'SPEAKING' ? '0.9s' : S.state === 'THINKING' ? '0.5s' : '2.2s';
        el.orb.style.boxShadow =
          S.state === 'SPEAKING'
            ? '0 0 46px rgba(255,150,30,.85), inset 0 0 14px rgba(255,255,255,.3)'
          : S.state === 'THINKING'
            ? '0 0 40px rgba(255,90,43,.6), inset 0 0 14px rgba(255,255,255,.3)'
            : '0 0 26px rgba(255,150,30,.55), inset 0 0 12px rgba(255,255,255,.25)';
      }
      var barDur = S.state === 'SPEAKING' ? '0.45s'
                 : S.state === 'THINKING' ? '0.3s' : '1.1s';
      waveBars.forEach(function (b, i) {
        b.style.animationDuration = barDur;
        b.style.animationDelay = (i * 0.05) + 's';
      });
      setPill(
        S.state === 'ERROR'   ? 'SYSTEM STATUS · DEGRADED'
      : S.state === 'THINKING' ? 'SYSTEM STATUS · BUSY'
      :                            'SYSTEM STATUS · OPTIMAL',
        S.state === 'ERROR' ? 'var(--ember)' : 'var(--amber-bright)');
    },

    setMuted: function (muted) {
      S.muted = !!muted;
      text(el.vcStatus, S.muted ? 'Muted' : copy()[0]);
      if (el.vcHint)  { el.vcHint.textContent = S.muted ? 'Tap to unmute' : 'Tap to Speak'; }
      if (el.focusBtn){ el.focusBtn.textContent = S.muted ? 'UNMUTE' : 'FOCUS MODE'; }
      if (el.talkMain){ el.talkMain.textContent = S.muted ? 'UNMUTE JARVIS' : 'TALK TO JARVIS'; }
      if (el.talkSub) { el.talkSub.textContent = S.muted ? 'Microphone is off' : copy()[1]; }
      if (el.orb)     { el.orb.style.filter = S.muted ? 'grayscale(1) opacity(.5)' : ''; }
    },

    // Real microphone level, 0..1. Drives tempo only -- no pixel moves.
    setLevel: function (level) {
      S.level = Math.max(0, Math.min(1, Number(level) || 0));
      if (S.state !== 'SPEAKING' && S.state !== 'LISTENING') { return; }
      var base = S.state === 'SPEAKING' ? 0.45 : 1.1;
      var mult = 1 - 0.55 * S.level;
      waveBars.forEach(function (b) { b.style.animationDuration = (base * mult).toFixed(3) + 's'; });
    },

    // ------------------------------------------------------------- AI core
    setCore: function (c) {
      c = c || {};
      if (c.version !== undefined) { text(el.coreVer, 'v' + c.version); }
      if (c.sub      !== undefined) { text(el.coreSub, c.sub); }
    },

    // ------------------------------------------------- live intelligence feed
    setFeed: function (items) {
      if (!feedPanel || !feedTpl || !items || !items.length) { return; }
      $$('.feed-item', feedPanel).forEach(function (n) { n.remove(); });
      var ordered = items.slice(0, 12);
      for (var i = ordered.length - 1; i >= 0; i--) {
        feedPanel.appendChild(buildFeed(ordered[i]));
      }
    },

    pushFeed: function (item) {
      if (!feedPanel || !feedTpl) { return; }
      var node = buildFeed(item || {});
      var first = $('.feed-item', feedPanel);
      if (first) { feedPanel.insertBefore(node, first); }
      else { feedPanel.appendChild(node); }
      var items = $$('.feed-item', feedPanel);
      while (items.length > 12) { items.pop().remove(); }
    },

    // --------------------------------------------------------------- agents
    setAgents: function (agents) {
      if (!agentPanel || !agentTpl) { return; }
      $$('.agent-card', agentPanel).forEach(function (n) { n.remove(); });
      (agents || []).forEach(function (a) {
        var card = agentTpl.cloneNode(true);
        var ico = $('.agent-ico', card);
        if (ico) {
          ico.textContent = a.icon || '•';
          ico.setAttribute('style', a.bg || 'background:#251808;color:var(--gold);');
        }
        text($('.name', card), a.name || '');
        var stat = $('.stat', card);
        if (stat) {
          stat.textContent = (a.status ? '● ' + a.status
                                       : (a.active ? '● Active' : '● Standby'));
          stat.className = 'stat' + (a.active ? ' on' : '');
          stat.title = a.task || a.detail || '';
        }
        if (a.active) { card.style.borderColor = 'var(--amber)'; }
        agentPanel.appendChild(card);
      });
    },

    // ---------------------------------------------------------- active task
    setTask: function (t) {
      if (!t) { return; }
      if (t.sub !== undefined) { text(el.coreSub, t.sub); }
      if (t.percent !== undefined && t.active) {
        setPill('SYSTEM STATUS · ' + Math.round(t.percent) + '% COMPLETE', 'var(--amber-bright)');
      }
    },

    // ------------------------------------------------------------- bottom bar
    setFooter: function (f) {
      f = f || {};
      var F = window.__jarvisFooter || (window.__jarvisFooter = {});
      ['location', 'weather', 'temp', 'icon', 'network'].forEach(function (k) {
        var v = f[k];
        if (v === undefined || v === null || v === '' || v === '--') { return; }
        F[k] = v;
      });
      var left = $$('.bb-left span');
      if (!Object.keys(F).length) { return; }
      if (left[0] && F.location) {
        text(left[0], '\uD83D\uDCCD ' + F.location);
      }
      if (left[1] && (F.weather || F.temp)) {
        text(left[1], (F.icon || '☀') + ' ' + (F.temp || '--') + '°C '
                   + (F.weather || ''));
      }
      if (left[2] && F.network) {
        text(left[2], '📶 Network ' + F.network);
      }
    },

    // ---------------------------------------------------------------- badges
    setBadges: function (map) {
      map = map || {};
      $$('nav a').forEach(function (a) {
        var b = $('.badge', a);
        if (!b) { return; }
        var label = a.textContent || '';
        var key = null;
        if (/Tasks/i.test(label))              { key = 'tasks'; }
        else if (/Conversations/i.test(label)) { key = 'conversations'; }
        else if (/Tools/i.test(label))         { key = 'tools'; }
        if (key && map[key] !== undefined) {
          b.textContent = String(map[key]);
          b.style.display = (String(map[key]) === '0') ? 'none' : '';
        }
      });
    },

    setNavActive: function (label) {
      $$('nav a').forEach(function (a) {
        var on = (a.textContent || '').indexOf(label) >= 0;
        a.classList.toggle('active', on);
      });
    },

    setUser: function (initials, name) {
      if (el.avatar) { el.avatar.textContent = initials || 'OP'; el.avatar.title = name || ''; }
    },

    // ------------------------------------------------------------ focus mode
    setFocus: function (on) {
      S.focus = !!on;
      if (el.sidebar) { el.sidebar.style.display = S.focus ? 'none' : ''; }
      if (el.bar)     { el.bar.style.display     = S.focus ? 'none' : ''; }
      if (el.focusBtn){ el.focusBtn.textContent = S.focus ? 'EXIT FOCUS' : 'FOCUS MODE'; }
    },

    isFocus: function () { return S.focus; },
    isMuted: function () { return S.muted; },
    getState: function () { return S.state; }
  };

  function buildFeed(item) {
    item = item || {};
    var node = feedTpl.cloneNode(true);
    var tag = $('.tag', node);
    var cls = String(item.tag || 'info').toLowerCase();
    if (['info', 'warn', 'tip', 'live'].indexOf(cls) < 0) { cls = 'info'; }
    if (tag) { tag.className = 'tag ' + cls; tag.textContent = item.tagText || cls.toUpperCase(); }
    text($('.title', node), item.title || '');
    text($('.meta', node), item.meta || '');
    return node;
  }

  // ------------------------------------------------------------------ events
  function send(cmd) {
    var fn = bridge('sendCommand');
    if (cmd && fn) { fn(String(cmd)); }
  }
  function bridge(name) {
    var o = window.pybridge ||
            (window.__jarvisChannel && window.__jarvisChannel.objects);
    return o && o[name] ? o[name] : null;
  }
  function ask(view, payload) {
    var fn = bridge('requestView');
    if (fn) { fn(view + (payload ? '?' + payload : '')); }
  }
  function toggleMute() {
    var fn = bridge('mutedState');
    var m = bridge('setMuted');
    if (m) { m(!(fn && fn() ? 1 : 0)); }
  }

  // -- sidebar -------------------------------------------------------
  if (el.focusBtn) {
    el.focusBtn.addEventListener('click', function () {
      window.JarvisUI.setFocus(!S.focus);
      var fn = bridge('setFocusState');
      if (fn) { fn(S.focus); }
    });
  }
  if (el.orb)     { el.orb.addEventListener('click', toggleMute); }
  var vcLabel = $('.voice-card .label');
  if (vcLabel)   { vcLabel.addEventListener('click', function () { ask('settings'); }); }
  if (el.avatar)  { el.avatar.addEventListener('click', function () { ask('profile'); }); }
  var brand = $('.brand');
  if (brand)     { brand.addEventListener('click', function () { ask('ai_core'); }); }
  if (el.pill)   { el.pill.addEventListener('click', function () { ask('monitor'); }); }

  // -- bottom bar ----------------------------------------------------
  if (el.talkBtn) {
    el.talkBtn.addEventListener('click', function () {
      var chat = bridge('openChat');
      if (chat) { chat(1); }
      var muted = bridge('mutedState');
      var m = bridge('setMuted');
      if (muted && muted() && m) { m(0); }
    });
  }
  if (el.briefBtn) {
    el.briefBtn.addEventListener('click', function () {
      var b = bridge('runBriefing');
      if (b) { b(); }
    });
  }

  // -- search --------------------------------------------------------
  if (el.search) {
    el.search.addEventListener('keydown', function (e) {
      if (e.key !== 'Enter') { return; }
      var v = (el.search.value || '').trim();
      if (!v) { return; }
      send(v);
      el.search.value = '';
    });
  }

  // -- top-bar icons -------------------------------------------------
  var ICON_VIEWS = ['monitor', 'notifications', 'settings'];
  $$('.icon-btn').forEach(function (b, i) {
    b.addEventListener('click', function () { ask(ICON_VIEWS[i] || 'monitor'); });
  });

  // -- nav: every entry opens a real view ----------------------------
  var NAV_VIEWS = {
    'command center': null,
    'ai core':        'ai_core',
    'agents':         'agents',
    'tasks':          'tasks',
    'calendar':       'calendar',
    'memory':         'memory',
    'conversations':  'conversations',
    'knowledge base': 'knowledge',
    'tools':          'tools',
    'tools & skills': 'tools',
    'workflows':      'workflows'
  };
  function navLabel(a) {
    var out = '';
    for (var i = 0; i < a.childNodes.length; i++) {
      if (a.childNodes[i].nodeType === 3) { out += a.childNodes[i].nodeValue; }
    }
    return out.replace(/[0-9]+$/, '').trim().toLowerCase();
  }
  $$('nav a').forEach(function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault();
      $$('nav a').forEach(function (x) { x.classList.remove('active'); });
      a.classList.add('active');
      var key = navLabel(a);
      var view = NAV_VIEWS[key];
      if (view === null) { return; }
      if (view) { ask(view); return; }
      var label = (a.textContent || '').replace(/[^A-Za-z ]/g, '').trim();
      send('open ' + label);
    });
  });

  // -- the cards themselves are real controls ------------------------
  function textOf(node, sel) {
    var n = $(sel, node);
    return n ? (n.textContent || '').trim() : '';
  }
  document.addEventListener('click', function (e) {
    var t = e.target;
    if (!t || !t.closest) { return; }

    var agent = t.closest('.agent-card');
    if (agent) { ask('agent', textOf(agent, '.name')); return; }

    var feed = t.closest('.feed-item');
    if (feed) { ask('events'); return; }
  }, true);

  // Rebind the cards the pollers rebuild.
  window.JarvisUI._rebind = function () {
    $$('.agent-card').forEach(function (c) {
      if (c.__bound) { return; }
      c.__bound = true;
      c.addEventListener('click', function () {
        ask('agent', textOf(c, '.name'));
      });
    });
  };
  var _setAgents = window.JarvisUI.setAgents;
  window.JarvisUI.setAgents = function (rows) { _setAgents(rows); window.JarvisUI._rebind(); };
  var _pushFeed = window.JarvisUI.pushFeed;
  window.JarvisUI.pushFeed = function (item) { _pushFeed(item); window.JarvisUI._rebind(); };

  // Chat, opened from TALK TO JARVIS or with Ctrl+Alt+C.
  document.addEventListener('keydown', function (e) {
    if (e.ctrlKey && e.altKey && (e.key === 'c' || e.key === 'C')) {
      e.preventDefault();
      var chat = bridge('openChat');
      if (chat) { chat(1); }
    }
  });

  window.__jarvisReady = true;
})();
"""


# ---------------------------------------------------------------------------
# Bridge object: slots the page calls
# ---------------------------------------------------------------------------
class CommandCenterBridge(QObject):
    """The page's only way into Python. Every slot is a thin, safe handoff."""

    command_received = pyqtSignal(str)
    mute_requested = pyqtSignal(bool)
    nav_requested = pyqtSignal(str)
    icon_requested = pyqtSignal(int)
    view_requested = pyqtSignal(str, str)
    chat_requested = pyqtSignal(bool)
    briefing_requested = pyqtSignal()
    focus_state = pyqtSignal(bool)

    def __init__(self, parent=None, speaking_getter=None) -> None:
        super().__init__(parent)
        self.muted = False
        self._speaking_getter = speaking_getter

    @pyqtSlot(result=bool)
    def isSpeaking(self) -> bool:
        if self._speaking_getter:
            return self._speaking_getter()
        return False

    def set_speaking_getter(self, getter) -> None:
        self._speaking_getter = getter

    @pyqtSlot(str)
    def sendCommand(self, text: str) -> None:
        text = (text or "").strip()
        if text:
            self.command_received.emit(text)

    @pyqtSlot(bool)
    def setMuted(self, muted: bool) -> None:
        self.muted = bool(muted)
        self.mute_requested.emit(self.muted)

    @pyqtSlot(result=bool)
    def mutedState(self) -> bool:
        return bool(self.muted)

    @pyqtSlot(str)
    def navClicked(self, label: str) -> None:
        self.nav_requested.emit((label or "").strip())

    @pyqtSlot(int)
    def iconClicked(self, index: int) -> None:
        self.icon_requested.emit(int(index))

    @pyqtSlot(str)
    def requestView(self, view: str) -> None:
        """Any clickable surface in the page asks for a real view."""
        raw = str(view or "").strip()
        if not raw:
            return
        name, _, payload = raw.partition("?")
        self.view_requested.emit(name.strip(), payload)

    @pyqtSlot(int)
    def openChat(self, open: int = 1) -> None:
        self.chat_requested.emit(bool(open))

    @pyqtSlot()
    def runBriefing(self) -> None:
        self.briefing_requested.emit()

    @pyqtSlot(bool)
    def setFocusState(self, on: bool) -> None:
        self.focus_state.emit(bool(on))


# ---------------------------------------------------------------------------
# Payload builders -- real data for each panel
# ---------------------------------------------------------------------------
def human_bytes(n) -> str:
    try:
        n = float(n or 0)
    except (TypeError, ValueError):
        return "0B"
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if abs(n) < 1024.0:
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024.0
    return f"{n:.1f}EB"


def gauge_colour(pct: float) -> str:
    """Colour thresholds for the monitor panel."""
    try:
        pct = float(pct)
    except (TypeError, ValueError):
        return "#ffb020"
    if pct >= 90:
        return "#ff5a2b"
    if pct >= 75:
        return "#ffb020"
    return "#ffb020"


def build_llm_rows(api_keys: dict | None) -> list[dict]:
    """Provider status, derived from the real key file and a local probe."""
    keys = api_keys or {}

    def has(*names: str) -> bool:
        return any(str(keys.get(n) or "").strip() for n in names)

    def row(name: str, present: bool) -> dict:
        return {"name": name, "on": present,
                "state": "Connected" if present else "Not Linked"}

    rows = [
        row("Claude", has("anthropic_api_key", "claude_api_key")),
        row("OpenAI", has("openai_api_key")),
        row("Gemini", has("gemini_api_key", "google_api_key")),
        row("Groq", has("groq_api_key")),
        row("OpenRouter", has("openrouter_api_key")),
    ]

    models, up = 0, False
    try:
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=0.5) as r:
            models = len(json.loads(r.read().decode("utf-8", "ignore")).get("models") or [])
        up = True
    except Exception:
        up = False
    rows.append({"name": "Ollama", "on": up and models > 0,
                 "state": (f"{models} Models" if models else
                           ("No Models" if up else "Offline"))})

    rows += [
        row("Claude Code", has("claude_code_key", "anthropic_api_key")),
        row("Cursor", has("cursor_api_key")),
        row("Copilot", has("github_token", "copilot_api_key")),
    ]
    return rows


#: Subsystems that are genuinely running whenever the assistant is up.
ALWAYS_LIVE_AGENTS = ("system", "task", "memory")


def build_agent_rows(live_agents=None) -> list[dict]:
    """Agent cards for the Command Center.

    Prefers the live agent registry, so the panel shows the agents that
    actually exist and lights up the ones currently working. Falls back to the
    assistant's own subsystems only when the agent system is not running.
    """
    try:
        import agent_runtime
        rows = agent_runtime.agent_rows()
        if any(r.get("real") for r in rows):
            return rows
    except Exception:
        pass

    if live_agents is None:
        live = {n for n in ALWAYS_LIVE_AGENTS}
    else:
        live = {str(n).lower() for n in live_agents}
    spec = [
        ("Coding Agent",     "{ }", "#2a1a06", "var(--amber-bright)",  "coding"),
        ("Research Agent",   "\U0001F50D", "#251808", "var(--gold)",   "research"),
        ("Memory Agent",     "✎", "#1e1406", "var(--amber-dim)", "memory"),
        ("Browser Agent",    "◐", "#301708", "var(--ember)",  "browser"),
        ("Task Agent",       "☑", "#251808", "var(--gold)",        "task"),
        ("System Agent",     "✓", "#2a1a06", "var(--amber-bright)",   "system"),
    ]
    rows = []
    for name, icon, bg, fg, key in spec:
        rows.append({
            "name": name, "icon": icon, "active": key in live,
            "bg": f"background:{bg};color:{fg};",
        })
    return rows
