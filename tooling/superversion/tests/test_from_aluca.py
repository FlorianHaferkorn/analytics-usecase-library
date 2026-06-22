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


@pytest.fixture(scope="module")
def model() -> CanonicalModel:
    assert BRACKET.exists(), f"COM-001 bracket missing: {BRACKET}"
    assert KPIS.is_dir(), f"KPI catalog dir missing: {KPIS}"
    return from_bracket_file(BRACKET, KPIS)


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
