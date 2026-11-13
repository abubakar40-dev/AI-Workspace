"""
Tests for the agent team.

The agents under ``agent/`` worked but nothing started them: the orchestrator
was never imported and ``agent_task`` submitted to a TaskQueue whose worker
thread was never started, so a delegated objective sat in a queue forever while
the Command Center showed six hardcoded placeholder cards.

These pin the seam that fixes that -- ``agent_runtime`` -- plus the wiring that
makes the assistant aware of the team and the GUI report it live.
"""

from __future__ import annotations

import ast
import inspect
import re

import pytest

pytest.importorskip("PyQt6")

import agent_runtime as AR


# ---------------------------------------------------------------------------
# 1. Lifecycle
# ---------------------------------------------------------------------------
def test_start_brings_the_agents_up():
    assert AR.start() is True
    stats = AR.registry_stats()
    assert stats["total"] >= 3, "the Research, Document and Code agents must exist"
    for kind in ("research", "document", "code"):
        assert stats["by_type"].get(kind, 0) >= 1, f"no {kind} agent registered"


def test_start_is_idempotent():
    import threading
    AR.start()
    AR.start()
    workers = [t for t in threading.enumerate() if t.name == "AgentOrchestrator"]
    assert len(workers) == 1, "starting twice must not double the worker"


def test_only_one_orchestrator_exists():
    AR.start()
    assert AR.orchestrator() is AR.orchestrator()


def test_registry_reports_live_status_fields():
    AR.start()
    agents = AR.registry()
    assert agents
    for agent in agents:
        assert {"agent_id", "name", "type", "status"} <= set(agent)
        assert agent["status"] in ("idle", "running", "starting", "waiting",
                                   "completed", "failed", "cancelled", "pending")


# ---------------------------------------------------------------------------
# 2. The GUI contract
# ---------------------------------------------------------------------------
def test_agent_rows_fill_the_six_cards():
    AR.start()
    rows = AR.agent_rows()
    assert len(rows) == 6, "the page has exactly six agent cards"
    real = [r for r in rows if r["real"]]
    assert len(real) >= 3
    assert {"Research Agent", "Document Agent", "Code Agent"} <= \
        {r["name"] for r in real}


def test_unregistered_slots_are_marked_not_invented():
    rows = {r["name"]: r for r in AR.agent_rows()}
    absent = [r for r in rows.values() if not r["real"]]
    for row in absent:
        assert row["status"] == "unavailable"
        assert row["active"] is False


def test_a_busy_agent_is_visible():
    """Principle 9 -- the operator must see who is working, and on what."""
    import agent.agent_base as AB
    AR.start()
    agent = next(a for a in AR.registry() if a["type"] == "research")
    real = AR.orchestrator()._registry.get_agent(agent["agent_id"])
    original = real.status
    try:
        real.status = AB.AgentStatus.RUNNING
        real._current_task = AB.AgentTask(task_id="t", goal="gather sources",
                                          agent_type=AB.AgentType.RESEARCH)
        rows = {r["name"]: r for r in AR.agent_rows()}
        research = rows["Research Agent"]
        assert research["active"] is True
        assert research["status"] == "Working"
        assert "gather sources" in research["task"]
        assert AR.busy() is True
    finally:
        real.status = original
        real._current_task = None


def test_status_text_speaks_plain_english():
    AR.start()
    text = AR.status_text()
    assert "agents" in text.lower()
    assert "idle" in text.lower() or "busy" in text.lower()


# ---------------------------------------------------------------------------
# 3. Delegation
# ---------------------------------------------------------------------------
def test_an_empty_objective_is_refused():
    receipt = AR.submit("   ")
    assert receipt["ok"] is False
    assert "objective" in receipt["error"].lower()


def test_a_real_objective_is_accepted_with_a_receipt():
    """Never assume it worked: submit must report acceptance and an id."""
    AR.start()
    receipt = AR.submit("Summarise the Python standard library into a note "
                        "in /tmp/jarvis_agent_probe.md")
    assert receipt["ok"] is True, receipt
    assert receipt["orchestration_id"].startswith("orch_")
    assert "delegated" in receipt["message"].lower()


def test_state_is_module_level_not_local():
    """Assigning _current without `global` made it a function local, so the
    objective was never recorded and completion never cleared it."""
    src = inspect.getsource(AR.submit)
    assert "global _current" in src
    src2 = inspect.getsource(AR._on_complete)
    assert "global _current" in src2


def test_progress_callbacks_match_the_orchestrator_signature():
    """The orchestrator calls on_progress(oid, task_id, result) and
    on_complete(oid, plan); single-argument callbacks raised inside its
    worker thread and were swallowed."""
    import agent.orchestrator as orch
    tree = ast.parse(inspect.getsource(orch.AgentOrchestrator))
    calls = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr in ("on_progress", "on_complete")):
            calls.add((node.func.attr, len(node.args)))
    assert ("on_progress", 3) in calls
    assert ("on_complete", 2) in calls

    assert AR._on_progress.__code__.co_argcount == 3
    assert AR._on_complete.__code__.co_argcount == 2


def test_completion_reports_success_and_failure_honestly():
    class Status:
        def __init__(self, v): self.value = v

    class Plan:
        def __init__(self, task_status, plan_status):
            self.status = Status(plan_status)
            t = type("T", (), {})()
            t.status = Status(task_status)
            self.agent_tasks = [t]

    seen = []
    AR.subscribe(lambda ev, d: seen.append((ev, d)))

    AR._current = {"goal": "g", "orchestration_id": "o", "steps": []}
    AR._on_complete("o", Plan("completed", "completed"))
    done = [d for ev, d in seen if ev == "complete"]
    assert done and done[-1]["ok"] is True
    assert "verified" in done[-1]["headline"].lower()
    assert AR._current == {}, "completion must clear the working state"
    assert AR.busy() is False

    AR._current = {"goal": "g", "orchestration_id": "o", "steps": []}
    AR._on_complete("o", Plan("failed", "failed"))
    failed = [d for ev, d in seen if ev == "complete"]
    assert failed[-1]["ok"] is False
    assert "failed" in failed[-1]["headline"].lower()


def test_progress_is_recorded_and_broadcast():
    class Result:
        agent_id = "ResearchAgent_x"
        result = "Found 6 sources about asyncio"
        success = True

    seen = []
    AR.subscribe(lambda ev, d: seen.append((ev, d)))
    AR._current = {"goal": "g", "orchestration_id": "o", "steps": []}
    AR._on_progress("o", "task1", Result())
    steps = AR.progress()["steps"]
    assert steps, "the step must be recorded"
    assert "asyncio" in steps[-1]["text"]
    assert any(ev == "progress" for ev, _ in seen)


# ---------------------------------------------------------------------------
# 4. The assistant knows about them
# ---------------------------------------------------------------------------
def test_main_starts_the_agent_system():
    import main as M
    src = inspect.getsource(M.main)
    assert "agent_runtime" in src, "the runner never starts the agents"
    assert "_agent_runtime.start()" in src


def test_agent_task_delegates_to_the_orchestrator():
    """It used to submit to a TaskQueue whose worker was never started, so the
    objective was accepted and then silently never happened."""
    import main as M
    src = inspect.getsource(M)
    assert "agent_runtime" in src
    assert "_ar.submit(" in src, "agent_task must route through the orchestrator"
    # the dead path must be gone
    assert "get_queue().submit(goal=" not in src


def _decl(name: str) -> dict:
    import main as M
    for entry in M.TOOL_DECLARATIONS:
        if isinstance(entry, dict) and entry.get("name") == name:
            return entry
    raise AssertionError(f"tool {name} is not advertised")


def test_a_status_tool_is_advertised():
    """Principle 9: the model can be asked what the team is doing."""
    decl = _decl("agent_status")
    assert "agent" in decl["description"].lower()


def test_the_delegation_tool_documents_the_objective_flow():
    desc = _decl("agent_task")["description"].lower()
    assert "delegate" in desc
    assert "objective" in desc


def test_agents_cannot_act_without_a_user_turn():
    """The delegation tool must stay behind the same tool gate as every other
    tool, or it becomes an unprompted action."""
    import main as M
    src = inspect.getsource(M.JarvisLive._execute_tool)
    assert "_tool_gate_open" in inspect.getsource(M.JarvisLive) or True
    assert "_tool_gate_open" in inspect.getsource(M.JarvisLive)


def test_the_tools_panel_lists_the_real_tools():
    """It showed an empty list: TOOL_DECLARATIONS is a list of dicts and was
    being read as a mapping."""
    import command_panels as CP
    names = CP._tool_names()
    assert len(names) > 20, f"only found {len(names)} tools"
    assert "agent_task" in names
    assert "agent_status" in names
    title, sub, html = CP.build_view("tools", {})
    assert "TOOLS THE ASSISTANT CAN CALL" in html
    assert "agent_task" in html


def test_the_agents_panel_shows_the_registry_not_placeholders():
    import re
    import command_panels as CP
    AR.start()
    title, sub, html = CP.build_view("agents", {})
    text = re.sub(r"<[^>]+>", " ", html)
    assert "Research Agent" in text
    assert "Document Agent" in text
    assert "registered" in text
    # the unregistered slots must say so rather than pretend to exist
    assert "not registered" in text
    # and it must be a table, because Qt's rich text ignores div borders
    assert "<table" in html
    assert "display:flex" not in html


def test_agent_status_panel_reports_live_state():
    import command_panels as CP
    AR.start()
    title, sub, html = CP.build_view("agent_status", {})
    assert "AGENT STATUS" in title
    assert "registered" in html.lower()
