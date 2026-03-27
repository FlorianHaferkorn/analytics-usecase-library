"""
Golden Thread Discovery Studio – State model.

DiscoverySession is the single source of truth for Tree and YAML.
UseCaseDraft mirrors UseCase_Bracket schema (schema_version 2.0) plus status and optional source_refs.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict


# --- UseCaseDraft: Bracket-equivalent with status and optional traceability ---

class Governance(TypedDict, total=False):
    owner_role: str
    steward_role: str


class Orchestration(TypedDict, total=False):
    strategic_kpi_id: str
    influencing_kpi_ids: List[str]
    supporting_kpi_ids: List[str]
    action_code_ids: List[str]


class ValueDriverModel(TypedDict, total=False):
    formula: str
    impact_direction: Literal["maximize", "minimize"]
    primary_driver: str
    impact_logic: str
    critical_threshold: float


class Documentation(TypedDict, total=False):
    business_factsheet: str


# Minimal ux_layout_rules for schema compliance (required keys only)
class Component3s(TypedDict):
    kpi_id: str
    visual_type: str


class Component30(TypedDict, total=False):
    kpi_id: str
    kpi_ids: List[str]
    visual_type: str
    slot_id: str


class Page1Summary(TypedDict, total=False):
    title: str
    template_id: str
    component_3s: Component3s
    component_30s: List[Component30]


class Component300s(TypedDict, total=False):
    evidence_grain: str
    evidence_columns: List[str]
    evidence_measures: List[str]
    action_panel: bool
    payload_mode: str


class Page2Execution(TypedDict, total=False):
    title: str
    template_id: str
    component_300s: Component300s


class UxLayoutRules(TypedDict, total=False):
    report_structure: str
    report_canvas: Dict[str, int]
    page_1_summary: Page1Summary
    page_2_execution: Page2Execution


class SourceRef(TypedDict, total=False):
    source_id: str
    excerpt: str
    line: Optional[int]


class SourceRefsMap(TypedDict, total=False):
    strategic_kpi_id: SourceRef
    influencing_kpi_ids: List[SourceRef]
    action_code_ids: List[SourceRef]


class UseCaseDraft(TypedDict, total=False):
    """One use case in the session; aligns with UseCase_Bracket.yaml (schema 2.0)."""
    schema_version: str
    id: str
    title: str
    domain: str
    governance: Governance
    orchestration: Orchestration
    value_driver_model: ValueDriverModel
    ux_layout_rules: UxLayoutRules
    documentation: Documentation
    overrides: Dict[str, Any]

    # Studio-only
    status: Literal["draft", "approved"]
    source_refs: SourceRefsMap


# --- Catalog snapshot (read-only per session) ---

class CatalogSnapshot(TypedDict):
    kpi_ids: List[str]
    action_code_ids: List[str]


# --- Brownfield: imported artefacts and mappings ---

class ImportedArtefact(TypedDict, total=False):
    id: str
    type: str  # e.g. "kpi", "report", "semantic_model"
    name: str
    raw: Any


# import_id -> framework_id or "suggested_new"
Mappings = Dict[str, str]


# --- Source: document/URL for grounding (NotebookLM-style) ---

class Source(TypedDict, total=False):
    """One source (URL or uploaded file) for Discovery Chat grounding."""
    id: str
    type: str  # "url" | "pdf" | "file"
    name: str
    content_or_url: str
    chunks: List[str]
    include_in_chat: bool  # hook up/down: when True, source is used for strategy/chat context


# --- DiscoverySession: global state ---

class ChatMessage(TypedDict, total=False):
    role: Literal["user", "assistant"]
    content: str


class DiscoverySession(TypedDict, total=False):
    """Single source of truth for Tree and YAML. All views read/write this."""
    sources: List[Dict[str, Any]]  # list of Source-like dicts: id, type, name, content_or_url, include_in_chat
    chat_messages: List[Dict[str, Any]]  # list of { role, content } for Discovery Chat
    strategy_anchors: List[str]
    use_cases: List[UseCaseDraft]
    catalog_snapshot: CatalogSnapshot
    selected_use_case_id: Optional[str]
    project_mode: Literal["greenfield", "brownfield"]
    imported_artefacts: List[ImportedArtefact]
    mappings: Mappings
