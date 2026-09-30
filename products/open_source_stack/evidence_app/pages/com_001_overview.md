---
title: Sales Performance vs Plan & LY
use_case: COM-001
generated: true
---

# Sales Performance vs Plan & LY

_Sales Performance vs Plan & LY — Overview_

## 3-Second Layer — KPI Headlines

```sql kpi_com_013
SELECT
  metric_value AS value,
  'KPI-COM-013' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-013'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'KPI-COM-013'
  )
```

<BigValue data={kpi_com_013} value="value" title=""KPI-COM-013"" />

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

```sql kpi_com_005
SELECT
  metric_value AS value,
  'KPI-COM-005' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-005'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'KPI-COM-005'
  )
```

<BigValue data={kpi_com_005} value="value" title=""KPI-COM-005"" />

```sql kpi_com_009
SELECT
  metric_value AS value,
  'KPI-COM-009' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-009'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'KPI-COM-009'
  )
```

<BigValue data={kpi_com_009} value="value" title=""KPI-COM-009"" />

```sql kpi_com_008
SELECT
  metric_value AS value,
  'KPI-COM-008' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-008'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'KPI-COM-008'
  )
```

<BigValue data={kpi_com_008} value="value" title=""KPI-COM-008"" />

```sql kpi_com_010
SELECT
  metric_value AS value,
  'KPI-COM-010' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-010'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'KPI-COM-010'
  )
```

<BigValue data={kpi_com_010} value="value" title=""KPI-COM-010"" />

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

```sql kpi_com_004
SELECT
  metric_value AS value,
  'KPI-COM-004' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-004'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'KPI-COM-004'
  )
```

<BigValue data={kpi_com_004} value="value" title=""KPI-COM-004"" />

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

## 30-Second Layer — Trends

```sql kpi_com_013_trend
SELECT
  period,
  metric_value AS metric_value
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-013'
GROUP BY period, metric_value
ORDER BY period
```

<LineChart data={kpi_com_013_trend} x="period" y="metric_value" title=""KPI-COM-013"" />

```sql kpi_fin_011_trend
SELECT
  period,
  metric_value AS metric_value
FROM gold.metric_observations
WHERE kpi_id = 'KPI-FIN-011'
GROUP BY period, metric_value
ORDER BY period
```

<LineChart data={kpi_fin_011_trend} x="period" y="metric_value" title=""KPI-FIN-011"" />

```sql kpi_com_005_trend
SELECT
  period,
  metric_value AS metric_value
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-005'
GROUP BY period, metric_value
ORDER BY period
```

<LineChart data={kpi_com_005_trend} x="period" y="metric_value" title=""KPI-COM-005"" />

> Core formula: KPI-COM-013 = f(KPI-COM-005, KPI-COM-009, KPI-COM-008, KPI-COM-010, KPI-COM-011, KPI-COM-004)
> Impact logic: Improving KPI-COM-005 is the primary lever for maximizing KPI-COM-013.
