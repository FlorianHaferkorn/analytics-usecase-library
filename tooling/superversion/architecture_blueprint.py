"""
architecture_blueprint.py — ADR-0015 / T3.

Deterministic derivation of an `ArchitectureBlueprint` (the five OneLake patterns +
ai_grounding) from ALUCA's governed truth. No LLM, no randomness: same input → same
output. Anything genuinely underspecified is emitted as an explicit HITL gap, never
guessed — mirroring the KPI-DSL `hitl` / Wirkungs-Loop `UNCOMPUTED` honesty rules.

The IR is the field-identical, cross-repo-mirrored contract validated by
`tooling/generator/schemas/architecture_blueprint.schema.json` (see the shared spec
`docs/architecture/research/architecture-blueprint-ir-spec.md`).

Public API:
  - derive_blueprint(inputs) -> {"blueprint": <dict>, "hitl": [str, ...]}
  - assemble_inputs_from_repo(repo_root) -> inputs dict (best-effort, marks HITL)
  - validate_blueprint(blueprint) -> None  (raises on schema violation; soft-skip w/o jsonschema)
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "0.1.0"

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCHEMA_FILE = _REPO_ROOT / "tooling" / "generator" / "schemas" / "architecture_blueprint.schema.json"

# --- P1: deterministic shortcut-vs-mirror heuristic --------------------------------
# Databases → mirror (reliable isolated copy); lakes/object stores → shortcut (zero-copy).
_DB_HINTS = ("sql", "postgres", "mysql", "oracle", "dataverse", "d365", "dynamics", "erp", "database", "db")
_LAKE_HINTS = ("adls", "gen2", "s3", "gcs", "onelake", "lake", "blob", "parquet", "delta")


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(s).strip().lower()).strip("-")


def _access_mode(source_system: str | None) -> str:
    """Deterministic default: mirror for databases, shortcut otherwise (§ lakehouse 6.3.1)."""
    text = (source_system or "").lower()
    if any(h in text for h in _LAKE_HINTS):
        return "shortcut"
    if any(h in text for h in _DB_HINTS):
        return "mirror"
    return "shortcut"  # documented safe default (virtualize, don't duplicate)


def derive_blueprint(inputs: dict[str, Any]) -> dict[str, Any]:
    """Map governed inputs → a schema-valid ArchitectureBlueprint + a HITL-gap list.

    inputs = {
      "stack": "fabric",                 # optional, default "fabric"
      "blueprint_ref": 1|None,           # optional (Meridian only)
      "silver_contract_ref": "...",      # optional; default HITL
      "domains": [ {
          "name": "Commercial",
          "data_contract_ref": "...",    # optional
          "gold_products": [ {"name": "dim_x", "kind": "dimension", "grain": "..."} ],
          "sources": [ {"source": "...", "source_system": "...",
                        "access_mode": "shortcut|mirror|copy"?, "sensitivity": "..."?} ],
          "endorsement": "none|promoted|certified"?,   # optional, default promoted
          "intended_audience": "internal|partner|public"?,  # optional, default internal
      } ],
    }
    """
    hitl: list[str] = []
    stack = inputs.get("stack", "fabric")
    domains_in = list(inputs.get("domains", []))
    if not domains_in:
        hitl.append("no domains supplied — mesh/gold cannot be derived")

    # --- P1 ingestion (deterministic, sorted by source for stable output) ----------
    ingestion: list[dict[str, Any]] = []
    for dom in domains_in:
        for src in dom.get("sources", []):
            entry: dict[str, Any] = {
                "source": src["source"],
                "access_mode": src.get("access_mode") or _access_mode(src.get("source_system")),
                "rationale": src.get("rationale")
                or f"default access mode for {src.get('source_system') or 'unknown source'}",
            }
            if src.get("source_system"):
                entry["source_system"] = src["source_system"]
            if src.get("sensitivity"):
                entry["sensitivity"] = src["sensitivity"]
            ingestion.append(entry)
    ingestion.sort(key=lambda e: e["source"])

    # --- P2 medallion (global; gold = union of all domains' products) --------------
    gold_products: list[dict[str, Any]] = []
    for dom in domains_in:
        prods = dom.get("gold_products")
        if not prods:
            hitl.append(f"gold.data_products underspecified for domain '{dom.get('name')}'")
            continue
        for p in prods:
            gp: dict[str, Any] = {"name": p["name"], "kind": p["kind"]}
            if p.get("grain"):
                gp["grain"] = p["grain"]
            gold_products.append(gp)
    gold_products.sort(key=lambda p: p["name"])

    silver_ref = inputs.get("silver_contract_ref")
    if not silver_ref:
        silver_ref = "HITL: silver data_contract_ref not supplied"
        hitl.append("medallion.silver.data_contract_ref not supplied")

    medallion: dict[str, Any] = {
        "bronze": {  # silver-first default: bronze outsourced but specified (data_layers §2.1)
            "enabled": False,
            "outsourced": True,
            "immutable": True,
            "append_only": True,
        },
        "silver": {"data_contract_ref": silver_ref},
        "gold": {"data_products": gold_products},
        "no_layer_skip": True,
    }

    # --- P3 mesh (domain → workspaces + publishing) --------------------------------
    domains_out: list[dict[str, Any]] = []
    for dom in sorted(domains_in, key=lambda d: d.get("name", "")):
        name = dom["name"]
        slug = _slug(name)
        product_names = sorted(p["name"] for p in dom.get("gold_products", []))
        publishing: dict[str, Any] = {
            "endorsement": dom.get("endorsement", "promoted"),
            "intended_audience": dom.get("intended_audience", "internal"),
        }
        domains_out.append(
            {
                "name": name,
                "workspaces": [
                    {"name": f"ws-{slug}-gold", "role": "gold"},
                    {"name": f"ws-{slug}-reporting", "role": "reporting"},
                ],
                "data_products": product_names,
                "publishing": publishing,
            }
        )

    # --- AI-era grounding (constant surface; retrieval builtin-first) --------------
    ai_grounding: dict[str, Any] = {
        "grounding_surface": ["gold", "silver"],  # never bronze (ai_readiness §3.6)
        "retrieval": [
            {"domain": dom["name"], "strategy": "builtin", "auth_required": True}
            for dom in sorted(domains_in, key=lambda d: d.get("name", ""))
        ],
        "emits": ["mcp_grounding.json"],
    }

    blueprint: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "platform": {
            "stack": stack,
            "ownership_boundaries": [
                {"workload_class": wc, "owner_platform": stack}
                for wc in ("ingestion", "transformation", "serving")
            ],
        },
        "ingestion": ingestion,
        "medallion": medallion,
        "mesh": {"domains": domains_out},
        "sharing": [],
        "ai_grounding": ai_grounding,
    }
    if inputs.get("blueprint_ref") is not None:
        blueprint["platform"]["blueprint_ref"] = inputs["blueprint_ref"]

    return {"blueprint": blueprint, "hitl": sorted(set(hitl))}


def assemble_inputs_from_repo(repo_root: Path | None = None) -> dict[str, Any]:
    """Best-effort assembly of derivation inputs from ALUCA's data contracts.

    Discovers domains from core/data_contracts/domains/*.yaml (deterministic, sorted).
    Gold products / sources are left for the caller to enrich; missing pieces become
    HITL gaps in derive_blueprint. Kept intentionally honest — no fabricated inventory.
    """
    root = Path(repo_root) if repo_root else _REPO_ROOT
    contracts_dir = root / "core" / "data_contracts" / "domains"
    domains: list[dict[str, Any]] = []
    if contracts_dir.is_dir():
        for f in sorted(contracts_dir.glob("*.yaml")):
            domains.append(
                {
                    "name": f.stem.replace("_", " ").title().replace(" ", ""),
                    "data_contract_ref": str(f.relative_to(root)),
                }
            )
    silver_ref = (
        str((contracts_dir).relative_to(root)) if contracts_dir.is_dir() else None
    )
    return {"stack": "fabric", "silver_contract_ref": silver_ref, "domains": domains}


def validate_blueprint(blueprint: dict[str, Any]) -> None:
    """Validate against the IR JSON Schema. Soft-skip if jsonschema is unavailable."""
    try:
        from jsonschema import Draft202012Validator
    except Exception:  # pragma: no cover - optional dependency
        return
    schema = json.loads(_SCHEMA_FILE.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(blueprint)
