"""packs — tool-specific domain-rule packs (task I-5.4, G7).

Importing this package registers the platform packs (unity_catalog, purview, dbt)
on the contract in `base.py`. Packs are additive over the generic engines (I-5.3);
disabling a pack falls back to the generic rules (rollback).
Run via `python -m tooling.superversion.layer_tools.packs.cli`.
"""
from tooling.superversion.layer_tools.packs import (  # noqa: F401 — register on import
    dbt,
    purview,
    unity_catalog,
)
from tooling.superversion.layer_tools.packs.base import (
    Pack,
    PackContractError,
    PackFinding,
    PackReport,
    PackRule,
    available,
    evaluate,
    get,
    register,
)

__all__ = [
    "Pack", "PackRule", "PackFinding", "PackReport", "PackContractError",
    "register", "get", "available", "evaluate",
]
