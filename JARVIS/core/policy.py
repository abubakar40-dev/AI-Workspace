"""Policy decisions.

The policy layer turns a capability tier into an actual answer:

    allow   -> run it
    confirm -> run it only with a valid confirmation token
    deny    -> do not run it, ever

It deliberately knows nothing about tools, LLMs or the UI. Callers pass a tool
name and its arguments; they get back a ``Decision`` they must honour. That
keeps enforcement in one place instead of scattered across dispatch branches.

Confirmation is verified here rather than in the tool so that a tool cannot
accidentally bypass it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional

from .capabilities import (
    TIER_CONSEQUENTIAL,
    TIER_FORBIDDEN,
    TIER_LOCAL_WRITE,
    TIER_READ,
    classify,
)

ALLOW = "allow"
CONFIRM = "confirm"
DENY = "deny"


@dataclass(frozen=True)
class Decision:
    """The result of evaluating one tool call."""

    outcome: str
    tool: str
    action: str = ""
    tier: str = TIER_LOCAL_WRITE
    capability: Optional[str] = None
    reason: str = ""
    # True when the caller must supply a confirmation token issued for this
    # exact tool + arguments.
    requires_confirmation: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def allowed(self) -> bool:
        return self.outcome in (ALLOW, CONFIRM)

    @property
    def denied(self) -> bool:
        return self.outcome == DENY


def _action_of(params: Mapping[str, Any]) -> str:
    for key in ("action", "command"):
        value = params.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
    return ""


def evaluate(
    tool: str,
    params: Optional[Mapping[str, Any]] = None,
    *,
    confirmation_token: str = "",
    consume=None,
) -> Decision:
    """Evaluate one tool call.

    ``confirmation_token`` is checked only when the tier requires it. ``consume``
    is injected so this module stays state-free and trivially testable; the
    default is the real single-use store in :mod:`core.confirmation`.
    """
    params = dict(params or {})
    action = _action_of(params)
    tier, cap = classify(tool, action)
    capability_name = cap.name if cap else None

    if tier == TIER_FORBIDDEN:
        return Decision(
            outcome=DENY,
            tool=tool,
            action=action,
            tier=tier,
            capability=capability_name,
            reason=f"'{action or tool}' is permanently disabled by policy",
        )

    if tier == TIER_READ:
        return Decision(outcome=ALLOW, tool=tool, action=action, tier=tier,
                        capability=capability_name, reason="read-only")

    if tier == TIER_CONSEQUENTIAL:
        if not confirmation_token:
            return Decision(
                outcome=DENY,
                tool=tool,
                action=action,
                tier=tier,
                capability=capability_name,
                reason=(
                    "this action changes something outside the assistant and needs "
                    "explicit confirmation"
                ),
                requires_confirmation=True,
            )
        if consume is None:
            from .confirmation import consume as _consume
            consume = _consume
        ok, why = consume(confirmation_token, tool, params)
        if not ok:
            return Decision(
                outcome=DENY,
                tool=tool,
                action=action,
                tier=tier,
                capability=capability_name,
                reason=f"confirmation rejected: {why}",
                requires_confirmation=True,
            )
        return Decision(outcome=ALLOW, tool=tool, action=action, tier=tier,
                        capability=capability_name, reason="confirmed")

    # local-write, or anything unclassified
    return Decision(
        outcome=ALLOW,
        tool=tool,
        action=action,
        tier=tier,
        capability=capability_name,
        reason="local write" if capability_name else "unclassified tool",
    )
