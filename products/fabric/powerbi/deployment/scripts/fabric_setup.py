#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fabric Infrastructure Setup Script

Creates Fabric workspaces, connections, Git integration, and permissions
based on environment JSON configuration files.

Usage:
    CLIENT_SECRET=<secret> python fabric_setup.py --environment dev --tenant_id <id> --client_id <id>
    python fabric_setup.py --environment dev --dry-run  # Simulate without executing
"""
import os
import sys
import io
import argparse
import json
import time
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path for module imports
sys.path.insert(0, str(Path(__file__).parent))

import modules.fabric_cli_functions as fabcli
import modules.misc_functions as misc
import modules.preflight_checks as preflight
import modules.health_checks as health

try:
    import modules.rollback_manager as rollback
except ImportError:
    rollback = None

try:
    import modules.report_generator as report_gen
except ImportError:
    report_gen = None

# Default values
DEFAULT_ENVIRONMENT = "dev"
DEFAULT_ACTION = "create"


# --- Workspace target picture (I-21 W1.9, W1.11, W1.12; Microsoft Learn read 01.10.2026) ------
#
# Declared target values per workspace type (layer DE/DM/BI/Shared) and environment. None of
# this is applied by an API call: the workspace-level surge settings have no documented
# endpoint, OAP and the item-creation policy are tenant/capacity decisions with their own
# preconditions. The script prints them as manual steps (`--target-picture` prints JSON).
# `None` = open decision (Leerstelle), never a guessed value.

#: OAP stances. "off" = must stay off for the cut to work; "on_with_rules" = protect and open
#: the listed destinations; "open_decision" = not decided by this cut.
OAP_STANCES = ("off", "on_with_rules", "open_decision")

#: W1.9 — outbound access protection (OAP) per workspace type.
#: Sources: fabric/security/workspace-outbound-access-protection-overview (Power BI items other
#: than semantic models unsupported; unsupported items block enabling OAP),
#: …-power-bi-reports (preview: a report in a protected workspace binds only to a model in the
#: SAME workspace), …-semantic-models (same-workspace sources need SQL Server + ADLS Gen2
#: rules; no reports in the workspace), fabric/cicd/cicd-security (Git blocked under OAP until
#: "Allow Git integration" is on; deployment pipelines unsupported with INBOUND protection).
NETWORK_STANCE_BY_LAYER = {
    "DE": {
        "outbound_access_protection": "open_decision",
        "reason": "Lakehouse, notebooks and pipelines support OAP (managed private endpoints / "
                  "data connection rules); whether DE_ is protected is a separate decision.",
        "connection_rules": [],
    },
    "DM": {
        "outbound_access_protection": "on_with_rules",
        "reason": "Semantic models support OAP (preview) but need a rule even for Fabric "
                  "sources; without it the refresh fails.",
        "connection_rules": [
            "SQL Server connector: SQL analytics endpoint FQDN of the DE_ lakehouse",
            "ADLS Gen2 connector: OneLake URL of the DE_ workspace",
        ],
    },
    "BI": {
        "outbound_access_protection": "off",
        "reason": "BI_ reports bind to semantic models in DM_ (another workspace). Under OAP a "
                  "report may bind only to a model in the same workspace (preview), and the "
                  "OAP overview still lists reports as unsupported.",
        "connection_rules": [],
    },
    "Shared": {
        "outbound_access_protection": "open_decision",
        "reason": "No items declared for Shared; nothing to decide yet.",
        "connection_rules": [],
    },
}

#: OAP prerequisites/consequences that hold for every protected workspace (same sources).
OAP_PRECONDITIONS = (
    "Tenant setting 'Configure workspace-level outbound network rules' enabled",
    "Workspace on a Fabric F SKU (no trial, P or EM SKU)",
    "Only OAP-supported items in the workspace (no report, dashboard, paginated report)",
    "'Allow Git integration' on before any Git operation, else connect/update fails",
    "PUT .../networking/communicationPolicy must also send 'inbound', else it resets to Allow",
)

#: W1.12 — allowed item types per workspace type (target picture for the Fabric policy
#: "Allow item creation", capacity scope, preview). None = not restricted.
ALLOWED_ITEM_TYPES_BY_LAYER = {
    "DE": ("Lakehouse", "Notebook", "DataPipeline"),
    "DM": ("SemanticModel",),
    "BI": ("Report",),
    "Shared": None,
}

#: Learn fabric/governance/fabric-policies-overview (read 01.10.2026), General limitations.
FABRIC_POLICY_UNSUPPORTED_REGIONS = ("West Europe", "North Europe", "West US")

#: W1.11 — workspace surge-protection class per environment (preview).
#: "mission_critical" = workspace availability "Mission critical" (exempt from the workspace
#: CU limit); "capped" = availability "Available" under the capacity-wide workspace CU limit.
SURGE_CLASS_BY_ENVIRONMENT = {
    "dev": "capped",
    "tst": "capped",
    "prd": "mission_critical",
}
SURGE_AVAILABILITY = {"mission_critical": "Mission critical", "capped": "Available"}


def _surge_target(env_definition: dict) -> dict:
    """Surge-protection target for the environment of ``env_definition``.

    The workspace CU limit is ONE percentage per capacity (Learn enterprise/surge-protection,
    read 01.10.2026), so it lives in ``generic.surge_protection`` of the environment JSON and
    stays None until the capacity admin sets it.
    """
    generic = env_definition.get("generic", {})
    environment = generic.get("environment_name", "dev")
    surge_class = SURGE_CLASS_BY_ENVIRONMENT.get(environment)
    if surge_class is None:
        raise ValueError(f"no surge class declared for environment '{environment}'")
    surge_cfg = generic.get("surge_protection") or {}
    target = {
        "class": surge_class,
        "workspace_availability": SURGE_AVAILABILITY[surge_class],
        "capacity": generic.get("capacity_name"),
        "mechanism": "manual",
        "manual_path": "OneLake catalog > Govern > Capacities > <capacity> > Workspaces > "
                       "gear icon > Workspace availability",
    }
    if surge_class == "capped":
        target["workspace_cu_limit_pct"] = surge_cfg.get("workspace_cu_limit_pct")
        target["block_hours"] = surge_cfg.get("block_hours")
    return target


def item_type_violations(env_definition: dict) -> list:
    """Layers whose configured ``items`` contain a type outside the allowed list (W1.12)."""
    violations = []
    for layer_name, layer_def in env_definition.get("layers", {}).items():
        if not isinstance(layer_def, dict):
            continue
        allowed = ALLOWED_ITEM_TYPES_BY_LAYER.get(layer_name)
        if allowed is None:
            continue
        for item_type in (layer_def.get("items") or {}):
            if item_type not in allowed:
                violations.append(f"{layer_name}: item type '{item_type}' not in {list(allowed)}")
    return violations


def _item_creation_rules(workspace_names: dict) -> list:
    """Allow-list rules for the 'Allow item creation' policy (target picture).

    An active rule turns the policy into an allow list for the WHOLE capacity, so a last rule
    keeps every other workspace unrestricted (Learn example "Limit item creation in production
    workspaces"). Workspace conditions are ID-based in Fabric; names here are placeholders.
    """
    rules = []
    restricted = []
    for layer_name, ws_name in workspace_names.items():
        allowed = ALLOWED_ITEM_TYPES_BY_LAYER.get(layer_name)
        if allowed is None:
            continue
        restricted.append(ws_name)
        rules.append({
            "name": f"{layer_name}-item-types",
            "workspaces": {"AnyOf": [ws_name]},
            "item_type": {"AnyOf": list(allowed)},
        })
    if restricted:
        rules.append({"name": "all-other-workspaces", "workspaces": {"NoneOf": restricted}})
    return rules


def workspace_target_picture(env_definition: dict) -> dict:
    """Declared target values per workspace of one environment (no Fabric call)."""
    generic = env_definition.get("generic", {})
    environment = generic.get("environment_name", "dev")
    template = env_definition.get("name", "")
    workspace_names = {}
    workspaces = []
    for layer_name, layer_def in env_definition.get("layers", {}).items():
        if not isinstance(layer_def, dict):
            continue
        ws_name = misc.format_workspace_name(template, layer_name, environment)
        workspace_names[layer_name] = ws_name
        network = NETWORK_STANCE_BY_LAYER.get(layer_name)
        if network is None:
            raise ValueError(f"no network stance declared for layer '{layer_name}'")
        allowed = ALLOWED_ITEM_TYPES_BY_LAYER.get(layer_name)
        workspaces.append({
            "layer": layer_name,
            "workspace": ws_name,
            "outbound_access_protection": network["outbound_access_protection"],
            "oap_reason": network["reason"],
            "oap_connection_rules": list(network["connection_rules"]),
            "allowed_item_types": list(allowed) if allowed is not None else None,
        })
    return {
        "environment": environment,
        "workspaces": workspaces,
        "oap_preconditions": list(OAP_PRECONDITIONS),
        "surge_protection": _surge_target(env_definition),
        "item_creation_policy": {
            "status": "target_picture",
            "scope": "capacity",
            "capacity": generic.get("capacity_name"),
            "unsupported_regions": list(FABRIC_POLICY_UNSUPPORTED_REGIONS),
            "rules": _item_creation_rules(workspace_names),
        },
        "item_type_violations": item_type_violations(env_definition),
    }


def print_workspace_target_picture(picture: dict) -> None:
    """Print the target picture as manual steps (nothing here is applied by this script)."""
    misc.print_header("Workspace target picture (manual steps, not applied)")
    for ws in picture["workspaces"]:
        types = ws["allowed_item_types"]
        misc.print_info(f"  {ws['workspace']}: OAP={ws['outbound_access_protection']}; "
                        f"item types={', '.join(types) if types else 'not restricted'}")
        for rule in ws["oap_connection_rules"]:
            misc.print_info(f"    - OAP rule: {rule}")
    surge = picture["surge_protection"]
    line = (f"  Surge protection: class={surge['class']} "
            f"(workspace availability '{surge['workspace_availability']}')")
    if surge["class"] == "capped":
        pct = surge["workspace_cu_limit_pct"]
        line += (f", capacity '{surge['capacity']}' workspace CU limit="
                 f"{str(pct) + '%' if pct is not None else 'LEERSTELLE (capacity admin)'}")
    misc.print_info(line)
    misc.print_info(f"    - no documented API; set via {surge['manual_path']}")
    regions = ", ".join(picture["item_creation_policy"]["unsupported_regions"])
    misc.print_info(f"  Item creation policy (preview): not available in {regions}")
    for violation in picture["item_type_violations"]:
        misc.print_warning(f"  Item type outside target picture: {violation}")


def setup_connections(env_definition, tenant_id, client_id, client_secret, github_pat, dry_run=False):
    """Create and configure Fabric connections."""
    generic = env_definition.get("generic", {})
    is_primary = generic.get("is_primary", False)
    fabric_connections = generic.get("fabric_connections", [])
    connection_permissions = generic.get("permissions", {})
    environment = generic.get("environment_name", "dev")

    if not fabric_connections or not is_primary:
        return None

    misc.print_header("Configuring Fabric Connections")

    if dry_run:
        misc.print_info("  [DRY-RUN] Would create connections:", bold=True)

    created_connections = {}

    for connection in fabric_connections:
        connection_name = misc.replace_template_variables(
            connection.get("name"),
            {"environment": environment}
        )

        misc.print_info(f"Creating Fabric connection '{connection_name}'...", bold=True, end="")

        if dry_run:
            misc.print_info(" [DRY-RUN]")
            created_connections[connection_name] = {"id": "dry-run-id", "name": connection_name}
            continue

        if fabcli.connection_exists(connection_name):
            misc.print_warning(" [Already exists]")
            created_connections[connection_name] = fabcli.get_connection(connection_name)
        else:
            connection_obj = fabcli.create_fabric_connection(
                connection_name,
                connection.get("type"),
                tenant_id,
                client_id,
                client_secret
            )

            if connection_obj:
                misc.print_success(f" {misc.CHECKMARK}")
                created_connections[connection_name] = connection_obj

                # Assign connection permissions
                if connection_permissions:
                    print(f"  {misc.BULLET} Assigning connection permissions...", end="")
                    for permission_role, definitions in connection_permissions.items():
                        for definition in definitions:
                            role = "Owner" if permission_role == "Admin" else "User"
                            fabcli.add_connection_roleassignment(
                                connection_obj.get("id"),
                                definition.get("id"),
                                definition.get("type"),
                                role
                            )
                    misc.print_success(f" {misc.CHECKMARK}")
            else:
                misc.print_error(f" {misc.CROSSMARK} Failed!")

    return created_connections


def setup_git_connection(env_definition, tenant_id, client_id, client_secret, github_pat, dry_run=False):
    """Create and configure Git connection."""
    generic = env_definition.get("generic", {})
    git_settings = generic.get("git_settings")
    environment = generic.get("environment_name", "dev")

    if not git_settings:
        return None

    misc.print_header("Configuring Git Connection")

    if dry_run:
        misc.print_info("  [DRY-RUN] Would create Git connection", bold=True)

    git_creds = git_settings.get("myGitCredentials", {})
    connection_name_template = git_creds.get("connection_name", "")
    connection_name = misc.replace_template_variables(
        connection_name_template,
        {"environment": environment}
    )

    misc.print_info(f"Creating source control connection '{connection_name}'...", bold=True, end="")

    if dry_run:
        misc.print_info(" [DRY-RUN]")
        return {"id": "dry-run-git-id", "name": connection_name}

    if fabcli.connection_exists(connection_name):
        misc.print_warning(" [Already exists]")
        git_connection = fabcli.get_connection(connection_name)
    else:
        git_provider = git_settings.get("gitProviderDetails", {})
        provider_type = git_provider.get("gitProviderType", "").lower()

        if provider_type == "github":
            owner = git_provider.get("ownerName")
            repo = git_provider.get("repositoryName")
            repo_url = f"https://github.com/{owner}/{repo}"
            git_connection = fabcli.create_github_connection(connection_name, repo_url, github_pat)
        else:  # AzureDevOps
            org = git_provider.get("organizationName")
            project = git_provider.get("projectName")
            repo = git_provider.get("repositoryName")
            repo_url = f"https://dev.azure.com/{org}/{project}/_git/{repo}"
            git_connection = fabcli.create_azuredevops_connection(
                connection_name, repo_url, tenant_id, client_id, client_secret
            )

        if git_connection:
            misc.print_success(f" {misc.CHECKMARK}")

            # Assign connection permissions
            connection_permissions = generic.get("permissions", {})
            if connection_permissions:
                print(f"  {misc.BULLET} Assigning connection permissions...", end="")
                for permission_role, definitions in connection_permissions.items():
                    for definition in definitions:
                        role = "Owner" if permission_role == "Admin" else "User"
                        fabcli.add_connection_roleassignment(
                            git_connection.get("id"),
                            definition.get("id"),
                            definition.get("type"),
                            role
                        )
                misc.print_success(f" {misc.CHECKMARK}")
        else:
            misc.print_error(f" {misc.CROSSMARK} Failed!")
            return None

    return git_connection


def _create_workspace_if_missing(workspace_name, capacity_name, dry_run, fabcli) -> dict:
    """Check existence and create if missing. Return workspace info dict."""
    if dry_run:
        return {"id": "dry-run-workspace-id", "displayName": workspace_name}

    if fabcli.workspace_exists(workspace_name):
        misc.print_warning(f"Workspace '{workspace_name}' already exists")
        workspace = fabcli.get_workspace(workspace_name)
    else:
        misc.print_info(f"Creating workspace '{workspace_name}'...", bold=True, end="")
        workspace = fabcli.create_workspace(workspace_name, capacity_name)

        if workspace:
            misc.print_success(f" {misc.CHECKMARK}")
        else:
            misc.print_error(f" {misc.CROSSMARK} Failed!")

    return workspace


def _assign_workspace_permissions(workspace_id, permissions, dry_run, fabcli) -> None:
    """Assign role assignments to workspace."""
    if not permissions or dry_run:
        return

    misc.print_info(f"  {misc.BULLET} Assigning workspace permissions...", end="")
    for role_name, principals in permissions.items():
        if not principals:
            continue
        for principal in principals:
            fabcli.add_workspace_roleassignment(
                workspace_id,
                principal.get("id"),
                principal.get("type"),
                role_name
            )
    misc.print_success(f" {misc.CHECKMARK}")


def _provision_workspace_items(workspace_id, items, dry_run, fabcli, workspace_name) -> None:
    """Create items (Lakehouse etc.) in workspace. Includes SQL endpoint wait."""
    if not items or dry_run:
        return

    misc.print_info(f"  {misc.BULLET} Creating workspace items...")
    for item_type, item_list in items.items():
        if not isinstance(item_list, list):
            continue
        for item_def in item_list:
            if item_def.get("skip_item_creation", False):
                continue

            item_name = item_def.get("item_name")
            if not item_name:
                continue

            misc.print_info(f"    {misc.BULLET} {item_type}: {item_name}...", end="")

            item_path = f"{workspace_name}.Workspace/{item_name}.{item_type}"
            if fabcli.item_exists(item_path):
                misc.print_warning(" [Already exists]")
            else:
                # Create item via CLI
                result = fabcli.run_command(f"create '{item_path}'")
                if result:
                    misc.print_success(f" {misc.CHECKMARK}")
                    # Wait for Lakehouse SQL endpoint if needed
                    if item_type == "Lakehouse":
                        time.sleep(5)  # Give time for SQL endpoint provisioning
                else:
                    misc.print_error(f" {misc.CROSSMARK} Failed!")


def setup_workspaces(env_definition, capacity_name, dry_run=False):
    """Create workspaces for each layer."""
    solution_name_template = env_definition.get("name", "")
    layers = env_definition.get("layers", {})
    environment = env_definition.get("generic", {}).get("environment_name", "dev")
    generic_permissions = env_definition.get("generic", {}).get("permissions", {})

    misc.print_header(f"Setting up {environment.upper()} environment workspaces")

    if dry_run:
        misc.print_info("  [DRY-RUN] Would create workspaces:", bold=True)

    created_workspaces = {}

    for layer_name, layer_def in layers.items():
        if not isinstance(layer_def, dict):
            continue

        workspace_name = misc.format_workspace_name(
            solution_name_template,
            layer_name,
            environment
        )

        misc.print_subheader(f"Layer: {layer_name} - Workspace: {workspace_name}")

        if dry_run:
            misc.print_info(f"  [DRY-RUN] Would create workspace: {workspace_name}")
            misc.print_info(f"    - Capacity: {capacity_name}")
            misc.print_info(f"    - Git Directory: {layer_def.get('git_directoryName', 'N/A')}")
            created_workspaces[layer_name] = {
                "workspace_id": "dry-run-workspace-id",
                "workspace_name": workspace_name,
                "workspace": {"id": "dry-run-workspace-id", "displayName": workspace_name}
            }
            continue

        workspace = _create_workspace_if_missing(workspace_name, capacity_name, dry_run, fabcli)

        if not workspace:
            continue

        workspace_id = workspace.get("id")
        created_workspaces[layer_name] = {
            "workspace_id": workspace_id,
            "workspace_name": workspace_name,
            "workspace": workspace
        }

        # Assign workspace permissions
        layer_permissions = layer_def.get("permissions") or generic_permissions
        _assign_workspace_permissions(workspace_id, layer_permissions, dry_run, fabcli)

        # Create workspace identity if needed
        if layer_def.get("create_workspace_identity", False):
            misc.print_info(f"  {misc.BULLET} Creating workspace identity...", end="")
            # Note: Workspace identity creation via CLI may require additional implementation
            misc.print_warning(" [Not implemented yet]")

        # Create workspace items if specified
        _provision_workspace_items(workspace_id, layer_def.get("items", {}), dry_run, fabcli, workspace_name)

    return created_workspaces


def connect_workspaces_to_git(env_definition, created_workspaces, git_connection, dry_run=False):
    """Connect workspaces to Git repository."""
    if not git_connection or not created_workspaces:
        return

    misc.print_header("Connecting workspaces to Git")

    if dry_run:
        misc.print_info("  [DRY-RUN] Would connect workspaces to Git", bold=True)

    generic = env_definition.get("generic", {})
    git_settings = generic.get("git_settings", {})
    git_provider = git_settings.get("gitProviderDetails", {})
    branch_name = git_provider.get("branchName", "main")

    layers = env_definition.get("layers", {})

    for layer_name, workspace_info in created_workspaces.items():
        workspace_id = workspace_info.get("workspace_id")
        workspace_name = workspace_info.get("workspace_name")
        layer_def = layers.get(layer_name, {})
        git_directory = layer_def.get("git_directoryName", "")

        if not git_directory:
            misc.print_warning(f"  [No git_directoryName for layer {layer_name}, skipping Git connection]")
            continue

        misc.print_info(f"Connecting '{workspace_name}' to Git (branch: {branch_name}, "
                        f"folder: {git_directory})...", end="")

        if dry_run:
            misc.print_info(" [DRY-RUN]")
            continue

        # Prepare Git connection settings
        git_connect_settings = {
            "connectionId": git_connection.get("id"),
            "repositoryUrl": git_provider.get("repositoryUrl", ""),
            "branchName": branch_name,
            "folderName": git_directory
        }

        result = fabcli.connect_workspace_to_git(workspace_id, git_connect_settings)

        if result:
            misc.print_success(f" {misc.CHECKMARK}")
        else:
            misc.print_error(f" {misc.CROSSMARK} Failed!")


def load_env_definition(environment: str):
    """Merged ``infrastructure.json`` + ``infrastructure.<environment>.json`` (None on error)."""
    env_dir = Path(__file__).parent.parent / "resources" / "environments"
    base_json = misc.load_json(str(env_dir / "infrastructure.json"))
    env_json = misc.load_json(str(env_dir / f"infrastructure.{environment}.json"))
    if not base_json or not env_json:
        return None
    return misc.merge_json(base_json, env_json)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Fabric Infrastructure Setup Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fabric_setup.py --environment dev
  python fabric_setup.py --environment tst --action create
  python fabric_setup.py --environment prd --dry-run  # Simulate without executing
        """
    )

    parser.add_argument(
        "--environment",
        required=False,
        default=DEFAULT_ENVIRONMENT,
        choices=["dev", "tst", "prd"],
        help=f"Environment to setup (default: {DEFAULT_ENVIRONMENT})"
    )

    parser.add_argument(
        "--action",
        required=False,
        default=DEFAULT_ACTION,
        choices=["create", "delete"],
        help=f"Action to perform (default: {DEFAULT_ACTION})"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate execution without making actual changes (no Fabric capacity required)"
    )

    parser.add_argument(
        "--tenant_id",
        required=False,
        default=os.environ.get('TENANT_ID'),
        help="Azure AD tenant ID (or set TENANT_ID env var)"
    )

    parser.add_argument(
        "--client_id",
        required=False,
        default=os.environ.get('CLIENT_ID'),
        help="Service principal client ID (or set CLIENT_ID env var)"
    )

    # Geheimnisse nur ueber CLIENT_SECRET / GITHUB_PAT; die Argumente lehnen
    # einen alten Aufruf ab, statt den Wert in der Prozessliste zu dulden.
    parser.add_argument(
        "--client_secret",
        required=False,
        default=None,
        help=argparse.SUPPRESS
    )

    parser.add_argument(
        "--github_pat",
        required=False,
        default=None,
        help=argparse.SUPPRESS
    )

    parser.add_argument(
        "--skip-framework-validation",
        action="store_true",
        help="Skip Stage 1 and Fabric checks (requires repo root and PowerShell when not set)"
    )

    parser.add_argument(
        "--enable-rollback",
        action="store_true",
        help="On failure, roll back (delete) created workspaces and connections"
    )

    parser.add_argument(
        "--target-picture",
        action="store_true",
        help="Print the declared workspace target picture (OAP stance, surge class, allowed "
             "item types) for --environment as JSON and exit; no auth, no Fabric call"
    )

    args = parser.parse_args()
    args.client_secret = fabcli.secret_from_environment(
        args.client_secret, "--client_secret", "CLIENT_SECRET")
    args.github_pat = fabcli.secret_from_environment(
        args.github_pat, "--github_pat", "GITHUB_PAT")

    if args.target_picture:
        definition = load_env_definition(args.environment)
        if not definition:
            misc.print_error("Failed to load environment configuration files")
            sys.exit(1)
        print(json.dumps(workspace_target_picture(definition), indent=2, ensure_ascii=False))
        sys.exit(0)

    # In dry-run mode, skip authentication
    if not args.dry_run:
        # Validate required arguments
        if not args.tenant_id or not args.client_id or not args.client_secret:
            misc.print_error("Error: tenant_id, client_id, and client_secret are required (or use --dry-run)")
            misc.print_info("Set TENANT_ID/CLIENT_ID as arguments or environment variables, "
                            "CLIENT_SECRET only as environment variable")
            sys.exit(1)

        # Authenticate with Fabric CLI
        misc.print_header("Authenticating with Fabric")
        fabcli.run_command("config set encryption_fallback_enabled true")
        if not fabcli.login_service_principal(args.tenant_id, args.client_id, args.client_secret):
            misc.print_error("Authentication failed: fab auth status meldet keine Anmeldung")
            sys.exit(1)

        misc.print_success("Authentication successful")
    else:
        misc.print_header("DRY-RUN MODE - No actual changes will be made")
        misc.print_info("Simulating setup without Fabric capacity or authentication", bold=True)

    # Load and merge environment JSON files
    env_definition = load_env_definition(args.environment)
    if not env_definition:
        misc.print_error("Failed to load environment configuration files")
        sys.exit(1)

    # Run pre-flight checks
    checker = preflight.PreflightChecker(
        args.environment,
        env_definition,
        args.dry_run,
        skip_framework_validation=getattr(args, "skip_framework_validation", False),
    )
    all_checks_passed, check_results = checker.check_all()

    checker.print_summary()

    if not all_checks_passed:
        misc.print_error("Pre-flight checks failed. Please fix the issues above before proceeding.")
        misc.print_info("You can use --dry-run to validate configuration without Fabric capacity.")
        sys.exit(1)

    if args.action.lower() == "create":
        enable_rollback = getattr(args, "enable_rollback", False) and rollback and not args.dry_run
        created_workspaces_list = []
        created_connections_list = []

        try:
            # Setup connections
            fabric_connections = setup_connections(
                env_definition, args.tenant_id, args.client_id, args.client_secret, args.github_pat, args.dry_run
            )
            if enable_rollback and fabric_connections:
                created_connections_list = [
                    {"id": c.get("id"), "name": c.get("name")}
                    for c in fabric_connections.values() if isinstance(c, dict)
                ]

            # Setup Git connection
            git_connection = setup_git_connection(
                env_definition, args.tenant_id, args.client_id, args.client_secret, args.github_pat, args.dry_run
            )

            # Setup workspaces
            capacity_name = env_definition.get("generic", {}).get("capacity_name", "MyCapacity")
            created_workspaces = setup_workspaces(env_definition, capacity_name, args.dry_run)
            print_workspace_target_picture(workspace_target_picture(env_definition))
            if enable_rollback and created_workspaces:
                created_workspaces_list = [
                    {"id": w.get("id"), "name": w.get("name")}
                    for w in created_workspaces.values() if isinstance(w, dict)
                ]

            # Connect workspaces to Git
            if git_connection:
                connect_workspaces_to_git(env_definition, created_workspaces, git_connection, args.dry_run)

            # Run post-deployment health checks
            health_checker = None
            health_results_list = []
            if not args.dry_run:
                health_checker = health.HealthChecker(args.environment, env_definition, args.dry_run)
                all_healthy, health_results_list = health_checker.check_all()
                health_checker.print_summary()

            if not args.dry_run and report_gen:
                preflight_dicts = [
                    {"name": r.name, "passed": r.passed, "message": r.message, **r.details}
                    for r in checker.results
                ]
                health_dicts = [
                    {"name": r.name, "status": r.status, "message": r.message, **r.details}
                    for r in health_results_list
                ]
                workspace_details = [
                    {"name": w.get("name"), "id": w.get("id")}
                    for w in created_workspaces.values() if isinstance(w, dict)
                ]
                html_path, json_path = report_gen.write_report(
                    args.environment,
                    True,
                    preflight_results=preflight_dicts,
                    health_results=health_dicts,
                    workspace_details=workspace_details,
                )
                if html_path:
                    misc.print_info(f"Deployment report: {html_path}")

            if enable_rollback and (created_workspaces_list or created_connections_list):
                snap_path, _ = rollback.create_snapshot(
                    args.environment,
                    "setup",
                    created_workspaces=created_workspaces_list,
                    created_connections=created_connections_list,
                )
                if snap_path:
                    misc.print_info(f"Rollback snapshot saved: {snap_path}")

            misc.print_header("Setup Complete")
            if args.dry_run:
                misc.print_success(f"Simulation completed for {args.environment.upper()} environment")
                misc.print_info("Run without --dry-run to execute actual setup")
            else:
                misc.print_success(f"Successfully set up {args.environment.upper()} environment")

        except Exception as e:
            if enable_rollback and (created_workspaces_list or created_connections_list):
                misc.print_error(f"Setup failed: {e}")
                misc.print_header("Rolling back created resources")
                snap_path, _ = rollback.create_snapshot(
                    args.environment,
                    "setup",
                    created_workspaces=created_workspaces_list,
                    created_connections=created_connections_list,
                )
                if snap_path:
                    success, errs = rollback.execute_rollback_setup(
                        rollback.load_snapshot(snap_path), dry_run=False
                    )
                    if not success:
                        for err in errs:
                            misc.print_error(err)
                raise
            raise

    elif args.action.lower() == "delete":
        misc.print_error("Delete action not yet implemented")
        sys.exit(1)


if __name__ == "__main__":
    main()
