-- Contract of gold.metric_evidence (300-second detail layer), long format: one row
-- per KPI, period and dimension combination. Columns = METRIC_EVIDENCE_COLUMNS in
-- tooling/page_generator/sql_builder.py (pinned by test_sql_builder.py).
-- One all-NULL carrier row, same reason as metric_observations.sql. No KPI values.
SELECT
  CAST(NULL AS VARCHAR) AS kpi_id,
  CAST(NULL AS DATE) AS period,
  CAST(NULL AS VARCHAR) AS entity,
  CAST(NULL AS VARCHAR) AS region,
  CAST(NULL AS VARCHAR) AS country,
  CAST(NULL AS VARCHAR) AS product_category,
  CAST(NULL AS VARCHAR) AS promotion,
  CAST(NULL AS VARCHAR) AS mechanic,
  CAST(NULL AS DOUBLE) AS metric_value
