# Provider Abstraction Verification

## Boundary

| Element | Location | Role |
|---|---|---|
| `ProviderAdapter` (Protocol) | `aj/providers.py` | `slug`, `usable()`, `complete(request, model, timeout)` |
| `ProviderSpec` / `ModelSpec` | `aj/providers.py` | declared provider, base URL, credential env **name**, models |
| `OpenAICompatibleAdapter` | `aj/providers.py` | one implementation for chat-completions-shaped providers |
| `Gateway` | `aj/providers.py` | candidate selection, bounded attempts, fallback, health |
| `MockProvider` (new) | `aj/providers.py` | deterministic offline adapter for tests/demos |
| Error codes | `aj/errors.py` | `provider_auth`, `provider_rate_limited`, `provider_unavailable`, `provider_bad_request`, … |

Core code never names a vendor. The registry is built from `providers.adapters` configuration; an adapter is usable only when it has a base URL, a credential present in the environment, **and** a transport.

## Verified

### No silent success without a provider

`aj --check` → `providers` check:

- builds the registry from configuration with `transport=None`;
- asserts **0 adapters usable**;
- calls `Gateway.complete(...)` and requires it to raise `provider_unavailable`;
- returns `{"providers": [...], "usable": 0}`.

If the gateway had returned an empty answer, the check would fail.

### Mock provider, no network, no credential

`tests/test_runtime.py::test_mock_provider_completes_without_network_or_credentials`

- `MockProvider(text="local mock reply")` registered under `ProviderSpec(slug="mock", ...)`;
- response is `"local mock reply"`, provider `mock`, one recorded request;
- the recorded request preserves the message content (`"hi"`).

### Normalised failure, no fallthrough

`tests/test_runtime.py::test_mock_provider_failure_is_normalised_and_does_not_fall_through`

- `MockProvider(error=ProviderError("down", retryable=False))`;
- `Gateway(max_attempts=1)` raises `AjError` with code `provider_unavailable`;
- no fabricated response is returned.

### Pre-existing coverage (now executed)

`tests/test_providers.py` (7 tests): successful normalisation, 429 fallback, 401 no-retry/no-silent-fallback, no usable provider is an error, quota cooldown, adapter refuses without transport, capability requirements filter candidates.

## Not verified

- Any real provider call. Deliberately excluded: no paid call, no credential, no network. The audit's Hermes→Honcho misroute is a reminder that endpoint identity must be proven, not assumed.
- Streaming, tool calling, vision and usage accounting beyond the normalised fields.
- Provider/model provenance in the canonical memory record: the runtime does not call providers yet, so no provenance is written today. When a provider-backed action is added, `ChatResponse.provider/model` must be recorded as metadata.
