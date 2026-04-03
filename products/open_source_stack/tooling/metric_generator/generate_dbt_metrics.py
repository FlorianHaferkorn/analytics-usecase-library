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
from typing import Any, Dict, List, Optional, Set

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


def _collect_required_kpi_ids(ir: Dict[str, Any], use_cases: Optional[List[str]] = None) -> List[str]:
    use_case_objects = ir.get("objects", {}).get("use_cases", {})
    measure_specs = ir.get("measure_spec", {})
    selected = use_cases or sorted(use_case_objects.keys())
    ordered: List[str] = []
    seen: Set[str] = set()

    def add_with_dependencies(kpi_id: str) -> None:
        if not isinstance(kpi_id, str) or not kpi_id:
            return
        spec = measure_specs.get(kpi_id, {}) if isinstance(measure_specs, dict) else {}
        dependencies = spec.get("depends_on_measures", []) if isinstance(spec, dict) else []
        if isinstance(dependencies, list):
            for dep in dependencies:
                add_with_dependencies(dep)
        if kpi_id not in seen:
            seen.add(kpi_id)
            ordered.append(kpi_id)

    for use_case_id in selected:
        use_case = use_case_objects.get(use_case_id, {}) if isinstance(use_case_objects, dict) else {}
        orch = use_case.get("orchestration", {}) if isinstance(use_case, dict) else {}
        for candidate in [orch.get("strategic_kpi_id")]:
            if isinstance(candidate, str) and candidate:
                add_with_dependencies(candidate)
        for key in ("influencing_kpi_ids", "supporting_kpi_ids"):
            values = orch.get(key, []) if isinstance(orch, dict) else []
            if isinstance(values, list):
                for value in values:
                    if isinstance(value, str) and value:
                        add_with_dependencies(value)

    return ordered


def kpi_to_core_metric(
    kpi_id: str,
    kpi_node: Dict[str, Any],
    measure_spec: Dict[str, Any],
    required_by_use_cases: List[str],
) -> Dict[str, Any]:
    label = kpi_node.get("label") or kpi_node.get("title") or measure_spec.get("kpi_key") or kpi_id
    description = (
        measure_spec.get("purpose")
        or measure_spec.get("description")
        or f"Core-governed KPI {kpi_id} exposed via generic metric observations"
    )
    metric_name = kpi_id.lower().replace("-", "_").replace(".", "_")
    return {
        "name": metric_name,
        "label": label,
        "description": description,
        "type": "simple",
        "type_params": {"measure": "metric_value"},
        "meta": {
            "kpi_id": kpi_id,
            "source": "core_ir",
            "calculation_logic_source": "core",
            "required_by_use_cases": required_by_use_cases,
            "semantic_projection": {
                "table": "metric_observations",
                "filter_column": "kpi_id",
                "filter_value": kpi_id,
            },
        },
    }


def generate_metrics_yaml(
    ir_path: Path,
    mode: str = "legacy",
    use_cases: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Generate a dbt _metrics.yml structure from IR."""
    ir = json.loads(ir_path.read_text(encoding="utf-8-sig"))

    if mode == "core":
        objects = ir.get("objects", {})
        kpi_objects = objects.get("kpis", {}) if isinstance(objects, dict) else {}
        measure_specs = ir.get("measure_spec", {}) if isinstance(ir.get("measure_spec", {}), dict) else {}
        selected_use_cases = use_cases or sorted((objects.get("use_cases", {}) or {}).keys())
        required_kpi_ids = _collect_required_kpi_ids(ir, selected_use_cases)

        metrics = []
        for kpi_id in required_kpi_ids:
            kpi_node = kpi_objects.get(kpi_id, {}) if isinstance(kpi_objects, dict) else {}
            metric = kpi_to_core_metric(
                kpi_id=kpi_id,
                kpi_node=kpi_node if isinstance(kpi_node, dict) else {},
                measure_spec=measure_specs.get(kpi_id, {}) if isinstance(measure_specs.get(kpi_id, {}), dict) else {},
                required_by_use_cases=selected_use_cases,
            )
            metrics.append(metric)

        return {"version": 2, "metrics": metrics}

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
    parser.add_argument("--mode", choices=["legacy", "core"], default="legacy")
    parser.add_argument("--use-cases", default="", help="Comma-separated use case IDs to scope generated metrics")
    args = parser.parse_args()

    use_cases = [item.strip() for item in args.use_cases.split(",") if item.strip()]
    metrics = generate_metrics_yaml(args.ir_path, mode=args.mode, use_cases=use_cases or None)
    out = write_metrics_file(metrics, args.output_dir / "_metrics.yml")
    print(f"  Generated {len(metrics.get('metrics', []))} metrics → {out}")


if __name__ == "__main__":
    main()
