"""
Rollback Manager Module

Creates pre-deployment snapshots and executes rollback (delete created resources).
Snapshots store IDs and names only; rollback = cleanup of created resources + optional redeploy from Git.
"""
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import modules.fabric_cli_functions as fabcli
import modules.misc_functions as misc


def get_snapshots_dir(deployment_root: Optional[Path] = None) -> Path:
    """Return path to deployment/snapshots directory."""
    if deployment_root is not None:
        return deployment_root / "snapshots"
    # From scripts/modules -> deployment root
    script_dir = Path(__file__).resolve().parent
    return script_dir.parent.parent / "snapshots"


def create_snapshot(
    environment: str,
    snapshot_type: str,
    created_workspaces: Optional[List[Dict[str, Any]]] = None,
    created_connections: Optional[List[Dict[str, Any]]] = None,
    items_by_workspace: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    deployment_root: Optional[Path] = None,
) -> Tuple[Optional[Path], Optional[str]]:
    """
    Create a rollback snapshot JSON file.

    Args:
        environment: Environment name (dev, tst, prd)
        snapshot_type: 'setup' or 'release'
        created_workspaces: List of {id, name} for workspaces created in this run
        created_connections: List of {id, name} for connections created in this run
        items_by_workspace: Optional dict workspace_id -> list of {id, name, type} items (for release)
        deployment_root: Optional deployment directory (parent of snapshots/)

    Returns:
        (path to saved snapshot file, deployment_id) or (None, None) on failure
    """
    created_workspaces = created_workspaces or []
    created_connections = created_connections or []
    items_by_workspace = items_by_workspace or {}

    deployment_id = str(uuid.uuid4())[:8]
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    snap_dir = get_snapshots_dir(deployment_root) / environment
    snap_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{timestamp}-{deployment_id}.json"
    filepath = snap_dir / filename

    payload = {
        "deployment_id": deployment_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "environment": environment,
        "snapshot_type": snapshot_type,
        "created_workspaces": [{"id": w.get("id"), "name": w.get("name")} for w in created_workspaces],
        "created_connections": [{"id": c.get("id"), "name": c.get("name")} for c in created_connections],
        "items_by_workspace": items_by_workspace,
    }

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return (filepath, deployment_id)
    except Exception as e:
        misc.print_error(f"Failed to write snapshot: {e}")
        return (None, None)


def load_snapshot(snapshot_path: str) -> Optional[Dict[str, Any]]:
    """Load and validate a snapshot JSON file."""
    if not os.path.isfile(snapshot_path):
        return None
    try:
        with open(snapshot_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "snapshot_type" not in data:
            return None
        return data
    except Exception:
        return None


def execute_rollback_setup(snapshot: Dict[str, Any], dry_run: bool = False) -> Tuple[bool, List[str]]:
    """
    Rollback setup: delete created workspaces and connections in reverse order.

    Returns:
        (success, list of error messages)
    """
    errors = []
    created_workspaces = snapshot.get("created_workspaces") or []
    created_connections = snapshot.get("created_connections") or []

    # Delete workspaces first (reverse order)
    for w in reversed(created_workspaces):
        wid = w.get("id")
        wname = w.get("name")
        if not wid:
            continue
        if dry_run:
            misc.print_info(f"  [DRY-RUN] Would delete workspace: {wname or wid}")
            continue
        if fabcli.delete_workspace(wid):
            misc.print_success(f"  Deleted workspace: {wname or wid}")
        else:
            errors.append(f"Failed to delete workspace: {wname or wid}")

    # Then connections (reverse order)
    for c in reversed(created_connections):
        cid = c.get("id")
        cname = c.get("name")
        if not cid:
            continue
        if dry_run:
            misc.print_info(f"  [DRY-RUN] Would delete connection: {cname or cid}")
            continue
        if fabcli.delete_connection(cid):
            misc.print_success(f"  Deleted connection: {cname or cid}")
        else:
            errors.append(f"Failed to delete connection: {cname or cid}")

    return (len(errors) == 0, errors)


def execute_rollback_release(
    snapshot: Dict[str, Any],
    token_credential: Any,
    repository_directory: str,
    dry_run: bool = False,
) -> Tuple[bool, List[str]]:
    """
    Rollback release: unpublish items that were deployed.
    Snapshot stores items_by_workspace; we rely on fabric-cicd unpublish or manual steps.
    This is best-effort: unpublish_all_orphan_items or revert via Git redeploy.

    Returns:
        (success, list of error messages)
    """
    errors = []
    if dry_run:
        misc.print_info("  [DRY-RUN] Release rollback would unpublish items or redeploy from Git.")
        return (True, [])

    # Without fabric-cicd we cannot unpublish by ID easily; document that user should redeploy from Git.
    try:
        from fabric_cicd import FabricWorkspace, unpublish_all_orphan_items
    except ImportError:
        errors.append("fabric-cicd not available; release rollback: redeploy previous version from Git.")
        return (False, errors)

    items_by_workspace = snapshot.get("items_by_workspace") or {}
    for workspace_id, items in items_by_workspace.items():
        # Reconstruct workspace and call unpublish; requires env and repo path
        # For simplicity we only report that rollback should be done via Git redeploy
        pass

    errors.append("Release rollback: redeploy previous version from Git (e.g. previous commit).")
    return (False, errors)


def execute_rollback(
    snapshot_path: str,
    token_credential: Any = None,
    repository_directory: str = "",
    dry_run: bool = False,
) -> Tuple[bool, List[str]]:
    """
    Load snapshot and execute rollback (setup or release).

    Returns:
        (success, list of error messages)
    """
    snapshot = load_snapshot(snapshot_path)
    if not snapshot:
        return (False, [f"Invalid or missing snapshot: {snapshot_path}"])

    stype = snapshot.get("snapshot_type", "")
    if stype == "setup":
        return execute_rollback_setup(snapshot, dry_run=dry_run)
    if stype == "release":
        return execute_rollback_release(
            snapshot,
            token_credential or None,
            repository_directory or "",
            dry_run=dry_run,
        )
    return (False, [f"Unknown snapshot_type: {stype}"])
