"""
Brand Designer — Studio module for authoring tool-agnostic BrandSpec.

Provides a Streamlit pane that lets the user define brand parameters
(identity, colors, typography, canvas profiles) and export to:
  - showcases/<name>/brand/brand_spec.yaml
  - (preview of PBI theme and CSS variable derivation)

Schema reference: core/brand/BrandSpec.schema.yaml
Derivation guides: core/brand/tool_derivations/powerbi_mapping.md
                   core/brand/tool_derivations/css_mapping.md
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import streamlit as st

try:
    import yaml  # type: ignore
    _YAML_OK = True
except ImportError:
    _YAML_OK = False

_STUDIO_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _STUDIO_DIR.parents[1]
_BRAND_SCHEMA = _REPO_ROOT / "core" / "brand" / "BrandSpec.schema.yaml"
_BRAND_SAMPLE = _REPO_ROOT / "core" / "brand" / "samples" / "generic_brand.yaml"
_SHOWCASES_DIR = _REPO_ROOT / "showcases"


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _hex_swatch(hex_color: str, label: str = "", size: int = 40) -> str:
    """Return an HTML color swatch block."""
    safe = hex_color.strip() or "#CCCCCC"
    name = label or safe
    return (
        f'<span title="{name}" style="display:inline-block;width:{size}px;height:{size}px;'
        f'background:{safe};border:1px solid #ccc;border-radius:4px;margin:2px;'
        f'vertical-align:middle;"></span>'
    )


def _render_swatches(colors: Dict[str, str]) -> str:
    """Render a row of named color swatches as HTML."""
    parts = []
    for name, hex_val in colors.items():
        parts.append(_hex_swatch(hex_val, label=f"{name}: {hex_val}"))
    return "".join(parts)


def _load_existing_spec(showcase_name: str) -> Optional[Dict[str, Any]]:
    """Load existing brand_spec.yaml for a showcase if it exists."""
    if not showcase_name:
        return None
    spec_path = _SHOWCASES_DIR / showcase_name / "brand" / "brand_spec.yaml"
    if spec_path.exists() and _YAML_OK:
        try:
            return yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
        except Exception:
            return None
    return None


def _save_brand_spec(showcase_name: str, spec: Dict[str, Any]) -> Path:
    """Save brand_spec.yaml to the showcase brand/ directory."""
    brand_dir = _SHOWCASES_DIR / showcase_name / "brand"
    brand_dir.mkdir(parents=True, exist_ok=True)
    spec_path = brand_dir / "brand_spec.yaml"
    if _YAML_OK:
        spec_path.write_text(
            yaml.dump(spec, allow_unicode=True, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )
    else:
        import json
        spec_path.with_suffix(".json").write_text(
            json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    return spec_path


def _list_showcases() -> list[str]:
    """Return list of showcase directory names."""
    if not _SHOWCASES_DIR.exists():
        return []
    return sorted(p.name for p in _SHOWCASES_DIR.iterdir() if p.is_dir() and not p.name.startswith("."))


def _derive_neutral_scale(base_dark: str) -> Dict[str, str]:
    """
    Derive a 6-step neutral scale from a base dark color.
    Returns a dict with keys "50","100","200","400","700","900".
    Simple linear interpolation from near-white to the dark base.
    """
    def parse_hex(h: str):
        h = h.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    def lerp(c1, c2, t):
        return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))

    def to_hex(rgb):
        return "#{:02X}{:02X}{:02X}".format(*rgb)

    try:
        dark = parse_hex(base_dark)
    except Exception:
        dark = (32, 32, 32)

    white = (255, 255, 255)
    steps = {
        "50":  to_hex(lerp(white, dark, 0.03)),
        "100": to_hex(lerp(white, dark, 0.08)),
        "200": to_hex(lerp(white, dark, 0.18)),
        "400": to_hex(lerp(white, dark, 0.40)),
        "700": to_hex(lerp(white, dark, 0.72)),
        "900": to_hex(lerp(white, dark, 1.00)),
    }
    return steps


def _build_spec_dict(state: Dict[str, Any]) -> Dict[str, Any]:
    """Build a BrandSpec dict from the form state."""
    neutral = _derive_neutral_scale(state.get("neutral_base", "#201F1E"))
    spec: Dict[str, Any] = {
        "$schema": "analytics-usecase-library/brand/v1",
        "identity": {
            "brand_id": state.get("brand_id", ""),
            "brand_name": state.get("brand_name", ""),
            "brand_version": state.get("brand_version", "1.0.0"),
            "created_by": state.get("created_by", ""),
            "approved": state.get("approved", False),
        },
        "color": {
            "primary": state.get("primary_color", "#2B5EB4"),
            "secondary": state.get("secondary_color", "#3B8EA5"),
            "semantic": {
                "positive": {"color": state.get("positive_color", "#107C10"), "icon": "▲", "label": "positive"},
                "negative": {"color": state.get("negative_color", "#D13438"), "icon": "▼", "label": "negative"},
                "warning":  {"color": state.get("warning_color",  "#F7630C"), "icon": "⚠", "label": "warning"},
                "neutral":  {"color": state.get("neutral_signal", "#605E5C"), "icon": "─", "label": "neutral"},
            },
            "neutral_scale": neutral,
            "mode": state.get("mode", "light"),
        },
        "typography": {
            "font_family": {
                "primary": state.get("font_primary", "Segoe UI, system-ui, -apple-system, sans-serif"),
                "secondary": None,
                "monospace": "Cascadia Code, Consolas, 'Courier New', monospace",
            },
            "type_scale": {
                "xs":    {"size_rem": 0.625, "line_height": 1.4},
                "sm":    {"size_rem": 0.75,  "line_height": 1.4},
                "md":    {"size_rem": 0.875, "line_height": 1.5},
                "lg":    {"size_rem": 1.0,   "line_height": 1.5},
                "xl":    {"size_rem": 1.25,  "line_height": 1.3},
                "2xl":   {"size_rem": 1.5,   "line_height": 1.2},
                "3xl":   {"size_rem": 2.0,   "line_height": 1.1},
            },
            "role_map": {
                "kpi_value": "3xl", "kpi_label": "sm", "kpi_delta": "md", "kpi_period": "xs",
                "chart_title": "md", "axis_label": "xs", "legend_label": "xs",
                "body": "md", "caption": "xs",
                "heading_1": "2xl", "heading_2": "xl", "heading_3": "lg",
                "table_header": "sm", "table_cell": "sm",
            },
            "tool_minimums": {
                "powerbi": {
                    "body_pt": state.get("pbi_body_pt", 12),
                    "label_pt": state.get("pbi_label_pt", 10),
                    "kpi_pt": state.get("pbi_kpi_pt", 18),
                    "canvas_design_base": "1280x720",
                    "canvas_production": "1920x1080",
                },
                "web":       {"body_rem": 1.0, "label_rem": 0.75},
                "export_pdf": {"body_pt": 11, "label_pt": 9},
            },
        },
        "spacing": {
            "base_unit": 8,
            "scale": {"xs": 4, "sm": 8, "md": 16, "lg": 24, "xl": 32, "2xl": 48, "3xl": 64},
        },
        "border": {
            "radius": {"none": 0, "sm": 2, "md": 4, "lg": 8, "full": 9999},
            "width": {"hairline": 1, "thin": 1, "medium": 2},
        },
        "shadow": {
            "none":   "none",
            "low":    "0 1px 3px rgba(0,0,0,0.10), 0 1px 2px rgba(0,0,0,0.06)",
            "medium": "0 4px 12px rgba(0,0,0,0.12), 0 2px 6px rgba(0,0,0,0.08)",
            "high":   "0 8px 24px rgba(0,0,0,0.16), 0 4px 12px rgba(0,0,0,0.10)",
        },
        "logo": {
            "light_bg_asset": state.get("logo_path") or None,
            "dark_bg_asset":  None,
            "clear_space":    16,
            "min_width":      80,
        },
        "canvas_profiles": {
            "powerbi_design_base": {
                "width": 1280, "height": 720,
                "description": "Design reference — layout and fonts at 100% readability.",
            },
            "powerbi_production": {
                "width": 1920, "height": 1080, "font_size_delta_pt": 2,
                "description": "Production — fonts +2pt to compensate for FitToPage scale-down.",
            },
            "web_fluid": {
                "breakpoints": {"sm": 640, "md": 768, "lg": 1024, "xl": 1280, "2xl": 1536},
                "description": "Browser context — fluid typography, 12-column CSS grid.",
            },
        },
        "tool_derivations": {
            "powerbi_theme": None,
            "css_variables":  None,
            "sass_variables": None,
        },
    }
    return spec


def _generate_css_preview(spec: Dict[str, Any]) -> str:
    """Generate a CSS :root preview from the spec dict."""
    color = spec.get("color", {})
    primary = color.get("primary", "#2B5EB4")
    secondary = color.get("secondary", "#3B8EA5")
    sem = color.get("semantic", {})
    neutral = color.get("neutral_scale", {})
    typo = spec.get("typography", {})
    font = typo.get("font_family", {}).get("primary", "system-ui")
    spacing = spec.get("spacing", {}).get("scale", {})

    lines = [
        ":root {",
        f"  --brand-color-primary:    {primary};",
        f"  --brand-color-secondary:  {secondary};",
        f"  --brand-color-positive:   {sem.get('positive', {}).get('color', '#107C10')};",
        f"  --brand-color-negative:   {sem.get('negative', {}).get('color', '#D13438')};",
        f"  --brand-color-warning:    {sem.get('warning',  {}).get('color', '#F7630C')};",
        f"  --brand-color-neutral:    {sem.get('neutral',  {}).get('color', '#605E5C')};",
        "",
        f"  --brand-neutral-50:   {neutral.get('50',  '#FAFAFA')};",
        f"  --brand-neutral-100:  {neutral.get('100', '#F3F2F1')};",
        f"  --brand-neutral-200:  {neutral.get('200', '#E1DFDD')};",
        f"  --brand-neutral-400:  {neutral.get('400', '#A19F9D')};",
        f"  --brand-neutral-700:  {neutral.get('700', '#3B3A39')};",
        f"  --brand-neutral-900:  {neutral.get('900', '#201F1E')};",
        "",
        f"  --brand-font-primary: {font};",
        "",
        f"  --brand-spacing-sm:   {spacing.get('sm', 8)}px;",
        f"  --brand-spacing-md:   {spacing.get('md', 16)}px;",
        f"  --brand-spacing-lg:   {spacing.get('lg', 24)}px;",
        f"  --brand-spacing-xl:   {spacing.get('xl', 32)}px;",
        "}",
    ]
    return "\n".join(lines)


# ─────────────────────────────────────────────
# Main pane render function
# ─────────────────────────────────────────────

def render_brand_designer(repo_root: Optional[Path] = None) -> None:
    """
    Render the Brand Designer pane inside a Streamlit app.
    Call this from within a tab or expander in app.py.
    """
    global _SHOWCASES_DIR, _BRAND_SAMPLE, _BRAND_SCHEMA
    if repo_root:
        _SHOWCASES_DIR = repo_root / "showcases"
        _BRAND_SAMPLE  = repo_root / "core" / "brand" / "samples" / "generic_brand.yaml"
        _BRAND_SCHEMA  = repo_root / "core" / "brand" / "BrandSpec.schema.yaml"

    st.subheader("Brand Design Studio")
    st.caption(
        "Define a tool-agnostic brand specification. "
        "From here, Power BI themes and CSS variables are derived automatically. "
        "Schema: `core/brand/BrandSpec.schema.yaml`"
    )

    # ── Showcase selection ──────────────────────────────────
    showcases = _list_showcases()
    col_sel, col_new = st.columns([3, 2])
    with col_sel:
        showcase_name = st.selectbox(
            "Showcase / Customer",
            options=[""] + showcases,
            help="Select an existing showcase or type a new name below.",
        )
    with col_new:
        new_showcase = st.text_input("New showcase name", placeholder="e.g. acme_corp")
    if new_showcase.strip():
        showcase_name = new_showcase.strip().lower().replace(" ", "_")

    # Load existing spec if available
    existing = _load_existing_spec(showcase_name) or {}
    eid = existing.get("identity", {})
    ec = existing.get("color", {})
    esem = ec.get("semantic", {})
    etypo = existing.get("typography", {})
    etool = etypo.get("tool_minimums", {}).get("powerbi", {})

    st.divider()

    # ── Identity ────────────────────────────────────────────
    with st.expander("1 · Identity", expanded=True):
        c1, c2, c3 = st.columns(3)
        brand_id    = c1.text_input("Brand ID (slug)",   value=eid.get("brand_id", showcase_name or ""))
        brand_name  = c2.text_input("Brand Name",        value=eid.get("brand_name", ""))
        brand_ver   = c3.text_input("Version",           value=eid.get("brand_version", "1.0.0"))
        created_by  = st.text_input("Created by",        value=eid.get("created_by", ""))
        approved    = st.checkbox("Approved by brand owner", value=bool(eid.get("approved", False)))

    # ── Color System ────────────────────────────────────────
    with st.expander("2 · Color System", expanded=True):
        st.markdown("**Brand Colors**")
        cc1, cc2 = st.columns(2)
        primary_color   = cc1.color_picker("Primary color",   value=ec.get("primary", "#2B5EB4"))
        secondary_color = cc2.color_picker("Secondary color", value=ec.get("secondary", "#3B8EA5"))

        st.markdown("**Semantic Signal Colors**")
        sc1, sc2, sc3, sc4 = st.columns(4)
        positive_color = sc1.color_picker("Positive (▲)",  value=esem.get("positive", {}).get("color", "#107C10"))
        negative_color = sc2.color_picker("Negative (▼)",  value=esem.get("negative", {}).get("color", "#D13438"))
        warning_color  = sc3.color_picker("Warning (⚠)",   value=esem.get("warning",  {}).get("color", "#F7630C"))
        neutral_signal = sc4.color_picker("Neutral (─)",   value=esem.get("neutral",  {}).get("color", "#605E5C"))

        st.info(
            "ℹ Semantic colors must always be paired with icons (▲▼⚠─) "
            "and never used alone as the only colorblind-safety mechanism."
        )

        st.markdown("**Neutral Scale Base**")
        neutral_base = st.color_picker(
            "Dark neutral base (darkest text / headlines)",
            value=ec.get("neutral_scale", {}).get("900", "#201F1E"),
        )
        derived = _derive_neutral_scale(neutral_base)
        swatch_html = "<br>".join(
            f'{_hex_swatch(v, label=f"neutral-{k}: {v}", size=28)} '
            f'<span style="font-size:11px;font-family:monospace;">'
            f'neutral-{k} &nbsp; {v}</span>'
            for k, v in derived.items()
        )
        st.markdown(swatch_html, unsafe_allow_html=True)

        mode = st.selectbox("Color mode", ["light", "dark", "both"],
                            index=["light", "dark", "both"].index(ec.get("mode", "light")))

    # ── Typography ──────────────────────────────────────────
    with st.expander("3 · Typography", expanded=False):
        font_primary = st.text_input(
            "Primary font stack",
            value=etypo.get("font_family", {}).get("primary", "Segoe UI, system-ui, -apple-system, sans-serif"),
            help="Use system fonts first (Segoe UI, system-ui). Custom fonts must be available in target tool.",
        )
        st.caption(
            "Type scale roles are defined by the schema. The generator maps these to tool-specific sizes. "
            "Override minimum-safe sizes for Power BI below."
        )
        tc1, tc2, tc3 = st.columns(3)
        pbi_body_pt  = tc1.number_input("PBI body min (pt)",  min_value=8, max_value=24, value=int(etool.get("body_pt", 12)))
        pbi_label_pt = tc2.number_input("PBI label min (pt)", min_value=6, max_value=16, value=int(etool.get("label_pt", 10)))
        pbi_kpi_pt   = tc3.number_input("PBI KPI value (pt)", min_value=12, max_value=48, value=int(etool.get("kpi_pt", 18)))
        st.caption(
            "Canvas: design at 1280×720 (fonts legible at 100%), deploy at 1920×1080 with FitToPage (+2pt). "
            "See `core/brand/tool_derivations/powerbi_mapping.md` for details."
        )

    # ── Logo ────────────────────────────────────────────────
    with st.expander("4 · Logo", expanded=False):
        logo_path = st.text_input(
            "Logo asset path (relative to showcase root)",
            value=existing.get("logo", {}).get("light_bg_asset") or "",
            placeholder="company/Logo.png",
        )

    # ── Build spec dict ─────────────────────────────────────
    form_state: Dict[str, Any] = {
        "brand_id": brand_id, "brand_name": brand_name, "brand_version": brand_ver,
        "created_by": created_by, "approved": approved,
        "primary_color": primary_color, "secondary_color": secondary_color,
        "positive_color": positive_color, "negative_color": negative_color,
        "warning_color": warning_color, "neutral_signal": neutral_signal,
        "neutral_base": neutral_base, "mode": mode,
        "font_primary": font_primary,
        "pbi_body_pt": pbi_body_pt, "pbi_label_pt": pbi_label_pt, "pbi_kpi_pt": pbi_kpi_pt,
        "logo_path": logo_path,
    }
    spec = _build_spec_dict(form_state)

    # ── Preview ─────────────────────────────────────────────
    st.divider()
    st.markdown("**Color Preview**")
    all_colors: Dict[str, str] = {
        "Primary": primary_color, "Secondary": secondary_color,
        "▲ Positive": positive_color, "▼ Negative": negative_color,
        "⚠ Warning": warning_color, "─ Neutral": neutral_signal,
        **{f"neutral-{k}": v for k, v in derived.items()},
    }
    st.markdown(_render_swatches(all_colors), unsafe_allow_html=True)

    # ── Export ──────────────────────────────────────────────
    st.divider()
    col_save, col_yaml, col_css = st.columns(3)

    with col_save:
        if st.button("💾 Save BrandSpec.yaml", disabled=not showcase_name):
            try:
                path = _save_brand_spec(showcase_name, spec)
                st.success(f"Saved: `{path.relative_to(_REPO_ROOT)}`")
            except Exception as exc:
                st.error(f"Save failed: {exc}")

    with col_yaml:
        yaml_str = yaml.dump(spec, allow_unicode=True, default_flow_style=False, sort_keys=False) if _YAML_OK else json.dumps(spec, indent=2)
        st.download_button(
            "⬇ Download YAML",
            data=yaml_str.encode("utf-8"),
            file_name=f"{brand_id or 'brand'}_spec.yaml",
            mime="text/yaml",
        )

    with col_css:
        css_str = _generate_css_preview(spec)
        st.download_button(
            "⬇ Download CSS Preview",
            data=css_str.encode("utf-8"),
            file_name=f"{brand_id or 'brand'}_variables.css",
            mime="text/css",
        )

    # ── CSS Preview ─────────────────────────────────────────
    with st.expander("CSS Variables Preview", expanded=False):
        st.code(_generate_css_preview(spec), language="css")

    # ── PBI Derivation hint ─────────────────────────────────
    with st.expander("Power BI Theme Derivation", expanded=False):
        st.markdown(
            "To generate the Power BI theme from this spec, run the theme generator "
            "after saving `brand_spec.yaml`:\n\n"
            "```bash\n"
            "python products/fabric/powerbi/tooling/setup_theme_defaults.py \\\n"
            f"  --showcase {showcase_name or '<name>'} \\\n"
            f"  --theme \"<BrandName>__Monochromatic__Light__{primary_color}\"\n"
            "```\n\n"
            "Mapping reference: `core/brand/tool_derivations/powerbi_mapping.md`"
        )

    # ── Full YAML preview ───────────────────────────────────
    with st.expander("Full BrandSpec YAML Preview", expanded=False):
        st.code(
            yaml.dump(spec, allow_unicode=True, default_flow_style=False, sort_keys=False) if _YAML_OK
            else json.dumps(spec, indent=2),
            language="yaml",
        )
