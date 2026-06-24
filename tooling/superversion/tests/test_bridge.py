"""Tests for the Studio→Superversion bridge (task I-6.2, ADR-0007).

The bridge is the subprocess seam the Studio spawns. Verify the JSON contract:
success shape + exit 0, deterministic, JSON-serializable, bad bracket → ok:false
+ exit 1.
"""
from __future__ import annotations

import json
from pathlib import Path

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
