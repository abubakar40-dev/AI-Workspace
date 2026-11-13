from __future__ import annotations

from types import SimpleNamespace

from agent.agent_base import AgentResult, AgentStatus
from agent.helix_manager import HelixManager, HelixTaskStatus


class FakeOrchestrator:
    def __init__(self):
        self.created = []
        self.cancelled = []

    def create_orchestration(self, goal, **kwargs):
        self.created.append((goal, kwargs))
        return "orch_test"

    def cancel_orchestration(self, orchestration_id):
        self.cancelled.append(orchestration_id)
        return True


def test_manager_returns_structured_receipt_and_deduplicates():
    orchestrator = FakeOrchestrator()
    manager = HelixManager(orchestrator)

    first = manager.submit(
        "Research memory architecture",
        source="JARVIS",
        request_id="retry-1",
        context={"constraints": ["use SQLite"]},
        priority="high",
    )
    second = manager.submit("Research memory architecture",
                            source="JARVIS", request_id="retry-1")

    assert first["ok"] is True
    assert first["assigned_to"] == "HELIX"
    assert first["status"] == HelixTaskStatus.DELEGATED.value
    assert second["task_id"] == first["task_id"]
    assert second["duplicate"] is True
    assert len(orchestrator.created) == 1


def test_manager_consolidates_verified_completion():
    orchestrator = FakeOrchestrator()
    manager = HelixManager(orchestrator)
    seen = []
    receipt = manager.submit("Create a report", on_complete=lambda *_: seen.append(True))
    record = manager._tasks[receipt["task_id"]]
    result = AgentResult(
        agent_id="document-1",
        agent_type="document",
        goal="Create a report",
        status=AgentStatus.COMPLETED,
        data="report ready",
    )
    plan = SimpleNamespace(
        status=AgentStatus.COMPLETED,
        results={"document_1": result},
    )

    manager._complete(record, "orch_test", plan, lambda *_: seen.append(True))

    assert manager.get(receipt["task_id"])["status"] == "completed"
    assert manager.get(receipt["task_id"])["result"]["tasks"]["document_1"]["data"] == "report ready"
    assert seen


def test_manager_cancellation_is_forwarded():
    orchestrator = FakeOrchestrator()
    manager = HelixManager(orchestrator)
    receipt = manager.submit("Build a prototype")

    assert manager.cancel(receipt["task_id"]) is True
    assert manager.get(receipt["task_id"])["status"] == "cancelled"
    assert orchestrator.cancelled == ["orch_test"]
