"""eval.refinement — Wirkungs-Loop feedback: Refinement-Trigger (task I-8.3, ADR-0009 §5).

Turns measured effects (AttributionRecords from I-8.2) into **reviewable proposals** to
refine the ontology — and nothing more. Per ADR-0009 the core is **never** auto-mutated:
a proposal carries `status="pending_review"` and is destined for the Freigabe-Schleuse
(human, two-person rule). This module only *derives* proposals; it applies none.

Honesty (ADR-0009):
  - Only **computed**, scale-able records produce a proposal — an `uncomputed` record or a
    zero/None baseline yields **no** proposal (no signal from an unknown; missing ≠ trigger).
  - `before_after` deltas are associations, not causation — proposals say "prüfen", never
    "die Action verursachte X".
Deterministic + pure: same records + thresholds → same proposals.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from tooling.superversion.eval.wirkung import AttributionRecord

TriggerKind = Literal["no_effect", "material_effect"]


@dataclass(frozen=True)
class RefinementProposal:
    action_code_id: str
    kpi_id: str
    trigger: TriggerKind
    rel_change: float
    rationale: str
    status: Literal["pending_review"] = "pending_review"

    def to_dict(self) -> dict:
        return {
            "action_code_id": self.action_code_id, "kpi_id": self.kpi_id,
            "trigger": self.trigger, "rel_change": self.rel_change,
            "rationale": self.rationale, "status": self.status,
        }


def _proposal_for(rec: AttributionRecord, no_effect_rel: float, material_rel: float) -> Optional[RefinementProposal]:
    # No proposal from unknowns or unscalable baselines (missing ≠ trigger).
    if rec.status != "computed" or rec.delta is None or not rec.t0:
        return None
    rel = rec.delta / rec.t0
    mag = abs(rel)
    if mag < no_effect_rel:
        return RefinementProposal(
            rec.action_code_id, rec.kpi_id, "no_effect", rel,
            f"Action bewegte outcome-KPI kaum (rel {rel:+.1%}) — Wirksamkeit prüfen "
            f"(Assoziation, nicht Kausalität)",
        )
    if mag >= material_rel:
        return RefinementProposal(
            rec.action_code_id, rec.kpi_id, "material_effect", rel,
            f"Materielle Bewegung (rel {rel:+.1%}) — als wirksam kandidieren; "
            f"Kausalität via Kontroll-Segment (diff_in_diff/holdout) verifizieren",
        )
    return None  # moderate movement: nothing to flag


def derive_refinements(
    records: list[AttributionRecord], *,
    no_effect_rel: float = 0.01, material_rel: float = 0.10,
) -> list[RefinementProposal]:
    """Derive reviewable refinement proposals from attribution records (never applied)."""
    out: list[RefinementProposal] = []
    for rec in records:
        p = _proposal_for(rec, no_effect_rel, material_rel)
        if p is not None:
            out.append(p)
    return out
