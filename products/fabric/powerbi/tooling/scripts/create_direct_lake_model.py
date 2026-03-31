#!/usr/bin/env python3
"""
create_direct_lake_model.py
Automate creation of a Direct Lake semantic model from a Fabric Lakehouse.

Extracts table schemas from the lakehouse SQL endpoint, generates TMDL files,
and imports the semantic model into the destination workspace via the fab CLI.

AGENT USAGE GUIDE:
------------------
Use this script to bootstrap a Direct Lake semantic model from an existing
Fabric Lakehouse. It generates a minimal but valid TMDL file set that can be
imported and then enriched with measures and relationships.

COMMON PATTERNS:
  # Create model from all tables in a lakehouse
  py -3 create_direct_lake_model.py \\
      "SourceWS.Workspace/BronzeLH.Lakehouse" \\
      "DestWS.Workspace/MyModel.SemanticModel"

  # Limit to specific tables
  py -3 create_direct_lake_model.py \\
      "SourceWS.Workspace/GoldLH.Lakehouse" \\
      "DestWS.Workspace/SalesModel.SemanticModel" \\
      -t dbo.Sales -t dbo.Date -t dbo.Customer

  # Dry run — generate TMDL locally without importing
  py -3 create_direct_lake_model.py \\
      "SourceWS.Workspace/GoldLH.Lakehouse" \\
      "DestWS.Workspace/SalesModel.SemanticModel" \\
      --output-dir ./my_model --dry-run

PREREQUISITES:
  - fab CLI installed and authenticated (fab auth login)
  - fab config set mode command_line

OUTPUT STRUCTURE:
  <output_dir>/
    .platform
    definition.pbism
    definition/
      database.tmdl
      model.tmdl
      tables/
        <TableName>.tmdl    (one per table)

Usage:
    py -3 create_direct_lake_model.py --help
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from typing import Dict, List, Optional, Tuple


# SQL type → TMDL dataType mapping
SQL_TO_TMDL_TYPE: Dict[str, str] = {
    # Integer types
    "bigint": "int64",
    "int": "int64",
    "integer": "int64",
    "smallint": "int64",
    "tinyint": "int64",
    "byteint": "int64",
    # Numeric / decimal
    "decimal": "decimal",
    "numeric": "decimal",
    "float": "double",
    "double": "double",
    "real": "double",
    "double precision": "double",
    # Boolean
    "boolean": "boolean",
    "bool": "boolean",
    # String
    "string": "string",
    "varchar": "string",
    "char": "string",
    "text": "string",
    "nvarchar": "string",
    "nchar": "string",
    # Date/time
    "date": "dateTime",
    "timestamp": "dateTime",
    "timestamp_ntz": "dateTime",
    "timestamp_tz": "dateTime",
    "datetime": "dateTime",
    "time": "dateTime",
    # Binary / other
    "binary": "binary",
    "varbinary": "binary",
    "bytes": "binary",
}

# TMDL dataType → default summarizeBy
DEFAULT_SUMMARIZE_BY: Dict[str, str] = {
    "int64": "none",
    "decimal": "sum",
    "double": "sum",
    "string": "none",
    "boolean": "none",
    "dateTime": "none",
    "binary": "none",
}


def run_fab(args: List[str], timeout: int = 60) -> Tuple[bool, str]:
    """Run a fab CLI command. Returns (success, output)."""
    try:
        result = subprocess.run(
            ["fab"] + args,
            capture_output=True, text=True, timeout=timeout
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, result.stderr.strip() or result.stdout.strip()
    except FileNotFoundError:
        return False, "fab CLI not found. Install from https://aka.ms/fabriccli"
    except subprocess.TimeoutExpired:
        return False, f"fab command timed out after {timeout}s"


def get_lakehouse_tables(lakehouse_path: str, filter_tables: Optional[List[str]] = None) -> List[Dict]:
    """
    Retrieve table schemas from a lakehouse using fab table schema.
    Returns list of dicts: {schema, table, columns: [{name, type}]}
    """
    print(f"Listing tables in {lakehouse_path}...", file=sys.stderr)
    ok, output = run_fab(["ls", f"{lakehouse_path}/Tables"])
    if not ok:
        print(f"Error listing tables: {output}", file=sys.stderr)
        return []

    table_entries = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        # fab ls output format: "TableName.table" or "schema/TableName.table"
        table_name = line.rstrip(".table").rstrip("/")
        if "/" in table_name:
            schema, table = table_name.rsplit("/", 1)
        else:
            schema, table = "dbo", table_name

        full_table = f"{schema}.{table}"
        if filter_tables and full_table not in filter_tables:
            continue

        table_entries.append({"schema": schema, "table": table, "full": full_table})

    if not table_entries:
        print("No tables found in lakehouse (or all filtered out).", file=sys.stderr)
        return []

    # Get schema for each table
    tables_with_schema = []
    for entry in table_entries:
        print(f"  Getting schema for {entry['full']}...", file=sys.stderr)
        ok, schema_output = run_fab(["table", "schema", f"{lakehouse_path}/Tables/{entry['full']}"])
        if not ok:
            print(f"  Warning: Could not get schema for {entry['full']}: {schema_output}", file=sys.stderr)
            continue

        columns = parse_schema_output(schema_output)
        tables_with_schema.append({
            "schema": entry["schema"],
            "table": entry["table"],
            "full": entry["full"],
            "columns": columns
        })

    return tables_with_schema


def parse_schema_output(output: str) -> List[Dict]:
    """Parse fab table schema output into column list."""
    columns = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        # Try JSON parse first
        try:
            col = json.loads(line)
            columns.append({"name": col.get("name", line), "type": col.get("type", "string")})
            continue
        except (json.JSONDecodeError, ValueError):
            pass
        # Fallback: "col_name  col_type" tab/space separated
        parts = line.split()
        if len(parts) >= 2:
            columns.append({"name": parts[0], "type": parts[1].lower()})
        elif len(parts) == 1:
            columns.append({"name": parts[0], "type": "string"})

    return columns


def map_type(sql_type: str) -> str:
    """Map a SQL/Delta type string to a TMDL dataType."""
    clean = sql_type.lower().split("(")[0].strip()  # strip precision, e.g. decimal(18,2)
    return SQL_TO_TMDL_TYPE.get(clean, "string")


def generate_platform_file(model_name: str) -> str:
    """Generate the .platform metadata file content."""
    return json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {
            "type": "SemanticModel",
            "displayName": model_name
        },
        "config": {
            "version": "2.0",
            "logicalId": ""
        }
    }, indent=2)


def generate_pbism() -> str:
    """Generate the definition.pbism connection file."""
    return json.dumps({
        "version": "4.0",
        "settings": {}
    }, indent=2)


def generate_database_tmdl(model_name: str) -> str:
    """Generate the database.tmdl file."""
    return f"""database {model_name}
\tcompatibilityLevel: 1604
"""


def generate_model_tmdl(model_name: str, table_names: List[str]) -> str:
    """Generate the model.tmdl file."""
    table_refs = "\n".join(f"\tref table '{name}'" for name in table_names)
    return f"""model Model
\tculture: en-US

{table_refs}
"""


def generate_table_tmdl(table: Dict, lakehouse_item_id: str = "") -> str:
    """Generate a TMDL file for a single table with Direct Lake partition."""
    table_name = table["table"]
    schema = table.get("schema", "dbo")
    columns = table.get("columns", [])

    lines = [f"table '{table_name}'"]

    # Columns
    for col in columns:
        tmdl_type = map_type(col["type"])
        summarize = DEFAULT_SUMMARIZE_BY.get(tmdl_type, "none")
        col_name = col["name"]
        lines.append(f"\tcolumn '{col_name}'")
        lines.append(f"\t\tdataType: {tmdl_type}")
        if summarize == "none":
            lines.append(f"\t\tsummarizeBy: none")
        lines.append(f"\t\tsourceColumn: {col_name}")
        lines.append("")

    # Direct Lake partition
    lines.append(f"\tpartition '{table_name}'")
    lines.append(f"\t\tmode: directLake")
    lines.append(f"\t\tsource = entity")
    lines.append(f"\t\t\tschemaName: {schema}")
    lines.append(f"\t\t\tentityName: {table_name}")
    lines.append("")

    return "\n".join(lines)


def write_model_files(
    tables: List[Dict],
    model_name: str,
    output_dir: str
) -> None:
    """Write the complete TMDL file set to the output directory."""
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "definition", "tables"), exist_ok=True)

    # .platform
    with open(os.path.join(output_dir, ".platform"), "w", encoding="utf-8") as f:
        f.write(generate_platform_file(model_name))

    # definition.pbism
    with open(os.path.join(output_dir, "definition.pbism"), "w", encoding="utf-8") as f:
        f.write(generate_pbism())

    # definition/database.tmdl
    with open(os.path.join(output_dir, "definition", "database.tmdl"), "w", encoding="utf-8") as f:
        f.write(generate_database_tmdl(model_name))

    # definition/model.tmdl
    table_names = [t["table"] for t in tables]
    with open(os.path.join(output_dir, "definition", "model.tmdl"), "w", encoding="utf-8") as f:
        f.write(generate_model_tmdl(model_name, table_names))

    # definition/tables/<TableName>.tmdl
    for table in tables:
        tmdl = generate_table_tmdl(table)
        table_file = os.path.join(output_dir, "definition", "tables", f"{table['table']}.tmdl")
        with open(table_file, "w", encoding="utf-8") as f:
            f.write(tmdl)

    print(f"Generated {len(tables)} table files in {output_dir}", file=sys.stderr)


def import_to_fabric(output_dir: str, dest_path: str) -> bool:
    """Import the generated model to Fabric using fab import."""
    print(f"Importing to {dest_path}...", file=sys.stderr)
    ok, output = run_fab(["import", dest_path, "-i", output_dir, "-f"], timeout=120)
    if ok:
        print(f"Import successful.", file=sys.stderr)
        return True
    print(f"Import failed: {output}", file=sys.stderr)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a Direct Lake semantic model from a Fabric Lakehouse.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # All tables
  %(prog)s "SourceWS.Workspace/GoldLH.Lakehouse" "DestWS.Workspace/MyModel.SemanticModel"

  # Specific tables only
  %(prog)s "SourceWS.Workspace/GoldLH.Lakehouse" "DestWS.Workspace/MyModel.SemanticModel" \\
      -t dbo.Sales -t dbo.Date -t dbo.Customer

  # Dry run (generate files locally, no import)
  %(prog)s "SourceWS.Workspace/GoldLH.Lakehouse" "DestWS.Workspace/MyModel.SemanticModel" \\
      --output-dir ./my_model --dry-run
        """
    )

    parser.add_argument("source", help="Source lakehouse path (e.g. 'WorkspaceName.Workspace/LakehouseName.Lakehouse')")
    parser.add_argument("destination", help="Destination semantic model path (e.g. 'WorkspaceName.Workspace/ModelName.SemanticModel')")
    parser.add_argument("-t", "--table", dest="tables", action="append",
                        help="Include only this table (schema.table format, e.g. dbo.Sales). Repeat for multiple tables.")
    parser.add_argument("--output-dir", help="Write TMDL files to this directory (default: temp dir)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Generate files locally only; do not import to Fabric")
    parser.add_argument("--model-name", help="Override semantic model display name (default: derived from destination path)")

    args = parser.parse_args()

    # Derive model name from destination path
    model_name = args.model_name
    if not model_name:
        dest_parts = args.destination.split("/")
        if dest_parts:
            model_name = dest_parts[-1].split(".")[0]
        else:
            model_name = "DirectLakeModel"

    # Retrieve table schemas
    tables = get_lakehouse_tables(args.source, args.tables)
    if not tables:
        print("Error: No tables found. Cannot generate model.", file=sys.stderr)
        return 1

    print(f"\nFound {len(tables)} tables. Generating TMDL...", file=sys.stderr)

    # Write files
    if args.output_dir:
        output_dir = args.output_dir
        write_model_files(tables, model_name, output_dir)
    else:
        with tempfile.TemporaryDirectory() as tmp:
            model_dir = os.path.join(tmp, f"{model_name}.SemanticModel")
            write_model_files(tables, model_name, model_dir)

            if not args.dry_run:
                if not import_to_fabric(model_dir, args.destination):
                    return 1
            else:
                print("Dry run — skipping import.", file=sys.stderr)
        return 0

    if not args.dry_run:
        if not import_to_fabric(output_dir, args.destination):
            return 1
    else:
        print(f"\nDry run complete. Files in: {output_dir}", file=sys.stderr)
        print("Run without --dry-run to import to Fabric.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
