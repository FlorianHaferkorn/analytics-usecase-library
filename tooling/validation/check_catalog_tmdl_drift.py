#!/usr/bin/env python3
"""
check_catalog_tmdl_drift.py — Catalog ↔ TMDL drift gate.

Checks that every KPI catalog entry with a non-empty measure_name is either:
  1. Implemented in a _Measures.tmdl file (exact match OR via a suffixed proxy, e.g.
     "Action Outcome Rate %" is satisfied by "Action Outcome Rate % (XD Log)"), OR
  2. Listed in core/kpi_catalog/planned.yaml (warning, not error).

Also enforces the cross-domain proxy naming rule:
  If the same un-suffixed measure name appears in two or more _Measures.tmdl files,
  the check fails (at least one must carry a parenthetical suffix).

Exit codes:
  0  — no errors (warnings may be present)
  1  — one or more errors found

Usage:
  python3 tooling/validation/check_catalog_tmdl_drift.py [--strict] [--repo-root PATH]

Options:
  --strict      Treat all missing measures (not in planned.yaml) as errors.
                Without this flag, missing measures that are also not in planned.yaml
                are still errors; planned entries emit warnings only.
  --repo-root   Path to the repository root (default: cwd).
"""

import argparse
import re
import sys
import os
import glob
from collections import defaultdict
from datetime import date

try:
    import yaml
except ImportError:
    yaml = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_yaml(path):
    if yaml is None:
        raise RuntimeError("PyYAML is required: pip install pyyaml")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _strip_suffix(name: str) -> str:
    """Return the base name without a parenthetical suffix, e.g.:
    'Action Outcome Rate % (XD Log)' -> 'Action Outcome Rate %'
    'NPS Index (Service)'            -> 'NPS Index'
    """
    return re.sub(r"\s*\([^)]+\)\s*$", "", name).strip()


def _has_suffix(name: str) -> bool:
    """Return True if name ends with a parenthetical suffix."""
    return bool(re.search(r"\s*\([^)]+\)\s*$", name))


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def parse_catalog(catalog_path: str) -> dict:
    """Parse KPI_Catalog.md and return {kpi_id: measure_name} for entries
    that have a non-empty measure_name."""
    with open(catalog_path, encoding="utf-8") as f:
        content = f.read()

    blocks = re.split(r"\n(?=- kpi_id:)", content)
    result = {}
    for block in blocks:
        kpi_match = re.search(r"^- kpi_id:\s*(\S+)", block)
        mn_match = re.search(r'measure_name:\s*"(.+?)"', block)
        if kpi_match and mn_match:
            kpi_id = kpi_match.group(1)
            measure_name = mn_match.group(1).strip()
            if measure_name:
                result[kpi_id] = measure_name
    return result


def parse_tmdl_measures(tmdl_files: list) -> dict:
    """Parse _Measures.tmdl files and return {filepath: [measure_name, ...]}
    excluding Action_* measures."""
    result = {}
    for path in tmdl_files:
        measures = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                m = re.match(r"\s*measure '(.+?)'", line)
                if m:
                    name = m.group(1)
                    if not name.startswith("Action_"):
                        measures.append(name)
        result[path] = measures
    return result


def parse_planned(planned_path: str) -> dict:
    """Parse planned.yaml and return {kpi_id: entry_dict}."""
    if not os.path.exists(planned_path):
        return {}
    data = _load_yaml(planned_path)
    if not data:
        return {}
    return {entry["kpi_id"]: entry for entry in data if "kpi_id" in entry}


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def _model_name_from_path(path: str) -> str:
    """Extract the SemanticModel name from a _Measures.tmdl file path.
    e.g. '.../Experience.SemanticModel/definition/tables/_Measures.tmdl'
         -> 'Experience.SemanticModel'
    """
    parts = path.replace("\\", "/").split("/")
    for part in parts:
        if part.endswith(".SemanticModel"):
            return part
    return os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(path))))


def check_duplicate_unsuffixed(tmdl_by_file: dict) -> list:
    """Return errors if the same un-suffixed measure name appears in 2+ distinct
    SemanticModel domains (i.e., different *.SemanticModel directories).

    Mirrors of the same model across dist/ and showcases/ are treated as one domain.
    """
    # Map un-suffixed name -> set of unique model names where it appears unsuffixed
    base_to_models = defaultdict(set)
    for path, names in tmdl_by_file.items():
        model_name = _model_name_from_path(path)
        for name in names:
            if not _has_suffix(name):
                base = _strip_suffix(name)
                base_to_models[base].add(model_name)

    errors = []
    for base, models in sorted(base_to_models.items()):
        if len(models) >= 2:
            models_str = ", ".join(sorted(models))
            errors.append(
                f"DUPLICATE: Un-suffixed measure '{base}' appears in {len(models)} domain models "
                f"({models_str}). Add a parenthetical suffix to cross-domain proxies per "
                f"TMDL_Allowed_Subset.md §20."
            )
    return errors


def check_catalog_coverage(
    catalog: dict,
    tmdl_by_file: dict,
    planned: dict,
    strict: bool,
) -> tuple:
    """Check that every catalog measure_name is covered by TMDL or planned.yaml.

    Returns (errors, warnings).
    """
    # Build a flat set of all TMDL measure names and their base names
    all_tmdl_names = set()
    all_tmdl_bases = set()
    for names in tmdl_by_file.values():
        for n in names:
            all_tmdl_names.add(n)
            all_tmdl_bases.add(_strip_suffix(n))

    errors = []
    warnings = []

    for kpi_id, measure_name in sorted(catalog.items()):
        base = _strip_suffix(measure_name)

        # Exact match OR proxy (suffixed variant) covers this entry
        if measure_name in all_tmdl_names or base in all_tmdl_bases:
            continue

        if kpi_id in planned:
            entry = planned[kpi_id]
            eta = entry.get("eta_date", "TBD")
            owner = entry.get("owner", "TBD")
            warnings.append(
                f"PLANNED [{kpi_id}] measure '{measure_name}' not yet in TMDL "
                f"(eta: {eta}, owner: {owner})"
            )
        else:
            errors.append(
                f"MISSING [{kpi_id}] measure '{measure_name}' is not implemented in "
                f"any _Measures.tmdl and is not listed in planned.yaml"
            )

    return errors, warnings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on any missing measure not covered by planned.yaml.",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root directory (default: current working directory).",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root or os.getcwd()

    catalog_path = os.path.join(repo_root, "core", "kpi_catalog", "KPI_Catalog.md")
    planned_path = os.path.join(repo_root, "core", "kpi_catalog", "planned.yaml")

    # Find all _Measures.tmdl files (exclude cursor/publish_staging and .cursor dirs)
    pattern = os.path.join(repo_root, "products", "**", "_Measures.tmdl")
    tmdl_files = [
        p for p in glob.glob(pattern, recursive=True)
        if ".cursor" not in p and "publish_staging" not in p
    ]

    if not os.path.exists(catalog_path):
        print(f"ERROR: KPI catalog not found at {catalog_path}", file=sys.stderr)
        return 1

    # Parse inputs
    catalog = parse_catalog(catalog_path)
    tmdl_by_file = parse_tmdl_measures(tmdl_files)
    planned = parse_planned(planned_path)

    all_errors = []
    all_warnings = []

    # Check 1: duplicate un-suffixed names
    dup_errors = check_duplicate_unsuffixed(tmdl_by_file)
    all_errors.extend(dup_errors)

    # Check 2: catalog coverage
    cov_errors, cov_warnings = check_catalog_coverage(catalog, tmdl_by_file, planned, args.strict)
    all_errors.extend(cov_errors)
    all_warnings.extend(cov_warnings)

    # Report
    if all_warnings:
        print(f"\n=== WARNINGS ({len(all_warnings)}) ===")
        for w in all_warnings:
            print(f"  WARNING: {w}")

    if all_errors:
        print(f"\n=== ERRORS ({len(all_errors)}) ===")
        for e in all_errors:
            print(f"  ERROR: {e}")
        print(f"\nDrift check FAILED: {len(all_errors)} error(s), {len(all_warnings)} warning(s)")
        return 1

    print(
        f"Drift check PASSED: 0 errors, {len(all_warnings)} warning(s) "
        f"({len(catalog)} catalog entries, {sum(len(v) for v in tmdl_by_file.values())} TMDL measures, "
        f"{len(planned)} planned entries)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
