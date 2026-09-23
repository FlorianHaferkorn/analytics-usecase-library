"""Action-Trigger-DAX kommt aus den Action-Codes (R6.4, 23.09.2026).

Bis zu diesem Datum standen die Schwellen als Literale in einem Patch-Skript, und 13 von
39 widersprachen dem YAML. Diese Tests halten fest, dass die ausgelieferten Modelle genau
das tragen, was der Generator aus `core/action_codes/` erzeugt.
"""
from __future__ import annotations

import copy
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tooling.codegen import action_trigger_dax as atd  # noqa: E402


@pytest.fixture(scope="module")
def ergebnisse():
    return {(e.modell, e.code): e for e in atd.pruefe()}


def _neu(ergebnisse, code):
    treffer = [e for (m, c), e in ergebnisse.items() if c == code and e.neu]
    assert treffer, code
    return treffer[0].neu


def test_shipped_models_carry_exactly_the_generated_expression(ergebnisse):
    fehler = [f"{m} {c}: {e.fehler}" for (m, c), e in ergebnisse.items() if e.fehler]
    drift = [f"{m} {c}" for (m, c), e in ergebnisse.items() if e.neu is not None and e.neu != e.alt]
    assert fehler == []
    assert drift == [], "python -m tooling.codegen.action_trigger_dax --write"


def test_every_exception_names_a_reason_and_a_date():
    for key, (grund, datum) in atd.NICHT_ABLEITBAR.items():
        assert len(grund) > 20, key
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", datum), key


def test_o_o1_4_triggers_on_throughput_as_governed_not_on_oee(ergebnisse):
    dax = _neu(ergebnisse, "O-O1.4")
    assert "[Throughput Units]" in dax and "[OEE %]" not in dax
    assert "Throughput Constraint Resolution" in dax


def test_relative_threshold_is_measured_against_the_rolling_baseline(ergebnisse):
    dax = _neu(ergebnisse, "S-I1.1")               # DIO +10 / +25 / +40 %, P90D
    assert "_v0 > _b0 * 1.1 )" in dax and "_v0 > _b0 * 1.4 )" in dax
    assert "'dim_date'[Date] >= _ref - 90" in dax
    assert "> 55" not in dax                       # die frueher geratene Basis


def test_absolute_deviation_is_added_to_the_baseline(ergebnisse):
    dax = _neu(ergebnisse, "F-C1.2")               # DSO +3 / +7 / +12 Tage
    assert "_v0 > _b0 + 3 )" in dax and "_v0 > _b0 + 12 )" in dax
    assert "> 33" not in dax


def test_percent_thresholds_become_fractions_for_the_measure(ergebnisse):
    assert "_v0 < 0.97 )" in _neu(ergebnisse, "C-C3.1")       # YAML 97.0 %
    assert "_v0 > 0.003 )" in _neu(ergebnisse, "O-Q3.5")      # YAML 0.3 %, Beschwerdequote


def test_owner_text_and_annotation_come_from_the_same_field():
    tmdl = (atd.DIST / "Operations.SemanticModel/definition/tables/_Measures.tmdl").read_text(encoding="utf-8")
    block = tmdl.split("measure 'Action_O-O1.4_Text'", 1)[1].split("\n\n", 1)[0]
    assert "Owner: operations_director" in block
    assert 'ActionReady_ResponsibleRole = "operations_director"' in block


# --- Konvention in den Action-Codes: `unit: %` heisst Prozent (92.0 = 92 %) -----------

# Quoten, deren Schwellen legitim unter einem Prozent liegen. Grund ist Pflicht.
UNTER_EINEM_PROZENT = {"O-Q3.5": "Beschwerdequote, Schwellen 0,3 / 0,6 / 1,0 %"}


def test_percent_thresholds_are_written_in_percent_not_as_fractions():
    formate = atd._kpi_formate()
    verdaechtig = []
    for code, ac in atd.action_codes().items():
        levels = ((ac.get("trigger") or {}).get("levels")) or {}
        werte = []
        for L in ("L1", "L2", "L3"):
            cond = (levels.get(L) or {}).get("condition") or {}
            th = cond.get("threshold") or {}
            if (str(th.get("unit")) in atd.PROZENT and th.get("value") is not None
                    and (formate.get(cond.get("metric_kpi_id"), "").startswith("percent")
                         or th.get("basis") == "relative")):
                werte.append(float(th["value"]))
        if werte and any(werte) and all(abs(v) <= 1 for v in werte) and code not in UNTER_EINEM_PROZENT:
            verdaechtig.append((code, werte))
    assert verdaechtig == []


# --- Gegenproben am synthetischen Code ------------------------------------------------

def _code(**schwelle):
    lvl = lambda v: {"severity": "x", "condition": {"metric_kpi_id": "k", "comparator": "gt",
                                                     "threshold": {**schwelle, "value": v}}}
    return {"id": "T-1", "name": "Test", "owner_role": "r",
            "trigger": {"levels": {"L1": lvl(1), "L2": lvl(2), "L3": lvl(3)}},
            "impact_valuation": {"success_window": {"success_criteria": {"baseline_window": "P30D"}}}}


def test_a_changed_threshold_changes_the_expression():
    a, _ = atd.dax_fuer(_code(basis="absolute", unit="days"), {"k": "K"}, {"k": "days_0"})
    b_ac = _code(basis="absolute", unit="days")
    b_ac["trigger"]["levels"]["L3"]["condition"]["threshold"]["value"] = 9
    b, _ = atd.dax_fuer(b_ac, {"k": "K"}, {"k": "days_0"})
    assert a != b and "_v0 > 9 )" in b


def test_a_kpi_missing_in_the_model_is_an_error_not_a_guess():
    with pytest.raises(atd.Fehler, match="kein Measure"):
        atd.dax_fuer(_code(basis="absolute", unit="days"), {"k": "K"}, {"k": "days_0"}, definiert={"Anderes"})


def test_relative_without_baseline_window_is_an_error():
    ac = _code(basis="relative", unit="%")
    ac["impact_valuation"] = {}
    with pytest.raises(atd.Fehler, match="baseline_window"):
        atd.dax_fuer(ac, {"k": "K"}, {"k": "days_0"})


def test_band_and_abs_comparators():
    ac = copy.deepcopy(_code(basis="absolute", unit="%"))
    for L in ("L1", "L2", "L3"):
        ac["trigger"]["levels"][L]["condition"]["comparator"] = "abs_gt"
    dax, _ = atd.dax_fuer(ac, {"k": "K"}, {"k": "percent_1"})
    assert "ABS ( _v0 ) > 0.03 )" in dax


# --- Persistenz und Mengen-Guardrail (R6.4b, 23.09.2026) ------------------------------

def test_monthly_persistence_requires_the_prior_month_too(ergebnisse):
    dax = _neu(ergebnisse, "S-I1.1")             # sku_location_month, min_consecutive_periods 2
    assert "VAR _idx = MAX ( 'dim_date'[Year] ) * 12 + MAX ( 'dim_date'[MonthNumber] )" in dax
    assert "= _idx - 1 ) )" in dax and "= _idx - 2" not in dax
    assert "DATEADD" not in dax                   # neben einem Monats-Slicer leer, siehe Modul


def test_volume_guardrail_blocks_below_the_minimum(ergebnisse):
    assert "[Sales Units] >= 5000" in _neu(ergebnisse, "S-I1.1")


def test_weekly_persistence_is_reported_not_faked(ergebnisse):
    e = next(e for (m, c), e in ergebnisse.items() if c == "S-I1.3" and e.neu)   # sku_location_week
    assert "_idx" not in e.neu and "persistence" in e.nicht_ausgewertet


def test_persistence_changes_the_expression_gegenprobe():
    ac = _code(basis="absolute", unit="days")
    ac["trigger"]["evaluation"] = {"grain": "month", "persistence": {"required": True, "min_consecutive_periods": 3}}
    dax, offen = atd.dax_fuer(ac, {"k": "K"}, {"k": "days_0"})
    assert "= _idx - 1 )" in dax and "= _idx - 2 )" in dax and "persistence" not in offen
    ac["trigger"]["evaluation"]["persistence"]["required"] = False
    assert "_idx" not in atd.dax_fuer(ac, {"k": "K"}, {"k": "days_0"})[0]
