---
title: Promotion Effectiveness
use_case: COM-004
generated: true
---

# Promotion Effectiveness

_Promotion Effectiveness — Detail_

## Filters

```sql period_options
SELECT DISTINCT
  period
FROM gold.metric_observations
ORDER BY period
```

<DateRange name=period_range data={period_options} dates=period />

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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

<BigValue data={kpi_com_016} value="value" title="KPI-COM-016" />

_Data as of <Value data={kpi_com_016} column="period" />_

<Details title="Source and definition: KPI-COM-016">

- Catalog id: KPI-COM-016
- Definition, target and threshold: core/kpi_catalog/KPI_Catalog.md, line 4886
- Owner: Head of Marketing Controlling; steward: Trade Marketing Analyst
- Action codes: C-P4.1, C-M2.1, C-M2.2
- Lineage: core/data_contracts/domains/commercial_sales.yaml

Query as executed:

```text
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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

</Details>

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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

<BigValue data={kpi_com_021} value="value" title="KPI-COM-021" />

_Data as of <Value data={kpi_com_021} column="period" />_

<Details title="Source and definition: KPI-COM-021">

- Catalog id: KPI-COM-021
- Definition, target and threshold: core/kpi_catalog/KPI_Catalog.md, line 5445
- Owner: Head of Marketing Controlling; steward: Trade Marketing Analyst
- Action codes: C-P4.1, C-M2.1, C-M2.2
- Lineage: core/data_contracts/domains/commercial_sales.yaml

Query as executed:

```text
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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

</Details>

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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

<BigValue data={kpi_fin_012} value="value" title="KPI-FIN-012" />

_Data as of <Value data={kpi_fin_012} column="period" />_

<Details title="Source and definition: KPI-FIN-012">

- Catalog id: KPI-FIN-012
- Definition, target and threshold: core/kpi_catalog/KPI_Catalog.md, line 4938
- Owner: Head of Marketing Controlling; steward: Trade Marketing Analyst
- Action codes: C-P4.1, C-M2.1, C-M2.2
- Lineage: core/data_contracts/domains/commercial_sales.yaml

Query as executed:

```text
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
- Action codes: C-P4.1, C-M2.1, C-M2.2
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
- Action codes: C-P4.1, C-M2.1, C-M2.2
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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

<BigValue data={kpi_com_003} value="value" title="KPI-COM-003" />

_Data as of <Value data={kpi_com_003} column="period" />_

<Details title="Source and definition: KPI-COM-003">

- Catalog id: KPI-COM-003
- Definition, target and threshold: core/kpi_catalog/KPI_Catalog.md, line 3156
- Owner: Head of Sales Controlling; steward: Pricing Analyst
- Action codes: C-P4.1, C-M2.1, C-M2.2
- Lineage: core/data_contracts/domains/commercial_sales.yaml

Query as executed:

```text
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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

</Details>

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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

<BigValue data={kpi_com_018} value="value" title="KPI-COM-018" />

_Data as of <Value data={kpi_com_018} column="period" />_

<Details title="Source and definition: KPI-COM-018">

- Catalog id: KPI-COM-018
- Definition, target and threshold: core/kpi_catalog/KPI_Catalog.md, line 5092
- Owner: Head of Marketing Controlling; steward: Trade Marketing Analyst
- Action codes: C-P4.1, C-M2.1, C-M2.2
- Lineage: core/data_contracts/domains/commercial_sales.yaml

Query as executed:

```text
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
- Action codes: C-P4.1, C-M2.1, C-M2.2
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
- Action codes: C-P4.1, C-M2.1, C-M2.2
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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

<BigValue data={kpi_com_020} value="value" title="KPI-COM-020" />

_Data as of <Value data={kpi_com_020} column="period" />_

<Details title="Source and definition: KPI-COM-020">

- Catalog id: KPI-COM-020
- Definition, target and threshold: core/kpi_catalog/KPI_Catalog.md, line 5399
- Owner: Head of Marketing Controlling; steward: Trade Marketing Analyst
- Action codes: C-P4.1, C-M2.1, C-M2.2
- Lineage: not set in the catalog

Query as executed:

```text
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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

</Details>

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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

<BigValue data={kpi_com_017} value="value" title="KPI-COM-017" />

_Data as of <Value data={kpi_com_017} column="period" />_

<Details title="Source and definition: KPI-COM-017">

- Catalog id: KPI-COM-017
- Definition, target and threshold: core/kpi_catalog/KPI_Catalog.md, line 5044
- Owner: Head of Marketing Controlling; steward: Trade Marketing Analyst
- Action codes: C-P4.1, C-M2.1, C-M2.2
- Lineage: not set in the catalog

Query as executed:

```text
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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

</Details>

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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

<BigValue data={kpi_com_014} value="value" title="KPI-COM-014" />

_Data as of <Value data={kpi_com_014} column="period" />_

<Details title="Source and definition: KPI-COM-014">

- Catalog id: KPI-COM-014
- Definition, target and threshold: core/kpi_catalog/KPI_Catalog.md, line 4774
- Owner: Head of Marketing Controlling; steward: Trade Marketing Analyst
- Action codes: C-P4.1, C-M2.1, C-M2.2
- Lineage: not set in the catalog

Query as executed:

```text
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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

</Details>

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
      AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
  )
```

<BigValue data={kpi_com_015} value="value" title="KPI-COM-015" />

_Data as of <Value data={kpi_com_015} column="period" />_

<Details title="Source and definition: KPI-COM-015">

- Catalog id: KPI-COM-015
- Definition, target and threshold: core/kpi_catalog/KPI_Catalog.md, line 4821
- Owner: Head of Marketing Controlling; steward: Trade Marketing Analyst
- Action codes: C-P4.1, C-M2.1, C-M2.2
- Lineage: not set in the catalog

Query as executed:

```text
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
- Action codes: C-P4.1, C-M2.1, C-M2.2
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
- Action codes: C-P4.1, C-M2.1, C-M2.2
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

## 30-Second Layer — Trends

```sql kpi_com_016_trend
SELECT
  period,
  metric_value AS metric_value
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-016'
  AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
GROUP BY period, metric_value
ORDER BY period
```

<LineChart data={kpi_com_016_trend} x="period" y="metric_value" title="KPI-COM-016" />

```sql kpi_com_016_trend_as_of
SELECT
  MAX(period) AS as_of
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-016'
  AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
```

_Data as of <Value data={kpi_com_016_trend_as_of} column="as_of" />_

<Details title="Source and definition: KPI-COM-016">

- Catalog id: KPI-COM-016
- Definition, target and threshold: core/kpi_catalog/KPI_Catalog.md, line 4886
- Owner: Head of Marketing Controlling; steward: Trade Marketing Analyst
- Action codes: C-P4.1, C-M2.1, C-M2.2
- Lineage: core/data_contracts/domains/commercial_sales.yaml

Query as executed:

```text
SELECT
  period,
  metric_value AS metric_value
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-016'
  AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
GROUP BY period, metric_value
ORDER BY period
```

<DataTable data={kpi_com_016_trend} downloadable=true />

</Details>

```sql kpi_com_021_trend
SELECT
  period,
  metric_value AS metric_value
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-021'
  AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
GROUP BY period, metric_value
ORDER BY period
```

<LineChart data={kpi_com_021_trend} x="period" y="metric_value" title="KPI-COM-021" />

```sql kpi_com_021_trend_as_of
SELECT
  MAX(period) AS as_of
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-021'
  AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
```

_Data as of <Value data={kpi_com_021_trend_as_of} column="as_of" />_

<Details title="Source and definition: KPI-COM-021">

- Catalog id: KPI-COM-021
- Definition, target and threshold: core/kpi_catalog/KPI_Catalog.md, line 5445
- Owner: Head of Marketing Controlling; steward: Trade Marketing Analyst
- Action codes: C-P4.1, C-M2.1, C-M2.2
- Lineage: core/data_contracts/domains/commercial_sales.yaml

Query as executed:

```text
SELECT
  period,
  metric_value AS metric_value
FROM gold.metric_observations
WHERE kpi_id = 'KPI-COM-021'
  AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
GROUP BY period, metric_value
ORDER BY period
```

<DataTable data={kpi_com_021_trend} downloadable=true />

</Details>

```sql kpi_fin_012_trend
SELECT
  period,
  metric_value AS metric_value
FROM gold.metric_observations
WHERE kpi_id = 'KPI-FIN-012'
  AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
GROUP BY period, metric_value
ORDER BY period
```

<LineChart data={kpi_fin_012_trend} x="period" y="metric_value" title="KPI-FIN-012" />

```sql kpi_fin_012_trend_as_of
SELECT
  MAX(period) AS as_of
FROM gold.metric_observations
WHERE kpi_id = 'KPI-FIN-012'
  AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
```

_Data as of <Value data={kpi_fin_012_trend_as_of} column="as_of" />_

<Details title="Source and definition: KPI-FIN-012">

- Catalog id: KPI-FIN-012
- Definition, target and threshold: core/kpi_catalog/KPI_Catalog.md, line 4938
- Owner: Head of Marketing Controlling; steward: Trade Marketing Analyst
- Action codes: C-P4.1, C-M2.1, C-M2.2
- Lineage: core/data_contracts/domains/commercial_sales.yaml

Query as executed:

```text
SELECT
  period,
  metric_value AS metric_value
FROM gold.metric_observations
WHERE kpi_id = 'KPI-FIN-012'
  AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
GROUP BY period, metric_value
ORDER BY period
```

<DataTable data={kpi_fin_012_trend} downloadable=true />

</Details>

> Core formula: KPI-COM-016 = f(KPI-COM-021, KPI-FIN-012, KPI-COM-003, KPI-COM-018)
> Impact logic: Improving KPI-COM-021 is the primary lever for maximizing KPI-COM-016.

## 300-Second Layer — Diagnostics

```sql detail_data
SELECT
  promotion, product_category, mechanic, KPI-COM-021, KPI-COM-016, KPI-COM-003, KPI-COM-018, KPI-COM-015
FROM gold.metric_evidence
WHERE kpi_id = 'KPI-COM-016'
  AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
ORDER BY period DESC
LIMIT 500
```

<DataTable data={detail_data} downloadable=true />

```sql detail_data_as_of
SELECT
  MAX(period) AS as_of
FROM gold.metric_evidence
WHERE kpi_id = 'KPI-COM-016'
  AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
```

_Data as of <Value data={detail_data_as_of} column="as_of" />_

<Details title="Source and definition: KPI-COM-016">

- Catalog id: KPI-COM-016
- Definition, target and threshold: core/kpi_catalog/KPI_Catalog.md, line 4886
- Owner: Head of Marketing Controlling; steward: Trade Marketing Analyst
- Action codes: C-P4.1, C-M2.1, C-M2.2
- Lineage: core/data_contracts/domains/commercial_sales.yaml

Query as executed:

```text
SELECT
  promotion, product_category, mechanic, KPI-COM-021, KPI-COM-016, KPI-COM-003, KPI-COM-018, KPI-COM-015
FROM gold.metric_evidence
WHERE kpi_id = 'KPI-COM-016'
  AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'
ORDER BY period DESC
LIMIT 500
```

</Details>

> Action panel enabled for this use case. Use the linked action codes and governance flow for execution.
