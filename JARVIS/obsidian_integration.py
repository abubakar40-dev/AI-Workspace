# obsidian_integration.py
#
# Obsidian vault integration for JARVIS.
#
# Stores all conversations, memories, and personal data as markdown
# files in a local Obsidian vault. JARVIS can read/write from this
# vault both online (when connected) and offline (local files only).
#
# The existing SQLite database (personal_memory.sqlite3) is preserved
# as a backup; this module writes to BOTH SQLite and Obsidian.
#
# Vault structure:
#   ~/.obsidian-vault/
#     conversations/YYYY-MM-DD.md   — daily conversation logs
#     memory/{category}/            — memory facts in markdown
#     projects/{project}/           — project notes
#     templates/                    — templates
#     _attachments/                 — attached files

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from threading import Lock
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from memory.memory_db import remember as db_remember, all_entries, forget as db_forget

# ─── Configuration ──────────────────────────────────────────────────────

_VAULT_DIR = Path.home() / ".obsidian-vault"
_CONVERSATIONS_DIR = _VAULT_DIR / "conversations"
_MEMORY_DIR = _VAULT_DIR / "memory"
_PROJECTS_DIR = _VAULT_DIR / "projects"
_TEMPLATES_DIR = _VAULT_DIR / "templates"
_ATTACHMENTS_DIR = _VAULT_DIR / "_attachments"
_VAULT_LOCK = Lock()

# Local REST API configuration (port 27124 from Obsidian)
_OBSIDIAN_API_URL = "http://127.0.0.1:27124"
_OBSIDIAN_API_KEY = "a730ebd2fd9b0490e9273c64ba9142c8a70664219a9e8482c1a30f8610e5d570"
_OBSIDIAN_API_HEADERS = {
    "Authorization": f"Bearer {_OBSIDIAN_API_KEY}",
    "Content-Type": "application/json",
}
_OBSIDIAN_API_ENABLED = True

# Ensure directories exist
for d in [_VAULT_DIR, _CONVERSATIONS_DIR, _MEMORY_DIR, _PROJECTS_DIR, _TEMPLATES_DIR, _ATTACHMENTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ─── Helper Functions ───────────────────────────────────────────────────

def _sanitize_filename(text: str) -> str:
    """Sanitize text for use as a filename."""
    text = re.sub(r'[<>:/"\\|?*\x00-\x1f]', '_', text)
    text = text.strip().strip('.')
    return text[:100] if text else "untitled"


def _format_yaml_frontmatter(data: dict) -> str:
    """Create YAML frontmatter block for a markdown file."""
    lines = ["---"]
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        lines.append(f"{key}: \"{value}\"")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def _write_markdown(path: Path, content: str, frontmatter: dict = None) -> None:
    """Write content as markdown with optional YAML frontmatter."""
    with _VAULT_LOCK:
        path.parent.mkdir(parents=True, exist_ok=True)
        if frontmatter:
            full_content = _format_yaml_frontmatter(frontmatter) + content
        else:
            full_content = content
        path.write_text(full_content, encoding="utf-8")


def _read_markdown(path: Path) -> str:
    """Read markdown content, stripping YAML frontmatter if present."""
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    # Strip YAML frontmatter
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            text = text[end + 3:].strip()
    return text


# ─── Conversation Storage ───────────────────────────────────────────────

def save_conversation(user_text: str, jarvis_response: str, date: str = None) -> str:
    """
    Save a conversation entry to the Obsidian vault.
    
    Creates/updates a daily conversation markdown file.
    Returns the path where the conversation was saved.
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    time_now = datetime.now().strftime("%H:%M")
    conversation_file = _CONVERSATIONS_DIR / f"{date}.md"
    
    entry = f"""## {time_now}
**You:** {user_text}
**Jarvis:** {jarvis_response}

"""
    
    with _VAULT_LOCK:
        conversation_file.parent.mkdir(parents=True, exist_ok=True)
        # Append to existing file or create new
        if conversation_file.exists():
            existing = conversation_file.read_text(encoding="utf-8")
            # Check if this exact entry already exists
            if user_text in existing and jarvis_response in existing:
                return str(conversation_file)
            full_content = existing.rstrip("\n") + "\n\n" + entry
        else:
            # Create new file with YAML frontmatter
            frontmatter = {
                "title": f"Jarvis Conversation Log — {date}",
                "date": date,
                "type": "conversation",
                "entries": 1,
                "tags": ["jarvis", "conversation", "personal"]
            }
            full_content = _format_yaml_frontmatter(frontmatter) + entry
        
        conversation_file.write_text(full_content, encoding="utf-8")
    
    return str(conversation_file)


def save_conversation_batch(conversations: list[dict], date: str = None) -> str:
    """
    Save multiple conversation entries at once.
    
    conversations: list of {"user_text": ..., "jarvis_response": ..., "time": ...}
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    conversation_file = _CONVERSATIONS_DIR / f"{date}.md"
    
    entries = []
    for conv in conversations:
        time_val = conv.get("time", datetime.now().strftime("%H:%M"))
        entries.append(f"""## {time_val}
**You:** {conv["user_text"]}
**Jarvis:** {conv["jarvis_response"]}
""")
    
    with _VAULT_LOCK:
        conversation_file.parent.mkdir(parents=True, exist_ok=True)
        if conversation_file.exists():
            existing = conversation_file.read_text(encoding="utf-8")
            full_content = existing.rstrip("\n") + "\n\n" + "\n\n".join(entries)
        else:
            frontmatter = {
                "title": f"Jarvis Conversation Log — {date}",
                "date": date,
                "type": "conversation",
                "entries": len(entries),
                "tags": ["jarvis", "conversation", "personal"]
            }
            full_content = _format_yaml_frontmatter(frontmatter) + "\n\n".join(entries)
        
        conversation_file.write_text(full_content, encoding="utf-8")
    
    return str(conversation_file)


# ─── Memory Storage ─────────────────────────────────────────────────────

def save_memory(category: str, value: str, key: str = None, source: str = "voice") -> str:
    """
    Save a memory fact to Obsidian AND SQLite.
    
    Creates a markdown file in memory/{category}/ for each fact.
    Also writes to SQLite via memory_db.remember() for compatibility.
    
    Returns the Obsidian file path.
    """
    # Write to SQLite (preserves existing data)
    db_key = db_remember(category, value, key=key, source=source)
    
    # Write to Obsidian vault
    category_dir = _MEMORY_DIR / category
    category_dir.mkdir(parents=True, exist_ok=True)
    
    if key:
        file_name = _sanitize_filename(key) + ".md"
    else:
        # Generate a name from the value
        short_value = value[:50].replace("\n", " ").strip()
        file_name = _sanitize_filename(short_value) + ".md"
    
    # Ensure unique filename
    file_path = category_dir / file_name
    counter = 1
    while file_path.exists():
        stem = file_path.stem + f"_{counter}"
        file_path = category_dir / stem + ".md"
        counter += 1
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = f"""{value}

---
*Category: {category} | Source: {source} | Updated: {now}*
"""
    
    frontmatter = {
        "category": category,
        "key": key or _sanitize_filename(value[:30]),
        "value": value[:200],
        "source": source,
        "created": now[:10],
        "updated": now[:10],
        "tags": ["jarvis-memory", category]
    }
    
    _write_markdown(file_path, content, frontmatter)
    
    return str(file_path)


def save_memory_batch(memory_update: dict) -> list[str]:
    """
    Save multiple memory facts at once.
    
    memory_update: dict of {category: [values] or {key: value}}
    Returns list of file paths created.
    """
    paths = []
    for category, items in memory_update.items():
        category = category.lower().strip()
        if category == "wishes":
            category = "future"
        if category not in ["identity", "past", "present", "future", "dreams",
                           "relationships", "preferences", "personality", "projects", "notes"]:
            category = "notes"
        
        if isinstance(items, dict):
            for key, entry in items.items():
                val = entry.get("value") if isinstance(entry, dict) else entry
                if val and str(val).strip():
                    paths.append(save_memory(category, str(val)[:500], key=key, source="voice"))
        elif isinstance(items, list):
            for val in items:
                if val and str(val).strip():
                    paths.append(save_memory(category, str(val)[:500], source="voice"))
        elif isinstance(items, str) and items.strip():
            paths.append(save_memory(category, items[:500], source="voice"))
    
    return paths


def forget_memory(category: str, key: str) -> bool:
    """Delete a memory fact from both Obsidian and SQLite."""
    # Delete from SQLite
    db_deleted = db_forget(category, key)
    
    # Delete from Obsidian
    category_dir = _MEMORY_DIR / category
    if category_dir.exists():
        for f in category_dir.glob(f"{_sanitize_filename(key)}*.md"):
            f.unlink()
            return True
    
    return db_deleted


# ─── Query/Search ───────────────────────────────────────────────────────

def get_conversation_history(date: str = None, limit: int = 50) -> str:
    """Get conversation history from Obsidian vault."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    conversation_file = _CONVERSATIONS_DIR / f"{date}.md"
    if conversation_file.exists():
        return _read_markdown(conversation_file)
    
    # Try to find the most recent conversation file
    conv_files = sorted(_CONVERSATIONS_DIR.glob("*.md"), reverse=True)
    for f in conv_files[:limit]:
        content = _read_markdown(f)
        if content:
            return content
    
    return ""


def get_memory_context() -> str:
    """Get all memory facts formatted for LLM context."""
    parts = []
    for category in ["identity", "past", "present", "future", "dreams",
                     "relationships", "preferences", "personality", "projects", "notes"]:
        cat_dir = _MEMORY_DIR / category
        if cat_dir.exists():
            for f in sorted(cat_dir.glob("*.md")):
                content = _read_markdown(f).strip()
                if content:
                    parts.append(f"**[{category}]**: {content[:200]}")
    
    return "\n".join(parts) if parts else ""


def search_vault(query: str, max_results: int = 10) -> list[dict]:
    """
    Search the entire vault for text matches.
    
    Returns list of {"path": ..., "snippet": ..., "category": ...}
    """
    results = []
    query_lower = query.lower()
    
    # Search conversations
    for f in _CONVERSATIONS_DIR.glob("**/*.md"):
        content = _read_markdown(f)
        if query_lower in content.lower():
            idx = content.lower().index(query_lower)
            snippet = content[max(0, idx-30):idx+len(query)+50].strip()
            results.append({
                "path": str(f),
                "snippet": snippet,
                "category": "conversation",
                "date": f.stem
            })
    
    # Search memory
    for f in _MEMORY_DIR.glob("**/*.md"):
        content = _read_markdown(f)
        if query_lower in content.lower():
            idx = content.lower().index(query_lower)
            snippet = content[max(0, idx-30):idx+len(query)+50].strip()
            results.append({
                "path": str(f),
                "snippet": snippet,
                "category": f.parent.name,
                "date": f.parent.name
            })
    
    # Search projects
    for f in _PROJECTS_DIR.glob("**/*.md"):
        content = _read_markdown(f)
        if query_lower in content.lower():
            idx = content.lower().index(query_lower)
            snippet = content[max(0, idx-30):idx+len(query)+50].strip()
            results.append({
                "path": str(f),
                "snippet": snippet,
                "category": "project",
                "date": f.parent.name
            })
    
    return results[:max_results]


# ─── Migration: SQLite → Obsidian ──────────────────────────────────────

def migrate_sqlite_to_obsidian() -> dict:
    """
    Migrate all existing SQLite memory data to Obsidian vault.
    
    Returns stats about the migration.
    """
    from memory import memory_db
    
    stats = {"memory": 0, "categories": set()}
    
    all_rows = memory_db.all_entries()
    for row in all_rows:
        category = row["category"]
        value = row["value"]
        key = row["key"]
        source = row["source"]
        
        # Skip if already exists in Obsidian
        cat_dir = _MEMORY_DIR / category
        if cat_dir.exists():
            expected_file = cat_dir / f"{_sanitize_filename(key)}.md"
            if expected_file.exists():
                stats["categories"].add(category)
                continue
        
        save_memory(category, value, key=key, source=source)
        stats["memory"] += 1
        stats["categories"].add(category)
    
    # Migrate chat history files
    chat_dir = Path(__file__).resolve().parent / "chat_history"
    if chat_dir.exists():
        migrated = 0
        for f in chat_dir.glob("*.md"):
            date_str = f.stem
            content = f.read_text(encoding="utf-8")
            dest = _CONVERSATIONS_DIR / f"{date_str}.md"
            if not dest.exists():
                dest.write_text(content, encoding="utf-8")
                migrated += 1
        stats["conversations_migrated"] = migrated
    
    stats["categories"] = list(stats["categories"])
    return stats


# ─── Context Retrieval for LLM ─────────────────────────────────────────

def get_vault_context(text: str = None) -> str:
    """
    Get vault context to send to the LLM.
    
    Includes recent conversations, memory facts, and project notes.
    This enables JARVIS to have full context whether online or offline.
    """
    parts = []
    
    # Recent conversations
    today = datetime.now().strftime("%Y-%m-%d")
    conv = get_conversation_history(today, limit=20)
    if conv:
        parts.append(f"## Today's Conversations\n\n{conv[:3000]}")
    
    # Memory facts
    memory = get_memory_context()
    if memory:
        parts.append(f"## Memory Facts\n\n{memory[:3000]}")
    
    # Recent projects
    for f in sorted(_PROJECTS_DIR.glob("**/*.md"))[-5:]:
        content = _read_markdown(f).strip()
        if content:
            parts.append(f"## Project: {f.parent.name}\n\n{content[:1000]}")
    
    # Search for relevant context if text provided
    if text:
        search_results = search_vault(text, max_results=5)
        if search_results:
            search_part = "\n".join(
                f"- [{r['category']}] {r['snippet'][:150]}..."
                for r in search_results
            )
            parts.append(f"## Related Context\n\n{search_part}")
    
    return "\n\n---\n\n".join(parts) if parts else ""


# ─── Status & Health Check ──────────────────────────────────────────────

def get_vault_stats() -> dict:
    """Get statistics about the vault."""
    stats = {
        "vault_path": str(_VAULT_DIR),
        "conversations": len(list(_CONVERSATIONS_DIR.glob("*.md"))),
        "memory_files": len(list(_MEMORY_DIR.glob("**/*.md"))),
        "project_files": len(list(_PROJECTS_DIR.glob("**/*.md"))),
        "categories": [],
        "total_size": 0,
    }
    
    for cat in ["identity", "past", "present", "future", "dreams",
                "relationships", "preferences", "personality", "projects", "notes"]:
        cat_dir = _MEMORY_DIR / cat
        if cat_dir.exists():
            files = list(cat_dir.glob("*.md"))
            if files:
                stats["categories"].append({"category": cat, "files": len(files)})
    
    # Calculate total size
    for f in _VAULT_DIR.rglob("*.md"):
        try:
            stats["total_size"] += f.stat().st_size
        except OSError:
            pass
    
    stats["total_size_human"] = _format_bytes(stats["total_size"])
    return stats


def _format_bytes(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def health_check() -> dict:
    """Check if the Obsidian vault is working properly."""
    import os as _os
    
    status = {
        "vault_exists": _VAULT_DIR.exists(),
        "writable": False,
        "conversations_dir": _CONVERSATIONS_DIR.exists(),
        "memory_dir": _MEMORY_DIR.exists(),
        "sqlite_db_exists": _os.path.exists(str(Path(__file__).resolve().parent / "memory" / "personal_memory.sqlite3")),
        "total_entries": 0,
        "errors": [],
    }
    
    if _VAULT_DIR.exists():
        try:
            test_file = _VAULT_DIR / "_health_test.md"
            test_file.write_text("health check", encoding="utf-8")
            status["writable"] = test_file.exists()
            test_file.unlink()
        except Exception as e:
            status["errors"].append(f"Write test failed: {e}")
    
    # Count total entries
    status["total_entries"] = (
        len(list(_CONVERSATIONS_DIR.glob("*.md"))) +
        len(list(_MEMORY_DIR.glob("**/*.md"))) +
        len(list(_PROJECTS_DIR.glob("**/*.md")))
    )
    
    return status


# ─── Local REST API (Obsidian 27124) ──────────────────────────────

def api_request(method: str, endpoint: str, data: dict = None) -> dict | None:
    """
    Make a request to the Obsidian Local REST API (port 27124).
    
    NOTE: The 'Local REST API with MCP' plugin uses MCP protocol (WebSocket),
    not standard HTTP REST. File-system access is the primary method.
    This function provides optional HTTP access if the standard REST mode
    is enabled in plugin settings.
    
    Returns the JSON response or None if unavailable.
    """
    if not _OBSIDIAN_API_ENABLED:
        return None
    
    try:
        import requests
        url = f"{_OBSIDIAN_API_URL}/v1/{endpoint}"
        headers = dict(_OBSIDIAN_API_HEADERS)
        
        resp = requests.request(
            method, url, json=data, headers=headers, timeout=5
        )
        
        if resp.status_code in (200, 201):
            try:
                return resp.json()
            except Exception:
                return {"status": resp.status_code}
        elif resp.status_code == 401:
            print(f"[Obsidian API] ⚠️ Unauthorized — check API key")
            return None
        else:
            return {"status": resp.status_code, "error": resp.text[:100]}
    except requests.ConnectionError:
        return None
    except Exception as e:
        return None


def obsidian_list_files() -> list[dict]:
    """List all files in the vault via Local REST API (or file-system fallback)."""
    # Try REST API first
    result = api_request("GET", "files")
    if result and isinstance(result, list):
        return result
    
    # Fallback to file-system listing
    files = []
    for f in _VAULT_DIR.rglob("*.md"):
        rel = f.relative_to(_VAULT_DIR)
        files.append({"path": str(rel), "name": f.name})
    return files


def obsidian_read_file(path: str) -> str:
    """Read a file from the vault (REST API or file-system fallback)."""
    # Try REST API first
    result = api_request("GET", f"file?path={path}")
    if result and isinstance(result, dict) and "content" in result:
        return result["content"]
    
    # Fallback to file-system
    full_path = _VAULT_DIR / path
    if full_path.exists():
        return _read_markdown(full_path)
    return ""


def obsidian_create_file(path: str, content: str) -> bool:
    """Create a file in the vault (REST API or file-system fallback)."""
    # Try REST API first
    result = api_request("PUT", f"file?path={path}", {"content": content})
    if result is not None and result.get("status") == 201:
        return True
    
    # Fallback to file-system
    try:
        full_path = _VAULT_DIR / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return True
    except Exception:
        return False


def obsidian_search_vault(query: str, limit: int = 10) -> list[dict]:
    """Search the vault (REST API or file-system fallback)."""
    # Try REST API first
    result = api_request("GET", f"search?query={query}&limit={limit}")
    if result and isinstance(result, list):
        return result
    
    # Fallback to file-system search
    return search_vault(query, max_results=limit)


def obsidian_api_available() -> bool:
    """Check if the Local REST API is available via HTTP.
    
    Note: Returns True if the MCP server is running, even if
    standard HTTP endpoints don't respond (MCP uses WebSocket).
    """
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', 27124))
        sock.close()
        return result == 0
    except Exception:
        return False


# ─── Unified Read/Write (works regardless of API mode) ───────

def vault_read(path: str) -> str:
    """Read any vault file by relative path (e.g., 'memory/identity/user_name.md')."""
    full_path = _VAULT_DIR / path
    if full_path.exists():
        return _read_markdown(full_path)
    return ""


def vault_write(path: str, content: str) -> bool:
    """Write any vault file by relative path."""
    full_path = _VAULT_DIR / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")
    return True


def vault_delete(path: str) -> bool:
    """Delete a vault file by relative path."""
    full_path = _VAULT_DIR / path
    if full_path.exists():
        full_path.unlink()
        return True
    return False


def vault_exists(path: str) -> bool:
    """Check if a vault file exists."""
    return (_VAULT_DIR / path).exists()