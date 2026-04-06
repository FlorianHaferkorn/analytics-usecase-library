---
title: Promotion Effectiveness
use_case: COM-004
generated: true
---

# Promotion Effectiveness

_Promotion Effectiveness — Detail_

## 3-Second Layer — KPI Headlines

```sql sales_promo_roi_pct
SELECT
  metric_value AS value,
  'sales.promo.roi.pct' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'sales.promo.roi.pct'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'sales.promo.roi.pct'
  )
```

<BigValue data={sales_promo_roi_pct} value="value" title=""sales.promo.roi.pct"" />

```sql sales_promo_incremental_amount
SELECT
  metric_value AS value,
  'sales.promo.incremental.amount' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'sales.promo.incremental.amount'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'sales.promo.incremental.amount'
  )
```

<BigValue data={sales_promo_incremental_amount} value="value" title=""sales.promo.incremental.amount"" />

```sql margin_promo_gm_pct
SELECT
  metric_value AS value,
  'margin.promo.gm.pct' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'margin.promo.gm.pct'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'margin.promo.gm.pct'
  )
```

<BigValue data={margin_promo_gm_pct} value="value" title=""margin.promo.gm.pct"" />

```sql sales_price_list_amount
SELECT
  metric_value AS value,
  'sales.price.list.amount' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'sales.price.list.amount'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'sales.price.list.amount'
  )
```

<BigValue data={sales_price_list_amount} value="value" title=""sales.price.list.amount"" />

```sql sales_price_net_amount
SELECT
  metric_value AS value,
  'sales.price.net.amount' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'sales.price.net.amount'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'sales.price.net.amount'
  )
```

<BigValue data={sales_price_net_amount} value="value" title=""sales.price.net.amount"" />

```sql sales_price_realization_pct
SELECT
  metric_value AS value,
  'sales.price.realization_pct' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'sales.price.realization_pct'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'sales.price.realization_pct'
  )
```

<BigValue data={sales_price_realization_pct} value="value" title=""sales.price.realization_pct"" />

```sql sales_promo_cannibalization_pct
SELECT
  metric_value AS value,
  'sales.promo.cannibalization.pct' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'sales.promo.cannibalization.pct'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'sales.promo.cannibalization.pct'
  )
```

<BigValue data={sales_promo_cannibalization_pct} value="value" title=""sales.promo.cannibalization.pct"" />

```sql cost_cogs_amount
SELECT
  metric_value AS value,
  'cost.cogs.amount' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'cost.cogs.amount'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'cost.cogs.amount'
  )
```

<BigValue data={cost_cogs_amount} value="value" title=""cost.cogs.amount"" />

```sql sales_promo_baseline_sales_amount
SELECT
  metric_value AS value,
  'sales.promo.baseline_sales.amount' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'sales.promo.baseline_sales.amount'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'sales.promo.baseline_sales.amount'
  )
```

<BigValue data={sales_promo_baseline_sales_amount} value="value" title=""sales.promo.baseline_sales.amount"" />

```sql sales_promo_cannibalized_sales_amount
SELECT
  metric_value AS value,
  'sales.promo.cannibalized_sales.amount' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'sales.promo.cannibalized_sales.amount'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'sales.promo.cannibalized_sales.amount'
  )
```

<BigValue data={sales_promo_cannibalized_sales_amount} value="value" title=""sales.promo.cannibalized_sales.amount"" />

```sql sales_promo_cost_amount
SELECT
  metric_value AS value,
  'sales.promo.cost.amount' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'sales.promo.cost.amount'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'sales.promo.cost.amount'
  )
```

<BigValue data={sales_promo_cost_amount} value="value" title=""sales.promo.cost.amount"" />

```sql sales_promo_incremental_gm_amount
SELECT
  metric_value AS value,
  'sales.promo.incremental_gm.amount' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'sales.promo.incremental_gm.amount'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'sales.promo.incremental_gm.amount'
  )
```

<BigValue data={sales_promo_incremental_gm_amount} value="value" title=""sales.promo.incremental_gm.amount"" />

```sql sales_pvm_volume_effect_amount
SELECT
  metric_value AS value,
  'sales.pvm.volume_effect.amount' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'sales.pvm.volume_effect.amount'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'sales.pvm.volume_effect.amount'
  )
```

<BigValue data={sales_pvm_volume_effect_amount} value="value" title=""sales.pvm.volume_effect.amount"" />

## 30-Second Layer — Trends

```sql sales_promo_roi_pct_trend
SELECT
  period,
  metric_value AS metric_value
FROM gold.metric_observations
WHERE kpi_id = 'sales.promo.roi.pct'
GROUP BY period, metric_value
ORDER BY period
```

<LineChart data={sales_promo_roi_pct_trend} x="period" y="metric_value" title=""sales.promo.roi.pct"" />

```sql sales_promo_incremental_amount_trend
SELECT
  period,
  metric_value AS metric_value
FROM gold.metric_observations
WHERE kpi_id = 'sales.promo.incremental.amount'
GROUP BY period, metric_value
ORDER BY period
```

<LineChart data={sales_promo_incremental_amount_trend} x="period" y="metric_value" title=""sales.promo.incremental.amount"" />

```sql margin_promo_gm_pct_trend
SELECT
  period,
  metric_value AS metric_value
FROM gold.metric_observations
WHERE kpi_id = 'margin.promo.gm.pct'
GROUP BY period, metric_value
ORDER BY period
```

<LineChart data={margin_promo_gm_pct_trend} x="period" y="metric_value" title=""margin.promo.gm.pct"" />

> Core formula: sales.promo.roi.pct = f(sales.promo.incremental.amount, margin.promo.gm.pct, sales.price.realization_pct, sales.promo.cannibalization.pct)
> Impact logic: Improving sales.promo.incremental.amount is the primary lever for maximizing sales.promo.roi.pct.

## 300-Second Layer — Diagnostics

```sql detail_data
SELECT
  entity, period, sales.promo.roi.pct
FROM gold.metric_evidence
WHERE kpi_id = 'sales.promo.roi.pct'
ORDER BY period DESC
LIMIT 500
```

<DataTable data={detail_data} />

> Action panel enabled for this use case. Use the linked action codes and governance flow for execution.
