"""
test_architecture_blueprint_ground.py — ADR-0015 / T6.

Guards the `ground` verb (emit_grounding):
  - it emits a tool-free mcp_grounding.json + a per-domain retrieval record;
  - the manifest points only at gold/silver (no bronze anywhere);
  - retrieval defaults to built-in;
  - a blueprint that grounds on bronze is rejected;
  - output is deterministic.
"""
from __future__ import annotations

import json

import pytest

from tooling.superversion.architecture_blueprint import derive_blueprint, emit_grounding

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
            "endorsement": "certified",
        }
    ],
}


def _bp():
    return derive_blueprint(_FIXTURE)["blueprint"]


def test_emits_manifest_and_record():
    out = emit_grounding(_bp())
    assert set(out) == {"mcp_grounding.json", "retrieval_decisions.md"}
    manifest = json.loads(out["mcp_grounding.json"])
    assert manifest["grounding_surface"] == ["gold", "silver"]
    res = {r["domain"]: r["data_products"] for r in manifest["resources"]}
    assert res["Commercial"] == ["dim_customer", "fact_sales"]


def test_no_bronze_anywhere():
    out = emit_grounding(_bp())
    assert "bronze" not in out["mcp_grounding.json"]


def test_retrieval_defaults_builtin():
    manifest = json.loads(emit_grounding(_bp())["mcp_grounding.json"])
    assert all(r["strategy"] == "builtin" for r in manifest["retrieval"])
    assert "Commercial" in out_md(_bp())


def out_md(bp):
    return emit_grounding(bp)["retrieval_decisions.md"]


def test_bronze_grounding_is_rejected():
    bp = _bp()
    bp["ai_grounding"]["grounding_surface"] = ["gold", "bronze"]
    with pytest.raises(ValueError):
        emit_grounding(bp)


def test_deterministic():
    assert emit_grounding(_bp()) == emit_grounding(_bp())
