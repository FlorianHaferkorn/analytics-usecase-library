#!/usr/bin/env python3
"""
cache_pbir_schemas.py — Download Microsoft PBIR JSON schemas into tooling/schemas/pbir/.

Schemas are stored under tooling/schemas/pbir/microsoft/<path-from-url> so
check_pbir_schema.ps1 can validate each file against the $schema URL it declares.

Usage (from repository root):
    py -3 products/fabric/powerbi/tooling/cache_pbir_schemas.py
    py -3 products/fabric/powerbi/tooling/cache_pbir_schemas.py --force
    py -3 products/fabric/powerbi/tooling/cache_pbir_schemas.py --scan-dist
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from products.fabric.powerbi.tooling.validation.pbir_schema_resolver import (  # noqa: E402
    DEFAULT_SCHEMA_URLS,
    cache_schema,
    collect_schema_urls_from_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--schema-dir",
        type=Path,
        default=_REPO_ROOT / "tooling" / "schemas" / "pbir",
        help="Cache root (default: tooling/schemas/pbir)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even when cache file exists",
    )
    parser.add_argument(
        "--scan-dist",
        action="store_true",
        help="Also collect $schema URLs from products/fabric/powerbi/dist/*.Report",
    )
    args = parser.parse_args()
    schema_dir: Path = args.schema_dir.resolve()

    urls: set[str] = set(DEFAULT_SCHEMA_URLS)
    if args.scan_dist:
        dist = _REPO_ROOT / "products" / "fabric" / "powerbi" / "dist"
        for report in dist.glob("*.Report"):
            def_dir = report / "definition"
            urls.update(collect_schema_urls_from_report(def_dir))

    failed: list[str] = []
    for url in sorted(urls):
        try:
            path = cache_schema(schema_dir, url, force=args.force)
            print(f"OK  {url}")
            print(f"    -> {path.relative_to(_REPO_ROOT)}")
        except Exception as exc:
            print(f"FAIL {url}: {exc}", file=sys.stderr)
            failed.append(url)

    if failed:
        print(f"\n{len(failed)} schema(s) failed to cache.", file=sys.stderr)
        return 1
    print(f"\nCached {len(urls)} schema(s) under {schema_dir.relative_to(_REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
