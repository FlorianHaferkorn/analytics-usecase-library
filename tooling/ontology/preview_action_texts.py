#!/usr/bin/env python3
"""
Generate action text preview for Action Text measures.

Reads action codes from core/action_codes, produces tooling/ontology/out/action_text_preview.txt
with the exact text content intended for Action Text measures: multi-line, steps, trigger summary.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Reuse registry_builder's scan and parse
def _find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for _ in range(10):
        if (cur / ".git").exists():
            return cur
        cur = cur.parent
    return start


def _parse_yaml(path: Path) -> Any:
    try:
        import yaml
    except ImportError:
        return None
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _format_trigger_summary(raw: Dict[str, Any]) -> str:
    """Extract trigger levels and format as summary text."""
    trigger = raw.get("trigger", {})
    if not isinstance(trigger, dict):
        return ""
    levels = trigger.get("levels", {})
    if not isinstance(levels, dict):
        return ""
    parts: List[str] = []
    for lvl_name in sorted(levels.keys(), key=lambda x: (len(x), x)):
        lvl = levels.get(lvl_name)
        if not isinstance(lvl, dict):
            continue
        cond = lvl.get("condition", {})
        if not isinstance(cond, dict):
            continue
        kpi_id = cond.get("metric_kpi_id", "")
        comp = cond.get("comparator", "")
        th = cond.get("threshold", {})
        if isinstance(th, dict):
            val = th.get("value", "")
            unit = th.get("unit", "")
            if kpi_id and comp and val is not None:
                parts.append(f"  {lvl_name}: {kpi_id} {comp} {val} {unit}".strip())
    return "\n".join(parts) if parts else "  (no structured trigger levels)"


def _format_steps(raw: Dict[str, Any]) -> str:
    """Extract operational steps."""
    oe = raw.get("operational_execution", {})
    if not isinstance(oe, dict):
        return ""
    steps = oe.get("steps", [])
    if not isinstance(steps, list):
        return ""
    lines: List[str] = []
    for i, s in enumerate(steps, 1):
        if isinstance(s, str) and s.strip():
            lines.append(f"  {i}. {s.strip()}")
    return "\n".join(lines) if lines else "  (no steps defined)"


def _format_action_text(action_id: str, raw: Dict[str, Any]) -> str:
    name = raw.get("name", action_id)
    trigger_txt = _format_trigger_summary(raw)
    steps_txt = _format_steps(raw)
    buf = [f"--- {action_id} ---"]
    buf.append(f"Name: {name}")
    buf.append("")
    buf.append("Trigger:")
    buf.append(trigger_txt if trigger_txt else "  (no trigger)")
    buf.append("")
    buf.append("Steps:")
    buf.append(steps_txt if steps_txt else "  (no steps)")
    buf.append("")
    return "\n".join(buf)


def run(repo_root: Path, out_dir: Path) -> int:
    action_root = repo_root / "core" / "action_codes"
    if not action_root.exists():
        print("ERROR: core/action_codes not found")
        return 1

    action_files: List[Path] = []
    for p in action_root.rglob("*.yaml"):
        if "decision_spines" in p.parts:
            continue
        action_files.append(p)

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "action_text_preview.txt"
    sections: List[str] = []

    for p in sorted(action_files, key=lambda x: x.name):
        try:
            data = _parse_yaml(p)
        except Exception as e:
            sections.append(f"--- {p.name} ---\n(parse error: {e})\n")
            continue
        if not isinstance(data, dict):
            continue
        aid = data.get("id", p.stem)
        sections.append(_format_action_text(str(aid), data))

    content = "\n".join(sections)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Wrote {out_path} ({len(action_files)} action codes)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate action text preview for Action Text measures")
    parser.add_argument("--out-dir", default="tooling/ontology/out", help="Output directory")
    parser.add_argument("--repo-root", default=None, help="Repository root (default: auto-detect)")
    args = parser.parse_args()

    repo_root = Path(args.repo_root) if args.repo_root else _find_repo_root(Path.cwd())
    out_dir = (repo_root / args.out_dir).resolve()

    return run(repo_root, out_dir)


if __name__ == "__main__":
    sys.exit(main())
