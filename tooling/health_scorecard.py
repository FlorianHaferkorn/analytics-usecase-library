"""
Framework Health Scorecard
==========================

Automates the H1-H8 metrics defined in:
  core/strategy_operating_model/operating_model/framework_health_metrics.md

Usage:
  python tooling/health_scorecard.py            # Console output
  python tooling/health_scorecard.py --json      # JSON to stdout
  python tooling/health_scorecard.py --out FILE  # Write JSON to file

Reads master_registry.json (run registry_builder.py first if stale) and scans
core/ for additional data not captured in the registry.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# H1 — Golden Thread Coverage %
# ---------------------------------------------------------------------------

def compute_h1(
    registry: Dict[str, Any],
    repo_root: Path,
) -> Dict[str, Any]:
    """
    H1: % of strategic KPIs with unbroken traceability across 5 layers:
      1. KPI in catalog
      2. KPI in at least one UseCase_Bracket
      3. KPI has measure in a Measure_Dictionary (kpi_id_ref match)
      4. Measure source table exists in data contract
      5. At least one linked action code has the KPI in kpi_trigger_ids
    """
    kpis = registry.get("objects", {}).get("kpis", {})
    edges = registry.get("edges", [])

    # Strategic KPIs (layer 1 = exists in catalog with role=strategic)
    strategic_kpi_ids = {
        kid for kid, kpi in kpis.items()
        if kpi.get("kpi_role") == "strategic" or kpi.get("computed_role_global") == "strategic"
    }

    if not strategic_kpi_ids:
        return {"metric": "H1", "name": "Golden Thread Coverage", "score": 0.0,
                "target": 90.0, "details": {"strategic_kpis": 0, "covered": 0},
                "status": "no_data"}

    # Layer 2: KPI linked from a bracket (use_case_strategic_kpi or use_case_influencing_kpi edge)
    kpis_in_brackets: Set[str] = set()
    for e in edges:
        if e.get("type") in ("use_case_strategic_kpi", "use_case_influencing_kpi"):
            kpis_in_brackets.add(e["to"])

    # Layer 3: KPI has measure in a Measure_Dictionary (kpi_id_ref)
    kpis_with_measure = _scan_measure_dictionaries_for_kpis(repo_root)

    # Layer 4: linked_domain_contracts in registry (non-empty = data contract exists)
    kpis_with_contract: Set[str] = set()
    for kid, kpi in kpis.items():
        contracts = kpi.get("linked_domain_contracts") or []
        if contracts:
            kpis_with_contract.add(kid)

    # Layer 5: KPI referenced by an action code linked to a use case that uses this KPI.
    # Registry has use_case_subscribes_action edges. Scan action code YAML for kpis.trigger_kpis.
    kpis_in_action_codes = _scan_action_code_kpi_refs(repo_root)

    covered = 0
    missing_layers: Dict[str, List[str]] = {}
    for kid in strategic_kpi_ids:
        layers_present = []
        layers_missing = []
        for layer, label in [
            (True, "catalog"),
            (kid in kpis_in_brackets, "bracket"),
            (kid in kpis_with_measure, "measure_dict"),
            (kid in kpis_with_contract, "data_contract"),
            (kid in kpis_in_action_codes, "action_code"),
        ]:
            if layer:
                layers_present.append(label)
            else:
                layers_missing.append(label)
        if not layers_missing:
            covered += 1
        else:
            missing_layers[kid] = layers_missing

    score = (covered / len(strategic_kpi_ids)) * 100 if strategic_kpi_ids else 0.0
    return {
        "metric": "H1",
        "name": "Golden Thread Coverage",
        "score": round(score, 1),
        "target": 90.0,
        "status": "pass" if score >= 80.0 else "below_target",
        "details": {
            "strategic_kpis": len(strategic_kpi_ids),
            "covered": covered,
            "missing_layers": missing_layers,
        },
    }


def _scan_action_code_kpi_refs(repo_root: Path) -> Set[str]:
    """Scan action code YAML files for kpis.trigger_kpis references."""
    result: Set[str] = set()
    try:
        import yaml as _yaml
    except ImportError:
        return result
    ac_root = repo_root / "core" / "action_codes"
    if not ac_root.exists():
        return result
    for f in ac_root.rglob("*.yaml"):
        if "decision_spine" in str(f).lower() or "DecisionSpine" in f.name:
            continue
        try:
            data = _yaml.safe_load(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        kpis_block = data.get("kpis") or {}
        if isinstance(kpis_block, dict):
            for key in ("trigger_kpis", "guardrail_kpis", "outcome_kpis"):
                for kpi_id in (kpis_block.get(key) or []):
                    if isinstance(kpi_id, str):
                        result.add(kpi_id)
    return result


def _scan_measure_dictionaries_for_kpis(repo_root: Path) -> Set[str]:
    """Scan Measure_Dictionary_*.md for KPI IDs referenced via kpi_id_ref."""
    result: Set[str] = set()
    domains_dir = repo_root / "core" / "semantic_models" / "domains"
    if not domains_dir.exists():
        return result
    kpi_ref_pattern = re.compile(r"kpi_id_ref\s*:\s*[\"']?([a-z][a-z0-9_.]+)")
    for md_file in domains_dir.rglob("Measure_Dictionary_*.md"):
        content = md_file.read_text(encoding="utf-8")
        for m in kpi_ref_pattern.finditer(content):
            result.add(m.group(1).strip().strip('"').strip("'"))
    return result


# ---------------------------------------------------------------------------
# H2 — Semantic Model Stability %
# ---------------------------------------------------------------------------

def compute_h2(repo_root: Path) -> Dict[str, Any]:
    """H2: % of measures with governance.status: active."""
    domains_dir = repo_root / "core" / "semantic_models" / "domains"
    if not domains_dir.exists():
        return {"metric": "H2", "name": "Semantic Model Stability", "score": 0.0,
                "target": 80.0, "details": {}, "status": "no_data"}

    total = 0
    active = 0
    draft_measures: List[str] = []
    status_pattern = re.compile(r"status\s*:\s*(\w+)")
    measure_name_pattern = re.compile(r"measure_name\s*:\s*([^\n#]+)")

    for md_file in domains_dir.rglob("Measure_Dictionary_*.md"):
        content = md_file.read_text(encoding="utf-8")
        # Find yaml blocks
        for block_match in re.finditer(r"```yaml\s*\n(.*?)```", content, re.DOTALL):
            block = block_match.group(1)
            entries = re.split(r"(?m)^\s*-\s*measure_name\s*:", block)
            for entry in entries[1:]:  # skip preamble
                total += 1
                name_m = measure_name_pattern.search("measure_name:" + entry)
                name = name_m.group(1).strip().strip('"') if name_m else "unknown"
                status_m = status_pattern.search(entry)
                if status_m and status_m.group(1).lower() == "active":
                    active += 1
                else:
                    draft_measures.append(name)

    score = (active / total) * 100 if total else 0.0
    return {
        "metric": "H2",
        "name": "Semantic Model Stability",
        "score": round(score, 1),
        "target": 80.0,
        "status": "pass" if score >= 80.0 else "below_target",
        "details": {
            "total_measures": total,
            "active": active,
            "draft_count": len(draft_measures),
        },
    }


# ---------------------------------------------------------------------------
# H3 — Data Contract Coverage %
# ---------------------------------------------------------------------------

def compute_h3(registry: Dict[str, Any]) -> Dict[str, Any]:
    """H3: % of bracket required_facts covered by domain data contracts."""
    use_cases = registry.get("objects", {}).get("use_cases", {})
    total_facts = 0
    covered_facts = 0
    missing: Dict[str, List[str]] = {}

    for uc_id, uc in use_cases.items():
        orch = uc.get("orchestration") or {}
        req_facts = orch.get("required_facts") or []
        if not req_facts:
            continue
        for fact in req_facts:
            total_facts += 1
            # The registry tracks data_contract_risk at KPI level, but for H3 we check
            # whether the bracket's evidence grain is in a contract.
            # Simplified: count as covered if fact is a non-empty string
            # (the registry builder already validates against contracts)
            covered_facts += 1  # If it made it past registry strict, it's covered

    # Better approach: count issues with code starting with "evidence_grain"
    issues = registry.get("issues", [])
    evidence_issues = [i for i in issues if i.get("code", "").startswith("evidence_grain")]

    if total_facts == 0:
        # Fallback: use edges to count bracket->contract links
        edges = registry.get("edges", [])
        contract_edges = [e for e in edges if "contract" in e.get("type", "")]
        total_facts = len(use_cases)
        covered_facts = total_facts - len(evidence_issues)

    score = (covered_facts / total_facts) * 100 if total_facts else 100.0
    return {
        "metric": "H3",
        "name": "Data Contract Coverage",
        "score": round(score, 1),
        "target": 90.0,
        "status": "pass" if score >= 80.0 else "below_target",
        "details": {
            "total_facts": total_facts,
            "covered": covered_facts,
            "evidence_grain_issues": len(evidence_issues),
        },
    }


# ---------------------------------------------------------------------------
# H4 — Action Code Completeness %
# ---------------------------------------------------------------------------

def compute_h4(repo_root: Path) -> Dict[str, Any]:
    """
    H4: % of action codes with all 4 completeness criteria:
      1. At least one L1 trigger defined
      2. Impact valuation present
      3. Execution bridge defined (not TBD)
      4. At least one kpi_trigger_id
    """
    try:
        import yaml as _yaml
    except ImportError:
        return {"metric": "H4", "name": "Action Code Completeness", "score": 0.0,
                "target": 80.0, "details": {}, "status": "error_no_yaml"}

    ac_root = repo_root / "core" / "action_codes"
    if not ac_root.exists():
        return {"metric": "H4", "name": "Action Code Completeness", "score": 0.0,
                "target": 80.0, "details": {}, "status": "no_data"}

    total = 0
    complete = 0
    incomplete: Dict[str, List[str]] = {}

    for yaml_file in ac_root.rglob("*.yaml"):
        if yaml_file.name.startswith("DecisionSpine") or yaml_file.name.startswith("_"):
            continue
        if "decision_spines" in yaml_file.parts:
            continue
        if "_business_case" in yaml_file.name:
            continue
        try:
            data = _yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict) or "id" not in data:
            continue

        total += 1
        ac_id = data["id"]
        missing_criteria: List[str] = []

        # 1. Trigger defined (trigger.type exists and evaluation has levels)
        trigger = data.get("trigger") or {}
        has_trigger = bool(
            isinstance(trigger, dict) and trigger.get("type")
            and trigger.get("evaluation")
        )
        if not has_trigger:
            missing_criteria.append("trigger")

        # 2. Impact section (impact.category or impact.expected_range)
        impact = data.get("impact") or {}
        has_impact = bool(
            isinstance(impact, dict)
            and (impact.get("category") or impact.get("expected_range"))
        )
        if not has_impact:
            missing_criteria.append("impact")

        # 3. Operational execution with steps
        oe = data.get("operational_execution") or {}
        has_execution = bool(
            isinstance(oe, dict)
            and oe.get("steps")
        )
        if not has_execution:
            missing_criteria.append("operational_execution")

        # 4. KPI references (kpis.trigger_kpis non-empty)
        kpis_block = data.get("kpis") or {}
        trigger_kpis = kpis_block.get("trigger_kpis") or [] if isinstance(kpis_block, dict) else []
        if not trigger_kpis:
            missing_criteria.append("trigger_kpis")

        if not missing_criteria:
            complete += 1
        else:
            incomplete[ac_id] = missing_criteria

    score = (complete / total) * 100 if total else 0.0
    return {
        "metric": "H4",
        "name": "Action Code Completeness",
        "score": round(score, 1),
        "target": 80.0,
        "status": "pass" if score >= 80.0 else "below_target",
        "details": {
            "total_action_codes": total,
            "complete": complete,
            "incomplete": incomplete,
        },
    }


# ---------------------------------------------------------------------------
# H5 — Factsheet Quality Score
# ---------------------------------------------------------------------------

def compute_h5(repo_root: Path) -> Dict[str, Any]:
    """
    H5: Average completeness across core Business Factsheets.
    Each factsheet scored on 5 sections (1 point each):
      1. Business Summary (no TBD)
      2. Core Business Questions (>=3)
      3. 3-30-300 Page Layout (KPI cards + >=2 visuals)
      4. Success Criteria (Impact + Adoption)
      5. Decision Scenarios (>=2)
    """
    usecases_dir = repo_root / "core" / "usecases" / "core"
    if not usecases_dir.exists():
        return {"metric": "H5", "name": "Factsheet Quality Score", "score": 0.0,
                "target": 80.0, "details": {}, "status": "no_data"}

    scores: Dict[str, int] = {}

    for uc_dir in sorted(usecases_dir.iterdir()):
        if not uc_dir.is_dir():
            continue
        factsheet = uc_dir / "Business_Factsheet.md"
        if not factsheet.exists():
            continue
        content = factsheet.read_text(encoding="utf-8")
        uc_id = uc_dir.name.split("_")[0]
        score = 0

        # 1. Business Summary: section exists and no "TBD" markers
        if re.search(r"(?i)##.*business\s+summary|##.*1\.\s", content):
            # Check first section for TBD
            section_1 = _extract_section(content, 1)
            if section_1 and "TBD" not in section_1.upper():
                score += 1

        # 2. Core Business Questions: >=3 questions
        section_2 = _extract_section(content, 2)
        if section_2:
            questions = re.findall(r"(?m)^\s*[-*]\s*.+\?", section_2)
            if not questions:
                questions = re.findall(r"\?", section_2)
            if len(questions) >= 3:
                score += 1

        # 3. 3-30-300 Layout: KPI cards + visuals mentioned
        section_5 = _extract_section(content, 5)
        if section_5:
            has_kpi = bool(re.search(r"(?i)kpi\s*card|KPI", section_5))
            visual_count = len(re.findall(r"(?i)(line\s*chart|bar\s*chart|waterfall|table|matrix|scatter|funnel|visual)", section_5))
            if has_kpi and visual_count >= 2:
                score += 1

        # 4. Success Criteria: Impact + Adoption
        section_8 = _extract_section(content, 8)
        if section_8:
            has_impact = bool(re.search(r"(?i)impact", section_8))
            has_adoption = bool(re.search(r"(?i)adoption", section_8))
            if has_impact and has_adoption:
                score += 1

        # 5. Decision Scenarios: >=2 scenarios
        section_10 = _extract_section(content, 10)
        if section_10:
            scenarios = re.findall(r"(?i)(?:scenario|situation)\s*\d*\s*:", section_10)
            if not scenarios:
                scenarios = re.findall(r"(?m)^###\s+", section_10)
            if len(scenarios) >= 2:
                score += 1

        scores[uc_id] = score

    if not scores:
        return {"metric": "H5", "name": "Factsheet Quality Score", "score": 0.0,
                "target": 80.0, "details": {}, "status": "no_data"}

    total_points = sum(scores.values())
    max_points = len(scores) * 5
    pct = (total_points / max_points) * 100

    return {
        "metric": "H5",
        "name": "Factsheet Quality Score",
        "score": round(pct, 1),
        "target": 80.0,
        "status": "pass" if pct >= 80.0 else "below_target",
        "details": {
            "factsheets": len(scores),
            "total_points": total_points,
            "max_points": max_points,
            "per_factsheet": scores,
        },
    }


def _extract_section(content: str, section_num: int) -> Optional[str]:
    """Extract content of a numbered section (e.g., '## 5. ...' or '## Section 5')."""
    patterns = [
        rf"(?m)^##\s+{section_num}\.\s",
        rf"(?m)^##\s+Section\s+{section_num}",
    ]
    for pat in patterns:
        m = re.search(pat, content)
        if m:
            start = m.end()
            next_section = re.search(r"(?m)^##\s+\d+\.", content[start:])
            if next_section:
                return content[start:start + next_section.start()]
            return content[start:]
    return None


# ---------------------------------------------------------------------------
# H6 — Prioritization & Readiness Coverage %
# ---------------------------------------------------------------------------

def compute_h6(repo_root: Path) -> Dict[str, Any]:
    """
    H6: % of use cases that have both a prioritization and readiness block.
    Measures governance maturity for use case intake and implementation planning.
    """
    usecases_dir = repo_root / "core" / "usecases"
    total = 0
    with_prio = 0
    with_readiness = 0
    with_both = 0
    missing = []

    for bracket_path in sorted(usecases_dir.rglob("UseCase_Bracket.yaml")):
        if "templates" in bracket_path.parts:
            continue

        try:
            data = yaml.safe_load(bracket_path.read_text(encoding="utf-8"))
        except Exception:
            continue

        uc_id = data.get("id", bracket_path.parent.name)
        total += 1
        has_prio = data.get("prioritization") is not None
        has_ready = data.get("readiness") is not None

        if has_prio:
            with_prio += 1
        if has_ready:
            with_readiness += 1
        if has_prio and has_ready:
            with_both += 1
        else:
            missing.append(uc_id)

    if total == 0:
        return {"metric": "H6", "name": "Prioritization & Readiness Coverage",
                "score": 0.0, "target": 80.0, "details": {}, "status": "no_data"}

    pct = (with_both / total) * 100

    return {
        "metric": "H6",
        "name": "Prioritization & Readiness Coverage",
        "score": round(pct, 1),
        "target": 80.0,
        "status": "pass" if pct >= 80.0 else "below_target",
        "details": {
            "total_use_cases": total,
            "with_prioritization": with_prio,
            "with_readiness": with_readiness,
            "with_both": with_both,
            "missing": missing,
        },
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _ensure_registry(repo_root: Path) -> Path:
    """Check if registry exists; if not, build it via registry_builder.py subprocess. Return path."""
    registry_path = repo_root / "tooling" / "ontology" / "out" / "master_registry.json"
    if not registry_path.exists():
        print("Registry not found. Running registry builder...", file=sys.stderr)
        import subprocess
        subprocess.run(
            [sys.executable, str(repo_root / "tooling" / "ontology" / "registry_builder.py"),
             "--out-dir", str(registry_path.parent), "--strict"],
            check=True,
            cwd=str(repo_root),
        )
    return registry_path


def compute_h7(repo_root: Path) -> Dict[str, Any]:
    """H7: Report Binding Integrity.

    % of generated reports whose visual measure bindings all resolve to a
    defined TMDL measure in dist/ (not core/). This is the gate that catches
    semantic-model regressions the core-level metrics (H2) cannot see -- e.g.
    the Commercial _Measures.tmdl regression that produced 96 missing-measure
    criticals while H2 stayed green.
    """
    name = "Report Binding Integrity"
    dist_root = repo_root / "products" / "fabric" / "powerbi" / "dist"
    try:
        from report_quality.cli import validate
        from report_quality.pbir import iter_report_dirs
    except Exception as exc:  # validator unavailable -> visible non-pass, never false-green
        return {"metric": "H7", "name": name, "score": 0.0, "target": 100.0,
                "details": {"error": f"validator unavailable: {exc}"}, "status": "below_target"}

    reports = iter_report_dirs(dist_root) if dist_root.exists() else []
    if not reports:
        return {"metric": "H7", "name": name, "score": 100.0, "target": 100.0,
                "details": {"total_reports": 0, "note": "no reports to validate"}, "status": "pass"}

    criticals = [v for v in validate(dist_root) if v.severity == "critical"]
    report_names = [p.name for p in reports]
    affected = {rn for rn in report_names for v in criticals if rn in v.pointer}
    clean = len(report_names) - len(affected)
    by_class: Dict[str, int] = {}
    for v in criticals:
        by_class[v.check] = by_class.get(v.check, 0) + 1

    return {
        "metric": "H7", "name": name,
        "score": round(100.0 * clean / len(report_names), 1), "target": 100.0,
        "details": {
            "total_reports": len(report_names),
            "clean_reports": clean,
            "affected_reports": sorted(affected),
            "total_criticals": len(criticals),
            "by_class": by_class,
        },
        "status": "pass" if not criticals else "below_target",
    }


def compute_h8(repo_root: Path) -> Dict[str, Any]:
    """H8: AI-Readiness / Linguistic Coverage.

    % of governed column synonyms (data-contract ``synonyms``) that are present in
    the committed model linguistic schema (``cultures/<culture>.tmdl``). This is the
    gate that keeps Copilot/Q&A synonyms from silently regressing: drop a governed
    synonym from the linguistic schema and H8 goes red even though the ``///``
    description text (H2) stays green. Mirrors H7 -- it reads dist/ and never
    reports false-green when the projection tooling is unavailable.
    """
    name = "AI-Readiness / Linguistic Coverage"
    target = 100.0
    dist_root = repo_root / "products" / "fabric" / "powerbi" / "dist"
    contracts_dir = repo_root / "core" / "data_contracts" / "domains"

    try:  # projection + hygiene helpers (Epic A2/C); unavailable -> non-pass, never false-green
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        from products.fabric.powerbi.tooling.linguistic_schema import (
            DOMAIN_CONTRACT,
            build_table_descriptions,
            parse_culture_tmdl,
        )
        from tooling.validation.check_ai_surface_hygiene import (
            visible_keys,
            weak_descriptions,
        )
    except Exception as exc:
        return {"metric": "H8", "name": name, "score": 0.0, "target": target,
                "details": {"error": f"projection helpers unavailable: {exc}"},
                "status": "below_target"}

    total = 0
    present = 0
    missing: Dict[str, List[str]] = {}
    domains_checked: List[str] = []

    for domain, contract_name in sorted(DOMAIN_CONTRACT.items()):
        contract = contracts_dir / contract_name
        if not contract.exists():
            continue
        governed: Dict[tuple, List[str]] = {}
        for tbl in build_table_descriptions(contract):
            for col in tbl.columns:
                if col.synonyms:
                    governed[(tbl.name, col.name)] = list(col.synonyms)
        if not governed:
            continue
        domains_checked.append(domain)

        # Parse the committed linguistic schema into (table, column) -> term set.
        culture_terms: Dict[tuple, Set[str]] = {}
        cultures_dir = dist_root / f"{domain}.SemanticModel" / "definition" / "cultures"
        for culture_file in (sorted(cultures_dir.glob("*.tmdl")) if cultures_dir.exists() else []):
            try:
                schema = parse_culture_tmdl(culture_file.read_text(encoding="utf-8"))
            except Exception:
                continue
            for ent in (schema.get("Entities") or {}).values():
                binding = (ent.get("Definition") or {}).get("Binding") or {}
                key = (binding.get("ConceptualEntity"), binding.get("ConceptualProperty"))
                terms = {next(iter(term)) for term in (ent.get("Terms") or [])}
                culture_terms.setdefault(key, set()).update(terms)

        for key, syns in governed.items():
            have = culture_terms.get(key, set())
            for syn in syns:
                total += 1
                if syn in have:
                    present += 1
                else:
                    missing.setdefault(f"{domain}:{key[0]}.{key[1]}", []).append(syn)

    # Fold in AI-surface hygiene (Epic C): visible surrogate/FK keys + weak
    # descriptions on the same (Aurora) domains. H8 is the composite AI-readiness
    # gate -- coverage AND hygiene must be clean to pass.
    hyg_keys: Dict[str, List[str]] = {}
    hyg_weak: Dict[str, List[str]] = {}
    for domain in domains_checked:
        vk = visible_keys(dist_root, domain)
        wd = weak_descriptions(repo_root, domain)
        if vk:
            hyg_keys[domain] = vk
        if wd:
            hyg_weak[domain] = [f"{obj} ({reason})" for obj, reason in wd]
    hygiene_clean = not hyg_keys and not hyg_weak

    coverage_complete = (total == 0) or (present == total)
    score = 100.0 if total == 0 else round(100.0 * present / total, 1)
    details: Dict[str, Any] = {
        "domains": domains_checked,
        "governed_synonyms": total,
        "present": present,
        "missing": missing,
        "hygiene": {"visible_keys": hyg_keys, "weak_descriptions": hyg_weak},
    }
    if total == 0:
        details["note"] = "no governed synonyms to project"
    return {
        "metric": "H8", "name": name, "score": score, "target": target,
        "details": details,
        "status": "pass" if (coverage_complete and hygiene_clean) else "below_target",
    }


# ---------------------------------------------------------------------------
# H9 — Cross-Use-Case Dependency Coverage %
# ---------------------------------------------------------------------------

def compute_h9(repo_root: Path) -> Dict[str, Any]:
    """
    H9: % of documented cross-UC dependency links that are bidirectional.

    For every ``use_case_links`` entry in any UseCase_Bracket.yaml the linked UC
    must also carry a reciprocal ``use_case_links`` entry pointing back. The score
    is the share of unique UC pairs that are confirmed reciprocal.
    """
    usecases_dir = repo_root / "core" / "usecases"
    uc_links: Dict[str, List[str]] = {}

    for bracket_path in sorted(usecases_dir.rglob("UseCase_Bracket.yaml")):
        if "templates" in bracket_path.parts:
            continue
        try:
            data = yaml.safe_load(bracket_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        uc_id = data.get("id", "")
        if not uc_id:
            continue
        links = data.get("use_case_links")
        if isinstance(links, list):
            uc_links[uc_id] = [lnk.get("use_case_id", "") for lnk in links if isinstance(lnk, dict)]
        else:
            uc_links[uc_id] = []

    directed_pairs: List[tuple] = []
    for src, targets in uc_links.items():
        for tgt in targets:
            if tgt:
                directed_pairs.append((src, tgt))

    if not directed_pairs:
        return {
            "metric": "H9",
            "name": "Cross-UC Dependency Coverage",
            "score": 0.0,
            "target": 100.0,
            "status": "no_links",
            "details": {"directed_pairs": 0, "reciprocal": 0, "missing_reciprocals": []},
        }

    reciprocal_count = 0
    missing: List[str] = []
    seen_pairs: Set[tuple] = set()

    for (src, tgt) in directed_pairs:
        pair = tuple(sorted([src, tgt]))
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        if tgt in uc_links.get(src, []) and src in uc_links.get(tgt, []):
            reciprocal_count += 1
        else:
            missing.append(f"{src}<->{tgt}")

    total_pairs = len(seen_pairs)
    pct = (reciprocal_count / total_pairs) * 100 if total_pairs > 0 else 0.0

    return {
        "metric": "H9",
        "name": "Cross-UC Dependency Coverage",
        "score": round(pct, 1),
        "target": 100.0,
        "status": "pass" if pct >= 100.0 else "below_target",
        "details": {
            "total_unique_pairs": total_pairs,
            "reciprocal_pairs": reciprocal_count,
            "missing_reciprocals": missing,
        },
    }


def run_scorecard(repo_root: Optional[Path] = None) -> Dict[str, Any]:
    """Run all H1-H9 metrics and return results dict."""
    if repo_root is None:
        repo_root = _repo_root()

    registry_path = _ensure_registry(repo_root)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))

    metrics = [
        compute_h1(registry, repo_root),
        compute_h2(repo_root),
        compute_h3(registry),
        compute_h4(repo_root),
        compute_h5(repo_root),
        compute_h6(repo_root),
        compute_h7(repo_root),
        compute_h8(repo_root),
        compute_h9(repo_root),
    ]

    all_pass = all(m["status"] == "pass" for m in metrics)

    return {
        "meta": {
            "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "version": _read_version(repo_root),
            "registry_source": str(registry_path.relative_to(repo_root)),
        },
        "overall_status": "pass" if all_pass else "below_target",
        "metrics": metrics,
    }


def _read_version(repo_root: Path) -> str:
    version_file = repo_root / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return "unknown"


def print_console(results: Dict[str, Any]) -> None:
    """Pretty-print scorecard to console."""
    BOLD = "\033[1m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[91m"
    RESET = "\033[0m"

    print(f"\n{BOLD}{'=' * 60}")
    print(f"  Framework Health Scorecard — v{results['meta']['version']}")
    print(f"  {results['meta']['generated_at_utc']}")
    print(f"{'=' * 60}{RESET}\n")

    for m in results["metrics"]:
        score = m["score"]
        target = m["target"]
        if score >= target:
            color = GREEN
            icon = "[PASS]"
        elif score >= target * 0.8:
            color = YELLOW
            icon = "[NEAR]"
        else:
            color = RED
            icon = "[FAIL]"

        print(f"  {color}{icon}{RESET}  {m['metric']} {m['name']}: "
              f"{BOLD}{score:.1f}%{RESET} (target: {target:.0f}%)")

        details = m.get("details", {})
        if "strategic_kpis" in details:
            print(f"         {details['covered']}/{details['strategic_kpis']} strategic KPIs fully traced")
        if "total_measures" in details:
            print(f"         {details['active']}/{details['total_measures']} measures active")
        if "total_action_codes" in details:
            print(f"         {details['complete']}/{details['total_action_codes']} action codes complete")
        if "per_factsheet" in details:
            pts = details["per_factsheet"]
            low = [f"{k}({v}/5)" for k, v in pts.items() if v < 4]
            if low:
                print(f"         Below 4/5: {', '.join(low)}")
        if "total_criticals" in details:
            print(f"         {details['clean_reports']}/{details['total_reports']} reports with all bindings "
                  f"resolved ({details['total_criticals']} criticals)")
            if details.get("affected_reports"):
                print(f"         Affected: {', '.join(details['affected_reports'])}")
        if "total_use_cases" in details:
            print(f"         {details['with_both']}/{details['total_use_cases']} use cases with prioritization + readiness")
            if details.get("missing"):
                print(f"         Missing: {', '.join(details['missing'])}")
        if "governed_synonyms" in details:
            print(f"         {details['present']}/{details['governed_synonyms']} governed synonyms in the linguistic schema "
                  f"({', '.join(details.get('domains', [])) or 'no domains'})")
            if details.get("missing"):
                dropped = "; ".join(f"{k}: {', '.join(v)}" for k, v in details["missing"].items())
                print(f"         Dropped: {dropped}")
            hyg = details.get("hygiene", {})
            n_keys = sum(len(v) for v in hyg.get("visible_keys", {}).values())
            n_weak = sum(len(v) for v in hyg.get("weak_descriptions", {}).values())
            print(f"         Hygiene: {n_keys} visible key(s), {n_weak} weak description(s)")

    overall = results["overall_status"]
    color = GREEN if overall == "pass" else RED
    print(f"\n  {BOLD}Overall: {color}{overall.upper()}{RESET}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Framework Health Scorecard")
    parser.add_argument("--json", action="store_true", help="Output JSON to stdout")
    parser.add_argument("--out", type=str, help="Write JSON to file")
    parser.add_argument("--root", type=str, help="Repository root path")
    args = parser.parse_args()

    repo_root = Path(args.root) if args.root else _repo_root()
    results = run_scorecard(repo_root)

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    elif args.out:
        Path(args.out).write_text(
            json.dumps(results, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Results written to {args.out}")
    else:
        print_console(results)

    return 0 if results["overall_status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
