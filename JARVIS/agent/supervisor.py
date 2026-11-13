# agent/supervisor.py
# JARVIS CEO Supervisor - Real-time monitoring and progress reporting

import threading
import time
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.agent_base import AgentRegistry, AgentStatus, get_registry
from agent.orchestrator import get_orchestrator, OrchestrationStatus


@dataclass
class AgentSnapshot:
    """Snapshot of an agent's current state"""
    agent_id: str
    name: str
    type: str
    status: str
    current_task: Optional[str]
    progress_percent: int = 0
    last_update: float = field(default_factory=time.time)


@dataclass
class OrchestrationSnapshot:
    """Snapshot of an orchestration's current state"""
    orchestration_id: str
    goal: str
    status: str
    progress: str  # "3/5"
    tasks: List[Dict] = field(default_factory=list)
    started_at: Optional[float] = None
    elapsed_seconds: float = 0


class Supervisor:
    """JARVIS CEO Supervisor - Monitors all agents and orchestrations, provides real-time stats"""
    
    def __init__(self):
        self._registry = get_registry()
        self._orchestrator = get_orchestrator()
        self._lock = threading.Lock()
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._subscribers: List[Callable] = []  # Callbacks for real-time updates
        
        # Historical data for stats
        self._agent_history: List[Dict] = []  # Last 100 agent completions
        self._orchestration_history: List[Dict] = []  # Last 50 orchestrations
        self._start_time = time.time()
        
        # Stats
        self._total_tasks_completed = 0
        self._total_tasks_failed = 0
        self._total_orchestrations_completed = 0
        self._total_orchestrations_failed = 0
    
    def start(self):
        """Start the supervisor monitoring"""
        if self._running:
            return
        self._running = True
        self._orchestrator.start()
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="SupervisorMonitor"
        )
        self._monitor_thread.start()
        print("[Supervisor] ✅ CEO Supervisor started - monitoring all agents")
    
    def stop(self):
        """Stop the supervisor"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        print("[Supervisor] 🔴 Supervisor stopped")
    
    def subscribe(self, callback: Callable):
        """Subscribe to real-time updates"""
        self._subscribers.append(callback)
    
    def _notify_update(self, update_type: str, data: Dict):
        """Notify all subscribers of an update"""
        for cb in self._subscribers:
            try:
                cb(update_type, data)
            except Exception:
                pass
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self._running:
            try:
                # Get current snapshots
                agent_snapshots = self._get_agent_snapshots()
                orchestration_snapshots = self._get_orchestration_snapshots()
                
                # Notify subscribers
                self._notify_update("agent_status", {
                    "agents": [s.__dict__ for s in agent_snapshots],
                    "timestamp": time.time()
                })
                
                self._notify_update("orchestration_status", {
                    "orchestrations": [s.__dict__ for s in orchestration_snapshots],
                    "timestamp": time.time()
                })
                
                # Notify stats
                self._notify_update("stats", self.get_stats())
                
            except Exception as e:
                print(f"[Supervisor] ⚠️ Monitor loop error: {e}")
            
            time.sleep(2)  # Update every 2 seconds
    
    def _get_agent_snapshots(self) -> List[AgentSnapshot]:
        """Get current snapshots of all agents"""
        snapshots = []
        for agent_info in self._registry.get_all_statuses():
            snapshot = AgentSnapshot(
                agent_id=agent_info["agent_id"],
                name=agent_info["name"],
                type=agent_info["type"],
                status=agent_info["status"],
                current_task=agent_info.get("current_task"),
                progress_percent=self._estimate_progress(agent_info)
            )
            snapshots.append(snapshot)
        return snapshots
    
    def _estimate_progress(self, agent_info: Dict) -> int:
        """Estimate progress percentage for an agent"""
        status = agent_info["status"]
        if status == "completed":
            return 100
        elif status == "running":
            return 50  # Rough estimate
        elif status == "waiting":
            return 25
        elif status == "starting":
            return 10
        return 0
    
    def _get_orchestration_snapshots(self) -> List[OrchestrationSnapshot]:
        """Get current snapshots of all orchestrations"""
        snapshots = []
        for orch_info in self._orchestrator.get_all_orchestrations():
            # Get detailed status
            detail = self._orchestrator.get_orchestration_status(orch_info["orchestration_id"])
            if detail:
                snapshot = OrchestrationSnapshot(
                    orchestration_id=detail["orchestration_id"],
                    goal=detail["goal"],
                    status=detail["status"],
                    progress=detail.get("progress", "0/0"),
                    tasks=detail.get("tasks", []),
                    started_at=detail.get("started_at"),
                    elapsed_seconds=time.time() - detail["started_at"] if detail.get("started_at") else 0
                )
                snapshots.append(snapshot)
        return snapshots
    
    def get_stats(self) -> Dict:
        """Get comprehensive supervisor stats"""
        with self._lock:
            registry_stats = self._registry.get_total_stats()
            orch_stats = self._orchestrator.get_all_orchestrations()
            
            by_status = registry_stats.get("by_status", {})
            running_agents = by_status.get("running", 0)
            idle_agents = by_status.get("idle", 0)
            
            running_orchs = sum(1 for o in orch_stats if o["status"] == "running")
            pending_orchs = sum(1 for o in orch_stats if o["status"] == "planning")
            completed_orchs = sum(1 for o in orch_stats if o["status"] == "completed")
            failed_orchs = sum(1 for o in orch_stats if o["status"] == "failed")
            
            uptime = time.time() - self._start_time
            
            return {
                "uptime_seconds": uptime,
                "uptime_formatted": self._format_uptime(uptime),
                "agents": {
                    "total": registry_stats.get("total", 0),
                    "by_type": registry_stats.get("by_type", {}),
                    "by_status": registry_stats.get("by_status", {}),
                    "running": running_agents,
                    "idle": idle_agents,
                },
                "orchestrations": {
                    "total_active": len(orch_stats),
                    "running": running_orchs,
                    "pending": pending_orchs,
                    "completed": completed_orchs,
                    "failed": failed_orchs,
                },
                "lifetime": {
                    "tasks_completed": self._total_tasks_completed,
                    "tasks_failed": self._total_tasks_failed,
                    "orchestrations_completed": self._total_orchestrations_completed,
                    "orchestrations_failed": self._total_orchestrations_failed,
                },
                "timestamp": time.time()
            }
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime as human-readable string"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds/60)}m {int(seconds%60)}s"
        elif seconds < 86400:
            return f"{int(seconds/3600)}h {int((seconds%3600)/60)}m"
        else:
            return f"{int(seconds/86400)}d {int((seconds%86400)/3600)}h"
    
    def get_live_dashboard_data(self) -> Dict:
        """Get all data needed for a live dashboard"""
        return {
            "stats": self.get_stats(),
            "agents": [s.__dict__ for s in self._get_agent_snapshots()],
            "orchestrations": [s.__dict__ for s in self._get_orchestration_snapshots()],
            "timestamp": time.time()
        }
    
    def get_agent_details(self, agent_id: str) -> Optional[Dict]:
        """Get detailed info about a specific agent"""
        agent = self._registry.get_agent(agent_id)
        if not agent:
            return None
        
        return {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "type": agent.agent_type.value,
            "status": agent.status.value,
            "current_task": agent._current_task.goal if agent._current_task else None,
            "shared_data_keys": list(agent._shared_data.keys()),
        }
    
    def get_orchestration_details(self, orchestration_id: str) -> Optional[Dict]:
        """Get detailed info about a specific orchestration"""
        return self._orchestrator.get_orchestration_status(orchestration_id)
    
    def request_status_report(self) -> str:
        """Generate a human-readable status report"""
        stats = self.get_stats()
        agents = self._get_agent_snapshots()
        orchestrations = self._get_orchestration_snapshots()
        
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║                    JARVIS CEO SUPERVISOR REPORT               ║
╠══════════════════════════════════════════════════════════════╣
║ Uptime: {stats['uptime_formatted']:<50} ║
╠══════════════════════════════════════════════════════════════╣
║ AGENTS: {stats['agents']['total']} total | {stats['agents']['running']} running | {stats['agents']['idle']} idle                ║
"""
        
        # Agents by type
        for agent_type, count in stats['agents']['by_type'].items():
            report += f"║   {agent_type}: {count}\n"
        
        report += f"""╠══════════════════════════════════════════════════════════════╣
║ ORCHESTRATIONS: {stats['orchestrations']['total_active']} active | {stats['orchestrations']['running']} running | {stats['orchestrations']['completed']} done | {stats['orchestrations']['failed']} failed  ║
╠══════════════════════════════════════════════════════════════╣
║ LIFETIME STATS:                                               ║
║   Tasks Completed: {stats['lifetime']['tasks_completed']:<40} ║
║   Tasks Failed:    {stats['lifetime']['tasks_failed']:<40} ║
║   Orchestrations:  {stats['lifetime']['orchestrations_completed']} done / {stats['lifetime']['orchestrations_failed']} failed{'':<25} ║
"""
        
        if agents:
            report += "╠══════════════════════════════════════════════════════════════╣\n"
            report += "║ ACTIVE AGENTS:                                              ║\n"
            for agent in agents:
                if agent.status != "idle":
                    task = agent.current_task or "none"
                    report += f"║   {agent.name} ({agent.type}): {agent.status} - {task[:40]}\n"
        
        if orchestrations:
            report += "╠══════════════════════════════════════════════════════════════╣\n"
            report += "║ ACTIVE ORCHESTRATIONS:                                      ║\n"
            for orch in orchestrations:
                report += f"║   {orch.orchestration_id}: {orch.status} ({orch.progress}) - {orch.goal[:40]}\n"
                for task in orch.tasks:
                    report += f"║     → {task['task_id']} ({task['agent_type']}): {task['status']}\n"
        
        report += "╚══════════════════════════════════════════════════════════════╝"
        return report
    
    def speak_status(self, brief: bool = False) -> str:
        """Generate a spoken status update"""
        stats = self.get_stats()
        
        if brief:
            running = stats['agents']['running']
            active_orchs = stats['orchestrations']['running']
            if running == 0 and active_orchs == 0:
                return "All systems idle, sir. No active tasks."
            return f"{running} agents working on {active_orchs} orchestrations, sir."
        
        # Full verbal report
        parts = [f"Supervisor report. Uptime {stats['uptime_formatted']}."]
        parts.append(f"{stats['agents']['total']} agents registered: {stats['agents']['running']} active, {stats['agents']['idle']} idle.")
        
        if stats['orchestrations']['running'] > 0:
            parts.append(f"{stats['orchestrations']['running']} orchestrations in progress.")
            for orch in self._get_orchestration_snapshots():
                if orch.status == "running":
                    parts.append(f"{orch.orchestration_id} is {orch.progress} complete on {orch.goal[:40]}.")
        
        if stats['lifetime']['tasks_completed'] > 0:
            parts.append(f"Lifetime: {stats['lifetime']['tasks_completed']} tasks completed, {stats['lifetime']['tasks_failed']} failed.")
        
        return " ".join(parts)
    
    def record_task_completion(self, agent_id: str, success: bool):
        """Record a task completion for stats"""
        with self._lock:
            if success:
                self._total_tasks_completed += 1
            else:
                self._total_tasks_failed += 1
    
    def record_orchestration_completion(self, orchestration_id: str, success: bool):
        """Record an orchestration completion for stats"""
        with self._lock:
            if success:
                self._total_orchestrations_completed += 1
            else:
                self._total_orchestrations_failed += 1


# Global supervisor
_supervisor = Supervisor()
_supervisor_lock = threading.Lock()


def get_supervisor() -> Supervisor:
    global _supervisor
    with _supervisor_lock:
        return _supervisor


def start_supervisor():
    """Start the global supervisor"""
    sup = get_supervisor()
    sup.start()
    return sup


def get_supervisor_report() -> str:
    """Get a formatted status report"""
    return get_supervisor().request_status_report()


def speak_supervisor_status(brief: bool = False) -> str:
    """Get a spoken status update"""
    return get_supervisor().speak_status(brief)