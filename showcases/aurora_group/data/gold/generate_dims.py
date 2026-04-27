"""
Dimension Enrichment Generator
================================

Enriches existing dim_org and dim_date Parquet files with all domain-specific
columns required by Operations, Finance, SupplyChain, and Experience TMDL models.

dim_org additions  (all derived deterministically from existing hierarchy):
  Region       – DACH / Benelux / Nordics / SouthernEurope / CEE
  Entity       – Finance: org display name for P&L entities
  Plant        – Operations: manufacturing/fulfilment facility name
  Line         – Operations: production line code (Line A / B / C)
  Shift        – Operations: shift name (Day / Afternoon / Night)
  Location     – SupplyChain: location display name (store or DC city)
  Channel      – SupplyChain: distribution channel
  Customer     – SupplyChain: primary customer segment label
  Queue        – Experience: support queue name
  Agent Group  – Experience: agent team designation
  IssueType    – Experience: primary issue category handled
  Severity     – Experience: default severity level

dim_date additions:
  CalendarYearMonth  – "YYYY-MM"  (e.g. "2020-01")
  MonthNumber        – int 1-12
  Week               – ISO week string "YYYY-Www" (e.g. "2020-W01")

Run from repo root:
  python3 showcases/aurora_group/data/gold/generate_dims.py
"""
from __future__ import annotations

import sys
import random
from pathlib import Path

import numpy as np
import pandas as pd

GOLD = Path(__file__).resolve().parent
if str(GOLD) not in sys.path:
    sys.path.insert(0, str(GOLD))

DIMS = GOLD / "dimensions"

RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

_DIM_PRIMARY_KEYS: dict[str, str] = {
    "dim_date": "DateKey",
    "dim_org":  "OrgKey",
}


def _load_dim(name: str) -> pd.DataFrame:
    """Load a dimension, deduplicating on primary key so stale delta-overwrite
    files (which leave multiple physical copies of the same rows on disk) are
    handled correctly."""
    dim_dir = DIMS / name
    # Try deltalake snapshot first (authoritative, no stale files)
    try:
        from deltalake import DeltaTable
        return DeltaTable(str(dim_dir)).to_pandas()
    except Exception:
        pass
    files = sorted(dim_dir.rglob("*.parquet"))
    if not files:
        raise FileNotFoundError(f"No parquet files found under {dim_dir}")
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    # Deduplicate on primary key if known (removes stale delta overwrite copies)
    pk = _DIM_PRIMARY_KEYS.get(name)
    if pk and pk in df.columns:
        df = df.drop_duplicates(subset=[pk]).reset_index(drop=True)
    return df


def _write_dim(name: str, df: pd.DataFrame) -> None:
    out_dir = DIMS / name
    out_dir.mkdir(parents=True, exist_ok=True)
    # Remove ALL existing parquet files (including stale delta overwrite copies)
    for f in out_dir.rglob("*.parquet"):
        f.unlink()
    df.to_parquet(out_dir / "part-00000.parquet", index=False)
    print(f"  Written {name} ({len(df):,} rows, {len(df.columns)} cols): {list(df.columns)}")


# ---------------------------------------------------------------------------
# dim_date enrichment
# ---------------------------------------------------------------------------

def enrich_dim_date() -> None:
    print("Enriching dim_date …")
    df = _load_dim("dim_date")

    dates = pd.to_datetime(df["Date"])

    df["CalendarYearMonth"] = dates.dt.strftime("%Y-%m")
    df["MonthNumber"] = dates.dt.month.astype("int64")
    # ISO week: YYYY-Www
    df["Week"] = dates.dt.strftime("%G-W%V")   # %G=ISO year, %V=ISO week

    _write_dim("dim_date", df)


# ---------------------------------------------------------------------------
# dim_org enrichment
# ---------------------------------------------------------------------------

# Org-level → region name lookup built from hierarchy
def _build_region_map(df: pd.DataFrame) -> dict[int, str]:
    parent_map = dict(zip(df["OrgKey"], df["ParentOrgKey"]))
    level_map  = dict(zip(df["OrgKey"], df["OrgLevel"]))
    name_map   = dict(zip(df["OrgKey"], df["OrgName"]))

    result: dict[int, str] = {}
    for key in df["OrgKey"]:
        visited: set[int] = set()
        k = key
        while k and k not in visited:
            visited.add(k)
            if level_map.get(k) == "Region":
                result[key] = name_map[k].replace("Region ", "")
                break
            k = parent_map.get(k)  # type: ignore[arg-type]
    return result


# City lookup: extract city from OrgCode patterns like "STORE-DE-003" → look up by country
_COUNTRY_CITIES: dict[str, list[str]] = {
    "DE": ["Munich", "Berlin", "Frankfurt", "Hamburg", "Stuttgart", "Cologne", "Düsseldorf", "Leipzig"],
    "AT": ["Vienna", "Graz", "Linz", "Salzburg", "Innsbruck"],
    "CH": ["Zurich", "Geneva", "Basel", "Bern", "Lausanne"],
    "NL": ["Amsterdam", "Rotterdam", "The Hague", "Utrecht", "Eindhoven", "Tilburg"],
    "BE": ["Brussels", "Antwerp", "Ghent", "Bruges", "Liège"],
    "LU": ["Luxembourg City", "Esch-sur-Alzette"],
    "SE": ["Stockholm", "Gothenburg", "Malmö", "Uppsala", "Västerås"],
    "NO": ["Oslo", "Bergen", "Stavanger", "Trondheim", "Drammen"],
    "DK": ["Copenhagen", "Aarhus", "Odense", "Aalborg"],
    "FI": ["Helsinki", "Espoo", "Tampere", "Vantaa", "Oulu"],
    "IT": ["Milan", "Rome", "Naples", "Turin", "Florence", "Bologna"],
    "ES": ["Madrid", "Barcelona", "Valencia", "Seville", "Bilbao", "Zaragoza"],
    "PT": ["Lisbon", "Porto", "Braga", "Coimbra", "Faro"],
    "GR": ["Athens", "Thessaloniki", "Patras", "Heraklion"],
    "PL": ["Warsaw", "Krakow", "Wroclaw", "Gdansk", "Poznań", "Łódź"],
    "CZ": ["Prague", "Brno", "Ostrava", "Plzeň"],
    "HU": ["Budapest", "Debrecen", "Miskolc", "Pécs"],
    "SK": ["Bratislava", "Košice", "Prešov"],
}

_LINES = ["Line A", "Line B", "Line C", "Line D"]
_SHIFTS = ["Day Shift", "Afternoon Shift", "Night Shift"]
_CHANNELS = ["Retail", "Online", "Wholesale", "Marketplace", "Outlet"]
_QUEUES = [
    "General Support", "Technical Support", "Billing & Payments",
    "Order Management", "Returns & Refunds", "VIP Support",
]
_AGENT_GROUPS = [
    "Tier 1 – General", "Tier 2 – Specialist", "Tier 3 – Expert",
    "Escalation Team", "Back-Office", "VIP Desk",
]
_ISSUE_TYPES = ["Billing", "Technical", "Delivery", "Order", "Product", "Account"]
_SEVERITIES  = ["Low", "Medium", "High", "Critical"]

# channel weights per region (stable, not random per row)
_REGION_CHANNEL_WEIGHTS: dict[str, list[float]] = {
    "DACH":           [0.45, 0.25, 0.15, 0.10, 0.05],
    "Benelux":        [0.40, 0.30, 0.15, 0.10, 0.05],
    "Nordics":        [0.35, 0.35, 0.15, 0.10, 0.05],
    "SouthernEurope": [0.50, 0.20, 0.15, 0.10, 0.05],
    "CEE":            [0.50, 0.15, 0.20, 0.10, 0.05],
}


def _city_for_org(org_key: int, country: str | None, seq_no: int) -> str:
    """Return a city name deterministically from country's city list."""
    if not country or country not in _COUNTRY_CITIES:
        return "Metropolis"
    cities = _COUNTRY_CITIES[country]
    return cities[seq_no % len(cities)]


def enrich_dim_org() -> None:
    print("Enriching dim_org …")
    df = _load_dim("dim_org").copy()

    region_map = _build_region_map(df)

    # Assign a sequential index per country so city names rotate nicely
    country_seq: dict[str, int] = {}

    regions: list[str | None] = []
    entities: list[str] = []
    plants: list[str | None] = []
    lines: list[str | None] = []
    shifts: list[str | None] = []
    locations: list[str | None] = []
    channels: list[str | None] = []
    customers: list[str | None] = []
    queues: list[str | None] = []
    agent_groups: list[str | None] = []
    issue_types: list[str | None] = []
    severities: list[str | None] = []

    for _, row in df.iterrows():
        org_key  = int(row["OrgKey"])
        org_type = row["OrgType"]
        org_name = str(row["OrgName"])
        country  = row.get("Country") if pd.notna(row.get("Country")) else None
        region   = region_map.get(org_key)

        # Country-based city sequence
        seq_key  = country or "XX"
        seq_no   = country_seq.get(seq_key, 0)
        country_seq[seq_key] = seq_no + 1

        city = _city_for_org(org_key, country, seq_no)

        # --- Region (all levels) ---
        regions.append(region)

        # --- Entity (Finance) ---
        # Group → company name; Region → region label; Country → country entity;
        # Store/DC → store/facility entity
        if org_type == "Group":
            entity = "Aurora Group SE"
        elif org_type == "Region":
            entity = f"Aurora {region} Region"
        elif org_type == "Country":
            entity = f"Aurora {country} Entity"
        else:
            entity = org_name
        entities.append(entity)

        # --- Plant / Line / Shift (Operations) ---
        if org_type in ("Store", "DC"):
            plant = f"Aurora {city} {'Store' if org_type == 'Store' else 'DC'}"
            line  = _LINES[org_key % len(_LINES)]
            shift = _SHIFTS[org_key % len(_SHIFTS)]
        elif org_type == "Country":
            plant = f"Aurora {country} Operations"
            line  = None
            shift = None
        else:
            plant = None
            line  = None
            shift = None
        plants.append(plant)
        lines.append(line)
        shifts.append(shift)

        # --- Location / Channel / Customer (SupplyChain) ---
        if org_type in ("Store", "DC"):
            location = f"{city} {'Store' if org_type == 'Store' else 'Distribution Center'}"
            cw = _REGION_CHANNEL_WEIGHTS.get(region or "", [0.2] * 5)
            rng_ch = np.random.RandomState(org_key * 7 + 3)
            channel = rng_ch.choice(_CHANNELS, p=cw)
            if org_type == "DC":
                customer = "Wholesale Partner"
            else:
                seg_options = ["B2C Retail", "Loyalty Member", "VIP Account", "B2B Account", "Online Shopper"]
                customer = seg_options[org_key % len(seg_options)]
        elif org_type == "Region":
            location = f"{region} Region"
            channel  = "Wholesale"
            customer = f"{region} Distributor"
        elif org_type == "Country":
            location = f"{country} Market"
            channel  = "Direct"
            customer = f"{country} National Account"
        else:
            location = None
            channel  = None
            customer = None
        locations.append(location)
        channels.append(channel)
        customers.append(customer)

        # --- Queue / Agent Group / IssueType / Severity (Experience) ---
        if org_type in ("Store", "DC", "Country", "Region"):
            queue       = _QUEUES[org_key % len(_QUEUES)]
            agent_group = _AGENT_GROUPS[org_key % len(_AGENT_GROUPS)]
            issue_type  = _ISSUE_TYPES[org_key % len(_ISSUE_TYPES)]
            severity    = _SEVERITIES[org_key % len(_SEVERITIES)]
        else:
            queue       = None
            agent_group = None
            issue_type  = None
            severity    = None
        queues.append(queue)
        agent_groups.append(agent_group)
        issue_types.append(issue_type)
        severities.append(severity)

    df["Region"]       = regions
    df["Entity"]       = entities
    df["Plant"]        = plants
    df["Line"]         = lines
    df["Shift"]        = shifts
    df["Location"]     = locations
    df["Channel"]      = channels
    df["Customer"]     = customers
    df["Queue"]        = queues
    df["Agent Group"]  = agent_groups
    df["IssueType"]    = issue_types
    df["Severity"]     = severities

    _write_dim("dim_org", df)


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Dimension Enrichment ===")
    enrich_dim_date()
    enrich_dim_org()
    print("\n[OK] Dimension enrichment complete.")
