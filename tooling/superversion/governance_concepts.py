"""governance_concepts — pluggable, mixable GovernanceConcept strategies (ADR-0051 / I-20.2).

Cross-repo mirror of Meridian's `core.dataarch_engine.blueprint.governance_concepts` (contract surface).
Where the **architecture concept** (`architecture_concepts.py`) decides how the IR's layer section is
derived, the **governance concept** decides *what seeds the build* and *which validation gates carry
weight*. Four strategies register here; **ODCS-contract-first** is the best-practice default
(Official-First, ADR-0051):

  * ``odcs-contract-first`` — the (ODCS) data contract is the desired-state seed; conformance +
    catalog↔TMDL-drift + schema-load gates.
  * ``purview-data-product`` — the governed catalog's data products (single owning domain) seed the
    gold boundary; conformance + endorsement + access/RBAC gates.
  * ``glossary-first`` — the business glossary + KPI catalog align terms/measures first;
    measure-uniqueness + catalog-drift gates.
  * ``dq-first`` — data-quality rules lead; DQ + drift gates.

Concepts are **mixable**: ``resolve_governance(inputs)`` accepts one id or a list and merges the
profiles (union of seeds/gates, deduped) — the seam the mix-gate later validates. Each concept is a
*declarative profile*; it never re-defines KPI meaning (Golden-Thread). Deterministic.
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

DEFAULT_GOVERNANCE_CONCEPT = "odcs-contract-first"


@runtime_checkable
class GovernanceConcept(Protocol):
    """A strategy declaring the build's governance seed sources + emphasised gates."""
    id: str

    def profile(self) -> dict[str, Any]:
        """Return ``{seeds: [...], gates: [...], contract_standard: str|None, note: str}``."""
        ...


class OdcsContractFirst:
    """The data contract (ODCS) is the desired-state IR the build implements (best-practice default)."""
    id = "odcs-contract-first"

    def profile(self) -> dict[str, Any]:
        return {
            "seeds": ["data_contracts"],
            "gates": ["conformance", "catalog-tmdl-drift", "schema-validate"],
            "contract_standard": "odcs",
            "note": "Official-First: ODCS-Contract als desired-state; Build implementiert den Vertrag.",
        }


class PurviewDataProduct:
    """Purview Unified-Catalog data products (single owning domain) define the gold boundary."""
    id = "purview-data-product"

    def profile(self) -> dict[str, Any]:
        return {
            "seeds": ["purview_data_products", "governed_catalog"],
            "gates": ["conformance", "endorsement", "access-rbac"],
            "contract_standard": None,
            "note": "Data Product = ein besitzender Governance-Domain, über viele auffindbar (Gold-Grenze).",
        }


class GlossaryFirst:
    """The business glossary + KPI catalog align terms/measures before physical build."""
    id = "glossary-first"

    def profile(self) -> dict[str, Any]:
        return {
            "seeds": ["business_glossary", "kpi_catalog"],
            "gates": ["measure-uniqueness", "catalog-tmdl-drift"],
            "contract_standard": None,
            "note": "Begriffs-/KPI-Ausrichtung zuerst; Measures gegen das Glossar geerdet.",
        }


class DqFirst:
    """Data-quality rules lead; the build is gated on DQ before promotion."""
    id = "dq-first"

    def profile(self) -> dict[str, Any]:
        return {
            "seeds": ["data_quality"],
            "gates": ["dq", "catalog-tmdl-drift"],
            "contract_standard": None,
            "note": "Qualitäts-Gates führen; DQ-Regeln aus governance.json steuern die Promotion.",
        }


_REGISTRY: dict[str, GovernanceConcept] = {}


def register(concept: GovernanceConcept) -> GovernanceConcept:
    _REGISTRY[concept.id] = concept
    return concept


def get_governance_concept(name: str | None) -> GovernanceConcept:
    """Resolve one concept by id (``None`` → default). Unknown → ValueError (fail-fast, ADR-0051)."""
    key = name or DEFAULT_GOVERNANCE_CONCEPT
    concept = _REGISTRY.get(key)
    if concept is None:
        raise ValueError(f"unknown governance_concept {key!r}; choose one of {sorted(_REGISTRY)}")
    return concept


def available_governance_concepts() -> list[str]:
    return sorted(_REGISTRY)


def resolve_governance(inputs: dict) -> dict[str, Any]:
    """Resolve the governance profile from ``inputs['governance_concept']`` (id, list, or absent→default).

    Mixable: a list merges the profiles (union of seeds/gates, deduped+sorted). ``contract_standard``
    is the first non-null across the chosen concepts (conflicts surface in ``note`` — the mix-gate seam).
    """
    sel = inputs.get("governance_concept") or DEFAULT_GOVERNANCE_CONCEPT
    ids = [sel] if isinstance(sel, str) else list(sel)
    if not ids:
        ids = [DEFAULT_GOVERNANCE_CONCEPT]
    profiles = [get_governance_concept(i).profile() for i in ids]  # ValueError on unknown
    seeds = sorted({s for p in profiles for s in p["seeds"]})
    gates = sorted({g for p in profiles for g in p["gates"]})
    standards = [p["contract_standard"] for p in profiles if p.get("contract_standard")]
    notes = "; ".join(p["note"] for p in profiles)
    if len(set(standards)) > 1:
        notes += f"  ⚠ mehrere contract_standards gemischt: {sorted(set(standards))} (Mix-Gate prüft)."
    return {
        "concepts": ids,
        "seeds": seeds,
        "gates": gates,
        "contract_standard": standards[0] if standards else None,
        "note": notes,
    }


for _c in (OdcsContractFirst(), PurviewDataProduct(), GlossaryFirst(), DqFirst()):
    register(_c)
