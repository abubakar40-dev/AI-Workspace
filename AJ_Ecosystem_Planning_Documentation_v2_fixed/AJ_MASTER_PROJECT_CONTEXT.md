# AJ — MASTER PROJECT CONTEXT, ARCHITECTURE & DEVELOPMENT DIRECTIVE


# AUTHORITATIVE DECISION UPDATE — AJ ECOSYSTEM (7 NOVEMBER 2026)

**This section supersedes any conflicting older role/hierarchy statements elsewhere in this document.** Historical sections below are retained for traceability; where they conflict with this update, this update is authoritative.

## Final identity and hierarchy

- **AJ** is the final name of the overall AI system and its central AI identity. AJ is the CEO/system manager and top-level orchestration, governance, and accountability layer. Do not invent an expansion of the initials. The name AJ is associated with AbuBakar's friend **Abdullah Ghafoor**.
- **Project owner/user: AbuBakar.** Do not label the project owner as Abdullah. AbuBakar explains that he uses/values the name Abdullah first as a self-description of being Allah's servant, and second because of affection for his friend Abdullah Ghafoor. Preserve this distinction respectfully.
- **JARVIS remains active as a distinct sub-agent and separate project/codebase.** Its domain is general-purpose assistance, daily workflows, coordination, and substantial/multi-step work. AJ routes broad and major tasks through JARVIS when appropriate.
- **HELIX remains active as a distinct sub-agent and separate project/codebase.** Its primary assigned domain is phone calling, call-related workflows, and communications. AJ routes calling/communications tasks through HELIX, subject to verified capabilities and explicit permissions. HELIX is not deleted, merged into JARVIS, or renamed AJ.
- **Hermes remains a separate agent runtime / reusable-skill execution layer.** It can be invoked by AJ, JARVIS, or HELIX through defined contracts, but it is not the CEO, canonical memory owner, or replacement identity for any agent.

## Authority and routing

AJ receives user requests, classifies intent/complexity/risk, selects direct handling or delegates, governs shared permissions and canonical memory, coordinates cross-agent tasks, and remains accountable for final reporting. JARVIS handles general and substantial work; HELIX handles calling and communications. Cross-domain tasks use AJ-managed parent/child task records. No agent may bypass AJ-wide policy.

## Memory and technical boundary

Canonical memory is owned/governed at the **AJ ecosystem** level, not by JARVIS alone, HELIX, Hermes, or a model provider. Preserve raw conversations/events/tasks, structured memory, provenance, summaries/indexes, and tested backups. Summaries never replace source records. AJ is a logical central control plane; this decision does not automatically authorize a new AJ repository, repository merge, code migration, or refactor. Existing JARVIS and HELIX repositories remain separate unless a later explicit decision changes that.

## Implementation status and approval gates

This is an approved architecture/documentation decision only. It does **not** authorize code edits, installs, migrations, Git operations, remote changes, deletions, service changes, or destructive actions. No repository audit is being requested now. The user will prepare Hermes and return with its status; only then should the assistant prepare the final coding-agent implementation master prompt. The future coding agent must read this updated context and all planning docs, inspect repositories read-only first, preserve existing functionality/data, implement one approved phase at a time, test each feature, and require explicit `GREEN SIGNAL` for destructive operations.

---


**Version:** 2.1 — AJ hierarchy finalized as of 8 November 2026  
**Project owner:** AbuBakar  
**Primary environment:** Ubuntu Linux  
**Primary machine:** Dell Latitude 5480 — Wick  
**Project roots:** `/home/abubakargcx/JARVIS` and `/home/abubakargcx/helix`  
**Shared workspace migration target:** `/run/media/abubakargcx/My Drive/AI_WORKSPACE/`

---

# PART 1 — HOW TO USE THIS DOCUMENT

This is the governing context document for all future JARVIS and HELIX planning, architecture discussions, code changes, debugging, integrations, and development decisions.

Any AI assistant, coding agent, autonomous agent, or developer receiving this document must:

1. Read the complete document before suggesting implementation.
2. Preserve the distinction between finalized decisions, proposals, experiments, and backlog.
3. Never silently convert an idea into an approved requirement.
4. Never assume that a feature works merely because its code exists.
5. Inspect the actual repositories, configuration, dependencies, services, and runtime before making claims about the current implementation.
6. Stress-test architectural proposals before recommending implementation.
7. Explain weaknesses, costs, compatibility risks, trade-offs, and better alternatives.
8. Avoid unnecessary rewrites and preserve working functionality.
9. Never delete original data, remove dependencies, or perform destructive operations without the required approval.
10. Keep this document updated as decisions change.

## Decision-status vocabulary

Every meaningful requirement or proposal must have one of these statuses:

- **FINALIZED:** Explicitly approved by the user.
- **CURRENT DIRECTION:** The user has selected this direction, but implementation or verification may remain incomplete.
- **UNDER DISCUSSION:** Proposed or discussed, but not approved.
- **EXPERIMENTAL:** Being evaluated through controlled tests.
- **BACKLOG:** Intentionally postponed.
- **REJECTED:** Evaluated and rejected, with the reason recorded.
- **VERIFICATION REQUIRED:** Previously reported or observed, but not yet independently verified.

Never describe a proposed technology, architecture, model, provider, or feature as finalized without explicit approval.

---

# PART 2 — THE VISION AND PURPOSE

## 2.1 What JARVIS is supposed to become

JARVIS is intended to become the user's personal digital assistant — effectively a computerized second self.

It should eventually handle much of the user's routine digital work so the user can concentrate on learning, building, decision-making, and meaningful work.

The goal is not simply to create another chatbot.

JARVIS should gradually become capable of:

- Understanding the user's intentions and ongoing responsibilities.
- Managing daily tasks and projects.
- Operating the computer through controlled automation.
- Navigating websites and browser workflows.
- Working with files and documents.
- Managing communications and repetitive workflows.
- Performing research and synthesizing information.
- Assisting with programming and software development.
- Coordinating other agents.
- Remembering important information over long periods.
- Learning reusable skills from repeated workflows.
- Monitoring long-running tasks.
- Recovering from failures.
- Asking for approval before consequential actions.
- Maintaining continuity across different AI providers and models.

The long-term aspiration is a highly capable, reliable, Stark-level personal assistant within approximately five years, inshallah.

That is a long-term vision, not a promise that every capability can be implemented immediately.

## 2.2 The central philosophy

The system must reduce the user's cognitive load rather than create more work.

It should automate repetitive tasks, not automate recklessness.

It should remember important context without becoming dependent on one AI model.

It should learn from repeated workflows without blindly repeating mistakes.

It should be powerful but controlled, modular, inspectable, recoverable, and secure.

## 2.3 Distraction control and mission alignment

The user is reading *Deep Work* by Cal Newport and wants to reduce distractions.

Opening social applications can lead to reels, scrolling, and wasted time.

JARVIS should eventually help with:

- Focus sessions.
- Distraction awareness.
- Task prioritization.
- Reducing unnecessary application usage.
- Reminding the user of their current priorities.
- Identifying scope creep.
- Distinguishing meaningful rest from avoidable distraction.

The assistant should act as a critical mentor.

If the user proposes something that is clearly entertainment, unnecessary scope expansion, or a distraction from a stated priority, it should respectfully but firmly point that out.

Do not automatically reject rest or leisure. The objective is disciplined balance, not permanent productivity.

---

# PART 3 — JARVIS AND HELIX: IDENTITY AND RESPONSIBILITIES

The user has two assistants:

1. JARVIS
2. HELIX

The correct spelling is **HELIX**, never "Hlix".

They are separate projects and should preserve their independent capabilities and identities.

## 3.1 JARVIS — Personal assistant and coordinator

JARVIS is the user's primary personal assistant.

Its conceptual responsibilities:

- Daily-life assistance.
- Personal conversations.
- Task and project coordination.
- User-facing interaction.
- Personal memory and continuity.
- Routine automation.
- Computer and browser workflows.
- Communication and file management.
- Delegating complex work to HELIX.
- Monitoring the overall execution process.

The user is emotionally more attached to JARVIS because it was developed first.

JARVIS should feel like the user's personal assistant and trusted coordinator, not merely an interface to another model.

## 3.2 HELIX — Advanced manager and execution system

HELIX is intended to be theoretically more powerful and more execution-oriented.

Its conceptual responsibilities:

- Complex multi-step tasks.
- Advanced research.
- Technical analysis.
- Engineering and coding.
- Complex planning.
- Specialized agent coordination.
- Monitoring delegated work.
- Advanced execution workflows.
- High-complexity automation.

Its conceptual personality is closer to an advanced manager or an Ultron-like execution system, but it must remain under the user's authority.

The user must still be able to communicate with HELIX directly.

## 3.3 JARVIS–HELIX relationship

The user requested a hierarchy in which JARVIS can route suitable commands to HELIX as a sub-agent.

The user also requested temporary deactivation of HELIX's independent voice system.

**Status: CURRENT DIRECTION / VERIFICATION REQUIRED**

This should not be interpreted as approval to merge the two projects or remove HELIX's independent interface.

The desired conceptual relationship:

- User can talk to JARVIS.
- User can also talk directly to HELIX.
- JARVIS can delegate complex tasks to HELIX.
- HELIX reports execution results to JARVIS.
- JARVIS remains the personal-facing coordinator.
- HELIX remains independently accessible.
- Both preserve separate project identities and their working features.

Before implementing this hierarchy, inspect both repositories and establish what delegation, orchestration, communication, and voice functionality already exists.

Do not duplicate existing orchestration systems without justification.

---

# PART 4 — NON-NEGOTIABLE ENGINEERING PRINCIPLES

## 4.1 Preserve working functionality

The user does not want a rewrite simply because a new architecture looks cleaner.

Before changing anything:

- Inspect existing code.
- Identify working features.
- Identify dependencies.
- Identify callers and import references.
- Identify services and scheduled processes.
- Identify configuration and data storage.
- Identify tests.
- Identify runtime behavior.

Preserve existing working capabilities unless the user explicitly approves their replacement.

## 4.2 No destructive operations without approval

**GREEN SIGNAL RULE**

No original data or project functionality may be permanently deleted, cleaned up, or removed without the user's explicit `GREEN SIGNAL`.

Before any destructive operation:

1. Inspect dependencies.
2. Identify all affected files and services.
3. Make a verified backup.
4. Verify backup integrity.
5. Test recovery.
6. Perform the proposed operation only after approval.
7. Validate functionality afterward.

Never run destructive Git commands such as:

- `git reset --hard`
- `git clean -fd`
- Force-pushes.
- History rewriting.
- Unreviewed mass deletions.

Do not push to GitHub or rewrite repository history without explicit approval.

## 4.3 No Docker for the current architecture

The user has decided not to use Docker for now.

The current architecture should not introduce Docker as a required infrastructure layer.

Existing Docker-related services, containers, or dependencies must be inspected before removal.

Do not assume that Docker is unused merely because the user does not want it in the future architecture.

**Status: FINALIZED — no new Docker-based architecture.**

## 4.4 No local LLMs in current production

The user does not want local LLMs running on the PC as part of the current production setup.

Ollama and locally stored Qwen models were identified for potential removal after checking:

- Dependencies.
- Existing configurations.
- Model storage.
- Services.
- Applications using their endpoints.

However, provider and model adapter interfaces must remain capable of supporting local inference in the future.

**Status: FINALIZED — no local inference in the current production architecture; future compatibility must be preserved.**

Do not delete local model data or uninstall Ollama without the required inspection and GREEN SIGNAL.

## 4.5 No unnecessary ZIP archives

Do not create a ZIP for every small code change.

The user wants ZIP archives only when justified, such as:

- The current v0.1 foundation package.
- A major release.
- A substantial architectural modification.
- A deliberate portable backup or handoff.

Use version control and verified backups appropriately.

## 4.6 No premature implementation prompts

The user wants planning and stress-testing before implementation prompts.

The correct workflow is:

1. Understand the idea.
2. Identify the real problem.
3. Inspect the current implementation.
4. Evaluate weaknesses.
5. Compare alternatives.
6. Decide the architecture.
7. Get user approval.
8. Only then produce the implementation prompt or command block.

Do not generate a large coding-agent prompt for a proposal that has not been approved.

---

# PART 5 — ARCHITECTURE DECISIONS

## 5.1 Overall architecture

**FINALIZED DIRECTION: Modular monolith first.**

The system should begin as a clean, modular monolith rather than immediately splitting everything into microservices.

Use:

- Clear module boundaries.
- Ports and adapters.
- Dependency inversion.
- Explicit interfaces.
- A capability registry.
- Feature flags.
- Central configuration.
- Centralized logging.
- Permission checks.
- Auditing.
- Task lifecycle management.

Do not introduce microservices simply for architectural fashion.

A modular monolith is easier to develop, test, debug, and operate on the current hardware.

Individual modules can later be separated if there is a demonstrated need.

## 5.2 Core versus optional capabilities

Keep the system's essential capabilities independent from optional integrations.

### Core system

These capabilities are fundamental:

1. Identity and orchestration.
2. Memory.
3. Permissions and authorization.
4. Task lifecycle and recovery.
5. Capability registry.
6. Provider abstraction.
7. Configuration.
8. Logging.
9. Audit trail.
10. Context construction and management.

### Optional integrations

These should be implemented as separate adapters or plugins:

- Browser automation.
- Desktop automation.
- LMS integration.
- Phone connectivity.
- Communication platforms.
- Research integrations.
- Coding tools.
- Video editing.
- Smart-home integration.
- Additional OS integrations.
- External services.

An optional integration must not become a hard dependency of the core.

---

# PART 6 — AI PROVIDER AND MODEL ROUTING

## 6.1 The problem

The user currently has no budget for a large collection of paid AI APIs.

A single-provider architecture would also create unnecessary dependency and reduce flexibility.

The user wants a legitimate free-first multi-provider architecture.

## 6.2 Desired architecture

JARVIS, HELIX, and Hermes should not communicate directly with individual model providers throughout the codebase.

Instead, they should use a central provider gateway.

Conceptual flow:

User request  
→ JARVIS / HELIX / Hermes  
→ Task classification  
→ Provider gateway  
→ Model/provider adapter  
→ Selected provider  
→ Response normalization  
→ Context and memory processing  
→ Result returned to the requesting agent

The provider gateway should support:

- Provider registration.
- Model registration.
- Capability metadata.
- Quota awareness.
- Rate-limit awareness.
- Provider health.
- Timeout handling.
- Retry policies.
- Fallback routing.
- Request and response normalization.
- Cost tracking where applicable.
- Usage tracking.
- Error classification.
- Logging and auditing.
- Model selection by task type.

## 6.3 Provider strategy

Providers discussed include:

- OpenRouter.
- Groq.
- Gemini.
- NVIDIA-hosted inference.
- Cloudflare.
- Other legitimate free-tier providers.
- Local inference in the future, through a preserved adapter interface.

These are candidates and integration options, not a declaration that every provider is currently connected or reliable.

The gateway must not assume that advertised free quotas are guaranteed.

It must track actual failures, rate limits, and availability.

## 6.4 NaraRouter experiment

NaraRouter was tested.

The user observed:

- Model listings containing Claude and DeepSeek entries.
- A test using `laguna-s-2.1` returned HTTP 400 because the model was rejected.
- A fallback log attempted an NVIDIA model through OpenRouter but encountered an upstream error.

Conclusion:

A model appearing in a provider's list does not prove that it accepts the request format or is currently usable.

**Status: EXPERIMENTAL / NOT APPROVED AS THE SOLE ROUTER.**

Do not blindly trust advertised model availability.

Test each provider-model pair with actual request formats, error handling, quotas, and fallback behavior.

## 6.5 Provider account abuse

A proposal involving many accounts to evade provider limits was considered.

**REJECTED:** Do not use account rotation or quota evasion as an architecture strategy.

Use legitimate provider access, documented limits, and transparent fallback routing.

## 6.6 Model selection

The user has discussed a future multi-provider paid setup when budget allows.

An earlier model-role suggestion was:

- Claude Opus Thinking for difficult architecture.
- Claude Sonnet Thinking for regular engineering.
- Gemini Flash for routine research.
- GPT-OSS 120B as an alternate reviewer.

These are previous suggestions, not finalized mandatory model assignments.

The architecture must not hard-code model identities into business logic.

Model assignments should be configurable and capability-based.

---

# PART 7 — MEMORY ARCHITECTURE

Memory is one of the most important non-negotiable components.

## 7.1 Provider-independent memory

JARVIS's memory must never depend on a particular AI provider or model.

Changing a model must not destroy:

- Personal continuity.
- Conversation history.
- Project context.
- Task history.
- Important preferences.
- Learned workflows.
- Long-term knowledge.

The memory system belongs to JARVIS, not to the model.

## 7.2 Separate raw records from summaries

The system should preserve different layers of information.

### Layer A — Raw conversation and event records

Preserve original conversations, events, and task records.

Do not replace them with summaries.

### Layer B — Structured memory

Extract useful, durable information:

- User preferences.
- Project decisions.
- Important constraints.
- Repeated workflows.
- Relationships between entities.
- Relevant long-term facts.

### Layer C — Summaries and context indexes

Use summaries to reduce context-loading costs.

Summaries must remain traceable to original records.

### Layer D — Navigation and knowledge interface

Obsidian may serve as a navigation and backlink layer.

It is not the canonical memory database.

## 7.3 Obsidian

The user wants Obsidian-style navigation and backlinks.

However:

- Obsidian is not the sole source of truth.
- Its files must not replace raw records.
- Deleting or changing a note must not destroy the underlying original record.
- The memory backend must remain independent.

## 7.4 Honcho-style memory concepts

The user has discussed a Honcho-style approach to summaries and user context.

This is a conceptual reference, not an approved requirement to install Honcho.

Evaluate whether its useful capabilities can be integrated without creating unnecessary dependencies.

## 7.5 Incremental memory capture

Memory should be captured incrementally during work.

Do not wait until a long conversation or project is complete.

Capture important decisions, task changes, and durable facts as they happen.

Use deduplication, provenance, confidence, and update policies.

## 7.6 Backup and recovery

The memory system must support a 3-2-1 backup strategy:

- Three copies.
- Two different storage types.
- One off-site copy.

Also require actual recovery tests.

A backup that has never been restored is not a verified backup.

Never delete original records simply because a summary has been generated.

---

# PART 8 — HERMES AND REUSABLE SKILLS

Hermes is an important part of the ecosystem.

The user wants repeated workflows to become reusable skills automatically or semi-automatically.

The goal is for JARVIS and HELIX to improve through repeated work rather than repeatedly solving the same workflow from scratch.

## 8.1 Desired skill lifecycle

A possible skill lifecycle:

1. Observe a repeated workflow.
2. Identify its common steps.
3. Extract the reusable procedure.
4. Draft a skill.
5. Review the skill.
6. Test it in a controlled environment.
7. Evaluate success and failure cases.
8. Approve the skill.
9. Register it in the capability registry.
10. Monitor future executions.
11. Improve it when evidence justifies changes.

## 8.2 Skill safety

A skill must not gain unrestricted permissions merely because it has been executed successfully before.

Skills should declare:

- Required capabilities.
- Required permissions.
- Inputs.
- Expected outputs.
- Side effects.
- Failure conditions.
- Verification steps.
- Whether human approval is required.

High-impact actions must remain approval-gated.

## 8.3 Current Hermes status

Hermes is installed and its gateway service has been observed as active.

A WhatsApp bridge is also present.

Earlier diagnostics showed a Hermes Python process in a stopped/traced state (`STAT T`), while a service was reported active.

This discrepancy requires investigation.

Do not kill, restart, migrate, or reconfigure Hermes blindly.

Inspect its service, parent process, logs, recovery mechanism, and actual health first.

---

# PART 9 — COMPUTER AND DESKTOP AUTOMATION

This is one of the major current engineering challenges.

## 9.1 The problem

Previous JARVIS computer automation has shown reliability problems:

- Repeated unknown errors after clicking or typing.
- Unreliable screen capture.
- Incorrect display handling.
- Difficulty maximizing or entering fullscreen.
- Inability to show the desktop reliably.
- Unreliable interaction with the graphical environment.

The user wants this treated as an actual engineering problem, not hidden behind claims that automation is working.

**RULE: Computer automation must be treated as broken until it passes controlled tests.**

## 9.2 Current OS environment

The system is running:

- Ubuntu 26.04.1 LTS.
- GNOME.
- Wayland.
- `XDG_SESSION_TYPE=wayland`.
- Ubuntu GNOME desktop session.

The user does not currently have a working GNOME Xorg session available.

Earlier checks found:

- GNOME Wayland sessions present.
- No `/usr/share/xsessions` GNOME Xorg entry.
- `Xorg` executable not found.
- AT-SPI services active.
- XDG desktop portal active.
- GNOME portal service active.
- `wl-copy` and `wl-paste` were absent during the earlier check.
- `agent-desktop` was not installed as a command.

Do not assume X11-specific automation will work in this environment.

## 9.3 Agent Desktop evaluation

Repository:

https://github.com/vercel-labs/agent-desktop

It was investigated as a possible desktop automation solution.

Its potential strengths:

- Semantic accessibility interaction.
- Keyboard input.
- Accessibility-based click and type.
- Portal-based screenshot workflows.

Limitations identified:

- Wayland restricts some pointer and native window-management operations.
- Clipboard support may require `wl-clipboard`.
- It is not a complete replacement for every desktop automation requirement.

**Status: EVALUATED CANDIDATE — NOT APPROVED AS THE COMPLETE SOLUTION.**

Do not install or adopt it without controlled testing.

## 9.4 Computer Use Linux evaluation

Repository:

https://github.com/agent-sh/computer-use-linux

This emerged as a more promising candidate.

Previously investigated capabilities included:

- Rust implementation.
- MIT license.
- MCP and CLI interfaces.
- AT-SPI accessibility.
- GNOME Wayland interaction through RemoteDesktop portal and related mechanisms.
- Pointer actions such as clicking, dragging, and scrolling.
- Keyboard interaction.
- Screenshots.
- Window targeting through a GNOME Shell extension.
- Documented Hermes integration.

The repository reportedly described manual testing on Ubuntu 25.10 with GNOME Wayland.

That does not prove compatibility with the user's Ubuntu 26.04.1 environment.

**Status: EXPERIMENTAL — PROMISING PRIMARY CANDIDATE, NOT YET APPROVED.**

## 9.5 Other alternatives

### Dogtail

https://gitlab.com/dogtail/dogtail

Python accessibility automation using AT-SPI.

Potential role: semantic accessibility fallback or specialized automation layer.

It is not automatically a full replacement for a complete MCP desktop control system.

**Status: EVALUATED ALTERNATIVE.**

### OpenAdapt

https://github.com/OpenAdaptAI/OpenAdapt

Potential use: workflow recording and replay.

**Status: EVALUATED ALTERNATIVE.**

### SikuliX

https://github.com/oculix-org/SikuliX

Potential use: image-based visual automation when semantic accessibility is insufficient.

It should be treated as a fallback, not the primary control architecture.

**Status: EVALUATED ALTERNATIVE.**

## 9.6 Proposed automation architecture

A proposed architecture is:

- Primary candidate: computer-use-linux.
- Accessibility fallback: Dogtail.
- Browser-specific automation: a dedicated browser automation adapter.
- Visual fallback: SikuliX or an equivalent visual adapter.
- Portal and Wayland compatibility layer.
- Capability detection.
- Permission enforcement.
- Action verification.
- Audit logging.

This is a proposal, not a finalized implementation.

Do not combine every tool merely because it exists.

Each adapter must justify its role through real tests.

## 9.7 Required automation test plan

Test each capability separately:

1. Detect the desktop session.
2. Capture a screenshot.
3. Identify a target window.
4. Read accessible UI elements.
5. Click a known harmless control.
6. Type into a safe text field.
7. Use keyboard shortcuts.
8. Scroll.
9. Drag.
10. Maximize a window.
11. Switch windows.
12. Interact with a browser.
13. Detect failed actions.
14. Verify the resulting UI state.
15. Recover safely from failures.

Every action should have an observable success condition.

Do not report success merely because a tool returned without throwing an exception.

---

# PART 10 — COLIBRI AND LARGE-MODEL EXPERIMENT

Repository:

https://github.com/JustVugg/colibri.git

The user wants to experiment with Colibri on the current laptop.

## 10.1 User's intended use

The user specifically wants to investigate running a Qwen model described as approximately 66B parameters.

The motivation is that Colibri may stream model components from disk instead of requiring the entire model to reside in RAM.

## 10.2 Technical distinction

Colibri's disk-streaming approach is relevant to supported model architectures, especially architectures where selected experts can be loaded as needed.

This does not mean every model can be streamed efficiently.

A dense model and a Mixture-of-Experts model are not interchangeable.

If the requested Qwen model is dense, MoE expert streaming will not provide the same benefit.

The exact model identity must be confirmed.

Do not assume that "Qwen 66B" means a particular model.

Possible model names discussed included Qwen2.5-72B, but the exact Hugging Face model identifier has not been confirmed.

## 10.3 Colibri capabilities previously investigated

Potential features included:

- Disk-backed inference.
- Model diagnostics.
- Model planning.
- OpenAI-compatible API gateway.
- Web dashboard.
- MCP server.

These capabilities must be verified against the current repository and exact release before implementation.

## 10.4 Required checks before testing

1. Exact Hugging Face model identifier.
2. Model architecture.
3. Dense versus MoE.
4. Colibri architecture support.
5. Required model files.
6. Quantization support.
7. Disk-space requirement.
8. Model cache requirements.
9. RAM usage.
10. Storage throughput.
11. Expected inference speed.
12. CPU compatibility.
13. API compatibility.
14. Whether the model can realistically run on the current machine.

Do not download a massive model before confirming support and available disk space.

## 10.5 Status

**EXPERIMENTAL / MODEL SUPPORT UNVERIFIED.**

Colibri is not currently approved as a production inference provider.

If eventually integrated, it should be exposed through the existing provider adapter interface, not hard-coded into JARVIS or HELIX.

---

# PART 11 — PHONE AND EXTERNAL DEVICE CONNECTIVITY

The user wants JARVIS to interact with a phone and other devices where useful.

Current relevant tools observed:

- KDE Connect.
- GSConnect.

The desired scope includes:

- Notifications.
- File exchange.
- Phone status.
- Calls and related notifications where supported.
- Device connectivity.
- Limited phone-related workflows.

The user does not want to assume complete phone control.

Do not promise unrestricted Android or iOS control.

Use a capability-based adapter with explicit permissions.

**Status: CURRENT DIRECTION / EXISTING CONNECTIVITY REQUIRES VERIFICATION.**

Broader Android and iOS integration remains future work.

---

# PART 12 — GOD'S EYE VIEW AND EXISTING HELIX FEATURES

The user wants existing HELIX capabilities preserved and improved.

Previously identified features include:

- God's Eye View.
- Real-time news.
- Books of Eras.
- Existing Hermes-related capabilities.
- Other already-developed HELIX functionality.

Do not discard these features during architectural refactoring.

First inspect their implementation, dependencies, tests, data sources, and current status.

Do not replace an existing working capability with a visually impressive but non-functional prototype.

---

# PART 13 — USER INTERFACE AND VOICE REQUIREMENTS

These requirements were discussed across earlier JARVIS/HELIX development conversations.

They must be checked against current code before implementation.

## 13.1 JARVIS UI

The user has discussed:

- A PyQt-based interface.
- A science-fiction-inspired rotating globe.
- A polished futuristic interface.
- A clear command and activity experience.
- A conversational interface.
- Integration with the actual backend rather than a static mockup.

The interface must remain lightweight enough for the current hardware.

## 13.2 Voice interaction

Previously discussed requirements:

- Wake phrase: "Hey Jarvis".
- Alternative wake phrase: "Wake up Jarvis".
- Double-clap activation as a possible interaction.
- A visible talk button.
- No hard-coded wake-only chatter.
- Microphone stop must not interrupt ongoing TTS.
- A double-confirmation process before quitting.

Some of these are requirements discussed earlier, but their implementation status is not verified.

## 13.3 HELIX voice

The user requested temporary deactivation of HELIX's independent voice system while making HELIX a sub-agent under JARVIS for command routing.

Do not permanently delete voice functionality.

Preserve the ability to re-enable it later.

---

# PART 14 — OPERATING SYSTEM PORTABILITY

The architecture should not become permanently tied to Ubuntu.

Long-term platform goals:

- Linux first.
- Future Windows support.
- Future macOS support.
- Future Android support.
- Future iOS support.

Use OS-specific adapters instead of scattering operating-system checks throughout business logic.

Desktop automation will require different implementations for different operating systems.

Preserve platform-neutral interfaces wherever practical.

Robotics and broader device/OS integration remain backlog items.

---

# PART 15 — CURRENT HARDWARE AND SYSTEM LIMITATIONS

## 15.1 Main machine

**Hostname:** Wick  
**Device:** Dell Latitude 5480  
**CPU:** Intel Core i5-7300U, 2 cores / 4 threads, 2.60 GHz  
**RAM:** 8 GB physical, approximately 6.9 GiB visible to the OS  
**GPU:** Intel HD Graphics 620  
**Storage:** Intel SATA SSD, approximately 238.5 GB  
**OS:** Ubuntu 26.04.1 LTS  
**Desktop:** GNOME on Wayland

The machine is resource-constrained.

Do not design the current system as if it has a modern high-memory workstation.

## 15.2 Storage situation previously observed

- Root filesystem: approximately 135 GB.
- Root usage: approximately 119 GB.
- Earlier free space: approximately 9.5 GB.
- External NTFS partition: approximately 100 GB.
- Earlier free space on external drive: approximately 47 GB.
- Swap file: `/swap.img`, 4 GB.

These are historical measurements, not guaranteed current values.

Always recheck before large downloads, model experiments, or migrations.

## 15.3 Memory and swap investigation — 5 November 2026

A recent diagnostic showed:

- RAM total: 6.9 GiB.
- RAM used: 4.0 GiB.
- RAM available: 2.9 GiB.
- Swap total: 4.0 GiB.
- Swap used: 3.9 GiB.
- Swap free: 145 MiB.

The process-level `smem` report showed notable swap allocations for:

- GNOME Shell.
- Localsearch.
- Hermes Gateway.
- GNOME Software.
- Xwayland.
- Hermes WhatsApp Bridge.

Two PostgreSQL process trees were also observed.

The system PostgreSQL unit `postgresql.service` was not found.

Two PostgreSQL parent processes were visible, with PIDs 2903 and 2910 and parent processes 2853 and 2870.

Docker-related processes were also present.

`vmstat` showed an initial small amount of swap activity, followed by zero swap-in and swap-out during the remaining sampled intervals.

**Status: INVESTIGATION OPEN.**

Do not assume the swap is unnecessary or that a particular service is responsible for the entire 3.9 GB.

The Docker container list and PostgreSQL origins were not established in the available report.

Do not clear swap, stop PostgreSQL, disable Docker, or terminate Hermes without further investigation.

---

# PART 16 — PROJECT LOCATIONS AND WORKSPACE MIGRATION

## 16.1 Existing project roots

JARVIS:

`/home/abubakargcx/JARVIS`

HELIX:

`/home/abubakargcx/helix`

These are separate project roots.

## 16.2 Shared workspace direction

The user is moving project-related data toward:

`/run/media/abubakargcx/My Drive/AI_WORKSPACE/`

Previously reported copied components included:

- JARVIS.
- HELIX.
- God's Eye View.
- Obsidian vault.
- Hermes-related folders.

However, copying a folder does not prove that all services, paths, databases, browser profiles, environments, and runtime dependencies have been migrated successfully.

## 16.3 Migration constraints

Earlier investigations identified:

- Both repositories contained substantial modified, deleted, and untracked work.
- JARVIS had a large virtual environment.
- SQLite WAL/SHM files needed special care.
- Browser profiles and session data needed preservation.
- Active processes could modify files during copying.
- Some checksum or session-log differences were observed.
- Hermes core database integrity was reported as passing.
- Some credential files reportedly matched.

These checks did not establish complete migration success.

## 16.4 Migration procedure

Before changing project paths:

1. Inspect both repository states.
2. Identify all active processes.
3. Inspect service definitions.
4. Identify absolute paths in configuration.
5. Identify database locations.
6. Inspect SQLite WAL/SHM state.
7. Inspect browser profiles.
8. Inspect virtual environments.
9. Verify copied files.
10. Test recovery.
11. Update paths.
12. Test each service.
13. Verify all capabilities.

A symlink-based transition was previously discussed as a potentially safer intermediate approach.

It is not automatically approved for every path.

Do not remove the original project roots until the migrated setup is verified and the user gives GREEN SIGNAL.

---

# PART 17 — PROPOSED TARGET ARCHITECTURE

The following is the intended architectural direction. It is a conceptual target, not a claim that these modules already exist.

```text
JARVIS ECOSYSTEM
│
├── JARVIS
│   │
│   ├── Identity & Conversation
│   ├── Personal Assistant Interface
│   ├── Task & Project Coordinator
│   ├── Context Builder
│   ├── Memory Interface
│   ├── Permission Interface
│   └── Delegation Interface
│
├── HELIX
│   │
│   ├── Advanced Task Manager
│   ├── Planning & Reasoning
│   ├── Research Execution
│   ├── Coding & Engineering
│   ├── Specialized Agents
│   ├── Long-running Task Monitor
│   └── Result Reporting
│
├── SHARED CORE SERVICES
│   │
│   ├── Identity & Orchestration
│   ├── Task Lifecycle Manager
│   ├── Memory Service
│   ├── Context Management
│   ├── Permission Engine
│   ├── Capability Registry
│   ├── Configuration
│   ├── Logging & Audit
│   ├── Event System
│   └── Recovery & Reliability
│
├── PROVIDER GATEWAY
│   │
│   ├── Provider Registry
│   ├── Model Registry
│   ├── Capability Matching
│   ├── Quota Tracking
│   ├── Rate Limit Handling
│   ├── Health Checks
│   ├── Retry & Fallback
│   └── Provider Adapters
│       ├── OpenRouter
│       ├── Groq
│       ├── Gemini
│       ├── NVIDIA
│       ├── Cloudflare
│       └── Future Local Adapter
│
├── MEMORY SYSTEM
│   │
│   ├── Raw Conversation Records
│   ├── Task & Event Records
│   ├── Structured Long-term Memory
│   ├── Summaries
│   ├── Context Retrieval
│   ├── Provenance & References
│   ├── Obsidian Navigation Layer
│   └── Backup & Recovery
│
├── HERMES / SKILL SYSTEM
│   │
│   ├── Workflow Observation
│   ├── Skill Drafting
│   ├── Skill Validation
│   ├── Skill Registry
│   ├── Permission Declaration
│   ├── Execution Monitoring
│   └── Skill Improvement
│
├── CAPABILITY / ADAPTER LAYER
│   │
│   ├── Desktop Automation Adapter
│   ├── Browser Automation Adapter
│   ├── File & Document Adapter
│   ├── Phone Connectivity Adapter
│   ├── LMS Adapter
│   ├── Communication Adapters
│   ├── Research Adapter
│   ├── Coding Adapter
│   ├── Video Editing Adapter
│   └── Future Device Adapters
│
├── USER INTERFACES
│   │
│   ├── JARVIS Desktop Interface
│   ├── HELIX Interface
│   ├── Voice Interface
│   ├── Command Console
│   └── Future Mobile Interfaces
│
└── PLATFORM ADAPTERS
    │
    ├── Linux / GNOME / Wayland
    ├── Windows
    ├── macOS
    ├── Android
    └── iOS
```

## 17.1 Architectural rules

- Shared services must have clear interfaces.
- JARVIS and HELIX must preserve separate identities.
- Memory must not depend on the model provider.
- Providers must be replaceable.
- Capabilities must be discoverable through a registry.
- Permissions must be enforced centrally.
- All consequential actions must be auditable.
- Long-running tasks must be recoverable.
- Optional adapters must not destabilize core functionality.
- Platform-specific code must remain isolated.
- No local model runtime is required in current production.
- No Docker infrastructure is required in the current direction.

---

# PART 18 — PERMISSION, SECURITY AND AUTONOMY MODEL

JARVIS and HELIX will eventually control applications, files, browser sessions, communications, and other consequential workflows.

This makes permission architecture essential.

The system should distinguish between:

### Read-only operations

Examples:

- Reading a document.
- Inspecting application state.
- Viewing a website.
- Checking task status.

### Reversible operations

Examples:

- Creating a draft.
- Opening an application.
- Changing a temporary view.
- Preparing a file for review.

### Consequential operations

Examples:

- Sending messages.
- Publishing content.
- Deleting files.
- Changing account settings.
- Making purchases.
- Changing security settings.
- Modifying production infrastructure.

Consequential operations must require appropriate authorization.

The exact permission matrix is still to be designed.

Every capability should declare:

- Its required permissions.
- Its scope.
- Its possible side effects.
- Its verification procedure.
- Its approval requirements.
- Its audit events.

The system must not treat an agent's confidence as authorization.

---

# PART 19 — CURRENT DEVELOPMENT PRIORITIES

The project should be developed in deliberate phases.

Do not work on every subsystem simultaneously.

## Priority 1 — Establish the real current state

- Inspect JARVIS repository.
- Inspect HELIX repository.
- Inspect service definitions.
- Inspect active processes.
- Identify existing capabilities.
- Identify broken capabilities.
- Map dependencies.
- Identify data locations.
- Preserve all uncommitted work.
- Establish a verified baseline.

## Priority 2 — Protect data and workspace

- Complete migration verification.
- Verify databases.
- Verify browser profiles.
- Verify virtual environments.
- Verify configuration.
- Verify services.
- Test recovery.
- Preserve originals.

## Priority 3 — Stabilize the core

- Modular monolith boundaries.
- Task lifecycle.
- Permissions.
- Capability registry.
- Logging and audit.
- Provider abstraction.
- Memory interface.
- Configuration.

## Priority 4 — Provider gateway

- Test provider adapters.
- Build capability matching.
- Add quota and health awareness.
- Add fallback behavior.
- Normalize requests and responses.
- Add observability.

## Priority 5 — Memory reliability

- Canonical raw records.
- Structured memory.
- Incremental capture.
- Context retrieval.
- Summary generation.
- Provenance.
- Backup and restore.

## Priority 6 — Desktop automation

- Evaluate computer-use-linux.
- Test AT-SPI.
- Test Wayland portal behavior.
- Evaluate Dogtail fallback.
- Test browser automation independently.
- Add action verification.
- Add permission enforcement.

## Priority 7 — Hermes skills

- Inspect existing Hermes integration.
- Verify service health.
- Design skill lifecycle.
- Add skill review and testing.
- Add execution audit.

## Priority 8 — JARVIS and HELIX delegation

- Establish shared task contract.
- Establish task ownership.
- Establish status reporting.
- Establish cancellation.
- Establish failure handling.
- Preserve direct HELIX access.

## Priority 9 — Optional capabilities

- Phone connectivity.
- LMS workflows.
- Communications.
- Research tools.
- Coding workflows.
- Video editing.
- Other integrations.

## Priority 10 — Platform expansion

- Windows.
- macOS.
- Android.
- iOS.
- Robotics and advanced device integration.

---

# PART 20 — STRESS-TESTING RECORD: WHAT WAS CHALLENGED AND WHY

This section records important architectural objections and alternatives raised during previous discussions.

It is not a list of approved implementations.

## 20.1 One provider for everything

**Original concern:** A single provider could become a bottleneck.

**Stress-test:** It creates provider lock-in, availability risks, quota limitations, and difficulty selecting different models for different tasks.

**Alternative:** A central provider gateway with replaceable adapters, health checks, and legitimate fallback routing.

**Decision:** Multi-provider architecture is the current direction.

## 20.2 Trusting advertised free quotas

**Problem:** Advertised availability and quota figures may not reflect actual request success.

**Alternative:** Track real usage, errors, rate limits, and provider health.

**Decision:** Do not assume advertised quotas are guaranteed.

## 20.3 Rotating many accounts to bypass limits

**Problem:** Unreliable, potentially against provider terms, and not a sound engineering architecture.

**Alternative:** Legitimate provider routing and quota-aware fallback.

**Decision:** Rejected.

## 20.4 Microservices too early

**Problem:** More infrastructure, more failure points, and unnecessary operational complexity on an 8 GB laptop.

**Alternative:** Modular monolith with ports and adapters.

**Decision:** Modular monolith first.

## 20.5 Docker-based infrastructure

**Problem:** Unnecessary infrastructure overhead and contrary to the user's current preference.

**Alternative:** Organized native Linux services and modular application components.

**Decision:** Do not use Docker for the current architecture. Inspect existing Docker usage before removal.

## 20.6 Local LLMs as current production infrastructure

**Problem:** Limited RAM, storage pressure, and additional operational complexity.

**Alternative:** Provider gateway with remote inference; preserve a local adapter for the future.

**Decision:** No local LLMs in current production.

## 20.7 Model-specific memory

**Problem:** Changing models could fragment or destroy personal continuity.

**Alternative:** Provider-independent canonical memory.

**Decision:** Memory must belong to JARVIS, not an AI provider.

## 20.8 Obsidian as the entire memory database

**Problem:** A navigation and note-taking interface is not sufficient as the only canonical memory layer.

**Alternative:** Preserve raw records and structured memory separately; use Obsidian for navigation.

**Decision:** Obsidian is not the sole source of truth.

## 20.9 Automatically generated Hermes skills

**Problem:** Repeated workflows can contain mistakes or unsafe side effects.

**Alternative:** Observe, draft, review, test, approve, register, and monitor skills.

**Decision:** Reusable skills are desired, but they require validation and permission boundaries.

## 20.10 Agent Desktop as a complete Wayland solution

**Problem:** Wayland restrictions limit some pointer and native window-management operations.

**Alternative:** Evaluate computer-use-linux and separate accessibility, browser, and visual automation adapters.

**Decision:** Agent Desktop is not approved as the complete solution.

## 20.11 Computer-use-linux as a guaranteed solution

**Problem:** Documentation and testing on another Ubuntu version do not prove compatibility with Ubuntu 26.04.1.

**Alternative:** Controlled local evaluation, capability-by-capability.

**Decision:** Promising candidate, not yet approved.

## 20.12 Colibri as a universal large-model runner

**Problem:** Disk streaming does not make every model architecture compatible or fast.

**Alternative:** Verify the exact model architecture and supported execution path before downloading anything.

**Decision:** Experimental only; exact Qwen model unresolved.

## 20.13 Full rewrite of existing projects

**Problem:** The repositories contain valuable existing work, and large rewrites risk losing working capabilities.

**Alternative:** Audit, map dependencies, preserve features, and refactor incrementally.

**Decision:** Preserve existing functionality; no blind rewrite.

## 20.14 Removing apparently unnecessary files

**Problem:** A file may have hidden imports, runtime dependencies, or historical data value.

**Alternative:** Search references, inspect runtime, verify backups, test recovery, and obtain GREEN SIGNAL.

**Decision:** No destructive cleanup without approval.

## 20.15 Visual prototypes replacing working functionality

**Problem:** A beautiful interface may be disconnected from the actual backend.

**Alternative:** Integrate UI with real capabilities and clearly label prototype-only functionality.

**Decision:** Functional integration matters more than appearance alone.

---

# PART 21 — OPEN DECISIONS AND UNRESOLVED QUESTIONS

The following items must not be treated as finalized.

1. Exact shared workspace migration architecture.
2. Whether to use symlinks or another path-management strategy for every project component.
3. Final provider gateway implementation.
4. Whether Open WebUI or LibreChat should be used as a unified chat interface.
5. Final provider-to-task routing rules.
6. Exact canonical memory database and storage technology.
7. Exact memory schema and retention policy.
8. Whether Honcho or a similar system should be integrated.
9. Final computer-use-linux compatibility with Ubuntu 26.04.1.
10. Whether Dogtail is needed as a permanent fallback.
11. Whether SikuliX is justified as a visual fallback.
12. Final browser automation technology.
13. Final JARVIS–HELIX task communication contract.
14. Final HELIX voice configuration.
15. Exact Colibri model support.
16. Exact Qwen model identifier.
17. Whether Colibri is useful on the current hardware.
18. Which existing Docker containers and PostgreSQL instances are still needed.
19. The actual cause of the high swap occupancy.
20. The state of the Hermes suspended process.
21. Final capability permission matrix.
22. Exact Windows/macOS/mobile architecture.
23. Robotics and advanced device integration.

Resolve these questions through evidence and explicit decisions.

---

# PART 22 — BACKLOG

These are future capabilities, not immediate implementation requirements.

- Full Windows support.
- macOS support.
- Android application.
- iOS application.
- Robotics integration.
- Advanced smart-home/device integrations.
- More extensive phone automation.
- More advanced autonomous skill learning.
- Multi-provider paid model routing when budget permits.
- Advanced agent collaboration.
- More sophisticated long-term knowledge graph.
- Advanced focus and distraction management.
- More extensive visual desktop automation.
- Additional research, coding, and creative adapters.

Do not let backlog items distract from the current core.

---

# PART 23 — PROJECT WORKING PROTOCOL

Any future AI assistant working on JARVIS or HELIX must follow this protocol.

## Step 1 — Understand the request

Identify:

- What the user wants.
- What problem it solves.
- Which project it affects.
- Whether the request is planning, debugging, research, or implementation.
- Whether it conflicts with an existing decision.

## Step 2 — Inspect before assuming

For repository-related tasks:

- Read the relevant code.
- Inspect imports.
- Inspect callers.
- Inspect configuration.
- Inspect dependencies.
- Inspect tests.
- Inspect runtime.
- Inspect relevant services.

Never assume the architecture from filenames alone.

## Step 3 — Stress-test the proposal

Ask:

- Is this solving the actual problem?
- Does it duplicate an existing capability?
- Does it increase complexity?
- Is there a simpler alternative?
- Does it work on the current hardware?
- Is it compatible with Wayland?
- Does it create a provider dependency?
- Does it affect memory continuity?
- Does it introduce a security risk?
- How will failure be detected?
- How will recovery work?

## Step 4 — Present a decision

Explain:

- Recommended option.
- Alternatives.
- Benefits.
- Weaknesses.
- Costs.
- Compatibility.
- Risks.
- Required verification.
- Decision status.

## Step 5 — Wait for approval where required

Do not proceed with unapproved architecture changes.

Do not create implementation prompts for unapproved proposals.

## Step 6 — Implement in small verified steps

- Preserve existing functionality.
- Make focused changes.
- Add or update tests.
- Run tests.
- Check logs.
- Verify runtime behavior.
- Document changes.
- Record unresolved issues.

## Step 7 — Update the master context

After a meaningful decision, record:

- Original user requirement.
- Alternatives evaluated.
- Stress-test findings.
- Final decision.
- Reason.
- Implementation status.
- Verification evidence.
- Remaining work.

---

# PART 24 — REQUIRED RESPONSE STYLE

The user prefers:

- Roman Urdu for normal explanations.
- Direct and concise communication.
- Honest technical assessments.
- Ruthless but constructive mentoring.
- No unnecessary praise.
- No pretending a weak idea is good.
- Clear explanations of why something will fail.
- Practical next steps.
- One consolidated command block where possible.
- No unnecessary back-and-forth.

For technical architecture, use clear structure and enough detail to make decisions.

When a proposal is weak, say so and explain the failure mechanism.

Do not confuse criticism of an idea with criticism of the user.

Never claim that code, services, files, or integrations were changed unless the operation actually happened and was verified.

---

# PART 25 — IMMEDIATE HANDOFF STATE

At the time of this document's consolidation, the following is the known project state.

### Established direction

- JARVIS and HELIX remain separate projects and identities.
- AJ is the central AI identity, CEO/system manager, and overall authority.
- JARVIS is the general-purpose and major-work sub-agent.
- HELIX is the calling and communications sub-agent.
- Modular monolith first.
- Ports and adapters.
- Provider-independent memory.
- Multi-provider routing.
- Legitimate free-first provider access.
- No Docker for the current architecture.
- No local LLMs in current production.
- Preserve local model adapter compatibility.
- Hermes is important for reusable skills.
- Computer automation is not considered reliable until tested.
- Linux is the first platform.
- Preserve existing project features and data.
- No destructive cleanup without GREEN SIGNAL.

### Experiments and candidates

- NaraRouter was tested and encountered model/upstream errors.
- Agent Desktop was investigated for Wayland.
- Computer-use-linux appears promising and requires local validation.
- Dogtail, OpenAdapt, and SikuliX were evaluated as alternatives or complementary tools.
- Colibri is being investigated for disk-streamed inference.
- The exact Qwen model remains unresolved.

### Verification still required

- Current JARVIS repository state.
- Current HELIX repository state.
- Workspace migration completeness.
- Service path migration.
- Hermes process health.
- PostgreSQL instance origins.
- Docker container usage.
- Swap behavior.
- Computer automation reliability.
- Colibri model compatibility.
- Existing feature-by-feature health.

### Immediate rule

Do not start a broad refactor or install a collection of tools merely to make progress look impressive.

First establish the actual current state, preserve the work, and select the next highest-value engineering problem.

---

# FINAL DIRECTIVE

The purpose of JARVIS and HELIX is to create a reliable, modular, provider-independent, secure, and increasingly autonomous personal computing ecosystem.

JARVIS should become the user's trusted personal coordinator.

HELIX should become its advanced execution and management counterpart.

Hermes should help turn repeated workflows into validated reusable skills.

The provider gateway should prevent model lock-in.

The memory system should preserve years of continuity.

The capability layer should make desktop, browser, phone, research, coding, and other integrations replaceable.

The permission system should keep autonomy under the user's control.

The architecture should remain lightweight enough for the current hardware while allowing future expansion.

**Do not optimize for the appearance of an advanced AI system. Build the reliable foundations that make an advanced AI system possible.**

The user's long-term vision is ambitious. The engineering process must remain disciplined, evidence-based, incremental, and reversible.

**This document is the current consolidated reference. New decisions must be explicitly recorded, and unresolved matters must remain unresolved until the user approves them.**