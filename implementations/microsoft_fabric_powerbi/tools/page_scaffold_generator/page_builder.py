"""
Page Builder

Builds Power BI page structures.
"""

import uuid
from typing import Dict, Any, Optional
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
        visual_slot_mapping: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build complete page structure with visuals.
        
        Args:
            slots: Dictionary of slot activations
            template: Template type (T1, T2, T3, T4)
            has_action_panel: Whether Action Panel is present
            visual_slot_mapping: Visual-to-slot mapping configuration
        
        Returns:
            Dictionary with 'visuals' and 'slicers' lists
        """
        # Determine slicer placement (default: top)
        has_side_slicers = False  # Can be made configurable
        
        # Calculate visual positions
        visual_positions = self.layout_calculator.calculate_visual_positions(
            slots=slots,
            template=template,
            has_action_panel=has_action_panel,
            has_side_slicers=has_side_slicers
        )
        
        # Build visuals
        visuals = []
        tab_order = self.visual_builder.tab_order_base
        
        # KPI Cards (always present on overview pages, optional on detail)
        # Determine number of KPI cards from use case (default: 4)
        kpi_count = 4  # Can be made configurable or read from use case config
        kpi_positions = self.layout_calculator.calculate_kpi_card_positions(kpi_count)
        
        for i, pos in enumerate(kpi_positions):
            visual = self.visual_builder.build_kpi_card(pos)
            visual["position"]["tabOrder"] = tab_order + i
            visuals.append(visual)
        
        # Trend visual
        if slots.get('needs_trend', False) and 'trend' in visual_positions:
            visual = self.visual_builder.build_line_chart(visual_positions['trend'])
            visual["position"]["tabOrder"] = tab_order + 100
            visuals.append(visual)
        
        # Variance visual
        if slots.get('needs_variance', False) and 'variance' in visual_positions:
            visual = self.visual_builder.build_waterfall(visual_positions['variance'])
            visual["position"]["tabOrder"] = tab_order + 200
            visuals.append(visual)
        
        # Ranking visual
        if slots.get('needs_ranking', False) and 'ranking' in visual_positions:
            visual = self.visual_builder.build_horizontal_bar(visual_positions['ranking'])
            visual["position"]["tabOrder"] = tab_order + 300
            visuals.append(visual)
        
        # Mix visual
        if slots.get('needs_mix', False) and 'mix' in visual_positions:
            visual = self.visual_builder.build_stacked_bar(visual_positions['mix'])
            visual["position"]["tabOrder"] = tab_order + 400
            visuals.append(visual)
        
        # Exceptions visual
        if slots.get('needs_exceptions', False) and 'exceptions' in visual_positions:
            visual = self.visual_builder.build_table(visual_positions['exceptions'])
            visual["position"]["tabOrder"] = tab_order + 500
            visuals.append(visual)
        
        # Prescriptive visual
        if slots.get('needs_prescriptive', False) and 'prescriptive' in visual_positions:
            visual = self.visual_builder.build_table(visual_positions['prescriptive'])
            visual["position"]["tabOrder"] = tab_order + 600
            visuals.append(visual)
        
        # Root Cause visual
        if slots.get('needs_root_cause', False) and 'root_cause' in visual_positions:
            visual = self.visual_builder.build_scatter_plot(visual_positions['root_cause'])
            visual["position"]["tabOrder"] = tab_order + 700
            visuals.append(visual)
        
        # Funnel visual
        if slots.get('needs_funnel', False) and 'funnel' in visual_positions:
            visual = self.visual_builder.build_funnel(visual_positions['funnel'])
            visual["position"]["tabOrder"] = tab_order + 800
            visuals.append(visual)
        
        # Detail Matrix visual
        if slots.get('needs_detail_matrix', False) and 'detail_matrix' in visual_positions:
            # Use table by default, can be overridden to matrix
            visual = self.visual_builder.build_table(visual_positions['detail_matrix'])
            visual["position"]["tabOrder"] = tab_order + 900
            visuals.append(visual)
        
        # Build slicers (default: time slicer)
        slicers = []
        slicer_tab_order = self.slicer_builder.tab_order_base
        
        # Time slicer (always present unless excluded)
        if not slots.get('exclude_time_slicer', False):
            slicer_positions = self.layout_calculator.calculate_slicer_positions(
                slicers=[{"type": "time"}],
                placement="top"
            )
            if slicer_positions:
                slicer = self.slicer_builder.build_time_slicer(slicer_positions[0])
                slicer["position"]["tabOrder"] = slicer_tab_order
                slicers.append(slicer)
        
        # Action Panel placeholder (if T4)
        action_panel_visual = None
        if has_action_panel:
            action_panel_pos = self.layout_calculator.calculate_action_panel_position()
            # Action Panel is a special visual type (textbox or custom)
            # For now, create a placeholder textbox
            action_panel_visual = {
                "$schema": self.visual_builder.VISUAL_SCHEMA,
                "name": self.visual_builder._generate_visual_id(),
                "position": {
                    "x": action_panel_pos.x,
                    "y": action_panel_pos.y,
                    "z": 15000,  # Above other visuals
                    "height": action_panel_pos.height,
                    "width": action_panel_pos.width,
                    "tabOrder": 10000
                },
                "visual": {
                    "visualType": "textbox",
                    "query": {},
                    "objects": {
                        "text": [
                            {
                                "properties": {
                                    "text": {
                                        "expr": {
                                            "Literal": {
                                                "Value": "'Action Panel Placeholder'"
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
