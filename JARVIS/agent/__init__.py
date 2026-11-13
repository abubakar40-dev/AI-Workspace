# agent/__init__.py
# Multi-Agent System for JARVIS

"""
JARVIS Multi-Agent System

This package provides a sophisticated multi-agent architecture where specialized
agents collaborate under JARVIS (CEO) supervision to accomplish complex tasks.

Architecture:
- BaseAgent: Abstract base class for all agents
- Specialized Agents: ResearchAgent, DocumentAgent, CodeAgent, etc.
- Orchestrator: Coordinates multiple agents with dependency management
- Supervisor: JARVIS CEO - real-time monitoring and progress reporting
- TaskQueue: Background task queue with priorities and cancellation

Usage:
    from agent import orchestrate, get_supervisor, start_supervisor
    
    # Start the supervisor (call once at startup)
    start_supervisor()
    
    # Start a complex multi-agent task
    orchestration_id = orchestrate(
        "Research AI trends and create a professional PDF report"
    )
    
    # Get real-time status
    report = get_supervisor_report()
    print(report)
"""

# Core infrastructure
from agent.agent_base import (
    BaseAgent,
    AgentRegistry,
    AgentType,
    AgentStatus,
    AgentResult,
    AgentTask,
    get_registry,
)

# Specialized agents
from agent.research_agent import (
    ResearchAgent,
    create_research_agent,
)

from agent.document_agent import (
    DocumentAgent,
    create_document_agent,
)

from agent.code_agent import (
    CodeAgent,
    create_code_agent,
)

# Orchestration & Supervision
from agent.orchestrator import (
    AgentOrchestrator,
    OrchestrationStatus,
    get_orchestrator,
    orchestrate,
)
from agent.helix_manager import HelixManager, HelixTask, HelixTaskStatus

from agent.supervisor import (
    Supervisor,
    get_supervisor,
    start_supervisor,
    get_supervisor_report,
    speak_supervisor_status,
)

# Existing modules (planner, executor, error_handler)
from agent.planner import create_plan, replan
from agent.executor import AgentExecutor, _call_tool
from agent.error_handler import analyze_error, generate_fix, ErrorDecision

__all__ = [
    # Core
    "BaseAgent",
    "AgentRegistry",
    "AgentType",
    "AgentStatus",
    "AgentResult",
    "AgentTask",
    "get_registry",
    
    # Specialized Agents
    "ResearchAgent",
    "create_research_agent",
    "DocumentAgent",
    "create_document_agent",
    "CodeAgent",
    "create_code_agent",
    
    # Orchestration
    "AgentOrchestrator",
    "OrchestrationStatus",
    "get_orchestrator",
    "orchestrate",
    "HelixManager",
    "HelixTask",
    "HelixTaskStatus",
    
    # Supervision
    "Supervisor",
    "get_supervisor",
    "start_supervisor",
    "get_supervisor_report",
    "speak_supervisor_status",
    
    # Existing
    "create_plan",
    "replan",
    "AgentExecutor",
    "_call_tool",
    "analyze_error",
    "generate_fix",
    "ErrorDecision",
]

# Version
__version__ = "2.0.0"