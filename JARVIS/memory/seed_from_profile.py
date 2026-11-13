# memory/seed_from_profile.py
#
# Imports a structured personal profile (## IDENTITY / ## PAST / ## PRESENT /
# ## FUTURE / ## DREAMS / ## RELATIONSHIPS / ## PREFERENCES /
# ## PERSONALITY & WORKING STYLE / ## NOTES, each with "- bullet" facts)
# into the SQLite personal memory database.
#
# Usage:
#   python memory/seed_from_profile.py path/to/profile.md

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from memory import memory_db

HEADING_MAP = {
    "IDENTITY": "identity",
    "PAST": "past",
    "PRESENT": "present",
    "FUTURE": "future",
    "DREAMS": "dreams",
    "RELATIONSHIPS": "relationships",
    "PREFERENCES": "preferences",
    "PERSONALITY & WORKING STYLE": "personality",
    "PERSONALITY AND WORKING STYLE": "personality",
    "PROJECTS": "projects",
    "NOTES": "notes",
}

# For IDENTITY specifically, try to parse "Key: Value" into a real key so
# it reads naturally in the prompt context ("Name: AbuBakar" -> key="name").
_KV_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9 /]{1,40}?):\s+(.+)$")


def parse_profile(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current = None
    for line in text.splitlines():
        stripped = line.strip()
        heading_match = re.match(r"^#{1,3}\s*(.+?)\s*$", stripped)
        if heading_match:
            heading = heading_match.group(1).upper().strip()
            current = HEADING_MAP.get(heading)
            if current and current not in sections:
                sections[current] = []
            continue
        if current and stripped.startswith(("-", "*")):
            fact = stripped.lstrip("-*").strip()
            if fact:
                sections[current].append(fact)
    return sections


def import_profile(path: str) -> int:
    text = Path(path).read_text(encoding="utf-8")
    sections = parse_profile(text)

    imported = 0
    for category, facts in sections.items():
        for fact in facts:
            key = None
            if category == "identity":
                m = _KV_RE.match(fact)
                if m:
                    key = m.group(1).strip().lower().replace(" ", "_").replace("/", "_")
                    fact = m.group(2).strip()
            memory_db.remember(category, fact, key=key, source="seed")
            imported += 1

    return imported


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python memory/seed_from_profile.py path/to/profile.md")
        sys.exit(1)

    n = import_profile(sys.argv[1])
    print(f"Imported {n} facts.")
    print(f"Total facts now in database: {memory_db.count()}")
