#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup helper for configuring theme defaults (showcase-specific or framework-wide).

Usage:
    # Set showcase default
    python setup_theme_defaults.py --showcase aurora_group --theme "Aurora Group__NeutralAccent__Light__#118DFF"
    
    # Set framework default
    python setup_theme_defaults.py --framework --theme "Generic__Monochromatic__Light__#118DFF"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Repo root
REPO_ROOT = Path(__file__).resolve().parents[4]
THEME_GENERATOR_CONFIG = REPO_ROOT / "products" / "fabric" / "powerbi" / "tooling" / "theme_generator" / "themes.config.json"
SHOWCASES_DIR = REPO_ROOT / "showcases"


def set_showcase_default(showcase_name: str, theme_name: str) -> None:
    """Create or update showcase theme_config.json with defaultThemeName."""
    showcase_dir = SHOWCASES_DIR / showcase_name
    if not showcase_dir.exists():
        raise FileNotFoundError(f"Showcase directory not found: {showcase_dir}")
    
    config_file = showcase_dir / "theme_config.json"
    config_data = {}
    if config_file.exists():
        config_data = json.loads(config_file.read_text(encoding="utf-8"))
    
    config_data["defaultThemeName"] = theme_name
    
    config_file.write_text(json.dumps(config_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[OK] Showcase default theme set: {showcase_name} → {theme_name}")
    print(f"     Config file: {config_file}")


def set_framework_default(theme_name: str) -> None:
    """Update framework defaultThemeName in themes.config.json."""
    if not THEME_GENERATOR_CONFIG.exists():
        raise FileNotFoundError(f"Theme generator config not found: {THEME_GENERATOR_CONFIG}")
    
    config_data = json.loads(THEME_GENERATOR_CONFIG.read_text(encoding="utf-8"))
    config_data["defaultThemeName"] = theme_name
    
    THEME_GENERATOR_CONFIG.write_text(json.dumps(config_data, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[OK] Framework default theme set: {theme_name}")
    print(f"     Config file: {THEME_GENERATOR_CONFIG}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Configure theme defaults for showcases or framework-wide",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--showcase",
        type=str,
        help="Showcase name (e.g., 'aurora_group'). Creates/updates showcases/<name>/theme_config.json",
    )
    group.add_argument(
        "--framework",
        action="store_true",
        help="Set framework-wide default in themes.config.json",
    )
    parser.add_argument(
        "--theme",
        type=str,
        required=True,
        help="Theme name (e.g., 'Aurora Group__NeutralAccent__Light__#118DFF')",
    )
    
    args = parser.parse_args()
    
    try:
        if args.showcase:
            set_showcase_default(args.showcase, args.theme)
        else:
            set_framework_default(args.theme)
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
