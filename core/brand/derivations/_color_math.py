"""
Pure color math utilities for BrandSpec derivations.

All functions are stateless and side-effect-free. No file I/O.
Used by pbi_theme.py and css_variables.py — never imported directly by callers.
"""

from __future__ import annotations

import colorsys


# ─────────────────────────────────────────────
# Hex parse / serialize
# ─────────────────────────────────────────────

def parse_hex(hex_color: str) -> tuple[int, int, int]:
    """Return (r, g, b) ints 0–255 from a hex string (#RGB or #RRGGBB)."""
    h = hex_color.strip().lstrip("#")
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    if len(h) != 6:
        raise ValueError(f"Invalid hex color: {hex_color!r}")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def to_hex(r: int, g: int, b: int) -> str:
    """Return #RRGGBB string from (r, g, b) ints 0–255."""
    return "#{:02X}{:02X}{:02X}".format(
        max(0, min(255, r)),
        max(0, min(255, g)),
        max(0, min(255, b)),
    )


# ─────────────────────────────────────────────
# HLS transforms (all return #RRGGBB strings)
# ─────────────────────────────────────────────

def lighten(hex_color: str, amount: float) -> str:
    """
    Increase lightness by `amount` (0.0–1.0 fraction of remaining headroom).
    E.g. lighten("#107C10", 0.3) moves lightness 30% closer to white.
    """
    r, g, b = parse_hex(hex_color)
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    l = l + (1.0 - l) * amount
    r2, g2, b2 = colorsys.hls_to_rgb(h, l, s)
    return to_hex(round(r2 * 255), round(g2 * 255), round(b2 * 255))


def darken(hex_color: str, amount: float) -> str:
    """
    Decrease lightness by `amount` (0.0–1.0 fraction of current lightness).
    E.g. darken("#107C10", 0.2) moves lightness 20% closer to black.
    """
    r, g, b = parse_hex(hex_color)
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    l = l * (1.0 - amount)
    r2, g2, b2 = colorsys.hls_to_rgb(h, l, s)
    return to_hex(round(r2 * 255), round(g2 * 255), round(b2 * 255))


def rotate_hue(hex_color: str, degrees: float) -> str:
    """Rotate hue by `degrees` (positive = clockwise on color wheel)."""
    r, g, b = parse_hex(hex_color)
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    h = (h + degrees / 360.0) % 1.0
    r2, g2, b2 = colorsys.hls_to_rgb(h, l, s)
    return to_hex(round(r2 * 255), round(g2 * 255), round(b2 * 255))


def with_opacity_hex(hex_color: str, alpha: float) -> str:
    """
    Return an 8-digit hex string (#RRGGBBAA) with the given alpha (0.0–1.0).
    Use when the target format supports 8-digit hex (CSS level 4, some PBI props).
    """
    r, g, b = parse_hex(hex_color)
    a = max(0, min(255, round(alpha * 255)))
    return "#{:02X}{:02X}{:02X}{:02X}".format(r, g, b, a)


def with_opacity_rgba(hex_color: str, alpha: float) -> str:
    """Return an rgba(r, g, b, a) CSS string."""
    r, g, b = parse_hex(hex_color)
    return f"rgba({r}, {g}, {b}, {alpha:.2f})"


# ─────────────────────────────────────────────
# Data palette derivation
# ─────────────────────────────────────────────

def derive_data_palette(
    primary: str,
    secondary: str,
    concept: str = "Monochromatic",
) -> list[str]:
    """
    Derive an 8-color data palette from primary and secondary brand colors.

    Concept rules (from powerbi_mapping.md):
      Monochromatic — all colors derived from primary via lightness/saturation steps.
      NeutralAccent  — primary + secondary; remaining 6 are tints/shades of both.
      Divergent      — primary at one pole, secondary at other; neutral grey midpoint.

    Returns a list of exactly 8 hex color strings.
    """
    concept_key = concept.lower().replace(" ", "").replace("_", "")

    if concept_key == "monochromatic":
        return _palette_monochromatic(primary)
    elif concept_key == "divergent":
        return _palette_divergent(primary, secondary)
    else:
        # NeutralAccent (default for multi-color)
        return _palette_neutral_accent(primary, secondary)


def _palette_monochromatic(primary: str) -> list[str]:
    """8 steps: primary + 7 lightness/saturation variations."""
    r, g, b = parse_hex(primary)
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)

    def make(lightness: float, saturation: float) -> str:
        r2, g2, b2 = colorsys.hls_to_rgb(h, lightness, saturation)
        return to_hex(round(r2 * 255), round(g2 * 255), round(b2 * 255))

    return [
        primary,                        # [0] base
        make(min(l + 0.20, 0.95), s),   # [1] lighter
        make(min(l + 0.35, 0.95), s),   # [2] lightest tint
        make(max(l - 0.15, 0.05), s),   # [3] slightly darker
        make(max(l - 0.30, 0.05), s),   # [4] shade
        make(l, max(s - 0.30, 0.0)),    # [5] desaturated
        make(min(l + 0.12, 0.95), max(s - 0.15, 0.0)),  # [6] muted tint
        make(max(l - 0.45, 0.05), s),   # [7] darkest shade
    ]


def _palette_neutral_accent(primary: str, secondary: str) -> list[str]:
    """8 steps: primary, secondary, tints and shades of both."""
    return [
        primary,                     # [0] primary
        secondary,                   # [1] secondary
        lighten(primary,   0.25),    # [2] primary tint
        lighten(secondary, 0.25),    # [3] secondary tint
        rotate_hue(primary, 30),     # [4] primary analogous
        rotate_hue(secondary, -30),  # [5] secondary complementary
        darken(primary,   0.20),     # [6] primary shade
        darken(secondary, 0.20),     # [7] secondary shade
    ]


def _palette_divergent(primary: str, secondary: str) -> list[str]:
    """8 steps: primary pole → neutral mid → secondary pole."""
    neutral_mid = "#A19F9D"
    return [
        primary,
        lighten(primary, 0.35),
        lighten(primary, 0.60),
        neutral_mid,
        lighten(secondary, 0.60),
        lighten(secondary, 0.35),
        secondary,
        darken(secondary, 0.20),
    ]
