"""HELIX manager layer between JARVIS and specialist agents.

The manager owns the task contract and lifecycle while the existing
``AgentOrchestrator`` continues to execute specialist work.
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional

from agent.orchestrator import AgentOrchestrator


class HelixTaskStatus(Enum):
    CREATED = "created"
    ACCEPTED = "accepted"
    ANALYZING = "analyzing"
    PLANNED = "planned"
    DELEGATED = "delegated"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


_TERMINAL = {
    HelixTaskStatus.COMPLETED,
    HelixTaskStatus.FAILED,
    HelixTaskStatus.CANCELLED,
}


@dataclass
class HelixTask:
    task_id: str
    source: str
    task: str
    objective: str
    context: Dict[str, Any] = field(default_factory=dict)
    requirements: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    expected_output: str = ""
    priority: str = "normal"
    references: list[str] = field(default_factory=list)
    status: HelixTaskStatus = HelixTaskStatus.CREATED
    orchestration_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    events: list[dict] = field(default_factory=list)
    result: Optional[dict] = None
    error: str = ""
    request_key: str = ""

    def transition(self, status: HelixTaskStatus, detail: str = "") -> None:
        self.status = status
        self.updated_at = time.time()
        event = {"status": status.value, "at": self.updated_at}
        if detail:
            event["detail"] = detail
        self.events.append(event)

    def receipt(self, duplicate: bool = False) -> dict:
        return {
            "task_id": self.task_id,
            "source": self.source,
            "assigned_to": "HELIX",
            "task": self.task,
            "objective": self.objective,
            "priority": self.priority,
            "status": self.status.value,
            "orchestration_id": self.orchestration_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "duplicate": duplicate,
        }

    def report(self) -> dict:
        data = self.receipt()
        data.update({
            "context": self.context,
            "requirements": self.requirements,
            "constraints": self.constraints,
            "expected_output": self.expected_output,
            "references": self.references,
            "events": list(self.events),
            "result": self.result,
            "error": self.error,
        })
        return data


class HelixManager:
    """Receive JARVIS tasks, delegate them, and return verified reports."""

    def __init__(self, orchestrator: AgentOrchestrator):
        self._orchestrator = orchestrator
        self._lock = threading.RLock()
        self._tasks: Dict[str, HelixTask] = {}
        self._active_keys: Dict[str, str] = {}

    @staticmethod
    def _key(objective: str, request_id: Optional[str]) -> str:
        if request_id:
            return f"request:{request_id.strip()}"
        return "objective:" + " ".join(objective.lower().split())

    @staticmethod
    def _normalise_priority(priority: str) -> str:
        value = str(priority or "normal").lower().strip()
        return value if value in {"low", "normal", "high"} else "normal"

    def submit(
        self,
        task: str,
        *,
        source: str = "JARVIS",
        objective: Optional[str] = None,
        context: Optional[dict] = None,
        requirements: Optional[list[str]] = None,
        constraints: Optional[list[str]] = None,
        expected_output: str = "",
        priority: str = "normal",
        references: Optional[list[str]] = None,
        request_id: Optional[str] = None,
        on_progress: Optional[Callable] = None,
        on_complete: Optional[Callable] = None,
    ) -> dict:
        objective = str(objective or task or "").strip()
        task = str(task or objective).strip()
        if not task:
            return {"ok": False, "error": "No task given."}
        if not isinstance(context, (dict, type(None))):
            return {"ok": False, "error": "Context must be an object."}

        request_key = self._key(objective, request_id)
        with self._lock:
            existing_id = self._active_keys.get(request_key)
            if existing_id:
                existing = self._tasks.get(existing_id)
                if existing and existing.status not in _TERMINAL:
                    return {"ok": True, **existing.receipt(duplicate=True),
                            "message": "Duplicate task ignored; existing HELIX task is active."}

            record = HelixTask(
                task_id=f"helix_{uuid.uuid4().hex[:12]}",
                source=str(source or "JARVIS"),
                task=task,
                objective=objective,
                context=dict(context or {}),
                requirements=list(requirements or []),
                constraints=list(constraints or []),
                expected_output=str(expected_output or ""),
                priority=self._normalise_priority(priority),
                references=list(references or []),
                request_key=request_key,
            )
            record.transition(HelixTaskStatus.ACCEPTED, "Task received from JARVIS")
            self._tasks[record.task_id] = record
            self._active_keys[request_key] = record.task_id

        record.transition(HelixTaskStatus.ANALYZING)
        record.transition(HelixTaskStatus.PLANNED)
        try:
            orchestration_id = self._orchestrator.create_orchestration(
                objective,
                context=record.context,
                priority=record.priority,
                on_progress=lambda oid, tid, result: self._progress(
                    record, oid, tid, result, on_progress
                ),
                on_complete=lambda oid, plan: self._complete(
                    record, oid, plan, on_complete
                ),
            )
        except Exception as exc:
            with self._lock:
                record.error = str(exc)
                record.transition(HelixTaskStatus.FAILED, record.error)
                self._active_keys.pop(request_key, None)
            return {"ok": False, "error": f"Could not start HELIX task: {exc}",
                    **record.receipt()}

        with self._lock:
            record.orchestration_id = orchestration_id
            record.transition(HelixTaskStatus.DELEGATED)
        return {
            "ok": True,
            **record.receipt(),
            "message": f"Task accepted by HELIX ({record.task_id}) and delegated.",
        }

    def _progress(self, record, orchestration_id, task_id, result, callback):
        with self._lock:
            if record.status not in _TERMINAL:
                record.transition(HelixTaskStatus.IN_PROGRESS)
        if callback:
            callback(orchestration_id, task_id, result)

    def _complete(self, record, orchestration_id, plan, callback):
        failed = [r for r in plan.results.values()
                  if getattr(getattr(r, "status", None), "value", "") == "failed"]
        with self._lock:
            record.transition(HelixTaskStatus.REVIEWING)
            record.result = {
                "orchestration_id": orchestration_id,
                "status": getattr(getattr(plan, "status", None), "value", "unknown"),
                "tasks": {key: value.to_dict() for key, value in plan.results.items()},
            }
            if failed or getattr(getattr(plan, "status", None), "value", "") != "completed":
                record.error = "One or more delegated tasks failed."
                record.transition(HelixTaskStatus.FAILED, record.error)
            else:
                record.transition(HelixTaskStatus.COMPLETED, "Results verified by HELIX")
            self._active_keys.pop(record.request_key, None)
            report = record.report()
        if callback:
            callback(orchestration_id, plan)

    def get(self, task_id: str) -> Optional[dict]:
        with self._lock:
            task = self._tasks.get(task_id)
            return task.report() if task else None

    def cancel(self, task_id: str) -> bool:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task or task.status in _TERMINAL:
                return False
            task.transition(HelixTaskStatus.CANCELLED, "Cancelled by JARVIS")
            self._active_keys.pop(task.request_key, None)
            orchestration_id = task.orchestration_id
        if orchestration_id:
            self._orchestrator.cancel_orchestration(orchestration_id)
        return True

    def list_tasks(self) -> list[dict]:
        with self._lock:
            return [task.report() for task in self._tasks.values()]
