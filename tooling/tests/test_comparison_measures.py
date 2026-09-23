"""Deklarierte Vergleiche werden gezeichnet (R6.1, 23.09.2026).

Die Brackets deklarierten `comparison: vs_target | vs_plan | vs_py`, der Generator las das
Feld nie. `tooling/codegen/comparison_measures.py` erzeugt die Referenz-Measures und die
Zieltabelle; diese Tests halten die ausgelieferten Modelle daran fest.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tooling.codegen import comparison_measures as cm  # noqa: E402


def test_models_carry_exactly_the_generated_comparison_layer():
    drift, luecken = cm.pruefe()
    assert luecken == []
    assert drift == [], "python -m tooling.codegen.comparison_measures --write"


def test_every_model_has_the_target_table_and_its_date_relationship():
    for m in sorted(cm.DIST.glob("*.SemanticModel")):
        d = m / "definition"
        assert (d / "tables" / "fact_target.tmdl").exists(), m.name
        assert "fromColumn: fact_target.DateKey" in (d / "relationships" / "dim_date_fact_target.tmdl").read_text(encoding="utf-8")
        assert "ref table fact_target\n" in (d / "model.tmdl").read_text(encoding="utf-8")


def test_generated_names_are_exactly_the_exempted_ones():
    """Die Drift-Checks nehmen diese Measures per Namensmuster aus. Passt ein erzeugter Name nicht
    ins Muster, faellt er dort als undokumentiert auf; passt ein governter hinein, wird er versteckt."""
    for m in sorted(cm.DIST.glob("*.SemanticModel")):
        text = (m / "definition" / "tables" / "_Measures.tmdl").read_text(encoding="utf-8")
        for block in re.split(r"\n(?=\t(?:///|measure ))", text):
            name = re.search(r"^\tmeasure '([^']+)'", block, re.M)
            if not name:
                continue
            erzeugt = f'annotation {cm.MARKE} = "comparison_measures"' in block
            assert bool(cm.ABGELEITET.match(name.group(1))) == erzeugt, (m.name, name.group(1))


def test_target_reads_the_customer_table_and_py_uses_time_intelligence():
    ops = (cm.DIST / "Operations.SemanticModel/definition/tables/_Measures.tmdl").read_text(encoding="utf-8")
    assert re.search(r"measure 'Overall Equipment Effectiveness \(OEE\) % Target' = CALCULATE \( AVERAGE \( "
                     r"fact_target\[Target Value\] \), fact_target\[kpi_id\] = \"ops.oee.pct\"", ops)
    com = (cm.DIST / "Commercial.SemanticModel/definition/tables/_Measures.tmdl").read_text(encoding="utf-8")
    assert "SAMEPERIODLASTYEAR ( 'dim_date'[Date] )" in com          # COM-003 CLV vs_py


def test_a_governed_plan_wins_over_the_target_table():
    """COM-001 fuehrt `sales.net_sales.plan.amount` -- dafuer entsteht kein zweiter Plan."""
    loader = cm._loader()
    b = loader.load_use_case_bracket("COM-001")
    d = loader._target_model_dir(b)
    refs = cm.referenzen_fuer_bracket(b, loader.measure_map_for_model(d),
                                      set(loader._model_symbols_for_dir(d).measure_names))
    assert refs.get("sales.net_sales.amount|vs_plan") == "Plan Sales Amount"


def test_the_trend_draws_its_declared_target():
    """OPS-001 Main_1 fragt "Is OEE on target, and is the gap closing or widening?"."""
    v = json.loads((cm.DIST / "OPS-001_Operations_Performance.Report/definition/pages/Page_OPS001_Overview/"
                    "visuals/Main_1/visual.json").read_text(encoding="utf-8"))
    ys = [p["field"]["Measure"]["Property"] for p in v["visual"]["query"]["queryState"]["Y"]["projections"]]
    assert ys == ["Overall Equipment Effectiveness (OEE) %", "Overall Equipment Effectiveness (OEE) % Target"]


def test_target_values_are_empty_in_the_demo_on_purpose():
    import pyarrow.parquet as pq
    files = list((REPO_ROOT / "showcases/aurora_group/data/gold/facts/fact_target").glob("*.parquet"))
    assert files and sum(pq.read_metadata(str(f)).num_rows for f in files) == 0
    assert pq.read_schema(str(files[0])).names == ["kpi_id", "scenario", "DateKey", "Target Value"]
