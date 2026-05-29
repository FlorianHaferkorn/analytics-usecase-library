#!/usr/bin/env python3
"""Validate one PBIR JSON file against a cached schema file.

Used by check_pbir_schema.ps1. Prints one violation per line as:
  <json-path>|<message>

Exit 0 when valid, 2 when jsonschema is missing or inputs are invalid.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print(
            "Usage: validate_pbir_jsonschema.py <instance.json> <schema.json>",
            file=sys.stderr,
        )
        return 2

    try:
        import jsonschema
    except ImportError:
        print("ERROR: jsonschema not installed", file=sys.stderr)
        return 2

    json_path = Path(sys.argv[1])
    schema_path = Path(sys.argv[2])

    instance = json.loads(json_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft7Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.path))

    for err in errors:
        path = "/".join(str(p) for p in err.path) if err.path else "(root)"
        print(f"{path}|{err.message}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
