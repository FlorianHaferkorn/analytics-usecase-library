"""packs.unity_catalog — Databricks Unity Catalog rule pack (Official-First, I-5.4).

Static rules from UC's documented object conventions: identifiers are lowercase
(UC folds/recommends lowercase snake_case) and columns are typed. Storage/managed
location + catalog binding need the UC API → declared planned ("geplant").
"""
from __future__ import annotations

import re

from tooling.superversion.canonical_contract import CanonicalModel
from tooling.superversion.layer_tools.packs.base import Pack, PackRule, register

_SNAKE = re.compile(r"^[a-z][a-z0-9_]*$")


def _bad_table_names(c: CanonicalModel) -> list[str]:
    return [t.name for t in c.semantic.tables if not _SNAKE.match(t.name)]


def _untyped_columns(c: CanonicalModel) -> list[str]:
    return [f"{t.name}.{col.name}"
            for t in c.semantic.tables for col in t.columns
            if not (col.data_type or "").strip()]


register(Pack(
    id="unity_catalog",
    platform="Databricks Unity Catalog",
    label="Unity Catalog rule pack (Official-First)",
    rules=(
        PackRule("UC_TABLE_NAMING", "warn",
                 "table name is not lowercase snake_case (UC convention)", _bad_table_names),
        PackRule("UC_COLUMN_TYPED", "warn",
                 "column has no data type (UC requires typed columns)", _untyped_columns),
    ),
    planned=(
        "managed-location / storage-credential enforcement (Unity Catalog API)",
        "catalog/schema three-level binding (Unity Catalog API)",
    ),
))
