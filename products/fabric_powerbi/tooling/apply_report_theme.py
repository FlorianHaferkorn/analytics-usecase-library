#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply a custom theme to a PBIP report: copy theme to RegisteredResources and update definition/report.json.

Base theme stays fixed (e.g. CY25SU10); custom theme is the overlay. Targets PBIP definition format only
(definition/report.json). Optional: validate theme JSON against pinned schema before copying.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Repo root (apply_report_theme.py lives in products/fabric_powerbi/tooling/)
REPO_ROOT = Path(__file__).resolve().parents[3]
THEME_GENERATOR_THEMES = REPO_ROOT / "implementations" / "microsoft_fabric_powerbi" / "tools" / "theme_generator" / "themes"
THEME_GENERATOR_CONFIG = REPO_ROOT / "implementations" / "microsoft_fabric_powerbi" / "tools" / "theme_generator" / "themes.config.json"
SHOWCASES_DIR = REPO_ROOT / "showcases"
DEFAULT_BASE_THEME = "CY25SU10"
REPORT_VERSION_AT_IMPORT = {"visual": "2.1.0", "report": "3.0.0", "page": "2.3.0"}


def _safe_filename(name: str) -> str:
    """Return a safe filename stem (no path, no .json)."""
    stem = Path(name).stem if name else "theme"
    return re.sub(r"[^\w\-]", "_", stem) or "theme"


def _find_theme_in_generator(theme_name: str) -> Optional[Path]:
    """Locate theme JSON under theme_generator/themes by name (with or without .json)."""
    stem = Path(theme_name).stem
    if not THEME_GENERATOR_THEMES.exists():
        return None
    for p in THEME_GENERATOR_THEMES.rglob("*.json"):
        if p.stem == stem:
            return p
    return None


def resolve_theme_path(theme_name: str) -> Optional[Path]:
    """
    Resolve a theme name to its file path under theme_generator/themes/.
    For use by scaffold generator or other callers that need the path before calling apply_theme.
    """
    return _find_theme_in_generator(theme_name)


def get_default_theme_name(report_path: Optional[Path] = None) -> Optional[str]:
    """
    Get default theme name using configuration hierarchy:
    1. Showcase default (if report_path is under showcases/<name>/)
    2. Framework default (from themes.config.json)
    3. None if neither exists
    
    Args:
        report_path: Optional path to report. If provided and under showcases/, checks for showcase config.
    
    Returns:
        Theme name string or None if no default configured.
    """
    # Try showcase default first
    if report_path:
        report_path = Path(report_path).resolve()
        try:
            # Check if report_path is under showcases/<name>/
            parts = report_path.parts
            if "showcases" in parts:
                idx = parts.index("showcases")
                if idx + 1 < len(parts):
                    showcase_name = parts[idx + 1]
                    showcase_config = SHOWCASES_DIR / showcase_name / "theme_config.json"
                    if showcase_config.exists():
                        try:
                            config_data = json.loads(showcase_config.read_text(encoding="utf-8"))
                            theme_name = config_data.get("defaultThemeName")
                            if theme_name:
                                return theme_name
                        except Exception:
                            pass  # Fall through to framework default
        except Exception:
            pass  # Fall through to framework default
    
    # Try framework default
    if THEME_GENERATOR_CONFIG.exists():
        try:
            config_data = json.loads(THEME_GENERATOR_CONFIG.read_text(encoding="utf-8"))
            theme_name = config_data.get("defaultThemeName")
            if theme_name:
                return theme_name
        except Exception:
            pass
    
    return None


def _run_theme_generator(color: str, concept: str, mode: str, brand: str, secondary: Optional[str] = None) -> None:
    """Run theme generator agent_cli with given args."""
    agent = REPO_ROOT / "implementations" / "microsoft_fabric_powerbi" / "tools" / "theme_generator" / "tools" / "theme-agent" / "agent_cli.py"
    if not agent.exists():
        raise FileNotFoundError(f"Theme agent not found: {agent}")
    cmd = [
        sys.executable,
        str(agent),
        "--input", f"#all --color {color} --concept {concept} --mode {mode} --brand {brand!r}",
    ]
    if secondary:
        cmd[-1] += f" --secondary {secondary}"
    subprocess.run(cmd, check=True, cwd=str(agent.parent))


def _validate_theme_against_schema(theme_path: Path) -> bool:
    """Validate theme JSON against pinned schema if available. Return True if valid or skip."""
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return True
    # Resolve theme_generator theme-agent for fetch_latest_theme_schema
    agent_dir = REPO_ROOT / "implementations" / "microsoft_fabric_powerbi" / "tools" / "theme_generator" / "tools" / "theme-agent"
    if agent_dir not in sys.path:
        sys.path.insert(0, str(agent_dir))
    try:
        from fetch_latest_theme_schema import get_schema_path
        schema_path = get_schema_path()
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        payload = json.loads(theme_path.read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(payload)
        return True
    except Exception:
        return False


def _ensure_report_structure(report_path: Path) -> Path:
    """Ensure definition/report.json and StaticResources/RegisteredResources exist. Return definition path."""
    report_path = Path(report_path).resolve()
    definition = report_path / "definition"
    report_json = definition / "report.json"
    if not report_json.exists():
        raise FileNotFoundError(
            f"PBIP definition not found: {report_json}. This script targets reports with definition/report.json only."
        )
    registered = report_path / "StaticResources" / "RegisteredResources"
    registered.mkdir(parents=True, exist_ok=True)
    return definition


def _read_report_json(definition_path: Path) -> Dict[str, Any]:
    with open(definition_path / "report.json", encoding="utf-8") as f:
        return json.load(f)


def _write_report_json(definition_path: Path, data: Dict[str, Any]) -> None:
    with open(definition_path / "report.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _ensure_resource_packages(data: Dict[str, Any], base_theme: str, custom_theme_filename: str) -> None:
    """Ensure resourcePackages has SharedResources (base) and RegisteredResources (custom). No duplicates."""
    packages: List[Dict[str, Any]] = data.get("resourcePackages") or []
    shared = next((p for p in packages if p.get("type") == "SharedResources"), None)
    registered = next((p for p in packages if p.get("type") == "RegisteredResources"), None)

    if shared is None:
        shared = {
            "name": "SharedResources",
            "type": "SharedResources",
            "items": [],
        }
        packages.append(shared)
    items = shared.get("items") or []
    if not any(it.get("name") == base_theme for it in items):
        items.append({
            "name": base_theme,
            "path": f"BaseThemes/{base_theme}.json",
            "type": "BaseTheme",
        })
    shared["items"] = items

    if registered is None:
        registered = {
            "name": "RegisteredResources",
            "type": "RegisteredResources",
            "items": [],
        }
        packages.append(registered)
    reg_items = registered.get("items") or []
    # Replace existing custom theme entry with same name
    reg_items = [it for it in reg_items if it.get("name") != custom_theme_filename]
    reg_items.append({
        "name": custom_theme_filename,
        "path": custom_theme_filename,
        "type": "CustomTheme",
    })
    registered["items"] = reg_items
    data["resourcePackages"] = packages


def apply_theme(
    report_path: Path,
    theme_source_path: Path,
    custom_theme_name: Optional[str] = None,
    base_theme_name: str = DEFAULT_BASE_THEME,
    validate: bool = True,
) -> None:
    """
    Copy theme to report's RegisteredResources and update definition/report.json.
    
    Validates that base theme file exists before applying custom theme.
    """
    definition_path = _ensure_report_structure(report_path)
    
    # Validate base theme file exists
    base_theme_file = report_path / "StaticResources" / "SharedResources" / "BaseThemes" / f"{base_theme_name}.json"
    if not base_theme_file.exists():
        raise FileNotFoundError(
            f"Base theme file not found: {base_theme_file}. "
            f"Ensure base theme '{base_theme_name}' is present before applying custom theme."
        )
    
    theme_path = Path(theme_source_path).resolve()
    if not theme_path.is_file():
        raise FileNotFoundError(f"Theme file not found: {theme_path}")

    payload = json.loads(theme_path.read_text(encoding="utf-8"))
    if not isinstance(payload.get("name"), str) and "dataColors" not in payload and "colorPalette" not in payload:
        raise ValueError("File does not look like a Power BI theme JSON (missing name or dataColors/colorPalette).")

    if validate and not _validate_theme_against_schema(theme_path):
        raise ValueError("Theme failed validation against pinned report theme schema. Fix or run with --no-validate.")

    custom_stem = custom_theme_name if custom_theme_name else payload.get("name") or theme_path.stem
    custom_stem = _safe_filename(custom_stem)
    custom_filename = f"{custom_stem}.json"

    registered_dir = report_path / "StaticResources" / "RegisteredResources"
    dest = registered_dir / custom_filename
    shutil.copy2(theme_path, dest)

    data = _read_report_json(definition_path)
    if "themeCollection" not in data:
        data["themeCollection"] = {}
    tc = data["themeCollection"]
    tc["baseTheme"] = {
        "name": base_theme_name,
        "reportVersionAtImport": REPORT_VERSION_AT_IMPORT,
        "type": "SharedResources",
    }
    tc["customTheme"] = {
        "name": custom_filename,
        "reportVersionAtImport": REPORT_VERSION_AT_IMPORT,
        "type": "RegisteredResources",
    }
    _ensure_resource_packages(data, base_theme_name, custom_filename)
    _write_report_json(definition_path, data)
    print(f"Theme copied to {dest}", file=sys.stderr)
    print("report.json updated (baseTheme + customTheme + resourcePackages).", file=sys.stderr)


def _collect_report_paths_batch_showcase(showcase_name: str) -> List[Path]:
    """Return list of report paths under showcases/<showcase_name>/ (folders containing definition/report.json)."""
    base = SHOWCASES_DIR / showcase_name
    if not base.is_dir():
        return []
    report_paths: List[Path] = []
    for path in base.rglob("report.json"):
        if path.name == "report.json" and path.parent.name == "definition":
            report_root = path.parent.parent
            report_paths.append(report_root.resolve())
    return sorted(set(report_paths))


def _collect_report_paths_glob(glob_pattern: str) -> List[Path]:
    """Return list of report paths matching glob pattern (each must contain definition/report.json)."""
    resolved: List[Path] = []
    for p in glob.glob(glob_pattern):
        path = Path(p).resolve()
        if path.is_dir() and (path / "definition" / "report.json").exists():
            resolved.append(path)
    return sorted(set(resolved))


def _collect_report_paths_file(file_path: Path) -> List[Path]:
    """Read file with one report path per line; return list of existing report roots."""
    if not file_path.is_file():
        return []
    resolved: List[Path] = []
    for line in file_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        path = (REPO_ROOT / line).resolve() if not Path(line).is_absolute() else Path(line).resolve()
        if path.is_dir() and (path / "definition" / "report.json").exists():
            resolved.append(path)
    return resolved


def _run_batch(
    report_paths: List[Path],
    theme_path: Optional[Path],
    theme_name: Optional[str],
    base_theme_name: str,
    validate: bool,
    continue_on_error: bool,
) -> Tuple[int, int]:
    """
    Apply theme to each report. Returns (success_count, failure_count).
    If theme_path is None, theme_name must be set and we resolve it once (or use default per report).
    """
    success = 0
    failure = 0
    for report_path in report_paths:
        path_to_use: Optional[Path] = theme_path
        name_to_use: Optional[str] = theme_name
        if path_to_use is None and name_to_use is None:
            name_to_use = get_default_theme_name(report_path)
        if path_to_use is None and name_to_use:
            path_to_use = _find_theme_in_generator(name_to_use)
        if path_to_use is None:
            print(f"[FAIL] {report_path}: No theme specified and no default found.", file=sys.stderr)
            failure += 1
            if not continue_on_error:
                return success, failure
            continue
        try:
            apply_theme(
                report_path=report_path,
                theme_source_path=path_to_use,
                custom_theme_name=name_to_use,
                base_theme_name=base_theme_name,
                validate=validate,
            )
            success += 1
        except Exception as e:
            print(f"[FAIL] {report_path}: {e}", file=sys.stderr)
            failure += 1
            if not continue_on_error:
                return success, failure
    return success, failure


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply a custom theme to a PBIP report (definition format). Copies theme to RegisteredResources and updates report.json.",
    )
    parser.add_argument(
        "report",
        type=Path,
        nargs="?",
        default=None,
        help="Path to PBIP report root (folder containing definition/report.json). Omit when using batch mode.",
    )
    batch_group = parser.add_mutually_exclusive_group()
    batch_group.add_argument(
        "--batch-showcase",
        type=str,
        metavar="NAME",
        help="Apply theme to all reports under showcases/NAME/ (each folder with definition/report.json).",
    )
    batch_group.add_argument(
        "--batch",
        type=str,
        metavar="GLOB",
        help="Apply theme to all report paths matching GLOB (e.g. showcases/aurora_group/reports/*.Report).",
    )
    batch_group.add_argument(
        "--batch-file",
        type=Path,
        metavar="PATH",
        help="Text file with one report path per line (relative to repo root or absolute).",
    )
    theme_group = parser.add_mutually_exclusive_group()
    theme_group.add_argument("--theme-path", type=Path, help="Path to existing theme JSON file")
    theme_group.add_argument(
        "--theme-name",
        type=str,
        help="Theme name (e.g. 'Aurora Group__NeutralAccent__Light__#118DFF'); file is looked up under theme_generator/themes/",
    )
    theme_group.add_argument(
        "--use-default",
        action="store_true",
        help="Use default theme (showcase or framework). Only valid in batch mode or when report path is under a showcase.",
    )
    parser.add_argument(
        "--run-generator",
        action="store_true",
        help="Run theme generator before applying (use with --theme-name and generator args)",
    )
    parser.add_argument("--color", type=str, default="#118DFF", help="Primary color for generator (e.g. #118DFF)")
    parser.add_argument("--concept", type=str, default="Monochromatic")
    parser.add_argument("--mode", type=str, default="Light")
    parser.add_argument("--brand", type=str, default="Generic")
    parser.add_argument("--secondary", type=str, default=None)
    parser.add_argument("--custom-name", type=str, help="Custom theme filename stem in RegisteredResources (default: from theme)")
    parser.add_argument("--base-theme", type=str, default=DEFAULT_BASE_THEME, help=f"Base theme name (default: {DEFAULT_BASE_THEME})")
    parser.add_argument("--no-validate", action="store_true", help="Skip validation against pinned schema")
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="In batch mode, continue applying to remaining reports after a failure.",
    )
    args = parser.parse_args()

    # Batch mode
    if args.batch_showcase is not None:
        report_paths = _collect_report_paths_batch_showcase(args.batch_showcase)
        if not report_paths:
            print(f"No reports found under showcases/{args.batch_showcase}/", file=sys.stderr)
            return 1
    elif args.batch is not None:
        report_paths = _collect_report_paths_glob(args.batch)
        if not report_paths:
            print(f"No report folders matching '{args.batch}' (must contain definition/report.json).", file=sys.stderr)
            return 1
    elif args.batch_file is not None:
        report_paths = _collect_report_paths_file(args.batch_file)
        if not report_paths:
            print(f"No valid report paths in {args.batch_file}.", file=sys.stderr)
            return 1
    else:
        report_paths = []

    if report_paths:
        # Batch: resolve theme once if provided
        theme_path: Optional[Path] = None
        theme_name: Optional[str] = None
        if args.theme_path:
            theme_path = Path(args.theme_path).resolve()
        elif args.theme_name:
            if args.run_generator:
                _run_theme_generator(args.color, args.concept, args.mode, args.brand, args.secondary)
            theme_path = _find_theme_in_generator(args.theme_name)
            if theme_path:
                theme_name = args.theme_name
            else:
                print(f"Theme not found: {args.theme_name}.", file=sys.stderr)
                return 1
        elif not args.use_default:
            print("Batch mode requires --theme-name, --theme-path, or --use-default.", file=sys.stderr)
            return 1
        success, failure = _run_batch(
            report_paths=report_paths,
            theme_path=theme_path,
            theme_name=theme_name,
            base_theme_name=args.base_theme,
            validate=not args.no_validate,
            continue_on_error=args.continue_on_error,
        )
        print(f"Applied theme to {success} report(s). Failed: {failure}.", file=sys.stderr)
        return 0 if failure == 0 else 1

    # Single-report mode
    if args.report is None:
        parser.error("Either provide report path or use --batch-showcase, --batch, or --batch-file.")
    if args.use_default and not args.theme_path and not args.theme_name:
        theme_name = get_default_theme_name(args.report)
        if not theme_name:
            print("No default theme configured (showcase or framework). Use --theme-name or --theme-path.", file=sys.stderr)
            return 1
        theme_path = _find_theme_in_generator(theme_name)
        if not theme_path:
            print(f"Default theme '{theme_name}' not found under theme_generator/themes/.", file=sys.stderr)
            return 1
    else:
        if not args.theme_path and not args.theme_name:
            parser.error("Single-report mode requires --theme-name, --theme-path, or --use-default.")
        if args.theme_path:
            theme_path = Path(args.theme_path).resolve()
        else:
            if args.run_generator:
                _run_theme_generator(args.color, args.concept, args.mode, args.brand, args.secondary)
            theme_path = _find_theme_in_generator(args.theme_name)
            if not theme_path:
                print(
                    f"Theme not found: {args.theme_name}. Run from repo root and ensure theme exists under theme_generator/themes/ or use --theme-path.",
                    file=sys.stderr,
                )
                return 1

    try:
        apply_theme(
            report_path=args.report,
            theme_source_path=theme_path,
            custom_theme_name=args.custom_name,
            base_theme_name=args.base_theme,
            validate=not args.no_validate,
        )
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
