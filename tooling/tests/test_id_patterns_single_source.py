"""ID-Muster: das Schema ist die Quelle, Taxonomie und Preflight folgen.

Quelle: usecase_bracket.schema.json (id), kpi_definition.schema.json (kpi_id),
action_code.schema.json (id) — gelesen ueber tooling/generator_core/id_patterns.py.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from tooling.generator_core import id_patterns as ip
from tooling.generator_core.preflight.checks import PreflightContext, check_bracket_required_fields

ROOT = Path(__file__).resolve().parents[2]
TAX = ROOT / "tooling" / "validation" / "_index.yaml"


def test_taxonomy_equals_schema_patterns() -> None:
    pats = yaml.safe_load(TAX.read_text(encoding="utf-8"))["id_patterns"]
    assert pats["use_case"]["regex"] == ip.use_case_pattern()
    assert pats["kpi"]["regex"] == ip.kpi_pattern()
    assert pats["action_code"]["regex"] == ip.action_code_pattern()


def test_all_bracket_ids_match_schema() -> None:
    n = 0
    for p in (ROOT / "core" / "usecases").rglob("UseCase_Bracket.yaml"):
        uid = (yaml.safe_load(p.read_text(encoding="utf-8")) or {}).get("id")
        if uid:
            n += 1
            assert ip.use_case_re().match(uid), f"{p}: {uid}"
    assert n >= 20, f"nur {n} Brackets gelesen"


def test_all_action_code_ids_match_schema() -> None:
    n = 0
    for p in (ROOT / "core" / "action_codes").rglob("*.yaml"):
        if "decision_spines" in p.parts or p.name == "impactful_15.yaml" \
                or p.name.endswith("_business_case.yaml"):
            continue
        d = yaml.safe_load(p.read_text(encoding="utf-8"))
        if isinstance(d, dict) and "id" in d:
            n += 1
            assert ip.action_code_re().match(str(d["id"])), f"{p}: {d['id']}"
    assert n >= 50, f"nur {n} Action Codes gelesen"


def test_all_kpi_ids_match_schema() -> None:
    files = list((ROOT / "core" / "kpi_catalog" / "kpis").glob("KPI-*.yaml"))
    assert len(files) >= 100
    for p in files:
        assert ip.kpi_re().match(p.stem), p.name


def _ctx(uid: str) -> PreflightContext:
    return PreflightContext(
        bracket_path=Path("x"),
        bracket={"id": uid, "primary_kpi_ids": [], "ux_layout_rules": {}},
        kpi_catalog_root=Path("x"),
        action_codes_root=Path("x"),
    )


@pytest.mark.parametrize(("uid", "warns"), [
    ("COM-001", False), ("COM-EXT-001", False), ("COM-IND-R001", False),
    ("COMMS-001", True), ("com-001", True),
])
def test_preflight_uses_schema_pattern(uid: str, warns: bool) -> None:
    ctx = _ctx(uid)
    check_bracket_required_fields(ctx)
    assert any("BRACKET_ID_FORMAT" in w for w in ctx.warnings) is warns
