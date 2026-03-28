"""
OSS Stack Validation Runner

Runs all validation checks for the open-source Evidence.dev stack.
Mirrors tooling/run_stage1_checks.ps1 and
products/fabric/powerbi/tooling/run_fabric_checks.ps1 but for OSS artifacts.

Usage:
    python products/open_source_stack/tooling/validate_oss.py --root .
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Allow running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent))

from page_generator.page_validator import validate_page, validate_pages_directory


@dataclass
class CheckResult:
    check: str
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def check_evidence_pages(root: Path) -> CheckResult:
    """Validate all generated Evidence pages."""
    pages_dir = root / "products" / "open_source_stack" / "evidence_app" / "pages"
    result = CheckResult(check="validate_evidence_pages", passed=True)

    if not pages_dir.exists():
        result.warnings.append("No pages directory found — skipping")
        return result

    md_files = list(pages_dir.glob("*.md"))
    if not md_files:
        result.warnings.append("No .md files in pages/ — skipping")
        return result

    for md_file in sorted(md_files):
        content = md_file.read_text(encoding="utf-8")
        page_result = validate_page(content, str(md_file.relative_to(root)))
        result.errors.extend(
            f"{md_file.name}: {e}" for e in page_result.errors
        )
        result.warnings.extend(
            f"{md_file.name}: {w}" for w in page_result.warnings
        )

    result.passed = len(result.errors) == 0
    return result


def check_adapter_manifest(root: Path) -> CheckResult:
    """Validate the adapter manifest exists and is valid JSON."""
    result = CheckResult(check="validate_adapter_manifest", passed=True)
    manifest_path = root / "products" / "open_source_stack" / "adapter.json"

    if not manifest_path.exists():
        result.errors.append("adapter.json not found")
        result.passed = False
        return result

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        result.errors.append(f"Invalid JSON: {e}")
        result.passed = False
        return result

    required = ["schema_version", "adapter_id", "name", "version", "capabilities", "commands"]
    for key in required:
        if key not in data:
            result.errors.append(f"Missing required key: {key}")

    result.passed = len(result.errors) == 0
    return result


def check_metrics_vs_kpi(root: Path) -> CheckResult:
    """Check that dbt metrics exist for KPIs referenced in use case brackets."""
    result = CheckResult(check="check_metrics_vs_kpi", passed=True)
    dbt_metrics_dir = root / "products" / "open_source_stack" / "dbt_project" / "models" / "metrics"

    if not dbt_metrics_dir.exists():
        result.warnings.append("dbt metrics directory not found — skipping")
        return result

    # This is a placeholder for the full check.
    # When dbt metrics are generated, this will verify each KPI in the IR
    # has a corresponding dbt metric definition.
    result.warnings.append("Metric-vs-KPI check not yet implemented (Phase 2)")
    return result


def check_theme_tokens(root: Path) -> CheckResult:
    """Check that Evidence pages only use governed design tokens."""
    result = CheckResult(check="validate_theme_tokens", passed=True)
    pages_dir = root / "products" / "open_source_stack" / "evidence_app" / "pages"

    if not pages_dir.exists():
        return result

    governed = {"fill-primary", "text-brand-header", "bg-surface"}

    for md_file in sorted(pages_dir.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        custom_classes = re.findall(r'class="([^"]*)"', content)
        for cls_str in custom_classes:
            for cls in cls_str.split():
                if cls.startswith(("fill-", "text-brand-", "bg-")) and cls not in governed:
                    result.errors.append(f"{md_file.name}: non-governed token '{cls}'")

    result.passed = len(result.errors) == 0
    return result


def check_sql_style(root: Path) -> CheckResult:
    """Check SQL best practices in Evidence pages."""
    result = CheckResult(check="validate_sql_style", passed=True)
    pages_dir = root / "products" / "open_source_stack" / "evidence_app" / "pages"

    if not pages_dir.exists():
        return result

    for md_file in sorted(pages_dir.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        # Extract SQL blocks
        sql_blocks = re.findall(r"```sql\s+\w+\n(.*?)```", content, re.DOTALL)
        for i, sql in enumerate(sql_blocks):
            if re.search(r"SELECT\s+\*", sql, re.IGNORECASE):
                result.errors.append(f"{md_file.name}: SQL block {i+1} uses SELECT *")

    result.passed = len(result.errors) == 0
    return result


def run_all_checks(root: Path) -> List[CheckResult]:
    """Run all OSS validation checks."""
    checks = [
        check_adapter_manifest,
        check_evidence_pages,
        check_theme_tokens,
        check_sql_style,
        check_metrics_vs_kpi,
    ]
    return [check(root) for check in checks]


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate OSS stack artifacts")
    parser.add_argument("--root", type=Path, default=Path("."), help="Repository root")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    root = args.root.resolve()
    results = run_all_checks(root)

    if args.json:
        output = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": [asdict(r) for r in results],
            "passed": all(r.passed for r in results),
        }
        print(json.dumps(output, indent=2))
    else:
        all_passed = True
        for r in results:
            status = "PASS" if r.passed else "FAIL"
            print(f"  [{status}] {r.check}")
            for e in r.errors:
                print(f"         ERROR: {e}")
            for w in r.warnings:
                print(f"         WARN:  {w}")
            if not r.passed:
                all_passed = False

        print()
        if all_passed:
            print("All OSS checks passed.")
        else:
            print("Some OSS checks failed.")
            sys.exit(1)


if __name__ == "__main__":
    main()
