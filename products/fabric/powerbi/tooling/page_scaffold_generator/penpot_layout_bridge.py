"""
penpot_layout_bridge.py — Bridge between Penpot designs and PBIP grid templates.

Architecture:
  Designer creates a 1920×1080 Penpot frame per layout variant.
  Each visual slot is a named frame (e.g. "Main_1", "KPI_Cards").
  This module extracts absolute positions from Penpot and produces
  a grid_template-compatible dict with `position_mode: absolute`.

Penpot is a free, open-source alternative to Figma that uses web standards (SVG+JSON).
Unlike Figma, Penpot exports fully to JSON format without API rate limits.

Usage in UseCase_Bracket.yaml:
  ux_layout_rules:
    layout_source: "penpot://FILE_ID/PAGE_ID/FRAME_ID"   # overrides template_id
    page_template: pulse                                  # fallback if Penpot unreachable

Usage in code (via ConfigLoader):
  from penpot_layout_bridge import PenpotLayoutBridge
  bridge = PenpotLayoutBridge()
  layout = bridge.load_from_file("path/to/penpot_export.json")
  # Returns same schema as grid_template JSON but with pixel positions

Penpot JSON Structure:
  Penpot exports include a "penpot:objects" map keyed by UUID.
  Each object has:
    - name: frame name (e.g. "Main_1 [lineChart]")
    - type: frame type (typically "frame")
    - x, y: absolute position
    - width, height: frame dimensions
    - children (optional): array of child UUIDs
    - penpot:component-set (optional): component metadata

  Example Penpot object:
    "uuid-123": {
      "name": "Main_1 [lineChart]",
      "type": "frame",
      "x": 32,
      "y": 290,
      "width": 992,
      "height": 794,
      "children": [],
      "fill-color": null
    }

Schema of returned layout dict:
  {
    "template_id": "penpot_<frame_name>",
    "description": "Penpot layout: <frame_name>",
    "position_mode": "absolute",          # NEW field — tells PageBuilder to skip GridCalculator
    "canvas": {"width": _governtes_raster().width, "height": _governtes_raster().height},
    "slots": [
      {
        "slot_id": "Main_1",              # must match visual slot naming conventions
        "position": {"x": 32, "y": 290, "width": 992, "height": 794},
        "visual_type_hint": "lineChart",  # optional — from Penpot frame name annotation
        "penpot_uuid": "uuid-123"         # for round-trip debugging
      }
    ]
  }

PageBuilder integration:
  In _build_page_structure_from_grid(), detect `position_mode == "absolute"` and
  use slot["position"] directly instead of calling GridCalculator.calculate_visual_rect().

Penpot slot naming conventions (same as Figma, enforced by design system):
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

Visual type hints (from frame name annotations):
  Frame name format: "Main_1 [lineChart]" or "Main_1" (type inferred from component)
  Supported type strings: lineChart, clusteredBarChart, waterfallChart,
                          stackedBarChart, tableEx, cardVisual, slicer, textbox
"""

from __future__ import annotations

import re
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path


def _governtes_raster():
    """Defaults aus dem EINEN governten Raster (Konsolidierung 02.08.2026)."""
    from tooling.superversion.layer_tools.layout_grid import load

    return load("production")

logger = logging.getLogger(__name__)

# --- Slot naming: canonical slot IDs that map to visual positions ---
KNOWN_SLOT_IDS = {
    "KPI_Cards", "Slicer_Date", "Slicer_Entity", "Slicer_Pane",
    "Main_1", "Main_2", "Main_3",
    "Focus_Area", "Support_1", "Support_2",
    "Smart_Narrative", "Detail_Matrix", "ActionPanel",
}

# Penpot component name → Power BI visualType
# (adapted from Figma naming conventions)
PENPOT_COMPONENT_TO_VISUAL_TYPE: Dict[str, str] = {
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

# Penpot URI pattern: penpot://FILE_ID/PAGE_ID/FRAME_ID
_PENPOT_URI_RE = re.compile(r"penpot://([^/]+)/([^/]+)/(.+)")


class PenpotLayoutBridge:
    """
    Extracts PBIP-compatible layout definitions from Penpot frames.

    The bridge can load layouts from:
    1. Exported Penpot JSON files (via load_from_file)
    2. Penpot REST API (via load_from_url)
    3. Static test dicts (via from_static_dict)

    When Penpot is unavailable, it falls back gracefully to None and the caller
    should use the static `template_id` fallback from the bracket YAML.
    """

    def __init__(self):
        """Initialize the Penpot layout bridge."""
        pass

    @staticmethod
    def parse_layout_source(layout_source: str) -> Optional[Tuple[str, str, str]]:
        """
        Parse a layout_source string into (file_id, page_id, frame_id).

        Accepts:
          - penpot://FILE_ID/PAGE_ID/FRAME_ID

        Returns (file_id, page_id, frame_id) or None if unparseable.
        """
        if not layout_source:
            return None
        m = _PENPOT_URI_RE.match(layout_source)
        if m:
            return m.group(1), m.group(2), m.group(3)
        return None

    @staticmethod
    def extract_visual_type_hint(frame_name: str) -> Optional[str]:
        """
        Extract visual type hint from Penpot frame name.

        Convention: "Main_1 [lineChart]" → "lineChart"
        Also checks PENPOT_COMPONENT_TO_VISUAL_TYPE for component-level names.
        """
        m = _HINT_RE.search(frame_name)
        if m:
            hint = m.group(1).strip()
            return hint
        # Try component name lookup
        base_name = frame_name.strip()
        return PENPOT_COMPONENT_TO_VISUAL_TYPE.get(base_name)

    @staticmethod
    def normalize_slot_id(frame_name: str) -> Optional[str]:
        """
        Normalize a Penpot frame name to a canonical slot_id.

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

    def load_from_file(
        self,
        path: str,
        canvas_width: int = 1920,
        canvas_height: int = 1080,
    ) -> Optional[Dict[str, Any]]:
        """
        Load a layout from a Penpot JSON export file.

        Args:
            path: File path to exported Penpot JSON
            canvas_width: Leinwandbreite; None = governtes Raster (layout_grid.yaml)
            canvas_height: Leinwandhoehe; None = governtes Raster (layout_grid.yaml)

        Returns:
            Layout dict with position_mode="absolute", or None if unavailable.
        """
        file_path = Path(path)
        if not file_path.exists():
            logger.warning(f"PenpotLayoutBridge: File not found: {path}")
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"PenpotLayoutBridge: Error reading Penpot JSON {path}: {e}")
            return None

        return self.parse_penpot_json(data, canvas_width, canvas_height)

    def load_from_url(
        self,
        url: str,
        token: Optional[str] = None,
        canvas_width: int = 1920,
        canvas_height: int = 1080,
    ) -> Optional[Dict[str, Any]]:
        """
        Load a layout from Penpot REST API.

        Args:
            url: Penpot API URL (e.g., https://penpot.app/api/rpc/command/file/get?file-id=<id>)
            token: Optional authentication token for private files
            canvas_width: Leinwandbreite; None = governtes Raster (layout_grid.yaml)
            canvas_height: Leinwandhoehe; None = governtes Raster (layout_grid.yaml)

        Returns:
            Layout dict with position_mode="absolute", or None if unavailable.

        Note:
            This method requires network access and Penpot API credentials.
            For offline use, prefer load_from_file() with pre-exported JSON.
        """
        try:
            import urllib.request
            import json as json_mod

            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"

            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json_mod.load(response)
        except Exception as e:
            logger.warning(f"PenpotLayoutBridge: Error fetching from {url}: {e}")
            return None

        return self.parse_penpot_json(data, canvas_width, canvas_height)

    def parse_penpot_json(
        self,
        data: Dict[str, Any],
        canvas_width: int = 1920,
        canvas_height: int = 1080,
    ) -> Optional[Dict[str, Any]]:
        """
        Parse a Penpot JSON export into a layout dict.

        The Penpot JSON structure includes:
          {
            "penpot:objects": {
              "uuid-123": {
                "name": "Main_1",
                "type": "frame",
                "x": 32,
                "y": 290,
                "width": 992,
                "height": 794,
                "children": ["uuid-456", ...]
              },
              ...
            }
          }

        This method:
        1. Finds all frames with recognized slot_id names
        2. Extracts their position and dimensions
        3. Builds a layout dict with position_mode="absolute"
        4. Preserves visual type hints from frame names

        Args:
            data: Parsed Penpot JSON object
            canvas_width: Expected canvas width (default 1920)
            canvas_height: Expected canvas height (default 1080)

        Returns:
            Layout dict or None if no recognized slots found.
        """
        objects = data.get("penpot:objects") or {}
        if not objects:
            logger.warning("PenpotLayoutBridge: No 'penpot:objects' found in JSON")
            return None

        slots: List[Dict[str, Any]] = []
        root_frame_name = "penpot_layout"
        root_frame_id = None
        root_frame_w = canvas_width
        root_frame_h = canvas_height

        # First pass: find all frames with recognized slot names
        for uuid, obj in objects.items():
            if not isinstance(obj, dict):
                continue

            obj_type = obj.get("type")
            if obj_type != "frame":
                continue

            frame_name = obj.get("name", "")
            slot_id = self.normalize_slot_id(frame_name)
            if not slot_id:
                # Check if this is the root/canvas frame
                if "Main_1" not in objects and frame_name.lower() in ("page", "canvas", "artboard"):
                    root_frame_name = frame_name
                    root_frame_id = uuid
                continue

            x = round(obj.get("x", 0))
            y = round(obj.get("y", 0))
            w = round(obj.get("width", 0))
            h = round(obj.get("height", 0))

            visual_type_hint = self.extract_visual_type_hint(frame_name)

            slot: Dict[str, Any] = {
                "slot_id": slot_id,
                "position": {"x": x, "y": y, "width": w, "height": h},
                "penpot_uuid": uuid,
            }
            if visual_type_hint:
                slot["visual_type_hint"] = visual_type_hint

            slots.append(slot)

        if not slots:
            logger.warning("PenpotLayoutBridge: No recognized slots found in Penpot JSON")
            return None

        logger.info(
            f"PenpotLayoutBridge: Loaded {len(slots)} slots from Penpot "
            f"'{root_frame_name}' ({root_frame_w}×{root_frame_h})"
        )

        return {
            "template_id": f"penpot_{root_frame_id or 'unknown'}".replace(":", "_"),
            "description": f"Penpot layout: {root_frame_name}",
            "position_mode": "absolute",
            "canvas": {"width": canvas_width, "height": canvas_height},
            "slots": slots,
            "penpot_source": {
                "frame_name": root_frame_name,
                "frame_id": root_frame_id or "",
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
            canvas_width: Canvas width in pixels
            canvas_height: Canvas height in pixels

        Example:
            layout = PenpotLayoutBridge.from_static_dict({
                "KPI_Cards": {"x": 32, "y": 32, "width": 1856, "height": 120},
                "Main_1": {"x": 32, "y": 168, "width": 992, "height": 794, "visual_type_hint": "lineChart"},
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
