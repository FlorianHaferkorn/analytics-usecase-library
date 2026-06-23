"""_canonical_mirror — structure-identical mirror of Meridian's canonical contract.

This is ALUCA's **standalone substrate** (ADR-0005 rule 3, PRODUCT_PLAN F4): the
dataclasses are a verbatim mirror of Meridian's `core.pbi_engine.parsers.tmdl_parser`
/ `.pbir_parser` / `.model` — IDENTICAL field names, order, defaults and types — so
ALUCA builds and tests with **no** Meridian present.

`canonical_contract` re-exports Meridian's originals when the vendored core is
available and falls back to this mirror otherwise. Because the mirror is verbatim,
`model_to_json` is byte-identical in both modes (Invariant I2). Drift between this
mirror and the real contract is caught by `test_contract_parity_with_meridian`
(all dataclasses, both directions), enforced in CI where the vendored core is present.

Field parity verified against the vendored Meridian subtree (see PIN.json) on
2026-06-23. If Meridian's contract changes, the parity test fails and this mirror
must be re-synced in the same deliberate commit that moves the pin.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

__all__ = [
    "Column", "Measure", "RoleTablePermission", "RoleColumnPermission", "Role",
    "Table", "Relationship", "ModelFunction", "SemanticModel",
    "VisualCalculation", "Visual", "ReportPage", "ExtensionMeasure", "Bookmark",
    "ReportModel", "CanonicalModel",
]


# --- Semantic model (mirror of tmdl_parser) -------------------------------- #

@dataclass
class Column:
    name: str
    data_type: str = ""
    is_hidden: bool = False
    description: str = ""
    summarize_by: str = ""


@dataclass
class Measure:
    name: str
    expression: str = ""
    display_folder: str = ""
    description: str = ""
    format_string: str = ""
    is_hidden: bool = False
    expressions: dict = field(default_factory=dict)  # Dialekt-Map (core→dialekt)


@dataclass
class RoleTablePermission:
    table: str
    filter_expression: str = ""


@dataclass
class RoleColumnPermission:
    table: str
    column: str
    metadata_permission: str = "read"


@dataclass
class Role:
    name: str
    model_permission: str = "read"
    table_permissions: list[RoleTablePermission] = field(default_factory=list)
    column_permissions: list[RoleColumnPermission] = field(default_factory=list)


@dataclass
class Table:
    name: str
    description: str = ""
    is_hidden: bool = False
    is_date_table: bool = False
    columns: list[Column] = field(default_factory=list)
    measures: list[Measure] = field(default_factory=list)
    has_partition: bool = False
    partition_type: str = ""
    m_expression: str = ""
    hierarchy_columns: list[str] = field(default_factory=list)


@dataclass
class Relationship:
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    cardinality: str = ""
    cross_filter: str = ""
    is_active: bool = True


@dataclass
class ModelFunction:
    name: str
    expression: str = ""
    description: str = ""


@dataclass
class SemanticModel:
    name: str
    tables: list[Table] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    roles: list[Role] = field(default_factory=list)
    functions: list[ModelFunction] = field(default_factory=list)
    compatibility_level: Optional[int] = None
    parse_parity: dict = field(default_factory=dict)


# --- Report model (mirror of pbir_parser) ---------------------------------- #

@dataclass
class VisualCalculation:
    name: str
    expression: str = ""
    language: str = "dax"


@dataclass
class Visual:
    visual_id: str
    visual_type: str
    x: float = 0
    y: float = 0
    width: float = 0
    height: float = 0
    title: str = ""
    has_title: bool = True
    binds_measures: bool = False
    has_tooltip_fields: bool = False
    has_tooltip_vco: bool = False
    visual_calculations: list[VisualCalculation] = field(default_factory=list)
    bound_measures: list[str] = field(default_factory=list)
    rows: list[str] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    slicer_field: str = ""


@dataclass
class ReportPage:
    name: str
    display_name: str = ""
    visuals: list[Visual] = field(default_factory=list)
    width: int = 1280
    height: int = 720
    page_type: str = "Default"
    has_mobile_layout: bool = False
    is_hidden: bool = False


@dataclass
class ExtensionMeasure:
    name: str
    table: str
    expression: str = ""
    data_type: str = ""
    is_hidden: bool = False
    format_string: str = ""


@dataclass
class Bookmark:
    name: str
    display_name: str = ""
    target_page: str = ""


@dataclass
class ReportModel:
    name: str
    theme: str = ""
    pages: list[ReportPage] = field(default_factory=list)
    extension_measures: list[ExtensionMeasure] = field(default_factory=list)
    bookmarks: list[Bookmark] = field(default_factory=list)


@dataclass
class CanonicalModel:
    """Vereinheitlichtes kanonisches Modell: Semantik UND Report (wie Meridian)."""
    semantic: SemanticModel
    report: ReportModel
