"""I-7.1 — OSI target emits a valid OSI Core document from the canonical model.

DoD: OSI-jsonschema-validate grün. Validates the emitted document against the
official upstream OSI JSON Schema vendored at `targets/schemas/osi-schema.json`.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tooling.superversion.from_aluca import from_bracket_file
from tooling.superversion.targets import base
from tooling.superversion.targets import osi  # noqa: F401 — registers "osi"

REPO = Path(__file__).resolve().parents[3]
KPIS = REPO / "core/kpi_catalog/kpis"
COM001 = REPO / "core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml"
SCHEMA = Path(__file__).resolve().parents[1] / "targets" / "schemas" / "osi-schema.json"


def _emit_doc():
    model = from_bracket_file(COM001, KPIS)
    emitted = base.get("osi").emit(model)
    assert len(emitted) == 1
    return json.loads(next(iter(emitted.values())))


def test_osi_registered():
    assert "osi" in base.available()
    assert base.get("osi").status == "live"


def test_osi_validates_against_official_schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    doc = _emit_doc()
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(doc), key=lambda e: e.path)
    assert not errors, "OSI doc failed schema validation:\n" + "\n".join(
        f"  {list(e.path)}: {e.message}" for e in errors
    )


def test_osi_structure():
    doc = _emit_doc()
    assert doc["version"] == "0.2.0.dev0"
    assert isinstance(doc["semantic_model"], list) and len(doc["semantic_model"]) == 1
    sm = doc["semantic_model"][0]
    assert sm["name"] and len(sm["datasets"]) >= 1
    # COM-001 has measures → at least one metric, each with a dialect expression.
    assert sm.get("metrics"), "expected metrics from the use case's measures"
    for m in sm["metrics"]:
        assert m["expression"]["dialects"][0]["dialect"] in {
            "ANSI_SQL", "SNOWFLAKE", "MDX", "TABLEAU", "DATABRICKS", "MAQL",
        }
    for ds in sm["datasets"]:
        assert ds["name"] and ds["source"]


def test_osi_deterministic():
    assert base.get("osi").emit(from_bracket_file(COM001, KPIS)) == \
        base.get("osi").emit(from_bracket_file(COM001, KPIS))


# ---- I-10.0 follow-up ("go for 2"): multi-dialect (MDX + DATABRICKS) ------ #

CORE_5_BRACKETS = {
    "COM-001": REPO / "core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml",
    "COM-002": REPO / "core/usecases/core/COM-002_Margin_Price_Performance/UseCase_Bracket.yaml",
    "COM-003": REPO / "core/usecases/core/COM-003_Customer_Value/UseCase_Bracket.yaml",
    "FIN-002": REPO / "core/usecases/core/FIN-002_Cost_Performance/UseCase_Bracket.yaml",
    "SCM-002": REPO / "core/usecases/core/SCM-002_Supply_Reliability_OTIF/UseCase_Bracket.yaml",
}

# Same 4 no-flat-SQL-shape ops as targets/databricks.py's KNOWN_SQL_GAP_MEASURE_NAMES —
# these get an MDX-only dialects list (DATABRICKS entry absent, not a placeholder).
NO_DATABRICKS_DIALECT_MEASURE_NAMES = {
    "Customer Lifetime Revenue Amount", "CLV", "Volume Effect Amount", "Price Effect Amount",
}


def _metrics_for(bracket) -> list[dict]:
    model = from_bracket_file(bracket, KPIS)
    doc = json.loads(next(iter(base.get("osi").emit(model).values())))
    return doc["semantic_model"][0].get("metrics", [])


@pytest.mark.parametrize("uc,bracket", sorted(CORE_5_BRACKETS.items()))
def test_every_governed_metric_has_an_mdx_dialect(uc, bracket):
    """dax_synth covers all 16 ops — every metric backed by a resolvable
    `technical.calculation` must carry an MDX dialect entry (never just the
    placeholder-name fallback) across all 5 core use cases."""
    for metric in _metrics_for(bracket):
        dialects = {d["dialect"] for d in metric["expression"]["dialects"]}
        if metric["name"] in NO_DATABRICKS_DIALECT_MEASURE_NAMES:
            continue  # covered by test_no_databricks_dialect_for_documented_sql_gaps
        assert "MDX" in dialects, f"[{uc}] {metric['name']!r} has no MDX dialect entry"


@pytest.mark.parametrize("uc,bracket", sorted(CORE_5_BRACKETS.items()))
def test_databricks_dialect_present_except_documented_sql_gaps(uc, bracket):
    """Every metric gets a DATABRICKS dialect entry too, EXCEPT the 4 ops with
    no flat Metric-View-expr SQL shape — MDX-only for those, never a guessed
    DATABRICKS expression."""
    for metric in _metrics_for(bracket):
        dialects = {d["dialect"] for d in metric["expression"]["dialects"]}
        if metric["name"] in NO_DATABRICKS_DIALECT_MEASURE_NAMES:
            assert "DATABRICKS" not in dialects, (
                f"[{uc}] {metric['name']!r} unexpectedly has a DATABRICKS dialect "
                "— sql_synth should have raised SynthesisError for this op"
            )
        else:
            assert "DATABRICKS" in dialects, f"[{uc}] {metric['name']!r} missing expected DATABRICKS dialect"


def test_osi_hitl_gaps_are_never_silent():
    """Every metric `hitl_gaps()` flags carries a `HITL:`-prefixed description —
    OSI's schema requires `expression` be present, so the reason travels via
    `description` instead of an empty/placeholder value (never silent)."""
    for bracket in CORE_5_BRACKETS.values():
        model = from_bracket_file(bracket, KPIS)
        gaps = osi.hitl_gaps(model)
        if not gaps:
            continue
        metrics_by_name = {m["name"]: m for m in _metrics_for(bracket)}
        for gap in gaps:
            measure_name = gap.split(":", 1)[0].split(".", 1)[-1]
            assert metrics_by_name[measure_name]["description"].startswith("HITL:")
