"""
SQL Builder

Generates SQL queries from KPI catalog and data contract definitions.
Replaces DAX expressions with standard SQL for DuckDB / Trino / Postgres.

Each KPI in the IR with a measure_spec (dax_expression, kpi_key) gets
translated to a SQL query that can be embedded in an Evidence page.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

# Long-format contract of gold.metric_evidence (300-second detail layer): one row per
# KPI, period and dimension combination. The dimension columns carry governed
# evidence_columns token names; the value is the Power BI (table, column) each token
# stands for, identical to EVIDENCE_DIM_TOKENS in
# products/fabric/powerbi/tooling/page_scaffold_generator/config_loader.py
# (pinned by test_sql_builder.py, as is evidence_app/sources/gold/metric_evidence.sql).
METRIC_EVIDENCE_DIMENSIONS: Dict[str, Tuple[str, str]] = {
    "entity": ("dim_org", "OrgName"),
    "region": ("dim_org", "Region"),
    "country": ("dim_org", "Country"),
    "product_category": ("dim_product", "Category"),
    "promotion": ("dim_promo", "PromoName"),
    "mechanic": ("dim_promo", "Promo Mechanic"),
}
METRIC_EVIDENCE_COLUMNS: Tuple[str, ...] = (
    "kpi_id", "period", *METRIC_EVIDENCE_DIMENSIONS, "metric_value"
)
# Selected on every detail row, so a bracket naming them adds nothing.
_ALWAYS_SELECTED = frozenset({"kpi_id", "period", "metric_value"})
_KPI_ID_SHAPE = re.compile(r"^KPI-[A-Z]+-\d+$")


def resolve_evidence_columns(
    tokens: Iterable[str], known_kpi_ids: Iterable[str]
) -> Tuple[List[str], List[str]]:
    """Split bracket evidence_columns into gold.metric_evidence dimension columns and KPI ids.

    A governed KPI id becomes part of the ``kpi_id`` filter; a dimension token
    (``region``) or Power BI column (``dim_org.Region``) becomes the contract column.
    Anything else raises: a dimension the long table does not carry, or a KPI id
    outside the catalog, is a generator error, never a column passed through as SQL.
    """
    known = set(known_kpi_ids)
    by_pbi_column = {f"{t}.{c}".lower(): name for name, (t, c) in METRIC_EVIDENCE_DIMENSIONS.items()}
    dimensions: List[str] = []
    kpi_ids: List[str] = []
    unresolved: List[str] = []
    for token in tokens:
        if not isinstance(token, str) or not token.strip():
            continue
        token = token.strip()
        if token.lower() in _ALWAYS_SELECTED:
            continue
        column = token.lower() if token.lower() in METRIC_EVIDENCE_DIMENSIONS else by_pbi_column.get(token.lower())
        if token in known:
            target, value = kpi_ids, token
        elif column is not None and not _KPI_ID_SHAPE.match(token):
            target, value = dimensions, column
        else:
            unresolved.append(token)
            continue
        if value not in target:
            target.append(value)
    if unresolved:
        raise ValueError(
            f"component_300s.evidence_columns {unresolved} resolve neither to a column of "
            f"gold.metric_evidence {sorted(METRIC_EVIDENCE_DIMENSIONS)} nor to a governed KPI id. "
            "Add the dimension to METRIC_EVIDENCE_DIMENSIONS in sql_builder.py and to "
            "evidence_app/sources/gold/metric_evidence.sql, or fix the bracket."
        )
    return dimensions, kpi_ids


def _kpi_filter(kpi_ids: Sequence[str]) -> str:
    safe = [k.replace("'", "''") for k in kpi_ids]
    if len(safe) == 1:
        return f"kpi_id = '{safe[0]}'"
    return "kpi_id IN (" + ", ".join(f"'{k}'" for k in safe) + ")"


# DAX aggregation → SQL aggregation mapping
DAX_TO_SQL: Dict[str, str] = {
    "SUM":      "SUM",
    "AVERAGE":  "AVG",
    "COUNT":    "COUNT",
    "COUNTROWS": "COUNT(*)",
    "MIN":      "MIN",
    "MAX":      "MAX",
    "DISTINCTCOUNT": "COUNT(DISTINCT",
}


class SqlBuilder:
    """Generate SQL queries from KPI definitions."""

    def __init__(self, schema: str = "gold") -> None:
        self.schema = schema

    def kpi_to_query_name(self, kpi_id: str) -> str:
        """Convert KPI ID to a valid SQL / Evidence query name."""
        return re.sub(r"[^a-z0-9_]", "_", kpi_id.lower().replace("-", "_"))

    def dax_to_sql_expression(self, dax: str) -> str:
        """
        Best-effort translation of simple DAX to SQL.

        Handles: SUM(table[column]), AVERAGE(table[column]),
        DIVIDE(a, b), COUNTROWS(table).
        Complex DAX (CALCULATE, FILTER, etc.) returns a placeholder comment.
        """
        if not dax:
            return "-- TODO: translate complex DAX"

        # DIVIDE(a, b) → CASE WHEN b = 0 THEN NULL ELSE a / b END
        # Use a balanced-paren split to find the comma separating the two args.
        if re.match(r"DIVIDE\s*\(", dax, re.IGNORECASE):
            inner = dax[dax.index("(") + 1 : dax.rindex(")")]
            # Split on the top-level comma (not inside nested parens).
            depth, split_pos = 0, -1
            for i, ch in enumerate(inner):
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                elif ch == "," and depth == 0:
                    split_pos = i
                    break
            if split_pos > 0:
                a = self.dax_to_sql_expression(inner[:split_pos].strip())
                b = self.dax_to_sql_expression(inner[split_pos + 1 :].strip())
                return f"CASE WHEN ({b}) = 0 THEN NULL ELSE ({a}) * 1.0 / ({b}) END"

        # SUM(table[column]) → SUM(column)
        agg_match = re.match(r"(\w+)\s*\(\s*(\w+)\[(\w+)\]\s*\)", dax, re.IGNORECASE)
        if agg_match:
            func = agg_match.group(1).upper()
            column = agg_match.group(3)
            sql_func = DAX_TO_SQL.get(func)
            if sql_func:
                if sql_func == "COUNT(*)" :
                    return "COUNT(*)"
                if sql_func.startswith("COUNT(DISTINCT"):
                    return f"COUNT(DISTINCT {column})"
                return f"{sql_func}({column})"

        # Fallback: return as comment
        return f"-- TODO: translate DAX: {dax}"

    def build_kpi_headline_query(
        self,
        query_name: str,
        table: str,
        measure_expression: str,
        label: str,
        time_filter: str = "period = (SELECT MAX(period) FROM {table})",
    ) -> str:
        """Build a headline KPI query for the 3-second layer."""
        where = time_filter.format(table=table)
        return (
            f"```sql {query_name}\n"
            f"SELECT\n"
            f"  {measure_expression} AS value,\n"
            f"  '{label}' AS label\n"
            f"FROM {table}\n"
            f"WHERE {where}\n"
            f"```"
        )

    def build_metric_headline_query(
        self,
        query_name: str,
        kpi_id: str,
        label: str,
        table: str = "gold.metric_observations",
        period_column: str = "period",
        value_column: str = "metric_value",
        period_filter: Optional[str] = None,
    ) -> str:
        """Headline value at the latest period; with `period_filter` the latest period inside the slice (BC-DV-08)."""
        safe_kpi_id = kpi_id.replace("'", "''")
        safe_label = label.replace("'", "''")
        inner = f"\n      AND {period_filter}" if period_filter else ""
        return (
            f"```sql {query_name}\n"
            f"SELECT\n"
            f"  {value_column} AS value,\n"
            f"  '{safe_label}' AS label,\n"
            f"  {period_column}\n"
            f"FROM {table}\n"
            f"WHERE kpi_id = '{safe_kpi_id}'\n"
            f"  AND {period_column} = (\n"
            f"    SELECT MAX({period_column})\n"
            f"    FROM {table}\n"
            f"    WHERE kpi_id = '{safe_kpi_id}'{inner}\n"
            f"  )\n"
            f"```"
        )

    def build_trend_query(
        self,
        query_name: str,
        table: str,
        measure_expression: str,
        time_column: str = "period",
        segment_column: Optional[str] = None,
    ) -> str:
        """Build a trend query for the 30-second layer."""
        select_cols = [time_column, f"{measure_expression} AS metric_value"]
        group_cols = [time_column]
        if segment_column:
            select_cols.insert(1, segment_column)
            group_cols.append(segment_column)

        select_str = ",\n  ".join(select_cols)
        group_str = ", ".join(group_cols)
        return (
            f"```sql {query_name}\n"
            f"SELECT\n"
            f"  {select_str}\n"
            f"FROM {table}\n"
            f"GROUP BY {group_str}\n"
            f"ORDER BY {time_column}\n"
            f"```"
        )

    def build_metric_trend_query(
        self,
        query_name: str,
        kpi_id: str,
        table: str = "gold.metric_observations",
        period_column: str = "period",
        value_column: str = "metric_value",
        segment_column: Optional[str] = None,
        period_filter: Optional[str] = None,
    ) -> str:
        safe_kpi_id = kpi_id.replace("'", "''")
        where = f"WHERE kpi_id = '{safe_kpi_id}'" + (f"\n  AND {period_filter}" if period_filter else "")
        select_cols = [period_column, f"{value_column} AS metric_value"]
        group_cols = [period_column, value_column]
        if segment_column:
            select_cols.insert(1, segment_column)
            group_cols.insert(1, segment_column)
        select_str = ",\n  ".join(select_cols)
        group_str = ", ".join(group_cols)
        return (
            f"```sql {query_name}\n"
            f"SELECT\n"
            f"  {select_str}\n"
            f"FROM {table}\n"
            f"{where}\n"
            f"GROUP BY {group_str}\n"
            f"ORDER BY {period_column}\n"
            f"```"
        )

    def build_detail_query(
        self,
        query_name: str,
        table: str,
        columns: List[str],
        order_by: str = "period DESC",
        limit: int = 500,
    ) -> str:
        """Build a detail query for the 300-second layer."""
        cols = ", ".join(columns)
        return (
            f"```sql {query_name}\n"
            f"SELECT\n"
            f"  {cols}\n"
            f"FROM {table}\n"
            f"ORDER BY {order_by}\n"
            f"LIMIT {limit}\n"
            f"```"
        )

    def build_metric_detail_query(
        self,
        query_name: str,
        kpi_ids: Sequence[str],
        dimensions: Sequence[str],
        table: str = "gold.metric_evidence",
        order_by: str = "period DESC",
        limit: int = 500,
        period_filter: Optional[str] = None,
    ) -> str:
        """Detail rows of the long gold.metric_evidence table for the given KPIs."""
        unknown = [d for d in dimensions if d not in METRIC_EVIDENCE_DIMENSIONS]
        if unknown or not kpi_ids:
            raise ValueError(f"detail query needs KPI ids and contract dimensions, got {list(kpi_ids)}, {unknown}")
        cols = ", ".join([*dimensions, "kpi_id", "period", "metric_value"])
        where = f"WHERE {_kpi_filter(kpi_ids)}" + (f"\n  AND {period_filter}" if period_filter else "")
        return (
            f"```sql {query_name}\n"
            f"SELECT\n"
            f"  {cols}\n"
            f"FROM {table}\n"
            f"{where}\n"
            f"ORDER BY {order_by}\n"
            f"LIMIT {limit}\n"
            f"```"
        )

    def build_as_of_query(
        self,
        query_name: str,
        kpi_id: str | Sequence[str],
        table: str = "gold.metric_observations",
        period_column: str = "period",
        period_filter: Optional[str] = None,
    ) -> str:
        """Freshness stamp per chart (BC-TRANS-04): the latest period the chart shows."""
        kpi_ids = [kpi_id] if isinstance(kpi_id, str) else list(kpi_id)
        where = f"WHERE {_kpi_filter(kpi_ids)}" + (f"\n  AND {period_filter}" if period_filter else "")
        return (
            f"```sql {query_name}\n"
            f"SELECT\n"
            f"  MAX({period_column}) AS as_of\n"
            f"FROM {table}\n"
            f"{where}\n"
            f"```"
        )

    def build_period_options_query(
        self,
        query_name: str,
        table: str = "gold.metric_observations",
        period_column: str = "period",
    ) -> str:
        """The periods the date-range filter offers (BC-DV-08)."""
        return (
            f"```sql {query_name}\n"
            f"SELECT DISTINCT\n"
            f"  {period_column}\n"
            f"FROM {table}\n"
            f"ORDER BY {period_column}\n"
            f"```"
        )

    def infer_table_from_kpi(self, kpi_node: Dict[str, Any]) -> str:
        """Infer the gold table name from a KPI node's measure_spec or metadata."""
        spec = kpi_node.get("measure_spec", {})
        dax = spec.get("dax_expression", "")
        # Extract table name from SUM(table[col]) pattern
        m = re.search(r"(\w+)\[\w+\]", dax)
        if m:
            return f"{self.schema}.{m.group(1)}"
        # Fallback: derive from KPI domain
        domain = kpi_node.get("domain", "unknown")
        return f"{self.schema}.fact_{domain.lower()}"
