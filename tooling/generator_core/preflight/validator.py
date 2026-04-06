"""
Preflight Validator — runs all pre-generation checks and returns a report.

Usage
-----
    from tooling.generator_core.preflight.validator import PreflightValidator

    v = PreflightValidator(
        kpi_catalog_root=Path("core/kpi_catalog"),
        action_codes_root=Path("core/action_codes"),
        data_contracts_root=Path("core/data_contracts"),
        dist_root=Path("products/fabric/powerbi/dist"),
    )
    report = v.run(bracket_path=Path("core/usecases/core/COM-001_.../UseCase_Bracket.yaml"))
    if not report.passed:
        print(report.summary())
        sys.exit(1)

CLI
---
    python -m tooling.generator_core preflight --bracket core/usecases/core/COM-001_.../UseCase_Bracket.yaml
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml

from .checks import (
    ALL_CHECKS,
    FULL_CHECKS,
    QUICK_CHECKS,
    PreflightContext,
)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class PreflightReport:
    bracket_path: str
    use_case_id: str
    passed: bool                        # True iff no blocking errors
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    checks_run: int = 0

    def summary(self, verbose: bool = True) -> str:
        status = "PASSED" if self.passed else "FAILED"
        lines = [
            f"Preflight [{status}] — {self.use_case_id}",
            f"  Checks run : {self.checks_run}",
            f"  Errors     : {len(self.errors)}",
            f"  Warnings   : {len(self.warnings)}",
        ]
        if not self.passed or verbose:
            for e in self.errors:
                lines.append(f"  ERROR   {e}")
            for w in self.warnings:
                lines.append(f"  WARN    {w}")
            for s in self.suggestions:
                lines.append(f"  SUGGEST {s}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "bracket_path": self.bracket_path,
            "use_case_id": self.use_case_id,
            "passed": self.passed,
            "errors": self.errors,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "checks_run": self.checks_run,
        }


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

class PreflightValidator:
    """
    Runs pre-generation checks for a UseCase_Bracket.yaml.

    Parameters
    ----------
    kpi_catalog_root
        Path to core/kpi_catalog/
    action_codes_root
        Path to core/action_codes/
    data_contracts_root
        Path to core/data_contracts/ (optional; enables deeper checks)
    dist_root
        Path to the dist/ output directory (optional; enables model-presence checks)
    mode
        "quick" — only QUICK_CHECKS (fast, no file I/O beyond bracket + catalog)
        "full"  — ALL_CHECKS (recommended before first generation)
    """

    def __init__(
        self,
        kpi_catalog_root: Path,
        action_codes_root: Path,
        data_contracts_root: Optional[Path] = None,
        dist_root: Optional[Path] = None,
        mode: str = "full",
    ) -> None:
        self.kpi_catalog_root = Path(kpi_catalog_root)
        self.action_codes_root = Path(action_codes_root)
        self.data_contracts_root = Path(data_contracts_root) if data_contracts_root else None
        self.dist_root = Path(dist_root) if dist_root else None
        self.mode = mode
        self._checks = QUICK_CHECKS if mode == "quick" else ALL_CHECKS

    def run(self, bracket_path: Path) -> PreflightReport:
        """Run all checks for one bracket file."""
        bracket_path = Path(bracket_path)
        if not bracket_path.is_file():
            return PreflightReport(
                bracket_path=str(bracket_path),
                use_case_id="?",
                passed=False,
                errors=[f"[FILE_NOT_FOUND] Bracket file not found: {bracket_path}"],
            )

        with open(bracket_path, encoding="utf-8") as fh:
            bracket = yaml.safe_load(fh) or {}

        use_case_id = bracket.get("id", bracket_path.parent.name)

        ctx = PreflightContext(
            bracket_path=bracket_path,
            bracket=bracket,
            kpi_catalog_root=self.kpi_catalog_root,
            action_codes_root=self.action_codes_root,
            data_contracts_root=self.data_contracts_root,
            dist_root=self.dist_root,
        )

        for check_fn in self._checks:
            try:
                check_fn(ctx)
            except Exception as exc:
                ctx.warn("CHECK_EXCEPTION", f"Check '{check_fn.__name__}' raised: {exc}")

        return PreflightReport(
            bracket_path=str(bracket_path),
            use_case_id=use_case_id,
            passed=len(ctx.errors) == 0,
            errors=ctx.errors,
            warnings=ctx.warnings,
            suggestions=ctx.suggestions,
            checks_run=len(self._checks),
        )

    def run_all(self, bracket_paths: List[Path]) -> List[PreflightReport]:
        """Run checks for multiple bracket files."""
        return [self.run(p) for p in bracket_paths]

    def run_domain(self, use_cases_root: Path, domain_prefix: str) -> List[PreflightReport]:
        """
        Run checks for all use cases matching a domain prefix.

        Example: run_domain(Path("core/usecases/core"), "COM")
        """
        reports: List[PreflightReport] = []
        for bracket in use_cases_root.rglob("UseCase_Bracket.yaml"):
            parent_name = bracket.parent.name
            if parent_name.upper().startswith(domain_prefix.upper()):
                reports.append(self.run(bracket))
        return reports


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _cli_main() -> None:
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Run preflight checks before generation"
    )
    parser.add_argument(
        "--bracket", type=Path,
        help="Path to UseCase_Bracket.yaml",
    )
    parser.add_argument(
        "--domain", type=str,
        help="Domain prefix to check all at once (e.g. COM)",
    )
    parser.add_argument(
        "--use-cases-root", type=Path,
        default=Path("core/usecases/core"),
    )
    parser.add_argument(
        "--kpi-catalog-root", type=Path,
        default=Path("core/kpi_catalog"),
    )
    parser.add_argument(
        "--action-codes-root", type=Path,
        default=Path("core/action_codes"),
    )
    parser.add_argument(
        "--data-contracts-root", type=Path,
        default=Path("core/data_contracts"),
    )
    parser.add_argument(
        "--dist-root", type=Path,
        default=Path("products/fabric/powerbi/dist"),
    )
    parser.add_argument(
        "--mode", choices=["quick", "full"], default="full",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output results as JSON",
    )
    args = parser.parse_args()

    validator = PreflightValidator(
        kpi_catalog_root=args.kpi_catalog_root,
        action_codes_root=args.action_codes_root,
        data_contracts_root=args.data_contracts_root,
        dist_root=args.dist_root,
        mode=args.mode,
    )

    reports: List[PreflightReport] = []

    if args.bracket:
        reports.append(validator.run(args.bracket))
    elif args.domain:
        reports = validator.run_domain(args.use_cases_root, args.domain)
    else:
        # Run for all use cases
        for bracket in args.use_cases_root.rglob("UseCase_Bracket.yaml"):
            reports.append(validator.run(bracket))

    all_passed = all(r.passed for r in reports)

    if args.json:
        print(json.dumps([r.to_dict() for r in reports], indent=2))
    else:
        for r in reports:
            print(r.summary())
            print()

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    _cli_main()
