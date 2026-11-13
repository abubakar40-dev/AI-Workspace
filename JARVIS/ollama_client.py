# ollama_client.py
# Client for a locally-running Ollama server (e.g. `ollama run qwen2.5:3b`).
#
# No API key needed — Ollama serves a local HTTP API. This is intended to be
# Jarvis's fastest, most reliable "brain" for text-based work (typed input,
# planning, memory extraction, fallback replies) since it doesn't depend on
# any network connection or cloud rate limits — unlike Gemini Live and
# OpenRouter, which can rate-limit or drop connections.
#
# Requires Ollama running locally (default http://localhost:11434) with the
# model already pulled, e.g.:
#     ollama pull qwen2.5:3b
#     ollama serve            # usually already running as a background service

import json
import logging
import os

import requests

logger = logging.getLogger("ollama_client")

OLLAMA_HOST  = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")
DEFAULT_TIMEOUT = 60  # local inference on small models is normally fast


class OllamaUnavailable(Exception):
    """Raised when the local Ollama server can't be reached or errors out."""


class OllamaClient:
    def __init__(self, host: str = OLLAMA_HOST, model: str = OLLAMA_MODEL):
        self.host = host.rstrip("/")
        self.model = model
        self._checked_available: bool | None = None

    def is_available(self, force: bool = False) -> bool:
        """Cheap health check — avoids waiting on a full request timeout when
        Ollama isn't running at all."""
        if self._checked_available is not None and not force:
            return self._checked_available
        try:
            resp = requests.get(f"{self.host}/api/tags", timeout=2)
            self._checked_available = resp.status_code == 200
        except Exception:
            self._checked_available = False
        return self._checked_available

    def chat(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.4,
        max_tokens: int = 1024,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> str:
        """Single-turn chat completion. Raises OllamaUnavailable on any
        connection/server error so callers can fall through to the next
        model in their fallback chain."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            resp = requests.post(
                f"{self.host}/api/chat",
                json=payload,
                timeout=timeout,
            )
        except requests.exceptions.ConnectionError as e:
            self._checked_available = False
            raise OllamaUnavailable(
                f"Can't reach Ollama at {self.host} — is `ollama serve` running?"
            ) from e
        except requests.exceptions.Timeout as e:
            raise OllamaUnavailable(f"Ollama request timed out after {timeout}s") from e

        if resp.status_code == 404:
            raise OllamaUnavailable(
                f"Model '{self.model}' not found — run `ollama pull {self.model}`"
            )
        if resp.status_code != 200:
            raise OllamaUnavailable(f"Ollama HTTP {resp.status_code}: {resp.text[:200]}")

        try:
            data = resp.json()
            content = data.get("message", {}).get("content", "")
        except Exception as e:
            raise OllamaUnavailable(f"Couldn't parse Ollama response: {e}") from e

        self._checked_available = True
        return content.strip()

    def json_chat(self, prompt: str, system: str | None = None, temperature: float = 0.2) -> dict:
        """Same as chat(), but asks the model for JSON and parses it.
        Useful for planner/tool-routing style prompts."""
        raw = self.chat(prompt, system=system, temperature=temperature)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:]
        try:
            return json.loads(cleaned.strip())
        except Exception as e:
            logger.warning(f"[Ollama] JSON parse failed: {e}\nRaw: {raw[:300]}")
            raise OllamaUnavailable(f"Ollama did not return valid JSON: {e}") from e


client = OllamaClient()


if __name__ == "__main__":
    print("  Jarvis — Ollama Client Self-Test")
    print(f"  Host: {OLLAMA_HOST}   Model: {OLLAMA_MODEL}")
    if not client.is_available(force=True):
        print("  Ollama is not reachable. Start it with: ollama serve")
    else:
        print("  Ollama reachable. Sending test prompt...")
        try:
            print(" ", client.chat("Say 'ready' and nothing else."))
        except OllamaUnavailable as e:
            print("  Error:", e)
