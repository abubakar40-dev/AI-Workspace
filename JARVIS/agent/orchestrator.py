# agent/orchestrator.py
# Orchestrates multiple agents, manages dependencies, coordinates complex tasks

import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Set
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.agent_base import (
    BaseAgent, AgentRegistry, AgentType, AgentStatus, AgentResult, AgentTask, get_registry
)
from agent.research_agent import ResearchAgent
from agent.document_agent import DocumentAgent
from agent.code_agent import CodeAgent


class OrchestrationStatus(Enum):
    PLANNING = "planning"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class OrchestrationPlan:
    """Plan for multi-agent orchestration"""
    orchestration_id: str
    goal: str
    agent_tasks: List[AgentTask] = field(default_factory=list)
    status: OrchestrationStatus = OrchestrationStatus.PLANNING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    results: Dict[str, AgentResult] = field(default_factory=dict)
    error: str = ""
    on_progress: Optional[Callable] = None
    on_complete: Optional[Callable] = None


class AgentOrchestrator:
    """Orchestrates multiple agents to complete complex tasks"""
    
    def __init__(self):
        self._registry = get_registry()
        self._orchestrations: Dict[str, OrchestrationPlan] = {}
        self._lock = threading.Lock()
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        
        # Initialize default agents
        self._ensure_default_agents()
    
    def _ensure_default_agents(self):
        """Ensure we have at least one agent of each type"""
        defaults = [
            (AgentType.RESEARCH, ResearchAgent),
            (AgentType.DOCUMENT, DocumentAgent),
            (AgentType.CODE, CodeAgent),
        ]
        
        for agent_type, agent_class in defaults:
            agents = self._registry.get_agents_by_type(agent_type)
            if not agents:
                agent = agent_class()
                self._registry.register(agent)
    
    def start(self):
        """Start the orchestrator"""
        if self._running:
            return
        self._running = True
        self._worker_thread = threading.Thread(
            target=self._orchestration_loop,
            daemon=True,
            name="AgentOrchestrator"
        )
        self._worker_thread.start()
        print("[Orchestrator] ✅ Started")
    
    def stop(self):
        """Stop the orchestrator"""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
        print("[Orchestrator] 🔴 Stopped")
    
    def create_orchestration(
        self,
        goal: str,
        on_progress: Callable = None,
        on_complete: Callable = None,
        context: Optional[Dict[str, Any]] = None,
        priority: str = "normal",
    ) -> str:
        """Create a new multi-agent orchestration for a complex goal"""
        orchestration_id = f"orch_{str(uuid.uuid4())[:8]}"
        
        # Analyze goal and create agent tasks
        agent_tasks = self._decompose_goal(goal)
        for task in agent_tasks:
            task.context.update(context or {})
            task.priority = {"high": 1, "normal": 2, "low": 3}.get(priority, 2)
        
        plan = OrchestrationPlan(
            orchestration_id=orchestration_id,
            goal=goal,
            agent_tasks=agent_tasks,
            on_progress=on_progress,
            on_complete=on_complete
        )
        
        with self._lock:
            self._orchestrations[orchestration_id] = plan
        
        print(f"[Orchestrator] 📋 Created orchestration: {orchestration_id} with {len(agent_tasks)} agent tasks")
        return orchestration_id
    
    def _decompose_goal(self, goal: str) -> List[AgentTask]:
        """Decompose a complex goal into agent tasks with dependencies"""
        goal_lower = goal.lower()
        tasks = []
        
        # Determine what types of agents are needed
        needs_research = any(kw in goal_lower for kw in [
            "research", "find", "search", "analyze", "investigate", "study", "explore",
            "information", "data", "facts", "statistics", "market", "trend"
        ])
        
        needs_document = any(kw in goal_lower for kw in [
            "pdf", "report", "document", "write", "create", "generate", "make",
            "presentation", "ppt", "slides", "spreadsheet", "excel", "xlsx"
        ])
        
        needs_code = any(kw in goal_lower for kw in [
            "code", "program", "script", "develop", "build", "implement",
            "debug", "refactor", "test", "api", "function", "class"
        ])
        
        # Create tasks in dependency order
        task_id = 0
        
        # Research first (if needed)
        research_task = None
        if needs_research:
            task_id += 1
            research_task = AgentTask(
                task_id=f"research_{task_id}",
                goal=f"Research and gather comprehensive information for: {goal}",
                agent_type=AgentType.RESEARCH,
                priority=1,
            )
            tasks.append(research_task)
        
        # Document creation (depends on research)
        if needs_document:
            task_id += 1
            doc_type = "report"
            if "presentation" in goal_lower or "ppt" in goal_lower or "slides" in goal_lower:
                doc_type = "presentation"
            elif "spreadsheet" in goal_lower or "excel" in goal_lower or "xlsx" in goal_lower:
                doc_type = "spreadsheet"
            
            deps = [research_task.task_id] if research_task else []
            doc_task = AgentTask(
                task_id=f"document_{task_id}",
                goal=f"Create a professional {doc_type} based on research for: {goal}",
                agent_type=AgentType.DOCUMENT,
                dependencies=deps,
                priority=2,
            )
            tasks.append(doc_task)
        
        # Code development (may depend on research)
        if needs_code:
            task_id += 1
            deps = [research_task.task_id] if research_task else []
            code_task = AgentTask(
                task_id=f"code_{task_id}",
                goal=f"Implement code solution for: {goal}",
                agent_type=AgentType.CODE,
                dependencies=deps,
                priority=2,
            )
            tasks.append(code_task)
        
        # If no specific type detected, default to research then general
        if not tasks:
            task_id += 1
            research_task = AgentTask(
                task_id=f"research_{task_id}",
                goal=f"Research and provide comprehensive answer for: {goal}",
                agent_type=AgentType.RESEARCH,
                priority=1,
            )
            tasks.append(research_task)
            
            task_id += 1
            general_task = AgentTask(
                task_id=f"general_{task_id}",
                goal=f"Synthesize and present findings for: {goal}",
                agent_type=AgentType.GENERAL,
                dependencies=[research_task.task_id],
                priority=2,
            )
            tasks.append(general_task)
        
        return tasks
    
    def _orchestration_loop(self):
        """Main orchestration loop"""
        while self._running:
            with self._lock:
                # Find orchestrations that need processing
                for plan in list(self._orchestrations.values()):
                    if plan.status == OrchestrationStatus.PLANNING:
                        plan.status = OrchestrationStatus.RUNNING
                        plan.started_at = time.time()
                        self._start_orchestration(plan)
                    elif plan.status == OrchestrationStatus.RUNNING:
                        self._check_orchestration_progress(plan)
            
            time.sleep(1)
    
    def _start_orchestration(self, plan: OrchestrationPlan):
        """Start executing an orchestration"""
        # Start tasks that have no dependencies or whose dependencies are met
        for task in plan.agent_tasks:
            if self._can_start_task(task, plan):
                self._start_agent_task(task, plan)
    
    def _can_start_task(self, task: AgentTask, plan: OrchestrationPlan) -> bool:
        """Check if a task can start (dependencies met)"""
        if task.status != AgentStatus.PENDING:
            return False
        
        for dep_id in task.dependencies:
            dep_result = plan.results.get(dep_id)
            if not dep_result or dep_result.status != AgentStatus.COMPLETED:
                return False
        
        return True
    
    def _start_agent_task(self, task: AgentTask, plan: OrchestrationPlan):
        """Start an agent task"""
        task.status = AgentStatus.WAITING
        
        # Get appropriate agent
        agent = self._registry.get_available_agent(task.agent_type)
        if not agent:
            # Create new agent if none available
            agent = self._create_agent_for_type(task.agent_type)
        
        # Prepare context from completed dependencies
        context = dict(task.context)
        for dep_id in task.dependencies:
            if dep_id in plan.results:
                context[dep_id] = plan.results[dep_id].to_dict()
        
        task.context = context
        
        # Define completion callback
        def on_task_complete(task_id: str, result: AgentResult):
            plan.results[task_id] = result
            
            # Notify progress
            if plan.on_progress:
                try:
                    plan.on_progress(plan.orchestration_id, task_id, result)
                except Exception:
                    pass
            
            # Check if we can start more tasks
            self._check_and_start_pending(plan)
        
        task.on_complete = on_task_complete
        
        # Execute in background thread
        thread = threading.Thread(
            target=self._run_agent_task,
            args=(agent, task, plan),
            daemon=True,
            name=f"AgentTask-{task.task_id}"
        )
        thread.start()
        
        task.status = AgentStatus.RUNNING
        print(f"[Orchestrator] ▶️ Started {task.task_id} on {agent.name}")
    
    def _run_agent_task(self, agent: BaseAgent, task: AgentTask, plan: OrchestrationPlan):
        """Run an agent task"""
        try:
            result = agent.execute_task(task)
            # Callback will be called by agent
        except Exception as e:
            print(f"[Orchestrator] ❌ Agent task {task.task_id} failed: {e}")
            task.status = AgentStatus.FAILED
            error_result = AgentResult(
                agent_id=agent.agent_id,
                agent_type=agent.agent_type.value,
                goal=task.goal,
                status=AgentStatus.FAILED,
                error=str(e),
                started_at=task.started_at or time.time(),
                completed_at=time.time()
            )
            plan.results[task.task_id] = error_result
            if plan.on_progress:
                try:
                    plan.on_progress(plan.orchestration_id, task.task_id, error_result)
                except Exception:
                    pass
            if task.on_complete:
                try:
                    task.on_complete(task.task_id, error_result)
                except Exception:
                    pass
    
    def _check_and_start_pending(self, plan: OrchestrationPlan):
        """Check for tasks that can now start"""
        for task in plan.agent_tasks:
            if self._can_start_task(task, plan):
                self._start_agent_task(task, plan)
    
    def _check_orchestration_progress(self, plan: OrchestrationPlan):
        """Check if orchestration is complete"""
        failed_ids = {
            task.task_id for task in plan.agent_tasks
            if task.status in (AgentStatus.FAILED, AgentStatus.CANCELLED)
        }
        for task in plan.agent_tasks:
            if task.status in (AgentStatus.PENDING, AgentStatus.WAITING) and any(
                dep_id in failed_ids for dep_id in task.dependencies
            ):
                task.status = AgentStatus.FAILED
                task.result = AgentResult(
                    agent_id="orchestrator",
                    agent_type="orchestrator",
                    goal=task.goal,
                    status=AgentStatus.FAILED,
                    error="A dependency failed or was cancelled.",
                    started_at=task.created_at,
                    completed_at=time.time(),
                )

        all_done = True
        any_failed = False
        
        for task in plan.agent_tasks:
            if task.status in (AgentStatus.PENDING, AgentStatus.WAITING, AgentStatus.RUNNING):
                all_done = False
            elif task.status == AgentStatus.FAILED:
                any_failed = True
        
        if all_done:
            plan.status = OrchestrationStatus.FAILED if any_failed else OrchestrationStatus.COMPLETED
            plan.completed_at = time.time()
            
            if plan.on_complete:
                try:
                    plan.on_complete(plan.orchestration_id, plan)
                except Exception:
                    pass
            
            print(f"[Orchestrator] ✅ Orchestration {plan.orchestration_id} {plan.status.value}")
    
    def _create_agent_for_type(self, agent_type: AgentType) -> BaseAgent:
        """Create a new agent for the given type"""
        if agent_type == AgentType.RESEARCH:
            agent = ResearchAgent()
        elif agent_type == AgentType.DOCUMENT:
            agent = DocumentAgent()
        elif agent_type == AgentType.CODE:
            agent = CodeAgent()
        else:
            agent = BaseAgent(agent_type)
        
        self._registry.register(agent)
        return agent
    
    def get_orchestration_status(self, orchestration_id: str) -> Optional[Dict]:
        """Get status of an orchestration"""
        with self._lock:
            plan = self._orchestrations.get(orchestration_id)
            if not plan:
                return None
            
            return {
                "orchestration_id": plan.orchestration_id,
                "goal": plan.goal,
                "status": plan.status.value,
                "created_at": plan.created_at,
                "started_at": plan.started_at,
                "completed_at": plan.completed_at,
                "tasks": [
                    {
                        "task_id": t.task_id,
                        "goal": t.goal[:60],
                        "agent_type": t.agent_type.value,
                        "status": t.status.value,
                        "dependencies": t.dependencies,
                    }
                    for t in plan.agent_tasks
                ],
                "completed_tasks": len([t for t in plan.agent_tasks if t.status == AgentStatus.COMPLETED]),
                "total_tasks": len(plan.agent_tasks),
            }
    
    def get_all_orchestrations(self) -> List[Dict]:
        """Get all orchestrations"""
        with self._lock:
            return [
                {
                    "orchestration_id": p.orchestration_id,
                    "goal": p.goal[:80],
                    "status": p.status.value,
                    "progress": f"{len([t for t in p.agent_tasks if t.status == AgentStatus.COMPLETED])}/{len(p.agent_tasks)}",
                }
                for p in self._orchestrations.values()
            ]
    
    def cancel_orchestration(self, orchestration_id: str) -> bool:
        """Cancel an orchestration"""
        with self._lock:
            plan = self._orchestrations.get(orchestration_id)
            if not plan:
                return False
            
            plan.status = OrchestrationStatus.CANCELLED
            for task in plan.agent_tasks:
                task.cancel_flag.set()
            
            return True


# Global orchestrator
_orchestrator = AgentOrchestrator()
_orchestrator_lock = threading.Lock()


def get_orchestrator() -> AgentOrchestrator:
    global _orchestrator
    with _orchestrator_lock:
        return _orchestrator


def orchestrate(goal: str, on_progress: Callable = None, on_complete: Callable = None) -> str:
    """Convenience function to start an orchestration"""
    orch = get_orchestrator()
    if not _orchestrator._running:
        orch.start()
    return orch.create_orchestration(goal, on_progress, on_complete)