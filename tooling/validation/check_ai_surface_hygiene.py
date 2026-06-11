#!/usr/bin/env python3
"""
check_ai_surface_hygiene.py — Epic C: AI-surface hygiene (model clarity).

Two anti-patterns the Tabular Editor AI-readiness guide calls out:

  C1 — visible surrogate/FK keys. Surrogate join keys (``*Key``) are meaningless on
       the AI/user surface and should be hidden. Reports every visible ``*Key``
       column in the generated model; ``--fix`` hides them (adds ``isHidden``).

  C2 — name-restating / low-information descriptions. A description that merely
       restates the object name (or is below a minimum-information bar) tells an LLM
       nothing it can't read off the name. Lints the governed descriptions
       (data-contract columns + measure-dictionary definitions).

Both fold into the H8 AI-Readiness gate (see tooling/health_scorecard.py) and run
standalone in CI. Default is a report (exit 0); ``--strict`` exits 1 on any
violation.

Usage::

    python tooling/validation/check_ai_surface_hygiene.py --domain Commercial
    python tooling/validation/check_ai_surface_hygiene.py --domain Commercial --fix
    python tooling/validation/check_ai_surface_hygiene.py --strict
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root

from tooling.generator_core.ai_description import build_table_descriptions

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

DOMAIN_CONTRACT: Dict[str, str] = {
    "Commercial": "commercial_sales.yaml",
    "Finance": "finance.yaml",
    "Operations": "operations.yaml",
    "SupplyChain": "supply_chain.yaml",
    "Experience": "experience.yaml",
}

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DIST = _REPO_ROOT / "products" / "fabric" / "powerbi" / "dist"
_CONTRACTS = _REPO_ROOT / "core" / "data_contracts" / "domains"
_MEASURE_DOMAINS = _REPO_ROOT / "core" / "semantic_models" / "domains"

_COLUMN_RE = re.compile(r"^\tcolumn (.+)$")
_KEY_SUFFIX = "Key"
_FENCE_RE = re.compile(r"```yaml\s*\n(.*?)```", re.DOTALL)


# ─────────────────────────────────────────────────────────────────────────────
# C1 — visible surrogate/FK keys (reads the generated model)
# ─────────────────────────────────────────────────────────────────────────────

def _iter_tables(dist_root: Path, domain: str) -> List[Path]:
    tdir = Path(dist_root) / f"{domain}.SemanticModel" / "definition" / "tables"
    return [f for f in sorted(tdir.glob("*.tmdl")) if not f.name.startswith("_")] if tdir.is_dir() else []


def _column_blocks(lines: List[str]):
    """Yield (col_name, start_idx, end_idx) for each ``\\tcolumn`` block."""
    i = 0
    while i < len(lines):
        m = _COLUMN_RE.match(lines[i])
        if not m:
            i += 1
            continue
        name = m.group(1).strip().strip("'")
        j = i + 1
        while j < len(lines) and (lines[j].startswith("\t\t") or lines[j].strip() == ""):
            j += 1
        yield name, i, j
        i = j


def visible_keys(dist_root: Path = _DIST, domain: str = "Commercial") -> List[str]:
    """Return ``table.column`` for every ``*Key`` column that is not ``isHidden``."""
    out: List[str] = []
    for f in _iter_tables(dist_root, domain):
        lines = f.read_text(encoding="utf-8").splitlines()
        for name, start, end in _column_blocks(lines):
            if not name.endswith(_KEY_SUFFIX):
                continue
            hidden = any(lines[k].strip() == "isHidden" for k in range(start, end))
            if not hidden:
                out.append(f"{f.stem}.{name}")
    return out


def hide_visible_keys(dist_root: Path = _DIST, domain: str = "Commercial") -> List[str]:
    """Hide every visible ``*Key`` column (insert ``isHidden`` after ``dataType``).
    Idempotent; returns the ``table.column`` list that was changed."""
    fixed: List[str] = []
    for f in _iter_tables(dist_root, domain):
        lines = f.read_text(encoding="utf-8").splitlines()
        # Work back-to-front so insertions don't shift earlier indices.
        edits: List[Tuple[int, str]] = []
        for name, start, end in _column_blocks(lines):
            if not name.endswith(_KEY_SUFFIX):
                continue
            if any(lines[k].strip() == "isHidden" for k in range(start, end)):
                continue
            insert_at = start + 1
            for k in range(start + 1, end):
                if lines[k].lstrip().startswith("dataType:"):
                    insert_at = k + 1
                    break
            edits.append((insert_at, f"{f.stem}.{name}"))
        for insert_at, loc in sorted(edits, reverse=True):
            lines.insert(insert_at, "\t\tisHidden")
            fixed.append(loc)
        if edits:
            f.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return sorted(fixed)


# ─────────────────────────────────────────────────────────────────────────────
# C2 — description-quality lint (governed sources)
# ─────────────────────────────────────────────────────────────────────────────

def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def weak_reason(name: str, desc: str) -> str | None:
    """Return why ``desc`` is weak for object ``name``, or None when it clears the bar."""
    d, n = _norm(desc), _norm(name)
    if not d:
        return None  # absence is a coverage gap, not a quality violation
    if d == n:
        return "restates the name"
    words = d.split()
    if len(words) < 3:
        return "below minimum-information bar (<3 words)"
    extra = [w for w in words if w not in set(n.split())]
    if len(extra) < 2:
        return "adds <2 words beyond the name"
    return None


def weak_descriptions(repo_root: Path = _REPO_ROOT, domain: str = "Commercial") -> List[Tuple[str, str]]:
    """Lint contract column descriptions + measure-dictionary definitions.
    Returns ``[(object, reason), ...]``."""
    out: List[Tuple[str, str]] = []
    contract = Path(repo_root) / "core" / "data_contracts" / "domains" / DOMAIN_CONTRACT[domain]
    for tbl in build_table_descriptions(contract):
        for col in tbl.columns:
            reason = weak_reason(col.name, col.description)
            if reason:
                out.append((f"{tbl.name}.{col.name}", reason))
    if yaml is not None:
        for md in sorted((Path(repo_root) / "core" / "semantic_models" / "domains" / domain).glob("Measure_Dictionary_*.md")):
            fence = _FENCE_RE.search(md.read_text(encoding="utf-8"))
            if not fence:
                continue
            try:
                entries = yaml.safe_load(fence.group(1)) or []
            except yaml.YAMLError:
                continue
            for e in entries if isinstance(entries, list) else []:
                if not isinstance(e, dict) or not e.get("measure_name"):
                    continue
                desc = (e.get("documentation") or {}).get("description", "")
                reason = weak_reason(e["measure_name"], desc)
                if reason:
                    out.append((f"measure:{e['measure_name']}", reason))
    return out


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AI-surface hygiene: visible keys + weak descriptions.")
    parser.add_argument("--domain", "-d", choices=list(DOMAIN_CONTRACT.keys()))
    parser.add_argument("--fix", action="store_true", help="Hide visible *Key columns (C1)")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on any violation")
    args = parser.parse_args(argv)

    domains = [args.domain] if args.domain else list(DOMAIN_CONTRACT)
    violations = 0
    for domain in domains:
        if not (_CONTRACTS / DOMAIN_CONTRACT[domain]).exists():
            continue
        if args.fix:
            fixed = hide_visible_keys(_DIST, domain)
            if fixed:
                print(f"{domain}: hid {len(fixed)} visible key column(s): {', '.join(fixed)}")
        keys = visible_keys(_DIST, domain)
        weak = weak_descriptions(_REPO_ROOT, domain)
        if keys or weak:
            print(f"{domain}: {len(keys)} visible key(s), {len(weak)} weak description(s)")
            for k in keys:
                print(f"    visible key:      {k}")
            for obj, reason in weak:
                print(f"    weak description: {obj} — {reason}")
            violations += len(keys) + len(weak)
        else:
            print(f"{domain}: clean (0 visible keys, 0 weak descriptions)")
    if args.strict and violations:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
