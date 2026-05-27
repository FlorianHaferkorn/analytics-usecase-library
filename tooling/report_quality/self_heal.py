"""Deterministic self-heal loop for structural report quality violations."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .models import Violation
from .pbir import parse_report
from .structural_validator import ReportSpec, default_spec


@dataclass
class SelfHealResult:
    success: bool
    iterations: int
    initial_violations: int
    fixed_count: int
    remaining: list[Violation]
    fix_log: list[str] = field(default_factory=list)


def self_heal(report_dir: Path, spec: ReportSpec | None = None, max_iterations: int = 5) -> SelfHealResult:
    """Run `check -> deterministic fix -> re-check` with a hard iteration cap."""

    active_spec = spec or default_spec()
    initial = active_spec.check(parse_report(report_dir))
    if not initial:
        return SelfHealResult(True, 0, 0, 0, [], [])

    fixed_count = 0
    fix_log: list[str] = []

    for iteration in range(1, max_iterations + 1):
        report = parse_report(report_dir)
        current = active_spec.check(report)
        if not current:
            return SelfHealResult(True, iteration - 1, len(initial), fixed_count, [], fix_log)

        progress = False
        for violation in current:
            invariant = next((i for i in active_spec.invariants if getattr(i, "name", None) == violation.check), None)
            fix_fn = getattr(invariant, "fix", None)
            if fix_fn is None:
                continue
            for page in report.pages.values():
                try:
                    if fix_fn(report, page, violation):
                        progress = True
                        fixed_count += 1
                        fix_log.append(f"iter={iteration} fixed {violation.check} @ {violation.pointer}")
                        break
                except Exception:
                    continue

        if not progress:
            return SelfHealResult(False, iteration, len(initial), fixed_count, current, fix_log)

    remaining = active_spec.check(parse_report(report_dir))
    return SelfHealResult(not remaining, max_iterations, len(initial), fixed_count, remaining, fix_log)
