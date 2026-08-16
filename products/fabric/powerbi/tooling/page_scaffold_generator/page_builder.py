"""
Page Builder

Builds Power BI page structures. Supports legacy row-based layout and grid-based layout (Master Grid 12×12).
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from .layout_calculator import LayoutCalculator, Position
from .grid_calculator import GridCalculator, GridPosition
from .visual_builder import VisualBuilder
from .slicer_builder import SlicerBuilder
from .title_policy import resolve_header
from products.fabric.powerbi.tooling.schema_registry import PAGE_SCHEMA as _PAGE_SCHEMA

logger = logging.getLogger(__name__)


class PageBuilder:
    """Builds page JSON structures for PBIP format."""

    PAGE_SCHEMA = _PAGE_SCHEMA
    
    def __init__(self, assert_statement_titles: bool = True):
        """Initialize page builder.

        ``assert_statement_titles`` (title_policy): when True (default, data-backed reports) the
        governed exhibit **message** leads as the visual header (IBCS statement title, authored knowing
        the data). Set False for a report generated **without known data** — then the always-true
        **question** leads and the message renders as a framed *expected-finding* subtitle, so a static
        title can never contradict the chart (see title_policy.py)."""
        self.layout_calculator = LayoutCalculator()
        self.visual_builder = VisualBuilder()
        self.slicer_builder = SlicerBuilder()
        self.assert_statement_titles = assert_statement_titles
    
    def generate_page_id(self) -> str:
        """Generate unique page ID (20 hex characters)."""
        return uuid.uuid4().hex[:20]

    def _build_page_structure_from_grid(
        self,
        grid_blueprint: Dict[str, Any],
        canvas_width: int,
        canvas_height: int,
        card_measure_names: List[str],
        card_kpi_ids: List[str],
        visual_templates: Dict[str, Dict[str, Any]],
        has_action_panel: bool = False,
        action_panel_content: Optional[str] = None,
        detail_matrix_columns: Optional[List[str]] = None,
        detail_matrix_measures: Optional[List[str]] = None,
        smart_narrative_text: Optional[str] = None,
        component_30s: Optional[List[Dict[str, Any]]] = None,
        kpi_id_to_measure_name: Optional[Dict[str, str]] = None,
        big_idea_text: Optional[str] = None,
        detail_matrix_sort_by: Optional[Dict[str, str]] = None,
        detail_matrix_top_n: Optional[int] = None,
        detail_matrix_highlight_rule: Optional[Dict[str, str]] = None,
        detail_matrix_topn_field: Optional[tuple] = None,
        narrative_measure_name: Optional[str] = None,
        active_actions_measure_name: Optional[str] = None,
        semantic_delta_cards: bool = False,
    ) -> Dict[str, Any]:
        """Build page structure from grid blueprint (Master Grid 12×12). All visuals aligned to grid."""
        canvas = grid_blueprint.get("canvas") or {}
        w = canvas.get("width") or canvas_width
        h = canvas.get("height") or canvas_height
        # outer_margin/gutter NICHT mehr durchreichen: der GridCalculator holt sie aus
        # dem governten Raster. Sie hier erneut anzugeben haette die Konsolidierung
        # ausgehebelt — der haeufigste Weg, auf dem eine Dublette zurueckkommt.
        calc = GridCalculator(canvas_width=w, canvas_height=h)
        slots_list = grid_blueprint.get("slots") or []
        visuals: List[Dict[str, Any]] = []
        slicers: List[Dict[str, Any]] = []
        tab = self.visual_builder.tab_order_base
        # Detail_Matrix: resolved dim columns (list of (table,col) tuples) + measure names
        detail_dim_cols = detail_matrix_columns if isinstance(detail_matrix_columns, list) else []
        detail_measures = detail_matrix_measures if detail_matrix_measures is not None else []

        # 30s slot binding: map Main_1/2/3 sequentially to component_30s items
        # component_30s[0] → Main_1, component_30s[1] → Main_2, component_30s[2] → Main_3
        _MAIN_SLOTS_ORDER = ["Main_1", "Main_2", "Main_3"]
        _kpi_to_measure = kpi_id_to_measure_name or {}
        _c30s = component_30s if isinstance(component_30s, list) else []
        _main_slot_binding: Dict[str, Dict[str, Any]] = {}
        for _idx, _c_item in enumerate(_c30s):
            if _idx >= len(_MAIN_SLOTS_ORDER):
                break
            _slot_name = _MAIN_SLOTS_ORDER[_idx]
            _vt = _c_item.get("visual_type") or "trend_line"
            _kid = _c_item.get("kpi_id")
            _kids = _c_item.get("kpi_ids") or ([_kid] if _kid else [])
            if not isinstance(_kids, list):
                _kids = [_kids] if _kids else []
            _measures = [_kpi_to_measure.get(k, k) for k in _kids if isinstance(k, str) and k.strip()]
            # category_field from bracket: "table.Column" → split into entity/property
            _cat_field = _c_item.get("category_field")
            _cat_entity, _cat_prop = None, None
            if _cat_field and isinstance(_cat_field, str) and "." in _cat_field:
                _cat_entity, _cat_prop = _cat_field.split(".", 1)
            _main_slot_binding[_slot_name] = {
                "visual_type": _vt,
                "measures": _measures,
                "category_entity": _cat_entity,
                "category_property": _cat_prop,
                # BC-NARR-01 (K2): the governed exhibit statement + the question it answers.
                # title_policy decides which becomes the static header (question by default).
                "message": (_c_item.get("message") or "").strip() or None,
                "question": (_c_item.get("question") or "").strip() or None,
            }

        # Detect absolute-position mode (Figma-sourced layouts)
        position_mode = grid_blueprint.get("position_mode", "grid")

        for i, slot_def in enumerate(slots_list):
            slot_id = slot_def.get("slot_id") or f"Slot_{i}"

            # Resolve position: absolute (Figma) or grid (12×12 GridCalculator)
            if position_mode == "absolute":
                abs_pos = slot_def.get("position") or {}
                if not abs_pos:
                    continue
                position = Position(
                    x=abs_pos.get("x", 0),
                    y=abs_pos.get("y", 0),
                    width=abs_pos.get("width", 100),
                    height=abs_pos.get("height", 100),
                )
            else:
                grid = slot_def.get("grid")
                if not grid or len(grid) != 4:
                    continue
                col_start, row_start, col_span, row_span = grid[0], grid[1], grid[2], grid[3]
                pos = calc.calculate_visual_rect(col_start, row_start, col_span, row_span)
                position = Position(x=pos.x, y=pos.y, width=pos.width, height=pos.height)

            if slot_id == "ActionPanel":
                if has_action_panel:
                    if active_actions_measure_name:
                        # R2.3-Fund follow-up: real dist/ binds ActionPanel to the
                        # governed domain-level "Active Actions Text (<SUFFIX>)"
                        # measure (auto-reads current filter context), not a
                        # generator-synthesized literal action-code dump.
                        vis = self.visual_builder.build_narrative_card(
                            position, measure_ref=active_actions_measure_name, name="ActionPanel"
                        )
                        vis["position"]["z"] = 15000
                    else:
                        text_value = (action_panel_content or "'Action Panel Placeholder'")
                        vis = {
                            "$schema": self.visual_builder.VISUAL_SCHEMA,
                            "name": "ActionPanel",
                            "position": {
                                "x": position.x,
                                "y": position.y,
                                "z": 15000,
                                "height": position.height,
                                "width": position.width,
                                "tabOrder": tab + i
                            },
                            "visual": {
                                "visualType": "textbox",
                                "objects": {
                                    "text": [
                                        {
                                            "properties": {
                                                "text": {
                                                    "expr": {"Literal": {"Value": text_value}}
                                                }
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    vis["position"]["tabOrder"] = tab + i
                    visuals.append(vis)
                continue

            visual_type_hint = slot_def.get("visual_type_hint")
            vt_template = None
            for _vid, vdef in visual_templates.items():
                if slot_id in (vdef.get("slot_compatibility") or []):
                    vt_template = vdef
                    break
            visual_type = (
                (vt_template or {}).get("visual_type")
                or visual_type_hint
                or "cardVisual"
            )

            if visual_type == "slicer":
                sl = self.slicer_builder.build_time_slicer(position, name=slot_id)
                sl["position"]["tabOrder"] = tab + i
                slicers.append(sl)
                continue

            if visual_type == "slicer_entity":
                # Entity slicer (OrgName) for filtering Detail pages by business unit
                sl = self.slicer_builder.build_categorical_slicer(position, field="dim_org.OrgName", name=slot_id)
                sl["position"]["tabOrder"] = tab + i
                slicers.append(sl)
                continue

            if visual_type == "slicer_region":
                # Region slicer for Overview cross-filter (dim_org.Region)
                sl = self.slicer_builder.build_categorical_slicer(position, field="dim_org.Region", name=slot_id)
                sl["position"]["tabOrder"] = tab + i
                slicers.append(sl)
                continue

            if visual_type == "slicer_product":
                # Product Category slicer for Overview cross-filter (dim_product.Category)
                sl = self.slicer_builder.build_categorical_slicer(position, field="dim_product.Category", name=slot_id)
                sl["position"]["tabOrder"] = tab + i
                slicers.append(sl)
                continue

            # 30s chart slots (Main_1/2/3): use component_30s binding when available;
            # fallback for unbound main slots: clusteredBarChart with KPI card measures (ranking view)
            if slot_id in _main_slot_binding:
                _binding = _main_slot_binding[slot_id]
                _ux_vt = _binding["visual_type"]
                _measures = _binding["measures"]
                # Label for naming/tooltip; the governed statement (message) renders as the header (BC-NARR-01).
                _label = (_measures[0] if len(_measures) == 1 else slot_id).replace("_", " ").replace(".", " ")
                _cat_entity = _binding.get("category_entity")
                _cat_prop = _binding.get("category_property")
                # title_policy: question leads the static header; message = framed expected-finding
                # subtitle (unless value-verified/dynamic — wired via value_verified when available).
                _hdr, _sub = resolve_header(_binding.get("question"), _binding.get("message"),
                                            value_verified=self.assert_statement_titles)
                vis = self.visual_builder.build_by_ux_visual_type(
                    _ux_vt, position, name=slot_id, measures=_measures, title=_label,
                    statement_title=_hdr, subtitle=_sub,
                    category_entity=_cat_entity, category_property=_cat_prop,
                )
                # R2.3: Main_3 is canonically the Ranking slot (Design_Spec_3_30_300.md
                # §5.3) -- a single-measure ranking visual is meaningless unsorted, so
                # apply descending sort by its own measure automatically. This is a
                # structural default (implied by the slot's canonical purpose), not a
                # per-report Bracket declaration -- component_30s has no sort_by field.
                if slot_id == "Main_3" and len(_measures) == 1:
                    vis.setdefault("visual", {}).setdefault("query", {})["sortDefinition"] = {
                        "sort": [
                            {
                                "field": {
                                    "Measure": {
                                        "Expression": {"SourceRef": {"Entity": "_Measures"}},
                                        "Property": _measures[0],
                                    }
                                },
                                "direction": "Descending",
                            }
                        ],
                        "isDefaultSort": True,
                    }
            elif slot_id in _MAIN_SLOTS_ORDER:
                # Ungebundener Main-Slot -> KEIN Visual. Bis 01.08.2026 stand hier ein
                # Fallback, der die ersten vier KPI-Card-Measures auf eine Balkenachse
                # legte ("KPI by Entity"). Das war erfundener Report-Inhalt: kein Bracket
                # deklariert ihn, der Titel war hartkodiert, und die vier Measures
                # stammten aus verschiedenen Skalenfamilien (%, Tage, Waehrung).
                #
                # Zwei Pruefer meldeten dieselbe Wurzel: der Scorecard-Knock-out
                # `mixed-scale` auf Main_3 und `PBIR_ROLE_MAX_EXCEEDED` (Rolle Y mit
                # 2-5 Projektionen, max 1). Die Triage hatte daraus geschlossen, zwoelf
                # Use Cases muessten ein `component_30s[2]` nachdeklarieren — das war die
                # falsche Richtung. Der Golden Thread sagt: das Bracket ist die Autoritaet.
                # Deklariert es zwei Exponate, hat die Uebersicht zwei Exponate.
                #
                # Folge: bei zwei deklarierten Komponenten bleibt die Main_3-Flaeche im
                # Raster leer. Das ist die ehrliche Darstellung eines nicht kuratierten
                # Slots — sichtbar statt mit Fuellmaterial kaschiert.
                logger.info(
                    "Slot %s ohne governte Bindung (component_30s deklariert %d Eintrag/Eintraege) "
                    "— kein Visual emittiert; Inhalt waere nicht governt.",
                    slot_id, len(_c30s),
                )
                continue
            elif slot_id == "KPI_Cards" and visual_type == "cardVisual":
                # Semantic-delta band (intent v2): a variance/vs-plan KPI can't be colour-coded
                # inside the multi-value card (callouts format uniformly — card.md), so split it
                # out as its own single-value card coloured by sign. The level KPIs stay in the
                # multi-value card. Detected by governed kpi_id (…vs_plan… / …delta_pct…).
                _var_idx = None
                if semantic_delta_cards and card_kpi_ids:
                    for _j, _kid in enumerate(card_kpi_ids):
                        if isinstance(_kid, str) and (".vs_plan." in _kid or ".delta_pct." in _kid):
                            _var_idx = _j
                            break
                if _var_idx is not None and _var_idx < len(card_measure_names):
                    _delta_measure = card_measure_names[_var_idx]
                    _level_measures = [m for _k, m in enumerate(card_measure_names) if _k != _var_idx]
                    _gap, _delta_w = 16, 452
                    _levels_w = max(1, position.width - _delta_w - _gap)
                    _levels_pos = Position(x=position.x, y=position.y, width=_levels_w, height=position.height)
                    _delta_pos = Position(x=position.x + _levels_w + _gap, y=position.y,
                                          width=_delta_w, height=position.height)
                    _levels = self.visual_builder.build_kpi_cards_multi(
                        _levels_pos, _level_measures, name="KPI_Cards", title=None
                    )
                    _levels["position"]["tabOrder"] = tab + i
                    visuals.append(_levels)
                    vis = self.visual_builder.build_kpi_delta_card(
                        _delta_pos, _delta_measure, name="KPI_Delta", label=_delta_measure,
                        higher_is_better=True,
                    )
                else:
                    vis = self.visual_builder.build_kpi_cards_multi(
                        position, card_measure_names or [], name=slot_id, title=None
                    )
            elif visual_type == "cardVisual":
                measure_ref = (card_measure_names[0] if card_measure_names else None) or (card_kpi_ids[0] if card_kpi_ids else None)
                title = (card_kpi_ids[0] if card_kpi_ids else measure_ref or slot_id).replace(".", " ").replace("_", " ").title() if (card_kpi_ids or card_measure_names) else None
                vis = self.visual_builder.build_kpi_card(position, measure_ref=measure_ref, name=slot_id, title=title)
            elif visual_type == "textbox" and narrative_measure_name:
                # R2.3-Fund follow-up: real dist/ binds Smart_Narrative to the
                # governed domain-level "Narrative Text (<SUFFIX>)" measure
                # (auto-reads current filter context), not a generator-
                # synthesized literal string.
                vis = self.visual_builder.build_narrative_card(
                    position, measure_ref=narrative_measure_name, name=slot_id
                )
                vis["position"]["tabOrder"] = tab + i
            elif visual_type == "textbox":
                vis = self.visual_builder._build_base_visual("textbox", position, tab_order=tab + i, name=slot_id)
                _sn_raw = smart_narrative_text or "Filtering active – review current selection."
                _sn_escaped = _sn_raw.replace("'", "''")
                vis["visual"]["objects"] = {"text": [{"properties": {"text": {"expr": {"Literal": {"Value": f"'{_sn_escaped}'"}}}}}]}
            elif visual_type == "tableEx" and slot_id == "Detail_Matrix":
                vis = self.visual_builder.build_table(
                    position, columns=detail_dim_cols, measures=detail_measures, name=slot_id,
                    sort_by=detail_matrix_sort_by, top_n=detail_matrix_top_n,
                    top_n_field=detail_matrix_topn_field, highlight_rule=detail_matrix_highlight_rule,
                )
            elif visual_type == "tableEx":
                vis = self.visual_builder.build_table(position, columns=[], measures=[], name=slot_id)
            elif visual_type == "lineChart":
                _fb = (card_measure_names[:2] or None)
                vis = self.visual_builder.build_line_chart(position, name=slot_id, measures=_fb)
            elif visual_type == "pivotTable":
                _fb = (card_measure_names[:4] or None)
                vis = self.visual_builder.build_matrix(position, measures=_fb, name=slot_id)
            elif visual_type == "scatterChart":
                _fb = (card_measure_names[:2] or None)
                vis = self.visual_builder.build_scatter_plot(position, name=slot_id, measures=_fb)
            elif visual_type == "funnelChart":
                _fb = (card_measure_names[:1] or None)
                vis = self.visual_builder.build_funnel(position, name=slot_id, measures=_fb)
            elif visual_type in ("clusteredBarChart", "clusteredColumnChart"):
                _fb = (card_measure_names[:4] or None)
                vis = self.visual_builder.build_horizontal_bar(position, name=slot_id, measures=_fb)
            elif visual_type in ("hundredPercentStackedBarChart", "hundredPercentStackedColumnChart",
                                 "stackedBarChart", "stackedColumnChart"):
                _fb = (card_measure_names[:4] or None)
                vis = self.visual_builder.build_stacked_bar(position, name=slot_id, measures=_fb)
            elif visual_type == "waterfallChart":
                _fb = (card_measure_names[:1] or None)
                vis = self.visual_builder.build_waterfall(position, name=slot_id, measures=_fb)
            else:
                # Unknown visual type: use base structure (no queryState).
                # Validator will flag if the type is in VISUAL_TYPE_ROLES.
                vis = self.visual_builder._build_base_visual(visual_type, position, tab_order=tab + i, name=slot_id)
            vis["position"]["tabOrder"] = tab + i
            visuals.append(vis)

        if big_idea_text:
            # R2.3 / BIG_IDEA_HEADER_ZONE (design_rules.yaml): Header (Zone 0, above the
            # KPI band) renders page_1_summary.big_idea verbatim. Fixed absolute
            # position -- Zone 0 sits above the grid's slot area, not inside it.
            # Position/tabOrder match the R1.1 precedent (COM-002 Header, hand-applied
            # before this generator path existed).
            _big_idea_escaped = big_idea_text.replace("'", "''")
            visuals.append(
                {
                    "$schema": self.visual_builder.VISUAL_SCHEMA,
                    "name": "Header",
                    "position": {"x": 32, "y": 32, "z": 10000, "height": 56, "width": 1856, "tabOrder": 2999},
                    "visual": {
                        "visualType": "textbox",
                        "objects": {
                            "text": [
                                {"properties": {"text": {"expr": {"Literal": {"Value": f"'{_big_idea_escaped}'"}}}}}
                            ]
                        },
                    },
                }
            )

        return {"visuals": visuals, "slicers": slicers, "action_panel": None}

    def build_page_metadata(
        self,
        page_id: str,
        display_name: str,
        theme_name: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        is_drillthrough_target: bool = False,
    ) -> Dict[str, Any]:
        """
        Build page.json structure.
        
        Args:
            page_id: Unique page ID
            display_name: Page display name
            theme_name: Optional theme name
            width: Optional canvas width (default from layout_calculator)
            height: Optional canvas height (default from layout_calculator)
            is_drillthrough_target: If True, page is also a Drillthrough target (type, visibility, pageBinding).
        
        Returns:
            Page JSON structure
        """
        w = width if width is not None else self.layout_calculator.CANVAS_WIDTH
        h = height if height is not None else self.layout_calculator.CANVAS_HEIGHT
        page = {
            "$schema": self.PAGE_SCHEMA,
            "name": page_id,
            "displayName": display_name,
            "displayOption": "FitToPage",
            "height": h,
            "width": w,
        }
        if is_drillthrough_target:
            page["type"] = "Drillthrough"
            page["visibility"] = "AlwaysVisible"
            page["pageBinding"] = {
                "name": "Detail_Drillthrough",
                "type": "Drillthrough",
                "referenceScope": "Default",
                "acceptsFilterContext": "Default",
            }
        return page
    
    def build_page_structure(
        self,
        slots: Dict[str, bool],
        template: str,
        has_action_panel: bool = False,
        visual_slot_mapping: Optional[Dict[str, Any]] = None,
        component_30s: Optional[List[Dict[str, Any]]] = None,
        slot_order: Optional[List[str]] = None,
        card_kpi_ids: Optional[List[str]] = None,
        card_measure_names: Optional[List[str]] = None,
        kpi_id_to_measure_name: Optional[Dict[str, str]] = None,
        action_panel_content: Optional[str] = None,
        grid_blueprint: Optional[Dict[str, Any]] = None,
        canvas_width: Optional[int] = None,
        canvas_height: Optional[int] = None,
        visual_templates: Optional[Dict[str, Dict[str, Any]]] = None,
        detail_matrix_columns: Optional[List[str]] = None,
        detail_matrix_measures: Optional[List[str]] = None,
        smart_narrative_text: Optional[str] = None,
        big_idea_text: Optional[str] = None,
        detail_matrix_sort_by: Optional[Dict[str, str]] = None,
        detail_matrix_top_n: Optional[int] = None,
        detail_matrix_highlight_rule: Optional[Dict[str, str]] = None,
        detail_matrix_topn_field: Optional[tuple] = None,
        narrative_measure_name: Optional[str] = None,
        active_actions_measure_name: Optional[str] = None,
        semantic_delta_cards: bool = False,
    ) -> Dict[str, Any]:
        """
        Build complete page structure with visuals.

        Args:
            slots: Dictionary of slot activations
            template: Template type (T1, T2, T3, T4)
            has_action_panel: Whether Action Panel is present
            visual_slot_mapping: Visual-to-slot mapping configuration
            component_30s: Optional list from ux_layout_rules (each has visual_type, kpi_id/kpi_ids). When set with slot_order, exact visual type per position is used.
            slot_order: Optional list of layout slot names (e.g. ["trend", "variance"]) matching component_30s order.
            card_kpi_ids: Optional list of KPI IDs for KPI cards (for titles/fallback).
            card_measure_names: Optional list of DAX measure names for KPI cards (must match semantic model); used for measure binding when provided.
            kpi_id_to_measure_name: Optional map kpi_id -> measure name for resolving component_30s kpi_ids to DAX measure names.
            action_panel_content: Optional preformatted text for T4 Action Panel (from action codes); used when has_action_panel and template T4.
            grid_blueprint: Optional grid page template (template_id, canvas, slots with slot_id, grid, visual_type_hint). When set, uses Master Grid for positions.
            canvas_width: Optional canvas width (used with grid_blueprint; default 1920).
            canvas_height: Optional canvas height (used with grid_blueprint; default 1080).
            visual_templates: Optional dict of visual_template_id -> visual template (used with grid_blueprint for visual type).
            detail_matrix_columns: Optional list of (table,col) tuples for Detail_Matrix.
            detail_matrix_measures: Optional list of measure names for Detail_Matrix.
            smart_narrative_text: Optional context text for Smart_Narrative textbox on detail page.
            big_idea_text: Optional page_1_summary.big_idea text (R2.1/R2.3) -- renders as the
                Header (Zone 0) textbox, verbatim, when set. Grid path only.
            detail_matrix_sort_by: Optional {"measure","direction"} for Detail_Matrix (R2.1/R2.3).
            detail_matrix_top_n: Optional row limit for Detail_Matrix (R2.1/R2.3).
            detail_matrix_highlight_rule: Optional {"measure","type"} for Detail_Matrix (R2.1/R2.3).
            detail_matrix_topn_field: Optional (entity, property) tuple, the TopN filter's grain column.
            narrative_measure_name: Optional governed "Narrative Text (<SUFFIX>)" DAX measure name;
                when set, Smart_Narrative binds to it (cardVisual) instead of a synthesized textbox.
            active_actions_measure_name: Optional governed "Active Actions Text (<SUFFIX>)" DAX
                measure name; when set, ActionPanel binds to it (cardVisual) instead of a
                synthesized textbox.

        Returns:
            Dictionary with 'visuals' and 'slicers' lists
        """
        # Grid path: build from grid_blueprint when provided (Baukasten)
        if grid_blueprint:
            return self._build_page_structure_from_grid(
                grid_blueprint=grid_blueprint,
                canvas_width=canvas_width or 1920,
                canvas_height=canvas_height or 1080,
                card_measure_names=card_measure_names or [],
                card_kpi_ids=card_kpi_ids or [],
                visual_templates=visual_templates or {},
                has_action_panel=has_action_panel,
                action_panel_content=action_panel_content,
                detail_matrix_columns=detail_matrix_columns,
                detail_matrix_measures=detail_matrix_measures,
                smart_narrative_text=smart_narrative_text,
                component_30s=component_30s,
                kpi_id_to_measure_name=kpi_id_to_measure_name,
                big_idea_text=big_idea_text,
                detail_matrix_sort_by=detail_matrix_sort_by,
                detail_matrix_top_n=detail_matrix_top_n,
                detail_matrix_highlight_rule=detail_matrix_highlight_rule,
                detail_matrix_topn_field=detail_matrix_topn_field,
                narrative_measure_name=narrative_measure_name,
                active_actions_measure_name=active_actions_measure_name,
                semantic_delta_cards=semantic_delta_cards,
            )

        # Determine slicer placement (default: top)
        has_side_slicers = False  # Can be made configurable

        # T2 can show Action Teaser (slim textbox); reserve content width 1510 like panel
        use_teaser = template == "T2" and slots.get("action_teaser", True)
        effective_has_panel = has_action_panel or use_teaser

        # KPI count (configurable; default 4)
        kpi_count = 4  # Can be made configurable or read from use case config
        has_top_slicer = not slots.get("exclude_time_slicer", False)

        # Adaptive layout: single source of truth for PBIP and mockup (3-30-300: KPI then slicer then drivers)
        layout_bounds = self.layout_calculator.compute_adaptive_bounds(
            slots=slots,
            template=template,
            has_action_panel=effective_has_panel,
            kpi_count=kpi_count,
            has_top_slicer=has_top_slicer,
        )

        # Calculate visual positions (using adaptive bounds)
        visual_positions = self.layout_calculator.calculate_visual_positions(
            slots=slots,
            template=template,
            has_action_panel=effective_has_panel,
            has_side_slicers=has_side_slicers,
            layout_bounds=layout_bounds,
        )

        # Build visuals
        visuals = []
        tab_order = self.visual_builder.tab_order_base

        kpi_positions = self.layout_calculator.calculate_kpi_card_positions(kpi_count)
        card_kpi_ids = card_kpi_ids or []
        card_measure_names = card_measure_names or []
        for i, pos in enumerate(kpi_positions):
            # Binding: DAX measure name (card_measure_names); title from kpi_id if available
            measure_ref = (card_measure_names[i] if i < len(card_measure_names) else None) or (card_kpi_ids[i] if i < len(card_kpi_ids) else None)
            title_ref = card_kpi_ids[i] if i < len(card_kpi_ids) else measure_ref
            title = title_ref.replace(".", " ").replace("_", " ").title() if title_ref else None
            visual = self.visual_builder.build_kpi_card(
                pos, measure_ref=measure_ref, name=f"KPI_{i + 1}", title=title
            )
            visual["position"]["tabOrder"] = tab_order + i
            visuals.append(visual)

        # 30s layer: from ux_layout_rules — assign slot by slot_id (Main_1/2/3) when set, else by visual_type
        _SLOT_ID_TO_POSITION = {"Main_1": "trend", "Main_2": "variance", "Main_3": "ranking"}
        _UX_VISUAL_TYPE_TO_SLOT = {
            "trend_line": "trend",
            "waterfall": "variance",
            "bar_chart": "ranking",
            "stacked_bar": "mix",
            "hundred_percent_stacked_bar": "mix",
            "funnel": "funnel",
        }
        if component_30s and len(component_30s) > 0:
            fallback_slot_order = (slot_order or ["trend", "variance"])
            fallback_slot_order = [s.lower() for s in fallback_slot_order]
            slots_used = set()
            for i, item in enumerate(component_30s):
                vt = item.get("visual_type") or "trend_line"
                explicit_slot_id = (item.get("slot_id") or "").strip()
                if explicit_slot_id in _SLOT_ID_TO_POSITION and _SLOT_ID_TO_POSITION[explicit_slot_id] in visual_positions:
                    preferred_slot = _SLOT_ID_TO_POSITION[explicit_slot_id]
                else:
                    preferred_slot = _UX_VISUAL_TYPE_TO_SLOT.get(vt, "trend")
                slot_key = preferred_slot
                if preferred_slot in slots_used or preferred_slot not in visual_positions:
                    for s in fallback_slot_order:
                        if s in visual_positions and s not in slots_used:
                            slot_key = s
                            break
                    else:
                        continue
                if slot_key not in visual_positions:
                    continue
                slots_used.add(slot_key)
                pos = visual_positions[slot_key]
                kpi_id = item.get("kpi_id")
                kpi_ids = item.get("kpi_ids") or ([kpi_id] if kpi_id else [])
                if not isinstance(kpi_ids, list):
                    kpi_ids = [kpi_ids] if kpi_ids else []
                kpi_ids_clean = [x for x in kpi_ids if isinstance(x, str) and x.strip()]
                # Resolve to DAX measure names for visual binding (semantic model uses measure names, not KPI IDs)
                kpi_to_measure = kpi_id_to_measure_name or {}
                measures = [kpi_to_measure.get(k, k) for k in kpi_ids_clean]
                # Label for naming/tooltip; the governed statement (message) renders as the header (BC-NARR-01).
                display_title = measures[0] if len(measures) == 1 else (", ".join(measures[:3])[:40] if measures else f"Visual_{i + 1}")
                title = display_title.replace(".", " ").replace("_", " ").title()
                _hdr2, _sub2 = resolve_header(item.get("question"), item.get("message"),
                                              value_verified=self.assert_statement_titles)
                # Visual name must be folder-safe (no commas, no chars invalid in paths) so Fabric loads the visual
                raw_name = measures[0] if len(measures) == 1 else (", ".join(measures[:3])[:40] if measures else f"Visual_{i + 1}")
                if "," in raw_name or ":" in raw_name or "\\" in raw_name or "/" in raw_name:
                    name = slot_key.capitalize() + (f"_{i}" if i > 0 else "")
                else:
                    name = raw_name
                visual = self.visual_builder.build_by_ux_visual_type(
                    vt, pos, name=name, measures=measures, title=title,
                    statement_title=_hdr2, subtitle=_sub2
                )
                visual["position"]["tabOrder"] = tab_order + 100 + i * 100
                visuals.append(visual)
        else:
            # Trend visual
            if slots.get('needs_trend', False) and 'trend' in visual_positions:
                visual = self.visual_builder.build_line_chart(visual_positions['trend'], name="Trend")
                visual["position"]["tabOrder"] = tab_order + 100
                visuals.append(visual)

            # Variance visual
            if slots.get('needs_variance', False) and 'variance' in visual_positions:
                visual = self.visual_builder.build_waterfall(visual_positions['variance'], name="Variance")
                visual["position"]["tabOrder"] = tab_order + 200
                visuals.append(visual)

            # Ranking visual
            if slots.get('needs_ranking', False) and 'ranking' in visual_positions:
                visual = self.visual_builder.build_horizontal_bar(visual_positions['ranking'], name="Ranking")
                visual["position"]["tabOrder"] = tab_order + 300
                visuals.append(visual)

            # Mix visual
            if slots.get('needs_mix', False) and 'mix' in visual_positions:
                visual = self.visual_builder.build_stacked_bar(visual_positions['mix'], name="Mix")
                visual["position"]["tabOrder"] = tab_order + 400
                visuals.append(visual)

            # Exceptions visual
            if slots.get('needs_exceptions', False) and 'exceptions' in visual_positions:
                visual = self.visual_builder.build_table(visual_positions['exceptions'], name="Exceptions")
                visual["position"]["tabOrder"] = tab_order + 500
                visuals.append(visual)

            # Prescriptive visual
            if slots.get('needs_prescriptive', False) and 'prescriptive' in visual_positions:
                visual = self.visual_builder.build_table(
                    visual_positions['prescriptive'],
                    columns=[("dim_date", "Date"), ("dim_product", "ProductName")],
                    measures=["Net Sales Amount"],
                    name="Prescriptive",
                )
                visual["position"]["tabOrder"] = tab_order + 600
                visuals.append(visual)

            # Root Cause visual
            if slots.get('needs_root_cause', False) and 'root_cause' in visual_positions:
                visual = self.visual_builder.build_scatter_plot(visual_positions['root_cause'], name="RootCause")
                visual["position"]["tabOrder"] = tab_order + 700
                visuals.append(visual)

            # Funnel visual
            if slots.get('needs_funnel', False) and 'funnel' in visual_positions:
                visual = self.visual_builder.build_funnel(visual_positions['funnel'], name="Funnel")
                visual["position"]["tabOrder"] = tab_order + 800
                visuals.append(visual)

            # Detail Matrix visual — use evidence columns/measures from bracket if available
            if slots.get('needs_detail_matrix', False) and 'detail_matrix' in visual_positions:
                dm_cols = list(detail_matrix_columns) if detail_matrix_columns else [("dim_date", "Date"), ("dim_product", "ProductName")]
                dm_meas = list(detail_matrix_measures) if detail_matrix_measures else ["Net Sales Amount", "Gross Margin %"]
                visual = self.visual_builder.build_table(
                    visual_positions['detail_matrix'],
                    columns=dm_cols,
                    measures=dm_meas,
                    name="DetailMatrix",
                )
                visual["position"]["tabOrder"] = tab_order + 900
                visuals.append(visual)

        # Build slicers (default: time slicer) — speaking names
        slicers = []
        slicer_tab_order = self.slicer_builder.tab_order_base

        if not slots.get('exclude_time_slicer', False):
            slicer_positions = self.layout_calculator.calculate_slicer_positions(
                slicers=[{"type": "time"}],
                placement="top",
                y_start=layout_bounds.get("slicer_y_start"),
            )
            if slicer_positions:
                slicer = self.slicer_builder.build_time_slicer(slicer_positions[0], name="Slicer_Date")
                slicer["position"]["tabOrder"] = slicer_tab_order
                slicers.append(slicer)

        # Action Panel (T4) or Action Teaser (T2 per ActionPanel_Spec)
        action_panel_visual = None
        if has_action_panel:
            teaser_text = (action_panel_content if action_panel_content else "'Action Panel Placeholder'")  # T4
            if template == "T2":
                teaser_text = "'Key actions from variance → see Detail or T4'"  # T2 Teaser
            action_panel_pos = self.layout_calculator.calculate_action_panel_position()
            action_panel_visual = {
                "$schema": self.visual_builder.VISUAL_SCHEMA,
                "name": "ActionPanel",
                "position": {
                    "x": action_panel_pos.x,
                    "y": action_panel_pos.y,
                    "z": 15000,
                    "height": action_panel_pos.height,
                    "width": action_panel_pos.width,
                    "tabOrder": 10000
                },
                "visual": {
                    "visualType": "textbox",
                    "objects": {
                        "text": [
                            {
                                "properties": {
                                    "text": {
                                        "expr": {
                                            "Literal": {
                                                "Value": teaser_text
                                            }
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            }
            visuals.append(action_panel_visual)
        elif template == "T2" and slots.get("action_teaser", True):
            # T2: slim Action Teaser at same position (content width 1510)
            action_panel_pos = self.layout_calculator.calculate_action_panel_position()
            action_panel_visual = {
                "$schema": self.visual_builder.VISUAL_SCHEMA,
                "name": "ActionPanel",
                "position": {
                    "x": action_panel_pos.x,
                    "y": action_panel_pos.y,
                    "z": 15000,
                    "height": action_panel_pos.height,
                    "width": action_panel_pos.width,
                    "tabOrder": 10000
                },
                "visual": {
                    "visualType": "textbox",
                    "objects": {
                        "text": [
                            {
                                "properties": {
                                    "text": {
                                        "expr": {
                                            "Literal": {
                                                "Value": "'Key actions from variance → see Detail or T4'"
                                            }
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            }
            visuals.append(action_panel_visual)

        return {
            "visuals": visuals,
            "slicers": slicers,
            "action_panel": action_panel_visual
        }
