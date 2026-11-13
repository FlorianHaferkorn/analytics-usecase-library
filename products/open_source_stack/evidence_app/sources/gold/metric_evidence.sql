-- Contract of gold.metric_evidence (300-second detail layer):
-- kpi_id, period, entity, metric_value. One all-NULL carrier row, same reason
-- as metric_observations.sql. No KPI values.
SELECT
  CAST(NULL AS VARCHAR) AS kpi_id,
  CAST(NULL AS DATE) AS period,
  CAST(NULL AS VARCHAR) AS entity,
  CAST(NULL AS DOUBLE) AS metric_value
