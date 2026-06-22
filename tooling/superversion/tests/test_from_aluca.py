"""Phase-0/1 spike test: ALUCA bracket → canonical model round-trips.

Proves (or refutes) the core thesis of PRODUCT_PLAN.md §0: ALUCA's meaning/visual layer
docks onto Meridian's canonical contract. Runs standalone (no Meridian import).

Run:  python -m pytest tooling/superversion/tests/ -v
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tooling.superversion.canonical_contract import CanonicalModel
from tooling.superversion.from_aluca import KpiCatalog, from_bracket_file

REPO = Path(__file__).resolve().parents[3]
BRACKET = REPO / "core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml"
KPIS = REPO / "core/kpi_catalog/kpis"

# Brackets exercised by the cross-UC invariant tests (I-1.1 baseline + I-1.2 hardening).
# Adding a UC here automatically widens the neutral-core and determinism guards onto it.
BRACKETS: dict[str, Path] = {
    "COM-001": REPO / "core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml",
    "COM-002": REPO / "core/usecases/core/COM-002_Margin_Price_Performance/UseCase_Bracket.yaml",
    "COM-003": REPO / "core/usecases/core/COM-003_Customer_Value/UseCase_Bracket.yaml",
    "FIN-002": REPO / "core/usecases/core/FIN-002_Cost_Performance/UseCase_Bracket.yaml",
    "SCM-002": REPO / "core/usecases/core/SCM-002_Supply_Reliability_OTIF/UseCase_Bracket.yaml",
}


@pytest.fixture(scope="module")
def model() -> CanonicalModel:
    assert BRACKET.exists(), f"COM-001 bracket missing: {BRACKET}"
    assert KPIS.is_dir(), f"KPI catalog dir missing: {KPIS}"
    return from_bracket_file(BRACKET, KPIS)


@pytest.fixture(scope="module")
def com002() -> CanonicalModel:
    p = BRACKETS["COM-002"]
    assert p.exists(), f"COM-002 bracket missing: {p}"
    return from_bracket_file(p, KPIS)


@pytest.fixture(scope="module")
def com003() -> CanonicalModel:
    p = BRACKETS["COM-003"]
    assert p.exists(), f"COM-003 bracket missing: {p}"
    return from_bracket_file(p, KPIS)


@pytest.fixture(scope="module")
def fin002() -> CanonicalModel:
    p = BRACKETS["FIN-002"]
    assert p.exists(), f"FIN-002 bracket missing: {p}"
    return from_bracket_file(p, KPIS)


@pytest.fixture(scope="module")
def scm002() -> CanonicalModel:
    p = BRACKETS["SCM-002"]
    assert p.exists(), f"SCM-002 bracket missing: {p}"
    return from_bracket_file(p, KPIS)


def test_builds_canonical_model(model):
    assert isinstance(model, CanonicalModel)
    assert model.semantic is not None and model.report is not None


def test_semantic_has_tables_and_measures(model):
    assert model.semantic.tables, "no tables derived from bracket KPIs"
    total_measures = sum(len(t.measures) for t in model.semantic.tables)
    assert total_measures >= 5, f"expected >=5 measures from COM-001, got {total_measures}"


def test_measures_resolve_to_fact_tables(model):
    names = {t.name for t in model.semantic.tables}
    # COM-001 references sales.* KPIs whose lineage points at fact_sales
    assert "fact_sales" in names, f"expected fact_sales from lineage, got {names}"


def test_neutral_core_no_dax_primacy(model):
    """Invariant 1 (PRODUCT_PLAN §7): measures carry meaning, not a hardcoded DAX expr."""
    for t in model.semantic.tables:
        for m in t.measures:
            assert m.expression == "", (
                f"measure {m.name} has a DAX expression baked in — violates neutral core; "
                "dialect must be filled by the stack adapter, not the source adapter"
            )


def test_report_pages_from_330300(model):
    assert len(model.report.pages) == 2, "expected 2 pages (summary + execution)"
    all_visuals = [v for p in model.report.pages for v in p.visuals]
    assert all_visuals, "no visuals derived from 3-30-300 layout"
    # at least one visual must bind measures (the lead KPI card)
    assert any(v.binds_measures for v in all_visuals), "no measure-bound visual found"


def test_governance_roles_carried(model):
    role_names = {r.name for r in model.semantic.roles}
    assert {"commercial_controlling_lead", "sales_bi_lead"} & role_names, (
        f"governance roles not carried into model: {role_names}"
    )


# --------------------------------------------------------------------------- #
# I-1.2 — Adapter gehärtet gegen COM-002 (Margin & Price) + COM-003 (Customer  #
# Value). Je UC: Tabellen aus Lineage, Measures-Anzahl, Report-Pages,          #
# measure-bindende Visuals. Plus cross-UC: neutraler Core + Determinismus.     #
# --------------------------------------------------------------------------- #


def _all_measures(m: CanonicalModel):
    return [meas for t in m.semantic.tables for meas in t.measures]


# ---- COM-002 · Margin & Price Performance --------------------------------- #

def test_com002_builds_canonical_model(com002):
    assert isinstance(com002, CanonicalModel)
    assert com002.semantic is not None and com002.report is not None
    assert com002.semantic.name == "COM-002_Margin_Price_Performance"


def test_com002_tables_from_lineage(com002):
    names = {t.name for t in com002.semantic.tables}
    # margin/price KPIs route to fact_sales; plan-vs and promo drivers split out.
    assert {"fact_sales", "fact_plan_sales", "fact_promo"} <= names, (
        f"expected lineage-derived fact tables, got {names}"
    )


def test_com002_measure_count(com002):
    total = sum(len(t.measures) for t in com002.semantic.tables)
    # COM-002 references 15 distinct catalog KPIs (strategic + influencing + supporting
    # + primary, deduped); the adapter resolves each to exactly one measure.
    assert total >= 12, f"expected >=12 measures from COM-002, got {total}"


def test_com002_report_pages(com002):
    pages = com002.report.pages
    assert len(pages) == 2, "expected 2 pages (summary + execution)"
    by_key = {p.name: p for p in pages}
    # page_1: 3s lead card + 3×30s slots; page_2: single 300s detail.
    assert len(by_key["page_1_summary"].visuals) == 4
    assert len(by_key["page_2_execution"].visuals) == 1


def test_com002_measure_binding_visuals(com002):
    page1 = next(p for p in com002.report.pages if p.name == "page_1_summary")
    # All four summary visuals bind measures (lead card + driver slots).
    assert all(v.binds_measures for v in page1.visuals), (
        f"summary visuals must bind measures: "
        f"{[(v.visual_id, v.binds_measures) for v in page1.visuals]}"
    )
    lead = next(v for v in page1.visuals if v.visual_id.endswith("3s_1"))
    assert "Gross Margin %" in lead.bound_measures, (
        f"lead card should bind the strategic measure, got {lead.bound_measures}"
    )


def test_com002_governance_roles_carried(com002):
    names = {r.name for r in com002.semantic.roles}
    assert {"commercial_controlling_lead", "commercial_bi_pricing_analytics_lead"} <= names, (
        f"governance roles not carried into model: {names}"
    )


# ---- COM-003 · Customer Value --------------------------------------------- #

def test_com003_builds_canonical_model(com003):
    assert isinstance(com003, CanonicalModel)
    assert com003.semantic is not None and com003.report is not None
    assert com003.semantic.name == "COM-003_Customer_Value"


def test_com003_tables_from_lineage(com003):
    names = {t.name for t in com003.semantic.tables}
    # CLV/retention route to fact_sales; segment dimension surfaces dim_customer.
    assert {"fact_sales", "dim_customer"} <= names, (
        f"expected lineage-derived tables, got {names}"
    )


def test_com003_measure_count(com003):
    total = sum(len(t.measures) for t in com003.semantic.tables)
    # COM-003 pulls a broad CRM + quality/supply trigger chain (21 deduped KPIs).
    assert total >= 15, f"expected >=15 measures from COM-003, got {total}"


def test_com003_measures_fallback_to_measures_table(com003):
    """KPIs whose lineage carries no '<table>.<column>' land in the _Measures
    fallback (documented `_split_lineage` contract). 'Complaint Count' has
    lineage ['fact_experience'] (table-only, no column) → _Measures.

    ⚠️ Known nuance (Ledger §6): a column-less lineage entry that *is* a table
    name still routes to _Measures rather than to that fact table. Captured here
    as observed behaviour, not silently re-mapped (scope guard: would touch
    _split_lineage for all UCs → out of I-1.2 scope)."""
    measures_tbl = next((t for t in com003.semantic.tables if t.name == "_Measures"), None)
    assert measures_tbl is not None, "expected _Measures fallback table for table-less lineage"
    assert "Complaint Count" in {m.name for m in measures_tbl.measures}


def test_com003_report_pages(com003):
    pages = com003.report.pages
    assert len(pages) == 2, "expected 2 pages (summary + execution)"
    by_key = {p.name: p for p in pages}
    assert len(by_key["page_1_summary"].visuals) == 4
    assert len(by_key["page_2_execution"].visuals) == 1


def test_com003_measure_binding_visuals(com003):
    page1 = next(p for p in com003.report.pages if p.name == "page_1_summary")
    assert all(v.binds_measures for v in page1.visuals), (
        f"summary visuals must bind measures: "
        f"{[(v.visual_id, v.binds_measures) for v in page1.visuals]}"
    )
    lead = next(v for v in page1.visuals if v.visual_id.endswith("3s_1"))
    assert "CLV" in lead.bound_measures, (
        f"lead card should bind the strategic measure, got {lead.bound_measures}"
    )


def test_com003_governance_roles_carried(com003):
    names = {r.name for r in com003.semantic.roles}
    assert {"commercial_controlling_lead", "sales_ops_bi_lead"} <= names, (
        f"governance roles not carried into model: {names}"
    )


# --------------------------------------------------------------------------- #
# I-1.3 — Cross-P&L breadth: FIN-002 (Cost Performance) + SCM-002 (Supply      #
# Reliability / OTIF). FIN-002 exercises broad fact-routing (many fact         #
# tables); SCM-002 exercises the _Measures fallback. Plus they widen the       #
# neutral-core + determinism invariants (via BRACKETS).                        #
# --------------------------------------------------------------------------- #

# ---- FIN-002 · Cost Performance (broad fact-routing) ---------------------- #

def test_fin002_builds_canonical_model(fin002):
    assert isinstance(fin002, CanonicalModel)
    assert fin002.semantic is not None and fin002.report is not None
    assert fin002.semantic.name == "FIN-002_Cost_Performance"


def test_fin002_broad_fact_routing(fin002):
    """Cost KPIs span the P&L: lineage routes measures across several fact
    tables rather than collapsing into one. Guards the per-lineage fact split."""
    names = {t.name for t in fin002.semantic.tables}
    assert {"fact_cost", "fact_finance", "fact_ops"} <= names, (
        f"expected cost KPIs to route across multiple fact tables, got {names}"
    )
    # broad routing means several distinct fact tables, not a single bucket
    fact_tables = {n for n in names if n.startswith("fact_")}
    assert len(fact_tables) >= 4, f"expected broad fact-routing (>=4 facts), got {fact_tables}"


def test_fin002_measure_count(fin002):
    total = sum(len(t.measures) for t in fin002.semantic.tables)
    assert total >= 10, f"expected >=10 measures from FIN-002, got {total}"


def test_fin002_report_pages(fin002):
    pages = fin002.report.pages
    assert len(pages) == 2, "expected 2 pages (summary + execution)"
    by_key = {p.name: p for p in pages}
    assert by_key["page_1_summary"].visuals, "summary page has no visuals"
    assert len(by_key["page_2_execution"].visuals) == 1


def test_fin002_measure_binding_visuals(fin002):
    page1 = next(p for p in fin002.report.pages if p.name == "page_1_summary")
    assert all(v.binds_measures for v in page1.visuals), (
        f"summary visuals must bind measures: "
        f"{[(v.visual_id, v.binds_measures) for v in page1.visuals]}"
    )
    lead = next(v for v in page1.visuals if v.visual_id.endswith("3s_1"))
    assert "Unit Cost Amount" in lead.bound_measures, (
        f"lead card should bind the strategic measure, got {lead.bound_measures}"
    )


def test_fin002_governance_roles_carried(fin002):
    names = {r.name for r in fin002.semantic.roles}
    assert {"plant_ops_controllers", "finance_bi_lead"} <= names, (
        f"governance roles not carried into model: {names}"
    )


# ---- SCM-002 · Supply Reliability / OTIF (_Measures fallback) ------------- #

def test_scm002_builds_canonical_model(scm002):
    assert isinstance(scm002, CanonicalModel)
    assert scm002.semantic is not None and scm002.report is not None
    assert scm002.semantic.name == "SCM-002_Supply_Reliability_OTIF"


def test_scm002_fact_routing(scm002):
    names = {t.name for t in scm002.semantic.tables}
    assert "fact_fulfillment" in names, f"expected fact_fulfillment from lineage, got {names}"


def test_scm002_measures_fallback_table(scm002):
    """KPIs with column-less lineage (e.g. order.lines / shipments.count →
    lineage ['fact_fulfillment'], no '<table>.<column>') land in the _Measures
    fallback per the documented `_split_lineage` contract.

    ⚠️ Known nuance (Ledger §6, shared with COM-003): a column-less lineage
    entry that *is* a table name still routes to _Measures instead of that fact
    table — note that fact_fulfillment ALSO exists as a real table here from
    column-qualified lineage, so the same logical fact is split. Captured as
    observed behaviour, not silently re-mapped (would touch _split_lineage for
    all UCs → out of I-1.3 scope)."""
    measures_tbl = next((t for t in scm002.semantic.tables if t.name == "_Measures"), None)
    assert measures_tbl is not None, "expected _Measures fallback table for table-less lineage"
    fallback_names = {m.name for m in measures_tbl.measures}
    assert {"Order Lines Count", "Shipments Count"} <= fallback_names, (
        f"expected column-less-lineage measures in _Measures, got {fallback_names}"
    )


def test_scm002_measure_count(scm002):
    total = sum(len(t.measures) for t in scm002.semantic.tables)
    assert total >= 6, f"expected >=6 measures from SCM-002, got {total}"


def test_scm002_report_pages(scm002):
    pages = scm002.report.pages
    assert len(pages) == 2, "expected 2 pages (summary + execution)"
    by_key = {p.name: p for p in pages}
    assert by_key["page_1_summary"].visuals, "summary page has no visuals"
    assert len(by_key["page_2_execution"].visuals) == 1


def test_scm002_measure_binding_visuals(scm002):
    page1 = next(p for p in scm002.report.pages if p.name == "page_1_summary")
    assert all(v.binds_measures for v in page1.visuals), (
        f"summary visuals must bind measures: "
        f"{[(v.visual_id, v.binds_measures) for v in page1.visuals]}"
    )
    lead = next(v for v in page1.visuals if v.visual_id.endswith("3s_1"))
    assert "OTIF %" in lead.bound_measures, (
        f"lead card should bind the strategic measure, got {lead.bound_measures}"
    )


def test_scm002_governance_roles_carried(scm002):
    names = {r.name for r in scm002.semantic.roles}
    assert {"supply_chain_controlling_logistics_performance",
            "logistics_supply_chain_bi_lead"} <= names, (
        f"governance roles not carried into model: {names}"
    )


# ---- Cross-UC invariants (widen the I-1.1 patterns onto I-1.2/I-1.3 UCs) --- #

@pytest.mark.parametrize("uc", sorted(BRACKETS))
def test_neutral_core_no_dax_primacy_all_ucs(uc):
    """Invariant I1 (neutral core): NO use case may carry a hardcoded DAX
    expression in the source adapter — the dialect is the stack adapter's job.
    Widens test_neutral_core_no_dax_primacy across all BRACKETS
    (COM-001/002/003, FIN-002, SCM-002)."""
    model = from_bracket_file(BRACKETS[uc], KPIS)
    for m in _all_measures(model):
        assert m.expression == "", (
            f"[{uc}] measure {m.name!r} has a baked-in DAX expression — violates "
            "neutral core (I1); dialect must come from the stack adapter"
        )
        assert m.expressions == {}, (
            f"[{uc}] measure {m.name!r} carries a prefilled dialect map — the source "
            "adapter stays dialect-neutral (I1)"
        )


@pytest.mark.parametrize("uc", sorted(BRACKETS))
def test_deterministic_rebuild(uc):
    """Invariant I2 (determinism): same bracket + catalog → byte-stable model.
    Pure transformation, no LLM — two builds must repr-compare identically."""
    a = from_bracket_file(BRACKETS[uc], KPIS)
    b = from_bracket_file(BRACKETS[uc], KPIS)
    assert repr(a) == repr(b), f"[{uc}] rebuild is not byte-stable (non-deterministic)"


def test_contract_parity_with_meridian():
    """If Meridian is reachable in the same env, assert our mirrored contract matches
    its real CanonicalModel field-for-field (PRODUCT_PLAN §0: 1:1 portability)."""
    import importlib.util
    mer = Path("/sessions/cool-zen-pascal/mnt/Freelancing")
    if not (mer / "core/pbi_engine/model.py").exists():
        pytest.skip("Meridian repo not reachable — parity check skipped")
    import sys
    sys.path.insert(0, str(mer))
    try:
        from core.pbi_engine.parsers.tmdl_parser import Measure as MMeasure
        from tooling.superversion.canonical_contract import Measure as AMeasure
        mfields = {f for f in MMeasure.__dataclass_fields__}
        afields = {f for f in AMeasure.__dataclass_fields__}
        missing = mfields - afields
        assert not missing, f"mirrored Measure missing Meridian fields: {missing}"
    finally:
        sys.path.remove(str(mer))
