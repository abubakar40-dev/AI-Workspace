# JARVIS × Obsidian Integration Setup Guide

## Quick Start

### 1. Vault is Ready
Your Obsidian vault is already created at:
```
~/.obsidian-vault/
```

### 2. Install Obsidian
Download and install Obsidian from https://obsidian.md

Then open the vault:
- File → Open Vault → Select `~/.obsidian-vault/`

### 3. Recommended Plugins
Install these community plugins for best experience:
- **Local REST API** — Programmatic access to vault
- **Templater** — Auto-generate notes from templates
- **Data View** — Query notes as tables
- **Calendar** — Browse daily conversations
- **Smart Connections** — Find related memories

### 4. Vault Structure
```
~/.obsidian-vault/
├── conversations/          ← Daily conversation logs
│   ├── 2026-09-25.md
│   └── ...
├── memory/                 ← Memory facts organized by category
│   ├── identity/
│   ├── past/
│   ├── present/
│   ├── future/
│   ├── dreams/
│   ├── relationships/
│   ├── preferences/
│   ├── personality/
│   ├── projects/
│   └── notes/
├── projects/               ← Project notes
├── templates/              ← Templates
├── _attachments/           ← Attached files
└── .obsidian/              ← Obsidian config
    ├── app.json
    ├── appearance.json
    ├── core-plugins.json
    ├── vault.metadata.json
    └── workspace.json
```

### 5. How It Works

**Online Mode**: Conversations and memories are saved to both SQLite AND Obsidian vault
**Offline Mode**: JARVIS reads context from Obsidian vault (local files only)

### 6. Commands
- **"switch to offline mode"** → Uses local Ollama + Obsidian vault
- **"switch to online mode"** → Uses Gemini Live (cloud)
- **"search [query]"** → Searches vault for context
- **"what do you know about me?"** → Loads all memory facts from vault

### 7. Migration Done ✅
- 148 memory entries migrated from SQLite to Obsidian
- 9 conversation files migrated from `chat_history/` to vault
- Original SQLite database preserved at `memory/personal_memory.sqlite3`
- Total vault size: ~169 KB

### 8. Data Safety
- SQLite database is NOT deleted — it remains as backup
- Obsidian vault stores the same data in human-readable markdown
- Both systems are synced automatically going forward
- `update_memory()` writes to BOTH SQLite and Obsidian

### 9. Testing
Run the migration anytime:
```bash
source .venv/bin/activate
python3 migrate_to_obsidian.py
```

### 10. Health Check
```python
from obsidian_integration import health_check
print(health_check())
```

## File Locations
- Integration module: `obsidian_integration.py`
- Migration script: `migrate_to_obsidian.py`
- Setup guide: `OBSIDIAN_SETUP.md`
- Vault: `~/.obsidian-vault/`
- SQLite (backup): `memory/personal_memory.sqlite3`

## Notes
- The existing `memory/personal_memory.sqlite3` is preserved — NOT deleted
- All personal data is stored in BOTH systems for redundancy
- JARVIS reads from Obsidian vault for context whether online or offline
- Each conversation is stored as a dated markdown file with YAML frontmatter
- Memory facts are organized by category in separate markdown files
