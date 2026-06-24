"""value_gate — KPI-value certification gate (task I-4.2).

Compares **computed** KPI values against the checked-in reference expectations
(I-4.1) and FAILs when any deviation exceeds the per-KPI tolerance. This is the
"catch wrong VALUES, not just wrong structure" gate (Premium F6).

Where do "computed" values come from? The generated TMDL/PBIR model carries
measure *names*, but DAX is a HITL placeholder (`BLANK()`) and there is no engine
on the deterministic path (Invariant I2) to execute it. So the gate takes the
computed values from an explicit source — an engine run, a values file, or (for
tests/self-check) the reference oracle `refcalc` over the same dataset:

  - values provided → compare vs reference, **deviation > tolerance ⇒ FAIL**
    (the I-4.2 DoD: a deliberately wrong value goes red);
  - no values provided → **advisory** (no engine ⇒ cannot verify, P3): reported,
    never blocking.

Rollback: ``advisory=True`` (CLI ``--advisory``) downgrades every violation to a
non-blocking warning.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from tooling.superversion.eval import refdata


class ValueGateError(AssertionError):
    """A computed KPI value deviates from the certified reference beyond tolerance."""


@dataclass(frozen=True)
class ValueOutcome:
    measure_name: str
    expected: float
    actual: Optional[float]   # None → not computed (no engine / not provided)
    tolerance: float
    unit: str = ""

    @property
    def computed(self) -> bool:
        return self.actual is not None

    @property
    def deviation(self) -> Optional[float]:
        return None if self.actual is None else abs(self.actual - self.expected)

    @property
    def within(self) -> bool:
        """A non-computed KPI is not a violation (it is advisory/uncomputed)."""
        return self.actual is None or self.deviation <= self.tolerance


def check_values(use_case: str, computed: dict[str, float]) -> list[ValueOutcome]:
    """Compare computed KPI values against the reference expectations (pure)."""
    exp = refdata.load_expectations(use_case)
    outcomes: list[ValueOutcome] = []
    for kpi in exp.kpis:
        actual = computed.get(kpi.measure_name)
        outcomes.append(ValueOutcome(
            measure_name=kpi.measure_name,
            expected=kpi.value,
            actual=None if actual is None else float(actual),
            tolerance=kpi.tolerance,
            unit=kpi.unit,
        ))
    return outcomes


def assert_values(use_case: str, computed: dict[str, float], *, advisory: bool = False) -> list[ValueOutcome]:
    """Raise `ValueGateError` if any computed value violates tolerance.

    `advisory=True` (rollback) downgrades violations to non-blocking. Returns all
    outcomes for the caller to log.
    """
    outcomes = check_values(use_case, computed)
    violations = [o for o in outcomes if o.computed and not o.within]
    if violations and not advisory:
        lines = "\n".join(
            f"  {o.measure_name}: computed {o.actual} vs expected {o.expected} "
            f"(|Δ|={o.deviation} > tol {o.tolerance})"
            for o in violations
        )
        raise ValueGateError(f"Value-Gate violations ({len(violations)}):\n{lines}")
    return outcomes


# --------------------------------------------------------------------------- #
# Stage gate (CLI)                                                            #
# --------------------------------------------------------------------------- #

def _load_values(path: Path) -> dict[str, float]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    # Accept either a bare mapping or {"values": {...}}.
    mapping = raw.get("values", raw) if isinstance(raw, dict) else {}
    return {str(k): float(v) for k, v in mapping.items()}


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tooling.superversion.eval.value_gate",
        description="Value-Gate: computed KPI values vs certified reference (I-4.2).",
    )
    parser.add_argument("use_case", help="use case id, e.g. COM-001")
    parser.add_argument("--values", type=Path, default=None,
                        help="YAML of computed KPI values (measure_name: value). "
                             "Omit when no engine is available → advisory.")
    parser.add_argument("--advisory", action="store_true",
                        help="rollback: downgrade violations to non-blocking (exit 0)")
    args = parser.parse_args(argv)

    computed = _load_values(args.values) if args.values else {}
    if not computed:
        # No engine / no values → cannot verify; advisory by construction (P3).
        exp = refdata.load_expectations(args.use_case)
        print(f"[value-gate] {args.use_case}: ADVISORY — no computed values "
              f"(no live engine); {len(exp.kpis)} reference KPI(s) not verified.")
        return 0

    outcomes = check_values(args.use_case, computed)
    violations = [o for o in outcomes if o.computed and not o.within]
    for o in outcomes:
        if not o.computed:
            print(f"[value-gate] {args.use_case}: {o.measure_name}: UNCOMPUTED (advisory)")
        elif o.within:
            print(f"[value-gate] {args.use_case}: {o.measure_name}: OK ({o.actual} ≈ {o.expected})")
        else:
            print(f"[value-gate] {args.use_case}: {o.measure_name}: FAIL "
                  f"({o.actual} vs {o.expected}, |Δ|={o.deviation} > tol {o.tolerance})")

    if violations and not args.advisory:
        print(f"[value-gate] {len(violations)} violation(s) → exit 1")
        return 1
    if violations:
        print(f"[value-gate] {len(violations)} violation(s) downgraded (--advisory) → exit 0")
    else:
        print(f"[value-gate] {args.use_case}: all computed KPIs within tolerance.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
