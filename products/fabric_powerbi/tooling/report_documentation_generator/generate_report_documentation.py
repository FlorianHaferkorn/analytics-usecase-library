#!/usr/bin/env python3
"""
Generate report documentation (Markdown) from a PBIP report and use case factsheets.

Usage:
  python generate_report_documentation.py --report path/to/Report [--use-case COM-001] [--output path/to/Report_Documentation.md]
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Repo root: from this file go up to tools -> microsoft_fabric_powerbi -> implementations -> repo
_SCRIPT_DIR = Path(__file__).resolve().parent
_TOOLS_DIR = _SCRIPT_DIR.parent
_REPO_ROOT = _TOOLS_DIR.parent.parent.parent


def _find_repo_root() -> Path:
    """Return repo root (directory containing core/usecases)."""
    p = _TOOLS_DIR
    for _ in range(5):
        if (p / "core" / "usecases").exists():
            return p
        p = p.parent
    return _REPO_ROOT


def _resolve_business_factsheet_path(repo_root: Path, use_case_id: str) -> Optional[Path]:
    core = repo_root / "core" / "usecases" / "core"
    if core.exists():
        for p in core.iterdir():
            if p.is_dir() and p.name.startswith(f"{use_case_id}_"):
                f = p / "Business_Factsheet.md"
                if f.exists():
                    return f
    flat = core / f"{use_case_id}_Business_Factsheet.md"
    if flat.exists():
        return flat
    return None


def _resolve_use_case_bracket_path(repo_root: Path, use_case_id: str) -> Optional[Path]:
    core = repo_root / "core" / "usecases" / "core"
    if core.exists():
        for p in core.iterdir():
            if p.is_dir() and p.name.startswith(f"{use_case_id}_"):
                f = p / "UseCase_Bracket.yaml"
                if f.exists():
                    return f
    return None


def _load_use_case_bracket(repo_root: Path, use_case_id: str) -> Dict[str, Any]:
    """Load UseCase_Bracket.yaml (SSOT) for UX + action codes + KPI IDs."""
    p = _resolve_use_case_bracket_path(repo_root, use_case_id)
    if not p:
        return {}
    import yaml
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def _extract_frontmatter(path: Path) -> Dict[str, Any]:
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    import yaml
    return yaml.safe_load(parts[1]) or {}


def _extract_section_lines(content: str, heading: str) -> List[str]:
    """Return lines under a ## heading until the next ## or end."""
    marker = f"## {heading}"
    if marker not in content:
        return []
    after = content.split(marker, 1)[1]
    lines = []
    for line in after.split("\n"):
        s = line.strip()
        if s.startswith("##"):
            break
        if s:
            lines.append(s)
    return lines


def _extract_purpose_one_line(content: str) -> str:
    """Get first sentence of Purpose from Business Summary."""
    if "**Purpose:**" not in content:
        return ""
    after = content.split("**Purpose:**", 1)[1]
    first_line = after.split("\n")[0].strip()
    # One sentence
    if "." in first_line:
        return first_line.split(".")[0].strip() + "."
    return first_line


def _extract_core_questions(content: str) -> List[str]:
    """Bullet list under '## 2. Core Business Questions'."""
    lines = _extract_section_lines(content, "2. Core Business Questions")
    questions = []
    current = []
    for line in lines:
        if line.startswith("- ") and len(line) > 2:
            if current:
                questions.append(" ".join(current))
            current = [line[2:].strip()]
        elif current and line and not line.startswith("-"):
            current.append(line)
        elif line.startswith("- "):
            if current:
                questions.append(" ".join(current))
            current = [line[2:].strip()]
    if current:
        questions.append(" ".join(current))
    return questions


def _extract_required_kpis(content: str) -> List[Dict[str, str]]:
    """Parse required_kpis from YAML block in section 3."""
    if "## 3. Required KPIs" not in content:
        return []
    after = content.split("## 3. Required KPIs", 1)[1]
    if "```yaml" not in after:
        return []
    block = after.split("```yaml", 1)[1].split("```", 1)[0]
    import yaml
    try:
        data = yaml.safe_load(block)
        kpis = data.get("required_kpis") or []
        return [{"id": k.get("id", ""), "name": k.get("name", "")} for k in kpis if isinstance(k, dict)]
    except Exception:
        return []


def _extract_action_codes_summary(content: str) -> List[str]:
    """Action code IDs from section 4 if present."""
    if "## 4. Action Codes" not in content:
        return []
    after = content.split("## 4. Action Codes", 1)[1]
    ids = []
    for line in after.split("\n"):
        s = line.strip()
        if s.startswith("- ") and ("C-" in s or "F-" in s or "O-" in s or "S-" in s or "X-" in s):
            # e.g. "- C-M2.1" or "- id: C-M2.1"
            m = re.search(r"[A-Z]+-[A-Z0-9.]+", s)
            if m:
                ids.append(m.group(0))
    return ids[:20]


def _infer_use_case_from_report(report_path: Path) -> Optional[str]:
    """Infer use case ID from report path (e.g. COM-001.Report) or page names."""
    name = report_path.name
    if name.endswith(".Report"):
        name = name[:-7]
    if re.match(r"^[A-Z]+-\d+", name):
        return name
    pages_dir = report_path / "definition" / "pages"
    if not pages_dir.exists():
        return None
    for d in pages_dir.iterdir():
        if d.is_dir() and d.name.startswith("Page_") and "_" in d.name:
            # Page_COM001_Overview -> COM-001
            parts = d.name.split("_")
            if len(parts) >= 2 and re.match(r"^[A-Z]+-\d+", parts[1]):
                return parts[1]
    return None


def load_pbip_structure(report_path: Path) -> Dict[str, Any]:
    """Load report.json, pages order, and per-page/visual structure."""
    definition = report_path / "definition"
    if not (definition / "report.json").exists():
        return {}
    report = json.loads((definition / "report.json").read_text(encoding="utf-8"))
    pages_meta_path = definition / "pages" / "pages.json"
    page_order = []
    if pages_meta_path.exists():
        pages_meta = json.loads(pages_meta_path.read_text(encoding="utf-8"))
        page_order = pages_meta.get("pageOrder") or []
    pages_dir = definition / "pages"
    pages = []
    for page_name in page_order:
        page_dir = pages_dir / page_name
        if not page_dir.is_dir():
            continue
        page_json = page_dir / "page.json"
        if not page_json.exists():
            continue
        page_data = json.loads(page_json.read_text(encoding="utf-8"))
        visuals = []
        visuals_dir = page_dir / "visuals"
        if visuals_dir.exists():
            for v_dir in sorted(visuals_dir.iterdir()):
                if v_dir.is_dir():
                    v_json = v_dir / "visual.json"
                    if v_json.exists():
                        v_data = json.loads(v_json.read_text(encoding="utf-8"))
                        v_type = (v_data.get("visual") or {}).get("visualType") or "unknown"
                        visuals.append({"name": v_dir.name, "visualType": v_type})
        pages.append({
            "name": page_data.get("name", page_name),
            "displayName": page_data.get("displayName", page_name),
            "visuals": visuals,
        })
    theme_name = ""
    if report.get("themeCollection", {}).get("baseTheme"):
        theme_name = report["themeCollection"]["baseTheme"].get("name", "")
    return {
        "theme": theme_name,
        "report": report,
        "pages": pages,
    }


def load_page_template_mapping(repo_root: Path, use_case_id: str) -> Dict[str, Any]:
    """
    Page layout is taken from UseCase_Bracket.yaml (SSOT). This returns a derived page list.
    Legacy (Lean 1): UseCase_PageTemplate_Map.yaml.
    """
    bracket = _load_use_case_bracket(repo_root, use_case_id)
    ux = (bracket.get("ux_layout_rules") or {}) if isinstance(bracket, dict) else {}
    if not isinstance(ux, dict):
        return {}
    p1 = ux.get("page_1_summary") or {}
    p2 = ux.get("page_2_execution") or {}
    c300 = (p2.get("component_300s") or {}) if isinstance(p2, dict) else {}
    has_action_panel = bool(c300.get("action_panel", False)) if isinstance(c300, dict) else False
    return {
        "pages": [
            {"name": "overview", "layer": [3, 30], "template": "T2"},
            {"name": "detail", "layer": [300], "template": ("T4" if has_action_panel else "T2")},
        ]
    }


def build_markdown(
    report_path: Path,
    use_case_id: str,
    repo_root: Path,
    pbip: Dict[str, Any],
) -> str:
    """Build full report documentation Markdown."""
    factsheet_path = _resolve_business_factsheet_path(repo_root, use_case_id)
    content = factsheet_path.read_text(encoding="utf-8") if factsheet_path else ""
    fm = _extract_frontmatter(factsheet_path) if factsheet_path else {}
    page_templates = load_page_template_mapping(repo_root, use_case_id)
    template_pages = (page_templates.get("pages") or [])
    bracket = _load_use_case_bracket(repo_root, use_case_id)
    orch = (bracket.get("orchestration") or {}) if isinstance(bracket, dict) else {}
    action_codes = orch.get("action_code_ids") if isinstance(orch, dict) else []
    strategic_kpi = orch.get("strategic_kpi_id") if isinstance(orch, dict) else ""

    title = fm.get("id", use_case_id)
    domain = ""
    owner = ""
    for line in content.split("\n"):
        if "**Domain:**" in line:
            domain = line.split("**Domain:**", 1)[1].strip()
        if "**Business Owner:**" in line:
            owner = line.split("**Business Owner:**", 1)[1].strip()
            break

    from datetime import datetime
    date_str = datetime.now().strftime("%Y-%m-%d")

    md = []
    md.append(f"# Report Documentation: {title}")
    md.append("")
    md.append(f"**Use Case:** {title}  ")
    md.append(f"**Domain:** {domain}  ")
    md.append(f"**Report Owner:** {owner}  ")
    md.append(f"**Last Updated:** {date_str}  ")
    md.append(f"**Version:** 1.0  ")
    md.append(f"**Theme:** {pbip.get('theme') or 'Not set'}  ")
    md.append("")
    md.append("**Purpose:**  ")
    md.append(_extract_purpose_one_line(content) or "(From Business Factsheet.)")
    md.append("")
    md.append("**Target Audience:**  ")
    md.append("Management / Tactical (from Business Factsheet)")
    md.append("")
    md.append("**Usage Rhythm:**  ")
    md.append("Weekly / Monthly (from Business Factsheet)")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## Report Overview")
    md.append("")
    md.append("### Business Questions Answered")
    md.append("")
    for q in _extract_core_questions(content):
        md.append(f"- {q}")
    if not _extract_core_questions(content):
        md.append("- (See Business Factsheet section 2.)")
    md.append("")
    md.append("### Strategic Alignment")
    md.append("")
    md.append("**Strategic KPI:**  ")
    if isinstance(strategic_kpi, str) and strategic_kpi.strip():
        md.append(f"- `{strategic_kpi.strip()}`")
    else:
        md.append("- (See UseCase_Bracket.yaml)")
    md.append("")
    md.append("**Decision Type:** Tactical / Diagnostic (from use case.)")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## Page Documentation")
    md.append("")

    for i, page in enumerate(pbip.get("pages") or []):
        display_name = page.get("displayName", page.get("name", ""))
        name = page.get("name", "")
        # Short display for heading
        short_name = display_name[:80] + "..." if len(display_name) > 80 else display_name
        md.append(f"### Page: {short_name}")
        md.append("")
        # Map page to template (overview vs detail)
        page_type = "T2"
        layer = "3, 30"
        if "detail" in name.lower() or "Detail" in name:
            page_type = "T2"
            layer = "300"
            if i < len(template_pages):
                layer = ", ".join(str(x) for x in (template_pages[1].get("layer") or [300]))
        elif i < len(template_pages):
            pt = template_pages[i]
            page_type = pt.get("template", "T2")
            layer = ", ".join(str(x) for x in (pt.get("layer") or [3, 30]))
        md.append(f"**Page Type:** {page_type}  ")
        md.append(f"**Layer:** {layer}  ")
        md.append("")
        md.append("#### Visuals")
        md.append("")
        md.append("| Visual | Type | Slot (from template) |")
        md.append("|--------|------|----------------------|")
        for v in page.get("visuals") or []:
            slot = v.get("name", "").replace("_", " ")
            md.append(f"| {v.get('name', '')} | {v.get('visualType', '')} | {slot} |")
        md.append("")
        md.append("*(Measures to be bound from semantic model; scaffold only.)*  ")
        md.append("")
    md.append("---")
    md.append("")
    md.append("## Traceability")
    md.append("")
    md.append("- **Use case:** `core/usecases/core/` (`Business_Factsheet.md` + `UseCase_Bracket.yaml`)")
    md.append("- **KPI catalog:** `core/kpi_catalog/`")
    md.append("- **Action codes:** `core/action_codes/`")
    md.append("- **Page templates:** `core/templates/page_templates/`")
    if isinstance(action_codes, list) and action_codes:
        md.append("")
        md.append("**Action codes referenced:** " + ", ".join([str(x) for x in action_codes if isinstance(x, str)]))
    md.append("")
    return "\n".join(md)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate report documentation from PBIP and factsheets")
    parser.add_argument("--report", type=Path, required=True, help="Path to .Report folder (PBIP)")
    parser.add_argument("--use-case", type=str, default=None, help="Use case ID (e.g. COM-001); inferred from report if omitted")
    parser.add_argument("--output", type=Path, default=None, help="Output Markdown path; default: reporting/Report_Documentation_<id>.md next to report")
    parser.add_argument("--repo-root", type=Path, default=None, help="Repository root (auto-detected if omitted)")
    args = parser.parse_args()

    repo_root = args.repo_root or _find_repo_root()
    report_path = args.report.resolve()
    if not (report_path / "definition" / "report.json").exists():
        print(f"Error: Not a PBIP report (missing definition/report.json): {report_path}", file=sys.stderr)
        sys.exit(1)

    use_case_id = args.use_case or _infer_use_case_from_report(report_path)
    if not use_case_id:
        print("Error: Could not infer use case ID; specify --use-case", file=sys.stderr)
        sys.exit(1)

    pbip = load_pbip_structure(report_path)
    if not pbip:
        print("Error: Could not load PBIP structure", file=sys.stderr)
        sys.exit(1)

    md = build_markdown(report_path, use_case_id, repo_root, pbip)

    if args.output:
        out = args.output.resolve()
    else:
        # Default: same parent as report, in a 'reporting' or 'documentation' folder, or next to report
        parent = report_path.parent
        if parent.name == "reports":
            reporting = parent.parent / "reporting"
            reporting.mkdir(parents=True, exist_ok=True)
            out = reporting / f"Report_Documentation_{use_case_id}.md"
        else:
            out = parent / f"Report_Documentation_{use_case_id}.md"

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    print(f"Written: {out}")


if __name__ == "__main__":
    main()
