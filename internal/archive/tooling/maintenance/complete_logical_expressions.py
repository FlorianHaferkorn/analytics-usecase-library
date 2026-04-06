#!/usr/bin/env python3
"""
complete_logical_expressions.py
-------------------------------
Replaces placeholder logical expressions ('Fabric: see overlay / TMDL.')
in Measure Dictionary files with tool-agnostic pseudocode.

Sources:
1. Fabric overlay DAX expressions  → translated to pseudocode
2. KPI Catalog business definitions → used as fallback context
3. Measure metadata (dependencies, name patterns) → used to derive formulas

Run:
    python tooling/maintenance/complete_logical_expressions.py

Verify:
    grep -r "Fabric: see overlay" core/semantic_models/
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]

MEASURE_DICT_GLOB = "core/semantic_models/domains/*/Measure_Dictionary_*.md"
KPI_CATALOG_PATH = ROOT / "core" / "kpi_catalog" / "KPI_Catalog.md"
OVERLAY_PATH = ROOT / "products" / "fabric" / "powerbi" / "specs" / "fabric_measure_overlay.yaml"

PLACEHOLDER = "Fabric: see overlay / TMDL."

# ---------------------------------------------------------------------------
# 1. Parse KPI Catalog
# ---------------------------------------------------------------------------

def parse_kpi_catalog(path: Path) -> dict:
    """Return dict keyed by kpi_id with business definition, measure_name, lineage, depends_on."""
    text = path.read_text(encoding="utf-8")
    blocks = re.findall(r"```yaml\s*\n(.*?)```", text, re.DOTALL)
    catalog: dict = {}
    for block in blocks:
        try:
            items = yaml.safe_load(block)
        except yaml.YAMLError:
            continue
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            kpi_id = item.get("kpi_id", "")
            if not kpi_id:
                continue
            biz = item.get("business", {}) or {}
            tech = item.get("technical", {}) or {}
            catalog[kpi_id] = {
                "definition": biz.get("definition", ""),
                "purpose": biz.get("purpose", ""),
                "measure_name": tech.get("measure_name", ""),
                "lineage": tech.get("lineage", []) or [],
                "depends_on_measures": tech.get("depends_on_measures", []) or [],
            }
    return catalog


# ---------------------------------------------------------------------------
# 2. Parse Fabric Overlay (DAX expressions)
# ---------------------------------------------------------------------------

def parse_overlay(path: Path) -> dict:
    """Return dict keyed by dax_name (measure name) with dax_expression."""
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    overlay: dict = {}
    by_kpi_id: dict = {}
    for kpi_id, entry in data.items():
        if not isinstance(entry, dict):
            continue
        dax_name = entry.get("dax_name", "")
        dax_expr = entry.get("dax_expression", "")
        if dax_name:
            overlay[dax_name] = {"dax": dax_expr, "kpi_id": kpi_id}
        if kpi_id:
            by_kpi_id[kpi_id] = {"dax": dax_expr, "dax_name": dax_name}
    return overlay, by_kpi_id


# ---------------------------------------------------------------------------
# 3. DAX → Pseudocode translator
# ---------------------------------------------------------------------------

def translate_dax(dax: str, measure_name: str) -> str | None:
    """Translate a DAX expression to tool-agnostic pseudocode."""
    if not dax or not isinstance(dax, str):
        return None
    dax = dax.strip()
    # Skip TBD / BLANK placeholders
    if dax.startswith("-- TBD") or dax.strip() == "BLANK()":
        return None
    if "BLANK()" in dax and "TBD" in dax:
        return None

    result = dax

    # Handle VAR ... RETURN pattern: extract variable assignments and substitute
    var_pattern = re.compile(r"VAR\s+(\w+)\s*=\s*(.+?)(?=\n\s*VAR\s|\n\s*RETURN\s|\Z)", re.DOTALL | re.IGNORECASE)
    return_pattern = re.compile(r"RETURN\s+(.+)", re.DOTALL | re.IGNORECASE)

    vars_found = var_pattern.findall(result)
    return_match = return_pattern.search(result)

    if vars_found and return_match:
        # Build substitution map
        var_map = {}
        for var_name, var_expr in vars_found:
            var_map[var_name.strip()] = var_expr.strip().rstrip(",")

        final_expr = return_match.group(1).strip()
        # Substitute variables into the return expression
        for var_name, var_expr in var_map.items():
            # Replace word-boundary matches of variable name
            final_expr = re.sub(r'\b' + re.escape(var_name) + r'\b', var_expr, final_expr)
        result = final_expr
    elif return_match and not vars_found:
        result = return_match.group(1).strip()

    # Translate DIVIDE(a, b) → (a) / (b)
    def replace_divide(m):
        inner = m.group(1)
        # Find the top-level comma split
        depth = 0
        split_pos = -1
        for i, ch in enumerate(inner):
            if ch in ('(', '['):
                depth += 1
            elif ch in (')', ']'):
                depth -= 1
            elif ch == ',' and depth == 0:
                split_pos = i
                break
        if split_pos >= 0:
            a = inner[:split_pos].strip()
            b = inner[split_pos + 1:].strip()
            return f"({a}) / ({b})"
        return m.group(0)

    # Iteratively replace DIVIDE
    for _ in range(5):
        new_result = re.sub(r'DIVIDE\s*\(\s*((?:[^()]*|\((?:[^()]*|\([^()]*\))*\))*)\s*\)', replace_divide, result)
        if new_result == result:
            break
        result = new_result

    # Translate CALCULATE(expr, filter) → expr WHERE filter
    def replace_calculate(m):
        inner = m.group(1)
        depth = 0
        split_pos = -1
        for i, ch in enumerate(inner):
            if ch in ('(', '['):
                depth += 1
            elif ch in (')', ']'):
                depth -= 1
            elif ch == ',' and depth == 0:
                split_pos = i
                break
        if split_pos >= 0:
            expr = inner[:split_pos].strip()
            filt = inner[split_pos + 1:].strip()
            return f"{expr} WHERE {filt}"
        return inner

    for _ in range(5):
        new_result = re.sub(r'CALCULATE\s*\(\s*((?:[^()]*|\((?:[^()]*|\([^()]*\))*\))*)\s*\)', replace_calculate, result)
        if new_result == result:
            break
        result = new_result

    # Translate AVERAGEX(table, expr) → AVERAGE over table: expr
    result = re.sub(
        r'AVERAGEX\s*\(\s*(\w+(?:\s*\([^)]*\))?)\s*,\s*(.+?)\s*\)',
        r'AVERAGE over \1: \2',
        result,
        flags=re.DOTALL
    )

    # Translate COUNTROWS(table) → COUNT(table rows)
    result = re.sub(r'COUNTROWS\s*\(\s*(\w+)\s*\)', r'COUNT(\1 rows)', result)

    # Translate DISTINCTCOUNT(table[col]) → DISTINCT_COUNT(table[col])
    result = re.sub(r'DISTINCTCOUNT\s*\(', 'DISTINCT_COUNT(', result)

    # Translate SUMX(table, expr) → SUM over table: expr
    result = re.sub(
        r'SUMX\s*\(\s*(\w+)\s*,\s*(.+?)\s*\)',
        lambda m: f"SUM over {m.group(1)}: {m.group(2).strip()}",
        result,
        flags=re.DOTALL
    )

    # Remove extra whitespace / newlines
    result = re.sub(r'\s+', ' ', result).strip()

    # Remove leftover DAX keywords that don't apply
    result = result.replace("TRUE ()", "TRUE").replace("FALSE ()", "FALSE")

    # Clean up spacing around operators
    result = re.sub(r'\s*\*\s*', ' * ', result)
    result = re.sub(r'\s+', ' ', result).strip()

    return f"{measure_name} = {result}"


# ---------------------------------------------------------------------------
# 4. Derive expression from measure metadata
# ---------------------------------------------------------------------------

def derive_expression(measure: dict, kpi_catalog: dict) -> str:
    """Derive a logical expression from measure metadata when no DAX is available."""
    name = measure.get("measure_name", "")
    kpi_ref = measure.get("kpi_id_ref", "")
    deps = measure.get("dependencies", {}) or {}
    dep_cols = deps.get("columns", []) or []
    dep_measures = deps.get("measures", []) or []
    desc = (measure.get("documentation", {}) or {}).get("description", "")
    notes = (measure.get("documentation", {}) or {}).get("notes", "")

    # Try KPI catalog definition
    kpi_def = ""
    if kpi_ref and kpi_ref in kpi_catalog:
        kpi_entry = kpi_catalog[kpi_ref]
        kpi_def = kpi_entry.get("definition", "")

    # --- Pattern-based derivation ---

    name_lower = name.lower()

    # Single column dependency with SUM pattern
    if len(dep_cols) == 1 and not dep_measures:
        col = dep_cols[0]
        # Simple SUM measures (amounts, costs, counts of units, etc.)
        if any(kw in name_lower for kw in ("amount", "cost", "revenue", "sales", "volume", "units", "hours", "minutes")):
            return f"{name} = SUM({col})"
        if "count" in name_lower:
            if "DISTINCT" in col.upper() or "key" in col.lower() or "Key" in col:
                return f"{name} = DISTINCT_COUNT({col})"
            # Column is a flag or ID
            table = col.split("[")[0] if "[" in col else col
            return f"{name} = COUNT({table} rows)"
        if "index" in name_lower or "score" in name_lower:
            return f"{name} = SUM({col})"
        # Default for single column
        return f"{name} = SUM({col})"

    # Percentage / ratio with two measure dependencies
    if any(kw in name_lower for kw in ("% vs", "vs plan", "vs ly", "delta")):
        if len(dep_measures) >= 2:
            actual = dep_measures[0].strip("[]")
            comparator = dep_measures[1].strip("[]")
            return f"{name} = ([{actual}] - [{comparator}]) / [{comparator}]"
        if len(dep_measures) == 1 and dep_cols:
            actual = dep_measures[0].strip("[]")
            plan_col = dep_cols[0]
            return f"{name} = ([{actual}] - SUM({plan_col})) / SUM({plan_col})"

    # Percentage measures (ratio of two things)
    if "%" in name or "pct" in name_lower or "rate" in name_lower:
        if len(dep_measures) == 2:
            num = dep_measures[0].strip("[]")
            den = dep_measures[1].strip("[]")
            return f"{name} = [{num}] / [{den}]"
        if len(dep_cols) == 2:
            return f"{name} = SUM({dep_cols[0]}) / SUM({dep_cols[1]})"
        if dep_measures and dep_cols:
            num = dep_measures[0].strip("[]")
            den_col = dep_cols[0]
            return f"{name} = [{num}] / SUM({den_col})"

    # Margin amount = revenue - cost
    if "margin" in name_lower and "amount" in name_lower:
        if dep_measures and dep_cols:
            rev = dep_measures[0].strip("[]")
            cost_col = dep_cols[0]
            return f"{name} = [{rev}] - SUM({cost_col})"
        if len(dep_measures) >= 2:
            a = dep_measures[0].strip("[]")
            b = dep_measures[1].strip("[]")
            return f"{name} = [{a}] - [{b}]"

    # Margin % = margin / revenue
    if "margin" in name_lower and ("%" in name or "pct" in name_lower):
        if len(dep_measures) >= 2:
            num = dep_measures[0].strip("[]")
            den = dep_measures[1].strip("[]")
            return f"{name} = [{num}] / [{den}]"

    # Days-type measures (DSO, DIO, DPO)
    if "days" in name_lower or "day" in name_lower:
        if len(dep_cols) >= 2:
            return f"{name} = SUM({dep_cols[0]}) * 365 / SUM({dep_cols[1]})"
        if len(dep_measures) >= 2:
            a = dep_measures[0].strip("[]")
            b = dep_measures[1].strip("[]")
            return f"{name} = [{a}] + [{b}]"

    # Count measures
    if "count" in name_lower:
        if dep_cols:
            col = dep_cols[0]
            table = col.split("[")[0] if "[" in col else col
            if "key" in col.lower() or "id" in col.lower():
                return f"{name} = DISTINCT_COUNT({col})"
            return f"{name} = COUNT({table} rows)"
        if dep_measures:
            return f"{name} = [{dep_measures[0].strip('[]')}]"

    # Multi-measure formulas (e.g., CCC = DSO + DIO - DPO)
    if len(dep_measures) >= 3 and not dep_cols:
        parts = " + ".join(f"[{m.strip('[]')}]" for m in dep_measures)
        return f"{name} = {parts}"

    # ROI / per unit patterns
    if "roi" in name_lower or "per unit" in name_lower or "per_unit" in name_lower:
        if dep_measures and dep_cols:
            num = dep_measures[0].strip("[]")
            den_col = dep_cols[0]
            return f"{name} = [{num}] / SUM({den_col})"
        if len(dep_measures) >= 2:
            a = dep_measures[0].strip("[]")
            b = dep_measures[1].strip("[]")
            return f"{name} = [{a}] / [{b}]"

    # Incremental = actual - baseline
    if "incremental" in name_lower:
        if dep_cols and len(dep_cols) >= 2:
            return f"{name} = SUM({dep_cols[0]}) - SUM({dep_cols[1]})"
        if dep_measures:
            parts = " - ".join(f"[{m.strip('[]')}]" for m in dep_measures)
            return f"{name} = {parts}"

    # Effect amount measures (PVM)
    if "effect" in name_lower and "amount" in name_lower:
        if dep_measures:
            parts = []
            for m in dep_measures:
                parts.append(f"[{m.strip('[]')}]")
            if len(parts) >= 3:
                return f"{name} = {parts[0]} - {parts[1]} - SUM(fact_sales[Plan Sales Amount]) - {' - '.join(parts[2:])}"
            return f"{name} = {' - '.join(parts)}"

    # Turnover ratio
    if "turnover" in name_lower:
        if len(dep_cols) >= 2:
            return f"{name} = SUM({dep_cols[1]}) / SUM({dep_cols[0]})"

    # Generic with dependencies
    if dep_cols and not dep_measures:
        if len(dep_cols) == 1:
            return f"{name} = SUM({dep_cols[0]})"
        if len(dep_cols) == 2:
            if "%" in name or "pct" in name_lower or "rate" in name_lower:
                return f"{name} = SUM({dep_cols[0]}) / SUM({dep_cols[1]})"
            return f"{name} = SUM({dep_cols[0]}) - SUM({dep_cols[1]})"

    if dep_measures and not dep_cols:
        if len(dep_measures) == 1:
            m = dep_measures[0].strip("[]")
            return f"{name} = [{m}]"
        if len(dep_measures) == 2:
            a = dep_measures[0].strip("[]")
            b = dep_measures[1].strip("[]")
            if "%" in name or "pct" in name_lower:
                return f"{name} = [{a}] / [{b}]"
            return f"{name} = [{a}] - [{b}]"

    # Fallback: use KPI catalog definition
    if kpi_def:
        return f"{name} = {kpi_def}"

    # Fallback: use description
    if desc:
        return f"{name} = {desc}"

    return f"{name} = [see business definition]"


# ---------------------------------------------------------------------------
# 5. Aggregation method inference
# ---------------------------------------------------------------------------

def infer_aggregation_method(measure_name: str) -> str:
    """Infer aggregation_method from measure name."""
    n = measure_name.lower()
    if any(kw in n for kw in ("amount", "cost", "revenue", "value")):
        return "sum"
    if any(kw in n for kw in ("%", "pct", "rate", "ratio")):
        return "ratio"
    if any(kw in n for kw in ("count", "number")):
        return "count"
    if "days" in n or "day" in n:
        return "ratio"
    if any(kw in n for kw in ("index", "score")):
        return "average"
    if any(kw in n for kw in ("units", "volume", "hours", "minutes")):
        return "sum"
    if "turnover" in n:
        return "ratio"
    return "sum"


# ---------------------------------------------------------------------------
# 6. Markdown + YAML block processing
# ---------------------------------------------------------------------------

def process_md_file(
    md_path: Path,
    kpi_catalog: dict,
    overlay_by_name: dict,
    overlay_by_kpi: dict,
) -> int:
    """Process a single Measure Dictionary .md file. Returns count of replacements."""
    text = md_path.read_text(encoding="utf-8")

    # Find all fenced YAML blocks
    pattern = re.compile(r"(```yaml\s*\n)(.*?)(```)", re.DOTALL)
    count = 0

    def replace_block(m):
        nonlocal count
        prefix = m.group(1)
        yaml_text = m.group(2)
        suffix = m.group(3)

        if PLACEHOLDER not in yaml_text:
            return m.group(0)

        try:
            measures = yaml.safe_load(yaml_text)
        except yaml.YAMLError:
            return m.group(0)

        if not isinstance(measures, list):
            return m.group(0)

        modified = False
        for measure in measures:
            if not isinstance(measure, dict):
                continue

            expr_block = measure.get("expression", {})
            if not isinstance(expr_block, dict):
                continue

            logical = expr_block.get("logical", "")
            if logical != PLACEHOLDER:
                continue

            # --- Find the best expression ---
            mname = measure.get("measure_name", "")
            kpi_ref = measure.get("kpi_id_ref", "")

            new_logical = None

            # Source 1: Fabric overlay by measure name
            if mname in overlay_by_name:
                dax = overlay_by_name[mname].get("dax", "")
                new_logical = translate_dax(dax, mname)

            # Source 2: Fabric overlay by kpi_id
            if not new_logical and kpi_ref and kpi_ref in overlay_by_kpi:
                ov = overlay_by_kpi[kpi_ref]
                dax = ov.get("dax", "")
                new_logical = translate_dax(dax, mname)

            # Source 3: Derive from metadata
            if not new_logical:
                new_logical = derive_expression(measure, kpi_catalog)

            if new_logical:
                expr_block["logical"] = new_logical
                count += 1
                modified = True

            # Ensure aggregation_method is set
            if "aggregation_method" not in expr_block:
                expr_block["aggregation_method"] = infer_aggregation_method(mname)
                modified = True

        if not modified:
            return m.group(0)

        # Re-serialize YAML preserving style
        new_yaml = yaml_dump_measures(measures)
        return prefix + new_yaml + suffix

    new_text = pattern.sub(replace_block, text)
    if new_text != text:
        md_path.write_text(new_text, encoding="utf-8")

    return count


def yaml_dump_measures(measures: list) -> str:
    """Dump measures list to YAML string with controlled formatting."""
    # Use custom dumper that handles long strings properly
    class QuotedStr(str):
        pass

    def quoted_str_representer(dumper, data):
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style="'")

    class CustomDumper(yaml.SafeDumper):
        pass

    CustomDumper.add_representer(QuotedStr, quoted_str_representer)

    # Process measures to quote the logical expressions
    processed = []
    for m in measures:
        m_copy = deep_copy_measure(m)
        processed.append(m_copy)

    result = yaml.dump(
        processed,
        Dumper=CustomDumper,
        default_flow_style=False,
        allow_unicode=True,
        width=200,
        sort_keys=False,
    )
    return result


def deep_copy_measure(m):
    """Deep copy a measure dict, quoting string values that need it."""
    if isinstance(m, dict):
        out = {}
        for k, v in m.items():
            out[k] = deep_copy_measure(v)
        return out
    elif isinstance(m, list):
        return [deep_copy_measure(item) for item in m]
    elif isinstance(m, str):
        # Quote strings that contain colons, special chars, or are logical expressions
        return m
    else:
        return m


# ---------------------------------------------------------------------------
# 7. Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("Complete Logical Expressions in Measure Dictionaries")
    print("=" * 70)

    # Load sources
    print("\n[1] Loading KPI Catalog...")
    kpi_catalog = parse_kpi_catalog(KPI_CATALOG_PATH)
    print(f"    Loaded {len(kpi_catalog)} KPI entries")

    print("[2] Loading Fabric overlay...")
    overlay_by_name, overlay_by_kpi = parse_overlay(OVERLAY_PATH)
    print(f"    Loaded {len(overlay_by_name)} overlay entries")

    # Find all Measure Dictionary files
    import glob as globmod
    md_files = sorted(ROOT.glob(MEASURE_DICT_GLOB))
    print(f"\n[3] Found {len(md_files)} Measure Dictionary files\n")

    total = 0
    stats = []
    for md_path in md_files:
        domain = md_path.parent.name
        replaced = process_md_file(md_path, kpi_catalog, overlay_by_name, overlay_by_kpi)
        total += replaced
        if replaced > 0:
            stats.append((domain, replaced))
            print(f"    {domain:25s} → {replaced:3d} expressions completed")
        else:
            print(f"    {domain:25s} →   0 (no placeholders)")

    print(f"\n{'=' * 70}")
    print(f"Total: {total} logical expressions completed across {len(stats)} domains")
    print(f"{'=' * 70}")

    # Verify
    remaining = 0
    for md_path in md_files:
        text = md_path.read_text(encoding="utf-8")
        remaining += text.count(PLACEHOLDER)

    if remaining == 0:
        print("\n✓ Verification passed: 0 placeholders remaining")
    else:
        print(f"\n✗ WARNING: {remaining} placeholders still remaining")
        sys.exit(1)


if __name__ == "__main__":
    main()
