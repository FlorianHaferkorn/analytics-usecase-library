#!/usr/bin/env python3
"""
preflight_measure_names.py — Measure-name uniqueness preflight check.

Reads all UseCase_Bracket.yaml files in a use-cases root and detects cases
where two brackets within the same domain declare the same KPI measure name,
which would cause measure-overwrite during TMDL generation (Phase 2).

Usage:
    python3 tooling/generator/preflight_measure_names.py --usecases-root core/usecases --catalog core/kpi_catalog/KPI_Catalog.md

Exit code 0 = no conflicts. Exit code 1 = conflicts found (orchestrator should abort).
"""
import argparse
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


def load_kpi_measure_map(catalog_path: Path) -> dict[str, str]:
    """Return {kpi_id: measure_name} from KPI_Catalog.md YAML blocks."""
    measure_map: dict[str, str] = {}
    content = catalog_path.read_text(encoding="utf-8")
    # Extract YAML blocks between '- kpi_id:' entries
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
        measure_name = (doc.get("technical") or {}).get("measure_name")
        if kpi_id and measure_name:
            measure_map[kpi_id] = measure_name
    return measure_map


def load_brackets(usecases_root: Path) -> list[dict]:
    """Load all UseCase_Bracket.yaml files, return list of dicts with metadata."""
    brackets = []
    for bracket_path in sorted(usecases_root.rglob("UseCase_Bracket.yaml")):
        try:
            with bracket_path.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict):
                continue
            brackets.append({
                "path": bracket_path,
                "id": data.get("use_case_id", bracket_path.parent.name),
                "domain": data.get("domain", "unknown"),
                "kpi_ids": data.get("kpi_ids", []) + data.get("influencing_kpi_ids", []),
            })
        except (yaml.YAMLError, OSError):
            continue
    return brackets


def check_uniqueness(brackets: list[dict], measure_map: dict[str, str]) -> list[str]:
    """Detect measure-name collisions within the same domain across different use cases."""
    errors = []
    # Group by domain
    by_domain: dict[str, list[dict]] = {}
    for b in brackets:
        by_domain.setdefault(b["domain"], []).append(b)

    for domain, domain_brackets in by_domain.items():
        # For each domain, build map: measure_name -> [use_case_ids]
        name_to_cases: dict[str, list[str]] = {}
        for bracket in domain_brackets:
            for kpi_id in bracket["kpi_ids"]:
                measure_name = measure_map.get(kpi_id)
                if not measure_name:
                    continue
                name_to_cases.setdefault(measure_name, []).append(bracket["id"])
        # Report conflicts
        for name, cases in name_to_cases.items():
            unique_cases = list(dict.fromkeys(cases))  # preserve order, deduplicate
            if len(unique_cases) > 1:
                errors.append(
                    f"Domain '{domain}': measure '{name}' declared in multiple brackets: {unique_cases}"
                )
    return errors


def main():
    parser = argparse.ArgumentParser(description="Measure-name uniqueness preflight check")
    parser.add_argument("--usecases-root", default="core/usecases",
                        help="Root directory containing UseCase_Bracket.yaml files")
    parser.add_argument("--catalog", default="core/kpi_catalog/KPI_Catalog.md",
                        help="Path to KPI_Catalog.md")
    args = parser.parse_args()

    catalog_path = Path(args.catalog)
    usecases_root = Path(args.usecases_root)

    if not catalog_path.exists():
        print(f"ERROR: Catalog not found: {catalog_path}", file=sys.stderr)
        sys.exit(2)
    if not usecases_root.exists():
        print(f"ERROR: Use-cases root not found: {usecases_root}", file=sys.stderr)
        sys.exit(2)

    measure_map = load_kpi_measure_map(catalog_path)
    brackets = load_brackets(usecases_root)
    errors = check_uniqueness(brackets, measure_map)

    print(f"Preflight: {len(brackets)} brackets, {len(measure_map)} KPI->measure mappings")

    if errors:
        print(f"\nFAIL: {len(errors)} measure-name conflict(s) found:\n")
        for e in errors:
            print(f"  {e}")
        print("\nOrchestrator will abort. Resolve conflicts before generating TMDL.")
        sys.exit(1)

    print("OK: No measure-name conflicts found.")
    sys.exit(0)


if __name__ == "__main__":
    main()
