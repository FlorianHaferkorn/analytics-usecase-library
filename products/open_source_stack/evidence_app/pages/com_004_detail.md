---
title: Promotion Effectiveness
use_case: COM-004
generated: true
---

# Promotion Effectiveness

_Promotion Effectiveness — Detail_

## 3-Second Layer — KPI Headlines

```sql kpi_com_016
SELECT
  metric_value AS value,
  'KPI-COM-016' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-016'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'KPI-COM-016'
  )
```

<BigValue data={kpi_com_016} value="value" title=""KPI-COM-016"" />

```sql kpi_com_021
SELECT
  metric_value AS value,
  'KPI-COM-021' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-021'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'KPI-COM-021'
  )
```

<BigValue data={kpi_com_021} value="value" title=""KPI-COM-021"" />

```sql kpi_fin_012
SELECT
  metric_value AS value,
  'KPI-FIN-012' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'KPI-FIN-012'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'KPI-FIN-012'
  )
```

<BigValue data={kpi_fin_012} value="value" title=""KPI-FIN-012"" />

```sql kpi_com_001
SELECT
  metric_value AS value,
  'KPI-COM-001' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-001'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'KPI-COM-001'
  )
```

<BigValue data={kpi_com_001} value="value" title=""KPI-COM-001"" />

```sql kpi_com_002
SELECT
  metric_value AS value,
  'KPI-COM-002' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-002'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'KPI-COM-002'
  )
```

<BigValue data={kpi_com_002} value="value" title=""KPI-COM-002"" />

```sql kpi_com_003
SELECT
  metric_value AS value,
  'KPI-COM-003' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-003'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'KPI-COM-003'
  )
```

<BigValue data={kpi_com_003} value="value" title=""KPI-COM-003"" />

```sql kpi_com_018
SELECT
  metric_value AS value,
  'KPI-COM-018' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-018'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'KPI-COM-018'
  )
```

<BigValue data={kpi_com_018} value="value" title=""KPI-COM-018"" />

```sql kpi_fin_011
SELECT
  metric_value AS value,
  'KPI-FIN-011' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'KPI-FIN-011'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'KPI-FIN-011'
  )
```

<BigValue data={kpi_fin_011} value="value" title=""KPI-FIN-011"" />

```sql kpi_com_020
SELECT
  metric_value AS value,
  'KPI-COM-020' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-020'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'KPI-COM-020'
  )
```

<BigValue data={kpi_com_020} value="value" title=""KPI-COM-020"" />

```sql kpi_com_017
SELECT
  metric_value AS value,
  'KPI-COM-017' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-017'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'KPI-COM-017'
  )
```

<BigValue data={kpi_com_017} value="value" title=""KPI-COM-017"" />

```sql kpi_com_014
SELECT
  metric_value AS value,
  'KPI-COM-014' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-014'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'KPI-COM-014'
  )
```

<BigValue data={kpi_com_014} value="value" title=""KPI-COM-014"" />

```sql kpi_com_015
SELECT
  metric_value AS value,
  'KPI-COM-015' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-015'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'KPI-COM-015'
  )
```

<BigValue data={kpi_com_015} value="value" title=""KPI-COM-015"" />

```sql kpi_com_011
SELECT
  metric_value AS value,
  'KPI-COM-011' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-011'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'KPI-COM-011'
  )
```

<BigValue data={kpi_com_011} value="value" title=""KPI-COM-011"" />

## 30-Second Layer — Trends

```sql kpi_com_016_trend
SELECT
  period,
  metric_value AS metric_value
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-016'
GROUP BY period, metric_value
ORDER BY period
```

<LineChart data={kpi_com_016_trend} x="period" y="metric_value" title=""KPI-COM-016"" />

```sql kpi_com_021_trend
SELECT
  period,
  metric_value AS metric_value
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-021'
GROUP BY period, metric_value
ORDER BY period
```

<LineChart data={kpi_com_021_trend} x="period" y="metric_value" title=""KPI-COM-021"" />

```sql kpi_fin_012_trend
SELECT
  period,
  metric_value AS metric_value
FROM gold.metric_observations
WHERE kpi_id = 'KPI-FIN-012'
GROUP BY period, metric_value
ORDER BY period
```

<LineChart data={kpi_fin_012_trend} x="period" y="metric_value" title=""KPI-FIN-012"" />

> Core formula: KPI-COM-016 = f(KPI-COM-021, KPI-FIN-012, KPI-COM-003, KPI-COM-018)
> Impact logic: Improving KPI-COM-021 is the primary lever for maximizing KPI-COM-016.

## 300-Second Layer — Diagnostics

```sql detail_data
SELECT
  entity, period, KPI-COM-016
FROM gold.metric_evidence
WHERE kpi_id = 'KPI-COM-016'
ORDER BY period DESC
LIMIT 500
```

<DataTable data={detail_data} />

> Action panel enabled for this use case. Use the linked action codes and governance flow for execution.
