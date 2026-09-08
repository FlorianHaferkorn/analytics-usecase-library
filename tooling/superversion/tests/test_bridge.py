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


def test_resolve_bracket_by_governed_id():
    assert bridge.resolve_bracket(Path("COM-001")) == COM001.resolve()


def test_cli_resolve_emits_canonical_bracket(capsys):
    assert bridge.main(["resolve", "COM-001"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"ok": True, "bracket": "COM-001_Sales_Performance"}


def test_cli_missing_bracket_is_json_error(capsys):
    code = bridge.main(["precore", str(REPO / "nope.yaml")])
    assert code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False and "not found" in payload["error"]


# --- ping (I-6.5 readiness probe) --------------------------------------------

def test_cli_ping_reports_registries(capsys):
    assert bridge.main(["ping"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert "tmdl" in payload["targets_available"]
    assert "gov" in payload["engines_available"]


def test_ping_advertises_all_four_real_targets(capsys):
    """I-10.3: bridge.py previously only imported e2e_smoke (tmdl+pbir), so
    Studio's target picker (GateReportPanel) could never offer osi/databricks
    even though both targets are real and registered elsewhere (I-7.2/I-7.3).
    Importing them here must not be a silent, easy-to-miss registration gap."""
    assert bridge.main(["ping"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert set(payload["targets_available"]) == {"tmdl", "pbir", "osi", "databricks"}


@pytest.mark.parametrize("target", ["osi", "databricks"])
def test_generate_supports_osi_and_databricks_targets(target):
    """Same I-10.3 gap: `generate` must actually work for both, not just be
    listed in `targets_available` without being reachable."""
    result = bridge.generate(COM001, KPIS, target)
    assert result["target"] == target
    assert result["artifacts"]


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


def test_generate_can_include_content_for_studio_download():
    result = bridge.generate(COM001, KPIS, "pbir", include_content=True)
    assert result["artifacts"]
    assert all(set(a) == {"path", "bytes", "content"} for a in result["artifacts"])
    assert all(a["bytes"] == len(a["content"].encode("utf-8")) for a in result["artifacts"])


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


# --- attribute (Studio-Approval-Verdrahtung, ADR-0009 §5) --------------------

def test_attribute_resolves_outcome_kpis_from_governed_action_code():
    # C-M2.1's outcome_kpis are ['sales.price.realization_pct', 'margin.gm.pct'];
    # COM-001's reference data only has margin.gm.pct — the other stays honestly
    # uncomputed rather than being silently dropped or faked as 0.
    result = bridge.attribute("COM-001", "C-M2.1", {"margin.gm.pct": 0.45})
    assert result["ok"] is True
    assert result["outcome_kpis"] == ["sales.price.realization_pct", "margin.gm.pct"]
    by_kpi = {r["kpi_id"]: r for r in result["attribution"]}
    assert by_kpi["sales.price.realization_pct"]["status"] == "uncomputed"
    assert by_kpi["margin.gm.pct"]["status"] == "computed"
    assert by_kpi["margin.gm.pct"]["delta"] is not None


def test_attribute_derives_refinement_proposals_as_pending_review():
    result = bridge.attribute("COM-001", "C-M2.1", {"margin.gm.pct": 0.45})
    assert result["refinements"], "a material delta should derive a proposal"
    for p in result["refinements"]:
        assert p["status"] == "pending_review"  # ADR-0009: never auto-applied


def test_attribute_unknown_action_code_raises():
    with pytest.raises(ValueError, match="unknown action_code_id"):
        bridge.attribute("COM-001", "NOPE-0.0", {})


def test_attribute_deterministic():
    r1 = bridge.attribute("COM-001", "C-M2.1", {"margin.gm.pct": 0.45})
    r2 = bridge.attribute("COM-001", "C-M2.1", {"margin.gm.pct": 0.45})
    assert json.dumps(r1) == json.dumps(r2)


def test_cli_attribute_emits_valid_json(capsys):
    code = bridge.main(["attribute", "COM-001", "C-M2.1", "--t1", '{"margin.gm.pct": 0.45}'])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True and payload["attribution"]


def test_cli_attribute_unknown_action_code_is_json_error(capsys):
    code = bridge.main(["attribute", "COM-001", "NOPE-0.0", "--t1", "{}"])
    assert code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False and "unknown action_code_id" in payload["error"]


def test_cli_attribute_diff_in_diff_needs_control():
    code = bridge.main([
        "attribute", "COM-001", "C-M2.1",
        "--t1", '{"margin.gm.pct": 0.45}', "--method", "diff_in_diff",
    ])
    assert code == 0
    payload = json.loads(json.dumps(bridge.attribute(
        "COM-001", "C-M2.1", {"margin.gm.pct": 0.45}, method="diff_in_diff",
    )))
    by_kpi = {r["kpi_id"]: r for r in payload["attribution"]}
    assert by_kpi["margin.gm.pct"]["status"] == "uncomputed"
    assert "control" in by_kpi["margin.gm.pct"]["note"]
