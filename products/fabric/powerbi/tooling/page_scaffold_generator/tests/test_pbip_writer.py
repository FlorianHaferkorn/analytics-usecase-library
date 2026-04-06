"""
Tests for PBIPWriter

Covers:
- byPath and byConnection reference modes in definition.pbir
- All required files are written (version.json, pages.json, report.json, visual.json)
- Golden file snapshot regression: generated report matches committed fixture

Run with: python -m pytest tests/test_pbip_writer.py -v
"""

import json
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from pbip_writer import PBIPWriter

FIXTURES = Path(__file__).parent / "fixtures" / "golden" / "COM-001_Sales_Performance.Report"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# definition.pbir — byPath mode
# ---------------------------------------------------------------------------

class TestDefinitionPbirByPath:
    def test_bypath_creates_file(self, tmp_path):
        writer = PBIPWriter(tmp_path / "TestReport.Report")
        writer.create_pbip_structure()
        writer.write_report_json(
            dataset_reference_path="../Commercial.SemanticModel",
            connection_type="byPath",
        )
        pbir_file = tmp_path / "TestReport.Report" / "definition.pbir"
        assert pbir_file.exists(), "definition.pbir must be created"

    def test_bypath_schema(self, tmp_path):
        writer = PBIPWriter(tmp_path / "TestReport.Report")
        writer.create_pbip_structure()
        writer.write_report_json(
            dataset_reference_path="../Commercial.SemanticModel",
            connection_type="byPath",
        )
        data = load_json(tmp_path / "TestReport.Report" / "definition.pbir")
        assert "definitionProperties" in data["$schema"]
        assert data["version"] == "4.0"

    def test_bypath_reference_path(self, tmp_path):
        writer = PBIPWriter(tmp_path / "TestReport.Report")
        writer.create_pbip_structure()
        writer.write_report_json(
            dataset_reference_path="../Commercial.SemanticModel",
            connection_type="byPath",
        )
        data = load_json(tmp_path / "TestReport.Report" / "definition.pbir")
        ref = data["datasetReference"]["byPath"]["path"]
        assert ref == "../Commercial.SemanticModel"

    def test_bypath_no_byconnection_key(self, tmp_path):
        writer = PBIPWriter(tmp_path / "TestReport.Report")
        writer.create_pbip_structure()
        writer.write_report_json(
            dataset_reference_path="../Commercial.SemanticModel",
            connection_type="byPath",
        )
        data = load_json(tmp_path / "TestReport.Report" / "definition.pbir")
        assert "byConnection" not in data.get("datasetReference", {})

    def test_bypath_backslashes_normalised(self, tmp_path):
        """Windows-style backslash paths must be normalised to forward slashes."""
        writer = PBIPWriter(tmp_path / "TestReport.Report")
        writer.create_pbip_structure()
        writer.write_report_json(
            dataset_reference_path="..\\Commercial.SemanticModel",
            connection_type="byPath",
        )
        data = load_json(tmp_path / "TestReport.Report" / "definition.pbir")
        ref = data["datasetReference"]["byPath"]["path"]
        assert "\\" not in ref, "Backslashes must be normalised to forward slashes"
        assert ref == "../Commercial.SemanticModel"

    def test_bypath_empty_path_omits_datasetreference(self, tmp_path):
        """Empty path must not produce a broken byPath entry."""
        writer = PBIPWriter(tmp_path / "TestReport.Report")
        writer.create_pbip_structure()
        writer.write_report_json(
            dataset_reference_path="",
            connection_type="byPath",
        )
        data = load_json(tmp_path / "TestReport.Report" / "definition.pbir")
        # No path → no datasetReference
        assert "datasetReference" not in data


# ---------------------------------------------------------------------------
# definition.pbir — byConnection mode
# ---------------------------------------------------------------------------

SAMPLE_DATASET_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


class TestDefinitionPbirByConnection:
    def test_byconnection_creates_file(self, tmp_path):
        writer = PBIPWriter(tmp_path / "TestReport.Report")
        writer.create_pbip_structure()
        writer.write_report_json(
            connection_type="byConnection",
            dataset_id=SAMPLE_DATASET_ID,
        )
        assert (tmp_path / "TestReport.Report" / "definition.pbir").exists()

    def test_byconnection_has_correct_keys(self, tmp_path):
        writer = PBIPWriter(tmp_path / "TestReport.Report")
        writer.create_pbip_structure()
        writer.write_report_json(
            connection_type="byConnection",
            dataset_id=SAMPLE_DATASET_ID,
        )
        data = load_json(tmp_path / "TestReport.Report" / "definition.pbir")
        conn = data["datasetReference"]["byConnection"]
        assert conn["pbiModelDatabaseName"] == SAMPLE_DATASET_ID
        assert conn["connectionType"] == "pbiServiceXmlaStyleLive"
        assert conn["pbiModelVirtualServerName"] == "sobe_wowvirtualserver"
        assert conn["name"] == "EntityDataSource"

    def test_byconnection_no_bypath_key(self, tmp_path):
        writer = PBIPWriter(tmp_path / "TestReport.Report")
        writer.create_pbip_structure()
        writer.write_report_json(
            connection_type="byConnection",
            dataset_id=SAMPLE_DATASET_ID,
        )
        data = load_json(tmp_path / "TestReport.Report" / "definition.pbir")
        assert "byPath" not in data.get("datasetReference", {})


# ---------------------------------------------------------------------------
# report.json
# ---------------------------------------------------------------------------

class TestReportJson:
    def test_report_json_schema(self, tmp_path):
        writer = PBIPWriter(tmp_path / "R.Report")
        writer.create_pbip_structure()
        writer.write_report_json()
        data = load_json(tmp_path / "R.Report" / "definition" / "report.json")
        assert "report/definition/report" in data["$schema"]

    def test_report_json_has_required_sections(self, tmp_path):
        writer = PBIPWriter(tmp_path / "R.Report")
        writer.create_pbip_structure()
        writer.write_report_json()
        data = load_json(tmp_path / "R.Report" / "definition" / "report.json")
        assert "themeCollection" in data
        assert "settings" in data
        assert "filterConfig" in data

    def test_report_json_no_dataset_reference(self, tmp_path):
        """datasetReference must NOT appear in report.json — it belongs in definition.pbir only."""
        writer = PBIPWriter(tmp_path / "R.Report")
        writer.create_pbip_structure()
        writer.write_report_json(
            dataset_reference_path="../Foo.SemanticModel",
            connection_type="byPath",
        )
        data = load_json(tmp_path / "R.Report" / "definition" / "report.json")
        assert "datasetReference" not in data


# ---------------------------------------------------------------------------
# version.json
# ---------------------------------------------------------------------------

class TestVersionJson:
    def test_version_json_written(self, tmp_path):
        writer = PBIPWriter(tmp_path / "R.Report")
        writer.create_pbip_structure()
        writer.write_version_json()
        vf = tmp_path / "R.Report" / "definition" / "version.json"
        assert vf.exists()

    def test_version_json_schema_and_version(self, tmp_path):
        writer = PBIPWriter(tmp_path / "R.Report")
        writer.create_pbip_structure()
        writer.write_version_json()
        data = load_json(tmp_path / "R.Report" / "definition" / "version.json")
        assert "versionMetadata" in data["$schema"]
        assert data["version"] == "2.0.0"


# ---------------------------------------------------------------------------
# .pbip file
# ---------------------------------------------------------------------------

class TestPbipFile:
    def test_pbip_file_written_with_speaking_name(self, tmp_path):
        writer = PBIPWriter(tmp_path / "COM-001_Sales_Performance.Report")
        writer.create_pbip_structure()
        writer.write_pbip_file()
        pbip = tmp_path / "COM-001_Sales_Performance.Report" / "COM-001_Sales_Performance.pbip"
        assert pbip.exists(), "Speaking-name .pbip file must exist"

    def test_pbip_schema_is_pbip_properties(self, tmp_path):
        writer = PBIPWriter(tmp_path / "COM-001_Sales_Performance.Report")
        writer.create_pbip_structure()
        writer.write_pbip_file()
        data = load_json(tmp_path / "COM-001_Sales_Performance.Report" / "COM-001_Sales_Performance.pbip")
        assert "pbipProperties" in data["$schema"], "Must use pbipProperties schema (not itemShortcut)"

    def test_pbip_artifact_path_is_dot(self, tmp_path):
        writer = PBIPWriter(tmp_path / "COM-001_Sales_Performance.Report")
        writer.create_pbip_structure()
        writer.write_pbip_file()
        data = load_json(tmp_path / "COM-001_Sales_Performance.Report" / "COM-001_Sales_Performance.pbip")
        assert data["artifacts"][0]["report"]["path"] == "."

    def test_legacy_report_pbip_removed(self, tmp_path):
        """Legacy Report.pbip must be cleaned up when speaking-name file is written."""
        report_dir = tmp_path / "COM-001_Sales_Performance.Report"
        report_dir.mkdir(parents=True)
        # Simulate legacy file
        legacy = report_dir / "Report.pbip"
        legacy.write_text("{}")
        writer = PBIPWriter(report_dir)
        writer.create_pbip_structure()
        writer.write_pbip_file()
        assert not legacy.exists(), "Legacy Report.pbip must be removed"


# ---------------------------------------------------------------------------
# pages.json
# ---------------------------------------------------------------------------

class TestPagesJson:
    def test_pages_json_written(self, tmp_path):
        writer = PBIPWriter(tmp_path / "R.Report")
        writer.create_pbip_structure()
        writer.write_pages_json(["Page_OV", "Page_DT"])
        pf = tmp_path / "R.Report" / "definition" / "pages" / "pages.json"
        assert pf.exists()

    def test_pages_json_schema(self, tmp_path):
        writer = PBIPWriter(tmp_path / "R.Report")
        writer.create_pbip_structure()
        writer.write_pages_json(["Page_OV", "Page_DT"])
        data = load_json(tmp_path / "R.Report" / "definition" / "pages" / "pages.json")
        assert "pagesMetadata" in data["$schema"]

    def test_pages_json_active_page_default(self, tmp_path):
        writer = PBIPWriter(tmp_path / "R.Report")
        writer.create_pbip_structure()
        writer.write_pages_json(["Page_OV", "Page_DT"])
        data = load_json(tmp_path / "R.Report" / "definition" / "pages" / "pages.json")
        assert data["activePageName"] == "Page_OV"

    def test_pages_json_append_preserves_active(self, tmp_path):
        """Appending pages must not change the existing active page."""
        writer = PBIPWriter(tmp_path / "R.Report")
        writer.create_pbip_structure()
        writer.write_pages_json(["Page_OV"])
        writer.write_pages_json(["Page_DT"], append=True)
        data = load_json(tmp_path / "R.Report" / "definition" / "pages" / "pages.json")
        assert data["activePageName"] == "Page_OV", "Active page must remain Overview after append"
        assert "Page_DT" in data["pageOrder"]
        assert "Page_OV" in data["pageOrder"]

    def test_pages_json_append_no_duplicates(self, tmp_path):
        writer = PBIPWriter(tmp_path / "R.Report")
        writer.create_pbip_structure()
        writer.write_pages_json(["Page_OV"])
        writer.write_pages_json(["Page_OV", "Page_DT"], append=True)
        data = load_json(tmp_path / "R.Report" / "definition" / "pages" / "pages.json")
        assert data["pageOrder"].count("Page_OV") == 1, "Appending must not create duplicates"


# ---------------------------------------------------------------------------
# Golden file regression — COM-001
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not FIXTURES.exists(), reason="Golden fixtures not committed")
class TestGoldenCOM001:
    """
    Compare every JSON/PBIR file in the committed COM-001 fixture against the
    live dist/ output.  Fails if any file deviates — catches unintentional
    generator changes.
    """

    DIST_REPORT = (
        Path(__file__).resolve().parents[6]
        / "products/fabric/powerbi/dist/COM-001_Sales_Performance.Report"
    )

    def _fixture_files(self):
        return sorted(FIXTURES.rglob("*.json")) + sorted(FIXTURES.rglob("*.pbir")) + sorted(FIXTURES.rglob("*.pbip"))

    def test_fixture_files_exist_in_dist(self):
        for fixture_file in self._fixture_files():
            rel = fixture_file.relative_to(FIXTURES)
            dist_file = self.DIST_REPORT / rel
            assert dist_file.exists(), f"File exists in fixture but missing from dist: {rel}"

    def test_no_extra_files_in_dist(self):
        dist_files = set()
        for ext in ("*.json", "*.pbir", "*.pbip"):
            for f in self.DIST_REPORT.rglob(ext):
                rel = f.relative_to(self.DIST_REPORT)
                if "StaticResources" not in str(rel):
                    dist_files.add(str(rel))

        fixture_files = set()
        for ext in ("*.json", "*.pbir", "*.pbip"):
            for f in FIXTURES.rglob(ext):
                fixture_files.add(str(f.relative_to(FIXTURES)))

        extra = dist_files - fixture_files
        assert not extra, f"New files in dist not in golden fixture (add them): {extra}"

    def test_json_content_matches_fixture(self):
        mismatches = []
        for fixture_file in self._fixture_files():
            rel = fixture_file.relative_to(FIXTURES)
            dist_file = self.DIST_REPORT / rel
            if not dist_file.exists():
                continue
            fixture_data = json.loads(fixture_file.read_text(encoding="utf-8"))
            dist_data = json.loads(dist_file.read_text(encoding="utf-8"))
            if fixture_data != dist_data:
                mismatches.append(str(rel))
        assert not mismatches, (
            f"These files differ from golden fixture — either update the fixture "
            f"(if intentional) or revert the change:\n  " + "\n  ".join(mismatches)
        )

    def test_definition_pbir_bypath_is_correct(self):
        """Critical: byPath must resolve to sibling Commercial.SemanticModel."""
        data = load_json(self.DIST_REPORT / "definition.pbir")
        path = data["datasetReference"]["byPath"]["path"]
        assert path == "../Commercial.SemanticModel", (
            f"definition.pbir byPath must be '../Commercial.SemanticModel', got '{path}'"
        )

    def test_definition_pbir_version(self):
        data = load_json(self.DIST_REPORT / "definition.pbir")
        assert data["version"] == "4.0"

    def test_pages_json_has_two_pages(self):
        data = load_json(self.DIST_REPORT / "definition" / "pages" / "pages.json")
        assert len(data["pageOrder"]) == 2, "COM-001 must have exactly 2 pages (Overview + Detail)"

    def test_active_page_is_overview(self):
        data = load_json(self.DIST_REPORT / "definition" / "pages" / "pages.json")
        assert "Overview" in data["activePageName"], "Active page must be Overview"
