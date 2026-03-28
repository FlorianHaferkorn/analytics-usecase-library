# Brand Design System

> **Governing authority:** [`reporting_principles.md`](../strategy_operating_model/company/reporting_principles.md) and [`ux_design_system.md`](../strategy_operating_model/operating_model/ux_design_system.md).
> This document operationalizes the brand layer. It does not redefine reporting or UX principles.

The Brand Design System provides **tool-agnostic brand specifications** that serve as the single source of truth for visual identity across all analytical products. From a single brand spec, tool-specific outputs are derived automatically.

---

## Why Tool-Agnostic?

Brand decisions (primary color, typography, semantic signals) are made once by a brand designer and should not be re-entered per tool. The same brand spec drives:

- **Power BI** → theme JSON (data colors, good/bad/neutral/warning, font references)
- **Web / Open Source Stack** → CSS custom properties, Sass variables
- **Documentation** → Markdown color tables, design guidelines

The spec contains no tool-specific syntax. Tools read it and translate to their native format.

---

## File Structure

```
core/brand/
├── README.md                         # This file
├── BrandSpec.schema.yaml             # Canonical schema — all allowed properties
├── samples/
│   └── generic_brand.yaml           # Framework-neutral example (copy-paste start)
└── tool_derivations/
    ├── powerbi_mapping.md            # BrandSpec → Power BI theme JSON properties
    └── css_mapping.md               # BrandSpec → CSS custom properties
```

Per-showcase brand specs live under the showcase:

```
showcases/<name>/brand/
└── brand_spec.yaml                  # Customer brand (validated against BrandSpec.schema.yaml)
```

---

## Authoring a Brand Spec

1. Copy `core/brand/samples/generic_brand.yaml` to `showcases/<name>/brand/brand_spec.yaml`.
2. Fill in `brand_id`, `brand_name`, `color.primary`, `color.secondary`.
3. Set semantic colors (`positive`, `negative`, `warning`, `neutral`) — or accept defaults.
4. Define `typography.font_family.primary` (use system fonts if brand font is unavailable in target tool).
5. Set `canvas_profiles` if non-standard canvas sizes are needed.
6. Reference logo assets relative to the showcase root.
7. Run the tool derivation generators (see below).

---

## Derivation Model

```
brand_spec.yaml
     │
     ├── theme_generator (Power BI)  → themes/<BrandName>/*.json
     │     Referenced by: apply_report_theme.py, setup_theme_defaults.py
     │
     └── css_generator (Web)         → generated/variables.css, variables.scss
           Referenced by: open_source_stack styles
```

See `tool_derivations/powerbi_mapping.md` and `tool_derivations/css_mapping.md` for property-by-property mapping tables.

---

## What This System Does NOT Define

- Page layouts and slot definitions → [`core/templates/page_templates/`](../templates/page_templates/)
- Visual whitelist or chart type rules → [`core/templates/page_templates/governance/`](../templates/page_templates/governance/)
- Reporting principles → [`reporting_principles.md`](../strategy_operating_model/company/reporting_principles.md)
- Tool-specific theme implementation details → `products/fabric/powerbi/tooling/theme_generator/`

---

## Key Principle

> **Define once, derive everywhere.**
> A brand designer sets the spec. Tools consume it. No copy-paste of hex values between systems.
