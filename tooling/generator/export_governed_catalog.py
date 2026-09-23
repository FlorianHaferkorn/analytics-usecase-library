#!/usr/bin/env python3
"""
export_governed_catalog.py — export ALUCA's governed truth to a portable catalog.

Emits the ``meridian/governed-catalog/v1`` JSON consumed by the Meridian lineage drift check
(``core/dataarch_engine/blueprint/provision_lineage.py`` → ``drift_check.py``). It joins ALUCA's
**two** governed-truth authorities so drift can be checked at measure *and* table/column level:

- **KPI catalog** (``core/kpi_catalog/kpis/*.yaml``)  → measures (measure_name, aliases, lineage)
- **Data contracts** (``core/data_contracts/domains/*.yaml``) → tables + columns (the schema
  authority — not just KPIs)

The drift check then diffs a live Fabric admin scan against this file: MEASURE_MISSING /
MEASURE_UNDOCUMENTED / TABLE_MISSING / COLUMN_MISSING. Read-only; emits JSON, runs nothing.

Usage:
    python3 tooling/generator/export_governed_catalog.py --repo-root . --out governed_catalog.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    if __name__ == "__main__":
        print("ERROR: pyyaml not installed. Run: pip install pyyaml", file=sys.stderr)
        sys.exit(2)
    raise


def _load_measures(kpi_dir: Path) -> list[dict]:
    """One measure per KPI file: measure_name + aliases/synonyms + table.column lineage."""
    measures: list[dict] = []
    for path in sorted(kpi_dir.glob("*.yaml")):
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue
        if not isinstance(doc, dict):
            continue
        tech = doc.get("technical") or {}
        measure_name = tech.get("measure_name")
        if not measure_name:
            continue
        aliases = sorted({*(doc.get("aliases") or []), *(doc.get("synonyms") or [])} - {measure_name})
        measures.append({
            "kpi_id": doc.get("kpi_id", path.stem),
            "measure_name": measure_name,
            "aliases": aliases,
            "lineage": sorted(set(tech.get("lineage") or [])),   # ["fact_sales.Net Sales Amount", …]
        })
    return measures


def _load_tables(contracts_dir: Path) -> list[dict]:
    """Every dimension + fact table with its column names, from the data contracts."""
    tables: list[dict] = []
    for path in sorted(contracts_dir.glob("*.yaml")):
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue
        if not isinstance(doc, dict):
            continue
        domain = doc.get("domain", path.stem)
        for kind, key in (("dimension", "dimension"), ("fact", "fact")):
            for tbl in doc.get(key) or []:
                if not isinstance(tbl, dict) or not tbl.get("name"):
                    continue
                cols = [c.get("name") for c in (tbl.get("columns") or [])
                        if isinstance(c, dict) and c.get("name")]
                tables.append({
                    "name": tbl["name"],
                    "kind": kind,
                    "domain": domain,
                    "columns": sorted(set(cols)),
                })
    return tables


def build_governed_catalog(repo_root: Path) -> dict:
    """Join KPI catalog (measures) + data contracts (tables/columns) → governed-catalog/v1."""
    measures = _load_measures(repo_root / "core" / "kpi_catalog" / "kpis")
    tables = _load_tables(repo_root / "core" / "data_contracts" / "domains")
    return {
        "schema": "meridian/governed-catalog/v1",
        "measures": sorted(measures, key=lambda m: (m["measure_name"], m["kpi_id"])),
        "tables": sorted(tables, key=lambda t: t["name"]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export ALUCA governed truth → governed-catalog/v1")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, default=Path("governed_catalog.json"))
    args = parser.parse_args(argv)

    catalog = build_governed_catalog(args.repo_root)
    args.out.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"governed catalog: {len(catalog['measures'])} measures, {len(catalog['tables'])} tables "
          f"→ {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
