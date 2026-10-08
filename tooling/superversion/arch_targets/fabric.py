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

Gold target per domain (ADR-0024, 01.10.2026; amended 02.10.2026). ``gold_targets={domain: "mlv"}``
moves that domain's gold to Fabric Materialized Lake Views through the mirrored ``emit_mlv`` — called
the way Meridian's ``cli.py --emit-mlv`` calls it (``refresh_hints``, ``zeitplan``,
``governed_catalog``). Without the option nothing changes: the default ``lakehouse`` (the
recommendation — lakehouse Delta tables built by the mirrored notebook transforms) reproduces the
output from before the option existed, byte for byte. ``warehouse`` is a valid choice that this
target refuses by name: the mirror has ``emit_warehouse_gold``, but only table shells without a load
path and no ``create_warehouse`` step reachable through ``emit_apply`` (ADR-0024 §8.4). The IR
cannot carry the choice (its schema is byte-identical with Meridian's), so it arrives as a target option next to the
blueprint, from the inputs field ``domains[].gold_target``
(``architecture_blueprint.gold_targets``). ``onelake_rollen_modus`` (``gesamt|einzeln``) is
handed to the apply plan for every Fabric run that sets it, MLV or not.
"""
from __future__ import annotations

import copy
import json

from tooling.superversion.arch_targets.base import ArchAdapter, ArchContractError, register
from tooling.superversion.architecture_blueprint import (
    DEFAULT_GOLD_TARGET,
    GOLD_TARGETS,
    normalize_gold_target,
)
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

# --- Gold target MLV (ADR-0024) -------------------------------------------------------
#
# The emitters that BUILD gold. For a domain whose gold is a Materialized Lake View they get a
# blueprint view without that domain's gold products: a notebook and an MLV that both
# materialise `gold.<product>` are two stores for one object, and whichever ran last would win
# without an error — the conflict Meridian's apply plan names `decide_gold_store` (A.11).
# Bronze -> silver stays: the views read silver.
_GOLD_BUILDERS = ("emit_transforms", "emit_notebooks", "emit_orchestration")
# The emitters whose table names follow the lakehouse layout. MS Learn: "Features like
# materialized lake views require schema-enabled lakehouses" (quoted in `emit_mlv`), so a run
# with an MLV domain is schema-enabled throughout — `gold.<p>` instead of `gold_<p>` — and
# `provision.sh` creates the lakehouse with `enableSchemas=true`. A flat run never reaches here.
_SCHEMA_AWARE = ("emit_transforms", "emit_notebooks", "emit_lineage", "emit_ingestion",
                 "emit_lifecycle")
MLV_ZEITPLAENE = ("je_schicht", "graph")
ONELAKE_ROLLEN_MODI = ("gesamt", "einzeln")


def _ohne_gold(blueprint: dict, products: set[str]) -> dict:
    """The blueprint without ``products`` as gold — for the emitters that would build them."""
    view = copy.deepcopy(blueprint)
    for d in view.get("mesh", {}).get("domains", []) or []:
        d["data_products"] = [p for p in d.get("data_products", []) or [] if p not in products]
    gold = view.get("medallion", {}).get("gold")
    if isinstance(gold, dict):
        gold["data_products"] = [p for p in gold.get("data_products", []) or []
                                 if p.get("name") not in products]
    return view


def _nur_domaenen(blueprint: dict, names: set[str]) -> dict:
    """The blueprint reduced to the domains ``names`` and their gold — the MLV domains."""
    view = copy.deepcopy(blueprint)
    doms = [d for d in view.get("mesh", {}).get("domains", []) or [] if d.get("name") in names]
    view.setdefault("mesh", {})["domains"] = doms
    keep = {p for d in doms for p in d.get("data_products", []) or []}
    gold = view.get("medallion", {}).get("gold")
    if isinstance(gold, dict):
        gold["data_products"] = [p for p in gold.get("data_products", []) or []
                                 if p.get("name") in keep]
    return view


def _check_options(blueprint: dict, gold_targets: dict[str, str] | None,
                   governed_catalog: dict | None, mlv_refresh_hints: bool,
                   mlv_zeitplan: str, onelake_rollen_modus: str | None) -> list[str]:
    """Validate the target options; return the MLV domains (sorted).

    An option that cannot take effect is refused by name — silently ignoring it would read
    as if it had been honoured, which is the failure `base.render` already refuses for
    unknown options.
    """
    targets = {d: normalize_gold_target(t, f"gold_targets[{d}]")
               for d, t in (gold_targets or {}).items()}
    bad = {d: t for d, t in targets.items() if t not in GOLD_TARGETS}
    if bad:
        raise ArchContractError(f"gold_targets: unknown target(s) {bad}; allowed: {list(GOLD_TARGETS)}")
    warehouse = sorted(d for d, t in targets.items() if t == "warehouse")
    if warehouse:
        # A valid choice that this target does not build yet — refused, never half-built. The
        # mirror's `emit_warehouse_gold` writes `CREATE TABLE` shells only ("populate via
        # CTAS/COPY INTO from silver" is left to the reader), and the mirrored `emit_apply`
        # takes no `entscheidungen`, so the plan would run warehouse DDL without ever creating
        # the warehouse item (`create_warehouse` hangs on PLAT-LHTOPO in `build_apply_plan`).
        # Dropping the domain's notebook transforms for that would leave gold empty.
        raise ArchContractError(
            f"gold_target 'warehouse' is not generated yet for: {warehouse}. The recommendation "
            f"is 'lakehouse' (default); 'mlv' is available. Open in ADR-0024 §8.4 "
            f"(docs/architecture/adr/0024-gold-ziel-mlv-neben-dbt-warehouse.md): a warehouse "
            f"load path from silver and a create_warehouse step in the mirrored apply plan.")
    names = {d.get("name") for d in blueprint.get("mesh", {}).get("domains", []) or []}
    unknown = sorted(set(targets) - names)
    if unknown:
        raise ArchContractError(f"gold_targets names domain(s) the blueprint does not have: {unknown}")
    mlv = sorted(d for d, t in targets.items() if t == "mlv")
    if mlv_zeitplan not in MLV_ZEITPLAENE:
        raise ArchContractError(f"mlv_zeitplan {mlv_zeitplan!r} unknown; allowed: {list(MLV_ZEITPLAENE)}")
    if onelake_rollen_modus is not None and onelake_rollen_modus not in ONELAKE_ROLLEN_MODI:
        raise ArchContractError(f"onelake_rollen_modus {onelake_rollen_modus!r} unknown; "
                                f"allowed: {list(ONELAKE_ROLLEN_MODI)}")
    if not mlv:
        idle = [n for n, on in (("mlv_refresh_hints", mlv_refresh_hints),
                                ("mlv_zeitplan", mlv_zeitplan != "je_schicht"),
                                ("governed_catalog", governed_catalog is not None)) if on]
        if idle:
            raise ArchContractError(f"{', '.join(idle)} only take effect for a domain with "
                                    f"gold_target 'mlv' — none is set")
    # A conformed product owned by an MLV domain and a default domain would be built twice,
    # once per store. Which store wins is an architecture decision, not this target's.
    mlv_products = {p for d in blueprint.get("mesh", {}).get("domains", []) or []
                    if d.get("name") in mlv for p in d.get("data_products", []) or []}
    shared = sorted(p for d in blueprint.get("mesh", {}).get("domains", []) or []
                    if d.get("name") not in mlv
                    for p in d.get("data_products", []) or [] if p in mlv_products)
    if shared:
        raise ArchContractError(f"gold product(s) {shared} belong to an 'mlv' and a "
                                f"'{DEFAULT_GOLD_TARGET}' domain — one gold store per product")
    return mlv


def _mirrored_artifacts(blueprint: dict,
                        source_schema_results: dict[str, str] | None = None,
                        mlv_domains: list[str] | None = None,
                        governed_catalog: dict | None = None,
                        mlv_refresh_hints: bool = False,
                        mlv_zeitplan: str = "je_schicht",
                        onelake_rollen_modus: str | None = None,
                        ) -> tuple[dict[str, str], str, list[str]]:
    """Artifacts from the mirrored Meridian emitters, a one-line status and runbook notes.

    Returns ``({}, reason, [])`` when the mirror is unavailable — the caller then emits the
    topology layer alone and surfaces `reason` in the runbook.

    Without ``mlv_domains`` and ``onelake_rollen_modus`` every call is the one this function
    has always made; the options only add to it (ADR-0024).
    """
    try:
        from tooling.superversion._dataarch_vendor import VendorUnavailable, load_emitters
    except ImportError as exc:  # pragma: no cover - loader is part of the repo
        return {}, f"vendor loader unavailable ({exc})", []

    try:
        api = load_emitters()
    except VendorUnavailable as exc:
        return {}, str(exc), []

    out: dict[str, str] = {}
    empty: list[str] = []
    notes: list[str] = []
    mlv = sorted(mlv_domains or [])
    mlv_products = {p for d in blueprint.get("mesh", {}).get("domains", []) or []
                    if d.get("name") in mlv for p in d.get("data_products", []) or []}
    gold_view = _ohne_gold(blueprint, mlv_products) if mlv else blueprint
    # The apply plan links each step to the file it executes only when it sees the emitted
    # tree; Meridian's cli always passes it. ALUCA never did, so its plan carries no artifact
    # column and skips the steps that hang on an artifact (`apply_onelake_roles` among them).
    # Passing it for the default run would change the default output, which this change
    # promises not to do — so it is passed exactly when one of the new options is set.
    apply_with_tree = bool(mlv) or onelake_rollen_modus is not None

    def _take(name: str, artifacts: dict[str, str]) -> None:
        if not artifacts:
            empty.append(name)
        for path, content in artifacts.items():
            out[f"fabric/{path}"] = content

    for name, kwargs in _MIRRORED:
        if name == "emit_apply" and apply_with_tree:
            continue  # built last, against the whole tree (below)
        kw = dict(kwargs)
        if mlv and name in _SCHEMA_AWARE:
            kw["schemas"] = True
        _take(name, api[name](gold_view if name in _GOLD_BUILDERS else blueprint, **kw))

    # Tag-0 identity and secrets: the only emitter that does not read the blueprint at
    # all, because nothing about it depends on the architecture.
    _take("emit_prereq", api["emit_prereq"](stack="fabric"))
    _take("emit_gates", api["emit_gates"](stack="fabric", blueprint=blueprint))

    # A single script, not a set — it keeps the name Meridian gives it so a customer who
    # has seen one delivery recognises the other.
    out["fabric/provision.sh"] = (api["emit_fab_commands"](blueprint, schemas=True) if mlv
                                  else api["emit_fab_commands"](blueprint))

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

    if mlv:
        mlv_view = _nur_domaenen(blueprint, set(mlv))
        # Called as Meridian's cli.py calls it for `--emit-mlv` (schemas, catalog, hints,
        # zeitplan); runtime/ausloeser keep the emitter's defaults (1.3, zeitplan).
        _take("emit_mlv", api["emit_mlv"](mlv_view, schemas=True,
                                          governed_catalog=governed_catalog,
                                          refresh_hints=mlv_refresh_hints,
                                          zeitplan=mlv_zeitplan))
        notes.append(f"Gold as **Materialized Lake Views** for: {', '.join(mlv)} — `fabric/mlv/` "
                     "(schema-enabled lakehouse; the gold transforms and notebooks of these "
                     "domains are not emitted, one store per product). Refresh only when "
                     "triggered: `fabric/mlv/refresh_schedule.json` (D-529)"
                     + (", chained across lakehouses by `fabric/mlv/execution_definition.json` "
                        "(D-621)" if mlv_zeitplan == "graph" else "") + ".")
        if not governed_catalog:
            notes.append("No governed catalog was supplied: the views project `SELECT *` with a "
                         "TODO, carry no partition and no REFRESH_HINT. Export one with "
                         "`tooling/generator/export_governed_catalog.py`.")
        if mlv_refresh_hints:
            # REFRESH_HINT (Preview): Fabric does not check uniqueness, so every view with a
            # hint gets its uniqueness test in dq/ — one rule (`mlv_hint_schluessel`), two
            # readers, exactly as in Meridian's cli.
            keys = api["mlv_hint_schluessel"](mlv_view, governed_catalog)
            if keys:
                ct = (api["beziehungs_spaltentests"](governed_catalog,
                                                     basis=api["vertrags_spaltentests"](governed_catalog),
                                                     modelle=set(mlv_products))
                      if governed_catalog else None)
                _take("emit_dq_gates", api["emit_dq_gates"](mlv_view, schemas=True, column_tests=ct,
                                                            stack="fabric", schluessel_tests=keys))
                notes.append(f"REFRESH_HINT (Preview) on {len(keys)} view(s); their uniqueness "
                             "is tested by the dbt project in `fabric/dq/`, because Fabric does "
                             "not check it.")
            else:
                notes.append("REFRESH_HINT requested, but no view has a declared key — no hint "
                             "written, no uniqueness test needed.")

    if apply_with_tree:
        tree = {p[len("fabric/"):] for p in out}
        kw = {"stack": "fabric", "emitted": tree,
              "onelake_rollen_modus": onelake_rollen_modus or "gesamt"}
        if mlv:
            kw["sql_ddl_layers"] = ("mlv",)
        _take("emit_apply", api["emit_apply"](blueprint, **kw))
        # The mirrored plan treats an SQL-DDL layer per run, not per domain: with MLV for one
        # domain it also writes `run_sql_ddl` for the gold of the others, pointing at views
        # that were never emitted. Named here instead of edited out of a mirrored artifact.
        plan = json.loads(out.get("fabric/apply/APPLY_PLAN.json", "[]") or "[]")
        steps = plan if isinstance(plan, list) else plan.get("steps", plan.get("plan", []))
        stale = sorted(str(op.get("artifact")) for op in steps
                       if isinstance(op, dict) and op.get("action") == "run_sql_ddl"
                       and op.get("artifact") not in tree)
        if stale:
            notes.append(f"**Strike {len(stale)} `run_sql_ddl` step(s)** in `apply/APPLY_PLAN.json` "
                         f"before applying — they belong to `{DEFAULT_GOLD_TARGET}` domains and "
                         f"point at MLV DDL that was not emitted: "
                         + ", ".join(f"`{p}`" for p in stale)
                         + ". The mirrored plan takes the DDL layer per run, not per domain.")

    if empty:
        note = "; ".join(f"{n} — {_NEEDS_INPUT.get(n, 'no input')}" for n in sorted(empty))
        return out, f"mirrored emitters with nothing to emit: {note}", notes
    return out, "", notes


def emit(blueprint: dict,
         source_schema_results: dict[str, str] | None = None,
         gold_targets: dict[str, str] | None = None,
         governed_catalog: dict | None = None,
         mlv_refresh_hints: bool = False,
         mlv_zeitplan: str = "je_schicht",
         onelake_rollen_modus: str | None = None) -> dict[str, str]:
    """Render the Fabric scaffold.

    ``gold_targets`` — ``{domain: "lakehouse" | "mlv" | "warehouse"}`` (ADR-0024); absent
    domains keep the default ``lakehouse``, ``warehouse`` is refused (not generated yet), the
    deprecated alias ``warehouse_dbt`` is read as ``lakehouse`` with a warning.
    ``governed_catalog``, ``mlv_refresh_hints`` and ``mlv_zeitplan`` (``je_schicht|graph``, D-621)
    feed the MLV path and are refused without an MLV domain.
    ``onelake_rollen_modus`` (``gesamt|einzeln``) reaches the apply plan of every Fabric run.
    """
    mlv_domains = _check_options(blueprint, gold_targets, governed_catalog, mlv_refresh_hints,
                                 mlv_zeitplan, onelake_rollen_modus)
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
    if mlv_domains:
        lines.append("- Gold target per domain (ADR-0024): "
                     + ", ".join(f"{d['name']} → **{'mlv' if d['name'] in mlv_domains else DEFAULT_GOLD_TARGET}**"
                                 for d in domains))
    lines.append("")
    lines.append("## 4. Semantic binding & grounding (AI-era)")
    lines.append("- Direct Lake semantic model per domain, bound to gold.")
    lines.append(f"- Grounding surface: {', '.join(grounding.get('grounding_surface', []))} "
                 "(never bronze); grounding manifest emitted separately (`ground`).")
    lines.append("")

    mirrored, skip_reason, notes = _mirrored_artifacts(
        blueprint, source_schema_results, mlv_domains=mlv_domains,
        governed_catalog=governed_catalog, mlv_refresh_hints=mlv_refresh_hints,
        mlv_zeitplan=mlv_zeitplan, onelake_rollen_modus=onelake_rollen_modus)

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
        for note in notes:
            lines.append(note)
        if onelake_rollen_modus is not None:
            lines.append(f"OneLake roles are applied in mode **{onelake_rollen_modus}** "
                         "(`gesamt` = bulk PUT, GA, replaces the whole role set; `einzeln` = POST "
                         "per role, preview, smaller blast radius) — step `apply_onelake_roles`.")
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
    if cap.get("copilot"):
        lines.append(f"- Copilot / data agents: {cap['copilot']['statement']}")
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
