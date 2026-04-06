#!/usr/bin/env python3
"""
Output domain data contract schema as JSON for audit_data_contracts_content.ps1.
Prints to stdout: { "tables": { "table_name": { "columns": [...], "files": [...] } }, "cross_domain_duplicates": [...] }
"""

import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("{}", file=sys.stderr)
    sys.exit(1)


def resolve_root(root_arg: str) -> Path:
    root = Path(root_arg).resolve()
    if root.exists():
        return root
    return Path.cwd() / "."


def main() -> int:
    root_path = resolve_root(sys.argv[1] if len(sys.argv) > 1 else ".")
    contracts_dir = root_path / "core" / "data_contracts" / "domains"
    tables: dict = {}

    if not contracts_dir.is_dir():
        print(json.dumps({"tables": {}, "cross_domain_duplicates": []}))
        return 0

    for file_path in sorted(contracts_dir.glob("*.yaml")):
        rel_file = f"core/data_contracts/domains/{file_path.name}"
        try:
            data = yaml.safe_load(file_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not data or not isinstance(data, dict):
            continue

        for section in ("dimension", "fact"):
            items = data.get(section)
            if not items:
                continue
            if not isinstance(items, list):
                items = [items]
            for item in items:
                if not isinstance(item, dict) or not item.get("name"):
                    continue
                tname = item["name"]
                cols = []
                for c in item.get("columns") or []:
                    if isinstance(c, dict) and c.get("name"):
                        cols.append(c["name"].strip())
                    elif isinstance(c, str):
                        cols.append(c.strip())
                if tname not in tables:
                    tables[tname] = {"columns": cols, "files": []}
                else:
                    tables[tname]["columns"] = list(set(tables[tname]["columns"]) | set(cols))
                if rel_file not in tables[tname]["files"]:
                    tables[tname]["files"].append(rel_file)

    cross_domain_duplicates = [[tname, meta["files"]] for tname, meta in tables.items() if len(meta["files"]) > 1]
    out = {"tables": tables, "cross_domain_duplicates": cross_domain_duplicates}
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
