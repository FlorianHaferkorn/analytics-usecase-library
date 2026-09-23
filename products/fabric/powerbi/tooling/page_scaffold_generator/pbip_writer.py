"""
PBIP Writer

Writes Power BI page structures to PBIP file format.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

from products.fabric.powerbi.tooling.schema_registry import (
    REPORT_SCHEMA as _REPORT_SCHEMA,
    PAGES_METADATA_SCHEMA as _PAGES_SCHEMA,
    VERSION_METADATA_SCHEMA as _VERSION_SCHEMA,
    PBIP_SCHEMA as _PBIP_SCHEMA,
    DEFINITION_PBIR_SCHEMA as _DEFINITION_PBIR_SCHEMA,
    DEFINITION_PBIR_VERSION as _DEFINITION_PBIR_VERSION,
)
from products.fabric.powerbi.tooling.theme_registration import (
    custom_theme_collection_name,
    registered_theme_filename,
)


class PBIPWriter:
    """Writes PBIP folder structure and JSON files."""

    REPORT_SCHEMA = _REPORT_SCHEMA
    PAGES_SCHEMA = _PAGES_SCHEMA
    VERSION_SCHEMA = _VERSION_SCHEMA
    PBIP_SCHEMA = _PBIP_SCHEMA
    PBIXPROJ_VERSION = "1.25"

    def __init__(self, report_path: Path):
        """
        Initialize PBIP writer.
        
        Args:
            report_path: Path to .Report folder (e.g., "COM-001.Report")
        """
        self.report_path = Path(report_path).resolve()
        self.definition_path = self.report_path / "definition"
        self.pages_path = self.definition_path / "pages"
    
    def create_pbip_structure(self):
        """Create PBIP folder structure."""
        self.definition_path.mkdir(parents=True, exist_ok=True)
        self.pages_path.mkdir(parents=True, exist_ok=True)

    def _pbip_filename(self) -> str:
        """Speaking name: derive from report folder (e.g. COM-001_Sales_Performance.Report -> COM-001_Sales_Performance.pbip)."""
        name = self.report_path.name
        if name.endswith(".Report"):
            return name[:-7] + ".pbip"  # strip ".Report"
        return name + ".pbip" if not name.endswith(".pbip") else name

    def write_pbip_file(self) -> Path:
        """
        Write root .pbip ItemShortcut so the folder is a valid PBIP (openable in Desktop / pbi-tools).
        Path "." means report artifact is this folder (contains definition/).
        Filename is a speaking name derived from the report folder (e.g. COM-001_Sales_Performance.pbip).
        """
        pbip_data = {
            "$schema": self.PBIP_SCHEMA,
            "version": "1.0",
            "artifacts": [{"report": {"path": "."}}],
        }
        pbip_file = self.report_path / self._pbip_filename()
        # Remove legacy Report.pbip if present so only the speaking-name file remains
        legacy_pbip = self.report_path / "Report.pbip"
        if legacy_pbip.exists() and legacy_pbip != pbip_file:
            legacy_pbip.unlink()
        with open(pbip_file, "w", encoding="utf-8") as f:
            json.dump(pbip_data, f, indent=2, ensure_ascii=False)
            f.write("\n")  # end-of-file-fixer (pre-commit) erwartet den Zeilenumbruch
        return pbip_file

    def write_version_txt(self):
        """Write Version.txt for pbi-tools PbixProj compatibility."""
        version_file = self.report_path / "Version.txt"
        version_file.write_text(self.PBIXPROJ_VERSION, encoding="utf-8", newline="\n")

    def write_report_metadata_json(self):
        """Write minimal ReportMetadata.json for pbi-tools PbixProj compatibility."""
        metadata_file = self.report_path / "ReportMetadata.json"
        metadata_file.write_text("{}", encoding="utf-8", newline="\n")

    def write_report_settings_json(self):
        """Write minimal ReportSettings.json for pbi-tools PbixProj compatibility."""
        settings_file = self.report_path / "ReportSettings.json"
        settings_file.write_text("{}", encoding="utf-8", newline="\n")

    @staticmethod
    def _sanitize_path_segment(value: str) -> str:
        return re.sub(r'[<>:"/\\|?*]', '_', value)

    def sync_legacy_report_folder(self):
        """Materialize a minimal legacy Report/ tree so pbi-tools can compile PBIX with layout."""
        definition_report = self.definition_path / "report.json"
        if not definition_report.exists():
            return

        report_root = self.report_path / "Report"
        sections_root = report_root / "sections"
        sections_root.mkdir(parents=True, exist_ok=True)

        (report_root / "report.json").write_text(definition_report.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")

        for existing in sections_root.iterdir():
            if existing.is_dir():
                for child in sorted(existing.rglob('*'), reverse=True):
                    if child.is_file():
                        child.unlink()
                    elif child.is_dir():
                        child.rmdir()
                existing.rmdir()

        pages_meta_path = self.pages_path / "pages.json"
        page_order: List[str] = []
        if pages_meta_path.exists():
            try:
                pages_meta = json.loads(pages_meta_path.read_text(encoding="utf-8"))
                page_order = list(pages_meta.get("pageOrder") or [])
            except json.JSONDecodeError:
                page_order = []

        if not page_order:
            page_order = sorted(p.name for p in self.pages_path.iterdir() if p.is_dir())

        for index, page_id in enumerate(page_order):
            page_dir = self.pages_path / page_id
            page_json = page_dir / "page.json"
            if not page_json.exists():
                continue

            page_data = json.loads(page_json.read_text(encoding="utf-8"))
            display_name = page_data.get("displayName") or page_data.get("name") or page_id
            section_name = f"{index:03d}_{self._sanitize_path_segment(display_name)}"
            section_dir = sections_root / section_name
            visuals_dir = section_dir / "visualContainers"
            visuals_dir.mkdir(parents=True, exist_ok=True)

            (section_dir / "section.json").write_text(page_json.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")

            src_visuals = page_dir / "visuals"
            if not src_visuals.exists():
                continue

            for visual_dir in sorted(p for p in src_visuals.iterdir() if p.is_dir()):
                visual_json = visual_dir / "visual.json"
                if not visual_json.exists():
                    continue
                legacy_visual_dir = visuals_dir / visual_dir.name
                legacy_visual_dir.mkdir(parents=True, exist_ok=True)
                (legacy_visual_dir / "visualContainer.json").write_text(
                    visual_json.read_text(encoding="utf-8"),
                    encoding="utf-8",
                    newline="\n")

    def write_report_json(
        self,
        theme_name: Optional[str] = None,
        dataset_reference_path: Optional[str] = None,
        connection_type: str = "byPath",
        dataset_id: Optional[str] = None,
    ):
        """
        Write definition/report.json.

        Args:
            theme_name: Optional theme name to reference
            dataset_reference_path: Relative path to semantic model — used when connection_type="byPath"
                                    (e.g. "../../Commercial.SemanticModel"). Works locally but NOT via Fabric REST API.
            connection_type: "byPath" (default, local PBIP) or "byConnection" (Fabric REST API deploy).
            dataset_id: Semantic model GUID — required when connection_type="byConnection".
        """
        report_data = {
            "$schema": self.REPORT_SCHEMA,
            "themeCollection": {
                "baseTheme": {
                    "name": "CY25SU10",
                    "reportVersionAtImport": {
                        "visual": "2.1.0",
                        "report": "3.0.0",
                        "page": "2.3.0"
                    },
                    "type": "SharedResources"
                }
            },
            "filterConfig": {
                "filters": []
            },
            "objects": {
                "section": [
                    {
                        "properties": {
                            "verticalAlignment": {
                                "expr": {
                                    "Literal": {
                                        "Value": "'Top'"
                                    }
                                }
                            }
                        }
                    }
                ],
                "outspacePane": [
                    {
                        "properties": {
                            "expanded": {
                                "expr": {
                                    "Literal": {
                                        "Value": "false"
                                    }
                                }
                            }
                        }
                    }
                ]
            },
            "settings": {
                "useStylableVisualContainerHeader": True,
                "exportDataMode": "AllowSummarized",
                "defaultFilterActionIsDataFilter": True,
                "defaultDrillFilterOtherVisuals": True,
                "allowChangeFilterTypes": True,
                "useEnhancedTooltips": True,
                "useDefaultAggregateDisplayName": True,
                "queryLimitOption": "None",
                "customMemoryLimit": "1048576",
                "customTimeoutLimit": "225"
            }
        }
        # datasetReference must not appear in report.json; schema does not allow additional properties.
        # Dataset binding is in definition.pbir only (_write_definition_pbir).

        # Add custom theme if provided

        if theme_name:
            theme_stem = custom_theme_collection_name(theme_name)
            theme_filename = registered_theme_filename(theme_stem)
            report_data["themeCollection"]["customTheme"] = {
                "name": theme_stem,
                "reportVersionAtImport": {
                    "visual": "2.1.0",
                    "report": "3.0.0",
                    "page": "2.3.0"
                },
                "type": "RegisteredResources"
            }
            
            report_data["resourcePackages"] = [
                {
                    "name": "SharedResources",
                    "type": "SharedResources",
                    "items": [
                        {
                            "name": "CY25SU10",
                            "path": "BaseThemes/CY25SU10.json",
                            "type": "BaseTheme"
                        }
                    ]
                },
                {
                    "name": "RegisteredResources",
                    "type": "RegisteredResources",
                    "items": [
                        {
                            "name": theme_filename,
                            "path": theme_filename,
                            "type": "CustomTheme"
                        }
                    ]
                }
            ]
        
        report_file = self.definition_path / "report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
            f.write("\n")  # end-of-file-fixer (pre-commit) erwartet den Zeilenumbruch

        # Power BI Desktop (Feb 2026+) requires definition.pbir at report root with definitionProperties schema (not report definition).
        self._write_definition_pbir(
            dataset_reference_path=dataset_reference_path,
            connection_type=connection_type,
            dataset_id=dataset_id,
        )
    
    def _write_definition_pbir(
        self,
        dataset_reference_path: Optional[str] = None,
        connection_type: str = "byPath",
        dataset_id: Optional[str] = None,
    ):
        """
        Write definition.pbir (report properties: version, datasetReference).
        Schema must be definitionProperties/1.x or 2.x; Desktop rejects definition/report schema here.

        connection_type="byPath"  — local PBIP (Desktop, pbi-tools). dataset_reference_path required.
        connection_type="byConnection" — Fabric REST API deploy. dataset_id (SemanticModel GUID) required.
                                         byPath references are silently rejected by the Fabric Items API.
        """
        pbir_data = {
            "$schema": _DEFINITION_PBIR_SCHEMA,
            "version": _DEFINITION_PBIR_VERSION,
        }

        if connection_type == "byConnection":
            pbir_data["datasetReference"] = {
                "byConnection": {
                    "connectionString": None,
                    "pbiServiceModelId": None,
                    "pbiModelVirtualServerName": "sobe_wowvirtualserver",
                    "pbiModelDatabaseName": dataset_id,
                    "connectionType": "pbiServiceXmlaStyleLive",
                    "name": "EntityDataSource",
                }
            }
        else:
            path = (dataset_reference_path or "").replace("\\", "/")
            if path:
                pbir_data["datasetReference"] = {"byPath": {"path": path}}

        pbir_file = self.report_path / "definition.pbir"
        with open(pbir_file, 'w', encoding='utf-8') as f:
            json.dump(pbir_data, f, indent=2, ensure_ascii=False)
            f.write("\n")  # end-of-file-fixer (pre-commit) erwartet den Zeilenumbruch
    
    def write_pages_json(self, page_ids: List[str], active_page: Optional[str] = None, append: bool = False):
        """
        Write definition/pages/pages.json.
        
        Args:
            page_ids: List of page IDs
            active_page: Active page ID (defaults to first page)
            append: If True, append to existing pages.json instead of overwriting
        """
        if not page_ids:
            raise ValueError("At least one page ID required")
        
        if active_page is None:
            active_page = page_ids[0]
        
        pages_file = self.pages_path / "pages.json"
        
        # If appending and file exists, load existing data and keep current active page
        if append and pages_file.exists():
            try:
                with open(pages_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                # Merge page IDs, avoiding duplicates
                existing_order = existing_data.get("pageOrder", [])
                combined_order = list(existing_order)
                for page_id in page_ids:
                    if page_id not in combined_order:
                        combined_order.append(page_id)
                page_ids = combined_order
                # Keep existing active page so Overview stays default when appending Detail
                existing_active = existing_data.get("activePageName")
                if existing_active is not None and existing_active in page_ids:
                    active_page = existing_active
            except Exception:
                # If loading fails, just overwrite
                pass
        
        pages_data = {
            "$schema": self.PAGES_SCHEMA,
            "pageOrder": page_ids,
            "activePageName": active_page
        }
        
        with open(pages_file, 'w', encoding='utf-8') as f:
            json.dump(pages_data, f, indent=2, ensure_ascii=False)
            f.write("\n")  # end-of-file-fixer (pre-commit) erwartet den Zeilenumbruch
    
    def write_page_json(self, page_id: str, page_data: Dict[str, Any]):
        """
        Write definition/pages/{page_id}/page.json.
        
        Args:
            page_id: Page ID
            page_data: Page metadata dictionary
        """
        page_dir = self.pages_path / page_id
        page_dir.mkdir(parents=True, exist_ok=True)
        
        page_file = page_dir / "page.json"
        with open(page_file, 'w', encoding='utf-8') as f:
            json.dump(page_data, f, indent=2, ensure_ascii=False)
            f.write("\n")  # end-of-file-fixer (pre-commit) erwartet den Zeilenumbruch
    
    def write_visual_json(self, page_id: str, visual_data: Dict[str, Any]):
        """
        Write definition/pages/{page_id}/visuals/{visual_id}/visual.json.
        
        Args:
            page_id: Page ID
            visual_data: Visual JSON structure (must have "name" field)
        """
        visual_id = visual_data.get("name")
        if not visual_id:
            raise ValueError("Visual data must have 'name' field")
        
        visuals_dir = self.pages_path / page_id / "visuals" / visual_id
        visuals_dir.mkdir(parents=True, exist_ok=True)
        
        visual_file = visuals_dir / "visual.json"
        # Ensure parent directory exists
        visual_file.parent.mkdir(parents=True, exist_ok=True)
        with open(visual_file, 'w', encoding='utf-8') as f:
            json.dump(visual_data, f, indent=2, ensure_ascii=False)
            f.write("\n")  # end-of-file-fixer (pre-commit) erwartet den Zeilenumbruch
    
    def write_page_structure(
        self,
        page_id: str,
        page_metadata: Dict[str, Any],
        visuals: List[Dict[str, Any]],
        slicers: List[Dict[str, Any]] = None
    ):
        """
        Write complete page structure (page.json + all visuals).
        
        Args:
            page_id: Page ID
            page_metadata: Page metadata dictionary
            visuals: List of visual JSON structures
            slicers: Optional list of slicer JSON structures
        """
        # Write page.json
        self.write_page_json(page_id, page_metadata)
        
        # Write visual JSONs
        for visual in visuals:
            self.write_visual_json(page_id, visual)
        
        # Write slicer JSONs (slicers are also visuals)
        if slicers:
            for slicer in slicers:
                self.write_visual_json(page_id, slicer)
    
    def write_version_json(self):
        """Write definition/version.json (required by Desktop and validate_pbip)."""
        version_data = {
            "$schema": self.VERSION_SCHEMA,
            "version": "2.0.0",
        }
        version_file = self.definition_path / "version.json"
        with open(version_file, "w", encoding="utf-8") as f:
            json.dump(version_data, f, indent=2, ensure_ascii=False)
            f.write("\n")  # end-of-file-fixer (pre-commit) erwartet den Zeilenumbruch
