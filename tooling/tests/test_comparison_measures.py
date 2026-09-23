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
    # COM-003 CLV vs_py: Monatsindex-Shift um zwoelf, kein SAMEPERIODLASTYEAR (dim_date ist nicht
    # als Datumstabelle markiert, ein Monats-Slicer liefe daneben leer).
    py = re.search(r"^\tmeasure 'CLV \(Customer Lifetime Value\) PY' = (.*)$", com, re.M).group(1)
    assert "'dim_date'[MonthNumber] - 12" in py and "SAMEPERIODLASTYEAR" not in py


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


# --- Onboarding-Vorlage und Import (R6.1b, 23.09.2026) ---------------------------------

import csv  # noqa: E402

import pytest  # noqa: E402


def _ausfuellen(pfad, werte):
    zeilen = cm.vorlage_zeilen()
    for z in zeilen:
        z.update(werte.get((z["kpi_id"], z["scenario"]), {}))
    with open(pfad, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cm.VORLAGE_SPALTEN, delimiter=";")
        w.writeheader()
        w.writerows(zeilen)


def test_template_asks_only_for_what_a_report_compares():
    zeilen = cm.vorlage_zeilen()
    schluessel = {(z["kpi_id"], z["scenario"]) for z in zeilen}
    assert ("ops.oee.pct", "target") in schluessel
    assert not any(z["scenario"] == "py" for z in zeilen)          # PY rechnet sich selbst
    assert all(z["wert"] == "" and z["angabe_als"] for z in zeilen)


def test_a_filled_template_loads_one_value_per_month_end(tmp_path):
    import pyarrow.parquet as pq
    vorlage = tmp_path / "ziele.csv"
    _ausfuellen(vorlage, {("ops.oee.pct", "target"): {"gilt_ab": "2025-11", "gilt_bis": "2026-02", "wert": "0,85"}})
    assert cm.lade_vorlage(vorlage, tmp_path / "fact_target") == 4
    t = pq.read_table(tmp_path / "fact_target" / "part-00000.parquet").to_pydict()
    assert t["DateKey"] == [20251130, 20251231, 20260131, 20260228]
    assert set(t["Target Value"]) == {0.85} and set(t["scenario"]) == {"target"}


@pytest.mark.parametrize("werte, meldung", [
    ({("ops.oee.pct", "target"): {"gilt_ab": "2026-01", "gilt_bis": "2026-01", "wert": "85"}}, "Prozentpunkten"),
    ({("ops.oee.pct", "target"): {"gilt_ab": "2026-03", "gilt_bis": "2026-01", "wert": "0.8"}}, "leer oder ungueltig"),
])
def test_a_wrong_template_is_rejected_as_a_whole(tmp_path, werte, meldung):
    vorlage = tmp_path / "ziele.csv"
    _ausfuellen(vorlage, werte)
    with pytest.raises(ValueError, match=meldung):
        cm.lade_vorlage(vorlage, tmp_path / "fact_target")
    assert not (tmp_path / "fact_target").exists()                 # nichts halb geladen


def test_unknown_kpi_and_double_months_are_rejected(tmp_path):
    vorlage = tmp_path / "ziele.csv"
    _ausfuellen(vorlage, {})
    with open(vorlage, "a", encoding="utf-8", newline="") as f:
        f.write("sales.units;target;Sales Units;x;2026-01;2026-01;5\n")
        f.write("ops.oee.pct;target;OEE;x;2026-01;2026-02;0.8\n")
        f.write("ops.oee.pct;target;OEE;x;2026-02;2026-03;0.82\n")
    with pytest.raises(ValueError) as exc:
        cm.lade_vorlage(vorlage, tmp_path / "fact_target")
    assert "wird von keinem Report verglichen" in str(exc.value)
    assert "Monat 20260228 doppelt belegt" in str(exc.value)


# --- Delta-Karte im KPI-Band nur mit Daten (R6.1c, 23.09.2026) --------------------------

def _band(uc, gold):
    loader = cm._loader()
    b = loader.load_use_case_bracket(uc)
    d = loader._target_model_dir(b)
    return cm.band_delta(b, loader.measure_map_for_model(d),
                         set(loader._model_symbols_for_dir(d).measure_names), gold)


def test_a_target_delta_card_appears_only_once_the_customer_delivered_targets(tmp_path):
    assert _band("OPS-001", tmp_path / "leer") is None                 # keine Werte, keine "(Blank)"-Karte
    vorlage = tmp_path / "ziele.csv"
    _ausfuellen(vorlage, {("ops.oee.pct", "target"): {"gilt_ab": "2026-01", "gilt_bis": "2026-01", "wert": "0.85"}})
    cm.lade_vorlage(vorlage, tmp_path / "fact_target")
    assert _band("OPS-001", tmp_path / "fact_target") == (
        "Overall Equipment Effectiveness (OEE) % vs Target", "ops.oee.pct")


def test_a_py_delta_needs_no_customer_data(tmp_path):
    assert _band("COM-003", tmp_path / "leer") == ("CLV (Customer Lifetime Value) vs PY", "crm.clv.amount")
    kpi = json.loads((cm.DIST / "COM-003_Customer_Value.Report/definition/pages/Page_COM003_Overview/"
                      "visuals/KPI_Delta/visual.json").read_text(encoding="utf-8"))
    ys = kpi["visual"]["query"]["queryState"]["Data"]["projections"]
    assert ys[0]["field"]["Measure"]["Property"] == "CLV (Customer Lifetime Value) vs PY"
