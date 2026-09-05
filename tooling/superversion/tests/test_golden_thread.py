"""Tests for the Golden-Thread gate (task I-3.4).

DoD: a deliberately broken UC goes red; the gate is WARN-switchable (rollback);
real UCs keep their strategic anchors.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tooling.superversion.canonical_contract import (
    CanonicalModel,
    Measure,
    ReportModel,
    ReportPage,
    SemanticModel,
    Table,
    Visual,
)
from tooling.superversion.from_aluca import (
    UNRESOLVED_DISPLAY_FOLDER,
    from_bracket,
    from_bracket_file,
)
from tooling.superversion.golden_thread import (
    KIND_DANGLING,
    KIND_UNRESOLVED,
    GoldenThreadError,
    assert_golden_thread,
    main,
    validate_golden_thread,
)

REPO = Path(__file__).resolve().parents[3]
KPIS = REPO / "core/kpi_catalog/kpis"
UC = REPO / "core/usecases/core"
BRACKETS = {
    "COM-001": UC / "COM-001_Sales_Performance/UseCase_Bracket.yaml",
    "COM-002": UC / "COM-002_Margin_Price_Performance/UseCase_Bracket.yaml",
    "COM-003": UC / "COM-003_Customer_Value/UseCase_Bracket.yaml",
    "FIN-002": UC / "FIN-002_Cost_Performance/UseCase_Bracket.yaml",
    "SCM-002": UC / "SCM-002_Supply_Reliability_OTIF/UseCase_Bracket.yaml",
}


# ---- real UCs: strategic anchors intact -----------------------------------

@pytest.mark.parametrize("uc", sorted(BRACKETS))
def test_real_ucs_have_no_unresolved_measures(uc):
    model = from_bracket_file(BRACKETS[uc], KPIS)
    unresolved = [v for v in validate_golden_thread(model) if v.kind == KIND_UNRESOLVED]
    assert unresolved == [], f"{uc} has measures without a strategic anchor: {unresolved}"


@pytest.mark.parametrize("uc", sorted(BRACKETS))
def test_real_ucs_pass_default_gate(uc):
    # default severity: unresolved=error (none), dangling=warn → no raise
    model = from_bracket_file(BRACKETS[uc], KPIS)
    assert_golden_thread(model)  # must not raise


def test_known_dangling_binds_detected_and_strict_fails():
    """The gate surfaces the real drift in COM-002 and --strict escalates it.

    Bis zum 05.09.2026 stand hier COM-001. Dessen drei Bindungen (Plan/LY) waren
    behebbar und sind behoben: die zwei Vergleichsbasen tragen seit `22b6fd7d`
    eigene Katalog-IDs, das Bracket referenziert sie, das Modell materialisiert
    sie. COM-002 bleibt der Fall, an dem sich die Erkennung messen laesst — dort
    ist `PVM Bridge Value` ein bewusster Darstellungs-Helfer ohne governte KPI
    (so im Bracket begruendet), also kein Befund, den ein Diff schliesst.
    """
    model = from_bracket_file(BRACKETS["COM-002"], KPIS)
    dangling = [v for v in validate_golden_thread(model) if v.kind == KIND_DANGLING]
    assert dangling, "expected COM-002 to exhibit dangling visual binds"
    # default mode tolerates it (warn); strict escalates to error
    assert_golden_thread(model)  # warn → no raise
    with pytest.raises(GoldenThreadError):
        assert_golden_thread(model, strict=True)


def test_com001_binds_only_materialized_measures():
    """Gegenprobe zum vorigen Test: die COM-001-Bindungen sind wirklich zu, nicht
    nur unbeobachtet. Ohne diese Zeile wuerde ein Rueckfall (Bracket verliert die
    zwei supporting-KPIs wieder) nur noch als Warnung durchlaufen."""
    model = from_bracket_file(BRACKETS["COM-001"], KPIS)
    assert [v for v in validate_golden_thread(model) if v.kind == KIND_DANGLING] == []


# ---- synthetic: deliberately broken UC goes red ---------------------------

def _broken_bracket() -> dict:
    return {
        "id": "TST-001",
        "title": "Broken",
        "orchestration": {"strategic_kpi_id": "does.not.exist.kpi"},
        "primary_kpi_ids": ["does.not.exist.kpi"],
    }


def test_broken_uc_fails_default_gate():
    from tooling.superversion.from_aluca import KpiCatalog
    model = from_bracket(_broken_bracket(), KpiCatalog(KPIS))
    violations = validate_golden_thread(model)
    assert any(v.kind == KIND_UNRESOLVED for v in violations)
    with pytest.raises(GoldenThreadError):
        assert_golden_thread(model)


def test_broken_uc_warn_only_does_not_raise():
    """Rollback: warn_only downgrades everything to advisory."""
    from tooling.superversion.from_aluca import KpiCatalog
    model = from_bracket(_broken_bracket(), KpiCatalog(KPIS))
    assert_golden_thread(model, warn_only=True)  # must not raise


def test_clean_synthetic_model_passes():
    t = Table(name="fact_x", measures=[Measure(name="M", display_folder="Finance")])
    page = ReportPage(name="p", visuals=[Visual(visual_id="v", visual_type="card",
                                                bound_measures=["M"], binds_measures=True)])
    model = CanonicalModel(semantic=SemanticModel(name="S", tables=[t]),
                           report=ReportModel(name="S", pages=[page]))
    assert validate_golden_thread(model) == []
    assert_golden_thread(model, strict=True)  # nothing to flag even in strict


def test_dangling_visual_bind_detected():
    t = Table(name="fact_x", measures=[Measure(name="M", display_folder="Finance")])
    page = ReportPage(name="p", visuals=[Visual(visual_id="v", visual_type="card",
                                                bound_measures=["Ghost"], binds_measures=True)])
    model = CanonicalModel(semantic=SemanticModel(name="S", tables=[t]),
                           report=ReportModel(name="S", pages=[page]))
    v = validate_golden_thread(model)
    assert [x.kind for x in v] == [KIND_DANGLING]
    assert UNRESOLVED_DISPLAY_FOLDER  # constant is the shared SoT with from_aluca


# ---- CLI stage gate -------------------------------------------------------

def test_cli_default_passes_real_ucs():
    # real UCs: 0 unresolved, dangling=warn → exit 0
    assert main([]) == 0


def test_cli_strict_fails_on_dangling():
    # strict escalates COM-002's dangling bind (PVM Bridge Value) → exit 1
    assert main(["--strict"]) == 1


def test_cli_warn_rolls_back_to_advisory():
    assert main(["--warn"]) == 0
