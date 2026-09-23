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
      "grounding_surface": ["gold","silver"]?,   # optional, default ["gold","silver"]
      "retrieval_strategy": "builtin|mcp|both"?, # optional, default "builtin"
      "ownership_overrides": {"ingestion": "informatica"}?,  # optional, default {}
    }

    The last three exist because `open_questions` puts them in front of the customer as
    "contradict any that do not fit". Measured 26.08.2026 against the version before this
    change: four attempts to steer grounding surface, retrieval strategy and ownership
    (`ai_grounding`, `grounding_surface`, `retrieval_strategy`, `ownership_boundaries` in
    the inputs) left the derived blueprint **byte-identical** — the sheet invited a
    contradiction that had nowhere to land. Unset, they still reproduce the previous
    output exactly.
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
            if src.get("handover_layer"):          # SAP→Fabric handover layer (I-20 Stage 1, mirrored field)
                entry["handover_layer"] = src["handover_layer"]
            if src.get("connector"):               # physical handover connector (mirrored field)
                entry["connector"] = src["connector"]
            if src.get("sensitivity"):
                entry["sensitivity"] = src["sensitivity"]
            ingestion.append(entry)
    ingestion.sort(key=lambda e: e["source"])

    # --- P2 architecture concept (medallion default; ADR-0051 pluggable strategy) ----
    # The concept projects governed inputs onto the IR's storage-layer section. Medallion is the
    # best-practice default; the default output is byte-identical to the pre-strategy deriver.
    from tooling.superversion.architecture_concepts import get_concept
    medallion = get_concept(inputs.get("architecture_concept")).derive_layers(domains_in, inputs, hitl)

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
    # Bronze is never groundable (ai_readiness §3.6), so an answer that asks for it is
    # dropped rather than honoured — the enum in the schema says the same thing, and a
    # silently widened surface is the one mistake nobody notices until an assistant quotes
    # uncleaned data back at a customer.
    surface = [s for s in (inputs.get("grounding_surface") or ["gold", "silver"])
               if s in ("gold", "silver")] or ["gold", "silver"]
    strategy = inputs.get("retrieval_strategy") or "builtin"
    ai_grounding: dict[str, Any] = {
        "grounding_surface": surface,
        "retrieval": [
            {"domain": dom["name"], "strategy": strategy, "auth_required": True}
            for dom in sorted(domains_in, key=lambda d: d.get("name", ""))
        ],
        "emits": ["mcp_grounding.json"],
    }

    blueprint: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "platform": {
            "stack": stack,
            "ownership_boundaries": [
                {"workload_class": wc,
                 "owner_platform": (inputs.get("ownership_overrides") or {}).get(wc, stack)}
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
                    "data_contract_ref": f.relative_to(root).as_posix(),
                }
            )
    silver_ref = (
        (contracts_dir).relative_to(root).as_posix() if contracts_dir.is_dir() else None
    )
    return {"stack": "fabric", "silver_contract_ref": silver_ref, "domains": domains}


def emit_grounding(blueprint: dict[str, Any]) -> dict[str, str]:
    """`ground` verb (ADR-0015 / T6): emit a tool-free grounding manifest + a
    per-domain retrieval-decision record. Agents ground on gold/silver **only**.

    Returns ``{relative_path: content}``. Raises if the blueprint's grounding surface
    contains anything other than gold/silver (bronze must never be a grounding source).
    """
    grounding = blueprint.get("ai_grounding", {})
    surface = grounding.get("grounding_surface", [])
    bad = [x for x in surface if x not in ("gold", "silver")]
    if bad:
        raise ValueError(f"grounding surface must be gold/silver only, got {bad} (never bronze)")

    domains = sorted(blueprint.get("mesh", {}).get("domains", []), key=lambda d: d.get("name", ""))
    retrieval_by_domain = {r.get("domain"): r for r in grounding.get("retrieval", [])}

    resources = [
        {
            "domain": d["name"],
            "layer": "gold",
            "data_products": sorted(d.get("data_products", [])),
        }
        for d in domains
    ]
    retrieval = [
        {
            "domain": d["name"],
            "strategy": retrieval_by_domain.get(d["name"], {}).get("strategy", "builtin"),
            "auth_required": retrieval_by_domain.get(d["name"], {}).get("auth_required", True),
            "certified_sources": sorted(retrieval_by_domain.get(d["name"], {}).get("certified_sources", [])),
        }
        for d in domains
    ]

    manifest = {
        "schema": "mcp-grounding/0.1",
        "grounding_surface": list(surface),
        "resources": resources,
        "retrieval": retrieval,
        "note": "Tool-free grounding manifest. Agents ground on gold/silver data "
                "products only (ADR-0015 / ai_readiness §3.6); built-in retrieval "
                "first, MCP only for live/action.",
    }

    lines = ["# Retrieval decisions (per domain)", "",
             "| Domain | Strategy | Auth required | Certified sources |",
             "|---|---|---|---|"]
    for r in retrieval:
        cs = ", ".join(r["certified_sources"]) or "—"
        lines.append(f"| {r['domain']} | {r['strategy']} | {r['auth_required']} | {cs} |")
    record = "\n".join(lines) + "\n"

    return {
        "mcp_grounding.json": json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        "retrieval_decisions.md": record,
    }


def validate_blueprint(blueprint: dict[str, Any]) -> None:
    """Validate against the IR JSON Schema. Soft-skip if jsonschema is unavailable."""
    try:
        from jsonschema import Draft202012Validator
    except Exception:  # pragma: no cover - optional dependency
        return
    schema = json.loads(_SCHEMA_FILE.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(blueprint)
