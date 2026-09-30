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

Measures in ``--dist`` (30.09.2026): the committed dist is refreshed only where the
catalog render loses nothing the existing block carries (:func:`doc_losses`: a facet
the render drops, a value it shortens, an action code it removes, an extra free line).
Such a measure keeps its block and is reported; ``--dist --check`` exits 1 when a
measure would change. ``tooling/tests/test_enrich_measure_docs.py`` holds the
dist == catalog parity and the explicit exception list. ``--file`` (the orchestrator
step right after generation) replaces unconditionally, as before.

Columns (W5.6, 29.09.2026): ``--columns`` projects the data-contract column
description (``build_table_descriptions`` -> ``ColumnDescription.render_semantic_layer``)
onto each ``column`` of the table files -- the same single description path the
linguistic schema and the AI-surface checks read. Precedence, fixed by
``tooling/tests/test_enrich_column_docs.py``:

* a column whose contract entry has no ``description`` gets no ``///`` (never invented);
* a hand-written ``///`` block above a column is kept as is;
* a block this step wrote earlier (one line in the ``render_semantic_layer`` shape,
  ``/// <text>. Type: <type>[ · ...]``) is refreshed from the contract, and dropped when
  the contract no longer carries a description.

The column is looked up by its model name; a renamed column (``sourceColumn`` points at
the gold column, ``tooling/codegen/model_alignment.py``) falls back to its
``sourceColumn`` unless that name is itself a column of the table (an alias column does
not inherit the original's description).

Usage::

    python tooling/generator/enrich_measure_docs.py --dist products/fabric/powerbi/dist [--check]
    python tooling/generator/enrich_measure_docs.py --dist products/fabric/powerbi/dist --columns [--check]
    python tooling/generator/enrich_measure_docs.py --file <path>/_Measures.tmdl
    python tooling/generator/enrich_measure_docs.py --file <path> --stdout   # preview
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from tooling.generator_core.ai_description import ColumnDescription, TableDescription

# Make tooling/ importable (generator_core) and the repo root (tooling.*, products.*)
# when run as a standalone script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

_MEASURE_RE = re.compile(r"^\tmeasure '([^']+)'")
_DOC_RE = re.compile(r"^\t///")
_KEEP_RE = re.compile(r"\[!\]|UNTRUSTED|MISSING")
_COLUMN_RE = re.compile(r"^\tcolumn (?:'((?:[^']|'')+)'|([^\s=]+))")
_SOURCE_COLUMN_RE = re.compile(r"^\t\tsourceColumn:\s*(.+?)\s*$")
# Shape of ColumnDescription.render_semantic_layer() with a data type (every contract
# column carries one): the marker that tells a block this step wrote from a hand-written one.
_GENERATED_COLUMN_DOC_RE = re.compile(r"^\t/// .+\. Type: [A-Za-z0-9_]+(?: · .*)?$")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


_FACET_KEYS = ("Formula", "Grain", "Unit", "Good", "Drivers", "Owner", "Status", "Actions",
               "Synonyms", "Example question")
_FACET_RE = re.compile(r"^(%s):\s*(.*)$" % "|".join(_FACET_KEYS))


@dataclass(frozen=True)
class DocLoss:
    """One piece of the existing ``///`` block the catalog render would not carry."""

    measure: str
    facet: str   # "definition", a facet key ("Formula", "Grain", ...) or "line"
    kind: str    # "dropped" | "shortened" | "actions_removed" | "line_removed"
    old: str


def _facets(lines: List[str]) -> Tuple[Dict[str, str], List[str]]:
    """Split ``///`` lines (without the ``\t/// `` prefix) into facets and free lines.
    The first free line is the definition; further free lines are returned separately."""
    facets: Dict[str, str] = {}
    free: List[str] = []
    for line in lines:
        parts = [p.strip() for p in line.split(" · ")]
        matches = [_FACET_RE.match(p) for p in parts]
        if all(matches):
            for m in matches:
                facets[m.group(1)] = m.group(2).strip()
        elif "definition" not in facets and not free:
            facets["definition"] = line.strip()
        else:
            free.append(line.strip())
    return facets, free


def _norm(value: str) -> str:
    return value.strip().rstrip(".").strip()


def doc_losses(measure: str, old_block: List[str], new_block: List[str]) -> List[DocLoss]:
    """What ``old_block`` carries that ``new_block`` (the catalog render) would drop.

    Replacing a value is not a loss -- the catalog is the source of truth. A loss is
    a facet the render omits, a value it shortens (the render is contained in the old
    value), an action code it removes, or a free line it does not repeat. Warning
    lines are kept by the enricher and are not compared."""
    def strip(block: List[str]) -> List[str]:
        return [ln.strip()[3:].strip() for ln in block if not _KEEP_RE.search(ln)]

    old_f, old_free = _facets(strip(old_block))
    new_f, new_free = _facets(strip(new_block))
    losses: List[DocLoss] = []
    for key, old in old_f.items():
        if not old:
            continue
        new = new_f.get(key)
        if not new:
            losses.append(DocLoss(measure, key, "dropped", old))
        elif key == "Actions":
            removed = {a.strip() for a in old.split(",")} - {a.strip() for a in new.split(",")}
            if removed:
                losses.append(DocLoss(measure, key, "actions_removed", ", ".join(sorted(removed))))
        elif len(_norm(old)) > len(_norm(new)) and _norm(new) in _norm(old):
            losses.append(DocLoss(measure, key, "shortened", old))
    for line in old_free:
        if line not in new_free:
            losses.append(DocLoss(measure, "line", "line_removed", line))
    return losses


def enrich_text(text: str, repo_root: Path) -> str:
    """Return ``text`` with each resolvable measure's ``///`` block replaced by the
    rendered standard block. Pure function; never raises on unresolved measures."""
    return _enrich(text, repo_root, keep_richer=False)[0]


def enrich_text_guarded(text: str, repo_root: Path) -> Tuple[str, List[DocLoss]]:
    """Like :func:`enrich_text`, but a measure whose existing block would lose
    information (:func:`doc_losses`) keeps it; the losses are returned."""
    return _enrich(text, repo_root, keep_richer=True)


def _enrich(text: str, repo_root: Path, keep_richer: bool) -> Tuple[str, List[DocLoss]]:
    from generator_core.ai_description import load_kpi_catalog

    catalog = load_kpi_catalog(repo_root / "core" / "kpi_catalog" / "KPI_Catalog.md")
    name_to_kpi: dict[str, str] = {}
    for kid, kpi in catalog.items():
        key = kpi.get("kpi_key")
        if key:
            name_to_kpi.setdefault(key, kid)

    out: list[str] = []
    pending: list[str] = []
    skipped: List[DocLoss] = []
    for line in text.splitlines():
        if _DOC_RE.match(line):
            pending.append(line)
            continue
        match = _MEASURE_RE.match(line)
        if match:
            block = _render_block(name_to_kpi.get(match.group(1)), repo_root)
            losses = doc_losses(match.group(1), pending, block) if (block and keep_richer) else []
            if block is not None and not losses:
                out.extend(block)
                out.extend(p for p in pending if _KEEP_RE.search(p))  # keep warnings
            else:
                out.extend(pending)
                skipped.extend(losses)
            pending = []
            out.append(line)
            continue
        out.extend(pending)
        pending = []
        out.append(line)
    out.extend(pending)
    return "\n".join(out) + ("\n" if text.endswith("\n") else ""), skipped


def enrich_dist_measures(
    dist: Path, repo_root: Path, write: bool = True
) -> Tuple[List[Path], Dict[Tuple[str, str], List[DocLoss]]]:
    """Guarded refresh of every ``_Measures.tmdl`` under ``dist``. Returns the files that
    changed (or would, with ``write=False``) and the kept measures keyed by
    ``(model, measure)`` -- model is the ``<model>.SemanticModel`` folder stem."""
    changed: List[Path] = []
    kept: Dict[Tuple[str, str], List[DocLoss]] = {}
    for f in sorted(Path(dist).rglob("_Measures.tmdl")):
        model = next((p[: -len(".SemanticModel")] for p in f.parts if p.endswith(".SemanticModel")), f.parent.name)
        text = f.read_text(encoding="utf-8")
        new, losses = enrich_text_guarded(text, repo_root)
        for loss in losses:
            kept.setdefault((model, loss.measure), []).append(loss)
        if new != text:
            changed.append(f)
            if write:
                f.write_text(new, encoding="utf-8", newline="\n")
    return changed, kept


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


# ──────────────────────────────────────────────────────────────────────────────
# Columns (data contract -> TMDL ``///``)
# ──────────────────────────────────────────────────────────────────────────────


def _column_doc(
    name: str, source: Optional[str], by_name: Dict[str, "ColumnDescription"], model_columns: set
) -> Optional[str]:
    col = by_name.get(name)
    if col is None and source and source not in model_columns:
        col = by_name.get(source)
    if col is None or not col.description.strip():
        return None
    return "\t" + col.render_semantic_layer().strip()


def enrich_columns_text(text: str, table: Optional["TableDescription"]) -> str:
    """Return ``text`` (one table's TMDL) with the contract description as ``///`` above
    each column that has one. Pure; precedence rules in the module docstring."""
    if table is None:
        return text
    by_name = {c.name: c for c in table.columns}
    lines = text.splitlines()
    names: List[Optional[str]] = []
    for line in lines:
        m = _COLUMN_RE.match(line)
        names.append((m.group(1).replace("''", "'") if m.group(1) else m.group(2)) if m else None)
    model_columns = {n for n in names if n}

    out: List[str] = []
    pending: List[str] = []
    for i, line in enumerate(lines):
        if _DOC_RE.match(line):
            pending.append(line)
            continue
        name = names[i]
        if name is not None:
            source = None
            for follow in lines[i + 1:]:
                if not follow.startswith("\t\t"):
                    break
                sm = _SOURCE_COLUMN_RE.match(follow)
                if sm:
                    source = sm.group(1).strip("'")
                    break
            doc = _column_doc(name, source, by_name, model_columns)
            generated = len(pending) == 1 and _GENERATED_COLUMN_DOC_RE.match(pending[0])
            if not pending or generated:
                pending = [doc] if doc else []
        out.extend(pending)
        pending = []
        out.append(line)
    out.extend(pending)
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def _domain_tables(domain: str, contracts_dir: Path) -> Dict[str, "TableDescription"]:
    from products.fabric.powerbi.tooling.linguistic_schema import DOMAIN_CONTRACT
    from tooling.generator_core.ai_description import build_table_descriptions

    contract = DOMAIN_CONTRACT.get(domain)
    if not contract:
        return {}
    return {t.name: t for t in build_table_descriptions(Path(contracts_dir) / contract)}


def enrich_dist_columns(dist: Path, contracts_dir: Path, write: bool = True) -> List[Path]:
    """Apply :func:`enrich_columns_text` to every table file under ``dist``; return the
    files that changed (or would change with ``write=False``)."""
    changed: List[Path] = []
    for model in sorted(Path(dist).glob("*.SemanticModel")):
        tables = _domain_tables(model.name[: -len(".SemanticModel")], contracts_dir)
        for f in sorted((model / "definition" / "tables").glob("*.tmdl")):
            text = f.read_text(encoding="utf-8")
            new = enrich_columns_text(text, tables.get(f.stem))
            if new != text:
                changed.append(f)
                if write:
                    f.write_text(new, encoding="utf-8", newline="\n")
    return changed


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
    parser.add_argument("--columns", action="store_true",
                        help="With --dist: project data-contract column descriptions onto the table files.")
    parser.add_argument("--check", action="store_true",
                        help="With --dist: write nothing, exit 1 if a file would change.")
    args = parser.parse_args(argv)
    repo_root = _repo_root()

    if args.columns:
        if not args.dist:
            parser.error("--columns needs --dist")
        contracts = repo_root / "core" / "data_contracts" / "domains"
        changed = enrich_dist_columns(args.dist, contracts, write=not args.check)
        for f in changed:
            print(f"{'would change' if args.check else 'enriched'}: {f}")
        print(f"{len(changed)} table file(s) {'out of sync' if args.check else 'enriched'}")
        return 1 if (args.check and changed) else 0

    if args.file:
        if args.stdout:
            sys.stdout.write(enrich_text(args.file.read_text(encoding="utf-8"), repo_root))
            return 0
        changed = enrich_file(args.file, repo_root)
        print(f"{'enriched' if changed else 'unchanged'}: {args.file}")
        return 0

    if args.dist:
        changed, kept = enrich_dist_measures(args.dist, repo_root, write=not args.check)
        for (model, measure), losses in sorted(kept.items()):
            detail = "; ".join(f"{loss.facet} {loss.kind}" for loss in losses)
            print(f"kept (catalog render would lose information): {model} / {measure}: {detail}")
        for f in changed:
            print(f"{'would change' if args.check else 'enriched'}: {f}")
        print(f"{len(changed)} _Measures.tmdl file(s) {'out of sync' if args.check else 'enriched'}, "
              f"{len(kept)} measure(s) kept")
        return 1 if (args.check and changed) else 0

    parser.error("provide --file or --dist")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
