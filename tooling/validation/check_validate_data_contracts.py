#!/usr/bin/env python3
"""
Validate domain data contracts under core/data_contracts/domains/.
Writes tooling/validation/results/contract_validation.json with failed_contracts list.
Exit 0 if all valid, 1 if any fail (used by Stage 1 and registry_builder).

Structure: every contract has domain/dimension/fact, every table a name, every fact a grain.
Structured quality fields (A-20/A-23, see core/data_contracts/domains/README.md):

* table ``showcase`` (bool): false = the Aurora showcase has no data for this table.
* column ``nullable`` / ``target_state`` (bool); ``unknown_member`` (scalar, FK only, the
  column is then never NULL, so ``nullable`` must not be true).
* column ``checks``: list of entries with exactly one rule key out of ``gte gt lte lt``
  (number), ``between`` ([lo, hi], lo <= hi, inclusive), ``in`` (non-empty list of scalars),
  ``gte_column`` / ``lte_column`` (another column of the same table), plus optional
  ``when_present: true``.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    if __name__ == "__main__":
        print("FAIL: PyYAML required. Install with: pip install pyyaml", file=sys.stderr)
        sys.exit(1)
    raise


def resolve_root(root_arg: str) -> Path:
    root = Path(root_arg).resolve()
    if root.exists():
        return root
    cwd = Path.cwd()
    candidate = cwd / root_arg
    if candidate.exists():
        return candidate.resolve()
    return cwd / "."


NUMBER_RULES = ("gte", "gt", "lte", "lt")
COLUMN_RULES = ("gte_column", "lte_column")
RULE_KEYS = NUMBER_RULES + ("between", "in") + COLUMN_RULES
ENTRY_KEYS = set(RULE_KEYS) | {"when_present"}


def _is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _is_scalar(v) -> bool:
    return isinstance(v, (str, int, float)) and not isinstance(v, bool)


def check_entry(entry, column: str, table_columns: set[str]) -> list[str]:
    """Errors of one ``checks`` entry (empty list = valid)."""
    if not isinstance(entry, dict):
        return [f"check entry must be a mapping, got {type(entry).__name__}"]
    errors: list[str] = []
    unknown = sorted(set(entry) - ENTRY_KEYS)
    if unknown:
        errors.append(f"check entry has unknown key(s) {unknown}")
    rules = [k for k in entry if k in RULE_KEYS]
    if len(rules) != 1:
        errors.append(f"check entry needs exactly one rule key out of {list(RULE_KEYS)}, got {rules}")
    if "when_present" in entry and entry["when_present"] is not True:
        errors.append("when_present must be true when given")
    for key in rules:
        value = entry[key]
        if key in NUMBER_RULES and not _is_number(value):
            errors.append(f"{key} needs a number, got {value!r}")
        elif key == "between":
            if not (isinstance(value, list) and len(value) == 2 and all(_is_number(x) for x in value)):
                errors.append(f"between needs [lo, hi] numbers, got {value!r}")
            elif value[0] > value[1]:
                errors.append(f"between lower bound {value[0]} > upper bound {value[1]}")
        elif key == "in":
            if not (isinstance(value, list) and value and all(_is_scalar(x) for x in value)):
                errors.append(f"in needs a non-empty list of scalars, got {value!r}")
        elif key in COLUMN_RULES:
            if not isinstance(value, str) or not value:
                errors.append(f"{key} needs a column name, got {value!r}")
            elif value == column:
                errors.append(f"{key} points to the column itself")
            elif value not in table_columns:
                errors.append(f"{key} '{value}' is not a column of this table")
    return errors


def check_column(col: dict, table_columns: set[str]) -> list[str]:
    """Errors of the structured quality fields of one column."""
    errors: list[str] = []
    for key in ("nullable", "target_state"):
        if key in col and not isinstance(col[key], bool):
            errors.append(f"{key} must be a boolean, got {col[key]!r}")
    # source_column (29.09.2026): the physical Gold column when the contract name is the business
    # / model name — the same split as TMDL `column <name>` + `sourceColumn`.
    if "source_column" in col and (not isinstance(col["source_column"], str) or not col["source_column"].strip()):
        errors.append(f"source_column must be a non-empty string, got {col['source_column']!r}")
    elif col.get("source_column") == col.get("name"):
        errors.append("source_column equals name — drop it")
    if "unknown_member" in col:
        if not _is_scalar(col["unknown_member"]):
            errors.append(f"unknown_member must be a scalar, got {col['unknown_member']!r}")
        if not col.get("ref"):
            errors.append("unknown_member needs ref (it names the placeholder row of the referenced dimension)")
        if col.get("nullable") is True:
            errors.append("unknown_member means never NULL, but nullable is true")
    if "checks" in col:
        checks = col["checks"]
        if not isinstance(checks, list) or not checks:
            errors.append("checks must be a non-empty list")
        else:
            name = col.get("name", "?")
            for entry in checks:
                errors.extend(check_entry(entry, name, table_columns))
    return errors


def validate_contract(data) -> list[str]:
    """All errors of one parsed contract (empty list = valid)."""
    if not data or not isinstance(data, dict):
        return ["not a YAML object"]
    if data.get("domain") is None and data.get("dimension") is None and data.get("fact") is None:
        return ["missing domain, dimension, or fact"]
    errors: list[str] = []
    for kind in ("dimension", "fact"):
        tables = data.get(kind) or []
        tables = tables if isinstance(tables, list) else [tables]
        for tbl in tables:
            if not (isinstance(tbl, dict) and tbl.get("name")):
                errors.append(f"{kind} entry missing name")
                continue
            tname = tbl["name"]
            if kind == "fact" and not tbl.get("grain"):
                errors.append(f"fact '{tname}' missing grain")
            if "showcase" in tbl and not isinstance(tbl["showcase"], bool):
                errors.append(f"{tname}: showcase must be a boolean, got {tbl['showcase']!r}")
            cols = [c for c in (tbl.get("columns") or []) if isinstance(c, dict)]
            names = {c.get("name") for c in cols if c.get("name")}
            for col in cols:
                for err in check_column(col, names):
                    errors.append(f"{tname}.{col.get('name', '?')}: {err}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate domain data contracts.")
    parser.add_argument("--root", "-Root", default=".", help="Repo root path")
    parser.add_argument("--fail-on-error", "-FailOnError", action="store_true", help="Exit 1 on validation failure")
    args = parser.parse_args()

    root_path = resolve_root(args.root)
    contracts_dir = root_path / "core" / "data_contracts" / "domains"
    results_dir = root_path / "tooling" / "validation" / "results"
    out_path = results_dir / "contract_validation.json"

    failed_contracts: list[str] = []

    if not contracts_dir.is_dir():
        results_dir.mkdir(parents=True, exist_ok=True)
        payload = {"failed_contracts": [], "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"}
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8", newline="\n")
        print("check_validate_data_contracts: no core/data_contracts/domains, skipped.")
        return 0

    yaml_files = sorted(contracts_dir.glob("*.yaml"))
    for file_path in yaml_files:
        rel_path = file_path.relative_to(root_path).as_posix().replace("\\", "/")
        contract_path = f"core/data_contracts/domains/{file_path.name}"
        try:
            raw = file_path.read_text(encoding="utf-8")
            errors = validate_contract(yaml.safe_load(raw))
        except Exception as e:
            errors = [str(e)]
        for err in errors:
            print(f"FAIL {rel_path} : {err}")
        file_failed = bool(errors)

        if file_failed:
            failed_contracts.append(contract_path)

    results_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "failed_contracts": failed_contracts,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8", newline="\n")

    if failed_contracts:
        print(f"check_validate_data_contracts: {len(failed_contracts)} failed contract(s). Results: {out_path}")
        return 1
    print(f"check_validate_data_contracts: all domain contracts valid. Results: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
