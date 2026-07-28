"""
test_architecture_blueprint_fabric.py — ADR-0015 / T4.

Guards the Fabric arch-target renderer:
  - it emits the expected plan artifacts from a derived blueprint;
  - the shortcut/mirror plan reflects ingestion access modes (P1);
  - rendering is deterministic;
  - the gold data-product name-set in the output matches the blueprint (cross-target
    parity, analogous to targets/test_cross_target_equivalence);
  - render(dest) actually writes the files.
"""
from __future__ import annotations

import json

from tooling.superversion.architecture_blueprint import derive_blueprint
from tooling.superversion import arch_targets

_FIXTURE = {
    "stack": "fabric",
    "silver_contract_ref": "core/data_contracts/domains/commercial.yaml",
    "domains": [
        {
            "name": "Commercial",
            "gold_products": [
                {"name": "dim_customer", "kind": "dimension"},
                {"name": "fact_sales", "kind": "fact"},
            ],
            "sources": [
                {"source": "crm_orders", "source_system": "Dynamics 365"},
                {"source": "web_events", "source_system": "ADLS Gen2"},
            ],
            "endorsement": "certified",
        }
    ],
}


def _bp():
    return derive_blueprint(_FIXTURE)["blueprint"]


_TOPOLOGY = {
    "fabric/PROVISIONING_PLAN.md",
    "fabric/workspaces.json",
    "fabric/ingestion_plan.json",
    "fabric/medallion.json",
    "fabric/semantic_binding.json",
}


def test_emits_expected_artifacts():
    out = arch_targets.render("fabric", _bp())
    assert _TOPOLOGY <= set(out)
    ws = json.loads(out["fabric/workspaces.json"])
    names = {w["name"] for d in ws for w in d["workspaces"]}
    assert "ws-commercial-gold" in names and "ws-commercial-reporting" in names


def test_mirrored_meridian_layer_is_emitted_alongside_the_topology():
    """The topology layer alone was never the whole Fabric scaffold — governance,
    monitoring, lifecycle, connectivity and operability come from the mirrored Meridian
    emitters (SHARED_SUBSTANCE.md class A) instead of a second implementation here."""
    from tooling.superversion._dataarch_vendor import available

    out = arch_targets.render("fabric", _bp())
    if not available():
        # A broken/absent mirror must degrade loudly, not silently.
        assert "**Not emitted**" in out["fabric/PROVISIONING_PLAN.md"]
        assert set(out) == _TOPOLOGY
        return

    extra = set(out) - _TOPOLOGY
    assert extra, "mirror is available but contributed nothing"
    for prefix in ("fabric/governance/", "fabric/monitoring/", "fabric/lifecycle/",
                   "fabric/connectivity/"):
        assert any(p.startswith(prefix) for p in extra), f"no artifact under {prefix}"
    # And the runbook must name what it emitted, so the plan stays self-describing.
    plan = out["fabric/PROVISIONING_PLAN.md"]
    assert "mirrored Meridian emitters" in plan


def test_ingestion_access_modes():
    out = arch_targets.render("fabric", _bp())
    plan = {e["source"]: e["access_mode"] for e in json.loads(out["fabric/ingestion_plan.json"])}
    assert plan == {"crm_orders": "mirror", "web_events": "shortcut"}


def test_medallion_no_layer_skip_and_grounding():
    out = arch_targets.render("fabric", _bp())
    med = json.loads(out["fabric/medallion.json"])
    assert med["no_layer_skip"] is True
    assert "gold" in out["fabric/PROVISIONING_PLAN.md"].lower()
    assert "never bronze" in out["fabric/PROVISIONING_PLAN.md"]


def test_render_is_deterministic():
    a = arch_targets.render("fabric", _bp())
    b = arch_targets.render("fabric", _bp())
    assert a == b


def test_gold_name_parity_with_blueprint():
    bp = _bp()
    out = arch_targets.render("fabric", bp)
    med = json.loads(out["fabric/medallion.json"])
    out_names = sorted(p["name"] for p in med["gold"]["data_products"])
    bp_names = sorted(p["name"] for p in bp["medallion"]["gold"]["data_products"])
    assert out_names == bp_names == ["dim_customer", "fact_sales"]


def test_render_writes_files(tmp_path):
    written = arch_targets.render("fabric", _bp(), dest=tmp_path)
    for rel in written:
        assert (tmp_path / rel).is_file()
    assert (tmp_path / "fabric" / "PROVISIONING_PLAN.md").read_text(encoding="utf-8").startswith(
        "# Fabric Provisioning Plan"
    )


def test_fabric_is_registered():
    assert "fabric" in arch_targets.available()
