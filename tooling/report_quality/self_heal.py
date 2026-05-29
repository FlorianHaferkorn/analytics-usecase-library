"""Deterministic self-heal loop for structural report quality violations."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .models import Violation
from .pbir import iter_report_dirs, parse_report
from .structural_validator import ReportSpec, default_spec

logger = logging.getLogger(__name__)

# Only permit edits inside .Report/definition/** to prevent accidents.
_SAFE_SUFFIX = Path("definition")


def _is_safe_path(path: Path, report_dir: Path) -> bool:
    """Return True only if path is inside <report_dir>/definition/."""
    try:
        path.resolve().relative_to((report_dir / _SAFE_SUFFIX).resolve())
        return True
    except ValueError:
        return False


@dataclass
class FixRecord:
    """One deterministic fix (applied or simulated in dry-run)."""

    iteration: int
    check: str
    pointer: str
    file: str
    fix_id: str


@dataclass
class SelfHealResult:
    success: bool
    iterations: int
    initial_violations: int
    fixed_count: int
    remaining: list[Violation]
    fix_log: list[FixRecord] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "iterations": self.iterations,
            "initial_violations": self.initial_violations,
            "fixed_count": self.fixed_count,
            "remaining": [v.__dict__ for v in self.remaining],
            "fix_log": [asdict(r) for r in self.fix_log],
        }


def self_heal(
    report_dir: Path,
    spec: ReportSpec | None = None,
    max_iterations: int = 5,
    dry_run: bool = False,
) -> SelfHealResult:
    """Run ``check -> deterministic fix -> re-check`` with a hard iteration cap.

    Args:
        report_dir: Path to the .Report directory.
        spec: ReportSpec to use. Defaults to ``default_spec()``.
        max_iterations: Hard cap on fix iterations.
        dry_run: When True, simulate fixes without writing files.

    Returns:
        SelfHealResult with full fix log.
    """
    if not report_dir.is_dir():
        raise ValueError(f"report_dir does not exist: {report_dir}")

    active_spec = spec or default_spec()
    initial = active_spec.check(parse_report(report_dir))
    if not initial:
        return SelfHealResult(True, 0, 0, 0, [], [])

    fixed_count = 0
    fix_log: list[FixRecord] = []
    simulated_fixed: set[str] = set()

    def _filter_simulated(violations: list[Violation]) -> list[Violation]:
        if not dry_run:
            return violations
        return [v for v in violations if v.pointer not in simulated_fixed]

    for iteration in range(1, max_iterations + 1):
        report = parse_report(report_dir)
        current = _filter_simulated(active_spec.check(report))
        if not current:
            return SelfHealResult(True, iteration - 1, len(initial), fixed_count, [], fix_log)

        progress = False
        for violation in current:
            invariant = next(
                (i for i in active_spec.invariants if getattr(i, "name", None) == violation.check),
                None,
            )
            fix_fn = getattr(invariant, "fix", None)
            if fix_fn is None:
                continue

            violation_handled = False
            for page in report.pages.values():
                target_file = page.page_dir / "page.json"
                if not _is_safe_path(target_file, report_dir):
                    logger.warning(
                        "Skipping fix for %s: path outside definition/", violation.pointer
                    )
                    continue

                if dry_run:
                    fix_log.append(
                        FixRecord(
                            iteration=iteration,
                            check=violation.check,
                            pointer=violation.pointer,
                            file=str(target_file),
                            fix_id=f"{violation.check}:dry-run",
                        )
                    )
                    simulated_fixed.add(violation.pointer)
                    fixed_count += 1
                    progress = True
                    violation_handled = True
                    break

                try:
                    fixed = fix_fn(report, page, violation)
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "Fix %s failed at %s: %s", violation.check, violation.pointer, exc
                    )
                    continue

                if fixed:
                    progress = True
                    fixed_count += 1
                    fix_log.append(
                        FixRecord(
                            iteration=iteration,
                            check=violation.check,
                            pointer=violation.pointer,
                            file=str(target_file),
                            fix_id=f"{violation.check}:applied",
                        )
                    )
                    violation_handled = True
                    break

            if violation_handled and dry_run:
                break

        if not progress:
            remaining = _filter_simulated(active_spec.check(parse_report(report_dir)))
            return SelfHealResult(False, iteration, len(initial), fixed_count, remaining, fix_log)

    remaining = _filter_simulated(active_spec.check(parse_report(report_dir)))
    return SelfHealResult(not remaining, max_iterations, len(initial), fixed_count, remaining, fix_log)


def self_heal_all(
    dist_root: Path,
    spec: ReportSpec | None = None,
    max_iterations: int = 3,
    dry_run: bool = False,
) -> dict[str, SelfHealResult]:
    """Run self_heal for every .Report directory under dist_root."""
    results: dict[str, SelfHealResult] = {}
    for report_dir in iter_report_dirs(dist_root):
        results[report_dir.name] = self_heal(
            report_dir, spec=spec, max_iterations=max_iterations, dry_run=dry_run
        )
    return results


def write_fix_log(results: dict[str, SelfHealResult], output_path: Path) -> None:
    """Serialize all SelfHealResults to a JSON fix-log file."""
    payload = {name: result.to_dict() for name, result in results.items()}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
