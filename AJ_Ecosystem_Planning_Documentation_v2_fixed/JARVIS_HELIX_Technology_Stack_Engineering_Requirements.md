# PART 26 — COMPLETE TECHNOLOGY STACK & ENGINEERING REQUIREMENTS

**Status:** CURRENT DIRECTION + TECHNOLOGY EVALUATION  
**Purpose:** Define the technical knowledge, programming languages, frameworks, libraries, tools, and engineering disciplines required to develop, maintain, and expand the JARVIS + HELIX ecosystem.

## 26.1 Technology Selection Rules

Every technology must have one of these statuses:

- **EXISTING:** Already present in the current environment or project; actual usage must be verified.
- **SELECTED:** Explicitly approved for the architecture.
- **CURRENT DIRECTION:** Preferred direction, but implementation may remain incomplete.
- **UNDER EVALUATION:** Candidate requiring comparison and testing.
- **BACKLOG:** Future requirement.
- **REJECTED:** Explicitly rejected.

Do not introduce a framework merely because it is popular.

Before selecting a technology:
1. Inspect existing implementations and dependencies.
2. Check hardware compatibility.
3. Evaluate memory and CPU overhead.
4. Check Linux and Wayland compatibility.
5. Evaluate security and maintenance.
6. Check whether an existing component already solves the problem.
7. Prefer simpler, lightweight, maintainable solutions.
8. Avoid unnecessary dependencies and overlapping frameworks.

## 26.2 Core Programming Languages

| Language | Intended responsibility | Status |
|---|---|---|
| Python | AI orchestration, backend, agents, automation, integrations | CURRENT DIRECTION |
| TypeScript | Desktop UI, frontend, Node.js integrations | UNDER EVALUATION |
| JavaScript | UI and existing Node.js ecosystem | EXISTING / VERIFY |
| SQL | Relational databases and data operations | REQUIRED |
| Bash | Linux administration and automation | REQUIRED |
| Rust | Future performance-sensitive and system components | BACKLOG |
| C/C++ | Low-level system integration where necessary | BACKLOG |
| Dart | Potential future Flutter mobile application | BACKLOG |

Do not introduce multiple implementation languages into the same subsystem without a clear technical reason.

## 26.3 Backend Engineering

Required knowledge:
- REST API design.
- WebSockets and real-time communication.
- Asynchronous programming.
- Dependency injection.
- Authentication and authorization.
- Background jobs.
- Event-driven communication.
- API versioning.
- Error handling.
- Request validation.
- Logging and observability.

Technology candidates:

| Technology | Responsibility | Status |
|---|---|---|
| FastAPI | Python API services | UNDER EVALUATION / EXISTING IN SUPPORTING WORK |
| Pydantic | Data validation and schemas | UNDER EVALUATION |
| SQLAlchemy | Database abstraction and ORM | EXISTING IN SUPPORTING WORK / VERIFY |
| Alembic | Database migrations | UNDER EVALUATION |
| WebSockets | Real-time communication | UNDER EVALUATION |
| Node.js | JavaScript runtime and integrations | EXISTING / VERIFY |

The backend should remain modular. Avoid splitting the system into microservices without a demonstrated need.

## 26.4 AI Engineering

Required knowledge:
- LLM architecture and inference.
- Prompt engineering.
- Tool calling and function calling.
- Agent orchestration.
- Multi-agent collaboration.
- Context management.
- RAG.
- Embeddings.
- Semantic search.
- Memory retrieval.
- Model evaluation.
- Token and cost management.
- Provider abstraction.
- Model capability matching.
- Failure handling and fallback.

Framework candidates:

| Technology | Responsibility | Status |
|---|---|---|
| Pydantic AI | Structured AI agents | UNDER EVALUATION |
| LangGraph | Stateful agent workflows | UNDER EVALUATION |
| LlamaIndex | Data retrieval and RAG | UNDER EVALUATION |
| Haystack | Search and retrieval pipelines | BACKLOG |
| CrewAI | Multi-agent orchestration | UNDER EVALUATION |
| AutoGen | Multi-agent communication | BACKLOG |

No framework is mandatory. Prefer the existing Hermes and custom orchestration capabilities when they already satisfy the requirement.

## 26.5 AI Provider Gateway

Required engineering knowledge:
- Provider adapters.
- Model registry.
- Capability matching.
- Rate-limit handling.
- Quota tracking.
- Retry policies.
- Fallback routing.
- Health monitoring.
- Request/response normalization.
- Usage and cost tracking.
- Error classification.

Provider candidates:
- OpenRouter.
- Google Gemini.
- Groq.
- NVIDIA.
- Cloudflare.
- Other legitimate providers.
- Future local inference adapter.

**Architecture status: CURRENT DIRECTION.**

The provider gateway must remain independent of JARVIS, HELIX, and Hermes business logic.

No provider should become a permanent architectural dependency. Local inference is not required in current production, but its adapter interface must remain possible.

## 26.6 Database and Memory Engineering

Required knowledge:
- Relational database design.
- SQL queries and indexing.
- Transactions.
- Database migrations.
- Vector search.
- Data normalization.
- Data provenance.
- Backup and recovery.
- Database integrity.
- Persistent event storage.

| Technology | Responsibility | Status |
|---|---|---|
| PostgreSQL | Primary structured data storage | CURRENT DIRECTION / VERIFY |
| SQLite | Local records and lightweight persistence | EXISTING / VERIFY |
| pgvector | Vector similarity search | UNDER EVALUATION |
| Redis | Caching and transient coordination | UNDER EVALUATION |
| SQLAlchemy | Python database access | EXISTING IN SUPPORTING WORK / VERIFY |
| Alembic | Schema migrations | UNDER EVALUATION |
| Honcho | Memory/context infrastructure | EXPERIMENTAL / VERIFY |

Non-negotiable memory requirements:
- Memory must be independent of AI providers.
- Original conversation and task records must be preserved.
- Summaries must never replace original records.
- Incremental capture must be supported.
- Every important memory should have provenance.
- Backups and recovery must be tested.
- Obsidian remains a navigation and knowledge-organization layer, not the canonical memory database.

## 26.7 Desktop Application Engineering

Required knowledge:
- Desktop application architecture.
- UI/UX engineering.
- Inter-process communication.
- System tray integration.
- Native notifications.
- Audio device integration.
- Screen capture.
- Application lifecycle.
- Cross-platform packaging.

Technology candidates:

| Technology | Responsibility | Status |
|---|---|---|
| PySide6 / Qt | Python desktop interfaces | UNDER EVALUATION |
| PyQt6 | Python desktop interfaces | UNDER EVALUATION |
| Electron | Cross-platform desktop applications | UNDER EVALUATION |
| Tauri | Lightweight cross-platform desktop applications | UNDER EVALUATION |
| React | Component-based UI | UNDER EVALUATION |
| HTML / CSS | Interface development | REQUIRED IF WEB UI APPROACH IS SELECTED |

Do not select Electron, Tauri, or Qt merely by preference. Compare resource consumption, Linux integration, UI requirements, and future platform support first.

## 26.8 Linux and Computer Automation

Required knowledge:
- Linux system architecture.
- Ubuntu and GNOME.
- Process and service management.
- File systems and permissions.
- systemd.
- D-Bus.
- X11 and Wayland.
- Accessibility APIs.
- Browser automation.
- Keyboard and mouse automation.
- Screen capture and OCR.
- Action verification.

Technology candidates:

| Technology | Responsibility | Status |
|---|---|---|
| Playwright | Browser automation | UNDER EVALUATION |
| AT-SPI | Desktop accessibility automation | UNDER EVALUATION |
| Dogtail | Linux GUI automation | EXPERIMENTAL |
| Computer-use-linux | Linux computer interaction | EXPERIMENTAL |
| OpenCV | Image processing and computer vision | BACKLOG |
| OCR tools | Screen/document text extraction | UNDER EVALUATION |
| D-Bus | Linux application and service communication | REQUIRED KNOWLEDGE |
| systemd | Service lifecycle management | REQUIRED KNOWLEDGE |

Desktop automation must not be declared reliable until independently tested on the actual Ubuntu/GNOME/Wayland environment.

Every consequential automation action must have a verification procedure.

## 26.9 Voice and Audio Engineering

Required knowledge:
- Speech-to-Text.
- Text-to-Speech.
- Wake-word detection.
- Voice Activity Detection.
- Audio streaming.
- Microphone lifecycle.
- Noise reduction.
- Audio interruption management.
- Speech latency optimization.

Technology candidates:

| Technology | Responsibility | Status |
|---|---|---|
| Whisper / faster-whisper | Speech recognition | UNDER EVALUATION |
| Piper | Text-to-Speech | UNDER EVALUATION |
| Vosk | Speech recognition | BACKLOG |
| Porcupine | Wake-word detection | UNDER EVALUATION |
| PyAudio / sounddevice | Audio device access | UNDER EVALUATION |
| OpenAI-compatible voice APIs | Cloud voice services | UNDER EVALUATION |

Voice components must be replaceable and must not be tightly coupled to a specific AI model.

## 26.10 Security and Permission Engineering

Required knowledge:
- Authentication.
- Authorization.
- OAuth2.
- JWT.
- Secrets management.
- Encryption.
- Role-based access control.
- Sandboxing.
- Threat modeling.
- Audit trails.
- Secure file operations.
- Permission boundaries.

Required architecture:
- Central permission engine.
- Capability-level permission declarations.
- Read-only, reversible, and consequential action categories.
- Explicit approval for consequential operations.
- Audit logs for important actions.
- Secure credential storage.
- Skill-level permission declarations.
- Revocable permissions.

Security is a core requirement, not an optional future enhancement.

## 26.11 Software Architecture and Reliability

Required knowledge:
- Modular Monolith.
- Ports and Adapters.
- Dependency Injection.
- SOLID principles.
- Design Patterns.
- Event-driven architecture.
- State machines.
- Task lifecycle management.
- Fault tolerance.
- Retry and recovery.
- Plugin architecture.
- Feature flags.
- Configuration management.
- Observability.

Required architectural components:
- Identity and orchestration.
- Task lifecycle manager.
- Memory interface.
- Permission engine.
- Capability registry.
- Provider gateway.
- Configuration service.
- Event system.
- Logging and audit.
- Recovery mechanisms.
- Adapter interfaces.

**Architecture status: CURRENT DIRECTION.**

Modular Monolith first. Microservices only if a demonstrated scaling, isolation, or operational requirement justifies them.

## 26.12 Testing and Quality Engineering

Required knowledge:
- Unit testing.
- Integration testing.
- End-to-end testing.
- Regression testing.
- API testing.
- Database testing.
- Mocking and fixtures.
- Load and performance testing.
- Security testing.
- Failure injection.
- Recovery testing.

Technology candidates:

| Technology | Responsibility | Status |
|---|---|---|
| Pytest | Python testing | UNDER EVALUATION |
| Playwright Test | Browser end-to-end testing | UNDER EVALUATION |
| Postman | API testing | UNDER EVALUATION |
| Ruff | Python linting | UNDER EVALUATION |
| Mypy / Pyright | Type checking | UNDER EVALUATION |
| GitHub Actions | Automated CI | UNDER EVALUATION |

No subsystem is complete merely because its code executes. It must pass defined tests and runtime verification.

## 26.13 DevOps and Deployment

Required knowledge:
- Git and GitHub.
- Branch management.
- CI/CD.
- Linux services.
- Environment management.
- Application packaging.
- Logging and monitoring.
- Database backups.
- Release management.
- Cross-platform deployment.

Technology candidates:

| Technology | Responsibility | Status |
|---|---|---|
| Git | Version control | REQUIRED |
| GitHub | Repository hosting | EXISTING |
| systemd | Linux service management | REQUIRED KNOWLEDGE |
| GitHub Actions | CI/CD | UNDER EVALUATION |
| Docker | Containerization | NOT SELECTED FOR CURRENT ARCHITECTURE |
| Kubernetes | Container orchestration | REJECTED FOR CURRENT SCOPE / UNNECESSARY |
| PyInstaller | Python application packaging | UNDER EVALUATION |

Current architecture must remain Docker-independent.

## 26.14 Future Platform Engineering

The architecture should isolate platform-specific functionality.

Target platforms:
- Linux / GNOME / Wayland — first priority.
- Windows — future.
- macOS — future.
- Android — future.
- iOS — future.

Required knowledge:
- Platform-specific APIs.
- Mobile application architecture.
- Cross-platform communication.
- Secure device pairing.
- Synchronization.
- Platform permission systems.
- Native notifications and background execution.

Mobile frameworks must be selected only when mobile development enters an approved phase.

## 26.15 Engineering Roles and Knowledge Domains

The complete ecosystem requires combined expertise in:

1. Software Architecture Engineering.
2. Backend and Systems Engineering.
3. AI and Agent Engineering.
4. Database and Memory Engineering.
5. Desktop Application Engineering.
6. Linux and OS Automation Engineering.
7. Voice and Audio Engineering.
8. Security Engineering.
9. Testing and Reliability Engineering.
10. DevOps and Deployment Engineering.

One developer does not need expert-level knowledge of every domain before starting. However, the architecture must account for all of them, and specialized components must be reviewed by someone with the relevant expertise.

## 26.16 Development Priority for Learning and Implementation

Recommended order:

1. Programming fundamentals: Python, SQL, Bash, and relevant JavaScript/TypeScript.
2. Software architecture and clean code.
3. Backend engineering and APIs.
4. Database design and memory systems.
5. AI APIs, agents, and orchestration.
6. Provider gateway and model routing.
7. Linux system programming and automation.
8. Desktop application development.
9. Voice and audio engineering.
10. Security, testing, reliability, and recovery.
11. Packaging and cross-platform engineering.

This sequence is a learning and engineering roadmap, not permission to implement every subsystem immediately.

## 26.17 Final Technology Governance Rules

- Existing working technologies must be inspected before replacement.
- Do not add frameworks to duplicate existing functionality.
- Do not introduce unnecessary programming languages.
- Do not install every framework listed in this document.
- Keep the current hardware limitations in mind.
- Preserve provider-independent architecture.
- Keep memory independent of model selection.
- Keep platform-specific implementations isolated.
- Keep optional integrations outside the critical core.
- Avoid Docker infrastructure in the current direction.
- Do not deploy local LLMs in current production.
- Keep future local inference compatibility.
- Test every important integration.
- Record technology decisions and their reasons.
- Update this section whenever a technology is explicitly approved, rejected, replaced, or verified.

**Final principle: The objective is not to use the maximum number of technologies. The objective is to build the simplest reliable technology stack capable of supporting the complete JARVIS + HELIX vision.**
