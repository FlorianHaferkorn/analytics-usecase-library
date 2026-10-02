"""Feature x region in the capacity recommendation (FABCON W5.1, Meridian D-618).

Grounding: learn.microsoft.com/fabric/admin/region-availability, read 2026-10-01 via the
mirrored ``stack_capabilities``. Literal regions are asserted on purpose: the table changed
between 29.09. and 01.10.2026, and a test that only checks the mechanism would not notice
the next change in either direction.
"""
from __future__ import annotations

from tooling.superversion.capacity import recommend, region_features


def _bp(region: str | None = None, ontology: bool = False) -> dict:
    platform = {"sizing": {"region": region} if region else {}}
    bp: dict = {"platform": platform}
    if ontology:
        bp["ai_grounding"] = {"ontology": {"enabled": True}}
    return bp


def test_fabric_apps_are_available_in_germany_west_central_since_29_09_evening():
    assert region_features(_bp("Germany West Central"), {"fabric_apps"})["findings"] == []


def test_fabric_apps_missing_in_north_europe_names_an_eu_alternative():
    f = region_features(_bp("North Europe"), {"fabric_apps"})["findings"]
    assert [x["verdict"] for x in f] == ["fehlt"]
    assert "germanywestcentral" in f[0]["detail"] and "2026-10-01" in f[0]["detail"]


def test_ontology_is_read_from_the_ir_and_west_europe_is_fine_again():
    assert region_features(_bp("West Europe", ontology=True))["findings"] == []
    f = region_features(_bp("South Central US", ontology=True))["findings"]
    assert f and f[0]["verdict"] == "fehlt"


def test_no_region_is_a_warning_not_a_pass():
    f = region_features(_bp(None, ontology=True))["findings"]
    assert f and f[0]["verdict"] == "unbekannt"


def test_recommend_carries_the_findings_only_when_there_are_some():
    assert "region_features" not in recommend(_bp("Germany West Central", ontology=True))
    out = recommend(_bp("North Europe"), features={"fabric_apps"})
    assert out["region_features"]["data_as_of"] == "2026-10-01"
