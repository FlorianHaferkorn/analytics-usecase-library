"""arch_targets.fabric — ArchitectureBlueprint → Microsoft Fabric scaffolding (T4).

Plan-only renderer: emits a deterministic set of provisioning artifacts (a human
runbook + machine-readable plans) describing the Fabric/OneLake layout implied by the
blueprint — lakehouse/workspace/domain topology, the shortcut·mirror ingestion plan
(P1), the medallion layout (P2), and the Direct-Lake semantic binding. It does NOT
call `fab`/REST; live provisioning stays tenant-gated (IR spec §"Still open").

On top of that topology layer, the **mirrored Meridian emitters** contribute the
officially-grounded detail this module deliberately does not reimplement (SHARED_SUBSTANCE.md
class A — home is Meridian, ALUCA mirrors byte-identically): OneLake Security roles,
workspace-failure KQL + throttling alerts, Delta OPTIMIZE/VACUUM + BCDR, Managed Private
Endpoints, and operational readiness. Building a second version of those here would be
exactly the duplicate silo the doctrine exists to prevent.

Soft-skip: if the vendored subtree is absent or fails its sha256 PIN, only the topology
layer is emitted and a note records what is missing — a broken mirror must never silently
degrade into half-correct governance artifacts.

Contract: ``emit(blueprint) -> {relative_path: content}`` — deterministic for a given
blueprint and mirror state.
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


# Mirrored emitter → the prefix its artifacts land under. Order is fixed so the emitted
# set is deterministic.
_MIRRORED = ("emit_governance", "emit_monitoring", "emit_lifecycle",
             "emit_connectivity", "emit_operability")


def _mirrored_artifacts(blueprint: dict,
                        source_schema_results: dict[str, str] | None = None,
                        ) -> tuple[dict[str, str], str]:
    """Artifacts from the mirrored Meridian emitters, plus a one-line status.

    Returns ``({}, reason)`` when the mirror is unavailable — the caller then emits the
    topology layer alone and surfaces `reason` in the runbook.
    """
    try:
        from tooling.superversion._dataarch_vendor import VendorUnavailable, load_emitters
    except ImportError as exc:  # pragma: no cover - loader is part of the repo
        return {}, f"vendor loader unavailable ({exc})"

    try:
        api = load_emitters()
    except VendorUnavailable as exc:
        return {}, str(exc)

    out: dict[str, str] = {}
    for name in _MIRRORED:
        for path, content in api[name](blueprint).items():
            out[f"fabric/{path}"] = content

    # Source introspection is two-phase: the question always, the answer only once the
    # customer has run it. Phase 1 costs nothing and is the thing that gets forgotten, so
    # it is emitted unconditionally; `source_schema_results` upgrades the same call to
    # phase 2 without a second code path.
    for path, content in api["emit_source_schema"](blueprint, source_schema_results).items():
        out[f"fabric/{path}"] = content
    return out, ""


def emit(blueprint: dict,
         source_schema_results: dict[str, str] | None = None) -> dict[str, str]:
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
    lines.append("")

    mirrored, skip_reason = _mirrored_artifacts(blueprint, source_schema_results)

    lines.append("## 5. Governance, monitoring, lifecycle, connectivity, operability, "
                 "source introspection")
    if mirrored:
        lines.append(f"Emitted by the mirrored Meridian emitters ({len(mirrored)} artifact(s)) — "
                     "OneLake Security roles, failure/throttling alerts, Delta maintenance + "
                     "BCDR, Managed Private Endpoints, operational readiness, and the source "
                     "introspection statements. See `SHARED_SUBSTANCE.md` for why these are "
                     "not reimplemented here.")
        if not source_schema_results:
            lines.append("Source schemas are **not answered yet**: `fabric/source_schema/queries/` "
                         "holds the statements to run against each source; feed the results back "
                         "with `--source-schema-results` to ground the contracts. Until then the "
                         "sources stay visibly unknown rather than getting a plausible default.")
        for path in sorted(mirrored):
            lines.append(f"- `{path}`")
    else:
        lines.append("**Not emitted** — the mirrored Meridian emitters are unavailable: "
                     f"{skip_reason}")
        lines.append("Re-mirror with `python scripts/check_dataarch_mirror.py --write`. "
                     "Half-correct governance artifacts are worse than none, so nothing is "
                     "substituted here.")
    runbook = "\n".join(lines) + "\n"

    out = {
        "fabric/PROVISIONING_PLAN.md": runbook,
        "fabric/workspaces.json": _json(workspaces_plan),
        "fabric/ingestion_plan.json": _json(ingestion_plan),
        "fabric/medallion.json": _json(medallion),
        "fabric/semantic_binding.json": _json(semantic_binding),
    }
    out.update(mirrored)
    return out


register(ArchAdapter(id="fabric", label="Microsoft Fabric (OneLake)", emit=emit))
