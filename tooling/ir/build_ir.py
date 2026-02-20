"""
Build ActionReady IR (Intermediate Representation) from Core ABI outputs.

Inputs (Core ABI):
- tooling/ontology/out/master_registry.json
- tooling/ontology/out/value_map.json

Output:
- tooling/ir/out/ir_v1.json (default)

This script is intentionally deterministic and tool-agnostic.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_ir(*, master_registry: Dict[str, Any], value_map: Dict[str, Any], ir_version: str, master_path: str, value_path: str) -> Dict[str, Any]:
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
        ir["objects"]["action_codes"][aid] = {
            "id": a.get("id") or aid,
            "name": a.get("name"),
            "owner_domain": a.get("owner_domain"),
            "governance": {"owner_role": gov.get("owner_role"), "steward_role": gov.get("steward_role")},
            "impact_valuation": a.get("impact_valuation"),
            "execution_bridge": a.get("execution_bridge"),
            "source": a.get("source"),
        }

    # Optional: include impact paths for adapters that need prioritization.
    if isinstance(value_map, dict):
        impact_paths = value_map.get("impact_paths")
        if impact_paths is not None:
            # Keep this as non-schema additional data for now (future: extend schema additively).
            ir.setdefault("extras", {})["impact_paths"] = impact_paths

    return ir


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build ActionReady IR from registry outputs (Core ABI).")
    p.add_argument("--master-registry", default="tooling/ontology/out/master_registry.json")
    p.add_argument("--value-map", default="tooling/ontology/out/value_map.json")
    p.add_argument("--out", default="tooling/ir/out/ir_v1.json")
    p.add_argument("--ir-version", default="1.0")
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

    ir = build_ir(
        master_registry=master_registry,
        value_map=value_map,
        ir_version=args.ir_version,
        master_path=str(master_path.as_posix()),
        value_path=str(value_path.as_posix()),
    )
    _write_json(out_path, ir)
    print(f"IR written: {out_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

