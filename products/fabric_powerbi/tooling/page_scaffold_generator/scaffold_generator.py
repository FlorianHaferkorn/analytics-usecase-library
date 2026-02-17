"""
Scaffold Generator

Main generator class that orchestrates scaffold generation.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from .config_loader import ConfigLoader
from .page_builder import PageBuilder
from .pbip_writer import PBIPWriter


class PageScaffoldGenerator:
    """Generates Power BI page scaffolds from governance files."""
    
    def __init__(
        self,
        use_case_id: str,
        page_name: str,
        theme_name: Optional[str] = None,
        repo_root: Optional[Path] = None
    ):
        """
        Initialize scaffold generator.
        
        Args:
            use_case_id: Use case ID (e.g., "COM-001")
            page_name: Page name ("overview" or "detail")
            theme_name: Optional theme name (defaults to framework default)
            repo_root: Repository root path (auto-detected if None)
        """
        self.use_case_id = use_case_id
        self.page_name = page_name
        self.theme_name = theme_name
        self.repo_root = repo_root
        
        self.config_loader = ConfigLoader(repo_root)
        self.page_builder = PageBuilder()
        
        self.config = None
        self.page_config = None
        self.page_id = None
        self.page_structure = None
    
    def load_config(self):
        """Load all configuration files."""
        # Load page configuration
        self.page_config = self.config_loader.get_page_config(self.use_case_id, self.page_name)
        
        # Load governance files
        self.config = {
            "visual_slot_mapping": self.config_loader.load_visual_slot_mapping(),
            "layout_grid": self.config_loader.load_layout_grid(),
            "color_semantics": self.config_loader.load_color_semantics()
        }
        
        # Validate theme if provided
        if self.theme_name:
            if not self.config_loader.validate_theme_exists(self.theme_name):
                raise ValueError(f"Theme not found: {self.theme_name}")
    
    def generate(self):
        """Generate page scaffold."""
        if self.config is None:
            self.load_config()

        # Speaking page ID (human-readable; no Power BI default hex IDs)
        # e.g. Page_COM001_Overview, Page_COM001_Detail
        uc_normalized = self.use_case_id.replace("-", "")
        self.page_id = f"Page_{uc_normalized}_{self.page_name.capitalize()}"

        # Get display name
        display_name = self.config_loader.get_use_case_display_name(self.use_case_id)
        page_display_name = f"{display_name} - {self.page_name.capitalize()}"
        
        # Build page metadata
        page_metadata = self.page_builder.build_page_metadata(
            page_id=self.page_id,
            display_name=page_display_name,
            theme_name=self.theme_name
        )
        
        # Build page structure with visuals
        template = self.page_config.get('template', 'T2')
        has_action_panel = self.page_config.get('needs_action_panel', False)
        slots = self.page_config.get('slots', {})
        # Round-trip from ux_layout_rules: pass component_30s + slot_order so builder uses exact visual_type per position
        component_30s = self.page_config.get('component_30s') if self.page_name == 'overview' else None
        slot_order = ['trend', 'variance'] if self.page_name == 'overview' else None  # 2-Page-Lead order

        page_structure = self.page_builder.build_page_structure(
            slots=slots,
            template=template,
            has_action_panel=has_action_panel,
            visual_slot_mapping=self.config.get('visual_slot_mapping'),
            component_30s=component_30s,
            slot_order=slot_order,
        )
        
        self.page_structure = {
            "metadata": page_metadata,
            "visuals": page_structure["visuals"],
            "slicers": page_structure.get("slicers", []),
            "page_type": template,
        }
    
    def validate(self) -> List[str]:
        """
        Validate scaffold against rules.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if self.page_structure is None:
            errors.append("Page structure not generated. Call generate() first.")
            return errors
        
        # Validate speaking page name (e.g. Page_COM001_Overview)
        if not self.page_structure["metadata"]["name"].startswith("Page_"):
            errors.append("Page name should be speaking (e.g. Page_COM001_Overview)")

        # Validate template assignment
        template = self.page_config.get('template')
        if template not in ['T1', 'T2', 'T3', 'T4']:
            errors.append(f"Invalid template: {template}")
        
        # Validate slicer count
        slicer_count = len(self.page_structure.get("slicers", []))
        if slicer_count > 4:
            errors.append(f"Too many slicers: {slicer_count} (max 4)")
        
        # Validate Action Panel presence for T4
        if template == 'T4':
            has_action_panel = self.page_config.get('needs_action_panel', False)
            action_panel_visuals = [
                v for v in self.page_structure["visuals"]
                if v.get("visual", {}).get("visualType") == "textbox"
            ]
            if has_action_panel and not action_panel_visuals:
                errors.append("T4 template requires Action Panel but none found")
        
        # Validate Detail Matrix only on detail pages
        if self.page_name == "overview":
            detail_matrix_visuals = [
                v for v in self.page_structure["visuals"]
                if v.get("name") == "DetailMatrix"
            ]
            if detail_matrix_visuals:
                errors.append("Detail Matrix should only be on detail pages")
        
        return errors
    
    def write(self, output_path: Path):
        """
        Write PBIP structure to disk.
        
        Args:
            output_path: Path to .Report folder (e.g., "COM-001.Report")
        """
        if self.page_structure is None:
            raise ValueError("Page structure not generated. Call generate() first.")
        
        # Validate before writing
        errors = self.validate()
        if errors:
            raise ValueError(f"Validation errors: {', '.join(errors)}")
        
        # Initialize writer
        writer = PBIPWriter(output_path)
        writer.create_pbip_structure()
        
        # Write report.json with base theme only; when --theme was passed, CLI will call apply_theme() to copy theme and add customTheme + resourcePackages
        writer.write_report_json(theme_name=None)
        
        # Write pages.json (append if file exists)
        pages_file = writer.pages_path / "pages.json"
        append = pages_file.exists()
        writer.write_pages_json(page_ids=[self.page_id], active_page=self.page_id, append=append)
        
        # Write page.json and visuals
        writer.write_page_structure(
            page_id=self.page_id,
            page_metadata=self.page_structure["metadata"],
            visuals=self.page_structure["visuals"],
            slicers=self.page_structure.get("slicers", [])
        )
        
        # Write version.json
        writer.write_version_json()
    
    def get_page_structure(self) -> Dict[str, Any]:
        """
        Get generated page structure (for testing/mockup generation).
        
        Returns:
            Page structure dictionary
        """
        if self.page_structure is None:
            raise ValueError("Page structure not generated. Call generate() first.")
        
        return self.page_structure
