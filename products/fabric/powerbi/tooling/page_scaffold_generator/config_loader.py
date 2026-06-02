"""
Configuration Loader

Loads governance YAML files and use case configurations.
"""

import json
import logging
import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# Framework fallback data palette (used when no brand spec is configured).
_FRAMEWORK_DATA_COLORS = [
    "#0078D4",  # slot 0 — framework primary blue
    "#50E6FF",  # slot 1
    "#8661C5",  # slot 2
    "#F7630C",  # slot 3
    "#008575",  # slot 4
    "#E3008C",  # slot 5
    "#EF6950",  # slot 6
    "#FFB900",  # slot 7
]


def _derive_data_palette(primary: str, secondary: str) -> List[str]:
    """Build an 8-slot data color palette with brand primary/secondary at positions 0-1."""
    return [primary, secondary] + _FRAMEWORK_DATA_COLORS[2:]


def _resolve_template_family(page_block: Dict[str, Any]) -> str:
    """Derive the T1/T2/T3/T4 family letter from a page block in ux_layout_rules.

    Resolution order:
      1. ``template_variant``  e.g. "T2_DriverBridge"  → "T2"
      2. ``page_type``         e.g. "T2_Tactical_Variance" → "T2"
      3. Falls back to "T2" so existing reports keep working.
    """
    for field in ("template_variant", "page_type"):
        raw = (page_block.get(field) or "").strip()
        if raw:
            family = raw.split("_")[0].upper()
            if family in ("T1", "T2", "T3", "T4"):
                return family
    return "T2"


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
        self.tokens_root = self.page_templates_root / "tokens"   # machine-readable design tokens
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
        except Exception as exc:
            logger.warning("Failed to parse KPI catalog at %s: %s", self.kpi_catalog_path, exc)
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

    def _format_smart_narrative(self, bracket: Dict[str, Any], use_case_id: str) -> str:
        """Build a one-line Smart Narrative context text for the 300s detail page."""
        title = bracket.get("title") or use_case_id
        domain = bracket.get("domain") or ""
        orch = bracket.get("orchestration") or {}
        strategic_kpi_id = orch.get("strategic_kpi_id") or ""
        ux = bracket.get("ux_layout_rules") or {}
        p2 = ux.get("page_2_execution") or {}
        c300 = p2.get("component_300s") or {}
        grain = c300.get("evidence_grain") or "transaction"
        kpi_to_measure = self.load_kpi_id_to_measure_name_map()
        kpi_name = kpi_to_measure.get(strategic_kpi_id, strategic_kpi_id)
        domain_prefix = f"[{domain}] " if domain else ""
        text = f"{domain_prefix}{title}\nEvidence grain: {grain} | Strategic KPI: {kpi_name}"
        return text

    def _card_kpi_ids(self, bracket: Dict[str, Any]) -> List[str]:
        """KPI card band: component_3s lead + influencing KPIs, deduped, max 4."""
        ux = bracket.get("ux_layout_rules") or {}
        p1 = ux.get("page_1_summary") or {}
        c3s = p1.get("component_3s") if isinstance(p1, dict) else {}
        orch = bracket.get("orchestration") or {}
        lead = (c3s.get("kpi_id") if isinstance(c3s, dict) else None) or orch.get("strategic_kpi_id")
        influencing = orch.get("influencing_kpi_ids") or []
        out: List[str] = []
        seen: set = set()
        for kid in ([lead] if lead else []) + list(influencing):
            if not kid or kid in seen:
                continue
            seen.add(str(kid))
            out.append(str(kid))
            if len(out) >= 4:
                break
        return out

    def _format_trigger_condition(self, ac: Dict[str, Any]) -> Optional[str]:
        """Build a short human-readable trigger condition from action code trigger.levels."""
        trigger = ac.get("trigger") or {}
        if not isinstance(trigger, dict):
            return None
        levels = trigger.get("levels") or {}
        if not isinstance(levels, dict):
            return None
        # Use L2 as representative (RequiredIntervention) if present
        for level_key in ("L2", "L1", "L3"):
            level = levels.get(level_key)
            if not isinstance(level, dict):
                continue
            cond = level.get("condition") or {}
            if not isinstance(cond, dict):
                continue
            metric = cond.get("metric_kpi_id") or ""
            comp = cond.get("comparator") or ""
            th = cond.get("threshold")
            if isinstance(th, dict):
                val = th.get("value")
                unit = th.get("unit") or ""
            else:
                val, unit = th, ""
            if metric and comp and val is not None:
                comp_text = "<" if comp == "lt" else ">" if comp == "gt" else comp
                thresh = self._format_threshold_value(val, unit)
                return f"{metric} {comp_text} {thresh}".strip()
        return None

    @staticmethod
    def _format_threshold_value(val: Any, unit: str) -> str:
        unit = (unit or "").strip()
        if unit in ("%", "pp"):
            return f"{val}{unit}"
        if unit:
            return f"{val} {unit}"
        return str(val)

    def _format_impact_summary(self, ac: Dict[str, Any]) -> Optional[str]:
        """Build a short impact summary from action code impact / impact_valuation."""
        impact = ac.get("impact") or {}
        if isinstance(impact, dict) and impact.get("category"):
            cat = impact.get("category", "")
            val = ac.get("impact_valuation") or {}
            method = val.get("method", "") if isinstance(val, dict) else ""
            if method:
                return f"Impact: {cat}, {method}"
            return f"Impact: {cat}"
        val = ac.get("impact_valuation") or {}
        if isinstance(val, dict) and val.get("method"):
            return f"Impact: {val.get('method')}"
        return None

    def get_action_panel_content(self, use_case_id: str) -> Optional[str]:
        """
        Build Action Panel text from use case action codes (Bracket orchestration.action_code_ids).
        Loads each action code YAML and formats name, owner, steps, trigger condition, and impact.
        Respects payload_mode (full / summary / minimal) from component_300s.
        Returns None if no action codes or on error; caller uses placeholder then.
        """
        try:
            bracket = self.load_use_case_bracket(use_case_id)
            orch = bracket.get("orchestration") or {}
            ids = orch.get("action_code_ids") or []
            if not ids or not isinstance(ids, list):
                return None
            ux = bracket.get("ux_layout_rules") or {}
            p2 = ux.get("page_2_execution") or {}
            c300 = p2.get("component_300s") or {}
            payload_mode = (c300.get("payload_mode") or "full").strip().lower()
            lines = ["Recommended actions (from action codes)", ""]
            for ac_id in ids:
                if not isinstance(ac_id, str) or not ac_id.strip():
                    continue
                ac_id = ac_id.strip()
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
                lines.append(f"• {ac_id} — {name}")
                lines.append(f"  Owner: {owner}")
                if payload_mode != "minimal":
                    trigger_text = self._format_trigger_condition(ac)
                    if trigger_text:
                        lines.append(f"  Trigger: {trigger_text}")
                    impact_text = self._format_impact_summary(ac)
                    if impact_text:
                        lines.append(f"  {impact_text}")
                    # Phase D: add quantified impact range + confidence level
                    imp = ac.get("impact") or {}
                    if isinstance(imp, dict):
                        rng = imp.get("expected_range") or {}
                        if isinstance(rng, dict) and rng.get("value_low") is not None:
                            lo = rng.get("value_low")
                            hi = rng.get("value_high")
                            unit = (rng.get("unit") or "").strip()
                            range_str = f"{lo}–{hi} {unit}".strip()
                            lines.append(f"  Expected: {range_str}")
                        conf = imp.get("confidence") or {}
                        if isinstance(conf, dict) and conf.get("level"):
                            lines.append(f"  Confidence: {conf['level']}")
                if payload_mode == "full":
                    steps = []
                    exec_block = ac.get("operational_execution") or {}
                    if isinstance(exec_block, dict):
                        steps = exec_block.get("steps") or []
                    if isinstance(steps, list):
                        for s in steps[:3]:
                            if isinstance(s, str):
                                lines.append(f"  · {s}")
                    # Phase D: add first 2 gating rules as risk context
                    gating = ac.get("trigger", {}).get("gating_rules") if isinstance(ac.get("trigger"), dict) else []
                    if isinstance(gating, list) and gating:
                        lines.append(f"  ⚠ {gating[0]}")
                        if len(gating) > 1:
                            lines.append(f"  ⚠ {gating[1]}")
                lines.append("")
            if len(lines) <= 2:
                return None
            text = "\n".join(lines).strip()
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
        """Load tokens/visual_slot_mapping.yaml. Falls back to hardcoded mapping on error."""
        mapping_file = self.tokens_root / "visual_slot_mapping.yaml"
        if not mapping_file.exists():
            logger.warning("visual_slot_mapping.yaml not found at %s — using hardcoded fallback", mapping_file)
            return self._get_hardcoded_visual_slot_mapping()
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return data if isinstance(data, dict) else self._get_hardcoded_visual_slot_mapping()
        except Exception as exc:
            logger.warning("Failed to parse visual_slot_mapping.yaml: %s — using hardcoded fallback", exc)
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
        """Load tokens/layout_grid.yaml. Returns empty dict on error (caller uses defaults)."""
        token_file = self.tokens_root / "layout_grid.yaml"
        if not token_file.exists():
            logger.warning("layout_grid.yaml not found at %s — callers will use hardcoded defaults", token_file)
            return {}
        try:
            with open(token_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}
        except Exception as exc:
            logger.warning("Failed to parse layout_grid.yaml: %s", exc)
            return {}
    
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
        """Load tokens/color_semantics.yaml. Returns empty dict on error (caller uses defaults)."""
        token_file = self.tokens_root / "color_semantics.yaml"
        if not token_file.exists():
            logger.warning("color_semantics.yaml not found at %s — callers will use hardcoded defaults", token_file)
            return {}
        try:
            with open(token_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}
        except Exception as exc:
            logger.warning("Failed to parse color_semantics.yaml: %s", exc)
            return {}

    def _get_repo_showcase_id(self) -> Optional[str]:
        """Read showcase_id from repo_config.yaml at repo root. Returns None if not set."""
        config_path = self.repo_root / "repo_config.yaml"
        if not config_path.exists():
            return None
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
            sid = cfg.get("showcase_id")
            return str(sid) if sid else None
        except Exception as exc:
            logger.warning("Failed to read repo_config.yaml: %s", exc)
            return None

    def load_brand(self, showcase_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Load the brand spec for the active showcase.
        Returns None if no showcase configured (framework-only / fallback mode).

        Resolution order:
          1. Explicit showcase_id parameter (e.g. from UseCase_Bracket brand.brand_id)
          2. repo_config.yaml showcase_id
          3. None → caller uses framework semantic tokens only
        """
        sid = showcase_id or self._get_repo_showcase_id()
        if not sid:
            return None
        brand_path = self.repo_root / "showcases" / sid / "brand" / "brand_spec.yaml"
        if not brand_path.exists():
            logger.warning("Brand spec not found for showcase '%s' at %s", sid, brand_path)
            return None
        try:
            with open(brand_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as exc:
            logger.warning("Failed to load brand spec for '%s': %s", sid, exc)
            return None

    def resolve_color_tokens(self, showcase_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Merge framework semantic tokens with brand overrides.

        Token cascade:
          1. Framework defaults  (tokens/color_semantics.yaml  — semantic signals only)
          2. Brand semantic overrides  (brand_spec.yaml color.semantic.*)
          3. Brand palette injected as base["brand"]  (primary, secondary, data_colors)

        Returns the merged token dict. Callers access:
          tokens["semantic"]["positive/negative/warning/neutral"]
          tokens["brand"]["primary"], tokens["brand"]["secondary"], tokens["brand"]["data_colors"]
        """
        base = self.load_color_semantics()
        brand = self.load_brand(showcase_id)
        if not brand:
            return base

        color = brand.get("color", {})

        # Brand may override semantic signal colors (e.g. Aurora uses #D13438 for negative)
        brand_semantic = color.get("semantic", {})
        base_semantic = base.setdefault("semantic", {})
        for role in ("positive", "negative", "warning", "neutral"):
            role_block = brand_semantic.get(role)
            if isinstance(role_block, dict) and "color" in role_block:
                base_semantic[role] = role_block["color"]

        # Inject brand palette so callers don't have to re-load the brand spec
        primary = color.get("primary", "#0078D4")
        secondary = color.get("secondary", "#50E6FF")
        base["brand"] = {
            "primary":     primary,
            "secondary":   secondary,
            "data_colors": _derive_data_palette(primary, secondary),
        }
        return base

    def load_typography(self) -> Dict[str, Any]:
        """Load tokens/typography.yaml. Returns empty dict on error (caller uses defaults)."""
        token_file = self.tokens_root / "typography.yaml"
        if not token_file.exists():
            logger.warning("typography.yaml not found at %s — callers will use hardcoded defaults", token_file)
            return {}
        try:
            with open(token_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}
        except Exception as exc:
            logger.warning("Failed to parse typography.yaml: %s", exc)
            return {}
    
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
                vt = (item.get("visual_type") or "").strip().lower()
                if vt == "trend_line":
                    slots["needs_trend"] = True
                elif vt == "line_chart":
                    slots["needs_trend"] = True
                elif vt == "waterfall":
                    slots["needs_variance"] = True
                elif vt == "bar_chart_column":
                    # Clustered column is not a variance bridge; do not set needs_variance
                    pass
                elif vt in ("bar_chart", "bar_chart_horizontal", "bar_chart_vertical"):
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
            # Derive template family from template_variant (preferred) or page_type.
            # template_variant: "T2_DriverBridge" → family "T2"
            # page_type: "T2_Tactical_Variance" → family "T2"
            template = _resolve_template_family(p1)
            # Pass through for builder: exact visual_type per position (round-trip from layout editor).
            c3s = p1.get("component_3s")
            c30s = p1.get("component_30s")
            # Card KPI IDs: component_3s lead + influencing (deduped, max 4)
            card_kpi_ids = self._card_kpi_ids(bracket)
            kpi_to_measure = self.load_kpi_id_to_measure_name_map()
            card_measure_names = [kpi_to_measure.get(k, k) for k in card_kpi_ids]
            template_id = ux.get("page_template") or p1.get("template_id")
            layout_source = ux.get("layout_source")  # Figma URI: "figma://FILE_ID/NODE_ID" or Penpot URI: "penpot://FILE_ID/PAGE_ID/FRAME_ID"
            grid_blueprint = None
            # Figma layout takes precedence over static template_id when layout_source is set
            if layout_source and layout_source.startswith("figma://"):
                try:
                    from .figma_layout_bridge import FigmaLayoutBridge
                    bridge = FigmaLayoutBridge(figma_client=None)  # client injected at runtime if available
                    grid_blueprint = bridge.load_layout(layout_source)
                except Exception:
                    pass  # Fallback to static template below
            # Penpot layout as alternative when layout_source is a penpot:// URI
            elif layout_source and layout_source.startswith("penpot://"):
                try:
                    from .penpot_layout_bridge import PenpotLayoutBridge
                    bridge = PenpotLayoutBridge()
                    parsed = bridge.parse_layout_source(layout_source)
                    if parsed:
                        file_id, page_id, frame_id = parsed
                        # Try to load from file first (exported JSON), then fallback to URL
                        # Typical file path pattern: <project_root>/designs/penpot_exports/<file_id>_<page_id>_<frame_id>.json
                        export_path = self.repo_root / "designs" / "penpot_exports" / f"{file_id}_{page_id}_{frame_id}.json"
                        if export_path.exists():
                            grid_blueprint = bridge.load_from_file(str(export_path))
                        else:
                            # Fallback: try to load from Penpot REST API (requires token in environment)
                            import os
                            penpot_token = os.getenv("PENPOT_API_TOKEN")
                            if penpot_token:
                                api_url = f"https://penpot.app/api/rpc/command/file/get?file-id={file_id}"
                                grid_blueprint = bridge.load_from_url(api_url, token=penpot_token)
                except Exception:
                    pass  # Fallback to static template below
            if grid_blueprint is None and template_id:
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
                "layout_source": layout_source,
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
            # Derive template family from bracket page_type/template_variant; fall back to
            # T4 when action panel is explicitly configured, otherwise T2.
            template = _resolve_template_family(p2) or ("T4" if has_action_panel else "T2")
            slots["needs_detail_matrix"] = True
            slots["needs_prescriptive"] = has_action_panel
            # Use same KPI cards as overview (strategic + influencing) so detail cards have measure bindings
            card_kpi_ids = self._card_kpi_ids(bracket)
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
            evidence_columns = c300.get("evidence_columns")
            evidence_measures_raw = c300.get("evidence_measures")
            # --- Phase D: resolve evidence_columns to (table, col) tuples and measure names ---
            # Standard tokens map generic semantic names to Power BI table.column pairs
            EVIDENCE_DIM_TOKENS: Dict[str, tuple] = {
                "entity":            ("dim_org", "OrgName"),
                "period":            ("dim_date", "Date"),
                "customer":          ("dim_customer", "CustomerName"),
                "product":           ("dim_product", "ProductName"),
                "channel":           ("dim_org", "Channel"),
                "region":            ("dim_org", "Region"),
                "category":          ("dim_product", "Category"),
                "product_category":  ("dim_product", "Category"),
                "subcategory":       ("dim_product", "Subcategory"),
                "brand":             ("dim_product", "Brand"),
                "customer_segment":  ("dim_customer", "Segment"),
                "segment":           ("dim_customer", "Segment"),
                "country":           ("dim_org", "Country"),
                "org":               ("dim_org", "OrgName"),
            }
            resolved_dim_cols: list = []
            resolved_measures: list = []
            if isinstance(evidence_columns, list):
                for col in evidence_columns:
                    if not isinstance(col, str):
                        continue
                    token = col.strip().lower()
                    if token in EVIDENCE_DIM_TOKENS:
                        resolved_dim_cols.append(EVIDENCE_DIM_TOKENS[token])
                    else:
                        # Treat as KPI ID → resolve to DAX measure name
                        measure_name = kpi_to_measure.get(col, col)
                        resolved_measures.append(measure_name)
            # Explicit evidence_measures (if any) extend the resolved set
            if isinstance(evidence_measures_raw, list):
                for m in evidence_measures_raw:
                    if isinstance(m, str):
                        resolved_measures.append(kpi_to_measure.get(m, m))
            detail_matrix_columns = resolved_dim_cols   # list of (table, col) tuples
            detail_matrix_measures = resolved_measures  # list of DAX measure name strings
            smart_narrative_text = self._format_smart_narrative(bracket, use_case_id)
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
                "detail_matrix_columns": detail_matrix_columns,
                "detail_matrix_measures": detail_matrix_measures,
                "smart_narrative_text": smart_narrative_text,
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
