#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply a custom theme to a PBIP report: copy theme to RegisteredResources and update definition/report.json.

Base theme stays fixed (e.g. CY25SU10); custom theme is the overlay. Targets PBIP definition format only
(definition/report.json). Optional: validate theme JSON against pinned schema before copying.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Repo root (apply_report_theme.py lives in implementations/microsoft_fabric_powerbi/tools/)
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply a custom theme to a PBIP report (definition format). Copies theme to RegisteredResources and updates report.json.",
    )
    parser.add_argument("report", type=Path, help="Path to PBIP report root (folder containing definition/report.json)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--theme-path", type=Path, help="Path to existing theme JSON file")
    group.add_argument(
        "--theme-name",
        type=str,
        help="Theme name (e.g. 'Aurora Group__NeutralAccent__Light__#118DFF'); file is looked up under theme_generator/themes/",
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
    args = parser.parse_args()

    theme_path: Optional[Path] = None
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
