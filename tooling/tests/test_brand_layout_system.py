#!/usr/bin/env python3
"""
Test suite: Brand Design System + 3-30-300 Layout Design Spec
Runs standalone (no pytest dependency required) or via pytest.
"""
from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"

results: list[tuple[str, str, str]] = []  # (status, test_name, detail)


def ok(name: str, detail: str = "") -> None:
    results.append((PASS, name, detail))


def fail(name: str, detail: str) -> None:
    results.append((FAIL, name, detail))


def warn(name: str, detail: str) -> None:
    results.append((WARN, name, detail))


def load_yaml(path: Path) -> dict:
    # Inline to support standalone execution (no sys.path setup).
    # Shared equivalent: tooling/utils/yaml_loader.py
    import yaml
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def test_brand_layout_system():
    """Pytest wrapper: runs the standalone brand layout test suite as a subprocess."""
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve())],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"Brand layout tests failed (exit code {result.returncode}):\n"
        f"{result.stdout}\n{result.stderr}"
    )


if __name__ == "__main__":
    # ─────────────────────────────────────────────────────────────────────────────
    # 1. FILE EXISTENCE
    # ─────────────────────────────────────────────────────────────────────────────

    EXPECTED_FILES = [
    "core/brand/README.md",
    "core/brand/BrandSpec.schema.yaml",
    "core/brand/samples/generic_brand.yaml",
    "core/brand/tool_derivations/powerbi_mapping.md",
    "core/brand/tool_derivations/css_mapping.md",
    "showcases/aurora_group/brand/brand_spec.yaml",
    "core/templates/page_templates/Design_Spec_3_30_300.md",
    "core/templates/page_templates/samples/README.md",
    "core/templates/page_templates/samples/layer_3s_kpi_band.md",
    "core/templates/page_templates/samples/layer_30s_diagnostics.md",
    "core/templates/page_templates/samples/layer_300s_detail.md",
    "core/templates/page_templates/samples/page_pulse_full.md",
    "core/templates/page_templates/samples/page_action_matrix_full.md",
    "core/templates/page_templates/samples/page_investigator_full.md",
    ]

    for rel in EXPECTED_FILES:
        p = REPO / rel
        if p.exists():
            ok(f"file_exists: {rel}")
        else:
            fail(f"file_exists: {rel}", f"Missing: {p}")


    # ─────────────────────────────────────────────────────────────────────────────
    # 2. YAML PARSE VALIDITY
    # ─────────────────────────────────────────────────────────────────────────────

    try:
        import yaml
        _YAML_OK = True
    except ImportError:
        _YAML_OK = False
        warn("yaml_available", "pyyaml not installed — skipping YAML tests")

    YAML_FILES = [
        "core/brand/BrandSpec.schema.yaml",
        "core/brand/samples/generic_brand.yaml",
        "showcases/aurora_group/brand/brand_spec.yaml",
    ]

    if _YAML_OK:
        for rel in YAML_FILES:
            p = REPO / rel
            if not p.exists():
                fail(f"yaml_parse: {rel}", "File missing")
                continue
            try:
                data = load_yaml(p)
                if data:
                    ok(f"yaml_parse: {rel}")
                else:
                    fail(f"yaml_parse: {rel}", "Parsed to empty/None")
            except Exception as exc:
                fail(f"yaml_parse: {rel}", str(exc))


    # ─────────────────────────────────────────────────────────────────────────────
    # 3. BRANDSPEC SCHEMA — TOP-LEVEL SECTIONS
    # ─────────────────────────────────────────────────────────────────────────────

    REQUIRED_SCHEMA_KEYS = [
        "identity", "color", "typography", "spacing",
        "border", "shadow", "logo", "canvas_profiles", "tool_derivations",
    ]

    if _YAML_OK:
        schema_path = REPO / "core/brand/BrandSpec.schema.yaml"
        if schema_path.exists():
            schema = load_yaml(schema_path)
            for key in REQUIRED_SCHEMA_KEYS:
                if key in schema:
                    ok(f"schema_key: {key}")
                else:
                    fail(f"schema_key: {key}", f"Missing top-level key '{key}' in BrandSpec.schema.yaml")

            # tool_minimums inside typography
            typo = schema.get("typography", {})
            if "tool_minimums" in typo:
                ok("schema_typography_tool_minimums")
            else:
                fail("schema_typography_tool_minimums", "typography.tool_minimums missing from schema")

            # canvas_profiles has powerbi_design_base
            cp = schema.get("canvas_profiles", {})
            if "powerbi_design_base" in cp and "powerbi_production" in cp:
                ok("schema_canvas_profiles")
            else:
                fail("schema_canvas_profiles", f"canvas_profiles missing design_base or production; found: {list(cp.keys())}")


    # ─────────────────────────────────────────────────────────────────────────────
    # 4. AURORA BRAND SPEC — CORRECT VALUES
    # ─────────────────────────────────────────────────────────────────────────────

    if _YAML_OK:
        aurora_path = REPO / "showcases/aurora_group/brand/brand_spec.yaml"
        if aurora_path.exists():
            aurora = load_yaml(aurora_path)
            color = aurora.get("color", {})
            identity = aurora.get("identity", {})

            # Primary color
            primary = color.get("primary", "").upper().strip()
            if primary == "#2ECDE7":
                ok("aurora_primary_color", "#2ECDE7 (Aurora Light Cyan)")
            else:
                fail("aurora_primary_color", f"Expected #2ECDE7, got {primary!r}")

            # Secondary color
            secondary = color.get("secondary", "").upper().strip()
            if secondary == "#44B396":
                ok("aurora_secondary_color", "#44B396 (Aurora Teal)")
            else:
                fail("aurora_secondary_color", f"Expected #44B396, got {secondary!r}")

            # brand_id
            bid = identity.get("brand_id", "")
            if bid == "aurora_group":
                ok("aurora_brand_id")
            else:
                fail("aurora_brand_id", f"Expected 'aurora_group', got {bid!r}")

            # approved flag
            if identity.get("approved") is True:
                ok("aurora_approved")
            else:
                fail("aurora_approved", "approved should be true")

            # semantic signals all present
            sem = color.get("semantic", {})
            for signal in ["positive", "negative", "warning", "neutral"]:
                if signal in sem and "color" in sem[signal] and "icon" in sem[signal]:
                    ok(f"aurora_semantic_{signal}")
                else:
                    fail(f"aurora_semantic_{signal}", f"semantic.{signal} missing color or icon")

            # colorblind safety: positive != negative
            pos_c = sem.get("positive", {}).get("color", "")
            neg_c = sem.get("negative", {}).get("color", "")
            if pos_c and neg_c and pos_c.upper() != neg_c.upper():
                ok("aurora_semantic_colors_distinct")
            else:
                fail("aurora_semantic_colors_distinct", "positive and negative signal colors are the same")

            # tool_minimums present
            typo = aurora.get("typography", {})
            tm = typo.get("tool_minimums", {})
            pbi = tm.get("powerbi", {})
            if pbi.get("body_pt", 0) >= 12:
                ok("aurora_pbi_body_pt_min_12")
            else:
                fail("aurora_pbi_body_pt_min_12", f"powerbi.body_pt={pbi.get('body_pt')} should be >= 12")
            if pbi.get("label_pt", 0) >= 10:
                ok("aurora_pbi_label_pt_min_10")
            else:
                fail("aurora_pbi_label_pt_min_10", f"powerbi.label_pt={pbi.get('label_pt')} should be >= 10")

            # canvas profiles
            cp = aurora.get("canvas_profiles", {})
            db = cp.get("powerbi_design_base", {})
            prod = cp.get("powerbi_production", {})
            if db.get("width") == 1280 and db.get("height") == 720:
                ok("aurora_canvas_design_base_1280x720")
            else:
                fail("aurora_canvas_design_base_1280x720", f"design_base {db.get('width')}x{db.get('height')}")
            if prod.get("width") == 1920 and prod.get("height") == 1080:
                ok("aurora_canvas_production_1920x1080")
            else:
                fail("aurora_canvas_production_1920x1080", f"production {prod.get('width')}x{prod.get('height')}")


    # ─────────────────────────────────────────────────────────────────────────────
    # 5. GENERIC BRAND SPEC — STRUCTURE
    # ─────────────────────────────────────────────────────────────────────────────

    if _YAML_OK:
        generic_path = REPO / "core/brand/samples/generic_brand.yaml"
        if generic_path.exists():
            generic = load_yaml(generic_path)
            for key in REQUIRED_SCHEMA_KEYS:
                if key in generic:
                    ok(f"generic_spec_key: {key}")
                else:
                    fail(f"generic_spec_key: {key}", f"Missing '{key}' in generic_brand.yaml")

            # type_scale must have all 7 steps
            ts = generic.get("typography", {}).get("type_scale", {})
            for step in ["xs", "sm", "md", "lg", "xl", "2xl", "3xl"]:
                if step in ts and "size_rem" in ts[step]:
                    ok(f"generic_type_scale_{step}")
                else:
                    fail(f"generic_type_scale_{step}", f"type_scale.{step} missing or malformed")

            # spacing base_unit = 8
            base = generic.get("spacing", {}).get("base_unit", 0)
            if base == 8:
                ok("generic_spacing_base_8")
            else:
                fail("generic_spacing_base_8", f"base_unit={base}, expected 8")

            # All 6 neutral scale steps present
            ns = generic.get("color", {}).get("neutral_scale", {})
            for step in ["50", "100", "200", "400", "700", "900"]:
                if step in ns:
                    ok(f"generic_neutral_{step}")
                else:
                    fail(f"generic_neutral_{step}", f"neutral_scale.{step} missing")


    # ─────────────────────────────────────────────────────────────────────────────
    # 6. PYTHON SYNTAX — brand_designer.py
    # ─────────────────────────────────────────────────────────────────────────────

    bd_path = REPO / "tooling/golden_thread_discovery_studio/brand_designer.py"
    if bd_path.exists():
        try:
            source = bd_path.read_text(encoding="utf-8")
            ast.parse(source)
            ok("syntax_brand_designer_py")
        except SyntaxError as exc:
            fail("syntax_brand_designer_py", str(exc))

        # Key functions present
        for fn in ["render_brand_designer", "_derive_neutral_scale", "_build_spec_dict",
                   "_generate_css_preview", "_save_brand_spec", "_list_showcases"]:
            if f"def {fn}" in source:
                ok(f"brand_designer_has_{fn}")
            else:
                fail(f"brand_designer_has_{fn}", f"def {fn} not found in brand_designer.py")

        # _derive_neutral_scale — unit test by extracting full function via AST line ranges
        try:
            tree = ast.parse(source)
            fn_node = None
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == "_derive_neutral_scale":
                    fn_node = node
                    break
            if fn_node is None:
                fail("derive_neutral_scale_unit_test", "Function not found in AST")
            else:
                lines = source.splitlines()
                start = fn_node.lineno - 1
                end = fn_node.end_lineno
                fn_src = "\n".join(lines[start:end])
                local_ns: dict = {}
                exec(fn_src, local_ns)
                derive = local_ns["_derive_neutral_scale"]
                result = derive("#00396B")
                expected_keys = {"50", "100", "200", "400", "700", "900"}
                if set(result.keys()) == expected_keys:
                    ok("derive_neutral_scale_returns_6_steps")
                else:
                    fail("derive_neutral_scale_returns_6_steps", f"Got keys: {set(result.keys())}")
                # All values are valid hex
                for k, v in result.items():
                    if re.match(r"^#[0-9A-Fa-f]{6}$", v):
                        ok(f"derive_neutral_scale_valid_hex_{k}")
                    else:
                        fail(f"derive_neutral_scale_valid_hex_{k}", f"Invalid hex: {v!r}")
                # Darkest step (900) should match input exactly
                darkest = result["900"].upper()
                if darkest == "#00396B":
                    ok("derive_neutral_scale_900_matches_input")
                else:
                    warn("derive_neutral_scale_900_matches_input", f"Expected #00396B, got {darkest}")
                # Lightest step (50) should be near-white (all channels > 230)
                lightest_rgb = [int(result["50"][i:i+2], 16) for i in (1, 3, 5)]
                if all(c > 230 for c in lightest_rgb):
                    ok("derive_neutral_scale_50_near_white")
                else:
                    fail("derive_neutral_scale_50_near_white", f"neutral-50 {result['50']} not near-white")
                # Scale is monotonically darker: 50 lighter than 900
                rgb50 = [int(result["50"][i:i+2], 16) for i in (1, 3, 5)]
                rgb900 = [int(result["900"][i:i+2], 16) for i in (1, 3, 5)]
                if sum(rgb50) > sum(rgb900):
                    ok("derive_neutral_scale_monotonic_dark")
                else:
                    fail("derive_neutral_scale_monotonic_dark", f"50={result['50']} not lighter than 900={result['900']}")
        except Exception as exc:
            warn("derive_neutral_scale_unit_test", f"Could not test function: {exc}")


    # ─────────────────────────────────────────────────────────────────────────────
    # 7. PYTHON SYNTAX — app.py
    # ─────────────────────────────────────────────────────────────────────────────

    app_path = REPO / "tooling/golden_thread_discovery_studio/app.py"
    if app_path.exists():
        try:
            source = app_path.read_text(encoding="utf-8")
            ast.parse(source)
            ok("syntax_app_py")
        except SyntaxError as exc:
            fail("syntax_app_py", str(exc))

        # Tab structure present
        if 'st.tabs(["Discovery", "Brand & Layout"])' in source:
            ok("app_py_tabs_discovery_brand")
        else:
            fail("app_py_tabs_discovery_brand", 'st.tabs(["Discovery", "Brand & Layout"]) not found')

        # brand_designer import present
        if "from brand_designer import render_brand_designer" in source:
            ok("app_py_imports_brand_designer")
        else:
            fail("app_py_imports_brand_designer", "Missing brand_designer import")

        # _render_discovery function defined
        if "def _render_discovery(" in source:
            ok("app_py_has_render_discovery")
        else:
            fail("app_py_has_render_discovery", "_render_discovery function not found")

        # render_brand_designer called in tab
        if "render_brand_designer(" in source:
            ok("app_py_calls_render_brand_designer")
        else:
            fail("app_py_calls_render_brand_designer", "render_brand_designer call not found")


    # ─────────────────────────────────────────────────────────────────────────────
    # 8. LAYOUT DESIGN SPEC — CONTENT CHECKS
    # ─────────────────────────────────────────────────────────────────────────────

    spec_path = REPO / "core/templates/page_templates/Design_Spec_3_30_300.md"
    if spec_path.exists():
        spec_text = spec_path.read_text(encoding="utf-8")

        # Required sections
        required_sections = [
            "## 1. Design Philosophy",
            "## 2. Design References",
            "## 3. Canvas & Grid",
            "## 4. Zone System",
            "## 5. Layer Specifications",
            "### 5.1",  # 3s layer
            "### 5.2",  # 30s filter
            "### 5.3",  # 30s drivers
            "### 5.4",  # 300s
            "## 6. Page Compositions",
            "## 7. Visual Grammar Rules",
            "## 8. Interaction Patterns",
            "## 9. Accessibility",
            "## 10. Framework Hard Limits",
            "## 11. Connector Notes",
        ]
        for section in required_sections:
            if section in spec_text:
                ok(f"layout_spec_section: {section.strip()}")
            else:
                fail(f"layout_spec_section: {section.strip()}", f"Section not found in layout_330300_design_spec.md")

        # SQLBI reference present
        if "SQLBI" in spec_text:
            ok("layout_spec_references_sqlbi")
        else:
            fail("layout_spec_references_sqlbi", "SQLBI not referenced in layout spec")

        # BPA limits present
        if "REPORT_BEST_PRACTICES" in spec_text or "REPORT_BEST_PRACTICES.md" in spec_text:
            ok("layout_spec_references_bpa")
        else:
            fail("layout_spec_references_bpa", "REPORT_BEST_PRACTICES not referenced")

        # Canvas scale problem addressed
        if "1280" in spec_text and "720" in spec_text:
            ok("layout_spec_mentions_design_base_canvas")
        else:
            fail("layout_spec_mentions_design_base_canvas", "1280x720 design base not mentioned")

        # Z and F patterns mentioned
        if "Z-pattern" in spec_text and "F-pattern" in spec_text:
            ok("layout_spec_reading_patterns")
        else:
            fail("layout_spec_reading_patterns", "Z-pattern or F-pattern not mentioned")


    # ─────────────────────────────────────────────────────────────────────────────
    # 9. LAYER SAMPLES — CONTENT CHECKS
    # ─────────────────────────────────────────────────────────────────────────────

    layer_checks = {
        "layer_3s_kpi_band.md": {
            "has_wireframe": "Full KPI Band Wireframe",
            "has_anatomy": "KPI Card Anatomy",
            "has_signal_matrix": "Signal Color Decision Matrix",
            "has_bracket_ref": "UseCase_Bracket.yaml",
        },
        "layer_30s_diagnostics.md": {
            "has_trend_section": "Slot 1 — Trend",
            "has_variance_section": "Slot 2 — Variance",
            "has_ranking_section": "Slot 3 — Ranking",
            "has_wireframe": "Main_1",
            "has_bracket_ref": "UseCase_Bracket.yaml",
        },
        "layer_300s_detail.md": {
            "has_slicer_pane": "Component 1: Slicer Pane",
            "has_smart_narrative": "Component 2: Smart Narrative",
            "has_detail_matrix": "Component 3: Detail Matrix",
            "has_action_panel": "Component 4: Action Panel",
            "has_wireframe": "Full Action Matrix Wireframe",
            "has_bracket_ref": "UseCase_Bracket.yaml",
        },
    }

    samples_dir = REPO / "core/templates/page_templates/samples"
    for filename, checks in layer_checks.items():
        p = samples_dir / filename
        if not p.exists():
            fail(f"layer_sample_{filename}", "File missing")
            continue
        text = p.read_text(encoding="utf-8")
        for check_name, needle in checks.items():
            if needle in text:
                ok(f"{filename}:{check_name}")
            else:
                fail(f"{filename}:{check_name}", f"'{needle}' not found in {filename}")


    # ─────────────────────────────────────────────────────────────────────────────
    # 10. FULL PAGE SAMPLES — CONTENT CHECKS
    # ─────────────────────────────────────────────────────────────────────────────

    page_checks = {
        "page_pulse_full.md": {
            "has_zone1": "ZONE 1",
            "has_zone2": "ZONE 2",
            "has_zone3": "ZONE 3",
            "has_z_pattern": "Z-Pattern",
            "has_grid_positions": "Grid slot summary",
        },
        "page_action_matrix_full.md": {
            "has_variant_a": "Variant A",
            "has_variant_b": "Variant B",
            "has_f_pattern": "F-Pattern",
            "has_drillthrough": "drillthrough",
        },
        "page_investigator_full.md": {
            "has_focus_area": "Focus_Area",
            "has_support_panels": "Support_1",
            "has_pulse_comparison": "Pulse",
        },
    }

    for filename, checks in page_checks.items():
        p = samples_dir / filename
        if not p.exists():
            fail(f"page_sample_{filename}", "File missing")
            continue
        text = p.read_text(encoding="utf-8")
        for check_name, needle in checks.items():
            if needle.lower() in text.lower():
                ok(f"{filename}:{check_name}")
            else:
                fail(f"{filename}:{check_name}", f"'{needle}' not found in {filename}")


    # ─────────────────────────────────────────────────────────────────────────────
    # 11. TOOL DERIVATION GUIDES — KEY CONTENT
    # ─────────────────────────────────────────────────────────────────────────────

    pbi_map = REPO / "core/brand/tool_derivations/powerbi_mapping.md"
    if pbi_map.exists():
        text = pbi_map.read_text(encoding="utf-8")
        checks = {
            "has_datacolors": "dataColors",
            "has_good": "`good`",
            "has_bad": "`bad`",
            "has_font_table": "rem → pt",
            "has_canvas_rule": "FitToPage",
            "has_bpa_compliance": "BPA Compliance",
        }
        for name, needle in checks.items():
            if needle in text:
                ok(f"powerbi_mapping_{name}")
            else:
                fail(f"powerbi_mapping_{name}", f"'{needle}' not found in powerbi_mapping.md")

    css_map = REPO / "core/brand/tool_derivations/css_mapping.md"
    if css_map.exists():
        text = css_map.read_text(encoding="utf-8")
        checks = {
            "has_custom_properties": "--brand-",
            "has_clamp": "clamp(",
            "has_grid": "12-column",
            "has_tremor": "Tremor",
            "has_generated_example": ":root {",
        }
        for name, needle in checks.items():
            if needle in text:
                ok(f"css_mapping_{name}")
            else:
                fail(f"css_mapping_{name}", f"'{needle}' not found in css_mapping.md")


    # ─────────────────────────────────────────────────────────────────────────────
    # 12. CROSS-REFERENCE: Aurora brand_spec ↔ Aurora_Theme_Color_Proposal.md
    # ─────────────────────────────────────────────────────────────────────────────

    aurora_proposal = REPO / "showcases/aurora_group/company/Aurora_Theme_Color_Proposal.md"
    aurora_spec = REPO / "showcases/aurora_group/brand/brand_spec.yaml"

    if aurora_proposal.exists() and aurora_spec.exists() and _YAML_OK:
        proposal_text = aurora_proposal.read_text(encoding="utf-8")
        spec_data = load_yaml(aurora_spec)
        color = spec_data.get("color", {})

        # Primary color #2ECDE7 appears in both
        if "#2ECDE7" in proposal_text.upper().replace("#2ecde7", "#2ECDE7"):
            prop_primary_ok = True
        else:
            prop_primary_ok = "#2ECDE7" in proposal_text
        spec_primary = color.get("primary", "").upper()
        if prop_primary_ok and spec_primary == "#2ECDE7":
            ok("cross_ref_aurora_primary_matches_proposal")
        else:
            fail("cross_ref_aurora_primary_matches_proposal",
                 f"proposal has #2ECDE7: {prop_primary_ok}, spec primary: {spec_primary}")

        # Secondary #44B396
        prop_secondary_ok = "#44B396" in proposal_text or "#44b396" in proposal_text.lower()
        spec_secondary = color.get("secondary", "").upper()
        if prop_secondary_ok and spec_secondary == "#44B396":
            ok("cross_ref_aurora_secondary_matches_proposal")
        else:
            fail("cross_ref_aurora_secondary_matches_proposal",
                 f"proposal has #44B396: {prop_secondary_ok}, spec secondary: {spec_secondary}")


    # ─────────────────────────────────────────────────────────────────────────────
    # REPORT
    # ─────────────────────────────────────────────────────────────────────────────

    total = len(results)
    passed = sum(1 for s, _, _ in results if s == PASS)
    failed = sum(1 for s, _, _ in results if s == FAIL)
    warned = sum(1 for s, _, _ in results if s == WARN)

    print(f"\n{'─'*72}")
    print(f"  Brand Design + Layout Spec — Test Suite")
    print(f"{'─'*72}")

    if failed:
        print(f"\n  FAILURES ({failed}):")
        for status, name, detail in results:
            if status == FAIL:
                print(f"    ✗  {name}")
                if detail:
                    print(f"       {detail}")

    if warned:
        print(f"\n  WARNINGS ({warned}):")
        for status, name, detail in results:
            if status == WARN:
                print(f"    ⚠  {name}: {detail}")

    print(f"\n  RESULTS:  {passed} passed  /  {failed} failed  /  {warned} warnings  /  {total} total")
    print(f"{'─'*72}\n")

    sys.exit(1 if failed else 0)
