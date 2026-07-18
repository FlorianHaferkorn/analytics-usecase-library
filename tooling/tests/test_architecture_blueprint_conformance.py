"""
test_architecture_blueprint_conformance.py — ADR-0015 / T5.

Guards the blueprint_conformance scorecard:
  - a clean blueprint scores green (n/a where a pattern doesn't apply);
  - an adversarial blueprint scores red on exactly the violated patterns;
  - the gate is deterministic and renders a scorecard.
"""
from __future__ import annotations

from tooling.superversion.architecture_blueprint import derive_blueprint
from tooling.superversion.eval.blueprint_conformance import (
    conformance, P1, P2, P3, P4, P5, AI,
)

_CLEAN = {
    "stack": "fabric",
    "silver_contract_ref": "core/data_contracts/domains/commercial.yaml",
    "domains": [
        {
            "name": "Commercial",
            "gold_products": [{"name": "fact_sales", "kind": "fact"}],
            "sources": [{"source": "crm", "source_system": "Dynamics 365"}],
            "endorsement": "certified",
        }
    ],
}

_ADVERSARIAL = {
    "schema_version": "0.1.0",
    "platform": {"stack": "fabric", "ownership_boundaries": [
        {"workload_class": "transformation", "owner_platform": "fabric"},
        {"workload_class": "transformation", "owner_platform": "databricks"},  # duplicate → P4 red
    ]},
    "ingestion": [{"source": "s", "access_mode": "copy",
                   "rationale": "default access mode for x"}],  # copy w/o rationale → P1 red
    "medallion": {"bronze": {"enabled": True, "immutable": True, "append_only": True},
                  "silver": {"data_contract_ref": "x"},
                  "gold": {"data_products": []},          # empty gold → P2 amber (dominated by red)
                  "no_layer_skip": False},                # layer skip → P2 red
    "mesh": {"domains": [{"name": "D", "workspaces": [],   # no workspace → P3 red
                          "data_products": ["dim_x"],
                          "publishing": {"endorsement": "none", "intended_audience": "internal"}}]},
    "sharing": [{"external_product": "e", "source_gold_ref": "g",
                 "label": "public", "workspace": "w"}],   # no sanitization → P5 amber
    "ai_grounding": {"grounding_surface": ["gold", "bronze"],  # bronze → AI red
                     "retrieval": [{"domain": "D", "strategy": "mcp"}]},
}


def test_clean_blueprint_is_green():
    bp = derive_blueprint(_CLEAN)["blueprint"]
    r = conformance(bp)
    assert r.ok
    assert r.scorecard[P1] == "green"
    assert r.scorecard[P2] == "green"
    assert r.scorecard[P3] == "green"
    assert r.scorecard[P4] == "green"
    assert r.scorecard[P5] == "na"      # no external sharing declared
    assert r.scorecard[AI] == "green"


def test_adversarial_blueprint_scores_red():
    r = conformance(_ADVERSARIAL)
    assert not r.ok
    assert r.scorecard[P1] == "red"
    assert r.scorecard[P2] == "red"
    assert r.scorecard[P3] == "red"
    assert r.scorecard[P4] == "red"
    assert r.scorecard[P5] == "amber"
    assert r.scorecard[AI] == "red"


def test_bronze_grounding_is_flagged_red():
    r = conformance(_ADVERSARIAL)
    kinds = {f.kind for f in r.findings if f.pattern == AI}
    assert "invalid_grounding_surface" in kinds


def test_unpublished_domain_is_amber_when_otherwise_clean():
    bp = derive_blueprint({
        "stack": "fabric", "silver_contract_ref": "x.yaml",
        "domains": [{"name": "Finance", "gold_products": [{"name": "fact_gl", "kind": "fact"}],
                     "endorsement": "none"}],
    })["blueprint"]
    r = conformance(bp)
    assert r.scorecard[P3] == "amber"
    assert r.ok  # amber is not a hard block


def test_deterministic_and_renders():
    a = conformance(_ADVERSARIAL)
    b = conformance(_ADVERSARIAL)
    assert a.scorecard == b.scorecard
    md = a.to_markdown()
    assert "Pattern" in md and "🔴" in md
