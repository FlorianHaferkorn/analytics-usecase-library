"""DAX-Doktrin (docs/agent/rules/tmdl-dax.md, Abschnitt 'Filter propagation').

FILTER(ALL(<Tabelle>)) ist nur fuer Datumsfenster auf der Datumstabelle erlaubt.
Gemessen wird ueber KPI-Katalog, DAX-Generatoren und die ausgelieferten Modelle.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULE = ROOT / "docs" / "agent" / "rules" / "tmdl-dax.md"
DATE_TABLES = {"dim_date", "date", "calendar", "dim_calendar"}
PATTERN = re.compile(r"FILTER\s*\(\s*ALL\s*\(\s*'?([A-Za-z_][A-Za-z0-9_ ]*?)'?\s*[\),\[]", re.I)

SCAN = [
    (ROOT / "core" / "kpi_catalog", "*.yaml"),
    (ROOT / "tooling" / "codegen", "*.py"),
    (ROOT / "products" / "fabric" / "powerbi" / "dist", "*.tmdl"),
]


def _hits() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for base, glob in SCAN:
        for p in base.rglob(glob):
            for m in PATTERN.finditer(p.read_text(encoding="utf-8", errors="ignore")):
                out.append((p.relative_to(ROOT).as_posix(), m.group(1).strip()))
    return out


def test_filter_all_only_on_date_tables() -> None:
    hits = _hits()
    assert len(hits) >= 50, f"nur {len(hits)} FILTER(ALL())-Stellen gefunden — Scan defekt?"
    bad = [(f, t) for f, t in hits if t.lower() not in DATE_TABLES]
    assert not bad, f"FILTER(ALL()) auf Nicht-Datumstabelle: {bad[:10]}"


def test_rule_states_the_three_doctrine_points() -> None:
    text = RULE.read_text(encoding="utf-8")
    section = text.split("### Filter propagation", 1)[1]
    assert "Physical relationship first" in section
    assert "`TREATAS` for virtual relationships" in section
    assert "FILTER(ALL(<date table>), ...)` is allowed for date windows" in section
