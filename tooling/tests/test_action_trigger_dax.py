"""Action-Trigger-DAX kommt aus den Action-Codes (R6.4, 23.09.2026).

Bis zu diesem Datum standen die Schwellen als Literale in einem Patch-Skript, und 13 von
39 widersprachen dem YAML. Diese Tests halten fest, dass die ausgelieferten Modelle genau
das tragen, was der Generator aus `core/action_codes/` erzeugt.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tooling.codegen import action_trigger_dax as atd  # noqa: E402


@pytest.fixture
def evidence_source(tmp_path, monkeypatch):
    """Synthetic governed inputs, never customer/tenant data."""
    monkeypatch.setattr(atd, "REPO", tmp_path)
    action_path = tmp_path / "core/action_codes/test/T-1.yaml"
    bracket_path = tmp_path / "core/usecases/test/UseCase_Bracket.yaml"
    action_path.parent.mkdir(parents=True)
    bracket_path.parent.mkdir(parents=True)

    def generate(ac=None, *, proof_bindings=None, extra_measures=(), unit_format="percent_1", **kwargs):
        ac = copy.deepcopy(ac or _code(basis="relative", reference="baseline", unit="%"))
        ac["trigger"].setdefault("type", "Deviation")
        ac.setdefault("status", "draft")
        action_path.write_text(yaml.safe_dump(ac), encoding="utf-8")
        bracket_path.write_text(
            yaml.safe_dump({"id": "TEST-UC", "orchestration": {"action_code_ids": [ac["id"]]}}), encoding="utf-8")
        packet = atd.evidence_fuer(ac, {"k": "K", "plan": "K Plan"}, {"k": unit_format},
                                  action_code_path=action_path, bracket_path=bracket_path,
                                  definiert={"K", "K Plan", *extra_measures}, plan_ref={"k": "plan"},
                                  proof_bindings=proof_bindings, **kwargs)
        return packet, ac, action_path, bracket_path
    return generate


def _proof(role, name):
    return {"measure": name, "semantics": role, "action_code_id": "T-1", "use_case_id": "TEST-UC"}


def test_evidence_preserves_relative_percent_and_source_identity(evidence_source):
    packet, _, action_path, bracket_path = evidence_source()
    assert packet["value_native_per_display_unit"] == .01
    assert packet["threshold_unit"] == "%"
    assert packet["thresholds"]["L1"]["value"] == 1
    assert "_b0 * 1.01" in packet["measures"]["Threshold_L1"]["dax"]
    assert packet["action_status"] == "draft"
    assert packet["scope"] == {"use_case_id": "TEST-UC"}
    for key, path in (("action_code", action_path), ("bracket", bracket_path)):
        assert packet["source"][key]["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
        assert not Path(packet["source"][key]["path"]).is_absolute()


def test_evidence_target_percent_is_not_percentage_points(evidence_source):
    relative, *_ = evidence_source(_code(basis="target", reference="target", unit="%"))
    pp, *_ = evidence_source(_code(basis="target", reference="target", unit="pp"))
    assert "_z0 * 1.01" in relative["measures"]["Threshold_L1"]["dax"]
    assert "_z0 + 0.01" in pp["measures"]["Threshold_L1"]["dax"]


@pytest.mark.parametrize("fmt,unit", [("eur_per_unit_0", "EUR/unit"), ("eur_0", "EUR"),
                                      ("count_0", "count"), ("units_0", "units")])
def test_evidence_preserves_governed_unit_dimensions(evidence_source, fmt, unit):
    packet, *_ = evidence_source(_code(basis="absolute", unit=unit), unit_format=fmt)
    assert packet["value_unit"] == unit
    assert packet["value_native_per_display_unit"] == 1


def test_evidence_missing_proofs_cannot_claim_evaluated(evidence_source):
    ac = _prognose()
    ac["trigger"]["evaluation"]["minimum_data"] = {"min_observations": 3}
    ac["trigger"]["gating_rules"] = ["Category scope and source contract verified"]
    packet, *_ = evidence_source(ac, extra_measures=DEF)
    assert set(packet["unresolved_conditions"]) == {
        "persistence", "gating_rules", "minimum_observations", "evaluation_period_unavailable",
        "forecast_period_unavailable"}
    for field in ("Fired", "Level"):
        assert "IF ( COUNTROWS ( _unresolved ) = 0" in packet["measures"][field]["dax"]
    assert packet["measures"]["ForecastPeriodStart"]["dax"].endswith("RETURN BLANK ()")
    assert "EDATE" not in packet["measures"]["ForecastPeriodStart"]["dax"]
    assert packet["measures"]["PeriodStart"]["dax"].endswith("RETURN BLANK ()")


def test_explicit_proofs_are_dynamic_scoped_and_level_specific(evidence_source):
    ac = _prognose()
    ac["trigger"]["evaluation"]["minimum_data"] = {"min_observations": 3}
    ac["trigger"]["gating_rules"] = ["Proven scope"]
    names = {"observation_count": "N", "gating_met": "Scope OK", "period_start": "Window Start",
             "period_end": "Window End", "forecast_crossing": "Crossing Date",
             **{f"persistence_count_{level}": f"Runs {level}" for level in ("L1", "L2", "L3")}}
    bindings = {role: _proof(role, name) for role, name in names.items()}
    packet, *_ = evidence_source(ac, proof_bindings=bindings, extra_measures={*DEF, *names.values()})
    assert packet["unresolved_conditions"] == []
    dax = packet["measures"]["Level"]["dax"]
    assert '[N] < 3' in dax and '[Scope OK] = 1' in dax
    assert '[Runs L3] >= 2' in dax and '[Runs L1] >= 2' in dax
    assert '[Window Start] > [Window End]' in dax
    # No crossing is a valid result for a cleared or gated-off forecast. A date is
    # mandatory only for the same fully qualified level that feeds Fired/Level.
    crossing_guard = re.search(r'IF \( (.*?) && ISBLANK \( \[Crossing Date\] \), "forecast_period_missing"', dax)
    assert crossing_guard and 'NOT ISBLANK ( IF ( [Scope OK] = 1' in crossing_guard.group(1)
    assert '[Runs L3] >= 2' in crossing_guard.group(1)
    assert packet["measures"]["ForecastPeriodStart"]["dax"].endswith("RETURN [Crossing Date]")
    bindings["gating_met"]["use_case_id"] = "ANOTHER-UC"
    with pytest.raises(atd.Fehler, match="Scope"):
        evidence_source(ac, proof_bindings=bindings, extra_measures={*DEF, *names.values()})


def test_unknown_or_unproven_binding_is_rejected(evidence_source):
    with pytest.raises(atd.Fehler, match="nicht im Modell"):
        evidence_source(proof_bindings={"gating_met": _proof("gating_met", "Invented")})
    with pytest.raises(atd.Fehler, match="unbekannte"):
        evidence_source(proof_bindings={"always_true": {}})


def test_enabled_guardrail_missing_value_cannot_be_coerced_to_false(evidence_source):
    ac = _code(basis="absolute", unit="%")
    ac["trigger"]["evaluation"] = {"minimum_data": {"volume_guardrail": {
        "enabled": True, "metric_kpi_id": "plan", "comparator": "gte", "value": 10}}}
    packet, *_ = evidence_source(ac)
    assert 'ISBLANK ( [K Plan] ), "volume_guardrail_missing"' in packet["measures"]["Fired"]["dax"]
    assert '[K Plan] >= 10' in packet["measures"]["Fired"]["dax"]


def test_manifest_is_portable_and_hashes_exact_generated_expressions(evidence_source):
    packet, *_ = evidence_source()
    manifest = atd.evidence_manifest([packet])
    assert json.loads(json.dumps(manifest)) == manifest
    for role, measure in manifest["action_evidence"][0]["measures"].items():
        assert "dax" not in measure
        expression = packet["measures"][role]["dax"].replace("\r\n", "\n").replace("\r", "\n").strip()
        assert measure["dax_sha256"] == hashlib.sha256(expression.encode("utf-8")).hexdigest()
    tmdl = atd.evidence_tmdl([packet])
    assert "\tmeasure 'Action_T-1_Evidence_Evaluated' =" in tmdl
    assert "\t/// Purpose:" in tmdl and "formatString:" in tmdl
    with pytest.raises(atd.Fehler, match="Doppelte"):
        atd.evidence_manifest([packet, packet])
    with pytest.raises(atd.Fehler):
        atd.evidence_manifest([])


def test_evidence_source_payload_and_bracket_must_match(evidence_source):
    packet, ac, action_path, bracket_path = evidence_source()
    ac["status"] = "approved"
    with pytest.raises(atd.Fehler, match="Payload"):
        atd.evidence_fuer(ac, {"k": "K"}, {"k": "percent_1"}, action_code_path=action_path, bracket_path=bracket_path)
    original = yaml.safe_load(action_path.read_text(encoding="utf-8"))
    bracket_path.write_text(
        yaml.safe_dump({"id": "TEST-UC", "orchestration": {"action_code_ids": []}}), encoding="utf-8")
    with pytest.raises(atd.Fehler, match="explizite"):
        atd.evidence_fuer(original, {"k": "K"}, {"k": "percent_1"},
                         action_code_path=action_path, bracket_path=bracket_path)


def test_cli_evidence_is_opt_in_and_requires_complete_arguments():
    with pytest.raises(SystemExit) as exc:
        atd.main(["--evidence-use-case", "TEST-UC"])
    assert exc.value.code == 2


def test_cli_evidence_roundtrip_leaves_source_model_untouched(evidence_source, monkeypatch, tmp_path):
    packet, *_ = evidence_source()
    model = tmp_path / "dist/Test.SemanticModel"
    model.mkdir(parents=True)
    sentinel = model / "model.tmdl"
    sentinel.write_text("model Test\n", encoding="utf-8")
    monkeypatch.setattr(atd, "DIST", model.parent)
    monkeypatch.setattr(atd, "ACTION_CODES", tmp_path / "core/action_codes")
    monkeypatch.setattr(atd, "_kpi_formate", lambda: {"k": "percent_1"})
    monkeypatch.setattr(atd, "_kpi_plan", lambda: {})
    monkeypatch.setattr(atd, "_loader", lambda: SimpleNamespace(
        measure_map_for_model=lambda _: {"k": "K"},
        _model_symbols_for_dir=lambda _: SimpleNamespace(measure_names={"K", "Start", "End"})))
    bindings = {"T-1": {"period_start": _proof("period_start", "Start"),
                         "period_end": _proof("period_end", "End")}}
    binding_file = tmp_path / "bindings.json"
    binding_file.write_text(json.dumps(bindings), encoding="utf-8")
    out = tmp_path / "consumer-export"
    assert atd.main(["--evidence-use-case", "TEST-UC", "--evidence-model", model.name,
                     "--evidence-out", str(out), "--evidence-bindings", str(binding_file)]) == 0
    manifest = json.loads((out / "action_evidence.manifest.json").read_text(encoding="utf-8"))
    exported = manifest["action_evidence"][0]
    assert exported["source"]["model_name"] == "Test"
    assert exported["source"]["model_item_name"] == model.name
    assert exported["unresolved_conditions"] == []
    tmdl = (out / "action_evidence.tmdl").read_text(encoding="utf-8")
    assert b"\r" not in (out / "action_evidence.tmdl").read_bytes()
    assert b"\r" not in (out / "action_evidence.manifest.json").read_bytes()
    expressions = dict(re.findall(r"^\tmeasure '([^']+)' = (.*)$", tmdl, re.M))
    assert len(expressions) == len(packet["measures"])
    for measure in exported["measures"].values():
        assert hashlib.sha256(expressions[measure["name"]].strip().encode("utf-8")).hexdigest() == measure["dax_sha256"]
    assert list(model.iterdir()) == [sentinel]
    assert sentinel.read_text(encoding="utf-8") == "model Test\n"


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


def _prognose(compare="point", basis="relative"):
    ac = _code(basis=basis, unit="%", reference="baseline") if basis == "relative" else _code(basis=basis, unit="%")
    for L in ("L1", "L2", "L3"):
        ac["trigger"]["levels"][L]["condition"]["comparator"] = "lt"
    ac["trigger"]["type"] = "Forecast"
    ac["trigger"]["forecast"] = {"horizon": {"length": 3, "unit": "months"}, "forecast_measure": "K FC",
                                 "compare": compare,
                                 "band": {"kind": "prediction_interval", "level": 0.8,
                                          "lower_measure": "K FC lo", "upper_measure": "K FC hi"}}
    ac["trigger"]["evaluation"] = {"grain": "month", "persistence": {"required": True, "min_consecutive_periods": 2}}
    return ac


DEF = {"K", "K FC", "K FC lo", "K FC hi"}


def test_forecast_compares_the_forecast_and_keeps_the_actual_as_baseline():
    dax, offen = atd.dax_fuer(_prognose(), {"k": "K"}, {"k": "percent_1"}, definiert=DEF)
    assert "VAR _v0 = [K FC]" in dax
    assert "CALCULATE ( [K]," in dax                  # Basis aus dem Ist-Verlauf
    assert "_v0 < _b0 * 0.99 )" in dax                # L1 -1 % gegen die Basis
    assert "Prognose " in dax
    assert offen == ["persistence"]                   # fruehere Prognosestaende fehlen im Modell


def test_forecast_band_edge_uses_its_own_measure():
    lo, _ = atd.dax_fuer(_prognose("band_lower"), {"k": "K"}, {"k": "percent_1"}, definiert=DEF)
    hi, _ = atd.dax_fuer(_prognose("band_upper"), {"k": "K"}, {"k": "percent_1"}, definiert=DEF)
    assert "VAR _v0 = [K FC lo]" in lo and "VAR _v0 = [K FC hi]" in hi


def test_forecast_measure_missing_in_the_model_is_an_error():
    with pytest.raises(atd.Fehler, match="Prognose-Measure 'K FC lo'"):
        atd.dax_fuer(_prognose("band_lower"), {"k": "K"}, {"k": "percent_1"}, definiert={"K", "K FC"})


def test_deviation_gegenprobe_reads_the_actual():
    ac = _prognose()
    ac["trigger"]["type"] = "Deviation"
    dax, offen = atd.dax_fuer(ac, {"k": "K"}, {"k": "percent_1"}, definiert=DEF)
    assert "VAR _v0 = [K]" in dax and "[K FC]" not in dax and "persistence" not in offen


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


def test_c_m2_4_reads_the_lower_forecast_edge():
    """Erster Forecast-Code (ADR-0028): unterer Rand des 80-%-Intervalls gegen C-M2.3-Stufen."""
    ac = atd.action_codes()["C-M2.4"]
    namen = {"KPI-COM-033": "Private Label Penetration %", "KPI-COM-005": "Net Sales Amount"}
    fc = {"Private Label Penetration %", "Private Label Penetration % Forecast",
          "Private Label Penetration % Forecast Lower", "Private Label Penetration % Forecast Upper"}
    dax, offen = atd.dax_fuer(ac, namen, {"KPI-COM-033": "percent_1"}, definiert=fc)
    assert "VAR _v0 = [Private Label Penetration % Forecast Lower]" in dax
    assert "_v0 < _b0 * 0.98 )" in dax and "_v0 < _b0 * 0.94 )" in dax
    assert "persistence" in offen and "gating_rules" in offen
    with pytest.raises(atd.Fehler, match="Prognose-Measure"):
        atd.dax_fuer(ac, namen, {"KPI-COM-033": "percent_1"}, definiert={"Private Label Penetration %"})


# reference: target (Entscheidung Flo 30.10.2026, ADR-0028 Nachtrag): Abweichung vom Ziel-Measure,
# das der Katalog als plan_kpi_ref der Trigger-KPI fuehrt.
ZIEL = {"k": "K", "p": "K Ziel"}


def test_target_reference_in_percent_is_relative_to_the_target():
    dax, _ = atd.dax_fuer(_code(basis="target", unit="%", reference="target"), ZIEL,
                          {"k": "count_0"}, definiert={"K", "K Ziel"}, plan_ref={"k": "p"})
    assert "VAR _z0 = [K Ziel]" in dax
    assert "NOT ISBLANK ( _z0 ) && _v0 > _z0 * 1.01 )" in dax     # L1 +1 % ueber dem Ziel
    assert "_v0 > _z0 * 1.03 )" in dax


def test_target_reference_in_units_is_additive():
    dax, _ = atd.dax_fuer(_code(basis="absolute", unit="days", reference="target"), ZIEL,
                          {"k": "days_0"}, definiert={"K", "K Ziel"}, plan_ref={"k": "p"})
    assert "_v0 > _z0 + 2 )" in dax


def test_target_without_reference_stays_a_level():
    dax, _ = atd.dax_fuer(_code(basis="target", unit="days"), ZIEL, {"k": "days_0"},
                          plan_ref={"k": "p"})
    assert "_z0" not in dax and "_v0 > 3 )" in dax


def test_target_reference_without_plan_kpi_is_an_error():
    with pytest.raises(atd.Fehler, match="plan_kpi_ref"):
        atd.dax_fuer(_code(basis="target", unit="%", reference="target"), ZIEL, {"k": "count_0"})


def test_target_reference_with_plan_kpi_missing_in_the_model_is_an_error():
    with pytest.raises(atd.Fehler, match="Ziel-KPI 'p'"):
        atd.dax_fuer(_code(basis="target", unit="%", reference="target"), ZIEL, {"k": "count_0"},
                     definiert={"K"}, plan_ref={"k": "p"})


def test_e_s1_1_compares_against_the_target():
    th = atd.action_codes()["E-S1.1"]["trigger"]["levels"]["L1"]["condition"]["threshold"]
    assert th["reference"] == "target" and th["value"] == 5.0
