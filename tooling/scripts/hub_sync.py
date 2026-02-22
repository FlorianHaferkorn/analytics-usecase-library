"""
Sync Core YAML artifacts to Starlight (Astro) documentation Hub.

Reads governed YAML from core/ (action codes, UseCase_Bracket, decision spines)
and generates .mdx files in docs_hub/src/content/docs/ with:
- Tab/section "Business Logic (Agnostic)": canonical YAML or summary
- Tab/section "Implementation Details": placeholder for Fabric/TMDL or product-specific notes

Run from repo root after Core changes to keep the living docs in sync.
Usage:
  python tooling/scripts/hub_sync.py [--out docs_hub/src/content/docs] [--dry-run]
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


def _repo_root() -> Path:
    root = Path(__file__).resolve().parent.parent.parent
    assert (root / "core").is_dir(), f"Expected core/ under {root}"
    return root


def _read_yaml(path: Path) -> dict[str, Any] | None:
    if yaml is None:
        return None
    try:
        text = path.read_text(encoding="utf-8-sig")
        return yaml.safe_load(text) or {}
    except Exception:
        return None


def _escape_mdx(s: str) -> str:
    return s.replace("|", "\\|").replace("<", "\\<").replace(">", "\\>")


def _collect_core_yamls(root: Path) -> list[tuple[Path, str, str]]:
    """Collect (path, slug, title) for each Core YAML to document."""
    out: list[tuple[Path, str, str]] = []

    # Action codes: core/action_codes/<Domain>/*.yaml
    ac_dir = root / "core" / "action_codes"
    if ac_dir.is_dir():
        for yf in ac_dir.rglob("*.yaml"):
            if yf.name.startswith("ActionCode_") or "TEMPLATE" in yf.name:
                continue
            if "decision_spines" in yf.parts:
                continue
            data = _read_yaml(yf)
            aid = (data or {}).get("id") or yf.stem
            rel = yf.relative_to(ac_dir)
            slug = f"action-codes/{rel.parent.as_posix().lower()}/{aid}"
            title = (data or {}).get("name") or aid
            out.append((yf, slug, title))

    # Use case brackets: core/usecases/**/UseCase_Bracket.yaml
    uc_base = root / "core" / "usecases"
    if uc_base.is_dir():
        for yf in uc_base.rglob("UseCase_Bracket.yaml"):
            data = _read_yaml(yf)
            uid = (data or {}).get("id") or yf.parent.name.split("_")[0] if yf.parent else "unknown"
            title = (data or {}).get("title") or uid
            out.append((yf, f"use-cases/{uid}", title))

    # Decision spines: core/action_codes/decision_spines/*.yaml
    ds_dir = root / "core" / "action_codes" / "decision_spines"
    if ds_dir.is_dir():
        for yf in sorted(ds_dir.glob("*.yaml")):
            data = _read_yaml(yf)
            name = (data or {}).get("id") or (data or {}).get("name") or yf.stem
            out.append((yf, f"decision-spines/{yf.stem}", name))

    return out


def _mdx_content(path: Path, title: str, slug: str, yaml_content: str) -> str:
    return f"""---
title: {_escape_mdx(title)}
description: Core definition — {path.name}
sidebar:
  label: {_escape_mdx(title)}
---

## Business Logic (Agnostic)

Canonical definition from `core/`:

```yaml
{yaml_content}
```

## Implementation Details (Fabric / TMDL)

Implementation-specific notes and links (e.g. measures, report slots) go here.  
See `products/fabric_powerbi/` for the current lead implementation.
"""


def run(root: Path, out_dir: Path, dry_run: bool) -> None:
    out_dir = out_dir.resolve()
    items = _collect_core_yamls(root)
    for path, slug, title in items:
        raw = path.read_text(encoding="utf-8-sig")
        mdx = _mdx_content(path, title, slug, raw)
        mdx_path = out_dir / f"{slug}.mdx"
        if dry_run:
            print(f"[dry-run] would write {mdx_path.relative_to(root)}")
            continue
        mdx_path.parent.mkdir(parents=True, exist_ok=True)
        mdx_path.write_text(mdx, encoding="utf-8")
        print(f"Wrote {mdx_path.relative_to(root)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync Core YAML to Starlight docs_hub")
    root = _repo_root()
    default_out = root / "docs_hub" / "src" / "content" / "docs"
    parser.add_argument("--out", type=Path, default=default_out, help="Output directory for .mdx files")
    parser.add_argument("--dry-run", action="store_true", help="Print paths only, do not write")
    args = parser.parse_args()
    if yaml is None:
        print("Warning: PyYAML not installed. Install with: pip install pyyaml")
    run(root, args.out, args.dry_run)


if __name__ == "__main__":
    main()
