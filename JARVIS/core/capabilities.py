"""Capability registry.

A *capability* is one thing JARVIS is allowed to ask a tool to do. The registry
is the single place that answers two questions:

    1. Is this capability known at all?
    2. How risky is it?

Risk tiers
----------
``read``            Observes the world. Safe to run unattended.
``local-write``     Changes something on this machine, or is reversible and
                    contained. Safe to run unattended, but audited.
``consequential``   Visible outside this machine, hard to undo, or spends money
                    (send a message, delete permanently, run a shell command,
                    submit academic work). Requires an explicit confirmation.
``forbidden``       Never allowed, regardless of confirmation. Reserved for
                    assessment-taking against the LMS.

Unclassified tools default to ``local-write`` so that adding a tool cannot
silently widen the consequential surface. They are audited with
``capability="unclassified"`` so the gap is visible in the log.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Iterable, Optional, Tuple

TIER_READ = "read"
TIER_LOCAL_WRITE = "local-write"
TIER_CONSEQUENTIAL = "consequential"
TIER_FORBIDDEN = "forbidden"

_TIERS = (TIER_READ, TIER_LOCAL_WRITE, TIER_CONSEQUENTIAL, TIER_FORBIDDEN)


@dataclass(frozen=True)
class Capability:
    """One named capability and its risk profile."""

    name: str
    tier: str = TIER_LOCAL_WRITE
    description: str = ""
    project: str = "jarvis"
    # Tool honours a per-action risk. Only these actions are consequential;
    # every other action of the same tool keeps the base tier.
    consequential_actions: FrozenSet[str] = field(default_factory=frozenset)
    # Actions that are never permitted (used by the LMS integration later).
    forbidden_actions: FrozenSet[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if self.tier not in _TIERS:
            raise ValueError(f"unknown tier {self.tier!r} for capability {self.name!r}")

    def tier_for(self, action: str = "") -> str:
        """Return the effective tier for one action of this tool."""
        action = (action or "").strip().lower()
        if action and action in self.forbidden_actions:
            return TIER_FORBIDDEN
        if action and action in self.consequential_actions:
            return TIER_CONSEQUENTIAL
        return self.tier


def _c(name: str, tier: str, description: str = "", **kw) -> Tuple[str, Capability]:
    return name, Capability(name=name, tier=tier, description=description, **kw)


# ---------------------------------------------------------------------------
# Registry contents. Kept as data so it is easy to review in one place.
# ---------------------------------------------------------------------------
_BUILTIN: Dict[str, Capability] = dict([
    # --- observation -------------------------------------------------------
    _c("web_search", TIER_READ, "Search the web"),
    _c("weather_report", TIER_READ, "Look up the weather"),
    _c("flight_finder", TIER_READ, "Look up flights"),
    _c("youtube_video", TIER_READ, "Play or summarise a video"),
    _c("file_processor", TIER_READ, "Analyse a file's contents"),
    _c("recall_chat_history", TIER_READ, "Read past conversations"),
    _c("agent_status", TIER_READ, "Report agent state"),
    _c("browser_control", TIER_LOCAL_WRITE, "Drive the browser",
       consequential_actions=frozenset({"fill_form"})),

    # --- local, reversible --------------------------------------------------
    _c("open_app", TIER_LOCAL_WRITE, "Launch an application"),
    _c("computer_settings", TIER_LOCAL_WRITE, "Change a system setting"),
    _c("desktop_control", TIER_LOCAL_WRITE, "Organise the desktop"),
    _c("reminder", TIER_LOCAL_WRITE, "Create a reminder"),
    _c("save_memory", TIER_LOCAL_WRITE, "Write a personal-memory fact"),
    _c("agent_task", TIER_LOCAL_WRITE, "Delegate a goal to the agent team"),
    _c("agent_cancel", TIER_LOCAL_WRITE, "Cancel a delegated goal"),
    _c("presentation_builder", TIER_LOCAL_WRITE, "Generate a presentation"),
    _c("spreadsheet_builder", TIER_LOCAL_WRITE, "Generate a spreadsheet"),
    _c("word_document", TIER_LOCAL_WRITE, "Generate a document"),
    _c("pdf_document", TIER_LOCAL_WRITE, "Generate a PDF"),
    _c("url_downloader", TIER_LOCAL_WRITE, "Download a URL"),
    _c("file_controller", TIER_LOCAL_WRITE, "Read, write and organise files",
       consequential_actions=frozenset({"delete", "chmod", "chown", "trash_default"})),

    # --- consequential ------------------------------------------------------
    _c("send_message", TIER_CONSEQUENTIAL, "Send a message to a person"),
    _c("cmd_control", TIER_CONSEQUENTIAL, "Run a shell command"),
    _c("computer_control", TIER_CONSEQUENTIAL, "Synthesise input on this machine"),
    _c("game_updater", TIER_CONSEQUENTIAL, "Install or update software",
       consequential_actions=frozenset({"install", "update"})),
    _c("shutdown_jarvis", TIER_CONSEQUENTIAL, "Stop the assistant"),
])


_REGISTRY: Dict[str, Capability] = dict(_BUILTIN)


def register(capability: Capability) -> Capability:
    """Add or replace a capability. Idempotent for identical definitions."""
    if not capability.name:
        raise ValueError("capability needs a name")
    _REGISTRY[capability.name] = capability
    return capability


def register_many(items: Iterable[Capability]) -> None:
    for item in items:
        register(item)


_UNCLASSIFIED_SUFFIX = ""


def get_capability(name: str) -> Optional[Capability]:
    """Return the registered capability, or None when the tool is unknown."""
    return _REGISTRY.get((name or "").strip())


def all_capabilities() -> Dict[str, Capability]:
    return dict(_REGISTRY)


def classify(name: str, action: str = "") -> Tuple[str, Capability | None]:
    """Return ``(tier, capability)`` for a tool call.

    Unknown tools are ``local-write`` and reported with ``capability=None`` so
    the audit trail can mark them ``unclassified`` rather than pretending they
    were reviewed.
    """
    cap = get_capability(name)
    if cap is None:
        return TIER_LOCAL_WRITE, None
    return cap.tier_for(action), cap
