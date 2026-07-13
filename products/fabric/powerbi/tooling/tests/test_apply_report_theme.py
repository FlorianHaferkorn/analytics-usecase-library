"""Regression test for the PBIR CustomTheme naming convention, verified against the
official pbir-cli validator (`powerbi-report-author validate`) over the dist and
mirrored in the Meridian dist: a RegisteredResources/CustomTheme item must carry the
theme's `.json` filename in BOTH `name` and `path`, matching
`themeCollection.customTheme.name` and the theme file's internal `name` — all four
identical. (This is unlike the SharedResources/BaseTheme item, whose `name` is the bare
id.) A bare-stem CustomTheme name is flagged PBIR_THEME_NAME_MISSING_JSON_EXT; a name
that mismatches the referenced file is flagged PBIR_THEME_FILE_NAME_MISMATCH.
"""
from products.fabric.powerbi.tooling.apply_report_theme import _ensure_resource_packages


def test_registered_custom_theme_item_name_matches_json_filename():
    data: dict = {}
    _ensure_resource_packages(data, base_theme="CY25SU10", custom_theme_filename="Aurora_Theme.json")

    shared = next(p for p in data["resourcePackages"] if p["type"] == "SharedResources")
    registered = next(p for p in data["resourcePackages"] if p["type"] == "RegisteredResources")
    base_item = shared["items"][0]
    custom_item = next(i for i in registered["items"] if i["type"] == "CustomTheme")

    # SharedResources/BaseTheme item: name is the bare id, path has the extension.
    assert base_item["name"] == "CY25SU10"
    assert base_item["path"] == "BaseThemes/CY25SU10.json"

    # RegisteredResources/CustomTheme item: name == path == the .json filename.
    assert custom_item["name"] == "Aurora_Theme.json"
    assert custom_item["path"] == "Aurora_Theme.json"


def test_reapplying_theme_replaces_the_existing_entry_not_duplicates_it():
    data: dict = {}
    _ensure_resource_packages(data, base_theme="CY25SU10", custom_theme_filename="Aurora_Theme.json")
    _ensure_resource_packages(data, base_theme="CY25SU10", custom_theme_filename="Aurora_Theme.json")

    registered = next(p for p in data["resourcePackages"] if p["type"] == "RegisteredResources")
    custom_items = [i for i in registered["items"] if i["type"] == "CustomTheme"]
    assert len(custom_items) == 1


def test_reapplying_over_a_pre_fix_buggy_entry_replaces_it_by_path_not_name():
    """Migration case: a report.json written by the OLD buggy code has `name` == the
    bare stem (no .json). Re-running must replace that stale entry — identified by its
    stable `path` — rather than leaving it behind alongside a second, now-correct entry."""
    data = {
        "resourcePackages": [
            {
                "name": "RegisteredResources",
                "type": "RegisteredResources",
                "items": [
                    {"name": "Aurora_Theme", "path": "Aurora_Theme.json", "type": "CustomTheme"},
                ],
            }
        ]
    }
    _ensure_resource_packages(data, base_theme="CY25SU10", custom_theme_filename="Aurora_Theme.json")

    registered = next(p for p in data["resourcePackages"] if p["type"] == "RegisteredResources")
    custom_items = [i for i in registered["items"] if i["type"] == "CustomTheme"]
    assert len(custom_items) == 1
    assert custom_items[0]["name"] == "Aurora_Theme.json"
