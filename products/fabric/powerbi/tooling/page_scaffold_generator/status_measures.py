"""status_measures.py — deterministic variance/status measures (NOT narrative prose).

The honest, tool-agnostic answer to "how does this KPI stand vs its target": governed *derived
measures* — actual − target, the % variance, and a semantic status — computed deterministically.

Deliberately NOT a narrative/NLG measure and NOT the Power BI Smart-Narrative visual (a legacy dead
end superseded by Copilot/AI-Chat). Prose narration is left to the dynamic AI-Chat tier; this layer
produces the numbers that (a) drive semantic colour + deviation in the formatting layer, and (b) give
Copilot/AI-Chat clean, audit-grade grounding to talk about. Reuses the direction/threshold logic from
``visual_format_policy`` — one definition of "which way is good" and "how near-target counts".

The target reference is a measure name (e.g. the plan/org target ``[OTIF % Plan]``) or a numeric
literal (a normative benchmark). No target ⇒ no status is emitted (ADR-0009: never a fabricated
verdict). Output is DAX today; the same specs compile to the DSL→SQL path for Databricks.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

from .visual_format_policy import good_direction

TargetRef = Union[str, float, int]   # a measure name "[X Plan]" or a numeric literal


@dataclass(frozen=True)
class MeasureDef:
    name: str
    dax: str
    role: str                 # 'variance' | 'variance_pct' | 'status' | 'status_color'
    format: Optional[str] = None


def _target_expr(target: TargetRef) -> str:
    """A measure name is used as-is; a number becomes a DAX literal."""
    if isinstance(target, (int, float)):
        return repr(float(target))
    t = str(target).strip()
    return t if t.startswith("[") else f"[{t}]"


def variance_measures(kpi_key: str, target: Optional[TargetRef], status_logic: Optional[str],
                      *, warn_frac: float = 0.05, fmt: Optional[str] = None,
                      colors: Optional[dict[str, str]] = None) -> list[MeasureDef]:
    """Governed variance + status measures for a KPI. Empty list when no target (never fabricate)."""
    if target is None:
        return []
    gd = good_direction(status_logic)
    if gd is None:
        return []
    m = f"[{kpi_key}]"
    t = _target_expr(target)
    tokens = colors or {"positive": "#107C10", "warning": "#C08000", "negative": "#A4262C"}
    out = [
        MeasureDef(f"{kpi_key} Δ vs Target", f"{m} - {t}", "variance", fmt),
        MeasureDef(f"{kpi_key} Δ vs Target %", f"DIVIDE({m} - {t}, {t})", "variance_pct", "+0.0%;-0.0%;0.0%"),
    ]
    # status: +1 good / 0 near-target / -1 bad — direction-aware; near-target band = warn_frac
    if gd == "higher":
        good, near = f"{m} >= {t}", f"{m} >= {t} * (1 - {warn_frac})"
    else:  # lower is better
        good, near = f"{m} <= {t}", f"{m} <= {t} * (1 + {warn_frac})"
    out.append(MeasureDef(
        f"{kpi_key} Status",
        f"IF({good}, 1, IF({near}, 0, -1))", "status", "0"))
    # status_color: the governed semantic hex, ready to bind to conditional formatting (fill/font)
    out.append(MeasureDef(
        f"{kpi_key} Status Color",
        f'IF({good}, "{tokens["positive"]}", IF({near}, "{tokens["warning"]}", "{tokens["negative"]}"))',
        "status_color", None))
    return out
