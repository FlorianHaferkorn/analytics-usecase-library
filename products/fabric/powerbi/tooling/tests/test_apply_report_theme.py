"""Regression test for the THEME_FILE_NAME_MISMATCH bug (surfaced by the
official pbir-cli validator, `pbir validate --qa`): resourcePackages'
RegisteredResources/CustomTheme item must carry the theme's LOGICAL name (no
`.json`) in `name`, matching `themeCollection.customTheme.name` — exactly how
the SharedResources/BaseTheme item pairs a bare `name` with an extensioned
`path`. `_ensure_resource_packages` previously used the full filename for
both `name` and `path` of the CustomTheme item, which is what pbir-cli flags.
"""
from products.fabric.powerbi.tooling.apply_report_theme import _ensure_resource_packages


def test_registered_custom_theme_item_name_has_no_json_extension():
    data: dict = {}
    _ensure_resource_packages(data, base_theme="CY25SU10", custom_theme_filename="Aurora_Theme.json")

    shared = next(p for p in data["resourcePackages"] if p["type"] == "SharedResources")
    registered = next(p for p in data["resourcePackages"] if p["type"] == "RegisteredResources")
    base_item = shared["items"][0]
    custom_item = next(i for i in registered["items"] if i["type"] == "CustomTheme")

    # SharedResources/BaseTheme item: name has no extension, path does — this
    # is the known-good pattern (pbir-cli never flags it).
    assert base_item["name"] == "CY25SU10"
    assert base_item["path"] == "BaseThemes/CY25SU10.json"

    # RegisteredResources/CustomTheme item must follow the SAME pattern.
    assert custom_item["name"] == "Aurora_Theme"
    assert custom_item["path"] == "Aurora_Theme.json"


def test_reapplying_theme_replaces_the_existing_entry_not_duplicates_it():
    data: dict = {}
    _ensure_resource_packages(data, base_theme="CY25SU10", custom_theme_filename="Aurora_Theme.json")
    _ensure_resource_packages(data, base_theme="CY25SU10", custom_theme_filename="Aurora_Theme.json")

    registered = next(p for p in data["resourcePackages"] if p["type"] == "RegisteredResources")
    custom_items = [i for i in registered["items"] if i["type"] == "CustomTheme"]
    assert len(custom_items) == 1


def test_reapplying_over_a_pre_fix_buggy_entry_replaces_it_by_path_not_name():
    """Migration case: a report.json written by the OLD buggy code has
    `name` == the filename (e.g. from a prior run before this fix). Re-running
    must replace that stale entry — identified by its stable `path` — rather
    than leaving it behind alongside a second, now-correct entry."""
    data = {
        "resourcePackages": [
            {
                "name": "RegisteredResources",
                "type": "RegisteredResources",
                "items": [
                    {"name": "Aurora_Theme.json", "path": "Aurora_Theme.json", "type": "CustomTheme"},
                ],
            }
        ]
    }
    _ensure_resource_packages(data, base_theme="CY25SU10", custom_theme_filename="Aurora_Theme.json")

    registered = next(p for p in data["resourcePackages"] if p["type"] == "RegisteredResources")
    custom_items = [i for i in registered["items"] if i["type"] == "CustomTheme"]
    assert len(custom_items) == 1
    assert custom_items[0]["name"] == "Aurora_Theme"
