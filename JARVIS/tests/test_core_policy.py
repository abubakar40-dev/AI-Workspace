"""Tests for the foundational policy / confirmation / audit layer.

These exercise the real modules, not mocks of them: the point of the layer is
that its decisions are deterministic and its tokens cannot be replayed.
"""

import json
from pathlib import Path

import pytest

from core import audit, confirmation, policy
from core.capabilities import (
    TIER_CONSEQUENTIAL,
    TIER_FORBIDDEN,
    TIER_LOCAL_WRITE,
    TIER_READ,
    Capability,
    all_capabilities,
    classify,
    get_capability,
    register,
)


# --- registry ---------------------------------------------------------------

def test_known_tools_are_classified():
    assert classify("web_search")[0] == TIER_READ
    assert classify("send_message")[0] == TIER_CONSEQUENTIAL
    assert classify("file_controller", "list")[0] == TIER_LOCAL_WRITE
    assert classify("file_controller", "delete")[0] == TIER_CONSEQUENTIAL


def test_unknown_tool_is_local_write_not_silently_trusted():
    tier, cap = classify("some_new_tool")
    assert tier == TIER_LOCAL_WRITE
    assert cap is None


def test_registering_a_capability_takes_effect():
    register(Capability(name="quiz_attempt", tier=TIER_FORBIDDEN))
    assert policy.evaluate("quiz_attempt", {}).outcome == policy.DENY
    assert get_capability("quiz_attempt").tier == TIER_FORBIDDEN


# --- policy -----------------------------------------------------------------

def test_read_is_allowed():
    d = policy.evaluate("web_search", {"query": "weather"})
    assert d.allowed and d.outcome == policy.ALLOW


def test_consequential_without_token_is_denied_and_asks_for_one():
    d = policy.evaluate("send_message", {"text": "hello"})
    assert d.denied
    assert d.requires_confirmation
    assert d.tier == TIER_CONSEQUENTIAL


def test_forbidden_is_denied_even_with_a_token():
    register(Capability(name="quiz_attempt_2", tier=TIER_FORBIDDEN))
    token = confirmation.issue("quiz_attempt_2", {})
    d = policy.evaluate("quiz_attempt_2", {}, confirmation_token=token)
    assert d.denied


def test_consequential_with_valid_token_is_allowed():
    params = {"text": "hello"}
    token = confirmation.issue("send_message", params)
    d = policy.evaluate("send_message", params, confirmation_token=token)
    assert d.allowed and d.reason == "confirmed"


# --- confirmation -----------------------------------------------------------

def test_token_is_single_use():
    params = {"text": "hi"}
    token = confirmation.issue("send_message", params)
    assert confirmation.consume(token, "send_message", params)[0] is True
    ok, why = confirmation.consume(token, "send_message", params)
    assert ok is False and "already" in why


def test_token_is_bound_to_the_exact_payload():
    token = confirmation.issue("send_message", {"text": "hi"})
    ok, why = confirmation.consume(token, "send_message", {"text": "something else"})
    assert ok is False and "changed" in why


def test_token_is_bound_to_the_tool():
    token = confirmation.issue("send_message", {"text": "hi"})
    ok, why = confirmation.consume(token, "cmd_control", {"text": "hi"})
    assert ok is False


def test_token_expires():
    params = {"text": "hi"}
    token = confirmation.issue("send_message", params, ttl=1)
    entry = confirmation._tokens[token]
    entry["expires_at"] = entry["issued_at"] - 1
    ok, why = confirmation.consume(token, "send_message", params)
    assert ok is False and "expired" in why


def test_unknown_token_is_rejected():
    ok, why = confirmation.consume("not-a-token", "send_message", {})
    assert ok is False and "unknown" in why


# --- audit ------------------------------------------------------------------

def test_audit_writes_one_line_and_redacts_secrets(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "AUDIT_DIR", tmp_path)
    decision = policy.evaluate("cmd_control", {"command": "ls"})
    path = audit.record(
        "cmd_control",
        {"command": "ls", "password": "hunter2", "api_key": "sk-123"},
        decision,
        source="test",
    )
    assert path is not None
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["tool"] == "cmd_control"
    assert entry["policy"] == policy.DENY
    assert entry["params"]["password"] == "[redacted]"
    assert entry["params"]["api_key"] == "[redacted]"
    assert "hunter2" not in lines[0]


def test_audit_never_breaks_the_caller(tmp_path, monkeypatch):
    blocker = tmp_path / "file"
    blocker.write_text("not a directory", encoding="utf-8")
    monkeypatch.setattr(audit, "AUDIT_DIR", blocker / "nested")
    assert audit.record("web_search", {}, None) is None
