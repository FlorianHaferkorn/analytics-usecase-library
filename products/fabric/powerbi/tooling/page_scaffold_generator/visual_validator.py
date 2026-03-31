"""
Visual Validator

Validates generated Power BI visuals before writing to disk.
Catches common errors (wrong queryState roles, invalid names, out-of-bounds positions)
so the generator fails fast with clear messages instead of producing broken reports.
"""

import re
from typing import Dict, Any, List, Optional


# Mapping: Power BI visualType -> required queryState roles.
# Charts need Category+Y (or X+Y for scatter), tables need Values, cards use Data.
# None means no queryState required (e.g. textbox).
VISUAL_TYPE_ROLES: Dict[str, Optional[set]] = {
    "lineChart": {"Category", "Y"},
    "areaChart": {"Category", "Y"},
    "waterfallChart": {"Category", "Y"},
    "clusteredBarChart": {"Category", "Y"},
    "clusteredColumnChart": {"Category", "Y"},
    "hundredPercentStackedBarChart": {"Category", "Y"},
    "hundredPercentStackedColumnChart": {"Category", "Y"},
    "stackedBarChart": {"Category", "Y"},
    "stackedColumnChart": {"Category", "Y"},
    "funnelChart": {"Category", "Y"},
    "donutChart": {"Category", "Y"},
    "pieChart": {"Category", "Y"},
    "scatterChart": {"X", "Y"},
    "tableEx": {"Values"},
    "pivotTable": {"Rows", "Values"},
    "cardVisual": {"Data"},
    "card": {"Data"},
    "multiRowCard": {"Data"},
    "textbox": None,
    "actionButton": None,
    "shape": None,
    "image": None,
    "slicer": {"Values"},
}

# Characters not allowed in visual folder names (cause path/load issues in Power BI)
_UNSAFE_NAME_CHARS = re.compile(r'[,:\\/]')

# Hex-only pattern that indicates a generated UUID fallback (not a speaking name)
_HEX_ID_PATTERN = re.compile(r'^[0-9a-f]{16,}$')


def validate_visual(visual: Dict[str, Any], canvas_width: int = 1920, canvas_height: int = 1080) -> List[str]:
    """
    Validate a single visual JSON structure.

    Returns list of error messages (empty if valid).
    """
    errors: List[str] = []
    name = visual.get("name", "<unnamed>")

    # 1. Required fields
    if "$schema" not in visual:
        errors.append(f"Visual '{name}': missing $schema")
    if "name" not in visual:
        errors.append(f"Visual: missing 'name' field")
    pos = visual.get("position", {})
    for field in ("x", "y", "height", "width"):
        if field not in pos:
            errors.append(f"Visual '{name}': missing position.{field}")
    inner = visual.get("visual", {})
    if "visualType" not in inner:
        errors.append(f"Visual '{name}': missing visual.visualType")

    # 2. queryState roles
    visual_type = inner.get("visualType", "")
    expected_roles = VISUAL_TYPE_ROLES.get(visual_type)
    if expected_roles is not None:
        query_state = inner.get("query", {}).get("queryState", {})
        actual_roles = set(query_state.keys())
        # "Data" role is only valid for card-type visuals
        if "Data" in actual_roles and visual_type not in ("cardVisual", "card", "multiRowCard"):
            errors.append(
                f"Visual '{name}' ({visual_type}): uses 'Data' queryState role "
                f"(fields land in filter, not field wells). Expected roles: {sorted(expected_roles)}"
            )
        missing = expected_roles - actual_roles
        if missing:
            errors.append(
                f"Visual '{name}' ({visual_type}): missing queryState roles {sorted(missing)}. "
                f"Has: {sorted(actual_roles)}"
            )
    elif expected_roles is None:
        # Visuals like textbox should not have queryState with data roles
        pass

    # 3. Folder-safe name (no commas, colons, backslash, slash)
    if _UNSAFE_NAME_CHARS.search(name):
        errors.append(
            f"Visual '{name}': name contains unsafe characters for folder paths (, : \\ /)"
        )

    # 4. Speaking name (no hex-only UUID fallback)
    if _HEX_ID_PATTERN.match(name):
        errors.append(
            f"Visual '{name}': name looks like a generated hex ID, use a speaking name instead"
        )

    # 5. Canvas bounds
    x = pos.get("x", 0)
    y = pos.get("y", 0)
    w = pos.get("width", 0)
    h = pos.get("height", 0)
    if x + w > canvas_width + 50:  # small tolerance for rounding
        errors.append(
            f"Visual '{name}': x({x}) + width({w}) = {x + w} exceeds canvas width {canvas_width}"
        )
    if y + h > canvas_height + 50:
        errors.append(
            f"Visual '{name}': y({y}) + height({h}) = {y + h} exceeds canvas height {canvas_height}"
        )

    return errors


def validate_page(
    page_structure: Dict[str, Any],
    canvas_width: int = 1920,
    canvas_height: int = 1080,
) -> List[str]:
    """
    Validate all visuals and slicers in a page structure.

    Args:
        page_structure: Dict with 'visuals' and 'slicers' lists
        canvas_width: Canvas width for bounds checking
        canvas_height: Canvas height for bounds checking

    Returns:
        List of error messages (empty if valid)
    """
    errors: List[str] = []

    visuals = page_structure.get("visuals", [])
    slicers = page_structure.get("slicers", [])

    for visual in visuals:
        errors.extend(validate_visual(visual, canvas_width, canvas_height))

    for slicer in slicers:
        errors.extend(validate_visual(slicer, canvas_width, canvas_height))

    return errors
