"""
Layout Calculator

Maps the governance 12x12 grid system to CSS grid classes for Evidence pages.
Evidence uses standard HTML/CSS so we emit CSS grid or Tailwind utility
classes that match the governed slot positions.

Mirrors Fabric's GridCalculator but outputs CSS instead of pixel positions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class GridSlot:
    """A visual slot positioned on the CSS grid."""
    slot_id: str
    col_start: int   # 1-based grid column start
    row_start: int   # 1-based grid row start
    col_span: int
    row_span: int

    @property
    def css_grid_area(self) -> str:
        """CSS grid-area shorthand: row-start / col-start / row-end / col-end."""
        return (
            f"{self.row_start} / {self.col_start} / "
            f"{self.row_start + self.row_span} / {self.col_start + self.col_span}"
        )

    @property
    def tailwind_classes(self) -> str:
        """Tailwind CSS grid placement classes."""
        return (
            f"col-start-{self.col_start} col-span-{self.col_span} "
            f"row-start-{self.row_start} row-span-{self.row_span}"
        )


class LayoutCalculator:
    """Convert governance grid blueprints to CSS grid layout."""

    def __init__(self, columns: int = 12, rows: int = 12) -> None:
        self.columns = columns
        self.rows = rows

    def parse_slots(self, grid_blueprint: dict) -> List[GridSlot]:
        """Parse slot definitions from a UseCase Bracket grid_blueprint."""
        slots = []
        for slot_def in grid_blueprint.get("slots", []):
            grid = slot_def.get("grid")
            if not grid or len(grid) != 4:
                continue
            col_start, row_start, col_span, row_span = grid
            slots.append(GridSlot(
                slot_id=slot_def.get("slot_id", f"slot_{len(slots)}"),
                col_start=col_start,
                row_start=row_start,
                col_span=col_span,
                row_span=row_span,
            ))
        return slots

    def validate_slots(self, slots: List[GridSlot]) -> List[str]:
        """Validate that slots fit within the grid and don't overlap."""
        errors: List[str] = []
        occupied: set = set()
        for slot in slots:
            if slot.col_start < 1 or slot.row_start < 1:
                errors.append(f"{slot.slot_id}: grid position must be >= 1")
            if slot.col_start + slot.col_span - 1 > self.columns:
                errors.append(f"{slot.slot_id}: exceeds {self.columns} columns")
            if slot.row_start + slot.row_span - 1 > self.rows:
                errors.append(f"{slot.slot_id}: exceeds {self.rows} rows")
            for c in range(slot.col_start, slot.col_start + slot.col_span):
                for r in range(slot.row_start, slot.row_start + slot.row_span):
                    cell = (c, r)
                    if cell in occupied:
                        errors.append(f"{slot.slot_id}: overlaps at ({c}, {r})")
                    occupied.add(cell)
        return errors

    def generate_grid_container_css(self, gap: str = "1rem") -> str:
        """Generate the CSS for the grid container."""
        return (
            f"display: grid; "
            f"grid-template-columns: repeat({self.columns}, 1fr); "
            f"grid-template-rows: repeat({self.rows}, auto); "
            f"gap: {gap};"
        )

    def generate_evidence_grid_html(
        self,
        slots: List[GridSlot],
        slot_content: Optional[dict] = None,
    ) -> str:
        """Generate an HTML grid wrapper for Evidence pages."""
        content_map = slot_content or {}
        container_css = self.generate_grid_container_css()
        lines = [f'<div style="{container_css}">']
        for slot in slots:
            inner = content_map.get(slot.slot_id, f"<!-- {slot.slot_id} -->")
            lines.append(
                f'  <div style="grid-area: {slot.css_grid_area};">'
            )
            lines.append(f"    {inner}")
            lines.append("  </div>")
        lines.append("</div>")
        return "\n".join(lines)
