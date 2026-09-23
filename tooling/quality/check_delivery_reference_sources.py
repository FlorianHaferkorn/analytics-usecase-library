"""Fail when an authoritative delivery-reference source is overdue for review."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from tooling.superversion.project_package.delivery_quality import _load, assess_reference_review


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    model, schema = _load(args.model), _load(args.schema)
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(model),
        key=lambda item: list(item.absolute_path),
    )
    if errors:
        raise ValueError("invalid delivery quality model: " + "; ".join(error.message for error in errors))
    result = assess_reference_review(model)
    report = {
        "schema_version": "1.0.0",
        "model_id": model["id"],
        "model_version": model["version"],
        **result,
    }
    rendered = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    else:
        print(rendered, end="")
    return 0 if result["current"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
