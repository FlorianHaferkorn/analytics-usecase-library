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
    # Datumsgrenzen als VAR aus dem letzten ausgewaehlten Tag. Der fruehere Index
    # MAX(Year)*12 + MAX(MonthNumber) nahm Jahr und Monat getrennt: Nov 2025 bis Feb 2026
    # ergab 2026-11.
    assert "VAR _s1 = DATE ( YEAR ( _ende ), MONTH ( _ende ) - 1, 1 ) VAR _e1 = EOMONTH ( _s1, 0 )" in dax
    assert "_s2" not in dax and "_idx" not in dax
    assert "DATEADD" not in dax and "FILTER ( ALL (" not in dax
    assert "VAR _v0 = [Days in Inventory]" in dax  # Periode 0 bleibt beim Monat die Auswahl


def test_volume_guardrail_blocks_below_the_minimum_in_every_period(ergebnisse):
    dax = _neu(ergebnisse, "S-I1.1")
    assert "VAR _g = [Sales Units]" in dax
    assert "_g >= 5000 )" in dax and "_g_1 >= 5000 )" in dax


# --- Wochen-/Tages-Granularitaet (07.10.2026) -----------------------------------------

S_R2_2_VARS = (
    "VAR _ende = MAX ( 'dim_date'[Date] ) "
    "VAR _s0 = _ende - WEEKDAY ( _ende, 2 ) + 1 VAR _e0 = _s0 + 6 "
    "VAR _s1 = _s0 - 7 VAR _e1 = _e0 - 7 "
    "VAR _v0 = CALCULATE ( [On-Time %], REMOVEFILTERS ( 'dim_date' ), "
    "'dim_date'[Date] >= _s0, 'dim_date'[Date] <= _e0 ) "
    "VAR _v0_1 = CALCULATE ( [On-Time %], REMOVEFILTERS ( 'dim_date' ), "
    "'dim_date'[Date] >= _s1, 'dim_date'[Date] <= _e1 ) "
    "VAR _g = CALCULATE ( [Shipments Count], REMOVEFILTERS ( 'dim_date' ), "
    "'dim_date'[Date] >= _s0, 'dim_date'[Date] <= _e0 ) "
    "VAR _g_1 = CALCULATE ( [Shipments Count], REMOVEFILTERS ( 'dim_date' ), "
    "'dim_date'[Date] >= _s1, 'dim_date'[Date] <= _e1 ) RETURN "
)
S_R2_2_L3 = (
    "IF ( ( NOT ISBLANK ( _v0 ) && ( _v0 < 0.9 ) && _g >= 100 ) && "
    "( NOT ISBLANK ( _v0_1 ) && ( _v0_1 < 0.9 ) && _g_1 >= 100 ), "
    "\"🔴 L3 — S-R2.2 — Fulfillment & Transport Stabilisation\" & UNICHAR ( 10 ) & "
    "\"Owner: logistics_manager | \" & FORMAT ( _v0, \"0.0%\" ) & "
    "\" (week of \" & FORMAT ( _s0, \"yyyy-mm-dd\" ) & \")\""
)


def test_s_r2_2_two_consecutive_weeks_golden(ergebnisse):
    """S-R2.2: lane_dc_week, persistence 2 -- die laufende und die Vorwoche, je mit Guardrail."""
    e = ergebnisse[("SupplyChain.SemanticModel", "S-R2.2")]
    assert e.neu.startswith(S_R2_2_VARS)
    assert e.neu[len(S_R2_2_VARS):].startswith(S_R2_2_L3)
    assert "persistence" not in e.nicht_ausgewertet
    assert "lane x dc" in e.nicht_ausgewertet["grain_slot"]


def test_daily_persistence_shifts_by_days(ergebnisse):
    dax = _neu(ergebnisse, "X-R2.2")             # queue_day, min_consecutive_periods 3
    assert "VAR _s0 = _ende VAR _e0 = _ende VAR _s1 = _s0 - 1" in dax and "VAR _s2 = _s0 - 2" in dax
    assert "_v0_2 < 0.63 || _v0_2 > 0.95 )" in dax and "_g_2 >= 150 )" in dax


def test_persistence_is_evaluated_wherever_the_grain_has_a_time_part(ergebnisse):
    offen = sorted(c for (m, c), e in ergebnisse.items() if "persistence" in e.nicht_ausgewertet)
    assert offen == ["C-P4.1"]                    # grain promotion, window in executions
    assert "promotion" in ergebnisse[("Commercial.SemanticModel", "C-P4.1")].nicht_ausgewertet["persistence"]


def test_every_unevaluated_rule_carries_a_reason(ergebnisse):
    for (m, c), e in ergebnisse.items():
        for regel, grund in e.nicht_ausgewertet.items():
            assert isinstance(grund, str) and len(grund) > 10, (m, c, regel)


def _ev(grain, n=2, laenge=3, einheit="periods", **extra):
    return {"grain": grain, "window": {"kind": "rolling", "length": laenge, "unit": einheit},
            "persistence": {"required": True, "min_consecutive_periods": n}, **extra}


def test_grain_not_mappable_in_the_model_is_a_field_not_a_silent_degrade():
    ac = _code(basis="absolute", unit="days")
    ac["trigger"]["evaluation"] = _ev("lane_dc_week")
    dax, offen = atd.dax_fuer(ac, {"k": "K"}, {"k": "days_0"}, spalten={"dim_date.Year"})
    assert "dim_date.Date fehlt" in offen["grain_zeit"] and offen["persistence"] == offen["grain_zeit"]
    assert "_s0" not in dax and "_v0_1" not in dax
    dax, offen = atd.dax_fuer(ac, {"k": "K"}, {"k": "days_0"}, spalten={"dim_date.Date"})
    assert "grain_zeit" not in offen and "persistence" not in offen and "_v0_1" in dax


def test_window_unit_and_length_must_fit_the_persistence():
    ac = _code(basis="absolute", unit="days")
    ac["trigger"]["evaluation"] = _ev("queue_week", einheit="days")
    assert "window.unit" in atd.dax_fuer(ac, {"k": "K"}, {"k": "days_0"})[1]["persistence"]
    ac["trigger"]["evaluation"] = _ev("queue_week", n=3, laenge=2)
    assert "window.length" in atd.dax_fuer(ac, {"k": "K"}, {"k": "days_0"})[1]["persistence"]
    ac["trigger"]["evaluation"] = _ev("queue_week", einheit="weeks")
    assert "persistence" not in atd.dax_fuer(ac, {"k": "K"}, {"k": "days_0"})[1]


def test_weekly_grain_with_monthly_baseline_is_an_error():
    ac = _code(basis="relative", unit="%")
    ac["trigger"]["evaluation"] = _ev("sku_week")
    with pytest.raises(atd.Fehler, match="Monatsdurchschnitt"):
        atd.dax_fuer(ac, {"k": "K"}, {"k": "days_0"})


def test_code_without_persistence_and_time_grain_stays_on_the_selection():
    ac = _code(basis="absolute", unit="days")
    ac["trigger"]["evaluation"] = {"grain": "month", "persistence": {"required": False,
                                                                      "min_consecutive_periods": 1}}
    dax, offen = atd.dax_fuer(ac, {"k": "K"}, {"k": "days_0"})
    assert dax.startswith("VAR _v0 = [K] RETURN IF ( ( NOT ISBLANK ( _v0 ) && ( _v0 > 3 ) ), ")
    assert "CALCULATE" not in dax and "_ende" not in dax and offen == {}


def test_persistence_changes_the_expression_gegenprobe():
    ac = _code(basis="absolute", unit="days")
    ac["trigger"]["evaluation"] = _ev("month", n=3)
    dax, offen = atd.dax_fuer(ac, {"k": "K"}, {"k": "days_0"})
    assert "MONTH ( _ende ) - 1, 1 )" in dax and "MONTH ( _ende ) - 2, 1 )" in dax
    assert "persistence" not in offen
    ac["trigger"]["evaluation"]["persistence"]["required"] = False
    assert "_ende" not in atd.dax_fuer(ac, {"k": "K"}, {"k": "days_0"})[0]


def test_grain_teile():
    assert atd.grain_teile("lane_dc_week") == ("week", ["lane", "dc"])
    assert atd.grain_teile("month") == ("month", [])
    assert atd.grain_teile("promotion") == (None, ["promotion"])
