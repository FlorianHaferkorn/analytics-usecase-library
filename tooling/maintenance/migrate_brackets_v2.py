"""Migrate UseCase_Bracket.yaml files to Lean 2.0 structure.

Transforms:
  - name -> title
  - ontology_bracket -> orchestration
  - Enriches value_driver_model (impact_direction, primary_driver, impact_logic)
  - Replaces loose ux_layout_rules with structured layout
  - documentation keeps only business_factsheet
  - Rewrites governance roles to role IDs from org_roles.yaml
  - Removes governance.status and governance.last_review
"""

import sys, os, glob, re
from pathlib import Path

# Ensure we can import yaml
try:
    import yaml
except ImportError:
    print("PyYAML required. Install with: pip install pyyaml")
    sys.exit(1)


def load_org_roles(org_path: str) -> dict:
    """Load org_roles.yaml and build alias->id mapping."""
    with open(org_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    mapping = {}
    for role in data.get("roles", []):
        rid = role["id"]
        mapping[rid] = rid
        mapping[role["title"].lower().strip()] = rid
        for alias in role.get("aliases", []):
            mapping[alias.lower().strip()] = rid
    return mapping


def resolve_role(name: str, mapping: dict) -> str:
    """Resolve a display name to a role ID."""
    key = name.lower().strip()
    if key in mapping:
        return mapping[key]
    # Try partial match on first segment (before /)
    first = key.split("/")[0].strip()
    if first in mapping:
        return mapping[first]
    # Fallback: snake_case the name
    fallback = re.sub(r"[^a-z0-9]+", "_", key).strip("_")
    print(f"  WARN: No role match for '{name}', using fallback '{fallback}'")
    return fallback


def determine_impact_direction(strategic_kpi_id: str) -> str:
    """Heuristic: if KPI measures days/cost/defects -> minimize, else maximize."""
    minimize_patterns = [".days", ".hours", ".minutes", "cost.", "defect",
                         "scrap", "rework", "copq", "downtime", "shrinkage",
                         "overtime", "risk", "attrition", "complaint",
                         "cannibalization", "penalty", "expedite", "stockout",
                         "backlog", "escalation", "mape", "bias", "obsolete",
                         "unit.amount"]
    kpi_lower = strategic_kpi_id.lower()
    for p in minimize_patterns:
        if p in kpi_lower:
            return "minimize"
    return "maximize"


def determine_primary_driver(influencing_kpi_ids: list, strategic_kpi_id: str) -> str:
    """Pick the first influencing KPI as the primary driver."""
    if influencing_kpi_ids:
        return influencing_kpi_ids[0]
    return strategic_kpi_id


def build_impact_logic(strategic_kpi_id: str, primary_driver: str,
                       impact_direction: str) -> str:
    """Generate a default impact logic string."""
    verb = "maximizing" if impact_direction == "maximize" else "minimizing"
    return (f"Improving {primary_driver} is the primary lever for "
            f"{verb} {strategic_kpi_id}.")


def build_formula(strategic_kpi_id: str, influencing_kpi_ids: list) -> str:
    """Build a clean math-style formula."""
    if not influencing_kpi_ids:
        return f"{strategic_kpi_id} = f()"
    args = ", ".join(influencing_kpi_ids)
    return f"{strategic_kpi_id} = f({args})"


def migrate_bracket(data: dict, role_mapping: dict) -> dict:
    """Transform a single bracket dict to v2.0 structure."""
    uc_id = data["id"]
    domain = data.get("domain", "Unknown")

    # --- Title ---
    title = data.pop("name", data.get("title", uc_id))

    # --- Governance ---
    gov = data.get("governance", {})
    owner_role = resolve_role(gov.get("owner_role", "unknown"), role_mapping)
    steward_role = resolve_role(gov.get("steward_role", "unknown"), role_mapping)

    # --- Orchestration (was ontology_bracket) ---
    ob = data.get("ontology_bracket", data.get("orchestration", {}))
    strategic_kpi_id = ob.get("strategic_kpi_id", "")
    influencing_kpi_ids = ob.get("influencing_kpi_ids", [])
    action_code_ids = ob.get("action_code_ids", [])

    # --- Value Driver Model ---
    impact_direction = determine_impact_direction(strategic_kpi_id)
    primary_driver = determine_primary_driver(influencing_kpi_ids, strategic_kpi_id)
    impact_logic = build_impact_logic(strategic_kpi_id, primary_driver, impact_direction)
    formula = build_formula(strategic_kpi_id, influencing_kpi_ids)

    # --- UX Layout Rules ---
    # Determine domain label for titles
    domain_label = domain
    
    # Preserve existing evidence_grain or set TODO sentinel if missing/forbidden
    existing_grain = None
    old_ux = data.get("ux_layout_rules", {})
    if isinstance(old_ux, dict):
        old_p2 = old_ux.get("page_2_execution", {})
        if isinstance(old_p2, dict):
            old_c300 = old_p2.get("component_300s", {})
            if isinstance(old_c300, dict):
                existing_grain = old_c300.get("evidence_grain")
    
    evidence_grain_value = existing_grain
    overrides_note = None
    if not evidence_grain_value or evidence_grain_value == "transaction_line":
        evidence_grain_value = "TODO_SET_EVIDENCE_GRAIN"
        overrides_note = (
            "evidence_grain must be set to a governed fact-table grain from "
            "core/data_contracts/domains/*.yaml. Placeholder 'transaction_line' is "
            "forbidden. Refer to internal/evidence_grain_audit_results.md for the "
            "correct grain for this use case."
        )
    
    # Pick first 2 influencing KPIs for 30s component (or all if <= 3)
    comp_30s = []
    if len(influencing_kpi_ids) >= 2:
        comp_30s.append({
            "kpi_id": influencing_kpi_ids[0],
            "visual_type": "trend_line"
        })
        remaining = influencing_kpi_ids[1:min(4, len(influencing_kpi_ids))]
        if len(remaining) == 1:
            comp_30s.append({
                "kpi_id": remaining[0],
                "visual_type": "bar_chart"
            })
        else:
            comp_30s.append({
                "kpi_ids": remaining,
                "visual_type": "bar_chart"
            })
    elif len(influencing_kpi_ids) == 1:
        comp_30s.append({
            "kpi_id": influencing_kpi_ids[0],
            "visual_type": "trend_line"
        })

    ux_layout_rules = {
        "report_structure": "2-Page-Lead",
        "page_1_summary": {
            "title": f"{domain_label} Summary & Insights",
            "component_3s": {
                "kpi_id": strategic_kpi_id,
                "visual_type": "kpi_card"
            },
            "component_30s": comp_30s
        },
        "page_2_execution": {
            "title": f"{domain_label} Execution",
            "component_300s": {
                "evidence_grain": evidence_grain_value,
                "evidence_columns": ["entity", "period", strategic_kpi_id],
                "action_panel": True,
                "payload_mode": "full"
            }
        }
    }
    
    # --- Overrides (conditional) ---
    overrides_dict = {}
    if overrides_note:
        overrides_dict["evidence_grain_note"] = overrides_note

    # --- Build output ---
    result = {
        "schema_version": "2.0",
        "id": uc_id,
        "title": title,
        "domain": domain,
        "governance": {
            "owner_role": owner_role,
            "steward_role": steward_role
        },
        "orchestration": {
            "strategic_kpi_id": strategic_kpi_id,
            "influencing_kpi_ids": influencing_kpi_ids,
            "action_code_ids": action_code_ids
        },
        "value_driver_model": {
            "formula": formula,
            "impact_direction": impact_direction,
            "primary_driver": primary_driver,
            "impact_logic": impact_logic
        },
        "ux_layout_rules": ux_layout_rules,
        "documentation": {
            "business_factsheet": "./Business_Factsheet.md"
        }
    }
    
    # Add overrides section only if non-empty
    if overrides_dict:
        result["overrides"] = overrides_dict

    return result


class CleanDumper(yaml.SafeDumper):
    """Custom YAML dumper for clean output."""
    pass


def _str_representer(dumper, data):
    """Represent strings without unnecessary quoting."""
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    # Quote strings that look like they need quoting
    if data in ("true", "false", "null", "yes", "no", "on", "off", "True", "False"):
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="'")
    if data and data[0] in ("{", "[", "*", "&", "!", "|", ">", "'", '"', "%", "@", "`"):
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="'")
    # Check if it looks like a number
    try:
        float(data)
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="'")
    except (ValueError, TypeError):
        pass
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


def _bool_representer(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:bool", "true" if data else "false")


CleanDumper.add_representer(str, _str_representer)
CleanDumper.add_representer(bool, _bool_representer)


def main():
    repo_root = Path(__file__).resolve().parents[2]
    org_path = repo_root / "core" / "organization" / "org_roles.yaml"
    brackets_glob = str(repo_root / "core" / "usecases" / "core" / "*" / "UseCase_Bracket.yaml")

    if not org_path.exists():
        print(f"ERROR: Org-Registry not found at {org_path}")
        sys.exit(1)

    role_mapping = load_org_roles(str(org_path))
    bracket_files = sorted(glob.glob(brackets_glob))

    if not bracket_files:
        print("No bracket files found.")
        sys.exit(1)

    print(f"Found {len(bracket_files)} bracket files to migrate.\n")

    todo_grains = []
    for bf in bracket_files:
        print(f"Migrating: {os.path.relpath(bf, repo_root)}")
        with open(bf, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        migrated = migrate_bracket(data, role_mapping)
        
        # Track if TODO sentinel was set
        ux_rules = migrated.get("ux_layout_rules", {})
        if isinstance(ux_rules, dict):
            p2 = ux_rules.get("page_2_execution", {})
            if isinstance(p2, dict):
                c300 = p2.get("component_300s", {})
                if isinstance(c300, dict):
                    eg = c300.get("evidence_grain")
                    if eg == "TODO_SET_EVIDENCE_GRAIN":
                        todo_grains.append(migrated['id'])

        with open(bf, "w", encoding="utf-8") as f:
            yaml.dump(migrated, f, Dumper=CleanDumper, default_flow_style=False,
                      allow_unicode=True, sort_keys=False, width=120)

        print(f"  OK: {migrated['id']} - {migrated['title']}")

    print(f"\nDone. Migrated {len(bracket_files)} brackets.")
    
    if todo_grains:
        print(f"\nWARNING: {len(todo_grains)} bracket(s) have evidence_grain set to 'TODO_SET_EVIDENCE_GRAIN':")
        for uc in todo_grains:
            print(f"  - {uc}")
        print("\nRefer to internal/evidence_grain_audit_results.md for the correct governed grain.")
        print("Schema and registry builder will fail until a valid grain is set.")


if __name__ == "__main__":
    main()
