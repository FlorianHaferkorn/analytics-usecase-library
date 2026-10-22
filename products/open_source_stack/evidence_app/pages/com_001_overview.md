---
title: Sales Performance vs Plan & LY
use_case: COM-001
generated: true
---

# Sales Performance vs Plan & LY

_Sales Performance vs Plan & LY — Overview_

## Filters

```sql period_options
SELECT DISTINCT
  period
FROM gold.metric_observations
ORDER BY period
```

<DateRange name=period_range data={period_options} dates=period />

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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

<BigValue data={kpi_com_013} value="value" title="KPI-COM-013" />

_Data as of <Value data={kpi_com_013} column="period" />_

<Details title="Source and definition: KPI-COM-013">

- Catalog id: KPI-COM-013
- Definition, target and threshold: core/kpi_catalog/KPI_Catalog.md, line 4512
- Owner: Head of Controlling; steward: Controlling Analyst
- Action codes: C-M2.1, C-S1.1, C-S1.2
- Lineage: core/data_contracts/domains/commercial_sales.yaml, core/data_contracts/domains/executive.yaml, core/data_contracts/domains/finance.yaml

Query as executed:

```text
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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

</Details>

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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

<BigValue data={kpi_com_009} value="value" title="KPI-COM-009" />

_Data as of <Value data={kpi_com_009} column="period" />_

<Details title="Source and definition: KPI-COM-009">

- Catalog id: KPI-COM-009
- Definition, target and threshold: core/kpi_catalog/KPI_Catalog.md, line 3468
- Owner: Head of Sales Controlling; steward: Sales Analyst
- Action codes: C-M2.1, C-S1.1, C-S1.2
- Lineage: core/data_contracts/domains/commercial_sales.yaml, core/data_contracts/domains/finance.yaml

Query as executed:

```text
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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

</Details>

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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

<BigValue data={kpi_com_008} value="value" title="KPI-COM-008" />

_Data as of <Value data={kpi_com_008} column="period" />_

<Details title="Source and definition: KPI-COM-008">

- Catalog id: KPI-COM-008
- Definition, target and threshold: core/kpi_catalog/KPI_Catalog.md, line 3413
- Owner: Head of Sales Controlling; steward: Sales Analyst
- Action codes: C-M2.1, C-S1.1, C-S1.2
- Lineage: core/data_contracts/domains/commercial_sales.yaml, core/data_contracts/domains/executive.yaml

Query as executed:

```text
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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

</Details>

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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

<BigValue data={kpi_com_005} value="value" title="KPI-COM-005" />

_Data as of <Value data={kpi_com_005} column="period" />_

<Details title="Source and definition: KPI-COM-005">

- Catalog id: KPI-COM-005
- Definition, target and threshold: core/kpi_catalog/KPI_Catalog.md, line 3270
- Owner: Head of Sales; steward: Sales Analyst
- Action codes: C-M2.1, C-S1.1, C-S1.2
- Lineage: core/data_contracts/domains/commercial_sales.yaml

Query as executed:

```text
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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

</Details>

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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

<BigValue data={kpi_com_010} value="value" title="KPI-COM-010" />

_Data as of <Value data={kpi_com_010} column="period" />_

<Details title="Source and definition: KPI-COM-010">

- Catalog id: KPI-COM-010
- Definition, target and threshold: core/kpi_catalog/KPI_Catalog.md, line 3523
- Owner: Head of Sales Controlling; steward: Sales Analyst
- Action codes: C-M2.1, C-S1.1, C-S1.2
- Lineage: core/data_contracts/domains/commercial_sales.yaml

Query as executed:

```text
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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

</Details>

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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

<BigValue data={kpi_com_011} value="value" title="KPI-COM-011" />

_Data as of <Value data={kpi_com_011} column="period" />_

<Details title="Source and definition: KPI-COM-011">

- Catalog id: KPI-COM-011
- Definition, target and threshold: core/kpi_catalog/KPI_Catalog.md, line 3577
- Owner: Head of Sales Controlling; steward: Sales Analyst
- Action codes: C-M2.1, C-S1.1, C-S1.2
- Lineage: core/data_contracts/domains/commercial_sales.yaml

Query as executed:

```text
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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

</Details>

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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

<BigValue data={kpi_com_004} value="value" title="KPI-COM-004" />

_Data as of <Value data={kpi_com_004} column="period" />_

<Details title="Source and definition: KPI-COM-004">

- Catalog id: KPI-COM-004
- Definition, target and threshold: core/kpi_catalog/KPI_Catalog.md, line 3212
- Owner: Head of Sales Controlling; steward: Sales Analyst
- Action codes: C-M2.1, C-S1.1, C-S1.2
- Lineage: core/data_contracts/domains/commercial_sales.yaml

Query as executed:

```text
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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

</Details>

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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

<BigValue data={kpi_fin_011} value="value" title="KPI-FIN-011" />

_Data as of <Value data={kpi_fin_011} column="period" />_

<Details title="Source and definition: KPI-FIN-011">

- Catalog id: KPI-FIN-011
- Definition, target and threshold: core/kpi_catalog/KPI_Catalog.md, line 4465
- Owner: Head of Controlling; steward: Controlling Analyst
- Action codes: C-M2.1, C-S1.1, C-S1.2
- Lineage: core/data_contracts/domains/commercial_sales.yaml

Query as executed:

```text
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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

</Details>

```sql kpi_com_006
SELECT
  metric_value AS value,
  'KPI-COM-006' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-006'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'KPI-COM-006'
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

<BigValue data={kpi_com_006} value="value" title="KPI-COM-006" />

_Data as of <Value data={kpi_com_006} column="period" />_

<Details title="Source and definition: KPI-COM-006">

- Catalog id: KPI-COM-006
- Definition, target and threshold: core/kpi_catalog/KPI_Catalog.md, line 3322
- Owner: Head of Sales Controlling; steward: Sales Analyst
- Action codes: C-M2.1, C-S1.1, C-S1.2
- Lineage: not set in the catalog

Query as executed:

```text
SELECT
  metric_value AS value,
  'KPI-COM-006' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-006'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'KPI-COM-006'
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

</Details>

```sql kpi_com_007
SELECT
  metric_value AS value,
  'KPI-COM-007' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-007'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'KPI-COM-007'
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

<BigValue data={kpi_com_007} value="value" title="KPI-COM-007" />

_Data as of <Value data={kpi_com_007} column="period" />_

<Details title="Source and definition: KPI-COM-007">

- Catalog id: KPI-COM-007
- Definition, target and threshold: core/kpi_catalog/KPI_Catalog.md, line 3367
- Owner: Head of Sales Controlling; steward: Sales Analyst
- Action codes: C-M2.1, C-S1.1, C-S1.2
- Lineage: not set in the catalog

Query as executed:

```text
SELECT
  metric_value AS value,
  'KPI-COM-007' AS label,
  period
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-007'
  AND period = (
    SELECT MAX(period)
    FROM gold.metric_observations
    WHERE kpi_id = 'KPI-COM-007'
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

</Details>

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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

<BigValue data={kpi_com_001} value="value" title="KPI-COM-001" />

_Data as of <Value data={kpi_com_001} column="period" />_

<Details title="Source and definition: KPI-COM-001">

- Catalog id: KPI-COM-001
- Definition, target and threshold: core/kpi_catalog/KPI_Catalog.md, line 3064
- Owner: Head of Sales Controlling; steward: Pricing Analyst
- Action codes: C-M2.1, C-S1.1, C-S1.2
- Lineage: core/data_contracts/domains/commercial_sales.yaml

Query as executed:

```text
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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

</Details>

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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

<BigValue data={kpi_com_002} value="value" title="KPI-COM-002" />

_Data as of <Value data={kpi_com_002} column="period" />_

<Details title="Source and definition: KPI-COM-002">

- Catalog id: KPI-COM-002
- Definition, target and threshold: core/kpi_catalog/KPI_Catalog.md, line 3110
- Owner: Head of Sales Controlling; steward: Pricing Analyst
- Action codes: C-M2.1, C-S1.1, C-S1.2
- Lineage: core/data_contracts/domains/commercial_sales.yaml

Query as executed:

```text
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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

</Details>

## 30-Second Layer — Trends

```sql kpi_com_013_trend
SELECT
  period,
  metric_value AS metric_value
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-013'
  AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
GROUP BY period, metric_value
ORDER BY period
```

<LineChart data={kpi_com_013_trend} x="period" y="metric_value" title="KPI-COM-013" />

```sql kpi_com_013_trend_as_of
SELECT
  MAX(period) AS as_of
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-013'
  AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
```

_Data as of <Value data={kpi_com_013_trend_as_of} column="as_of" />_

<Details title="Source and definition: KPI-COM-013">

- Catalog id: KPI-COM-013
- Definition, target and threshold: core/kpi_catalog/KPI_Catalog.md, line 4512
- Owner: Head of Controlling; steward: Controlling Analyst
- Action codes: C-M2.1, C-S1.1, C-S1.2
- Lineage: core/data_contracts/domains/commercial_sales.yaml, core/data_contracts/domains/executive.yaml, core/data_contracts/domains/finance.yaml

Query as executed:

```text
SELECT
  period,
  metric_value AS metric_value
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-013'
  AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
GROUP BY period, metric_value
ORDER BY period
```

<DataTable data={kpi_com_013_trend} downloadable=true />

</Details>

```sql kpi_com_009_trend
SELECT
  period,
  metric_value AS metric_value
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-009'
  AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
GROUP BY period, metric_value
ORDER BY period
```

<LineChart data={kpi_com_009_trend} x="period" y="metric_value" title="KPI-COM-009" />

```sql kpi_com_009_trend_as_of
SELECT
  MAX(period) AS as_of
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-009'
  AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
```

_Data as of <Value data={kpi_com_009_trend_as_of} column="as_of" />_

<Details title="Source and definition: KPI-COM-009">

- Catalog id: KPI-COM-009
- Definition, target and threshold: core/kpi_catalog/KPI_Catalog.md, line 3468
- Owner: Head of Sales Controlling; steward: Sales Analyst
- Action codes: C-M2.1, C-S1.1, C-S1.2
- Lineage: core/data_contracts/domains/commercial_sales.yaml, core/data_contracts/domains/finance.yaml

Query as executed:

```text
SELECT
  period,
  metric_value AS metric_value
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-009'
  AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
GROUP BY period, metric_value
ORDER BY period
```

<DataTable data={kpi_com_009_trend} downloadable=true />

</Details>

```sql kpi_com_008_trend
SELECT
  period,
  metric_value AS metric_value
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-008'
  AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
GROUP BY period, metric_value
ORDER BY period
```

<LineChart data={kpi_com_008_trend} x="period" y="metric_value" title="KPI-COM-008" />

```sql kpi_com_008_trend_as_of
SELECT
  MAX(period) AS as_of
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-008'
  AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
```

_Data as of <Value data={kpi_com_008_trend_as_of} column="as_of" />_

<Details title="Source and definition: KPI-COM-008">

- Catalog id: KPI-COM-008
- Definition, target and threshold: core/kpi_catalog/KPI_Catalog.md, line 3413
- Owner: Head of Sales Controlling; steward: Sales Analyst
- Action codes: C-M2.1, C-S1.1, C-S1.2
- Lineage: core/data_contracts/domains/commercial_sales.yaml, core/data_contracts/domains/executive.yaml

Query as executed:

```text
SELECT
  period,
  metric_value AS metric_value
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-008'
  AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
GROUP BY period, metric_value
ORDER BY period
```

<DataTable data={kpi_com_008_trend} downloadable=true />

</Details>

> Core formula: KPI-COM-013 = f(KPI-COM-005, KPI-COM-009, KPI-COM-008, KPI-COM-010, KPI-COM-011, KPI-COM-004)
> Impact logic: Improving KPI-COM-005 is the primary lever for maximizing KPI-COM-013.
