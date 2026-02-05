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
        self.framework_root = self.repo_root / "framework" / "templates" / "page_templates"
        self.governance_root = self.framework_root / "governance"
        self.mappings_root = self.framework_root / "mappings"
        self.usecases_root = self.repo_root / "framework" / "usecases"
    
    def load_use_case_mapping(self) -> Dict[str, Any]:
        """Load UseCase_PageTemplate_Map.yaml."""
        mapping_file = self.mappings_root / "UseCase_PageTemplate_Map.yaml"
        if not mapping_file.exists():
            raise FileNotFoundError(f"Use case mapping not found: {mapping_file}")
        
        with open(mapping_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
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
        mapping = self.load_use_case_mapping()
        
        if use_case_id not in mapping.get('use_cases', {}):
            raise ValueError(f"Use case {use_case_id} not found in mapping")
        
        use_case_config = mapping['use_cases'][use_case_id]
        
        for page in use_case_config.get('pages', []):
            if page.get('name') == page_name:
                return page
        
        raise ValueError(f"Page {page_name} not found for use case {use_case_id}")
    
    def validate_theme_exists(self, theme_name: str) -> bool:
        """
        Validate that theme file exists.
        
        Args:
            theme_name: Theme name (e.g., "Brand Blue__Monochromatic__Light__#118DFF")
        
        Returns:
            True if theme exists, False otherwise
        """
        # Theme files are in theme_generator/themes/
        theme_root = self.repo_root / "implementations" / "microsoft_fabric_powerbi" / "tools" / "theme_generator" / "themes"
        
        # Search for theme file
        for theme_file in theme_root.rglob(f"{theme_name}.json"):
            if theme_file.exists():
                return True
        
        return False
