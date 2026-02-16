"""
Refactor Use Cases: Factsheets -> UseCase_Bracket.yaml
======================================================

LEGACY MIGRATION SCRIPT — Lean 2.0 cutover is complete.
Technical_Factsheet.md has been deleted; all machine-readable config now lives
in UseCase_Bracket.yaml. This script is retained for reference only.

Original goal (Stage 1 entkernung):
- Extract machine-readable YAML blocks from Business/Technical factsheets.
- Create `UseCase_Bracket.yaml` per use case folder (schema_version 2.0).
- Remove the extracted fenced YAML blocks from Markdown and replace with a short reference.
- Keep all descriptive prose intact.

This script intentionally uses raw fenced-YAML extraction (no Markdown parser),
to avoid indentation corruption of YAML blocks.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

import yaml


_FENCE_YAML_START = re.compile(r"^\s*```yaml\s*$", re.IGNORECASE)
_FENCE_END = re.compile(r"^\s*```\s*$")


@dataclass(frozen=True)
class YamlFence:
    start_idx: int  # inclusive index in lines (0-based)
    end_idx: int  # inclusive index in lines (0-based)
    yaml_lines: List[str]  # only the YAML content lines


def read_lines(path: Path) -> List[str]:
    return path.read_text(encoding="utf-8").splitlines()


def write_lines(path: Path, lines: Sequence[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def extract_yaml_fences(lines: Sequence[str]) -> List[YamlFence]:
    fences: List[YamlFence] = []
    i = 0
    while i < len(lines):
        if _FENCE_YAML_START.match(lines[i]):
            j = i + 1
            yaml_lines: List[str] = []
            while j < len(lines) and not _FENCE_END.match(lines[j]):
                yaml_lines.append(lines[j])
                j += 1
            end_idx = j if j < len(lines) else len(lines) - 1
            fences.append(YamlFence(start_idx=i, end_idx=end_idx, yaml_lines=yaml_lines))
            i = end_idx + 1
            continue
        i += 1
    return fences


def fence_contains_key(fence: YamlFence, key: str) -> bool:
    pat = re.compile(rf"^\s*{re.escape(key)}\s*:\s*$")
    return any(bool(pat.match(ln)) for ln in fence.yaml_lines)


def extract_ids_from_yaml_lines(yaml_lines: Sequence[str], item_key: str) -> List[str]:
    """
    Extract IDs by regex from YAML lines. Does not require YAML parsing.
    Example: - id: sales.net_sales.amount
    """
    pat = re.compile(rf"^\s*-\s*{re.escape(item_key)}\s*:\s*([^\s#]+)\s*(?:#.*)?$")
    out: List[str] = []
    for ln in yaml_lines:
        m = pat.match(ln)
        if not m:
            continue
        val = m.group(1).strip().strip('"').strip("'")
        if val and val not in out:
            out.append(val)
    return out


def parse_frontmatter_id(lines: Sequence[str]) -> Optional[str]:
    if not lines or not lines[0].strip() == "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            fm = lines[1:i]
            for ln in fm:
                m = re.match(r"^\s*id\s*:\s*(.+?)\s*$", ln)
                if m:
                    val = m.group(1).strip().strip('"').strip("'")
                    return val
            return None
    return None


def infer_name_from_h1(lines: Sequence[str], fallback: str) -> str:
    for ln in lines:
        if ln.startswith("# "):
            # "# COM-001 - Something"
            txt = ln[2:].strip()
            m = re.match(r"^[A-Z]{2,3}-\d{3}\s*-\s*(.+)$", txt)
            if m:
                return m.group(1).strip()
            return txt
    return fallback


def infer_domain_from_metadata(lines: Sequence[str]) -> Optional[str]:
    # Match: - **Domain:** Commercial
    pat = re.compile(r"^\s*-\s*\*\*Domain:\*\*\s*(.+?)\s*$")
    for ln in lines:
        m = pat.match(ln)
        if m:
            return m.group(1).strip()
    return None


def infer_business_owner_role(lines: Sequence[str]) -> Optional[str]:
    # prefer KPI Owner, else Business Owner
    pats = [
        re.compile(r"^\s*-\s*\*\*KPI Owner:\*\*\s*(.+?)\s*$"),
        re.compile(r"^\s*-\s*\*\*Business Owner:\*\*\s*(.+?)\s*$"),
    ]
    for pat in pats:
        for ln in lines:
            m = pat.match(ln)
            if m:
                return m.group(1).strip()
    return None


def infer_steward_role(lines: Sequence[str]) -> Optional[str]:
    # Technical Owner
    pat = re.compile(r"^\s*-\s*\*\*Technical Owner:\*\*\s*(.+?)\s*$")
    for ln in lines:
        m = pat.match(ln)
        if m:
            return m.group(1).strip()
    return None


def pick_strategic_kpi(required_kpis: Sequence[str], kpi_roles: Dict[str, Optional[str]]) -> Tuple[str, List[str]]:
    """
    Choose exactly 1 strategic KPI.
    Priority:
    - first KPI with catalog kpi_role == strategic
    - else first in required_kpis
    Returns (strategic_kpi_id, warnings)
    """
    warnings: List[str] = []
    strategic_candidates = [k for k in required_kpis if kpi_roles.get(k) == "strategic"]
    if len(strategic_candidates) >= 1:
        if len(strategic_candidates) > 1:
            warnings.append(f"Multiple strategic candidates in KPI catalog: {strategic_candidates}. Picking first.")
        return strategic_candidates[0], warnings
    if required_kpis:
        warnings.append("No KPI with kpi_role=strategic found; picking first required KPI as strategic.")
        return required_kpis[0], warnings
    raise ValueError("required_kpis is empty; cannot pick strategic KPI.")


def load_kpi_roles_from_catalog(repo_root: Path) -> Dict[str, Optional[str]]:
    """
    Best-effort: parse KPI_Catalog.md fenced YAML blocks and capture kpi_role per kpi_id.
    Avoid full YAML parsing to keep tolerant behavior.
    """
    catalog = repo_root / "core" / "kpi_catalog" / "KPI_Catalog.md"
    if not catalog.exists():
        return {}
    lines = read_lines(catalog)
    fences = extract_yaml_fences(lines)
    roles: Dict[str, Optional[str]] = {}
    for f in fences:
        # chunk per - kpi_id:
        starts: List[int] = []
        for idx, ln in enumerate(f.yaml_lines):
            if re.match(r"^\s*-\s*kpi_id\s*:\s*", ln):
                starts.append(idx)
        if not starts:
            continue
        starts.append(len(f.yaml_lines))
        for si in range(len(starts) - 1):
            chunk = f.yaml_lines[starts[si] : starts[si + 1]]
            m = re.match(r"^\s*-\s*kpi_id\s*:\s*([^\s#]+)\s*", chunk[0] if chunk else "")
            if not m:
                continue
            kpi_id = m.group(1).strip().strip('"').strip("'")
            role = None
            for cl in chunk:
                mm = re.match(r"^\s*kpi_role\s*:\s*([^\s#]+)\s*", cl)
                if mm:
                    role = mm.group(1).strip().strip('"').strip("'")
                    break
            roles[kpi_id] = role
    return roles


def build_bracket_yaml(
    *,
    uc_id: str,
    name: str,
    domain: str,
    owner_role: str,
    steward_role: str,
    strategic_kpi_id: str,
    influencing_kpi_ids: Sequence[str],
    action_code_ids: Sequence[str],
    business_factsheet_rel: str,
    technical_factsheet_rel: str,
) -> Dict:
    return {
        "schema_version": "2.0",
        "id": uc_id,
        "name": name,
        "domain": domain,
        "governance": {
            "owner_role": owner_role,
            "steward_role": steward_role,
            "status": "active",
            "last_review": date.today().isoformat(),
        },
        "ontology_bracket": {
            "strategic_kpi_id": strategic_kpi_id,
            "influencing_kpi_ids": list(influencing_kpi_ids),
            "action_code_ids": list(action_code_ids),
        },
        "value_driver_model": {
            "description": f"{strategic_kpi_id} is driven by influencing KPIs and operational levers.",
            "formula": f"{strategic_kpi_id} = f({', '.join(influencing_kpi_ids)})" if influencing_kpi_ids else f"{strategic_kpi_id} = f(...)",
        },
        "ux_layout_rules": {
            "report_structure": "2-Page-Lead",
            "page_1_summary_insights": {
                "title": f"{domain} Summary & Insights",
                "3s_component": f"North Star: {strategic_kpi_id}",
                "30s_components": [],
            },
            "page_2_execution": {
                "title": f"{domain} Execution",
                "300s_components": [
                    "Evidence_Table: (define evidence table requirements)",
                    "Action_Panel: Integrated Side-Panel for Subscribed Action Codes",
                    "Payload_Injection: Show Level (L1-L3) and Steps from Action Code YAML",
                ],
            },
        },
        "documentation": {
            "business_factsheet": business_factsheet_rel,
            # technical_factsheet removed in Lean 2.0; technical config lives in this bracket file
        },
    }


def remove_selected_fences(
    lines: List[str],
    *,
    keys_to_remove: Set[str],
    replacement_lines: Sequence[str],
) -> List[str]:
    fences = extract_yaml_fences(lines)
    remove_ranges: List[Tuple[int, int]] = []
    for f in fences:
        for k in keys_to_remove:
            if fence_contains_key(f, k):
                remove_ranges.append((f.start_idx, f.end_idx))
                break
    if not remove_ranges:
        return lines
    # merge overlapping ranges
    remove_ranges.sort()
    merged: List[Tuple[int, int]] = []
    for a, b in remove_ranges:
        if not merged or a > merged[-1][1] + 1:
            merged.append((a, b))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
    out: List[str] = []
    idx = 0
    for a, b in merged:
        out.extend(lines[idx:a])
        out.extend(list(replacement_lines))
        idx = b + 1
    out.extend(lines[idx:])
    return out


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Refactor use cases: extract YAML blocks into UseCase_Bracket.yaml.")
    parser.add_argument("--repo-root", default=".", help="Repo root (default: current dir).")
    parser.add_argument("--usecases-root", default="core/usecases/core", help="Use cases root under repo.")
    parser.add_argument("--apply", action="store_true", help="Write changes. If not set, dry-run.")
    parser.add_argument("--only", default="", help="Optional use case ID prefix filter (e.g. COM-001).")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    usecases_root = (repo_root / args.usecases_root).resolve()
    if not usecases_root.exists():
        raise SystemExit(f"Use cases root not found: {usecases_root}")

    kpi_roles = load_kpi_roles_from_catalog(repo_root)
    warnings: List[str] = []

    for uc_dir in sorted([p for p in usecases_root.iterdir() if p.is_dir()]):
        uc_id = uc_dir.name.split("_")[0]
        if args.only and not uc_id.startswith(args.only):
            continue
        business_path = uc_dir / "Business_Factsheet.md"
        technical_path = uc_dir / "Technical_Factsheet.md"
        if not business_path.exists() or not technical_path.exists():
            continue

        b_lines = read_lines(business_path)
        t_lines = read_lines(technical_path)
        bid = parse_frontmatter_id(b_lines)
        tid = parse_frontmatter_id(t_lines)
        if bid and bid != uc_id:
            warnings.append(f"{uc_dir}: directory UC id '{uc_id}' differs from Business frontmatter id '{bid}'.")
        if tid and tid != uc_id:
            warnings.append(f"{uc_dir}: directory UC id '{uc_id}' differs from Technical frontmatter id '{tid}'.")

        name = infer_name_from_h1(b_lines, fallback=uc_dir.name)
        domain = infer_domain_from_metadata(b_lines) or infer_domain_from_metadata(t_lines) or "UNKNOWN"
        owner_role = infer_business_owner_role(b_lines) or "TBD Owner Role"
        steward_role = infer_steward_role(t_lines) or "TBD Steward Role"

        # Extract required_kpis + action_codes from Business factsheet fenced YAML blocks
        b_fences = extract_yaml_fences(b_lines)
        required_kpis: List[str] = []
        action_codes: List[str] = []
        for f in b_fences:
            if fence_contains_key(f, "required_kpis"):
                required_kpis = extract_ids_from_yaml_lines(f.yaml_lines, "id")
            if fence_contains_key(f, "action_codes"):
                action_codes = extract_ids_from_yaml_lines(f.yaml_lines, "id")

        if not required_kpis:
            warnings.append(f"{business_path}: no required_kpis found; bracket will not be created.")
            continue
        if not action_codes:
            warnings.append(f"{business_path}: no action_codes found; bracket will still be created with empty action_code_ids.")

        strategic_kpi_id, pick_warn = pick_strategic_kpi(required_kpis, kpi_roles)
        warnings.extend([f"{uc_id}: {w}" for w in pick_warn])
        influencing_kpis = [k for k in required_kpis if k != strategic_kpi_id]

        bracket = build_bracket_yaml(
            uc_id=uc_id,
            name=name,
            domain=domain,
            owner_role=owner_role,
            steward_role=steward_role,
            strategic_kpi_id=strategic_kpi_id,
            influencing_kpi_ids=influencing_kpis,
            action_code_ids=action_codes,
            business_factsheet_rel="./Business_Factsheet.md",
            technical_factsheet_rel="./Technical_Factsheet.md",
        )

        bracket_path = uc_dir / "UseCase_Bracket.yaml"

        # Prepare markdown replacements
        b_repl = [
            "",
            "> Machine-readable KPI + Action configuration has been extracted to `UseCase_Bracket.yaml` (SSOT).",
            "> This factsheet focuses on business context only.",
            "",
        ]
        t_repl = [
            "",
            "> Machine-readable KPI-to-Measure mapping is governed by `UseCase_Bracket.yaml` (SSOT).",
            "> This factsheet focuses on technical context and modeling guidance.",
            "",
        ]

        new_b_lines = remove_selected_fences(
            b_lines, keys_to_remove={"required_kpis", "action_codes"}, replacement_lines=b_repl
        )
        new_t_lines = remove_selected_fences(
            t_lines, keys_to_remove={"kpi_to_measure_mapping"}, replacement_lines=t_repl
        )

        if args.apply:
            bracket_path.write_text(yaml.safe_dump(bracket, sort_keys=False, allow_unicode=True), encoding="utf-8")
            write_lines(business_path, new_b_lines)
            write_lines(technical_path, new_t_lines)

    if warnings:
        # print warnings to stdout for operator visibility
        print("\n".join(warnings))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
