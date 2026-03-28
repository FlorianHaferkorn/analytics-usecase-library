"""
dbt Metric Generator

Reads KPI definitions from ir_v1.json and generates dbt metric YAML files.
This is the OSS equivalent of generate_tmdl_measures.ps1.

Usage:
    python -m products.open_source_stack.tooling.metric_generator.generate_dbt_metrics \
        --ir-path tooling/ir/out/ir_v1.json \
        --output-dir products/open_source_stack/dbt_project/models/metrics
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


# DAX aggregation → dbt metric type mapping
DAX_AGG_TO_DBT: Dict[str, str] = {
    "SUM": "simple",
    "AVERAGE": "simple",
    "COUNT": "simple",
    "COUNTROWS": "simple",
    "DISTINCTCOUNT": "simple",
    "MIN": "simple",
    "MAX": "simple",
}

# DAX aggregation → dbt measure aggregation
DAX_AGG_TO_MEASURE: Dict[str, str] = {
    "SUM": "sum",
    "AVERAGE": "average",
    "COUNT": "count",
    "COUNTROWS": "count",
    "DISTINCTCOUNT": "count_distinct",
    "MIN": "min",
    "MAX": "max",
}


def _parse_dax_agg(dax: str) -> tuple[str, str, str]:
    """Parse DAX SUM(table[col]) → (agg_func, table, column)."""
    m = re.match(r"(\w+)\s*\(\s*(\w+)\[(\w+)\]\s*\)", dax.strip(), re.IGNORECASE)
    if m:
        return m.group(1).upper(), m.group(2), m.group(3)
    return "", "", ""


def kpi_to_metric(kpi_node: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Convert an IR KPI node to a dbt metric definition."""
    kpi_id = kpi_node.get("id", "")
    label = kpi_node.get("label", kpi_id)
    spec = kpi_node.get("measure_spec", {})
    dax = spec.get("dax_expression", "")

    if not dax:
        return None

    agg_func, table, column = _parse_dax_agg(dax)
    if not agg_func or agg_func not in DAX_AGG_TO_DBT:
        # Complex DAX — emit a placeholder
        return {
            "name": kpi_id.lower().replace("-", "_"),
            "label": label,
            "description": f"TODO: translate complex DAX: {dax}",
            "type": "derived",
            "type_params": {"expr": "1"},
            "meta": {"kpi_id": kpi_id, "source": "ir_v1.json", "needs_manual_review": True},
        }

    metric_name = kpi_id.lower().replace("-", "_")
    measure_name = f"{DAX_AGG_TO_MEASURE[agg_func]}_{column}"

    return {
        "name": metric_name,
        "label": label,
        "description": f"{label} ({agg_func} of {table}.{column})",
        "type": DAX_AGG_TO_DBT[agg_func],
        "type_params": {"measure": measure_name},
        "meta": {"kpi_id": kpi_id, "source": "ir_v1.json"},
    }


def generate_metrics_yaml(ir_path: Path) -> Dict[str, Any]:
    """Generate a dbt _metrics.yml structure from IR."""
    ir = json.loads(ir_path.read_text(encoding="utf-8-sig"))
    kpi_nodes = [n for n in ir.get("nodes", []) if n.get("type") == "kpi"]

    metrics = []
    for kpi in kpi_nodes:
        metric = kpi_to_metric(kpi)
        if metric:
            metrics.append(metric)

    return {"version": 2, "metrics": metrics}


def write_metrics_file(metrics_data: Dict[str, Any], output_path: Path) -> Path:
    """Write the metrics YAML file."""
    if yaml is None:
        raise ImportError("PyYAML is required: pip install pyyaml")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = yaml.dump(metrics_data, default_flow_style=False, sort_keys=False, allow_unicode=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate dbt metrics from IR")
    parser.add_argument("--ir-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    metrics = generate_metrics_yaml(args.ir_path)
    out = write_metrics_file(metrics, args.output_dir / "_metrics.yml")
    print(f"  Generated {len(metrics.get('metrics', []))} metrics → {out}")


if __name__ == "__main__":
    main()
