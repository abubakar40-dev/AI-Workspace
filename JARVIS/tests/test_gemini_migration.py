"""Regression tests for the google.generativeai -> google.genai migration.

Commit ``a9c6cac`` ("Migrate google.generativeai to google.genai and
consolidate JarvisUI class") converted six files but left every model call
broken:

* stray ``generate_content(model=..., system_instruction=...)`` calls issued
  *before* the prompt existed — no ``contents=`` (TypeError), and
  ``system_instruction`` is not a valid top-level keyword in google.genai,
* ``response = model.generate_content(prompt)`` left pointing at the ``model``
  variable the migration deleted (NameError),
* ``agent/executor.py`` also had two newline-collapsed lines, which made the
  whole module unimportable — so ``from agent.executor import AgentExecutor``
  crashed and the entire task-queue path was dead,
* ``actions/dev_agent._get_model`` returned a *response* where callers
  expected a *model object*.

Everything below runs **offline** against a fake ``google.genai.Client`` whose
signature deliberately requires ``model=`` and ``contents=`` exactly like the
real SDK, so any call that loses those arguments fails the suite instead of
silently falling back to a default answer.
"""

import ast
import importlib
import json
import pathlib
from types import SimpleNamespace

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

MIGRATED_FILES = (
    "agent/executor.py",
    "agent/planner.py",
    "agent/error_handler.py",
    "actions/dev_agent.py",
    "actions/file_processor.py",
    "actions/docx_tools.py",
)


class FakeAPI:
    """Stands in for ``google.genai.Client`` and records every request."""

    def __init__(self, *responses: str):
        self.responses = list(responses)
        self.calls = []
        self.client_kwargs = {}

    def install(self, monkeypatch):
        api = self

        class _Models:
            def generate_content(self, *, model, contents, config=None):
                # same required arguments as the real SDK
                if not isinstance(model, str) or not model.strip():
                    raise TypeError("model= must be a non-empty string")
                if not contents:
                    raise TypeError("contents= is required")
                api.calls.append(
                    {"model": model, "contents": contents, "config": config}
                )
                if len(api.responses) > 1:
                    text = api.responses.pop(0)
                elif api.responses:
                    text = api.responses[0]
                else:
                    text = ""
                return SimpleNamespace(text=text)

        class _Client:
            def __init__(self, **kwargs):
                api.client_kwargs = kwargs
                self.models = _Models()

        monkeypatch.setattr("google.genai.Client", _Client)
        return api

    @property
    def last(self):
        assert self.calls, "no model request was made"
        return self.calls[-1]


def system_instruction_of(call):
    config = call["config"]
    if config is None:
        return None
    if isinstance(config, dict):
        return config.get("system_instruction")
    return getattr(config, "system_instruction", None)


# ------------------------------------------------------------------ importable

@pytest.mark.parametrize("module", [
    "agent.executor",
    "agent.planner",
    "agent.error_handler",
    "actions.dev_agent",
    "actions.file_processor",
    "actions.docx_tools",
])
def test_migrated_modules_import(module):
    """agent/executor.py used to die with SyntaxError at import time."""
    assert importlib.import_module(module)


def test_executor_functions_are_not_collapsed_onto_one_line():
    """Guards the newline-collapse that made the module unimportable."""
    source = (REPO_ROOT / "agent" / "executor.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    names = {f.name for f in funcs}
    assert {"_detect_language", "_translate_to_goal_language",
            "_run_generated_code", "_inject_context"} <= names
    for fn in funcs:
        assert fn.body[0].lineno > fn.lineno, (
            f"{fn.name}: body starts on the def line (collapsed file?)"
        )


@pytest.mark.parametrize("path", MIGRATED_FILES)
def test_no_client_model_call_is_missing_required_arguments(path):
    """Every ``client.models.generate_content(...)`` needs model= and contents=.

    ``model.generate_content(prompt)`` (dev_agent's compatibility shim) is
    intentionally exempt — that is our own object, not the SDK.
    """
    tree = ast.parse((REPO_ROOT / path).read_text(encoding="utf-8"))
    checked = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "generate_content":
            continue
        receiver = ast.unparse(node.func)
        if not receiver.endswith("models.generate_content"):
            continue
        checked += 1
        keywords = {kw.arg for kw in node.keywords}
        assert "model" in keywords, f"{path}:{node.lineno} lost model="
        assert "contents" in keywords, f"{path}:{node.lineno} lost contents="
    assert checked, f"{path}: expected at least one SDK call"


# -------------------------------------------------------------- planner path

def test_create_plan_sends_goal_with_planner_system_prompt(monkeypatch):
    from agent import planner

    plan_json = json.dumps({
        "goal": "buy milk",
        "steps": [{"step": 1, "tool": "web_search", "description": "Search",
                   "parameters": {"query": "buy milk"}}],
    })
    api = FakeAPI(plan_json).install(monkeypatch)

    plan = planner.create_plan("buy milk")

    assert plan["steps"][0]["tool"] == "web_search"
    assert len(api.calls) == 1                      # no stray extra request
    assert api.last["model"] == "gemini-3.5-flash-lite"
    assert "buy milk" in api.last["contents"]
    assert system_instruction_of(api.last) == planner.PLANNER_PROMPT


def test_replan_does_not_reference_the_deleted_model_variable(monkeypatch):
    from agent import planner

    revised = json.dumps({
        "goal": "buy milk",
        "steps": [{"step": 2, "tool": "web_search", "description": "Retry",
                   "parameters": {"query": "buy milk"}}],
    })
    api = FakeAPI(revised).install(monkeypatch)

    plan = planner.replan(
        "buy milk",
        completed_steps=[{"step": 1, "tool": "web_search"}],
        failed_step={"tool": "weather_report", "description": "broke"},
        error="kaboom",
    )

    assert plan["steps"][0]["step"] == 2
    assert len(api.calls) == 1
    assert api.last["model"] == "gemini-3.6-flash"
    assert "kaboom" in api.last["contents"]         # the error reaches the model
    assert system_instruction_of(api.last) == planner.PLANNER_PROMPT


# ------------------------------------------------------------ error recovery

def test_analyze_error_returns_the_model_decision(monkeypatch):
    from agent import error_handler as eh

    api = FakeAPI(
        '{"decision":"retry","reason":"flaky network",'
        '"fix_suggestion":"","max_retries":1,"user_message":"trying again"}'
    ).install(monkeypatch)

    recovery = eh.analyze_error(
        {"step": 1, "tool": "web_search", "description": "Search", "parameters": {}},
        "boom", attempt=1, max_attempts=2,
    )

    assert recovery["decision"] == eh.ErrorDecision.RETRY
    assert api.last["model"] == "gemini-3.5-flash-lite"
    assert "boom" in api.last["contents"]
    assert system_instruction_of(api.last) == eh.ERROR_ANALYST_PROMPT


def test_generate_fix_takes_the_success_path_not_the_fallback(monkeypatch):
    from agent import error_handler as eh

    api = FakeAPI("print('alternative approach')").install(monkeypatch)

    fixed = eh.generate_fix(
        {"step": 1, "description": "make the report"},
        "boom",
        "try a different tool instead",
    )

    # success returns claude_code; a failed model call would fall back to
    # generated_code with the original description
    assert fixed["tool"] == "claude_code"
    assert api.last["model"] == "gemini-3.6-flash"
    assert "try a different tool instead" in api.last["contents"]


# ---------------------------------------------------------------- executor

def test_translation_actually_calls_the_model(monkeypatch):
    from agent import executor

    api = FakeAPI("Turkish", "cevrilmis metin").install(monkeypatch)

    out = executor._translate_to_goal_language("hello world", "Turkce metin hedefi")

    assert out == "cevrilmis metin"
    assert len(api.calls) == 2                       # detect language + translate
    assert api.calls[0]["contents"].find("Turkce") >= 0
    assert api.calls[1]["model"] == "gemini-3.6-flash"
    assert "hello world" in api.calls[1]["contents"]


def test_summarize_returns_the_model_sentence(monkeypatch):
    from agent.executor import AgentExecutor

    api = FakeAPI("Finished the report, sir.").install(monkeypatch)
    spoken = []

    out = AgentExecutor()._summarize(
        "create a report",
        [{"step": 1, "description": "created report.txt"}],
        speak=spoken.append,
    )

    assert out == "Finished the report, sir."
    assert spoken == ["Finished the report, sir."]
    assert api.last["model"] == "gemini-3.5-flash-lite"
    assert "created report.txt" in api.last["contents"]


def test_generated_code_runs_the_models_script(monkeypatch):
    from agent import executor

    api = FakeAPI("print('generated ok')").install(monkeypatch)

    out = executor._run_generated_code("print a greeting")

    assert out == "generated ok"
    assert api.last["model"] == "gemini-3.6-flash"
    assert "print a greeting" in api.last["contents"]
    instruction = system_instruction_of(api.last)
    assert instruction and "SYSTEM PATHS" in instruction
    assert "Desktop" in instruction


# ------------------------------------------------------------ actions layer

def test_dev_agent_model_shim_keeps_the_old_call_shape(monkeypatch):
    from actions import dev_agent

    api = FakeAPI("model reply").install(monkeypatch)

    model = dev_agent._get_model("gemini-test-model")
    response = model.generate_content("hi there")

    assert response.text == "model reply"
    assert api.last["model"] == "gemini-test-model"
    assert api.last["contents"] == "hi there"


def test_file_processor_json_analyze_reaches_the_model(monkeypatch, tmp_path):
    from actions.file_processor import file_processor

    target = tmp_path / "data.json"
    target.write_text(json.dumps({"a": 1, "b": "two"}), encoding="utf-8")

    api = FakeAPI("It is a tiny JSON object.").install(monkeypatch)
    out = file_processor({"file_path": str(target), "action": "analyze"})

    assert out == "It is a tiny JSON object."
    assert api.last["model"] == "gemini-3.6-flash"
    assert "Task: analyze this JSON data" in api.last["contents"]
    assert '"a": 1' in api.last["contents"]


def test_word_document_summarize_reaches_the_model(monkeypatch, tmp_path):
    from docx import Document

    from actions.docx_tools import word_document

    target = tmp_path / "report.docx"
    doc = Document()
    doc.add_paragraph("Quarterly numbers are up.")
    doc.save(str(target))

    api = FakeAPI("The report says numbers are up.").install(monkeypatch)
    out = word_document({"action": "summarize", "file_path": str(target)})

    assert out == "The report says numbers are up."
    assert api.last["model"] == "gemini-3.6-flash"
    assert "Quarterly numbers are up." in api.last["contents"]


# ------------------------------------------------------- harness self-checks

def test_harness_rejects_the_exact_migration_bug_shapes():
    """Self-check: the fake's contract mirrors what the real SDK rejects."""

    class _SDKShaped:
        def generate_content(self, *, model, contents, config=None):
            return SimpleNamespace(text="ok")

    call = _SDKShaped().generate_content

    # (1) the stray warm-up call: system_instruction passed top-level
    with pytest.raises(TypeError):
        call(model="gemini-3.5-flash-lite", system_instruction="prompt")

    # (2) the other stray shape: no contents at all
    with pytest.raises(TypeError):
        call(model="gemini-3.5-flash-lite")

    # (3) the repaired shape is accepted
    assert call(model="gemini-3.5-flash-lite", contents="hi").text == "ok"
