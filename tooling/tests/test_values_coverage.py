"""Tests for tooling/validation/check_values_coverage.py (Epic B2).

Covers the enumerable-column heuristic, the Commercial coverage split (safe fills
present, business-governed domains reported as a gap), determinism, and the
--strict gate.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "tooling" / "validation"))

from check_values_coverage import domain_coverage, is_enumerable, main
from tooling.generator_core.ai_description import ColumnDescription

_CONTRACTS = _REPO_ROOT / "core" / "data_contracts" / "domains"


# ---------------------------------------------------------------------------
# is_enumerable heuristic
# ---------------------------------------------------------------------------

def test_enumerable_classification():
    assert is_enumerable(ColumnDescription(name="Region", data_type="text", role="attribute"))
    assert is_enumerable(ColumnDescription(name="Segment", data_type="text", role="attribute"))
    # keys / foreign keys are not enumerable
    assert not is_enumerable(ColumnDescription(name="OrgKey", data_type="int", role="key"))
    assert not is_enumerable(ColumnDescription(name="CustomerKey", data_type="int", role="foreign_key"))
    # identifiers / labels (Name/Code suffix) are not enumerable
    assert not is_enumerable(ColumnDescription(name="ProductName", data_type="text", role="attribute"))
    assert not is_enumerable(ColumnDescription(name="OrgCode", data_type="text", role="attribute"))
    # documented high-cardinality / free-text columns are not enumerable
    assert not is_enumerable(ColumnDescription(name="Country", data_type="text", role="attribute"))
    assert not is_enumerable(ColumnDescription(name="Brand", data_type="text", role="attribute"))
    # non-text columns are not enumerable
    assert not is_enumerable(ColumnDescription(name="Year", data_type="int", role="attribute"))


# ---------------------------------------------------------------------------
# Commercial coverage (safe fills present; governed domains reported as gap)
# ---------------------------------------------------------------------------

def test_commercial_safe_fills_are_covered():
    cov = domain_coverage("Commercial", _CONTRACTS)
    for loc in ("dim_org.Region", "dim_org.Channel", "dim_date.Quarter",
                "dim_customer.Channel", "dim_customer.Region"):
        assert loc in cov.covered, f"{loc} should carry allowed_values"


def test_commercial_deferred_domains_reported_as_gap():
    cov = domain_coverage("Commercial", _CONTRACTS)
    # business-governed domains are reported, not invented
    assert set(cov.missing) == {
        "dim_product.Category",
        "dim_product.Subcategory",
        "dim_customer.Segment",
        "dim_promo.PromoType",
        "dim_promo.Mechanic",
    }
    assert cov.enumerable == 10 and len(cov.covered) == 5


def test_domain_coverage_is_deterministic():
    assert domain_coverage("Commercial", _CONTRACTS) == domain_coverage("Commercial", _CONTRACTS)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_report_mode_exits_zero():
    assert main(["--domain", "Commercial"]) == 0


def test_strict_mode_flags_the_gap():
    # the deferred domains are still missing, so --strict fails (the gate is honest)
    assert main(["--domain", "Commercial", "--strict"]) == 1
