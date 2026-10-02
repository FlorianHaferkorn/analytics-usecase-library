#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fabric Release Script

Deploys PBIP/TMDL items from Git repository to Fabric workspaces using fabric-cicd library.

Usage:
    python fabric_release.py --environment dev --repo_path ./solution
    python fabric_release.py --environment tst --layers DE,DM --item_types SemanticModel,Report

Deployment path: fabric-cicd (Fabric Items APIs), not Fabric deployment pipelines. The Learn
restriction "deployment pipelines are not supported with workspace inbound access protection"
(fabric/cicd/cicd-security, read 01.10.2026) therefore does not apply to this script; with
inbound protection the agent running it must still reach Fabric from an allowed network.
"""
import os
import sys
import io
import json
import time
import shutil
import argparse
import re
import tempfile
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

try:
    import modules.retry_logic as retry_logic
except ImportError:
    retry_logic = None

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

try:
    import modules.report_generator as report_gen
except ImportError:
    report_gen = None

# Default values
DEFAULT_ENVIRONMENT = "tst"
DEFAULT_REPO_PATH = "./solution"
DEFAULT_ITEM_TYPES = "Notebook,DataPipeline,Lakehouse,SemanticModel,Report"
DEFAULT_LAYERS = "DE,DM,BI,Shared"

# --- Deployment plan (preview), I-21 W2.7 ----------------------------------------------------
# Learn fabric/cicd/deployment-plan/deployment-plan-automation (read 01.10.2026): a plan is
# attached by adding `options.deploymentPlan` to Update From Git, Deploy Stage Content or Bulk
# Import Item Definitions, each with `?beta=true` and the extra scope Item.Execute.All. The same
# page states that the fabric-cicd library does NOT support deployment plans. This script
# publishes through fabric-cicd, so the flag only resolves and prints the documented Bulk Import
# request (dry run); a live release with a plan is refused instead of silently dropping it.
FABRIC_API = "https://api.fabric.microsoft.com/v1"
DEPLOYMENT_PLAN_SCOPES = ("Item.ReadWrite.All", "Item.Execute.All")
_GUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")



def _parse_bool(value: str) -> bool:
    """argparse helper: ``type=bool`` turns every non-empty string, including "false", into True."""
    v = str(value).strip().lower()
    if v in ("true", "1", "yes", "y"):
        return True
    if v in ("false", "0", "no", "n"):
        return False
    raise argparse.ArgumentTypeError(f"expected true or false, got {value!r}")

def deployment_plan_request(workspace_id: str, logical_id: str) -> dict:
    """Bulk Import Item Definitions request carrying a deployment plan (documented shape).

    Only the parts this script can know: URL, plan reference, required scopes. The item
    definition parts of the body are what fabric-cicd would publish and are not built here.
    """
    if not _GUID.match(logical_id or ""):
        raise ValueError(f"deployment plan logical ID is not a GUID: '{logical_id}'")
    return {
        "method": "POST",
        "url": f"{FABRIC_API}/workspaces/{workspace_id}/items/bulkImportDefinitions?beta=true",
        "options": {
            "allowPairingByName": False,
            "deploymentPlan": {"logicalId": logical_id, "referenceType": "ByLogicalId"},
        },
        "scopes": list(DEPLOYMENT_PLAN_SCOPES),
    }


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


def items_for_domain(repository_directory: str, domain: str) -> list:
    """Names of the PBIP item folders belonging to `domain`, sorted.

    The link is read from each report's ``definition.pbir``
    (``datasetReference.byPath.path`` → ``../<Domain>.SemanticModel``) plus the domain's
    own ``<Domain>.SemanticModel`` folder. Deriving it from the *binding* rather than from
    a ``COM-``/``FIN-`` name prefix keeps this working when reports are renamed and needs
    no prefix table to maintain.

    Returns [] when the domain has no items here — the caller must treat that as an error,
    not as "nothing to do".
    """
    root = Path(repository_directory)
    if not root.is_dir():
        return []

    model_folder = f"{domain}.SemanticModel"
    kept = set()

    if (root / model_folder).is_dir():
        kept.add(model_folder)

    for pbir in root.glob("*.Report/definition.pbir"):
        try:
            ref = json.loads(pbir.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        by_path = (ref.get("datasetReference") or {}).get("byPath") or {}
        target = str(by_path.get("path", "")).replace("\\", "/").rstrip("/")
        if target.rsplit("/", 1)[-1] == model_folder:
            kept.add(pbir.parent.name)

    return sorted(kept)


def stage_domain_subset(repository_directory: str, domain: str, kept: list) -> str:
    """Copy `kept` item folders into a temp dir and return it.

    fabric-cicd publishes whatever lives under ``repository_directory``; there is no
    per-item allowlist. Staging a subset is therefore the only way to scope a publish to
    one domain without touching the source tree.
    """
    staging = Path(tempfile.mkdtemp(prefix=f"fabric_release_{domain}_"))
    for name in kept:
        shutil.copytree(Path(repository_directory) / name, staging / name)
    return str(staging)


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
    for attempt in range(max_retries + 1):
        try:
            misc.print_info(f"  {misc.BULLET} Publishing items from {repository_directory}...", end="")
            publish_all_items(target_workspace)
            misc.print_success(f" {misc.CHECKMARK}")
            break
        except Exception as e:
            is_transient = retry_logic is not None and retry_logic.is_transient_failure(e, str(e))
            if attempt < max_retries and is_transient:
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
                is_transient = retry_logic is not None and retry_logic.is_transient_failure(e, str(e))
                if attempt < max_retries and is_transient:
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
        type=_parse_bool,
        help="Whether to unpublish orphan items: true|false (default: true)"
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

    # Geheimnis nur ueber die Umgebung (CLIENT_SECRET / AZURE_CLIENT_SECRET); das
    # Argument ist nur noch deklariert, um einen alten Aufruf laut abzulehnen.
    parser.add_argument(
        "--client_secret",
        required=False,
        default=None,
        help=argparse.SUPPRESS
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

    # The three flags below exist because orchestrator/deploy.ps1 passes them. They used
    # to be silently unknown here, so every real (non-dry-run) deploy died with argparse
    # exit 2 before a single item was published.
    parser.add_argument(
        "--workspace_id",
        required=False,
        default=None,
        help="Target workspace ID; skips the per-layer name lookup (deploy.ps1 has already "
             "resolved or created the workspace). Only valid with a single --layers entry."
    )

    parser.add_argument(
        "--domain_filter",
        required=False,
        default=None,
        help="Publish only the items of one domain (e.g. Commercial). Resolved from each "
             "report's definition.pbir dataset reference, not from a name prefix. Implies "
             "--no-unpublish, because orphan cleanup would delete the other domains."
    )

    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Resolve and report what would be published without calling Fabric"
    )

    parser.add_argument(
        "--deployment_plan_logical_id",
        required=False,
        default=None,
        help="Deployment plan (preview) logical ID from the plan's .platform file. Off by "
             "default. Dry run only: prints the Bulk Import request with options.deploymentPlan. "
             "fabric-cicd does not support deployment plans, so a live release with this flag "
             "is refused."
    )

    args = parser.parse_args()

    # deploy.ps1 exports SP credentials as AZURE_* (what azure-identity expects); accept
    # both spellings so the two sides cannot drift apart again.
    args.tenant_id = args.tenant_id or os.environ.get('AZURE_TENANT_ID')
    args.client_id = args.client_id or os.environ.get('AZURE_CLIENT_ID')
    args.client_secret = fabcli.secret_from_environment(
        args.client_secret, "--client_secret", "CLIENT_SECRET", "AZURE_CLIENT_SECRET")

    # A dry run with a known workspace ID needs no Fabric call at all — it only resolves
    # directories — so it must stay runnable without credentials (that is what makes it
    # usable as a CI check).
    offline_dry_run = args.dry_run and bool(args.workspace_id)

    if args.deployment_plan_logical_id:
        if not _GUID.match(args.deployment_plan_logical_id):
            misc.print_error("--deployment_plan_logical_id must be a GUID (the plan's logicalId)")
            sys.exit(1)
        if not args.dry_run:
            misc.print_error("--deployment_plan_logical_id: fabric-cicd does not support "
                             "deployment plans (Learn, deployment-plan-automation); this script "
                             "only prints the Bulk Import request in --dry_run. Release without "
                             "a plan, or attach the plan via Update From Git / Deploy Stage Content.")
            sys.exit(1)

    # Validate required arguments
    if not offline_dry_run and (not args.tenant_id or not args.client_id or not args.client_secret):
        misc.print_error("Error: tenant_id, client_id, and client_secret are required")
        misc.print_info("Set tenant/client ID as arguments or environment variables, the secret "
                        "only as environment variable "
                        "(TENANT_ID/CLIENT_ID/CLIENT_SECRET or AZURE_TENANT_ID/AZURE_CLIENT_ID/AZURE_CLIENT_SECRET)")
        sys.exit(1)

    if args.workspace_id and len([layer for layer in args.layers.split(",") if layer.strip()]) > 1:
        misc.print_error("--workspace_id targets one workspace but --layers names several; "
                         "pass a single layer or drop --workspace_id")
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

    token_credential = None
    if offline_dry_run:
        misc.print_info("Offline dry run (--dry_run with --workspace_id): skipping Fabric auth")
    else:
        # Authenticate with Fabric CLI (for workspace lookup)
        misc.print_header("Authenticating with Fabric")
        fabcli.run_command("config set encryption_fallback_enabled true")
        # Geheimnis ueber die Umgebung der fab-Aufrufe, nie als `-p` in argv.
        if not fabcli.login_service_principal(args.tenant_id, args.client_id, args.client_secret):
            misc.print_error("Authentication failed: fab auth status meldet keine Anmeldung")
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

        # An explicit --workspace_id wins: the caller already resolved/created it.
        if args.workspace_id:
            workspace_id = args.workspace_id
        else:
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

        # Scope the publish to one domain, if asked
        unpublish_orphans = args.unpublish_items
        staged_dir = None
        if args.domain_filter:
            kept = items_for_domain(repository_directory, args.domain_filter)
            if not kept:
                misc.print_error(
                    f"--domain_filter '{args.domain_filter}': no items found under "
                    f"{repository_directory} (expected '{args.domain_filter}.SemanticModel' "
                    f"and/or reports bound to it)"
                )
                fail_count += 1
                continue
            staged_dir = stage_domain_subset(repository_directory, args.domain_filter, kept)
            repository_directory = staged_dir
            # Orphan cleanup compares the workspace against the *staged* subset, so with a
            # filter it would unpublish every other domain. Never allowed to combine.
            if unpublish_orphans:
                misc.print_warning(
                    f"--domain_filter set: orphan unpublish disabled (it would delete the "
                    f"items of every other domain in '{workspace_name}')"
                )
                unpublish_orphans = False
            misc.print_info(f"  {misc.BULLET} {args.domain_filter}: {len(kept)} item(s) — "
                            f"{', '.join(kept)}")

        if args.dry_run:
            misc.print_info(
                f"  [DRY-RUN] would publish {item_type_list} from {repository_directory} "
                f"to '{workspace_name}' ({workspace_id}); "
                f"unpublish_orphans={unpublish_orphans}"
            )
            if args.deployment_plan_logical_id:
                plan_request = deployment_plan_request(workspace_id, args.deployment_plan_logical_id)
                misc.print_info(f"  [DRY-RUN] deployment plan request: {json.dumps(plan_request)}")
            if staged_dir:
                shutil.rmtree(staged_dir, ignore_errors=True)
            success_count += 1
            continue

        # Release to workspace
        success = release_to_workspace(
            workspace_name=workspace_name,
            workspace_id=workspace_id,
            repository_directory=repository_directory,
            item_types=item_type_list,
            environment=args.environment,
            token_credential=token_credential,
            unpublish_orphans=unpublish_orphans
        )

        if staged_dir:
            shutil.rmtree(staged_dir, ignore_errors=True)

        if success:
            success_count += 1
        else:
            fail_count += 1

    # Summary
    misc.print_header("Release Summary")
    misc.print_info(f"Successfully deployed to {success_count} workspace(s)")
    if report_gen:
        workspace_details = []
        for layer_name, layer_def in layers.items():
            if layer_name.upper() not in layers_to_deploy or not isinstance(layer_def, dict):
                continue
            workspace_name = misc.format_workspace_name(
                solution_name_template, layer_name, environment_name
            )
            workspace_id = get_workspace_id(workspace_name)
            if workspace_id:
                workspace_details.append({"name": workspace_name, "id": workspace_id})
        html_path, json_path = report_gen.write_report(
            args.environment,
            fail_count == 0,
            preflight_results=[],
            workspace_details=workspace_details,
            errors_warnings=[f"Failed to deploy to {fail_count} workspace(s)"] if fail_count > 0 else [],
            rollback_snapshot_path=release_snapshot_path,
        )
        if html_path:
            misc.print_info(f"Deployment report: {html_path}")

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
