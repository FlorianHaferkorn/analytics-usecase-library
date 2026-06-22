"""canonical_contract — strukturgleiche Spiegelung von Meridians kanonischem Modell.

Damit ALUCA eigenständig lauffähig bleibt (PRODUCT_PLAN §2 P5: kein Meridian-Import),
spiegeln wir den Ziel-Vertrag aus `core.pbi_engine.model` / `.parsers.tmdl_parser` /
`.parsers.pbir_parser` hier mit IDENTISCHEN Feldnamen.

Beim Einhängen in Meridian wird dieses Modul durch einen Import der Originale ersetzt:

    from core.pbi_engine.model import CanonicalModel
    from core.pbi_engine.parsers.tmdl_parser import SemanticModel, Table, Measure, ...
    from core.pbi_engine.parsers.pbir_parser import ReportModel, ReportPage, Visual

Feldnamen wurden gegen Meridian-`origin/main` (Stand 2026-06-18) verifiziert. Wenn sich
der Meridian-Vertrag ändert, fängt der Konformitätstest (test_contract_parity) das ab.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


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
    expressions: dict = field(default_factory=dict)  # Dialekt-Map (core→dialekt direkt)


@dataclass
class RoleTablePermission:
    table: str
    filter_expression: str = ""


@dataclass
class Role:
    name: str
    model_permission: str = "read"
    table_permissions: list[RoleTablePermission] = field(default_factory=list)


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
class Table:
    name: str
    description: str = ""
    is_hidden: bool = False
    is_date_table: bool = False
    columns: list[Column] = field(default_factory=list)
    measures: list[Measure] = field(default_factory=list)


@dataclass
class SemanticModel:
    name: str
    tables: list[Table] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    roles: list[Role] = field(default_factory=list)
    compatibility_level: Optional[int] = None


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
    bound_measures: list[str] = field(default_factory=list)


@dataclass
class ReportPage:
    name: str
    display_name: str = ""
    visuals: list[Visual] = field(default_factory=list)
    width: int = 1280
    height: int = 720
    page_type: str = "Default"
    is_hidden: bool = False


@dataclass
class ReportModel:
    name: str
    theme: str = ""
    pages: list[ReportPage] = field(default_factory=list)


@dataclass
class CanonicalModel:
    """Vereinheitlichtes kanonisches Modell: Semantik UND Report (wie Meridian)."""
    semantic: SemanticModel
    report: ReportModel
