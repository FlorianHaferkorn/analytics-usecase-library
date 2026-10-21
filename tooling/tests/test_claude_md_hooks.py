"""CLAUDE.md nennt genau die PostToolUse-Hooks, die .claude/settings.json verdrahtet.

Quelle ist settings.json; CLAUDE.md folgt. Kein Zähler im Text, sondern die Namen —
der Test vergleicht beide Mengen.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _settings_hooks() -> set[str]:
    data = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    names: set[str] = set()
    for block in data.get("hooks", {}).get("PostToolUse", []):
        for hook in block.get("hooks", []):
            m = re.search(r"([\w.-]+\.sh)", hook.get("command", ""))
            if m:
                names.add(m.group(1))
    return names


def _claude_md_hooks() -> set[str]:
    text = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    section = text.split("### PostToolUse-Hooks", 1)[1].split("\n### ", 1)[0]
    return set(re.findall(r"^- \*\*`([\w.-]+\.sh)`\*\*", section, flags=re.M))


def test_claude_md_lists_exactly_the_configured_hooks() -> None:
    configured = _settings_hooks()
    assert len(configured) >= 2, "settings.json ohne PostToolUse-Hooks gelesen"
    assert _claude_md_hooks() == configured


def test_claude_md_hook_section_has_no_counter_word() -> None:
    text = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    section = text.split("### PostToolUse-Hooks", 1)[1].split("\n### ", 1)[0]
    assert not re.search(r"\b(Zwei|Drei|Vier|Fünf|\d+)\s+Hooks\b", section)
