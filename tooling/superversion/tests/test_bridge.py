"""Tests for the Studio→Superversion bridge (task I-6.2, ADR-0007).

The bridge is the subprocess seam the Studio spawns. Verify the JSON contract:
success shape + exit 0, deterministic, JSON-serializable, bad bracket → ok:false
+ exit 1.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tooling.superversion import bridge

REPO = Path(__file__).resolve().parents[3]
KPIS = REPO / "core/kpi_catalog/kpis"
COM001 = REPO / "core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml"


def test_precore_shape():
    result = bridge.precore(COM001, KPIS)
    assert result["ok"] is True
    assert result["bracket"] == "COM-001_Sales_Performance"
    ids = {e["id"] for e in result["engines"]}
    assert {"gov", "dataarch", "dataeng"} <= ids
    for e in result["engines"]:
        assert e["status"] == "beta"
        assert set(e["counts"]) == {"info", "warn", "error"}
        for f in e["findings"]:
            assert set(f) == {"severity", "code", "detail"}


def test_precore_json_serializable_and_deterministic():
    r1 = bridge.precore(COM001, KPIS)
    r2 = bridge.precore(COM001, KPIS)
    assert json.dumps(r1) == json.dumps(r2)  # pure/deterministic + serializable


def test_cli_precore_emits_valid_json(capsys):
    code = bridge.main(["precore", str(COM001)])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True and payload["engines"]


def test_cli_precore_default_bracket(capsys):
    assert bridge.main(["precore"]) == 0
    assert json.loads(capsys.readouterr().out)["ok"] is True


def test_cli_missing_bracket_is_json_error(capsys):
    code = bridge.main(["precore", str(REPO / "nope.yaml")])
    assert code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False and "not found" in payload["error"]


# --- generate (I-6.3, "Nach dem Core") ---------------------------------------

def test_generate_shape():
    result = bridge.generate(COM001, KPIS, "tmdl")
    assert result["target"] == "tmdl"
    assert "tmdl" in result["targets_available"] and "pbir" in result["targets_available"]
    assert result["artifacts"] and all(set(a) == {"path", "bytes"} for a in result["artifacts"])
    stage_names = [s["name"] for s in result["gate"]["stages"]]
    assert stage_names[:2] == ["source", "golden_thread"]  # gate is first-class
    # ok mirrors the gate (no FAILED stage)
    assert result["ok"] == result["gate"]["ok"]


def test_generate_unknown_target_raises():
    with pytest.raises(ValueError, match="unknown target"):
        bridge.generate(COM001, KPIS, "nope")


def test_cli_generate_emits_valid_json(capsys):
    assert bridge.main(["generate", str(COM001), "--target", "tmdl"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["target"] == "tmdl" and "gate" in payload


def test_cli_generate_unknown_target_is_json_error(capsys):
    assert bridge.main(["generate", str(COM001), "--target", "nope"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False and "unknown target" in payload["error"]
