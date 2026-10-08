"""
Scaffold Generator

Main generator class that orchestrates scaffold generation.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from .config_loader import ConfigLoader
from .page_builder import PageBuilder
from .alt_text import apply_alt_text
from .pbip_writer import PBIPWriter
from .visual_validator import validate_page
from . import design_rules_enforcer


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
        self.bracket = None

    def load_config(self):
        """Load all configuration files."""
        # Load page configuration
        self.page_config = self.config_loader.get_page_config(self.use_case_id, self.page_name)
        # R2.3: raw bracket, needed by design_rules_enforcer (validate()).
        self.bracket = self.config_loader.load_use_case_bracket(self.use_case_id)
        
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

        # title_policy: are the exhibit statements value-verified (title_statements_verified)?
        # Default False (A-34, 08.10.2026; config_loader already defaulted to False since R6.2).
        # The question leads every visual header; the message is never the title (D-641).
        self.page_builder.assert_statement_titles = self.page_config.get("assert_statement_titles", False)
        # Titelblock (A-34): page_1_summary.title_lines -> Kernaussage ueber wer / was / wann.
        self.page_builder.title_lines = self.page_config.get("title_lines") if self.page_name == "overview" else None
        # Sprache des Alt-Texts aus dem Bracket (ux_layout_rules.report_locale, Default en-US).
        self.page_builder.report_locale = self.page_config.get("report_locale")
        self.page_builder.text_measures = frozenset(self.page_config.get("text_measures") or ())

        # Speaking page ID (human-readable; no Power BI default hex IDs)
        # e.g. Page_COM001_Overview, Page_COM001_Detail
        uc_normalized = self.use_case_id.replace("-", "")
        self.page_id = f"Page_{uc_normalized}_{self.page_name.capitalize()}"

        # Get display name
        page_display_name = f"{self.use_case_id} - {self.page_name.capitalize()}"
        
        # Build page metadata (canvas: report_canvas > grid_blueprint.canvas > default)
        report_canvas = self.page_config.get('report_canvas')
        grid_blueprint_for_meta = self.page_config.get('grid_blueprint')
        canvas_w = report_canvas.get('width') if report_canvas else None
        canvas_h = report_canvas.get('height') if report_canvas else None
        if canvas_w is None and grid_blueprint_for_meta:
            c = grid_blueprint_for_meta.get('canvas') or {}
            canvas_w, canvas_h = c.get('width'), c.get('height')
        page_metadata = self.page_builder.build_page_metadata(
            page_id=self.page_id,
            display_name=page_display_name,
            theme_name=self.theme_name,
            width=canvas_w,
            height=canvas_h,
            is_drillthrough_target=(self.page_name == "detail"),
        )
        
        # Build page structure with visuals (page_config from get_page_config)
        template = self.page_config.get('template', 'T2')
        has_action_panel = self.page_config.get('needs_action_panel', False)
        slots = self.page_config.get('slots', {})
        card_kpi_ids = self.page_config.get('card_kpi_ids') or []
        card_measure_names = self.page_config.get('card_measure_names') or []
        kpi_id_to_measure_name = self.page_config.get('kpi_id_to_measure_name') or {}
        # Round-trip from ux_layout_rules: pass component_30s + slot_order so builder uses exact visual_type per position
        component_30s = self.page_config.get('component_30s') if self.page_name == 'overview' else None
        slot_order = ['trend', 'variance'] if self.page_name == 'overview' else None  # 2-Page-Lead order
        # T4 Detail page: load Action Panel content from action codes (Bracket orchestration.action_code_ids)
        action_panel_content = None
        if has_action_panel and self.page_name == 'detail':
            action_panel_content = self.config_loader.get_action_panel_content(self.use_case_id)

        grid_blueprint = self.page_config.get('grid_blueprint')
        template_id = self.page_config.get('template_id')
        canvas_width = canvas_height = None
        if grid_blueprint:
            canvas = grid_blueprint.get('canvas') or {}
            canvas_width = canvas.get('width')
            canvas_height = canvas.get('height')
        report_canvas = self.page_config.get('report_canvas')
        if report_canvas:
            canvas_width = report_canvas.get('width') or canvas_width
            canvas_height = report_canvas.get('height') or canvas_height
        visual_templates = self.config_loader.load_all_visual_templates() if template_id else {}

        detail_matrix_columns = self.page_config.get('detail_matrix_columns') if self.page_name == 'detail' else None
        detail_matrix_measures = self.page_config.get('detail_matrix_measures') if self.page_name == 'detail' else None
        smart_narrative_text = self.page_config.get('smart_narrative_text') if self.page_name == 'detail' else None
        big_idea_text = self.page_config.get('big_idea_text') if self.page_name == 'overview' else None
        detail_matrix_sort_by = self.page_config.get('detail_matrix_sort_by') if self.page_name == 'detail' else None
        detail_matrix_top_n = self.page_config.get('detail_matrix_top_n') if self.page_name == 'detail' else None
        detail_matrix_highlight_rule = self.page_config.get('detail_matrix_highlight_rule') if self.page_name == 'detail' else None
        detail_matrix_topn_field = self.page_config.get('detail_matrix_topn_field') if self.page_name == 'detail' else None
        narrative_measure_name = self.page_config.get('narrative_measure_name') if self.page_name == 'detail' else None
        active_actions_measure_name = self.page_config.get('active_actions_measure_name') if self.page_name == 'detail' else None
        # Semantic-delta KPI band (Gap A): overview + per-bracket opt-in (semantic_delta_cards).
        # Default False keeps every other report's single KPI band unchanged (COM-002 opts in).
        semantic_delta_cards = self.page_name == 'overview' and bool(self.page_config.get('semantic_delta_cards', False))
        page_structure = self.page_builder.build_page_structure(
            slots=slots,
            template=template,
            has_action_panel=has_action_panel,
            visual_slot_mapping=self.config.get('visual_slot_mapping'),
            component_30s=component_30s,
            slot_order=slot_order,
            card_kpi_ids=card_kpi_ids,
            card_measure_names=card_measure_names,
            kpi_id_to_measure_name=kpi_id_to_measure_name,
            action_panel_content=action_panel_content,
            grid_blueprint=grid_blueprint,
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            visual_templates=visual_templates,
            detail_matrix_columns=detail_matrix_columns,
            detail_matrix_measures=detail_matrix_measures,
            smart_narrative_text=smart_narrative_text,
            big_idea_text=big_idea_text,
            detail_matrix_sort_by=detail_matrix_sort_by,
            detail_matrix_top_n=detail_matrix_top_n,
            detail_matrix_highlight_rule=detail_matrix_highlight_rule,
            detail_matrix_topn_field=detail_matrix_topn_field,
            narrative_measure_name=narrative_measure_name,
            active_actions_measure_name=active_actions_measure_name,
            semantic_delta_cards=semantic_delta_cards,
            model_columns=self.page_config.get("model_columns"),
            kpi_good_is=self.page_config.get("kpi_good_is") or {},
            variance_kpi_ids=self.page_config.get("variance_kpi_ids") or set(),
            comparison_refs=self.page_config.get("comparison_refs") or {},
            kpi_band_delta=self.page_config.get("kpi_band_delta") if self.page_name == "overview" else None,
        )

        self._add_last_refresh(page_structure["visuals"])
        # Alt-Text fuer jedes nicht-dekorative Visual (Learn-Checkliste, ENSURE_ALTTEXT aktiv seit
        # 01.10.2026). Haupt-Slots tragen ihn schon (mit Vergleichsreihe); apply_alt_text laesst
        # vorhandenen Alt-Text stehen.
        for _vis in page_structure["visuals"] + page_structure.get("slicers", []):
            apply_alt_text(_vis, locale=self.page_builder.report_locale,
                           text_measures=self.page_builder.text_measures)

        self.page_structure = {
            "metadata": page_metadata,
            "visuals": page_structure["visuals"],
            "slicers": page_structure.get("slicers", []),
            "page_type": template,
        }
    
    def _add_last_refresh(self, visuals: List[Dict[str, Any]]) -> None:
        """Datenstand oben rechts auf der Detailseite, gebunden an `Last Refresh (<SUFFIX>)`.

        Seit #436 (10.08.2026) stand dieses Visual in allen 17 Reports -- von Hand in dist/,
        nie im Generator. Beim ersten Rollout am 23.09.2026 waere es aus jedem Report
        verschwunden, ohne dass ein Tor es gemerkt haette. Die Aktualitaet der Daten ist
        Teil der Abnahme (ADR-0017 §Verification), also gehoert sie in den Generator.

        Die Position kommt aus dem Raster, nicht aus einer Zahl: Spalte und Breite des
        ActionPanel, Zeile und Hoehe des Smart_Narrative. Das ist die Zelle, die dist/ von
        Hand besetzt hatte (x 1592, y 32, 296 x 70 auf dem Produktionsraster).
        """
        name = self.page_config.get("last_refresh_measure_name") if self.page_name == "detail" else None
        if not name or any(v.get("name") == "Last_Refresh" for v in visuals):
            return
        pos = {v.get("name"): v.get("position") or {} for v in visuals}
        panel, narrativ = pos.get("ActionPanel"), pos.get("Smart_Narrative")
        if not panel or not narrativ:
            return
        from .layout_calculator import Position
        vis = self.page_builder.visual_builder.build_narrative_card(
            Position(x=panel["x"], y=narrativ["y"], width=panel["width"], height=narrativ["height"]),
            measure_ref=name, name="Last_Refresh")
        vis["position"]["tabOrder"] = max((p.get("tabOrder", 0) for p in pos.values()), default=0) + 1
        visuals.append(vis)

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
            # R2.3-Fund follow-up: ActionPanel is a cardVisual (bound to the
            # governed Active Actions Text measure) when a domain suffix is
            # resolvable, textbox otherwise (synthesized-text fallback) -- so
            # identify it by name, not a single expected visualType.
            action_panel_visuals = [
                v for v in self.page_structure["visuals"]
                if v.get("name") == "ActionPanel"
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

        # Visual-level validation (queryState roles, names, bounds)
        canvas_w = self.page_structure["metadata"].get("width", 1920)
        canvas_h = self.page_structure["metadata"].get("height", 1080)
        errors.extend(validate_page(self.page_structure, canvas_w, canvas_h))

        # R2.3: design_rules.yaml enforcement (R2.2). No-op for brackets that have not
        # opted into intent_rules_version: 2 (see design_rules_enforcer's own gating).
        if self.bracket is not None:
            rules = design_rules_enforcer.load_design_rules()
            kpi_id_to_calc_type = self.config_loader.load_kpi_id_to_calc_type_map()
            errors.extend(design_rules_enforcer.check_bracket_rules(rules, self.bracket, kpi_id_to_calc_type))
            if self.page_name == "overview":
                errors.extend(
                    design_rules_enforcer.check_output_rules(
                        rules, self.bracket, overview_visuals=self.page_structure["visuals"]
                    )
                )
            elif self.page_name == "detail":
                detail_matrix_visual = next(
                    (v for v in self.page_structure["visuals"] if v.get("name") == "Detail_Matrix"), None
                )
                errors.extend(
                    design_rules_enforcer.check_output_rules(
                        rules,
                        self.bracket,
                        detail_matrix_sort_by=self.page_config.get("detail_matrix_sort_by"),
                        detail_matrix_visual=detail_matrix_visual,
                    )
                )

        return errors
    
    def write(
        self,
        output_path: Path,
        *,
        append_page_only: bool = False,
        dataset_reference_path: Optional[str] = None,
    ):
        """
        Write PBIP structure to disk.
        
        Args:
            output_path: Path to .Report folder (e.g., "COM-001.Report")
            append_page_only: If True, only append this page (do not overwrite report.json or version.json)
            dataset_reference_path: Optional relative path to semantic model for report.json (used only when not append_page_only)
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
        
        if not append_page_only:
            # Write root .pbip (ItemShortcut) so folder is a valid PBIP; then report.json and version.json
            writer.write_pbip_file()
            writer.write_report_json(
                theme_name=None,
                dataset_reference_path=dataset_reference_path,
            )
            writer.write_version_json()
        
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
    
    def get_page_structure(self) -> Dict[str, Any]:
        """
        Get generated page structure (for testing/mockup generation).
        
        Returns:
            Page structure dictionary
        """
        if self.page_structure is None:
            raise ValueError("Page structure not generated. Call generate() first.")
        
        return self.page_structure
