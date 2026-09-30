"""
Tests for misc_functions module.

Run with: python -m pytest products/fabric/powerbi/deployment/scripts/modules/tests/test_misc_functions.py -v
"""

import json
import os
import tempfile
import pytest

import misc_functions as misc


class TestIsGuid:
    """Test GUID validation."""

    def test_valid_guid(self):
        assert misc.is_guid("12345678-1234-1234-1234-123456789abc") is True

    def test_valid_guid_uppercase(self):
        assert misc.is_guid("12345678-1234-1234-1234-123456789ABC") is True

    def test_invalid_guid_short(self):
        assert misc.is_guid("12345678-1234") is False

    def test_invalid_guid_no_dashes(self):
        assert misc.is_guid("12345678123412341234123456789abc") is False

    def test_invalid_guid_letters(self):
        assert misc.is_guid("not-a-guid-at-all-nope-definitely") is False

    def test_empty_string(self):
        assert misc.is_guid("") is False

    def test_none_value(self):
        assert misc.is_guid(None) is False


class TestLoadJson:
    """Test JSON file loading."""

    def test_load_valid_json(self, tmp_path):
        f = tmp_path / "valid.json"
        f.write_text('{"key": "value"}', encoding="utf-8")
        result = misc.load_json(str(f))
        assert result == {"key": "value"}

    def test_load_missing_file(self):
        result = misc.load_json("/nonexistent/path/file.json")
        assert result is None

    def test_load_invalid_json(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("{bad json", encoding="utf-8")
        result = misc.load_json(str(f))
        assert result is None


class TestMergeJson:
    """Test JSON deep merge."""

    def test_override_merge(self):
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = misc.merge_json(base, override, merge_type=1)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_deep_merge(self):
        base = {"a": {"x": 1, "y": 2}, "b": 3}
        override = {"a": {"y": 99, "z": 100}}
        result = misc.merge_json(base, override, merge_type=2)
        assert result["a"] == {"x": 1, "y": 99, "z": 100}
        assert result["b"] == 3

    def test_deep_merge_non_dict_override(self):
        base = {"a": {"x": 1}}
        override = {"a": "replaced"}
        result = misc.merge_json(base, override, merge_type=2)
        assert result["a"] == "replaced"


class TestReplaceTemplateVariables:
    """Test template variable replacement."""

    def test_single_variable(self):
        result = misc.replace_template_variables("{name}_workspace", {"name": "Sales"})
        assert result == "Sales_workspace"

    def test_multiple_variables(self):
        result = misc.replace_template_variables(
            "{layer}_{environment}",
            {"layer": "DM", "environment": "dev"},
        )
        assert result == "DM_dev"

    def test_no_variables(self):
        result = misc.replace_template_variables("plain text", {})
        assert result == "plain text"


class TestFormatWorkspaceName:
    """Test workspace name formatting."""

    def test_format_workspace(self):
        result = misc.format_workspace_name("{layer}_{environment}", "BI", "prod")
        assert result == "BI_prod"


class TestCapacityPerStageGroup:
    """D-596: production and non-production run on separate capacities."""

    @staticmethod
    def _merged(env: str) -> dict:
        from pathlib import Path
        root = Path(__file__).resolve().parents[3] / "resources" / "environments"
        base = json.loads((root / "infrastructure.json").read_text(encoding="utf-8"))
        over = json.loads((root / f"infrastructure.{env}.json").read_text(encoding="utf-8"))
        return misc.merge_json(base, over)

    def test_dev_and_tst_share_the_non_production_capacity(self):
        assert (self._merged("dev")["generic"]["capacity_name"]
                == self._merged("tst")["generic"]["capacity_name"])

    def test_production_has_its_own_capacity(self):
        assert (self._merged("prd")["generic"]["capacity_name"]
                != self._merged("dev")["generic"]["capacity_name"])
