#!/usr/bin/env bash
set -e
cd /home/abubakargcx/JARVIS
export OPENROUTER_API_KEY="$(
  .venv/bin/python -c 'import json; print(json.load(open("config/api_keys.json"))["openrouter_api_key"])'
)"
export GROQ_API_KEY="$(
  .venv/bin/python -c 'import json; print(json.load(open("config/api_keys.json"))["groq_api_key"])'
)"
export GEMINI_API_KEY="$(
  .venv/bin/python -c 'import json; print(json.load(open("config/api_keys.json"))["gemini_api_key"])'
)"
exec .venv/bin/litellm --config claude_fallback.yaml --host 127.0.0.1 --port 4000
