# Provider Research (Batch 01, partial)

## Current verified baseline
- Hermes default: `openrouter` / `openrouter/auto` (**VERIFIED**). Prior real chat test returned `PONG` (exit 0); credit-balance `max_tokens` adjustment observed. No additional OpenRouter/provider API tests run in this batch.

## Hermes support signals (local evidence)
- Model-provider plugins present include `openrouter`, `gemini`, `nvidia`, `ai-gateway`, `custom`, `nous`, `anthropic`, `openai-codex`, `ollama-cloud`, `lmstudio`, `deepseek`, `huggingface`, etc. (**OBSERVED**, `~/.hermes/hermes-agent/plugins/model-providers/`).
- Groq: `plugin-catalog/groq-provider.yaml` exists; Groq appeared in STT/voice config contexts in earlier inspection. **UNVERIFIED** as a Hermes chat model provider for this installed build — confirm before planning.
- Cloudflare target ambiguity: `ai-gateway` plugin exists (fallback docs referenced AI Gateway patterns); Cloudflare Workers AI / AI Gateway / Vercel AI Gateway must be distinguished. **UNVERIFIED** for chosen target.

## Time-sensitive unknowns (UNVERIFIED)
- Free quotas, RPM/TPM/daily/monthly limits, promo credits, billing triggers, and current model availability for OpenRouter/Gemini/NVIDIA/Groq/Cloudflare. **REQUIRES USER APPROVAL** for any live tests; use official docs and record verification dates before relying on free-tier claims.

## Proposal (not approved)
- Capability-based fallback order after explicit verification: keep verified OpenRouter path; add next provider only after credentials + approved minimal smoke test + clear limit/billing understanding. Preserve local adapter interface for future (no local inference now).
