"""
ActionReady Ontology Registry Builder
====================================

Stage 1 baseline:
- Build master_registry.json as graph-friendly SSOT index.
- Build orphans_report.json (full-scan vs linked-scan).
- Governance normalizer (legacy alias mapping to owner_role/steward_role).
- Precise source-line mapping for Markdown-embedded YAML references.

IMPORTANT:
- Do not parse Markdown with libraries that reformat YAML blocks.
- Prefer raw extraction of fenced ```yaml blocks and frontmatter boundaries.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

try:
    import yaml  # type: ignore
except Exception as e:  # pragma: no cover
    yaml = None
    _YAML_IMPORT_ERROR = e


@dataclasses.dataclass(frozen=True)
class SourceLocation:
    file: str  # repo-relative path
    line: int  # 1-based


@dataclasses.dataclass(frozen=True)
class Issue:
    severity: str  # "ERROR" | "WARN" | "INFO"
    code: str
    message: str
    location: Optional[SourceLocation] = None


class RegistryError(RuntimeError):
    def __init__(self, issue: Issue):
        super().__init__(issue.message)
        self.issue = issue


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _repo_root_from_file() -> Path:
    # tooling/ontology/registry_builder.py -> repo root is 3 parents up
    return Path(__file__).resolve().parents[2]


def _to_repo_rel(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def _read_text_lines(path: Path) -> List[str]:
    return path.read_text(encoding="utf-8").splitlines()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


_FRONTMATTER_START = re.compile(r"^\s*---\s*$")


def extract_frontmatter(lines: Sequence[str]) -> Optional[Tuple[int, int, List[str]]]:
    """
    Return (start_line, end_line, frontmatter_lines) where start/end are 1-based inclusive,
    not including the '---' boundary lines in frontmatter_lines.
    """
    if not lines or not _FRONTMATTER_START.match(lines[0]):
        return None
    for i in range(1, len(lines)):
        if _FRONTMATTER_START.match(lines[i]):
            # frontmatter is lines[1:i]
            return (1, i + 1, list(lines[1:i]))
    return None


def frontmatter_get_scalar(frontmatter_lines: Sequence[str], key: str) -> Optional[str]:
    pat = re.compile(rf"^\s*{re.escape(key)}\s*:\s*(.+?)\s*$")
    for ln in frontmatter_lines:
        m = pat.match(ln)
        if m:
            val = m.group(1).strip()
            # strip quotes if present
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            return val
    return None


_FENCE_YAML_START = re.compile(r"^\s*```yaml\s*$", re.IGNORECASE)
_FENCE_END = re.compile(r"^\s*```\s*$")


@dataclasses.dataclass(frozen=True)
class FencedYamlBlock:
    start_line: int  # 1-based inclusive (line containing ```yaml)
    end_line: int  # 1-based inclusive (line containing closing ```)
    yaml_start_line: int  # 1-based line number of first YAML content line
    yaml_lines: List[str]


def extract_fenced_yaml_blocks(lines: Sequence[str]) -> List[FencedYamlBlock]:
    blocks: List[FencedYamlBlock] = []
    i = 0
    while i < len(lines):
        if _FENCE_YAML_START.match(lines[i]):
            start_line = i + 1
            yaml_start_line = i + 2
            j = i + 1
            yaml_lines: List[str] = []
            while j < len(lines) and not _FENCE_END.match(lines[j]):
                yaml_lines.append(lines[j])
                j += 1
            if j >= len(lines):
                # Unclosed fence: treat as until EOF
                end_line = len(lines)
            else:
                end_line = j + 1
            blocks.append(
                FencedYamlBlock(
                    start_line=start_line,
                    end_line=end_line,
                    yaml_start_line=yaml_start_line,
                    yaml_lines=yaml_lines,
                )
            )
            i = j + 1
            continue
        i += 1
    return blocks


def find_line_for_yaml_kv(
    *,
    yaml_lines: Sequence[str],
    yaml_start_line: int,
    keys: Sequence[str],
    value: str,
) -> Optional[int]:
    """
    Find the line number (1-based in the file) of the first occurrence of any key:<value>
    in the given YAML text (raw lines).
    """
    # Keep this conservative: allow quotes and comments.
    key_alts = "|".join(re.escape(k) for k in keys)
    # match: key: value  OR key: "value" OR key: 'value'
    pat = re.compile(
        rf"^\s*(?:-?\s*)?(?:{key_alts})\s*:\s*(?P<q>['\"])?{re.escape(value)}(?P=q)?\s*(?:#.*)?$"
    )
    for idx, ln in enumerate(yaml_lines):
        if pat.match(ln):
            return yaml_start_line + idx
    return None


def find_line_containing_token(lines: Sequence[str], token: str) -> Optional[int]:
    """
    Best-effort line finder for YAML list items where key context is not on the same line.
    Returns 1-based line number.
    """
    if not token:
        return None
    # Match token as a YAML scalar (quoted or unquoted) on a line, typically list item: - token
    pat = re.compile(rf'^\s*-\s*(?P<q>["\'])?{re.escape(token)}(?P=q)?\s*(?:#.*)?$')
    for i, ln in enumerate(lines):
        if pat.match(ln):
            return i + 1
        # also accept token after ':' e.g. strategic_kpi_id: token
        if re.search(rf'(?<!\w){re.escape(token)}(?!\w)', ln):
            # keep conservative: only if line contains token and is YAML-ish
            if ":" in ln or ln.strip().startswith("-"):
                return i + 1
    return None


def _yaml_safe_load(text: str, *, source: str) -> Any:
    if yaml is None:  # pragma: no cover
        raise RuntimeError(
            f"PyYAML is required but not installed (import error: {_YAML_IMPORT_ERROR}). "
            f"Install with: pip install pyyaml. Source: {source}"
        )
    return yaml.safe_load(text)  # type: ignore[attr-defined]


def parse_yaml_file(path: Path) -> Any:
    return _yaml_safe_load(_read_text(path), source=str(path))


def list_files(root: Path, exts: Sequence[str]) -> List[Path]:
    out: List[Path] = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            out.append(p)
    return out


def scan_action_codes(repo_root: Path) -> Tuple[Dict[str, Dict[str, Any]], List[Issue]]:
    issues: List[Issue] = []
    action_root = repo_root / "core" / "action_codes"
    actions: Dict[str, Dict[str, Any]] = {}
    if not action_root.exists():
        return actions, issues
    for p in action_root.rglob("*.yaml"):
        if "decision_spines" in p.parts:
            continue
        rel = _to_repo_rel(repo_root, p)
        try:
            data = parse_yaml_file(p)
        except Exception as e:
            issues.append(Issue("ERROR", "action_code.yaml_parse_failed", f"YAML parse failed: {e}", SourceLocation(rel, 1)))
            continue
        if not isinstance(data, dict):
            issues.append(Issue("ERROR", "action_code.invalid_type", "Action code must be a YAML mapping/object.", SourceLocation(rel, 1)))
            continue
        action_id = data.get("id")
        if not action_id or not isinstance(action_id, str):
            # best-effort line search
            line = 1
            try:
                lines = _read_text_lines(p)
                for i, ln in enumerate(lines):
                    if re.match(r"^\s*id\s*:", ln):
                        line = i + 1
                        break
            except Exception:
                pass
            issues.append(Issue("ERROR", "action_code.missing_id", "Missing required field 'id'.", SourceLocation(rel, line)))
            continue
        actions[action_id] = {
            "id": action_id,
            "source": rel,
            "raw": data,
        }
    return actions, issues


@dataclasses.dataclass(frozen=True)
class KpiRecord:
    kpi_id: str
    source: str
    line: int
    kpi_role: Optional[str]
    governance: Dict[str, Optional[str]]  # business_owner, data_owner, steward, owner_role, steward_role


def scan_kpi_catalog(repo_root: Path) -> Tuple[Dict[str, KpiRecord], List[Issue]]:
    issues: List[Issue] = []
    kpi_root = repo_root / "core" / "kpi_catalog"
    kpis: Dict[str, KpiRecord] = {}
    if not kpi_root.exists():
        return kpis, issues

    md_files = [p for p in kpi_root.rglob("*.md") if p.is_file()]
    for p in md_files:
        rel = _to_repo_rel(repo_root, p)
        try:
            lines = _read_text_lines(p)
        except Exception as e:
            issues.append(Issue("ERROR", "kpi_catalog.read_failed", f"Read failed: {e}", SourceLocation(rel, 1)))
            continue
        blocks = extract_fenced_yaml_blocks(lines)
        for block in blocks:
            # Split into chunks per - kpi_id:
            chunk_starts: List[int] = []
            for idx, ln in enumerate(block.yaml_lines):
                if re.match(r"^\s*-\s*kpi_id\s*:\s*", ln):
                    chunk_starts.append(idx)
            if not chunk_starts:
                continue
            chunk_starts.append(len(block.yaml_lines))  # sentinel end
            for si in range(len(chunk_starts) - 1):
                start_idx = chunk_starts[si]
                end_idx = chunk_starts[si + 1]
                chunk_lines = block.yaml_lines[start_idx:end_idx]
                first_line = chunk_lines[0] if chunk_lines else ""
                m = re.match(r"^\s*-\s*kpi_id\s*:\s*([^\s#]+)\s*", first_line)
                if not m:
                    continue
                kpi_id = m.group(1).strip().strip('"').strip("'")
                kpi_line = block.yaml_start_line + start_idx

                def _get_field(key: str) -> Optional[str]:
                    pat = re.compile(rf"^\s*{re.escape(key)}\s*:\s*(.+?)\s*$")
                    for cl in chunk_lines:
                        mm = pat.match(cl)
                        if mm:
                            val = mm.group(1).strip()
                            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                                val = val[1:-1]
                            return val
                    return None

                kpi_role = _get_field("kpi_role")
                business_owner = _get_field("business_owner")
                data_owner = _get_field("data_owner")
                steward = _get_field("steward")

                # Normalize governance roles (legacy-safe alias map)
                owner_role = business_owner or data_owner
                steward_role = steward or data_owner
                gov = {
                    "business_owner": business_owner,
                    "data_owner": data_owner,
                    "steward": steward,
                    "owner_role": owner_role,
                    "steward_role": steward_role,
                }
                if kpi_id in kpis:
                    issues.append(
                        Issue(
                            "ERROR",
                            "kpi_catalog.duplicate_kpi_id",
                            f"Duplicate KPI ID '{kpi_id}' in catalog.",
                            SourceLocation(rel, kpi_line),
                        )
                    )
                    continue
                kpis[kpi_id] = KpiRecord(
                    kpi_id=kpi_id,
                    source=rel,
                    line=kpi_line,
                    kpi_role=kpi_role,
                    governance=gov,
                )
    return kpis, issues


def scan_usecase_brackets(repo_root: Path) -> Tuple[Dict[str, Dict[str, Any]], List[Issue]]:
    issues: List[Issue] = []
    uc_root = repo_root / "core" / "usecases"
    brackets: Dict[str, Dict[str, Any]] = {}
    if not uc_root.exists():
        return brackets, issues
    for p in uc_root.rglob("UseCase_Bracket.yaml"):
        rel = _to_repo_rel(repo_root, p)
        try:
            data = parse_yaml_file(p)
        except Exception as e:
            issues.append(Issue("ERROR", "usecase_bracket.yaml_parse_failed", f"YAML parse failed: {e}", SourceLocation(rel, 1)))
            continue
        if not isinstance(data, dict):
            issues.append(Issue("ERROR", "usecase_bracket.invalid_type", "UseCase_Bracket must be a YAML mapping/object.", SourceLocation(rel, 1)))
            continue
        uc_id = data.get("id")
        if not uc_id or not isinstance(uc_id, str):
            issues.append(Issue("ERROR", "usecase_bracket.missing_id", "Missing required field 'id'.", SourceLocation(rel, 1)))
            continue
        schema_version = data.get("schema_version")
        if schema_version != "2.0":
            # legacy logic flag (warning; strict can upgrade later)
            # try locate schema_version line
            line = 1
            try:
                lines = _read_text_lines(p)
                for i, ln in enumerate(lines):
                    if re.match(r"^\s*schema_version\s*:", ln):
                        line = i + 1
                        break
            except Exception:
                pass
            issues.append(
                Issue(
                    "WARN",
                    "usecase_bracket.legacy_schema_version",
                    f"UseCase_Bracket schema_version expected '2.0' but found '{schema_version}'.",
                    SourceLocation(rel, line),
                )
            )
        if uc_id in brackets:
            issues.append(Issue("ERROR", "usecase_bracket.duplicate_id", f"Duplicate UseCase_Bracket id '{uc_id}'.", SourceLocation(rel, 1)))
            continue
        brackets[uc_id] = {
            "id": uc_id,
            "source": rel,
            "raw": data,
        }
    return brackets, issues


def scan_usecase_factsheets(repo_root: Path) -> Tuple[Dict[str, Dict[str, Any]], List[Issue]]:
    """
    Factsheets are still hybrid. We only index them (id, paths) for reporting/drift,
    and to provide source-line mapping for missing references during migration.
    """
    issues: List[Issue] = []
    uc_root = repo_root / "core" / "usecases"
    out: Dict[str, Dict[str, Any]] = {}
    for p in uc_root.rglob("*_Factsheet.md"):
        # ignore templates
        if "templates" in p.parts:
            continue
        rel = _to_repo_rel(repo_root, p)
        try:
            lines = _read_text_lines(p)
        except Exception as e:
            issues.append(Issue("ERROR", "factsheet.read_failed", f"Read failed: {e}", SourceLocation(rel, 1)))
            continue
        fm = extract_frontmatter(lines)
        if not fm:
            issues.append(Issue("WARN", "factsheet.missing_frontmatter", "Factsheet missing YAML frontmatter.", SourceLocation(rel, 1)))
            continue
        _, _, fm_lines = fm
        uc_id = frontmatter_get_scalar(fm_lines, "id")
        if not uc_id:
            issues.append(Issue("WARN", "factsheet.missing_id", "Frontmatter missing 'id'.", SourceLocation(rel, 1)))
            continue
        rec = out.setdefault(uc_id, {"id": uc_id, "business": None, "technical": None})
        if p.name == "Business_Factsheet.md":
            rec["business"] = rel
        elif p.name == "Technical_Factsheet.md":
            rec["technical"] = rel
    return out, issues


def normalize_action_governance(action_raw: Dict[str, Any]) -> Tuple[Dict[str, Optional[str]], List[str]]:
    """
    Returns normalized governance dict and warnings.
    """
    warnings: List[str] = []
    operational = action_raw.get("operational_execution") if isinstance(action_raw, dict) else None
    owner_role = None
    if isinstance(operational, dict):
        por = operational.get("primary_owner_role")
        if isinstance(por, str) and por.strip():
            owner_role = por.strip()
    gov = action_raw.get("governance") if isinstance(action_raw, dict) else None
    steward_role = None
    if isinstance(gov, dict):
        sr = gov.get("steward_role")
        if isinstance(sr, str) and sr.strip():
            steward_role = sr.strip()
    if not steward_role:
        warnings.append("Missing governance.steward_role (required by ontology); add during migration.")
    if not owner_role:
        warnings.append("Missing operational_execution.primary_owner_role (owner_role).")
    return {"owner_role": owner_role, "steward_role": steward_role}, warnings


def build_linked_sets_from_brackets(brackets: Dict[str, Dict[str, Any]]) -> Tuple[Set[str], Set[str], Set[str], List[Issue]]:
    """
    Returns (usecase_ids_active, kpi_ids_linked, action_ids_linked, issues)
    """
    issues: List[Issue] = []
    uc_ids_active: Set[str] = set()
    kpi_ids: Set[str] = set()
    action_ids: Set[str] = set()
    for uc_id, rec in brackets.items():
        raw = rec.get("raw", {})
        src = rec.get("source", "")
        gov = raw.get("governance") if isinstance(raw, dict) else None
        status = None
        if isinstance(gov, dict):
            status = gov.get("status")
        is_active = (status == "active") or (status is None)  # default to active if not set
        if not is_active:
            continue
        uc_ids_active.add(uc_id)
        ob = raw.get("ontology_bracket") if isinstance(raw, dict) else None
        if not isinstance(ob, dict):
            issues.append(Issue("ERROR", "usecase_bracket.missing_ontology_bracket", "Missing ontology_bracket block.", SourceLocation(src, 1)))
            continue
        sk = ob.get("strategic_kpi_id")
        if isinstance(sk, str) and sk.strip():
            kpi_ids.add(sk.strip())
        else:
            issues.append(Issue("ERROR", "usecase_bracket.missing_strategic_kpi_id", "Missing ontology_bracket.strategic_kpi_id.", SourceLocation(src, 1)))
        infl = ob.get("influencing_kpi_ids")
        if infl is None:
            infl_list: List[str] = []
        elif isinstance(infl, list):
            infl_list = [x for x in infl if isinstance(x, str)]
        else:
            infl_list = []
            issues.append(Issue("ERROR", "usecase_bracket.invalid_influencing_kpi_ids", "ontology_bracket.influencing_kpi_ids must be a list.", SourceLocation(src, 1)))
        for k in infl_list:
            if k.strip():
                kpi_ids.add(k.strip())
        acts = ob.get("action_code_ids")
        if acts is None:
            act_list: List[str] = []
        elif isinstance(acts, list):
            act_list = [x for x in acts if isinstance(x, str)]
        else:
            act_list = []
            issues.append(Issue("ERROR", "usecase_bracket.invalid_action_code_ids", "ontology_bracket.action_code_ids must be a list.", SourceLocation(src, 1)))
        for a in act_list:
            if a.strip():
                action_ids.add(a.strip())
    return uc_ids_active, kpi_ids, action_ids, issues


def load_validation_results_if_present(repo_root: Path, results_path: Optional[Path]) -> Tuple[Optional[Dict[str, Any]], List[Issue]]:
    issues: List[Issue] = []
    if results_path is None:
        candidate = repo_root / "tooling" / "validation" / "results" / "latest_results.json"
        results_path = candidate if candidate.exists() else None
    if results_path is None:
        return None, issues
    rel = _to_repo_rel(repo_root, results_path)
    try:
        data = json.loads(_read_text(results_path))
        if not isinstance(data, dict):
            issues.append(Issue("WARN", "validation_results.invalid", "latest_results.json must be a JSON object.", SourceLocation(rel, 1)))
            return None, issues
        return data, issues
    except Exception as e:
        issues.append(Issue("WARN", "validation_results.read_failed", f"Failed to read validation results: {e}", SourceLocation(rel, 1)))
        return None, issues


def _extract_failed_data_contracts(results: Dict[str, Any]) -> Set[str]:
    """
    Best-effort: returns a set of repo-relative paths (posix) for data contracts that failed.
    The exact schema of latest_results.json is not yet fixed; we try common patterns.
    """
    failed: Set[str] = set()

    # Pattern A: { "checks": [ { "name": "...", "status": "FAIL", "targets": [...] } ] }
    checks = results.get("checks")
    if isinstance(checks, list):
        for c in checks:
            if not isinstance(c, dict):
                continue
            status = c.get("status") or c.get("result")
            if str(status).upper() not in {"FAIL", "FAILED", "ERROR"}:
                continue
            targets = c.get("targets") or c.get("files") or c.get("artifacts")
            if isinstance(targets, list):
                for t in targets:
                    if isinstance(t, str) and "core/data_contracts/domains/" in t.replace("\\", "/"):
                        failed.add(t.replace("\\", "/"))

    # Pattern B: { "artifacts": { "<path>": { "status": "FAIL" } } }
    artifacts = results.get("artifacts")
    if isinstance(artifacts, dict):
        for k, v in artifacts.items():
            if not isinstance(k, str):
                continue
            if "core/data_contracts/domains/" not in k.replace("\\", "/"):
                continue
            status = None
            if isinstance(v, dict):
                status = v.get("status") or v.get("result")
            if str(status).upper() in {"FAIL", "FAILED", "ERROR"}:
                failed.add(k.replace("\\", "/"))

    return failed


def _normalize_contract_ref(s: str) -> str:
    """
    Normalize known (sometimes duplicated) path patterns found in factsheets.
    Example: 'core/core/core/data_contracts/domains/commercial_sales.yaml' -> 'core/data_contracts/domains/commercial_sales.yaml'
    """
    if not s:
        return s
    p = s.strip().replace("\\", "/")
    # strip markdown link wrappers if any
    p = re.sub(r"^\[([^\]]+)\]\([^)]+\)$", r"\1", p)
    # collapse repeated 'core/' prefixes before data_contracts
    p = re.sub(r"(?:^|/)(core/)+(data_contracts/)", r"core/\2", p)
    # remove leading ./ if present
    p = p[2:] if p.startswith("./") else p
    # ensure no double slashes
    p = re.sub(r"/{2,}", "/", p)
    return p


def _extract_domain_contract_from_technical_factsheet(text: str) -> Optional[str]:
    """
    Extract the 'Domain Data Contract' reference path from a Technical_Factsheet.md body.
    """
    # Example: - **Domain Data Contract:** core/core/core/data_contracts/domains/commercial_sales.yaml
    m = re.search(r"(?m)^\s*-\s*\*\*Domain Data Contract:\*\*\s*(.+?)\s*$", text)
    if not m:
        return None
    return _normalize_contract_ref(m.group(1))


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build ActionReady master registry and orphan reports.")
    parser.add_argument("--repo-root", default="", help="Repository root. Default: inferred from this script location.")
    parser.add_argument("--out-dir", default=".", help="Output directory (relative to repo root). Default: repo root.")
    parser.add_argument("--strict", action="store_true", help="Fail (exit 1) if orphans detected or any ERROR issues.")
    parser.add_argument(
        "--validation-results",
        default="",
        help="Optional path to tooling/validation/results/latest_results.json. If omitted, script checks the default path.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve() if args.repo_root else _repo_root_from_file()
    out_dir = (repo_root / args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    issues: List[Issue] = []

    # Scan primitives
    kpis, kpi_issues = scan_kpi_catalog(repo_root)
    actions, action_issues = scan_action_codes(repo_root)
    brackets, bracket_issues = scan_usecase_brackets(repo_root)
    factsheets, factsheet_issues = scan_usecase_factsheets(repo_root)
    issues.extend(kpi_issues + action_issues + bracket_issues + factsheet_issues)

    # Linked sets from active brackets
    uc_ids_active, linked_kpis, linked_actions, link_issues = build_linked_sets_from_brackets(brackets)
    issues.extend(link_issues)

    # UseCase -> Data contract mapping (from Technical factsheet references)
    # This is needed for Trust-Score propagation.
    usecase_domain_contract: Dict[str, str] = {}
    for uc_id in brackets.keys():
        # Resolve technical factsheet path (documentation pointer default: ./Technical_Factsheet.md)
        uc_src = brackets[uc_id].get("source", "")
        uc_dir = (repo_root / uc_src).parent if uc_src else (repo_root / "core" / "usecases")
        tech_path = uc_dir / "Technical_Factsheet.md"
        if tech_path.exists():
            try:
                dom_contract = _extract_domain_contract_from_technical_factsheet(_read_text(tech_path))
                if dom_contract:
                    usecase_domain_contract[uc_id] = dom_contract
            except Exception as e:
                issues.append(
                    Issue(
                        "WARN",
                        "usecase.domain_contract.parse_failed",
                        f"Failed to parse Domain Data Contract from Technical_Factsheet.md: {e}",
                        SourceLocation(_to_repo_rel(repo_root, tech_path), 1),
                    )
                )

    # Referential integrity: bracket references must exist (hard errors with line mapping)
    for uc_id in sorted(uc_ids_active):
        rec = brackets.get(uc_id)
        if not rec:
            continue
        src = rec.get("source", "")
        raw = rec.get("raw", {})
        ob = raw.get("ontology_bracket", {}) if isinstance(raw, dict) else {}
        if isinstance(ob, dict):
            # strategic
            sk = ob.get("strategic_kpi_id")
            if isinstance(sk, str) and sk.strip() and sk.strip() not in kpis:
                p = repo_root / Path(src)
                line = 1
                try:
                    lines = _read_text_lines(repo_root / src)
                    line = find_line_for_yaml_kv(yaml_lines=lines, yaml_start_line=1, keys=["strategic_kpi_id"], value=sk.strip()) or 1
                except Exception:
                    pass
                issues.append(
                    Issue(
                        "ERROR",
                        "ref_integrity.missing_kpi",
                        f"KPI-ID '{sk.strip()}' not found in KPI catalog.",
                        SourceLocation(src, line),
                    )
                )
            # influencing list
            infl = ob.get("influencing_kpi_ids")
            if isinstance(infl, list):
                for kid in infl:
                    if isinstance(kid, str) and kid.strip() and kid.strip() not in kpis:
                        line = 1
                        try:
                            lines = _read_text_lines(repo_root / src)
                            line = find_line_containing_token(lines, kid.strip()) or 1
                        except Exception:
                            pass
                        issues.append(
                            Issue(
                                "ERROR",
                                "ref_integrity.missing_kpi",
                                f"KPI-ID '{kid.strip()}' not found in KPI catalog.",
                                SourceLocation(src, line),
                            )
                        )
            # actions
            acts = ob.get("action_code_ids")
            if isinstance(acts, list):
                for aid in acts:
                    if isinstance(aid, str) and aid.strip() and aid.strip() not in actions:
                        line = 1
                        try:
                            lines = _read_text_lines(repo_root / src)
                            # Find the action ID line in file (raw search)
                            for i, ln in enumerate(lines):
                                if aid in ln:
                                    line = i + 1
                                    break
                        except Exception:
                            pass
                        issues.append(
                            Issue(
                                "ERROR",
                                "ref_integrity.missing_action_code",
                                f"ActionCode '{aid.strip()}' not found in core/action_codes.",
                                SourceLocation(src, line),
                            )
                        )

    # Orphan detection (Full-scan vs Linked-scan)
    orphan_items: List[Dict[str, Any]] = []

    # KPI orphans: catalog KPI IDs not referenced by any active bracket
    for kpi_id, rec in sorted(kpis.items(), key=lambda kv: kv[0]):
        if kpi_id not in linked_kpis:
            orphan_items.append(
                {
                    "type": "kpi",
                    "id": kpi_id,
                    "source": rec.source,
                    "line": rec.line,
                    "reason": "Not referenced by any active UseCase_Bracket.",
                }
            )

    # Action orphans: action code files not referenced by any active bracket
    for aid, arec in sorted(actions.items(), key=lambda kv: kv[0]):
        if aid not in linked_actions:
            orphan_items.append(
                {
                    "type": "action_code",
                    "id": aid,
                    "source": arec.get("source"),
                    "reason": "Not referenced by any active UseCase_Bracket.",
                }
            )

    # Usecase orphans: usecases that exist as factsheets but have no bracket (during migration)
    for uc_id, frec in sorted(factsheets.items(), key=lambda kv: kv[0]):
        if uc_id not in brackets:
            orphan_items.append(
                {
                    "type": "use_case",
                    "id": uc_id,
                    "source": frec.get("business") or frec.get("technical"),
                    "reason": "Factsheets exist but no UseCase_Bracket.yaml found (migration pending).",
                }
            )

    # Trust-score integration
    results_path = Path(args.validation_results).resolve() if args.validation_results else None
    validation_results, vr_issues = load_validation_results_if_present(repo_root, results_path)
    issues.extend(vr_issues)
    failed_contracts: Set[str] = set()
    if validation_results:
        failed_contracts = {_normalize_contract_ref(x) for x in _extract_failed_data_contracts(validation_results)}

    # Contract -> KPI linkage (via UseCase_Bracket KPIs)
    contract_to_kpis: Dict[str, Set[str]] = {}
    if usecase_domain_contract:
        for uc_id in brackets.keys():
            contract = usecase_domain_contract.get(uc_id)
            if not contract:
                continue
            raw = brackets[uc_id].get("raw", {})
            ob = raw.get("ontology_bracket", {}) if isinstance(raw, dict) else {}
            if not isinstance(ob, dict):
                continue
            kset: Set[str] = set()
            sk = ob.get("strategic_kpi_id")
            if isinstance(sk, str) and sk.strip():
                kset.add(sk.strip())
            infl = ob.get("influencing_kpi_ids")
            if isinstance(infl, list):
                for kid in infl:
                    if isinstance(kid, str) and kid.strip():
                        kset.add(kid.strip())
            if contract not in contract_to_kpis:
                contract_to_kpis[contract] = set()
            contract_to_kpis[contract].update(kset)

    # Build master registry objects
    registry_kpis: Dict[str, Any] = {}
    for kpi_id, rec in kpis.items():
        trust_score: Optional[int] = None
        if validation_results:
            # Determine if KPI is linked to any domain contract(s)
            linked_contracts = [c for c, ks in contract_to_kpis.items() if kpi_id in ks]
            if linked_contracts:
                trust_score = 0 if any(c in failed_contracts for c in linked_contracts) else 1
        registry_kpis[kpi_id] = {
            "id": kpi_id,
            "kpi_role": rec.kpi_role,
            "governance": {
                "owner_role": rec.governance.get("owner_role"),
                "steward_role": rec.governance.get("steward_role"),
                "legacy": {
                    "business_owner": rec.governance.get("business_owner"),
                    "data_owner": rec.governance.get("data_owner"),
                    "steward": rec.governance.get("steward"),
                },
            },
            "trust_score": trust_score,
            "linked_domain_contracts": sorted([c for c, ks in contract_to_kpis.items() if kpi_id in ks]),
            "source": {"file": rec.source, "line": rec.line},
        }
        # Migration warnings for governance fallbacks
        if not rec.governance.get("owner_role"):
            issues.append(
                Issue(
                    "WARN",
                    "governance.owner_role.missing",
                    f"KPI '{kpi_id}' missing owner role; fallback failed (business_owner/data_owner empty).",
                    SourceLocation(rec.source, rec.line),
                )
            )
        if rec.governance.get("steward_role") and not rec.governance.get("steward"):
            # derived from data_owner
            issues.append(
                Issue(
                    "WARN",
                    "governance.steward_role.derived_from_data_owner",
                    f"KPI '{kpi_id}' steward_role derived from data_owner; add governance.steward for clean migration.",
                    SourceLocation(rec.source, rec.line),
                )
            )

    registry_actions: Dict[str, Any] = {}
    for aid, arec in actions.items():
        raw = arec.get("raw", {})
        gov_norm, gov_warnings = normalize_action_governance(raw if isinstance(raw, dict) else {})
        registry_actions[aid] = {
            "id": aid,
            "governance": gov_norm,
            "source": {"file": arec.get("source")},
        }
        for w in gov_warnings:
            issues.append(Issue("WARN", "governance.action_normalization", f"Action '{aid}': {w}", SourceLocation(arec.get("source", ""), 1)))

    registry_usecases: Dict[str, Any] = {}
    for uc_id, brec in brackets.items():
        raw = brec.get("raw", {})
        src = brec.get("source", "")
        gov = raw.get("governance", {}) if isinstance(raw, dict) else {}
        ob = raw.get("ontology_bracket", {}) if isinstance(raw, dict) else {}
        docs = raw.get("documentation", {}) if isinstance(raw, dict) else {}
        registry_usecases[uc_id] = {
            "id": uc_id,
            "name": raw.get("name"),
            "domain": raw.get("domain"),
            "governance": gov,
            "ontology_bracket": ob,
            "value_driver_model": raw.get("value_driver_model"),
            "ux_layout_rules": raw.get("ux_layout_rules"),
            "documentation": docs,
            "source": {"file": src},
        }
        # Governance required by ontology
        if isinstance(gov, dict):
            if not gov.get("owner_role"):
                issues.append(Issue("ERROR", "usecase_bracket.missing_owner_role", f"UseCase '{uc_id}' missing governance.owner_role.", SourceLocation(src, 1)))
            if not gov.get("steward_role"):
                issues.append(Issue("ERROR", "usecase_bracket.missing_steward_role", f"UseCase '{uc_id}' missing governance.steward_role.", SourceLocation(src, 1)))
        else:
            issues.append(Issue("ERROR", "usecase_bracket.missing_governance", f"UseCase '{uc_id}' missing governance block.", SourceLocation(src, 1)))

    edges: List[Dict[str, Any]] = []
    for uc_id in sorted(uc_ids_active):
        urec = brackets.get(uc_id, {})
        raw = urec.get("raw", {})
        src = urec.get("source", "")
        ob = raw.get("ontology_bracket", {}) if isinstance(raw, dict) else {}
        if not isinstance(ob, dict):
            continue
        sk = ob.get("strategic_kpi_id")
        if isinstance(sk, str) and sk.strip():
            edges.append({"type": "use_case_strategic_kpi", "from": uc_id, "to": sk.strip(), "evidence": {"file": src}})
        infl = ob.get("influencing_kpi_ids")
        if isinstance(infl, list):
            for kid in infl:
                if isinstance(kid, str) and kid.strip():
                    edges.append({"type": "use_case_influencing_kpi", "from": uc_id, "to": kid.strip(), "evidence": {"file": src}})
        acts = ob.get("action_code_ids")
        if isinstance(acts, list):
            for aid in acts:
                if isinstance(aid, str) and aid.strip():
                    edges.append({"type": "use_case_subscribes_action", "from": uc_id, "to": aid.strip(), "evidence": {"file": src}})

        # Use case -> domain contract edge (best-effort)
        contract = usecase_domain_contract.get(uc_id)
        if contract:
            edges.append({"type": "use_case_uses_domain_contract", "from": uc_id, "to": contract, "evidence": {"file": src}})

    # KPI -> domain contract edges (derived)
    for contract, ks in contract_to_kpis.items():
        for kpi_id in ks:
            edges.append({"type": "kpi_supported_by_domain_contract", "from": kpi_id, "to": contract, "evidence": {"derived_from": "usecase_bracket+technical_factsheet"}})

    # DisplayFolder conflict rule computation (strategic precedence across UCs)
    # Determine global strategic set: any KPI used as strategic in any active bracket.
    strategic_global: Set[str] = set()
    for uc_id in uc_ids_active:
        raw = brackets[uc_id]["raw"]
        ob = raw.get("ontology_bracket", {}) if isinstance(raw, dict) else {}
        if isinstance(ob, dict):
            sk = ob.get("strategic_kpi_id")
            if isinstance(sk, str) and sk.strip():
                strategic_global.add(sk.strip())

    # Add computed classification to KPI objects for downstream tooling.
    for kpi_id in registry_kpis.keys():
        if kpi_id in strategic_global:
            registry_kpis[kpi_id]["computed_role_global"] = "strategic"
        elif kpi_id in linked_kpis:
            registry_kpis[kpi_id]["computed_role_global"] = "influencing"
        else:
            registry_kpis[kpi_id]["computed_role_global"] = "unlinked"

    master_registry = {
        "meta": {
            "generated_at_utc": _utc_now_iso(),
            "registry_version": "0.1",
            "repo_root": repo_root.as_posix(),
            "validation_results_present": bool(validation_results),
            "failed_data_contracts": sorted(failed_contracts),
        },
        "objects": {
            "use_cases": registry_usecases,
            "kpis": registry_kpis,
            "action_codes": registry_actions,
        },
        "edges": edges,
        "issues": [
            {
                "severity": iss.severity,
                "code": iss.code,
                "message": iss.message,
                **(
                    {"location": {"file": iss.location.file, "line": iss.location.line}}
                    if iss.location
                    else {}
                ),
            }
            for iss in issues
        ],
    }

    orphans_report = {
        "meta": {
            "generated_at_utc": _utc_now_iso(),
            "strict_mode": bool(args.strict),
            "active_use_cases": sorted(uc_ids_active),
        },
        "orphans": orphan_items,
        "counts": {
            "total": len(orphan_items),
            "kpis": sum(1 for x in orphan_items if x.get("type") == "kpi"),
            "action_codes": sum(1 for x in orphan_items if x.get("type") == "action_code"),
            "use_cases": sum(1 for x in orphan_items if x.get("type") == "use_case"),
        },
    }

    master_path = out_dir / "master_registry.json"
    orphans_path = out_dir / "orphans_report.json"
    _write_json(master_path, master_registry)
    _write_json(orphans_path, orphans_report)

    # Determine exit code
    has_errors = any(iss.severity == "ERROR" for iss in issues)
    has_orphans = len(orphan_items) > 0
    if args.strict and (has_errors or has_orphans):
        return 1
    if has_errors:
        # non-strict still signals errors via non-zero? Keep 1 to be safe in CI usage.
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

