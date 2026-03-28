"""
BrandSpec → Power BI theme JSON converter.

Single responsibility: translate a validated BrandSpec dict into a
Power BI theme JSON dict, following the mapping defined in:
  core/brand/tool_derivations/powerbi_mapping.md

Pure function — no file I/O, no side effects.
The caller (derive_brand_artifacts.py) handles writing the result to disk.
"""

from __future__ import annotations

from typing import Any

from ._color_math import (
    derive_data_palette,
    lighten,
    with_opacity_hex,
)

# Power BI rem-to-pt conversion base.
# PBI uses 12px as 1rem equivalent. 1pt = 1.333px → 12px / 1.333 ≈ 9pt per rem.
_PBI_PT_PER_REM = 9.0

# Minimum safe pt sizes per PBI rendering constraints (FitToPage scaling).
_PBI_PT_FLOOR = {
    "xs":  10,
    "sm":  10,
    "md":  12,
    "lg":  12,
    "xl":  12,
    "2xl": 14,
    "3xl": 18,
}

# Visual type selectors that receive font settings.
# "*" covers all; specific types override for critical readability minima.
_FONT_VISUAL_TYPES = [
    "*",
    "tableEx",
    "matrix",
    "cardVisual",
    "card",
    "slicer",
    "textbox",
]


def spec_to_pbi_theme(
    spec: dict[str, Any],
    concept: str = "Monochromatic",
    canvas_profile: str = "powerbi_design_base",
) -> dict[str, Any]:
    """
    Convert a validated BrandSpec dict to a Power BI theme JSON dict.

    Args:
        spec: Validated BrandSpec dict (from loader.load_brand_spec).
        concept: Color palette concept — "Monochromatic", "NeutralAccent", or "Divergent".
        canvas_profile: BrandSpec canvas profile key to derive font size delta.

    Returns:
        Dict ready to be serialised as a Power BI theme JSON file.
    """
    color = spec["color"]
    typo = spec["typography"]
    pbi_min = typo["tool_minimums"]["powerbi"]

    primary = color["primary"]
    secondary = color["secondary"]
    sem = color["semantic"]
    neutral = color["neutral_scale"]
    font_stack = typo["font_family"]["primary"]

    # Canvas font delta (production canvas adds +2pt)
    font_delta = _font_delta_for_profile(spec, canvas_profile)

    data_colors = derive_data_palette(primary, secondary, concept)
    font_sizes = _derive_font_sizes(typo, pbi_min, font_delta)

    brand_id = spec.get("identity", {}).get("brand_id", "brand")
    brand_name = spec.get("identity", {}).get("brand_name", brand_id)
    theme_name = f"{brand_name}__{concept}__{canvas_profile}__{primary}"

    return {
        "name": theme_name,
        "$schema": "https://raw.githubusercontent.com/microsoft/powerbi-desktop-samples/main/Report%20Theme%20JSON%20Schema/reportThemeSchema-2.145.json",
        # Data colors — chart series palette
        "dataColors": data_colors,
        # Semantic signal colors
        "good":    sem["positive"]["color"],
        "bad":     sem["negative"]["color"],
        "neutral": sem["neutral"]["color"],
        "maximum": lighten(sem["positive"]["color"], 0.40),
        "minimum": lighten(sem["negative"]["color"], 0.40),
        "null":    neutral["400"],
        # Surface colors
        "background":  neutral["100"],
        "foreground":  neutral["900"],
        "tableAccent": with_opacity_hex(primary, 0.10),
        # Visual styles
        "visualStyles": _build_visual_styles(font_stack, font_sizes, neutral, sem),
    }


# ─────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────

def _font_delta_for_profile(spec: dict[str, Any], profile_key: str) -> int:
    """Return the font_size_delta_pt for the given canvas profile (default 0)."""
    profiles = spec.get("canvas_profiles", {})
    profile = profiles.get(profile_key, {})
    return int(profile.get("font_size_delta_pt", 0))


def _rem_to_pt(size_rem: float, delta: int) -> int:
    """
    Convert a BrandSpec rem value to Power BI pt, applying the canvas delta
    and the per-step minimum safe floor.
    """
    raw_pt = size_rem * _PBI_PT_PER_REM
    return int(raw_pt) + delta


def _derive_font_sizes(
    typo: dict[str, Any],
    pbi_min: dict[str, Any],
    delta: int,
) -> dict[str, int]:
    """
    Return a dict mapping type scale step names to pt sizes for PBI,
    applying rem→pt conversion, per-step floors, and canvas delta.
    """
    type_scale = typo.get("type_scale", {})
    body_floor = int(pbi_min.get("body_pt", 12))
    label_floor = int(pbi_min.get("label_pt", 10))
    kpi_floor = int(pbi_min.get("kpi_pt", 18))

    sizes: dict[str, int] = {}
    for step, spec_step in type_scale.items():
        rem = float(spec_step.get("size_rem", 1.0))
        raw = _rem_to_pt(rem, delta)
        schema_floor = _PBI_PT_FLOOR.get(step, 10)
        # Apply the most restrictive floor for each role
        if step == "3xl":
            sizes[step] = max(raw, kpi_floor, schema_floor)
        elif step in ("xs", "sm"):
            sizes[step] = max(raw, label_floor, schema_floor)
        else:
            sizes[step] = max(raw, body_floor, schema_floor)
    return sizes


def _build_visual_styles(
    font_stack: str,
    font_sizes: dict[str, int],
    neutral: dict[str, str],
    sem: dict[str, Any],
) -> dict[str, Any]:
    """
    Build the visualStyles block that applies font and color defaults
    across all visual types via PBI's wildcard selector pattern.
    """
    body_pt = font_sizes.get("md", 12)
    label_pt = font_sizes.get("xs", 10)
    kpi_pt = font_sizes.get("3xl", 18)
    heading_pt = font_sizes.get("2xl", 14)

    # Global wildcard — applies to all visuals unless overridden below
    global_style: dict[str, Any] = {
        "*": {
            "fontFamily": [{"value": font_stack}],
            "fontSize":   [{"value": body_pt}],
        }
    }

    return {
        # Global font defaults
        "*": global_style,
        # KPI card — callout value uses hero size
        "cardVisual": {
            "*": {
                "calloutValue": [
                    {"value": {"fontSize": kpi_pt, "fontFamily": font_stack}}
                ],
                "labels": [
                    {"value": {"fontSize": label_pt, "fontFamily": font_stack}}
                ],
            }
        },
        # Legacy card visual
        "card": {
            "*": {
                "labels":     [{"value": {"fontSize": kpi_pt, "fontFamily": font_stack}}],
                "categoryLabels": [{"value": {"fontSize": label_pt, "fontFamily": font_stack}}],
            }
        },
        # Table and matrix — body + header sizes
        "tableEx": {
            "*": {
                "values":  [{"value": {"fontSize": body_pt, "fontFamily": font_stack}}],
                "columnHeaders": [{"value": {"fontSize": body_pt, "fontFamily": font_stack}}],
                "background": [{"value": {"color": neutral["50"]}}],
            }
        },
        "matrix": {
            "*": {
                "values":  [{"value": {"fontSize": body_pt, "fontFamily": font_stack}}],
                "columnHeaders": [{"value": {"fontSize": body_pt, "fontFamily": font_stack}}],
                "rowHeaders":    [{"value": {"fontSize": body_pt, "fontFamily": font_stack}}],
                "background":    [{"value": {"color": neutral["50"]}}],
            }
        },
        # Axis labels (chart visuals)
        "lineChart":     _axis_style(label_pt, font_stack),
        "barChart":      _axis_style(label_pt, font_stack),
        "clusteredBarChart": _axis_style(label_pt, font_stack),
        "columnChart":   _axis_style(label_pt, font_stack),
        "areaChart":     _axis_style(label_pt, font_stack),
        "scatterChart":  _axis_style(label_pt, font_stack),
        # Slicers
        "slicer": {
            "*": {
                "items": [{"value": {"fontSize": body_pt, "fontFamily": font_stack}}],
                "header": [{"value": {"fontSize": label_pt, "fontFamily": font_stack}}],
            }
        },
        # Text boxes / smart narrative
        "textbox": {
            "*": {
                "paragraphs": [{"value": {"fontSize": body_pt, "fontFamily": font_stack}}]
            }
        },
    }


def _axis_style(label_pt: int, font_stack: str) -> dict[str, Any]:
    """Return a visualStyles sub-dict for chart axis label formatting."""
    return {
        "*": {
            "categoryAxis": [{"value": {"fontSize": label_pt, "fontFamily": font_stack}}],
            "valueAxis":    [{"value": {"fontSize": label_pt, "fontFamily": font_stack}}],
            "legend":       [{"value": {"fontSize": label_pt, "fontFamily": font_stack}}],
        }
    }
