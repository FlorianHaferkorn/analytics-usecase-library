"""Unit tests for studio cascading reconcile helpers (imported via subprocess-free logic copy)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# Minimal mirror of TS logic for CI — keep in sync with studio/src/lib/studio/cascading-reconcile.ts
# Table rows use single pipes (| col | col |), matching rebuildFactsheetSection3 output.
SAMPLE_BRACKET = """
orchestration:
  strategic_kpi_id: margin.gm.pct
  influencing_kpi_ids:
    - sales.net_sales.amount
  action_code_ids:
    - C-S1.1
""".strip()

SAMPLE_FACTSHEET = """
### 3. KPI & Action Code Overview

| KPI ID | Role |
|--------|------|
| margin.gm.pct | Strategic |
| sales.net_sales.amount | Influencing |
| cost.cogs.amount | Influencing |

**Action Codes:** C-S1.1, C-S1.2

> Full machine-readable configuration in `UseCase_Bracket.yaml` (SSOT).

---
""".strip()


def _extract_kpi_roles(markdown: str) -> list[tuple[str, str]]:
    section = re.search(
        r"###\s+3\.\s+KPI\s*&\s*Action Code Overview([\s\S]*?)(?=^##\s|\Z)",
        markdown,
        re.MULTILINE,
    )
    if not section:
        return []
    rows = []
    for m in re.finditer(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", section.group(1), re.MULTILINE):
        col1, col2 = m.group(1).strip(), m.group(2).strip()
        if col1.lower() == "kpi id" or col1.startswith("-"):
            continue
        if "." in col1:
            rows.append((col1, col2))
    return rows


def test_extract_factsheet_kpi_roles_finds_influencing():
    roles = _extract_kpi_roles(SAMPLE_FACTSHEET)
    ids = [r[0] for r in roles]
    assert "cost.cogs.amount" in ids
    assert "margin.gm.pct" in ids


def _upsert_yaml_list(yaml: str, key: str, values: list[str]) -> str:
    lines = yaml.split("\n")
    key_re = re.compile(rf"^(\s*){re.escape(key)}:\s*$")
    start = -1
    indent = "  "
    for i, line in enumerate(lines):
        m = key_re.match(line)
        if m:
            start = i
            indent = m.group(1) + "  "
            break
    if start == -1:
        return yaml
    end = start + 1
    while end < len(lines) and (
        lines[end].startswith(indent + "-") or lines[end].strip() == ""
    ):
        if lines[end].strip().startswith("-") or lines[end].strip() == "":
            end += 1
        else:
            break
    new_lines = [f"{indent}- {v}" for v in values]
    return "\n".join([*lines[: start + 1], *new_lines, *lines[end:]])


def _list_changed(next_vals: list[str], current: list[str] | None) -> bool:
    prev = current or []
    return next_vals != prev


def test_upsert_yaml_list_clears_items():
    cleared = _upsert_yaml_list(SAMPLE_BRACKET, "influencing_kpi_ids", [])
    assert "sales.net_sales.amount" not in cleared
    assert "influencing_kpi_ids:" in cleared


def test_list_changed_detects_empty_vs_populated():
    assert _list_changed([], ["sales.net_sales.amount"]) is True
    assert _list_changed([], []) is False


def test_cascading_reconcile_module_exists():
    path = Path("studio/src/lib/studio/cascading-reconcile.ts")
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "reconcileDeterministic" in text
    assert "listChanged" in text
