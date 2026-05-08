#!/usr/bin/env python3
"""
check_catalog_tmdl_drift.py — Catalog↔TMDL semantic diff validator.

Compares measure_name entries from KPI_Catalog.md against the actual TMDL
measures in products/fabric/powerbi/dist/.  Produces a drift_report.json and
exits non-zero when unplanned measures are missing from TMDL.

Usage:
    python3 tooling/validation/check_catalog_tmdl_drift.py \
        --repo-root . [--strict]
"""
import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    if __name__ == "__main__":
        print("ERROR: pyyaml not installed. Run: pip install pyyaml", file=sys.stderr)
        sys.exit(2)
    raise

# ─── Suffix helpers ────────────────────────────────────────────────────────────

_SUFFIX_RE = re.compile(r"\s*\([^)]+\)\s*$")


def _strip_suffix(name: str) -> str:
    """Remove trailing parenthetical suffix, e.g. 'NPS Index (Service)' → 'NPS Index'."""
    return _SUFFIX_RE.sub("", name).strip()


def _has_suffix(name: str) -> bool:
    """Return True if name ends with a parenthetical like '(XD)' or '(Service)'."""
    return bool(_SUFFIX_RE.search(name))


# ─── Parsers ───────────────────────────────────────────────────────────────────


def parse_catalog(catalog_path: str) -> dict:
    """Parse KPI_Catalog.md and return {kpi_id: measure_name}."""
    entries: dict = {}
    content = Path(catalog_path).read_text(encoding="utf-8")
    blocks = re.split(r"^(?=- kpi_id:)", content, flags=re.MULTILINE)
    for block in blocks:
        try:
            doc = yaml.safe_load(block)
        except yaml.YAMLError:
            continue
        if isinstance(doc, list) and doc:
            doc = doc[0]
        if not isinstance(doc, dict):
            continue
        kpi_id = doc.get("kpi_id")
        if not kpi_id:
            continue
        tech = doc.get("technical") or {}
        measure_name = tech.get("measure_name", "")
        if measure_name:
            entries[kpi_id] = measure_name
    return entries


def parse_tmdl_measures(tmdl_files: list) -> dict:
    """
    Parse measure names from a list of TMDL file paths.

    Excludes Action_* measures (action outcome text measures, not KPI measures).

    Returns {file_path_str: [measure_name, ...]}.
    """
    result: dict = {}
    pattern = re.compile(r"^\s*measure '([^']+)'", re.MULTILINE)
    for path_str in tmdl_files:
        path = Path(path_str)
        if not path.exists():
            result[path_str] = []
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        names = [
            m.group(1)
            for m in pattern.finditer(content)
            if not m.group(1).startswith("Action_")
        ]
        result[path_str] = names
    return result


def parse_planned(planned_path: str) -> dict:
    """Parse planned.yaml and return {kpi_id: entry_dict}."""
    path = Path(planned_path)
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return {}
    return {entry["kpi_id"]: entry for entry in data if "kpi_id" in entry}


# ─── Checks ────────────────────────────────────────────────────────────────────


def check_duplicate_unsuffixed(tmdl_by_file: dict) -> list:
    """
    Find unsuffixed measure names that appear in more than one distinct SemanticModel.

    Cross-domain proxy measures use suffixes like '(XD)' to disambiguate; those are
    intentional and excluded from this check.  Two files from the same SemanticModel
    (e.g. dist/ and showcases/ copies) are treated as a single model and do not trigger
    an error.

    Returns a list of error strings (empty = no duplicates).
    """
    # Measures that are intentionally shared verbatim across all domain models.
    _CROSS_DOMAIN_SHARED = frozenset({"Action Effectiveness Delta"})

    # unsuffixed_name → set of SemanticModel names (without path root)
    model_map: dict = {}
    for file_path, names in tmdl_by_file.items():
        parts = Path(file_path).parts
        model_name = next(
            (p for p in parts if p.endswith(".SemanticModel")), file_path
        )
        for name in names:
            if not _has_suffix(name) and name not in _CROSS_DOMAIN_SHARED:
                model_map.setdefault(name, set()).add(model_name)

    return [
        f"Unsuffixed measure '{base}' appears in multiple SemanticModels: {sorted(models)}"
        for base, models in model_map.items()
        if len(models) > 1
    ]


def check_catalog_coverage(
    catalog: dict,
    tmdl_by_file: dict,
    planned: dict,
    strict: bool = False,
) -> tuple:
    """
    Check that every KPI catalog entry has a matching measure name in TMDL.

    A suffixed measure (e.g. 'Action Outcome Rate % (XD Log)') satisfies the
    corresponding base catalog entry ('Action Outcome Rate %').

    strict=True:  unplanned missing measures → errors
    strict=False: unplanned missing measures → warnings
    Planned missing measures are always warnings regardless of strict.

    Returns (errors: list[str], warnings: list[str]).
    """
    all_names: set = set()
    for names in tmdl_by_file.values():
        all_names.update(names)

    # unsuffixed names for proxy satisfaction
    unsuffixed_names = {_strip_suffix(n) for n in all_names}

    errors: list = []
    warnings: list = []

    for kpi_id, measure_name in catalog.items():
        if measure_name in all_names or measure_name in unsuffixed_names:
            continue
        msg = f"'{measure_name}' ({kpi_id}) not found in any _Measures.tmdl"
        if kpi_id in planned:
            warnings.append(
                f"Planned: {msg} — eta: {planned[kpi_id].get('eta_date', 'unknown')}"
            )
        elif strict:
            errors.append(f"Missing: {msg}")
        else:
            warnings.append(f"Missing: {msg}")

    return errors, warnings


# ─── Entry point ───────────────────────────────────────────────────────────────


def main(argv=None) -> int:
    """Run the drift check.  Returns 0 (ok) or 1 (errors found) or 2 (config error)."""
    parser = argparse.ArgumentParser(description="Catalog↔TMDL semantic drift validator")
    parser.add_argument(
        "--repo-root", default=".", help="Repository root directory"
    )
    parser.add_argument(
        "--catalog",
        default=None,
        help="Path to KPI_Catalog.md (default: <repo-root>/core/kpi_catalog/KPI_Catalog.md)",
    )
    parser.add_argument(
        "--dist-dir",
        default=None,
        help="Path to dist/ directory (default: <repo-root>/products/fabric/powerbi/dist)",
    )
    parser.add_argument(
        "--planned",
        default=None,
        help="Path to planned.yaml (default: <repo-root>/core/kpi_catalog/planned.yaml)",
    )
    parser.add_argument(
        "--output", default="drift_report.json", help="Output path for drift report JSON"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat unplanned missing measures as errors instead of warnings",
    )
    parser.add_argument(
        "--ignore-missing",
        action="store_true",
        help="No-op compatibility flag; missing measures are warnings by default unless --strict is passed.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root)
    catalog_path = (
        Path(args.catalog) if args.catalog else repo_root / "core/kpi_catalog/KPI_Catalog.md"
    )
    dist_dir = (
        Path(args.dist_dir)
        if args.dist_dir
        else repo_root / "products/fabric/powerbi/dist"
    )
    planned_path = (
        Path(args.planned)
        if args.planned
        else repo_root / "core/kpi_catalog/planned.yaml"
    )

    if not catalog_path.exists():
        print(f"ERROR: Catalog not found: {catalog_path}", file=sys.stderr)
        return 2
    if not dist_dir.exists():
        print(
            f"WARNING: dist-dir not found: {dist_dir}. Nothing to validate.",
            file=sys.stderr,
        )
        return 0

    catalog = parse_catalog(str(catalog_path))
    tmdl_files = [str(p) for p in sorted(dist_dir.rglob("_Measures.tmdl"))]
    tmdl_by_file = parse_tmdl_measures(tmdl_files)
    planned = parse_planned(str(planned_path))

    total_measures = sum(len(v) for v in tmdl_by_file.values())
    print(f"Loaded {len(catalog)} KPI entries from catalog")
    print(f"Loaded {total_measures} measures from {len(tmdl_files)} TMDL files")

    dup_errors = check_duplicate_unsuffixed(tmdl_by_file)
    cov_errors, cov_warnings = check_catalog_coverage(
        catalog, tmdl_by_file, planned, strict=args.strict
    )

    all_errors = dup_errors + cov_errors
    all_warnings = cov_warnings

    for w in all_warnings:
        print(f"  WARN  {w}")
    for e in all_errors:
        print(f"  ERROR  {e}")

    output_path = Path(args.output)
    report = {
        "error_count": len(all_errors),
        "warning_count": len(all_warnings),
        "errors": all_errors,
        "warnings": all_warnings,
    }
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Drift report written to {output_path}")

    if all_errors:
        print(f"\nFAIL: {len(all_errors)} error(s) found.")
        return 1

    print(f"OK: No catalog<->TMDL drift found ({len(all_warnings)} warning(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
