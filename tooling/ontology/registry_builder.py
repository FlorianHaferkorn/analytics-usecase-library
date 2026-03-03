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
import difflib
import json
import os
import re
import sys
import textwrap
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
    depends_on_measures: List[str] = dataclasses.field(default_factory=list)
    causal_links: Optional[Dict[str, Any]] = None


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

                def _extract_depends_on_measures() -> List[str]:
                    """
                    Extract technical.depends_on_measures from this KPI YAML chunk using a line-based parser.
                    We avoid a full YAML parse here because some catalog chunks can be "loose YAML".
                    """
                    for i, ln in enumerate(chunk_lines):
                        mm = re.match(r"^(\s*)depends_on_measures\s*:\s*(.*?)\s*$", ln)
                        if not mm:
                            continue
                        indent = len(mm.group(1) or "")
                        tail = (mm.group(2) or "").strip()
                        out: List[str] = []
                        # Inline list: [a, b, c]
                        if tail.startswith("[") and tail.endswith("]"):
                            inner = tail[1:-1].strip()
                            if inner:
                                for part in inner.split(","):
                                    tok = part.strip().strip('"').strip("'")
                                    if tok:
                                        out.append(tok)
                            return out
                        # Multi-line list items (indented deeper than the key line)
                        for j in range(i + 1, len(chunk_lines)):
                            ln2 = chunk_lines[j]
                            lead = len(ln2) - len(ln2.lstrip(" "))
                            if lead < indent:
                                break
                            # Stop when we hit the next key at the same indentation level.
                            if lead == indent and re.match(r"^\s*[A-Za-z0-9_]+\s*:\s*", ln2):
                                break
                            m2 = re.match(r"^\s*-\s*([^\s#]+)\s*", ln2)
                            if m2:
                                tok = m2.group(1).strip().strip('"').strip("'")
                                if tok:
                                    out.append(tok)
                        return out
                    return []

                depends_on_measures: List[str] = _extract_depends_on_measures()
                causal_links: Optional[Dict[str, Any]] = None
                # Best-effort parse of causal_links (if present) from the chunk using YAML loader.
                if yaml is not None:
                    try:
                        parsed = yaml.safe_load("\n".join(chunk_lines))
                        # parsed can be a list with one mapping
                        if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
                            cl = parsed[0].get("causal_links")
                            if isinstance(cl, dict):
                                causal_links = cl
                    except Exception:
                        # keep best-effort: ignore parse errors here (Stage 1 validates catalog separately)
                        causal_links = None

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
                    depends_on_measures=depends_on_measures,
                    causal_links=causal_links,
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
        rec = out.setdefault(uc_id, {"id": uc_id, "business": None})
        if p.name == "Business_Factsheet.md":
            rec["business"] = rel
    return out, issues


def _action_code_display_fields(raw: Dict[str, Any], gov_norm: Dict[str, Optional[str]]) -> Dict[str, Any]:
    """
    Derive display fields for adapters (trigger_summary, owner_role, steps).
    Aligns with generate_tmdl_measures.ps1 Load-ActionCodeYaml for _ActionReady_Logic.tmdl.
    """
    out: Dict[str, Any] = {}
    if not isinstance(raw, dict):
        return out

    # trigger_summary: trigger.type + trigger.levels L1/L2/L3 severity
    trigger = raw.get("trigger")
    trigger_summary = "(no trigger defined)"
    if isinstance(trigger, dict):
        t_type = trigger.get("type")
        type_str = str(t_type).strip() if t_type else ""
        levels = trigger.get("levels")
        level_parts: List[str] = []
        if isinstance(levels, dict):
            for lvl in ("L1", "L2", "L3"):
                lvl_obj = levels.get(lvl)
                if isinstance(lvl_obj, dict):
                    sev = lvl_obj.get("severity")
                    if isinstance(sev, str) and sev.strip():
                        level_parts.append(f"{lvl}: {sev.strip()}")
        if level_parts:
            trigger_summary = f"{type_str} ({', '.join(level_parts)})" if type_str else f"({', '.join(level_parts)})"
        elif type_str:
            trigger_summary = type_str
    out["trigger_summary"] = trigger_summary

    # owner_role: primary_owner_role | owner_role | governance.owner_role
    owner = (
        (raw.get("primary_owner_role") if isinstance(raw.get("primary_owner_role"), str) else None)
        or (raw.get("owner_role") if isinstance(raw.get("owner_role"), str) else None)
        or (gov_norm.get("owner_role") if isinstance(gov_norm, dict) else None)
    )
    out["owner_role"] = (owner.strip() if owner else None) or "TBD"

    # steps: operational_execution.steps (list of strings)
    op_exec = raw.get("operational_execution")
    steps: List[str] = []
    if isinstance(op_exec, dict):
        s = op_exec.get("steps")
        if isinstance(s, list):
            for item in s:
                if isinstance(item, str) and item.strip():
                    steps.append(item.strip())
    out["steps"] = steps

    return out


def normalize_action_governance(action_raw: Dict[str, Any]) -> Tuple[Dict[str, Optional[str]], List[str]]:
    """
    Returns normalized governance dict and warnings.
    Lean 2.0: owner_role / steward_role are top-level fields.
    Legacy fallback: operational_execution.primary_owner_role, governance.steward_role.
    """
    warnings: List[str] = []
    if not isinstance(action_raw, dict):
        return {"owner_role": None, "steward_role": None}, ["Action raw data is not a dict."]

    # --- owner_role ---
    owner_role = None
    # Lean 2.0: top-level
    top_or = action_raw.get("owner_role")
    if isinstance(top_or, str) and top_or.strip():
        owner_role = top_or.strip()
    # Legacy fallback: operational_execution.primary_owner_role
    if not owner_role:
        operational = action_raw.get("operational_execution")
        if isinstance(operational, dict):
            por = operational.get("primary_owner_role")
            if isinstance(por, str) and por.strip():
                owner_role = por.strip()

    # --- steward_role ---
    steward_role = None
    # Lean 2.0: top-level
    top_sr = action_raw.get("steward_role")
    if isinstance(top_sr, str) and top_sr.strip():
        steward_role = top_sr.strip()
    # Legacy fallback: governance.steward_role
    if not steward_role:
        gov = action_raw.get("governance")
        if isinstance(gov, dict):
            sr = gov.get("steward_role")
            if isinstance(sr, str) and sr.strip():
                steward_role = sr.strip()

    if not owner_role:
        warnings.append("Missing owner_role (top-level or operational_execution.primary_owner_role).")
    if not steward_role:
        warnings.append("Missing steward_role (top-level or governance.steward_role).")
    return {"owner_role": owner_role, "steward_role": steward_role}, warnings


def _extract_kpis_from_action(raw: Dict[str, Any]) -> Set[str]:
    """
    Extract all KPI IDs referenced by an action code (for transitive linkage).
    Used to expand the active KPI set: KPIs referenced by subscribed actions count as linked.
    """
    kpis: Set[str] = set()
    if not isinstance(raw, dict):
        return kpis

    def _add(v: Any) -> None:
        if isinstance(v, str) and v.strip():
            kpis.add(v.strip())

    # kpis.trigger_kpis, guardrail_kpis, outcome_kpis
    kpis_block = raw.get("kpis")
    if isinstance(kpis_block, dict):
        for key in ("trigger_kpis", "guardrail_kpis", "outcome_kpis"):
            arr = kpis_block.get(key)
            if isinstance(arr, list):
                for item in arr:
                    if isinstance(item, dict):
                        _add(item.get("kpi_id"))

    # strategic_alignment.strategic_kpis
    strat = raw.get("strategic_alignment")
    if isinstance(strat, dict):
        sk_arr = strat.get("strategic_kpis")
        if isinstance(sk_arr, list):
            for item in sk_arr:
                if isinstance(item, dict):
                    _add(item.get("id"))

    # trigger.levels.*.condition.metric_kpi_id
    trigger = raw.get("trigger")
    if isinstance(trigger, dict):
        levels = trigger.get("levels")
        if isinstance(levels, dict):
            for lvl in levels.values():
                if isinstance(lvl, dict):
                    cond = lvl.get("condition")
                    if isinstance(cond, dict):
                        _add(cond.get("metric_kpi_id"))
        # trigger.evaluation.minimum_data.volume_guardrail.metric_kpi_id
        ev = trigger.get("evaluation")
        if isinstance(ev, dict):
            min_data = ev.get("minimum_data")
            if isinstance(min_data, dict):
                vg = min_data.get("volume_guardrail")
                if isinstance(vg, dict) and vg.get("enabled"):
                    _add(vg.get("metric_kpi_id"))

    # impact.expected_range.metric_kpi_id
    impact = raw.get("impact")
    if isinstance(impact, dict):
        er = impact.get("expected_range")
        if isinstance(er, dict):
            _add(er.get("metric_kpi_id"))

    # impact_valuation.success_window.metric_kpi_id
    iv = raw.get("impact_valuation")
    if isinstance(iv, dict):
        sw = iv.get("success_window")
        if isinstance(sw, dict):
            _add(sw.get("metric_kpi_id"))

    return kpis


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
        orch = raw.get("orchestration") or raw.get("ontology_bracket") if isinstance(raw, dict) else None
        if not isinstance(orch, dict):
            issues.append(Issue("ERROR", "usecase_bracket.missing_orchestration", "Missing orchestration block.", SourceLocation(src, 1)))
            continue
        sk = orch.get("strategic_kpi_id")
        if isinstance(sk, str) and sk.strip():
            kpi_ids.add(sk.strip())
        else:
            issues.append(Issue("ERROR", "usecase_bracket.missing_strategic_kpi_id", "Missing orchestration.strategic_kpi_id.", SourceLocation(src, 1)))
        infl = orch.get("influencing_kpi_ids")
        if infl is None:
            infl_list: List[str] = []
        elif isinstance(infl, list):
            infl_list = [x for x in infl if isinstance(x, str)]
        else:
            infl_list = []
            issues.append(Issue("ERROR", "usecase_bracket.invalid_influencing_kpi_ids", "orchestration.influencing_kpi_ids must be a list.", SourceLocation(src, 1)))
        for k in infl_list:
            if k.strip():
                kpi_ids.add(k.strip())
        acts = orch.get("action_code_ids")
        if acts is None:
            act_list: List[str] = []
        elif isinstance(acts, list):
            act_list = [x for x in acts if isinstance(x, str)]
        else:
            act_list = []
            issues.append(Issue("ERROR", "usecase_bracket.invalid_action_code_ids", "orchestration.action_code_ids must be a list.", SourceLocation(src, 1)))
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
        # latest_results.json may be written with a UTF-8 BOM depending on environment.
        data = json.loads(results_path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            issues.append(Issue("WARN", "validation_results.invalid", "latest_results.json must be a JSON object.", SourceLocation(rel, 1)))
            return None, issues
        return data, issues
    except Exception as e:
        issues.append(Issue("WARN", "validation_results.read_failed", f"Failed to read validation results: {e}", SourceLocation(rel, 1)))
        return None, issues


def _load_contract_validation_failed(repo_root: Path) -> Set[str]:
    """
    Read tooling/validation/results/contract_validation.json if present.
    Returns a set of normalized repo-relative paths (posix) for failed domain contracts.
    """
    path = repo_root / "tooling" / "validation" / "results" / "contract_validation.json"
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            return set()
        raw = data.get("failed_contracts")
        if not isinstance(raw, list):
            return set()
        return {_normalize_contract_ref(x) for x in raw if isinstance(x, str)}
    except Exception:
        return set()


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
    LEGACY: Extract the 'Domain Data Contract' reference path from a Technical_Factsheet.md body.
    Technical_Factsheet.md was removed in Lean 2.0; data contract refs now live in
    UseCase_Bracket.yaml overrides.data_contract_ref. This function is unused but retained
    for backward compatibility during migration.
    """
    # Example: - **Domain Data Contract:** core/core/core/data_contracts/domains/commercial_sales.yaml
    m = re.search(r"(?m)^\s*-\s*\*\*Domain Data Contract:\*\*\s*(.+?)\s*$", text)
    if not m:
        return None
    return _normalize_contract_ref(m.group(1))


def scan_allowed_grains(repo_root: Path) -> Tuple[Set[str], List[Issue]]:
    """
    Collect every ``fact[*].grain`` value from ``core/data_contracts/domains/*.yaml``.
    Returns the set of allowed evidence-grain tokens and any parse issues.
    """
    issues: List[Issue] = []
    grains: Set[str] = set()
    contracts_root = repo_root / "core" / "data_contracts" / "domains"
    if not contracts_root.exists():
        issues.append(
            Issue(
                "WARN",
                "evidence_grain.contracts_dir_missing",
                "Directory core/data_contracts/domains/ not found; evidence-grain validation skipped.",
                SourceLocation("core/data_contracts/domains", 1),
            )
        )
        return grains, issues
    for p in sorted(contracts_root.glob("*.yaml")):
        rel = _to_repo_rel(repo_root, p)
        try:
            data = parse_yaml_file(p)
        except Exception as e:
            issues.append(Issue("WARN", "evidence_grain.contract_parse_failed", f"YAML parse failed: {e}", SourceLocation(rel, 1)))
            continue
        if not isinstance(data, dict):
            continue
        facts = data.get("fact")
        if not isinstance(facts, list):
            continue
        for fact in facts:
            if isinstance(fact, dict):
                grain = fact.get("grain")
                if isinstance(grain, str) and grain.strip():
                    grains.add(grain.strip())
    return grains, issues


def validate_evidence_grains(
    brackets: Dict[str, Dict[str, Any]],
    allowed_grains: Set[str],
    repo_root: Path,
) -> List[Issue]:
    """
    Validate ``evidence_grain`` in every bracket against the governed set of grains
    extracted from domain contracts.

    Rules:
    - ``transaction_line`` is a known placeholder and always rejected (CRITICAL).
    - Any grain not present in ``allowed_grains`` is flagged as a Governance Gap (ERROR).
    """
    issues: List[Issue] = []
    for uc_id, rec in sorted(brackets.items()):
        raw = rec.get("raw", {})
        src = rec.get("source", "")
        ux = raw.get("ux_layout_rules") if isinstance(raw, dict) else None
        if not isinstance(ux, dict):
            continue
        p2 = ux.get("page_2_execution")
        if not isinstance(p2, dict):
            continue
        c300 = p2.get("component_300s")
        if not isinstance(c300, dict):
            continue
        eg = c300.get("evidence_grain")
        if not isinstance(eg, str) or not eg.strip():
            continue
        eg = eg.strip()

        # Locate source line for precise reporting
        line = 1
        try:
            lines = _read_text_lines(repo_root / src)
            found = find_line_for_yaml_kv(
                yaml_lines=lines, yaml_start_line=1, keys=["evidence_grain"], value=eg
            )
            if found:
                line = found
        except Exception:
            pass

        if eg == "transaction_line":
            msg = textwrap.dedent(f"""\
                CRITICAL ERROR: Stage 1 Placeholder Detected

                  File:   {src}
                  Field:  ux_layout_rules.page_2_execution.component_300s.evidence_grain
                  Value:  transaction_line

                  Action Required:
                  Der Wert 'transaction_line' ist ein unzulaessiger Platzhalter.
                  Ein Use Case kann nur "ActionReady" sein, wenn eine reale
                  Daten-Granularitaet definiert ist.
                  Bitte pruefe internal/evidence_grain_audit_results.md und trage
                  die korrekte Grain ein.""")
            issues.append(
                Issue("ERROR", "evidence_grain.placeholder_forbidden", msg, SourceLocation(src, line))
            )
        elif allowed_grains and eg not in allowed_grains:
            close = difflib.get_close_matches(eg, sorted(allowed_grains), n=1, cutoff=0.6)
            if close:
                hint_line = f"1. Pruefe auf Tippfehler. Meintest du eventuell '{close[0]}'?"
            else:
                hint_line = f"1. Erlaubte Grains: {sorted(allowed_grains)}."
            msg = textwrap.dedent(f"""\
                ERROR: Governance Gap - Ungoverned Evidence Grain

                  File:            {src}
                  Attempted Grain: {eg}

                  Reason:
                  Die angegebene Grain ist in keinem aktiven Data Contract unter
                  core/data_contracts/domains/*.yaml definiert.

                  Action Required:
                  {hint_line}
                  2. Falls die Grain neu ist: Erweitere zuerst den entsprechenden
                     Data Contract um diese Fact-Tabelle/Grain, bevor du sie im
                     Bracket verwendest.
                  Hinweis: Ein Use Case darf nur referenzieren, was technisch durch
                  einen Contract abgesichert ist.""")
            issues.append(
                Issue("ERROR", "evidence_grain.governance_gap", msg, SourceLocation(src, line))
            )
    return issues


# ---------------------------------------------------------------------------
# Grain-entity synonym map for action-step text validation
# ---------------------------------------------------------------------------

_GRAIN_ENTITY_SYNONYMS: Dict[str, List[str]] = {
    "invoice_line": ["invoice line", "invoice", "line item"],
    "customer_month": ["customer", "account"],
    "promotion": ["promotion", "promo", "campaign"],
    "entity_month": ["entity", "business unit", "company"],
    "plant_line_product_month": ["plant", "production line", "product"],
    "line_day": ["line", "production line", "shift"],
    "failure_event": ["failure", "event", "breakdown", "asset"],
    "location_sku_month": ["location", "sku", "warehouse", "inventory"],
    "sku_location_month": ["sku", "location", "forecast", "planning"],
    "shipment_line": ["shipment", "delivery", "order"],
    "case": ["case", "ticket", "incident"],
    "agent_day": ["agent", "representative", "resource"],
}


def _extract_evidence_grain(bracket_raw: Dict[str, Any]) -> Optional[str]:
    """Return the evidence_grain string from a bracket's raw YAML, or None."""
    ux = bracket_raw.get("ux_layout_rules")
    if not isinstance(ux, dict):
        return None
    p2 = ux.get("page_2_execution")
    if not isinstance(p2, dict):
        return None
    c300 = p2.get("component_300s")
    if not isinstance(c300, dict):
        return None
    eg = c300.get("evidence_grain")
    return eg.strip() if isinstance(eg, str) and eg.strip() else None


def validate_action_step_entity_references(
    brackets: Dict[str, Dict[str, Any]],
    actions: Dict[str, Dict[str, Any]],
) -> List[Issue]:
    """
    WARN-level check: for every active bracket, verify that each subscribed
    action code's ``operational_execution.steps`` text references the entity
    implied by the bracket's ``evidence_grain``.

    Uses ``_GRAIN_ENTITY_SYNONYMS`` for matching (case-insensitive).
    Non-blocking — emits WARN, does not fail the build.
    """
    issues: List[Issue] = []
    for uc_id, rec in sorted(brackets.items()):
        raw = rec.get("raw", {})
        src = rec.get("source", "")
        eg = _extract_evidence_grain(raw)
        if not eg:
            continue
        synonyms = _GRAIN_ENTITY_SYNONYMS.get(eg)
        if not synonyms:
            continue  # no synonym map for this grain yet; skip silently

        orch = raw.get("orchestration") if isinstance(raw, dict) else None
        if not isinstance(orch, dict):
            continue
        acts = orch.get("action_code_ids")
        if not isinstance(acts, list):
            continue

        for aid in acts:
            if not isinstance(aid, str):
                continue
            aid = aid.strip()
            arec = actions.get(aid)
            if not arec:
                continue
            araw = arec.get("raw", {})
            asrc = arec.get("source", "")
            op_exec = araw.get("operational_execution") if isinstance(araw, dict) else None
            if not isinstance(op_exec, dict):
                continue
            steps = op_exec.get("steps")
            if not isinstance(steps, list):
                continue

            # Concatenate all step texts for a single pass
            all_text = " ".join(str(s) for s in steps).lower()
            # Accept {entity} placeholder as valid entity reference (resolved at runtime)
            if "{entity}" in all_text:
                continue
            if any(syn.lower() in all_text for syn in synonyms):
                continue  # at least one synonym found — OK

            msg = textwrap.dedent(f"""\
                WARN: Action step text does not reference evidence grain entity

                  Action Code: {aid}
                  Use Case:    {uc_id}
                  Grain:       {eg}
                  Expected:    one of {synonyms}

                  None of the step texts mention the entity. Consider rephrasing
                  to prescriptive voice, e.g. "CHECK this {eg.replace('_', ' ')}
                  against the threshold.\"""")
            issues.append(
                Issue("WARN", "action_step.missing_entity_reference", msg, SourceLocation(asrc, 1))
            )
    return issues


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build ActionReady master registry and orphan reports.")
    parser.add_argument("--repo-root", default="", help="Repository root. Default: inferred from this script location.")
    parser.add_argument("--out-dir", default="tooling/ontology/out", help="Output directory (relative to repo root). Default: tooling/ontology/out (canonical).")
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

    # Evidence-grain governance: load allowed grains from domain contracts, validate brackets
    allowed_grains, grain_scan_issues = scan_allowed_grains(repo_root)
    issues.extend(grain_scan_issues)
    grain_validation_issues = validate_evidence_grains(brackets, allowed_grains, repo_root)
    issues.extend(grain_validation_issues)

    # Action-step entity-reference check (WARN-level, non-blocking)
    step_entity_issues = validate_action_step_entity_references(brackets, actions)
    issues.extend(step_entity_issues)

    # Linked sets from active brackets
    uc_ids_active, linked_kpis, linked_actions, link_issues = build_linked_sets_from_brackets(brackets)
    issues.extend(link_issues)

    # Transitive expansion: KPIs referenced by subscribed action codes are also active
    for aid in linked_actions:
        arec = actions.get(aid)
        if not arec:
            continue
        raw = arec.get("raw", {})
        if isinstance(raw, dict):
            linked_kpis.update(_extract_kpis_from_action(raw))

    # UseCase -> Data contract mapping (from bracket overrides.data_contract_ref)
    usecase_domain_contract: Dict[str, str] = {}
    for uc_id in brackets.keys():
        raw = brackets[uc_id].get("raw", {})
        overrides = raw.get("overrides", {}) if isinstance(raw, dict) else {}
        if isinstance(overrides, dict):
            dcr = overrides.get("data_contract_ref")
            if isinstance(dcr, str) and dcr.strip():
                usecase_domain_contract[uc_id] = _normalize_contract_ref(dcr.strip())

    # Org-Registry role validation (showcase override via ANALYTICS_SHOWCASE, default aurora_group; else core)
    _showcase_name = (os.environ.get("ANALYTICS_SHOWCASE") or "").strip() or "aurora_group"
    _showcase_org_roles = repo_root / "showcases" / _showcase_name / "organization" / "org_roles.yaml"
    _core_org_roles = repo_root / "core" / "organization" / "org_roles.yaml"
    org_roles_path = _showcase_org_roles if _showcase_org_roles.exists() else _core_org_roles
    org_roles_ref = str(org_roles_path.relative_to(repo_root)).replace("\\", "/")
    valid_role_ids: Set[str] = set()
    if org_roles_path.exists():
        try:
            org_data = parse_yaml_file(org_roles_path)
            if isinstance(org_data, dict):
                for role in (org_data.get("roles") or []):
                    if isinstance(role, dict) and isinstance(role.get("id"), str):
                        valid_role_ids.add(role["id"])
        except Exception as e:
            issues.append(Issue("WARN", "org_registry.parse_failed", f"Failed to parse org_roles.yaml: {e}",
                                SourceLocation(org_roles_ref, 1)))
    else:
        issues.append(Issue("WARN", "org_registry.not_found", f"{org_roles_ref} not found; role validation skipped.",
                            SourceLocation(org_roles_ref, 1)))

    if valid_role_ids:
        for uc_id, rec in brackets.items():
            raw = rec.get("raw", {})
            src = rec.get("source", "")
            gov = raw.get("governance", {}) if isinstance(raw, dict) else {}
            if isinstance(gov, dict):
                for role_field in ("owner_role", "steward_role"):
                    role_val = gov.get(role_field)
                    if isinstance(role_val, str) and role_val.strip() and role_val.strip() not in valid_role_ids:
                        issues.append(Issue("ERROR", "org_registry.invalid_role",
                                            f"UseCase '{uc_id}' governance.{role_field} '{role_val}' not found in {org_roles_ref}.",
                                            SourceLocation(src, 1)))
        for aid, arec in actions.items():
            raw = arec.get("raw", {}) or {}
            src = arec.get("source", "") or ""
            if not isinstance(raw, dict):
                continue
            for role_field in ("owner_role", "steward_role"):
                role_val = raw.get(role_field)
                if isinstance(role_val, str) and role_val.strip() and role_val.strip() not in valid_role_ids:
                    issues.append(
                        Issue(
                            "ERROR",
                            "org_registry.invalid_role",
                            f"ActionCode '{aid}' {role_field} '{role_val}' not found in {org_roles_ref}.",
                            SourceLocation(src, 1),
                        )
                    )

    # Referential integrity: bracket references must exist (hard errors with line mapping)
    for uc_id in sorted(uc_ids_active):
        rec = brackets.get(uc_id)
        if not rec:
            continue
        src = rec.get("source", "")
        raw = rec.get("raw", {})
        ob = (raw.get("orchestration") or raw.get("ontology_bracket", {})) if isinstance(raw, dict) else {}
        if isinstance(ob, dict):
            # strategic
            sk = ob.get("strategic_kpi_id")
            if isinstance(sk, str) and sk.strip():
                sk_id = sk.strip()
                if sk_id not in kpis:
                    line = 1
                    try:
                        lines = _read_text_lines(repo_root / src)
                        line = find_line_for_yaml_kv(yaml_lines=lines, yaml_start_line=1, keys=["strategic_kpi_id"], value=sk_id) or 1
                    except Exception:
                        pass
                    issues.append(
                        Issue(
                            "ERROR",
                            "ref_integrity.missing_kpi",
                            f"KPI-ID '{sk_id}' not found in KPI catalog.",
                            SourceLocation(src, line),
                        )
                    )
                else:
                    # Strategic KPI role check: must be kpi_role: strategic
                    kpi_rec = kpis[sk_id]
                    role = kpi_rec.kpi_role if hasattr(kpi_rec, "kpi_role") else None
                    if not role:
                        issues.append(
                            Issue(
                                "WARN",
                                "ref_integrity.strategic_kpi_role_missing",
                                f"Strategic KPI '{sk_id}' has no kpi_role; expected 'strategic'.",
                                SourceLocation(kpi_rec.source, kpi_rec.line),
                            )
                        )
                    elif role and str(role).strip().lower() not in ("strategic",):
                        issues.append(
                            Issue(
                                "ERROR",
                                "ref_integrity.strategic_kpi_role_mismatch",
                                f"Strategic KPI '{sk_id}' has kpi_role '{role}'; expected 'strategic'.",
                                SourceLocation(kpi_rec.source, kpi_rec.line),
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

    # Value-driver formula checks: LHS matches strategic_kpi_id, RHS refs in catalog, RHS consistent with influencing
    for uc_id in sorted(uc_ids_active):
        rec = brackets.get(uc_id)
        if not rec:
            continue
        raw = rec.get("raw", {})
        ob = (raw.get("orchestration") or raw.get("ontology_bracket", {})) if isinstance(raw, dict) else {}
        vdm = raw.get("value_driver_model", {}) if isinstance(raw, dict) else {}
        if not isinstance(ob, dict) or not isinstance(vdm, dict):
            continue
        # Lean 2.0: primary_driver should be either a DAX dependency of the strategic KPI or a KPI in the bracket (strategic or influencing).
        primary_driver = vdm.get("primary_driver")
        sk = ob.get("strategic_kpi_id")
        if isinstance(primary_driver, str) and primary_driver.strip() and isinstance(sk, str) and sk.strip():
            sk_id = sk.strip()
            pd = primary_driver.strip()
            kpi_rec = kpis.get(sk_id)
            allowed: Set[str] = set()
            # Allowed = depends_on_measures of strategic KPI (DAX dependency) + bracket KPIs (strategic + influencing).
            if kpi_rec and getattr(kpi_rec, "depends_on_measures", None):
                dom = [x for x in (kpi_rec.depends_on_measures or []) if isinstance(x, str) and x.strip()]
                dom = [x for x in dom if x != sk_id]
                allowed = set(dom)
            allowed.add(sk_id)
            for kid in ob.get("influencing_kpi_ids") or []:
                if isinstance(kid, str) and kid.strip():
                    allowed.add(kid.strip())
            if allowed and pd not in allowed:
                line = 1
                try:
                    lines = _read_text_lines(repo_root / rec.get("source", ""))
                    line = find_line_for_yaml_kv(yaml_lines=lines, yaml_start_line=1, keys=["primary_driver"], value=pd) or 1
                except Exception:
                    pass
                issues.append(
                    Issue(
                        "ERROR",
                        "value_driver.primary_driver_not_dependency",
                        f"UseCase '{uc_id}' primary_driver '{pd}' is not a dependency of strategic KPI '{sk_id}' "
                        f"(allowed depends_on_measures: {sorted(allowed)}).",
                        SourceLocation(rec.get("source", ""), line),
                    )
                )
            elif not allowed:
                issues.append(
                    Issue(
                        "WARN",
                        "value_driver.primary_driver_unverifiable",
                        f"UseCase '{uc_id}' primary_driver '{pd}' cannot be verified because KPI '{sk_id}' has no technical.depends_on_measures metadata.",
                        SourceLocation(rec.get("source", ""), 1),
                    )
                )
        formula = vdm.get("formula")
        if not isinstance(formula, str) or "=" not in formula:
            continue
        infl_set = set()
        for kid in (ob.get("influencing_kpi_ids") or []):
            if isinstance(kid, str) and kid.strip():
                infl_set.add(kid.strip())
        # Parse formula: "lhs = f(rhs1, rhs2, ...)" - extract lhs and rhs tokens
        try:
            lhs_part, rhs_part = formula.split("=", 1)
            lhs = lhs_part.strip().strip(".").strip()
            # Extract tokens from f(...) - simple regex for kpi-like ids (word.word.word)
            rhs_tokens = set(re.findall(r"[a-z]+\.[a-z0-9_.]+", rhs_part))
            if sk and lhs != sk.strip():
                issues.append(
                    Issue("WARN", "value_driver.lhs_mismatch", f"UseCase '{uc_id}' formula LHS '{lhs}' != strategic_kpi_id '{sk}'.", SourceLocation(rec.get("source", ""), 1))
                )
            for tok in rhs_tokens:
                if tok not in kpis:
                    issues.append(
                        Issue("WARN", "value_driver.rhs_unknown", f"UseCase '{uc_id}' formula RHS '{tok}' not in KPI catalog.", SourceLocation(rec.get("source", ""), 1))
                    )
            if infl_set and rhs_tokens:
                # Formula RHS should reference only KPIs that are part of the influencing set (subset check).
                # Influencing KPIs may be a strict superset of what the formula spells out.
                rhs_outside_infl = {t for t in rhs_tokens if t != (sk.strip() if isinstance(sk, str) else "")} - infl_set
                if rhs_outside_infl:
                    issues.append(
                        Issue(
                            "WARN",
                            "value_driver.rhs_not_in_influencing",
                            f"UseCase '{uc_id}' formula RHS references KPIs not listed in influencing_kpi_ids: {sorted(rhs_outside_infl)}.",
                            SourceLocation(rec.get("source", ""), 1),
                        )
                    )
        except Exception:
            pass

    # Causal links: if strategic KPI has causal_links, influencing KPIs should be covered
    for uc_id in sorted(uc_ids_active):
        rec = brackets.get(uc_id)
        if not rec:
            continue
        raw = rec.get("raw", {})
        ob = (raw.get("orchestration") or raw.get("ontology_bracket", {})) if isinstance(raw, dict) else {}
        if not isinstance(ob, dict):
            continue
        sk = ob.get("strategic_kpi_id")
        if not isinstance(sk, str) or not sk.strip():
            continue
        kpi_rec = kpis.get(sk.strip())
        if not kpi_rec or not getattr(kpi_rec, "causal_links", None):
            continue
        cl = kpi_rec.causal_links
        if not isinstance(cl, dict):
            continue
        causal_sources: Set[str] = set()
        for link in (cl.get("links") or []):
            if isinstance(link, dict):
                sid = link.get("influencing_kpi_id") or link.get("source")
                if sid:
                    causal_sources.add(str(sid).strip())
        infl = ob.get("influencing_kpi_ids") or []
        for kid in infl:
            if isinstance(kid, str) and kid.strip() and kid.strip() not in causal_sources:
                issues.append(
                    Issue("WARN", "causal_link.influencing_not_covered", f"UseCase '{uc_id}' influencing KPI '{kid}' not in strategic KPI '{sk}' causal_links.", SourceLocation(rec.get("source", ""), 1))
                )

    # Action alignment: subscribed action's trigger KPIs should overlap with bracket KPIs
    for uc_id in sorted(uc_ids_active):
        rec = brackets.get(uc_id)
        if not rec:
            continue
        raw = rec.get("raw", {})
        ob = (raw.get("orchestration") or raw.get("ontology_bracket", {})) if isinstance(raw, dict) else {}
        if not isinstance(ob, dict):
            continue
        bracket_kpis: Set[str] = set()
        sk = ob.get("strategic_kpi_id")
        if isinstance(sk, str) and sk.strip():
            bracket_kpis.add(sk.strip())
        infl = ob.get("influencing_kpi_ids")
        if isinstance(infl, list):
            for kid in infl:
                if isinstance(kid, str) and kid.strip():
                    bracket_kpis.add(kid.strip())
        acts = ob.get("action_code_ids") or []
        for aid in acts:
            if not isinstance(aid, str) or not aid.strip():
                continue
            arec = actions.get(aid.strip())
            if not arec:
                continue
            action_kpis = _extract_kpis_from_action(arec.get("raw", {}) or {})
            overlap = bracket_kpis & action_kpis
            if bracket_kpis and action_kpis and not overlap:
                issues.append(
                    Issue(
                        "WARN",
                        "action_alignment.no_overlap",
                        f"UseCase '{uc_id}' subscribes to action '{aid.strip()}' but action trigger KPIs ({sorted(action_kpis)}) have no overlap with bracket KPIs ({sorted(bracket_kpis)}); possible misalignment.",
                        SourceLocation(rec.get("source", ""), 1),
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
                    "source": frec.get("business"),
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
    # Merge failed contracts from contract_validation.json (written by check_validate_data_contracts.ps1)
    failed_contracts |= _load_contract_validation_failed(repo_root)

    # Contract -> KPI linkage (via UseCase_Bracket KPIs)
    contract_to_kpis: Dict[str, Set[str]] = {}
    if usecase_domain_contract:
        for uc_id in brackets.keys():
            contract = usecase_domain_contract.get(uc_id)
            if not contract:
                continue
            raw = brackets[uc_id].get("raw", {})
            ob = (raw.get("orchestration") or raw.get("ontology_bracket", {})) if isinstance(raw, dict) else {}
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
        linked_contracts_list = sorted([c for c, ks in contract_to_kpis.items() if kpi_id in ks])
        data_contract_risk: Optional[str] = None
        if kpi_id in linked_kpis and not linked_contracts_list:
            data_contract_risk = "high"
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
            "linked_domain_contracts": linked_contracts_list,
            "data_contract_risk": data_contract_risk,
            "causal_links": rec.causal_links,
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
        impact_valuation = raw.get("impact_valuation") if isinstance(raw, dict) else None
        execution_bridge = raw.get("execution_bridge") if isinstance(raw, dict) else None
        display_fields = _action_code_display_fields(raw if isinstance(raw, dict) else {}, gov_norm)
        registry_actions[aid] = {
            "id": aid,
            "name": raw.get("name") if isinstance(raw, dict) else None,
            "owner_domain": raw.get("owner_domain") if isinstance(raw, dict) else None,
            "governance": gov_norm,
            "impact_valuation": impact_valuation if isinstance(impact_valuation, dict) else None,
            "execution_bridge": execution_bridge if isinstance(execution_bridge, dict) else None,
            "source": {"file": arec.get("source")},
            "trigger_summary": display_fields.get("trigger_summary"),
            "owner_role": display_fields.get("owner_role"),
            "steps": display_fields.get("steps", []),
        }
        for w in gov_warnings:
            issues.append(Issue("WARN", "governance.action_normalization", f"Action '{aid}': {w}", SourceLocation(arec.get("source", ""), 1)))

    registry_usecases: Dict[str, Any] = {}
    for uc_id, brec in brackets.items():
        raw = brec.get("raw", {})
        src = brec.get("source", "")
        gov = raw.get("governance", {}) if isinstance(raw, dict) else {}
        ob = (raw.get("orchestration") or raw.get("ontology_bracket", {})) if isinstance(raw, dict) else {}
        docs = raw.get("documentation", {}) if isinstance(raw, dict) else {}
        registry_usecases[uc_id] = {
            "id": uc_id,
            "title": raw.get("title") or raw.get("name"),
            "domain": raw.get("domain"),
            "governance": gov,
            "orchestration": ob,
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
        ob = (raw.get("orchestration") or raw.get("ontology_bracket", {})) if isinstance(raw, dict) else {}
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
            edges.append({"type": "kpi_supported_by_domain_contract", "from": kpi_id, "to": contract, "evidence": {"derived_from": "usecase_bracket.overrides.data_contract_ref"}})

    # DisplayFolder conflict rule computation (strategic precedence across UCs)
    # Determine global strategic set: any KPI used as strategic in any active bracket.
    strategic_global: Set[str] = set()
    for uc_id in uc_ids_active:
        raw = brackets[uc_id]["raw"]
        ob = (raw.get("orchestration") or raw.get("ontology_bracket", {})) if isinstance(raw, dict) else {}
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

    # ---------------------------------------------------------------------
    # Value Map (Power BI frontend): causal links + valuation + impact paths
    # ---------------------------------------------------------------------
    causal_edges: List[Dict[str, Any]] = []
    for kpi_id, rec in kpis.items():
        cl = rec.causal_links
        if not isinstance(cl, dict):
            continue
        links = cl.get("links")
        if not isinstance(links, list):
            continue
        for link in links:
            if not isinstance(link, dict):
                continue
            src = link.get("influencing_kpi_id")
            if not isinstance(src, str) or not src.strip():
                continue
            causal_edges.append(
                {
                    "type": "kpi_causal_influence",
                    "from": src.strip(),
                    "to": kpi_id,
                    "effect": link.get("effect") if isinstance(link.get("effect"), dict) else None,
                    "formula": link.get("formula") if isinstance(link.get("formula"), dict) else None,
                    "applicability": link.get("applicability") if isinstance(link.get("applicability"), dict) else None,
                    "evidence": link.get("evidence") if isinstance(link.get("evidence"), dict) else None,
                    "source": {"file": rec.source, "line": rec.line},
                }
            )

    # Build inverse index: KPI -> UseCases that reference it (active brackets only)
    kpi_to_usecases: Dict[str, Set[str]] = {}
    for uc_id in sorted(uc_ids_active):
        urec = brackets.get(uc_id, {})
        raw = urec.get("raw", {})
        ob = (raw.get("orchestration") or raw.get("ontology_bracket", {})) if isinstance(raw, dict) else {}
        if not isinstance(ob, dict):
            continue
        sk = ob.get("strategic_kpi_id")
        if isinstance(sk, str) and sk.strip():
            kpi_to_usecases.setdefault(sk.strip(), set()).add(uc_id)
        infl = ob.get("influencing_kpi_ids")
        if isinstance(infl, list):
            for kid in infl:
                if isinstance(kid, str) and kid.strip():
                    kpi_to_usecases.setdefault(kid.strip(), set()).add(uc_id)

    # Impact paths: failed contract -> affected KPI -> affected use case -> strategic KPI -> subscribed actions -> valuation metadata
    impact_paths: List[Dict[str, Any]] = []
    for contract in sorted(failed_contracts):
        for kpi_id in sorted(contract_to_kpis.get(contract, set())):
            for uc_id in sorted(kpi_to_usecases.get(kpi_id, set())):
                urec = brackets.get(uc_id, {})
                raw = urec.get("raw", {})
                ob = (raw.get("orchestration") or raw.get("ontology_bracket", {})) if isinstance(raw, dict) else {}
                sk = ob.get("strategic_kpi_id") if isinstance(ob, dict) else None
                acts = ob.get("action_code_ids") if isinstance(ob, dict) else None
                action_ids = [a for a in acts if isinstance(a, str) and a.strip()] if isinstance(acts, list) else []
                valuations = []
                for aid in action_ids:
                    aobj = registry_actions.get(aid)
                    if isinstance(aobj, dict) and isinstance(aobj.get("impact_valuation"), dict):
                        valuations.append({"action_code_id": aid, "impact_valuation": aobj.get("impact_valuation")})
                impact_paths.append(
                    {
                        "data_contract": contract,
                        "kpi_id": kpi_id,
                        "use_case_id": uc_id,
                        "strategic_kpi_id": sk if isinstance(sk, str) else None,
                        "action_code_ids": action_ids,
                        "valuations": valuations,
                        "note": "Euro impact is computed in semantic model using facts; registry provides metadata and linkage only.",
                    }
                )

    value_map = {
        "meta": {
            "generated_at_utc": _utc_now_iso(),
            "registry_version": "0.1",
            "repo_root": repo_root.as_posix(),
            "failed_data_contracts": sorted(failed_contracts),
        },
        "nodes": {
            "use_cases": registry_usecases,
            "kpis": registry_kpis,
            "action_codes": registry_actions,
            "domain_contracts": {
                c: {"id": c, "status": ("failed" if c in failed_contracts else "ok")}
                for c in sorted(contract_to_kpis.keys())
            },
        },
        "edges": edges + causal_edges,
        "impact_paths": impact_paths,
        "formulas": {
            "note": "All formulas are metadata strings (standardized/latex) for UI; no execution in registry builder."
        },
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

    # Governance gaps: owner_role missing, steward_role missing, owner_role == steward_role
    governance_gaps: List[Dict[str, Any]] = []
    for kpi_id, rec in kpis.items():
        gov = rec.governance if hasattr(rec, "governance") else {}
        o = (gov.get("owner_role") or gov.get("business_owner") or gov.get("data_owner")) or ""
        s = (gov.get("steward_role") or gov.get("steward")) or ""
        if not o or not str(o).strip():
            governance_gaps.append({"type": "kpi", "id": kpi_id, "gap": "owner_role_missing", "source": rec.source})
        if not s or not str(s).strip():
            governance_gaps.append({"type": "kpi", "id": kpi_id, "gap": "steward_role_missing", "source": rec.source})
        if o and s and str(o).strip() == str(s).strip():
            governance_gaps.append({"type": "kpi", "id": kpi_id, "gap": "owner_equals_steward", "source": rec.source})
    for aid, arec in actions.items():
        raw = arec.get("raw", {}) or {}
        gov, _ = normalize_action_governance(raw if isinstance(raw, dict) else {})
        o = gov.get("owner_role") or ""
        s = gov.get("steward_role") or ""
        src = arec.get("source") or ""
        if not o or not str(o).strip():
            governance_gaps.append({"type": "action_code", "id": aid, "gap": "owner_role_missing", "source": src})
        if not s or not str(s).strip():
            governance_gaps.append({"type": "action_code", "id": aid, "gap": "steward_role_missing", "source": src})
        if o and s and str(o).strip() == str(s).strip():
            governance_gaps.append({"type": "action_code", "id": aid, "gap": "owner_equals_steward", "source": src})
    for uc_id, brec in brackets.items():
        raw = brec.get("raw", {}) or {}
        gov = raw.get("governance", {}) if isinstance(raw, dict) else {}
        if not isinstance(gov, dict):
            continue
        o = gov.get("owner_role") or ""
        s = gov.get("steward_role") or ""
        src = brec.get("source") or ""
        if not o or not str(o).strip():
            governance_gaps.append({"type": "use_case_bracket", "id": uc_id, "gap": "owner_role_missing", "source": src})
        if not s or not str(s).strip():
            governance_gaps.append({"type": "use_case_bracket", "id": uc_id, "gap": "steward_role_missing", "source": src})
        if o and s and str(o).strip() == str(s).strip():
            governance_gaps.append({"type": "use_case_bracket", "id": uc_id, "gap": "owner_equals_steward", "source": src})

    governance_gaps_path = out_dir / "governance_gaps.json"
    _write_json(governance_gaps_path, {"gaps": governance_gaps, "meta": {"generated_at_utc": _utc_now_iso()}})

    master_path = out_dir / "master_registry.json"
    orphans_path = out_dir / "orphans_report.json"
    value_map_path = out_dir / "value_map.json"
    _write_json(master_path, master_registry)
    _write_json(orphans_path, orphans_report)
    _write_json(value_map_path, value_map)

    # Generate UseCase_Inventory.md
    inventory_path = repo_root / "core" / "usecases" / "UseCase_Inventory.md"
    inventory_lines: List[str] = [
        "<!-- GENERATED FILE - DO NOT EDIT MANUALLY -->",
        "<!-- Source: tooling/ontology/registry_builder.py -->",
        "",
        "# Use Case Inventory",
        "",
        "| ID | Title | Domain | Strategic KPI | Influencing KPIs | Action Codes | Owner Role | Steward Role |",
        "|----|-------|--------|---------------|------------------|--------------|------------|--------------|",
    ]
    for uc_id in sorted(registry_usecases.keys()):
        urec = registry_usecases[uc_id]
        title = urec.get("title") or uc_id
        domain = urec.get("domain") or ""
        orch = urec.get("orchestration") or {}
        sk = orch.get("strategic_kpi_id", "") if isinstance(orch, dict) else ""
        infl = orch.get("influencing_kpi_ids", []) if isinstance(orch, dict) else []
        acts = orch.get("action_code_ids", []) if isinstance(orch, dict) else []
        gov = urec.get("governance") or {}
        owner = gov.get("owner_role", "") if isinstance(gov, dict) else ""
        steward = gov.get("steward_role", "") if isinstance(gov, dict) else ""
        infl_str = ", ".join(infl) if isinstance(infl, list) else ""
        acts_str = ", ".join(acts) if isinstance(acts, list) else ""
        inventory_lines.append(f"| {uc_id} | {title} | {domain} | {sk} | {infl_str} | {acts_str} | {owner} | {steward} |")
    inventory_lines.append("")
    inventory_path.write_text("\n".join(inventory_lines), encoding="utf-8")

    # Print actionable errors and warnings to stderr for CI visibility
    for iss in issues:
        if iss.severity in ("ERROR", "WARN"):
            print(iss.message, file=sys.stderr)
            print(file=sys.stderr)

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

