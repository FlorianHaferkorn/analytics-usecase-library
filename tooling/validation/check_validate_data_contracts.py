#!/usr/bin/env python3
"""
Validate domain data contracts under core/data_contracts/domains/.
Writes tooling/validation/results/contract_validation.json with failed_contracts list.
Exit 0 if all valid, 1 if any fail (used by Stage 1 and registry_builder).
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
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print("check_validate_data_contracts: no core/data_contracts/domains, skipped.")
        return 0

    yaml_files = sorted(contracts_dir.glob("*.yaml"))
    for file_path in yaml_files:
        rel_path = str(file_path.relative_to(root_path)).replace("\\", "/")
        contract_path = f"core/data_contracts/domains/{file_path.name}"
        file_failed = False
        try:
            raw = file_path.read_text(encoding="utf-8")
            data = yaml.safe_load(raw)
            if not data or not isinstance(data, dict):
                file_failed = True
                print(f"FAIL {rel_path} : not a YAML object")
            else:
                has_domain = data.get("domain") is not None
                has_dimension = data.get("dimension") is not None
                has_fact = data.get("fact") is not None
                if not (has_domain or has_dimension or has_fact):
                    file_failed = True
                    print(f"FAIL {rel_path} : missing domain, dimension, or fact")
                if not file_failed and data.get("dimension"):
                    dims = data["dimension"] if isinstance(data["dimension"], list) else [data["dimension"]]
                    for d in dims:
                        if not (isinstance(d, dict) and d.get("name")):
                            file_failed = True
                            print(f"FAIL {rel_path} : dimension entry missing name")
                            break
                if not file_failed and data.get("fact"):
                    facts = data["fact"] if isinstance(data["fact"], list) else [data["fact"]]
                    for f in facts:
                        if not (isinstance(f, dict) and f.get("name")):
                            file_failed = True
                            print(f"FAIL {rel_path} : fact entry missing name")
                            break
                        if not f.get("grain"):
                            file_failed = True
                            print(f"FAIL {rel_path} : fact '{f.get('name', '?')}' missing grain")
                            break
        except Exception as e:
            file_failed = True
            print(f"FAIL {rel_path} : {e}")

        if file_failed:
            failed_contracts.append(contract_path)

    results_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "failed_contracts": failed_contracts,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if failed_contracts:
        print(f"check_validate_data_contracts: {len(failed_contracts)} failed contract(s). Results: {out_path}")
        return 1
    print(f"check_validate_data_contracts: all domain contracts valid. Results: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
