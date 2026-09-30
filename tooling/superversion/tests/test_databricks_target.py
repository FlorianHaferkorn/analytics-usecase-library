"""I-7.2 — Databricks Metric View target emits valid metric-view YAML.

Second semantic-layer stack (Tool-Agnostik-Beweis). Validates the emitted YAML
against the docs-derived JSON Schema (ALUCA-authored from the official Databricks
YAML reference). The vendor's own validator (a Databricks workspace) is the
production gate and is out of scope offline (Ehrlichkeit v3) — see databricks.py.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from tooling.superversion.from_aluca import from_bracket_file
from tooling.superversion.targets import base
from tooling.superversion.targets import databricks  # noqa: F401 — registers "databricks"

REPO = Path(__file__).resolve().parents[3]
KPIS = REPO / "core/kpi_catalog/kpis"
COM001 = REPO / "core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml"
SCHEMA = Path(__file__).resolve().parents[1] / "targets" / "schemas" / "databricks_metricview.schema.json"


def _emit():
    model = from_bracket_file(COM001, KPIS)
    return base.get("databricks").emit(model)


def test_databricks_registered_beta():
    assert "databricks" in base.available()
    # beta: local gate is docs-derived; the vendor workspace validator is geplant.
    assert base.get("databricks").status == "beta"


def test_metricview_validates_against_docs_schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    emitted = _emit()
    assert emitted, "expected at least one metric view"
    for path, text in emitted.items():
        doc = yaml.safe_load(text)
        errors = sorted(validator.iter_errors(doc), key=lambda e: list(e.path))
        assert not errors, f"{path} failed schema validation:\n" + "\n".join(
            f"  {list(e.path)}: {e.message}" for e in errors
        )


def test_metricview_structure():
    emitted = _emit()
    # COM-001 has a fact table with measures → exactly one metric view, with measures.
    assert len(emitted) >= 1
    doc = yaml.safe_load(next(iter(emitted.values())))
    assert doc["version"] == "1.1"
    assert doc["source"]
    assert doc.get("measures"), "expected measures from the use case"
    for m in doc["measures"]:
        assert m["name"] and m["expr"]


def test_databricks_deterministic():
    assert _emit() == _emit()


# ---- I-10.0 follow-up ("go for 2"): DSL->SQL synthesis coverage ----------- #

CORE_5_BRACKETS = {
    "COM-001": REPO / "core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml",
    "COM-002": REPO / "core/usecases/core/COM-002_Margin_Price_Performance/UseCase_Bracket.yaml",
    "COM-003": REPO / "core/usecases/core/COM-003_Customer_Value/UseCase_Bracket.yaml",
    "FIN-002": REPO / "core/usecases/core/FIN-002_Cost_Performance/UseCase_Bracket.yaml",
    "SCM-002": REPO / "core/usecases/core/SCM-002_Supply_Reliability_OTIF/UseCase_Bracket.yaml",
}

# Known SQL gaps per UC (evidence-based, not derived — a regression guard,
# same style as test_calculation_coverage.py::KNOWN_HITL_KPI_MEASURE_NAMES).
# Two distinct reasons, both honest (never a guessed/wrong SQL expression):
#   (a) one of the 4 ops with no flat Metric-View-expr SQL shape (needs a
#       per-key GROUP BY subquery): pvm_volume_effect, pvm_price_effect,
#       sumx_over_key, avgx_over_key — genuinely narrower than the DAX side's
#       0-HITL-gap result.
#   (b) a sibling-measure reference to a KPI this bracket does NOT itself bind
#       as its own measure (e.g. COM-001's "Gross Margin %" divides by
#       [Gross Margin Amount], but COM-001 never binds KPI-COM-019
#       directly — DAX's `[Name]` resolves model-globally so this is invisible
#       on that side, but Databricks' `MEASURE(...)` is scoped to measures
#       actually defined in the SAME metric view, so a name absent from this
#       bracket's own measure set is a genuine, structural gap here) — or a
#       measure that transitively depends on an (a)/(b) gap (e.g. Mix Effect
#       Amount depends on the (a)-gapped Price/Volume Effect Amount).
KNOWN_SQL_GAP_MEASURE_NAMES = {
    "COM-001": {
        "Price Effect Amount", "Volume Effect Amount", "Gross Margin %", "PVM Bridge Value",
    },
    "COM-002": {
        "Price Effect Amount", "Volume Effect Amount", "Mix Effect Amount",
        "Gross Margin Amount", "Gross Margin %", "Incremental Gross Margin Amount",
        "Incremental Sales Amount", "PVM Bridge Value",
    },
    "COM-003": {"CLV", "Customer Lifetime Revenue Amount"},
    "FIN-002": set(),
    "SCM-002": set(),
}


@pytest.mark.parametrize("uc,bracket", sorted(CORE_5_BRACKETS.items()))
def test_sql_gaps_match_the_documented_scope_out(uc, bracket):
    """`hitl_gaps()` for the 5 core UCs only ever names the documented,
    evidence-based gaps (KNOWN_SQL_GAP_MEASURE_NAMES) — everything else with a
    `technical.calculation` must synthesize real Databricks SQL."""
    model = from_bracket_file(bracket, KPIS)
    gaps = databricks.hitl_gaps(model)
    gapped_names = {gap.split(":", 1)[0].split(".", 1)[-1] for gap in gaps}
    assert gapped_names == KNOWN_SQL_GAP_MEASURE_NAMES[uc], (
        f"[{uc}] SQL gaps drifted from the documented set — either sql_synth/ordering "
        f"newly covers one of these (shrink the allowlist) or a new gap appeared "
        f"(investigate, then extend the allowlist with a documented reason):\n"
        f"  actual   = {sorted(gapped_names)}\n"
        f"  expected = {sorted(KNOWN_SQL_GAP_MEASURE_NAMES[uc])}"
    )


@pytest.mark.parametrize("uc,bracket", sorted(CORE_5_BRACKETS.items()))
def test_covered_measures_never_null(uc, bracket):
    """Every measure NOT in the documented SQL-gap set gets a real SQL `expr` —
    never the `NULL` placeholder — across all 5 core use cases."""
    model = from_bracket_file(bracket, KPIS)
    emitted = base.get("databricks").emit(model)
    seen = set()
    for text in emitted.values():
        doc = yaml.safe_load(text)
        for m in doc.get("measures", []):
            seen.add(m["name"])
            if m["name"] in KNOWN_SQL_GAP_MEASURE_NAMES[uc]:
                assert m["expr"] == "NULL" and m.get("comment", "").startswith("HITL:")
                continue
            assert m["expr"] != "NULL", f"[{uc}] governed measure {m['name']!r} is still NULL"


def test_gap_measures_carry_hitl_comment_never_silent():
    """Every `NULL` placeholder measure carries an adjacent `HITL:`-prefixed
    comment — mirrors the DAX side's `/// HITL:` requirement (never silent)."""
    for bracket in CORE_5_BRACKETS.values():
        model = from_bracket_file(bracket, KPIS)
        emitted = base.get("databricks").emit(model)
        for text in emitted.values():
            doc = yaml.safe_load(text)
            for m in doc.get("measures", []):
                if m["expr"] == "NULL":
                    assert m.get("comment", "").startswith("HITL:"), (
                        f"{m['name']!r}: NULL placeholder with no HITL comment"
                    )
