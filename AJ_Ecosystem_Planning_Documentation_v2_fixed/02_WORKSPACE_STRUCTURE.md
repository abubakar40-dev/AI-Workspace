# 02 — AI_WORKSPACE Structure and Repository Boundaries

## 1. Workspace root

Target root: `/run/media/abubakargcx/My Drive/AI_WORKSPACE/`

JARVIS and HELIX remain separate sibling project directories. AJ is the parent system identity and logical control plane; it does not automatically require a new repository. Shared architecture and contracts are organized around the agents without forcing every module into its own Git repository.

## 2. Proposed logical directory structure

```text
AI_WORKSPACE/
├── AJ/                         # AJ governance, system-level docs, routing contracts
│   ├── architecture/
│   ├── decisions/
│   ├── policies/
│   └── orchestration-contracts/
├── JARVIS/                     # Independent JARVIS sub-agent project/repository
├── helix/                      # Independent HELIX sub-agent project/repository
├── HERMES_WORKSPACE/           # Hermes integration notes, reviewed skills, contracts
├── SHARED/
│   ├── contracts/              # Task, event, capability and result schemas
│   ├── provider-gateway/
│   ├── memory/                 # AJ-governed canonical memory design
│   ├── permissions/            # AJ-wide permission policies
│   ├── calling/                # HELIX-owned calling capability contracts
│   └── observability/
├── INTEGRATIONS/
│   ├── desktop/
│   ├── browser/
│   ├── phone/
│   ├── calling/                # HELIX domain; AJ policy/approval applies
│   ├── communication/
│   ├── lms/
│   ├── research/
│   └── coding/
├── DATA/                       # Private user data; not automatically Git-tracked
├── DOCS/                       # Authoritative architecture and project docs
├── RESEARCH/                   # Evaluations and source notes
├── EXTERNAL_PROJECTS/
│   └── gods-eye-view/          # Third-party upstream/fork work; isolated
├── BACKUPS/                    # Verified private backups
└── RELEASES/                   # Deliberate release/handoff artifacts
```

`AJ/` above is a proposed documentation/contract area, not an instruction to create a repository or move code now. AJ may initially be implemented as a logical control plane inside an existing project or shared module; that technical boundary is still to be decided after repository inspection by the future coding agent.

## 3. Identity and ownership interpretation

- `AJ` is the central AI identity and system manager.
- `JARVIS/` remains a separate general-purpose and major-work sub-agent.
- `helix/` remains a separate calling/communications sub-agent.
- `HERMES_WORKSPACE/` contains integration documentation and reviewed skills; it is not a proposal to relocate the live `~/.hermes` runtime.
- Shared contracts and canonical memory are governed at AJ ecosystem level.

This is a **logical target structure**, not an instruction to move, rename, or alter current folders.

## 4. Repository boundaries

| Area | Git boundary | Notes |
|---|---|---|
| AJ governance/docs | Initially workspace documentation | New AJ repo/core boundary not yet approved |
| JARVIS | Separate repository | General-purpose and major-work agent |
| HELIX | Separate repository | Calling and communications agent |
| Hermes | External upstream + local runtime | Integrate through adapter; do not merge blindly |
| Shared contracts/docs | Initially workspace documentation | Dedicated repo only if later justified |
| Calling adapter | Initially integration architecture | HELIX domain, AJ policy gate |
| God's Eye View | Third-party upstream/fork | Keep isolated |
| Backups | Not publishable by default | Preserve privately |
| Dental Lounge | Separate client project | Out of scope |

## 5. Structure principles

1. Separate the parent AI identity from sub-agent project/repository boundaries.
2. Keep JARVIS and HELIX histories independent.
3. Keep shared contracts stable and versioned.
4. Do not create a new repository for every module.
5. Keep runtime state, credentials, databases, and private user data outside public source history.
6. Use one authoritative documentation location.
7. Preserve existing paths until a migration plan and recovery procedure are approved.

## 6. Documentation index

`DOCS/README.md` should point to AJ master architecture, workspace map, repository catalogue, decision log, calling specification, provider gateway, canonical memory, Hermes integration contract, AJ-agent delegation contracts, roadmap, and test/acceptance criteria.

## 7. Not approved yet

- Moving existing folders into this proposed structure.
- Creating a new AJ code repository or moving orchestration code.
- Creating new repositories for SHARED or INTEGRATIONS.
- Renaming the existing `helix` directory or changing repository remotes.
- Moving Hermes runtime, credentials, databases, browser profiles, or virtual environments.
- Changing branches, remotes, or Git history.
