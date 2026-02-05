"""
Layout Calculator

Calculates visual positions and sizes based on Layout Grid System rules.
"""

from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass


@dataclass
class Position:
    """Position and size of a visual."""
    x: float
    y: float
    width: float
    height: float
    z: int = 10000


class LayoutCalculator:
    """Calculates layout positions based on grid system rules."""
    
    # Canvas constants
    CANVAS_WIDTH = 1920
    CANVAS_HEIGHT = 1080
    PADDING = 20
    GAP_BETWEEN_VISUALS = 20
    GAP_BETWEEN_GROUPS = 40
    
    # Row definitions
    ROW_1_Y_START = 0
    ROW_1_Y_END = 160
    ROW_2_Y_START = 180
    ROW_2_Y_END = 580
    ROW_3_Y_START = 600
    ROW_3_Y_END = 900
    ROW_4_Y_START = 920
    
    # KPI Card constants
    KPI_CARD_WIDTH_STANDARD = 280
    KPI_CARD_HEIGHT_STANDARD = 140
    KPI_CARD_WIDTH_COMPACT = 200
    KPI_CARD_HEIGHT_COMPACT = 120
    KPI_CARD_GAP = 20
    KPI_CARDS_MAX_PER_ROW = 6
    
    # Slicer constants
    SLICER_TOP_HEIGHT = 40
    SLICER_SIDE_WIDTH = 200
    SLICER_SIDE_X = 1570  # Right side placement
    
    # Action Panel constants
    ACTION_PANEL_WIDTH = 350
    ACTION_PANEL_X = 1570  # Right side placement

    def compute_adaptive_bounds(
        self,
        slots: Dict[str, bool],
        template: str,
        has_action_panel: bool = False,
        kpi_count: int = 4,
        use_compact_kpi: bool = False,
    ) -> Dict[str, float]:
        """
        Compute layout bounds that adapt to page type and actual visuals (resize/reflow).
        Single source of truth for both PBIP and mockup.
        
        Returns:
            Dict with kpi_band_y_end, row_2_y, row_2_height, row_3_y, row_3_height,
            detail_y, detail_height, and optionally row_2_visual_height (per-visual height when stacked).
        """
        card_height = self.KPI_CARD_HEIGHT_COMPACT if use_compact_kpi else self.KPI_CARD_HEIGHT_STANDARD
        # KPI band: 1 row or 2 rows
        if kpi_count <= self.KPI_CARDS_MAX_PER_ROW:
            kpi_band_y_end = self.PADDING + card_height + self.PADDING  # ~180
        else:
            kpi_band_y_end = self.PADDING + card_height + self.GAP_BETWEEN_VISUALS + card_height + self.PADDING  # ~340
        row_2_y = kpi_band_y_end + self.GAP_BETWEEN_GROUPS

        # Count primary and secondary visuals
        primary_count = 0
        if slots.get("needs_trend", False):
            primary_count += 1
        if slots.get("needs_variance", False):
            primary_count += 1
        if slots.get("needs_exceptions", False) and template == "T3":
            primary_count += 1
        if slots.get("needs_prescriptive", False) and template == "T4":
            primary_count += 1

        secondary_count = 0
        if slots.get("needs_ranking", False):
            secondary_count += 1
        if slots.get("needs_mix", False):
            secondary_count += 1
        if slots.get("needs_root_cause", False):
            secondary_count += 1
        if slots.get("needs_funnel", False) and template == "T2":
            secondary_count += 1

        has_detail = bool(slots.get("needs_detail_matrix", False))
        detail_height_min = 300
        remaining = self.CANVAS_HEIGHT - row_2_y - self.PADDING
        if has_detail:
            remaining -= detail_height_min + self.GAP_BETWEEN_GROUPS

        # Split remaining space between primary and secondary (by count or 50-50)
        total_mid_visuals = max(1, primary_count + secondary_count)
        primary_ratio = primary_count / total_mid_visuals if total_mid_visuals else 0.5
        secondary_ratio = secondary_count / total_mid_visuals if total_mid_visuals else 0.5
        row_2_height_total = remaining * primary_ratio if primary_count else 0
        row_3_height_total = remaining * secondary_ratio if secondary_count else 0
        # If only one zone has visuals, give it all mid space
        if primary_count and not secondary_count:
            row_2_height_total = remaining
            row_3_height_total = 0
        elif secondary_count and not primary_count:
            row_3_height_total = remaining
            row_2_height_total = 0

        row_2_height = row_2_height_total
        row_3_y = row_2_y + row_2_height_total + (self.GAP_BETWEEN_GROUPS if primary_count and secondary_count else 0)
        row_3_height = row_3_height_total
        detail_y = row_3_y + row_3_height + (self.GAP_BETWEEN_GROUPS if secondary_count else 0)
        if not secondary_count:
            detail_y = row_2_y + row_2_height + self.GAP_BETWEEN_GROUPS
        detail_height = self.CANVAS_HEIGHT - detail_y - self.PADDING if has_detail else 0

        return {
            "kpi_band_y_end": kpi_band_y_end,
            "row_2_y": row_2_y,
            "row_2_height": row_2_height,
            "row_3_y": row_3_y,
            "row_3_height": row_3_height,
            "detail_y": detail_y,
            "detail_height": max(detail_height_min, detail_height) if has_detail else 0,
            "primary_count": primary_count,
            "secondary_count": secondary_count,
        }
    
    def calculate_kpi_card_positions(
        self,
        count: int,
        use_compact: bool = False,
        layout_bounds: Optional[Dict[str, float]] = None,
    ) -> List[Position]:
        """
        Calculate KPI card positions.
        
        Args:
            count: Number of KPI cards
            use_compact: Use compact sizing
        
        Returns:
            List of Position objects
        """
        card_width = self.KPI_CARD_WIDTH_COMPACT if use_compact else self.KPI_CARD_WIDTH_STANDARD
        card_height = self.KPI_CARD_HEIGHT_COMPACT if use_compact else self.KPI_CARD_HEIGHT_STANDARD
        
        positions = []
        x_start = self.PADDING
        y = self.ROW_1_Y_START + self.PADDING

        # Calculate available width
        available_width = self.CANVAS_WIDTH - (2 * self.PADDING)

        # Calculate how many cards fit in first row
        cards_per_row = min(count, self.KPI_CARDS_MAX_PER_ROW)
        cards_in_first_row = min(count, cards_per_row)

        # Calculate total width needed for first row
        total_width = (cards_in_first_row * card_width) + ((cards_in_first_row - 1) * self.KPI_CARD_GAP)

        # Center cards if they don't fill the row
        if total_width < available_width:
            x_start = (self.CANVAS_WIDTH - total_width) / 2

        # First row
        for i in range(cards_in_first_row):
            x = x_start + (i * (card_width + self.KPI_CARD_GAP))
            positions.append(Position(x=x, y=y, width=card_width, height=card_height))

        # Second row if needed
        if count > cards_in_first_row:
            remaining = count - cards_in_first_row
            cards_in_second_row = min(remaining, self.KPI_CARDS_MAX_PER_ROW)
            total_width_second = (cards_in_second_row * card_width) + ((cards_in_second_row - 1) * self.KPI_CARD_GAP)
            x_start_second = (self.CANVAS_WIDTH - total_width_second) / 2
            y_second = y + card_height + self.GAP_BETWEEN_VISUALS

            for i in range(cards_in_second_row):
                x = x_start_second + (i * (card_width + self.KPI_CARD_GAP))
                positions.append(Position(x=x, y=y_second, width=card_width, height=card_height))

        return positions
    
    def calculate_slicer_positions(self, slicers: List[Dict[str, Any]], placement: str = "top") -> List[Position]:
        """
        Calculate slicer positions.
        
        Args:
            slicers: List of slicer configurations
            placement: "top" or "side"
        
        Returns:
            List of Position objects
        """
        positions = []
        
        if placement == "top":
            # Top placement: distribute across top row
            slicer_count = len(slicers)
            if slicer_count == 0:
                return positions
            
            # Calculate slicer width (equal distribution)
            available_width = self.CANVAS_WIDTH - (2 * self.PADDING)
            slicer_width = (available_width - ((slicer_count - 1) * self.GAP_BETWEEN_VISUALS)) / slicer_count
            
            x = self.PADDING
            y = self.ROW_1_Y_START
            
            for i in range(slicer_count):
                positions.append(Position(
                    x=x,
                    y=y,
                    width=slicer_width,
                    height=self.SLICER_TOP_HEIGHT
                ))
                x += slicer_width + self.GAP_BETWEEN_VISUALS
        
        else:  # side placement
            # Side placement: stack vertically on right side
            y = self.ROW_1_Y_START
            slicer_height = (self.CANVAS_HEIGHT - self.ROW_1_Y_START) / len(slicers) if len(slicers) > 0 else 300
            
            for i in range(len(slicers)):
                positions.append(Position(
                    x=self.SLICER_SIDE_X,
                    y=y,
                    width=self.SLICER_SIDE_WIDTH,
                    height=slicer_height
                ))
                y += slicer_height + self.GAP_BETWEEN_VISUALS
        
        return positions
    
    def calculate_visual_positions(
        self,
        slots: Dict[str, bool],
        template: str,
        has_action_panel: bool = False,
        has_side_slicers: bool = False,
        layout_bounds: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Position]:
        """
        Calculate visual positions based on slots and template.
        Uses layout_bounds when provided (adaptive layout); otherwise fixed row constants.
        
        Args:
            slots: Dictionary of slot activations (needs_trend, needs_variance, etc.)
            template: Template type (T1, T2, T3, T4)
            has_action_panel: Whether Action Panel is present
            has_side_slicers: Whether side slicers are present
            layout_bounds: Optional adaptive bounds from compute_adaptive_bounds()
        
        Returns:
            Dictionary mapping slot names to Position objects
        """
        positions = {}

        # Calculate available width (accounting for Action Panel and side slicers)
        available_width = self.CANVAS_WIDTH - (2 * self.PADDING)
        if has_action_panel:
            available_width -= (self.ACTION_PANEL_WIDTH + self.GAP_BETWEEN_VISUALS)
        elif has_side_slicers:
            available_width -= (self.SLICER_SIDE_WIDTH + self.GAP_BETWEEN_VISUALS)

        x_start = self.PADDING

        if layout_bounds:
            row_2_y = layout_bounds["row_2_y"]
            row_2_height = layout_bounds["row_2_height"]
            row_3_y = layout_bounds["row_3_y"]
            row_3_height = layout_bounds["row_3_height"]
            detail_y = layout_bounds["detail_y"]
            detail_height = layout_bounds["detail_height"]
            primary_count = int(layout_bounds.get("primary_count", 1))
            secondary_count = int(layout_bounds.get("secondary_count", 1))
            # Per-visual height when stacking in primary zone
            primary_single_height = (row_2_height - (primary_count - 1) * self.GAP_BETWEEN_VISUALS) / primary_count if primary_count else row_2_height
            secondary_single_height = (row_3_height - (secondary_count - 1) * self.GAP_BETWEEN_VISUALS) / secondary_count if secondary_count else row_3_height
        else:
            row_2_y = self.ROW_2_Y_START
            row_2_height = self.ROW_2_Y_END - self.ROW_2_Y_START
            row_3_y = self.ROW_3_Y_START
            row_3_height = self.ROW_3_Y_END - self.ROW_3_Y_START
            detail_y = self.ROW_4_Y_START
            detail_height = 300
            primary_single_height = row_2_height
            secondary_single_height = row_3_height

        # Row 2: Primary visuals (Trend, Variance, Exceptions, Prescriptive)
        visual_count_row_2 = 0
        primary_slots = [
            ("needs_trend", "trend"),
            ("needs_variance", "variance"),
            ("needs_exceptions", "exceptions"),
            ("needs_prescriptive", "prescriptive"),
        ]
        for slot_key, slot_name in primary_slots:
            if slot_key == "needs_exceptions" and template != "T3":
                continue
            if slot_key == "needs_prescriptive" and template != "T4":
                continue
            if not slots.get(slot_key, False):
                continue
            h = primary_single_height if layout_bounds else row_2_height
            y = row_2_y + visual_count_row_2 * (h + self.GAP_BETWEEN_VISUALS)
            positions[slot_name] = Position(x=x_start, y=y, width=available_width, height=h)
            visual_count_row_2 += 1

        # Row 3: Secondary visuals (Ranking, Mix, Root Cause, Funnel)
        visual_count_row_3 = 0
        secondary_slots = [
            ("needs_ranking", "ranking"),
            ("needs_mix", "mix"),
            ("needs_root_cause", "root_cause"),
            ("needs_funnel", "funnel"),
        ]
        for slot_key, slot_name in secondary_slots:
            if slot_key == "needs_funnel" and template != "T2":
                continue
            if not slots.get(slot_key, False):
                continue
            h = secondary_single_height if layout_bounds else row_3_height
            y = row_3_y + visual_count_row_3 * (h + self.GAP_BETWEEN_VISUALS)
            positions[slot_name] = Position(x=x_start, y=y, width=available_width, height=h)
            visual_count_row_3 += 1

        # Row 4: Detail Matrix (detail pages only)
        if slots.get("needs_detail_matrix", False):
            positions["detail_matrix"] = Position(
                x=x_start,
                y=detail_y,
                width=available_width,
                height=detail_height,
            )

        return positions
    
    def calculate_action_panel_position(self) -> Position:
        """Calculate Action Panel position (right side)."""
        return Position(
            x=self.ACTION_PANEL_X,
            y=self.ROW_1_Y_START,
            width=self.ACTION_PANEL_WIDTH,
            height=self.CANVAS_HEIGHT - self.ROW_1_Y_START
        )
    
    def get_available_width(self, has_action_panel: bool = False, has_side_slicers: bool = False) -> float:
        """
        Get available width for visuals.
        
        Args:
            has_action_panel: Whether Action Panel is present
            has_side_slicers: Whether side slicers are present
        
        Returns:
            Available width in pixels
        """
        available = self.CANVAS_WIDTH - (2 * self.PADDING)
        
        if has_action_panel:
            available -= (self.ACTION_PANEL_WIDTH + self.GAP_BETWEEN_VISUALS)
        elif has_side_slicers:
            available -= (self.SLICER_SIDE_WIDTH + self.GAP_BETWEEN_VISUALS)
        
        return available
