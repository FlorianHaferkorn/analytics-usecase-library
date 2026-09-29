#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fabric Rollback Script

Executes rollback from a snapshot file (delete created workspaces/connections for setup;
for release, instructs redeploy from Git).

Usage:
    python fabric_rollback.py --snapshot path/to/snapshot.json [--dry-run]
    python fabric_rollback.py --environment dev --latest  # use latest snapshot for env
"""
import os
import sys
import io
import argparse
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent))

import modules.misc_functions as misc
import modules.rollback_manager as rollback
import modules.fabric_cli_functions as fabcli


def get_latest_snapshot(environment: str) -> str:
    """Return path to latest snapshot file for environment."""
    snap_dir = rollback.get_snapshots_dir() / environment
    if not snap_dir.is_dir():
        return ""
    files = sorted(snap_dir.glob("*.json"), key=os.path.getmtime, reverse=True)
    return str(files[0]) if files else ""


def main():
    parser = argparse.ArgumentParser(
        description="Rollback Fabric deployment from a snapshot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--snapshot",
        required=False,
        help="Path to snapshot JSON file",
    )
    parser.add_argument(
        "--environment",
        required=False,
        choices=["dev", "tst", "prd"],
        help="Environment (used with --latest)",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Use latest snapshot for --environment",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate rollback without making changes",
    )
    parser.add_argument(
        "--tenant_id",
        default=os.environ.get("TENANT_ID"),
        help="Azure AD tenant ID (for release rollback if needed)",
    )
    parser.add_argument(
        "--client_id",
        default=os.environ.get("CLIENT_ID"),
        help="Service principal client ID",
    )
    # Geheimnis nur ueber CLIENT_SECRET; das Argument lehnt einen alten Aufruf ab.
    parser.add_argument(
        "--client_secret",
        default=None,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--repo_path",
        default="./solution",
        help="Repository path (for release rollback hint)",
    )
    args = parser.parse_args()
    args.client_secret = fabcli.secret_from_environment(
        args.client_secret, "--client_secret", "CLIENT_SECRET")

    snapshot_path = args.snapshot
    if args.latest and args.environment:
        snapshot_path = get_latest_snapshot(args.environment)
        if not snapshot_path:
            misc.print_error(f"No snapshots found for environment: {args.environment}")
            sys.exit(1)
        misc.print_info(f"Using latest snapshot: {snapshot_path}")
    if not snapshot_path or not os.path.isfile(snapshot_path):
        misc.print_error("Provide --snapshot <path> or --environment and --latest")
        sys.exit(1)

    # Auth required for setup rollback (delete workspace/connection)
    token_credential = None
    if not args.dry_run:
        if args.tenant_id and args.client_id and args.client_secret:
            fabcli.run_command("config set encryption_fallback_enabled true")
            if not fabcli.login_service_principal(args.tenant_id, args.client_id, args.client_secret):
                misc.print_error("Authentication failed: fab auth status meldet keine Anmeldung")
                sys.exit(1)

    misc.print_header("Rollback")
    if args.dry_run:
        misc.print_info("DRY-RUN: no changes will be made", bold=True)
    success, errors = rollback.execute_rollback(
        snapshot_path,
        token_credential=token_credential,
        repository_directory=args.repo_path,
        dry_run=args.dry_run,
    )
    if success:
        misc.print_success("Rollback completed successfully.")
    else:
        for e in errors:
            misc.print_error(e)
        misc.print_error("Rollback completed with errors.")
        sys.exit(1)


if __name__ == "__main__":
    main()
