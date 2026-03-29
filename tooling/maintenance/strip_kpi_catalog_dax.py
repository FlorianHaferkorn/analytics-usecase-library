"""
One-time migration: Remove tool-specific fields (dax_expression, formatString)
from core/kpi_catalog/KPI_Catalog.md and rename dax_name → measure_name.

Rationale: The KPI Catalog schema (kpi_catalog_SCHEMA.md §1.5) explicitly states
"Tool-specific logic or expressions (DAX/SQL/etc.) do NOT belong in the KPI Catalog."
DAX expressions belong in the Fabric overlay: products/fabric/powerbi/specs/fabric_measure_overlay.yaml
"""
from __future__ import annotations

import re
from pathlib import Path


def strip_dax_fields(text: str) -> str:
    """Remove dax_expression (with multi-line block), formatString, and rename dax_name → measure_name."""
    lines = text.split("\n")
    result: list[str] = []
    skip_block = False
    block_indent = 0

    for line in lines:
        # If we're skipping a multi-line block (dax_expression: |)
        if skip_block:
            stripped = line.lstrip()
            current_indent = len(line) - len(stripped)
            # Continue skipping while indented deeper than the key, or blank line within block
            if stripped == "" or current_indent > block_indent:
                continue
            else:
                skip_block = False
                # Fall through to process this line normally

        # Remove dax_expression: | (multi-line block scalar)
        if re.match(r"^(\s+)dax_expression:\s*\|", line):
            block_indent = len(line) - len(line.lstrip())
            skip_block = True
            continue

        # Remove dax_expression: "..." (inline scalar, rare but handle it)
        if re.match(r"^\s+dax_expression:", line):
            continue

        # Remove formatString: "..."
        if re.match(r"^\s+formatString:", line):
            continue

        # Rename dax_name → measure_name
        if re.match(r"^\s+dax_name:", line):
            line = line.replace("dax_name:", "measure_name:", 1)

        result.append(line)

    return "\n".join(result)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    kpi_path = repo_root / "core" / "kpi_catalog" / "KPI_Catalog.md"

    if not kpi_path.exists():
        raise FileNotFoundError(f"KPI Catalog not found: {kpi_path}")

    original = kpi_path.read_text(encoding="utf-8-sig")
    result = strip_dax_fields(original)

    # Stats
    removed_dax = original.count("dax_expression:") - result.count("dax_expression:")
    removed_fmt = original.count("formatString:") - result.count("formatString:")
    renamed = result.count("measure_name:") - original.count("measure_name:")

    kpi_path.write_text(result, encoding="utf-8")

    print(f"Stripped {removed_dax} dax_expression fields")
    print(f"Stripped {removed_fmt} formatString fields")
    print(f"Renamed {renamed} dax_name → measure_name")
    print(f"File written: {kpi_path}")


if __name__ == "__main__":
    main()
