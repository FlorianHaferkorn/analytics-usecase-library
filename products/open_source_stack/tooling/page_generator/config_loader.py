"""
Config Loader

Loads IR, UseCase Bracket, governance files, and theme configuration.
Mirrors the Fabric PageScaffoldGenerator's ConfigLoader but reads
from ir_v1.json instead of core/ directly.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


class ConfigLoader:
    """Load all configuration required by the Evidence page generator."""

    def __init__(self, repo_root: Optional[Path] = None) -> None:
        self.repo_root = repo_root or Path(__file__).resolve().parents[4]
        self._ir: Optional[Dict[str, Any]] = None

    # -- IR ----------------------------------------------------------------

    def load_ir(self, ir_path: Optional[Path] = None) -> Dict[str, Any]:
        """Load the Intermediate Representation (ir_v1.json)."""
        if self._ir is not None:
            return self._ir
        path = ir_path or self.repo_root / "tooling" / "ir" / "out" / "ir_v1.json"
        self._ir = json.loads(path.read_text(encoding="utf-8-sig"))
        return self._ir

    # -- UseCase Bracket ---------------------------------------------------

    def load_bracket(self, use_case_id: str) -> Dict[str, Any]:
        """Load UseCase_Bracket.yaml for a given use case."""
        if yaml is None:
            raise ImportError("PyYAML is required: pip install pyyaml")
        # Search across core/usecases/{core,extended,industry}
        for category in ("core", "extended", "industry"):
            base = self.repo_root / "core" / "usecases" / category
            if not base.is_dir():
                continue
            for uc_dir in sorted(base.iterdir()):
                if uc_dir.is_dir() and uc_dir.name.startswith(use_case_id):
                    bracket_file = uc_dir / "UseCase_Bracket.yaml"
                    if bracket_file.exists():
                        return yaml.safe_load(bracket_file.read_text(encoding="utf-8-sig"))
        raise FileNotFoundError(f"UseCase_Bracket.yaml not found for {use_case_id}")

    # -- Governance --------------------------------------------------------

    def load_visual_slot_mapping(self) -> Dict[str, Any]:
        path = self.repo_root / "core" / "templates" / "page_templates" / "governance" / "Visual_to_Slot_Mapping.yaml"
        return self._load_yaml(path)

    def load_layout_grid(self) -> Dict[str, Any]:
        path = self.repo_root / "core" / "templates" / "page_templates" / "governance" / "Layout_Grid_System.yaml"
        return self._load_yaml(path)

    def load_color_semantics(self) -> Dict[str, Any]:
        path = self.repo_root / "core" / "templates" / "page_templates" / "governance" / "Color_Semantics_Formatting.yaml"
        return self._load_yaml(path)

    # -- Theme -------------------------------------------------------------

    def load_theme_config(self, showcase: str = "aurora_group") -> Dict[str, Any]:
        path = self.repo_root / "showcases" / showcase / "theme_config.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8-sig"))

    # -- IR helpers --------------------------------------------------------
    # IR schema (from build_ir.py):
    #   ir.objects.use_cases  → {uc_id: {id, title, domain, orchestration: {strategic_kpi_id, influencing_kpi_ids, ...}}}
    #   ir.objects.kpis       → {kpi_id: {id, kpi_role, governance, ...}}
    #   ir.measure_spec       → {kpi_id: {dax_expression, formatString, ...}}  (optional, from --kpi-catalog)

    def get_use_case_from_ir(self, ir: Dict[str, Any], use_case_id: str) -> Optional[Dict[str, Any]]:
        """Extract a use case from the IR objects map."""
        objects = ir.get("objects", {})
        return objects.get("use_cases", {}).get(use_case_id)

    def get_kpis_for_use_case(self, ir: Dict[str, Any], use_case_id: str) -> List[Dict[str, Any]]:
        """Return all KPI dicts linked to a use case via orchestration fields."""
        uc = self.get_use_case_from_ir(ir, use_case_id)
        if not uc:
            return []
        orch = uc.get("orchestration", {})
        kpi_ids: List[str] = []
        strategic = orch.get("strategic_kpi_id")
        if strategic:
            kpi_ids.append(strategic)
        kpi_ids.extend(orch.get("influencing_kpi_ids", []))
        kpi_ids.extend(orch.get("supporting_kpi_ids", []))

        all_kpis = ir.get("objects", {}).get("kpis", {})
        measure_specs = ir.get("measure_spec", {})
        expanded_ids = self._expand_kpi_dependencies(kpi_ids, measure_specs)
        result = []
        for kpi_id in expanded_ids:
            kpi = all_kpis.get(kpi_id)
            if kpi:
                # Attach measure_spec from IR root if available
                enriched = dict(kpi)
                if kpi_id in measure_specs:
                    enriched["measure_spec"] = measure_specs[kpi_id]
                result.append(enriched)
        return result

    def _expand_kpi_dependencies(
        self,
        kpi_ids: List[str],
        measure_specs: Dict[str, Any],
    ) -> List[str]:
        ordered: List[str] = []
        seen: Set[str] = set()

        def add_with_dependencies(kpi_id: str) -> None:
            if not isinstance(kpi_id, str) or not kpi_id or kpi_id in seen:
                return
            spec = measure_specs.get(kpi_id, {})
            dependencies = spec.get("depends_on_measures", []) if isinstance(spec, dict) else []
            if isinstance(dependencies, list):
                for dep in dependencies:
                    add_with_dependencies(dep)
            seen.add(kpi_id)
            ordered.append(kpi_id)

        for kpi_id in kpi_ids:
            add_with_dependencies(kpi_id)

        return ordered

    def get_use_case_title(self, ir: Dict[str, Any], use_case_id: str) -> str:
        """Get the use case title (IR uses 'title', not 'label')."""
        uc = self.get_use_case_from_ir(ir, use_case_id)
        if uc:
            return uc.get("title") or use_case_id
        return use_case_id

    # -- Utilities ---------------------------------------------------------

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        if yaml is None:
            raise ImportError("PyYAML is required: pip install pyyaml")
        if not path.exists():
            return {}
        return yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
