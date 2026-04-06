"""
Knowledge Base — reads and writes the structured error KB (errors.yaml).

The KB stores known error patterns, their causes, and fixes.  When a new
error class is encountered that is not in the KB, the system appends a
skeleton entry so a human (or future AI pass) can fill in the fix.

errors.yaml format
------------------
version: "1.0"
entries:
  - id: "TMDL-001"
    category: "tmdl_syntax"
    symptom: "tabs_only|indentation"
    symptom_regex: true           # treat symptom as regex (default: false)
    cause: "..."
    fix: "..."
    auto_fix_commands: []         # optional shell commands
    added_date: "2026-01-15"
    source: "human"               # "human" | "agent" | "pipeline"

Usage
-----
    from tooling.generator_core.intelligence.kb import KnowledgeBase

    kb = KnowledgeBase()
    entry = kb.lookup("[MISSING_KPI] KPI 'com.foo' not in catalog")
    if entry:
        print(entry.fix)
    else:
        kb.append_unknown("some_new_error_message", category="unknown")
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class KBEntry:
    id: str
    category: str
    symptom: str
    cause: str
    fix: str
    symptom_regex: bool = False
    auto_fix_commands: List[str] = field(default_factory=list)
    added_date: str = ""
    source: str = "agent"          # "human" | "agent" | "pipeline"
    examples: List[str] = field(default_factory=list)

    def matches(self, error_message: str) -> bool:
        if self.symptom_regex:
            return bool(re.search(self.symptom, error_message, re.IGNORECASE))
        return self.symptom.lower() in error_message.lower()

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # Remove empty lists/defaults to keep YAML clean
        if not d["auto_fix_commands"]:
            d.pop("auto_fix_commands")
        if not d["examples"]:
            d.pop("examples")
        if not d["symptom_regex"]:
            d.pop("symptom_regex")
        return d


# ---------------------------------------------------------------------------
# Knowledge base
# ---------------------------------------------------------------------------

class KnowledgeBase:
    """
    Manages the structured error knowledge base.

    Parameters
    ----------
    kb_path
        Path to errors.yaml.  Defaults to the bundled knowledge_base/errors.yaml.
    auto_append
        If True (default), unknown errors are automatically appended as skeleton
        entries so they can be reviewed and completed by a human.
    """

    def __init__(
        self,
        kb_path: Optional[Path] = None,
        auto_append: bool = True,
    ) -> None:
        self.kb_path = kb_path or self._default_path()
        self.auto_append = auto_append
        self._entries: List[KBEntry] = []
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def lookup(self, error_message: str) -> Optional[KBEntry]:
        """Return the first KB entry whose symptom matches the error message."""
        for entry in self._entries:
            if entry.matches(error_message):
                return entry
        return None

    def lookup_by_category(self, category: str) -> List[KBEntry]:
        """Return all KB entries for a given category string."""
        return [e for e in self._entries if e.category == category]

    def is_known(self, error_message: str) -> bool:
        return self.lookup(error_message) is not None

    def append(self, entry: KBEntry) -> None:
        """Append a new entry and save to disk."""
        # Avoid duplicates by id
        if any(e.id == entry.id for e in self._entries):
            return
        self._entries.append(entry)
        self._save()

    def append_unknown(
        self,
        error_message: str,
        category: str = "unknown",
        entry_id: Optional[str] = None,
    ) -> KBEntry:
        """
        Auto-append a skeleton entry for an unseen error.

        The skeleton has placeholder cause/fix text so a human or future
        AI pass can complete it.  Returns the created entry.
        """
        # Build a stable ID from the error message
        if not entry_id:
            safe = re.sub(r"[^a-z0-9]", "_", error_message[:40].lower()).strip("_")
            entry_id = f"AUTO-{category[:4].upper()}-{safe[:20]}"

        if self.is_known(error_message):
            return self.lookup(error_message)  # type: ignore[return-value]

        entry = KBEntry(
            id=entry_id,
            category=category,
            symptom=error_message[:120],
            symptom_regex=False,
            cause="TODO: investigate cause",
            fix="TODO: document fix",
            auto_fix_commands=[],
            added_date=str(date.today()),
            source="agent",
            examples=[error_message[:200]],
        )
        if self.auto_append:
            self.append(entry)
        return entry

    def all_entries(self) -> List[KBEntry]:
        return list(self._entries)

    def entry_count(self) -> int:
        return len(self._entries)

    def categories(self) -> List[str]:
        return sorted({e.category for e in self._entries})

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if not self.kb_path.is_file():
            self._entries = []
            return
        with open(self.kb_path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        self._entries = [KBEntry(**e) for e in data.get("entries", [])]

    def _save(self) -> None:
        self.kb_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": "1.0",
            "entries": [e.to_dict() for e in self._entries],
        }
        with open(self.kb_path, "w", encoding="utf-8") as fh:
            yaml.dump(data, fh, allow_unicode=True, sort_keys=False, default_flow_style=False)

    @staticmethod
    def _default_path() -> Path:
        return Path(__file__).parent.parent / "knowledge_base" / "errors.yaml"
