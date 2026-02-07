# Aurora Report — Quality Improvement to Framework Standard

The current report pages are **scaffolded placeholders**. To reach the framework’s “world-class” bar, align with the **UX Design System**, **Layout Grid**, and **Page Definition of Done**.

---

## 1. Framework References (Authority)

| Topic | Location |
|-------|----------|
| UX principles, 3-30-300, components | `framework/strategy_operating_model/operating_model/ux_design_system.md` |
| Layout grid, spacing, row system, slicer/action panel placement | `framework/templates/page_templates/governance/Layout_Grid_System.yaml` |
| Page Definition of Done | `framework/templates/page_templates/governance/Page_DoD.md` |
| COM-001 / COM-002 page template (T2) | `framework/templates/page_templates/mappings/UseCase_PageTemplate_Map.yaml` |
| Slot definitions, visual whitelist | `framework/templates/page_templates/governance/` |

---

## 2. Current Gaps (Prioritized)

### 2.1 Content and binding — DONE

- **Action Panel:** Replaced with **Action Teaser** text per T2 (ActionPanel_Spec): "Key actions from variance → see Detail or T4".
- **KPI cards:** Bound to COM-001/COM-002 measures from `_Measures` (Net Sales Amount, Net Sales % vs Plan, Delta% Net Sales, Gross Margin %, Gross Margin Amount, Price Realization %, Gross Margin % vs Plan).
- **Trend / Variance / Ranking:** Bound to CoreActionReady (dim_date.Month Name, dim_org.OrgName, Price/Mix Effect Amount, Net Sales Amount, Gross Margin %). Detail Matrix: dim_date, dim_org, dim_product, measures as per Technical Factsheets.
- **Slicers:** One slicer per page (Date); bound to dim_date.Date. Max 3 respected.

### 2.2 Layout and hierarchy — DONE

- **Canvas:** 1920×1080; padding 20px; all visuals at least 20px from page edges from edges.
- **Row structure (T2 Overview):** Row 1 KPI at (20,320,620,920), slicer (1220,20); Row 2 Trend (20,180,1510×190), Variance (20,390,1510×190); Row 3 Ranking (20,600,1510×300). Action Teaser at x=1570, width 350.
- **Detail pages:** KPI row + Slicer same; Ranking (20,180,1880×300); Detail Matrix (20,520,1880×540).
- **Spacing:** 20px gaps; 40px between KPI band and row 2.

### 2.3 UX and governance

- **3-30-300:** Overview = 3s + 30s; Detail = 300-level matrix/drill. Compliant.
- **Reference lines:** Add in Desktop where KPI catalog defines targets (reference line styling per theme).
- **No pie/donut:** Only whitelisted visuals used (card, lineChart, waterfallChart, clusteredBarChart, tableEx, slicer, textbox).
- **Theme and formatting:** Report uses base theme; apply **Color_Semantics_Formatting.yaml** for variance (theme roles good/bad/neutral) in Desktop as needed.

### 2.4 Definition of Done (Page DoD)

- Each page to be verified against **Page_DoD.md**: T2, slots match UseCase_PageTemplate_Map, whitelisted visuals, ≤3 slicers, decision clarity (30s).

---

## 3. Recommended Order of Work

1. **Remove or replace placeholders**  
   Action Panel: real content or remove. All visuals: ensure data bindings point to CoreActionReady measures/dimensions.

2. **Align layout to Layout_Grid_System**  
   In Power BI Desktop (or by editing `visual.json` position/height/width): apply row system, 20px padding and gaps, KPI 280×140, Action Panel at x=1570 width 350.

3. **Bind KPIs to catalog measures**  
   For COM-001/COM-002, map each KPI card and chart to the measures defined in the use case and semantic model (e.g. measure dictionary / `_Measures`).

4. **Add reference lines**  
   Where the KPI catalog defines targets or thresholds, add reference lines to the relevant visuals.

5. **Apply theme and color semantics**  
   Use Aurora theme; apply variance color rules (e.g. positive/negative) from framework.

6. **Run Page DoD checklist**  
   Before release, verify every page against `framework/templates/page_templates/governance/Page_DoD.md`.

---

## 4. Optional: Scaffold Generator Alignment

To avoid repeated manual fixes, the **page scaffold** (or report generator) that produces PBIR pages should:

- Use **Layout_Grid_System.yaml** for all positions and sizes.
- Use **UseCase_PageTemplate_Map.yaml** to decide slots per use case and page type.
- Emit **queryState** with correct measure/dimension references (from Technical Factsheet / measure dictionary), not empty placeholders.
- Omit or clearly mark Action Panel as placeholder until action logic is implemented.

See `implementations/microsoft_fabric_powerbi/tools/` for existing scaffold/validation tooling.
