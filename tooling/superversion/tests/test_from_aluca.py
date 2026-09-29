"""Phase-0/1 spike test: ALUCA bracket → canonical model round-trips.

Proves (or refutes) the core thesis of docs/plans/PRODUCT_PLAN.md §0: ALUCA's meaning/visual layer
docks onto Meridian's canonical contract. Runs standalone (no Meridian import).

Run:  python -m pytest tooling/superversion/tests/ -v
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tooling.superversion.canonical_contract import CanonicalModel
from tooling.superversion.from_aluca import (
    KpiCatalog,
    _measure_from_kpi,
    _page_from_layout,
    from_bracket_file,
    main,
    model_to_json,
)

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
    # margin/price KPIs route to fact_sales; promo drivers split out. `margin.gm.vs_plan.pct`'s
    # calculation (I-10.0 grammar extension) resolves against fact_sales[Plan Sales Amount]/
    # [Plan COGS Amount] — matching the real legacy DAX, which never touched fact_plan_sales
    # (that lineage entry was itself the bug: no such "Plan Gross Margin Amount" column exists).
    assert {"fact_sales", "fact_promo"} <= names, (
        f"expected lineage-derived fact tables, got {names}"
    )


def test_com002_measure_count(com002):
    total = sum(len(t.measures) for t in com002.semantic.tables)
    # COM-002 references 15 distinct catalog KPIs (strategic + influencing + supporting
    # + primary, deduped); the adapter resolves each to exactly one measure.
    assert total >= 12, f"expected >=12 measures from COM-002, got {total}"



# Seitenmoebel (Slicer, Narrative, ActionPanel) kommen aus dem Manifest, nicht aus dem
# Bracket — dieselbe Trennung wie `CHROME_TOKENS` in der Visual-Library: die Registry
# beschreibt Absichten, und ein Slicer beantwortet keine Frage.
def _moebel(page):
    from tooling.superversion.layer_tools.visual_library import CHROME_TOKENS
    return [v for v in page.visuals if v.visual_type in CHROME_TOKENS]


def _inhalt(page):
    from tooling.superversion.layer_tools.visual_library import CHROME_TOKENS
    return [v for v in page.visuals if v.visual_type not in CHROME_TOKENS]

def test_com002_report_pages(com002):
    pages = com002.report.pages
    assert len(pages) == 2, "expected 2 pages (summary + execution)"
    by_key = {p.name: p for p in pages}
    # page_1: 3s lead card + 30s slots; page_2: 300s detail.
    #
    # Gezaehlt werden die **Inhalts**-Visuals. Seit 02.08.2026 ergaenzt der Adapter
    # zusaetzlich die Pflicht-Moebel der Seitenvariante (Slicer, ActionPanel) aus dem
    # Manifest — die traegt kein Bracket, und sie an dieser Zahl mitzuzaehlen wuerde
    # den Test bei jeder Manifest-Aenderung rot machen, ohne dass am Adapter etwas
    # falsch waere.
    assert len(_inhalt(by_key["page_1_summary"])) == 4
    assert len(_inhalt(by_key["page_2_execution"])) == 1
    # Und die Moebel sind wirklich Moebel: keins bindet eine Measure.
    for p in pages:
        for v in _moebel(p):
            assert not v.binds_measures, f"{v.visual_id} ist Chrome und bindet Measures"


def test_com002_measure_binding_visuals(com002):
    page1 = next(p for p in com002.report.pages if p.name == "page_1_summary")
    # All four summary visuals bind measures (lead card + driver slots).
    assert all(v.binds_measures for v in _inhalt(page1)), (
        f"summary content visuals must bind measures: "
        f"{[(v.visual_id, v.binds_measures) for v in _inhalt(page1)]}"
    )
    lead = next(v for v in page1.visuals if v.visual_id == "KPI_Cards")
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
    # CLV/lifetime-revenue route to fact_sales/fact_customer_value; retention/churn/active
    # route to fact_customer_events (I-10.0 grammar extension corrected these off a stale
    # dim_customer.CustomerKey lineage entry — the real legacy DAX never touched dim_customer).
    assert {"fact_sales", "fact_customer_events", "fact_customer_value"} <= names, (
        f"expected lineage-derived tables, got {names}"
    )


def test_com003_measure_count(com003):
    total = sum(len(t.measures) for t in com003.semantic.tables)
    # COM-003 pulls a broad CRM + quality/supply trigger chain (21 deduped KPIs).
    assert total >= 15, f"expected >=15 measures from COM-003, got {total}"


def test_measures_fallback_to_measures_table_for_column_less_lineage():
    """KPIs whose lineage carries no '<table>.<column>' land in the _Measures
    fallback (documented `_split_lineage` contract).

    ⚠️ Known nuance (Ledger §6): a column-less lineage entry that *is* a table
    name still routes to _Measures rather than to that fact table. Captured here
    as a direct unit test of `_measure_from_kpi`/`_split_lineage` (not tied to a
    real catalog KPI — `crm.complaint.count`, the previous real-world exemplar,
    was itself the documented lineage bug and has since been corrected to
    `fact_complaints.Complaint Count`, I-10.0 grammar extension)."""
    kpi = {
        "kpi_id": "test.bare_table_lineage",
        "kpi_key": "Bare Table Lineage KPI",
        "technical": {"measure_name": "Bare Table Lineage KPI", "lineage": ["fact_bare_table"]},
    }
    measure, source_table = _measure_from_kpi("test.bare_table_lineage", kpi, KpiCatalog(KPIS))
    assert source_table == ""


def test_com003_report_pages(com003):
    pages = com003.report.pages
    assert len(pages) == 2, "expected 2 pages (summary + execution)"
    by_key = {p.name: p for p in pages}
    assert len(_inhalt(by_key["page_1_summary"])) == 4
    assert len(_inhalt(by_key["page_2_execution"])) == 1


def test_com003_measure_binding_visuals(com003):
    page1 = next(p for p in com003.report.pages if p.name == "page_1_summary")
    assert all(v.binds_measures for v in _inhalt(page1)), (
        f"summary content visuals must bind measures: "
        f"{[(v.visual_id, v.binds_measures) for v in _inhalt(page1)]}"
    )
    lead = next(v for v in page1.visuals if v.visual_id == "KPI_Cards")
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
    assert len(_inhalt(by_key["page_2_execution"])) == 1


def test_fin002_measure_binding_visuals(fin002):
    page1 = next(p for p in fin002.report.pages if p.name == "page_1_summary")
    assert all(v.binds_measures for v in _inhalt(page1)), (
        f"summary content visuals must bind measures: "
        f"{[(v.visual_id, v.binds_measures) for v in _inhalt(page1)]}"
    )
    lead = next(v for v in page1.visuals if v.visual_id == "KPI_Cards")
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
    assert len(_inhalt(by_key["page_2_execution"])) == 1


def test_scm002_measure_binding_visuals(scm002):
    page1 = next(p for p in scm002.report.pages if p.name == "page_1_summary")
    assert all(v.binds_measures for v in _inhalt(page1)), (
        f"summary content visuals must bind measures: "
        f"{[(v.visual_id, v.binds_measures) for v in _inhalt(page1)]}"
    )
    lead = next(v for v in page1.visuals if v.visual_id == "KPI_Cards")
    assert "OTIF %" in lead.bound_measures, (
        f"lead card should bind the strategic measure, got {lead.bound_measures}"
    )


def test_scm002_governance_roles_carried(scm002):
    names = {r.name for r in scm002.semantic.roles}
    assert {"supply_chain_controlling_logistics_performance",
            "logistics_supply_chain_bi_lead"} <= names, (
        f"governance roles not carried into model: {names}"
    )


# --------------------------------------------------------------------------- #
# I-1.4 — component_300s Evidence-Grid sauber mappen. Der 3-30-300-Detail-Grid #
# (`evidence_columns`) wird zu einem measure-bindenden Visual auf Page 2 statt #
# einer leeren Karte. Dimensions-Spalten bleiben Dimensionen (keine Measures); #
# ohne KPI-Spalten greift der v0-Karten-Fallback (binds_measures=False).        #
# --------------------------------------------------------------------------- #

def test_com001_evidence_grid_binds_measures(model):
    """Named I-1.4 input: COM-001 component_300s. Page-2 evidence grid must now
    bind its catalog-resolvable evidence_columns as measures."""
    page2 = next(p for p in model.report.pages if p.name == "page_2_execution")
    assert page2.visuals, "page_2_execution has no visual"
    grid = page2.visuals[0]
    assert grid.binds_measures, "evidence grid must bind measures (was empty card in v0)"
    # KPI columns resolve to their catalog measure names
    assert "Net Sales Amount" in grid.bound_measures
    assert "Gross Margin %" in grid.bound_measures


def test_com001_evidence_grid_excludes_dimension_columns(model):
    """Dimension fields in evidence_columns (region, channel, …) are NOT measures."""
    page2 = next(p for p in model.report.pages if p.name == "page_2_execution")
    grid = page2.visuals[0]
    for dim in ("region", "channel", "product_category", "customer_segment"):
        assert dim not in grid.bound_measures, f"dimension {dim!r} leaked as a measure"


def test_com001_declared_categories_and_evidence_dimensions_reach_canonical_visuals(model):
    page1 = next(p for p in model.report.pages if p.name == "page_1_summary")
    assert next(v for v in page1.visuals if v.visual_id == "Main_1").rows == [
        "dim_date.CalendarYearMonth"
    ]
    page2 = next(p for p in model.report.pages if p.name == "page_2_execution")
    grid = page2.visuals[0]
    assert grid.rows[:2] == ["dim_org.Region", "dim_product.Category"]


def test_evidence_grid_bound_measures_deduped(model):
    """bound_measures carries no duplicates (evidence_columns may repeat a KPI)."""
    page2 = next(p for p in model.report.pages if p.name == "page_2_execution")
    grid = page2.visuals[0]
    assert len(grid.bound_measures) == len(set(grid.bound_measures)), (
        f"duplicate bound measures: {grid.bound_measures}"
    )


def test_evidence_grid_graceful_when_no_kpi_columns():
    """Fehlerfall/Rollback (I-1.4): an evidence grid with only dimension columns
    (none resolvable in the catalog) yields the v0 empty card — binds_measures
    stays False rather than crashing or binding dimension names."""
    catalog = KpiCatalog(KPIS)
    page = {
        "title": "Dims only",
        "component_300s": {
            "evidence_grain": "row",
            "evidence_columns": ["region", "channel", "product_category"],
        },
    }
    rp = _page_from_layout("page_2_execution", page, catalog)
    assert len(_inhalt(rp)) == 1
    assert rp.visuals[0].binds_measures is False
    assert rp.visuals[0].bound_measures == []


@pytest.mark.parametrize("uc", sorted(BRACKETS))
def test_page2_evidence_grid_binds_measures_all_ucs(uc):
    """Across all in-scope UCs the page-2 evidence grid binds measures (each one
    carries KPI-id evidence_columns). Guards the I-1.4 fix from regressing."""
    m = from_bracket_file(BRACKETS[uc], KPIS)
    page2 = next((p for p in m.report.pages if p.name == "page_2_execution"), None)
    assert page2 is not None and page2.visuals, f"[{uc}] no page_2 visual"
    assert page2.visuals[0].binds_measures, f"[{uc}] evidence grid does not bind measures"


# ---- Cross-UC invariants (widen the I-1.1 patterns onto I-1.2/I-1.3 UCs) --- #

@pytest.mark.parametrize("uc", sorted(BRACKETS))
def test_neutral_core_no_dax_primacy_all_ucs(uc):
    """Invariant I1 (neutral core): NO use case may carry a hardcoded DAX
    expression in the source adapter — the dialect is the stack adapter's job.
    Widens test_neutral_core_no_dax_primacy across all BRACKETS
    (COM-001/002/003, FIN-002, SCM-002).

    I-10.0 correction (Review Befund A1): I1 means "neutral FORMULA", not "NO
    formula". `expressions['dsl']` (the governed, stack-neutral calculation
    resolved from the KPI catalog) and `expressions['hitl_reason']` (a
    diagnosable reason string, not an expression) are allowed here — only a
    real dialect key (`dax`, `sql`, ...) would violate neutrality, because
    that is the stack adapter's job (`targets/tmdl.py`), never the source
    adapter's."""
    model = from_bracket_file(BRACKETS[uc], KPIS)
    for m in _all_measures(model):
        assert m.expression == "", (
            f"[{uc}] measure {m.name!r} has a baked-in DAX expression — violates "
            "neutral core (I1); dialect must come from the stack adapter"
        )
        assert set(m.expressions) <= {"dsl", "hitl_reason"}, (
            f"[{uc}] measure {m.name!r} carries a dialect key {set(m.expressions)!r} — "
            "the source adapter stays dialect-neutral (I1); only the neutral 'dsl' "
            "formula (or a 'hitl_reason' marker) may live here, never 'dax'/'sql'"
        )


@pytest.mark.parametrize("uc", sorted(BRACKETS))
def test_deterministic_rebuild(uc):
    """Invariant I2 (determinism): same bracket + catalog → byte-stable model.
    Pure transformation, no LLM — two builds must repr-compare identically."""
    a = from_bracket_file(BRACKETS[uc], KPIS)
    b = from_bracket_file(BRACKETS[uc], KPIS)
    assert repr(a) == repr(b), f"[{uc}] rebuild is not byte-stable (non-deterministic)"


# --------------------------------------------------------------------------- #
# I-1.5 — CLI + golden snapshot je UC. `model_to_json` ist deterministisch;    #
# je UC liegt ein eingecheckter Snapshot unter tests/golden/. Der Regressions- #
# test diff't den frisch gebauten gegen den Snapshot (byte-stabil, I2). Drift  #
# = bewusst regenerieren (CLI) oder Bug fixen.                                  #
# --------------------------------------------------------------------------- #

GOLDEN = Path(__file__).resolve().parent / "golden"


@pytest.mark.parametrize("uc", sorted(BRACKETS))
def test_golden_snapshot_matches(uc):
    """Regression: rebuilt model serialises byte-for-byte to the checked-in
    golden snapshot. On intended change, regenerate via:
        python -m tooling.superversion.from_aluca <bracket> --out tests/golden/<UC>.json
    """
    snapshot = GOLDEN / f"{uc}.json"
    assert snapshot.exists(), (
        f"missing golden snapshot for {uc}: {snapshot} — generate it via the CLI"
    )
    built = model_to_json(from_bracket_file(BRACKETS[uc], KPIS))
    assert built == snapshot.read_text(encoding="utf-8"), (
        f"[{uc}] model drifted from golden snapshot — fix the bug or regenerate "
        "the snapshot deliberately via the CLI"
    )


@pytest.mark.parametrize("uc", sorted(BRACKETS))
def test_model_to_json_byte_stable(uc):
    """I2: serialising the same model twice is byte-identical (no set ordering,
    no timestamps, deterministic field order)."""
    model = from_bracket_file(BRACKETS[uc], KPIS)
    assert model_to_json(model) == model_to_json(model)


def test_cli_writes_snapshot_identical_to_golden(tmp_path):
    """The CLI (`--out`) produces exactly the checked-in golden file — proves the
    snapshots are reproducible from the documented command."""
    out = tmp_path / "COM-001.json"
    rc = main([str(BRACKETS["COM-001"]), "--out", str(out), "--kpis", str(KPIS)])
    assert rc == 0
    assert out.read_text(encoding="utf-8") == (GOLDEN / "COM-001.json").read_text(encoding="utf-8")


def test_cli_stdout_matches_serializer(capsys):
    """Without --out the CLI writes the deterministic JSON to stdout."""
    rc = main([str(BRACKETS["SCM-002"]), "--kpis", str(KPIS)])
    assert rc == 0
    captured = capsys.readouterr().out
    assert captured == model_to_json(from_bracket_file(BRACKETS["SCM-002"], KPIS))


# --------------------------------------------------------------------------- #
# I-2.2 — Meridian-core vendored (ADR-0005). canonical_contract re-exports the   #
# real dataclasses when the vendored subtree is present; the mirror is the       #
# standalone fallback. These guard the seam: full field-for-field parity (both   #
# directions, ALL dataclasses), mirror≡originals output equivalence, manifest    #
# integrity, and the soft-fallback contract.                                     #
# --------------------------------------------------------------------------- #

_CONTRACT_NAMES = (
    "Column", "Measure", "RoleTablePermission", "RoleColumnPermission", "Role",
    "Table", "Relationship", "ModelFunction", "SemanticModel",
    "VisualCalculation", "Visual", "ReportPage", "ExtensionMeasure", "Bookmark",
    "ReportModel", "CanonicalModel",
)


def test_vendored_meridian_present_and_active():
    """The pinned Meridian subtree is vendored, intact, and re-exported by the
    contract seam (ADR-0005). If this skips, the vendor is gone and CI must catch it."""
    from tooling.superversion import _meridian_vendor as mv
    from tooling.superversion import canonical_contract as cc
    if not mv.PIN_PATH.exists():
        pytest.skip("vendored Meridian subtree absent — standalone mirror mode")
    assert mv.is_available(), "vendored subtree present but failed to load/verify"
    assert cc.USING_MERIDIAN_ORIGINALS, "contract seam did not re-export vendored originals"


def test_vendor_manifest_integrity():
    """PIN.json sha256 manifest matches the vendored files (local-divergence guard,
    ADR-0005 rule 6). Tampering with a vendored file must fail this."""
    from tooling.superversion import _meridian_vendor as mv
    if not mv.PIN_PATH.exists():
        pytest.skip("vendored Meridian subtree absent")
    import json
    pin = json.loads(mv.PIN_PATH.read_text(encoding="utf-8"))
    # _verify_manifest raises VendorUnavailable on any mismatch/missing file.
    mv._verify_manifest(pin)
    assert pin["files"], "manifest lists no files"


def test_contract_parity_with_meridian():
    """ADR-0005 rule 3 / I-2.2 DoD: the standalone mirror matches the vendored
    Meridian contract **field-for-field, both directions, across ALL dataclasses**
    (names, order, defaults) — so the mirror and the originals are interchangeable.
    Located via the in-repo vendor path (not a hardcoded absolute path)."""
    from tooling.superversion import _canonical_mirror as mirror
    from tooling.superversion._meridian_vendor import VendorUnavailable, load_contract
    try:
        vendored = load_contract()
    except VendorUnavailable:
        pytest.skip("vendored Meridian subtree not reachable — parity check skipped")

    for name in _CONTRACT_NAMES:
        m = getattr(mirror, name)
        v = vendored[name]
        # field NAMES, both directions
        mf, vf = set(m.__dataclass_fields__), set(v.__dataclass_fields__)
        assert mf == vf, (
            f"{name}: mirror-only={mf - vf}, vendor-only={vf - mf} "
            "— mirror drifted from Meridian; re-sync the mirror + bump the pin"
        )
        # field ORDER
        assert list(m.__dataclass_fields__) == list(v.__dataclass_fields__), (
            f"{name}: field order differs between mirror and Meridian"
        )
        # field DEFAULTS (so asdict output is identical)
        for fname, mfd in m.__dataclass_fields__.items():
            vfd = v.__dataclass_fields__[fname]
            import dataclasses as _dc
            m_has = mfd.default is not _dc.MISSING or mfd.default_factory is not _dc.MISSING
            v_has = vfd.default is not _dc.MISSING or vfd.default_factory is not _dc.MISSING
            assert m_has == v_has, f"{name}.{fname}: default presence differs"
            if mfd.default is not _dc.MISSING or vfd.default is not _dc.MISSING:
                assert mfd.default == vfd.default, f"{name}.{fname}: default value differs"


def test_mirror_and_originals_serialise_identically():
    """The whole point of verbatim parity (Invariant I2): a model built under the
    mirror serialises byte-identically to one built under Meridian's originals, so
    output never depends on whether the vendored core is present."""
    from tooling.superversion._meridian_vendor import VendorUnavailable, load_contract
    try:
        vendored = load_contract()
    except VendorUnavailable:
        pytest.skip("vendored Meridian subtree not reachable")
    from tooling.superversion import _canonical_mirror as mirror

    def build(ns) -> str:
        # construct the same tiny model under each contract and serialise it
        import dataclasses as _dc
        import json as _json
        sm = ns.SemanticModel(
            name="X",
            tables=[ns.Table(name="fact_x", measures=[ns.Measure(name="M", display_folder="D")])],
            roles=[ns.Role(name="r")],
        )
        rep = ns.ReportModel(
            name="X",
            pages=[ns.ReportPage(name="p", visuals=[
                ns.Visual(visual_id="v1", visual_type="card", bound_measures=["M"], binds_measures=True)
            ])],
        )
        model = ns.CanonicalModel(semantic=sm, report=rep)
        return _json.dumps(_dc.asdict(model), indent=2, ensure_ascii=False) + "\n"

    class _Ns:
        pass
    ven_ns = _Ns()
    for n in _CONTRACT_NAMES:
        setattr(ven_ns, n, vendored[n])
    assert build(mirror) == build(ven_ns), "mirror and Meridian originals serialise differently"
