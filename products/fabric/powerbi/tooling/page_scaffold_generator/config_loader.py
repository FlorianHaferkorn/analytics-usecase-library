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

from .alt_text import bracket_locale, text_measures

# Threshold units that were KPI-ID suffixes before D-594 and were never displayed; same set as
# tooling/generator_core/ir/compiler.py SUFFIX_UNITS (tooling/tests/test_kpi_id_migration.py).
_SUFFIX_UNITS = frozenset({"amount", "count", "index", "pct", "days", "hours", "minutes", "units"})

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
        self._kpi_id_to_calc_type: Optional[Dict[str, str]] = None

    def _band_delta(self, bracket: Dict[str, Any]):
        """(Delta-Measure, kpi_id) fuer das KPI-Band oder None (R6.1c), aus comparison_measures."""
        from tooling.codegen.comparison_measures import band_delta
        d = self._target_model_dir(bracket)
        if d is None:
            return None
        return band_delta(bracket, self.measure_map_for_model(d),
                          set(self._model_symbols_for_dir(d).measure_names))

    def _comparison_refs(self, bracket: Dict[str, Any]) -> Dict[str, str]:
        """`<kpi_id>|<art>` -> Referenz-Measure im gebundenen Modell (R6.1).

        Namen und Existenzpruefung kommen aus tooling/codegen/comparison_measures.py, demselben
        Modul, das die Measures erzeugt -- zwei Stellen, die Namen bilden, waeren zwei Meinungen.
        """
        from tooling.codegen.comparison_measures import referenzen_fuer_bracket
        d = self._target_model_dir(bracket)
        if d is None:
            return {}
        return referenzen_fuer_bracket(bracket, self.measure_map_for_model(d),
                                       set(self._model_symbols_for_dir(d).measure_names))

    def load_kpi_good_is(self) -> Dict[str, str]:
        """KPI-ID -> `good_is` (higher/lower/band/zero) aus den Katalogdateien.

        KPIs ohne Richtung fehlen im Ergebnis: der Katalog behauptet dort keine (R6.3).
        """
        if "_good_is" in self.__dict__:
            return self._good_is
        out: Dict[str, str] = {}
        for f in sorted((self.repo_root / "core" / "kpi_catalog" / "kpis").glob("*.yaml")):
            try:
                d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
            except yaml.YAMLError:
                continue
            if isinstance(d, dict) and d.get("kpi_id") and d.get("good_is"):
                out[str(d["kpi_id"])] = str(d["good_is"])
        self._good_is = out
        return out

    def load_variance_kpi_ids(self) -> set:
        """KPI-IDs, die eine Abweichung sind (Katalogfeld `is_variance`). Bis D-594 am Teilstring
        `.vs_plan.`/`.delta_pct.` der ID erkannt; die ID traegt seither keine Bedeutung mehr."""
        if "_variance_ids" in self.__dict__:
            return self._variance_ids
        out = set()
        for f in sorted((self.repo_root / "core" / "kpi_catalog" / "kpis").glob("*.yaml")):
            try:
                d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
            except yaml.YAMLError:
                continue
            if isinstance(d, dict) and d.get("kpi_id") and d.get("is_variance") is True:
                out.add(str(d["kpi_id"]))
        self._variance_ids = out
        return out

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

    # --- Measure-Namen gegen das Zielmodell, nicht gegen den Katalog (23.09.2026) -------
    #
    # Der Katalog fuehrt den fachlichen Namen (`kpi_key`), das Modell den technischen, und
    # beide sind nicht immer gleich. Gemessen 23.09.2026 beim Neuerzeugen aller Reports:
    #
    #   * 5 der 109 KPIs mit Dictionary-Eintrag loesten auf einen Namen auf, den KEIN
    #     Modell definiert (`Plan Net Sales Amount` statt `Plan Sales Amount`).
    #   * 6 Bindungen zeigten auf ein Measure, das es nur in einem FREMDEN Modell gibt:
    #     FIN-001 bekam `OTIF %`, sein Finance-Modell fuehrt `OTIF % (FIN)`.
    #
    # Die zweite Sorte sieht der Referenz-Validator nicht, weil er die Measures aller
    # Modelle zusammenlegt. Im ausgelieferten dist/ fehlte beides nur, weil es von Hand
    # nachgezogen war -- beim naechsten Lauf des Generators waere es zurueckgekommen.
    #
    # Die Bindung KPI -> Measure steht im Measure-Dictionary (`kpi_id_ref`). Aufgeloest
    # wird gegen das Modell, an das der Report bindet (`../<domain>.SemanticModel`).
    # Korrigiert wird nur, was dort nachweislich fehlt, und nur, wenn genau ein
    # Dictionary-Name dort existiert. Mehr als ein Treffer bleibt stehen und faellt im
    # Validator auf: eine Wahl zwischen zwei Namen ist keine Korrektur, sondern ein Raten.

    def _target_model_dir(self, bracket: Dict[str, Any]) -> Optional[Path]:
        """Das Modell, an das der Report bindet.

        Erste Quelle ist die `definition.pbir` des Reports: sie sagt, woran er tatsaechlich
        haengt. `domain` taugt dafuer nur ersatzweise -- gemessen 23.09.2026 tragen Brackets
        dort Werte wie `Experience / Service` oder `Executive / Cross-Functional`, und XD-003
        (`Executive`) bindet an das Experience-Modell. Ein Pfad aus `domain` haette in
        diesen Faellen still ins Leere gegriffen.
        """
        dist = self.repo_root / "products" / "fabric" / "powerbi" / "dist"
        uc_id = (bracket or {}).get("id")
        uc_dir = self._resolve_use_case_dir(uc_id) if uc_id else None
        if uc_dir is not None:
            pbir = dist / f"{uc_dir.name}.Report" / "definition.pbir"
            if pbir.exists():
                ref = ((json.loads(pbir.read_text(encoding="utf-8")).get("datasetReference") or {})
                       .get("byPath") or {}).get("path")
                if ref:
                    d = (pbir.parent / ref).resolve()
                    if d.exists():
                        return d
        domain = str((bracket or {}).get("domain") or "").split("/")[0].strip()
        d = dist / f"{domain}.SemanticModel"
        return d if domain and d.exists() else None

    def _model_symbols_for(self, bracket: Dict[str, Any]):
        return self._model_symbols_for_dir(self._target_model_dir(bracket))

    def _model_symbols_for_dir(self, d: Optional[Path]):
        from tooling.report_quality.dax_reference_validator import ModelSymbols, TableSymbols, parse_tmdl_table
        cache = self.__dict__.setdefault("_symbols_cache", {})
        if d in cache:
            return cache[d]
        sym = ModelSymbols()
        if d is not None:
            for t in sorted((d / "definition" / "tables").glob("*.tmdl")):
                tab = parse_tmdl_table(t)
                if tab:
                    sym.tables.setdefault(tab.name, TableSymbols(tab.name))
                    sym.tables[tab.name].columns |= tab.columns
                    sym.tables[tab.name].measures.update(tab.measures)
        cache[d] = sym
        return sym

    def _dictionary_measure_names(self) -> Dict[str, set]:
        if "_dict_names" in self.__dict__:
            return self._dict_names
        out: Dict[str, set] = {}
        for f in sorted((self.repo_root / "core" / "semantic_models" / "domains").glob(
                "*/measures/*.yaml")):
            try:
                d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
            except yaml.YAMLError:
                continue
            if isinstance(d, dict) and d.get("kpi_id_ref") and d.get("measure_name"):
                out.setdefault(str(d["kpi_id_ref"]), set()).add(str(d["measure_name"]))
        self._dict_names = out
        return out

    def measure_map_for(self, bracket: Dict[str, Any]) -> Dict[str, str]:
        """KPI-ID -> Measure-Name, wie das Zielmodell dieses Brackets ihn fuehrt."""
        return self.measure_map_for_model(self._target_model_dir(bracket))

    def measure_map_for_model(self, model_dir: Optional[Path]) -> Dict[str, str]:
        """KPI-ID -> Measure-Name, wie das Modell unter `model_dir` ihn fuehrt.

        Dieselbe Aufloesung fuer Report-Visuals und fuer die Action-Trigger
        (`tooling/codegen/action_trigger_dax.py`); zwei Aufloesungen waeren zwei Meinungen.
        """
        result = dict(self.load_kpi_id_to_measure_name_map())
        definiert = self._model_symbols_for_dir(model_dir).measure_names
        if not definiert:
            return result                  # kein Modell zur Hand: nichts behaupten
        dictionary = self._dictionary_measure_names()
        for kpi_id in sorted(set(result) | set(dictionary)):
            if result.get(kpi_id) in definiert:
                continue
            basis = set(dictionary.get(kpi_id, ())) | ({result[kpi_id]} if kpi_id in result else set())
            treffer = sorted(n for n in basis if n in definiert)
            if not treffer:
                # Domaenen-Variante: `DSO Days` heisst im Finance-Modell `DSO Days (FIN)`.
                # Die Konvention steht in .claude/rules/connect-pbid.md; hier gilt sie nur,
                # wenn das Modell genau EINEN solchen Namen fuehrt.
                treffer = sorted(n for n in definiert
                                 if any(n.startswith(b + " (") and n.endswith(")") for b in basis))
            if len(treffer) == 1:
                result[kpi_id] = treffer[0]
        return result

    def _model_columns(self, bracket: Dict[str, Any]) -> Optional[set]:
        """Alle `tabelle.Spalte` des Zielmodells; None, wenn kein Modell zur Hand ist."""
        sym = self._model_symbols_for(bracket)
        if not sym.tables:
            return None
        return {f"{t}.{c}" for t, tab in sym.tables.items() for c in tab.columns}

    def _pick_column(self, token: str, eintrag: tuple, bracket: Dict[str, Any]) -> tuple:
        """Den ersten Kandidaten, den das Zielmodell fuehrt.

        Ein Eintrag ist entweder ein Paar (tabelle, spalte) oder eine geordnete Liste
        solcher Paare. Bis 23.09.2026 galt ein Paar fuer alle fuenf Modelle; SCM-002
        bekam so `dim_customer.CustomerName`, das SupplyChain-Modell kennt nur
        `dim_org.Customer`. Fuehrt das Modell keinen Kandidaten, bricht der Lauf ab --
        eine Spalte ins Leere ist derselbe Fehler wie eine Measure ins Leere.
        """
        kandidaten = eintrag if isinstance(eintrag[0], tuple) else (eintrag,)
        spalten = self._model_columns(bracket)
        if spalten is None:
            return kandidaten[0]
        for t, c in kandidaten:
            if f"{t}.{c}" in spalten:
                return (t, c)
        raise ValueError(
            f"evidence_columns: Token {token!r} -- keiner der Kandidaten "
            f"{[f'{t}.{c}' for t, c in kandidaten]} existiert im Zielmodell "
            f"{self._target_model_dir(bracket)}.")

    def _table_column(self, ref: str, bracket: Dict[str, Any]) -> Optional[tuple]:
        """`tabelle.Spalte` -> (tabelle, Spalte), wenn das Zielmodell die Spalte fuehrt.

        None, wenn der Teil vor dem Punkt keine Tabelle dieses Modells ist (dann ist es
        etwa eine KPI-Kennung oder ein roher Measure-Name). Kennt das Modell die Tabelle,
        aber nicht die Spalte, bricht der Lauf ab: das ist ein Tippfehler, und still daraus
        eine Measure zu machen ist genau der Fehler, den dieser Zweig schliesst.
        """
        if "." not in ref:
            return None
        tabelle, spalte = ref.split(".", 1)
        sym = self._model_symbols_for(bracket)
        if tabelle not in sym.table_names:
            return None
        if not sym.has_column(tabelle, spalte):
            raise ValueError(
                f"evidence_columns: {ref!r} -- Tabelle {tabelle!r} existiert, die Spalte "
                f"{spalte!r} nicht. Vorhanden: {sorted(sym.tables[tabelle].columns)}")
        return (tabelle, spalte)

    def load_kpi_id_to_calc_type_map(self) -> Dict[str, str]:
        """
        Load KPI catalog and return mapping kpi_id -> calc_type (amount/rate/ratio/
        count/percentage/quantity/index -- see validate_kpi_catalog.ps1's
        $allowedCalc). Used by R2.2's ONE_MESSAGE_PER_CHART design rule to check that
        a component_30s entry's declared `unit` (R2.1) matches every referenced KPI's
        own governed calc_type. Same chunk-based parsing technique as
        load_kpi_id_to_measure_name_map (the catalog's YAML block is not always valid
        as a single document).
        """
        if self._kpi_id_to_calc_type is not None:
            return self._kpi_id_to_calc_type
        result: Dict[str, str] = {}
        if not self.kpi_catalog_path.exists():
            return result
        try:
            content = self.kpi_catalog_path.read_text(encoding="utf-8")
            match = re.search(r"```yaml\s*\n(.*?)```", content, re.DOTALL)
            if not match:
                return result
            block = match.group(1)
            chunk_starts = list(re.finditer(r"(?m)^\s*-\s*kpi_id\s*:\s*([^\s#\r\n]+)", block))
            for i, mo in enumerate(chunk_starts):
                kpi_id = mo.group(1).strip()
                start = mo.start()
                end = chunk_starts[i + 1].start() if i + 1 < len(chunk_starts) else len(block)
                chunk = block[start:end]
                calc_type_m = re.search(r'(?m)^\s*calc_type\s*:\s*(?:"([^"]*)"|([^\r\n#]+))', chunk)
                calc_type = (calc_type_m.group(1) or (calc_type_m.group(2) or "").strip()) if calc_type_m else None
                if calc_type:
                    result[kpi_id] = calc_type.strip().lower()
            self._kpi_id_to_calc_type = result
        except Exception as exc:
            logger.warning("Failed to parse KPI catalog calc_type at %s: %s", self.kpi_catalog_path, exc)
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

    # R2.3-Fund follow-up: data_contract_ref -> domain semantic model suffix, verified
    # against the real 'Narrative Text (<SUFFIX>)'/'Active Actions Text (<SUFFIX>)'
    # measures in each *.SemanticModel/definition/tables/_Measures.tmdl (not
    # invented) -- these are domain-level shared measures (one per
    # *.SemanticModel, not per use case), cross-checked against the real,
    # committed dist/ Smart_Narrative and ActionPanel visual.json bindings for
    # COM-002 (COM), XD-003 (XD, data_contract=executive.yaml), and FIN-002 (FIN).
    _DATA_CONTRACT_TO_DOMAIN_SUFFIX: Dict[str, str] = {
        "commercial_sales.yaml": "COM",
        "finance.yaml": "FIN",
        "operations.yaml": "OPS",
        "supply_chain.yaml": "SCM",
        "experience.yaml": "XD",
        "executive.yaml": "XD",
    }

    def _domain_measure_suffix(self, bracket: Dict[str, Any]) -> Optional[str]:
        """Resolve the '(SUFFIX)' domain-measure-name suffix for this Bracket's
        Smart_Narrative/ActionPanel binding, from overrides.data_contract_ref.
        Returns None for an unmapped/missing data_contract_ref (e.g. XD-004's
        governance.yaml -- not yet verified against a real semantic model;
        callers fall back to the synthesized-text path rather than guess)."""
        ref = (bracket.get("overrides") or {}).get("data_contract_ref") or ""
        filename = ref.rsplit("/", 1)[-1]
        suffix = self._DATA_CONTRACT_TO_DOMAIN_SUFFIX.get(filename)
        if suffix:
            return suffix
        # Rueckfall, seit 23.09.2026 gemessen statt geraten: das Modell, an das der Report
        # bindet, fuehrt genau EINE `Narrative Text (<SUFFIX>)`-Measure. Fuer XD-004
        # (governance.yaml, bisher ohne Zuordnung) ist das `XD` im Experience-Modell --
        # genau die Bindung, die dist/ von Hand trug. Mehr oder weniger als ein Treffer:
        # kein Suffix, der Aufrufer faellt wie bisher auf den Text zurueck.
        kandidaten = sorted({
            m[len("Narrative Text ("):-1]
            for m in self._model_symbols_for(bracket).measure_names
            if m.startswith("Narrative Text (") and m.endswith(")")
        })
        return kandidaten[0] if len(kandidaten) == 1 else None

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
        kpi_to_measure = self.measure_map_for(bracket)
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
                thresh = self._format_threshold_value(val, unit, metric)
                return f"{metric} {comp_text} {thresh}".strip()
        return None

    @staticmethod
    def _format_threshold_value(val: Any, unit: str, metric: str = "") -> str:
        # Unit-class words stay hidden as while they were KPI-ID suffixes (D-594); same set
        # as the IR compiler (tooling/generator_core/ir/compiler.py SUFFIX_UNITS).
        unit = (unit or "").strip()
        if unit in _SUFFIX_UNITS:
            unit = ""
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
                # Registry-Schreibweisen (ADR-0018) auf die hier verwendeten Alt-Token
                # zurueckfuehren. Ohne diese Zeile faellt jede umbenannte Deklaration
                # durch alle elif-Zweige und setzt STILL keinen einzigen Slot-Bedarf.
                vt = {"kpi_card_with_delta": "kpi_card",
                      "horizontal_bar_chart": "bar_chart_horizontal",
                      "column_chart": "bar_chart_column",
                      "waterfall_chart": "waterfall",
                      "scatter_plot": "scatter"}.get(vt, vt)
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
            kpi_to_measure = self.measure_map_for(bracket)
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
            # R2.3: render big_idea verbatim in the Header (Zone 0) only once the bracket
            # has opted into the R2.1 intent layer (intent_rules_version: 2) -- legacy
            # brackets keep their current (Header-less) output unchanged.
            intent_rules_version = ux.get("intent_rules_version")
            big_idea_text = p1.get("big_idea") if intent_rules_version == 2 else None
            # title_policy: nur wer seine Aussagen wertgeprueft hat, bekommt sie als Titel
            # (`title_statements_verified: true`). Bis 23.09.2026 war das der Standard -- 15 von
            # 20 Brackets behaupteten damit eine Pruefung, die nie stattfand, und 22 von 38
            # Charttiteln stellten einen Befund fest, der an keinen Daten hing (R6.2). Jetzt
            # fuehrt die Frage, die Aussage steht als "Expected finding --" darunter.
            assert_statement_titles = bool(ux.get("title_statements_verified", False))
            # Titelblock (A-34, IBCS UN 2.2): wer / was / wann aus page_1_summary.title_lines.
            # Nicht abgeleitet: Berichtseinheit und Zeitraum kennt nur der Bracket bzw. Kunde.
            from .title_policy import check_key_message_position, frame_key_message, title_lines_from
            title_lines = title_lines_from(p1.get("title_lines"))
            # Position der Kernaussage (UN 2.1) aus dem Bracket; unbekannt = Fehler.
            key_message_position = check_key_message_position(p1.get("key_message_position"))
            # Kopfzeile nach derselben Regel (R6.2): ungeprueft fuehrt die Frage der Seite,
            # die Big Idea folgt als Erwartung -- auch ohne Frage gerahmt (A-34; bis 08.10.2026
            # stand sie dann ungerahmt da). design_rules BIG_IDEA_HEADER_ZONE prueft, dass sie
            # woertlich enthalten bleibt.
            big_idea_text = frame_key_message(big_idea_text, p1.get("decision_question"),
                                              value_verified=assert_statement_titles)
            # Gap A opt-in: split the vs-plan variance into its own sign-coloured KPI card.
            # Default False so only opted-in reports (COM-002 reference) change; the rest keep
            # their single KPI band until deliberately migrated.
            semantic_delta_cards = bool(ux.get("semantic_delta_cards", False))
            return {
                "name": "overview",
                "model_columns": self._model_columns(bracket),
                "layer": [3, 30],
                "template": template,
                "template_id": template_id,
                "layout_source": layout_source,
                "grid_blueprint": grid_blueprint,
                "report_canvas": report_canvas,
                # Sprache der vom Generator formulierten Texte (Alt-Text), alt_text.bracket_locale.
                "report_locale": bracket_locale(bracket),
                # Text-Measures des gebundenen Modells (formatString @) fuer den Kachel-Alt-Text.
                "text_measures": text_measures(self._target_model_dir(bracket)),
                "needs_action_panel": False,
                "slots": slots,
                "component_3s": dict(c3s) if isinstance(c3s, dict) else {},
                "component_30s": list(c30s) if isinstance(c30s, list) else [],
                "card_kpi_ids": card_kpi_ids,
                "card_measure_names": card_measure_names,
                "kpi_id_to_measure_name": kpi_to_measure,
                "kpi_good_is": self.load_kpi_good_is(),
                "variance_kpi_ids": self.load_variance_kpi_ids(),
                "comparison_refs": self._comparison_refs(bracket),
                "kpi_band_delta": self._band_delta(bracket),
                "intent_rules_version": intent_rules_version,
                "big_idea_text": big_idea_text,
                "assert_statement_titles": assert_statement_titles,
                "title_lines": title_lines,
                "key_message_position": key_message_position,
                "semantic_delta_cards": semantic_delta_cards,
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
            kpi_to_measure = self.measure_map_for(bracket)
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
                # Zwei Modelle, zwei Orte: Commercial fuehrt dim_customer, SupplyChain den
                # Kunden als dim_org.Customer. Aufgeloest wird unten gegen das Zielmodell.
                "customer":          (("dim_customer", "CustomerName"), ("dim_org", "Customer")),
                "product":           ("dim_product", "ProductName"),
                "channel":           ("dim_org", "Channel"),
                "region":            ("dim_org", "Region"),
                "category":          ("dim_product", "Category"),
                "product_category":  ("dim_product", "Category"),
                "subcategory":       ("dim_product", "Subcategory"),
                "sku":               ("dim_product", "ProductCode"),
                "brand":             ("dim_product", "Brand"),
                "customer_segment":  ("dim_customer", "Segment"),
                "segment":           ("dim_customer", "Segment"),
                "country":           ("dim_org", "Country"),
                "org":               ("dim_org", "OrgName"),
                # R2.4 (Cut C2): additions verified against the real, existing dim
                # tables in each domain's *.SemanticModel/definition/tables/ TMDL --
                # not invented. Tokens with no real backing table anywhere in the
                # semantic model (e.g. "plant", "line", "shift", "location",
                # "agent_group") are intentionally NOT added here; brackets using
                # them are curated onto a real token instead (see per-bracket
                # ledger notes), not silently passed through to become a bogus
                # _Measures.<token> reference (the same failure class as R2.3's
                # "sku" bug, just for tokens this dict never covered).
                "asset":             ("dim_asset", "AssetName"),        # Operations.SemanticModel
                "asset_class":       ("dim_asset", "AssetClass"),
                "criticality":       ("dim_asset", "Criticality"),
                "queue":             ("dim_case_queue", "QueueName"),   # Experience.SemanticModel
                "issue_type":        ("dim_issue_type", "IssueType"),
                "severity":          ("dim_issue_type", "Severity"),
                "promotion":         ("dim_promo", "PromoName"),        # Commercial.SemanticModel
                "promo_type":        ("dim_promo", "Promo Type"),
                "mechanic":          ("dim_promo", "Promo Mechanic"),
                "lane":              ("dim_lane", "Mode"),              # SupplyChain.SemanticModel
                "abc_class":         ("dim_product", "ABC_Class"),
                "xyz_class":         ("dim_product", "XYZ_Class"),
            }
            resolved_dim_cols: list = []
            resolved_measures: list = []
            # R2.4 follow-up: an evidence_columns token shaped like a dimension
            # reference (bare lowercase snake_case word -- the exact shape of
            # every real EVIDENCE_DIM_TOKENS key) that is neither a known dim
            # token nor a known governed KPI id is almost certainly a typo'd or
            # not-yet-modeled dimension (e.g. "plant", "agent_group") -- not a
            # deliberate raw-measure-name escape hatch (those are always
            # Title-Case-with-spaces DAX names, e.g. "Plan Sales Amount", and a
            # dotted KPI id like "KPI-COM-005" never matches this
            # shape either). Silently passing it through would mint a bogus
            # _Measures.<token> reference -- the same failure class R2.3/R2.4
            # found and fixed case-by-case ("sku", "asset", "queue", ...); this
            # closes the class instead of the individual instances.
            _DIM_LIKE_TOKEN = re.compile(r"^[a-z][a-z0-9_]*$")
            unresolved_dim_like_tokens: list = []
            if isinstance(evidence_columns, list):
                for col in evidence_columns:
                    if not isinstance(col, str):
                        continue
                    token = col.strip().lower()
                    if token in EVIDENCE_DIM_TOKENS:
                        resolved_dim_cols.append(self._pick_column(token, EVIDENCE_DIM_TOKENS[token], bracket))
                    elif col in kpi_to_measure:
                        resolved_measures.append(kpi_to_measure[col])
                    elif self._table_column(col, bracket) is not None:
                        # `dim_org.Region`: eine Spalte, ausdruecklich benannt. Bis zum
                        # 23.09.2026 fiel diese Form in den Measure-Zweig darunter und wurde
                        # zu `_Measures.'dim_org.Region'` -- gemessen an COM-001 (2 Spalten)
                        # und XD-004 (6). Aufgeloest wird nur gegen eine Spalte, die das
                        # Modell tatsaechlich fuehrt.
                        resolved_dim_cols.append(self._table_column(col, bracket))
                    elif _DIM_LIKE_TOKEN.match(token):
                        unresolved_dim_like_tokens.append(col)
                    else:
                        # Genuine escape hatch: raw DAX measure name, used as-is
                        # (same "no catalog ID exists yet" pattern component_30s
                        # kpi_ids already supports).
                        resolved_measures.append(col)
            if unresolved_dim_like_tokens:
                raise ValueError(
                    f"{use_case_id}: component_300s.evidence_columns references "
                    f"unresolvable dimension token(s) {unresolved_dim_like_tokens} -- "
                    "not in EVIDENCE_DIM_TOKENS and not a governed KPI id in the "
                    "catalog. Either add a verified (table, column) entry to "
                    "config_loader.py's EVIDENCE_DIM_TOKENS (grounded against a "
                    "real *.SemanticModel/definition/tables/dim_*.tmdl), or "
                    "replace the token with a real dimension/KPI reference."
                )
            # Explicit evidence_measures (if any) extend the resolved set
            if isinstance(evidence_measures_raw, list):
                for m in evidence_measures_raw:
                    if isinstance(m, str):
                        resolved_measures.append(kpi_to_measure.get(m, m))
            detail_matrix_columns = resolved_dim_cols   # list of (table, col) tuples
            detail_matrix_measures = resolved_measures  # list of DAX measure name strings
            smart_narrative_text = self._format_smart_narrative(bracket, use_case_id)
            # R2.3-Fund follow-up: real dist/ binds Smart_Narrative/ActionPanel to
            # governed domain-level DAX measures (cardVisual + Data role), not a
            # generator-synthesized literal string -- see _domain_measure_suffix's
            # docstring. None when unresolvable; callers fall back to the
            # synthesized text (smart_narrative_text / action_panel_content).
            _domain_suffix = self._domain_measure_suffix(bracket)
            narrative_measure_name = f"Narrative Text ({_domain_suffix})" if _domain_suffix else None
            active_actions_measure_name = f"Active Actions Text ({_domain_suffix})" if _domain_suffix else None
            _lr = f"Last Refresh ({_domain_suffix})" if _domain_suffix else None
            last_refresh_measure_name = _lr if _lr in self._model_symbols_for(bracket).measure_names else None

            # R2.3: sort_by/top_n/highlight_rule (R2.1 fields) -> generated Detail_Matrix
            # sortDefinition/TopN filter/data-bar formatting, gated the same way as the
            # Header (intent_rules_version: 2 only -- legacy brackets are unaffected).
            intent_rules_version = ux.get("intent_rules_version")
            detail_matrix_sort_by = None
            detail_matrix_top_n = None
            detail_matrix_highlight_rule = None
            detail_matrix_topn_field = detail_matrix_columns[-1] if detail_matrix_columns else None
            if intent_rules_version == 2:
                raw_sort_by = c300.get("sort_by")
                if isinstance(raw_sort_by, dict) and raw_sort_by.get("measure"):
                    measure_ref = raw_sort_by["measure"]
                    detail_matrix_sort_by = {
                        "measure": kpi_to_measure.get(measure_ref, measure_ref),
                        "direction": raw_sort_by.get("direction", "descending"),
                    }
                raw_top_n = c300.get("top_n")
                if isinstance(raw_top_n, int):
                    detail_matrix_top_n = raw_top_n
                raw_highlight = c300.get("highlight_rule")
                if isinstance(raw_highlight, dict) and raw_highlight.get("column"):
                    column_ref = raw_highlight["column"]
                    detail_matrix_highlight_rule = {
                        "measure": kpi_to_measure.get(column_ref, column_ref),
                        "type": raw_highlight.get("type", "data_bar"),
                    }

            return {
                "name": "detail",
                "model_columns": self._model_columns(bracket),
                "layer": [300],
                "template": template,
                "template_id": template_id,
                "grid_blueprint": grid_blueprint,
                "report_canvas": report_canvas,
                # Sprache der vom Generator formulierten Texte (Alt-Text), alt_text.bracket_locale.
                "report_locale": bracket_locale(bracket),
                # Text-Measures des gebundenen Modells (formatString @) fuer den Kachel-Alt-Text.
                "text_measures": text_measures(self._target_model_dir(bracket)),
                "needs_action_panel": has_action_panel,
                "slots": slots,
                "card_kpi_ids": card_kpi_ids,
                "card_measure_names": card_measure_names,
                "kpi_id_to_measure_name": kpi_to_measure,
                "kpi_good_is": self.load_kpi_good_is(),
                "variance_kpi_ids": self.load_variance_kpi_ids(),
                "comparison_refs": self._comparison_refs(bracket),
                "kpi_band_delta": self._band_delta(bracket),
                "detail_matrix_columns": detail_matrix_columns,
                "detail_matrix_measures": detail_matrix_measures,
                "smart_narrative_text": smart_narrative_text,
                "narrative_measure_name": narrative_measure_name,
                "active_actions_measure_name": active_actions_measure_name,
                "last_refresh_measure_name": last_refresh_measure_name,
                "intent_rules_version": intent_rules_version,
                "detail_matrix_sort_by": detail_matrix_sort_by,
                "detail_matrix_top_n": detail_matrix_top_n,
                "detail_matrix_highlight_rule": detail_matrix_highlight_rule,
                "detail_matrix_topn_field": detail_matrix_topn_field,
                "assert_statement_titles": bool(ux.get("title_statements_verified", False)),
            }

        raise ValueError(f"Page {page_name} not supported (expected 'overview' or 'detail')")
    
    def validate_theme_exists(self, theme_name: str) -> bool:
        """
        Validate that theme file exists.
        
        Args:
            theme_name: Theme name (e.g., "Brand Blue__Monochromatic__Light__118DFF"; '#' optional)
        
        Returns:
            True if theme exists, False otherwise
        """
        # Vendored engine output (themes/) and ALUCA-owned local output (themes_local/),
        # resolved relative to this loader's repo_root — see theme_paths.py.
        from products.fabric.powerbi.tooling.theme_paths import find_theme

        powerbi = self.repo_root / "products" / "fabric" / "powerbi"
        return find_theme(theme_name, roots=(powerbi / "themes_local", powerbi / "themes")) is not None
