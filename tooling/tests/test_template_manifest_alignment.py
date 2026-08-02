"""CI gate: every UseCase_Bracket.yaml that declares template_variant resolves
to a valid entry in core/templates/page_templates/template_manifest.yaml.

This test enforces Gate 1 from IMPLEMENTATION_ROADMAP.md:
  "CI gate rejects a bracket that references a non-existent template variant."

The field is optional (non-breaking) — brackets without template_variant are skipped.
"""
from __future__ import annotations

import pytest
import yaml
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
USECASES_ROOT = REPO_ROOT / "core" / "usecases"
MANIFEST_PATH = REPO_ROOT / "core" / "templates" / "page_templates" / "template_manifest.yaml"
VISUAL_REGISTRY_PATH = REPO_ROOT / "core" / "templates" / "page_templates" / "visual_registry.yaml"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_manifest() -> dict:
    return yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))


def _load_registry() -> dict:
    return yaml.safe_load(VISUAL_REGISTRY_PATH.read_text(encoding="utf-8"))


def _all_brackets() -> list[Path]:
    return list(USECASES_ROOT.rglob("UseCase_Bracket.yaml"))


def _valid_variant_ids(manifest: dict) -> set[str]:
    ids: set[str] = set()
    for family in manifest.get("page_families", []):
        for variant in family.get("variants", []):
            ids.add(variant["variant_id"])
    return ids


def _valid_block_ids(registry: dict) -> set[str]:
    return {block["block_id"] for block in registry.get("information_blocks", [])}


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestManifestFilesExist:
    def test_template_manifest_exists(self):
        assert MANIFEST_PATH.exists(), (
            "core/templates/page_templates/template_manifest.yaml must exist. "
            "See REPORT_ENGINE_TARGET_ARCHITECTURE.md §2 (primary gap)."
        )

    def test_visual_registry_exists(self):
        assert VISUAL_REGISTRY_PATH.exists(), (
            "core/templates/page_templates/visual_registry.yaml must exist. "
            "See REPORT_ENGINE_TARGET_ARCHITECTURE.md §2."
        )

    def test_manifest_is_valid_yaml(self):
        manifest = _load_manifest()
        assert isinstance(manifest, dict), "template_manifest.yaml must parse as a YAML mapping"
        assert "page_families" in manifest, "template_manifest.yaml must have a 'page_families' key"

    def test_registry_is_valid_yaml(self):
        registry = _load_registry()
        assert isinstance(registry, dict), "visual_registry.yaml must parse as a YAML mapping"
        assert "information_blocks" in registry, "visual_registry.yaml must have an 'information_blocks' key"

    def test_manifest_has_all_four_families(self):
        manifest = _load_manifest()
        family_ids = {f["family_id"] for f in manifest.get("page_families", [])}
        assert {"T1", "T2", "T3", "T4"} == family_ids, (
            f"template_manifest.yaml must define exactly T1, T2, T3, T4 families. Got: {family_ids}"
        )

    def test_registry_has_required_blocks(self):
        registry = _load_registry()
        block_ids = _valid_block_ids(registry)
        required = {
            "status_signal", "time_trend", "variance_explanation",
            "entity_ranking", "exception_list", "structural_mix",
            "prescriptive_action", "detail_matrix", "root_cause_context",
        }
        missing = required - block_ids
        assert not missing, (
            f"visual_registry.yaml is missing required information blocks: {missing}"
        )


class TestBracketVariantAlignment:
    """For every bracket that declares template_variant, the value must resolve
    to a valid variant in template_manifest.yaml."""

    def test_declared_variants_resolve(self):
        manifest = _load_manifest()
        valid = _valid_variant_ids(manifest)
        brackets = _all_brackets()

        errors: list[str] = []
        for bracket_path in brackets:
            try:
                doc = yaml.safe_load(bracket_path.read_text(encoding="utf-8"))
            except yaml.YAMLError as e:
                # YAML parse errors are caught by other tests; skip here
                continue

            if not isinstance(doc, dict):
                continue

            ux = doc.get("ux_layout_rules", {})

            # Check page_1_summary
            p1 = ux.get("page_1_summary", {})
            variant = p1.get("template_variant")
            if variant and variant not in valid:
                errors.append(
                    f"{bracket_path.relative_to(REPO_ROOT)}: "
                    f"page_1_summary.template_variant '{variant}' is not in template_manifest.yaml. "
                    f"Valid variants: {sorted(valid)}"
                )

            # Check page_2_execution
            p2 = ux.get("page_2_execution", {})
            variant2 = p2.get("template_variant")
            if variant2 and variant2 not in valid:
                errors.append(
                    f"{bracket_path.relative_to(REPO_ROOT)}: "
                    f"page_2_execution.template_variant '{variant2}' is not in template_manifest.yaml. "
                    f"Valid variants: {sorted(valid)}"
                )

        assert not errors, (
            "UseCase_Bracket.yaml files reference undefined template_variants:\n"
            + "\n".join(f"  - {e}" for e in errors)
        )

    def test_t4_variants_require_action_codes(self):
        """T4 variants require at least one action code. Flag brackets that
        declare T4_* template_variant but have no action_code_ids."""
        manifest = _load_manifest()
        valid = _valid_variant_ids(manifest)
        t4_variants = {v for v in valid if v.startswith("T4_")}
        brackets = _all_brackets()

        warnings: list[str] = []
        for bracket_path in brackets:
            try:
                doc = yaml.safe_load(bracket_path.read_text(encoding="utf-8"))
            except yaml.YAMLError:
                continue
            if not isinstance(doc, dict):
                continue

            ux = doc.get("ux_layout_rules", {})
            p1 = ux.get("page_1_summary", {})
            variant = p1.get("template_variant", "")
            if variant in t4_variants:
                action_ids = doc.get("orchestration", {}).get("action_code_ids", [])
                if not action_ids:
                    warnings.append(
                        f"{bracket_path.relative_to(REPO_ROOT)}: "
                        f"template_variant '{variant}' is T4 (prescriptive) "
                        f"but orchestration.action_code_ids is empty. "
                        f"Author the Action Code before using T4 variants."
                    )

        assert not warnings, (
            "T4 template variants require action codes:\n"
            + "\n".join(f"  - {w}" for w in warnings)
        )


class TestBracketSlotManifestAlignment:
    """When template_variant is set, Main_2 visual_type must match manifest information_block."""

    _VARIANCE_VISUAL_TYPES = {"waterfall", "waterfall_chart", "variance_bar"}
    _RANKING_VISUAL_TYPES = {"bar_chart", "bar_chart_horizontal", "bar_chart_column", "bar_chart_vertical"}
    _TREND_VISUAL_TYPES = {"line_chart", "trend_line", "area_chart"}

    def _slot_block(self, manifest: dict, variant_id: str, slot_id: str, page: str = "overview_slots") -> str | None:
        for family in manifest.get("page_families", []):
            for variant in family.get("variants", []):
                if variant.get("variant_id") != variant_id:
                    continue
                for slot in variant.get(page, []):
                    if slot.get("slot_id") == slot_id:
                        return slot.get("information_block")
        return None

    def test_t2_driver_bridge_main2_uses_variance_visual(self):
        manifest = _load_manifest()
        expected_block = self._slot_block(manifest, "T2_DriverBridge", "Main_2")
        assert expected_block == "variance_explanation"

        errors: list[str] = []
        for bracket_path in _all_brackets():
            try:
                doc = yaml.safe_load(bracket_path.read_text(encoding="utf-8"))
            except yaml.YAMLError:
                continue
            if not isinstance(doc, dict):
                continue

            p1 = (doc.get("ux_layout_rules") or {}).get("page_1_summary") or {}
            if p1.get("template_variant") != "T2_DriverBridge":
                continue

            for item in p1.get("component_30s") or []:
                if not isinstance(item, dict):
                    continue
                if item.get("slot_id") != "Main_2":
                    continue

                vt = (item.get("visual_type") or "").strip().lower()
                if vt not in self._VARIANCE_VISUAL_TYPES:
                    errors.append(
                        f"{bracket_path.relative_to(REPO_ROOT)}: T2_DriverBridge Main_2 uses "
                        f"visual_type '{vt}' but template_manifest requires "
                        f"variance_explanation (use waterfall with Plan → drivers → Actual)."
                    )

        assert not errors, "\n".join(f"  - {e}" for e in errors)


class TestManifestInternalConsistency:
    """Smoke checks on template_manifest.yaml internal references."""

    def test_all_variants_have_grid_template(self):
        manifest = _load_manifest()
        known_grid_templates = {
            "pulse", "pulse_asymmetric", "executive_kpi",
            "investigator", "investigator_focus", "action_matrix",
        }
        errors: list[str] = []
        for family in manifest.get("page_families", []):
            for variant in family.get("variants", []):
                gt = variant.get("grid_template")
                if gt not in known_grid_templates:
                    errors.append(
                        f"Variant {variant['variant_id']}: "
                        f"grid_template '{gt}' is not in known_grid_templates {known_grid_templates}"
                    )
        assert not errors, "\n".join(errors)

    def test_all_slot_information_blocks_are_in_registry(self):
        """Every information_block referenced in template_manifest must exist in visual_registry."""
        manifest = _load_manifest()
        registry = _load_registry()
        block_ids = _valid_block_ids(registry)

        errors: list[str] = []
        for family in manifest.get("page_families", []):
            for variant in family.get("variants", []):
                vid = variant["variant_id"]
                for page in ("overview_slots", "detail_slots"):
                    for slot in variant.get(page, []):
                        ib = slot.get("information_block")
                        if ib and ib not in block_ids:
                            errors.append(
                                f"Variant {vid}/{page}/slot {slot['slot_id']}: "
                                f"information_block '{ib}' not found in visual_registry.yaml"
                            )
        assert not errors, (
            "template_manifest.yaml references information blocks not in visual_registry:\n"
            + "\n".join(f"  - {e}" for e in errors)
        )

    def test_grid_template_slots_declared_in_manifest(self):
        """Every slot_id in grid_templates/*.json must appear in grid_template_slots."""
        import json

        manifest = _load_manifest()
        declared = manifest.get("grid_template_slots") or {}
        assert declared, "template_manifest.yaml must define grid_template_slots"

        grid_dir = REPO_ROOT / "core" / "templates" / "page_templates" / "grid_templates"
        errors: list[str] = []
        for path in sorted(grid_dir.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            template_id = data.get("template_id") or path.stem
            slot_ids = [s["slot_id"] for s in data.get("slots", []) if isinstance(s, dict)]
            allowed = set(declared.get(template_id) or [])
            if not allowed:
                errors.append(
                    f"{path.name}: template_id '{template_id}' missing from grid_template_slots"
                )
                continue
            for slot_id in slot_ids:
                if slot_id not in allowed:
                    errors.append(
                        f"{path.name}: slot '{slot_id}' not declared under "
                        f"grid_template_slots.{template_id}"
                    )
        assert not errors, "\n".join(f"  - {e}" for e in errors)


class TestManifestGridIsNotASecondOpinion:
    """Das Manifest fuehrt die Rasterwerte ein ZWEITES Mal — das muss erzwungen sein.

    Gemessen am 02.08.2026: `template_manifest.yaml` traegt `design_canvas`,
    `production_canvas` und `grid` (columns/rows/outer_margin_px/gutter_px/
    internal_padding_px/zone_gap_px) — dieselben Zahlen, die `tokens/layout_grid.yaml`
    governt. Sie stimmen ueberein; das war bis hierher Glueck, nicht Zwang.

    Das ist dieselbe Klasse wie die 38 Leinwand-Literale aus KONZEPT §11, nur eine
    Ebene hoeher: die dortige Raeumung und ihr Waechter (`test_konsolidierung.py`)
    zielen auf Zahlen-Literale in **Code**. Eine zweite governte YAML faellt nicht
    darunter — die Zahl „0 Leinwand-Meinungen" galt fuer Code, nicht fuer YAML.
    Dieser Test schliesst die Luecke, statt die Dublette aufzuloesen: das Manifest ist
    ein Autorendokument, sein Rasterblock dort dokumentarisch nuetzlich.
    """

    def test_manifest_grid_matches_layout_grid_yaml(self):
        from tooling.superversion.layer_tools.layout_grid import load
        from tooling.superversion.layer_tools.page_templates import manifest_grid

        m = manifest_grid()
        prod = load("production")
        design = load("design_base")

        erwartet = {
            "design_width": design.width, "design_height": design.height,
            "production_width": prod.width, "production_height": prod.height,
            "cols": prod.cols, "rows": prod.rows,
            "outer_margin": prod.outer, "gutter": prod.gutter,
        }
        abweichung = {k: (m.get(k), v) for k, v in erwartet.items() if m.get(k) != v}
        assert not abweichung, (
            "template_manifest.yaml widerspricht tokens/layout_grid.yaml "
            f"(Manifest, layout_grid): {abweichung}"
        )


class TestPageTemplateReader:
    """Der Leser aus `layer_tools/page_templates.py` — die einzige Slot-Autoritaet."""

    def test_every_declared_variant_loads(self):
        from tooling.superversion.layer_tools.page_templates import alle_varianten, load

        for vid in sorted(alle_varianten()):
            spec = load(vid)
            assert spec.variant_id == vid
            assert spec.family_id, f"{vid} ohne family_id"
            assert spec.grid_template, f"{vid} ohne grid_template"

    def test_unknown_variant_raises_instead_of_returning_empty(self):
        """Eine leere Pflichtliste sieht aus wie 'alles erfuellt' — deshalb: Abbruch."""
        from tooling.superversion.layer_tools.page_templates import (
            PageTemplateError, load,
        )

        with pytest.raises(PageTemplateError):
            load("T9_GibtEsNicht")

    def test_variant_slot_ids_all_resolve_to_grid_template_slots(self):
        """Die Variantenebene fuehrt echte Slot-IDs — keine Slot-Arten."""
        from tooling.superversion.layer_tools.page_templates import alle_varianten, load

        manifest = _load_manifest()
        bekannt = {s for v in (manifest.get("grid_template_slots") or {}).values() for s in v}
        offen = {sid for vid in alle_varianten() for sid in load(vid).erlaubt()} - bekannt
        assert not offen, f"Slot-IDs ohne grid_template_slot: {sorted(offen)}"

    def test_family_level_vocabulary_is_kept_separate(self):
        """`family.mandatory_slots` ist eine ANDERE Achse und darf nicht einfliessen.

        Von den 7 Woertern dort sind 5 keine Slot-IDs, sondern Slot-Arten
        (`Exceptions`, `Funnel`, `Prescriptive`, `Root_Cause`, `Variance`). Sie in die
        Pflichtliste zu mischen hiesse Schreibweisen vergleichen statt Dinge — genau
        der Fehlalarm aus L2, als `waterfall` als global verboten galt, obwohl es der
        Default eines Blocks war.
        """
        from tooling.superversion.layer_tools.page_templates import (
            alle_varianten, family_slot_kinds, load,
        )

        echte_slot_ids = {sid for vid in alle_varianten() for sid in load(vid).erlaubt()}
        arten = set()
        for fid in ("T1", "T2", "T3", "T4"):
            k = family_slot_kinds(fid)
            arten |= set(k["mandatory"]) | set(k["disallowed"])
        assert arten - echte_slot_ids, (
            "Das Familien-Vokabular enthaelt nur Slot-IDs — dann waere die Trennung "
            "in diesem Modul unnoetig und der Kommentar dort falsch."
        )
        # Und: keine Pflichtliste einer Variante enthaelt je eine dieser Arten.
        for vid in alle_varianten():
            eingemischt = set(load(vid).pflicht()) & (arten - echte_slot_ids)
            assert not eingemischt, f"{vid} mischt Slot-Arten in die Pflichtliste: {eingemischt}"
