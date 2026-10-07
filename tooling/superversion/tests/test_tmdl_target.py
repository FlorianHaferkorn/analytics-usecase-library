"""Tests for the TMDL semantic-model target adapter (task I-3.2).

Gates per the DoD: TMDL hard-rules (the real `.claude/hooks/validate_tmdl_style.sh`
runs green on emitted files) + a parse round-trip through Meridian's vendored
tmdl_parser + determinism.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from tooling.superversion import _meridian_vendor
from tooling.superversion.canonical_contract import (
    CanonicalModel,
    Measure,
    ReportModel,
    SemanticModel,
    Table,
)
from tooling.superversion.e2e_smoke import resolve_bash
from tooling.superversion.from_aluca import from_bracket_file
from tooling.superversion.targets import base
from tooling.superversion.targets import tmdl  # noqa: F401 — registers the "tmdl" adapter

REPO = Path(__file__).resolve().parents[3]
KPIS = REPO / "core/kpi_catalog/kpis"
COM001 = REPO / "core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml"
HOOK = REPO / ".claude/hooks/validate_tmdl_style.sh"


@pytest.fixture
def model() -> CanonicalModel:
    return from_bracket_file(COM001, KPIS)


def test_tmdl_adapter_registered():
    assert "tmdl" in base.available()
    assert base.get("tmdl").fmt == "tmdl"


def test_emit_one_file_per_table(model):
    out = tmdl.emit(model)
    tables = {t.name for t in model.semantic.tables}
    expected = {f"{model.semantic.name}.SemanticModel/definition/tables/{t}.tmdl" for t in tables}
    assert set(tmdl.table_files(out)) == expected
    assert all(c.endswith("\n") for c in out.values())


def test_emit_carries_the_semantic_model_item_frame(model):
    """Since 07.10.2026: the folder is a semantic model Desktop can open — the
    Microsoft-required `definition.pbism` plus `.platform`, `database.tmdl`, `model.tmdl`
    (Learn: "Power BI Desktop project semantic model folder")."""
    out = tmdl.emit(model)
    item = f"{model.semantic.name}.SemanticModel"
    for rel in ("definition.pbism", ".platform", "definition/database.tmdl",
                "definition/model.tmdl"):
        assert f"{item}/{rel}" in out, rel
    assert json.loads(out[f"{item}/definition.pbism"])["version"] == "4.2"
    assert json.loads(out[f"{item}/.platform"])["metadata"]["type"] == "SemanticModel"
    assert "compatibilityLevel: 1702" in out[f"{item}/definition/database.tmdl"]
    model_tmdl = out[f"{item}/definition/model.tmdl"]
    assert "defaultPowerBIDataSourceVersion: PowerBI_V3" in model_tmdl
    for t in model.semantic.tables:
        assert f"ref table {tmdl.quote_name(t.name)}" in model_tmdl


def test_every_table_has_a_partition_and_a_column(model):
    """TOM needs a partition per import table; a measure-only table gets the hidden
    `Column1` the legacy `_Measures` tables carry."""
    for rel, content in tmdl.table_files(tmdl.emit(model)).items():
        assert "\tpartition " in content and "\t\tmode: import" in content, rel
        assert "\tcolumn " in content, rel


def test_names_with_spaces_are_quoted():
    from tooling.superversion.canonical_contract import Column, Relationship
    t = Table(name="fact_x", columns=[Column(name="OTIF Flag", data_type="boolean"),
                                       Column(name="DateKey", data_type="int64")])
    d = Table(name="dim_date", columns=[Column(name="DateKey", data_type="int64")])
    sm = CanonicalModel(semantic=SemanticModel(
        name="S-1", tables=[t, d],
        relationships=[Relationship("fact_x", "DateKey", "dim_date", "DateKey")]),
        report=ReportModel(name="S-1"))
    out = tmdl.emit(sm)
    assert "\tcolumn 'OTIF Flag'" in out["S-1.SemanticModel/definition/tables/fact_x.tmdl"]
    assert '#"OTIF Flag" = logical' in out["S-1.SemanticModel/definition/tables/fact_x.tmdl"]
    assert out["S-1.SemanticModel/definition/database.tmdl"].startswith("database 'S-1'\n")
    rel = out["S-1.SemanticModel/definition/relationships.tmdl"]
    assert "\tfromColumn: fact_x.DateKey\n\ttoColumn: dim_date.DateKey" in rel


def test_emit_is_deterministic(model):
    assert tmdl.emit(model) == tmdl.emit(model)


def test_tmdl_hardrules_no_spaces_no_assign_no_description(model):
    for content in tmdl.table_files(tmdl.emit(model)).values():
        for i, line in enumerate(content.splitlines(), 1):
            assert not line.startswith("  "), f"leading spaces at line {i}: {line!r}"
            assert ":=" not in line, f"forbidden ':=' at line {i}"
            assert not line.lstrip().startswith("description:"), f"'description:' at line {i}"
        # measures use the canonical /// doc form + '=' assignment
        assert "measure " in content
        assert "\tmeasure " in content  # tab-indented


def test_neutral_core_placeholder_dax():
    """Source stays dialect-neutral (I1): with no derivable formula, the emitter
    writes a deterministic HITL BLANK() placeholder, never invented DAX — every
    placeholder carries a diagnosable `/// HITL:` reason, generic or specific.

    Synthetic model (not COM-001): the DSL grammar extension (I-10.0 follow-up)
    closed the last 13 documented HITL gaps referenced by the 5 MVP use cases,
    so COM-001 itself now has 0 gaps to observe this on — this test exercises
    the emitter's HITL/BLANK() contract directly instead."""
    hitl_measure = Measure(
        name="Unresolvable Measure",
        expression="",
        expressions={"hitl_reason": "HITL: no derivable formula — beyond the governed grammar."},
    )
    model = CanonicalModel(
        semantic=SemanticModel(name="Synthetic", tables=[Table(name="fact_test", measures=[hitl_measure])]),
        report=ReportModel(name="Synthetic"),
    )
    blob = "\n".join(tmdl.emit(model).values())
    assert "= BLANK()" in blob
    assert "/// HITL:" in blob


def test_real_tmdl_hook_passes_on_emitted_files(model, tmp_path):
    """The actual PostToolUse hook (validate_tmdl_style.sh) exits 0 on emitted TMDL."""
    if not HOOK.exists():
        pytest.skip("TMDL hook not present")
    bash = resolve_bash()
    if bash is None:
        pytest.skip("bash not on PATH or at the Git-for-Windows default install path (I-10.1)")
    for rel, content in tmdl.emit(model).items():
        f = tmp_path / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content, encoding="utf-8")
        payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": str(f)}})
        res = subprocess.run([bash, str(HOOK)], input=payload, capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert res.returncode == 0, f"hook blocked {rel}: {res.stdout}\n{res.stderr}"


def test_parse_roundtrip_with_vendored_parser(model):
    """Emitted TMDL parses back through Meridian's real tmdl_parser: table name +
    measure names/folders survive the round trip."""
    try:
        parser = _meridian_vendor._load_module(
            "_mer_tmdl_roundtrip",
            _meridian_vendor.VENDOR_DIR / "core/pbi_engine/parsers/tmdl_parser.py",
        )
    except Exception:
        pytest.skip("vendored tmdl_parser not loadable")

    by_table = {t.name: t for t in model.semantic.tables}
    for rel, content in tmdl.table_files(tmdl.emit(model)).items():
        table_name = rel.rsplit("/", 1)[-1][: -len(".tmdl")]
        parsed = parser._parse_table(content, table_name)
        assert parsed is not None and parsed.name == table_name
        src = by_table[table_name]
        assert {m.name for m in parsed.measures} == {m.name for m in src.measures}
        for pm in parsed.measures:
            sm = next(m for m in src.measures if m.name == pm.name)
            assert pm.display_folder == sm.display_folder
            assert pm.expression  # round-tripped DAX (real or placeholder) is non-empty


def test_synthetic_table_with_columns_renders_summarizeby():
    """A table WITH columns emits summarizeBy (hard-rule) and round-trips."""
    from tooling.superversion.canonical_contract import Column
    t = Table(name="fact_x", columns=[Column(name="Amount", data_type="decimal", summarize_by="sum")],
              measures=[Measure(name="M", display_folder="F", format_string="0.0%")])
    sm = CanonicalModel(semantic=SemanticModel(name="S", tables=[t]), report=ReportModel(name="S"))
    content = next(iter(tmdl.table_files(tmdl.emit(sm)).values()))
    assert "\t\tsummarizeBy: sum" in content
    assert "\t\tformatString: \"0.0%\"" in content
    assert "\tcolumn Amount" in content
