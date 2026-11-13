# agent/agent_base.py
# Base classes for specialized agents in JARVIS multi-agent system

import threading
import time
import uuid
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Any, Optional, Dict, List
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.planner import create_plan
from agent.executor import AgentExecutor
from agent.error_handler import analyze_error, generate_fix, ErrorDecision


class AgentStatus(Enum):
    PENDING = "pending"
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    WAITING = "waiting"  # Waiting for another agent's result
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentType(Enum):
    RESEARCH = "research"
    DOCUMENT = "document"
    CODE = "code"
    ANALYSIS = "analysis"
    WEB = "web"
    FILE = "file"
    GENERAL = "general"


@dataclass
class AgentResult:
    """Result from an agent execution"""
    agent_id: str
    agent_type: str
    goal: str
    status: AgentStatus
    data: Any = None
    error: str = ""
    started_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "goal": self.goal,
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration": (self.completed_at - self.started_at) if self.completed_at else None,
            "metadata": self.metadata
        }


@dataclass
class AgentTask:
    """A task assigned to an agent"""
    task_id: str
    goal: str
    agent_type: AgentType
    dependencies: List[str] = field(default_factory=list)  # Other agent task IDs to wait for
    priority: int = 2  # 1=high, 2=normal, 3=low
    context: Dict = field(default_factory=dict)  # Shared context/data from other agents
    status: AgentStatus = AgentStatus.PENDING
    result: Optional[AgentResult] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    cancel_flag: threading.Event = field(default_factory=threading.Event)
    on_progress: Optional[Callable] = None
    on_complete: Optional[Callable] = None


class BaseAgent:
    """Base class for all specialized agents"""
    
    def __init__(self, agent_type: AgentType, name: str = None):
        self.agent_type = agent_type
        self.name = name or agent_type.value
        self.agent_id = f"{self.name}_{str(uuid.uuid4())[:8]}"
        self.status = AgentStatus.IDLE
        self._executor = AgentExecutor()
        self._lock = threading.Lock()
        self._current_task: Optional[AgentTask] = None
        self._shared_data: Dict[str, Any] = {}  # Data shared with other agents
        self._subscribers: List[Callable] = []  # Callbacks for status updates
        
    def subscribe(self, callback: Callable):
        """Subscribe to agent status updates"""
        self._subscribers.append(callback)
        
    def _notify_progress(self, status: AgentStatus, message: str = ""):
        """Notify subscribers of progress"""
        with self._lock:
            self.status = status
            for cb in self._subscribers:
                try:
                    cb(self.agent_id, self.name, self.agent_type.value, status.value, message)
                except Exception:
                    pass
    
    def get_shared_data(self, key: str) -> Any:
        """Get data from shared context"""
        return self._shared_data.get(key)
    
    def set_shared_data(self, key: str, value: Any):
        """Set data in shared context"""
        self._shared_data[key] = value
    
    def prepare_context(self, task: AgentTask) -> str:
        """Prepare context string from dependencies' results"""
        if not task.context:
            return ""
        
        context_parts = []
        for dep_id, dep_result in task.context.items():
            if dep_result and isinstance(dep_result, dict):
                if dep_result.get("data"):
                    context_parts.append(f"=== Result from {dep_id} ===\n{dep_result['data'][:3000]}")
        
        if context_parts:
            return "\n\nCONTEXT FROM DEPENDENCIES:\n" + "\n\n".join(context_parts)
        return ""
    
    def execute_task(self, task: AgentTask) -> AgentResult:
        """Execute a task - to be overridden by subclasses"""
        with self._lock:
            self._current_task = task
        
        self._notify_progress(AgentStatus.STARTING, f"Starting task: {task.goal[:50]}")
        
        task.status = AgentStatus.RUNNING
        task.started_at = time.time()
        
        # Build context from dependencies
        context = self.prepare_context(task)
        
        # Create plan with context
        plan = create_plan(task.goal, context=context)
        
        # Execute with custom executor that reports progress
        result_text = self._execute_plan(plan, task)
        
        task.completed_at = time.time()
        
        # Create result object
        if task.cancel_flag.is_set():
            task.status = AgentStatus.CANCELLED
            agent_result = AgentResult(
                agent_id=self.agent_id,
                agent_type=self.agent_type.value,
                goal=task.goal,
                status=AgentStatus.CANCELLED,
                error="Task cancelled",
                started_at=task.started_at,
                completed_at=task.completed_at
            )
        elif self._is_error_result(result_text):
            task.status = AgentStatus.FAILED
            agent_result = AgentResult(
                agent_id=self.agent_id,
                agent_type=self.agent_type.value,
                goal=task.goal,
                status=AgentStatus.FAILED,
                data=result_text,
                error=result_text,
                started_at=task.started_at,
                completed_at=task.completed_at
            )
        else:
            task.status = AgentStatus.COMPLETED
            agent_result = AgentResult(
                agent_id=self.agent_id,
                agent_type=self.agent_type.value,
                goal=task.goal,
                status=AgentStatus.COMPLETED,
                data=result_text,
                started_at=task.started_at,
                completed_at=task.completed_at
            )
        
        task.result = agent_result
        
        # Store in shared data for other agents
        self.set_shared_data(task.task_id, agent_result.to_dict())
        
        self._notify_progress(task.status, f"Completed: {task.goal[:50]}")
        
        if task.on_complete:
            try:
                task.on_complete(task.task_id, agent_result)
            except Exception:
                pass
        
        return agent_result
    
    def _execute_plan(self, plan: dict, task: AgentTask) -> str:
        """Execute a plan step by step"""
        steps = plan.get("steps", [])
        if not steps:
            return "No valid plan created"
        
        completed_steps = []
        step_results = {}
        
        for step in steps:
            if task.cancel_flag.is_set():
                return "Task cancelled"
            
            step_num = step.get("step", "?")
            tool = step.get("tool", "")
            desc = step.get("description", "")
            params = step.get("parameters", {})
            
            # Inject context from previous steps
            from agent.executor import _inject_context
            params = _inject_context(params, tool, step_results, goal=task.goal)
            
            self._notify_progress(AgentStatus.RUNNING, f"Step {step_num}: {desc[:60]}")
            
            print(f"\n[{self.name}] ▶️ Step {step_num}: [{tool}] {desc}")
            
            attempt = 1
            step_ok = False
            
            while attempt <= 3:
                if task.cancel_flag.is_set():
                    return "Task cancelled"
                
                try:
                    from agent.executor import _call_tool
                    result = _call_tool(tool, params, None)
                    step_results[step_num] = result
                    completed_steps.append(step)
                    print(f"[{self.name}] ✅ Step {step_num} done")
                    step_ok = True
                    break
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"[{self.name}] ❌ Step {step_num} attempt {attempt} failed: {error_msg}")
                    
                    recovery = analyze_error(step, error_msg, attempt=attempt)
                    decision = recovery["decision"]
                    
                    if decision == ErrorDecision.RETRY:
                        attempt += 1
                        time.sleep(2)
                        continue
                    elif decision == ErrorDecision.SKIP:
                        completed_steps.append(step)
                        step_ok = True
                        break
                    elif decision == ErrorDecision.ABORT:
                        return f"Task aborted: {recovery.get('reason', '')}"
                    else:
                        fix_suggestion = recovery.get("fix_suggestion", "")
                        if fix_suggestion and tool != "generated_code":
                            try:
                                fixed_step = generate_fix(step, error_msg, fix_suggestion)
                                from agent.executor import _call_tool
                                res = _call_tool(fixed_step["tool"], fixed_step["parameters"], None)
                                step_results[step_num] = res
                                completed_steps.append(step)
                                step_ok = True
                                break
                            except Exception:
                                pass
                        
                        return f"Step failed: {error_msg}"
            
            if not step_ok:
                return f"Step {step_num} failed after retries"
        
        # Summarize
        return self._summarize(task.goal, completed_steps)
    
    def _is_error_result(self, result_text: str) -> bool:
        """Check if result text indicates a genuine error (not just content containing error words)"""
        if not result_text:
            return True
        
        result_lower = result_text.lower().strip()
        
        # Check for explicit error prefixes
        error_prefixes = [
            "error:", "failed:", "exception:", "traceback", 
            "task aborted", "task cancelled", "step failed",
            "aborted:", "cancelled:", "unavailable:", "not available"
        ]
        for prefix in error_prefixes:
            if result_lower.startswith(prefix):
                return True
        
        # Check for short error messages (likely genuine errors)
        if len(result_text) < 200 and any(word in result_lower for word in ["error", "failed", "exception", "traceback"]):
            return True
        
        # Long results with "error" or "failed" in content are likely research reports
        return False
    
    def _summarize(self, goal: str, completed_steps: list) -> str:
        """Summarize completed work"""
        try:
            from google import genai
            from agent.executor import _get_api_key
            client = genai.Client(api_key=_get_api_key(), http_options={"api_version": "v1beta"})
            steps_str = "\n".join(f"- {s.get('description', '')}" for s in completed_steps)
            prompt = (
                f'User goal: "{goal}"\n'
                f"Completed steps:\n{steps_str}\n\n"
                "Write a concise summary of what was accomplished. "
                "Be direct and factual."
            )
            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt,
            )
            return response.text.strip()
        except Exception:
            return f"Completed {len(completed_steps)} steps for: {goal[:60]}"
    
    def cancel_current(self):
        """Cancel current task"""
        if self._current_task:
            self._current_task.cancel_flag.set()
            self._notify_progress(AgentStatus.CANCELLED, "Task cancelled")


class AgentRegistry:
    """Registry for managing all agents"""
    
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._agents_by_type: Dict[AgentType, List[BaseAgent]] = {}
        self._lock = threading.Lock()
        
    def register(self, agent: BaseAgent):
        with self._lock:
            self._agents[agent.agent_id] = agent
            if agent.agent_type not in self._agents_by_type:
                self._agents_by_type[agent.agent_type] = []
            self._agents_by_type[agent.agent_type].append(agent)
            print(f"[Registry] ✅ Registered agent: {agent.name} ({agent.agent_id})")
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        return self._agents.get(agent_id)
    
    def get_agents_by_type(self, agent_type: AgentType) -> List[BaseAgent]:
        return self._agents_by_type.get(agent_type, [])
    
    def get_available_agent(self, agent_type: AgentType) -> Optional[BaseAgent]:
        """Get an idle agent of the specified type"""
        agents = self.get_agents_by_type(agent_type)
        for agent in agents:
            if agent.status == AgentStatus.IDLE:
                return agent
        return None
    
    def get_all_statuses(self) -> List[Dict]:
        with self._lock:
            return [
                {
                    "agent_id": a.agent_id,
                    "name": a.name,
                    "type": a.agent_type.value,
                    "status": a.status.value,
                    "current_task": a._current_task.goal[:50] if a._current_task else None
                }
                for a in self._agents.values()
            ]
    
    def get_total_stats(self) -> Dict:
        with self._lock:
            stats = {"total": len(self._agents), "by_type": {}, "by_status": {}}
            for agent in self._agents.values():
                t = agent.agent_type.value
                s = agent.status.value
                stats["by_type"][t] = stats["by_type"].get(t, 0) + 1
                stats["by_status"][s] = stats["by_status"].get(s, 0) + 1
            return stats


# Global registry
_registry = AgentRegistry()
_registry_lock = threading.Lock()


def get_registry() -> AgentRegistry:
    global _registry
    with _registry_lock:
        return _registry