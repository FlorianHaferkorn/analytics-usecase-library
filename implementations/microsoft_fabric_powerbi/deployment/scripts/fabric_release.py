#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fabric Release Script

Deploys PBIP/TMDL items from Git repository to Fabric workspaces using fabric-cicd library.

Usage:
    python fabric_release.py --environment dev --repo_path ./solution
    python fabric_release.py --environment tst --layers DE,DM --item_types SemanticModel,Report
"""
import os
import sys
import io
import time
import argparse
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

from fabric_cicd import FabricWorkspace, publish_all_items, unpublish_all_orphan_items
from azure.identity import ClientSecretCredential

import modules.fabric_cli_functions as fabcli
import modules.misc_functions as misc
import modules.retry_logic as retry_logic

try:
    import modules.framework_validator as framework_validator
except ImportError:
    framework_validator = None

try:
    import modules.parameter_validator as parameter_validator
except ImportError:
    parameter_validator = None

try:
    import modules.rollback_manager as rollback
except ImportError:
    rollback = None

# Default values
DEFAULT_ENVIRONMENT = "tst"
DEFAULT_REPO_PATH = "./solution"
DEFAULT_ITEM_TYPES = "Notebook,DataPipeline,Lakehouse,SemanticModel,Report"
DEFAULT_LAYERS = "DE,DM,BI,Shared"


def load_environment_config(environment: str):
    """Load and merge environment JSON configuration."""
    script_dir = Path(__file__).parent
    base_json_path = script_dir.parent / "resources" / "environments" / "infrastructure.json"
    env_json_path = script_dir.parent / "resources" / "environments" / f"infrastructure.{environment}.json"
    
    base_json = misc.load_json(str(base_json_path))
    env_json = misc.load_json(str(env_json_path))
    
    if not base_json or not env_json:
        misc.print_error(f"Failed to load environment configuration for {environment}")
        return None
    
    return misc.merge_json(base_json, env_json)


def get_workspace_id(workspace_name: str) -> str:
    """Get workspace ID by name."""
    workspace = fabcli.get_workspace(workspace_name)
    if workspace:
        return workspace.get("id", "")
    return ""


def release_to_workspace(
    workspace_name: str,
    workspace_id: str,
    repository_directory: str,
    item_types: list,
    environment: str,
    token_credential: ClientSecretCredential,
    unpublish_orphans: bool = True
):
    """Release items from repository directory to Fabric workspace."""
    misc.print_subheader(f"Releasing to workspace: {workspace_name}")
    
    if not os.path.exists(repository_directory):
        misc.print_error(f"Repository directory not found: {repository_directory}")
        return False
    
    target_workspace = FabricWorkspace(
        workspace_id=workspace_id,
        environment=environment.upper(),
        repository_directory=repository_directory,
        item_type_in_scope=item_types,
        token_credential=token_credential
    )

    max_retries = 3
    last_exc = None
    for attempt in range(max_retries + 1):
        try:
            misc.print_info(f"  {misc.BULLET} Publishing items from {repository_directory}...", end="")
            publish_all_items(target_workspace)
            misc.print_success(f" {misc.CHECKMARK}")
            break
        except Exception as e:
            last_exc = e
            if attempt < max_retries and retry_logic.is_transient_failure(e, str(e)):
                misc.print_warning(f" Transient failure (attempt {attempt + 1}/{max_retries + 1}), retrying...")
                time.sleep(2.0 * (2 ** attempt))
            else:
                misc.print_error(f" {misc.CROSSMARK} Failed: {e}")
                return False

    if unpublish_orphans:
        for attempt in range(max_retries + 1):
            try:
                misc.print_info(f"  {misc.BULLET} Unpublishing orphan items...", end="")
                unpublish_all_orphan_items(target_workspace)
                misc.print_success(f" {misc.CHECKMARK}")
                break
            except Exception as e:
                last_exc = e
                if attempt < max_retries and retry_logic.is_transient_failure(e, str(e)):
                    misc.print_warning(f" Transient failure (attempt {attempt + 1}/{max_retries + 1}), retrying...")
                    time.sleep(2.0 * (2 ** attempt))
                else:
                    misc.print_error(f" {misc.CROSSMARK} Unpublish failed: {e}")
                    return False

    return True


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Fabric Release Script - Deploy items from Git to Fabric",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fabric_release.py --environment dev --repo_path ./solution
  python fabric_release.py --environment tst --layers DE,DM
  python fabric_release.py --environment prd --item_types SemanticModel,Report
        """
    )
    
    parser.add_argument(
        "--environment",
        required=True,
        choices=["dev", "tst", "prd"],
        help="Target environment"
    )
    
    parser.add_argument(
        "--layers",
        required=False,
        default=DEFAULT_LAYERS,
        help=f"Comma-separated list of layers to deploy (default: {DEFAULT_LAYERS})"
    )
    
    parser.add_argument(
        "--item_types",
        required=False,
        default=DEFAULT_ITEM_TYPES,
        help=f"Comma-separated list of item types (default: {DEFAULT_ITEM_TYPES})"
    )
    
    parser.add_argument(
        "--repo_path",
        required=False,
        default=DEFAULT_REPO_PATH,
        help=f"Path to repository directory (default: {DEFAULT_REPO_PATH})"
    )
    
    parser.add_argument(
        "--unpublish_items",
        required=False,
        default=True,
        type=bool,
        help="Whether to unpublish orphan items (default: True)"
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
        "--skip-framework-validation",
        action="store_true",
        help="Skip Stage 1 and Fabric checks before release (requires repo root and PowerShell when not set)"
    )

    parser.add_argument(
        "--validate-parameters",
        action="store_true",
        help="Validate parameter.yml in each layer directory before release"
    )

    parser.add_argument(
        "--enable-rollback",
        action="store_true",
        help="Create snapshot before release; on failure, snapshot is saved for manual rollback or Git redeploy"
    )

    args = parser.parse_args()
    
    # Validate required arguments
    if not args.tenant_id or not args.client_id or not args.client_secret:
        misc.print_error("Error: tenant_id, client_id, and client_secret are required")
        misc.print_info("Set them as arguments or environment variables (TENANT_ID, CLIENT_ID, CLIENT_SECRET)")
        sys.exit(1)

    # Optional: run framework validation (Stage 1 + Fabric checks) before release
    if not args.skip_framework_validation and framework_validator:
        misc.print_header("Framework Validation")
        ok, msg, _ = framework_validator.run_framework_validation(
            include_stage1=True,
            include_fabric=True,
            dry_run=False,
        )
        if not ok:
            misc.print_error(msg)
            sys.exit(1)
        misc.print_success(msg)

    # Authenticate with Fabric CLI (for workspace lookup)
    misc.print_header("Authenticating with Fabric")
    fabcli.run_command("config set encryption_fallback_enabled true")
    auth_result = fabcli.run_command(
        f"auth login -u {args.client_id} -p {args.client_secret} --tenant {args.tenant_id}"
    )
    
    if "error" in auth_result.lower() or "failed" in auth_result.lower():
        misc.print_error(f"Authentication failed: {auth_result}")
        sys.exit(1)
    
    misc.print_success("Authentication successful")
    
    # Create token credential for fabric-cicd
    token_credential = ClientSecretCredential(
        tenant_id=args.tenant_id,
        client_id=args.client_id,
        client_secret=args.client_secret
    )
    
    # Load environment configuration
    env_definition = load_environment_config(args.environment)
    if not env_definition:
        sys.exit(1)
    
    # Parse layers and item types
    layers_to_deploy = [layer.strip().upper() for layer in args.layers.split(",")]
    item_type_list = [item_type.strip() for item_type in args.item_types.split(",")]
    
    # Get solution name template and capacity
    solution_name_template = env_definition.get("name", "")
    environment_name = env_definition.get("generic", {}).get("environment_name", args.environment)
    layers = env_definition.get("layers", {})
    
    misc.print_header(f"Releasing to {environment_name.upper()} environment")
    
    success_count = 0
    fail_count = 0
    enable_rollback = getattr(args, "enable_rollback", False) and rollback
    release_snapshot_path = None

    if enable_rollback:
        snap_path, _ = rollback.create_snapshot(
            args.environment,
            "release",
            created_workspaces=[],
            created_connections=[],
            items_by_workspace={},
        )
        if snap_path:
            release_snapshot_path = str(snap_path)
            misc.print_info(f"Rollback snapshot created: {release_snapshot_path}")

    # Deploy to each layer
    for layer_name, layer_def in layers.items():
        if layer_name.upper() not in layers_to_deploy:
            continue
        
        if not isinstance(layer_def, dict):
            continue
        
        # Get workspace name and ID
        workspace_name = misc.format_workspace_name(
            solution_name_template,
            layer_name,
            environment_name
        )
        
        workspace_id = get_workspace_id(workspace_name)
        if not workspace_id:
            misc.print_error(f"Workspace '{workspace_name}' not found")
            fail_count += 1
            continue
        
        # Get Git directory for this layer
        git_directory = layer_def.get("git_directoryName", f"solution/{layer_name.lower()}")
        repository_directory = os.path.join(args.repo_path, git_directory.replace("solution/", ""))

        # Optional parameter validation
        if getattr(args, "validate_parameters", False) and parameter_validator:
            ok, errs, _ = parameter_validator.validate_parameter_file_from_repo(
                args.repo_path,
                git_directory,
            )
            if not ok and errs:
                misc.print_warning(f"Parameter validation for {layer_name}: {errs[0]}")
                # Don't fail release; just warn

        # Release to workspace
        success = release_to_workspace(
            workspace_name=workspace_name,
            workspace_id=workspace_id,
            repository_directory=repository_directory,
            item_types=item_type_list,
            environment=args.environment,
            token_credential=token_credential,
            unpublish_orphans=args.unpublish_items
        )
        
        if success:
            success_count += 1
        else:
            fail_count += 1
    
    # Summary
    misc.print_header("Release Summary")
    misc.print_info(f"Successfully deployed to {success_count} workspace(s)")
    if fail_count > 0:
        misc.print_error(f"Failed to deploy to {fail_count} workspace(s)")
        if release_snapshot_path:
            misc.print_info(f"Rollback snapshot: {release_snapshot_path}")
            misc.print_info("To roll back: redeploy from Git (e.g. previous commit) or run fabric_rollback.py")
        sys.exit(1)
    else:
        misc.print_success("All deployments completed successfully")


if __name__ == "__main__":
    main()
