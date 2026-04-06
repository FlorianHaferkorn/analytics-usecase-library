"""
IR (Intermediate Representation) — tool-agnostic spec objects.

A DashboardSpec fully describes what to generate (pages, visuals, measures,
bindings) without referencing any target BI platform.  Adapters consume IR and
emit platform-specific files (PBIP JSON, Metabase JSON, Grafana YAML, …).

Design rules
------------
* All fields use Python types — no Power BI / PBIP nomenclature.
* VisualType values are from the UseCase_Bracket visual_type vocabulary.
* Position is always in canvas-fraction coordinates (0.0–1.0) so adapters
  can scale to any target canvas size.
* Binding uses measure/column *names* (human readable); adapters resolve
  table references internally.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class VisualType(str, Enum):
    KPI_CARD = "kpi_card"
    TREND_LINE = "trend_line"
    BAR_CHART = "bar_chart"
    WATERFALL = "waterfall"
    SCATTER = "scatter"
    MATRIX = "matrix"
    TABLE = "table"
    SLICER = "slicer"
    SMART_NARRATIVE = "smart_narrative"
    ACTION_PANEL = "action_panel"
    TEXT_BOX = "text_box"


class PageRole(str, Enum):
    OVERVIEW = "overview"   # 3s KPI cards + 30s driver visuals
    DETAIL = "detail"       # 300s deep-dive matrix + action panel


class PageType(str, Enum):
    T1_STRATEGIC_OVERVIEW = "T1"
    T2_TACTICAL_VARIANCE = "T2"
    T3_OPERATIONAL_MONITORING = "T3"
    T4_PRESCRIPTIVE_RECOMMENDATION = "T4"


class AdapterTarget(str, Enum):
    PBIP = "pbip"
    METABASE = "metabase"
    GRAFANA = "grafana"
    SUPERSET = "superset"
    REDASH = "redash"


# ---------------------------------------------------------------------------
# Layout primitives
# ---------------------------------------------------------------------------

@dataclass
class Position:
    """Canvas-fraction position (0.0–1.0 on each axis)."""
    x: float = 0.0
    y: float = 0.0
    width: float = 0.25
    height: float = 0.25

    def to_pixels(self, canvas_w: int, canvas_h: int) -> Dict[str, int]:
        return {
            "x": round(self.x * canvas_w),
            "y": round(self.y * canvas_h),
            "width": round(self.width * canvas_w),
            "height": round(self.height * canvas_h),
        }


# ---------------------------------------------------------------------------
# Data binding
# ---------------------------------------------------------------------------

@dataclass
class Binding:
    """
    Declares what data a visual consumes.

    All names are human-readable (from KPI catalog / data contract).
    The adapter resolves table references when emitting platform JSON.
    """
    measure: Optional[str] = None           # Primary measure name
    measures: List[str] = field(default_factory=list)  # Multi-measure (cards, matrix)
    category: Optional[str] = None          # Category axis: table.column or just column
    series: Optional[str] = None            # Series/legend column
    columns: List[str] = field(default_factory=list)   # Table columns (matrix, detail)
    filter_table: Optional[str] = None      # Slicer target table
    filter_column: Optional[str] = None     # Slicer target column
    sort_by: Optional[str] = None           # Default sort column/measure
    top_n: Optional[int] = None             # Top-N filter if applicable


# ---------------------------------------------------------------------------
# Visual specification
# ---------------------------------------------------------------------------

@dataclass
class VisualSpec:
    """
    Describes a single visual — platform-agnostic.

    ``id`` is the slot identifier from UseCase_Bracket (KPI_Cards, Main_1, …).
    ``config`` holds adapter-specific overrides that the adapter merges in.
    """
    id: str                                 # Slot ID: "KPI_Cards", "Main_2", "ActionPanel"
    visual_type: VisualType
    page_role: PageRole
    position: Position
    binding: Binding
    title: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    # Metadata
    kpi_id: Optional[str] = None            # Source KPI ID from catalog
    action_code_id: Optional[str] = None    # Source action code ID


# ---------------------------------------------------------------------------
# Page specification
# ---------------------------------------------------------------------------

@dataclass
class PageSpec:
    """Describes one report page (Overview or Detail)."""
    id: str                                 # Stable slug: "Overview", "Detail"
    display_name: str                       # Shown in report tab
    role: PageRole
    page_type: PageType = PageType.T1_STRATEGIC_OVERVIEW
    visuals: List[VisualSpec] = field(default_factory=list)
    order: int = 0                          # Tab order (0 = first)

    def visuals_by_type(self, vtype: VisualType) -> List[VisualSpec]:
        return [v for v in self.visuals if v.visual_type == vtype]

    def visual_by_id(self, vid: str) -> Optional[VisualSpec]:
        return next((v for v in self.visuals if v.id == vid), None)


# ---------------------------------------------------------------------------
# Measure specification
# ---------------------------------------------------------------------------

@dataclass
class MeasureSpec:
    """Describes one DAX measure (model layer)."""
    kpi_id: str                             # e.g. "com.sales.net_sales_amount"
    name: str                               # Display name in Power BI field list
    dax: str                                # DAX expression (single-line)
    format_string: str = "#,0"
    display_folder: str = ""
    is_hidden: bool = False
    description: Optional[str] = None
    annotations: Dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Evidence / detail table
# ---------------------------------------------------------------------------

@dataclass
class EvidenceTableSpec:
    """Detail-page matrix configuration (from bracket evidence_grain)."""
    grain: str                              # e.g. "customer_invoice_line"
    columns: List[str] = field(default_factory=list)
    measures: List[str] = field(default_factory=list)
    sort_by: Optional[str] = None
    limit: int = 500
    data_bars: bool = False


# ---------------------------------------------------------------------------
# Action panel specification
# ---------------------------------------------------------------------------

@dataclass
class ActionPanelSpec:
    """Action panel text config (Detail page, right sidebar)."""
    enabled: bool = False
    action_code_ids: List[str] = field(default_factory=list)
    payload_mode: str = "full"              # "full" | "summary" | "minimal"
    title: str = "Recommended Actions"
    rendered_text: Optional[str] = None     # Filled by compiler after loading YAMLs


# ---------------------------------------------------------------------------
# Root dashboard specification
# ---------------------------------------------------------------------------

@dataclass
class DashboardSpec:
    """
    Complete, platform-agnostic spec for one use case's reports + model.

    This is the handoff object between the compiler and any adapter.
    """
    use_case_id: str                        # "COM-001"
    domain: str                             # "Commercial"
    title: str                              # Human-readable label
    pages: List[PageSpec] = field(default_factory=list)
    measures: List[MeasureSpec] = field(default_factory=list)
    semantic_model: str = ""                # Target model name: "Commercial.SemanticModel"
    source_bracket: str = ""                # Path to UseCase_Bracket.yaml
    target_adapter: AdapterTarget = AdapterTarget.PBIP
    evidence_table: Optional[EvidenceTableSpec] = None
    action_panel: Optional[ActionPanelSpec] = None
    # Provenance
    generated_at: str = ""
    generator_version: str = "1.0.0"

    def overview_page(self) -> Optional[PageSpec]:
        return next((p for p in self.pages if p.role == PageRole.OVERVIEW), None)

    def detail_page(self) -> Optional[PageSpec]:
        return next((p for p in self.pages if p.role == PageRole.DETAIL), None)

    def measure_by_kpi(self, kpi_id: str) -> Optional[MeasureSpec]:
        return next((m for m in self.measures if m.kpi_id == kpi_id), None)
