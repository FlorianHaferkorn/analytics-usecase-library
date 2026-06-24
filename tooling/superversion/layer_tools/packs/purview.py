"""packs.purview — Microsoft Purview rule pack (Official-First, I-5.4).

Static rules for data-catalog completeness: catalog assets (tables) and measures
should carry a business description (glossary readiness). Sensitivity-label
classification + lineage push need the Purview/Atlas API → declared planned.
"""
from __future__ import annotations

from tooling.superversion.canonical_contract import CanonicalModel
from tooling.superversion.layer_tools.packs.base import Pack, PackRule, register


def _undescribed_tables(c: CanonicalModel) -> list[str]:
    return [t.name for t in c.semantic.tables if not (t.description or "").strip()]


def _undescribed_measures(c: CanonicalModel) -> list[str]:
    return [f"{t.name}[{m.name}]"
            for t in c.semantic.tables for m in t.measures
            if not (m.description or "").strip()]


register(Pack(
    id="purview",
    platform="Microsoft Purview",
    label="Purview rule pack (Official-First)",
    rules=(
        PackRule("PURVIEW_TABLE_DESCRIBED", "warn",
                 "table has no description (glossary/catalog completeness)", _undescribed_tables),
        PackRule("PURVIEW_MEASURE_DESCRIBED", "info",
                 "measure has no description (glossary/catalog completeness)", _undescribed_measures),
    ),
    planned=(
        "sensitivity-label classification scan (Purview API)",
        "lineage push to the data map (Purview Atlas API)",
    ),
))
