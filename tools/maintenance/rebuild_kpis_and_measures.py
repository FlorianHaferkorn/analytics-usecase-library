#!/usr/bin/env python3
"""Rebuild KPI catalogs to the new schema and generate domain measure dictionaries."""

from __future__ import annotations

import argparse
import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_DIR = REPO_ROOT / "_includes" / "kpi_catalog"
SCHEMA_REF = "`/_includes/kpi_catalog/KPI_Catalog_SCHEMA.md`"
MEASURE_SCHEMA_REF = "`/_includes/kpi_catalog/Domain_Measure_Dictionary_Schema.md`"
CATALOG_PATTERN = "KPI_Catalog_*.md"

PLACEHOLDER_ID = "__MISSING__"


@dataclass
class ParsedEntry:
    data: Dict
    cluster: str
    source_path: Path


def run_git_show(rel_path: str) -> Optional[str]:
    result = subprocess.run(
        ["git", "show", f"HEAD:{rel_path}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return result.stdout
    return None


def load_source_text(path: Path) -> str:
    try:
        rel = path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        rel = path.as_posix()
    from_git = run_git_show(rel)
    if from_git is not None:
        return from_git
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            try:
                return path.read_text(encoding="utf-16")
            except UnicodeDecodeError:
                return path.read_text(encoding="cp1252")


def extract_yaml_blocks(text: str) -> List[str]:
    pattern = re.compile(r"```(?:yaml|yml)\s*(.*?)\s*```", re.S | re.IGNORECASE)
    return pattern.findall(text)


def split_entries(block: str) -> List[str]:
    entries: List[str] = []
    lines = block.splitlines()
    current: List[str] = []
    for raw in lines:
        line = raw.rstrip()
        if not line.strip() and not current:
            continue
        if line.startswith("- kpi_id:"):
            if current:
                entries.append("\n".join(current))
                current = []
            current.append(line)
        elif line.startswith("kpi_key:"):
            if current:
                entries.append("\n".join(current))
                current = []
            current.append(f"- kpi_id: \"{PLACEHOLDER_ID}\"")
            current.append(line)
        else:
            if current:
                current.append(line)
    if current:
        entries.append("\n".join(current))
    return entries


def parse_catalog(path: Path) -> List[Dict]:
    text = load_source_text(path)
    blocks = extract_yaml_blocks(text)
    parsed: List[Dict] = []
    for block in blocks:
        for entry_text in split_entries(block):
            try:
                data = yaml.safe_load(entry_text)
            except yaml.YAMLError:
                continue
            if isinstance(data, list):
                data = data[0]
            if isinstance(data, dict):
                parsed.append(data)
    return parsed


def ensure_list(value) -> List:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def sanitize_text(value: Optional[str]) -> str:
    if not value:
        return ""
    text = str(value)
    char_map = {
        "\u0394": "Delta",
        "\u03b4": "delta",
    }
    text = "".join(char_map.get(ch, ch) for ch in text)
    replacements = {
        "\u20ac": "EUR",
        "\ufffd": "-",
        "CO\uFFFD": "CO2",
        "CO\u2082": "CO2",
        "CO�": "CO2",
        "Î”": "Delta",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    text = text.replace("Scopes 1-3", "Scopes 1-3")
    return text.encode("ascii", "ignore").decode("ascii").strip()


def normalize_date(value: Optional[str]) -> str:
    if not value:
        return date.today().strftime("%d.%m.%Y")
    value = value.strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y.%m.%d"):
        try:
            return datetime.strptime(value, fmt).strftime("%d.%m.%Y")
        except ValueError:
            continue
    return value


def slugify(value: str) -> str:
    base = sanitize_text(value).lower()
    base = base.replace("%", "pct").replace("?", "")
    slug = re.sub(r"[^a-z0-9]+", "_", base)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "kpi"


def infer_prefix(
    entry: Dict,
    cluster: str,
    domain_tag_prefix: Dict[str, str],
    impact_prefix: Dict[str, str],
    cluster_prefix: Dict[str, str],
) -> str:
    tags = ensure_list(entry.get("domain_tag"))
    for tag in tags:
        prefix = domain_tag_prefix.get(tag)
        if prefix:
            return prefix
    impact = entry.get("impact_dimension")
    if impact and impact_prefix.get(impact):
        return impact_prefix[impact]
    if cluster_prefix.get(cluster):
        return cluster_prefix[cluster]
    fallback = {
        "Growth": "sales",
        "Profitability": "margin",
        "Liquidity": "fin",
        "Efficiency": "ops",
        "CustomerValue": "crm",
        "ESG": "esg",
        "Governance": "gov",
        "InnovationPeople": "people",
        "Risk": "risk",
    }
    return fallback.get(cluster, "kpi")


def aggregate_prefix_mappings(entries: List[ParsedEntry]):
    domain_tag_prefix = defaultdict(Counter)
    impact_prefix = defaultdict(Counter)
    cluster_prefix = defaultdict(Counter)
    for parsed in entries:
        kpi_id = parsed.data.get("kpi_id")
        if not kpi_id or kpi_id == PLACEHOLDER_ID:
            continue
        prefix = kpi_id.split(".")[0]
        for tag in ensure_list(parsed.data.get("domain_tag")):
            domain_tag_prefix[tag].update([prefix])
        impact = parsed.data.get("impact_dimension")
        if impact:
            impact_prefix[impact].update([prefix])
        cluster_prefix[parsed.cluster].update([prefix])
    def to_simple(mapping: Dict[str, Counter]) -> Dict[str, str]:
        return {key: counter.most_common(1)[0][0] for key, counter in mapping.items() if counter}
    return to_simple(domain_tag_prefix), to_simple(impact_prefix), to_simple(cluster_prefix)


def resolve_dep_measures(entry: Dict, id_to_measure: Dict[str, str]) -> List[str]:
    measures: List[str] = []
    dep_ids = ensure_list(entry.get("depends_on_ids") or (entry.get("technical") or {}).get("depends_on_ids"))
    dep_names = ensure_list(entry.get("depends_on") or (entry.get("technical") or {}).get("depends_on"))
    if dep_ids:
        for dep in dep_ids:
            measures.append(id_to_measure.get(dep) or dep)
    elif dep_names:
        measures.extend(dep_names)
    existing = ensure_list((entry.get("technical") or {}).get("depends_on_measures"))
    if not measures and existing:
        measures.extend(existing)
    return [m for m in measures if m]


def build_kpi_entry(entry: Dict, dep_measures: List[str]) -> Dict:
    business = entry.get("business") or {}
    technical = entry.get("technical") or {}
    governance = entry.get("governance") or {}
    metadata = entry.get("metadata_quality") or {}

    def biz_field(field: str, default: str = "") -> str:
        value = business.get(field, default)
        if isinstance(value, list):
            value = " ".join(str(v) for v in value)
        value = sanitize_text(value)
        if not value and field == "interpretation":
            return "TODO - add interpretation."
        return value

    lineage = ensure_list(technical.get("lineage"))
    lineage = [sanitize_text(item) for item in lineage if item]

    kpi = {
        "kpi_id": entry.get("kpi_id"),
        "kpi_key": sanitize_text(entry.get("kpi_key")),
        "kpi_type": entry.get("kpi_type"),
        "impact_dimension": entry.get("impact_dimension"),
        "domain_tag": ensure_list(entry.get("domain_tag")),
        "use_case_ref": ensure_list(entry.get("use_case_ref")),
        "calc_type": entry.get("calc_type"),
        "business": {
            "purpose": biz_field("purpose"),
            "definition": biz_field("definition"),
            "grain_scope": biz_field("grain_scope"),
            "unit_format": biz_field("unit_format"),
            "interpretation": biz_field("interpretation"),
        },
        "technical": {
            "dax_name": sanitize_text(technical.get("dax_name") or technical.get("daxName") or entry.get("kpi_key")),
            "depends_on_measures": dep_measures,
            "lineage": lineage,
        },
        "governance": {
            "business_owner": governance.get("business_owner", ""),
            "data_owner": governance.get("data_owner", ""),
            "steward": governance.get("steward", ""),
            "review_cycle": governance.get("review_cycle", ""),
            "validation_process": governance.get("validation_process", ""),
            "qa_rules": ensure_list(governance.get("qa_rules")),
            "version": governance.get("version", "v1.0"),
        },
        "metadata_quality": {
            "completeness_score": float(metadata.get("completeness_score", 0.8)),
            "last_review": normalize_date(metadata.get("last_review") or governance.get("last_review")),
        },
    }
    aliases = ensure_list(entry.get("aliases"))
    if aliases:
        kpi["aliases"] = aliases
    return kpi


def build_measure_entry(entry: Dict, dep_measures: List[str], cluster: str) -> Dict:
    technical = entry.get("technical") or {}
    governance = entry.get("governance") or {}
    metadata = entry.get("metadata_quality") or {}
    business = entry.get("business") or {}

    dax_name = sanitize_text(technical.get("dax_name") or technical.get("daxName") or entry.get("kpi_key"))
    dax_expression = sanitize_text(technical.get("dax_expression") or "")
    if not dax_expression:
        dax_expression = "// TODO: add expression"
    format_string = sanitize_text(technical.get("formatString") or "")
    documentation = technical.get("description") or business.get("definition") or entry.get("kpi_key")
    lineage = ensure_list(technical.get("lineage"))
    lineage = [sanitize_text(item) for item in lineage if item]

    dependencies = {}
    if dep_measures:
        dependencies["measures"] = dep_measures
    if lineage:
        dependencies["columns"] = lineage

    measure = {
        "measure_name": dax_name,
        "is_kpi_measure": True,
        "kpi_id_ref": entry.get("kpi_id"),
        "semantic_model": f"{cluster}_SemanticModel",
        "category": "KPI",
        "expression": {
            "dax": dax_expression,
            "formatString": format_string,
        },
        "documentation": {
            "description": sanitize_text(documentation),
            "notes": "",
        },
        "governance": {
            "owner": governance.get("data_owner", ""),
            "status": (entry.get("status") or "active").lower(),
            "version": governance.get("version", "v1.0"),
            "last_review": normalize_date(metadata.get("last_review") or governance.get("last_review")),
        },
    }
    display_folder = technical.get("displayFolder")
    if display_folder:
        measure["display_folder"] = display_folder
    if dependencies:
        measure["dependencies"] = dependencies
    return measure


def write_catalog(cluster: str, entries: List[Dict], target_path: Path):
    strategic = [e for e in entries if (e.get("kpi_type") or "").lower() == "strategic"]
    supporting = [e for e in entries if (e.get("kpi_type") or "").lower() != "strategic"]
    header = [
        f"# KPI Catalog - {cluster}",
        "",
        "---",
        "",
        f"Schema: see {SCHEMA_REF}",
        "",
        "## KPIs - Strategic",
        "```yaml",
        yaml.safe_dump(strategic, sort_keys=False, width=120, allow_unicode=True).strip(),
        "```",
        "",
        "## KPIs - Supporting / Diagnostic",
        "```yaml",
        yaml.safe_dump(supporting, sort_keys=False, width=120, allow_unicode=True).strip(),
        "```",
        "",
    ]
    target_path.write_text("\n".join(header), encoding="utf-8")


def write_measure_dictionary(cluster: str, measures: List[Dict], target_path: Path):
    header = [
        f"# Measure Dictionary - {cluster}",
        "",
        f"Schema: see {MEASURE_SCHEMA_REF}",
        "",
        "```yaml",
        yaml.safe_dump(measures, sort_keys=False, width=120, allow_unicode=True).strip(),
        "```",
        "",
    ]
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text("\n".join(header), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Rebuild KPI catalogs and domain measure dictionaries.")
    parser.add_argument(
        "--catalog",
        action="append",
        help="Optional specific KPI catalog files (e.g., KPI_Catalog_Efficiency.md). Defaults to all catalogs.",
    )
    args = parser.parse_args()

    catalog_files = args.catalog or [
        p.name for p in sorted(CATALOG_DIR.glob(CATALOG_PATTERN)) if not p.name.endswith("_SCHEMA.md")
    ]

    parsed_entries: List[ParsedEntry] = []
    for filename in catalog_files:
        path = CATALOG_DIR / filename
        cluster = filename.replace("KPI_Catalog_", "").replace(".md", "")
        entries = parse_catalog(path)
        for entry in entries:
            parsed_entries.append(ParsedEntry(entry, cluster, path))

    domain_tag_prefix, impact_prefix, cluster_prefix = aggregate_prefix_mappings(parsed_entries)

    existing_ids = set()
    for parsed in parsed_entries:
        entry = parsed.data
        kpi_id = entry.get("kpi_id")
        if not kpi_id or kpi_id == PLACEHOLDER_ID:
            prefix = infer_prefix(entry, parsed.cluster, domain_tag_prefix, impact_prefix, cluster_prefix)
            slug = slugify(entry.get("kpi_key", "kpi"))
            candidate = f"{prefix}.{slug}" if prefix else slug
            suffix = 1
            new_id = candidate
            while new_id in existing_ids:
                suffix += 1
                new_id = f"{candidate}_{suffix}"
            entry["kpi_id"] = new_id
            kpi_id = new_id
        existing_ids.add(kpi_id)

    id_to_measure = {}
    for parsed in parsed_entries:
        technical = parsed.data.get("technical") or {}
        measure_name = technical.get("dax_name") or technical.get("daxName") or parsed.data.get("kpi_key")
        id_to_measure[parsed.data.get("kpi_id")] = measure_name

    cluster_to_entries: Dict[str, List[Dict]] = defaultdict(list)
    cluster_to_measures: Dict[str, Dict[str, Dict]] = defaultdict(dict)

    for parsed in parsed_entries:
        dep_measures = resolve_dep_measures(parsed.data, id_to_measure)
        kpi_entry = build_kpi_entry(parsed.data, dep_measures)
        cluster_to_entries[parsed.cluster].append(kpi_entry)

        measure_entry = build_measure_entry(parsed.data, dep_measures, parsed.cluster)
        measure_name = measure_entry["measure_name"]
        cluster_measures = cluster_to_measures[parsed.cluster]
        if measure_name not in cluster_measures:
            cluster_measures[measure_name] = measure_entry

    for cluster, entries in cluster_to_entries.items():
        target = CATALOG_DIR / f"KPI_Catalog_{cluster}.md"
        write_catalog(cluster, entries, target)
        measures = list(cluster_to_measures[cluster].values())
        measure_path = (
            REPO_ROOT / "semantic_models" / cluster / f"Measure_Dictionary_{cluster}.md"
        )
        write_measure_dictionary(cluster, measures, measure_path)

    print("Rebuilt KPI catalogs and measure dictionaries for clusters:", ", ".join(sorted(cluster_to_entries.keys())))


if __name__ == "__main__":
    main()
