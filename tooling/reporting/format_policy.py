"""visual_format_policy.py — governed axis / format / deviation / semantic-colour decisions.

Classic BI craft the generator did not yet apply: value-axis (zero baseline + format), number
formatting, deviation-vs-target, and semantic colour. This is the **pure decision layer** — given a
KPI's governed metadata it returns a ``FormatSpec`` the generator (and the preview, and validators)
consume. It reuses, never reinvents:

  • semantic colours  → core/templates/page_templates/tokens/color_semantics.yaml (positive/negative/
                        warning/neutral + severity tints), the WCAG-validated SoT.
  • targets/direction → core/kpi_catalog/benchmarks.yaml (per-KPI benchmark value + direction).
  • good direction    → the bracket's component_3s ``status_logic`` (higher/lower_is_better).
  • number format     → the KPI's ``unit_format``.

Colour rule (the repo's Farb-Einsatz-Prinzip): colour is used ONLY for a semantic verdict
(good/warning/bad vs target), never to distinguish equal categories. ``classify`` needs a value +
target to pick a token; at generation time (no data) the generator emits the *rule* (good direction +
target) as conditional formatting bound to the status measure — this module supplies both.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

REPO = Path(__file__).resolve().parents[2]   # …/tooling/reporting/<file> → repo root
_SEM_PATH = REPO / "core/templates/page_templates/tokens/color_semantics.yaml"
_BENCH_PATH = REPO / "core/kpi_catalog/benchmarks.yaml"

_ZERO_BASELINE_VISUALS = {"bar_chart", "bar", "clustered_bar", "clustered_column", "column",
                          "stacked_bar", "hundred_percent_stacked_bar", "waterfall"}


def semantic_tokens() -> dict[str, str]:
    """The governed semantic palette (hex by token). Falls back to the documented defaults."""
    try:
        d = yaml.safe_load(_SEM_PATH.read_text(encoding="utf-8")) or {}
        sem = d.get("semantic") or {}
        if sem:
            return sem
    except Exception:
        pass
    return {"positive": "#107C10", "negative": "#A4262C", "warning": "#C08000", "neutral": "#605E5C"}


def benchmark_target(kpi_id: str) -> Optional[dict[str, Any]]:
    """Return {value, direction} for a KPI from benchmarks.yaml, or None if none is registered."""
    try:
        d = yaml.safe_load(_BENCH_PATH.read_text(encoding="utf-8")) or {}
        for b in d.get("benchmarks", []) or []:
            if b.get("kpi_id") == kpi_id:
                return {"value": b.get("value"), "direction": b.get("direction"),
                        "unit": b.get("unit"), "class": b.get("benchmark_class")}
    except Exception:
        pass
    return None


def target_source(kpi_id: Optional[str], comparison: Optional[str]) -> dict:
    """Where does this KPI's target come from — the honest resolution behind deviation/semantic colour.

      • 'benchmark' — an external industry/normative benchmark exists in benchmarks.yaml (value known now).
      • 'plan'      — no external benchmark, but the KPI steers vs an org/plan target (comparison
                      vs_plan / vs_target): semantic colour computes against the plan-target MEASURE
                      (e.g. [KPI Plan]) once it exists in the model — no external benchmark required.
      • 'none'      — neither: a target must be defined (org target) before a verdict is possible.

    This stops the false-gap that treats "no industry benchmark" as a defect: most KPIs (EBITDA margin,
    savings realisation, an internal index) are legitimately steered vs plan, not vs an industry number.

    **`measure` ist eine Konvention, keine Messung — gemessen 09.09.2026.** Der zurueckgegebene
    Name `[<kpi_id> Plan]` folgt dem Muster „kpi_id + Plan" und existiert in KEINEM Modell des
    Repos: gezaehlt ueber alle 230 Measure-Namen in allen TMDL-Dateien, null Treffer fuer dieses
    Muster. Real heissen die Ziel-Measures nach ihrer Anzeige-Measure mit Praefix (`Plan Sales
    Amount`), und es gibt genau diese eine. Heute faellt das niemandem auf, weil beide Aufrufer
    nur `kind` lesen und `measure` nirgends konsumiert wird — der Name ist also schlafend, nicht
    kaputt. Er bleibt hier als Absichtserklaerung stehen, aber:

    **Diesen String NICHT an eine Visual-Rolle binden.** Wer die `Goal`-Rolle des `kpi`-Visuals
    damit fuellt, erzeugt einen baumelnden Measure-Verweis — ein Bericht, der rendert und nicht
    stimmt, genau die Klasse aus `.claude/rules/connect-pbid.md`. Eine echte Ziel-Bindung
    verlangt eine Measure, deren Existenz im Modell geprueft ist.
    """
    b = benchmark_target(kpi_id) if kpi_id else None
    if b and b.get("value") is not None:
        return {"kind": "benchmark", "value": b.get("value"), "direction": b.get("direction")}
    c = (comparison or "").lower()
    if c in ("vs_plan", "vs_target", "vs_ly", "vs_prior"):
        return {"kind": "plan",
                # `measure_is_verified: False` sagt das, was der Name allein verschweigt.
                # Ein Aufrufer, der bindet statt nur anzuzeigen, muss hier abbiegen.
                "measure": f"[{kpi_id} Plan]" if kpi_id else None,
                "measure_is_verified": False}
    return {"kind": "none"}


# Kanonische Einheiten-Tokens -> Formatstring je Profil (04.08.2026).
#
# `business.unit_format` im KPI-Katalog ist seit dem 04.08.2026 auf ein geschlossenes
# Vokabular normiert. Davor war es Freitext (28 verschiedene Werte fuer 18 Einheiten,
# `count` neben `'count'`), und DREI Stellen im Repo haben daraus per Substring-Suche
# ein Format geraten: hier, `from_aluca._fmt_from_unit` und `build_ir`. Substring-Raten
# auf Freitext ist genau die Klasse, die still falsch liegt statt zu scheitern -- ein
# unbekannter Wert faellt durch alle Zweige und bekommt kommentarlos den Default.
#
# Drei Profile, weil dieselbe Einheit an drei Stellen verschieden gerendert wird:
#   model   -- formatString der Measure im Semantikmodell (so steht es im dist)
#   visual  -- Achsen-/Label-Format im Report (traegt Symbol und Einheit)
#   sv      -- Superversion-Emitter (eigene Waehrungsschreibweise mit Negativteil)
# Die Werte sind aus dem Bestand uebernommen, nicht neu erfunden: `model` ist fuer
# alle 108 KPIs mit Vorbild im handgebauten dist identisch zu dem, was dort steht;
# `visual` und `sv` reproduzieren, was die beiden Substring-Matcher vorher lieferten.
_UNIT_FORMATS: dict[str, dict[str, str]] = {
    #  Token              model        visual            sv
    "percent_1":       {"model": "0.0%",   "visual": "0.0%",        "sv": "0.0%"},
    "percent_0":       {"model": "0%",     "visual": "0%",          "sv": "0.0%"},
    "eur_0":           {"model": "#,0",    "visual": '"€"#,0',      "sv": r"\€#,0.00;-\€#,0.00"},
    "eur_2":           {"model": "#,0.00", "visual": '"€"#,0.00',   "sv": r"\€#,0.00;-\€#,0.00"},
    "eur_per_unit_0":  {"model": "#,0",    "visual": '"€"#,0.00',   "sv": r"\€#,0.00;-\€#,0.00"},
    "count_0":         {"model": "#,0",    "visual": "#,0",         "sv": ""},
    "units_0":         {"model": "#,0",    "visual": "#,0",         "sv": ""},
    "days_0":          {"model": "0",      "visual": '#,0 "d"',     "sv": ""},
    "days_1":          {"model": "#,0.0",  "visual": '#,0 "d"',     "sv": ""},
    "hours_0":         {"model": "0",      "visual": '#,0 "h"',     "sv": ""},
    "minutes_1":       {"model": "#,0.0",  "visual": "#,0.0",       "sv": ""},
    "index_0":         {"model": "0",      "visual": "#,0",         "sv": ""},
    "index_signed_0":  {"model": "#,0",    "visual": "#,0",         "sv": ""},
    "score_1":         {"model": "0.0",    "visual": "#,0.0",       "sv": ""},
    "ratio_1":         {"model": "0.0",    "visual": "#,0.0",       "sv": ""},
    "ratio_2":         {"model": "0.00",   "visual": "#,0.0",       "sv": ""},
    "turns_1":         {"model": "0.0",    "visual": "#,0.0",       "sv": ""},
    "per_1k_0":        {"model": "#,0",    "visual": "#,0",         "sv": ""},
    "defects_per_1k_0":{"model": "#,0",    "visual": "#,0",         "sv": ""},
    # Tonnen CO2-Aequivalent (KPI-ESG-001, 02.10.2026): kein dist-Vorbild, Zahlformat wie units_0.
    "tco2e_0":         {"model": "#,0",    "visual": '#,0 "t"',     "sv": ""},
}


def unit_format_string(unit_format: Optional[str], profile: str = "visual") -> Optional[str]:
    """Kanonisches Token -> Formatstring fuer `profile`, oder None bei unbekanntem Token.

    `None` ist Absicht: der Aufrufer soll den Altpfad waehlen oder scheitern koennen,
    statt einen Default zu bekommen, der wie ein Treffer aussieht.
    """
    entry = _UNIT_FORMATS.get((unit_format or "").strip())
    return None if entry is None else entry.get(profile)


def format_string(unit_format: Optional[str]) -> str:
    """Map a KPI unit_format to a Power BI custom format string (Profil `visual`)."""
    canonical = unit_format_string(unit_format, "visual")
    if canonical is not None:
        return canonical
    u = (unit_format or "").lower()
    if "%" in u or "pct" in u or u in ("rate",):
        return "0%" if "0 decimal" in u else "0.0%"
    if "eur per unit" in u:
        return '"€"#,0.00'
    if "eur" in u or "currency" in u:
        return '"€"#,0' if ("0 decimal" in u or "0 decimals" in u) else '"€"#,0.00'
    if "day" in u:
        return '#,0 "d"'
    if "hour" in u:
        return '#,0 "h"'
    if "index" in u:
        return "#,0"
    if u in ("count", "units") or "unit" in u:
        return "#,0"
    if u in ("ratio", "x") or "coverage" in u:
        return '0.0"x"'
    return "#,0.0"


def value_axis(visual_type: Optional[str], unit_format: Optional[str], title: Optional[str] = None) -> dict:
    """Value-axis spec: zero baseline for bar/column families (a non-zero base exaggerates deltas —
    BC-CHART / IBCS), plus the number format and an optional axis title."""
    vt = (visual_type or "").strip().lower()
    return {"zero_based": vt in _ZERO_BASELINE_VISUALS, "format": format_string(unit_format),
            "title": title}


def good_direction(status_logic: Optional[str], bench_direction: Optional[str] = None) -> Optional[str]:
    """'higher' or 'lower' — which way is good. status_logic wins; benchmark direction is the fallback."""
    s = (status_logic or "").lower()
    if "higher" in s:
        return "higher"
    if "lower" in s:
        return "lower"
    b = (bench_direction or "").lower()
    if "higher" in b:
        return "higher"
    if "lower" in b:
        return "lower"
    return None


def classify(status_logic: Optional[str], actual: Optional[float], target: Optional[float],
             warn_frac: float = 0.05, bench_direction: Optional[str] = None) -> str:
    """Return a semantic token name for actual-vs-target. 'neutral' when no target/direction is known
    (never invent a verdict). warn_frac = the near-target band (default ±5%)."""
    gd = good_direction(status_logic, bench_direction)
    if actual is None or target is None or gd is None or target == 0:
        return "neutral"
    ratio = actual / target
    if gd == "higher":
        if actual >= target:
            return "positive"
        return "warning" if ratio >= (1 - warn_frac) else "negative"
    else:  # lower is better
        if actual <= target:
            return "positive"
        return "warning" if ratio <= (1 + warn_frac) else "negative"


def deviation_spec(comparison: Optional[str], status_logic: Optional[str]) -> dict:
    """Whether to show an actual-vs-reference deviation (value + % + ▲/▼) and which way is good."""
    c = (comparison or "").lower()
    show = c in ("vs_target", "vs_plan", "vs_ly", "vs_prior")
    gd = good_direction(status_logic)
    return {"show": show, "reference": c.replace("vs_", "") or None,
            "positive_is_good": (gd == "higher") if gd else None}


def tooltip_measures(strategic: Optional[str], influencing: Optional[list[str]], cap: int = 4) -> list[str]:
    """Context measures to surface on hover: the strategic KPI first, then its influencing drivers."""
    out: list[str] = []
    if strategic:
        out.append(strategic)
    for k in (influencing or []):
        if k and k not in out:
            out.append(k)
        if len(out) >= cap:
            break
    return out


@dataclass
class FormatSpec:
    kpi_id: Optional[str]
    value_axis: dict
    semantic: dict            # {good_direction, tokens, target}
    deviation: dict
    tooltip: list[str] = field(default_factory=list)


def format_spec(kpi_id: Optional[str], visual_type: Optional[str], unit_format: Optional[str],
                status_logic: Optional[str], comparison: Optional[str],
                strategic: Optional[str] = None, influencing: Optional[list[str]] = None) -> FormatSpec:
    """One governed formatting decision for a visual — the object the generator/preview applies."""
    bench = benchmark_target(kpi_id) if kpi_id else None
    return FormatSpec(
        kpi_id=kpi_id,
        value_axis=value_axis(visual_type, unit_format),
        semantic={"good_direction": good_direction(status_logic, bench and bench.get("direction")),
                  "tokens": semantic_tokens(),
                  "target": bench and bench.get("value"),
                  "target_source": target_source(kpi_id, comparison)},
        deviation=deviation_spec(comparison, status_logic),
        tooltip=tooltip_measures(strategic, influencing),
    )
