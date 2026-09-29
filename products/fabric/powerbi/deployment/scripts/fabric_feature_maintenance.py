#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Feature Branch Workspace Maintenance

Creates or deletes isolated Fabric workspaces for feature branches.

Usage:
    python fabric_feature_maintenance.py --action create --branch_name feature/my-feature
    python fabric_feature_maintenance.py --action delete --branch_name feature/my-feature
"""
import os
import sys
import io
import argparse
import re
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

DEFAULT_ACTION = "create"


def sanitize_branch_name(branch_name: str) -> str:
    """Sanitize branch name for use in workspace name."""
    # Remove 'feature/' prefix if present
    name = branch_name.replace("feature/", "").replace("features/", "")
    # Replace invalid characters with underscore
    name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    # Limit length
    if len(name) > 50:
        name = name[:50]
    return name


def create_feature_workspace(branch_name: str, env_definition, capacity_name: str):
    """Create workspace for feature branch."""
    sanitized_name = sanitize_branch_name(branch_name)
    workspace_name = f"DE_Feature_{sanitized_name} [dev]"
    
    misc.print_header(f"Creating feature workspace: {workspace_name}")
    
    if fabcli.workspace_exists(workspace_name):
        misc.print_warning(f"Workspace '{workspace_name}' already exists")
        return fabcli.get_workspace(workspace_name)
    
    misc.print_info(f"Creating workspace '{workspace_name}'...", bold=True, end="")
    workspace = fabcli.create_workspace(workspace_name, capacity_name)
    
    if workspace:
        misc.print_success(f" {misc.CHECKMARK}")
        misc.print_info(f"Workspace ID: {workspace.get('id')}")
        return workspace
    else:
        misc.print_error(f" {misc.CROSSMARK} Failed!")
        return None


def delete_feature_workspace(branch_name: str):
    """Delete workspace for feature branch (safety checks included)."""
    sanitized_name = sanitize_branch_name(branch_name)
    workspace_name = f"DE_Feature_{sanitized_name} [dev]"
    
    # Safety check: only delete if name matches pattern and is in dev
    if "Feature_" not in workspace_name or "[dev]" not in workspace_name:
        misc.print_error(f"Safety check failed: workspace name '{workspace_name}' does not match feature pattern")
        return False
    
    misc.print_header(f"Deleting feature workspace: {workspace_name}")
    
    if not fabcli.workspace_exists(workspace_name):
        misc.print_warning(f"Workspace '{workspace_name}' does not exist")
        return True
    
    misc.print_info(f"Deleting workspace '{workspace_name}'...", bold=True, end="")
    
    # Note: Workspace deletion via Fabric CLI may require additional implementation
    # For now, warn user to delete manually
    misc.print_warning(" [Workspace deletion via CLI not fully implemented]")
    misc.print_info("Please delete workspace manually in Fabric portal or implement deletion API call")
    
    return False


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Feature Branch Workspace Maintenance",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--action",
        required=False,
        default=DEFAULT_ACTION,
        choices=["create", "delete"],
        help=f"Action to perform (default: {DEFAULT_ACTION})"
    )
    
    parser.add_argument(
        "--branch_name",
        required=True,
        help="Feature branch name (e.g., 'feature/my-feature')"
    )
    
    parser.add_argument(
        "--tenant_id",
        required=False,
        default=os.environ.get('TENANT_ID'),
        help="Azure AD tenant ID"
    )
    
    parser.add_argument(
        "--client_id",
        required=False,
        default=os.environ.get('CLIENT_ID'),
        help="Service principal client ID"
    )
    
    # Geheimnis nur ueber CLIENT_SECRET; das Argument lehnt einen alten Aufruf ab.
    parser.add_argument(
        "--client_secret",
        required=False,
        default=None,
        help=argparse.SUPPRESS
    )
    
    args = parser.parse_args()
    args.client_secret = fabcli.secret_from_environment(
        args.client_secret, "--client_secret", "CLIENT_SECRET")
    
    # Validate required arguments
    if not args.tenant_id or not args.client_id or not args.client_secret:
        misc.print_error("Error: tenant_id, client_id, and client_secret are required")
        sys.exit(1)
    
    # Authenticate
    misc.print_header("Authenticating with Fabric")
    fabcli.run_command("config set encryption_fallback_enabled true")
    if not fabcli.login_service_principal(args.tenant_id, args.client_id, args.client_secret):
        misc.print_error("Authentication failed: fab auth status meldet keine Anmeldung")
        sys.exit(1)
    
    misc.print_success("Authentication successful")
    
    # Load base configuration (for capacity name)
    script_dir = Path(__file__).parent
    base_json_path = script_dir.parent / "resources" / "environments" / "infrastructure.json"
    base_json = misc.load_json(str(base_json_path))
    
    if not base_json:
        misc.print_error("Failed to load base configuration")
        sys.exit(1)
    
    capacity_name = base_json.get("generic", {}).get("capacity_name", "MyCapacity")
    
    if args.action == "create":
        workspace = create_feature_workspace(args.branch_name, base_json, capacity_name)
        if workspace:
            misc.print_success("Feature workspace created successfully")
        else:
            misc.print_error("Failed to create feature workspace")
            sys.exit(1)
    
    elif args.action == "delete":
        success = delete_feature_workspace(args.branch_name)
        if success:
            misc.print_success("Feature workspace deleted successfully")
        else:
            misc.print_error("Failed to delete feature workspace")
            sys.exit(1)


if __name__ == "__main__":
    main()
