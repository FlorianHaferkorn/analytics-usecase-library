# Page Templates

Purpose:
Single source of truth for the 3–30–300 reporting patterns used by the ActionReady Analytics Framework.

Scope:
- Canonical Overview, Insights, and Explorer page patterns
- KPI card, chart, diagnostics table, slicer, and tooltip patterns
- Color, typography, and grid rules for consistent look and feel
- Not included: unvetted mockups or ad-hoc visual experiments
- Not included: platform build scripts

Structure:
- `overview_page_template.md` – 3-second layer emphasis with storyline tiles
- `insights_page_template.md` – 30-second guided diagnostics
- `explorer_page_template.md` – 300-second free-form drill with guardrails
- Slot/visual maps (e.g., `PageTemplate_SlotVisual_Map.md`) remain as references

Usage:
- Pick the template upfront and map every visual to a defined slot before build
- Keep KPI IDs, measures, and Action Codes aligned with catalogs and maps
- Enforce slicer and color rules; flag any deviations as draft until approved

Relations:
- PATTERNS layer; relies on Operating Model UX rules, Measure System, and Action Codes
- Feeds Use Case pages; must stay consistent with KPI catalog, semantic models, and data contracts.
