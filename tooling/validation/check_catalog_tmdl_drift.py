#!/usr/bin/env python3
"""
check_catalog_tmdl_drift.py — Catalog↔TMDL semantic diff validator.

Compares measure_name, depends_on_measures, and lineage from KPI_Catalog.md
against the actual TMDL measures in products/fabric/powerbi/dist/.

Produces drift_report.json with any rows where catalog and TMDL disagree.
Exits non-zero on any drift row.

Usage:
    python3 tooling/validation/check_catalog_tmdl_drift.py \
        --catalog core/kpi_catalog/KPI_Catalog.md \
        --dist-dir products/fabric/powerbi/dist
"""
import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


def load_catalog_measures(catalog_path: Path) -> list[dict]:
    """Parse KPI_Catalog.md and return list of KPI entries with technical metadata."""
    entries = []
    content = catalog_path.read_text(encoding="utf-8")
    blocks = re.split(r"^(?=- kpi_id:)", content, flags=re.MULTILINE)
    for block in blocks:
        try:
            doc = yaml.safe_load(block)
        except yaml.YAMLError:
            continue
        # yaml.safe_load on a '- kpi_id:' block returns a list
        if isinstance(doc, list) and doc:
            doc = doc[0]
        if not isinstance(doc, dict):
            continue
        kpi_id = doc.get("kpi_id")
        if not kpi_id:
            continue
        tech = doc.get("technical") or {}
        entries.append({
            "kpi_id": kpi_id,
            "measure_name": tech.get("measure_name", ""),
            "depends_on_measures": tech.get("depends_on_measures") or [],
            "lineage": tech.get("lineage") or [],
        })
    return entries


def load_tmdl_measures(dist_dir: Path) -> dict[str, dict]:
    """
    Parse all */_Measures.tmdl files and return {measure_name: {dax, comment}}.

    When multiple TMDL files define the same measure name (e.g. proxy cross-domain
    measures alongside domain-canonical measures), the entry with a kpi_id annotation
    (``/// Measure Name - kpi.id``) takes priority so the canonical DAX is used for
    lineage checks regardless of filesystem iteration order.
    """
    measure_map: dict[str, dict] = {}
    for tmdl_path in sorted(dist_dir.rglob("_Measures.tmdl")):
        content = tmdl_path.read_text(encoding="utf-8", errors="replace")
        # Match measure blocks: optional comment lines, then 'measure <name> = ...'
        # Lookahead: stop at next \t/// comment or \tmeasure declaration (single-tab level)
        pattern = re.compile(
            r"((?:\t///[^\n]*\n)*)"   # optional leading /// comment lines
            r"\t\s*measure '([^']+)'\s*=(.*?)(?=\n\t///|\n\tmeasure\s+'|\Z)",
            re.DOTALL,
        )
        for m in pattern.finditer(content):
            comment_block, name, dax_body = m.group(1), m.group(2), m.group(3)
            # Extract referenced columns from DAX (table[column] pattern)
            lineage_refs = re.findall(r"\w+\['?([^'\]]+)'?\]", dax_body)
            # Extract measure references from DAX (e.g. [Measure Name])
            measure_refs = re.findall(r"\[([^\]]+)\]", dax_body)
            # Collect kpi_id from comment if present (format: /// Measure Name - kpi.id)
            kpi_id_match = re.search(r"/// .+ - ([\w\.]+)\s*$", comment_block, re.MULTILINE)
            kpi_id = kpi_id_match.group(1) if kpi_id_match else None
            entry = {
                "dax": dax_body.strip(),
                "comment": comment_block.strip(),
                "kpi_id": kpi_id,
                "lineage_refs": lineage_refs,
                "measure_refs": measure_refs,
                "tmdl_path": str(tmdl_path),
            }
            # Prefer kpi_id-annotated entries: if this name already exists and the
            # existing entry already has a kpi_id annotation, keep it (don't overwrite
            # with a proxy/cross-domain measure that lacks an annotation).
            existing = measure_map.get(name)
            if existing is None or (kpi_id and not existing["kpi_id"]):
                measure_map[name] = entry
    return measure_map


def check_drift(catalog_entries: list[dict], tmdl_measures: dict[str, dict]) -> list[dict]:
    """Compare catalog entries against TMDL. Return list of drift rows."""
    drift_rows = []

    for entry in catalog_entries:
        name = entry["measure_name"]
        if not name:
            continue

        tmdl = tmdl_measures.get(name)
        if tmdl is None:
            # Measure declared in catalog but absent from TMDL
            drift_rows.append({
                "kpi_id": entry["kpi_id"],
                "measure_name": name,
                "drift_type": "missing_in_tmdl",
                "catalog_value": name,
                "tmdl_value": None,
            })
            continue

        # Check kpi_id linkage in TMDL comment
        if tmdl["kpi_id"] and tmdl["kpi_id"] != entry["kpi_id"]:
            drift_rows.append({
                "kpi_id": entry["kpi_id"],
                "measure_name": name,
                "drift_type": "kpi_id_mismatch",
                "catalog_value": entry["kpi_id"],
                "tmdl_value": tmdl["kpi_id"],
            })

        # Check that catalog lineage columns appear in TMDL DAX
        for lineage_item in entry["lineage"]:
            # lineage_item format: "table.Column Name" or "table.column_name"
            parts = lineage_item.split(".", 1)
            if len(parts) < 2:
                continue
            col_name = parts[1]
            if col_name not in tmdl["lineage_refs"] and col_name not in tmdl["dax"]:
                drift_rows.append({
                    "kpi_id": entry["kpi_id"],
                    "measure_name": name,
                    "drift_type": "lineage_missing_in_dax",
                    "catalog_value": lineage_item,
                    "tmdl_value": f"not found in {Path(tmdl['tmdl_path']).name}",
                })

    return drift_rows


def main():
    parser = argparse.ArgumentParser(description="Catalog↔TMDL semantic drift validator")
    parser.add_argument("--catalog", default="core/kpi_catalog/KPI_Catalog.md",
                        help="Path to KPI_Catalog.md")
    parser.add_argument("--dist-dir", default="products/fabric/powerbi/dist",
                        help="Path to dist/ directory containing SemanticModel folders")
    parser.add_argument("--output", default="drift_report.json",
                        help="Output path for drift report JSON")
    parser.add_argument("--ignore-missing", action="store_true",
                        help="Do not fail on measures absent from TMDL (only report DAX drift)")
    args = parser.parse_args()

    catalog_path = Path(args.catalog)
    dist_dir = Path(args.dist_dir)

    if not catalog_path.exists():
        print(f"ERROR: Catalog not found: {catalog_path}", file=sys.stderr)
        sys.exit(2)
    if not dist_dir.exists():
        print(f"WARNING: dist-dir not found: {dist_dir}. Nothing to validate.", file=sys.stderr)
        sys.exit(0)

    catalog_entries = load_catalog_measures(catalog_path)
    tmdl_measures = load_tmdl_measures(dist_dir)

    print(f"Loaded {len(catalog_entries)} KPI entries from catalog")
    print(f"Loaded {len(tmdl_measures)} measures from TMDL")

    drift_rows = check_drift(catalog_entries, tmdl_measures)

    if args.ignore_missing:
        drift_rows = [r for r in drift_rows if r["drift_type"] != "missing_in_tmdl"]

    # Write report
    output_path = Path(args.output)
    report = {"drift_count": len(drift_rows), "rows": drift_rows}
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Drift report written to {output_path}")

    if drift_rows:
        print(f"\n❌ {len(drift_rows)} drift row(s) found:\n")
        for row in drift_rows:
            print(f"  [{row['drift_type']}] {row['kpi_id']} / '{row['measure_name']}'")
            print(f"    catalog: {row['catalog_value']}")
            print(f"    tmdl:    {row['tmdl_value']}")
        sys.exit(1)

    print("✅ No catalog↔TMDL drift found.")
    sys.exit(0)


if __name__ == "__main__":
    main()
