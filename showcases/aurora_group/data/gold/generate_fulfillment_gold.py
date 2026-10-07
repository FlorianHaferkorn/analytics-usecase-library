"""Schreibt auf dem vorhandenen Aurora-Gold nur `fact_fulfillment` neu (07.10.2026).

Logik in `_fulfillment.py` (OTIF = On-Time AND In-Full, OrgKey = DC der Lane, Guardrail-Volumen,
On-Time-Abfall in zwei Lanes). Liest `dim_lane`, `dim_org`, `dim_product` aus dem Gold, schreibt
`facts/fact_fulfillment` (Delta, Fiscal-Year-Partitionen) und raeumt danach per VACUUM
(Aufbewahrung 0) die ersetzten Dateien weg, damit der Arbeitsbaum nur aktive Dateien traegt.

Warum ein eigener Schritt statt `generate_supply_chain_gold.py`: der Gesamtlauf schreibt auch
`fact_inventory` neu, und das weicht vom Release ab (gemessen 07.10.2026: `Average/Obsolete
Inventory *` in 0 % der 18.000 Zeilen gleich; dim_lane, fact_cogs, fact_stockout,
fact_forecast dagegen inhaltsgleich). Dieser Schritt aendert nur die eine Tabelle.

Run from repo root (braucht `deltalake==1.6.2`):
  python3 showcases/aurora_group/data/gold/generate_fulfillment_gold.py
"""
from __future__ import annotations

import sys
from pathlib import Path

GOLD = Path(__file__).resolve().parent
if str(GOLD) not in sys.path:
    sys.path.insert(0, str(GOLD))

import _fulfillment as ff  # noqa: E402
from _generator_utils import get_fact_date_range, write_fact_delta  # noqa: E402

RANDOM_SEED = 12345  # wie generate_supply_chain_gold.py


def main(gold: Path = GOLD) -> int:
    dims = gold / "dimensions"
    df = ff.erzeuge(ff.lies_tabelle(dims / "dim_lane"), ff.lies_tabelle(dims / "dim_org"),
                    ff.lies_tabelle(dims / "dim_product"), get_fact_date_range(), RANDOM_SEED)
    ziel = gold / "facts" / "fact_fulfillment"
    fmt = write_fact_delta(ziel, df, partition_by=["Fiscal Year"])
    if fmt == "Delta":
        from deltalake import DeltaTable
        DeltaTable(str(ziel)).vacuum(retention_hours=0, enforce_retention_duration=False, dry_run=False)
    s = ff.slots(df)
    stufen = s["stufe"].value_counts().to_dict()
    print(f"Written fact_fulfillment ({len(df):,} records) [{fmt}]; "
          f"On-Time {df['On-Time Flag'].mean():.4f}, In-Full {df['In-Full Flag'].mean():.4f}, "
          f"OTIF {df['OTIF Flag'].mean():.4f}; Lane/DC/Woche >= {ff.GUARDRAIL}: "
          f"{int((s['Sendungen'] >= ff.GUARDRAIL).sum())} von {len(s)}; "
          f"S-R2.2 (persistiert) L1 {stufen.get('L1', 0)}, L2 {stufen.get('L2', 0)}, L3 {stufen.get('L3', 0)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
