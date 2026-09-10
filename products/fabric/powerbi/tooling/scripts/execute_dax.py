#!/usr/bin/env python3
"""
execute_dax.py
Execute DAX queries against a Fabric semantic model via the Power BI REST API.

Resolves workspace and dataset by name using the Fabric CLI, then calls the
Power BI executeQueries endpoint with az CLI for token acquisition.

AGENT USAGE GUIDE:
------------------
Use this script to validate measures, test calculations, or inspect model data
without opening Power BI Desktop.

COMMON PATTERNS:
  # Simple scalar measure test
  py -3 execute_dax.py --workspace "MyWorkspace" --dataset "MyModel" \
      --query "EVALUATE ROW(\"Revenue\", [Total Revenue])"

  # Table query
  py -3 execute_dax.py --workspace "MyWorkspace" --dataset "MyModel" \
      --query "EVALUATE TOPN(10, 'Sales', [Date])" --output table

  # Save to JSON
  py -3 execute_dax.py --workspace "MyWorkspace" --dataset "MyModel" \
      --query "EVALUATE VALUES('Date'[Year])" --output json --out results.json

  # Using GUIDs directly
  py -3 execute_dax.py --workspace-id <guid> --dataset-id <guid> \
      --query "EVALUATE ROW(\"Count\", COUNTROWS('Sales'))"

PREREQUISITES:
  - Azure CLI installed and logged in (az login)
  - fab CLI installed and authenticated (fab auth login)
  - Python packages: requests (pip install requests)

Usage:
    py -3 execute_dax.py --help
"""

import argparse
import json
import subprocess
import sys
import csv
import io
from pathlib import Path
from typing import Any, Dict, List, Optional

# Die Repo-Wurzel auf den Suchpfad: dieses Skript wird direkt aufgerufen, aus
# einem beliebigen Arbeitsverzeichnis.
sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
from tooling.prozess import befehl, kind_umgebung, programm  # noqa: E402


def get_token(resource: str = "https://analysis.windows.net/powerbi/api") -> Optional[str]:
    """Acquire an Entra ID token for the Power BI API via Azure CLI."""
    try:
        result = subprocess.run(
            ["az", "account", "get-access-token", "--resource", resource],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return json.loads(result.stdout).get("accessToken")
        print(f"Error: az CLI not authenticated. Run 'az login' first.\n{result.stderr}", file=sys.stderr)
        return None
    except FileNotFoundError:
        print("Error: Azure CLI not installed.", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error acquiring token: {e}", file=sys.stderr)
        return None


def resolve_ids(workspace_name: str, dataset_name: str) -> tuple[Optional[str], Optional[str]]:
    """
    Resolve workspace and dataset names to GUIDs using the fab CLI.
    Returns (workspace_id, dataset_id) or (None, None) on failure.
    """
    # Aufgeloester Pfad statt nacktem Namen: auf Windows liegt `fab` je nach
    # Installationsweg als `fab.exe` oder als `fab.cmd` vor. `shutil.which`
    # findet die Huelle ueber PATHEXT, `CreateProcess` haengt nur `.exe` an und
    # meldet WinError 2 -- Waechter und Lauf pruefen sonst verschiedene
    # Programme. `befehl()` startet eine Huelle ueber den Kommandoprozessor.
    fab = programm("fab")
    if fab is None:
        print("Error: fab CLI not installed or not in PATH. "
              "Install from https://aka.ms/fabriccli", file=sys.stderr)
        return None, None
    try:
        # Get workspace ID
        ws_result = subprocess.run(
            befehl(fab, "get", f"{workspace_name}.Workspace", "-q", "id"),
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=kind_umgebung(), timeout=30
        )
        if ws_result.returncode != 0:
            print(f"Error: Could not find workspace '{workspace_name}'. Run 'fab ls' to list workspaces.", file=sys.stderr)
            return None, None
        ws_id = ws_result.stdout.strip().strip('"')

        # Get dataset ID
        ds_result = subprocess.run(
            befehl(fab, "get", f"{workspace_name}.Workspace/{dataset_name}.SemanticModel",
                   "-q", "id"),
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=kind_umgebung(), timeout=30
        )
        if ds_result.returncode != 0:
            print(f"Error: Could not find dataset '{dataset_name}' in workspace '{workspace_name}'.", file=sys.stderr)
            return ws_id, None
        ds_id = ds_result.stdout.strip().strip('"')

        return ws_id, ds_id

    except FileNotFoundError:
        print("Error: fab CLI not installed or not in PATH. Install from https://aka.ms/fabriccli", file=sys.stderr)
        return None, None
    except Exception as e:
        print(f"Error resolving IDs: {e}", file=sys.stderr)
        return None, None


def execute_dax(
    workspace_id: str,
    dataset_id: str,
    query: str,
    token: str,
    include_nulls: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Execute a DAX query against the Power BI executeQueries endpoint.

    Returns the parsed JSON response or None on failure.
    Endpoint: POST /v1.0/myorg/groups/{workspaceId}/datasets/{datasetId}/executeQueries
    """
    import urllib.request

    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/executeQueries"

    payload = {
        "queries": [{"query": query}],
        "serializerSettings": {"includeNulls": include_nulls}
    }

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code} error from Power BI API:\n{err_body}", file=sys.stderr)
        if e.code == 403:
            print("\nHint: 403 may mean the workspace role is Viewer (read-only). Request Contributor or higher.", file=sys.stderr)
        if e.code == 404:
            print("\nHint: 404 may mean the dataset ID is wrong or the model has no data. Verify workspace/dataset names.", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Request failed: {e}", file=sys.stderr)
        return None


def format_table(rows: List[Dict], columns: List[str]) -> str:
    """Format results as an ASCII table."""
    if not rows:
        return "(no rows returned)"

    # Compute column widths
    widths = {col: len(col) for col in columns}
    for row in rows:
        for col in columns:
            val = str(row.get(col, ""))
            widths[col] = max(widths[col], len(val))

    sep = "+-" + "-+-".join("-" * widths[col] for col in columns) + "-+"
    header = "| " + " | ".join(col.ljust(widths[col]) for col in columns) + " |"

    lines = [sep, header, sep]
    for row in rows:
        line = "| " + " | ".join(str(row.get(col, "")).ljust(widths[col]) for col in columns) + " |"
        lines.append(line)
    lines.append(sep)
    return "\n".join(lines)


def format_csv(rows: List[Dict], columns: List[str]) -> str:
    """Format results as CSV."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def extract_results(response: Dict) -> tuple[List[str], List[Dict]]:
    """Extract column names and rows from a Power BI executeQueries response."""
    try:
        result = response["results"][0]["tables"][0]
        rows = result.get("rows", [])
        if rows:
            # Strip DAX table prefix from column names (e.g. "[Sales].[Amount]" → "Amount")
            columns = []
            for key in rows[0].keys():
                # Column names come as "TableName[ColumnName]" — strip the table prefix
                if "[" in key:
                    columns.append(key.split("[", 1)[1].rstrip("]"))
                else:
                    columns.append(key)

            # Remap rows to clean column names
            clean_rows = []
            for row in rows:
                clean_row = {}
                for (orig_key, col_name) in zip(rows[0].keys(), columns):
                    clean_row[col_name] = row[orig_key]
                clean_rows.append(clean_row)

            return columns, clean_rows
        else:
            return [], []
    except (KeyError, IndexError) as e:
        print(f"Unexpected response structure: {e}\nRaw: {json.dumps(response, indent=2)}", file=sys.stderr)
        return [], []


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Execute a DAX query against a Fabric semantic model.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test a measure
  %(prog)s --workspace "Sales WS" --dataset "Sales Model" \\
      --query "EVALUATE ROW(\\"Revenue\\", [Total Revenue])"

  # Top 10 rows
  %(prog)s --workspace "Sales WS" --dataset "Sales Model" \\
      --query "EVALUATE TOPN(10, 'Sales')" --output table

  # Save JSON output
  %(prog)s --workspace "Sales WS" --dataset "Sales Model" \\
      --query "EVALUATE VALUES('Date'[Year])" --output json --out years.json
        """
    )

    # Target (name-based, resolved via fab CLI)
    name_group = parser.add_argument_group("Target (by name — resolved via fab CLI)")
    name_group.add_argument("--workspace", "-w", help="Workspace display name")
    name_group.add_argument("--dataset", "-d", help="Semantic model / dataset display name")

    # Target (ID-based, bypasses fab CLI)
    id_group = parser.add_argument_group("Target (by GUID — bypasses fab CLI resolution)")
    id_group.add_argument("--workspace-id", help="Workspace GUID")
    id_group.add_argument("--dataset-id", help="Dataset / semantic model GUID")

    # Query
    parser.add_argument("--query", "-q", required=True, help="DAX query string (EVALUATE ...)")
    parser.add_argument("--include-nulls", action="store_true", help="Include null values in serialized output")

    # Output
    parser.add_argument("--output", "-o",
                        choices=["table", "json", "csv"],
                        default="table",
                        help="Output format: table (default), json, csv")
    parser.add_argument("--out", help="Write output to this file instead of stdout")

    args = parser.parse_args()

    # Resolve workspace/dataset IDs
    if args.workspace_id and args.dataset_id:
        ws_id, ds_id = args.workspace_id, args.dataset_id
    elif args.workspace and args.dataset:
        print(f"Resolving IDs for '{args.workspace}' / '{args.dataset}'...", file=sys.stderr)
        ws_id, ds_id = resolve_ids(args.workspace, args.dataset)
        if not ws_id or not ds_id:
            return 1
    else:
        parser.error("Provide either --workspace + --dataset OR --workspace-id + --dataset-id")

    # Acquire token
    print("Acquiring Power BI token...", file=sys.stderr)
    token = get_token()
    if not token:
        return 1

    # Execute query
    print(f"Executing DAX query against dataset {ds_id}...", file=sys.stderr)
    response = execute_dax(ws_id, ds_id, args.query, token, args.include_nulls)
    if not response:
        return 1

    # Format output
    columns, rows = extract_results(response)

    if args.output == "json":
        output = json.dumps({"columns": columns, "rows": rows}, indent=2, default=str)
    elif args.output == "csv":
        output = format_csv(rows, columns)
    else:
        output = format_table(rows, columns)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Output written to {args.out} ({len(rows)} rows)", file=sys.stderr)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
