"""arch_targets.fabric — ArchitectureBlueprint → Microsoft Fabric scaffolding (T4).

Plan-only renderer: emits a deterministic set of provisioning artifacts (a human
runbook + machine-readable plans) describing the Fabric/OneLake layout implied by the
blueprint — lakehouse/workspace/domain topology, the shortcut·mirror ingestion plan
(P1), the medallion layout (P2), and the Direct-Lake semantic binding. It does NOT
call `fab`/REST; live provisioning stays tenant-gated (IR spec §"Still open").

Contract: ``emit(blueprint) -> {relative_path: content}`` — pure & deterministic.
"""
from __future__ import annotations

import json

from tooling.superversion.arch_targets.base import ArchAdapter, register

_ACCESS_ACTION = {
    "shortcut": "OneLake shortcut (zero-copy, virtualize in place)",
    "mirror": "Mirroring (managed replicated copy in OneLake)",
    "copy": "Physical copy (requires the recorded rationale)",
}


def _json(obj) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def emit(blueprint: dict) -> dict[str, str]:
    platform = blueprint.get("platform", {})
    medallion = blueprint.get("medallion", {})
    mesh = blueprint.get("mesh", {})
    ingestion = sorted(blueprint.get("ingestion", []), key=lambda e: e.get("source", ""))
    domains = sorted(mesh.get("domains", []), key=lambda d: d.get("name", ""))
    grounding = blueprint.get("ai_grounding", {})

    # --- machine-readable plans -------------------------------------------------
    workspaces_plan = [
        {
            "domain": d["name"],
            "workspaces": d.get("workspaces", []),
            "data_products": sorted(d.get("data_products", [])),
            "publishing": d.get("publishing", {}),
        }
        for d in domains
    ]
    ingestion_plan = [
        {
            "source": e["source"],
            "source_system": e.get("source_system", ""),
            "access_mode": e["access_mode"],
            "action": _ACCESS_ACTION.get(e["access_mode"], e["access_mode"]),
            "rationale": e.get("rationale", ""),
        }
        for e in ingestion
    ]
    semantic_binding = [
        {"domain": d["name"], "mode": "Direct Lake", "bound_to": f"{d['name']}.SemanticModel",
         "reads": "gold Delta tables"}
        for d in domains
    ]

    # --- human runbook (deterministic) ------------------------------------------
    lines: list[str] = []
    lines.append("# Fabric Provisioning Plan (generated — plan-only)")
    lines.append("")
    lines.append(f"Stack: **{platform.get('stack', 'fabric')}** · "
                 f"schema_version {blueprint.get('schema_version', '?')}")
    lines.append("")
    lines.append("> Generated from an ArchitectureBlueprint by `arch_targets.fabric`. "
                 "No live provisioning is performed; run against a tenant separately.")
    lines.append("")
    lines.append("## 1. Domains & workspaces (data mesh — P3)")
    for d in domains:
        ws = ", ".join(f"`{w['name']}` ({w['role']})" for w in d.get("workspaces", []))
        pub = d.get("publishing", {})
        lines.append(f"- **{d['name']}** → {ws or '(no workspaces)'}; "
                     f"endorsement: {pub.get('endorsement', '?')}, "
                     f"audience: {pub.get('intended_audience', '?')}")
    lines.append("")
    lines.append("## 2. Ingestion (access unification — P1)")
    for e in ingestion_plan:
        lines.append(f"- `{e['source']}` — **{e['access_mode']}**: {e['action']}"
                     + (f" ({e['source_system']})" if e["source_system"] else ""))
    if not ingestion_plan:
        lines.append("- (no sources declared)")
    lines.append("")
    lines.append("## 3. Medallion (P2)")
    bronze = medallion.get("bronze", {})
    lines.append(f"- Bronze: enabled={bronze.get('enabled')}, outsourced={bronze.get('outsourced')} "
                 f"(immutable, append-only system of record)")
    lines.append(f"- Silver: contract `{medallion.get('silver', {}).get('data_contract_ref', '?')}`")
    gp = sorted(p["name"] for p in medallion.get("gold", {}).get("data_products", []))
    lines.append(f"- Gold data products: {', '.join(f'`{n}`' for n in gp) or '(none — HITL)'}")
    lines.append(f"- No-layer-skip: {medallion.get('no_layer_skip')}")
    lines.append("")
    lines.append("## 4. Semantic binding & grounding (AI-era)")
    lines.append("- Direct Lake semantic model per domain, bound to gold.")
    lines.append(f"- Grounding surface: {', '.join(grounding.get('grounding_surface', []))} "
                 "(never bronze); grounding manifest emitted separately (`ground`).")
    runbook = "\n".join(lines) + "\n"

    return {
        "fabric/PROVISIONING_PLAN.md": runbook,
        "fabric/workspaces.json": _json(workspaces_plan),
        "fabric/ingestion_plan.json": _json(ingestion_plan),
        "fabric/medallion.json": _json(medallion),
        "fabric/semantic_binding.json": _json(semantic_binding),
    }


register(ArchAdapter(id="fabric", label="Microsoft Fabric (OneLake)", emit=emit))
