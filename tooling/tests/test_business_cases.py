"""Tests for CEO-grade business cases and ROI presets.

Covers:
  - Impactful-15 business cases (one per action code)
  - Golden-20 ROI presets (one per KPI)
  - Business case validator script (check_business_cases.py)
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml
import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
ACTION_CODES_ROOT = REPO_ROOT / "core" / "action_codes"
PRESETS_DIR = REPO_ROOT / "core" / "templates" / "business_case" / "presets"
IMPACTFUL_15 = REPO_ROOT / "core" / "action_codes" / "impactful_15.yaml"
GOLDEN_20 = REPO_ROOT / "core" / "kpi_catalog" / "golden_20.yaml"
VALIDATOR = REPO_ROOT / "tooling" / "generator" / "validation" / "check_business_cases.py"
SCHEMA_PATH = REPO_ROOT / "tooling" / "generator" / "schemas" / "business_case.schema.json"


def load_impactful_15() -> list[dict]:
    data = yaml.safe_load(IMPACTFUL_15.read_text(encoding="utf-8"))
    return data.get("action_codes") or data.get("action_code_ids", [])


def load_golden_20_ids() -> list[str]:
    data = yaml.safe_load(GOLDEN_20.read_text(encoding="utf-8"))
    entries = data.get("kpi_ids", [])
    return [e["id"] for e in entries if "id" in e]


# ---------------------------------------------------------------------------
# Business Cases (Impactful-15)
# ---------------------------------------------------------------------------


class TestImpactful15BusinessCases:
    """Each Impactful-15 action code must have a valid business_case YAML."""

    def test_all_business_cases_exist(self):
        codes = load_impactful_15()
        missing = []
        for entry in codes:
            ac_id = entry["id"]
            domain = entry.get("domain", "")
            bc_path = ACTION_CODES_ROOT / domain / f"{ac_id}_business_case.yaml"
            if not bc_path.exists():
                missing.append(f"{domain}/{ac_id}_business_case.yaml")
        assert not missing, f"Missing business case files: {missing}"

    def test_all_business_cases_are_valid_yaml(self):
        codes = load_impactful_15()
        errors = []
        for entry in codes:
            ac_id = entry["id"]
            domain = entry.get("domain", "")
            bc_path = ACTION_CODES_ROOT / domain / f"{ac_id}_business_case.yaml"
            try:
                data = yaml.safe_load(bc_path.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    errors.append(f"{ac_id}: not a mapping")
            except yaml.YAMLError as exc:
                errors.append(f"{ac_id}: YAML error - {exc}")
        assert not errors, f"Business case YAML errors: {errors}"

    def test_required_fields_present(self):
        required = [
            "action_code_id", "kpi_id",
            "impact_range_eur_min", "impact_range_eur_likely", "impact_range_eur_max",
            "time_to_effect_days", "confidence", "owner", "assumptions",
        ]
        codes = load_impactful_15()
        errors = []
        for entry in codes:
            ac_id = entry["id"]
            domain = entry.get("domain", "")
            bc_path = ACTION_CODES_ROOT / domain / f"{ac_id}_business_case.yaml"
            data = yaml.safe_load(bc_path.read_text(encoding="utf-8"))
            for field in required:
                if field not in data:
                    errors.append(f"{ac_id}: missing '{field}'")
        assert not errors, f"Missing required fields: {errors}"

    def test_eur_range_ordering(self):
        codes = load_impactful_15()
        errors = []
        for entry in codes:
            ac_id = entry["id"]
            domain = entry.get("domain", "")
            bc_path = ACTION_CODES_ROOT / domain / f"{ac_id}_business_case.yaml"
            data = yaml.safe_load(bc_path.read_text(encoding="utf-8"))
            lo = data.get("impact_range_eur_min")
            mid = data.get("impact_range_eur_likely")
            hi = data.get("impact_range_eur_max")
            if all(isinstance(v, (int, float)) for v in (lo, mid, hi)):
                if not (lo <= mid <= hi):
                    errors.append(f"{ac_id}: EUR range invalid ({lo}, {mid}, {hi})")
        assert not errors, f"EUR range ordering errors: {errors}"

    def test_confidence_enum(self):
        valid = {"low", "medium", "high"}
        codes = load_impactful_15()
        errors = []
        for entry in codes:
            ac_id = entry["id"]
            domain = entry.get("domain", "")
            bc_path = ACTION_CODES_ROOT / domain / f"{ac_id}_business_case.yaml"
            data = yaml.safe_load(bc_path.read_text(encoding="utf-8"))
            conf = data.get("confidence")
            if conf not in valid:
                errors.append(f"{ac_id}: invalid confidence '{conf}'")
        assert not errors, f"Confidence enum errors: {errors}"

    def test_assumptions_non_empty(self):
        codes = load_impactful_15()
        errors = []
        for entry in codes:
            ac_id = entry["id"]
            domain = entry.get("domain", "")
            bc_path = ACTION_CODES_ROOT / domain / f"{ac_id}_business_case.yaml"
            data = yaml.safe_load(bc_path.read_text(encoding="utf-8"))
            assumptions = data.get("assumptions", [])
            if not isinstance(assumptions, list) or len(assumptions) == 0:
                errors.append(f"{ac_id}: 'assumptions' must be a non-empty list")
        assert not errors, f"Empty assumptions: {errors}"

    def test_action_code_id_matches_filename(self):
        codes = load_impactful_15()
        errors = []
        for entry in codes:
            ac_id = entry["id"]
            domain = entry.get("domain", "")
            bc_path = ACTION_CODES_ROOT / domain / f"{ac_id}_business_case.yaml"
            data = yaml.safe_load(bc_path.read_text(encoding="utf-8"))
            if data.get("action_code_id") != ac_id:
                errors.append(f"{ac_id}: action_code_id mismatch in file")
        assert not errors, f"action_code_id mismatches: {errors}"

    def test_exactly_15_business_cases(self):
        codes = load_impactful_15()
        assert len(codes) == 15, f"Expected 15 action codes, got {len(codes)}"
        found = 0
        for entry in codes:
            ac_id = entry["id"]
            domain = entry.get("domain", "")
            bc_path = ACTION_CODES_ROOT / domain / f"{ac_id}_business_case.yaml"
            if bc_path.exists():
                found += 1
        assert found == 15, f"Expected 15 business case files, found {found}"


# ---------------------------------------------------------------------------
# ROI Presets (Golden-20)
# ---------------------------------------------------------------------------


class TestGolden20RoiPresets:
    """Each Golden-20 KPI must have a ROI preset YAML in templates/business_case/presets/."""

    def test_presets_directory_exists(self):
        assert PRESETS_DIR.exists(), f"Presets directory not found: {PRESETS_DIR}"

    def test_all_golden20_presets_exist(self):
        ids = load_golden_20_ids()
        missing = [kpi_id for kpi_id in ids if not (PRESETS_DIR / f"{kpi_id}.yaml").exists()]
        assert not missing, f"Missing ROI preset files for: {missing}"

    def test_exactly_20_presets(self):
        ids = load_golden_20_ids()
        assert len(ids) == 20, f"Expected 20 golden KPI IDs, got {len(ids)}"
        found = [kpi_id for kpi_id in ids if (PRESETS_DIR / f"{kpi_id}.yaml").exists()]
        assert len(found) == 20, f"Expected 20 preset files, found {len(found)}"

    def test_preset_required_fields(self):
        ids = load_golden_20_ids()
        required = ["kpi_id", "label", "baseline_range", "target_range", "time_horizon_months", "driver_notes"]
        errors = []
        for kpi_id in ids:
            path = PRESETS_DIR / f"{kpi_id}.yaml"
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
                for field in required:
                    if field not in data:
                        errors.append(f"{kpi_id}: missing '{field}'")
            except (yaml.YAMLError, OSError) as exc:
                errors.append(f"{kpi_id}: {exc}")
        assert not errors, f"Preset field errors: {errors}"

    def test_preset_kpi_id_matches_filename(self):
        ids = load_golden_20_ids()
        errors = []
        for kpi_id in ids:
            path = PRESETS_DIR / f"{kpi_id}.yaml"
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            if data.get("kpi_id") != kpi_id:
                errors.append(f"{kpi_id}: kpi_id field mismatch")
        assert not errors, f"kpi_id mismatches: {errors}"

    def test_preset_driver_notes_non_empty(self):
        ids = load_golden_20_ids()
        errors = []
        for kpi_id in ids:
            path = PRESETS_DIR / f"{kpi_id}.yaml"
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            notes = data.get("driver_notes", [])
            if not isinstance(notes, list) or len(notes) == 0:
                errors.append(f"{kpi_id}: driver_notes must be non-empty list")
        assert not errors, f"Empty driver_notes: {errors}"


# ---------------------------------------------------------------------------
# Validator script
# ---------------------------------------------------------------------------


class TestBusinessCaseValidator:
    """check_business_cases.py --strict must exit 0."""

    def test_validator_exists(self):
        assert VALIDATOR.exists(), f"Validator not found: {VALIDATOR}"

    def test_validator_exits_zero(self):
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), "--strict"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"check_business_cases.py failed:\n{result.stdout}\n{result.stderr}"
        )

    def test_schema_is_valid_json(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        assert schema.get("$schema"), "Schema must have $schema property"
        assert schema.get("title"), "Schema must have title"
        assert "required" in schema, "Schema must have required fields"
