"""
test_governance_concepts.py — pluggable, mixable GovernanceConcept strategies (ADR-0051 / I-20.2).
Cross-repo mirror of Meridian's test_governance_concepts.

ODCS-contract-first is the best-practice default; each strategy declares its seed sources + emphasised
gates; unknown ids fail fast; and ``resolve_governance`` merges a list of concepts (union of seeds/gates,
deduped+sorted) with a mixed-standards warning — the seam the mix-gate later validates.
"""
from __future__ import annotations

import pytest

from tooling.superversion.governance_concepts import (
    DEFAULT_GOVERNANCE_CONCEPT,
    OdcsContractFirst,
    available_governance_concepts,
    get_governance_concept,
    register,
    resolve_governance,
)


def test_odcs_is_the_registered_default():
    assert DEFAULT_GOVERNANCE_CONCEPT == "odcs-contract-first"
    assert "odcs-contract-first" in available_governance_concepts()
    assert get_governance_concept(None).id == "odcs-contract-first"
    assert isinstance(get_governance_concept("odcs-contract-first"), OdcsContractFirst)


def test_unknown_concept_fails_fast():
    with pytest.raises(ValueError, match="unknown governance_concept"):
        get_governance_concept("zero-trust-x")
    with pytest.raises(ValueError, match="unknown governance_concept"):
        resolve_governance({"governance_concept": "nope"})


def test_all_four_strategies_registered():
    assert available_governance_concepts() == [
        "dq-first", "glossary-first", "odcs-contract-first", "purview-data-product",
    ]


def test_each_strategy_declares_seeds_and_gates():
    odcs = get_governance_concept("odcs-contract-first").profile()
    assert odcs["seeds"] == ["data_contracts"]
    assert odcs["contract_standard"] == "odcs"
    assert "conformance" in odcs["gates"]

    purview = get_governance_concept("purview-data-product").profile()
    assert "purview_data_products" in purview["seeds"]
    assert purview["contract_standard"] is None

    glossary = get_governance_concept("glossary-first").profile()
    assert glossary["seeds"] == ["business_glossary", "kpi_catalog"]

    dq = get_governance_concept("dq-first").profile()
    assert dq["seeds"] == ["data_quality"]
    assert "dq" in dq["gates"]


def test_resolve_single_concept_defaults_to_odcs():
    out = resolve_governance({})
    assert out["concepts"] == ["odcs-contract-first"]
    assert out["seeds"] == ["data_contracts"]
    assert out["contract_standard"] == "odcs"


def test_resolve_merges_a_list_union_deduped_sorted():
    out = resolve_governance({"governance_concept": ["odcs-contract-first", "glossary-first"]})
    assert out["concepts"] == ["odcs-contract-first", "glossary-first"]
    assert out["seeds"] == ["business_glossary", "data_contracts", "kpi_catalog"]
    assert out["gates"] == ["catalog-tmdl-drift", "conformance", "measure-uniqueness", "schema-validate"]
    assert out["contract_standard"] == "odcs"
    assert "⚠" not in out["note"]


def test_resolve_flags_mixed_contract_standards():
    class _StubStandardB:
        id = "_stub_std_b"
        def profile(self):
            return {"seeds": ["x"], "gates": ["g"], "contract_standard": "other-std", "note": "stub"}
    register(_StubStandardB())
    out = resolve_governance({"governance_concept": ["odcs-contract-first", "_stub_std_b"]})
    assert "⚠" in out["note"]
    assert "other-std" in out["note"] and "odcs" in out["note"]


def test_empty_list_falls_back_to_default():
    out = resolve_governance({"governance_concept": []})
    assert out["concepts"] == ["odcs-contract-first"]


def test_deterministic():
    assert resolve_governance({"governance_concept": ["dq-first", "purview-data-product"]}) == \
        resolve_governance({"governance_concept": ["dq-first", "purview-data-product"]})
