"""packs.dbt — dbt model-convention rule pack (Official-First, I-5.4).

Static rules from dbt's documented modeling guide: models carry a layer prefix
(stg_/int_/fct_/dim_/fact_/mart_). Test coverage + source freshness need the dbt
artifacts (manifest.json / sources.json) → declared planned ("geplant").
"""
from __future__ import annotations

from tooling.superversion.canonical_contract import CanonicalModel
from tooling.superversion.layer_tools.packs.base import Pack, PackRule, register

_LAYER_PREFIXES = ("stg_", "int_", "fct_", "fact_", "dim_", "mart_")


def _unlayered_models(c: CanonicalModel) -> list[str]:
    return [t.name for t in c.semantic.tables
            if not t.name.startswith(_LAYER_PREFIXES)]


register(Pack(
    id="dbt",
    platform="dbt",
    label="dbt model-convention rule pack (Official-First)",
    rules=(
        PackRule("DBT_MODEL_NAMING", "info",
                 "model lacks a dbt layer prefix (stg_/int_/fct_/dim_/mart_)", _unlayered_models),
    ),
    planned=(
        "test coverage per model (dbt manifest.json)",
        "source freshness (dbt sources.json)",
    ),
))
