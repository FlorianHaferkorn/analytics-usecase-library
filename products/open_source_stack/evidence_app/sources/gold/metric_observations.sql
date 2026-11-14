-- Contract of gold.metric_observations as the page generator queries it
-- (tooling/page_generator/sql_builder.py): kpi_id, period, metric_value.
-- One all-NULL carrier row: Evidence 40 writes a zero-row result as an
-- unreadable parquet file (KNOWN_ERRORS: Evidence build). A NULL kpi_id matches
-- no KPI filter, so no page shows a value. KPI values come from the governed
-- pipeline (dbt), never from this file.
SELECT
  CAST(NULL AS VARCHAR) AS kpi_id,
  CAST(NULL AS DATE) AS period,
  CAST(NULL AS DOUBLE) AS metric_value
