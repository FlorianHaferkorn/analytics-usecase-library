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
    
    def calculate_kpi_card_positions(self, count: int, use_compact: bool = False) -> List[Position]:
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
        has_side_slicers: bool = False
    ) -> Dict[str, Position]:
        """
        Calculate visual positions based on slots and template.
        
        Args:
            slots: Dictionary of slot activations (needs_trend, needs_variance, etc.)
            template: Template type (T1, T2, T3, T4)
            has_action_panel: Whether Action Panel is present
            has_side_slicers: Whether side slicers are present
        
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
        
        # Row 2: Primary visuals (Trend, Variance, Exceptions, Prescriptive)
        row_2_y = self.ROW_2_Y_START
        row_2_height = self.ROW_2_Y_END - self.ROW_2_Y_START
        
        visual_count_row_2 = 0
        
        if slots.get('needs_trend', False):
            positions['trend'] = Position(
                x=x_start,
                y=row_2_y,
                width=available_width,
                height=row_2_height
            )
            visual_count_row_2 += 1
        
        if slots.get('needs_variance', False):
            y = row_2_y if visual_count_row_2 == 0 else row_2_y + row_2_height + self.GAP_BETWEEN_VISUALS
            positions['variance'] = Position(
                x=x_start,
                y=y,
                width=available_width,
                height=row_2_height
            )
            visual_count_row_2 += 1
        
        if slots.get('needs_exceptions', False) and template == 'T3':
            y = row_2_y if visual_count_row_2 == 0 else row_2_y + row_2_height + self.GAP_BETWEEN_VISUALS
            positions['exceptions'] = Position(
                x=x_start,
                y=y,
                width=available_width,
                height=row_2_height
            )
            visual_count_row_2 += 1
        
        if slots.get('needs_prescriptive', False) and template == 'T4':
            y = row_2_y if visual_count_row_2 == 0 else row_2_y + row_2_height + self.GAP_BETWEEN_VISUALS
            positions['prescriptive'] = Position(
                x=x_start,
                y=y,
                width=available_width,
                height=row_2_height
            )
            visual_count_row_2 += 1
        
        # Row 3: Secondary visuals (Ranking, Mix, Root Cause)
        row_3_y = self.ROW_3_Y_START
        row_3_height = self.ROW_3_Y_END - self.ROW_3_Y_START
        
        visual_count_row_3 = 0
        
        if slots.get('needs_ranking', False):
            positions['ranking'] = Position(
                x=x_start,
                y=row_3_y,
                width=available_width,
                height=row_3_height
            )
            visual_count_row_3 += 1
        
        if slots.get('needs_mix', False):
            y = row_3_y if visual_count_row_3 == 0 else row_3_y + row_3_height + self.GAP_BETWEEN_VISUALS
            positions['mix'] = Position(
                x=x_start,
                y=y,
                width=available_width,
                height=row_3_height
            )
            visual_count_row_3 += 1
        
        if slots.get('needs_root_cause', False):
            y = row_3_y if visual_count_row_3 == 0 else row_3_y + row_3_height + self.GAP_BETWEEN_VISUALS
            positions['root_cause'] = Position(
                x=x_start,
                y=y,
                width=available_width,
                height=row_3_height
            )
            visual_count_row_3 += 1
        
        if slots.get('needs_funnel', False) and template == 'T2':
            y = row_3_y if visual_count_row_3 == 0 else row_3_y + row_3_height + self.GAP_BETWEEN_VISUALS
            positions['funnel'] = Position(
                x=x_start,
                y=y,
                width=available_width,
                height=row_3_height
            )
            visual_count_row_3 += 1
        
        # Row 4: Detail Matrix (detail pages only)
        if slots.get('needs_detail_matrix', False):
            positions['detail_matrix'] = Position(
                x=x_start,
                y=self.ROW_4_Y_START,
                width=available_width,
                height=300  # Minimum height, can expand
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
