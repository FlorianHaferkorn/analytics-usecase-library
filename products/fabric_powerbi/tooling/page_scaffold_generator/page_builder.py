"""
Page Builder

Builds Power BI page structures.
"""

import uuid
from typing import Dict, Any, List, Optional
from .layout_calculator import LayoutCalculator, Position
from .visual_builder import VisualBuilder
from .slicer_builder import SlicerBuilder
import uuid


class PageBuilder:
    """Builds page JSON structures for PBIP format."""
    
    PAGE_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json"
    
    def __init__(self):
        """Initialize page builder."""
        self.layout_calculator = LayoutCalculator()
        self.visual_builder = VisualBuilder()
        self.slicer_builder = SlicerBuilder()
    
    def generate_page_id(self) -> str:
        """Generate unique page ID (20 hex characters)."""
        return uuid.uuid4().hex[:20]
    
    def build_page_metadata(
        self,
        page_id: str,
        display_name: str,
        theme_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build page.json structure.
        
        Args:
            page_id: Unique page ID
            display_name: Page display name
            theme_name: Optional theme name
        
        Returns:
            Page JSON structure
        """
        page = {
            "$schema": self.PAGE_SCHEMA,
            "name": page_id,
            "displayName": display_name,
            "displayOption": "FitToPage",
            "height": self.layout_calculator.CANVAS_HEIGHT,
            "width": self.layout_calculator.CANVAS_WIDTH
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
        
        Returns:
            Dictionary with 'visuals' and 'slicers' lists
        """
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
        
        for i, pos in enumerate(kpi_positions):
            visual = self.visual_builder.build_kpi_card(pos, name=f"KPI_{i + 1}")
            visual["position"]["tabOrder"] = tab_order + i
            visuals.append(visual)

        # 30s layer: from ux_layout_rules — assign slot by visual_type so layout matches intent (e.g. waterfall→variance, trend_line→trend)
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
                name = (item.get("kpi_id") or (", ".join(item.get("kpi_ids") or [])[:30]) or f"Visual_{i + 1}")
                visual = self.visual_builder.build_by_ux_visual_type(vt, pos, name=name)
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
                visual = self.visual_builder.build_table(visual_positions['prescriptive'], name="Prescriptive")
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

            # Detail Matrix visual
            if slots.get('needs_detail_matrix', False) and 'detail_matrix' in visual_positions:
                visual = self.visual_builder.build_table(visual_positions['detail_matrix'], name="DetailMatrix")
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
            teaser_text = "'Action Panel Placeholder'"  # T4
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
                    "query": {"queryState": {"Data": {"projections": []}}},
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
                    "query": {"queryState": {"Data": {"projections": []}}},
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
