"""
MockSAPService — deterministic in-memory SAP OData responses for CI.

Returns RecordBatches that match the Aurora target schemas in schema_map.py.
Row counts are small (20 rows per entity) so tests stay fast.

Usage:
    from tooling.connectors.sap.mock_service import MockSAPService
    service = MockSAPService(seed=42)
    batches = list(service.fetch("fact_sales"))
"""

from __future__ import annotations

import random
from typing import Iterator, List

import pyarrow as pa

from tooling.connectors.sap.schema_map import (
    FACT_GL_JOURNAL_SCHEMA,
    FACT_INVENTORY_SCHEMA,
    FACT_SALES_SCHEMA,
)

_CUSTOMERS = ["C-1001", "C-1002", "C-1003", "C-1004", "C-1005"]
_PRODUCTS  = ["P-MAT-001", "P-MAT-002", "P-MAT-003", "P-MAT-004"]
_ORGS      = ["1000", "2000", "3000"]
_PLANTS    = ["PL01", "PL02"]
_ACCOUNTS  = ["400000", "500000", "600000", "700000"]
_DOC_TYPES = ["RV", "RE", "DR", "KR"]


class MockSAPService:
    """
    Generates deterministic fake SAP data for all three Aurora fact entities.

    Parameters
    ----------
    seed:
        Random seed for reproducibility.  CI always passes seed=42.
    rows_per_entity:
        Number of rows to generate per entity (default 20).
    fiscal_year:
        Fiscal year to stamp on all generated rows (default 2025).
    """

    def __init__(
        self,
        seed: int = 42,
        rows_per_entity: int = 20,
        fiscal_year: int = 2025,
    ) -> None:
        self._rng = random.Random(seed)
        self._rows = rows_per_entity
        self._fy = fiscal_year

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch(self, entity: str) -> Iterator[pa.RecordBatch]:
        """Yield one RecordBatch for the requested Aurora entity."""
        generators = {
            "fact_sales":      self._fact_sales,
            "fact_gl_journal": self._fact_gl_journal,
            "fact_inventory":  self._fact_inventory,
        }
        if entity not in generators:
            raise KeyError(f"MockSAPService: unknown entity '{entity}'. "
                           f"Valid entities: {sorted(generators)}")
        yield generators[entity]()

    # ------------------------------------------------------------------
    # Private generators
    # ------------------------------------------------------------------

    def _fact_sales(self) -> pa.RecordBatch:
        n = self._rows
        rng = self._rng
        line_ids      = [f"5000{i:04d}-{i:04d}" for i in range(n)]
        date_keys     = [20250101 + rng.randint(0, 364) for _ in range(n)]
        orgs          = [rng.choice(_ORGS) for _ in range(n)]
        products      = [rng.choice(_PRODUCTS) for _ in range(n)]
        customers     = [rng.choice(_CUSTOMERS) for _ in range(n)]
        promos        = [rng.choice(["PR-001", "PR-002", None]) for _ in range(n)]
        quantities    = [round(rng.uniform(1, 100), 2) for _ in range(n)]
        list_price    = [round(rng.uniform(50, 500), 2) for _ in range(n)]
        discount_pct  = [rng.uniform(0, 0.15) for _ in range(n)]
        net_sales     = [round(l * (1 - d), 2) for l, d in zip(list_price, discount_pct)]
        discounts     = [round(l - n_, 2) for l, n_ in zip(list_price, net_sales)]
        cogs          = [round(n_ * rng.uniform(0.4, 0.7), 2) for n_ in net_sales]
        fiscal_months = [rng.randint(1, 12) for _ in range(n)]

        return pa.record_batch(
            [
                pa.array(line_ids,                           type=pa.string()),
                pa.array(date_keys,                          type=pa.int32()),
                pa.array(orgs,                               type=pa.string()),
                pa.array(products,                           type=pa.string()),
                pa.array(customers,                          type=pa.string()),
                pa.array(promos,                             type=pa.string()),
                pa.array(quantities,                         type=pa.float64()),
                pa.array(list_price,                         type=pa.float64()),
                pa.array([round(l * 0.95, 2) for l in list_price], type=pa.float64()),
                pa.array(discounts,                          type=pa.float64()),
                pa.array(net_sales,                          type=pa.float64()),
                pa.array(cogs,                               type=pa.float64()),
                pa.array([self._fy] * n,                     type=pa.int32()),
                pa.array(fiscal_months,                      type=pa.int32()),
            ],
            schema=FACT_SALES_SCHEMA,
        )

    def _fact_gl_journal(self) -> pa.RecordBatch:
        n = self._rows
        rng = self._rng
        line_ids     = [f"1000{i:04d}-{i:03d}" for i in range(n)]
        accounts     = [rng.choice(_ACCOUNTS) for _ in range(n)]
        cost_centers = [f"CC{rng.randint(100, 199):03d}" for _ in range(n)]
        profit_ctrs  = [f"PC{rng.randint(100, 199):03d}" for _ in range(n)]
        date_keys    = [20250101 + rng.randint(0, 364) for _ in range(n)]
        amounts      = [round(rng.uniform(-50000, 100000), 2) for _ in range(n)]
        currencies   = ["EUR"] * n
        dc_flags     = [rng.choice(["S", "H"]) for _ in range(n)]
        periods      = [rng.randint(1, 12) for _ in range(n)]
        doc_types    = [rng.choice(_DOC_TYPES) for _ in range(n)]

        return pa.record_batch(
            [
                pa.array(line_ids,     type=pa.string()),
                pa.array(accounts,     type=pa.string()),
                pa.array(cost_centers, type=pa.string()),
                pa.array(profit_ctrs,  type=pa.string()),
                pa.array(date_keys,    type=pa.int32()),
                pa.array(amounts,      type=pa.float64()),
                pa.array(currencies,   type=pa.string()),
                pa.array(dc_flags,     type=pa.string()),
                pa.array([self._fy] * n, type=pa.int32()),
                pa.array(periods,      type=pa.int32()),
                pa.array(doc_types,    type=pa.string()),
            ],
            schema=FACT_GL_JOURNAL_SCHEMA,
        )

    def _fact_inventory(self) -> pa.RecordBatch:
        n = self._rows
        rng = self._rng
        materials  = [rng.choice(_PRODUCTS) for _ in range(n)]
        plants     = [rng.choice(_PLANTS) for _ in range(n)]
        stor_locs  = [f"SL{rng.randint(1, 4):02d}" for _ in range(n)]
        date_keys  = [20250101 + rng.randint(0, 364) for _ in range(n)]
        avg_units  = [round(rng.uniform(0, 10000), 0) for _ in range(n)]
        avg_amt    = [round(u * rng.uniform(10, 200), 2) for u in avg_units]
        obs_pct    = [rng.uniform(0, 0.05) for _ in range(n)]
        obs_units  = [round(u * p, 0) for u, p in zip(avg_units, obs_pct)]
        obs_amt    = [round(a * p, 2) for a, p in zip(avg_amt, obs_pct)]
        months     = [rng.randint(1, 12) for _ in range(n)]

        return pa.record_batch(
            [
                pa.array(materials,  type=pa.string()),
                pa.array(plants,     type=pa.string()),
                pa.array(stor_locs,  type=pa.string()),
                pa.array(date_keys,  type=pa.int32()),
                pa.array(avg_amt,    type=pa.float64()),
                pa.array(obs_amt,    type=pa.float64()),
                pa.array(avg_units,  type=pa.float64()),
                pa.array(obs_units,  type=pa.float64()),
                pa.array([self._fy] * n, type=pa.int32()),
                pa.array(months,     type=pa.int32()),
            ],
            schema=FACT_INVENTORY_SCHEMA,
        )
