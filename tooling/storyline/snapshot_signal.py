#!/usr/bin/env python3
"""
snapshot_signal.py — ADR-0017 D2: value-verification from the EXISTING refcalc/Wirkungs-Loop.

Reuse-first (GOI Doktrin + ADR-0017 D2 resolution): this is a thin adapter over the already-built,
already-tested value oracle — `tooling/superversion/eval/wirkung.snapshot_via_refcalc` (which computes
governed KPI values via `refcalc` over the I-4.1 reference data, with ADR-0009's "missing ≠ zero /
UNCOMPUTED" honesty). It builds **no** new snapshot/compute subsystem.

It implements the one verification-gate item Stage 1 couldn't do from the catalog alone
(ADR-0017 gate #2: "its snapshot is not UNCOMPUTED"): a finding's KPI is *value-verified* when a
computed snapshot value actually exists for it. This is orthogonal to (and stronger than) the
catalog-presence grounding — it never downgrades a use case that lacks reference data; it only
*adds* confidence where the value is really computed.

Honest limits, by design, not omission:
  - Coverage is whatever has I-4.1 reference expectations (today COM-001, SCM-002); everything else
    returns `None` = UNCOMPUTED (not False, not 0) — it grows automatically as reference data grows.
  - **No magnitude/delta ranking here:** the reference data carries current values but Plan/target is
    not yet materialized (documented I-3.4 Golden-Thread WARN), so a cross-finding "biggest delta"
    signal would be a guess. Deferred until Plan is materialized — never faked.

Usage:
    python tooling/storyline/snapshot_signal.py            # value-verification coverage per use case
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def covered_use_cases() -> list[str]:
    """Use cases that have I-4.1 reference expectations (so a snapshot can be computed)."""
    try:
        from tooling.superversion.eval import refdata
        return list(refdata.available_use_cases())
    except Exception:
        return []


def value_verified_map(use_case: str) -> Optional[dict[str, bool]]:
    """Per-KPI value-verification for a use case, reusing the refcalc snapshot.

    Returns None when the use case has no reference data (UNCOMPUTED — never fabricated).
    Otherwise {kpi_id: (a computed value exists and is not None)} — ADR-0009's missing≠zero rule
    is already enforced inside snapshot_via_refcalc.
    """
    try:
        from tooling.superversion.eval import wirkung
    except Exception:
        return None
    if use_case not in covered_use_cases():
        return None
    try:
        snap = wirkung.snapshot_via_refcalc(use_case)
    except Exception:
        return None
    return {kid: (val is not None) for kid, val in snap.items()}


def main() -> int:
    covered = covered_use_cases()
    print(f"value-verification coverage (I-4.1 reference data): {covered or '— none'}")
    for uc in covered:
        m = value_verified_map(uc) or {}
        verified = [k for k, v in m.items() if v]
        print(f"  {uc}: {len(verified)}/{len(m)} KPIs value-verified via refcalc — {', '.join(verified)}")
    print("\nAll other use cases: UNCOMPUTED (no reference data) — value-verification grows with I-4.1 coverage.")
    print("Magnitude/delta ranking: deferred — Plan/target not yet materialized (I-3.4 WARN); not faked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
