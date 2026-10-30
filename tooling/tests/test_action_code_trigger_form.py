"""Form des Ausloesers in den Action-Codes (ADR-0028, 30.10.2026).

Zwei Felder, die bis dahin nur Freitext waren: `trigger.type` (jetzt Enum mit `Forecast`) und
`threshold.value_status` (open | assumed | set). Ein Tippfehler im Typ oder eine Schwelle mit
Wert und Status `open` fiel vorher keinem Test auf.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema
import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((REPO / "tooling/generator/schemas/action_code.schema.json").read_text(encoding="utf-8"))
VALIDATOR = jsonschema.Draft7Validator(SCHEMA)
STATUS = {"open", "assumed", "set"}


def _codes() -> dict[str, dict]:
    out = {}
    for f in sorted((REPO / "core/action_codes").glob("*/*.yaml")):
        # dieselbe Auswahl wie Stage 1 (check_schema_validation.ps1): ohne Decision Spines
        if f.name.endswith("_business_case.yaml") or f.parent.name == "decision_spines" \
                or f.name == "impactful_15.yaml":
            continue
        d = yaml.safe_load(f.read_text(encoding="utf-8"))
        if isinstance(d, dict) and d.get("id"):
            out[d["id"]] = d
    return out


CODES = _codes()
FORECAST = {"horizon": {"length": 3, "unit": "months"}, "forecast_measure": "X Forecast", "compare": "point"}
BAND = {"kind": "prediction_interval", "level": 0.8, "lower_measure": "X FC lo", "upper_measure": "X FC hi"}


def _fehler(d: dict) -> int:
    return len(list(VALIDATOR.iter_errors(d)))


def test_every_action_code_passes_the_schema():
    assert len(CODES) >= 60
    bad = {c: [e.message for e in VALIDATOR.iter_errors(d)] for c, d in CODES.items() if _fehler(d)}
    assert bad == {}


@pytest.mark.parametrize("name,typ,block,erwartet", [
    ("Forecast mit Block", "Forecast", FORECAST, 0),
    ("Forecast ohne Block", "Forecast", None, 1),
    ("Block ohne Forecast", "Deviation", FORECAST, 1),
    ("Bandrand ohne Band", "Forecast", {**FORECAST, "compare": "band_lower"}, 1),
    ("Bandrand mit Band", "Forecast", {**FORECAST, "compare": "band_lower", "band": BAND}, 0),
    ("Band ohne Rand-Measure", "Forecast", {**FORECAST, "compare": "band_lower",
                                            "band": {"kind": "prediction_interval", "level": 0.8}}, 2),
    ("Tippfehler im Typ", "Forcast", FORECAST, 2),
])
def test_forecast_needs_its_block_and_only_forecast_may_carry_it(name, typ, block, erwartet):
    d = copy.deepcopy(CODES["C-M2.3"])
    d["trigger"]["type"] = typ
    if block is not None:
        d["trigger"]["forecast"] = block
    assert _fehler(d) == erwartet, name


def _schwellen():
    for code, d in CODES.items():
        for lvl, l in ((d.get("trigger") or {}).get("levels") or {}).items():
            th = ((l or {}).get("condition") or {}).get("threshold")
            if isinstance(th, dict) and "value_status" in th:
                yield code, lvl, th


def test_value_status_matches_the_value():
    gesehen = list(_schwellen())
    assert len(gesehen) >= 9                       # C-E1.1, C-M2.3, E-S1.1 je L1-L3
    falsch = [(c, L, th) for c, L, th in gesehen
              if th["value_status"] not in STATUS
              or (th["value_status"] == "open") != (th.get("value") is None)]
    assert falsch == []


def test_assumed_thresholds_say_so_in_the_file():
    """Eine angenommene Schwelle steht als ANNAHME im Code, nicht nur im Statusfeld."""
    annahme = {c for c, _, th in _schwellen() if th["value_status"] == "assumed"}
    assert "C-M2.3" in annahme
    for c in sorted(annahme):
        f = next((REPO / "core/action_codes").glob(f"*/{c}.yaml"))
        assert "ANNAHME, ungeprueft" in f.read_text(encoding="utf-8"), c
