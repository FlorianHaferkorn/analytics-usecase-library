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

Per table, additively (older consumers read only ``name/kind/domain/columns``, which stay as they
were): ``showcase`` (bool, default true: the Aurora showcase has data for the table) and
``column_specs`` — one object per column with only the keys the contract sets out of
``name, source_column, type, nullable, ref, unknown_member, checks, target_state, agg, synonyms`` (A-23; the
structured quality fields are described in ``core/data_contracts/domains/README.md``). ``agg`` (default
aggregation of a measure column) and ``synonyms`` (curated names) since 30.09.2026: ODCS v3.2 writes them
as ``semanticType: measure`` and ``synonyms`` (Meridian D-590, ``tooling/superversion/odcs.py``).

**Exactly one entry per table name** (Bus-Matrix, 29.09.2026): a conformed table is defined once,
in its owning domain; other domains refer to it (``conformed_from``). ``domain`` is the owning
domain, ``domains`` the sorted list of every domain that defines or refers to the table. Name-keyed
consumers (ODCS ``to_odcs``, Meridian ``_katalog_tabelle`` for ``emit_dq_gates``/``emit_mlv``) now
see the one definition instead of the first of several.

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

if __package__ in (None, ""):          # run as a script: make `tooling.` importable
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tooling.utils.data_contracts import is_reference, load_contracts, users  # noqa: E402


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


SPEC_KEYS = ("name", "source_column", "type", "nullable", "ref", "unknown_member", "checks", "target_state",
             "agg", "synonyms")


def _column_spec(col: dict) -> dict:
    """The column as an object, with only the keys the contract sets (order of SPEC_KEYS)."""
    return {k: col[k] for k in SPEC_KEYS if k in col}


def _load_tables(contracts_dir: Path) -> list[dict]:
    """Every dimension + fact table with its column names and column specs, from the contracts.

    One entry per definition — a conformed reference (``conformed_from``) adds only its domain to
    the owner's ``domains`` list, never a second entry.
    """
    tables: list[dict] = []
    contracts = load_contracts(contracts_dir)
    used_by = users(contracts)
    for path, doc in contracts:
        domain = doc.get("domain", path.stem)
        for kind, key in (("dimension", "dimension"), ("fact", "fact")):
            for tbl in doc.get(key) or []:
                if not isinstance(tbl, dict) or not tbl.get("name") or is_reference(tbl):
                    continue
                specs, seen = [], set()
                for c in tbl.get("columns") or []:
                    if isinstance(c, dict) and c.get("name") and c["name"] not in seen:
                        seen.add(c["name"])
                        specs.append(_column_spec(c))
                tables.append({
                    "name": tbl["name"],
                    "kind": kind,
                    "domain": domain,
                    "domains": used_by.get(tbl["name"], [domain]),
                    "columns": sorted(seen),
                    "showcase": tbl.get("showcase", True) is not False,
                    "column_specs": specs,
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
