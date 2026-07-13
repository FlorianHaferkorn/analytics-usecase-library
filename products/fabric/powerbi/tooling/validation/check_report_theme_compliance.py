#!/usr/bin/env python3
"""
check_report_theme_compliance.py

Audits PBIP reports for theme wiring and theme-first formatting hygiene.

Blocking failures:
- report.json missing themeCollection / resourcePackages wiring
- referenced base/custom theme files missing
- resourcePackages entries inconsistent with themeCollection

Non-blocking warnings:
- hardcoded hex colors in visual.json files
- visual-level formatting override usage via objects / visualContainerObjects
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[5]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from products.fabric.powerbi.tooling.schema_registry import REPORT_SCHEMA
from products.fabric.powerbi.tooling.theme_registration import (
    custom_theme_collection_name,
    find_registered_custom_theme_item,
)
HEX_COLOR_RE = re.compile(r"#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?")

STYLE_OBJECT_PROPERTIES: dict[str, set[str]] = {
    "background": {"show", "color", "transparency"},
    "border": {"show", "color", "radius"},
    "dropShadow": {"show", "color", "blur", "angle", "distance", "opacity"},
    "title": {"fontColor", "alignment", "textSize", "fontFamily"},
    "header": {"textSize", "fontColor", "backgroundColor", "outlineColor"},
    "items": {"textSize", "fontColor", "backgroundColor", "outlineColor"},
    "legend": {"fontColor", "textSize", "titleText"},
    "labels": {"color", "fontSize", "fontFamily"},
    "dataLabels": {"color", "fontSize", "fontFamily"},
    "categoryLabels": {"color", "fontSize", "fontFamily"},
    "valueAxis": {"labelColor", "titleColor", "fontSize", "fontFamily"},
    "categoryAxis": {"labelColor", "titleColor", "fontSize", "fontFamily"},
    "grid": {"outlineColor", "gridHorizontalColor", "gridVerticalColor"},
    "cards": {"labelColor", "calloutColor", "fontSize", "fontFamily", "backgroundColor"},
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_strings(value):
    if isinstance(value, dict):
        for nested in value.values():
            yield from iter_strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from iter_strings(nested)
    elif isinstance(value, str):
        yield value


def collect_hex_colors(payload: dict) -> Counter[str]:
    colors: Counter[str] = Counter()
    for string_value in iter_strings(payload):
        for match in HEX_COLOR_RE.findall(string_value):
            colors[match.upper()] += 1
    return colors


def iter_theme_override_paths(visual_root: dict) -> list[str]:
    object_root = visual_root.get("objects")
    if not isinstance(object_root, dict):
        return []

    flagged_paths: list[str] = []
    for object_name, object_instances in object_root.items():
        if not isinstance(object_instances, list):
            continue
        style_properties = STYLE_OBJECT_PROPERTIES.get(object_name, set())
        if not style_properties:
            continue
        for object_instance in object_instances:
            if not isinstance(object_instance, dict):
                continue
            properties = object_instance.get("properties")
            if not isinstance(properties, dict):
                continue
            for property_name in properties:
                if property_name in style_properties:
                    flagged_paths.append(f"{object_name}.{property_name}")
    return flagged_paths


def get_package_item(package: dict, item_type: str, item_name: str) -> dict | None:
    for item in package.get("items", []):
        if item.get("type") == item_type and item.get("name") == item_name:
            return item
    return None


def find_package(report_json: dict, package_type: str) -> dict | None:
    for package in report_json.get("resourcePackages", []):
        if package.get("type") == package_type:
            return package
    return None


def audit_report(report_dir: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    report_json_path = report_dir / "definition" / "report.json"
    if not report_json_path.exists():
        errors.append(f"{report_dir.name}: definition/report.json missing")
        return errors, warnings

    try:
        report_json = load_json(report_json_path)
    except json.JSONDecodeError as exc:
        errors.append(f"{report_dir.name}: invalid report.json - {exc}")
        return errors, warnings

    schema = report_json.get("$schema")
    if schema != REPORT_SCHEMA:
        errors.append(f"{report_dir.name}: report.json schema must be {REPORT_SCHEMA}")

    theme_collection = report_json.get("themeCollection") or {}
    base_theme = theme_collection.get("baseTheme") or {}
    custom_theme = theme_collection.get("customTheme") or {}

    if base_theme.get("type") != "SharedResources" or not base_theme.get("name"):
        errors.append(f"{report_dir.name}: themeCollection.baseTheme must reference SharedResources with a valid name")
    if custom_theme.get("type") != "RegisteredResources" or not custom_theme.get("name"):
        errors.append(f"{report_dir.name}: themeCollection.customTheme must reference RegisteredResources with a valid name")

    shared_package = find_package(report_json, "SharedResources")
    registered_package = find_package(report_json, "RegisteredResources")
    if not shared_package:
        errors.append(f"{report_dir.name}: resourcePackages missing SharedResources entry")
    if not registered_package:
        errors.append(f"{report_dir.name}: resourcePackages missing RegisteredResources entry")

    if shared_package and base_theme.get("name"):
        base_item = get_package_item(shared_package, "BaseTheme", base_theme["name"])
        if not base_item:
            errors.append(f"{report_dir.name}: SharedResources package missing BaseTheme item for {base_theme['name']}")
        else:
            expected_path = report_dir / "StaticResources" / "SharedResources" / base_item.get("path", "")
            if not expected_path.exists():
                errors.append(f"{report_dir.name}: referenced base theme file missing: {expected_path.relative_to(report_dir)}")

    if registered_package and custom_theme.get("name"):
        custom_logical_name = custom_theme["name"]
        # PBIR CustomTheme convention (verified against the official pbir-cli 0.1.1 and
        # mirrored in the Meridian dist): customTheme.name, the RegisteredResources item
        # name + path, and the theme file's internal `name` are ALL the same .json
        # filename. Unlike the SharedResources BaseTheme (bare id + path), a CustomTheme
        # name without the extension is flagged PBIR_THEME_NAME_MISSING_JSON_EXT; a name
        # that mismatches the referenced file is flagged PBIR_THEME_FILE_NAME_MISMATCH.
        if not custom_logical_name.endswith(".json"):
            errors.append(
                f"{report_dir.name}: themeCollection.customTheme.name must carry the .json "
                f"extension and match the RegisteredResources item, not '{custom_logical_name}'"
            )

        custom_item = find_registered_custom_theme_item(registered_package, custom_logical_name)
        if not custom_item:
            errors.append(
                f"{report_dir.name}: RegisteredResources package missing CustomTheme item for "
                f"{custom_logical_name}"
            )
        else:
            expected_path = report_dir / "StaticResources" / "RegisteredResources" / custom_item.get("path", "")
            if not expected_path.exists():
                errors.append(f"{report_dir.name}: referenced custom theme file missing: {expected_path.relative_to(report_dir)}")
            else:
                try:
                    theme_payload = load_json(expected_path)
                except json.JSONDecodeError as exc:
                    errors.append(
                        f"{report_dir.name}: invalid custom theme JSON at "
                        f"{expected_path.relative_to(report_dir)} - {exc}"
                    )
                else:
                    # All four references must equal the .json filename (== customTheme.name).
                    expected_name = custom_logical_name
                    if theme_payload.get("name") != expected_name:
                        errors.append(
                            f"{report_dir.name}: custom theme internal name "
                            f"'{theme_payload.get('name')}' must match themeCollection.customTheme.name "
                            f"'{expected_name}' (PBIR_THEME_FILE_NAME_MISMATCH otherwise)"
                        )
                    item_name = custom_item.get("name", "")
                    if item_name != expected_name:
                        errors.append(
                            f"{report_dir.name}: resourcePackages CustomTheme item name "
                            f"'{item_name}' must equal themeCollection.customTheme.name "
                            f"'{expected_name}' (all four references share the same .json filename; "
                            f"the official pbir-cli flags a mismatch as THEME_FILE_NAME_MISMATCH)"
                        )

    visual_paths = sorted(report_dir.glob("definition/pages/**/visual.json"))
    visuals_with_theme_objects = 0
    visuals_with_container_objects = 0
    hardcoded_color_hits: Counter[str] = Counter()
    visuals_with_hardcoded_colors: list[str] = []
    theme_object_examples: list[str] = []

    for visual_path in visual_paths:
        try:
            visual_json = load_json(visual_path)
        except json.JSONDecodeError as exc:
            errors.append(f"{report_dir.name}: invalid visual.json at {visual_path.relative_to(report_dir)} - {exc}")
            continue

        visual_root = visual_json.get("visual") or {}
        theme_override_paths = iter_theme_override_paths(visual_root)
        if theme_override_paths:
            visuals_with_theme_objects += 1
            preview = ", ".join(sorted(set(theme_override_paths))[:3])
            theme_object_examples.append(f"{visual_path.parent.name} ({preview})")
        if "visualContainerObjects" in visual_root:
            visuals_with_container_objects += 1

        colors = collect_hex_colors(visual_json)
        if colors:
            hardcoded_color_hits.update(colors)
            visuals_with_hardcoded_colors.append(str(visual_path.relative_to(report_dir)))

    if visuals_with_theme_objects > 0:
        warnings.append(
            f"{report_dir.name}: {visuals_with_theme_objects} visual(s) use style-relevant visual.objects overrides; review whether formatting should come from theme defaults"
        )
        warnings.append(
            f"{report_dir.name}: example style override visual(s): {', '.join(theme_object_examples[:3])}"
        )
    if visuals_with_container_objects > 0:
        warnings.append(
            f"{report_dir.name}: {visuals_with_container_objects} visual(s) use visual.visualContainerObjects overrides; review for stale container formatting"
        )
    if hardcoded_color_hits:
        top_colors = ", ".join(f"{color} x{count}" for color, count in hardcoded_color_hits.most_common(5))
        warnings.append(
            f"{report_dir.name}: hardcoded visual colors detected ({top_colors}); prefer theme tokens or theme inheritance"
        )
        preview = ", ".join(visuals_with_hardcoded_colors[:3])
        warnings.append(f"{report_dir.name}: example visual(s) with hardcoded colors: {preview}")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit PBIP reports for theme compliance")
    parser.add_argument("--dist-root", default="products/fabric/powerbi/dist", help="Path to dist folder containing .Report directories")
    parser.add_argument("--strict-warnings", action="store_true", help="Treat warnings as failures")
    args = parser.parse_args()

    dist_root = Path(args.dist_root)
    if not dist_root.exists():
        print(f"Dist root not found: {dist_root}", file=sys.stderr)
        return 1

    report_dirs = sorted(dist_root.glob("*.Report"))
    if not report_dirs:
        print(f"No .Report directories found in {dist_root}", file=sys.stderr)
        return 1

    total_errors: list[str] = []
    total_warnings: list[str] = []

    print(f"Checking {len(report_dirs)} report(s) for theme compliance...\n")
    for report_dir in report_dirs:
        errors, warnings = audit_report(report_dir)
        total_errors.extend(errors)
        total_warnings.extend(warnings)
        if not errors and not warnings:
            print(f"  OK {report_dir.name}: theme wiring and compliance baseline valid")
            continue
        for error in errors:
            print(f"  FAIL {error}")
        for warning in warnings:
            print(f"  WARN {warning}")

    print(f"\nTheme compliance summary: {len(total_errors)} error(s), {len(total_warnings)} warning(s)")
    if total_errors:
        return 1
    if total_warnings and args.strict_warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())