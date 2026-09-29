"""I-10.0 / Cut S-1 DoD gates: the compiler computes, it doesn't just structure.

Review `docs/plans/SUPERVERSION_ZIELBILD_REVIEW.md` Befund A1 (Critical): before this task,
`from_aluca` always set `expressions={}` and the TMDL target always emitted
`BLANK()` — all 16 use cases passed F1–F6 while zero measures actually computed
anything. These tests are the mechanical proof that the gap is closed for the
governed KPIs the 5 MVP use cases (COM-001/002/003, FIN-002, SCM-002) reference,
and that everything else is an explicit, counted HITL gap — never a silent one.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from tooling.superversion.from_aluca import _default_kpis_dir, from_bracket_file
from tooling.superversion.targets import tmdl

REPO = Path(__file__).resolve().parents[3]
KPIS = _default_kpis_dir()

ALL_16_BRACKETS = sorted(Path(REPO / "core/usecases/core").glob("*/UseCase_Bracket.yaml"))

CORE_5_BRACKETS = {
    "COM-001": REPO / "core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml",
    "COM-002": REPO / "core/usecases/core/COM-002_Margin_Price_Performance/UseCase_Bracket.yaml",
    "COM-003": REPO / "core/usecases/core/COM-003_Customer_Value/UseCase_Bracket.yaml",
    "FIN-002": REPO / "core/usecases/core/FIN-002_Cost_Performance/UseCase_Bracket.yaml",
    "SCM-002": REPO / "core/usecases/core/SCM-002_Supply_Reliability_OTIF/UseCase_Bracket.yaml",
}

# Cut S-1 originally scoped out 13 KPIs as explicit HITL ("komplexe KPIs jenseits
# sum/ratio/delta bleiben HITL, aber gezählt"). The DSL grammar extension (mul,
# delta_chain, distinctcount, count_threshold, round, sumx_over_key, avgx_over_key,
# pvm_volume_effect, pvm_price_effect, recursive calc_ref) now covers all 13 —
# the 5 core use cases are fully computed, 0 documented HITL gaps remain.
KNOWN_HITL_KPI_MEASURE_NAMES: set[str] = set()


def _all_measures(model):
    for table in model.semantic.tables:
        yield from table.measures


@pytest.mark.parametrize("bracket", ALL_16_BRACKETS, ids=lambda p: p.parent.name)
def test_zero_silent_blank_across_all_16_use_cases(bracket):
    """Every `BLANK()` placeholder — in ANY of the 16 use cases, not just the 5
    MVP ones — carries an explicit, diagnosable `/// HITL:` reason. There is no
    code path that emits `= BLANK()` without an adjacent HITL comment (Review
    Befund A1: "gezählt, nicht still BLANK()")."""
    model = from_bracket_file(bracket, KPIS)
    for rel, content in tmdl.emit(model).items():
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if line.strip().endswith("= BLANK()"):
                window = lines[max(0, i - 3):i]
                assert any("/// HITL:" in w for w in window), (
                    f"{bracket.parent.name} {rel}: silent BLANK() at line {i + 1} "
                    f"with no preceding HITL marker: {line!r}"
                )


@pytest.mark.parametrize("uc,bracket", sorted(CORE_5_BRACKETS.items()))
def test_hitl_gaps_matches_the_documented_scope_out(uc, bracket):
    """`hitl_gaps()` for the 5 core UCs never names a KPI outside
    `KNOWN_HITL_KPI_MEASURE_NAMES` (currently empty — the DSL grammar
    extension closed the last 13 gaps) — never a KPI that has a
    `technical.calculation` entry (those must resolve, or the test below
    catches it)."""
    model = from_bracket_file(bracket, KPIS)
    gaps = tmdl.hitl_gaps(model)
    for gap in gaps:
        measure_name = gap.split(":", 1)[0].split(".", 1)[-1]
        assert measure_name in KNOWN_HITL_KPI_MEASURE_NAMES, (
            f"[{uc}] unexpected HITL gap {gap!r} — either author its "
            "technical.calculation or add it to KNOWN_HITL_KPI_MEASURE_NAMES "
            "with a documented reason (never let it pass silently)"
        )


def test_all_5_core_use_cases_are_fully_computed():
    """All 5 MVP use cases (COM-001/002/003, FIN-002, SCM-002) reference zero
    KPIs left as `op: hitl` — the DSL grammar extension closed the last 13
    gaps (PVM effects, margin-vs-plan, promo incremental GM, COM-003 customer
    analytics). 0 HITL gaps, matching Cut S-1's `BLANK()`-quote=0 target."""
    for uc, bracket in CORE_5_BRACKETS.items():
        model = from_bracket_file(bracket, KPIS)
        assert tmdl.hitl_gaps(model) == [], f"{uc} should be fully computed (0 HITL gaps)"


_DAX_MEASURE_RE = re.compile(r"measure '([^']+)' = (.+)")


@pytest.mark.parametrize("uc,bracket", sorted(CORE_5_BRACKETS.items()))
def test_covered_kpis_never_blank(uc, bracket):
    """Every measure NOT in the documented HITL set computes a real DAX
    expression — never `BLANK()` — across all 5 core use cases."""
    model = from_bracket_file(bracket, KPIS)
    content = "\n".join(tmdl.emit(model).values())
    seen = set()
    for name, expr in _DAX_MEASURE_RE.findall(content):
        seen.add(name)
        if name in KNOWN_HITL_KPI_MEASURE_NAMES:
            continue
        assert expr.strip() != "BLANK()", f"[{uc}] governed measure {name!r} is still BLANK()"
    # sanity: the parametrized regex actually matched real measures (not a no-op test)
    assert seen - KNOWN_HITL_KPI_MEASURE_NAMES, f"[{uc}] no non-HITL measures found — regex or fixture broken"


def test_dsl_never_leaks_into_expressions_dax_or_expression():
    """Invariant I1 (corrected): the neutral DSL payload lives ONLY in
    `expressions['dsl']` — it must never be mistaken for (or promoted to) a
    real dialect key by the source adapter."""
    for uc, bracket in CORE_5_BRACKETS.items():
        model = from_bracket_file(bracket, KPIS)
        for m in _all_measures(model):
            assert m.expression == "", f"[{uc}] {m.name!r} has a non-empty bare `expression` (I1 violation)"
            assert "dax" not in m.expressions, f"[{uc}] {m.name!r} carries 'dax' in the SOURCE adapter (I1 violation)"
            assert "sql" not in m.expressions, f"[{uc}] {m.name!r} carries 'sql' in the SOURCE adapter (I1 violation)"
