#!/usr/bin/env python3
"""
check_business_cases.py -- Validate business cases for all Impactful-15 action codes.

Usage:
    python3 tooling/generator/validation/check_business_cases.py
    python3 tooling/generator/validation/check_business_cases.py --strict

Exit codes:
    0  All business cases present and schema-valid.
    1  One or more business cases missing or invalid.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

try:
    from jsonschema import validate, ValidationError, SchemaError
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

# Resolve relative to script location (3 parents = repo root)
REPO_ROOT = Path(__file__).resolve().parents[3]
IMPACTFUL_15_PATH = REPO_ROOT / "core" / "action_codes" / "impactful_15.yaml"
ACTION_CODES_DIR = REPO_ROOT / "core" / "action_codes"
SCHEMA_PATH = REPO_ROOT / "tooling" / "generator" / "schemas" / "business_case.schema.json"


def load_impactful_15() -> list[dict]:
    with open(IMPACTFUL_15_PATH, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    # Support both key names for forward/backward compatibility
    codes = data.get("action_codes") or data.get("action_code_ids", [])
    if not isinstance(codes, list):
        raise ValueError(
            "impactful_15.yaml must have an 'action_codes' or 'action_code_ids' list."
        )
    return codes


def load_schema() -> dict | None:
    if not SCHEMA_PATH.exists():
        return None
    with open(SCHEMA_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def find_business_case(action_code_id: str, domain: str) -> Path | None:
    """Find <Domain>/<ID>_business_case.yaml co-located next to the action code."""
    domain_dir = ACTION_CODES_DIR / domain
    candidate = domain_dir / f"{action_code_id}_business_case.yaml"
    return candidate if candidate.exists() else None


def validate_bc(path: Path, schema: dict | None, expected_id: str) -> list[str]:
    errors: list[str] = []

    try:
        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except Exception as exc:
        errors.append(f"YAML parse error: {exc}")
        return errors

    if not isinstance(data, dict):
        errors.append("Root document must be a YAML mapping.")
        return errors

    # ID match
    if data.get("action_code_id") != expected_id:
        errors.append(
            f"action_code_id '{data.get('action_code_id')}' does not match expected '{expected_id}'."
        )

    # Required fields
    for field in [
        "action_code_id", "kpi_id",
        "impact_range_eur_min", "impact_range_eur_likely", "impact_range_eur_max",
        "time_to_effect_days", "confidence", "owner", "assumptions",
    ]:
        if field not in data:
            errors.append(f"Missing required field: '{field}'.")

    # Assumptions list
    assumptions = data.get("assumptions")
    if isinstance(assumptions, list):
        if not assumptions:
            errors.append("'assumptions' must have at least one entry.")
        for i, a in enumerate(assumptions):
            if not isinstance(a, str) or len(a) < 10:
                errors.append(f"assumptions[{i}] must be a string with >= 10 characters.")
    elif "assumptions" in data:
        errors.append("'assumptions' must be a list.")

    # EUR ordering
    lo = data.get("impact_range_eur_min")
    mid = data.get("impact_range_eur_likely")
    hi = data.get("impact_range_eur_max")
    if all(isinstance(v, (int, float)) for v in (lo, mid, hi)):
        if not (lo <= mid <= hi):
            errors.append(f"EUR range ordering invalid: min={lo} likely={mid} max={hi}.")

    # Confidence enum
    conf = data.get("confidence")
    if conf is not None and conf not in ("low", "medium", "high"):
        errors.append(f"'confidence' must be 'low'|'medium'|'high'; got '{conf}'.")

    # JSON Schema (optional)
    if schema and HAS_JSONSCHEMA:
        try:
            validate(instance=data, schema=schema)
        except ValidationError as exc:
            errors.append(f"JSON Schema: {exc.message}")
        except SchemaError as exc:
            print(f"  WARNING: schema file error: {exc.message}", file=sys.stderr)

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Impactful-15 business cases."
    )
    parser.add_argument("--strict", action="store_true",
                        help="Exit non-zero on any failure (same as default).")
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args()

    if args.repo_root:
        global REPO_ROOT, IMPACTFUL_15_PATH, ACTION_CODES_DIR, SCHEMA_PATH
        REPO_ROOT = args.repo_root.resolve()
        IMPACTFUL_15_PATH = REPO_ROOT / "core" / "action_codes" / "impactful_15.yaml"
        ACTION_CODES_DIR = REPO_ROOT / "core" / "action_codes"
        SCHEMA_PATH = REPO_ROOT / "tooling" / "generator" / "schemas" / "business_case.schema.json"

    print("check_business_cases: Impactful-15 validation")
    print(f"  manifest : {IMPACTFUL_15_PATH}")
    print(f"  schema   : {SCHEMA_PATH}")
    if not HAS_JSONSCHEMA:
        print("  NOTE: jsonschema not installed; skipping JSON Schema step.")

    try:
        codes = load_impactful_15()
    except Exception as exc:
        print(f"ERROR: Cannot load impactful_15.yaml: {exc}", file=sys.stderr)
        return 1

    schema = load_schema()
    total = len(codes)
    passed = 0
    failed: list[str] = []

    for entry in codes:
        ac_id = entry.get("id", "?")
        domain = entry.get("domain", "")
        bc_path = find_business_case(ac_id, domain)

        if bc_path is None:
            print(f"  FAIL  {ac_id}: business_case YAML not found "
                  f"(expected {domain}/{ac_id}_business_case.yaml)")
            failed.append(ac_id)
            continue

        errs = validate_bc(bc_path, schema, ac_id)
        if errs:
            print(f"  FAIL  {ac_id}:")
            for e in errs:
                print(f"          - {e}")
            failed.append(ac_id)
        else:
            print(f"  OK    {ac_id}")
            passed += 1

    print(f"\nResult: {passed}/{total} valid.")
    if failed:
        print(f"Failed: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
