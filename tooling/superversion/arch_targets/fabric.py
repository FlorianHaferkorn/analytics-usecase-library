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
from tooling.superversion.capacity import recommend as _capacity_recommend

_ACCESS_ACTION = {
    "shortcut": "OneLake shortcut (zero-copy, virtualize in place)",
    "mirror": "Mirroring (managed replicated copy in OneLake)",
    "copy": "Physical copy (requires the recorded rationale)",
}


def _json(obj) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


# Mirrored emitter → the keyword arguments ALUCA supplies. Order is fixed so the emitted
# set is deterministic. Anything not listed keeps Meridian's own default: this table
# decides what ALUCA *knows*, never what the emitter *is* — the emitter is the mirror's,
# and editing it here would break the byte-identity the whole mechanism rests on.
#
# The first five are the operational concerns this module has always mirrored. The rest
# is the execution half, mirrored 26.08.2026: without it ALUCA emitted a topology and a
# runbook, and every officially-shaped artifact a platform actually needs — `fab` calls,
# fabric-cicd, Terraform, Variable Library, Copy jobs, notebooks, pipelines — existed
# only in Meridian.
_MIRRORED: tuple[tuple[str, dict], ...] = (
    ("emit_governance", {}),
    ("emit_monitoring", {}),
    ("emit_lifecycle", {}),
    ("emit_connectivity", {}),
    ("emit_operability", {}),
    ("emit_apply", {"stack": "fabric"}),
    ("emit_cicd", {"stack": "fabric"}),
    ("emit_fabric_cicd", {"stack": "fabric"}),
    ("emit_terraform", {}),
    ("emit_variable_library", {"stack": "fabric"}),
    ("emit_transforms", {"stack": "fabric"}),
    ("emit_notebooks", {"stack": "fabric"}),
    ("emit_orchestration", {"stack": "fabric"}),
    ("emit_ingestion", {"stack": "fabric"}),
    ("emit_lineage", {"stack": "fabric"}),
    ("emit_chargeback", {}),
    ("emit_direct_lake_guardrails", {}),
    ("emit_metricflow", {}),
    ("emit_translations", {}),
    ("emit_governance_strategy", {}),
)

# Emitters whose signature is not ``(blueprint, **kw)``. Kept as an explicit list rather
# than smoothed into the table above — a wrapper that hides the difference is the place
# where a changed upstream signature stops being noticed.
_SPECIAL = ("emit_prereq", "emit_gates", "emit_fab_commands", "emit_source_schema",
            "emit_ingress_dq")

# Emitters that legitimately return nothing when their input is absent, plus the input
# they wait for. A mirrored emitter that produces no file is reported, never silent:
# "found nothing" and "never ran" look identical from the outside, and that is exactly
# how a broken mirror would hide.
_NEEDS_INPUT = {
    "emit_ingestion": "a source with access_mode 'copy' (shortcut/mirror need no Copy job)",
    "emit_translations": "a culture list — the IR carries no multilingual requirement yet",
    "emit_governance_strategy": "blueprint['governance'] — ALUCA's deriver emits no such section",
    "emit_ingress_dq": "answered source introspections (--source-schema-results)",
}


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
    empty: list[str] = []

    def _take(name: str, artifacts: dict[str, str]) -> None:
        if not artifacts:
            empty.append(name)
        for path, content in artifacts.items():
            out[f"fabric/{path}"] = content

    for name, kwargs in _MIRRORED:
        _take(name, api[name](blueprint, **kwargs))

    # Tag-0 identity and secrets: the only emitter that does not read the blueprint at
    # all, because nothing about it depends on the architecture.
    _take("emit_prereq", api["emit_prereq"](stack="fabric"))
    _take("emit_gates", api["emit_gates"](stack="fabric", blueprint=blueprint))

    # A single script, not a set — it keeps the name Meridian gives it so a customer who
    # has seen one delivery recognises the other.
    out["fabric/provision.sh"] = api["emit_fab_commands"](blueprint)

    # Source introspection is two-phase: the question always, the answer only once the
    # customer has run it. Phase 1 costs nothing and is the thing that gets forgotten, so
    # it is emitted unconditionally; `source_schema_results` upgrades the same call to
    # phase 2 without a second code path.
    _take("emit_source_schema",
          api["emit_source_schema"](blueprint, source_schema_results))

    # Phase 2 pays off here: the answered introspection becomes ingress DQ gates. Parsed
    # through the mirror's own converter, so ALUCA never decides for itself what counts
    # as a REST source.
    by_source = api["tables_by_source"](blueprint, source_schema_results)
    _take("emit_ingress_dq",
          api["emit_ingress_dq"](blueprint, by_source) if by_source else {})

    if empty:
        note = "; ".join(f"{n} — {_NEEDS_INPUT.get(n, 'no input')}" for n in sorted(empty))
        return out, f"mirrored emitters with nothing to emit: {note}"
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

    lines.append("## 5. Provisioning, CI/CD, governance, operations")
    if mirrored:
        lines.append(f"Emitted by the mirrored Meridian emitters ({len(mirrored)} artifact(s)) — "
                     "the Tag-0 identity bootstrap, the `fab` provisioning script, Copy jobs, "
                     "transforms, notebooks and the orchestrating pipeline, the Variable "
                     "Library, Terraform, fabric-cicd and the stage gates, OneLake Security "
                     "roles, failure/throttling alerts, Delta maintenance + BCDR, Managed "
                     "Private Endpoints, lineage, chargeback, Direct-Lake guardrails, "
                     "operational readiness, and the source introspection statements. See "
                     "`SHARED_SUBSTANCE.md` for why these are not reimplemented here.")
        if not source_schema_results:
            lines.append("Source schemas are **not answered yet**: `fabric/source_schema/queries/` "
                         "holds the statements to run against each source; feed the results back "
                         "with `--source-schema-results` to ground the contracts. Until then the "
                         "sources stay visibly unknown rather than getting a plausible default.")
        if skip_reason:
            # Named, not swallowed. An emitter that writes nothing because it has no input
            # reads exactly like an emitter that never ran, and the difference is the whole
            # point of pinning the mirror in the first place.
            lines.append(f"Nothing to emit for some of them — {skip_reason}.")
        for path in sorted(mirrored):
            lines.append(f"- `{path}`")
    else:
        lines.append("**Not emitted** — the mirrored Meridian emitters are unavailable: "
                     f"{skip_reason}")
        lines.append("Re-mirror with `python scripts/check_dataarch_mirror.py --write`. "
                     "Half-correct governance artifacts are worse than none, so nothing is "
                     "substituted here.")
    # --- capacity: floor + procurement ------------------------------------------
    # The schema has always said an absent capacity_sku means consumers must state a
    # recommended FLOOR instead of assuming one. Nobody computed it, so it was either
    # guessed or omitted. Sizing and procurement are reported separately because they
    # have different owners: the architect sizes, the customer buys.
    cap = _capacity_recommend(blueprint)
    lines.append("")
    lines.append("## 6. Capacity (sizing floor + procurement)")
    if cap.get("assigned_sku"):
        lines.append(f"- Assigned: **{cap['assigned_sku']}**")
    else:
        lines.append("- Assigned: **none** — the floor below is a recommendation, not an "
                     "assignment.")
    if cap.get("recommended_floor"):
        lines.append(f"- Recommended floor: **{cap['recommended_floor']}**")
        for reason in cap["floor_reasons"]:
            lines.append(f"  - {reason}")
        hr = cap.get("headroom_at_floor", {})
        lines.append(f"  - Headroom at floor: {hr.get('spark_vcores_baseline')} Spark vCores "
                     f"({hr.get('spark_vcores_burst')} with burst), "
                     f"{hr.get('parallel_model_refreshes')} parallel model refreshes")
        lb = cap.get("licence_breakeven", {})
        if lb.get("applicable") and lb.get("viewers"):
            lines.append(f"  - F64 becomes cheaper than the floor plus Pro licences above "
                         f"~{lb['viewers']} viewers ({lb.get('basis', '')})")
        elif lb.get("applicable"):
            lines.append("  - F64 licence break-even not computed: prices are inputs and were "
                         f"not supplied ({', '.join(lb.get('missing', []))})")
    else:
        lines.append("- Recommended floor: **not derivable** from the declared sizing inputs.")
    if cap.get("conflict"):
        lines.append(f"- **Conflict:** {cap['conflict']}")
    proc = cap.get("procurement", {})
    if proc.get("model"):
        lines.append(f"- Procurement: **{proc['model']}** — {proc.get('reason', '')}")
        for key in ("term", "requires", "caveat"):
            if proc.get(key):
                lines.append(f"  - {proc[key]}")
    spl = cap.get("split", {})
    if spl.get("capacities"):
        n = spl["capacities"]
        lines.append(f"- Split: **{n} {'capacity' if n == 1 else 'capacities'}** — "
                     f"{spl.get('reason', '')}")
        if spl.get("cost"):
            lines.append(f"  - Trade-off: {spl['cost']}")
    if cap.get("unknowns"):
        lines.append("- **Missing inputs** (declare them under `platform.sizing`; they are "
                     "reported rather than defaulted):")
        for u in cap["unknowns"]:
            lines.append(f"  - {u}")
    lines.append("- Storage is billed per GB, is not covered by a reservation and keeps "
                 "running while the capacity is paused. It is added on top of every "
                 "scenario and never changes the reserved-vs-pay-as-you-go decision.")

    runbook = "\n".join(lines) + "\n"

    out = {
        "fabric/PROVISIONING_PLAN.md": runbook,
        "fabric/workspaces.json": _json(workspaces_plan),
        "fabric/ingestion_plan.json": _json(ingestion_plan),
        "fabric/medallion.json": _json(medallion),
        "fabric/semantic_binding.json": _json(semantic_binding),
        "fabric/capacity_plan.json": _json(cap),
    }
    out.update(mirrored)
    return out


register(ArchAdapter(id="fabric", label="Microsoft Fabric (OneLake)", emit=emit))
