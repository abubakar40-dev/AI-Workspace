"""Optional nRouter/NaraRouter OpenAI-compatible fallback.

The service is only attempted when ``nrouter_api_key`` is configured. Its
endpoint and model remain configurable because account deployments differ.
"""

import json
import os
import re
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parent
API_KEY_PATH = BASE_DIR / "config" / "api_keys.json"
DEFAULT_URL = "https://router.bynara.id/v1/chat/completions"


def _settings() -> tuple[str, str, str]:
    try:
        data = json.loads(API_KEY_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    key = str(
        data.get("nrouter_api_key")
        or data.get("nararouter_api_key")
        or os.environ.get("NROUTER_API_KEY")
        or os.environ.get("NARAROUTER_API_KEY")
        or ""
    ).strip()
    url = str(
        data.get("nrouter_api_url")
        or os.environ.get("NROUTER_API_URL")
        or DEFAULT_URL
    ).strip()
    model = str(
        data.get("nrouter_model")
        or os.environ.get("NROUTER_MODEL")
        or "deepseek-v4-flash"
    ).strip()
    return key, url, model


def chat(
    prompt: str,
    system: str = "You are Jarvis, a concise and helpful personal assistant.",
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> str:
    key, url, model = _settings()
    if not key:
        raise PermissionError(
            "[nRouter] API key is missing; configure nrouter_api_key in "
            "config/api_keys.json or NROUTER_API_KEY in the environment."
        )
    response = requests.post(
        url,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        },
        timeout=60,
    )
    if response.status_code >= 400:
        if response.status_code == 401:
            raise PermissionError("[nRouter] Authentication failed; check the NaraRouter API key.")
        if response.status_code == 402:
            raise RuntimeError("[nRouter] Account has no available credits or plan entitlement.")
        raise RuntimeError(f"[nRouter] HTTP {response.status_code}")
    return str(response.json()["choices"][0]["message"].get("content") or "").strip()


def chat_json(prompt: str, system: str = "Return only valid JSON.", max_tokens: int = 4096) -> dict:
    raw = chat(prompt, system=system, max_tokens=max_tokens, temperature=0.2)
    clean = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    value = json.loads(clean)
    if not isinstance(value, dict):
        raise ValueError("[nRouter] JSON response was not an object")
    return value
