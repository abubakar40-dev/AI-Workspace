# Integration Architecture (Batch 01, design/evidence-limited)

## Governing model (master doc)
- **AJ:** CEO/system manager, routing, governance, accountability (logical control plane). **JARVIS:** general-purpose/daily/major-work sub-agent, user-facing coordinator. **HELIX:** calling/communications domain, independently accessible. **Hermes:** execution/skill runtime layer, not CEO/canonical memory owner/replacement identity. No repo merge authorized.

## Current evidence (limited)
- Hermes running with OpenRouter default and Honcho integration signals (`honcho.json`). OmniRush preserved but Hermes chat integration removed.
- AJ pre-Hermes foundation exists in `AI_WORKSPACE/AJ` (contracts, orchestrator, permissions, task/audit/capability/provider/memory/calling ports/adapters — per README, unverified runtime). HELIX and JARVIS historical repos exist in workspace/home/backup forms with unresolved canonical active paths.

## Shared task contract (proposal, Category B design — REQUIRES USER APPROVAL before implementation)
Minimum fields: `task_id`, `parent_task_id`, `requesting_agent`, `assigned_agent`, `owner`, `description`, `required_capabilities`, `required_permissions`, `context_refs`, `status` (queued/running/blocked/waiting_approval/succeeded/failed/cancelled), `progress`, `result_ref`, `errors`, `audit_events`, `created_at`, `updated_at`, `idempotency_key`, cancellation/recovery metadata. Consequential actions require explicit approval gates and audit events.

## Gaps
Actual inter-process/API contracts between AJ/JARVIS/HELIX/Hermes not inspected. Direct user access to JARVIS and HELIX must be preserved.
