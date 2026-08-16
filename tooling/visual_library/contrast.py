"""contrast.py — the Visual Library colour-safety checker (zero-dependency, deterministic).

Extends the token governance from text/fill-vs-background contrast to SERIES-vs-SERIES
discriminability under colour-vision deficiency (CVD) — the gap the roadmap named: a palette
whose neighbours stay distinguishable for deuteranopia / protanopia / tritanopia, plus an honest
pattern/shape fallback once a categorical palette is exhausted.

Pure math, no third-party deps (mirrors render.py/resolve.py), so it ships in the Workflow-B bundle
and runs anywhere Python does:
  - WCAG 2.1 relative luminance + contrast ratio (SC 1.4.3 text, SC 1.4.11 non-text)
  - Machado, Oliveira & Fernandes (2009) CVD simulation matrices (severity 1.0), applied in
    linear-RGB per DaltonLens/colorspacious convention
  - CIEDE2000 perceptual colour difference (CIE 2001) in CIELAB (D65)

CLI:
  contrast.py ratio <fg_hex> <bg_hex>              # WCAG contrast ratio
  contrast.py palette [n] [--name okabe_ito|tol_bright]   # first n CVD-safe series colours + fallback
  contrast.py check <hex> <hex> [<hex> ...]        # min pairwise ΔE under normal + 3 CVD sims
"""
from __future__ import annotations

import sys

# --------------------------------------------------------------------------- #
# sRGB <-> linear, hex
# --------------------------------------------------------------------------- #

def hex_to_rgb(h: str) -> "tuple[int, int, int]":
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def rgb_to_hex(rgb: "tuple[float, float, float]") -> str:
    return "#" + "".join(f"{max(0, min(255, round(c))):02X}" for c in rgb)


def _srgb_to_linear(c: float) -> float:
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(c: float) -> float:
    c = max(0.0, min(1.0, c))
    v = 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055
    return v * 255.0


# --------------------------------------------------------------------------- #
# WCAG contrast
# --------------------------------------------------------------------------- #

def relative_luminance(h: str) -> float:
    r, g, b = (_srgb_to_linear(c) for c in hex_to_rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg: str, bg: str) -> float:
    l1, l2 = relative_luminance(fg), relative_luminance(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return round((hi + 0.05) / (lo + 0.05), 2)


# --------------------------------------------------------------------------- #
# CVD simulation — Machado et al. 2009, severity 1.0 (applied in linear RGB)
# --------------------------------------------------------------------------- #

_MACHADO = {
    "protan": ((0.152286, 1.052583, -0.204868),
               (0.114503, 0.786281, 0.099216),
               (-0.003882, -0.048116, 1.051998)),
    "deutan": ((0.367322, 0.860646, -0.227968),
               (0.280085, 0.672501, 0.047413),
               (-0.011820, 0.042940, 0.968881)),
    "tritan": ((1.255528, -0.076749, -0.178779),
               (-0.078411, 0.930809, 0.147602),
               (0.004733, 0.691367, 0.303900)),
}
CVD_KINDS = ("protan", "deutan", "tritan")


def simulate_cvd(h: str, kind: str) -> str:
    """Simulate how a colour appears under `kind` CVD (protan|deutan|tritan)."""
    if kind not in _MACHADO:
        raise ValueError(f"unknown CVD kind '{kind}' (use one of {CVD_KINDS})")
    m = _MACHADO[kind]
    lin = [_srgb_to_linear(c) for c in hex_to_rgb(h)]
    out = [sum(m[i][j] * lin[j] for j in range(3)) for i in range(3)]
    return rgb_to_hex(tuple(_linear_to_srgb(c) for c in out))


# --------------------------------------------------------------------------- #
# CIELAB (D65) + CIEDE2000
# --------------------------------------------------------------------------- #

def _hex_to_lab(h: str) -> "tuple[float, float, float]":
    r, g, b = (_srgb_to_linear(c) for c in hex_to_rgb(h))
    # linear sRGB -> XYZ (D65)
    x = 0.4124564 * r + 0.3575761 * g + 0.1804375 * b
    y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    z = 0.0193339 * r + 0.1191920 * g + 0.9503041 * b
    xn, yn, zn = 0.95047, 1.0, 1.08883  # D65 reference white

    def f(t: float) -> float:
        return t ** (1 / 3) if t > 216 / 24389 else (841 / 108) * t + 4 / 29

    fx, fy, fz = f(x / xn), f(y / yn), f(z / zn)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def delta_e_ciede2000(lab1: tuple, lab2: tuple) -> float:
    import math
    L1, a1, b1 = lab1
    L2, a2, b2 = lab2
    avg_Lp = (L1 + L2) / 2
    C1 = math.hypot(a1, b1)
    C2 = math.hypot(a2, b2)
    avg_C = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(avg_C ** 7 / (avg_C ** 7 + 25 ** 7))) if avg_C > 0 else 0.5
    a1p, a2p = a1 * (1 + G), a2 * (1 + G)
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    avg_Cp = (C1p + C2p) / 2

    def _hp(ap: float, b: float) -> float:
        if ap == 0 and b == 0:
            return 0.0
        h = math.degrees(math.atan2(b, ap))
        return h + 360 if h < 0 else h

    h1p, h2p = _hp(a1p, b1), _hp(a2p, b2)
    dLp = L2 - L1
    dCp = C2p - C1p
    if C1p * C2p == 0:
        dhp = 0.0
    elif abs(h2p - h1p) <= 180:
        dhp = h2p - h1p
    elif h2p - h1p > 180:
        dhp = h2p - h1p - 360
    else:
        dhp = h2p - h1p + 360
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp) / 2)

    if C1p * C2p == 0:
        avg_hp = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        avg_hp = (h1p + h2p) / 2
    elif h1p + h2p < 360:
        avg_hp = (h1p + h2p + 360) / 2
    else:
        avg_hp = (h1p + h2p - 360) / 2

    T = (1 - 0.17 * math.cos(math.radians(avg_hp - 30))
         + 0.24 * math.cos(math.radians(2 * avg_hp))
         + 0.32 * math.cos(math.radians(3 * avg_hp + 6))
         - 0.20 * math.cos(math.radians(4 * avg_hp - 63)))
    d_ro = 30 * math.exp(-(((avg_hp - 275) / 25) ** 2))
    Rc = 2 * math.sqrt(avg_Cp ** 7 / (avg_Cp ** 7 + 25 ** 7)) if avg_Cp > 0 else 0.0
    Sl = 1 + (0.015 * (avg_Lp - 50) ** 2) / math.sqrt(20 + (avg_Lp - 50) ** 2)
    Sc = 1 + 0.045 * avg_Cp
    Sh = 1 + 0.015 * avg_Cp * T
    Rt = -math.sin(math.radians(2 * d_ro)) * Rc
    return math.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2
                     + Rt * (dCp / Sc) * (dHp / Sh))


def delta_e(h1: str, h2: str, cvd: "str | None" = None) -> float:
    """Perceptual difference between two colours; if `cvd` is set, both are simulated first."""
    if cvd:
        h1, h2 = simulate_cvd(h1, cvd), simulate_cvd(h2, cvd)
    return round(delta_e_ciede2000(_hex_to_lab(h1), _hex_to_lab(h2)), 2)


# --------------------------------------------------------------------------- #
# Palette safety
# --------------------------------------------------------------------------- #

def min_pairwise_delta_e(palette: "list[str]", cvd: "str | None" = None) -> float:
    m = float("inf")
    for i in range(len(palette)):
        for j in range(i + 1, len(palette)):
            m = min(m, delta_e(palette[i], palette[j], cvd))
    return round(m, 2) if m != float("inf") else 0.0


def palette_report(palette: "list[str]", bg: str = "#FFFFFF") -> dict:
    """Full safety report: min pairwise ΔE under normal vision AND each CVD, plus each colour's
    non-text contrast vs the background (WCAG SC 1.4.11 wants ≥3:1 for a data mark)."""
    dists = {"normal": min_pairwise_delta_e(palette)}
    for k in CVD_KINDS:
        dists[k] = min_pairwise_delta_e(palette, k)
    worst_cvd = min(dists[k] for k in CVD_KINDS)
    contrasts = {c: contrast_ratio(c, bg) for c in palette}
    return {
        "palette": list(palette),
        "min_delta_e": dists,
        "worst_cvd_delta_e": worst_cvd,
        "contrast_on_bg": contrasts,
        "min_contrast_on_bg": min(contrasts.values()),
    }


# Okabe & Ito (2008) "Color Universal Design" — the CVD-safe categorical gold standard.
# Ordered for on-white SERIES use: the five ≥3:1-on-white hues first (safe as a solid fill),
# then the three that stay CVD-distinguishable but fall below WCAG SC 1.4.11 non-text contrast on
# white (#E69F00 / #56B4E9 / #F0E442) and so need an outline/stroke or a darker ground.
OKABE_ITO = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#000000", "#E69F00", "#56B4E9", "#F0E442"]
# Paul Tol "bright" (2021) — an alternative, more lightness-uniform CVD-safe set.
TOL_BRIGHT = ["#4477AA", "#EE6677", "#228833", "#CCBB44", "#66CCEE", "#AA3377", "#BBBBBB"]
_PALETTES = {"okabe_ito": OKABE_ITO, "tol_bright": TOL_BRIGHT}

# Colour-only series ceiling: beyond this many series, colour alone can no longer carry the
# distinction and a pattern/dash/shape channel becomes MANDATORY (the roadmap's documented fallback).
SERIES_CAP = len(OKABE_ITO)  # 8


def solid_safe_on_white(h: str) -> bool:
    """True if the colour meets WCAG SC 1.4.11 non-text contrast (≥3:1) as a solid fill on white."""
    return contrast_ratio(h, "#FFFFFF") >= 3.0


def series_palette(n: int, name: str = "okabe_ito") -> dict:
    """The first `n` governed CVD-safe series colours + honest usability flags: which need an
    outline on white, and whether a pattern/shape channel is mandatory at this series count."""
    pal = _PALETTES.get(name)
    if pal is None:
        raise KeyError(f"unknown palette '{name}' (have {sorted(_PALETTES)})")
    colors = pal[: min(n, len(pal))]
    outline = [c for c in colors if not solid_safe_on_white(c)]
    fallback = n > len(pal)
    return {
        "palette": name,
        "requested": n,
        "colors": colors,
        "outline_needed_on_white": outline,          # <3:1 as a solid fill — stroke or dark ground
        "series_cap": len(pal),
        "pattern_fallback": fallback,
        "note": (f"{n} series exceeds the {len(pal)} colour-only distinguishable hues — a "
                 f"pattern/dash/shape channel is mandatory (never rely on colour alone)"
                 if fallback else
                 (f"colour is sufficient; {len(outline)} colour(s) need an outline on white"
                  if outline else "colour alone is sufficient at this series count")),
    }


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv: "list[str]") -> int:
    if not argv:
        print(__doc__)
        return 2
    cmd = argv[0]
    if cmd == "ratio" and len(argv) >= 3:
        r = contrast_ratio(argv[1], argv[2])
        aa_text = "PASS" if r >= 4.5 else "FAIL"
        aa_nontext = "PASS" if r >= 3.0 else "FAIL"
        print(f"{argv[1]} on {argv[2]}: {r}:1   text(4.5)={aa_text}  non-text(3.0)={aa_nontext}")
        return 0 if r >= 3.0 else 1
    if cmd == "palette":
        rest = [a for a in argv[1:] if not a.startswith("--")]
        name = argv[argv.index("--name") + 1] if "--name" in argv else "okabe_ito"
        n = int(rest[0]) if rest else 6
        r = series_palette(n, name)
        print(f"{r['palette']} × {n}: {' '.join(r['colors'])}")
        print(f"  series_cap={r['series_cap']}  pattern_fallback={r['pattern_fallback']}  "
              f"outline_on_white={' '.join(r['outline_needed_on_white']) or '-'}")
        print(f"  {r['note']}")
        return 0
    if cmd == "check" and len(argv) >= 3:
        pal = argv[1:]
        rep = palette_report(pal)
        print(f"palette: {' '.join(pal)}")
        print(f"  min ΔE normal={rep['min_delta_e']['normal']}  "
              f"protan={rep['min_delta_e']['protan']}  deutan={rep['min_delta_e']['deutan']}  "
              f"tritan={rep['min_delta_e']['tritan']}  (worst CVD={rep['worst_cvd_delta_e']})")
        print(f"  min non-text contrast on white: {rep['min_contrast_on_bg']}:1")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
