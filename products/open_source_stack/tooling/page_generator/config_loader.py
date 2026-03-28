"""
Config Loader

Loads IR, UseCase Bracket, governance files, and theme configuration.
Mirrors the Fabric PageScaffoldGenerator's ConfigLoader but reads
from ir_v1.json instead of core/ directly.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

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

    def get_use_case_from_ir(self, ir: Dict[str, Any], use_case_id: str) -> Optional[Dict[str, Any]]:
        """Extract a use case node from the IR by ID."""
        for node in ir.get("nodes", []):
            if node.get("id") == use_case_id and node.get("type") == "use_case":
                return node
        return None

    def get_kpis_for_use_case(self, ir: Dict[str, Any], use_case_id: str) -> List[Dict[str, Any]]:
        """Return all KPI nodes linked to a use case via edges."""
        linked_kpi_ids = set()
        for edge in ir.get("edges", []):
            if edge.get("source") == use_case_id and edge.get("target_type") == "kpi":
                linked_kpi_ids.add(edge["target"])
            elif edge.get("target") == use_case_id and edge.get("source_type") == "kpi":
                linked_kpi_ids.add(edge["source"])
        return [n for n in ir.get("nodes", []) if n.get("id") in linked_kpi_ids]

    # -- Utilities ---------------------------------------------------------

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        if yaml is None:
            raise ImportError("PyYAML is required: pip install pyyaml")
        if not path.exists():
            return {}
        return yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
