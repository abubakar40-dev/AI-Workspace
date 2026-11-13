"""Foundational cross-cutting interfaces for JARVIS.

This package holds the small number of things that must be shared by every
caller (voice, agent loop, bridge, future integrations):

    capabilities  - what the assistant is allowed to do, and how risky it is
    policy        - the decision: allow / require confirmation / deny
    confirmation  - single-use, payload-bound approval tokens
    audit         - append-only record of consequential actions
    voice         - the one shared voice contract

Nothing here imports the application. Keeping this package dependency-free is
what makes it safe to import from ``main.py``, ``agent/``, ``bridge_ws.py`` and
from HELIX without creating an import cycle.
"""

from .capabilities import Capability, TIER_READ, TIER_LOCAL_WRITE, TIER_CONSEQUENTIAL, TIER_FORBIDDEN, get_capability, all_capabilities
from .policy import Decision, evaluate
from .audit import record as record_audit
from .confirmation import issue as issue_confirmation, consume as consume_confirmation

__all__ = [
    "Capability",
    "TIER_READ",
    "TIER_LOCAL_WRITE",
    "TIER_CONSEQUENTIAL",
    "TIER_FORBIDDEN",
    "get_capability",
    "all_capabilities",
    "Decision",
    "evaluate",
    "record_audit",
    "issue_confirmation",
    "consume_confirmation",
]
