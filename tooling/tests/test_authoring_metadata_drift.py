"""Drift guard for the authoring-metadata snapshot (ADR 0001).

The generator's queryState role table (``visual_validator.VISUAL_TYPE_ROLES``) is
sourced from the vendored snapshot for every non-policy visual type. These tests
fail if a future snapshot refresh changes the official roles out from under our
table, or if the snapshot-sourced table stops matching the pure-Python fallback.
"""

from __future__ import annotations

import pytest

from tooling.report_quality import authoring_metadata as am

# Visual types where the snapshot is authoritative (no local-policy override).
# clusteredColumnChart / pivotTable / card / multiRowCard / stacked* / funnelChart
# are intentionally excluded -- see visual_validator._LOCAL_ROLE_POLICY.
_EXPECTED_OFFICIAL_ROLES = {
    "lineChart": {"Category", "Y"},
    "areaChart": {"Category", "Y"},
    "waterfallChart": {"Category", "Y"},
    "clusteredBarChart": {"Category", "Y"},
    "hundredPercentStackedBarChart": {"Category", "Y"},
    "hundredPercentStackedColumnChart": {"Category", "Y"},
    "donutChart": {"Category", "Y"},
    "pieChart": {"Category", "Y"},
    "scatterChart": {"X", "Y"},
    "tableEx": {"Values"},
    "cardVisual": {"Data"},
    "slicer": {"Values"},
}


def test_vendored_snapshot_available() -> None:
    assert am.is_available() is True


@pytest.mark.parametrize("visual_type,expected", sorted(_EXPECTED_OFFICIAL_ROLES.items()))
def test_official_required_roles_unchanged(visual_type: str, expected: set) -> None:
    assert set(am.required_roles(visual_type)) == expected, (
        f"Official requiredRoles for {visual_type} changed. Re-run "
        "refresh_authoring_metadata.py and review visual_validator._LOCAL_ROLE_POLICY."
    )


def test_generator_role_table_is_behaviour_preserving() -> None:
    """Snapshot-sourced table must equal the pure-Python fallback (no output drift)."""
    from products.fabric.powerbi.tooling.page_scaffold_generator import visual_validator as vv

    assert vv._authoring_metadata is not None and vv._authoring_metadata.is_available()
    assert vv.VISUAL_TYPE_ROLES == vv._FALLBACK_ROLES
