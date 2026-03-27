"""
figma_layout_bridge.py — Bridge between Figma designs and PBIP grid templates.

Architecture:
  Designer creates a 1920×1080 Figma frame per layout variant.
  Each visual slot is a named child frame (e.g. "Main_1", "KPI_Cards").
  This module extracts absolute positions from Figma and produces
  a grid_template-compatible dict with `position_mode: absolute`.

Usage in UseCase_Bracket.yaml:
  ux_layout_rules:
    layout_source: "figma://FILE_ID/NODE_ID"   # overrides template_id
    page_template: pulse                        # fallback if Figma unreachable

Usage in code (via ConfigLoader):
  from figma_layout_bridge import FigmaLayoutBridge
  bridge = FigmaLayoutBridge(figma_mcp_client)
  layout = bridge.load_layout("figma://FILE_ID/NODE_ID")
  # Returns same schema as grid_template JSON but with pixel positions

Schema of returned layout dict:
  {
    "template_id": "figma_<node_id>",
    "description": "<Figma frame name>",
    "position_mode": "absolute",          # NEW field — tells PageBuilder to skip GridCalculator
    "canvas": {"width": 1920, "height": 1080},
    "slots": [
      {
        "slot_id": "Main_1",              # must match visual slot naming conventions
        "position": {"x": 0, "y": 290, "width": 608, "height": 758},
        "visual_type_hint": "lineChart",  # optional — from Figma component name / annotation
        "figma_node_id": "123:456"        # for round-trip debugging
      }
    ]
  }

PageBuilder integration:
  In _build_page_structure_from_grid(), detect `position_mode == "absolute"` and
  use slot["position"] directly instead of calling GridCalculator.calculate_visual_rect().

Figma slot naming conventions (enforced by design system):
  - KPI_Cards       — top KPI card strip
  - Slicer_Date     — date/time filter
  - Slicer_Entity   — entity (OrgName) filter
  - Main_1          — primary 30s chart (trend)
  - Main_2          — secondary 30s chart (comparison)
  - Main_3          — tertiary 30s chart (ranking/entity)
  - Slicer_Pane     — detail page date filter
  - Smart_Narrative — context text on detail page
  - Detail_Matrix   — evidence table on detail page
  - ActionPanel     — action recommendations on detail page

Visual type hints (Figma component names or annotations):
  Frame name format: "Main_1 [lineChart]" or "Main_1" (type from component property)
  Supported type strings: lineChart, clusteredBarChart, waterfallChart,
                          stackedBarChart, tableEx, cardVisual, slicer, textbox
"""

from __future__ import annotations

import re
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# --- Slot naming: canonical slot IDs that map to visual positions ---
KNOWN_SLOT_IDS = {
    "KPI_Cards", "Slicer_Date", "Slicer_Entity", "Slicer_Pane",
    "Main_1", "Main_2", "Main_3",
    "Focus_Area", "Support_1", "Support_2",
    "Smart_Narrative", "Detail_Matrix", "ActionPanel",
}

# Figma component name → Power BI visualType
FIGMA_COMPONENT_TO_VISUAL_TYPE: Dict[str, str] = {
    "Trend Line": "lineChart",
    "Bar Chart": "clusteredBarChart",
    "Waterfall Chart": "waterfallChart",
    "Stacked Bar": "stackedBarChart",
    "KPI Card": "cardVisual",
    "Table": "tableEx",
    "Matrix": "matrixVisual",
    "Slicer": "slicer",
    "Text Box": "textbox",
    "Scatter Chart": "scatterChart",
    "Funnel Chart": "funnelChart",
}

# Regex to extract visual type hint from frame name: "Main_1 [lineChart]"
_HINT_RE = re.compile(r"\[([^\]]+)\]")

# Figma URL pattern: figma://FILE_ID/NODE_ID  or  https://figma.com/file/FILE_ID/...#node=NODE_ID
_FIGMA_URI_RE = re.compile(r"figma://([^/]+)/(.+)")
_FIGMA_URL_RE = re.compile(r"figma\.com/(?:file|design)/([^/?]+).*node-id=([^&]+)")


class FigmaLayoutBridge:
    """
    Extracts PBIP-compatible layout definitions from Figma frames.

    The bridge is designed to work with the Figma MCP (mcp__d9301186-5d57-4267-8b50-777fd092c841).
    When the MCP is unavailable, it falls back gracefully to None and the caller
    should use the static `template_id` fallback from the bracket YAML.
    """

    def __init__(self, figma_client: Any = None):
        """
        Args:
            figma_client: Optional Figma MCP client proxy. If None, bridge
                          operates in offline mode (returns None from load_layout).
        """
        self._client = figma_client

    @staticmethod
    def parse_layout_source(layout_source: str) -> Optional[Tuple[str, str]]:
        """
        Parse a layout_source string into (file_id, node_id).

        Accepts:
          - figma://FILE_ID/NODE_ID
          - https://www.figma.com/file/FILE_ID/...?node-id=NODE_ID
          - https://www.figma.com/design/FILE_ID/...?node-id=NODE_ID

        Returns (file_id, node_id) or None if unparseable.
        """
        if not layout_source:
            return None
        m = _FIGMA_URI_RE.match(layout_source)
        if m:
            return m.group(1), m.group(2)
        m = _FIGMA_URL_RE.search(layout_source)
        if m:
            node_id = m.group(2).replace("-", ":")  # Figma URL uses "-", API uses ":"
            return m.group(1), node_id
        return None

    @staticmethod
    def extract_visual_type_hint(frame_name: str) -> Optional[str]:
        """
        Extract visual type hint from Figma frame name.

        Convention: "Main_1 [lineChart]" → "lineChart"
        Also checks FIGMA_COMPONENT_TO_VISUAL_TYPE for component-level names.
        """
        m = _HINT_RE.search(frame_name)
        if m:
            hint = m.group(1).strip()
            return hint
        # Try component name lookup
        base_name = frame_name.strip()
        return FIGMA_COMPONENT_TO_VISUAL_TYPE.get(base_name)

    @staticmethod
    def normalize_slot_id(frame_name: str) -> Optional[str]:
        """
        Normalize a Figma frame name to a canonical slot_id.

        Strips type hints, spaces, and matches against KNOWN_SLOT_IDS.
        Returns None if the frame is not a recognized visual slot.
        """
        # Remove type hint annotation
        clean = _HINT_RE.sub("", frame_name).strip()
        # Direct match
        if clean in KNOWN_SLOT_IDS:
            return clean
        # Case-insensitive match
        clean_lower = clean.lower().replace(" ", "_").replace("-", "_")
        for sid in KNOWN_SLOT_IDS:
            if sid.lower() == clean_lower:
                return sid
        return None

    def load_layout(
        self,
        layout_source: str,
        canvas_width: int = 1920,
        canvas_height: int = 1080,
    ) -> Optional[Dict[str, Any]]:
        """
        Load a layout from Figma and return a grid_template-compatible dict.

        Args:
            layout_source: Figma URI (figma://FILE_ID/NODE_ID) or HTTPS URL
            canvas_width: Expected canvas width (default 1920 for PBI standard)
            canvas_height: Expected canvas height (default 1080 for PBI standard)

        Returns:
            Layout dict with position_mode="absolute", or None if unavailable.
        """
        if self._client is None:
            logger.warning(
                "FigmaLayoutBridge: No Figma client configured — "
                "falling back to static template_id. "
                "To enable Figma layouts, pass a Figma MCP client to FigmaLayoutBridge()."
            )
            return None

        parsed = self.parse_layout_source(layout_source)
        if not parsed:
            logger.warning(f"FigmaLayoutBridge: Cannot parse layout_source '{layout_source}'")
            return None

        file_id, node_id = parsed
        try:
            design_context = self._client.get_design_context(
                file_key=file_id,
                node_id=node_id,
                depth=2,  # frame + direct children (visual slots)
            )
        except Exception as e:
            logger.warning(f"FigmaLayoutBridge: Figma API error for {layout_source}: {e}")
            return None

        return self._parse_design_context(design_context, canvas_width, canvas_height)

    def _parse_design_context(
        self,
        design_context: Dict[str, Any],
        canvas_width: int,
        canvas_height: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Parse Figma design context response into a layout dict.

        The design context JSON follows the Figma MCP schema:
          { "frames": [{ "id": "...", "name": "...", "width": 1920, "height": 1080,
                         "children": [{ "id": "...", "name": "Main_1",
                                        "x": 32, "y": 290, "width": 608, "height": 758 }] }] }
        """
        frames = design_context.get("frames") or []
        if not frames:
            # Some MCP clients return top-level node directly
            frames = [design_context]

        root_frame = frames[0]
        frame_name = root_frame.get("name", "figma_layout")
        frame_w = root_frame.get("width", canvas_width)
        frame_h = root_frame.get("height", canvas_height)

        # Scale factor if Figma canvas differs from PBI canvas
        scale_x = canvas_width / frame_w if frame_w else 1.0
        scale_y = canvas_height / frame_h if frame_h else 1.0

        slots: List[Dict[str, Any]] = []
        children = root_frame.get("children") or []

        for child in children:
            child_name = child.get("name", "")
            slot_id = self.normalize_slot_id(child_name)
            if not slot_id:
                logger.debug(f"FigmaLayoutBridge: Skipping unrecognized frame '{child_name}'")
                continue

            x = round(child.get("x", 0) * scale_x)
            y = round(child.get("y", 0) * scale_y)
            w = round(child.get("width", 0) * scale_x)
            h = round(child.get("height", 0) * scale_y)

            visual_type_hint = self.extract_visual_type_hint(child_name)
            # Also check component name from Figma component metadata
            component_name = (child.get("componentProperties") or {}).get("visual_type")
            if component_name and not visual_type_hint:
                visual_type_hint = FIGMA_COMPONENT_TO_VISUAL_TYPE.get(component_name)

            slot: Dict[str, Any] = {
                "slot_id": slot_id,
                "position": {"x": x, "y": y, "width": w, "height": h},
                "figma_node_id": child.get("id", ""),
            }
            if visual_type_hint:
                slot["visual_type_hint"] = visual_type_hint

            slots.append(slot)

        if not slots:
            logger.warning(f"FigmaLayoutBridge: No recognized slots found in Figma frame '{frame_name}'")
            return None

        logger.info(
            f"FigmaLayoutBridge: Loaded {len(slots)} slots from Figma frame "
            f"'{frame_name}' ({frame_w}×{frame_h})"
        )

        return {
            "template_id": f"figma_{root_frame.get('id', 'unknown').replace(':', '_')}",
            "description": f"Figma layout: {frame_name}",
            "position_mode": "absolute",
            "canvas": {"width": canvas_width, "height": canvas_height},
            "slots": slots,
            "figma_source": {
                "frame_name": frame_name,
                "frame_id": root_frame.get("id", ""),
                "original_size": {"width": frame_w, "height": frame_h},
            },
        }

    @classmethod
    def from_static_dict(
        cls,
        slots_dict: Dict[str, Dict[str, Any]],
        template_id: str = "custom",
        description: str = "Custom absolute layout",
        canvas_width: int = 1920,
        canvas_height: int = 1080,
    ) -> Dict[str, Any]:
        """
        Build a layout dict from a manually specified slots dictionary.
        Useful for testing and migration from hardcoded pixel values.

        Args:
            slots_dict: {slot_id: {"x", "y", "width", "height", "visual_type_hint"}}
            template_id: Identifier for this layout
            description: Human-readable description

        Example:
            layout = FigmaLayoutBridge.from_static_dict({
                "KPI_Cards": {"x": 32, "y": 32, "width": 1856, "height": 156},
                "Main_1": {"x": 32, "y": 290, "width": 608, "height": 758, "visual_type_hint": "lineChart"},
                ...
            })
        """
        slots = []
        for slot_id, props in slots_dict.items():
            slot = {
                "slot_id": slot_id,
                "position": {
                    "x": props.get("x", 0),
                    "y": props.get("y", 0),
                    "width": props.get("width", 100),
                    "height": props.get("height", 100),
                },
            }
            if props.get("visual_type_hint"):
                slot["visual_type_hint"] = props["visual_type_hint"]
            slots.append(slot)

        return {
            "template_id": template_id,
            "description": description,
            "position_mode": "absolute",
            "canvas": {"width": canvas_width, "height": canvas_height},
            "slots": slots,
        }
