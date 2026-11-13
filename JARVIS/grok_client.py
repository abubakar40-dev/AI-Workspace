"""Small OpenAI-compatible xAI/Grok fallback client."""

import json
import logging
import time
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger("grok_client")
BASE_DIR = Path(__file__).resolve().parent
API_KEY_PATH = BASE_DIR / "config" / "api_keys.json"
API_URL = "https://api.x.ai/v1/chat/completions"
MODELS = ("grok-4-1-fast-reasoning", "grok-4-1-fast-non-reasoning")


def _load_key() -> str:
    try:
        data = json.loads(API_KEY_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    return str(data.get("grok_api_key") or data.get("xai_api_key") or "").strip()


class GrokClient:
    def __init__(self) -> None:
        self.api_key = _load_key()

    def chat(
        self,
        prompt: str,
        system: str = "You are Jarvis, a concise and helpful personal assistant.",
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        if not self.api_key:
            raise PermissionError(
                "[Grok] API key is missing. Add grok_api_key to config/api_keys.json."
            )
        models = (model,) if model else MODELS
        last_error = ""
        for selected in models:
            try:
                response = requests.post(
                    API_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": selected,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": prompt},
                        ],
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                    },
                    timeout=60,
                )
                if response.status_code == 429:
                    last_error = f"rate limited ({selected})"
                    continue
                if response.status_code >= 400:
                    last_error = f"HTTP {response.status_code} ({selected})"
                    continue
                content = response.json()["choices"][0]["message"].get("content", "")
                if content:
                    return str(content).strip()
                last_error = f"empty response ({selected})"
            except (OSError, requests.RequestException, ValueError, KeyError) as exc:
                last_error = str(exc)
            time.sleep(0.2)
        raise RuntimeError(f"[Grok] All models failed: {last_error}")


client = GrokClient()
