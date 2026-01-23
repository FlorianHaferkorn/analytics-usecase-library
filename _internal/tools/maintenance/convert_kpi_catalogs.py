#!/usr/bin/env python3
"""Utility to normalize KPI catalogs to the new business schema."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List

import yaml

CATALOG_PATTERN = "KPI_Catalog.md"
SCHEMA_FILENAME = "KPI_Catalog_SCHEMA.md"

BUSINESS_KEYS = {"purpose", "definition", "grain_scope", "unit_format", "interpretation"}
TECHNICAL_KEYS = {
    "dax_name",
    "dax_expression",
    "formatString",
    "description",
    "lineage",
    "source_grain",
    "source_column_ref",
    "depends_on",
    "depends_on_ids",
    "source_system",
    "verified",
    "displayFolder",
}


@dataclass
class CatalogEntry:
    raw: str
    data: Dict


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def normalize_entry(block: str) -> str:
    """Fix indentation quirks so PyYAML can parse the legacy files."""
    lines = block.splitlines()
    normalized: List[str] = []
    current_section: str | None = None

    for line in lines:
        stripped = line.lstrip()
        if not stripped:
            normalized.append(line)
            continue

        if stripped.startswith("- kpi_id:"):
            current_section = None
            normalized.append(stripped if line.startswith("-") else line)
            continue

        if stripped.startswith("business:"):
            current_section = "business"
            normalized.append("  business:")
            continue

        if stripped.startswith("technical:"):
            current_section = "technical"
            normalized.append("  technical:")
            continue

        if stripped.startswith("governance:"):
            current_section = "governance"
            normalized.append("  governance:")
            continue

        if stripped.startswith("metadata_quality:"):
            current_section = "metadata_quality"
            normalized.append("  metadata_quality:")
            continue

        key = stripped.split(":", 1)[0]
        if current_section == "business" and key in BUSINESS_KEYS:
            normalized.append(f"    {stripped}")
            continue

        if current_section == "technical" and key in TECHNICAL_KEYS:
            normalized.append(f"    {stripped}")
            continue

        normalized.append(line)

    return "\n".join(normalized)


def parse_catalog(path: Path) -> List[CatalogEntry]:
    text = path.read_text(encoding="utf-8")
    blocks = re.findall(r"```yaml\s*(.*?)\s*```", text, flags=re.S)
    entries: List[CatalogEntry] = []

    for block in blocks:
        current: List[str] = []
        for line in block.splitlines():
            if line.strip().startswith("- kpi_id:") and current:
                entries.append(_load_entry("\n".join(current)))
                current = []
            if current or line.strip():
                current.append(line)
        if current:
            entries.append(_load_entry("\n".join(current)))
    return entries


def _load_entry(raw_block: str) -> CatalogEntry:
    normalized = normalize_entry(raw_block)
    data = yaml.safe_load(normalized)
    if isinstance(data, list):
        data = data[0]
    return CatalogEntry(raw=normalized, data=data)


def normalize_date(value) -> str:
    if not value:
        return date.today().strftime("%d.%m.%Y")
    value = str(value).strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y.%m.%d"):
        try:
            return datetime.strptime(value, fmt).strftime("%d.%m.%Y")
        except ValueError:
            continue
    return value


def sanitize_text(value: str) -> str:
    return value.replace("€", "EUR").strip()


def transform_entry(entry: Dict, id_to_measure: Dict[str, str]) -> Dict:
    kpi = {
        "kpi_id": entry.get("kpi_id"),
        "kpi_key": entry.get("kpi_key"),
        "kpi_type": entry.get("kpi_type"),
    }

    impact = entry.get("impact_dimension") or entry.get("impact")
    if impact and impact.lower() == "efficiency":
        impact = "Efficiency"
    kpi["impact_dimension"] = impact

    domain_tag = entry.get("domain_tag")
    if isinstance(domain_tag, str):
        domain_tag = [domain_tag]
    if not domain_tag and impact:
        domain_tag = [impact]
    kpi["domain_tag"] = domain_tag or []

    use_case = entry.get("use_case_ref")
    if isinstance(use_case, str):
        use_case = [use_case]
    kpi["use_case_ref"] = use_case or []
    kpi["calc_type"] = entry.get("calc_type") or "amount"

    business = entry.get("business") or {}
    biz_block = {}
    for key in ["purpose", "definition", "grain_scope", "unit_format", "interpretation"]:
        val = business.get(key)
        if isinstance(val, list):
            val = " ".join(str(v) for v in val)
        if val:
            val = sanitize_text(str(val))
        else:
            val = "TODO - add interpretation." if key == "interpretation" else ""
        biz_block[key] = val
    kpi["business"] = biz_block

    tech = entry.get("technical") or {}
    lineage = tech.get("lineage") or []
    if isinstance(lineage, str):
        lineage = [lineage]
    dep_ids = entry.get("depends_on_ids") or tech.get("depends_on_ids") or []
    dep_names = entry.get("depends_on") or tech.get("depends_on") or []
    if isinstance(dep_ids, str):
        dep_ids = [dep_ids]
    if isinstance(dep_names, str):
        dep_names = [dep_names]
    depends = []
    if dep_ids:
        for dep in dep_ids:
            depends.append(id_to_measure.get(dep) or dep)
    elif dep_names:
        depends.extend(dep_names)
    else:
        existing = tech.get("depends_on_measures")
        if isinstance(existing, list):
            depends = existing
        elif isinstance(existing, str):
            depends = [existing]
    kpi["technical"] = {
        "dax_name": tech.get("dax_name") or tech.get("daxName") or "",
        "depends_on_measures": depends,
        "lineage": lineage,
    }

    gov = entry.get("governance") or {}
    qa_rules = gov.get("qa_rules")
    if isinstance(qa_rules, str):
        qa_rules = [qa_rules]
    elif not isinstance(qa_rules, list):
        qa_rules = []
    kpi["governance"] = {
        "business_owner": gov.get("business_owner", ""),
        "data_owner": gov.get("data_owner", ""),
        "steward": gov.get("steward", ""),
        "review_cycle": gov.get("review_cycle", ""),
        "validation_process": gov.get("validation_process", ""),
        "qa_rules": qa_rules,
        "version": gov.get("version", "v1.0"),
    }

    md = entry.get("metadata_quality") or {}
    try:
        completeness = round(float(md.get("completeness_score")), 2)
    except (TypeError, ValueError):
        completeness = 0.8
    kpi["metadata_quality"] = {
        "completeness_score": completeness,
        "last_review": normalize_date(md.get("last_review") or gov.get("last_review")),
    }

    aliases = entry.get("aliases")
    if aliases:
        if isinstance(aliases, str):
            aliases = [aliases]
        kpi["aliases"] = aliases

    return kpi


def build_catalog_content(entries: List[Dict], title: str) -> str:
    strategic = [e for e in entries if (e.get("kpi_type") or "").lower() == "strategic"]
    supporting = [e for e in entries if (e.get("kpi_type") or "").lower() != "strategic"]
    strategic_yaml = yaml.safe_dump(strategic, sort_keys=False, width=120, allow_unicode=True)
    supporting_yaml = yaml.safe_dump(supporting, sort_keys=False, width=120, allow_unicode=True)

    header = (
        f"# KPI Catalog - {title}\n\n---\n\n"
        "Schema: see `/_includes/kpi_catalog/{schema}`\n\n"
        "## KPIs - Strategic\n```yaml\n{strategic}```\n\n"
        "## KPIs - Supporting / Diagnostic\n```yaml\n{supporting}```\n"
    )
    return header.format(
        schema=SCHEMA_FILENAME,
        strategic=strategic_yaml,
        supporting=supporting_yaml,
    )


def process_catalog(path: Path, dry_run: bool = False) -> None:
    entries = parse_catalog(path)
    id_to_measure = {
        entry.data.get("kpi_id"): (entry.data.get("technical") or {}).get("dax_name", "")
        for entry in entries
    }
    converted = [transform_entry(entry.data, id_to_measure) for entry in entries]
    title = path.stem.replace("KPI_Catalog_", "").replace("_", " ")
    content = build_catalog_content(converted, title)

    if dry_run:
        print(f"=== Preview {path.name} ({len(entries)} KPIs) ===")
        print("\n".join(content.splitlines()[:40]))
        print("...")  # truncate preview
    else:
        path.write_text(content, encoding="utf-8")
        print(f"Updated {path.name} ({len(entries)} KPIs)")


def resolve_catalogs(targets: List[str], all_flag: bool) -> List[Path]:
    catalog_dir = repo_root() / "_includes" / "kpi_catalog"
    if all_flag:
        files = [
            p
            for p in catalog_dir.glob(CATALOG_PATTERN)
            if not p.name.endswith("_SCHEMA.md")
        ]
        return sorted(files)

    resolved = []
    for name in targets:
        path = Path(name)
        if not path.is_absolute():
            path = catalog_dir / path.name
        if not path.exists():
            raise FileNotFoundError(f"Catalog not found: {name}")
        resolved.append(path)
    return resolved


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert KPI catalogs to the new schema.")
    parser.add_argument(
        "--catalog",
        action="append",
        help="Specific KPI catalog file to convert (e.g., KPI_Catalog.md)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Convert every KPI catalog under _includes/kpi_catalog",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview output without writing files")
    args = parser.parse_args()

    if not args.all and not args.catalog:
        parser.error("Specify --all or at least one --catalog")

    targets = resolve_catalogs(args.catalog or [], args.all)
    for catalog_path in targets:
        process_catalog(catalog_path, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

