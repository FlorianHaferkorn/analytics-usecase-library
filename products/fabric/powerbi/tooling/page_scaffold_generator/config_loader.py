"""
Configuration Loader

Loads governance YAML files and use case configurations.
"""

import json
import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List


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
        self.grid_templates_root = self.page_templates_root / "grid_templates"
        self.visual_templates_root = self.page_templates_root / "visual_templates"
        self.governance_root = self.page_templates_root / "governance"
        self.usecases_root = self.repo_root / "core" / "usecases"
        self.kpi_catalog_path = self.repo_root / "core" / "kpi_catalog" / "KPI_Catalog.md"
        self.action_codes_root = self.repo_root / "core" / "action_codes"
        self._kpi_id_to_measure_name: Optional[Dict[str, str]] = None

    def load_kpi_id_to_measure_name_map(self) -> Dict[str, str]:
        """
        Load KPI catalog and return mapping kpi_id -> measure name (as in semantic model).
        Measure name = kpi_key or technical.dax_name, matching generate_tmdl_measures.ps1.
        Uses chunk-based parsing (split by "- kpi_id:") because the full YAML block can be
        invalid as a single document (e.g. malformed list items).
        """
        if self._kpi_id_to_measure_name is not None:
            return self._kpi_id_to_measure_name
        result: Dict[str, str] = {}
        if not self.kpi_catalog_path.exists():
            return result
        try:
            content = self.kpi_catalog_path.read_text(encoding="utf-8")
            match = re.search(r"```yaml\s*\n(.*?)```", content, re.DOTALL)
            if not match:
                return result
            block = match.group(1)
            # Split into chunks by list item start "- kpi_id:"
            chunk_starts = list(re.finditer(r"(?m)^\s*-\s*kpi_id\s*:\s*([^\s#\r\n]+)", block))
            for i, mo in enumerate(chunk_starts):
                kpi_id = mo.group(1).strip()
                start = mo.start()
                end = chunk_starts[i + 1].start() if i + 1 < len(chunk_starts) else len(block)
                chunk = block[start:end]
                # kpi_key: "quoted" or kpi_key: unquoted
                kpi_key_m = re.search(r'(?m)^\s*kpi_key\s*:\s*(?:"([^"]*)"|([^\r\n#]+))', chunk)
                kpi_key = (kpi_key_m.group(1) or (kpi_key_m.group(2) or "").strip()) if kpi_key_m else None
                # technical.dax_name: line "dax_name: ..." (may be under technical:)
                dax_m = re.search(r'(?m)^\s*dax_name\s*:\s*(?:"([^"]*)"|([^\r\n#]+))', chunk)
                dax_name = (dax_m.group(1) or (dax_m.group(2) or "").strip()) if dax_m else None
                measure_name = (kpi_key or dax_name or kpi_id).strip()
                if measure_name:
                    result[kpi_id] = measure_name
            self._kpi_id_to_measure_name = result
        except Exception:
            pass
        return result

    def _resolve_use_case_dir(self, use_case_id: str) -> Optional[Path]:
        """Resolve core use case directory: core/usecases/core/<ID>_*/."""
        core = self.usecases_root / "core"
        if not core.exists():
            return None
        for p in core.iterdir():
            if p.is_dir() and p.name.startswith(f"{use_case_id}_"):
                return p
        return None

    def get_action_panel_content(self, use_case_id: str) -> Optional[str]:
        """
        Build Action Panel text from use case action codes (Bracket orchestration.action_code_ids).
        Loads each action code YAML and formats name, owner, and first steps for the textbox.
        Returns None if no action codes or on error; caller uses placeholder then.
        """
        try:
            bracket = self.load_use_case_bracket(use_case_id)
            orch = bracket.get("orchestration") or {}
            ids = orch.get("action_code_ids") or []
            if not ids or not isinstance(ids, list):
                return None
            lines = ["Recommended actions (from action codes)", ""]
            for ac_id in ids:
                if not isinstance(ac_id, str) or not ac_id.strip():
                    continue
                ac_id = ac_id.strip()
                # Find YAML under action_codes (skip decision_spines)
                found = None
                for path in self.action_codes_root.rglob(f"{ac_id}.yaml"):
                    if "decision_spines" in path.parts:
                        continue
                    found = path
                    break
                if not found or not found.exists():
                    lines.append(f"• {ac_id} (definition not found)")
                    continue
                with open(found, "r", encoding="utf-8") as f:
                    ac = yaml.safe_load(f) or {}
                name = ac.get("name") or ac_id
                owner = ac.get("owner_role") or "—"
                steps = []
                exec_block = ac.get("operational_execution") or {}
                if isinstance(exec_block, dict):
                    steps = exec_block.get("steps") or []
                if not isinstance(steps, list):
                    steps = []
                steps = steps[:3]
                lines.append(f"• {ac_id} — {name}")
                lines.append(f"  Owner: {owner}")
                for s in steps:
                    if isinstance(s, str):
                        lines.append(f"  · {s}")
                lines.append("")
            if len(lines) <= 2:
                return None
            text = "\n".join(lines).strip()
            # Escape single quotes for Power BI Literal (double them)
            text = text.replace("'", "''")
            return f"'{text}'"
        except Exception:
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
    
    def load_grid_page_template(self, template_id: str) -> Dict[str, Any]:
        """
        Load a grid page template (pulse, investigator, action_matrix) by template_id.
        Returns dict with template_id, canvas, slots (list of slot_id, grid, visual_type_hint).
        """
        path = self.grid_templates_root / f"{template_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Grid page template not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_visual_template(self, visual_template_id: str) -> Optional[Dict[str, Any]]:
        """Load a visual template by visual_template_id (e.g. KPI_Card_WithDelta)."""
        if not self.visual_templates_root.exists():
            return None
        for p in self.visual_templates_root.glob("*.json"):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("visual_template_id") == visual_template_id:
                    return data
            except (json.JSONDecodeError, KeyError):
                continue
        return None

    def load_all_visual_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load all visual templates from visual_templates/ keyed by visual_template_id."""
        result: Dict[str, Dict[str, Any]] = {}
        if not self.visual_templates_root.exists():
            return result
        for p in self.visual_templates_root.glob("*.json"):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                vid = data.get("visual_template_id")
                if vid:
                    result[vid] = data
            except (json.JSONDecodeError, KeyError):
                continue
        return result

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
                elif vt == "waterfall":
                    slots["needs_variance"] = True
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
            # Pass through for builder: exact visual_type per position (round-trip from layout editor).
            c3s = p1.get("component_3s")
            c30s = p1.get("component_30s")
            # Card KPI IDs: strategic (component_3s) + first 3 influencing from orchestration
            orch = (bracket.get("orchestration") or {}) if isinstance(bracket, dict) else {}
            strategic = (c3s.get("kpi_id") if isinstance(c3s, dict) else None) or orch.get("strategic_kpi_id", "")
            influencing = orch.get("influencing_kpi_ids") or []
            card_kpi_ids = ([strategic] if strategic else []) + list(influencing)[:3]
            kpi_to_measure = self.load_kpi_id_to_measure_name_map()
            card_measure_names = [kpi_to_measure.get(k, k) for k in card_kpi_ids]
            template_id = ux.get("page_template") or p1.get("template_id")
            grid_blueprint = None
            if template_id:
                try:
                    grid_blueprint = self.load_grid_page_template(template_id)
                except FileNotFoundError:
                    pass
            report_canvas = ux.get("report_canvas") if isinstance(ux.get("report_canvas"), dict) else None
            return {
                "name": "overview",
                "layer": [3, 30],
                "template": template,
                "template_id": template_id,
                "grid_blueprint": grid_blueprint,
                "report_canvas": report_canvas,
                "needs_action_panel": False,
                "slots": slots,
                "component_3s": dict(c3s) if isinstance(c3s, dict) else {},
                "component_30s": list(c30s) if isinstance(c30s, list) else [],
                "card_kpi_ids": card_kpi_ids,
                "card_measure_names": card_measure_names,
                "kpi_id_to_measure_name": kpi_to_measure,
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
            # Use same KPI cards as overview (strategic + influencing) so detail cards have measure bindings
            orch = (bracket.get("orchestration") or {}) if isinstance(bracket, dict) else {}
            p1 = ux.get("page_1_summary") or {}
            c3s = p1.get("component_3s") if isinstance(p1, dict) else {}
            strategic = (c3s.get("kpi_id") if isinstance(c3s, dict) else None) or orch.get("strategic_kpi_id", "")
            influencing = orch.get("influencing_kpi_ids") or []
            card_kpi_ids = ([strategic] if strategic else []) + list(influencing)[:3]
            kpi_to_measure = self.load_kpi_id_to_measure_name_map()
            card_measure_names = [kpi_to_measure.get(k, k) for k in card_kpi_ids]
            template_id = ux.get("page_template") or p2.get("template_id")
            grid_blueprint = None
            if template_id:
                try:
                    grid_blueprint = self.load_grid_page_template(template_id)
                except FileNotFoundError:
                    pass
            report_canvas = ux.get("report_canvas") if isinstance(ux.get("report_canvas"), dict) else None
            return {
                "name": "detail",
                "layer": [300],
                "template": template,
                "template_id": template_id,
                "grid_blueprint": grid_blueprint,
                "report_canvas": report_canvas,
                "needs_action_panel": has_action_panel,
                "slots": slots,
                "card_kpi_ids": card_kpi_ids,
                "card_measure_names": card_measure_names,
                "kpi_id_to_measure_name": kpi_to_measure,
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
        theme_root = self.repo_root / "products" / "fabric" / "powerbi" / "tooling" / "theme_generator" / "themes"
        
        # Search for theme file
        for theme_file in theme_root.rglob(f"{theme_name}.json"):
            if theme_file.exists():
                return True
        
        return False
