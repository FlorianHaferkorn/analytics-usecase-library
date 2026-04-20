"""
tooling/ir — Stable public surface for the tool-agnostic IR types.

Import from here rather than from tooling.generator_core.ir.specs in all
code outside the generator_core package (Studio, OSS adapters, scripts).

    from tooling.ir import DashboardSpec, PageSpec, VisualSpec, MeasureSpec
"""
from tooling.generator_core.ir.specs import (
    ActionPanelSpec,
    AdapterTarget,
    Binding,
    DashboardSpec,
    EvidenceTableSpec,
    MeasureSpec,
    PageRole,
    PageSpec,
    PageType,
    Position,
    VisualSpec,
    VisualType,
)

__all__ = [
    "ActionPanelSpec",
    "AdapterTarget",
    "Binding",
    "DashboardSpec",
    "EvidenceTableSpec",
    "MeasureSpec",
    "PageRole",
    "PageSpec",
    "PageType",
    "Position",
    "VisualSpec",
    "VisualType",
]
