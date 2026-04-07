"""Migrate Action Code YAMLs from v1.1 to v2.0 (lean schema).

Changes applied:
  - schema_version -> "2.0"
  - Remove: lifecycle, category, tags, strategic_alignment
  - Promote operational_execution.primary_owner_role -> top-level owner_role
  - Add steward_role (derived from owner_domain)
  - KPI lists (trigger_kpis, guardrail_kpis, outcome_kpis) -> IDs only
  - Remove primary_owner_role from operational_execution

Usage:
  py -3 tooling/maintenance/migrate_action_codes_v2.py --dry-run
  py -3 tooling/maintenance/migrate_action_codes_v2.py --apply
"""

import argparse
import pathlib
import sys

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
ACTION_CODES_DIR = REPO_ROOT / "core" / "action_codes"
DECISION_SPINES_DIR = ACTION_CODES_DIR / "decision_spines"

# Default steward_role per domain (derived from existing patterns)
DOMAIN_STEWARD_MAP = {
    "Commercial": "Commercial BI Lead",
    "Finance": "Finance BI Lead",
    "Operations": "Operations BI Lead",
    "SupplyChain": "Supply Chain BI Lead",
    "Enterprise": "Enterprise BI Lead",
    "People": "People Analytics Lead",
    "Service": "Service Analytics Lead",
}

REMOVED_KEYS = {"lifecycle", "category", "tags", "strategic_alignment"}


def infer_steward(owner_domain: str) -> str:
    """Derive steward_role from owner_domain string."""
    for key, role in DOMAIN_STEWARD_MAP.items():
        if key.lower() in owner_domain.lower():
            return role
    # Fallback: generic
    return f"{owner_domain} BI Lead"


def simplify_kpi_list(items):
    """Convert list of objects with kpi_id to list of ID strings."""
    if not items:
        return []
    result = []
    for item in items:
        if isinstance(item, dict) and "kpi_id" in item:
            result.append(item["kpi_id"])
        elif isinstance(item, str):
            result.append(item)
        # else skip malformed entries
    return result


def migrate(data: dict) -> dict:
    """Transform a v1.1 action code dict into v2.0."""
    # Already migrated?
    if data.get("schema_version") == "2.0":
        return data

    data["schema_version"] = "2.0"

    # Promote owner_role from operational_execution
    op_exec = data.get("operational_execution", {})
    owner_role = op_exec.pop("primary_owner_role", None)
    if owner_role:
        data["owner_role"] = owner_role
    elif "owner_role" not in data:
        data["owner_role"] = "TBD"

    # Derive steward_role
    if "steward_role" not in data:
        data["steward_role"] = infer_steward(data.get("owner_domain", ""))

    # Remove deprecated blocks
    for key in REMOVED_KEYS:
        data.pop(key, None)

    # Simplify KPI lists to IDs only
    kpis = data.get("kpis", {})
    if kpis:
        for field in ("trigger_kpis", "guardrail_kpis", "outcome_kpis"):
            if field in kpis:
                kpis[field] = simplify_kpi_list(kpis[field])

    return data


class OrderedDumper(yaml.SafeDumper):
    """Dump YAML preserving key insertion order and clean formatting."""
    pass


def _str_representer(dumper, data):
    """Only quote strings that would be misinterpreted by YAML parsers."""
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    # Must quote: empty, booleans, numbers, special-char starts, contains mapping chars
    needs_quote = False
    if not data:
        needs_quote = True
    elif data.lower() in ("true", "false", "null", "yes", "no", "on", "off", "~"):
        needs_quote = True
    else:
        try:
            float(data)
            needs_quote = True
        except (ValueError, TypeError):
            pass
    if needs_quote:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')
    # Let PyYAML decide (plain style for most strings)
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


OrderedDumper.add_representer(str, _str_representer)


# Key ordering for top-level fields
TOP_LEVEL_ORDER = [
    "schema_version", "inherits_decision_spine",
    "id", "name", "owner_domain", "impact_dimension",
    "status", "owner_role", "steward_role",
    "use_case_links", "kpis", "scope", "trigger",
    "impact_valuation", "impact", "operational_execution",
    "data_requirements", "automation", "tracking",
    "governance", "execution_bridge", "quality_rules",
]


def ordered_dump(data: dict) -> str:
    """Dump YAML with controlled top-level key order."""
    ordered = {}
    for key in TOP_LEVEL_ORDER:
        if key in data:
            ordered[key] = data[key]
    # Append any remaining keys
    for key in data:
        if key not in ordered:
            ordered[key] = data[key]
    return yaml.dump(ordered, Dumper=OrderedDumper,
                     default_flow_style=False, allow_unicode=True,
                     sort_keys=False, width=120)


def main():
    parser = argparse.ArgumentParser(description="Migrate Action Codes to v2.0")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Report changes without writing")
    group.add_argument("--apply", action="store_true", help="Write migrated files")
    args = parser.parse_args()

    yaml_files = sorted(
        f for f in ACTION_CODES_DIR.rglob("*.yaml")
        if DECISION_SPINES_DIR not in f.parents and f.parent != DECISION_SPINES_DIR
    )

    print(f"Found {len(yaml_files)} action code YAML files (excluding decision_spines).")

    migrated = 0
    skipped = 0
    for path in yaml_files:
        rel = path.relative_to(REPO_ROOT)
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or not isinstance(data, dict):
            print(f"  SKIP (not a dict): {rel}")
            skipped += 1
            continue

        if data.get("schema_version") == "2.0":
            print(f"  SKIP (already v2.0): {rel}")
            skipped += 1
            continue

        new_data = migrate(data)

        if args.dry_run:
            print(f"  WOULD MIGRATE: {rel}")
            print(f"    owner_role: {new_data.get('owner_role')}")
            print(f"    steward_role: {new_data.get('steward_role')}")
            kpis = new_data.get("kpis", {})
            print(f"    trigger_kpis: {kpis.get('trigger_kpis', [])}")
        else:
            output = ordered_dump(new_data)
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(output)
            print(f"  MIGRATED: {rel}")

        migrated += 1

    print(f"\nDone. Migrated: {migrated}, Skipped: {skipped}")
    if args.dry_run:
        print("(dry-run mode — no files were changed)")


if __name__ == "__main__":
    main()
