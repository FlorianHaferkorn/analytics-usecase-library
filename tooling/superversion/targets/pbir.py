"""targets.pbir — PBIR report emitter (concrete target adapter, task I-3.3).

Second concrete adapter on the I-3.1 contract (ADR-0006): emits a Power BI
**PBIR** report FROM the canonical model, *official-first*. File layout, `$schema`
URLs, ID rules and the visual/role contract follow Microsoft's
``microsoft/skills-for-fabric`` › ``powerbi-report-authoring`` skill, and the
gate is the official ``powerbi-report-author validate`` CLI (0 errors) —
ALUCA NEVER re-implements that validator (§0.5 official-first doctrine).

Mirrors I-3.2 (TMDL) in spirit: the source adapter ``from_aluca`` stays neutral;
report mechanics are materialized HERE. ALUCA carries *meaning* (which KPIs a
visual binds), not full report layout — so where the canonical model lacks a
field the official visual REQUIRES (e.g. a chart's ``Category`` dimension), we
emit a deterministic **HITL placeholder** projection (the PBIR analogue of
TMDL's ``BLANK()`` + ``/// HITL:`` marker), never invented business data. Those
gaps (and measures dropped when an official role's ``maxPerRole`` is exceeded)
are recorded and surfaced via :func:`hitl_gaps` for the E2E run / ledger.

PBIR contract constants (from the skill's ``references/authoring.md`` and the
official catalog; verified against ``powerbi-report-author validate``):
  - ``definition.pbir`` → ``"version": "4.0"``; ``version.json`` → ``"2.0.0"``
  - every visual MUST carry a ``query.queryState`` with ≥1 projection
  - every *required* role of a visual type MUST be populated (and ``maxPerRole``
    is enforced) — both are validation errors otherwise
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from tooling.superversion.canonical_contract import CanonicalModel

# --- Official PBIR format constants (copy $schema URLs from same-type files) -- #
_SCHEMA = {
    "defprops": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
    "version": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
    "report": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.3.0/schema.json",
    "pages": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
    "page": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
    "visual": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json",
    # Die Item-Metadatendatei jedes Fabric-Items im Git-Format. Sie fehlte — und fiel erst auf,
    # als die CI die CLI ungepinnt installierte und 0.1.4 statt des Repo-Pins 0.1.1 bekam:
    # `PBIR_PLATFORM_MISSING`, gemessen 01.08.2026 (Lauf 30683999822). 0.1.1 prueft es nicht,
    # Fabric braucht es trotzdem — der neuere Pruefer hatte recht, nicht der aeltere.
    "platform": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/"
                "platformProperties/2.0.0/schema.json",
}

# Placeholder entity for HITL/unresolved field references. validate(--no-schema)
# checks PBIR structure, not model resolution, so a clearly-named placeholder
# satisfies a required role while screaming "assign me" to a human.
_HITL_ENTITY = "_HITL"


@dataclass(frozen=True)
class _TypePlan:
    """How an ALUCA visual maps onto an official PBIR visual type + its roles.

    ``primary_role`` is the visual's main data role; it is filled from
    ``bound_measures`` when ``primary_kind == "Measure"`` (cards/charts) or from
    the canonical dimension fields when ``primary_kind == "Column"`` (slicers),
    capped at ``primary_max``. Each role in ``dim_roles`` is a *required*
    grouping role (Column-kind) filled from the canonical dimension fields when
    present, else a HITL placeholder. The placeholder kind always matches the
    role kind — a Column expression in a Measure-only role is a validation error
    (``PBIR_ROLE_KIND_MISMATCH``).
    """
    visual_type: str
    primary_role: str
    primary_kind: str  # "Measure" | "Column"
    primary_max: int | None
    dim_roles: tuple[str, ...]
    # Optional SECOND measure role for visuals that need two distinct measure axes
    # (e.g. scatterChart X + Y). None for every single-measure plan — then emit() takes the
    # unchanged single-primary path, so existing output stays byte-identical.
    secondary_role: str | None = None
    secondary_max: int = 1


# ALUCA visual_type → official PBIR plan. Roles/kinds/maxima taken verbatim from
# `powerbi-report-author catalog describe <type>` (deterministic constants here;
# no CLI call at emit time, so emit() stays pure — Invariant I2).
#
# The `visual_type` of each CHART plan is now governed by the evidence-based idiom
# library (core/templates/page_templates/visual_library/): it must equal the
# powerbi_native visualType of the corresponding governed idiom AND be in the registry's
# allowed set — both enforced by tooling/superversion/tests/test_visual_library.py (see
# layer_tools/visual_idioms.py for the visual_type → idiom bridge). Kept as literal
# constants — not read from the library at runtime — so emit() keeps I2 purity; the tests
# keep them from drifting.
_PLANS: dict[str, _TypePlan] = {
    "card": _TypePlan("cardVisual", "Data", "Measure", None, ()),
    "kpi_card": _TypePlan("cardVisual", "Data", "Measure", None, ()),
    "line_chart": _TypePlan("lineChart", "Y", "Measure", None, ("Category",)),
    "trend_line": _TypePlan("lineChart", "Y", "Measure", None, ("Category",)),
    # Both bar variants → clusteredBarChart: the Visual-Library (I-5.1) standardises
    # length-encoding charts on clusteredBarChart (evidence S2), so we align with the
    # registry rather than emit clusteredColumnChart (which it never sanctions).
    "bar_chart": _TypePlan("clusteredBarChart", "Y", "Measure", None, ("Category",)),
    "bar_chart_horizontal": _TypePlan("clusteredBarChart", "Y", "Measure", None, ("Category",)),
    # clusteredColumnChart shares clusteredBarChart's role schema exactly (Y/Measure + Category —
    # orientation only), so column_time (columns over time) is safe to wire.
    "column_chart": _TypePlan("clusteredColumnChart", "Y", "Measure", None, ("Category",)),
    "column_time": _TypePlan("clusteredColumnChart", "Y", "Measure", None, ("Category",)),
    "waterfall": _TypePlan("waterfallChart", "Y", "Measure", 1, ("Category",)),
    # Roles below are DERIVED FROM THE GOVERNED native goldens (core/…/visual_library/golden/
    # <idiom>.powerbi_native.json) — not guessed — and bound to them by
    # test_visual_library.test_pbir_plans_emit_the_governed_golden_roles, so the generator and the
    # library can never drift. (native output stays Desktop-gated for the whole track, as always.)
    "donut": _TypePlan("donutChart", "Y", "Measure", None, ("Category",)),
    "bar_stacked": _TypePlan("stackedColumnChart", "Y", "Measure", None, ("Category", "Series")),
    "area_stacked": _TypePlan("stackedAreaChart", "Y", "Measure", None, ("Category", "Series")),
    "stacked_100": _TypePlan("hundredPercentStackedColumnChart", "Y", "Measure", None, ("Category", "Series")),
    "decomposition_tree": _TypePlan("decompositionTreeVisual", "Analysis", "Measure", None, ("Explain By",)),
    # scatter needs TWO measure axes → primary X + secondary Y, with Details as the column role.
    "scatter": _TypePlan("scatterChart", "X", "Measure", 1, ("Details",), secondary_role="Y", secondary_max=1),
    "slicer": _TypePlan("slicer", "Values", "Column", 1, ()),
    "table": _TypePlan("tableEx", "Values", "Measure", None, ()),
    "matrix": _TypePlan("tableEx", "Values", "Measure", None, ()),
}
# Unknown ALUCA types fall back to a card (required role: Data only) so the
# report still validates; the mapping is recorded as a gap.
_FALLBACK = _TypePlan("cardVisual", "Data", "Measure", None, ())


def _measure_field(entity: str, prop: str) -> dict:
    return {
        "field": {"Measure": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}},
        "queryRef": f"{entity}.{prop}",
        "nativeQueryRef": prop,
    }


def _column_field(entity: str, prop: str) -> dict:
    return {
        "field": {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}},
        "queryRef": f"{entity}.{prop}",
        "nativeQueryRef": prop,
    }


def _measure_owner_index(canonical: CanonicalModel) -> dict[str, str]:
    """measure name → owning table name (so a projection's Entity matches TMDL)."""
    owner: dict[str, str] = {}
    for table in canonical.semantic.tables:
        for measure in table.measures:
            owner.setdefault(measure.name, table.name)
    return owner


def _dim_fields(visual) -> list[str]:
    """Canonical dimension fields available to fill a chart's Category role."""
    fields = list(visual.rows) + list(visual.columns)
    if visual.slicer_field:
        fields.append(visual.slicer_field)
    return fields


def _visual_json(visual, idx: int, owner: dict[str, str], gaps: list[str]) -> dict:
    plan = _PLANS.get(visual.visual_type)
    if plan is None:
        plan = _FALLBACK
        gaps.append(f"visual '{visual.visual_id}': unknown visual_type "
                    f"'{visual.visual_type}' → mapped to {plan.visual_type}")

    query_state: dict[str, dict] = {}
    available_dims = _dim_fields(visual)

    # Primary role ← measures (Measure-kind) or dimension fields (Column-kind),
    # capped at the official maxPerRole; placeholder kind matches the role kind.
    measure_primary = plan.primary_kind == "Measure"
    items = list(visual.bound_measures) if measure_primary else list(available_dims)
    # Measures reserved for the measure role(s): primary, plus a secondary axis when the plan
    # declares one (scatter X+Y). For single-role plans this equals primary_max, so both the
    # truncation and the emitted output stay byte-identical to before.
    reserved = plan.primary_max
    if plan.secondary_role and plan.primary_max is not None:
        reserved += plan.secondary_max
    if reserved is not None and len(items) > reserved:
        dropped = items[reserved:]
        items = items[:reserved]
        gaps.append(f"visual '{visual.visual_id}': {plan.visual_type}.{plan.primary_role} "
                    f"max {plan.primary_max} exceeded — dropped {dropped}")
    p_items = items[: plan.primary_max] if plan.primary_max is not None else items
    if measure_primary:
        primary_projs = [_measure_field(owner.get(m, "_Measures"), m) for m in p_items]
    else:
        primary_projs = [_column_field(_HITL_ENTITY, f) for f in p_items]

    if not primary_projs:
        # The required primary role still needs a projection to validate; use the
        # role's own kind so we never trip PBIR_ROLE_KIND_MISMATCH.
        placeholder = (_measure_field if plan.primary_kind == "Measure" else _column_field)
        primary_projs = [placeholder(_HITL_ENTITY, f"[HITL] assign {plan.primary_role}")]
        gaps.append(f"visual '{visual.visual_id}': no source field — "
                    f"HITL placeholder in {plan.visual_type}.{plan.primary_role}")
    query_state[plan.primary_role] = {"projections": primary_projs}

    # Optional second measure axis (e.g. scatter Y) ← the next measure after the primary,
    # HITL when the canonical carries only one measure. Skipped entirely for single-role plans.
    if plan.secondary_role:
        s_items = items[plan.primary_max:(plan.primary_max or 0) + plan.secondary_max]
        if s_items:
            sec_projs = [_measure_field(owner.get(m, "_Measures"), m) for m in s_items]
        else:
            sec_projs = [_measure_field(_HITL_ENTITY, f"[HITL] assign {plan.secondary_role}")]
            gaps.append(f"visual '{visual.visual_id}': {plan.visual_type} requires "
                        f"'{plan.secondary_role}' — HITL placeholder (canonical has one measure)")
        query_state[plan.secondary_role] = {"projections": sec_projs}

    # Required grouping roles ← canonical dim fields, else a HITL placeholder.
    for i, role in enumerate(plan.dim_roles):
        if i < len(available_dims):
            projs = [_column_field(_HITL_ENTITY, available_dims[i])]
        else:
            projs = [_column_field(_HITL_ENTITY, f"[HITL] assign {role}")]
            gaps.append(f"visual '{visual.visual_id}': {plan.visual_type} requires "
                        f"'{role}' — HITL placeholder (canonical carries no dimension)")
        query_state[role] = {"projections": projs}

    width = int(visual.width) or 400
    height = int(visual.height) or 300
    z = (idx + 1) * 1000
    return {
        "$schema": _SCHEMA["visual"],
        "name": visual.visual_id,
        "position": {
            "x": int(visual.x), "y": int(visual.y), "z": z,
            "height": height, "width": width, "tabOrder": z,
        },
        "visual": {"visualType": plan.visual_type, "query": {"queryState": query_state}},
    }


def _dumps(obj: dict) -> str:
    """Deterministic JSON text (Invariant I2): stable indent + trailing newline."""
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def _build(canonical: CanonicalModel) -> tuple[dict[str, str], list[str]]:
    report = canonical.report
    base = f"{report.name}.Report"
    owner = _measure_owner_index(canonical)
    gaps: list[str] = []
    out: dict[str, str] = {}

    # `.platform` zuerst: ohne sie ist der Ordner kein Fabric-Item, sondern ein Haufen JSON.
    # `logicalId` bleibt die Nullkennung — sie wird beim Import vergeben; eine erfundene GUID
    # waere schlimmer als keine, weil sie beim naechsten Import kollidieren kann.
    out[f"{base}/.platform"] = _dumps({
        "$schema": _SCHEMA["platform"],
        "metadata": {"type": "Report", "displayName": report.name},
        "config": {"version": "2.0", "logicalId": "00000000-0000-0000-0000-000000000000"},
    })
    out[f"{base}/definition.pbir"] = _dumps({
        "$schema": _SCHEMA["defprops"],
        "version": "4.0",
        "datasetReference": {"byPath": {"path": f"../{canonical.semantic.name}.SemanticModel"}},
    })
    out[f"{base}/definition/version.json"] = _dumps({
        "$schema": _SCHEMA["version"], "version": "2.0.0",
    })
    # Minimal report.json — themes carry their own validation surface
    # (PBIR_THEME_NAME_MISSING_JSON_EXT etc.); deferred as a gap when requested.
    out[f"{base}/definition/report.json"] = _dumps({"$schema": _SCHEMA["report"]})
    if report.theme:
        gaps.append(f"report theme '{report.theme}' not emitted (theme packaging deferred)")

    page_names = [p.name for p in report.pages]
    out[f"{base}/definition/pages/pages.json"] = _dumps({
        "$schema": _SCHEMA["pages"],
        "pageOrder": page_names,
        "activePageName": page_names[0] if page_names else "",
    })

    for page in report.pages:
        page_obj = {
            "$schema": _SCHEMA["page"],
            "name": page.name,
            "displayName": page.display_name or page.name,
            "displayOption": "FitToPage",
            "height": page.height,
            "width": page.width,
        }
        if page.is_hidden:
            page_obj["visibility"] = "HiddenInViewMode"
        out[f"{base}/definition/pages/{page.name}/page.json"] = _dumps(page_obj)
        for idx, visual in enumerate(page.visuals):
            vj = _visual_json(visual, idx, owner, gaps)
            out[f"{base}/definition/pages/{page.name}/visuals/{visual.visual_id}/visual.json"] = _dumps(vj)

    return out, gaps


def emit(canonical: CanonicalModel) -> dict[str, str]:
    """Canonical model → {path: PBIR JSON}. Pure & deterministic (Invariant I2)."""
    return _build(canonical)[0]


def hitl_gaps(canonical: CanonicalModel) -> list[str]:
    """Human-in-the-loop gaps in the emitted PBIR (missing dimensions, dropped
    measures, unmapped visual types, deferred theme) — for the E2E run / ledger."""
    return _build(canonical)[1]


# Register the adapter. Marked `live` only once it passes the official validator
# (`powerbi-report-author validate`, 0 errors) — that CLI is the I-3.3 gate.
from tooling.superversion.targets.base import TargetAdapter, register  # noqa: E402

register(TargetAdapter(
    id="pbir",
    label="Power BI report (PBIR)",
    fmt="pbir",
    emit=emit,
    data_platform="Fabric/Power BI",
    visualization="Power BI",
    status="geplant",
))
