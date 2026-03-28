"""
BrandSpec → CSS custom properties converter.

Single responsibility: translate a validated BrandSpec dict into a CSS
:root { } block string, following the mapping defined in:
  core/brand/tool_derivations/css_mapping.md

Pure function — no file I/O, no side effects.
The caller (derive_brand_artifacts.py) handles writing the result to disk.
"""

from __future__ import annotations

from typing import Any

from ._color_math import with_opacity_rgba

# Fluid type scale clamp values per step (from css_mapping.md).
# Format: (min_rem, preferred_expression, max_rem)
_TYPE_SCALE_CLAMP: dict[str, tuple[str, str, str]] = {
    "xs":  ("0.625rem", "0.6rem + 0.1vw",  "0.75rem"),
    "sm":  ("0.75rem",  "0.7rem + 0.15vw", "0.875rem"),
    "md":  ("0.875rem", "0.85rem + 0.2vw", "1rem"),
    "lg":  ("1rem",     "0.95rem + 0.25vw","1.125rem"),
    "xl":  ("1.125rem", "1.1rem + 0.3vw",  "1.375rem"),
    "2xl": ("1.375rem", "1.3rem + 0.5vw",  "1.75rem"),
    "3xl": ("1.75rem",  "1.6rem + 0.8vw",  "2.5rem"),
}

# Role → type scale step mapping (from css_mapping.md and BrandSpec schema).
_ROLE_TO_STEP: dict[str, str] = {
    "kpi_value":    "3xl",
    "kpi_label":    "sm",
    "kpi_delta":    "md",
    "kpi_period":   "xs",
    "chart_title":  "md",
    "axis_label":   "xs",
    "legend_label": "xs",
    "body":         "md",
    "caption":      "xs",
    "heading_1":    "2xl",
    "heading_2":    "xl",
    "heading_3":    "lg",
    "table_header": "sm",
    "table_cell":   "sm",
}

# CSS property name for each role (underscores → hyphens, prefixed).
def _role_css_name(role: str) -> str:
    return f"--brand-type-{role.replace('_', '-')}"


def spec_to_css(spec: dict[str, Any], source_hint: str = "") -> str:
    """
    Convert a validated BrandSpec dict to a CSS :root { } string.

    Args:
        spec: Validated BrandSpec dict (from loader.load_brand_spec).
        source_hint: Optional path string shown in the generated file header comment.

    Returns:
        Complete CSS string with a :root block containing all brand custom properties.
    """
    identity = spec.get("identity", {})
    color = spec["color"]
    typo = spec["typography"]
    spacing = spec.get("spacing", {}).get("scale", {})
    border = spec.get("border", {})
    shadow = spec.get("shadow", {})

    primary = color["primary"]
    secondary = color["secondary"]
    sem = color["semantic"]
    neutral = color["neutral_scale"]
    font = typo["font_family"]

    brand_name = identity.get("brand_name", identity.get("brand_id", "Brand"))
    brand_id = identity.get("brand_id", "brand")
    source = source_hint or f"showcases/{brand_id}/brand/brand_spec.yaml"

    lines: list[str] = [
        f"/* {'─' * 41}",
        f"   Brand: {brand_name} ({brand_id})",
        f"   Generated from: {source}",
        f"   Schema: core/brand/BrandSpec.schema.yaml v1.0",
        f"   {'─' * 41} */",
        "",
        ":root {",
    ]

    lines += _color_section(primary, secondary, sem, neutral)
    lines += _typography_section(font, typo.get("type_scale", {}))
    lines += _spacing_section(spacing)
    lines += _border_section(border)
    lines += _shadow_section(shadow)

    lines.append("}")
    lines.append("")
    return "\n".join(lines)


# ─────────────────────────────────────────────
# Section builders — each returns list[str] of CSS lines
# ─────────────────────────────────────────────

def _color_section(
    primary: str,
    secondary: str,
    sem: dict[str, Any],
    neutral: dict[str, str],
) -> list[str]:
    pos = sem["positive"]["color"]
    neg = sem["negative"]["color"]
    warn = sem["warning"]["color"]
    neut = sem["neutral"]["color"]

    return [
        "  /* Brand Colors */",
        f"  --brand-color-primary:          {primary};",
        f"  --brand-color-secondary:        {secondary};",
        f"  --brand-color-primary-subtle:   {with_opacity_rgba(primary, 0.10)};",
        f"  --brand-color-secondary-subtle: {with_opacity_rgba(secondary, 0.10)};",
        "",
        "  /* Semantic Signals */",
        f"  --brand-color-positive:         {pos};",
        f"  --brand-color-negative:         {neg};",
        f"  --brand-color-warning:          {warn};",
        f"  --brand-color-neutral:          {neut};",
        f"  --brand-color-positive-bg:      {with_opacity_rgba(pos, 0.15)};",
        f"  --brand-color-negative-bg:      {with_opacity_rgba(neg, 0.15)};",
        f"  --brand-color-warning-bg:       {with_opacity_rgba(warn, 0.15)};",
        "",
        "  /* Neutral Scale */",
        f"  --brand-neutral-50:             {neutral.get('50',  '#FAFAFA')};",
        f"  --brand-neutral-100:            {neutral.get('100', '#F3F2F1')};",
        f"  --brand-neutral-200:            {neutral.get('200', '#E1DFDD')};",
        f"  --brand-neutral-400:            {neutral.get('400', '#A19F9D')};",
        f"  --brand-neutral-700:            {neutral.get('700', '#3B3A39')};",
        f"  --brand-neutral-900:            {neutral.get('900', '#201F1E')};",
        "",
        "  /* Semantic Role Aliases */",
        "  --brand-color-background:       var(--brand-neutral-50);",
        "  --brand-color-surface:          var(--brand-neutral-100);",
        "  --brand-color-border:           var(--brand-neutral-200);",
        "  --brand-color-muted:            var(--brand-neutral-400);",
        "  --brand-color-body:             var(--brand-neutral-700);",
        "  --brand-color-heading:          var(--brand-neutral-900);",
        "",
    ]


def _typography_section(
    font: dict[str, Any],
    type_scale: dict[str, Any],
) -> list[str]:
    primary_font = font.get("primary", "system-ui, sans-serif")
    secondary_font = font.get("secondary") or f"var(--brand-font-primary)"
    mono_font = font.get("monospace", "monospace")

    lines: list[str] = [
        "  /* Typography */",
        f"  --brand-font-primary:   {primary_font};",
        f"  --brand-font-secondary: {secondary_font};",
        f"  --brand-font-mono:      {mono_font};",
        "",
        "  /* Type Scale (fluid clamp) */",
    ]

    for step, (min_r, pref, max_r) in _TYPE_SCALE_CLAMP.items():
        lines.append(f"  --brand-type-{step}:{_pad(step)}clamp({min_r}, {pref}, {max_r});")

    lines += [
        "",
        "  /* Type Role Aliases */",
    ]
    for role, step in _ROLE_TO_STEP.items():
        css_name = _role_css_name(role)
        lines.append(f"  {css_name}:{_pad_role(role)}var(--brand-type-{step});")

    lines.append("")
    return lines


def _spacing_section(scale: dict[str, Any]) -> list[str]:
    steps = ["xs", "sm", "md", "lg", "xl", "2xl", "3xl"]
    defaults = {"xs": 4, "sm": 8, "md": 16, "lg": 24, "xl": 32, "2xl": 48, "3xl": 64}
    lines = ["  /* Spacing */"]
    for step in steps:
        val = scale.get(step, defaults.get(step, 0))
        lines.append(f"  --brand-spacing-{step}:{_pad_sp(step)}{val}px;")
    lines.append("")
    return lines


def _border_section(border: dict[str, Any]) -> list[str]:
    radius = border.get("radius", {})
    width = border.get("width", {})
    return [
        "  /* Borders */",
        f"  --brand-radius-none:     {radius.get('none', 0)}px;",
        f"  --brand-radius-sm:       {radius.get('sm', 2)}px;",
        f"  --brand-radius-md:       {radius.get('md', 4)}px;",
        f"  --brand-radius-lg:       {radius.get('lg', 8)}px;",
        f"  --brand-radius-full:     {radius.get('full', 9999)}px;",
        f"  --brand-border-hairline: {width.get('hairline', 1)}px;",
        f"  --brand-border-thin:     {width.get('thin', 1)}px;",
        f"  --brand-border-medium:   {width.get('medium', 2)}px;",
        "",
    ]


def _shadow_section(shadow: dict[str, Any]) -> list[str]:
    return [
        "  /* Shadows */",
        f"  --brand-shadow-none:   {shadow.get('none', 'none')};",
        f"  --brand-shadow-low:    {shadow.get('low', 'none')};",
        f"  --brand-shadow-medium: {shadow.get('medium', 'none')};",
        f"  --brand-shadow-high:   {shadow.get('high', 'none')};",
    ]


# ─────────────────────────────────────────────
# Alignment helpers (cosmetic column padding)
# ─────────────────────────────────────────────

def _pad(step: str, width: int = 6) -> str:
    return " " * max(1, width - len(step))


def _pad_role(role: str, width: int = 16) -> str:
    css = role.replace("_", "-")
    return " " * max(1, width - len(css))


def _pad_sp(step: str, width: int = 5) -> str:
    return " " * max(1, width - len(step))
