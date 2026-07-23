"""
test_architecture_concepts.py — pluggable ArchitectureConcept strategies over the neutral IR
(ADR-0051 / I-20.1). Cross-repo mirror of Meridian's test_concepts.

Medallion is extracted from the deriver as the first strategy and the best-practice default; the
default output stays byte-identical (parity), unknown concepts fail fast, and a new concept registers
without touching the deriver.
"""
from __future__ import annotations

import pytest

from tooling.superversion.architecture_blueprint import derive_blueprint
from tooling.superversion.architecture_concepts import (
    DEFAULT_CONCEPT,
    MedallionConcept,
    available_concepts,
    get_concept,
    register,
)

_INPUTS = {
    "stack": "fabric", "silver_contract_ref": "domains/commercial.yaml",
    "domains": [{"name": "Commercial",
                 "gold_products": [{"name": "dim_customer", "kind": "dimension"},
                                   {"name": "fact_sales", "kind": "fact", "grain": "order line"}],
                 "sources": [{"source": "crm", "source_system": "Dynamics 365 db"}]}],
}


def test_medallion_is_the_registered_default():
    assert DEFAULT_CONCEPT == "medallion"
    assert "medallion" in available_concepts()
    assert get_concept(None).id == "medallion"          # None → default
    assert isinstance(get_concept("medallion"), MedallionConcept)


def test_unknown_concept_fails_fast():
    with pytest.raises(ValueError, match="unknown architecture_concept"):
        get_concept("data-vault-x")
    with pytest.raises(ValueError, match="unknown architecture_concept"):
        derive_blueprint({**_INPUTS, "architecture_concept": "nope"})


def test_default_output_is_byte_identical_parity():
    a = derive_blueprint(_INPUTS)["blueprint"]["medallion"]
    b = derive_blueprint({**_INPUTS, "architecture_concept": "medallion"})["blueprint"]["medallion"]
    assert a == b
    assert a["bronze"] == {"enabled": False, "outsourced": True, "immutable": True, "append_only": True}
    assert a["no_layer_skip"] is True
    assert a["silver"]["data_contract_ref"] == "domains/commercial.yaml"
    assert [p["name"] for p in a["gold"]["data_products"]] == ["dim_customer", "fact_sales"]  # sorted


def test_silver_ref_absent_marks_hitl():
    out = derive_blueprint({k: v for k, v in _INPUTS.items() if k != "silver_contract_ref"})
    assert any("silver.data_contract_ref" in g for g in out["hitl"])


def test_a_new_concept_registers_without_touching_the_deriver():
    class _StubConcept:
        id = "_stub_test_concept"
        def derive_layers(self, domains_in, inputs, hitl):
            return {"stub": True, "domains": len(domains_in)}
    register(_StubConcept())
    assert "_stub_test_concept" in available_concepts()
    bp = derive_blueprint({**_INPUTS, "architecture_concept": "_stub_test_concept"})["blueprint"]
    assert bp["medallion"] == {"stub": True, "domains": 1}
    assert derive_blueprint(_INPUTS)["blueprint"]["medallion"]["no_layer_skip"] is True


def test_deterministic():
    assert derive_blueprint(_INPUTS) == derive_blueprint(_INPUTS)
