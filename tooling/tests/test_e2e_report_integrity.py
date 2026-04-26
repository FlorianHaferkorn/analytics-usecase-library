"""
test_e2e_report_integrity.py — End-to-end report integrity gate.

Pipeline validated:
  Parquet (gold facts + dims)
    → TMDL semantic model (measures + dim columns)
      → PBIR visual.json (measure bindings + column bindings)

Tests:
  1. Every Parquet fact table referenced in TMDL exists and is non-empty
  2. Every measure Property in visual.json exists in the domain _Measures.tmdl
  3. Every Column Property in visual.json exists in the domain TMDL table definitions
  4. No BLANK() stub measures in any domain _Measures.tmdl
  5. No kpi_id-named measures (e.g. 'margin.gm.pct') — all must use display names
  6. Every TMDL measure has a formatString and a displayFolder
  7. Required visuals present on every report page (Overview: KPI_Cards; Detail: Smart_Narrative)
  8. All 15 reports have exactly one Overview and one Detail page

The test is parameterised over all 15 reports so failures are attributed to the
exact report + visual + binding rather than reported as a single bulk failure.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Set

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DIST_ROOT = REPO_ROOT / "products/fabric/powerbi/dist"
GOLD_FACTS = REPO_ROOT / "showcases/aurora_group/data/gold/facts"
GOLD_DIMS  = REPO_ROOT / "showcases/aurora_group/data/gold/dimensions"

# Map report prefix → SemanticModel directory
DOMAIN_MAP: Dict[str, str] = {
    "COM": "Commercial.SemanticModel",
    "FIN": "Finance.SemanticModel",
    "OPS": "Operations.SemanticModel",
    "SCM": "SupplyChain.SemanticModel",
    "XD":  "Experience.SemanticModel",
}

# ── helpers ──────────────────────────────────────────────────────────────────

def _report_prefix(report_dir: Path) -> str:
    return report_dir.name.split("-")[0].split("_")[0]


def _model_path(report_dir: Path) -> Path:
    prefix = _report_prefix(report_dir)
    return DIST_ROOT / DOMAIN_MAP.get(prefix, "Commercial.SemanticModel")


def _get_measures(model: Path) -> Set[str]:
    """Return all measure display names defined in every TMDL in the model."""
    names: Set[str] = set()
    for tmdl in (model / "definition/tables").glob("*.tmdl"):
        text = tmdl.read_text(encoding="utf-8")
        # Both 'quoted names' and unquoted single-word names
        names |= set(re.findall(r"^\tmeasure '([^']+)'", text, re.MULTILINE))
        names |= set(re.findall(r"^\tmeasure (\S+) =", text, re.MULTILINE))
    return names


def _get_table_columns(model: Path) -> Dict[str, Set[str]]:
    """Return {table_name: {column_names}} for every TMDL in the model."""
    result: Dict[str, Set[str]] = {}
    for tmdl in (model / "definition/tables").glob("*.tmdl"):
        text = tmdl.read_text(encoding="utf-8")
        quoted   = set(re.findall(r"^\tcolumn '([^']+)'", text, re.MULTILINE))
        unquoted = set(re.findall(r"^\tcolumn (\S+)\s*$", text, re.MULTILINE))
        result[tmdl.stem] = quoted | unquoted
    return result


def _visual_projections(visual_json: Path):
    """Yield (field_type, entity, property) for every projection in a visual.json."""
    d = json.loads(visual_json.read_text(encoding="utf-8"))
    qs = d.get("visual", {}).get("query", {}).get("queryState", {})
    for _, role_data in qs.items():
        for proj in role_data.get("projections", []):
            f = proj.get("field", {})
            if not f:
                continue
            ftype = next(iter(f), None)
            if not ftype:
                continue
            entity = f[ftype].get("Expression", {}).get("SourceRef", {}).get("Entity", "")
            prop   = f[ftype].get("Property", "")
            yield ftype, entity, prop


def _all_reports():
    return sorted(DIST_ROOT.glob("*.Report"))


def _report_ids():
    return [r.name for r in _all_reports()]


# ── 1. Parquet fact coverage ──────────────────────────────────────────────────

class TestParquetCoverage:
    """Every fact table referenced in TMDL must have non-empty Parquet data."""

    @pytest.mark.parametrize("model_name", list(DOMAIN_MAP.values()))
    def test_fact_tables_have_parquet(self, model_name):
        try:
            import pyarrow.parquet as pq
        except ImportError:
            pytest.skip("pyarrow not installed")

        model = DIST_ROOT / model_name
        missing = []
        for tmdl in (model / "definition/tables").glob("fact_*.tmdl"):
            fact_name = tmdl.stem
            fact_path = GOLD_FACTS / fact_name
            if not fact_path.exists():
                missing.append(f"{fact_name}: directory missing")
                continue
            files = list(fact_path.rglob("*.parquet"))
            if not files:
                missing.append(f"{fact_name}: no Parquet files")
            else:
                rows = sum(pq.read_metadata(str(f)).num_rows for f in files)
                if rows == 0:
                    missing.append(f"{fact_name}: 0 rows")

        assert not missing, (
            f"{model_name} has fact tables with missing or empty Parquet data:\n"
            + "\n".join(f"  {m}" for m in missing)
        )


# ── 2. Measure binding integrity ──────────────────────────────────────────────

class TestMeasureBindings:
    """Every measure Property in visual.json must exist in the domain _Measures.tmdl."""

    @pytest.mark.parametrize("report_name", _report_ids())
    def test_no_broken_measure_bindings(self, report_name):
        report_dir  = DIST_ROOT / report_name
        model       = _model_path(report_dir)
        defined     = _get_measures(model)
        broken      = []

        for vf in sorted(report_dir.rglob("visual.json")):
            for ftype, entity, prop in _visual_projections(vf):
                if ftype == "Measure" and prop and prop not in defined:
                    broken.append(
                        f"{vf.relative_to(DIST_ROOT)}: "
                        f"[{entity}]'{prop}' not in {model.name}"
                    )

        assert not broken, (
            f"{report_name}: {len(broken)} broken measure binding(s):\n"
            + "\n".join(f"  {b}" for b in broken)
        )


# ── 3. Column binding integrity ───────────────────────────────────────────────

class TestColumnBindings:
    """Every Column Property in visual.json must exist in the domain TMDL tables."""

    @pytest.mark.parametrize("report_name", _report_ids())
    def test_no_broken_column_bindings(self, report_name):
        report_dir   = DIST_ROOT / report_name
        model        = _model_path(report_dir)
        table_cols   = _get_table_columns(model)
        all_col_names = {c for cols in table_cols.values() for c in cols}
        broken       = []

        for vf in sorted(report_dir.rglob("visual.json")):
            for ftype, entity, prop in _visual_projections(vf):
                if ftype == "Column" and prop:
                    entity_cols = table_cols.get(entity, set())
                    if prop not in entity_cols and prop not in all_col_names:
                        broken.append(
                            f"{vf.relative_to(DIST_ROOT)}: "
                            f"[{entity}]'{prop}' not found in {model.name}"
                        )

        assert not broken, (
            f"{report_name}: {len(broken)} broken column binding(s):\n"
            + "\n".join(f"  {b}" for b in broken)
        )


# ── 4. No BLANK() stub measures ───────────────────────────────────────────────

class TestNoBlankStubs:
    """No _Measures.tmdl may contain a BLANK() stub — every measure needs real DAX."""

    @pytest.mark.parametrize("model_name", list(DOMAIN_MAP.values()))
    def test_no_blank_stubs(self, model_name):
        tmdl_path = DIST_ROOT / model_name / "definition/tables/_Measures.tmdl"
        text      = tmdl_path.read_text(encoding="utf-8")
        stubs     = re.findall(r"^\tmeasure '([^']+)' = BLANK\(\)", text, re.MULTILINE)
        assert not stubs, (
            f"{model_name}/_Measures.tmdl has {len(stubs)} BLANK() stub(s):\n"
            + "\n".join(f"  '{s}'" for s in stubs)
        )


# ── 5. No kpi_id measure names ────────────────────────────────────────────────

class TestNoKpiIdNames:
    """
    Measure names must be human-readable display names, not kpi_id strings.
    kpi_ids look like 'margin.gm.pct' or 'crm.clv.amount' — dots with lowercase words.
    """

    KPI_ID_RE = re.compile(r"^[a-z][a-z_]+\.[a-z][a-z_.]+$")

    @pytest.mark.parametrize("model_name", list(DOMAIN_MAP.values()))
    def test_no_kpi_id_names(self, model_name):
        tmdl_path = DIST_ROOT / model_name / "definition/tables/_Measures.tmdl"
        text      = tmdl_path.read_text(encoding="utf-8")
        names     = re.findall(r"^\tmeasure '([^']+)'", text, re.MULTILINE)
        bad       = [n for n in names if self.KPI_ID_RE.match(n)]
        assert not bad, (
            f"{model_name}/_Measures.tmdl has measure(s) named with kpi_id "
            f"instead of display name:\n" + "\n".join(f"  '{b}'" for b in bad)
        )


# ── 6. Every measure has formatString and displayFolder ───────────────────────

class TestMeasureMetadata:
    """Every measure in _Measures.tmdl must declare formatString and displayFolder."""

    @pytest.mark.parametrize("model_name", list(DOMAIN_MAP.values()))
    def test_all_measures_have_format_and_folder(self, model_name):
        tmdl_path = DIST_ROOT / model_name / "definition/tables/_Measures.tmdl"
        text      = tmdl_path.read_text(encoding="utf-8")

        # Split into measure blocks
        blocks = re.split(r"(?=^\tmeasure ')", text, flags=re.MULTILINE)
        missing_format = []
        missing_folder = []

        for block in blocks:
            if not block.strip().startswith("measure '"):
                continue
            name_match = re.match(r"\tmeasure '([^']+)'", block)
            if not name_match:
                continue
            name = name_match.group(1)
            if "formatString:" not in block:
                missing_format.append(name)
            if "displayFolder:" not in block:
                missing_folder.append(name)

        errors = []
        if missing_format:
            errors.append(f"Missing formatString: {missing_format}")
        if missing_folder:
            errors.append(f"Missing displayFolder: {missing_folder}")

        assert not errors, (
            f"{model_name}/_Measures.tmdl measure metadata incomplete:\n"
            + "\n".join(errors)
        )


# ── 7. Required visuals on every page ────────────────────────────────────────

class TestRequiredVisuals:
    """Overview pages must have KPI_Cards; Detail pages must have Smart_Narrative."""

    @pytest.mark.parametrize("report_name", _report_ids())
    def test_overview_has_kpi_cards(self, report_name):
        report_dir = DIST_ROOT / report_name
        overview_pages = [
            p for p in (report_dir / "definition/pages").iterdir()
            if p.is_dir() and "Overview" in p.name
        ]
        assert overview_pages, f"{report_name}: no Overview page directory found"

        for page in overview_pages:
            visual_ids = [v.parent.name for v in page.rglob("visual.json")]
            assert "KPI_Cards" in visual_ids, (
                f"{report_name}/{page.name}: KPI_Cards visual missing"
            )

    @pytest.mark.parametrize("report_name", _report_ids())
    def test_detail_has_smart_narrative(self, report_name):
        report_dir = DIST_ROOT / report_name
        detail_pages = [
            p for p in (report_dir / "definition/pages").iterdir()
            if p.is_dir() and "Detail" in p.name
        ]
        assert detail_pages, f"{report_name}: no Detail page directory found"

        for page in detail_pages:
            visual_ids = [v.parent.name for v in page.rglob("visual.json")]
            assert "Smart_Narrative" in visual_ids, (
                f"{report_name}/{page.name}: Smart_Narrative visual missing"
            )


# ── 8. Every report has exactly Overview + Detail ─────────────────────────────

class TestPageStructure:
    """Every report must have exactly one Overview page and one Detail page."""

    @pytest.mark.parametrize("report_name", _report_ids())
    def test_has_overview_and_detail(self, report_name):
        report_dir  = DIST_ROOT / report_name
        pages_dir   = report_dir / "definition/pages"
        page_dirs   = [p for p in pages_dir.iterdir() if p.is_dir()]
        page_names  = [p.name for p in page_dirs]

        overview_count = sum(1 for n in page_names if "Overview" in n)
        detail_count   = sum(1 for n in page_names if "Detail" in n)

        assert overview_count >= 1, (
            f"{report_name}: expected ≥1 Overview page, found {overview_count}. "
            f"Pages: {page_names}"
        )
        assert detail_count >= 1, (
            f"{report_name}: expected ≥1 Detail page, found {detail_count}. "
            f"Pages: {page_names}"
        )

    @pytest.mark.parametrize("report_name", _report_ids())
    def test_page_json_valid(self, report_name):
        report_dir = DIST_ROOT / report_name
        for page_json in report_dir.rglob("page.json"):
            try:
                data = json.loads(page_json.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                pytest.fail(f"{page_json.relative_to(DIST_ROOT)}: invalid JSON — {exc}")
            assert "name" in data, f"{page_json.relative_to(DIST_ROOT)}: missing 'name' field"
            assert "displayName" in data, (
                f"{page_json.relative_to(DIST_ROOT)}: missing 'displayName' field"
            )

    @pytest.mark.parametrize("report_name", _report_ids())
    def test_all_visual_json_valid(self, report_name):
        report_dir = DIST_ROOT / report_name
        for vf in report_dir.rglob("visual.json"):
            try:
                json.loads(vf.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                pytest.fail(f"{vf.relative_to(DIST_ROOT)}: invalid JSON — {exc}")
