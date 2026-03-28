"""
SQL Builder

Generates SQL queries from KPI catalog and data contract definitions.
Replaces DAX expressions with standard SQL for DuckDB / Trino / Postgres.

Each KPI in the IR with a measure_spec (dax_expression, kpi_key) gets
translated to a SQL query that can be embedded in an Evidence page.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


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
        return kpi_id.lower().replace("-", "_")

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
