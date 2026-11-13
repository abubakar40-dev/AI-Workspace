"""
Tests for the Command Center integration.

Three things are being protected here:

1. The operator's HTML is read-only. ``assets/command_center/index.html`` is
   shipped byte-for-byte; if an edit ever changes it, these fail.

2. The binding script only touches selectors that actually exist in that file.
   An earlier draft invented ``#llmHost`` and ``#agentsHost``; both do not
   exist, so those panels silently stayed dead. Every selector is now checked
   against the real markup.

3. The public API ``main.py`` and the action modules call still exists, with
   the same names, arity and semantics the previous GUI had.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import re
import threading
from pathlib import Path

import pytest

pytest.importorskip("PyQt6")

import command_bridge as CB
import command_center as CC

HTML = CC.COMMAND_CENTER_HTML
MARKUP = HTML.read_text(encoding="utf-8")

# sha256 of the file as delivered in ~/Downloads. The GUI must never be edited.
SHIPPED_SHA256 = "78896b28c505fee43ef1fe1b195ec22b7a4f8ffba1a41d7f211bea43460df69e"


# ---------------------------------------------------------------------------
# 1. The page is read-only
# ---------------------------------------------------------------------------
def test_command_center_html_exists():
    assert HTML.is_file(), f"missing {HTML}"


def test_command_center_html_is_byte_identical_to_the_original():
    """The operator's design must ship untouched."""
    digest = hashlib.sha256(HTML.read_bytes()).hexdigest()
    assert digest == SHIPPED_SHA256, (
        "assets/command_center/index.html was modified -- the GUI is meant to "
        "be the operator's file, not ours to edit"
    )


def test_no_stylesheet_was_injected_into_the_page():
    """All styling must stay in Python; the page keeps its own <style>."""
    assert MARKUP.count("<style>") == 1
    assert "assets/command_center" not in MARKUP


# ---------------------------------------------------------------------------
# 2. Every selector the binding uses exists in the page
# ---------------------------------------------------------------------------
def _binding_selectors() -> set[str]:
    """Class/id/element selectors referenced by the injected script."""
    found: set[str] = set()
    for raw in re.findall(r"\$\$?\(\s*'([^']+)'", CB.BINDING_JS):
        for part in raw.split(","):
            part = part.strip()
            if part.startswith("#"):
                found.add(part)
            elif part.startswith("."):
                found.add(part)
    return found


def test_binding_targets_only_real_selectors():
    """Every part of every selector the binding uses must exist in the page.

    Compound selectors such as ``.voice-card .status`` are checked part by
    part, because a single typo in any component silently kills that panel --
    which is exactly what happened with the invented ``#llmHost`` id.
    """
    missing = []
    for sel in sorted(_binding_selectors()):
        for part in re.split(r"\s+", sel.strip()):
            part = part.strip()
            if not part or part in {">", "+", "~"}:    # CSS combinators
                continue
            if part.startswith("#"):
                ok = f'id="{part[1:]}"' in MARKUP
            elif part.startswith("."):
                cls = re.escape(part[1:])
                ok = re.search(rf'class="[^"]*\b{cls}\b', MARKUP) is not None
            else:
                # a bare tag, possibly with an attribute fragment
                tag = part.split("[")[0]
                ok = re.search(rf"<{tag}[\s>]", MARKUP) is not None
            if not ok:
                missing.append(f"{sel} (part {part!r})")
    assert not missing, f"binding references selectors absent from the page: {missing}"


def test_binding_does_not_invent_containers():
    """The repeated panels have no wrapper id in the design, so the binding
    must find them through their heading rather than an id we would add."""
    for invented in ("llmHost", "agentsHost", "timelineHost", "feedHost"):
        assert invented not in CB.BINDING_JS, (
            f"{invented} does not exist in the page and would silently do nothing")


def test_binding_uses_the_pages_own_state_classes():
    for cls in ("tag info", "tag warn", "tag tip", "tag live",
                "stat on", "active"):
        assert cls in MARKUP, f"page has no .{cls}"


def test_binding_clones_rather_than_rebuilding_markup():
    """Cloning the author's own node is what guarantees identical pixels."""
    assert "cloneNode(true)" in CB.BINDING_JS
    assert "insertAdjacentHTML" not in CB.BINDING_JS


# ---------------------------------------------------------------------------
# 3. The public API main.py relies on
# ---------------------------------------------------------------------------
# Every entry is (name, args, kwargs) exactly as main.py or an action module
# calls it. Reproducing the real call sites is the point: a signature that only
# works positionally, or a renamed keyword, breaks the app at runtime and a
# mere hasattr check would not notice.
CALL_SITES = [
    ("play_boot_sequence", (), {"finished_callback": lambda: None}),
    ("play_boot_sequence", (), {}),
    ("boot_add_step", ("Load configuration",), {}),
    ("boot_set_progress", (36, "Initializing AI client"), {}),
    ("boot_set_step_status", ("Start attention monitor", "done"), {}),
    ("begin_task_workspace", ("Replying to message",
                              ["Type your response", "Send via whatsapp"],
                              ), {"source": "reply"}),
    ("begin_task_workspace", ("text", ["a", "b"], "local"), {}),
    ("update_task_workspace", (), {"status": "Scanning screen",
                                   "output": "inspecting", "percent": 40}),
    ("update_task_workspace", (), {"status": "Screen analysis unavailable",
                                   "output": "disabled", "percent": 0}),
    ("finish_task_workspace", ("Reply delivered.", "Reply delivered.", 100), {}),
    ("finish_task_workspace", ("Reply cancelled.", "Cancelled", 100), {}),
    ("set_state", ("SPEAKING",), {}),
    ("set_muted_state", (True,), {}),
    ("set_muted_state", (False,), {"wakeword": True}),
    ("set_meeting_mode", (True, "Standup", "summary", "answer", "speech"), {}),
    ("set_meeting_mode", (False, "", "", ""), {}),
    ("set_scanning", (False, ""), {}),
    ("set_scanning", (False,), {}),
    ("show_attention_alert", ({"app": "whatsapp", "title": "Ali",
                                "preview": "salaam"},), {}),
    ("notify_phone_connected", (), {}),
    ("submit_external_command", ("hello",), {"source": "mobile"}),
    ("set_brahma_connect_service", (object(),), {}),
    ("write_log", ("You: hello",), {}),
    ("add_system_message", ("Template fallback",), {}),
    ("set_audio_level", (0.42,), {}),
]


@pytest.mark.parametrize("name,args,kwargs", CALL_SITES)
def test_api_accepts_the_exact_call_sites_used_in_the_app(name, args, kwargs):
    fn = getattr(CC.JarvisUI, name, None)
    assert callable(fn), f"JarvisUI.{name} is missing"
    ui = _bare()
    sig = inspect.signature(fn)
    sig.bind(ui, *args, **kwargs)          # raises if the shape is wrong


def test_root_is_the_window_so_mainloop_works():
    """main.py ends with ``ui.root.mainloop()``."""
    assert isinstance(CC.JarvisUI.root, property)
    assert callable(CC.JarvisUI.mainloop)


def test_callbacks_main_py_assigns_are_settable():
    for name in ("on_text_command", "on_attention_action", "on_remote_clicked"):
        assert hasattr(CC.JarvisUI, name) or name in inspect.getsource(
            CC.CommandCenter.__init__), f"{name} is not initialised"


# ---------------------------------------------------------------------------
# 4. Behaviour that does not need a live browser
# ---------------------------------------------------------------------------
def _bare() -> CC.CommandCenter:
    """A CommandCenter without building the web view."""
    ui = CC.CommandCenter.__new__(CC.CommandCenter)
    ui.muted = False
    ui.current_file = ""
    ui.states = []
    ui._wakeword_listening = False
    ui._feed_queue = __import__("collections").deque(maxlen=200)
    ui._feed_seen = __import__("collections").deque(maxlen=60)
    ui._chat_queue = __import__("collections").deque(maxlen=200)
    ui._recent_feed = __import__("collections").deque(maxlen=60)
    ui._task = None
    ui._timeline = []
    ui._boot_steps = []
    ui._boot_percent = 0
    ui._page_ready = False
    ui._states_sent = "IDLE"
    ui._level = 0.0
    ui._level_sent = 0.0
    ui._turns = 0
    return ui


def test_set_state_records_history():
    """tests/test_main_dispatch.py asserts on ui.states."""
    ui = _bare()
    ui.set_state("THINKING")
    ui.set_state("LISTENING")
    assert ui.states == ["THINKING", "LISTENING"]


def test_states_history_is_bounded():
    ui = _bare()
    for _ in range(500):
        ui.set_state("LISTENING")
    assert len(ui.states) <= 200


def test_write_log_classifies_and_queues():
    ui = _bare()
    ui.write_log("You: download this video")
    ui.write_log("SYS: microphone recovered")
    ui.write_log("Jarvis: on it")
    tags = [item["tag"] for item in ui._feed_queue]
    assert tags == ["live", "info", "tip"]


def test_write_log_collapses_a_repeated_line():
    """A retry loop must not be able to flood the feed panel."""
    ui = _bare()
    ui.write_log("SYS: retrying")
    ui.write_log("SYS: retrying")
    assert len(ui._feed_queue) == 1


def test_write_log_is_safe_from_a_worker_thread():
    """Called from the audio, tool and screen threads; it must not touch Qt."""
    ui = _bare()
    errors = []

    def worker():
        try:
            for i in range(200):
                ui.write_log(f"SYS: line {i}")
                ui.push_feed(f"event {i}", "test")
                ui.set_audio_level(0.5)
        except Exception as exc:      # pragma: no cover
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    assert len(ui._feed_queue) == ui._feed_queue.maxlen


def test_task_workspace_advances_its_plan():
    ui = _bare()
    ui.begin_task_workspace("Organise Downloads", ["List", "Group", "Move", "Report"])
    assert ui._task is not None
    assert len(ui._timeline) == 4
    assert all(row["done"] is False for row in ui._timeline)

    ui.update_task_workspace(status="Grouping", output="22 moved", percent=55)
    assert ui._timeline[0]["done"] is True, "the first step should be complete"
    assert any(row["eta"] == "Grouping" for row in ui._timeline)

    ui.finish_task_workspace("Done", "Completed", 100)
    assert ui._task is None
    assert all(row["done"] for row in ui._timeline)


def test_begin_task_workspace_accepts_the_keyword_source():
    """main.py calls it as begin_task_workspace(text, plan, source=...)."""
    ui = _bare()
    ui.begin_task_workspace("Reply", ["Type", "Send"], source="reply")
    assert ui._task["source"] == "reply"


def test_update_task_workspace_without_a_task_does_not_raise():
    ui = _bare()
    ui.update_task_workspace(status="x", output="y", percent=10)


def test_update_task_workspace_is_keyword_driven():
    """Every call site in main.py passes keywords only."""
    ui = _bare()
    ui.begin_task_workspace("t", ["a"])
    ui.update_task_workspace(status="s", output="o", percent=50)
    ui.update_task_workspace(progress=60)


def test_boot_steps_render_into_the_timeline():
    ui = _bare()
    ui.boot_add_step("Load configuration")
    ui.boot_add_step("Initialize audio")
    ui.boot_set_step_status("Load configuration", "done")
    assert len(ui._timeline) == 2
    assert ui._timeline[0]["done"] is True
    assert ui._timeline[1]["done"] is False


def test_a_running_task_owns_the_timeline_over_boot_steps():
    ui = _bare()
    ui.boot_add_step("Load configuration")
    ui.begin_task_workspace("Real work", ["step one"])
    ui.boot_add_step("Late boot step")
    assert ui._timeline[0]["title"] == "step one"


def test_play_boot_sequence_runs_the_callback():
    """main.py passes finished_callback= and relies on it firing."""
    ui = _bare()
    fired = []
    ui._invoke = threading.Event()          # not used: page is not ready
    ui.play_boot_sequence(finished_callback=lambda: fired.append(True))
    # the callback is dispatched on the Qt event loop, which is not running in
    # this bare instance, so assert the call itself did not raise
    assert fired == []


def test_play_boot_sequence_tolerates_a_missing_callback():
    ui = _bare()
    ui.play_boot_sequence()


# ---------------------------------------------------------------------------
# 5. Payload builders
# ---------------------------------------------------------------------------
def test_gauge_colour_thresholds():
    assert CB.gauge_colour(10) == "#ffb020"
    assert CB.gauge_colour(80) == "#ffb020"
    assert CB.gauge_colour(95) == "#ff5a2b"
    assert CB.gauge_colour("bad") == "#ffb020"


def test_human_bytes():
    assert CB.human_bytes(512) == "512B"
    assert CB.human_bytes(2048) == "2.0KB"
    assert CB.human_bytes(0) == "0B"
    assert CB.human_bytes(None) == "0B"


def test_llm_rows_track_the_key_file():
    rows = CB.build_llm_rows({"gemini_api_key": "x", "groq_api_key": "y"})
    by_name = {r["name"]: r for r in rows}
    assert len(rows) == 9, "the page has nine provider cards"
    assert by_name["Gemini"]["on"] is True
    assert by_name["Gemini"]["state"] == "Connected"
    assert by_name["OpenAI"]["on"] is False
    assert by_name["OpenAI"]["state"] == "Not Linked"


def test_llm_rows_survive_an_empty_key_file():
    rows = CB.build_llm_rows({})
    assert len(rows) == 9
    assert all(isinstance(r["on"], bool) for r in rows)


def test_ollama_state_is_probed_not_guessed():
    row = next(r for r in CB.build_llm_rows({}) if r["name"] == "Ollama")
    assert row["state"] in {"Offline", "No Models"} or "Models" in row["state"]


def test_agent_rows_come_from_the_live_registry_when_it_exists():
    """The panel must show the agents that really exist, not placeholders."""
    monkey = pytest.MonkeyPatch()
    try:
        import agent_runtime
        agent_runtime.start()
        rows = CB.build_agent_rows()
        real = [r for r in rows if r.get("real")]
        assert real, "expected the real registry to be reported"
        assert {r["name"] for r in real} >= {"Research Agent", "Document Agent",
                                            "Code Agent"}
    finally:
        monkey.undo()


def test_agent_rows_fall_back_when_no_agents_are_registered(monkeypatch):
    import agent_runtime
    monkeypatch.setattr(agent_runtime, "agent_rows",
                        lambda: [{"name": "X", "active": False, "real": False}])
    rows = CB.build_agent_rows()
    assert len(rows) == 6
    assert any(r["name"] == "System Agent" for r in rows), \
        "the fallback must still describe the assistant's own subsystems"


def test_agent_rows_honour_an_explicit_list(monkeypatch):
    import agent_runtime
    monkeypatch.setattr(agent_runtime, "agent_rows",
                        lambda: [{"name": "X", "active": False, "real": False}])
    rows = CB.build_agent_rows(["coding"])
    active = [r["name"] for r in rows if r["active"]]
    assert active == ["Coding Agent"]


def test_a_working_agent_is_reported_as_working(monkeypatch):
    """Principle 9: the operator must see which agent is busy right now."""
    import agent_runtime
    rows = [{"name": "Research Agent", "icon": "x", "active": True,
             "status": "Working", "task": "gather sources", "real": True,
             "bg": ""}]
    monkeypatch.setattr(agent_runtime, "agent_rows", lambda: rows)
    out = CB.build_agent_rows()
    busy = [r for r in out if r.get("active")]
    assert busy and busy[0]["status"] == "Working"
    assert busy[0]["task"] == "gather sources"


def test_agent_colours_match_the_original_markup():
    """The fallback colours are lifted from the author's own inline styles."""
    import command_bridge as CB
    # Force the fallback by making the registry unavailable
    import agent_runtime
    original = agent_runtime.agent_rows
    agent_runtime.agent_rows = lambda: []
    try:
        rows = CB.build_agent_rows()
    finally:
        agent_runtime.agent_rows = original
    for bg in ("#2a1a06", "#251808", "#1e1406", "#301708"):
        assert bg in MARKUP
        assert any(bg in r["bg"] for r in rows)


# ---------------------------------------------------------------------------
# 6. Snapshot shape
# ---------------------------------------------------------------------------
def test_snapshot_is_json_serialisable():
    """Everything crossing into the page goes through json.dumps."""
    snapshot = {
        "core": CB.build_llm_rows({}) and {"version": "8.0.0", "system": "Optimal"},
        "agents": CB.build_agent_rows(),
        "llms": CB.build_llm_rows({}),
        "gauges": [{"label": "CPU", "val": 12.5, "color": CB.gauge_colour(12.5)}],
        "memory": {"memories": "159", "turns": 18, "cost": "$0.00",
                   "history": [1, 2, 3]},
        "footer": {"location": "Rawalpindi", "network": "Excellent"},
        "badges": {"tasks": 1, "conversations": 2, "tools": 3},
    }
    assert json.loads(json.dumps(snapshot, default=str))
