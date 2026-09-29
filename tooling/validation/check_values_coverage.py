#!/usr/bin/env python3
"""
check_values_coverage.py — Epic B2: enumerated `Values:` coverage on dimensions.

Reports which **enumerable** dimension columns in a data contract carry curated
`allowed_values` (the `Values:` grounding facet, see AI_Description_Standard.md) and
which are still a gap. Enumerated values are the single biggest lever for NL ->
column-value mapping ("sales in the north" resolves only if `Region`'s domain is
known).

"Enumerable" (transparent heuristic — about column *semantics*, never the data):
a dimension column that is a low-cardinality categorical attribute — text-typed,
not a key/foreign key, whose name is not an identifier/label (``*Key``/``*Code``/
``*Id``/``*Name``) and not on a documented high-cardinality/free-text denylist.

Default output is a report (exit 0). Use ``--strict`` to exit 1 when an enumerable
column lacks `allowed_values` (off by default: some domains are deferred to
business curation rather than guessed).

Usage::

    python tooling/validation/check_values_coverage.py                 # all domains, report
    python tooling/validation/check_values_coverage.py --domain Commercial
    python tooling/validation/check_values_coverage.py --strict        # gate
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root for imports

from tooling.generator_core.ai_description import build_table_descriptions

# Domain -> contract filename (mirrors generate_semantic_model.DOMAIN_CONTRACT).
DOMAIN_CONTRACT: Dict[str, str] = {
    "Commercial": "commercial_sales.yaml",
    "Finance": "finance.yaml",
    "Operations": "operations.yaml",
    "SupplyChain": "supply_chain.yaml",
    "Experience": "experience.yaml",
}

_TEXT_TYPES = {"text", "string"}
_IDENTIFIER_SUFFIXES = ("Key", "Code", "Id", "ID", "Name")
# Documented high-cardinality / free-text columns — labels, not enumerable domains.
_NOT_ENUMERABLE = {
    "Country", "City", "Brand", "ProductFamily", "Month", "Week", "Promotion",
    # high-cardinality references (confirmed against the Aurora gold data)
    "Entity", "Plant", "Location", "Customer",
    # period labels, one value per month (132 in Aurora gold dim_date, measured 29.09.2026)
    "Fiscal Period", "CalendarYearMonth",
}


def is_enumerable(col) -> bool:
    """True when a dimension column is a low-cardinality categorical attribute."""
    if (col.data_type or "").lower() not in _TEXT_TYPES:
        return False
    if col.role in ("key", "foreign_key"):
        return False
    if col.name.endswith(_IDENTIFIER_SUFFIXES):
        return False
    if col.name in _NOT_ENUMERABLE:
        return False
    return True


@dataclass
class DomainCoverage:
    domain: str
    covered: List[str]   # "table.column" with allowed_values
    missing: List[str]   # enumerable "table.column" without allowed_values

    @property
    def enumerable(self) -> int:
        return len(self.covered) + len(self.missing)

    @property
    def pct(self) -> float:
        return 100.0 if self.enumerable == 0 else 100.0 * len(self.covered) / self.enumerable


def domain_coverage(domain: str, contracts_dir: Path) -> DomainCoverage:
    contract = Path(contracts_dir) / DOMAIN_CONTRACT[domain]
    covered: List[str] = []
    missing: List[str] = []
    for tbl in build_table_descriptions(contract):
        if tbl.kind != "dimension":
            continue
        for col in tbl.columns:
            if not is_enumerable(col):
                continue
            (covered if col.allowed_values else missing).append(f"{tbl.name}.{col.name}")
    return DomainCoverage(domain, covered, missing)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report enumerated Values: coverage on dimensions.")
    parser.add_argument("--domain", "-d", choices=list(DOMAIN_CONTRACT.keys()))
    parser.add_argument("--strict", action="store_true", help="Exit 1 if any enumerable column lacks allowed_values")
    parser.add_argument("--contracts-dir", default=str(Path(__file__).resolve().parents[2] / "core" / "data_contracts" / "domains"))
    args = parser.parse_args(argv)

    contracts_dir = Path(args.contracts_dir)
    domains = [args.domain] if args.domain else list(DOMAIN_CONTRACT)
    any_missing = False
    for domain in domains:
        if not (contracts_dir / DOMAIN_CONTRACT[domain]).exists():
            continue
        cov = domain_coverage(domain, contracts_dir)
        if cov.enumerable == 0:
            continue
        print(f"{domain}: {len(cov.covered)}/{cov.enumerable} enumerable dim columns carry Values: ({cov.pct:.0f}%)")
        for loc in cov.missing:
            any_missing = True
            print(f"    gap: {loc} — no allowed_values")
    if args.strict and any_missing:
        print("FAIL: enumerable dimension columns are missing allowed_values.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
