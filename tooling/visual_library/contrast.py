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
  - OKLab / OKLCH (Ottosson 2020) for hue-preserving lightness steps (ensure_contrast)

Brand-theme derivation (Meridian mirrors this file byte-for-byte):
  - ensure_contrast   steps a brand colour's OKLCH lightness until it meets a contrast ratio
  - reserved_conflicts flags categorical colours too close to reserved status/variance colours
  - palette_gate      one verdict: CVD separation + reserved conflicts (fail), low non-text
                      contrast (warn: needs a label/outline, WCAG 1.4.11)

CLI:
  contrast.py ratio <fg_hex> <bg_hex>              # WCAG contrast ratio
  contrast.py palette [n] [--name okabe_ito|tol_bright]   # first n CVD-safe series colours + fallback
  contrast.py check <hex> <hex> [<hex> ...]        # min pairwise ΔE under normal + 3 CVD sims
  contrast.py ensure <hex> <bg_hex> [ratio]        # hue-kept OKLCH lightness step to ≥ratio (3.0)
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


def contrast_ratio_exact(fg: str, bg: str) -> float:
    """WCAG contrast, unrounded — the value every threshold decision uses. Rounding first let 2.9965 pass as
    3.00 (Meridian theme gate measures unrounded and failed: #0FB2C9 on white, 01.10.2026, BO-036)."""
    l1, l2 = relative_luminance(fg), relative_luminance(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def contrast_ratio(fg: str, bg: str) -> float:
    """WCAG contrast rounded to two places, for reports and messages — not for pass/fail."""
    return round(contrast_ratio_exact(fg, bg), 2)


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
    return contrast_ratio_exact(h, "#FFFFFF") >= 3.0


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
# OKLab / OKLCH (Ottosson 2020) — hue-preserving lightness steps
# --------------------------------------------------------------------------- #

def _linear_rgb_to_oklab(r: float, g: float, b: float) -> "tuple[float, float, float]":
    l_ = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m_ = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s_ = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b

    def cbrt(x: float) -> float:
        return x ** (1 / 3) if x >= 0 else -((-x) ** (1 / 3))

    l_, m_, s_ = cbrt(l_), cbrt(m_), cbrt(s_)
    return (0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
            1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
            0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_)


def _oklab_to_linear_rgb(L: float, a: float, b: float) -> "tuple[float, float, float]":
    l_ = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m_ = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s_ = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return (4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_,
            -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
            -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_)


def hex_to_oklch(h: str) -> "tuple[float, float, float]":
    """(L 0..1, C, hue degrees 0..360) of an sRGB hex colour."""
    import math
    L, a, b = _linear_rgb_to_oklab(*(_srgb_to_linear(c) for c in hex_to_rgb(h)))
    hue = math.degrees(math.atan2(b, a))
    return (L, math.hypot(a, b), hue + 360 if hue < 0 else hue)


def _in_gamut(rgb: "tuple[float, float, float]", eps: float = 1e-7) -> bool:
    return all(-eps <= c <= 1 + eps for c in rgb)


def oklch_to_hex(L: float, C: float, hue: float) -> str:
    """OKLCH -> sRGB hex. Keeps L and hue; if out of gamut, reduces chroma only (bisection)."""
    import math
    ca, sa = math.cos(math.radians(hue)), math.sin(math.radians(hue))

    def rgb(c: float) -> "tuple[float, float, float]":
        return _oklab_to_linear_rgb(L, c * ca, c * sa)

    if not _in_gamut(rgb(C)):
        lo, hi = 0.0, C
        for _ in range(40):                      # deterministic, ~1e-12 chroma resolution
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if _in_gamut(rgb(mid)) else (lo, mid)
        C = lo
    return rgb_to_hex(tuple(_linear_to_srgb(c) for c in rgb(C)))


# Lightness step in OKLab L (0..1). 0.01 is ~1 % perceived lightness — fine enough that the first
# passing shade overshoots the target ratio only marginally, coarse enough to stay a short loop.
ENSURE_STEP_L = 0.01
# Background split: above this relative luminance the ground counts as light (step darker),
# at/below it as dark (step lighter). 0.18 is where a colour has equal contrast against pure
# white and pure black ((1.05)/(Y+.05) == (Y+.05)/.05 -> Y ~ 0.179).
LIGHT_BG_LUMINANCE = 0.18


def ensure_contrast(color: str, bg: str, min_ratio: float = 3.0) -> str:
    """Return `color`, or the first shade of the same OKLCH hue whose WCAG contrast against `bg`
    reaches `min_ratio`. Steps OKLab lightness by ENSURE_STEP_L — darker on a light ground,
    lighter on a dark one — reducing chroma only where the sRGB gamut forces it. Deterministic.
    ValueError if the ratio cannot be reached in that direction (L hits 0 or 1)."""
    if not 1.0 <= min_ratio <= 21.0:
        raise ValueError(f"min_ratio {min_ratio} outside the WCAG range 1..21")
    color = rgb_to_hex(hex_to_rgb(color))           # normalised uppercase '#RRGGBB'
    if contrast_ratio_exact(color, bg) >= min_ratio:
        return color
    L, C, hue = hex_to_oklch(color)
    step = -ENSURE_STEP_L if relative_luminance(bg) > LIGHT_BG_LUMINANCE else ENSURE_STEP_L
    k = 1
    while True:
        Lk = L + k * step
        if Lk < 0.0 or Lk > 1.0:
            break
        cand = oklch_to_hex(Lk, C, hue)
        if contrast_ratio_exact(cand, bg) >= min_ratio:
            return cand
        k += 1
    # last resort at the lightness end-point itself (pure black / white carry no hue)
    end = oklch_to_hex(0.0 if step < 0 else 1.0, 0.0, hue)
    if contrast_ratio_exact(end, bg) >= min_ratio:
        return end
    raise ValueError(f"{color} cannot reach {min_ratio}:1 on {bg} by "
                     f"{'darkening' if step < 0 else 'lightening'} (max {contrast_ratio(end, bg)}:1)")


def for_dark_ground(color: str, dark_bg: str, light_bg: str = "#FFFFFF",
                    min_ratio: "float | None" = None) -> str:
    """The same colour role on a dark ground, keeping its SALIENCE (A-31 R6).

    On a light card salience is distance below the card's lightness (ink is dark, a gridline is
    near-white); on a dark card it is distance above. Mapping OKLab L so that distance is kept —
    L' = L_dark + (L_light - L) / L_light * (1 - L_dark) — keeps hue, chroma and the ORDER of
    emphasis: ink stays the loudest, a gridline stays recessive, a lighter PY stays quieter than AC.
    Measured 30.09.2026: lifting every colour only to a minimum contrast turned the #E1DFDD grid
    brighter than the lifted data ink. `min_ratio` then lifts the result to a floor (text 4.5,
    marks 3.0); leave it None for decoration."""
    L, C, h = hex_to_oklch(color)
    Ll, Ld = hex_to_oklch(light_bg)[0], hex_to_oklch(dark_bg)[0]
    distance = max(0.0, (Ll - L) / Ll) if Ll > 0 else 0.0
    out = oklch_to_hex(min(1.0, Ld + distance * (1 - Ld)), C, h)
    return ensure_contrast(out, dark_bg, min_ratio) if min_ratio else out


# --------------------------------------------------------------------------- #
# Reserved semantic colours + palette gate
# --------------------------------------------------------------------------- #

# A categorical colour must stay at least as far from a reserved status/variance colour as the
# governed palette's own colours must stay from each other: tests pin Okabe-Ito's worst-case CVD
# min pairwise ΔE00 at ≥10, so 10 is the bar for "a reader can tell category from status".
# (JND is ~1–2.3 ΔE00; Szafir 2017 shows small marks need several times that to be told apart,
# so 10 keeps headroom for thin bars/points.) Measured 30.09.2026: ALUCA negative #A4262C vs a
# near copy #A5282D = 0.4 (flagged); vs Okabe-Ito #0072B2 worst-case 39.56 (protan, not flagged).
RESERVED_MIN_DELTA_E = 10.0


# Which visions the reserved check uses by default: normal only. A status colour never travels
# alone (icon + label, dataviz non-negotiable; IBCS UN 4.1 also defines a colourless variance
# notation), so a CVD reader does not read status from hue — the misreading this gate prevents
# ("red category looks like a bad variance", Design Lab finding 3, 30.09.2026) is a normal-vision
# one. Measured: with CVD included, Okabe-Ito vermillion vs positive green is 0.79 (protan) and
# the ALUCA status colours collide among themselves at 4.16 (deutan) — no palette could pass.
# Pass `visions=ALL_VISIONS` where hue alone must carry the meaning.
ALL_VISIONS = ("normal",) + CVD_KINDS


def reserved_conflicts(palette: "list[str]", reserved: "dict[str, str]",
                       min_delta_e: float = RESERVED_MIN_DELTA_E,
                       visions: "tuple[str, ...]" = ("normal",)) -> "list[dict]":
    """Every categorical colour closer than `min_delta_e` (CIEDE2000) to a reserved semantic
    colour under any of `visions` ("normal" and/or CVD kinds). One finding per (colour, role)
    pair, reporting the vision in which the two sit closest."""
    out = []
    for c in palette:
        for role, r in reserved.items():
            dists = {v: delta_e(c, r, None if v == "normal" else v) for v in visions}
            vision = min(dists, key=lambda v: (dists[v], v))
            if dists[vision] < min_delta_e:
                out.append({"color": c, "reserved": r, "role": role,
                            "delta_e": dists[vision], "vision": vision})
    return out


def palette_gate(palette: "list[str]", bg: str, reserved: "dict[str, str]", *,
                 min_cvd_delta_e: float = 8.0, min_nontext: float = 3.0) -> dict:
    """One verdict for a categorical palette on a given ground (light or dark).

    failures: worst-case CVD min pairwise ΔE below `min_cvd_delta_e`; any reserved conflict.
    warnings: colours below `min_nontext` against `bg` -> `needs_label_or_outline` (WCAG 1.4.11
              accepts a label/outline as the non-colour carrier, so this is not a failure)."""
    worst_by_kind = {k: min_pairwise_delta_e(palette, k) for k in CVD_KINDS}
    worst_kind = min(CVD_KINDS, key=lambda k: (worst_by_kind[k], k))
    worst = worst_by_kind[worst_kind] if len(palette) > 1 else float("inf")
    conflicts = reserved_conflicts(palette, reserved)
    contrasts = {c: contrast_ratio(c, bg) for c in palette}
    needs_label = [c for c in palette if contrasts[c] < min_nontext]

    failures: "list[dict]" = []
    if worst < min_cvd_delta_e:
        failures.append({"check": "cvd_separation", "vision": worst_kind, "delta_e": worst,
                         "min": min_cvd_delta_e})
    failures += [{"check": "reserved_conflict", **f} for f in conflicts]
    warnings = [{"check": "needs_label_or_outline", "color": c, "contrast": contrasts[c],
                 "min": min_nontext} for c in needs_label]
    return {
        "ok": not failures,
        "failures": failures,
        "warnings": warnings,
        "bg": bg,
        "worst_cvd_delta_e": worst_by_kind[worst_kind] if len(palette) > 1 else None,
        "worst_cvd_kind": worst_kind if len(palette) > 1 else None,
        "contrast_on_bg": contrasts,
        "needs_label_or_outline": needs_label,
        "reserved_conflicts": conflicts,
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
        r, exact = contrast_ratio(argv[1], argv[2]), contrast_ratio_exact(argv[1], argv[2])
        aa_text = "PASS" if exact >= 4.5 else "FAIL"
        aa_nontext = "PASS" if exact >= 3.0 else "FAIL"
        print(f"{argv[1]} on {argv[2]}: {r}:1   text(4.5)={aa_text}  non-text(3.0)={aa_nontext}")
        return 0 if exact >= 3.0 else 1
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
    if cmd == "ensure" and len(argv) >= 3:
        ratio = float(argv[3]) if len(argv) >= 4 else 3.0
        try:
            out = ensure_contrast(argv[1], argv[2], ratio)
        except ValueError as exc:
            print(f"UNREACHABLE: {exc}")
            return 1
        L0, _, h0 = hex_to_oklch(argv[1])
        L1, _, h1 = hex_to_oklch(out)
        print(f"{argv[1]} on {argv[2]} -> {out}: {contrast_ratio(out, argv[2])}:1 "
              f"(was {contrast_ratio(argv[1], argv[2])}:1; OKLCH L {L0:.3f}->{L1:.3f}, "
              f"hue {h0:.1f}->{h1:.1f})")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
