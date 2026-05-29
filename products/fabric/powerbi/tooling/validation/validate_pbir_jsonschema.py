#!/usr/bin/env python3
"""Validate one PBIR JSON file against the schema declared in its $schema field.

Used by check_pbir_schema.ps1. Prints one violation per line as:
  <json-path>|<message>

Usage:
    validate_pbir_jsonschema.py <instance.json> <schema_dir>

Exit 0 when valid, 2 when jsonschema is missing or inputs are invalid.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[5]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from products.fabric.powerbi.tooling.validation.pbir_schema_resolver import (  # noqa: E402
    validate_instance,
)


def main() -> int:
    if len(sys.argv) != 3:
        print(
            "Usage: validate_pbir_jsonschema.py <instance.json> <schema_dir>",
            file=sys.stderr,
        )
        return 2

    instance_path = Path(sys.argv[1]).resolve()
    schema_dir = Path(sys.argv[2]).resolve()

    if not instance_path.is_file():
        print(f"ERROR: instance file not found: {instance_path}", file=sys.stderr)
        return 2
    if not schema_dir.is_dir():
        print(f"ERROR: schema directory not found: {schema_dir}", file=sys.stderr)
        return 2

    try:
        errors = validate_instance(instance_path, schema_dir, allow_fetch=True)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    for path, message in errors:
        print(f"{path}|{message}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
