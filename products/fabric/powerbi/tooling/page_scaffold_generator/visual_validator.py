"""
Visual Validator

Validates generated Power BI visuals before writing to disk.
Catches common errors (wrong queryState roles, invalid names, out-of-bounds positions,
slot whitelist violations) so the generator fails fast with clear messages instead of
producing broken reports.
"""

import re
from typing import Dict, Any, List, Optional


# Mapping: Power BI visualType -> required queryState roles.
# Charts need Category+Y (or X+Y for scatter), tables need Values, cards use Data.
# None means no queryState required (e.g. textbox).
#
# The authoritative source is the vendored authoring-metadata snapshot captured
# from Microsoft's official CLI (ADR 0001). _FALLBACK_ROLES below is the
# pure-Python floor used verbatim when the snapshot is unavailable; the snapshot
# overlays it for every type except the documented local-policy deviations.

# Defensive import: in contexts without the repo root on sys.path (e.g. the
# generator's own unit tests) this is skipped and the fallback table is used.
try:
    from tooling.report_quality import authoring_metadata as _authoring_metadata
except Exception:  # pragma: no cover - import-context dependent
    _authoring_metadata = None


_FALLBACK_ROLES: Dict[str, Optional[set]] = {
    "lineChart": {"Category", "Y"},
    "areaChart": {"Category", "Y"},
    "waterfallChart": {"Category", "Y"},
    "clusteredBarChart": {"Category", "Y"},
    # Category is optional for clusteredColumnChart: each Y-measure renders as one bar
    # (no category axis = PVM decomposition view, e.g. Price/Volume/Mix as separate bars)
    "clusteredColumnChart": {"Y"},
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

# Intentional local deviations from Microsoft's official requiredRoles. These keys
# keep their _FALLBACK_ROLES value and are NOT overwritten by the snapshot:
#   clusteredColumnChart -> {Y}            (Category optional: PVM decomposition view)
#   pivotTable           -> {Rows, Values} (stricter than official {Values})
#   card / multiRowCard  -> {Data}         (legacy cards driven like cardVisual)
#   stacked* / funnelChart                 (absent from the official catalogue v0.1.1)
_LOCAL_ROLE_POLICY = frozenset({
    "clusteredColumnChart",
    "pivotTable",
    "card",
    "multiRowCard",
    "stackedBarChart",
    "stackedColumnChart",
    "funnelChart",
})


def _build_visual_type_roles() -> Dict[str, Optional[set]]:
    """Snapshot-sourced role table with documented local deviations and a floor.

    Equals _FALLBACK_ROLES exactly today (the snapshot agrees for every non-policy
    type -- guarded by tests); sourcing it from the snapshot keeps it in sync with
    the official metadata and makes drift detectable.
    """
    table: Dict[str, Optional[set]] = dict(_FALLBACK_ROLES)
    am = _authoring_metadata
    if am is None or not am.is_available():
        return table
    for visual_type in table:
        if visual_type in _LOCAL_ROLE_POLICY:
            continue  # keep the deliberate local value
        required = set(am.required_roles(visual_type))
        if required:  # snapshot knows this type -> use the authoritative roles
            table[visual_type] = required
    return table


VISUAL_TYPE_ROLES: Dict[str, Optional[set]] = _build_visual_type_roles()

# ─── Slot whitelist ───────────────────────────────────────────────────────────

# Abstract visual type → PBI visualType strings.
# Source: core/templates/page_templates/Abstract_Visual_Types.md
_ABSTRACT_TO_PBI: Dict[str, set] = {
    "line_chart":          {"lineChart"},
    "area_chart":          {"areaChart"},
    # small_multiples: implemented as a standard line/bar chart with the Power BI
    # "Small multiples" field well populated. The underlying visualType is unchanged;
    # governance enforcement is via the slot mapping rule (identical scale required).
    "small_multiples":     {"lineChart", "clusteredBarChart"},
    "waterfall":           {"waterfallChart"},
    "bar_chart_horizontal":{"clusteredBarChart"},
    "bar_chart_column":    {"clusteredColumnChart"},
    "stacked_bar_100pct":  {"hundredPercentStackedBarChart", "hundredPercentStackedColumnChart",
                            "stackedBarChart", "stackedColumnChart"},
    "scatter_plot":        {"scatterChart"},
    "funnel_chart":        {"funnelChart"},
    "kpi_card":            {"cardVisual", "card"},
    "kpi_card_hero":       {"cardVisual"},
    "kpi_card_compact":    {"cardVisual"},
    "status_tile":         {"cardVisual"},
    "table_with_databars": {"tableEx"},
    "matrix":              {"pivotTable"},
    "slicer_range":        {"slicer"},
    "slicer_dropdown":     {"slicer"},
    "slicer_list":         {"slicer"},
    "smart_narrative":     {"textbox"},
    "action_card":         {"actionButton"},
    "sparkline":           {"lineChart"},
}

# PBI visual types that are globally disallowed regardless of slot.
# Source: core/templates/page_templates/governance/Visual_Whitelist.md
_GLOBALLY_DISALLOWED_PBI_TYPES = frozenset({
    "pieChart", "donutChart", "gauge", "gaugeVisual",
    "radarChart", "treemap", "filled_map", "ribbonChart",
})

# Characters not allowed in visual folder names (cause path/load issues in Power BI)
_UNSAFE_NAME_CHARS = re.compile(r'[,:\\/]')

# Hex-only pattern that indicates a generated UUID fallback (not a speaking name)
_HEX_ID_PATTERN = re.compile(r'^[0-9a-f]{16,}$')


def validate_slot_compliance(
    slot_id: str,
    pbi_visual_type: str,
    template_id: Optional[str] = None,
    slot_mapping: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """
    Check whether a PBI visual type is permitted for a given slot.

    Args:
        slot_id:       Canonical slot name (e.g. "Main_1", "KPI_Cards").
        pbi_visual_type: Power BI visualType string (e.g. "lineChart").
        template_id:   Page template (T1–T4). If provided, checks allowed_templates.
        slot_mapping:  Parsed visual_slot_mapping.yaml dict. If None, only global
                       disallowed check runs (no per-slot rules).

    Returns:
        List of error strings. Empty = compliant.
    """
    errors: List[str] = []

    # 1. Global hard disallowed (governance: never use, any slot)
    if pbi_visual_type in _GLOBALLY_DISALLOWED_PBI_TYPES:
        errors.append(
            f"Slot '{slot_id}': '{pbi_visual_type}' is globally disallowed "
            f"(governance hard rule — see Visual_Whitelist.md)"
        )
        return errors  # per-slot checks irrelevant if globally forbidden

    if not slot_mapping:
        return errors

    slots = slot_mapping.get("slots", {})
    slot_def = slots.get(slot_id)
    if slot_def is None:
        return errors  # unknown slot — unknown slots pass (custom slots allowed)

    # 2. Template constraint
    if template_id is not None:
        allowed_templates = slot_def.get("allowed_templates") or []
        if allowed_templates and template_id not in allowed_templates:
            errors.append(
                f"Slot '{slot_id}': not allowed on template '{template_id}'. "
                f"Allowed: {allowed_templates}"
            )

    # 3. Per-slot disallowed abstract types → PBI types
    vt_def = slot_def.get("visual_types") or {}
    for abstract_type in (vt_def.get("disallowed") or []):
        pbi_equivalents = _ABSTRACT_TO_PBI.get(abstract_type, set())
        if pbi_visual_type in pbi_equivalents:
            errors.append(
                f"Slot '{slot_id}': '{pbi_visual_type}' is disallowed "
                f"(abstract type '{abstract_type}' is in this slot's disallowed list)"
            )

    return errors


def validate_visual(
    visual: Dict[str, Any],
    canvas_width: int = 1920,
    canvas_height: int = 1080,
    slot_mapping: Optional[Dict[str, Any]] = None,
    template_id: Optional[str] = None,
) -> List[str]:
    """
    Validate a single visual JSON structure.

    Args:
        visual:        Visual JSON dict (as generated by VisualBuilder).
        canvas_width:  Canvas width for bounds checking.
        canvas_height: Canvas height for bounds checking.
        slot_mapping:  Parsed visual_slot_mapping.yaml. When provided, slot whitelist
                       compliance is checked (allowed_templates, disallowed visual types).
        template_id:   Page template (T1–T4) for slot template constraint check.

    Returns:
        List of error messages. Empty = valid.
    """
    errors: List[str] = []
    name = visual.get("name", "<unnamed>")

    # 1. Required fields
    if "$schema" not in visual:
        errors.append(f"Visual '{name}': missing $schema")
    if "name" not in visual:
        errors.append("Visual: missing 'name' field")
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
    query_state = inner.get("query", {}).get("queryState", {})
    actual_roles = set(query_state.keys())
    if expected_roles is not None:
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
        # Authoritative unknown-role check (ADR 0001): flag roles that are not valid
        # for this visual type per the official metadata snapshot. Skipped when the
        # snapshot is unavailable or does not cover this type (local-only types).
        if _authoring_metadata is not None and _authoring_metadata.is_available():
            known_roles = set(_authoring_metadata.roles(visual_type))
            unknown_roles = actual_roles - known_roles
            if known_roles and unknown_roles:
                errors.append(
                    f"Visual '{name}' ({visual_type}): unknown queryState roles "
                    f"{sorted(unknown_roles)} (valid roles: {sorted(known_roles)})."
                )
    else:
        # No-data-role visuals (textbox, shape, image, actionButton) must not carry a
        # data queryState -- it is invalid per the official metadata (PBIR_ROLE_UNKNOWN).
        if query_state:
            errors.append(
                f"Visual '{name}' ({visual_type}): has queryState roles "
                f"{sorted(actual_roles)} but '{visual_type}' takes no data roles. Remove the query."
            )

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

    # 6. Slot whitelist compliance (only when slot_mapping provided)
    if slot_mapping is not None and visual_type:
        errors.extend(
            validate_slot_compliance(name, visual_type, template_id=template_id, slot_mapping=slot_mapping)
        )

    return errors


def validate_page(
    page_structure: Dict[str, Any],
    canvas_width: int = 1920,
    canvas_height: int = 1080,
    slot_mapping: Optional[Dict[str, Any]] = None,
    template_id: Optional[str] = None,
) -> List[str]:
    """
    Validate all visuals and slicers in a page structure.

    Args:
        page_structure: Dict with 'visuals' and 'slicers' lists.
        canvas_width:   Canvas width for bounds checking.
        canvas_height:  Canvas height for bounds checking.
        slot_mapping:   Parsed visual_slot_mapping.yaml for slot whitelist checks.
        template_id:    Page template (T1–T4) for template constraint checks.

    Returns:
        List of error messages (empty if valid).
    """
    errors: List[str] = []

    visuals = page_structure.get("visuals", [])
    slicers = page_structure.get("slicers", [])

    for visual in visuals:
        errors.extend(validate_visual(visual, canvas_width, canvas_height, slot_mapping, template_id))

    for slicer in slicers:
        errors.extend(validate_visual(slicer, canvas_width, canvas_height, slot_mapping, template_id))

    return errors
