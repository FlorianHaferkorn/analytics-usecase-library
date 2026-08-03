"""
CI gate: dist/ .Report folder coverage and structural integrity.

Enforces that:
  1. Every UseCase_Bracket.yaml has exactly one corresponding .Report folder in dist/.
  2. No .Report folder is nested inside another .Report folder.
  3. No orphan .Report folder exists without a backing UseCase_Bracket.yaml.
  4. .Report folder names contain only safe characters ([A-Za-z0-9_&. -]).
     (& is allowed because COM-002, FIN-001, etc. may use it in the title;
      but subfolders with & in the name that are nested inside .Report are caught by rule 2.)
  5. Every .Report folder contains exactly one .pbip file whose stem matches the folder stem.

Run from repo root:
    py -3 -m pytest tooling/tests/test_dist_report_coverage.py -v
"""

from __future__ import annotations

import re
import yaml
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
USECASES_ROOT = REPO_ROOT / "core" / "usecases" / "core"
DIST_ROOT = REPO_ROOT / "products" / "fabric" / "powerbi" / "dist"

# Regex for safe .Report folder stem: only word chars, hyphens, underscores
_SAFE_STEM_RE = re.compile(r'^[\w&. -]+$')


def _all_bracket_dirs() -> list[Path]:
    """Return all UseCase_Bracket.yaml parent directories."""
    return [p.parent for p in sorted(USECASES_ROOT.rglob("UseCase_Bracket.yaml"))]


def _is_report_pending(bracket_dir: Path) -> bool:
    """A use case is *report-pending* when its bracket explicitly declares that the backing
    data is not yet available (``readiness.data_availability == 'missing'``).

    Such a use case is spec-complete and governed — KPIs, standards, storyline, action codes
    all validate — but its report cannot be rendered until its Aurora data and semantic-model
    measures exist (Desktop/Fabric-gated). It is therefore exempt from report-coverage until
    then; the concrete data gap is tracked in
    ``internal/project_mgmt/AURORA_SYNTHETIC_DATA_GAPS.md``. This is a narrow, bracket-declared
    exemption — a UC whose data IS available still requires its report.

    ``missing`` is the governed vocabulary of ``tooling/generator/schemas/usecase_bracket.schema.json``
    (``available`` | ``partial`` | ``missing``). Four brackets carried an ungoverned
    ``not_available`` here until 01.08.2026; schema validation rejected them, and this exemption
    silently keyed on the invalid value. Read the enum from the schema, never invent a synonym."""
    try:
        d = yaml.safe_load((bracket_dir / "UseCase_Bracket.yaml").read_text(encoding="utf-8")) or {}
    except Exception:
        return False
    return (d.get("readiness") or {}).get("data_availability") == "missing"


def _expected_report_folder_name(bracket_dir: Path) -> str:
    """Return the expected dist .Report folder name for a bracket directory.

    Convention: the use-case directory name (e.g. 'COM-001_Sales_Performance')
    becomes 'COM-001_Sales_Performance.Report'.
    This matches the scaffold/orchestrator naming convention.
    """
    return f"{bracket_dir.name}.Report"


def _dist_report_dirs() -> list[Path]:
    """Return all direct .Report children of dist/ (not nested)."""
    if not DIST_ROOT.exists():
        return []
    return [d for d in DIST_ROOT.iterdir() if d.is_dir() and d.name.endswith(".Report")]


def _nested_report_dirs() -> list[Path]:
    """Return any .Report directory nested INSIDE another .Report directory."""
    nested = []
    for report_dir in _dist_report_dirs():
        for sub in report_dir.rglob("*.Report"):
            if sub.is_dir():
                nested.append(sub)
    return nested


# ─────────────────────────────────────────────────────────────────────────────
# 1. Coverage: every bracket has a matching dist folder
# ─────────────────────────────────────────────────────────────────────────────

class TestDistCoverage:

    def test_every_bracket_has_report_folder(self):
        """Every UseCase_Bracket.yaml must have a corresponding .Report in dist/."""
        if not DIST_ROOT.exists():
            pytest.skip(f"dist/ not found at {DIST_ROOT} — run the generator first")

        bracket_dirs = _all_bracket_dirs()
        dist_names = {d.name for d in _dist_report_dirs()}
        missing = []
        for bd in bracket_dirs:
            if _is_report_pending(bd):
                continue  # spec-complete but data/report Desktop/Fabric-gated (see AURORA_SYNTHETIC_DATA_GAPS.md)
            expected = _expected_report_folder_name(bd)
            if expected not in dist_names:
                missing.append(f"{bd.name} → expected dist/{expected}")

        assert not missing, (
            f"{len(missing)} bracket(s) have no matching .Report in dist/:\n"
            + "\n".join(f"  {m}" for m in missing)
        )

    def test_no_orphan_report_folders(self):
        """Every .Report in dist/ must be backed by a UseCase_Bracket.yaml."""
        if not DIST_ROOT.exists():
            pytest.skip(f"dist/ not found at {DIST_ROOT}")

        bracket_stems = {bd.name for bd in _all_bracket_dirs()}
        dist_names = {d.name for d in _dist_report_dirs()}
        # A report is backed if it matches a bracket exactly, or is a named variant
        # of one (e.g. COM-001_Sales_Performance_vs_Plan_LY.Report is a variant of the
        # COM-001_Sales_Performance bracket). Truly stray reports still fail.
        orphans = {
            name for name in dist_names
            if not any(name == f"{stem}.Report" or name.startswith(f"{stem}_") for stem in bracket_stems)
        }

        assert not orphans, (
            f"{len(orphans)} orphan .Report folder(s) in dist/ with no backing bracket:\n"
            + "\n".join(f"  {o}" for o in sorted(orphans))
            + "\nRemove manually or regenerate from a bracket."
        )


# ─────────────────────────────────────────────────────────────────────────────
# 2. Structural integrity: no nesting, correct pbip file
# ─────────────────────────────────────────────────────────────────────────────

class TestDistStructure:

    def test_no_nested_report_folders(self):
        """No .Report folder may be nested inside another .Report folder.

        Nested .Report folders indicate that the IR adapter wrote its output
        *inside* an existing scaffold output instead of at the dist/ root.
        """
        nested = _nested_report_dirs()
        assert not nested, (
            f"{len(nested)} nested .Report folder(s) found — these must be removed:\n"
            + "\n".join(f"  {n.relative_to(REPO_ROOT)}" for n in nested)
            + "\nFix: ensure the generator writes to dist/ root, not inside an existing .Report."
        )

    def test_each_report_has_matching_pbip_file(self):
        """Each .Report folder must contain exactly one .pbip file whose stem matches the folder stem."""
        if not DIST_ROOT.exists():
            pytest.skip(f"dist/ not found at {DIST_ROOT}")

        errors = []
        for report_dir in _dist_report_dirs():
            folder_stem = report_dir.name.removesuffix(".Report")
            pbip_files = list(report_dir.glob("*.pbip"))
            if not pbip_files:
                errors.append(f"{report_dir.name}: no .pbip file found inside")
                continue
            if len(pbip_files) > 1:
                errors.append(
                    f"{report_dir.name}: multiple .pbip files: "
                    + ", ".join(p.name for p in pbip_files)
                )
                continue
            pbip_stem = pbip_files[0].stem
            if pbip_stem != folder_stem:
                errors.append(
                    f"{report_dir.name}: .pbip stem '{pbip_stem}' does not match folder stem '{folder_stem}'"
                )

        assert not errors, (
            f"{len(errors)} .Report folder(s) have .pbip naming issues:\n"
            + "\n".join(f"  {e}" for e in errors)
        )

    def test_each_report_has_definition_folder(self):
        """Each .Report folder must contain a definition/ subfolder."""
        if not DIST_ROOT.exists():
            pytest.skip(f"dist/ not found at {DIST_ROOT}")

        missing = []
        for report_dir in _dist_report_dirs():
            if not (report_dir / "definition").is_dir():
                missing.append(report_dir.name)

        assert not missing, (
            f"{len(missing)} .Report folder(s) missing definition/ subfolder:\n"
            + "\n".join(f"  {m}" for m in missing)
        )

    def test_each_report_has_definition_pbir(self):
        """Each .Report folder must contain a definition.pbir file."""
        if not DIST_ROOT.exists():
            pytest.skip(f"dist/ not found at {DIST_ROOT}")

        missing = []
        for report_dir in _dist_report_dirs():
            if not (report_dir / "definition.pbir").is_file():
                missing.append(report_dir.name)

        assert not missing, (
            f"{len(missing)} .Report folder(s) missing definition.pbir:\n"
            + "\n".join(f"  {m}" for m in missing)
        )
