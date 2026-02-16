"""
Configuration Loader

Loads governance YAML files and use case configurations.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import os


class ConfigLoader:
    """Loads configuration files for scaffold generation."""
    
    def __init__(self, repo_root: Optional[Path] = None):
        """
        Initialize config loader.
        
        Args:
            repo_root: Root path of repository. If None, auto-detect from current file.
        """
        if repo_root is None:
            # Auto-detect repo root (go up from tools/page_scaffold_generator)
            current_file = Path(__file__).resolve()
            repo_root = current_file.parent.parent.parent.parent.parent
        
        self.repo_root = Path(repo_root)
        # Lean 2.0: Bracket is SSOT for UX config; mapping file removed.
        # Canonical paths are under core/.
        self.page_templates_root = self.repo_root / "core" / "templates" / "page_templates"
        self.governance_root = self.page_templates_root / "governance"
        self.usecases_root = self.repo_root / "core" / "usecases"
    
    def _resolve_use_case_dir(self, use_case_id: str) -> Optional[Path]:
        """Resolve core use case directory: core/usecases/core/<ID>_*/."""
        core = self.usecases_root / "core"
        if not core.exists():
            return None
        for p in core.iterdir():
            if p.is_dir() and p.name.startswith(f"{use_case_id}_"):
                return p
        return None

    def load_use_case_bracket(self, use_case_id: str) -> Dict[str, Any]:
        """Load UseCase_Bracket.yaml for a given use case."""
        uc_dir = self._resolve_use_case_dir(use_case_id)
        if not uc_dir:
            raise FileNotFoundError(f"Use case directory not found for {use_case_id} under {self.usecases_root / 'core'}")
        bracket_file = uc_dir / "UseCase_Bracket.yaml"
        if not bracket_file.exists():
            raise FileNotFoundError(f"UseCase_Bracket.yaml not found: {bracket_file}")
        with open(bracket_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    
    def load_visual_slot_mapping(self) -> Dict[str, Any]:
        """Load Visual_to_Slot_Mapping.yaml (or return hardcoded mapping if file is markdown)."""
        mapping_file = self.governance_root / "Visual_to_Slot_Mapping.yaml"
        if not mapping_file.exists():
            raise FileNotFoundError(f"Visual slot mapping not found: {mapping_file}")
        
        # Try to load as YAML first
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Check if it's markdown (starts with #)
                if content.strip().startswith('#'):
                    # Return hardcoded mapping based on documentation
                    return self._get_hardcoded_visual_slot_mapping()
                return yaml.safe_load(content)
        except Exception:
            # If YAML parsing fails, return hardcoded mapping
            return self._get_hardcoded_visual_slot_mapping()
    
    def _get_hardcoded_visual_slot_mapping(self) -> Dict[str, Any]:
        """Return hardcoded visual-to-slot mapping based on governance documentation."""
        return {
            "kpi_summary": {"visual_type": "cardVisual", "templates": ["T1", "T2", "T3", "T4"]},
            "trend": {"visual_type": "lineChart", "templates": ["T1", "T2", "T3"]},
            "variance": {"visual_type": "waterfallChart", "templates": ["T1", "T2"]},
            "ranking": {"visual_type": "clusteredBarChart", "templates": ["T1", "T2", "T3"]},
            "mix": {"visual_type": "hundredPercentStackedBarChart", "templates": ["T1", "T2"]},
            "exceptions": {"visual_type": "tableEx", "templates": ["T3"]},
            "prescriptive": {"visual_type": "tableEx", "templates": ["T4"]},
            "root_cause": {"visual_type": "scatterChart", "templates": ["T3", "T4"]},
            "funnel": {"visual_type": "funnelChart", "templates": ["T2"]},
            "detail_matrix": {"visual_type": "tableEx", "templates": ["T1", "T2", "T3", "T4"]}
        }
    
    def load_layout_grid(self) -> Dict[str, Any]:
        """Load Layout_Grid_System.yaml (or return hardcoded values if file is markdown)."""
        layout_file = self.governance_root / "Layout_Grid_System.yaml"
        if not layout_file.exists():
            raise FileNotFoundError(f"Layout grid not found: {layout_file}")
        
        # Try to load as YAML first
        try:
            with open(layout_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if content.strip().startswith('#'):
                    return {}  # Return empty dict, layout calculator uses hardcoded values
                return yaml.safe_load(content)
        except Exception:
            return {}  # Return empty dict, layout calculator uses hardcoded values
    
    def load_color_semantics(self) -> Dict[str, Any]:
        """Load Color_Semantics_Formatting.yaml (or return empty dict if file is markdown)."""
        color_file = self.governance_root / "Color_Semantics_Formatting.yaml"
        if not color_file.exists():
            raise FileNotFoundError(f"Color semantics not found: {color_file}")
        
        # Try to load as YAML first
        try:
            with open(color_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if content.strip().startswith('#'):
                    return {}  # Return empty dict, formatting uses theme roles
                return yaml.safe_load(content)
        except Exception:
            return {}  # Return empty dict, formatting uses theme roles
    
    def load_use_case_factsheet(self, use_case_id: str) -> Optional[Dict[str, Any]]:
        """
        Load Business Factsheet for use case to get display name.
        
        Args:
            use_case_id: Use case ID (e.g., "COM-001")
        
        Returns:
            Factsheet content or None if not found
        """
        # Try core use cases first
        factsheet_file = self.usecases_root / "core" / f"{use_case_id}_Business_Factsheet.md"
        
        if not factsheet_file.exists():
            # Try other locations
            factsheet_file = self.usecases_root / f"{use_case_id}_Business_Factsheet.md"
        
        if not factsheet_file.exists():
            return None
        
        # Read frontmatter (YAML between --- markers)
        with open(factsheet_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                return frontmatter
        
        return None

    def _resolve_business_factsheet_path(self, use_case_id: str) -> Optional[Path]:
        """Resolve path to Business Factsheet: core/{id}_Name/Business_Factsheet.md or core/{id}_Business_Factsheet.md."""
        core = self.usecases_root / "core"
        # Folder per use case: COM-001_Sales_Performance/Business_Factsheet.md
        if core.exists():
            for p in core.iterdir():
                if p.is_dir() and p.name.startswith(f"{use_case_id}_"):
                    f = p / "Business_Factsheet.md"
                    if f.exists():
                        return f
        # Flat file
        flat = core / f"{use_case_id}_Business_Factsheet.md"
        if flat.exists():
            return flat
        flat = self.usecases_root / f"{use_case_id}_Business_Factsheet.md"
        return flat if flat.exists() else None

    def get_primary_decision_question(self, use_case_id: str) -> Optional[str]:
        """
        Get the primary decision question (first Core Business Question) from the use case Business Factsheet.
        Used for mockup header so the analytics path is self-explanatory.

        Args:
            use_case_id: Use case ID (e.g., "COM-001")

        Returns:
            First question from section "2. Core Business Questions" or None if not found
        """
        factsheet_path = self._resolve_business_factsheet_path(use_case_id)
        if not factsheet_path:
            return None
        with open(factsheet_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Find "## 2. Core Business Questions" and take first list item
        marker = "## 2. Core Business Questions"
        if marker not in content:
            return None
        after = content.split(marker, 1)[1]
        # Next section starts with ## or end of file; first list item only (with optional continuation lines)
        lines = after.split("\n")
        first_text = None
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("##"):
                break
            if stripped.startswith("- ") and len(stripped) > 2:
                if first_text is not None:
                    break  # already have first bullet; stop
                first_text = stripped[2:].strip()
                continue
            if first_text is not None and stripped and not stripped.startswith("-"):
                first_text = f"{first_text} {stripped}"
        return first_text

    def load_use_case_inventory(self) -> Dict[str, Any]:
        """Load UseCase_Inventory.md to get use case titles."""
        inventory_file = self.repo_root / "framework" / "usecases" / "UseCase_Inventory.md"
        
        if not inventory_file.exists():
            return {}
        
        # Parse markdown table to extract use case titles
        with open(inventory_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Simple parsing: look for table rows with use case IDs
        use_cases = {}
        lines = content.split('\n')
        for line in lines:
            if '|' in line and ('COM-' in line or 'FIN-' in line or 'OPS-' in line or 'SCM-' in line or 'XD-' in line):
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3 and parts[1].startswith(('COM-', 'FIN-', 'OPS-', 'SCM-', 'XD-')):
                    use_case_id = parts[1]
                    title = parts[2] if len(parts) > 2 else use_case_id
                    use_cases[use_case_id] = title
        
        return use_cases
    
    def get_use_case_display_name(self, use_case_id: str) -> str:
        """
        Get display name for use case.
        
        Args:
            use_case_id: Use case ID
        
        Returns:
            Display name or use case ID if not found
        """
        # Try factsheet first
        factsheet = self.load_use_case_factsheet(use_case_id)
        if factsheet and 'title' in factsheet:
            return factsheet['title']
        
        # Try inventory
        inventory = self.load_use_case_inventory()
        if use_case_id in inventory:
            return inventory[use_case_id]
        
        # Fallback to ID
        return use_case_id
    
    def get_page_config(self, use_case_id: str, page_name: str) -> Dict[str, Any]:
        """
        Get page configuration for a specific use case and page.
        
        Args:
            use_case_id: Use case ID
            page_name: Page name (overview or detail)
        
        Returns:
            Page configuration dictionary
        """
        bracket = self.load_use_case_bracket(use_case_id)
        ux = (bracket.get("ux_layout_rules") or {}) if isinstance(bracket, dict) else {}
        if not isinstance(ux, dict):
            ux = {}

        # Default slot set expected by the scaffold generator
        slots: Dict[str, bool] = {
            "needs_trend": False,
            "needs_variance": False,
            "needs_ranking": False,
            "needs_mix": False,
            "needs_exceptions": False,
            "needs_detail_matrix": False,
            "needs_root_cause": False,
            "needs_prescriptive": False,
            "needs_funnel": False,
            # Generator-specific toggles
            "exclude_time_slicer": False,
            "action_teaser": True,
        }

        def _apply_from_component_30s(component_30s: Any) -> None:
            if not isinstance(component_30s, list):
                return
            for item in component_30s:
                if not isinstance(item, dict):
                    continue
                vt = item.get("visual_type")
                if vt == "trend_line":
                    slots["needs_trend"] = True
                elif vt == "bar_chart":
                    # Heuristic: multi-KPI bar chart indicates variance/bridge; otherwise ranking.
                    kpi_ids = item.get("kpi_ids")
                    if isinstance(kpi_ids, list) and len([x for x in kpi_ids if isinstance(x, str) and x.strip()]) >= 2:
                        slots["needs_variance"] = True
                    slots["needs_ranking"] = True
                elif vt in ("stacked_bar", "hundred_percent_stacked_bar"):
                    slots["needs_mix"] = True
                elif vt == "funnel":
                    slots["needs_funnel"] = True

        if page_name == "overview":
            p1 = ux.get("page_1_summary") or {}
            if not isinstance(p1, dict):
                p1 = {}
            _apply_from_component_30s(p1.get("component_30s"))
            # Overview pages are typically diagnostic/variance.
            template = "T2"
            return {
                "name": "overview",
                "layer": [3, 30],
                "template": template,
                "needs_action_panel": False,
                "slots": slots,
            }

        if page_name == "detail":
            p2 = ux.get("page_2_execution") or {}
            if not isinstance(p2, dict):
                p2 = {}
            c300 = p2.get("component_300s") or {}
            if not isinstance(c300, dict):
                c300 = {}
            has_action_panel = bool(c300.get("action_panel", False))
            # Detail pages are execution-focused; treat as prescriptive when action panel is enabled.
            template = "T4" if has_action_panel else "T2"
            slots["needs_detail_matrix"] = True
            slots["needs_prescriptive"] = has_action_panel
            return {
                "name": "detail",
                "layer": [300],
                "template": template,
                "needs_action_panel": has_action_panel,
                "slots": slots,
            }

        raise ValueError(f"Page {page_name} not supported (expected 'overview' or 'detail')")
    
    def validate_theme_exists(self, theme_name: str) -> bool:
        """
        Validate that theme file exists.
        
        Args:
            theme_name: Theme name (e.g., "Brand Blue__Monochromatic__Light__#118DFF")
        
        Returns:
            True if theme exists, False otherwise
        """
        # Theme files are in theme_generator/themes/
        theme_root = self.repo_root / "products" / "fabric_powerbi" / "tooling" / "theme_generator" / "themes"
        
        # Search for theme file
        for theme_file in theme_root.rglob(f"{theme_name}.json"):
            if theme_file.exists():
                return True
        
        return False
