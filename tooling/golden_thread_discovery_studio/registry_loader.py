"""
Load Registry and catalog data for Golden Thread Discovery Studio.

Provides: kpi_ids, action_code_ids, use_cases (from master_registry),
allowed_grains (from domain contracts), domain_contracts (from value_map or scan).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# Optional: use registry_builder for allowed_grains (add repo root to path if needed)
def _get_scan_allowed_grains():
    try:
        import sys
        repo = _repo_root_from_studio()
        if str(repo) not in sys.path:
            sys.path.insert(0, str(repo))
        from tooling.ontology.registry_builder import scan_allowed_grains
        return scan_allowed_grains
    except Exception:
        return None


def _repo_root_from_studio() -> Path:
    """tooling/golden_thread_discovery_studio/registry_loader.py -> repo root (2 parents up)."""
    return Path(__file__).resolve().parents[2]


def load_master_registry(repo_root: Path) -> Dict[str, Any]:
    """Load tooling/ontology/out/master_registry.json. Returns {} if missing."""
    path = repo_root / "tooling" / "ontology" / "out" / "master_registry.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def get_catalog_snapshot(repo_root: Path) -> Tuple[List[str], List[str]]:
    """
    Extract kpi_ids and action_code_ids from master_registry for catalog matching.
    Returns (kpi_ids, action_code_ids). Runs registry builder in memory not required;
    reads existing master_registry.json.
    """
    reg = load_master_registry(repo_root)
    objects = reg.get("objects") or {}
    kpis = objects.get("kpis") or {}
    actions = objects.get("action_codes") or {}
    kpi_ids = sorted(kpis.keys())
    action_code_ids = sorted(actions.keys())
    return kpi_ids, action_code_ids


def get_allowed_grains(repo_root: Path) -> Set[str]:
    """
    Set of allowed evidence_grain values from core/data_contracts/domains/*.yaml.
    Uses registry_builder.scan_allowed_grains if available; else scans contracts directly.
    """
    scan_fn = _get_scan_allowed_grains()
    if scan_fn is not None:
        grains, _ = scan_fn(repo_root)
        return grains
    # Fallback: scan domain contracts for fact[].grain
    grains: Set[str] = set()
    contracts_root = repo_root / "core" / "data_contracts" / "domains"
    if not contracts_root.exists():
        return grains
    try:
        import yaml
    except ImportError:
        return grains
    for p in sorted(contracts_root.glob("*.yaml")):
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        facts = data.get("fact")
        if not isinstance(facts, list):
            continue
        for fact in facts:
            if isinstance(fact, dict):
                g = fact.get("grain")
                if isinstance(g, str) and g.strip():
                    grains.add(g.strip())
    return grains


def load_value_map(repo_root: Path) -> Dict[str, Any]:
    """Load tooling/ontology/out/value_map.json. Returns {} if missing."""
    path = repo_root / "tooling" / "ontology" / "out" / "value_map.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def get_domain_contracts(repo_root: Path) -> Dict[str, Dict[str, str]]:
    """
    Domain contract id -> { id, status }. From value_map.nodes.domain_contracts if present;
    else scan core/data_contracts/domains/*.yaml for contract identifiers.
    """
    vm = load_value_map(repo_root)
    nodes = vm.get("nodes") or {}
    dc = nodes.get("domain_contracts")
    if isinstance(dc, dict):
        return {k: v if isinstance(v, dict) else {"id": k, "status": "ok"} for k, v in dc.items()}
    # Fallback: list YAML files in domains/
    contracts: Dict[str, Dict[str, str]] = {}
    domains = repo_root / "core" / "data_contracts" / "domains"
    if domains.exists():
        for p in sorted(domains.glob("*.yaml")):
            cid = p.stem
            contracts[cid] = {"id": cid, "status": "ok"}
    return contracts


def load_registry_for_studio(repo_root: Path) -> Dict[str, Any]:
    """
    One-shot load for Studio: catalog_snapshot (kpi_ids, action_code_ids),
    allowed_grains, domain_contracts, and raw use_cases from master_registry.
    """
    kpi_ids, action_code_ids = get_catalog_snapshot(repo_root)
    allowed_grains = get_allowed_grains(repo_root)
    domain_contracts = get_domain_contracts(repo_root)
    reg = load_master_registry(repo_root)
    use_cases_reg = (reg.get("objects") or {}).get("use_cases") or {}
    return {
        "catalog_snapshot": {"kpi_ids": kpi_ids, "action_code_ids": action_code_ids},
        "allowed_grains": sorted(allowed_grains),
        "domain_contracts": domain_contracts,
        "use_cases_registry": use_cases_reg,
    }
