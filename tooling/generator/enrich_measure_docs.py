#!/usr/bin/env python3
"""Rewrite the ``///`` doc block above each measure in a ``_Measures.tmdl`` to the
AI-description standard -- a *projection* of the governed catalog rather than a
bespoke comment. Idempotent.

Canonical post-generation step: run after the measure generator (PowerShell or
Python) so semantic-layer descriptions are projections of
``core/semantic_models/AI_Description_Standard.md``. Each measure is resolved by
display name -> ``kpi_id`` (via the KPI catalog ``kpi_key``); measures that do
not resolve to a catalog KPI keep their existing ``///`` lines, and warning lines
(``[!]`` / ``UNTRUSTED`` / ``MISSING``) are always preserved.

Usage::

    python tooling/generator/enrich_measure_docs.py --dist products/fabric/powerbi/dist
    python tooling/generator/enrich_measure_docs.py --file <path>/_Measures.tmdl
    python tooling/generator/enrich_measure_docs.py --file <path> --stdout   # preview
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Make tooling/ importable (generator_core) when run as a standalone script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_MEASURE_RE = re.compile(r"^\tmeasure '([^']+)'")
_DOC_RE = re.compile(r"^\t///")
_KEEP_RE = re.compile(r"\[!\]|UNTRUSTED|MISSING")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def enrich_text(text: str, repo_root: Path) -> str:
    """Return ``text`` with each resolvable measure's ``///`` block replaced by the
    rendered standard block. Pure function; never raises on unresolved measures."""
    from generator_core.ai_description import load_kpi_catalog

    catalog = load_kpi_catalog(repo_root / "core" / "kpi_catalog" / "KPI_Catalog.md")
    name_to_kpi: dict[str, str] = {}
    for kid, kpi in catalog.items():
        key = kpi.get("kpi_key")
        if key:
            name_to_kpi.setdefault(key, kid)

    out: list[str] = []
    pending: list[str] = []
    for line in text.splitlines():
        if _DOC_RE.match(line):
            pending.append(line)
            continue
        match = _MEASURE_RE.match(line)
        if match:
            block = _render_block(name_to_kpi.get(match.group(1)), repo_root)
            if block is not None:
                out.extend(block)
                out.extend(p for p in pending if _KEEP_RE.search(p))  # keep warnings
            else:
                out.extend(pending)
            pending = []
            out.append(line)
            continue
        out.extend(pending)
        pending = []
        out.append(line)
    out.extend(pending)
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def _render_block(kpi_id: str | None, repo_root: Path) -> list[str] | None:
    if not kpi_id:
        return None
    from generator_core.ai_description import build_description

    desc = build_description(kpi_id, repo_root)
    if desc is None:
        return None
    rendered = desc.render_semantic_layer().strip()
    if not rendered:
        return None
    return ["\t" + line for line in rendered.splitlines()]


def enrich_file(path: Path, repo_root: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    new = enrich_text(text, repo_root)
    if new != text:
        path.write_text(new, encoding="utf-8", newline="\n")
        return True
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--file", type=Path, help="A single _Measures.tmdl to enrich in place.")
    parser.add_argument("--dist", type=Path, help="A dist root; enrich every _Measures.tmdl beneath it.")
    parser.add_argument("--stdout", action="store_true", help="Preview output (with --file) instead of writing.")
    args = parser.parse_args(argv)
    repo_root = _repo_root()

    if args.file:
        if args.stdout:
            sys.stdout.write(enrich_text(args.file.read_text(encoding="utf-8"), repo_root))
            return 0
        changed = enrich_file(args.file, repo_root)
        print(f"{'enriched' if changed else 'unchanged'}: {args.file}")
        return 0

    if args.dist:
        count = sum(1 for f in args.dist.rglob("_Measures.tmdl") if enrich_file(f, repo_root))
        print(f"enriched {count} _Measures.tmdl file(s)")
        return 0

    parser.error("provide --file or --dist")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
