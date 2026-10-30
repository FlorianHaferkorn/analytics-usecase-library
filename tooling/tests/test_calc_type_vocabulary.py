"""calc_type: das Enum in kpi_definition.schema.json ist die Quelle.

Folger: validate_kpi_catalog.ps1 ($allowedCalc), usecase_bracket.schema.json
(component_30s.unit) und comparison_measures.SUMME (Teilmenge). Alle KPI-Dateien
tragen nur Werte aus dem Enum.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterator

import yaml

from tooling.codegen.comparison_measures import SUMME

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "tooling" / "generator" / "schemas"


def _schema_enum() -> set[str]:
    s = json.loads((SCHEMAS / "kpi_definition.schema.json").read_text(encoding="utf-8"))
    return set(s["properties"]["calc_type"]["enum"])


def _walk(node: Any) -> Iterator[tuple[str, Any]]:
    if isinstance(node, dict):
        for k, v in node.items():
            yield k, v
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


def test_ps1_allowed_calc_equals_schema() -> None:
    text = (ROOT / "tooling" / "validation" / "validate_kpi_catalog.ps1").read_text(encoding="utf-8")
    m = re.search(r"\$allowedCalc\s*=\s*@\(([^)]*)\)", text)
    assert m, "$allowedCalc nicht gefunden"
    assert set(re.findall(r"'([^']+)'", m.group(1))) == _schema_enum()


def test_bracket_unit_enum_equals_schema() -> None:
    s = json.loads((SCHEMAS / "usecase_bracket.schema.json").read_text(encoding="utf-8"))
    units = [v["enum"] for k, v in _walk(s)
             if k == "unit" and isinstance(v, dict) and "enum" in v]
    assert len(units) >= 1
    for enum in units:
        assert set(enum) == _schema_enum()


def test_summe_is_subset_of_schema() -> None:
    assert SUMME <= _schema_enum()


def test_all_kpis_use_schema_values() -> None:
    allowed = _schema_enum()
    files = list((ROOT / "core" / "kpi_catalog" / "kpis").glob("KPI-*.yaml"))
    assert len(files) >= 100, f"nur {len(files)} KPI-Dateien"
    bad = [f"{p.name}: {d.get('calc_type')}" for p in files
           if (d := yaml.safe_load(p.read_text(encoding="utf-8"))).get("calc_type") not in allowed]
    assert not bad, bad
