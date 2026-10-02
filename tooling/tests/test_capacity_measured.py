"""W5.3: Groesse aus der gemessenen 30-Sekunden-Spitze, Reservierung plus PAYG (4-Tage-Regel).

Quelle: Learn ``enterprise/capacity-planning-manage-capacity-growth-governance`` (gelesen
01.10.2026): "if added capacity is needed more than four days a week, RI can offer better value";
ein Timepoint hat 30 Sekunden, das Budget einer SKU ist CU x 30.
"""
from __future__ import annotations

import pytest

from tooling.superversion.capacity import (
    peak_floor,
    recommend,
    surge_procurement,
)


def test_peak_fits_eighty_percent_of_the_budget():
    # F64 = 1920 CU-s je Timepoint, 80 % = 1536.
    assert peak_floor(1536)["sku"] == "F64"
    assert peak_floor(1537)["sku"] == "F128"


def test_peak_beyond_every_sku_says_split():
    r = peak_floor(10**9)
    assert r["sku"] is None and "split" in r["reason"]


@pytest.mark.parametrize("bad", [0, -5, None])
def test_peak_must_be_a_measurement(bad):
    with pytest.raises(ValueError):
        peak_floor(bad)


@pytest.mark.parametrize("days, model", [(1, "reservation+pay-as-you-go"),
                                         (4, "reservation+pay-as-you-go"),
                                         (4.5, "reservation+reservation"),
                                         (7, "reservation+reservation")])
def test_four_day_rule(days, model):
    assert surge_procurement("F64", days)["model"] == model


def test_surge_rejects_unknown_sku_and_bad_days():
    with pytest.raises(ValueError):
        surge_procurement("F3", 1)
    with pytest.raises(ValueError):
        surge_procurement("F64", 8)


def _bp():
    return {"platform": {"stack": "fabric", "sizing": {"largest_model_gb": 2}},
            "mesh": {"domains": []}}


def test_measured_peak_raises_the_floor_and_is_named():
    ohne = recommend(_bp())
    mit = recommend(_bp(), measured={"peak_cu_seconds": 3000})
    assert ohne["recommended_floor"] == "F2"
    assert mit["recommended_floor"] == "F128"
    assert any("peak 3000 CU-s" in r for r in mit["floor_reasons"])


def test_surge_lands_in_procurement_without_changing_the_base_model():
    out = recommend(_bp(), measured={"surge": {"extra_sku": "F64", "days_per_week": 1}})
    assert out["procurement"]["surge"]["model"] == "reservation+pay-as-you-go"
    assert "model" in out["procurement"]
