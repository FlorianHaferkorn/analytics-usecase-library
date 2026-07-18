"""architecture_concepts — pluggable ArchitectureConcept strategies over the neutral IR (ADR-0051 / I-20.1).

Cross-repo mirror of Meridian's `core.dataarch_engine.blueprint.concepts` (contract surface only — the
concept/gov *registries*, not the delivery-layer emitters, which live only in Meridian). The **architecture
concept** decides how the IR's storage/layer section is derived from governed inputs. **Medallion**
(bronze/silver/gold, silver-first) is the first strategy and the **best-practice default** (MS-recommended).
Further concepts register here **without touching the deriver** — implement `derive_layers` and `register(...)`.

Golden-Thread: concepts *project* governed inputs onto the IR; they never re-define KPI meaning, targets or
lineage. Selection is derive-time (`inputs["architecture_concept"]`, default `medallion`); the default output
is byte-identical to the pre-strategy deriver (I-20.1 parity), so the cross-repo IR mirror is unaffected.
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

DEFAULT_CONCEPT = "medallion"


@runtime_checkable
class ArchitectureConcept(Protocol):
    """A strategy that derives the IR storage-layer section from governed inputs.

    ``derive_layers`` returns the dict assigned to ``blueprint["medallion"]`` (the IR's layer
    section). It may append HITL gaps to ``hitl`` (deduped+sorted by the deriver). Deterministic.
    """
    id: str

    def derive_layers(self, domains_in: list[dict], inputs: dict, hitl: list[str]) -> dict[str, Any]:
        ...


class MedallionConcept:
    """Bronze/Silver/Gold, **silver-first** (bronze outsourced but specified; `no_layer_skip`).

    Microsoft's recommended design for Fabric (OneLake medallion) and our best-practice default.
    Gold = union of all domains' gold products; silver keyed by a data-contract ref (HITL if absent).
    """
    id = "medallion"

    def derive_layers(self, domains_in: list[dict], inputs: dict, hitl: list[str]) -> dict[str, Any]:
        gold_products: list[dict[str, Any]] = []
        for dom in domains_in:
            prods = dom.get("gold_products")
            if not prods:
                hitl.append(f"gold.data_products underspecified for domain '{dom.get('name')}'")
                continue
            for p in prods:
                gp: dict[str, Any] = {"name": p["name"], "kind": p["kind"]}
                if p.get("grain"):
                    gp["grain"] = p["grain"]
                gold_products.append(gp)
        gold_products.sort(key=lambda p: p["name"])

        silver_ref = inputs.get("silver_contract_ref")
        if not silver_ref:
            silver_ref = "HITL: silver data_contract_ref not supplied"
            hitl.append("medallion.silver.data_contract_ref not supplied")

        return {
            "bronze": {  # silver-first default: bronze outsourced but specified (data_layers §2.1)
                "enabled": False,
                "outsourced": True,
                "immutable": True,
                "append_only": True,
            },
            "silver": {"data_contract_ref": silver_ref},
            "gold": {"data_products": gold_products},
            "no_layer_skip": True,
        }


class DataVaultConcept:
    """Data Vault 2.0: a **raw vault** as materialised, insert-only bronze; business vault in silver.

    Cross-repo mirror of Meridian's DataVaultConcept — a genuinely distinct paradigm from silver-first
    medallion, schema-valid (the raw vault *is* an ``enabled`` + ``immutable`` + ``append_only`` bronze).
    """
    id = "data-vault"

    def derive_layers(self, domains_in: list[dict], inputs: dict, hitl: list[str]) -> dict[str, Any]:
        layers = MedallionConcept().derive_layers(domains_in, inputs, hitl)
        layers["bronze"] = {"enabled": True, "outsourced": False, "immutable": True, "append_only": True}
        hitl.append("data-vault: silver business-vault modeling (hubs/links/satellites) required per domain")
        return layers


_REGISTRY: dict[str, ArchitectureConcept] = {}


def register(concept: ArchitectureConcept) -> ArchitectureConcept:
    """Register an architecture concept by its ``id`` (idempotent). Returns the concept."""
    _REGISTRY[concept.id] = concept
    return concept


def get_concept(name: str | None) -> ArchitectureConcept:
    """Resolve a concept by id (``None`` → default). Unknown → ValueError (fail-fast, ADR-0051)."""
    key = name or DEFAULT_CONCEPT
    concept = _REGISTRY.get(key)
    if concept is None:
        raise ValueError(f"unknown architecture_concept {key!r}; "
                         f"choose one of {sorted(_REGISTRY)}")
    return concept


def available_concepts() -> list[str]:
    return sorted(_REGISTRY)


register(MedallionConcept())  # the best-practice default; first registered strategy
register(DataVaultConcept())  # mirrored from Meridian (contract surface) — keeps the two repos in sync
