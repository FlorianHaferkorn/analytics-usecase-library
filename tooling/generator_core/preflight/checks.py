"""
Preflight check functions.

Each check is a plain function that takes a ``PreflightContext`` and appends
to ``ctx.errors`` (blocking) or ``ctx.warnings`` (non-blocking).

Adding a new check
------------------
1. Write a function ``check_<name>(ctx: PreflightContext) -> None``
2. Register it in ALL_CHECKS at the bottom of this file.
3. Optionally add it to a named subset (QUICK_CHECKS, FULL_CHECKS).

Check contract
--------------
* NEVER raise — append to ctx.errors or ctx.warnings only.
* Keep each check focused on one concern.
* Include a ``check_id`` in every message so the classifier can categorise it:
      ctx.errors.append("[MISSING_KPI] KPI 'com.foo.bar' not found in catalog")
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml


# ---------------------------------------------------------------------------
# Context object passed to every check
# ---------------------------------------------------------------------------

@dataclass
class PreflightContext:
    bracket_path: Path
    bracket: Dict[str, Any]
    kpi_catalog_root: Path
    action_codes_root: Path
    data_contracts_root: Optional[Path] = None
    dist_root: Optional[Path] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def error(self, check_id: str, msg: str) -> None:
        self.errors.append(f"[{check_id}] {msg}")

    def warn(self, check_id: str, msg: str) -> None:
        self.warnings.append(f"[{check_id}] {msg}")

    def suggest(self, msg: str) -> None:
        self.suggestions.append(msg)


# ---------------------------------------------------------------------------
# Check: bracket has required top-level fields
# ---------------------------------------------------------------------------

def check_bracket_required_fields(ctx: PreflightContext) -> None:
    b = ctx.bracket
    required = ["id", "primary_kpi_ids", "ux_layout_rules"]
    for field_name in required:
        if field_name not in b:
            ctx.error("BRACKET_MISSING_FIELD", f"Required field '{field_name}' missing from bracket")
    if "id" in b:
        if not re.match(r"^[A-Z]{2,5}-\d{3}$", b["id"]):
            ctx.warn(
                "BRACKET_ID_FORMAT",
                f"Bracket id '{b['id']}' does not match expected pattern COM-001",
            )


# ---------------------------------------------------------------------------
# Check: all primary_kpi_ids exist in KPI catalog
# ---------------------------------------------------------------------------

def check_kpi_refs_exist(ctx: PreflightContext) -> None:
    b = ctx.bracket
    orch = b.get("orchestration") or {}
    kpi_ids: List[str] = []
    kpi_ids += b.get("primary_kpi_ids", [])
    # Laut Schema stehen Nordstern und Hebel unter `orchestration`; ein
    # `influencing_kpi_ids` auf oberster Ebene verbietet es (additionalProperties).
    # Bis zum 29.09.2026 wurde nur die oberste Ebene gelesen -- die Hebel-KPIs
    # echter Brackets wurden nie gegen den Katalog geprueft.
    if orch.get("strategic_kpi_id"):
        kpi_ids.append(orch["strategic_kpi_id"])
    kpi_ids += orch.get("influencing_kpi_ids", [])
    kpi_ids += b.get("influencing_kpi_ids", [])  # Altform, falls ohne Schema erzeugt
    kpi_ids = list(dict.fromkeys(kpi_ids))

    for kpi_id in kpi_ids:
        filename = f"{kpi_id}.yaml"
        matches = list(ctx.kpi_catalog_root.rglob(filename))
        if not matches:
            ctx.error(
                "MISSING_KPI",
                f"KPI '{kpi_id}' referenced in bracket but not found in KPI catalog ({ctx.kpi_catalog_root})",
            )
            ctx.suggest(
                f"Add '{kpi_id}.yaml' to core/kpi_catalog/ or remove it from bracket primary_kpi_ids"
            )


# ---------------------------------------------------------------------------
# Check: action code IDs exist
# ---------------------------------------------------------------------------

def check_action_code_refs_exist(ctx: PreflightContext) -> None:
    ac_ids: List[str] = (
        ctx.bracket.get("orchestration", {}).get("action_code_ids", [])
    )
    for ac_id in ac_ids:
        found = any(
            f
            for f in ctx.action_codes_root.rglob(f"{ac_id}.yaml")
            if "decision_spines" not in str(f)
        )
        if not found:
            ctx.error(
                "MISSING_ACTION_CODE",
                f"Action code '{ac_id}' not found under {ctx.action_codes_root}",
            )
            ctx.suggest(
                f"Create 'core/action_codes/<domain>/{ac_id}.yaml' or remove it from orchestration.action_code_ids"
            )


# ---------------------------------------------------------------------------
# Check: no duplicate measure names across domain (if dist_root provided)
# ---------------------------------------------------------------------------

def check_no_duplicate_measures(ctx: PreflightContext) -> None:
    if not ctx.dist_root:
        return
    b = ctx.bracket
    domain = _infer_domain(b.get("id", ""))
    model_dir = ctx.dist_root / f"{domain}.SemanticModel" / "definition" / "tables"
    if not model_dir.is_dir():
        return
    existing_names: Set[str] = set()
    for tmdl in model_dir.glob("*.tmdl"):
        content = tmdl.read_text(encoding="utf-8", errors="ignore")
        for match in re.finditer(r"^\s+measure '([^']+)'", content, re.MULTILINE):
            existing_names.add(match.group(1))

    # Check if any new KPIs would collide with existing measure names
    for kpi_id in b.get("primary_kpi_ids", []):
        kpi_file = next(ctx.kpi_catalog_root.rglob(f"{kpi_id}.yaml"), None)
        if not kpi_file:
            continue
        with open(kpi_file, encoding="utf-8") as fh:
            kpi = yaml.safe_load(fh) or {}
        name = kpi.get("name", "")
        if name and name in existing_names:
            ctx.warn(
                "DUPLICATE_MEASURE",
                f"Measure name '{name}' (KPI '{kpi_id}') already exists in {model_dir.parent.parent.name}",
            )


# ---------------------------------------------------------------------------
# Check: evidence columns exist in data contract (if data_contracts_root given)
# ---------------------------------------------------------------------------

def check_evidence_columns_in_contract(ctx: PreflightContext) -> None:
    if not ctx.data_contracts_root:
        return
    eg = ctx.bracket.get("evidence_grain", {})
    if not eg:
        return
    cols: List[str] = eg.get("columns", [])
    if not cols:
        return

    domain = _infer_domain(ctx.bracket.get("id", ""))
    contract_file = ctx.data_contracts_root / "domains" / f"{domain.lower()}.yaml"
    if not contract_file.is_file():
        ctx.warn(
            "DATA_CONTRACT_MISSING",
            f"Data contract for domain '{domain}' not found at {contract_file}",
        )
        return

    with open(contract_file, encoding="utf-8") as fh:
        contract = yaml.safe_load(fh) or {}

    all_contract_cols: Set[str] = set()
    for entity in contract.get("entities", []):
        for col in entity.get("columns", []):
            col_name = col.get("name", "") if isinstance(col, dict) else col
            all_contract_cols.add(col_name)

    for col in cols:
        short_col = col.split(".")[-1] if "." in col else col
        if short_col not in all_contract_cols and col not in all_contract_cols:
            ctx.warn(
                "EVIDENCE_COL_NOT_IN_CONTRACT",
                f"Evidence column '{col}' not found in data contract for domain '{domain}'",
            )


# ---------------------------------------------------------------------------
# Check: visual slot coverage (at least one 30s component declared)
# ---------------------------------------------------------------------------

def check_visual_slot_coverage(ctx: PreflightContext) -> None:
    ux = ctx.bracket.get("ux_layout_rules", {})
    page1 = ux.get("page_1_summary", {})
    comp_30s = page1.get("component_30s", [])
    if not comp_30s:
        ctx.warn(
            "NO_30S_COMPONENTS",
            "ux_layout_rules.page_1_summary.component_30s is empty — Overview page will have no driver visuals",
        )
    if not ctx.bracket.get("primary_kpi_ids"):
        ctx.error(
            "NO_PRIMARY_KPIS",
            "primary_kpi_ids is empty — KPI_Cards will be blank",
        )


# ---------------------------------------------------------------------------
# Check: target domain model exists (if dist_root provided)
# ---------------------------------------------------------------------------

def check_domain_model_exists(ctx: PreflightContext) -> None:
    if not ctx.dist_root:
        return
    domain = _infer_domain(ctx.bracket.get("id", ""))
    model_dir = ctx.dist_root / f"{domain}.SemanticModel"
    if not model_dir.is_dir():
        ctx.warn(
            "DOMAIN_MODEL_MISSING",
            f"Semantic model directory '{model_dir}' does not exist yet — will be created during generation",
        )
        ctx.suggest(
            f"Run orchestrate_full_model.ps1 -Domain {domain} first to create the base model"
        )


# ---------------------------------------------------------------------------
# Check: bracket YAML is valid JSON-schema (usecase_bracket.schema.json)
# ---------------------------------------------------------------------------

def check_bracket_schema_compliance(ctx: PreflightContext) -> None:
    # Schema-Autoritaet ist `tooling/generator/schemas/` (CLAUDE.md, Golden Thread).
    # Bis zum 29.09.2026 stand hier `tooling/ai/schemas/` -- einen Pfad, den es nicht
    # gibt: die Pruefung lief nie, gemeldet wurde nur eine Warnung. Gemessen am selben
    # Tag: alle 21 UseCase_Bracket.yaml bestehen das Schema.
    schema_path = (
        Path(__file__).parents[3]
        / "tooling" / "generator" / "schemas" / "usecase_bracket.schema.json"
    )
    if not schema_path.is_file():
        # Ein Pruefer, der ohne seine Regeln gruen meldet, ist schlimmer als keiner:
        # fehlt das Schema, ist das ein Fehler, keine Warnung, die niemand liest.
        ctx.error(
            "BRACKET_SCHEMA_MISSING",
            f"Bracket-Schema fehlt ({schema_path}) — Bracket NICHT geprueft.",
        )
        return
    # `jsonschema` steht in requirements.txt und pyproject.toml. Der Rueckfall
    # schuetzte vor nichts und schaltete nur die Pruefung ab, wenn jemand die
    # Installation vermurkst hat.
    import jsonschema
    try:
        with open(schema_path, encoding="utf-8") as fh:
            schema = json.load(fh)
        jsonschema.validate(instance=ctx.bracket, schema=schema)
    except jsonschema.ValidationError as exc:
        ctx.error(
            "BRACKET_SCHEMA_VIOLATION",
            f"Bracket does not conform to usecase_bracket.schema.json: {exc.message}",
        )
    except Exception:
        pass  # Schema validation errors are advisory — don't block on unexpected errors


# ---------------------------------------------------------------------------
# Check: action panel requires action_code_ids to be set
# ---------------------------------------------------------------------------

def check_action_panel_consistency(ctx: PreflightContext) -> None:
    ux = ctx.bracket.get("ux_layout_rules", {})
    page2 = ux.get("page_2_execution", {})
    comp_300s = page2.get("component_300s", {}) if isinstance(page2, dict) else {}
    ap_enabled = False
    if isinstance(comp_300s, dict):
        ap_enabled = comp_300s.get("action_panel", False)
    elif isinstance(comp_300s, list):
        ap_enabled = any(
            (c.get("action_panel") if isinstance(c, dict) else False)
            for c in comp_300s
        )
    if not ap_enabled:
        return
    ac_ids = ctx.bracket.get("orchestration", {}).get("action_code_ids", [])
    if not ac_ids:
        ctx.error(
            "ACTION_PANEL_NO_CODES",
            "action_panel is enabled but orchestration.action_code_ids is empty — ActionPanel will be blank",
        )
        ctx.suggest(
            "Add action code IDs to orchestration.action_code_ids or set action_panel: false"
        )


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _infer_domain(use_case_id: str) -> str:
    prefix = use_case_id.split("-")[0].upper() if use_case_id else ""
    _map = {
        "COM": "Commercial",
        "FIN": "Finance",
        "OPS": "Operations",
        "SCM": "SupplyChain",
        "XD": "Experience",
    }
    return _map.get(prefix, prefix.capitalize() or "Unknown")


# ---------------------------------------------------------------------------
# Check registry
# ---------------------------------------------------------------------------

#: Fast checks (run always)
QUICK_CHECKS = [
    check_bracket_required_fields,
    check_kpi_refs_exist,
    check_visual_slot_coverage,
    check_action_panel_consistency,
]

#: Full checks (run when dist_root and data_contracts_root are available)
FULL_CHECKS = QUICK_CHECKS + [
    check_action_code_refs_exist,
    check_no_duplicate_measures,
    check_evidence_columns_in_contract,
    check_domain_model_exists,
    check_bracket_schema_compliance,
]

ALL_CHECKS = FULL_CHECKS
