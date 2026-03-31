# Layer Sample: 3-Second — The KPI Band

> **Layer:** Zone 1 (rows 0–1 of the 12×12 grid, full width)
> **Purpose:** Immediate orientation — status vs. target at a glance
> **Rule:** Nothing else shares this zone. No slicers. No logos. No buttons.
> **Spec ref:** `layout_330300_design_spec.md §5.1`

---

## What the 3-Second Layer Answers

> *Am I on track?*

The reader needs to know — within one glance — whether the key metrics are green or red. No explanation needed at this stage. Explanation is the job of the 30-second layer.

---

## Full KPI Band Wireframe (5 cards, COM-001 Sales Performance example)

```
Canvas: 1280×720 (design base)  |  Grid: 12 cols × 2 rows (rows 0–1)
─────────────────────────────────────────────────────────────────────

Col:  0──────2    2──────4    4──────6    6──────8    8─────10   10────12
      │                                                                  │
 R0 ──┤                                                                  │
      │  NET SALES  │  GM MARGIN  │  UNITS SOLD  │  CUSTOMERS  │  AVG ORD │
      │             │             │              │             │          │
      │  €42.3M     │  18.4%      │  1.24M       │  98.7K      │  €428    │
      │  [GREEN]    │  [RED]      │  [GREEN]     │  [GREEN]    │  [GREY]  │
      │  ▲ +8.2%    │  ▼ -1.1pp   │  ▲ +3.4%     │  ▲ +5.0%    │  ─ ±0%  │
      │  vs Plan    │  vs Plan    │  vs PY        │  vs PY      │  vs PY  │
      │  ▬▬▬▬▬▬▬▬  │  ▬▬▬▬▬▬▬▬  │  ▬▬▬▬▬▬▬▬    │  ▬▬▬▬▬▬▬▬  │         │
 R1 ──┤                                                                  │
      └──────────────────────────────────────────────────────────────────┘

Slot: KPI_Cards  [col=0, row=0, col_span=12, row_span=2]
```

---

## KPI Card Anatomy (Single Card — Detailed)

```
┌──────────────────────────────┐
│ NET SALES            ◉ info  │  ← kpi_label (sm, neutral-700)   [card title]
│                              │
│  €42.3M                      │  ← kpi_value (3xl, neutral-900)  [hero number]
│                              │
│  ▲ +€3.2M   +8.2%            │  ← kpi_delta (md)                [delta absolute + %]
│              [GREEN]         │    color: semantic.positive
│                              │
│  vs Plan  ·  MTD Oct 2025    │  ← kpi_period (xs, neutral-400)  [reference + period]
│                              │
│  ╭──────────────────────╮    │
│  │  ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ │    │  ← sparkline (12-month trend)
│  ╰──────────────────────╯    │    [optional — shown only when sparkline_field defined]
└──────────────────────────────┘

Height: 140px (standard)  |  Width: ~220px (at 1280×720, 5 cards + slicer)
```

### Component Fields

| Field | Required | Role | Signal logic |
|---|---|---|---|
| Card title (label) | Yes | `kpi_label` | No signal |
| Hero value | Yes | `kpi_value` | No signal — raw number only |
| Delta absolute | Recommended | `kpi_delta` | Signal color + icon |
| Delta % | Recommended | `kpi_delta` | Signal color + icon (same as absolute) |
| Reference label | Yes | `kpi_period` | "vs Plan", "vs PY", "vs Budget", "vs Prior Month" |
| Period label | Recommended | `kpi_period` | "MTD Oct 2025", "FY25", "WK42" |
| Sparkline | Optional | — | Mini trend (last 12 periods); no axes, no labels |
| Info icon | Optional | — | Opens tooltip with KPI definition |

---

## Signal Color Decision Matrix

Applied to the **delta** value. Color + icon always used together.

| Condition | Color | Icon | Example |
|---|---|---|---|
| Favourable delta above threshold | `semantic.positive` (green) | ▲ | Revenue +8.2% vs Plan |
| Unfavourable delta below threshold | `semantic.negative` (red) | ▼ | Margin -1.1pp vs Plan |
| Within tolerance band (±2%) | `semantic.warning` (amber) | ⚠ | Units -1.8% vs Plan |
| No reference / no signal | `semantic.neutral` (grey) | ─ | Avg Order Value (informational) |

> **Directionality matters:** For cost or return rate KPIs, a positive number may be negative in meaning. The `status_logic` field in `UseCase_Bracket.yaml` (e.g. `"lower_is_better"`) controls signal direction. Do not hardcode directionality in layout.

---

## KPI Card Sizing Variants

| Variant | Width | Height | Max cards/row | When to use |
|---|---|---|---|---|
| Standard | ~280px | 140px | 5 | Default for ≤5 KPIs |
| Compact | ~200px | 120px | 6 | 6 KPIs on same row |
| Hero | ~360px | 180px | 3 | T1 Strategic, single dominant KPI |
| Mini | ~160px | 100px | 8 | Monitoring dashboards (T3), informational KPIs |

---

## Variants: KPI Band Configurations

### Variant A — 3 Cards (T1 Strategic, hero layout)

```
│ ◉ HERO KPI (span 4)    │  KPI 2 (span 4)   │  KPI 3 (span 4)   │
│                         │                   │                   │
│  €42.3M  ▲ +8.2%        │  18.4%  ▼ -1.1pp  │  1.24M  ▲ +3.4%   │
│  (hero card, 2 rows)    │                   │                   │
```

### Variant B — 6 Cards (compact, maximum)

```
│ KPI 1 (2w) │ KPI 2 (2w) │ KPI 3 (2w) │ KPI 4 (2w) │ KPI 5 (2w) │ KPI 6 (2w) │
│ €42.3M ▲   │ 18.4% ▼    │ 1.24M ▲    │ 98.7K ▲    │ €428 ─     │ 3.2 ▼      │
│ +8.2% plan │ -1.1pp plan│ +3.4% PY   │ +5.0% PY   │ ±0% PY     │ -0.4 plan  │
```

### Variant C — KPI Band + Date Slicer in same row (alternative)

Only when slicer must share visible space with KPIs for space reasons. Date slicer placed at rightmost columns.

```
│ KPI 1 (2w) │ KPI 2 (2w) │ KPI 3 (2w) │ KPI 4 (2w) │  [Date Slicer  (4w)]  │
```

> **Note:** SQLBI recommends placing slicers in Zone 2, not Zone 1. The above variant is a space-saving exception only.

---

## What Does NOT Belong in Zone 1

| Element | Why not |
|---|---|
| Slicers | Zone 2 — slicers interrupt the "glance" experience |
| Logos or brand assets | Visual noise; do not add decision value |
| Navigation buttons | Interaction; distracts from signal |
| Text banners / titles | Page title goes in page header, not KPI band |
| Charts or mini-charts (other than sparklines) | 3s is status only — charts are 30s layer |

---

## UseCase_Bracket.yaml Reference

The KPI band is configured in `ux_layout_rules.page_1_summary.component_3s`:

```yaml
ux_layout_rules:
  page_1_summary:
    component_3s:
      kpi_id: margin.gm.pct        # Strategic KPI (first card, visual priority)
      visual_type: kpi_card
      sparkline_field: "GM%_monthly"
      comparison: "vs_plan"
      status_logic: "higher_is_better"
```

Additional KPI cards (influencing KPIs) are added as `kpi_cards` array. Card order in the band follows `ux_layout_rules` definition order, not alphabetical.
