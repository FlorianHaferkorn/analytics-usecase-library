"""
test_schema_registry.py — Unit tests for schema_registry.py and schema_manifest.json.

Ensures:
  - All schema URLs are well-formed Microsoft Fabric URLs.
  - Version segments can be extracted.
  - schema_manifest.json exists and is in sync with the registry.
  - Cached schema $id values match the registry.
  - update_schema_manifest.py --check-only passes (manifest is not stale).
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from products.fabric.powerbi.tooling.schema_registry import (
    REPORT_SCHEMA,
    PAGE_SCHEMA,
    VISUAL_SCHEMA,
    PAGES_METADATA_SCHEMA,
    VERSION_METADATA_SCHEMA,
    PBIP_SCHEMA,
    DEFINITION_PBIR_SCHEMA,
    SEMANTIC_MODEL_SCHEMA,
    PLATFORM_PROPERTIES_SCHEMA,
    THEME_SCHEMA_PINNED_VERSION,
    THEME_SCHEMA_URL,
    all_schemas,
    visual_schema_version,
    page_schema_version,
    report_schema_version,
)

_MANIFEST = REPO_ROOT / "tooling" / "schemas" / "pbir" / "schema_manifest.json"
_CACHED_SCHEMAS = {
    "visual": REPO_ROOT / "tooling" / "schemas" / "pbir" / "visual.schema.json",
    "page":   REPO_ROOT / "tooling" / "schemas" / "pbir" / "page.schema.json",
    "definition_pbir": REPO_ROOT / "tooling" / "schemas" / "pbir" / "definition.pbir.schema.json",
}

_FABRIC_BASE = "https://developer.microsoft.com/json-schemas/fabric"
_THEME_BASE  = "https://raw.githubusercontent.com/microsoft/powerbi-desktop-samples/main"


class TestRegistryURLs:
    """Schema URLs must be well-formed Microsoft Fabric JSON schema URLs."""

    @pytest.mark.parametrize("name,url", [
        ("report",           REPORT_SCHEMA),
        ("page",             PAGE_SCHEMA),
        ("visual",           VISUAL_SCHEMA),
        ("pages_metadata",   PAGES_METADATA_SCHEMA),
        ("version_metadata", VERSION_METADATA_SCHEMA),
        ("pbip",             PBIP_SCHEMA),
        ("definition_pbir",  DEFINITION_PBIR_SCHEMA),
        ("semantic_model",   SEMANTIC_MODEL_SCHEMA),
        ("platform",         PLATFORM_PROPERTIES_SCHEMA),
    ])
    def test_url_starts_with_fabric_base(self, name, url):
        assert url.startswith(_FABRIC_BASE), (
            f"{name}: expected URL starting with {_FABRIC_BASE}, got {url}"
        )

    @pytest.mark.parametrize("name,url", [
        ("report",           REPORT_SCHEMA),
        ("page",             PAGE_SCHEMA),
        ("visual",           VISUAL_SCHEMA),
        ("pages_metadata",   PAGES_METADATA_SCHEMA),
        ("version_metadata", VERSION_METADATA_SCHEMA),
        ("pbip",             PBIP_SCHEMA),
        ("definition_pbir",  DEFINITION_PBIR_SCHEMA),
        ("semantic_model",   SEMANTIC_MODEL_SCHEMA),
        ("platform",         PLATFORM_PROPERTIES_SCHEMA),
    ])
    def test_url_ends_with_schema_json(self, name, url):
        assert url.endswith("/schema.json"), (
            f"{name}: URL must end with /schema.json, got {url}"
        )

    def test_theme_url_contains_pinned_version(self):
        assert THEME_SCHEMA_PINNED_VERSION in THEME_SCHEMA_URL

    def test_theme_url_starts_with_github_base(self):
        assert THEME_SCHEMA_URL.startswith(_THEME_BASE)

    def test_definition_pbir_has_no_double_definition_segment(self):
        """The definition.pbir schema must NOT contain /definition/definitionProperties."""
        assert "/definition/definitionProperties" not in DEFINITION_PBIR_SCHEMA, (
            "DEFINITION_PBIR_SCHEMA must use definitionProperties (no /definition/ prefix). "
            "See KNOWN_ERRORS_AND_FIXES.md: 'UnrecognizedSchemaVersion'."
        )


class TestRegistryHelpers:
    def test_visual_schema_version_is_semver(self):
        v = visual_schema_version()
        parts = v.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_page_schema_version_is_semver(self):
        v = page_schema_version()
        parts = v.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_report_schema_version_is_semver(self):
        v = report_schema_version()
        parts = v.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_all_schemas_returns_dict(self):
        schemas = all_schemas()
        assert isinstance(schemas, dict)
        assert "report" in schemas
        assert "visual" in schemas
        assert "theme_url" in schemas


class TestSchemaManifest:
    """schema_manifest.json must exist and be in sync with the registry."""

    def test_manifest_exists(self):
        assert _MANIFEST.exists(), f"schema_manifest.json not found at {_MANIFEST}"

    def test_manifest_is_valid_json(self):
        data = json.loads(_MANIFEST.read_text(encoding="utf-8"))
        assert "schemas" in data

    def test_manifest_report_url_matches_registry(self):
        data = json.loads(_MANIFEST.read_text(encoding="utf-8"))
        assert data["schemas"]["report"]["url"] == REPORT_SCHEMA

    def test_manifest_visual_url_matches_registry(self):
        data = json.loads(_MANIFEST.read_text(encoding="utf-8"))
        assert data["schemas"]["visual"]["url"] == VISUAL_SCHEMA

    def test_manifest_page_url_matches_registry(self):
        data = json.loads(_MANIFEST.read_text(encoding="utf-8"))
        assert data["schemas"]["page"]["url"] == PAGE_SCHEMA

    def test_manifest_theme_version_matches_registry(self):
        data = json.loads(_MANIFEST.read_text(encoding="utf-8"))
        assert data["schemas"]["theme"]["pinned_version"] == THEME_SCHEMA_PINNED_VERSION

    def test_manifest_up_to_date(self):
        """update_schema_manifest.py --check-only must exit 0 (manifest is current)."""
        script = REPO_ROOT / "products" / "fabric" / "powerbi" / "tooling" / "update_schema_manifest.py"
        result = subprocess.run(
            [sys.executable, str(script), "--check-only"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0, (
            f"schema_manifest.json is stale. Run update_schema_manifest.py to fix.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )


class TestCachedSchemaIds:
    """Cached schema files must declare the same version that generators produce."""

    def test_visual_schema_id_matches_registry(self):
        data = json.loads(_CACHED_SCHEMAS["visual"].read_text(encoding="utf-8"))
        assert data["$id"] == VISUAL_SCHEMA, (
            f"visual.schema.json $id ({data['$id']}) does not match VISUAL_SCHEMA ({VISUAL_SCHEMA}). "
            f"Update $id to match schema_registry.VISUAL_SCHEMA."
        )

    def test_page_schema_id_matches_registry(self):
        data = json.loads(_CACHED_SCHEMAS["page"].read_text(encoding="utf-8"))
        assert data["$id"] == PAGE_SCHEMA, (
            f"page.schema.json $id ({data['$id']}) does not match PAGE_SCHEMA ({PAGE_SCHEMA}). "
            f"Update $id to match schema_registry.PAGE_SCHEMA."
        )

    def test_definition_pbir_schema_id_matches_registry(self):
        data = json.loads(_CACHED_SCHEMAS["definition_pbir"].read_text(encoding="utf-8"))
        assert data["$id"] == DEFINITION_PBIR_SCHEMA, (
            f"definition.pbir.schema.json $id ({data['$id']}) does not match "
            f"DEFINITION_PBIR_SCHEMA ({DEFINITION_PBIR_SCHEMA})."
        )


class TestIRAdapterSchemas:
    """IR adapter render() output must use registry-pinned schema URLs."""

    def test_ir_adapter_uses_registry_report_schema(self):
        from products.fabric.powerbi.tooling.adapters.pbip import _build_report_json
        from tooling.generator_core.ir.specs import DashboardSpec

        spec = DashboardSpec(use_case_id="T-001", domain="Test", title="T")
        result = _build_report_json(spec)
        assert result["$schema"] == REPORT_SCHEMA

    def test_ir_adapter_uses_registry_version_schema(self):
        from products.fabric.powerbi.tooling.adapters.pbip import _build_version_json
        result = _build_version_json()
        assert result["$schema"] == VERSION_METADATA_SCHEMA

    def test_ir_adapter_uses_registry_definition_pbir_schema(self):
        from products.fabric.powerbi.tooling.adapters.pbip import _build_definition_pbir
        result = _build_definition_pbir("Test.SemanticModel")
        assert result["$schema"] == DEFINITION_PBIR_SCHEMA
