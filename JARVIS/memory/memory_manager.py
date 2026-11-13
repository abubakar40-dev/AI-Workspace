# memory/memory_manager.py
#
# Public API used by main.py -- unchanged function names/signatures so the
# rest of the app doesn't need edits. Internally this now delegates to
# memory/memory_db.py (SQLite, unbounded) instead of the old flat JSON file
# that silently deleted old facts once it hit a 2200-character cap.

import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from memory import memory_db

# Obsidian vault integration — dual-write to both SQLite and Obsidian
try:
    from obsidian_integration import save_memory as obsidian_save_memory
    _OBSIDIAN_ENABLED = True
except ImportError:
    _OBSIDIAN_ENABLED = False

# New, richer category set. "wishes" (old schema) maps onto "future".
CATEGORIES = ["identity", "past", "present", "future", "dreams",
              "relationships", "preferences", "personality", "projects", "notes"]

MAX_VALUE_LENGTH = 500
_stage1_retry_at = 0.0
_stage1_warning_logged = False


def load_memory() -> dict:
    """Returns the full memory as a nested dict, same shape the old JSON
    store used (category -> key -> {"value": ..., "updated": ...}), for
    any code that still expects that shape."""
    memory_db.migrate_legacy_json()
    out = {cat: {} for cat in CATEGORIES}
    for row in memory_db.all_entries():
        cat = row["category"] if row["category"] in CATEGORIES else "notes"
        out[cat][row["key"]] = {
            "value": row["value"],
            "updated": row["updated_at"][:10],
            "source": row["source"],
        }
    return out


def update_memory(memory_update: dict) -> dict:
    """Accepts the same nested-dict shape the LLM extraction prompt
    produces (category -> key -> {"value": ...} or category -> narrative
    string) and writes each fact into the database."""
    if not isinstance(memory_update, dict) or not memory_update:
        return load_memory()

    saved_any = False
    for category, items in memory_update.items():
        category = category.lower().strip()
        if category == "wishes":
            category = "future"
        if category not in CATEGORIES:
            category = "notes"

        if isinstance(items, dict):
            for key, entry in items.items():
                val = entry.get("value") if isinstance(entry, dict) else entry
                if val and str(val).strip():
                    memory_db.remember(category, str(val)[:MAX_VALUE_LENGTH], key=key, source="voice")
                    saved_any = True
        elif isinstance(items, list):
            for val in items:
                if val and str(val).strip():
                    memory_db.remember(category, str(val)[:MAX_VALUE_LENGTH], source="voice")
                    saved_any = True
        elif isinstance(items, str) and items.strip():
            memory_db.remember(category, items[:MAX_VALUE_LENGTH], source="voice")
            saved_any = True

    if saved_any:
        print(f"[Memory] 💾 Saved facts: {list(memory_update.keys())}")

    # Also write to Obsidian vault (dual-write)
    if _OBSIDIAN_ENABLED:
        try:
            from obsidian_integration import save_memory_batch
            save_memory_batch(memory_update)
            print(f"[Memory] 📝 Synced to Obsidian vault")
        except Exception:
            pass  # Obsidian write failure doesn't break SQLite

    return load_memory()


def should_extract_memory(user_text: str, brahma_text: str, api_key: str = "") -> bool:
    global _stage1_retry_at, _stage1_warning_logged
    if time.time() < _stage1_retry_at:
        return False

    combined = f"User: {user_text[:300]}\nJarvis: {brahma_text[:1000]}"
    prompt = (
        f"Does this conversation contain ANY of the following worth remembering long-term?\n"
        f"- Personal facts (name, age, city, job, birthday, nationality)\n"
        f"- Life history, background, past events\n"
        f"- Current projects, current situation, ongoing challenges\n"
        f"- Future goals, plans, ambitions\n"
        f"- Deeper dreams, aspirations, what they care about\n"
        f"- People in their life (friends, family, partner, colleagues)\n"
        f"- Preferences or favorites\n"
        f"- Personality or working-style patterns\n"
        f"- Any other fact worth remembering long-term\n\n"
        f"Reply only YES or NO.\n\nConversation:\n{combined}"
    )
    system = "You are a memory relevance checker. Reply only YES or NO."

    try:
        from or_client import client
        result = client.chat(prompt, system=system, max_tokens=5, temperature=0.0)
        return "YES" in result.upper()
    except Exception as e:
        if not _stage1_warning_logged:
            print(f"[Memory] ⚠️ Stage1 provider unavailable; using local fallback: {e}")

    try:
        import nrouter_client
        result = nrouter_client.chat(prompt, system=system, max_tokens=5, temperature=0.0)
        return "YES" in result.upper()
    except Exception as e:
        if not _stage1_warning_logged:
            print(f"[Memory] ⚠️ Stage1 nRouter unavailable: {e}")

    try:
        from ollama_client import client as ollama_client
        result = ollama_client.chat(prompt, system=system, max_tokens=5, temperature=0.0)
        return "YES" in result.upper()
    except Exception as e:
        _stage1_retry_at = time.time() + 60
        if not _stage1_warning_logged:
            print(f"[Memory] ⚠️ Memory extraction paused for 60s: {e}")
            _stage1_warning_logged = True
        return False


def extract_memory(user_text: str, brahma_text: str, api_key: str = "") -> dict:
    combined = f"User: {user_text[:600]}\nJarvis: {brahma_text[:300]}"
    prompt = (
        f"Extract ALL memorable personal facts from this conversation. Any language.\n"
        f"Return ONLY valid JSON. Use {{}} if truly nothing is worth saving.\n\n"
        f"Category guide:\n"
        f"  identity      → name, age, birthday, city, country, job, school, nationality, language\n"
        f"  past          → life history, background, past events, career history, formative experiences\n"
        f"  present       → current projects, current job/situation, current challenges, what they're\n"
        f"                  actively working on or dealing with right now\n"
        f"  future        → goals, plans, ambitions, things they want to do, upcoming events\n"
        f"  dreams        → deeper aspirations, what they care about, what they're working toward on\n"
        f"                  a deeper level, recurring themes in what they say they want out of life\n"
        f"  relationships → people mentioned: friends, family, partner, colleagues, and what's known\n"
        f"                  about them and the relationship\n"
        f"  preferences   → ANY favorite or preferred thing: food, color, music, film, game, sport,\n"
        f"                  book, tools, working style, communication style, dislikes, etc.\n"
        f"  personality   → patterns in how they think, work, communicate, make decisions\n"
        f"  projects      → specific named projects/tools they're building\n"
        f"  notes         → anything else worth remembering (habits, schedule, etc.)\n\n"
        f"IMPORTANT:\n"
        f"- Be LIBERAL: if something MIGHT be worth remembering, include it.\n"
        f"- Extract from BOTH user and Jarvis turns.\n"
        f"- Skip: weather, reminders, search results, one-time commands.\n"
        f"- Use concise English values regardless of conversation language.\n"
        f"- For past/present/future/dreams/personality/notes, keys are optional -- you can just\n"
        f"  provide a list of short fact strings if a natural key isn't obvious.\n\n"
        f"Format:\n"
        f'{{"identity":{{"name":{{"value":"Ali"}}}},\n'
        f' "present":["Building a new mobile app", "Studying for finals"],\n'
        f' "dreams":["Wants to become financially independent by 30"],\n'
        f' "preferences":{{"favorite_color":{{"value":"blue"}}}},\n'
        f' "relationships":{{"friend_yusuf":{{"value":"close friend"}}}}}}\n\n'
        f"Conversation:\n{combined}\n\nJSON:"
    )
    system = "Return ONLY valid JSON. No markdown, no explanation, no extra text."

    def _clean_and_parse(raw: str) -> dict:
        clean = raw.strip()
        clean = re.sub(r"```(?:json)?", "", clean).strip().rstrip("`").strip()
        if not clean or clean == "{}":
            return {}
        return json.loads(clean)

    try:
        from or_client import client
        raw = client.chat(prompt, system=system, max_tokens=1024, temperature=0.2)
        return _clean_and_parse(raw)
    except json.JSONDecodeError:
        return {}
    except Exception as e:
        if "429" not in str(e):
            print(f"[Memory] ⚠️ Extract failed (OpenRouter): {e}")

    try:
        import nrouter_client
        return _clean_and_parse(nrouter_client.chat(
            prompt, system=system, max_tokens=1024, temperature=0.2
        ))
    except Exception as e:
        if "429" not in str(e):
            print(f"[Memory] ⚠️ Extract failed (nRouter): {e}")

    try:
        from ollama_client import client as ollama_client
        raw = ollama_client.chat(prompt, system=system, max_tokens=1024, temperature=0.2)
        return _clean_and_parse(raw)
    except json.JSONDecodeError:
        return {}
    except Exception as e:
        print(f"[Memory] ⚠️ Extract failed (local Qwen too): {e}")
        return {}


def _section(title: str, category: str, limit: int = 12, bullet_keys: bool = True) -> list[str]:
    rows = memory_db.recent(category, limit=limit)
    if not rows:
        return []
    lines = ["", f"{title}:"]
    for row in rows:
        if bullet_keys and not row["key"].startswith(f"{category}_"):
            # a real, human-meaningful key (e.g. "name", "favorite_color")
            lines.append(f"  - {row['key'].replace('_', ' ').title()}: {row['value']}")
        else:
            # auto-generated hash key -- narrative fact, no title needed
            lines.append(f"  - {row['value']}")
    return lines


def format_memory_for_prompt(memory: dict | None = None) -> str:
    """Builds the context block fed to Jarvis's system prompt each turn.
    Pulls the most recently-updated facts per category from the database
    (which itself never deletes anything) so the LLM context stays a
    manageable size even as lifelong memory grows unbounded in storage."""
    lines: list[str] = []

    identity_rows = memory_db.recent("identity", limit=20)
    if identity_rows:
        for row in identity_rows:
            if row["key"].startswith("identity_"):
                # auto-generated hash key -- narrative fact with no clean
                # "Key: Value" form, just print the fact plainly.
                lines.append(row["value"])
            else:
                lines.append(f"{row['key'].replace('_', ' ').title()}: {row['value']}")

    lines += _section("Life history", "past", limit=10)
    lines += _section("Current situation", "present", limit=10)
    lines += _section("Future goals / plans", "future", limit=10)
    lines += _section("Deeper dreams / aspirations", "dreams", limit=8)
    lines += _section("People in their life", "relationships", limit=10)
    lines += _section("Preferences", "preferences", limit=15)
    lines += _section("Personality / working style", "personality", limit=8)
    lines += _section("Active projects", "projects", limit=8)
    lines += _section("Other notes", "notes", limit=8)

    if not lines:
        return ""

    header = (
        "[WHAT YOU KNOW ABOUT THIS PERSON — use naturally in conversation, "
        "never recite as a list]\n"
    )
    result = header + "\n".join(lines)
    # Gemini's context window is enormous relative to a personal-memory
    # block -- this cap exists only to avoid unbounded growth over years
    # of use, not because a few thousand extra characters cost anything
    # meaningful. Truncate at a line boundary, never mid-word.
    MAX_PROMPT_CHARS = 8000
    if len(result) > MAX_PROMPT_CHARS:
        result = result[:MAX_PROMPT_CHARS]
        last_newline = result.rfind("\n")
        if last_newline > 0:
            result = result[:last_newline]
        result += "\n…"
    return result + "\n"


def remember(key: str, value: str, category: str = "notes") -> str:
    if category not in CATEGORIES:
        category = "notes"
    memory_db.remember(category, value, key=key, source="manual")
    return f"Remembered: {category}/{key} = {value}"


def forget(key: str, category: str = "notes") -> str:
    if memory_db.forget(category, key):
        return f"Forgotten: {category}/{key}"
    return f"Not found: {category}/{key}"
