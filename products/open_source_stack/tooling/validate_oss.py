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
from typing import Any, Dict, Iterable, List, Set

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

# Allow running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent))

from page_generator.page_validator import validate_page, validate_pages_directory


@dataclass
class CheckResult:
    check: str
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


STRICT_METRIC_PLACEHOLDER_PATTERNS = (
    re.compile(r"TODO:\s*translate", re.IGNORECASE),
    re.compile(r"\[manual\]", re.IGNORECASE),
)


def _load_ir(root: Path) -> Dict[str, Any]:
    ir_path = root / "tooling" / "ir" / "out" / "ir_v1.json"
    if not ir_path.exists():
        raise FileNotFoundError(f"IR file not found: {ir_path}")
    return json.loads(ir_path.read_text(encoding="utf-8-sig"))


def _collect_required_kpi_ids(ir: Dict[str, Any], selected_use_cases: List[str] | None = None) -> Set[str]:
    required: Set[str] = set()
    use_case_objects = ir.get("objects", {}).get("use_cases", {})
    selected = use_case_objects.keys() if selected_use_cases is None else selected_use_cases
    measure_specs = ir.get("measure_spec", {}) if isinstance(ir.get("measure_spec", {}), dict) else {}

    def add_with_dependencies(kpi_id: str) -> None:
        if not isinstance(kpi_id, str) or not kpi_id or kpi_id in required:
            return
        spec = measure_specs.get(kpi_id, {}) if isinstance(measure_specs, dict) else {}
        dependencies = spec.get("depends_on_measures", []) if isinstance(spec, dict) else []
        if isinstance(dependencies, list):
            for dep in dependencies:
                add_with_dependencies(dep)
        required.add(kpi_id)

    for use_case_id in selected:
        use_case = use_case_objects.get(use_case_id, {}) if isinstance(use_case_objects, dict) else {}
        orch = use_case.get("orchestration", {}) if isinstance(use_case, dict) else {}
        strategic = orch.get("strategic_kpi_id")
        if isinstance(strategic, str) and strategic:
            add_with_dependencies(strategic)
        for key in ("influencing_kpi_ids", "supporting_kpi_ids"):
            values = orch.get(key, [])
            if isinstance(values, list):
                for value in values:
                    if isinstance(value, str) and value:
                        add_with_dependencies(value)
    return required


def _iter_metric_files(dbt_metrics_dir: Path) -> Iterable[Path]:
    yield from sorted(dbt_metrics_dir.glob("*.yml"))
    yield from sorted(dbt_metrics_dir.glob("*.yaml"))


def _load_metrics_by_kpi(dbt_metrics_dir: Path) -> Dict[str, Dict[str, Any]]:
    if yaml is None:
        raise ImportError("PyYAML is required to validate dbt metrics")

    metrics_by_kpi: Dict[str, Dict[str, Any]] = {}
    for metrics_file in _iter_metric_files(dbt_metrics_dir):
        data = yaml.safe_load(metrics_file.read_text(encoding="utf-8-sig")) or {}
        for metric in data.get("metrics", []) or []:
            if not isinstance(metric, dict):
                continue
            meta = metric.get("meta", {}) if isinstance(metric.get("meta"), dict) else {}
            kpi_id = meta.get("kpi_id")
            if isinstance(kpi_id, str) and kpi_id:
                metrics_by_kpi[kpi_id] = metric
    return metrics_by_kpi


def _metric_has_placeholder(metric: Dict[str, Any]) -> bool:
    description = metric.get("description")
    if isinstance(description, str) and any(p.search(description) for p in STRICT_METRIC_PLACEHOLDER_PATTERNS):
        return True

    meta = metric.get("meta", {}) if isinstance(metric.get("meta"), dict) else {}
    if meta.get("needs_manual_review") is True:
        return True

    type_params = metric.get("type_params", {}) if isinstance(metric.get("type_params"), dict) else {}
    expr = type_params.get("expr")
    if isinstance(expr, str) and expr.strip() == "1":
        return True

    return False


def check_evidence_pages(root: Path, selected_use_cases: List[str] | None = None) -> CheckResult:
    """Validate all generated Evidence pages."""
    pages_dir = root / "products" / "open_source_stack" / "evidence_app" / "pages"
    result = CheckResult(check="validate_evidence_pages", passed=True)

    if not pages_dir.exists():
        result.errors.append("Evidence pages directory not found")
        result.passed = False
        return result

    md_files = list(pages_dir.glob("*.md"))
    if not md_files:
        result.errors.append("No generated Evidence pages found in pages/")
        result.passed = False
        return result

    scoped_files = md_files
    if selected_use_cases:
        expected_prefixes = [use_case.lower().replace("-", "_") + "_" for use_case in selected_use_cases]
        scoped_files = [
            md_file for md_file in md_files
            if any(md_file.name.startswith(prefix) for prefix in expected_prefixes)
        ]
        missing_use_cases = [
            use_case for use_case in selected_use_cases
            if not any(md_file.name.startswith(use_case.lower().replace("-", "_") + "_") for md_file in md_files)
        ]
        for use_case in missing_use_cases:
            result.errors.append(f"No generated Evidence pages found for use case '{use_case}'")

    for md_file in sorted(scoped_files):
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


def check_metrics_vs_kpi(root: Path, selected_use_cases: List[str] | None = None) -> CheckResult:
    """Check that dbt metrics exist for KPIs referenced in use case brackets."""
    result = CheckResult(check="check_metrics_vs_kpi", passed=True)
    dbt_metrics_dir = root / "products" / "open_source_stack" / "dbt_project" / "models" / "metrics"

    if not dbt_metrics_dir.exists():
        result.errors.append("dbt metrics directory not found")
        result.passed = False
        return result

    metric_files = list(_iter_metric_files(dbt_metrics_dir))
    if not metric_files:
        result.errors.append("No dbt metric definition files found")
        result.passed = False
        return result

    try:
        ir = _load_ir(root)
        metrics_by_kpi = _load_metrics_by_kpi(dbt_metrics_dir)
    except (FileNotFoundError, ImportError, json.JSONDecodeError, yaml.YAMLError) as exc:  # type: ignore[attr-defined]
        result.errors.append(str(exc))
        result.passed = False
        return result

    required_kpis = _collect_required_kpi_ids(ir, selected_use_cases)
    if not required_kpis:
        result.warnings.append("No orchestrated KPI references found in IR")
        return result

    for kpi_id in sorted(required_kpis):
        metric = metrics_by_kpi.get(kpi_id)
        if metric is None:
            result.errors.append(f"Missing dbt metric for KPI '{kpi_id}'")
            continue
        if _metric_has_placeholder(metric):
            result.errors.append(f"dbt metric for KPI '{kpi_id}' still contains placeholder/manual review markers")

    extra_metrics = sorted(set(metrics_by_kpi) - required_kpis)
    if extra_metrics:
        result.warnings.append(f"Found dbt metrics without orchestrated KPI reference: {', '.join(extra_metrics[:10])}")

    result.passed = len(result.errors) == 0
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


def run_all_checks(root: Path, selected_use_cases: List[str] | None = None) -> List[CheckResult]:
    """Run all OSS validation checks."""
    return [
        check_adapter_manifest(root),
        check_evidence_pages(root, selected_use_cases),
        check_theme_tokens(root),
        check_sql_style(root),
        check_metrics_vs_kpi(root, selected_use_cases),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate OSS stack artifacts")
    parser.add_argument("--root", type=Path, default=Path("."), help="Repository root")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--use-cases", default="", help="Comma-separated use case IDs to scope validation")
    args = parser.parse_args()

    root = args.root.resolve()
    selected_use_cases = [item.strip() for item in args.use_cases.split(",") if item.strip()]
    results = run_all_checks(root, selected_use_cases or None)

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
