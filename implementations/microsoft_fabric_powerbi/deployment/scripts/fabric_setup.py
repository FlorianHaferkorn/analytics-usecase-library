#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fabric Infrastructure Setup Script

Creates Fabric workspaces, connections, Git integration, and permissions
based on environment JSON configuration files.

Usage:
    python fabric_setup.py --environment dev --tenant_id <id> --client_id <id> --client_secret <secret>
    python fabric_setup.py --environment dev --dry-run  # Simulate without executing
"""
import os
import sys
import io
import argparse
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
        
        # Check if workspace exists
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
                continue
        
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
        if layer_permissions:
            misc.print_info(f"  {misc.BULLET} Assigning workspace permissions...", end="")
            for role_name, principals in layer_permissions.items():
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
        
        # Create workspace identity if needed
        if layer_def.get("create_workspace_identity", False):
            misc.print_info(f"  {misc.BULLET} Creating workspace identity...", end="")
            # Note: Workspace identity creation via CLI may require additional implementation
            misc.print_warning(" [Not implemented yet]")
        
        # Create workspace items if specified
        items = layer_def.get("items", {})
        if items:
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
        
        misc.print_info(f"Connecting '{workspace_name}' to Git (branch: {branch_name}, folder: {git_directory})...", end="")
        
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
    
    parser.add_argument(
        "--client_secret",
        required=False,
        default=os.environ.get('CLIENT_SECRET'),
        help="Service principal client secret (or set CLIENT_SECRET env var)"
    )
    
    parser.add_argument(
        "--github_pat",
        required=False,
        default=os.environ.get('GITHUB_PAT'),
        help="GitHub Personal Access Token (or set GITHUB_PAT env var)"
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

    args = parser.parse_args()
    
    # In dry-run mode, skip authentication
    if not args.dry_run:
        # Validate required arguments
        if not args.tenant_id or not args.client_id or not args.client_secret:
            misc.print_error("Error: tenant_id, client_id, and client_secret are required (or use --dry-run)")
            misc.print_info("Set them as arguments or environment variables (TENANT_ID, CLIENT_ID, CLIENT_SECRET)")
            sys.exit(1)
        
        # Authenticate with Fabric CLI
        misc.print_header("Authenticating with Fabric")
        fabcli.run_command("config set encryption_fallback_enabled true")
        auth_result = fabcli.run_command(
            f"auth login -u {args.client_id} -p {args.client_secret} --tenant {args.tenant_id}"
        )
        
        if "error" in auth_result.lower() or "failed" in auth_result.lower():
            misc.print_error(f"Authentication failed: {auth_result}")
            sys.exit(1)
        
        misc.print_success("Authentication successful")
    else:
        misc.print_header("DRY-RUN MODE - No actual changes will be made")
        misc.print_info("Simulating setup without Fabric capacity or authentication", bold=True)
    
    # Load and merge environment JSON files
    script_dir = Path(__file__).parent
    base_json_path = script_dir.parent / "resources" / "environments" / "infrastructure.json"
    env_json_path = script_dir.parent / "resources" / "environments" / f"infrastructure.{args.environment}.json"
    
    base_json = misc.load_json(str(base_json_path))
    env_json = misc.load_json(str(env_json_path))
    
    if not base_json or not env_json:
        misc.print_error("Failed to load environment configuration files")
        sys.exit(1)
    
    env_definition = misc.merge_json(base_json, env_json)
    
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
            if enable_rollback and created_workspaces:
                created_workspaces_list = [
                    {"id": w.get("id"), "name": w.get("name")}
                    for w in created_workspaces.values() if isinstance(w, dict)
                ]

            # Connect workspaces to Git
            if git_connection:
                connect_workspaces_to_git(env_definition, created_workspaces, git_connection, args.dry_run)

            # Run post-deployment health checks
            if not args.dry_run:
                health_checker = health.HealthChecker(args.environment, env_definition, args.dry_run)
                all_healthy, health_results = health_checker.check_all()
                health_checker.print_summary()

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
