# TASK: Implement JARVIS → HELIX → SPECIALIST AGENTS Hierarchy

## Objective

Modify the existing JARVIS and HELIX architecture to establish the following command hierarchy:

**JARVIS (CEO / Primary Assistant) → HELIX (Manager / Execution Coordinator) → Specialist Sub-Agents (Workers)**

JARVIS must be able to directly assign tasks to HELIX.

HELIX must analyze incoming tasks, break them into smaller subtasks, select appropriate specialist agents, delegate work, monitor execution, consolidate results, and report back to JARVIS.

This is an architectural and integration change. Do not rebuild either assistant from scratch.

---

# 1. TEMPORARILY DEACTIVATE HELIX VOICE SYSTEM

Temporarily disable HELIX's independent voice interaction system.

Requirements:

- Disable HELIX's voice input and wake-word activation.
- Disable independent voice-triggered conversation startup.
- Prevent HELIX from competing with JARVIS for microphone access.
- Prevent duplicate voice responses.
- Keep HELIX's text-based interaction and execution capabilities operational.
- Preserve all existing voice-related source code, configuration, and dependencies.
- Do not uninstall voice packages or permanently delete voice functionality.
- Implement a reversible configuration flag or feature toggle, such as:

  `HELIX_VOICE_ENABLED=false`

- Make sure this setting does not accidentally disable JARVIS voice functionality.
- Keep HELIX's voice architecture available for future reactivation.

**Important:** JARVIS remains the primary voice-enabled assistant. HELIX operates as a background/secondary execution manager unless directly accessed through an approved text interface.

---

# 2. ESTABLISH THE ASSISTANT HIERARCHY

Implement the following hierarchy:

```text
USER
  |
  v
JARVIS
(Primary Assistant / CEO)
  |
  | Direct task delegation
  v
HELIX
(Manager / Execution Coordinator)
  |
  | Task analysis and delegation
  |
  +--------------------+---------------+--------+--------+
  |         |          |               |
  v         v          v               v           (new agent addition should be easily possible)
Research   Code      Document          PC
Agent      Agent     Agent            Agent
  |         |          |
  +---------+----------+--------+--------+--------+--------+
                       |
                       v
                HELIX consolidates
                  results and verifies
                       |
                       v
                  JARVIS receives
                  final result
                       |
                       v
                      USER
```

This diagram represents the intended logical hierarchy. Verify actual available agents and interfaces before implementation.

---

# 3. JARVIS MUST DIRECTLY COMMAND HELIX

JARVIS should be able to send structured tasks directly to HELIX.

Example:

User:
"JARVIS, research the best architecture for our new memory system."

JARVIS:
Understands the request and sends a task directly to HELIX.

HELIX receives:

- Task description.
- Objective.
- Relevant context.
- Requirements.
- Constraints.
- Expected output.
- Priority.
- Relevant project files or references, when authorized.

HELIX should acknowledge task receipt and return a task ID.

Example:

```json
{
  "task_id": "generated-task-id",
  "source": "JARVIS",
  "assigned_to": "HELIX",
  "task": "Research and evaluate memory architecture",
  "priority": "high",
  "status": "accepted"
}
```

Use the project's existing communication architecture if suitable.

If no reliable communication interface exists, design a minimal authenticated local API or another appropriate transport.

Do not create unnecessary duplicate communication systems.

---

# 4. HELIX MUST ACT AS THE MANAGER

HELIX is not merely another worker agent.

Its responsibilities are:

1. Receive tasks from JARVIS.
2. Understand and analyze the task.
3. Determine whether the task can be completed directly.
4. Break complex tasks into smaller subtasks.
5. Identify required specialist capabilities.
6. Assign subtasks to appropriate agents.
7. Manage dependencies between subtasks.
8. Monitor agent progress.
9. Handle agent failures.
10. Verify and consolidate results.
11. Return a structured report to JARVIS.

HELIX should decide which agents are necessary rather than activating every agent for every task.

For simple tasks, HELIX may execute directly.

For complex tasks, it should delegate.

---

# 5. SPECIALIST AGENT MANAGEMENT

First inspect the existing specialist agents.

Historical agents included:

- ResearchAgent.
- DocumentAgent.
- CodeAgent.

Verify whether these agents currently exist, their actual names, their capabilities, and whether they are functional.

Reuse existing agents wherever possible.

Do not create duplicate agents unnecessarily.

Potential responsibilities:

### Research Agent
- Research.
- Source discovery.
- Fact verification.
- Comparative analysis.
- Research summaries.

### Code Agent
- Software development.
- Debugging.
- Code analysis.
- Testing.
- Technical implementation.

### Document Agent
- Reports.
- Documentation.
- Structured deliverables.
- Technical specifications.

Additional agents may be introduced only when a real requirement justifies them.

Every agent should have a clearly defined role and interface.

---

# 6. TASK LIFECYCLE AND STATUS MANAGEMENT

Implement a reliable task lifecycle.

Suggested states:

- CREATED
- ACCEPTED
- ANALYZING
- PLANNED
- DELEGATED
- IN_PROGRESS
- WAITING
- REVIEWING
- COMPLETED
- FAILED
- CANCELLED

HELIX should provide progress updates to JARVIS.

Example:

```text
JARVIS → HELIX:
Research memory architecture.

HELIX:
Task accepted.

HELIX:
Analyzing requirements.

HELIX:
Research Agent assigned.
Document Agent assigned.

HELIX:
Research completed.
Document Agent preparing report.

HELIX:
Results verified and consolidated.

HELIX → JARVIS:
Task completed. Final report attached.
```

Do not report completion before actual verification.

Support cancellation and failure recovery.

Prevent duplicate execution when the same task is accidentally submitted more than once.

---

# 7. CONTEXT SHARING

JARVIS must provide HELIX with enough information to understand the task.

Context may include:

- User instructions.
- Relevant conversation history.
- Project master context.
- Previous decisions.
- Constraints.
- Relevant files.
- Expected results.

However:

- Do not share the entire private conversation unnecessarily.
- Do not give HELIX unrestricted access to JARVIS's canonical memory.
- Share only authorized, relevant context.
- Preserve the original conversation and task records.
- Ensure agents receive the context they need to execute their subtasks.

HELIX must maintain its own execution history and report relevant outcomes to JARVIS.

---

# 8. PERMISSIONS AND SAFETY

Maintain the existing security model.

JARVIS can delegate tasks, but delegation does not automatically authorize every possible action.

Require appropriate approval for:

- Destructive file operations.
- System-wide configuration changes.
- Sensitive account operations.
- Financial actions.
- Production deployments.
- High-risk security operations.

Specialist agents must not bypass HELIX's policies or the system's central permission enforcement.

All important actions must be auditable.

---

# 9. ARCHITECTURAL REQUIREMENTS

Before implementation:

1. Inspect both existing repositories.
2. Understand their current architecture.
3. Identify existing orchestration and agent-management code.
4. Identify how JARVIS and HELIX currently communicate.
5. Inspect voice activation and microphone ownership.
6. Identify existing task queues and task states.
7. Identify existing agent interfaces.
8. Produce a short implementation plan.

Use existing components wherever practical.

Prefer stable typed interfaces and versioned task contracts.

Avoid introducing microservices or additional infrastructure without justification.

Maintain compatibility with existing functionality.

---

# 10. TESTING REQUIREMENTS

Perform the following tests:

### Voice tests
- HELIX voice activation remains disabled.
- JARVIS voice functionality still works.
- HELIX does not compete for microphone access.
- HELIX's text interface remains functional.
- HELIX voice can be re-enabled through configuration.

### Delegation tests
- JARVIS can directly assign a task to HELIX.
- HELIX acknowledges the task.
- HELIX analyzes the task.
- HELIX delegates subtasks correctly.
- Specialist agents execute their assigned tasks.
- HELIX consolidates the results.
- JARVIS receives the final report.

### Failure tests
- Agent failure.
- Agent timeout.
- Duplicate task submission.
- Task cancellation.
- Missing context.
- Communication failure.
- Partial task completion.

### Regression tests
- Existing JARVIS features still work.
- Existing HELIX execution functionality remains available.
- Existing specialist agents are not broken.
- Existing memory and task history remain intact.

Do not declare success merely because the application starts.

Run relevant automated tests and verify real end-to-end task delegation.

---

# 11. BACKUP AND CHANGE MANAGEMENT

Before modifying files:

- Inspect Git status.
- Identify uncommitted user changes.
- Preserve the current working state.
- Create a suitable recovery point.
- Do not overwrite existing configuration without preserving it.

Implement in small, reviewable stages.

Do not delete historical code.

After successful completion:

- Document changes.
- Document configuration changes.
- Document how to reactivate HELIX voice.
- Document the new delegation architecture.
- Provide test results.
- Create a ZIP backup after this major modification.
- Provide the backup location.

---

# 12. FINAL ACCEPTANCE CRITERIA

The implementation is accepted only when:

1. HELIX's independent voice system is temporarily disabled.
2. JARVIS voice continues to work.
3. JARVIS can directly command HELIX.
4. HELIX behaves as a manager rather than an ordinary worker.
5. HELIX analyzes tasks before delegating.
6. Existing specialist agents can execute subtasks.
7. HELIX consolidates and verifies their results.
8. HELIX reports progress and final outcomes to JARVIS.
9. Failure handling and task status management work.
10. Existing functionality is preserved.
11. The implementation is documented and recoverable.

---

# FINAL INSTRUCTION

Do not rebuild JARVIS or HELIX.

Do not introduce unrelated features.

Do not implement Windows, macOS, Android, iOS, or robotics functionality as part of this task.

Focus exclusively on:

**JARVIS = CEO / Primary Assistant**

**HELIX = Manager / Execution Coordinator**

**Specialist Agents = Workers**

First audit, then propose the exact changes, then implement and test.

If the current architecture cannot safely support a requirement, explain the blocker and propose the smallest reliable architectural change instead of forcing a fragile implementation.