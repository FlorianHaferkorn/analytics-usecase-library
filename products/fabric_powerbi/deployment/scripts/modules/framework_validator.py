"""
Framework Validator Module

Executes Stage 1 and Fabric checks via PowerShell.
Requires execution from repository root (or REPO_ROOT set) and PowerShell on the agent.
"""
import os
import re
import subprocess
from pathlib import Path
from typing import Tuple, Optional, Dict, Any


def get_repo_root() -> Optional[Path]:
    """
    Get repository root directory.
    Uses REPO_ROOT env var if set, otherwise infers from this file's location
    (deployment/scripts/modules -> go up to repo root).
    """
    repo_root = os.environ.get("REPO_ROOT")
    if repo_root and os.path.isdir(repo_root):
        return Path(repo_root)

    # From products/fabric_powerbi/deployment/scripts/modules/framework_validator.py
    # -> products/fabric_powerbi/deployment/scripts/modules
    # -> ... -> repo root (has _internal, framework)
    this_file = Path(__file__).resolve()
    candidate = this_file.parent
    for _ in range(8):
        if candidate is None or not candidate.parent:
            break
        if (candidate / "_internal" / "tools").is_dir() and (candidate / "framework").is_dir():
            return candidate
        candidate = candidate.parent
    return None


def run_powershell_script(
    script_path: Path,
    args: Optional[list] = None,
    cwd: Optional[Path] = None,
    timeout_seconds: int = 600,
) -> Tuple[bool, str, int]:
    """
    Run a PowerShell script and return success, combined output, and exit code.

    Args:
        script_path: Full path to .ps1 script
        args: Optional list of arguments
        cwd: Working directory (default: script's parent)
        timeout_seconds: Timeout for the process

    Returns:
        (success, combined_stdout_stderr, exit_code)
    """
    args = args or []
    cwd = cwd or script_path.parent
    pwsh_cmd = ["pwsh", "-NoProfile", "-NonInteractive", "-File", str(script_path)] + args
    try:
        result = subprocess.run(
            pwsh_cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        combined = (result.stdout or "") + "\n" + (result.stderr or "")
        return (result.returncode == 0, combined.strip(), result.returncode)
    except subprocess.TimeoutExpired:
        return (False, "Script timed out", -1)
    except FileNotFoundError:
        return (False, "PowerShell (pwsh) not found. Install PowerShell Core or set PATH.", -1)
    except Exception as e:
        return (False, str(e), -1)


def run_stage1_checks(repo_root: Optional[Path] = None) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Run Stage 1 CI checks (run_stage1_checks.ps1).

    Args:
        repo_root: Repository root. If None, uses get_repo_root().

    Returns:
        (success, message, details)
    """
    root = repo_root or get_repo_root()
    if not root:
        return (
            False,
            "Repository root not found. Set REPO_ROOT or run from repo root.",
            {"repo_root": None},
        )

    script_path = root / "_internal" / "tools" / "run_stage1_checks.ps1"
    if not script_path.is_file():
        return (
            False,
            f"Stage 1 script not found: {script_path}",
            {"script_path": str(script_path)},
        )

    # Stage 1 script expects to be run with -Root; it also uses Get-Location so we run from repo root
    success, output, exit_code = run_powershell_script(
        script_path,
        args=["-Root", str(root)],
        cwd=root,
    )

    details = {
        "repo_root": str(root),
        "script_path": str(script_path),
        "exit_code": exit_code,
        "output_snippet": output[-2000:] if len(output) > 2000 else output,
    }

    if success:
        return (True, "Stage 1 checks passed.", details)
    # Parse for FAIL line to get failing check
    fail_match = re.search(r"FAIL\s+(\S+)\s*\((\d+)\)", output)
    if fail_match:
        failing_check = fail_match.group(1)
        return (False, f"Stage 1 check failed: {failing_check}", details)
    return (False, "Stage 1 checks failed.", details)


def run_fabric_checks(
    repo_root: Optional[Path] = None,
    aurora_tables_dir: str = "",
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Run Fabric checks (run_fabric_checks.ps1).

    Args:
        repo_root: Repository root. If None, uses get_repo_root().
        aurora_tables_dir: Optional path to Aurora tables dir for showcase validation.

    Returns:
        (success, message, details)
    """
    root = repo_root or get_repo_root()
    if not root:
        return (
            False,
            "Repository root not found. Set REPO_ROOT or run from repo root.",
            {"repo_root": None},
        )

    script_path = root / "implementations" / "microsoft_fabric_powerbi" / "tools" / "run_fabric_checks.ps1"
    if not script_path.is_file():
        return (
            False,
            f"Fabric checks script not found: {script_path}",
            {"script_path": str(script_path)},
        )

    args = []
    if aurora_tables_dir:
        args.extend(["-AuroraTablesDir", aurora_tables_dir])

    success, output, exit_code = run_powershell_script(
        script_path,
        args=args,
        cwd=root,
    )

    details = {
        "repo_root": str(root),
        "script_path": str(script_path),
        "exit_code": exit_code,
        "output_snippet": output[-2000:] if len(output) > 2000 else output,
    }

    if success:
        return (True, "Fabric checks passed.", details)
    return (False, "Fabric checks failed.", details)


def run_framework_validation(
    include_stage1: bool = True,
    include_fabric: bool = True,
    repo_root: Optional[Path] = None,
    dry_run: bool = False,
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Run Stage 1 and/or Fabric validation.

    Args:
        include_stage1: Run Stage 1 checks
        include_fabric: Run Fabric checks
        repo_root: Repository root (optional)
        dry_run: If True, skip actual execution and return simulated success

    Returns:
        (success, message, details)
    """
    if dry_run:
        return (
            True,
            "Framework validation skipped (dry-run).",
            {"dry_run": True, "stage1": "skipped", "fabric": "skipped"},
        )

    root = repo_root or get_repo_root()
    details = {"repo_root": str(root) if root else None, "stage1": None, "fabric": None}

    if include_stage1:
        ok, msg, d1 = run_stage1_checks(root)
        details["stage1"] = {"success": ok, "message": msg, **d1}
        if not ok:
            return (False, msg, details)

    if include_fabric:
        ok, msg, d2 = run_fabric_checks(root)
        details["fabric"] = {"success": ok, "message": msg, **d2}
        if not ok:
            return (False, msg, details)

    return (True, "All framework validations passed.", details)
