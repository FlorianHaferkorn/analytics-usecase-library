"""
PBIP Writer

Writes Power BI page structures to PBIP file format.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional


class PBIPWriter:
    """Writes PBIP folder structure and JSON files."""
    
    REPORT_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.0.0/schema.json"
    PAGES_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json"
    
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
    
    def write_report_json(
        self,
        theme_name: Optional[str] = None,
        dataset_reference_path: Optional[str] = None,
    ):
        """
        Write definition/report.json.
        
        Args:
            theme_name: Optional theme name to reference
            dataset_reference_path: Optional relative path to semantic model (e.g. for datasetReference.byPath.path)
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
        if dataset_reference_path:
            report_data["datasetReference"] = {
                "byPath": {"path": dataset_reference_path}
            }
        
        # Add custom theme if provided
        if theme_name:
            report_data["themeCollection"]["customTheme"] = {
                "name": f"{theme_name}.json",
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
                            "name": f"{theme_name}.json",
                            "path": f"{theme_name}.json",
                            "type": "CustomTheme"
                        }
                    ]
                }
            ]
        
        report_file = self.definition_path / "report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
    
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
        
        # If appending and file exists, load existing data
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
        """Write definition/version.json."""
        version_data = {
            "version": "1.0"
        }
        
        version_file = self.definition_path / "version.json"
        with open(version_file, 'w', encoding='utf-8') as f:
            json.dump(version_data, f, indent=2, ensure_ascii=False)
