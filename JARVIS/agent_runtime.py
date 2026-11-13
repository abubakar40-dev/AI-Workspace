"""
One place that owns the agent system.

The agents under ``agent/`` already existed and worked, but nothing started
them: ``main.py`` never imported the orchestrator, and ``agent_task`` submitted
to a ``TaskQueue`` whose worker thread was never started, so a delegated goal
sat in a queue forever and the GUI showed six hardcoded placeholder cards.

This module is the seam. It starts the orchestrator and the supervisor once,
routes objectives to the orchestrator (which is the CEO/delegation layer in the
target architecture), and exposes the live registry state to both the assistant
and the Command Center. It adds no new agent logic -- Principle 4, reuse what
is there.
"""

from __future__ import annotations

import threading
import time
from typing import Callable

_lock = threading.RLock()
_orchestrator = None
_supervisor = None
_manager = None
_listeners: list[Callable[[str, dict], None]] = []
_current: dict = {}          # the objective being worked on right now
_history: list[dict] = []


def _log(event: str, data: dict | None = None) -> None:
    """Tell whoever is watching -- the GUI feed and the console."""
    payload = data or {}
    for fn in list(_listeners):
        try:
            fn(event, payload)
        except Exception:
            pass


def subscribe(callback: Callable[[str, dict], None]) -> None:
    with _lock:
        if callback not in _listeners:
            _listeners.append(callback)


def start() -> bool:
    """Start the orchestrator and the supervisor. Idempotent."""
    global _orchestrator, _supervisor, _manager
    with _lock:
        if _orchestrator is not None:
            return True
        # The supervisor starts the orchestrator in its own constructor, so
        # start it first and only fall back to starting the orchestrator
        # directly. Starting both made the log claim two orchestrators when
        # there is only ever one worker thread.
        try:
            from agent.supervisor import Supervisor
            _supervisor = Supervisor()
            _supervisor.start()
        except Exception as exc:
            print(f"[Agents] supervisor unavailable: {exc}")
            _supervisor = None
        try:
            from agent.orchestrator import AgentOrchestrator
            _orchestrator = getattr(_supervisor, "_orchestrator", None)
            if _orchestrator is None:
                _orchestrator = AgentOrchestrator()
                _orchestrator.start()
        except Exception as exc:
            print(f"[Agents] orchestrator unavailable: {exc}")
            _orchestrator = None
        if _orchestrator is not None:
            try:
                from agent.helix_manager import HelixManager
                _manager = HelixManager(_orchestrator)
            except Exception as exc:
                print(f"[Agents] HELIX manager unavailable: {exc}")
                _manager = None
        ok = _orchestrator is not None
        stats = registry_stats()
        threads = [t.name for t in threading.enumerate()
                   if t.name == "AgentOrchestrator"]
        print(f"[Agents] started: {stats.get('total', 0)} agents "
              f"({', '.join(f'{k}={v}' for k, v in stats.get('by_type', {}).items())}), "
              f"{len(threads)} orchestrator worker(s)")
        _log("started", stats)
        return ok


def orchestrator():
    """The live orchestrator, or None when the agent system is unavailable."""
    start()
    return _orchestrator


def manager():
    """Return the HELIX manager that fronts the specialist orchestrator."""
    start()
    return _manager


# ---------------------------------------------------------------------------
# Delegation
# ---------------------------------------------------------------------------
def submit(
    goal: str,
    *,
    objective: str | None = None,
    context: dict | None = None,
    priority: str = "normal",
    request_id: str | None = None,
    requirements: list[str] | None = None,
    constraints: list[str] | None = None,
    expected_output: str = "",
    references: list[str] | None = None,
) -> dict:
    """Hand a high-level objective to the orchestrator.

    The orchestrator decomposes it, assigns the pieces to the right agents,
    respects dependencies and shares data between them. Returns a receipt the
    assistant can read back, including whether the objective was accepted --
    never assume it worked (Principle 5).
    """
    global _current

    goal = str(goal or "").strip()
    if not goal:
        return {"ok": False, "error": "No objective given."}

    helix = manager()
    if helix is None:
        return {"ok": False, "error": "The agent system is unavailable."}

    with _lock:
        _current = {"goal": goal, "started": time.time(), "steps": [],
                    "orchestration_id": None}

    # The orchestrator calls these as (orchestration_id, task_id, result) and
    # (orchestration_id, plan) -- three and two positional arguments. An
    # earlier single-argument callback raised inside the worker thread and no
    # progress ever reached the GUI.
    def on_progress(oid, task_id, result) -> None:
        _on_progress(oid, task_id, result)

    def on_complete(oid, plan) -> None:
        _on_complete(oid, plan)

    receipt = helix.submit(
        goal,
        source="JARVIS",
        objective=objective,
        context=context,
        priority=priority,
        request_id=request_id,
        requirements=requirements,
        constraints=constraints,
        expected_output=expected_output,
        references=references,
        on_progress=on_progress,
        on_complete=on_complete,
    )
    if not receipt.get("ok"):
        with _lock:
            _current = {}
        return receipt

    with _lock:
        _current["orchestration_id"] = receipt.get("orchestration_id")
        _current["task_id"] = receipt.get("task_id")
        entry = {"goal": goal, "id": receipt.get("orchestration_id"),
                 "task_id": receipt.get("task_id"), "started": time.time(), "done": False}
        _history.append(entry)
        del _history[:-20]
    _log("submitted", {"goal": goal, "id": receipt.get("orchestration_id"),
                       "task_id": receipt.get("task_id")})
    receipt["goal"] = goal
    receipt["message"] = (
        f"Objective accepted by HELIX and delegated "
        f"({receipt.get('task_id')}). I will report when it is verified."
    )
    return receipt


def task_status(task_id: str) -> dict | None:
    helix = manager()
    return helix.get(task_id) if helix else None


def cancel(task_id: str) -> bool:
    helix = manager()
    return bool(helix and helix.cancel(task_id))


def _on_progress(oid, task_id, result) -> None:
    """One agent finished a step. Turn it into something the operator can read."""
    goal_text = getattr(result, "result", None) or ""
    agent_id = getattr(result, "agent_id", "") or ""
    ok = getattr(result, "success", None)
    with _lock:
        agent_name = agent_id
        for agent in registry():
            if agent.get("agent_id") == agent_id:
                agent_name = agent["name"]
                break
        label = f"{agent_name}: {_first_line(goal_text)}" if goal_text \
            else f"{agent_name}: step complete"
        if ok is False:
            label = f"{agent_name}: step failed"
        steps = _current.setdefault("steps", [])
        if not steps or steps[-1]["text"] != label:
            steps.append({"text": label, "agent": agent_name, "at": time.time()})
            del steps[:-30]
    _log("progress", {"agent": agent_name, "message": label,
                      "success": ok, "task_id": task_id})


def _first_line(text: str, limit: int = 90) -> str:
    line = str(text or "").strip().splitlines()
    line = line[0] if line else ""
    return line[:limit]


def _on_complete(oid, plan) -> None:
    """The objective finished. Report the outcome honestly, including failure."""
    global _current

    status = getattr(getattr(plan, "status", None), "value", "unknown")
    tasks = list(getattr(plan, "agent_tasks", []) or [])
    done = [t for t in tasks if getattr(t, "status", None)
            and getattr(t.status, "value", "") == "completed"]
    failed = [t for t in tasks if getattr(t, "status", None)
              and getattr(t.status, "value", "") == "failed"]
    succeeded = status == "completed" and not failed

    with _lock:
        goal = _current.get("goal", "")
        for entry in _history:
            if entry["id"] == oid:
                entry["done"] = True
                entry["ok"] = succeeded
                entry["summary"] = f"{len(done)}/{len(tasks)} steps completed"

    if succeeded:
        headline = f"Objective complete: {len(done)} of {len(tasks)} steps verified."
    elif failed:
        headline = (f"Objective finished with {len(failed)} failed step(s) "
                    f"of {len(tasks)}.")
    else:
        headline = f"Objective ended with status {status}."

    _log("complete", {"goal": goal, "headline": headline, "ok": succeeded,
                      "steps": len(done), "total": len(tasks),
                      "summary": _first_line(goal)})
    with _lock:
        _current = {}


# ---------------------------------------------------------------------------
# Observability
# ---------------------------------------------------------------------------
def registry() -> list[dict]:
    """Every registered agent with its live status."""
    try:
        from agent.agent_base import get_registry
        return get_registry().get_all_statuses()
    except Exception:
        return []


def registry_stats() -> dict:
    try:
        from agent.agent_base import get_registry
        return get_registry().get_total_stats()
    except Exception:
        return {"total": 0, "by_type": {}, "by_status": {}}


def orchestrations() -> list[dict]:
    orch = _orchestrator
    if orch is None:
        return []
    try:
        return orch.get_all_orchestrations()
    except Exception:
        return []


def busy() -> bool:
    """True while an agent is actually working -- drives the GUI's live state."""
    return any(a.get("status") in ("running", "starting")
               for a in registry()) or bool(_current)


def progress() -> dict:
    """What the assistant should say when asked what it is doing."""
    agents = registry()
    working = [a for a in agents
               if a.get("status") in ("running", "starting")]
    with _lock:
        goal = _current.get("goal", "")
        steps = list(_current.get("steps", []))[-6:]
    return {
        "agents_total": len(agents),
        "working": [{"name": a["name"], "task": a.get("current_task")}
                    for a in working],
        "goal": goal,
        "steps": steps,
        "stats": registry_stats(),
    }


#: The page has exactly six agent cards, so map the real roster onto six slots
#: by type. Anything beyond the first agent of a type is reported as idle
#: rather than invented.
_SLOT_ORDER = ("research", "document", "code", "analysis", "web", "file")
_SLOT_META = {
    "research":  ("Research Agent",  "\U0001F50D", "#101f38", "#7ac8ff"),
    "document":  ("Document Agent",  "\u270E",     "#1c1533", "var(--purple)"),
    "code":      ("Code Agent",      "{ }",       "#123024", "var(--green)"),
    "analysis":  ("Analysis Agent",  "\u25D0",     "#3a2a10", "var(--amber)"),
    "web":       ("Web Agent",       "\u25CE",     "#101f38", "#7ac8ff"),
    "file":      ("File Agent",      "\u2611",     "#101f38", "#7ac8ff"),
}
_STATUS_COPY = {
    "idle": "Standby", "running": "Working", "starting": "Starting",
    "waiting": "Waiting", "completed": "Done", "failed": "Failed",
    "pending": "Queued", "cancelled": "Cancelled",
}


def agent_rows() -> list[dict]:
    """Live rows for the Command Center's six agent cards."""
    by_type: dict[str, dict] = {}
    for agent in registry():
        by_type.setdefault(agent.get("type", ""), agent)

    rows = []
    for slot in _SLOT_ORDER:
        meta = _SLOT_META[slot]
        agent = by_type.get(slot)
        if agent is None:
            rows.append({"name": meta[0], "icon": meta[1],
                         "bg": f"background:{meta[2]};color:{meta[3]};",
                         "active": False, "status": "unavailable",
                         "detail": "not registered", "task": None,
                         "real": False})
            continue
        status = agent.get("status", "idle")
        rows.append({
            "name": meta[0],
            "icon": meta[1],
            "bg": f"background:{meta[2]};color:{meta[3]};",
            "active": status in ("running", "starting"),
            "status": _STATUS_COPY.get(status, status),
            "detail": f"{agent.get('name', '')} · {status}",
            "task": agent.get("current_task"),
            "real": True,
        })
    return rows


def status_text() -> str:
    """A spoken summary, for the assistant to read out when asked."""
    info = progress()
    if not info["agents_total"]:
        return "No agents are registered."
    if not info["working"]:
        return (f"{info['agents_total']} agents registered, all idle. "
                f"Give me an objective and I will delegate it.")
    parts = [f"Working on {w['name']}"
             + (f": {w['task']}" if w.get("task") else "")
             for w in info["working"]]
    return f"{len(info['working'])} of {info['agents_total']} agents busy. " \
           + "; ".join(parts)
