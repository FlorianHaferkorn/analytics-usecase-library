#!/usr/bin/env python3
"""
generate_action_payload.py — regenerate ActionPanel content for a use case.

Reads UseCase_Bracket.yaml (action_code_ids + payload_mode), loads each
action-code YAML, and writes the formatted ActionPanel visual.json into the
matching .Report in dist/.

If --stdout is set, prints the raw text to stdout instead of writing files.

Usage:
    python generate_action_payload.py --use-case COM-001
    python generate_action_payload.py --use-case COM-001 --mode summary
    python generate_action_payload.py --use-case COM-001 --stdout
    python generate_action_payload.py --all

Run from repository root.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    if __name__ == "__main__":
        print("ERROR: PyYAML required — pip install pyyaml", file=sys.stderr)
        sys.exit(1)
    raise

try:
    from products.fabric.powerbi.tooling.schema_registry import VISUAL_SCHEMA as _VISUAL_SCHEMA
except ImportError:
    _VISUAL_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.3.0/schema.json"


# ── Action code text formatter ────────────────────────────────────────────────

def _format_trigger(ac: Dict[str, Any]) -> Optional[str]:
    trigger = ac.get("trigger") or {}
    if not isinstance(trigger, dict):
        return None
    levels = trigger.get("levels") or {}
    if not isinstance(levels, dict):
        return None
    for level_key in ("L2", "L1", "L3"):
        level = levels.get(level_key)
        if not isinstance(level, dict):
            continue
        cond = level.get("condition") or {}
        if not isinstance(cond, dict):
            continue
        metric = cond.get("metric_kpi_id") or ""
        comp = cond.get("comparator") or ""
        th = cond.get("threshold")
        if isinstance(th, dict):
            val, unit = th.get("value"), (th.get("unit") or "")
        else:
            val, unit = th, ""
        if metric and comp and val is not None:
            comp_text = "<" if comp == "lt" else ">" if comp == "gt" else comp
            return f"{metric} {comp_text} {_format_threshold_value(val, unit)}".strip()
    return None


def _format_threshold_value(val: Any, unit: str) -> str:
    unit = (unit or "").strip()
    if unit in ("%", "pp"):
        return f"{val}{unit}"
    if unit:
        return f"{val} {unit}"
    return str(val)


def _format_impact(ac: Dict[str, Any]) -> Optional[str]:
    impact = ac.get("impact") or {}
    if isinstance(impact, dict) and impact.get("category"):
        cat = impact.get("category", "")
        val = ac.get("impact_valuation") or {}
        method = val.get("method", "") if isinstance(val, dict) else ""
        return f"Impact: {cat}, {method}" if method else f"Impact: {cat}"
    val = ac.get("impact_valuation") or {}
    if isinstance(val, dict) and val.get("method"):
        return f"Impact: {val.get('method')}"
    return None


def build_action_panel_text(
    action_code_ids: List[str],
    action_codes_root: Path,
    payload_mode: str = "full",
    title: str = "Recommended actions (from action codes)",
) -> str:
    """Build the ActionPanel plain text from action code YAMLs."""
    lines = [title, ""]

    for ac_id in action_code_ids:
        if not isinstance(ac_id, str) or not ac_id.strip():
            continue
        ac_id = ac_id.strip()

        # Find action code YAML (any subdirectory, skip decision_spines)
        found: Optional[Path] = None
        for path in action_codes_root.rglob(f"{ac_id}.yaml"):
            if "decision_spines" not in path.parts:
                found = path
                break

        if not found or not found.exists():
            lines.append(f"• {ac_id} (definition not found)")
            lines.append("")
            continue

        ac = yaml.safe_load(found.read_text(encoding="utf-8")) or {}
        name  = ac.get("name") or ac_id
        owner = ac.get("owner_role") or "—"
        lines.append(f"• {ac_id} — {name}")
        lines.append(f"  Owner: {owner}")

        if payload_mode != "minimal":
            trigger_text = _format_trigger(ac)
            if trigger_text:
                lines.append(f"  Trigger: {trigger_text}")
            impact_text = _format_impact(ac)
            if impact_text:
                lines.append(f"  {impact_text}")

        if payload_mode == "full":
            exec_block = ac.get("operational_execution") or {}
            steps = exec_block.get("steps") or [] if isinstance(exec_block, dict) else []
            for step in list(steps)[:3]:
                if isinstance(step, str):
                    lines.append(f"  · {step}")

        lines.append("")

    return "\n".join(lines).strip()


# ── ActionPanel visual.json writer ────────────────────────────────────────────

ACTION_PANEL_TEMPLATE: Dict[str, Any] = {
    "$schema": _VISUAL_SCHEMA,
    "name": "ActionPanel",
    "position": {
        "x": 1592, "y": 118, "z": 15000,
        "height": 930, "width": 296, "tabOrder": 3003
    },
    "visual": {
        "visualType": "textbox",
        "query": {"queryState": {"Data": {"projections": []}}},
        "objects": {
            # PBIR textbox text: general.paragraphs[].textRuns[].value (plain string). text.text
            # is not a textbox property (PBIR_FORMATTING_PROP_UNKNOWN, CLI Pin 0.4.0).
            "general": [{"properties": {"paragraphs": [{"textRuns": [{"value": ""}]}]}}]
        }
    }
}


def write_action_panel_visual(report_dir: Path, text: str) -> Path:
    """Write ActionPanel/visual.json in the Detail page directory."""
    pages_dir = report_dir / "definition" / "pages"
    detail_dir: Optional[Path] = None
    for d in pages_dir.iterdir():
        if d.is_dir() and "detail" in d.name.lower():
            detail_dir = d
            break
    if not detail_dir:
        raise FileNotFoundError(f"No Detail page directory found under {pages_dir}")

    panel_dir = detail_dir / "visuals" / "ActionPanel"
    panel_dir.mkdir(parents=True, exist_ok=True)
    out_path = panel_dir / "visual.json"

    visual = json.loads(json.dumps(ACTION_PANEL_TEMPLATE))  # deep copy
    # textRuns carry plain text -- no PBIR literal quoting/escaping.
    visual["visual"]["objects"]["general"][0]["properties"]["paragraphs"][0]["textRuns"][0]["value"] = text

    out_path.write_text(json.dumps(visual, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    return out_path


# ── Per-use-case processing ────────────────────────────────────────────────────

def process_use_case(
    uc_id: str,
    uc_root: Path,
    dist_root: Path,
    action_codes_root: Path,
    mode_override: Optional[str],
    stdout_only: bool,
) -> bool:
    """Returns True on success."""
    # Locate bracket
    bracket_path: Optional[Path] = None
    for d in uc_root.iterdir():
        if d.is_dir() and d.name.startswith(uc_id):
            candidate = d / "UseCase_Bracket.yaml"
            if candidate.exists():
                bracket_path = candidate
                break

    if not bracket_path:
        print(f"  WARN [{uc_id}] UseCase_Bracket.yaml not found under {uc_root}", file=sys.stderr)
        return False

    bracket = yaml.safe_load(bracket_path.read_text(encoding="utf-8")) or {}
    orch     = bracket.get("orchestration") or {}
    ids      = orch.get("action_code_ids") or []
    if not ids:
        print(f"  [{uc_id}] No action_code_ids in bracket — skipping")
        return True

    ux       = bracket.get("ux_layout_rules") or {}
    p2       = ux.get("page_2_execution") or {}
    c300     = p2.get("component_300s") or {}
    mode     = mode_override or (c300.get("payload_mode") or "full").strip().lower()

    text = build_action_panel_text(
        action_code_ids=ids,
        action_codes_root=action_codes_root,
        payload_mode=mode,
    )

    if stdout_only:
        print(f"=== {uc_id} ActionPanel ({mode}) ===")
        print(text)
        print()
        return True

    # Prefer orchestrator-canonical report folder (use case directory name), then any match.
    uc_folder_name = bracket_path.parent.name
    preferred = dist_root / f"{uc_folder_name}.Report"
    report_dir: Optional[Path] = preferred if preferred.is_dir() else None
    if report_dir is None:
        for d in sorted(dist_root.iterdir()):
            if d.is_dir() and d.name.startswith(uc_id) and d.name.endswith(".Report"):
                report_dir = d
                break

    if not report_dir:
        print(f"  WARN [{uc_id}] No .Report directory found in {dist_root} — skipping write")
        return False

    try:
        out = write_action_panel_visual(report_dir, text)
        print(f"  OK  [{uc_id}] ActionPanel written -> {out.relative_to(dist_root.parent.parent.parent.parent)}")
    except Exception as e:
        print(f"  FAIL [{uc_id}] {e}", file=sys.stderr)
        return False

    return True


# ── Main ──────────────────────────────────────────────────────────────────────

def find_repo_root() -> Path:
    p = Path(__file__).resolve()
    while p != p.parent:
        if (p / "core").exists() and (p / "tooling").exists():
            return p
        p = p.parent
    raise RuntimeError("Repository root not found")


def main() -> None:
    parser = argparse.ArgumentParser(description="Regenerate ActionPanel content from action-code YAML")
    parser.add_argument("--use-case",  help="Use case ID (e.g. COM-001)")
    parser.add_argument("--all",       action="store_true", help="Process all use cases in use-case-root")
    parser.add_argument("--mode",      choices=["full", "summary", "minimal"], help="Override payload_mode from bracket")
    parser.add_argument("--stdout",    action="store_true", help="Print text to stdout only (no file writes)")
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--dist-root", type=Path, default=None)
    parser.add_argument("--use-case-root", type=Path, default=None)
    args = parser.parse_args()

    if not args.use_case and not args.all:
        parser.error("Specify --use-case <ID> or --all")

    repo_root = args.repo_root.resolve() if args.repo_root else find_repo_root()
    dist_root = (args.dist_root.resolve() if args.dist_root
                 else repo_root / "products" / "fabric" / "powerbi" / "dist")
    uc_root   = (args.use_case_root.resolve() if args.use_case_root
                 else repo_root / "core" / "usecases" / "core")
    ac_root   = repo_root / "core" / "action_codes"

    if args.all:
        uc_ids = sorted(
            re.match(r"^([A-Z]{2,3}-\d+)", d.name).group(1)
            for d in uc_root.iterdir()
            if d.is_dir() and re.match(r"^([A-Z]{2,3}-\d+)", d.name)
            and (d / "UseCase_Bracket.yaml").exists()
        )
    else:
        uc_ids = [args.use_case]

    failures = 0
    for uc_id in uc_ids:
        ok = process_use_case(
            uc_id=uc_id,
            uc_root=uc_root,
            dist_root=dist_root,
            action_codes_root=ac_root,
            mode_override=args.mode,
            stdout_only=args.stdout,
        )
        if not ok:
            failures += 1

    if failures:
        print(f"\n{failures} use case(s) failed.", file=sys.stderr)
        sys.exit(1)
    print("\nDone.")


if __name__ == "__main__":
    main()
