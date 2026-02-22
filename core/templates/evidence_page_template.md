# Evidence.dev Page Template (Framework)

Use this template when generating Evidence pages from Core (KPI catalog, semantic model, use case).  
Design tokens: use Tailwind classes `fill-primary`, `text-brand-header`, `bg-surface` so the agent and themes stay consistent.

---

## 3-Second Layer — KPI Cards

```sql kpi_headline
-- Replace with SQL that reflects Core KPI definition (grain, filters).
-- Source: core/kpi_catalog/ and semantic model for this use case.
SELECT
  SUM(net_sales) AS value,
  'Net Sales' AS label
FROM your_gold_table
WHERE period = (SELECT MAX(period) FROM your_gold_table)
```

<BigValue data={kpi_headline} value="value" title="value" />

<!-- Repeat for each KPI in the use case's component_3s / strategic_kpi_id. Use class="text-brand-header" on container if your theme exposes it. -->

---

## 30-Second Layer — Main Visuals

```sql trend_data
SELECT
  period,
  metric_value,
  segment
FROM your_gold_table
ORDER BY period
```

<LineChart data={trend_data} x="period" y="metric_value" series="segment" title="Trend" />

<!-- Use BarChart, AreaChart, etc. as per layout_330300 component_30s. -->

---

## 300-Second Layer — Diagnostics (optional)

```sql detail_table
SELECT entity, period, kpi_value, driver
FROM your_evidence_grain_table
ORDER BY period DESC, kpi_value
LIMIT 500
```

<DataTable data={detail_table} />

---

## Design tokens (Tailwind)

When customizing Evidence with Tailwind, define in `themes/` or app config:

- `--color-primary` / `fill-primary`: primary brand (e.g. #003366)
- `--color-brand-header` / `text-brand-header`: headings
- `--color-surface` / `bg-surface`: card/page background

The agent must use only these classes when generating new charts and cards so design stays consistent.
