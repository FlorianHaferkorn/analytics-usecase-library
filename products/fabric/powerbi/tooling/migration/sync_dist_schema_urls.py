#!/usr/bin/env python3
"""Rewrite dist PBIR $schema URLs to match products/fabric/powerbi/tooling/schema_registry.py."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[5]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from products.fabric.powerbi.tooling.schema_registry import (  # noqa: E402
    DEFINITION_PBIR_SCHEMA,
    PAGE_SCHEMA,
    PAGES_METADATA_SCHEMA,
    REPORT_SCHEMA,
    VERSION_METADATA_SCHEMA,
    VISUAL_SCHEMA,
)


def _set_schema(path: Path, schema: str, *, dry_run: bool) -> bool:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("$schema") == schema:
        return False
    if not dry_run:
        data["$schema"] = schema
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return True


def sync_report_dir(report_dir: Path, *, dry_run: bool) -> int:
    updated = 0
    for rel, schema in (
        ("definition/report.json", REPORT_SCHEMA),
        ("definition/version.json", VERSION_METADATA_SCHEMA),
        ("definition/pages/pages.json", PAGES_METADATA_SCHEMA),
        ("definition.pbir", DEFINITION_PBIR_SCHEMA),
    ):
        path = report_dir / rel
        if path.exists() and _set_schema(path, schema, dry_run=dry_run):
            updated += 1

    pages = report_dir / "definition" / "pages"
    if pages.is_dir():
        for page_dir in pages.iterdir():
            if not page_dir.is_dir():
                continue
            page_json = page_dir / "page.json"
            if page_json.exists() and _set_schema(page_json, PAGE_SCHEMA, dry_run=dry_run):
                updated += 1
            visuals = page_dir / "visuals"
            if not visuals.is_dir():
                continue
            for visual_dir in visuals.iterdir():
                visual_json = visual_dir / "visual.json"
                if visual_json.exists() and _set_schema(visual_json, VISUAL_SCHEMA, dry_run=dry_run):
                    updated += 1
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist-root", default="products/fabric/powerbi/dist")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    dist_root = Path(args.dist_root)
    if not dist_root.is_absolute():
        dist_root = _REPO_ROOT / dist_root
    if not dist_root.is_dir():
        print(f"Dist root not found: {dist_root}", file=sys.stderr)
        return 1

    total = 0
    for report_dir in sorted(dist_root.glob("*.Report")):
        total += sync_report_dir(report_dir, dry_run=args.dry_run)

    action = "Would update" if args.dry_run else "Updated"
    print(f"{action} $schema in {total} file(s) under {dist_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
