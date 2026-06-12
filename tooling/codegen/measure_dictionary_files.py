#!/usr/bin/env python3
"""Machine-readable SSOT for the domain measure dictionaries (Phase A, slice 2).

Each ``core/semantic_models/domains/<Domain>/Measure_Dictionary_<Domain>.md``
holds a YAML block listing that semantic model's measures. The source of truth
moves to one file per measure under
``core/semantic_models/domains/<Domain>/measures/<measure_id>.yaml``; the
Markdown becomes a *generated view*.

A measure belongs to exactly one semantic model, so measures are organised
per-domain (unlike KPIs, which span domains and are tagged). ``measure_id`` is a
slug of ``measure_name``; genuine duplicate names within a domain (a latent
defect this lift surfaces) are preserved faithfully with a ``__N`` suffix so the
round-trip loses nothing.

Subcommands: extract / render / check (see kpi_catalog_files.py for the pattern).
``check`` compares each dictionary's block to its per-measure files as an
*ordered list* (element-wise), so duplicates are handled correctly.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
DOMAINS = REPO / "core" / "semantic_models" / "domains"
FENCE_OPEN = "```yaml"
FENCE_CLOSE = "```"

GENERATED_NOTE = (
    "> **Generated view.** The source of truth is the per-measure files under "
    "[`measures/`](measures/). Edit those (or use ActionReady Studio); regenerate "
    "this file with `python tooling/codegen/measure_dictionary_files.py render`.\n"
)


def dict_paths() -> list[Path]:
    return sorted(DOMAINS.glob("*/Measure_Dictionary_*.md"))


def _slug(name: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", name.lower())).strip("_")


def _split(md_text: str) -> tuple[str, str, str]:
    lines = md_text.splitlines(keepends=True)
    open_i = next(i for i, ln in enumerate(lines) if ln.rstrip("\n") == FENCE_OPEN)
    close_i = next(
        i for i in range(open_i + 1, len(lines)) if lines[i].rstrip("\n") == FENCE_CLOSE
    )
    return "".join(lines[: open_i + 1]), "".join(lines[open_i + 1 : close_i]), "".join(lines[close_i:])


def _block_entries(md_path: Path) -> list[dict]:
    entries = yaml.safe_load(_split(md_path.read_text(encoding="utf-8"))[1])
    if not isinstance(entries, list):
        raise SystemExit(f"{md_path}: block did not parse as a list")
    return entries


def _dump(entry: dict) -> str:
    return yaml.safe_dump(
        entry, sort_keys=False, allow_unicode=True, default_flow_style=False, width=4096
    )


def _measures_dir(md_path: Path) -> Path:
    return md_path.parent / "measures"


def _assign_slugs(entries: list[dict]) -> list[str]:
    order: list[str] = []
    used: set[str] = set()
    for e in entries:
        base = _slug(e["measure_name"])
        s, n = base, 2
        while s in used:
            s, n = f"{base}__{n}", n + 1
        used.add(s)
        order.append(s)
    return order


def _ensure_note(pre: str) -> str:
    if "Generated view." in pre:
        return pre
    lines = pre.splitlines(keepends=True)
    for i, ln in enumerate(lines):
        if ln.startswith("# "):
            lines.insert(i + 1, "\n" + GENERATED_NOTE)
            break
    return "".join(lines)


def _load_files(md_path: Path) -> list[dict]:
    mdir = _measures_dir(md_path)
    order = yaml.safe_load((mdir / "_index.yaml").read_text(encoding="utf-8"))["order"]
    on_disk = {p.stem for p in mdir.glob("*.yaml") if p.name != "_index.yaml"}
    if set(order) != on_disk:
        raise SystemExit(f"{mdir}: index/_files mismatch {set(order) ^ on_disk}")
    return [yaml.safe_load((mdir / f"{s}.yaml").read_text(encoding="utf-8")) for s in order]


def cmd_extract(_args) -> int:
    total = 0
    for md in dict_paths():
        entries = _block_entries(md)
        order = _assign_slugs(entries)
        mdir = _measures_dir(md)
        mdir.mkdir(parents=True, exist_ok=True)
        for slug, e in zip(order, entries):
            (mdir / f"{slug}.yaml").write_text(_dump(e), encoding="utf-8")
        (mdir / "_index.yaml").write_text(
            yaml.safe_dump({"order": order}, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        total += len(order)
        print(f"extract: {md.parent.name:16} {len(order):3} measures -> {mdir}")
    print(f"extract: {total} measures across {len(dict_paths())} dictionaries")
    return 0


def cmd_render(_args) -> int:
    for md in dict_paths():
        pre, _, post = _split(md.read_text(encoding="utf-8"))
        dumped = yaml.safe_dump(
            _load_files(md), sort_keys=False, allow_unicode=True,
            default_flow_style=False, width=4096,
        )
        body = re.sub(r"\n- ", "\n\n- ", dumped)
        md.write_text(_ensure_note(pre) + body + post, encoding="utf-8")
        print(f"render: {md}")
    return 0


def cmd_check(_args) -> int:
    failed = 0
    total = 0
    for md in dict_paths():
        block = _block_entries(md)
        files = _load_files(md)
        total += len(block)
        if len(block) != len(files):
            print(f"FAIL {md.parent.name}: count block={len(block)} files={len(files)}", file=sys.stderr)
            failed += 1
            continue
        drift = [i for i, (a, b) in enumerate(zip(block, files)) if a != b]
        if drift:
            i = drift[0]
            print(f"FAIL {md.parent.name}: entry #{i} differs "
                  f"({block[i].get('measure_name')!r})", file=sys.stderr)
            failed += 1
    if failed:
        print(f"check: {failed} dictionary/-ies drifted", file=sys.stderr)
        return 1
    print(f"check: OK — {total} measures identical between views and per-measure files")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("extract").set_defaults(func=cmd_extract)
    sub.add_parser("render").set_defaults(func=cmd_render)
    sub.add_parser("check").set_defaults(func=cmd_check)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
