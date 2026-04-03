---
title: Sales Performance vs Plan & LY
use_case: COM-001
generated: true
---

# Sales Performance vs Plan & LY

_Sales Performance vs Plan & LY — Overview_

## 3-Second Layer — KPI Headlines

```sql margin_gm_pct
SELECT
  metric_value AS value,
  'margin.gm.pct' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'margin.gm.pct'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'margin.gm.pct'
  )
```

<BigValue data={margin_gm_pct} value="value" title=""margin.gm.pct"" />

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

```sql sales_net_sales_amount
SELECT
  metric_value AS value,
  'sales.net_sales.amount' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'sales.net_sales.amount'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'sales.net_sales.amount'
  )
```

<BigValue data={sales_net_sales_amount} value="value" title=""sales.net_sales.amount"" />

```sql sales_net_sales_delta_pct_plan
SELECT
  metric_value AS value,
  'sales.net_sales.delta_pct.plan' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'sales.net_sales.delta_pct.plan'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'sales.net_sales.delta_pct.plan'
  )
```

<BigValue data={sales_net_sales_delta_pct_plan} value="value" title=""sales.net_sales.delta_pct.plan"" />

```sql sales_net_sales_delta_pct_ly
SELECT
  metric_value AS value,
  'sales.net_sales.delta_pct.ly' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'sales.net_sales.delta_pct.ly'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'sales.net_sales.delta_pct.ly'
  )
```

<BigValue data={sales_net_sales_delta_pct_ly} value="value" title=""sales.net_sales.delta_pct.ly"" />

```sql sales_pvm_price_effect_amount
SELECT
  metric_value AS value,
  'sales.pvm.price_effect.amount' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'sales.pvm.price_effect.amount'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'sales.pvm.price_effect.amount'
  )
```

<BigValue data={sales_pvm_price_effect_amount} value="value" title=""sales.pvm.price_effect.amount"" />

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

```sql sales_pvm_mix_effect_amount
SELECT
  metric_value AS value,
  'sales.pvm.mix_effect.amount' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'sales.pvm.mix_effect.amount'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'sales.pvm.mix_effect.amount'
  )
```

<BigValue data={sales_pvm_mix_effect_amount} value="value" title=""sales.pvm.mix_effect.amount"" />

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

## 30-Second Layer — Trends

```sql margin_gm_pct_trend
SELECT
  period,
  metric_value AS metric_value
FROM gold.metric_observations
WHERE kpi_id = 'margin.gm.pct'
GROUP BY period, metric_value
ORDER BY period
```

<LineChart data={margin_gm_pct_trend} x="period" y="metric_value" title=""margin.gm.pct"" />

```sql cost_cogs_amount_trend
SELECT
  period,
  metric_value AS metric_value
FROM gold.metric_observations
WHERE kpi_id = 'cost.cogs.amount'
GROUP BY period, metric_value
ORDER BY period
```

<LineChart data={cost_cogs_amount_trend} x="period" y="metric_value" title=""cost.cogs.amount"" />

```sql sales_net_sales_amount_trend
SELECT
  period,
  metric_value AS metric_value
FROM gold.metric_observations
WHERE kpi_id = 'sales.net_sales.amount'
GROUP BY period, metric_value
ORDER BY period
```

<LineChart data={sales_net_sales_amount_trend} x="period" y="metric_value" title=""sales.net_sales.amount"" />

> Core formula: margin.gm.pct = f(sales.net_sales.amount, sales.net_sales.delta_pct.plan, sales.net_sales.delta_pct.ly, sales.pvm.price_effect.amount, sales.pvm.volume_effect.amount, sales.pvm.mix_effect.amount)
> Impact logic: Improving sales.net_sales.amount is the primary lever for maximizing margin.gm.pct.
