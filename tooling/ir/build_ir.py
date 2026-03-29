"""
Build ActionReady IR (Intermediate Representation) from Core ABI outputs.

Inputs (Core ABI):
- tooling/ontology/out/master_registry.json
- tooling/ontology/out/value_map.json

Optional (for IR-first adapters):
- --kpi-catalog: scan core/kpi_catalog for measure specs (dax_expression, formatString, etc.)
  and add measure_spec to IR so adapters need not read Core.

Output:
- tooling/ir/out/ir_v1.json (default)

This script is intentionally deterministic and tool-agnostic.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _extract_scalar(chunk: str, key: str) -> str | None:
    """Extract scalar value for key (key: value or key: \"value\"). Matches at any indentation.
    Unquoted values may contain spaces (e.g. kpi_key: List Price Amount); we take the rest of the line until # or newline."""
    m = re.search(rf"(?m)^\s*{re.escape(key)}\s*:\s*(?:\|\s*)?(?:\r?\n)?(?:\s*\"([^\"]*)\"|\s*'([^']*)'|\s*([^\r\n#]+))", chunk)
    if not m:
        return None
    raw = (m.group(1) or m.group(2) or m.group(3) or "").strip()
    # Strip trailing inline comment
    if "#" in raw:
        raw = raw.split("#", 1)[0].strip()
    return raw or None


def _extract_literal_block(chunk: str, key: str) -> str | None:
    """Extract YAML literal block value for key (key: | followed by indented lines)."""
    m = re.search(rf"(?m)^(\s*){re.escape(key)}\s*:\s*\|\s*\r?\n", chunk)
    if not m:
        return None
    key_indent = len(m.group(1))
    start = m.end()
    lines: list[str] = []
    for line in chunk[start:].splitlines():
        if line.strip() and re.match(r"^\s*", line):
            line_indent = len(line) - len(line.lstrip())
            if line_indent <= key_indent:
                break
        lines.append(line)
    # Strip common indentation
    non_empty = [ln for ln in lines if ln.strip()]
    if not non_empty:
        return None
    min_indent = min(len(ln) - len(ln.lstrip()) for ln in non_empty)
    result = "\n".join(ln[min_indent:] if len(ln) >= min_indent else ln for ln in lines)
    return result.rstrip() or None


def _extract_list(chunk: str, key: str) -> list[str]:
    """Extract YAML list for key (key: [] or key: followed by indented lines starting with -)."""
    m = re.search(rf"(?m)^(\s*){re.escape(key)}\s*:\s*(?:\r?\n)?", chunk)
    if not m:
        return []
    key_indent = len(m.group(1))
    start = m.end()
    # Inline empty list
    rest = chunk[start : start + 50].strip()
    if rest.startswith("[]"):
        return []
    items: list[str] = []
    for line in chunk[start:].splitlines():
        line_stripped = line.strip()
        if not line:
            if items:
                break
            continue
        line_indent = len(line) - len(line.lstrip())
        # New key at same or less indent: stop
        if line_indent <= key_indent and re.match(r"^\s*\w+\s*:", line):
            break
        bullet = re.match(r"^\s*-\s*(.+)$", line)
        if bullet:
            val = bullet.group(1).strip().strip("'\"").split("#")[0].strip()
            if val:
                items.append(val)
        elif items and line_indent <= key_indent:
            break
    return items


def _scan_kpi_catalog(root: Path) -> Dict[str, Dict[str, Any]]:
    """
    Scan KPI catalog .md files for yaml blocks; extract per-kpi_id measure specs
    (measure_name, description, purpose, depends_on_measures).
    Tool-specific fields (dax_expression, format_string) come from the Fabric overlay.
    """
    measure_spec: Dict[str, Dict[str, Any]] = {}
    for path in sorted(root.glob("*.md")):
        if path.name in ("README.md", "SCHEMA.md"):
            continue
        text = path.read_text(encoding="utf-8-sig")
        for block in re.finditer(r"```yaml\s*(.*?)```", text, re.DOTALL):
            yaml_content = block.group(1)
            # Split into list items by "- kpi_id:"
            parts = re.split(r"(?m)^\s*-\s*kpi_id\s*:\s*", yaml_content)
            for i, part in enumerate(parts):
                if i == 0 and not re.search(r"(?m)^\s*-\s*kpi_id\s*:\s*", yaml_content):
                    continue
                kpi_id_m = re.match(r"([a-z][a-z0-9_.]+)\s*[\r\n#]", part)
                if not kpi_id_m:
                    continue
                kpi_id = kpi_id_m.group(1).strip()
                # Prefer nested technical.* then top-level keys
                chunk = part
                dax_expr = _extract_literal_block(chunk, "dax_expression") or _extract_scalar(chunk, "dax_expression")
                if not dax_expr and "technical:" in chunk:
                    sub = re.search(r"(?s)technical:\s*\n(.*?)(?=\n\w|\n\s*\n\w|$)", chunk)
                    if sub:
                        dax_expr = _extract_literal_block(sub.group(1), "dax_expression") or _extract_scalar(sub.group(1), "dax_expression")
                format_str = _extract_scalar(chunk, "formatString")
                if not format_str and "technical:" in chunk:
                    sub = re.search(r"(?s)technical:\s*\n(.*?)(?=\n\w|\n\s*\n\w|$)", chunk)
                    if sub:
                        format_str = _extract_scalar(sub.group(1), "formatString")
                dax_name = _extract_scalar(chunk, "measure_name") or _extract_scalar(chunk, "dax_name")
                if not dax_name and "technical:" in chunk:
                    sub = re.search(r"(?s)technical:\s*\n(.*?)(?=\n\w|\n\s*\n\w|$)", chunk)
                    if sub:
                        dax_name = _extract_scalar(sub.group(1), "measure_name") or _extract_scalar(sub.group(1), "dax_name")
                display_folder = _extract_scalar(chunk, "displayFolder") or ""
                description = _extract_scalar(chunk, "description")
                if not description and "technical:" in chunk:
                    sub = re.search(r"(?s)technical:\s*\n(.*?)(?=\n\w|\n\s*\n\w|$)", chunk)
                    if sub:
                        description = _extract_scalar(sub.group(1), "description")
                purpose = _extract_scalar(chunk, "purpose")
                if not purpose and "business:" in chunk:
                    sub = re.search(r"(?s)business:\s*\n(.*?)(?=\n\w|\n\s*\n\w|$)", chunk)
                    if sub:
                        purpose = _extract_scalar(sub.group(1), "purpose")
                kpi_key = _extract_scalar(chunk, "kpi_key")
                depends_on = _extract_list(chunk, "depends_on_measures")
                if not depends_on and "technical:" in chunk:
                    sub = re.search(r"(?s)technical:\s*\n(.*?)(?=\n\w|\n\s*\n\w|$)", chunk)
                    if sub:
                        depends_on = _extract_list(sub.group(1), "depends_on_measures")
                if kpi_id not in measure_spec or dax_expr:
                    measure_spec[kpi_id] = {
                        "dax_expression": dax_expr,
                        "format_string": format_str or "",
                        "dax_name": dax_name,
                        "display_folder": display_folder,
                        "description": description or "",
                        "purpose": purpose or "",
                        "kpi_key": kpi_key,
                        "depends_on_measures": depends_on,
                    }
    return measure_spec


def _load_fabric_overlay(path: Path) -> Dict[str, Dict[str, Any]]:
    """Load Fabric measure overlay YAML: kpi_id -> { dax_expression, format_string, dax_name, display_folder }."""
    if not path.exists():
        return {}
    if yaml is None:
        raise SystemExit("PyYAML required for --fabric-overlay; install with: pip install pyyaml")
    raw = yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
    overlay: Dict[str, Dict[str, Any]] = {}
    for kpi_id, fields in raw.items():
        if not isinstance(fields, dict):
            continue
        overlay[kpi_id] = {
            "dax_expression": fields.get("dax_expression"),
            "format_string": fields.get("format_string") or "",
            "dax_name": fields.get("dax_name"),
            "display_folder": fields.get("display_folder") or "",
        }
    return overlay


def _merge_fabric_overlay(
    measure_spec: Dict[str, Dict[str, Any]], overlay: Dict[str, Dict[str, Any]]
) -> None:
    """Merge Fabric overlay into measure_spec in place. Overlay overwrites dax_expression, format_string, dax_name, display_folder."""
    for kpi_id, fab in overlay.items():
        if kpi_id in measure_spec:
            if fab.get("dax_expression") is not None:
                measure_spec[kpi_id]["dax_expression"] = fab["dax_expression"]
            if fab.get("format_string") != "":
                measure_spec[kpi_id]["format_string"] = fab["format_string"]
            if fab.get("dax_name") is not None:
                measure_spec[kpi_id]["dax_name"] = fab["dax_name"]
            if fab.get("display_folder") != "":
                measure_spec[kpi_id]["display_folder"] = fab["display_folder"]
        else:
            measure_spec[kpi_id] = {
                "dax_expression": fab.get("dax_expression"),
                "format_string": fab.get("format_string") or "",
                "dax_name": fab.get("dax_name"),
                "display_folder": fab.get("display_folder") or "",
                "description": "",
                "purpose": "",
                "kpi_key": None,
                "depends_on_measures": [],
            }


def _write_fabric_overlay(measure_spec: Dict[str, Dict[str, Any]], path: Path) -> None:
    """Write Fabric-relevant fields of measure_spec to a YAML overlay file."""
    if yaml is None:
        raise SystemExit("PyYAML required for --write-fabric-overlay; install with: pip install pyyaml")
    path.parent.mkdir(parents=True, exist_ok=True)
    overlay = {
        kpi_id: {
            "dax_expression": spec.get("dax_expression"),
            "format_string": spec.get("format_string") or "",
            "dax_name": spec.get("dax_name"),
            "display_folder": spec.get("display_folder") or "",
        }
        for kpi_id, spec in sorted(measure_spec.items())
    }
    path.write_text(yaml.dump(overlay, default_flow_style=False, allow_unicode=True, sort_keys=False), encoding="utf-8")


def build_ir(
    *,
    master_registry: Dict[str, Any],
    value_map: Dict[str, Any],
    ir_version: str,
    master_path: str,
    value_path: str,
    measure_spec: Dict[str, Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    objects = master_registry.get("objects") or {}
    use_cases = objects.get("use_cases") or {}
    kpis = objects.get("kpis") or {}
    action_codes = objects.get("action_codes") or {}

    # Keep transformation conservative: copy stable fields only.
    ir = {
        "ir_version": ir_version,
        "generated_at_utc": _utc_now_iso(),
        "source": {
            "core_abi": {
                "core_abi_version": (master_registry.get("meta") or {}).get("registry_version"),
                "master_registry_path": master_path,
                "value_map_path": value_path,
            }
        },
        "objects": {
            "use_cases": {},
            "kpis": {},
            "action_codes": {},
        },
    }

    for uc_id, u in use_cases.items():
        if not isinstance(u, dict):
            continue
        ir["objects"]["use_cases"][uc_id] = {
            "id": u.get("id") or uc_id,
            "title": u.get("title"),
            "domain": u.get("domain") or "",
            "governance": {
                "owner_role": (u.get("governance") or {}).get("owner_role"),
                "steward_role": (u.get("governance") or {}).get("steward_role"),
            },
            "orchestration": {
                "strategic_kpi_id": (u.get("orchestration") or {}).get("strategic_kpi_id"),
                "influencing_kpi_ids": list((u.get("orchestration") or {}).get("influencing_kpi_ids") or []),
                "action_code_ids": list((u.get("orchestration") or {}).get("action_code_ids") or []),
            },
            "value_driver_model": u.get("value_driver_model"),
            "ux_layout_rules": u.get("ux_layout_rules"),
            "documentation": u.get("documentation"),
        }

    for kpi_id, k in kpis.items():
        if not isinstance(k, dict):
            continue
        ir["objects"]["kpis"][kpi_id] = {
            "id": k.get("id") or kpi_id,
            "kpi_role": k.get("kpi_role"),
            "computed_role_global": k.get("computed_role_global"),
            "governance": k.get("governance"),
            "trust_score": k.get("trust_score"),
            "linked_domain_contracts": list(k.get("linked_domain_contracts") or []),
            "data_contract_risk": k.get("data_contract_risk"),
            "causal_links": k.get("causal_links"),
            "source": k.get("source"),
        }

    for aid, a in action_codes.items():
        if not isinstance(a, dict):
            continue
        gov = a.get("governance") or {}
        entry = {
            "id": a.get("id") or aid,
            "name": a.get("name"),
            "owner_domain": a.get("owner_domain"),
            "governance": {"owner_role": gov.get("owner_role"), "steward_role": gov.get("steward_role")},
            "impact_valuation": a.get("impact_valuation"),
            "execution_bridge": a.get("execution_bridge"),
            "source": a.get("source"),
        }
        if a.get("trigger_summary") is not None:
            entry["trigger_summary"] = a.get("trigger_summary")
        if a.get("owner_role") is not None:
            entry["owner_role"] = a.get("owner_role")
        if a.get("steps") is not None:
            entry["steps"] = list(a.get("steps"))
        ir["objects"]["action_codes"][aid] = entry

    # Optional: include impact paths for adapters that need prioritization.
    if isinstance(value_map, dict):
        impact_paths = value_map.get("impact_paths")
        if impact_paths is not None:
            # Keep this as non-schema additional data for now (future: extend schema additively).
            ir.setdefault("extras", {})["impact_paths"] = impact_paths

    # Optional: measure specs for IR-first adapters (no direct Core reads).
    if measure_spec is not None:
        ir["measure_spec"] = measure_spec

    return ir


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build ActionReady IR from registry outputs (Core ABI).")
    p.add_argument("--master-registry", default="tooling/ontology/out/master_registry.json")
    p.add_argument("--value-map", default="tooling/ontology/out/value_map.json")
    p.add_argument("--out", default="tooling/ir/out/ir_v1.json")
    p.add_argument("--ir-version", default="1.0")
    p.add_argument("--kpi-catalog", default="", help="Optional path to core/kpi_catalog to add measure_spec to IR (for IR-first adapters).")
    p.add_argument("--fabric-overlay", default="", help="Optional path to Fabric measure overlay YAML; merged over measure_spec (dax_expression, format_string, dax_name, display_folder).")
    p.add_argument("--write-fabric-overlay", default="", help="Optional path to write current measure_spec Fabric fields to YAML (one-time extraction from KPI catalog).")
    args = p.parse_args(argv)

    master_path = Path(args.master_registry)
    value_path = Path(args.value_map)
    out_path = Path(args.out)

    if not master_path.exists():
        raise SystemExit(f"Missing master registry: {master_path}")
    if not value_path.exists():
        raise SystemExit(f"Missing value map: {value_path}")

    master_registry = _read_json(master_path)
    value_map = _read_json(value_path)

    measure_spec: Dict[str, Dict[str, Any]] | None = None
    if args.kpi_catalog:
        kpi_root = Path(args.kpi_catalog)
        if not kpi_root.is_dir():
            raise SystemExit(f"KPI catalog path is not a directory: {kpi_root}")
        measure_spec = _scan_kpi_catalog(kpi_root)
        print(f"measure_spec: {len(measure_spec)} KPIs from {kpi_root.as_posix()}")

        if args.fabric_overlay:
            overlay_path = Path(args.fabric_overlay)
            overlay = _load_fabric_overlay(overlay_path)
            _merge_fabric_overlay(measure_spec, overlay)
            print(f"merged fabric overlay: {overlay_path.as_posix()} ({len(overlay)} entries)")

        if args.write_fabric_overlay:
            out_overlay = Path(args.write_fabric_overlay)
            _write_fabric_overlay(measure_spec, out_overlay)
            print(f"wrote fabric overlay: {out_overlay.as_posix()}")

    ir = build_ir(
        master_registry=master_registry,
        value_map=value_map,
        ir_version=args.ir_version,
        master_path=str(master_path.as_posix()),
        value_path=str(value_path.as_posix()),
        measure_spec=measure_spec,
    )
    _write_json(out_path, ir)
    print(f"IR written: {out_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

