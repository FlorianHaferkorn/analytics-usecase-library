"""Parity test (Cut S-1 (d)): new DSL→DAX synthesis vs. the legacy PowerShell
generator's checked-in output (`products/fabric/powerbi/dist/**/_Measures.tmdl`),
for the 5 MVP use cases (COM-001/002/003, FIN-002, SCM-002).

Per Cut S-1: "semantisch, nicht zwingend byte-gleich" — VAR-scaffolding and
bracket-measure-reference style differ between the two generators (the legacy
generator prefers `VAR x = SUM(...) ... RETURN DIVIDE(x, y)`; the new
synthesizer prefers inline `DIVIDE ( SUM(...), SUM(...) )`), so this test
normalizes BOTH sides down to the **set of terminal `table[Column]` references**
they touch and asserts those sets are equal — not full-text equality. Where the
legacy generator has no counterpart at all (a KPI never emitted historically,
e.g. `margin.ebitda.pct`), parity is reported as "no legacy counterpart", not a
failure — the whole point of this test is to catch DIVERGENCE, not to demand a
legacy measure exist.

Where the two generators genuinely diverge, that is a documented **finding**,
not silently reconciled (Review Befund A2 methodology) — see the
`KNOWN_DIVERGENCES` map below, each entry justified inline.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from tooling.superversion.from_aluca import KpiCatalog, _resolve_calculation
from tooling.superversion.targets import dax_synth

REPO = Path(__file__).resolve().parents[3]
KPIS_DIR = REPO / "core/kpi_catalog/kpis"
DIST = REPO / "products/fabric/powerbi/dist"

# kpi_id -> (legacy dist file, legacy measure name)
KPI_TO_LEGACY = {
    "sales.net_sales.amount": ("Commercial.SemanticModel", "Net Sales Amount"),
    # Am 05.08.2026 aus `op: hitl` geloest: der Katalog behauptete, die Quelltabelle
    # fehle im Data Contract — das handgebaute Modell liest sie aber. Die Grammatik
    # konnte beide Faelle laengst (count / avg / sum), es fehlte nur die Berechnung.
    "enterprise.action_routed.count": ("Experience.SemanticModel", "Actions Routed Count"),
    "scm.supplier_risk.score": ("Finance.SemanticModel", "Supplier Risk Score"),
    "fin.liquidity.payables.amount": ("Finance.SemanticModel", "Payables Amount"),
    # 05.08.2026 aus `op: hitl` geloest, ohne neue Operation: das Muster "Iterator ueber
    # VALUES + mehrere CALCULATE" kommt im Korpus 4x vor (DSO/DIO/DPO/MAPE) und die
    # Grammatik trug es laengst — `value` von avgx_over_key ist ein calc_ref und darf
    # verschachteln. ABS steht im Zaehler statt um den Bruch: fuer nicht-negative Mengen
    # rechnerisch identisch, aber BLANK kommt so direkt aus DIVIDE (Doku: leerer Nenner
    # -> BLANK) und AVERAGEX ueberspringt die Zeile — genau was der Legacy-IF-Guard tat.
    "plan.forecast.mape.pct": ("SupplyChain.SemanticModel", "Forecast MAPE %"),
    # 05.08.2026 ausformuliert, ohne Legacy-Gegenstueck: distinctcount und die Division
    # durch ein Literal konnte die Grammatik laengst — die frueheren hitl-Begruendungen
    # ("distinctcount fehlt", "keine Einheitenumrechnung") waren schlicht falsch.
    "retail.basket.items_per_transaction": (None, "Items per Transaction"),
    "retail.basket.value.average": (None, "Average Basket Value"),
    "ops.planned.hours": (None, "Planned Hours"),
    "cost.cogs.amount": ("Commercial.SemanticModel", "Cost of Goods Sold Amount"),
    "sales.price.list.amount": ("Commercial.SemanticModel", "List Price Amount"),
    "sales.price.net.amount": ("Commercial.SemanticModel", "Net Price Amount"),
    "sales.promo.baseline_sales.amount": ("Commercial.SemanticModel", "Baseline Sales Amount"),
    "sales.promo.cost.amount": ("Commercial.SemanticModel", "Promo Cost"),
    "quality.copq.amount": ("Operations.SemanticModel", "Cost of Poor Quality"),
    "margin.gm.amount": ("Commercial.SemanticModel", "Gross Margin Amount"),
    "sales.promo.incremental.amount": ("Commercial.SemanticModel", "Incremental Sales Amount"),
    "margin.gm.pct": ("Commercial.SemanticModel", "Gross Margin %"),
    "sales.price.realization_pct": ("Commercial.SemanticModel", "Price Realization %"),
    "cost.cogs_per_unit.amount": ("Commercial.SemanticModel", "COGS per Unit"),
    "cost.unit.amount": ("Finance.SemanticModel", "Unit Cost Amount"),
    "margin.cogs.pct": ("Finance.SemanticModel", "COGS % of Sales"),
    "cost.material.pct": ("Finance.SemanticModel", "Material Cost %"),
    "ops.quality.defect_rate.pct": ("Finance.SemanticModel", "Quality Defect Rate %"),
    "quality.fpy.pct": ("Operations.SemanticModel", "First Pass Yield %"),
    "quality.scrap.pct": ("Operations.SemanticModel", "Scrap Rate %"),
    "quality.rework.pct": ("Operations.SemanticModel", "Rework Rate %"),
    "quality.complaint.pct": ("Operations.SemanticModel", "Complaint Rate %"),
    "quality.defect_density": ("Operations.SemanticModel", "Defect Density"),
    "ops.labor.productivity.pct": ("Finance.SemanticModel", "Labor Productivity %"),
    "cost.opex.vs_plan.pct": ("Finance.SemanticModel", "OpEx vs Plan %"),
    "sales.net_sales.delta_pct.plan": ("Commercial.SemanticModel", "Net Sales % vs Plan"),
    "sales.net_sales.delta_pct.ly": ("Commercial.SemanticModel", "Delta% Net Sales"),
    "supply.on_time.pct": ("SupplyChain.SemanticModel", "On-Time %"),
    "supply.in_full.pct": ("SupplyChain.SemanticModel", "In-Full %"),
    "supply.otif.pct": ("SupplyChain.SemanticModel", "OTIF %"),
    "order.lines": ("SupplyChain.SemanticModel", "Order Lines Count"),
    "shipments.count": ("SupplyChain.SemanticModel", "Shipments Count"),
    "supply.stockout_impact.pct": ("SupplyChain.SemanticModel", "Stockout Impact %"),
    "supply.penalty.amount": ("SupplyChain.SemanticModel", "Penalty Amount"),
    "supply.expedite.amount": ("SupplyChain.SemanticModel", "Expedite Cost Amount"),
    # The 13 KPIs closed by the DSL grammar extension (mul, delta_chain, distinctcount,
    # count_threshold, round, sumx_over_key, avgx_over_key, pvm_volume_effect,
    # pvm_price_effect, recursive calc_ref) — Cut S-1 follow-up, "go for 1".
    "sales.pvm.volume_effect.amount": ("Commercial.SemanticModel", "Volume Effect Amount"),
    "sales.pvm.price_effect.amount": ("Commercial.SemanticModel", "Price Effect Amount"),
    "sales.pvm.mix_effect.amount": ("Commercial.SemanticModel", "Mix Effect Amount"),
    "margin.gm.vs_plan.pct": ("Commercial.SemanticModel", "Gross Margin % vs Plan"),
    "sales.promo.incremental_gm.amount": ("Commercial.SemanticModel", "Incremental Gross Margin Amount"),
    "crm.churned_customers.count": ("Commercial.SemanticModel", "Churned Customers"),
    "crm.active_customers.count": ("Commercial.SemanticModel", "Active Customers"),
    "crm.retention.pct": ("Commercial.SemanticModel", "Customer Retention %"),
    "crm.nps.index": ("Commercial.SemanticModel", "Net Promoter Score (NPS)"),
    "crm.lifetime_revenue.amount": ("Commercial.SemanticModel", "Customer Lifetime Revenue Amount"),
    "crm.clv.amount": ("Commercial.SemanticModel", "CLV (Customer Lifetime Value)"),
    "crm.revenue_at_risk.amount": ("Commercial.SemanticModel", "Revenue at Risk Amount"),
    "crm.complaint.count": ("Commercial.SemanticModel", "Complaint Count"),
    # COM-004 (Promotion Effectiveness) — not one of the 5 MVP use cases, but
    # this test checks every non-hitl calculation in the whole catalog, not
    # just the 5-UC subset (its docstring undersells its own scope).
    "sales.promo.cannibalized_sales.amount": ("Commercial.SemanticModel", "Cannibalized Sales Amount"),
    "sales.promo.roi.pct": ("Commercial.SemanticModel", "Promo ROI %"),
    "margin.promo.gm.pct": ("Commercial.SemanticModel", "GM % During Promo"),
    "sales.promo.cannibalization.pct": ("Commercial.SemanticModel", "Cannibalization %"),
    # Operations domain (OPS-001/002/003) — I-10.0 follow-up, "finish ADR-0011"
    # (extending the grammar closure beyond the 5 MVP use cases).
    "ops.availability.pct": ("Operations.SemanticModel", "Availability %"),
    "ops.performance.pct": ("Operations.SemanticModel", "Performance %"),
    "ops.quality.pct": ("Operations.SemanticModel", "Quality %"),
    "ops.oee.pct": ("Operations.SemanticModel", "OEE %"),
    "ops.throughput.units": ("Operations.SemanticModel", "Throughput Units"),
    "ops.downtime.pct": ("Operations.SemanticModel", "Downtime %"),
    "ops.planned_output.units": ("Operations.SemanticModel", "Planned Output Units"),
    "ops.mtbf.hours": ("Operations.SemanticModel", "MTBF (hours)"),
    "ops.mttr.hours": ("Operations.SemanticModel", "MTTR (hours)"),
    "ops.downtime.unplanned.pct": ("Operations.SemanticModel", "Unplanned Downtime %"),
    "ops.failure.count": ("Operations.SemanticModel", "Failure Count"),
    "ops.pm.task.count": ("Operations.SemanticModel", "Preventive Maintenance Task Count"),
    "ops.spare_parts.stockout.pct": ("Operations.SemanticModel", "Spare Parts Stockout %"),
    "ops.pm_compliance.pct": ("Operations.SemanticModel", "PM Compliance %"),
    # Finance domain (FIN-001 Cash/Liquidity) — I-10.0 follow-up, "finish ADR-0011".
    "wc.dso.days": ("Finance.SemanticModel", "DSO Days"),
    "wc.dio.days": ("Finance.SemanticModel", "DIO Days"),
    "wc.dpo.days": ("Finance.SemanticModel", "DPO Days"),
    "wc.ccc.days": ("Finance.SemanticModel", "CCC Days"),
    "fin.cash.balance": ("Finance.SemanticModel", "Cash Balance"),
    "fin.cash.ocf": ("Finance.SemanticModel", "Operating Cash Flow"),
    "fin.cash.vs_plan.pct": ("Finance.SemanticModel", "Cash vs Plan %"),
    "fin.liquidity.inventory.amount": ("Finance.SemanticModel", "Inventory Amount"),
    "fin.overdue_ar.pct": (None, None),  # new-territory, no legacy DAX ever generated
    # SupplyChain domain (SCM-001 Inventory / SCM-003 Forecast) — I-10.0 follow-up.
    "inv.dio.days": ("SupplyChain.SemanticModel", "Days in Inventory"),
    "inv.turnover": ("SupplyChain.SemanticModel", "Inventory Turnover"),
    "inv.stockout.pct": ("SupplyChain.SemanticModel", "Stockout Rate %"),
    "inv.obsolete.pct": ("SupplyChain.SemanticModel", "Obsolete Inventory %"),
    "plan.forecast.accuracy.pct": ("SupplyChain.SemanticModel", "Forecast Accuracy %"),
    "plan.forecast.bias.pct": ("SupplyChain.SemanticModel", "Forecast Bias %"),
    "plans.count": ("SupplyChain.SemanticModel", "Plans Count"),
    # sales.units: the governed calculation matches SupplyChain.SemanticModel's
    # 'Sales Units' = SUM(fact_sales[Sales Units]) exactly (same as the catalog's
    # own lineage). NOTE: Operations.SemanticModel's alias 'Sales Units (OPS)' =
    # SUM(fact_ops[Output Units]) is a DIFFERENT, deliberate legacy proxy (Output
    # Units standing in for Sales Units where OPS-003 has no transaction-level
    # sales data) — a genuine, pre-existing per-semantic-model divergence this
    # single-formula-per-KPI architecture can't represent; not checked here.
    "sales.units": ("SupplyChain.SemanticModel", "Sales Units"),
    # No legacy counterpart was ever generated for these (new-territory KPIs) —
    # parity is vacuous (nothing to diverge from), documented, not asserted.
    "cost.base_volume.amount": (None, None),
    "cost.opex.base.amount": (None, None),
    "margin.ebitda.pct": (None, None),
    # Experience domain (XD-001/002/003/004) — I-10.0 follow-up.
    "svc.sla.attainment.pct": ("Experience.SemanticModel", "SLA Attainment %"),
    "svc.fcr.pct": ("Experience.SemanticModel", "FCR %"),
    "svc.escalation.pct": ("Experience.SemanticModel", "Escalation %"),
    "svc.aht.minutes": ("Experience.SemanticModel", "AHT Minutes"),
    "svc.backlog.count": ("Experience.SemanticModel", "Backlog Count"),
    "svc.tickets.closed.count": ("Experience.SemanticModel", "Tickets Closed Count"),
    "svc.tickets.created.count": ("Experience.SemanticModel", "Tickets Created Count"),
    "res.utilization.pct": ("Experience.SemanticModel", "Utilization %"),
    "res.occupancy.pct": ("Experience.SemanticModel", "Occupancy %"),
    "res.overtime.pct": ("Experience.SemanticModel", "Overtime %"),
    "res.shrinkage.pct": ("Experience.SemanticModel", "Shrinkage %"),
    "ops.working_capital.ccc.days": ("Experience.SemanticModel", "Cash Conversion Cycle (Days)"),
    "enterprise.value_at_risk.index": ("Experience.SemanticModel", "Enterprise Value-at-Risk Index"),
    "enterprise.actions_executed.count": ("Experience.SemanticModel", "Actions Executed Count (XD)"),
    "enterprise.avg_time_to_outcome.days": ("Experience.SemanticModel", "Avg Time-to-Outcome Days (XD)"),
    "enterprise.action_roi.pct": ("Experience.SemanticModel", "Action ROI % (XD)"),
    "enterprise.action_effectiveness_delta.amount": ("Experience.SemanticModel", "Action Effectiveness Delta"),
    # Chosen over the superseded 'Action Outcome Rate % (XD Log)' duplicate — see
    # this KPI's own governance.qa_rules for why.
    "enterprise.action_outcome_rate.pct": ("Experience.SemanticModel", "Action Outcome Rate % (XD)"),
    # Die 4 Use Cases aus `143a984c` (Portfolio-Luecken + Procurement): HR-001,
    # SCM-004, COM-005, FIN-003. Sie haben **keinen** Legacy-Gegenpart — mechanisch
    # geprueft: kein `_Measures.tmdl` unter dist/ fuehrt einen dieser Measure-Namen,
    # und es gibt gar kein HR-/Procurement-Semantikmodell. Die beiden namensaehnlichen
    # Treffer sind andere Kennzahlen: `Attrition Risk %` (XD-003) ist ein
    # BLANK()-Platzhalter fuer ein noch fehlendes Praediktionsmodell, nicht die
    # realisierte Fluktuation ueber `fact_workforce`; `Supplier Risk Score` ist ein
    # Risiko-Score, keine Liefertreue. Parity ist hier also vakuum — es gibt nichts,
    # wovon abgewichen werden koennte. Was **nicht** vakuum ist: die Synthese muss
    # aufloesen, und genau das prueft
    # `test_no_legacy_counterpart_kpis_are_still_resolvable` fuer jeden dieser 17.
    "margin.ebitda.amount": (None, None),
    "margin.ebitda.delta_pct.plan": (None, None),
    "people.absence.pct": (None, None),
    "people.attrition.pct": (None, None),
    "people.cost.per_fte.amount": (None, None),
    "people.engagement.index": (None, None),
    "people.headcount.fte": (None, None),
    "people.timetofill.days": (None, None),
    "procurement.oncontract.pct": (None, None),
    "procurement.ppv.pct": (None, None),
    "procurement.savings.realized.pct": (None, None),
    "procurement.spend.managed.amount": (None, None),
    "procurement.supplier.otd.pct": (None, None),
    "sales.pipeline.coverage.ratio": (None, None),
    "sales.pipeline.value.amount": (None, None),
    "sales.sales_cycle.days": (None, None),
    "sales.win_rate.pct": (None, None),
}

# Documented, deliberate divergences (Review Befund A2 methodology: ledger, not
# silently reconciled). Each maps kpi_id -> human-readable reason the raw
# column-set differs from the legacy generator's.
KNOWN_DIVERGENCES: dict[str, str] = {}

_MEASURE_BLOCK_RE = re.compile(
    r"measure '([^']+)' =\s*(.*?)(?=\n\t(?:///|measure |column )|\Z)", re.S
)
_TABLE_COL_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\[([^\]]+)\]")
_COUNTROWS_BARE_TABLE_RE = re.compile(r"COUNTROWS\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)")
# Legacy sometimes spells the same "count rows matching a condition" semantics
# as `COUNTROWS ( FILTER ( table, cond ) )` instead of the synthesis side's
# `CALCULATE ( COUNTROWS ( table ), cond )` — both touch the whole table (same
# `(table, "*")` sentinel), so both spellings must normalize identically or a
# purely textual-idiom difference reads as a false column-set divergence.
_COUNTROWS_FILTER_TABLE_RE = re.compile(r"COUNTROWS\s*\(\s*FILTER\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*,")
# Negative lookbehind excludes the `[Column]` half of `table[Column]` (a
# genuine column access, already handled by `_TABLE_COL_RE`) — only a bracket
# NOT immediately preceded by an identifier character is a bracket-MEASURE
# reference (`[Measure Name]`). Without this, a measure named e.g. "Net Sales
# Amount" existing in ANY KPI's catalog entry would wrongly "resolve"
# `fact_finance[Net Sales Amount]` (a raw column in a DIFFERENT table) by
# matching on the bracket CONTENT alone — caught by a cross-domain name
# collision (`fact_sales.Net Sales Amount` vs `fact_finance.Net Sales Amount`)
# once the synthesis-side measures map spans the whole catalog (see
# `_all_synthesized_dax`).
_BRACKET_RE = re.compile(r"(?<![A-Za-z0-9_])\[([^\]]+)\]")
_VAR_RE = re.compile(r"VAR\s+(\w+)\s*=\s*(.*?)(?=VAR\s+\w+\s*=|RETURN\b|\Z)", re.S)


def _extract_column_refs(text: str) -> set[tuple[str, str]]:
    """`table[Column]` refs plus bare `COUNTROWS ( table )` and
    `COUNTROWS ( FILTER ( table, ... ) )` refs (neither has a `table[Column]`
    bracket for the table itself — both represented as `(table, "*")`,
    matching the synthesis side's `count`/`count_filtered`/`avg_filtered`
    sentinel)."""
    refs = set(_TABLE_COL_RE.findall(text))
    refs |= {(t, "*") for t in _COUNTROWS_BARE_TABLE_RE.findall(text)}
    refs |= {(t, "*") for t in _COUNTROWS_FILTER_TABLE_RE.findall(text)}
    return refs


def _load_dist_measures(model_name: str) -> dict[str, str]:
    """{measure_name: raw_body_text} for every measure in one dist _Measures.tmdl."""
    path = DIST / model_name / "definition/tables/_Measures.tmdl"
    text = path.read_text(encoding="utf-8")
    return {name: body for name, body in _MEASURE_BLOCK_RE.findall(text)}


def _inline_vars(body: str) -> str:
    """`VAR x = expr ... RETURN result` -> `result` with each VAR name substituted
    by its (parenthesized) expression.

    Deliberately a SINGLE pass per binding name (never re-scanning text a prior
    substitution just inserted): DAX column/measure names routinely CONTAIN a
    var name as a whole word (e.g. var `COGS` vs. column `fact_finance[COGS
    Amount]`) — a naive repeat-until-fixpoint substitution would re-match and
    re-wrap that inserted text forever. Bindings are resolved against EARLIER
    bindings only (DAX requires VARs to be declared before use, so declaration
    order is already dependency order), then substituted into the RETURN body
    once each, longest name first (avoids one name being a prefix of another)."""
    if "RETURN" not in body:
        return body
    var_part, _, return_part = body.partition("RETURN")
    # Alles VOR dem ersten VAR gehoert zum Ausdruck, nicht zu den Bindungen. Stehen die
    # VARs INNERHALB eines Iterators — `AVERAGEX ( VALUES ( t[key] ), VAR x = ... RETURN
    # ... )` — dann steckt dort das Tabellenargument. Es wegzuwerfen loescht `t[key]` aus
    # der Spaltenmenge und laesst die Legacy-Seite aermer aussehen, als sie ist; der
    # Parity-Test meldet dann eine Abweichung, die es nicht gibt (gefunden 05.08.2026 an
    # `Forecast MAPE %`). Bei VARs auf oberster Ebene ist das Praefix leer — unveraendert.
    prefix, _, var_part = var_part.partition("VAR ")
    var_part = ("VAR " + var_part) if var_part else ""
    resolved: dict[str, str] = {}
    for name, expr in _VAR_RE.findall(var_part):
        e = expr.strip()
        for prev_name in sorted(resolved, key=len, reverse=True):
            e = re.sub(rf"\b{re.escape(prev_name)}\b", f"({resolved[prev_name]})", e)
        resolved[name] = e
    result = return_part.strip()
    for name in sorted(resolved, key=len, reverse=True):
        result = re.sub(rf"\b{re.escape(name)}\b", f"({resolved[name]})", result)
    return (prefix + result) if prefix.strip() else result


def _resolve_bracket_refs(text: str, measures: dict[str, str], depth: int = 4) -> str:
    """Substitute `[Measure Name]` refs with that measure's own (VAR-inlined)
    body, recursively, up to `depth` levels — resolves comparison-only measures
    (e.g. `[Plan Sales Amount]`) down to their terminal `table[Column]`."""
    for _ in range(depth):
        changed = False

        def _sub(m: "re.Match[str]") -> str:
            nonlocal changed
            name = m.group(1)
            if name in measures:
                changed = True
                return f"({_inline_vars(measures[name])})"
            return m.group(0)

        new_text = _BRACKET_RE.sub(_sub, text)
        if not changed:
            break
        text = new_text
    return text


def _leaf_column_set(model_name: str, measure_name: str) -> set[tuple[str, str]]:
    measures = _load_dist_measures(model_name)
    body = _inline_vars(measures[measure_name])
    resolved = _resolve_bracket_refs(body, measures)
    return _extract_column_refs(resolved)


def _catalog() -> dict[str, dict]:
    return {
        f.stem: yaml.safe_load(f.read_text(encoding="utf-8"))
        for f in KPIS_DIR.glob("*.yaml")
        if f.stem != "_index"
    }


def _all_synthesized_dax(catalog: dict[str, dict]) -> dict[str, str]:
    """measure_name -> synthesized DAX text, for every KPI with a resolvable
    `technical.calculation` — built by calling the REAL production pipeline
    (`from_aluca._resolve_calculation` + `dax_synth.synthesize_dax`), not a
    parallel test-side re-implementation of the resolution/synthesis logic.
    A sibling-measure reference (`{kpi: ...}`) resolves to a bracket ref
    (`[Measure Name]`) in the synthesized DAX, same as it would in the real
    emitted TMDL — resolving THOSE down to terminal columns reuses the exact
    same `_resolve_bracket_refs`/`_inline_vars` machinery as the legacy side
    (there is nothing to inline here — no VAR/RETURN scaffolding — so
    `_inline_vars` is a no-op passthrough on synthesized text)."""
    kpi_catalog = KpiCatalog(KPIS_DIR)
    out: dict[str, str] = {}
    for kpi in catalog.values():
        measure_name = (kpi.get("technical", {}) or {}).get("measure_name")
        if not measure_name:
            continue
        resolved, _hitl_reason = _resolve_calculation(kpi, kpi_catalog)
        if resolved is None:
            continue
        out[measure_name] = dax_synth.synthesize_dax(resolved)
    return out


def _synthesized_leaf_columns(kpi_id: str, catalog: dict[str, dict]) -> set[tuple[str, str]] | None:
    """Terminal (table, column) pairs the REAL synthesized DAX for `kpi_id`
    touches, after resolving sibling-measure bracket refs — the synthesis-side
    counterpart to `_leaf_column_set` above. Returns None if unresolvable
    (op:hitl, missing calculation, no measure_name)."""
    kpi = catalog.get(kpi_id)
    if not kpi:
        return None
    measure_name = (kpi.get("technical", {}) or {}).get("measure_name")
    if not measure_name:
        return None
    synthesized = _all_synthesized_dax(catalog)
    dax_text = synthesized.get(measure_name)
    if dax_text is None:
        return None
    resolved_text = _resolve_bracket_refs(dax_text, synthesized)
    return _extract_column_refs(resolved_text)


_PARITY_CASES = [(kid, model, name) for kid, (model, name) in KPI_TO_LEGACY.items() if model is not None]


@pytest.mark.parametrize("kpi_id,model_name,measure_name", _PARITY_CASES, ids=[c[0] for c in _PARITY_CASES])
def test_synthesis_matches_legacy_column_set(kpi_id, model_name, measure_name):
    if kpi_id in KNOWN_DIVERGENCES:
        pytest.skip(f"documented divergence: {KNOWN_DIVERGENCES[kpi_id]}")
    catalog = _catalog()
    synthesized = _synthesized_leaf_columns(kpi_id, catalog)
    assert synthesized is not None, f"{kpi_id}: no resolvable calculation (check catalog authoring)"

    legacy = _leaf_column_set(model_name, measure_name)
    assert synthesized == legacy, (
        f"{kpi_id} ({measure_name!r} in {model_name}) column-set diverges from legacy:\n"
        f"  synthesized = {sorted(synthesized)}\n"
        f"  legacy      = {sorted(legacy)}"
    )


def test_no_legacy_counterpart_kpis_are_still_resolvable():
    """KPIs with no historical legacy measure (new territory) must still
    resolve on the synthesis side — parity has nothing to compare against, but
    the formula itself must not be broken."""
    catalog = _catalog()
    for kpi_id, (model_name, _) in KPI_TO_LEGACY.items():
        if model_name is not None:
            continue
        assert _synthesized_leaf_columns(kpi_id, catalog) is not None, (
            f"{kpi_id}: no legacy counterpart AND no resolvable synthesis — check catalog authoring"
        )


def test_parity_case_count_covers_all_non_hitl_core_kpis():
    """Guard against silently shrinking parity coverage: every KPI carrying a
    non-hitl `technical.calculation` that is referenced by the 5 core use cases
    must appear in KPI_TO_LEGACY (mapped to a legacy measure, or explicitly
    'no legacy counterpart') — never just missing from this file."""
    catalog = _catalog()
    computed_kpi_ids = {
        kid for kid, kpi in catalog.items()
        if (kpi.get("technical", {}) or {}).get("calculation", {}).get("op") not in (None, "hitl")
    }
    missing = computed_kpi_ids - set(KPI_TO_LEGACY)
    assert not missing, f"KPIs with a calculation but no parity-test entry: {sorted(missing)}"


# ---------------------------------------------------------------------------
# Es gibt keine zweite DAX-Quelle mehr
#
# Bis 03.08.2026 trug `products/fabric/powerbi/specs/fabric_measure_overlay.yaml`
# fuer 105 KPIs je eine handgeschriebene `dax_expression` und speiste damit den
# pwsh-Generator, waehrend der Katalog ueber `technical.calculation` die Synthese
# speiste. Zwei Quellen fuer dieselbe Wahrheit. Als das FIN-001-Modell fachlich
# richtiggestellt wurde, zog der Katalog nach und das Overlay nicht -- der
# Generator erzeugte weiter `SUM` statt `LASTNONBLANKVALUE`, und kein Test schlug an.
#
# Die Datei ist am 05.08.2026 geloescht. Ihre vier Felder brauchten sie nicht:
# dax_name stand als technical.measure_name im Katalog, display_folder war 105 mal
# leer und folgt dem Use Case, format_string ist aus business.unit_format ableitbar
# (fuer alle 108 KPIs mit Vorbild im dist exakt reproduziert), und die DAX kommt aus
# der Grammatik. Die letzten sieben Eintraege waren keine Formeln, sondern
# `-- TBD: see Measure Dictionary` + BLANK() -- Platzhalter, die weniger sagten als
# der `op: hitl`-Grund im Katalog, der sie ersetzt hat.
#
# Dieser Test haelt den Zustand: taucht die Datei wieder auf oder traegt eine andere
# Spezifikation eine `dax_expression`, ist die Zweitquelle zurueck.
# ---------------------------------------------------------------------------

SPECS_DIR = REPO / "products/fabric/powerbi/specs"
RETIRED_OVERLAY = SPECS_DIR / "fabric_measure_overlay.yaml"


def test_measure_overlay_stays_retired():
    assert not RETIRED_OVERLAY.exists(), (
        f"{RETIRED_OVERLAY.relative_to(REPO)} ist wieder da. Die Datei war eine zweite "
        "Quelle fuer Rechenvorschriften; ihre Felder kommen seit 05.08.2026 aus dem "
        "Katalog. Wenn eine Formel wirklich handgeschrieben sein muss, gehoert sie als "
        "`op: hitl` mit Begruendung in den KPI-Katalog, nicht in eine Parallelspezifikation."
    )


def test_no_spec_file_carries_dax_expressions():
    """Keine Datei unter specs/ traegt DAX. Sonst ist die Zweitquelle nur umgezogen."""
    offenders = []
    for f in sorted(SPECS_DIR.glob("*.y*ml")) if SPECS_DIR.is_dir() else []:
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            continue
        hits = [k for k, v in data.items() if isinstance(v, dict) and v.get("dax_expression")]
        if hits:
            offenders.append(f"{f.relative_to(REPO)}: {len(hits)} Eintrag/Eintraege, u. a. {hits[:3]}")
    assert not offenders, "DAX in einer Spezifikationsdatei gefunden:\n" + "\n".join(f"    {o}" for o in offenders)


def test_every_kpi_resolves_or_declares_why():
    """Jeder KPI hat entweder eine aufloesbare calculation oder ein begruendetes hitl.

    Eine FEHLENDE `calculation` ist der schlechteste Zustand: sie sieht aus wie ein
    Versehen und liest sich wie eine Absicht. Am 05.08.2026 hatten sechs KPIs gar
    keine -- sie sind jetzt als `op: hitl` mit Grund deklariert.
    """
    import sys as _sys
    if str(REPO) not in _sys.path:
        _sys.path.insert(0, str(REPO))
    from tooling.ir.build_ir import synthesize_catalog_dax

    synthesized, unresolved = synthesize_catalog_dax(REPO / "core/kpi_catalog")
    catalog = _catalog()
    undeclared = []
    for kpi_id in unresolved:
        calc = ((catalog.get(kpi_id) or {}).get("technical") or {}).get("calculation") or {}
        if calc.get("op") != "hitl" or not str(calc.get("reason") or "").strip():
            undeclared.append(kpi_id)
    assert not undeclared, (
        "Diese KPIs haben weder eine aufloesbare calculation noch ein begruendetes "
        "`op: hitl` — die Luecke ist da, aber nirgends erklaert:\n"
        + "\n".join(f"    {k}" for k in sorted(undeclared))
    )


# ---------------------------------------------------------------------------
# Offene Faelle sind maschinenlesbar, nicht nur beschrieben
#
# `op: hitl` trug bis 05.08.2026 nur `reason` als Fliesstext. Fuer einen Menschen
# lesbar, fuer Code und Agent nicht: Datenluecke, Grammatikluecke und "Formel noch
# nicht festgelegt" sahen identisch aus, und wer wissen wollte, wie viele wovon,
# musste zwoelf Absaetze lesen. Seit `blocked_by` ist die Klasse ein Feld.
#
# Der eigentliche Gewinn ist der Zaehler. Ob eine Grammatik-Operation gebaut wird,
# war bisher eine Diskussion; jetzt ist es eine Messung: `occurrences_in_corpus`
# haelt fest, wie oft das Muster im dist-Korpus vorkommt. Bei 1 lohnt die Operation
# nicht (sie kostet mehr, als sie traegt). Ab 2 ist sie faellig — und das sagt der
# Test unten, nicht ein Gespraech.
#
# Beleg fuer die Schwelle: am 05.08.2026 wurde `Forecast MAPE %` OHNE neue Operation
# ausgedrueckt, weil sein Muster (Iterator ueber VALUES + mehrere CALCULATE) 4x
# vorkam und die Grammatik es laengst trug. `Service Impact %` blieb offen, weil
# sein Muster genau 1x vorkommt.
# ---------------------------------------------------------------------------

_HITL_CLASSES = {"data_contract", "grammar", "authoring", "decision"}


def _hitl_entries() -> dict[str, dict]:
    out = {}
    for kpi_id, kpi in _catalog().items():
        calc = ((kpi.get("technical") or {}).get("calculation") or {})
        if calc.get("op") == "hitl":
            out[kpi_id] = calc
    return out


def test_hitl_entries_are_machine_readable():
    """Jeder offene Fall sagt einer Maschine, WAS ihn blockiert."""
    bad = []
    for kpi_id, calc in sorted(_hitl_entries().items()):
        blocked = calc.get("blocked_by")
        if blocked not in _HITL_CLASSES:
            bad.append(f"{kpi_id}: blocked_by={blocked!r} (erlaubt: {sorted(_HITL_CLASSES)})")
        elif blocked == "grammar" and not calc.get("pattern"):
            bad.append(f"{kpi_id}: blocked_by=grammar ohne `pattern` — ohne Musternamen "
                       "sind gleichartige Faelle nicht zaehlbar")
    assert not bad, "hitl-Eintraege ohne maschinenlesbare Klasse:\n" + "\n".join(f"    {b}" for b in bad)


def test_recurring_grammar_gap_forces_an_operation():
    """Ab dem ZWEITEN Vorkommen eines Musters wird die Operation faellig.

    Zwei Wege dorthin, beide zaehlen: derselbe `pattern` bei mehreren KPIs, oder ein
    einzelner KPI, dessen gemessenes `occurrences_in_corpus` >= 2 ist. Ein Muster,
    das sich wiederholt, ist kein Einzelfall mehr — und ein Einzelfall ist das
    einzige Argument dafuer, die Operation NICHT zu bauen.
    """
    import collections
    by_pattern = collections.Counter()
    measured = {}
    for kpi_id, calc in _hitl_entries().items():
        if calc.get("blocked_by") != "grammar":
            continue
        pat = calc["pattern"]
        by_pattern[pat] += 1
        occ = calc.get("occurrences_in_corpus")
        if isinstance(occ, int):
            measured[pat] = max(measured.get(pat, 0), occ)

    due = sorted({p for p, n in by_pattern.items() if n >= 2} | {p for p, n in measured.items() if n >= 2})
    assert not due, (
        "Diese DAX-Muster kommen mehrfach vor und sind damit keine Einzelfaelle mehr — "
        "die Grammatik-Operation ist faellig:\n"
        + "\n".join(f"    {p}  (KPIs: {by_pattern[p]}, im Korpus gemessen: {measured.get(p, '—')})"
                    for p in due)
        + "\n\n  Entweder die Operation bauen (dax_synth + from_aluca + sql_synth + Schema), "
        "oder — wenn die Faelle doch verschieden sind — die `pattern`-Namen trennen."
    )
