"""
Quality Scorer — rates generated output on multiple dimensions.

A QualityScore of 1.0 means perfect compliance; 0.0 means critical issues.
Scores are computed per-dimension and rolled up to an overall score.

Dimensions
----------
visual_coverage      Required visual slots all present (KPI_Cards, Smart_Narrative, …)
measure_completeness All bracket primary_kpi_ids have measures in the model
dax_completeness     No TODO/placeholder DAX expressions in generated measures
action_panel_quality ActionPanel text has trigger + steps (if action_panel enabled)
layout_compliance    3-30-300 template rules satisfied (2 pages, correct page types)
tmdl_cleanliness     No known TMDL anti-patterns in generated files

Usage
-----
    from tooling.generator_core.intelligence.scorer import QualityScorer

    scorer = QualityScorer()
    score = scorer.score(
        report_dir=Path("products/fabric/powerbi/dist/COM-001.Report"),
        bracket_path=Path("core/usecases/core/COM-001_.../UseCase_Bracket.yaml"),
        model_dir=Path("products/fabric/powerbi/dist/Commercial.SemanticModel"),
    )
    print(score.overall, score.dimensions)
    print(score.findings)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


# ---------------------------------------------------------------------------
# Score dataclass
# ---------------------------------------------------------------------------

@dataclass
class QualityScore:
    overall: float                          # 0.0–1.0
    dimensions: Dict[str, float] = field(default_factory=dict)
    findings: List[str] = field(default_factory=list)
    use_case_id: str = ""

    def grade(self) -> str:
        if self.overall >= 0.95:
            return "A"
        if self.overall >= 0.85:
            return "B"
        if self.overall >= 0.70:
            return "C"
        if self.overall >= 0.50:
            return "D"
        return "F"

    def summary(self) -> str:
        lines = [
            f"Quality Score: {self.overall:.2f} ({self.grade()}) — {self.use_case_id}",
        ]
        for dim, val in sorted(self.dimensions.items()):
            bar = "█" * round(val * 10) + "░" * (10 - round(val * 10))
            lines.append(f"  {dim:<28} {bar} {val:.2f}")
        if self.findings:
            lines.append("  Findings:")
            for f in self.findings:
                lines.append(f"    - {f}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "use_case_id": self.use_case_id,
            "overall": round(self.overall, 4),
            "grade": self.grade(),
            "dimensions": {k: round(v, 4) for k, v in self.dimensions.items()},
            "findings": self.findings,
        }


# ---------------------------------------------------------------------------
# Dimension weights
# ---------------------------------------------------------------------------

_WEIGHTS: Dict[str, float] = {
    "visual_coverage":      0.25,
    "measure_completeness": 0.25,
    "dax_completeness":     0.15,
    "action_panel_quality": 0.10,
    "layout_compliance":    0.15,
    "tmdl_cleanliness":     0.10,
}

_REQUIRED_OVERVIEW_VISUALS = {"KPI_Cards", "Main_1", "Slicer_Date"}
_REQUIRED_DETAIL_VISUALS   = {"Smart_Narrative", "Slicer_Pane"}


# ---------------------------------------------------------------------------
# Scorer
# ---------------------------------------------------------------------------

class QualityScorer:
    """
    Scores a generated use-case report + model.

    All path parameters are optional — missing paths skip the corresponding
    dimension (treated as 1.0 / neutral, not as failure).
    """

    def score(
        self,
        bracket_path: Path,
        report_dir: Optional[Path] = None,
        model_dir: Optional[Path] = None,
    ) -> QualityScore:
        bracket_path = Path(bracket_path)
        with open(bracket_path, encoding="utf-8") as fh:
            bracket = yaml.safe_load(fh) or {}
        use_case_id = bracket.get("id", bracket_path.parent.name)

        dimensions: Dict[str, float] = {}
        findings: List[str] = []

        # Visual coverage
        if report_dir and Path(report_dir).is_dir():
            score_vc, finds_vc = self._score_visual_coverage(Path(report_dir))
            dimensions["visual_coverage"] = score_vc
            findings.extend(finds_vc)
        else:
            dimensions["visual_coverage"] = 1.0

        # Measure completeness
        if model_dir and Path(model_dir).is_dir():
            score_mc, finds_mc = self._score_measure_completeness(bracket, Path(model_dir))
            dimensions["measure_completeness"] = score_mc
            findings.extend(finds_mc)

            score_dax, finds_dax = self._score_dax_completeness(Path(model_dir))
            dimensions["dax_completeness"] = score_dax
            findings.extend(finds_dax)

            score_tmdl, finds_tmdl = self._score_tmdl_cleanliness(Path(model_dir))
            dimensions["tmdl_cleanliness"] = score_tmdl
            findings.extend(finds_tmdl)
        else:
            dimensions["measure_completeness"] = 1.0
            dimensions["dax_completeness"] = 1.0
            dimensions["tmdl_cleanliness"] = 1.0

        # Action panel quality
        score_ap, finds_ap = self._score_action_panel(bracket, report_dir)
        dimensions["action_panel_quality"] = score_ap
        findings.extend(finds_ap)

        # Layout compliance
        if report_dir and Path(report_dir).is_dir():
            score_lc, finds_lc = self._score_layout_compliance(bracket, Path(report_dir))
            dimensions["layout_compliance"] = score_lc
            findings.extend(finds_lc)
        else:
            dimensions["layout_compliance"] = 1.0

        # Weighted roll-up
        overall = sum(
            dimensions.get(dim, 1.0) * weight
            for dim, weight in _WEIGHTS.items()
        )

        return QualityScore(
            overall=round(overall, 4),
            dimensions=dimensions,
            findings=findings,
            use_case_id=use_case_id,
        )

    # ------------------------------------------------------------------
    # Dimension scorers
    # ------------------------------------------------------------------

    def _score_visual_coverage(
        self, report_dir: Path
    ) -> tuple[float, List[str]]:
        findings: List[str] = []
        pages_dir = report_dir / "definition" / "pages"
        if not pages_dir.is_dir():
            return 0.0, ["No pages/ directory in report"]

        page_dirs = [d for d in pages_dir.iterdir() if d.is_dir()]
        overview_dirs = [d for d in page_dirs if "overview" in d.name.lower()]
        detail_dirs   = [d for d in page_dirs if "detail" in d.name.lower()]

        if not overview_dirs:
            findings.append("No Overview page found")
            return 0.0, findings
        if not detail_dirs:
            findings.append("No Detail page found")

        def visual_ids(page_dir: Path) -> set:
            v_dir = page_dir / "visuals"
            if not v_dir.is_dir():
                return set()
            return {d.name for d in v_dir.iterdir() if d.is_dir()}

        ov_visuals = visual_ids(overview_dirs[0])
        missing_ov = _REQUIRED_OVERVIEW_VISUALS - ov_visuals
        for m in missing_ov:
            findings.append(f"Overview missing visual: {m}")

        det_visuals = visual_ids(detail_dirs[0]) if detail_dirs else set()
        missing_det = _REQUIRED_DETAIL_VISUALS - det_visuals
        for m in missing_det:
            findings.append(f"Detail missing visual: {m}")

        total_required = len(_REQUIRED_OVERVIEW_VISUALS) + len(_REQUIRED_DETAIL_VISUALS)
        missing_total = len(missing_ov) + len(missing_det)
        score = max(0.0, 1.0 - missing_total / total_required)
        return score, findings

    def _score_measure_completeness(
        self, bracket: Dict, model_dir: Path
    ) -> tuple[float, List[str]]:
        findings: List[str] = []
        kpi_ids = bracket.get("primary_kpi_ids", [])
        if not kpi_ids:
            return 1.0, []

        tmdl_dir = model_dir / "definition" / "tables"
        if not tmdl_dir.is_dir():
            findings.append(f"Model tables directory not found: {tmdl_dir}")
            return 0.0, findings

        # Collect all measure names from .tmdl files
        measure_names: set = set()
        for tmdl in tmdl_dir.glob("*.tmdl"):
            content = tmdl.read_text(encoding="utf-8", errors="ignore")
            for m in re.finditer(r"^\s+measure '([^']+)'", content, re.MULTILINE):
                measure_names.add(m.group(1))
            for m in re.finditer(r"^\s+measure ([^\s'=]+) =", content, re.MULTILINE):
                measure_names.add(m.group(1))

        missing = 0
        for kpi_id in kpi_ids:
            # Check if any measure name contains the KPI ID fragment
            kpi_short = kpi_id.split(".")[-1].replace("_", " ")
            if not any(kpi_short.lower() in n.lower() for n in measure_names):
                findings.append(f"No measure found for KPI: {kpi_id}")
                missing += 1

        score = max(0.0, 1.0 - missing / len(kpi_ids))
        return score, findings

    def _score_dax_completeness(
        self, model_dir: Path
    ) -> tuple[float, List[str]]:
        findings: List[str] = []
        tmdl_dir = model_dir / "definition" / "tables" / "_Measures.tmdl"
        if not tmdl_dir.is_file():
            return 1.0, []

        content = tmdl_dir.read_text(encoding="utf-8", errors="ignore")
        measures = re.findall(r"measure '([^']+)' = (.+)", content)
        total = len(measures)
        if total == 0:
            return 1.0, []

        placeholder_count = sum(
            1 for _, dax in measures
            if "TODO" in dax or "// TODO" in dax.upper() or dax.strip() == ""
        )
        if placeholder_count:
            findings.append(f"{placeholder_count}/{total} measures have placeholder DAX")
        score = max(0.0, 1.0 - placeholder_count / total)
        return score, findings

    def _score_tmdl_cleanliness(
        self, model_dir: Path
    ) -> tuple[float, List[str]]:
        findings: List[str] = []
        tmdl_files = list((model_dir / "definition").rglob("*.tmdl"))
        if not tmdl_files:
            return 1.0, []

        violations = 0
        total_checks = 0

        for tmdl in tmdl_files:
            content = tmdl.read_text(encoding="utf-8", errors="ignore")
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                # Check for spaces-only indentation
                if line and line[0] == " " and line.strip():
                    violations += 1
                    if violations <= 3:
                        findings.append(f"{tmdl.name}:{i} — space indentation (should be tab)")
                    total_checks += 1

                # Check for := in DAX
                if ":=" in line and "measure" in line.lower():
                    violations += 1
                    findings.append(f"{tmdl.name}:{i} — ':=' found (should be '=')")
                    total_checks += 1

                # Check for description: property
                if re.match(r"\s+description:", line) and "///" not in lines[max(0, i-2)]:
                    violations += 1
                    findings.append(f"{tmdl.name}:{i} — 'description:' property (use '/// Purpose: ...')")
                    total_checks += 1

        if total_checks == 0:
            return 1.0, findings
        score = max(0.0, 1.0 - violations / max(total_checks, 1))
        return round(score, 3), findings

    def _score_action_panel(
        self, bracket: Dict, report_dir: Optional[Path]
    ) -> tuple[float, List[str]]:
        findings: List[str] = []
        ux = bracket.get("ux_layout_rules", {})
        page2 = ux.get("page_2_execution", {}) if isinstance(ux, dict) else {}
        comp_300s = page2.get("component_300s", {}) if isinstance(page2, dict) else {}
        ap_enabled = (
            comp_300s.get("action_panel", False)
            if isinstance(comp_300s, dict)
            else False
        )

        if not ap_enabled:
            return 1.0, []  # Not applicable

        ac_ids = bracket.get("orchestration", {}).get("action_code_ids", [])
        if not ac_ids:
            findings.append("action_panel enabled but no action_code_ids declared")
            return 0.5, findings

        if not report_dir or not Path(report_dir).is_dir():
            return 1.0, []

        # Find ActionPanel visual.json
        ap_files = list(Path(report_dir).rglob("ActionPanel/visual.json"))
        if not ap_files:
            findings.append("ActionPanel visual.json not found in report")
            return 0.0, findings

        # Check that text content is non-trivial
        import json as _json
        for ap_file in ap_files:
            try:
                data = _json.loads(ap_file.read_text(encoding="utf-8"))
                text = str(data)
                if "TODO" in text or len(text) < 100:
                    findings.append("ActionPanel appears to have placeholder content")
                    return 0.5, findings
            except Exception:
                findings.append("ActionPanel visual.json is invalid JSON")
                return 0.0, findings

        return 1.0, findings

    def _score_layout_compliance(
        self, bracket: Dict, report_dir: Path
    ) -> tuple[float, List[str]]:
        findings: List[str] = []
        pages_dir = report_dir / "definition" / "pages"
        if not pages_dir.is_dir():
            return 0.0, ["No pages/ directory"]

        page_dirs = [d for d in pages_dir.iterdir() if d.is_dir() and d.name != "pages.json"]
        non_json = [d for d in page_dirs if not d.suffix]
        if len(non_json) != 2:
            findings.append(f"Expected 2 page directories, found {len(non_json)}")
            return 0.5, findings

        # Check active page is Overview (not Detail)
        pages_json_path = pages_dir / "pages.json"
        if pages_json_path.is_file():
            import json as _json
            try:
                pj = _json.loads(pages_json_path.read_text(encoding="utf-8"))
                active = pj.get("activePageName", "")
                if active and "detail" in active.lower():
                    findings.append(f"activePageName is '{active}' — should be Overview")
                    return 0.8, findings
            except Exception:
                pass

        return 1.0, findings
