#!/usr/bin/env python3
"""Machine-readable SSOT for the KPI catalog (Phase A of the streamline refactor).

The single source of truth for KPIs moves from the embedded YAML block inside
``core/kpi_catalog/KPI_Catalog.md`` to one file per KPI under
``core/kpi_catalog/kpis/<kpi_id>.yaml``. The Markdown becomes a *generated view*:
its fenced ``yaml`` block is rendered from the per-entity files, byte-stable
prose around it preserved verbatim.

Subcommands
-----------
extract  Parse the Markdown block and write per-KPI files + ``_index.yaml`` (order).
render   Rebuild the Markdown's ``yaml`` block from the per-KPI files (in index order).
check    Assert the per-KPI files carry data identical to the Markdown block
         (semantic round-trip — order-independent, formatting-independent).

``check`` is the CI guard: it fails if the SSOT files and the generated view
have drifted, so the two can never silently diverge.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
MD_PATH = REPO / "core" / "kpi_catalog" / "KPI_Catalog.md"
KPIS_DIR = REPO / "core" / "kpi_catalog" / "kpis"
INDEX = KPIS_DIR / "_index.yaml"
FENCE_OPEN = "```yaml"
FENCE_CLOSE = "```"

GENERATED_NOTE = (
    "> **Generated view.** The source of truth is the per-KPI files under "
    "[`kpis/`](kpis/). Edit those (or use ActionReady Studio); regenerate this "
    "file with `python tooling/codegen/kpi_catalog_files.py render`.\n"
)


def _split(md_text: str) -> tuple[str, str, str]:
    """Return (pre, body, post): text before+including the opening fence, the
    YAML body between fences, and the closing fence + everything after."""
    lines = md_text.splitlines(keepends=True)
    open_i = next(i for i, ln in enumerate(lines) if ln.rstrip("\n") == FENCE_OPEN)
    close_i = next(
        i for i in range(open_i + 1, len(lines)) if lines[i].rstrip("\n") == FENCE_CLOSE
    )
    pre = "".join(lines[: open_i + 1])
    body = "".join(lines[open_i + 1 : close_i])
    post = "".join(lines[close_i:])
    return pre, body, post


def _load_md_entries(md_path: Path) -> list[dict]:
    _, body, _ = _split(md_path.read_text(encoding="utf-8"))
    entries = yaml.safe_load(body)
    if not isinstance(entries, list):
        raise SystemExit("KPI catalog block did not parse as a list")
    return entries


def _dump(entry: dict) -> str:
    return yaml.safe_dump(
        entry, sort_keys=False, allow_unicode=True, default_flow_style=False, width=4096
    )


def _ensure_note(pre: str) -> str:
    if "Generated view." in pre:
        return pre
    lines = pre.splitlines(keepends=True)
    # insert the note after the H1 (first line starting with "# ")
    for i, ln in enumerate(lines):
        if ln.startswith("# "):
            lines.insert(i + 1, "\n" + GENERATED_NOTE)
            break
    return "".join(lines)


def cmd_extract(_args) -> int:
    entries = _load_md_entries(MD_PATH)
    KPIS_DIR.mkdir(parents=True, exist_ok=True)
    order: list[str] = []
    seen: set[str] = set()
    for e in entries:
        kid = e["kpi_id"]
        if kid in seen:
            raise SystemExit(f"duplicate kpi_id in catalog: {kid}")
        seen.add(kid)
        order.append(kid)
        (KPIS_DIR / f"{kid}.yaml").write_text(_dump(e), encoding="utf-8")
    INDEX.write_text(
        yaml.safe_dump({"order": order}, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    print(f"extract: wrote {len(order)} KPI files + _index.yaml to {KPIS_DIR}")
    return 0


def _load_files() -> list[dict]:
    order = yaml.safe_load(INDEX.read_text(encoding="utf-8"))["order"]
    files = {p.stem for p in KPIS_DIR.glob("*.yaml") if p.name != "_index.yaml"}
    if set(order) != files:
        missing = set(order) - files
        extra = files - set(order)
        raise SystemExit(f"index/_files mismatch — missing={missing} extra={extra}")
    return [yaml.safe_load((KPIS_DIR / f"{kid}.yaml").read_text("utf-8")) for kid in order]


def cmd_render(_args) -> int:
    pre, _, post = _split(MD_PATH.read_text(encoding="utf-8"))
    dumped = yaml.safe_dump(
        _load_files(), sort_keys=False, allow_unicode=True,
        default_flow_style=False, width=4096,
    )
    body = re.sub(r"\n- ", "\n\n- ", dumped)  # blank line between top-level entries
    MD_PATH.write_text(_ensure_note(pre) + body + post, encoding="utf-8")
    print(f"render: regenerated {MD_PATH} from {KPIS_DIR}")
    return 0


def cmd_check(_args) -> int:
    md = {e["kpi_id"]: e for e in _load_md_entries(MD_PATH)}
    files = {e["kpi_id"]: e for e in _load_files()}
    if md.keys() != files.keys():
        print(f"FAIL: id sets differ — only_md={md.keys() - files.keys()} "
              f"only_files={files.keys() - md.keys()}", file=sys.stderr)
        return 1
    drift = [k for k in md if md[k] != files[k]]
    if drift:
        print(f"FAIL: {len(drift)} KPI(s) drifted between view and files: {drift[:10]}",
              file=sys.stderr)
        return 1
    print(f"check: OK — {len(md)} KPIs identical between view and per-entity files")
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
