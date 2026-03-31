#!/usr/bin/env python3
"""
DataHub V2 API Search Script
search_across_workspaces.py

Cross-workspace search for Power BI and Fabric items using the internal DataHub V2 API.
Returns rich metadata not available via standard APIs (storage mode, last visited, owner, SKU).

AGENT USAGE GUIDE:
------------------
This script searches across ALL workspaces without requiring admin access.
Use it to find items by type, filter by various fields, and get detailed metadata.

IMPORTANT: For semantic models/datasets, use --type Model (not SemanticModel).
           For dataflows, use --type DataFlow (capital F).
           For notebooks, use --type SynapseNotebook.

COMMON PATTERNS:
  # Find all semantic models
  py -3 search_across_workspaces.py --type Model

  # Find models by name
  py -3 search_across_workspaces.py --type Model --filter "Sales"

  # Find items not accessed in 6+ months
  py -3 search_across_workspaces.py --type Model --not-visited-since 2024-06-01

  # Find models refreshed in last month
  py -3 search_across_workspaces.py --type Model --refreshed-since 2024-11-01

  # Find stale data (models not refreshed in 30+ days)
  py -3 search_across_workspaces.py --type Model --not-refreshed-since 2024-11-01

  # Find recently modified items
  py -3 search_across_workspaces.py --type PowerBIReport --updated-since 2024-11-01

  # Find items by owner
  py -3 search_across_workspaces.py --type PowerBIReport --owner "kurt"

  # Find Direct Lake models
  py -3 search_across_workspaces.py --type Model --storage-mode directlake

  # Find items in specific workspace
  py -3 search_across_workspaces.py --type Lakehouse --workspace "fit-data"

  # Get JSON for programmatic use
  py -3 search_across_workspaces.py --type Model --output json

  # Sort by last visited (find stale items)
  py -3 search_across_workspaces.py --type Model --sort last-visited --sort-order asc

DATE FILTERS:
  --visited-since / --not-visited-since    When user last opened item
  --refreshed-since / --not-refreshed-since When data was last refreshed (models)
  --updated-since / --not-updated-since    When definition was last modified

UNIQUE DATAHUB FIELDS:
  - lastVisitedTimeUTC: When item was last opened/used
  - lastRefreshTime: When model data was last refreshed
  - modifiedDate: When item definition was last changed
  - storageMode: Import (1), DirectQuery (2), or DirectLake
  - ownerUser: Full owner details (name, email)
  - sharedFromEnterpriseCapacitySku: Capacity SKU (F2, F64, PP, etc.)
  - naturalLanguageSupported: Copilot/Q&A readiness
  - cachedModelEnabled: Whether caching is on

These fields are NOT available via fab api or admin APIs.

Usage:
    py -3 search_across_workspaces.py --help
"""

import argparse
import json
import subprocess
import sys
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any


#region Configuration

REGIONS = {
    "west-europe": "wabi-west-europe-e-primary-redirect.analysis.windows.net",
    "north-europe": "wabi-north-europe-e-primary-redirect.analysis.windows.net",
    "us-east": "wabi-us-east-e-primary-redirect.analysis.windows.net",
    "us-east2": "wabi-us-east2-e-primary-redirect.analysis.windows.net",
    "us-west": "wabi-us-west-e-primary-redirect.analysis.windows.net",
    "us-north-central": "wabi-us-north-central-e-primary-redirect.analysis.windows.net",
    "us-south-central": "wabi-us-south-central-e-primary-redirect.analysis.windows.net",
    "south-east-asia": "wabi-south-east-asia-e-primary-redirect.analysis.windows.net",
    "australia-east": "wabi-australia-east-e-primary-redirect.analysis.windows.net",
    "brazil-south": "wabi-brazil-south-e-primary-redirect.analysis.windows.net",
    "canada-central": "wabi-canada-central-e-primary-redirect.analysis.windows.net",
    "india-west": "wabi-india-west-e-primary-redirect.analysis.windows.net",
    "japan-east": "wabi-japan-east-e-primary-redirect.analysis.windows.net",
    "uk-south": "wabi-uk-south-e-primary-redirect.analysis.windows.net",
}

# Item types supported by DataHub API
# IMPORTANT: For semantic models use "Model", for dataflows use "DataFlow"
ITEM_TYPES = {
    # Reports & Dashboards
    "PowerBIReport": {"trident": "report", "category": "Reports", "desc": "Power BI reports (.pbix)"},
    "Report": {"trident": "report", "category": "Reports", "desc": "Alias for PowerBIReport"},
    "PaginatedReport": {"trident": "rdlreport", "category": "Reports", "desc": "Paginated/RDL reports"},
    "Dashboard": {"trident": "dashboard", "category": "Reports", "desc": "Power BI dashboards"},
    "OrgApp": {"trident": "OrgApp", "category": "Reports", "desc": "Published Power BI apps"},
    # Models - USE "Model" FOR SEMANTIC MODELS
    "Model": {"trident": "dataset", "category": "Models", "desc": "Semantic models/datasets (USE THIS)"},
    "SemanticModel": {"trident": "semanticModel", "category": "Models", "desc": "Alternative (often returns 0)"},
    "MetricSet": {"trident": "MetricSet", "category": "Models", "desc": "Metric sets"},
    # Data Storage
    "Lakehouse": {"trident": "Lakehouse", "category": "Data", "desc": "Fabric lakehouses"},
    "Warehouse": {"trident": "Warehouse", "category": "Data", "desc": "Fabric data warehouses"},
    "Datamart": {"trident": "datamart", "category": "Data", "desc": "Power BI datamarts"},
    "Sql": {"trident": "datamart", "category": "Data", "desc": "SQL endpoints"},
    "KustoDatabase": {"trident": "KustoDatabase", "category": "Data", "desc": "KQL databases"},
    "KustoEventHouse": {"trident": "KustoEventHouse", "category": "Data", "desc": "Eventhouse"},
    "SQLDbNative": {"trident": "SQLDbNative", "category": "Data", "desc": "SQL databases"},
    # Data Integration - USE "DataFlow" WITH CAPITAL F
    "DataFlow": {"trident": "dataflow", "category": "Integration", "desc": "Power BI dataflows (USE THIS)"},
    "DataflowFabric": {"trident": "DataflowFabric", "category": "Integration", "desc": "Fabric dataflows Gen2"},
    "Pipeline": {"trident": "Pipeline", "category": "Integration", "desc": "Data pipelines"},
    "DataPipeline": {"trident": "DataPipeline", "category": "Integration", "desc": "Alias for Pipeline"},
    # Compute - USE "SynapseNotebook" FOR NOTEBOOKS
    "SynapseNotebook": {"trident": "SynapseNotebook", "category": "Compute", "desc": "Fabric notebooks (USE THIS)"},
    "Notebook": {"trident": "SynapseNotebook", "category": "Compute", "desc": "Alias for SynapseNotebook"},
    "SparkJobDefinition": {"trident": "SparkJobDefinition", "category": "Compute", "desc": "Spark job definitions"},
    # ML & AI
    "MLModel": {"trident": "MLModel", "category": "ML", "desc": "ML models"},
    "MLExperiment": {"trident": "MLExperiment", "category": "ML", "desc": "ML experiments"},
    # Real-Time Intelligence
    "Reflex": {"trident": "Reflex", "category": "Solutions", "desc": "Reflex/Activator items"},
}

DEFAULT_REGION = "west-europe"

#endregion


#region Authentication

def get_fabric_token() -> Optional[str]:
    """Get Fabric access token using Azure CLI."""
    try:
        result = subprocess.run(
            ["az", "account", "get-access-token", "--resource", "https://analysis.windows.net/powerbi/api"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get("accessToken")
        print("Error: Azure CLI not authenticated. Run 'az login' first.", file=sys.stderr)
        return None
    except subprocess.TimeoutExpired:
        print("Error: Command timed out", file=sys.stderr)
        return None
    except FileNotFoundError:
        print("Error: Azure CLI not installed.", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error getting token: {e}", file=sys.stderr)
        return None

#endregion


#region DataHub API

def search_datahub(
    token: str,
    item_types: List[str],
    region: str = DEFAULT_REGION,
    workspace_id: Optional[str] = None,
    page_size: int = 100,
    page_number: int = 1
) -> Dict[str, Any]:
    """Search DataHub V2 API for items across all workspaces."""
    host = REGIONS.get(region)
    if not host:
        return {"success": False, "error": f"Unknown region: {region}. Use --list-regions to see options."}

    trident_types = []
    for item_type in item_types:
        if item_type in ITEM_TYPES:
            trident_types.append(ITEM_TYPES[item_type]["trident"])
        else:
            trident_types.append(item_type.lower())

    filters = []
    if workspace_id:
        filters.append({"datahubFilterType": "workspace", "values": [workspace_id]})

    payload = {
        "filters": filters,
        "hostFamily": 4,
        "orderBy": "Default",
        "orderDirection": "",
        "pageNumber": page_number,
        "pageSize": min(page_size, 1000),
        "supportedTypes": item_types,
        "tridentSupportedTypes": trident_types
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = f"https://{host}/metadata/datahub/V2/artifacts"

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            items = response.json()
            return {
                "success": True,
                "items": items if isinstance(items, list) else [],
                "count": len(items) if isinstance(items, list) else 0,
                "region": region,
                "host": host
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text[:200]}",
                "region": region
            }
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timed out (60s)", "region": region}
    except Exception as e:
        return {"success": False, "error": str(e), "region": region}

#endregion


#region Filtering

def _parse_odata_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse OData /Date(ms)/ or ISO date string to datetime."""
    if not date_str:
        return None
    if date_str.startswith("/Date(") and date_str.endswith(")/"):
        try:
            ms = int(date_str[6:-2])
            return datetime.fromtimestamp(ms / 1000)
        except (ValueError, OSError):
            return None
    try:
        return datetime.strptime(date_str[:10], "%Y-%m-%d")
    except ValueError:
        return None


def _get_item_refresh_time(item: Dict) -> Optional[str]:
    refresh_time = item.get("lastRefreshTime")
    if refresh_time:
        return refresh_time
    artifact = item.get("artifact", {})
    refresh_time = artifact.get("LastRefreshTime") or artifact.get("lastRefreshTime")
    if refresh_time:
        return refresh_time
    return artifact.get("lastUpdatedDate")


def apply_filters(
    items: List[Dict],
    name_filter: Optional[str] = None,
    workspace_filter: Optional[str] = None,
    owner_filter: Optional[str] = None,
    visited_since: Optional[str] = None,
    not_visited_since: Optional[str] = None,
    refreshed_since: Optional[str] = None,
    not_refreshed_since: Optional[str] = None,
    updated_since: Optional[str] = None,
    not_updated_since: Optional[str] = None,
    storage_mode: Optional[str] = None,
    capacity_sku: Optional[str] = None,
) -> List[Dict]:
    """Apply multiple filters to items list."""
    result = items

    if name_filter:
        name_lower = name_filter.lower()
        result = [i for i in result if name_lower in i.get("displayName", "").lower() or name_lower in i.get("name", "").lower()]

    if workspace_filter:
        ws_lower = workspace_filter.lower()
        result = [i for i in result if ws_lower in i.get("workspaceName", "").lower()]

    if owner_filter:
        owner_lower = owner_filter.lower()
        result = [
            i for i in result
            if owner_lower in i.get("ownerUser", {}).get("emailAddress", "").lower()
            or owner_lower in i.get("ownerUser", {}).get("givenName", "").lower()
            or owner_lower in i.get("ownerUser", {}).get("familyName", "").lower()
        ]

    if visited_since:
        try:
            since_date = datetime.strptime(visited_since, "%Y-%m-%d")
            result = [i for i in result if i.get("lastVisitedTimeUTC") and datetime.strptime(i["lastVisitedTimeUTC"][:10], "%Y-%m-%d") >= since_date]
        except ValueError:
            print(f"Warning: Invalid date format '{visited_since}', use YYYY-MM-DD", file=sys.stderr)

    if not_visited_since:
        try:
            since_date = datetime.strptime(not_visited_since, "%Y-%m-%d")
            result = [i for i in result if i.get("lastVisitedTimeUTC") and datetime.strptime(i["lastVisitedTimeUTC"][:10], "%Y-%m-%d") < since_date]
        except ValueError:
            print(f"Warning: Invalid date format '{not_visited_since}', use YYYY-MM-DD", file=sys.stderr)

    def get_refresh_dt(item):
        return _parse_odata_date(_get_item_refresh_time(item))

    if refreshed_since:
        try:
            since_date = datetime.strptime(refreshed_since, "%Y-%m-%d")
            result = [i for i in result if get_refresh_dt(i) and get_refresh_dt(i) >= since_date]
        except ValueError:
            print(f"Warning: Invalid date format '{refreshed_since}', use YYYY-MM-DD", file=sys.stderr)

    if not_refreshed_since:
        try:
            since_date = datetime.strptime(not_refreshed_since, "%Y-%m-%d")
            result = [i for i in result if get_refresh_dt(i) and get_refresh_dt(i) < since_date]
        except ValueError:
            print(f"Warning: Invalid date format '{not_refreshed_since}', use YYYY-MM-DD", file=sys.stderr)

    if updated_since:
        try:
            since_date = datetime.strptime(updated_since, "%Y-%m-%d")
            result = [i for i in result if _parse_odata_date(i.get("modifiedDate")) and _parse_odata_date(i.get("modifiedDate")) >= since_date]
        except ValueError:
            print(f"Warning: Invalid date format '{updated_since}', use YYYY-MM-DD", file=sys.stderr)

    if not_updated_since:
        try:
            since_date = datetime.strptime(not_updated_since, "%Y-%m-%d")
            result = [i for i in result if _parse_odata_date(i.get("modifiedDate")) and _parse_odata_date(i.get("modifiedDate")) < since_date]
        except ValueError:
            print(f"Warning: Invalid date format '{not_updated_since}', use YYYY-MM-DD", file=sys.stderr)

    if storage_mode:
        mode_lower = storage_mode.lower()
        def matches_storage(item):
            artifact = item.get("artifact", {})
            sm = artifact.get("storageMode")
            dl = artifact.get("directLakeMode", False)
            if mode_lower == "import" and sm == 1:
                return True
            if mode_lower == "directquery" and sm == 2:
                return True
            if mode_lower == "directlake" and dl:
                return True
            return False
        result = [i for i in result if matches_storage(i)]

    if capacity_sku:
        sku_upper = capacity_sku.upper()
        result = [i for i in result if sku_upper in i.get("artifact", {}).get("sharedFromEnterpriseCapacitySku", "").upper()]

    return result

#endregion


#region Sorting & Output

def sort_items(items: List[Dict], sort_by: str, sort_order: str = "desc") -> List[Dict]:
    """Sort items by specified field."""
    reverse = sort_order.lower() != "asc"
    if sort_by == "name":
        return sorted(items, key=lambda x: x.get("displayName", "").lower(), reverse=reverse)
    elif sort_by == "workspace":
        return sorted(items, key=lambda x: x.get("workspaceName", "").lower(), reverse=reverse)
    elif sort_by == "last-visited":
        return sorted(items, key=lambda x: x.get("lastVisitedTimeUTC", ""), reverse=reverse)
    elif sort_by == "last-refreshed":
        return sorted(items, key=lambda x: _get_item_refresh_time(x) or "", reverse=reverse)
    elif sort_by == "last-modified":
        return sorted(items, key=lambda x: x.get("modifiedDate", ""), reverse=reverse)
    elif sort_by == "owner":
        return sorted(items, key=lambda x: x.get("ownerUser", {}).get("emailAddress", "").lower(), reverse=reverse)
    return items


def _get_storage_mode(item: Dict) -> str:
    artifact = item.get("artifact", {})
    if artifact.get("directLakeMode"):
        return "DirectLake"
    sm = artifact.get("storageMode")
    if sm == 1:
        return "Import"
    elif sm == 2:
        return "DirectQuery"
    return "Unknown"


def _get_refresh_iso(item: Dict) -> Optional[str]:
    rt = _get_item_refresh_time(item)
    dt = _parse_odata_date(rt)
    return dt.isoformat() if dt else None


def _get_modified_iso(item: Dict) -> Optional[str]:
    dt = _parse_odata_date(item.get("modifiedDate"))
    return dt.isoformat() if dt else None


def format_output(items: List[Dict], output_format: str = "table") -> str:
    """Format items for display."""
    if output_format == "json":
        cleaned = []
        for item in items:
            cleaned.append({
                "name": item.get("displayName", item.get("name")),
                "workspace": item.get("workspaceName"),
                "workspaceId": item.get("workspaceObjectId"),
                "id": item.get("objectId"),
                "lastVisited": item.get("lastVisitedTimeUTC"),
                "lastRefreshed": _get_refresh_iso(item),
                "lastModified": _get_modified_iso(item),
                "owner": item.get("ownerUser", {}).get("emailAddress"),
                "ownerName": f"{item.get('ownerUser', {}).get('givenName', '')} {item.get('ownerUser', {}).get('familyName', '')}".strip(),
                "storageMode": _get_storage_mode(item),
                "capacitySku": item.get("artifact", {}).get("sharedFromEnterpriseCapacitySku"),
                "isDiscoverable": item.get("isDiscoverable"),
            })
        return json.dumps(cleaned, indent=2)

    if not items:
        return "No items found."

    if output_format == "brief":
        return "\n".join(f"{i.get('workspaceName', '')}/{i.get('displayName', i.get('name', 'Unknown'))}" for i in items)

    if output_format == "detailed":
        lines = []
        for item in items:
            lines.append(f"Name:        {item.get('displayName', item.get('name', 'Unknown'))}")
            lines.append(f"Workspace:   {item.get('workspaceName', 'N/A')}")
            lines.append(f"ID:          {item.get('objectId', 'N/A')}")
            lines.append(f"Last Visit:  {(item.get('lastVisitedTimeUTC') or 'N/A')[:19]}")
            owner = item.get("ownerUser", {})
            lines.append(f"Owner:       {owner.get('givenName', '')} {owner.get('familyName', '')} <{owner.get('emailAddress', 'N/A')}>")
            lines.append(f"Storage:     {_get_storage_mode(item)}")
            lines.append(f"Capacity:    {item.get('artifact', {}).get('sharedFromEnterpriseCapacitySku', 'N/A')}")
            lines.append("-" * 60)
        return "\n".join(lines)

    # Table format (default)
    lines = [f"{'Name':<35} {'Workspace':<22} {'Last Visited':<12} {'Owner':<20}",
             "-" * 92]
    for item in items:
        name = item.get("displayName", item.get("name", "Unknown"))[:34]
        workspace = item.get("workspaceName", "")[:21]
        last_visit = (item.get("lastVisitedTimeUTC") or "")[:10]
        owner = item.get("ownerUser", {})
        owner_name = f"{owner.get('givenName', '')} {owner.get('familyName', '')}".strip()[:19]
        lines.append(f"{name:<35} {workspace:<22} {last_visit:<12} {owner_name:<20}")
    return "\n".join(lines)

#endregion


#region Main

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Cross-workspace search for Fabric/Power BI items using DataHub V2 API.\n\n"
                    "Returns metadata not available via standard APIs: lastVisited, storageMode, owner, SKU.\n\n"
                    "IMPORTANT: use --type Model for semantic models, DataFlow for dataflows, SynapseNotebook for notebooks.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --type Model
  %(prog)s --type Model --filter "Sales"
  %(prog)s --type Model --not-visited-since 2024-06-01
  %(prog)s --type Model --storage-mode directlake
  %(prog)s --type PowerBIReport --owner "kurt" --output json
  %(prog)s --type Lakehouse --workspace "Production"
        """
    )

    parser.add_argument("--type", "-t", dest="item_type",
                        help="Item type (Model, PowerBIReport, Lakehouse, …). Use --list-types for all options.")

    filter_group = parser.add_argument_group("Filters")
    filter_group.add_argument("--filter", "-f", dest="filter_text", help="Filter by name (contains)")
    filter_group.add_argument("--workspace", "-w", dest="workspace_filter", help="Filter by workspace name")
    filter_group.add_argument("--workspace-id", help="Filter by workspace GUID")
    filter_group.add_argument("--owner", help="Filter by owner name or email")
    filter_group.add_argument("--visited-since", help="Only items visited on or after YYYY-MM-DD")
    filter_group.add_argument("--not-visited-since", help="Only items NOT visited since YYYY-MM-DD (stale)")
    filter_group.add_argument("--refreshed-since", help="Only items refreshed on or after YYYY-MM-DD")
    filter_group.add_argument("--not-refreshed-since", help="Only items NOT refreshed since YYYY-MM-DD (stale data)")
    filter_group.add_argument("--updated-since", help="Only items modified on or after YYYY-MM-DD")
    filter_group.add_argument("--not-updated-since", help="Only items NOT modified since YYYY-MM-DD")
    filter_group.add_argument("--storage-mode", choices=["import", "directquery", "directlake"])
    filter_group.add_argument("--capacity-sku", help="Filter by capacity SKU (F2, F64, PP, etc.)")

    sort_group = parser.add_argument_group("Sorting")
    sort_group.add_argument("--sort", choices=["name", "workspace", "last-visited", "last-refreshed", "last-modified", "owner"])
    sort_group.add_argument("--sort-order", choices=["asc", "desc"], default="desc")

    output_group = parser.add_argument_group("Output")
    output_group.add_argument("--output", "-o", choices=["table", "json", "brief", "detailed"], default="table")
    output_group.add_argument("--limit", type=int, help="Limit number of results displayed")

    api_group = parser.add_argument_group("API Options")
    api_group.add_argument("--region", "-r", default=DEFAULT_REGION,
                           help=f"Fabric region (default: {DEFAULT_REGION})")
    api_group.add_argument("--page-size", type=int, default=200)

    info_group = parser.add_argument_group("Information")
    info_group.add_argument("--list-types", action="store_true", help="List all available item types")
    info_group.add_argument("--list-regions", action="store_true", help="List all available regions")

    args = parser.parse_args()

    if args.list_types:
        print("Available item types:\n")
        print("IMPORTANT: Use 'Model' for semantic models, 'DataFlow' for dataflows, 'SynapseNotebook' for notebooks\n")
        by_category: Dict[str, list] = {}
        for name, info in ITEM_TYPES.items():
            cat = info["category"]
            by_category.setdefault(cat, []).append((name, info.get("desc", "")))
        for cat, types in sorted(by_category.items()):
            print(f"  {cat}:")
            for name, desc in sorted(types):
                print(f"    {name:<30} {desc}")
            print()
        return 0

    if args.list_regions:
        print("Available regions:\n")
        for region, host in sorted(REGIONS.items()):
            default = " (default)" if region == DEFAULT_REGION else ""
            print(f"  {region:<20} {host}{default}")
        return 0

    if not args.item_type:
        parser.error("--type is required for search (or use --list-types)")

    if args.item_type not in ITEM_TYPES:
        print(f"Warning: '{args.item_type}' not in known types. Trying anyway...", file=sys.stderr)

    print("Getting access token...", file=sys.stderr)
    token = get_fabric_token()
    if not token:
        return 1

    print(f"Searching for {args.item_type} in {args.region}...", file=sys.stderr)
    result = search_datahub(
        token=token,
        item_types=[args.item_type],
        region=args.region,
        workspace_id=args.workspace_id,
        page_size=args.page_size
    )

    if not result["success"]:
        print(f"Error: {result['error']}", file=sys.stderr)
        return 1

    items = result["items"]
    print(f"API returned {len(items)} items", file=sys.stderr)

    items = apply_filters(
        items,
        name_filter=args.filter_text,
        workspace_filter=args.workspace_filter,
        owner_filter=args.owner,
        visited_since=args.visited_since,
        not_visited_since=args.not_visited_since,
        refreshed_since=args.refreshed_since,
        not_refreshed_since=args.not_refreshed_since,
        updated_since=args.updated_since,
        not_updated_since=args.not_updated_since,
        storage_mode=args.storage_mode,
        capacity_sku=args.capacity_sku,
    )

    if args.sort:
        items = sort_items(items, args.sort, args.sort_order)

    if args.limit:
        items = items[:args.limit]

    print(f"\nFound {len(items)} items after filtering:\n", file=sys.stderr)
    print(format_output(items, args.output))

    return 0

#endregion


if __name__ == "__main__":
    sys.exit(main())
