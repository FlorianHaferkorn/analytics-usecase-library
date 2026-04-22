"""Tests for tooling/validation/check_catalog_tmdl_drift.py.

Covers:
  - parse_catalog extracts measure_name correctly
  - parse_tmdl_measures parses measure names (excludes Action_*)
  - _strip_suffix / _has_suffix helpers
  - duplicate un-suffixed detection (cross-domain)
  - catalog coverage check (errors vs warnings)
  - planned.yaml schema validation
  - full integration: --strict returns 0 against the real repo
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import textwrap
from pathlib import Path

import pytest
import yaml

# Make the validation module importable
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "tooling" / "validation"))

from check_catalog_tmdl_drift import (
    _has_suffix,
    _strip_suffix,
    check_catalog_coverage,
    check_duplicate_unsuffixed,
    parse_catalog,
    parse_planned,
    parse_tmdl_measures,
    main,
)


# ---------------------------------------------------------------------------
# Unit tests — helpers
# ---------------------------------------------------------------------------


def test_strip_suffix_removes_parenthetical():
    assert _strip_suffix("Action Outcome Rate % (XD Log)") == "Action Outcome Rate %"
    assert _strip_suffix("NPS Index (Service)") == "NPS Index"
    assert _strip_suffix("DSO Days (XD)") == "DSO Days"


def test_strip_suffix_unchanged_when_no_suffix():
    assert _strip_suffix("Net Sales Amount") == "Net Sales Amount"
    assert _strip_suffix("OTIF %") == "OTIF %"


def test_has_suffix_true():
    assert _has_suffix("NPS Index (Customer)") is True
    assert _has_suffix("Sales Units (Ops)") is True


def test_has_suffix_false():
    assert _has_suffix("NPS Index") is False
    assert _has_suffix("Net Sales Amount") is False


# ---------------------------------------------------------------------------
# Unit tests — parse_catalog
# ---------------------------------------------------------------------------


def test_parse_catalog_extracts_measure_names(tmp_path):
    catalog = tmp_path / "KPI_Catalog.md"
    catalog.write_text(
        textwrap.dedent(
            """\
            - kpi_id: foo.bar.pct
              kpi_key: Foo Bar
              technical:
                measure_name: "Foo Bar %"

            - kpi_id: baz.qux.count
              kpi_key: Baz Qux
              technical:
                measure_name: "Baz Qux Count"

            - kpi_id: no.measure.here
              kpi_key: No Measure
            """
        ),
        encoding="utf-8",
    )
    result = parse_catalog(str(catalog))
    assert result == {
        "foo.bar.pct": "Foo Bar %",
        "baz.qux.count": "Baz Qux Count",
    }


# ---------------------------------------------------------------------------
# Unit tests — parse_tmdl_measures
# ---------------------------------------------------------------------------


def test_parse_tmdl_measures_excludes_action_measures(tmp_path):
    tmdl = tmp_path / "_Measures.tmdl"
    tmdl.write_text(
        textwrap.dedent(
            """\
            table _Measures
            \tmeasure 'Net Sales Amount' = SUM ( fact_sales[Net Sales Amount] )
            \t\tformatString: "#,0.00"
            \tmeasure 'Action_C-C3.1_Text' = "some action"
            \t\tisHidden
            \tmeasure 'NPS Index (Service)' = 42
            \t\tformatString: "#,0"
            """
        ),
        encoding="utf-8",
    )
    result = parse_tmdl_measures([str(tmdl)])
    names = result[str(tmdl)]
    assert "Net Sales Amount" in names
    assert "NPS Index (Service)" in names
    assert "Action_C-C3.1_Text" not in names


# ---------------------------------------------------------------------------
# Unit tests — duplicate detection
# ---------------------------------------------------------------------------


def test_duplicate_detection_fires_for_cross_domain(tmp_path):
    # Two files in different SemanticModel directories with same unsuffixed name
    m1_dir = tmp_path / "Finance.SemanticModel" / "definition" / "tables"
    m2_dir = tmp_path / "Experience.SemanticModel" / "definition" / "tables"
    m1_dir.mkdir(parents=True)
    m2_dir.mkdir(parents=True)

    for d in (m1_dir, m2_dir):
        (d / "_Measures.tmdl").write_text(
            "\tmeasure 'DSO Days' = 1\n", encoding="utf-8"
        )

    tmdl_by_file = parse_tmdl_measures(
        [str(m1_dir / "_Measures.tmdl"), str(m2_dir / "_Measures.tmdl")]
    )
    errors = check_duplicate_unsuffixed(tmdl_by_file)
    assert any("DSO Days" in e for e in errors)


def test_duplicate_detection_skips_suffixed(tmp_path):
    m1_dir = tmp_path / "Finance.SemanticModel" / "definition" / "tables"
    m2_dir = tmp_path / "Experience.SemanticModel" / "definition" / "tables"
    m1_dir.mkdir(parents=True)
    m2_dir.mkdir(parents=True)

    (m1_dir / "_Measures.tmdl").write_text(
        "\tmeasure 'DSO Days' = 1\n", encoding="utf-8"
    )
    (m2_dir / "_Measures.tmdl").write_text(
        "\tmeasure 'DSO Days (XD)' = 1\n", encoding="utf-8"
    )

    tmdl_by_file = parse_tmdl_measures(
        [str(m1_dir / "_Measures.tmdl"), str(m2_dir / "_Measures.tmdl")]
    )
    errors = check_duplicate_unsuffixed(tmdl_by_file)
    assert not errors


def test_duplicate_detection_ignores_same_model_mirrored(tmp_path):
    # dist/ and showcases/ copies of same model — same SemanticModel name
    d1 = tmp_path / "dist" / "Ops.SemanticModel" / "definition" / "tables"
    d2 = tmp_path / "showcases" / "Ops.SemanticModel" / "definition" / "tables"
    for d in (d1, d2):
        d.mkdir(parents=True)
        (d / "_Measures.tmdl").write_text(
            "\tmeasure 'OEE %' = 1\n", encoding="utf-8"
        )

    tmdl_by_file = parse_tmdl_measures(
        [str(d1 / "_Measures.tmdl"), str(d2 / "_Measures.tmdl")]
    )
    errors = check_duplicate_unsuffixed(tmdl_by_file)
    assert not errors


# ---------------------------------------------------------------------------
# Unit tests — catalog coverage
# ---------------------------------------------------------------------------


def test_catalog_coverage_missing_is_error(tmp_path):
    catalog = {"my.kpi": "My KPI Measure"}
    tmdl_by_file = {}  # no TMDL files
    planned = {}
    errors, warnings = check_catalog_coverage(catalog, tmdl_by_file, planned, strict=True)
    assert any("My KPI Measure" in e for e in errors)
    assert not warnings


def test_catalog_coverage_planned_is_warning(tmp_path):
    catalog = {"my.kpi": "My KPI Measure"}
    tmdl_by_file = {}
    planned = {
        "my.kpi": {
            "kpi_id": "my.kpi",
            "owner": "team",
            "eta_date": "2026-12-31",
            "reason": "not yet",
        }
    }
    errors, warnings = check_catalog_coverage(catalog, tmdl_by_file, planned, strict=False)
    assert not errors
    assert any("My KPI Measure" in w for w in warnings)


def test_catalog_coverage_suffixed_proxy_satisfies_base(tmp_path):
    catalog = {"my.kpi": "Action Outcome Rate %"}
    m1_dir = tmp_path / "Experience.SemanticModel" / "definition" / "tables"
    m1_dir.mkdir(parents=True)
    (m1_dir / "_Measures.tmdl").write_text(
        "\tmeasure 'Action Outcome Rate % (XD Log)' = 1\n", encoding="utf-8"
    )
    tmdl_by_file = parse_tmdl_measures([str(m1_dir / "_Measures.tmdl")])
    errors, warnings = check_catalog_coverage(catalog, tmdl_by_file, {}, strict=True)
    # Suffixed proxy should satisfy the base catalog entry
    assert not errors
    assert not warnings


# ---------------------------------------------------------------------------
# Unit tests — planned.yaml schema
# ---------------------------------------------------------------------------


def test_planned_kpi_schema_is_valid_json():
    schema_path = (
        _REPO_ROOT / "tooling" / "generator" / "schemas" / "planned_kpi.schema.json"
    )
    assert schema_path.exists(), f"Schema file missing: {schema_path}"
    with open(schema_path, encoding="utf-8") as f:
        data = json.load(f)
    assert data.get("type") == "array"
    assert "items" in data


def test_planned_yaml_validates_against_schema():
    """Every entry in planned.yaml must conform to planned_kpi.schema.json."""
    planned_path = _REPO_ROOT / "core" / "kpi_catalog" / "planned.yaml"
    schema_path = (
        _REPO_ROOT / "tooling" / "generator" / "schemas" / "planned_kpi.schema.json"
    )
    assert planned_path.exists(), "planned.yaml does not exist"
    with open(planned_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)

    try:
        import jsonschema
        jsonschema.validate(instance=data, schema=schema)
    except ImportError:
        pytest.skip("jsonschema not installed; skipping schema validation")


def test_planned_yaml_kpi_ids_in_catalog():
    """All kpi_ids in planned.yaml must exist in KPI_Catalog.md."""
    planned_path = _REPO_ROOT / "core" / "kpi_catalog" / "planned.yaml"
    catalog_path = _REPO_ROOT / "core" / "kpi_catalog" / "KPI_Catalog.md"
    with open(planned_path, encoding="utf-8") as f:
        planned_data = yaml.safe_load(f)
    catalog = parse_catalog(str(catalog_path))
    for entry in planned_data:
        kpi_id = entry["kpi_id"]
        assert kpi_id in catalog, f"planned.yaml kpi_id '{kpi_id}' not found in KPI_Catalog.md"


# ---------------------------------------------------------------------------
# Integration test — full repo drift check
# ---------------------------------------------------------------------------


def test_catalog_drift_strict_passes_on_real_repo():
    """Run check_catalog_tmdl_drift.py --strict against the actual repository.
    This is the acceptance-criteria gate: must return exit code 0.
    """
    result = main(["--strict", "--repo-root", str(_REPO_ROOT)])
    assert result == 0, (
        "check_catalog_tmdl_drift.py --strict returned non-zero; "
        "see output above for details."
    )


def test_nps_measure_names_are_distinct():
    """crm.nps.index and svc.nps.index must have different, non-empty measure_name."""
    catalog_path = _REPO_ROOT / "core" / "kpi_catalog" / "KPI_Catalog.md"
    catalog = parse_catalog(str(catalog_path))
    crm_name = catalog.get("crm.nps.index", "")
    svc_name = catalog.get("svc.nps.index", "")
    assert crm_name, "crm.nps.index has empty measure_name"
    assert svc_name, "svc.nps.index has empty measure_name"
    assert crm_name != svc_name, (
        f"crm.nps.index and svc.nps.index have identical measure_name: '{crm_name}'"
    )


def test_action_outcome_rate_not_duplicated():
    """Un-suffixed 'Action Outcome Rate %' must appear in at most one _Measures.tmdl."""
    import re, glob

    pattern = str(_REPO_ROOT / "products" / "**" / "_Measures.tmdl")
    tmdl_files = [
        p for p in glob.glob(pattern, recursive=True)
        if ".cursor" not in p and "publish_staging" not in p
    ]

    unsuffixed_files = []
    for path in tmdl_files:
        with open(path, encoding="utf-8") as f:
            for line in f:
                m = re.match(r"\s*measure '(Action Outcome Rate %)'", line)
                if m:
                    unsuffixed_files.append(path)
    assert len(unsuffixed_files) <= 1, (
        f"Un-suffixed 'Action Outcome Rate %' found in multiple files: {unsuffixed_files}"
    )
