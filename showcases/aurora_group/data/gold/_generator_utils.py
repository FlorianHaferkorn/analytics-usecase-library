"""
Generator Utilities Module
==========================

Shared utilities for synthetic data generation:
- Time period management (consistent 2020-2024)
- Seasonality functions with year-over-year and week-over-week variation
- Common data generation patterns

Usage:
    from _generator_utils import get_fact_date_range, apply_monthly_seasonality, apply_weekly_seasonality
    
    dates = get_fact_date_range()
    factor = apply_monthly_seasonality(date, base_factor=1.0, seed=12345)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Tuple


# Standard time period for all facts
FACTS_START = datetime(2020, 1, 1)
FACTS_END = datetime(2024, 12, 31)


def get_fact_date_range() -> pd.DatetimeIndex:
    """
    Get standard date range for fact tables (2020-01-01 to 2024-12-31).
    
    Returns:
        DatetimeIndex covering the full fact period
    """
    return pd.date_range(start=FACTS_START, end=FACTS_END, freq='D')


def get_fact_date_keys() -> list[int]:
    """
    Get list of DateKey values (YYYYMMDD integers) for fact period.
    
    Returns:
        List of DateKey integers
    """
    dates = get_fact_date_range()
    return [int(d.strftime('%Y%m%d')) for d in dates]


def apply_monthly_seasonality(
    date: datetime,
    base_factor: float = 1.0,
    seed: Optional[int] = None,
) -> float:
    """
    Apply monthly seasonality with year-over-year variation.
    
    Each year has slightly different monthly patterns to avoid identical distributions
    in year-over-year comparisons. Uses deterministic seed based on year and month.
    
    Args:
        date: Date to calculate seasonality for
        base_factor: Base multiplier (default 1.0)
        seed: Optional base seed (defaults to year * 1000 + month)
    
    Returns:
        Seasonality factor (multiplier)
    """
    # Base monthly pattern (retail: Q4 peak, summer boost)
    base_monthly = {
        1: 0.85,   # January post-holiday dip
        2: 0.90,   # February
        3: 1.00,   # March baseline
        4: 1.05,   # April spring
        5: 1.00,   # May
        6: 1.05,   # June summer start
        7: 1.10,   # July peak summer
        8: 0.95,   # August vacation dip
        9: 1.05,   # September back-to-school
        10: 1.10,  # October
        11: 1.40,  # November Black Friday start
        12: 1.60,  # December holiday peak
    }
    
    month = date.month
    base_value = base_monthly.get(month, 1.0)
    
    # Year-over-year variation: each year gets a unique modifier per month
    # Use deterministic seed: year * 1000 + month
    if seed is not None:
        year_seed = seed + date.year * 1000 + month
    else:
        year_seed = date.year * 1000 + month
    
    rng = np.random.RandomState(year_seed)
    # Year-specific variation: ±5% per year
    year_variation = rng.uniform(0.95, 1.05)
    
    return base_factor * base_value * year_variation


def apply_weekly_seasonality(
    date: datetime,
    base_factor: float = 1.0,
    seed: Optional[int] = None,
) -> float:
    """
    Apply weekly seasonality with week-over-week variation.
    
    Each week has slightly different weekday patterns to avoid identical distributions
    in week-over-week comparisons. Uses deterministic seed based on year, week, and weekday.
    
    Args:
        date: Date to calculate seasonality for
        base_factor: Base multiplier (default 1.0)
        seed: Optional base seed (defaults to year * 10000 + week * 10 + weekday)
    
    Returns:
        Seasonality factor (multiplier)
    """
    # Base weekday pattern (retail: weekend peak, Sunday lower)
    base_weekday = {
        0: 0.95,  # Monday
        1: 1.00,  # Tuesday baseline
        2: 1.05,  # Wednesday
        3: 1.10,  # Thursday
        4: 1.20,  # Friday peak
        5: 1.30,  # Saturday highest
        6: 0.40,  # Sunday reduced trading
    }
    
    weekday = date.weekday()
    base_value = base_weekday.get(weekday, 1.0)
    
    # Week-over-week variation: each week gets a unique modifier per weekday
    # Use deterministic seed: year * 10000 + week_number * 10 + weekday
    year = date.year
    week_number = date.isocalendar()[1]  # ISO week number
    
    if seed is not None:
        week_seed = seed + year * 10000 + week_number * 10 + weekday
    else:
        week_seed = year * 10000 + week_number * 10 + weekday
    
    rng = np.random.RandomState(week_seed)
    # Week-specific variation: ±3% per week
    week_variation = rng.uniform(0.97, 1.03)
    
    return base_factor * base_value * week_variation


def apply_combined_seasonality(
    date: datetime,
    base_factor: float = 1.0,
    monthly_weight: float = 0.6,
    weekly_weight: float = 0.4,
    seed: Optional[int] = None,
) -> float:
    """
    Apply combined monthly and weekly seasonality.
    
    Args:
        date: Date to calculate seasonality for
        base_factor: Base multiplier
        monthly_weight: Weight for monthly seasonality (default 0.6)
        weekly_weight: Weight for weekly seasonality (default 0.4)
        seed: Optional base seed
    
    Returns:
        Combined seasonality factor
    """
    monthly = apply_monthly_seasonality(date, base_factor=1.0, seed=seed)
    weekly = apply_weekly_seasonality(date, base_factor=1.0, seed=seed)
    
    # Weighted combination
    combined = (monthly * monthly_weight) + (weekly * weekly_weight)
    
    return base_factor * combined


def generate_date_keys_for_period(
    start_date: datetime,
    end_date: datetime,
) -> list[int]:
    """
    Generate DateKey list for a specific period.
    
    Args:
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
    
    Returns:
        List of DateKey integers (YYYYMMDD)
    """
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    return [int(d.strftime('%Y%m%d')) for d in dates]


def get_monthly_date_keys(year: int, month: int) -> list[int]:
    """
    Get DateKey list for a specific month.
    
    Args:
        year: Year (e.g., 2020)
        month: Month (1-12)
    
    Returns:
        List of DateKey integers for that month
    """
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = datetime(year, month + 1, 1) - timedelta(days=1)
    
    return generate_date_keys_for_period(start, end)


def get_quarterly_date_keys(year: int, quarter: int) -> list[int]:
    """
    Get DateKey list for a specific quarter.
    
    Args:
        year: Year (e.g., 2020)
        quarter: Quarter (1-4)
    
    Returns:
        List of DateKey integers for that quarter
    """
    month_start = (quarter - 1) * 3 + 1
    start = datetime(year, month_start, 1)
    
    if quarter == 4:
        end = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = datetime(year, month_start + 3, 1) - timedelta(days=1)
    
    return generate_date_keys_for_period(start, end)


# ---------------------------------------------------------------------------
# Delta Lake write (optional)
# ---------------------------------------------------------------------------

try:
    from deltalake import write_deltalake
    _DELTA_AVAILABLE = True
except ImportError:
    _DELTA_AVAILABLE = False


def write_fact_delta(fact_path, df: pd.DataFrame, partition_by: Optional[list] = None) -> str:
    """
    Write fact DataFrame as Delta Lake (partitioned by Fiscal Year) or single parquet.
    fact_path: pathlib.Path to the fact folder (e.g. facts / "fact_cogs").
    df must contain DateKey; Fiscal Year is derived and added for partitioning.
    Returns "Delta" or "Parquet".
    """
    from pathlib import Path
    fact_path = Path(fact_path)
    fact_path.mkdir(parents=True, exist_ok=True)
    if "Fiscal Year" not in df.columns and "DateKey" in df.columns:
        df = df.copy()
        df["Fiscal Year"] = df["DateKey"].astype(str).str[:4]
    if _DELTA_AVAILABLE and partition_by and "Fiscal Year" in df.columns:
        write_deltalake(str(fact_path), df, mode="overwrite", partition_by=partition_by)
        return "Delta"
    out = df.drop(columns=["Fiscal Year"], errors="ignore")
    out.to_parquet(fact_path / "part-00000.parquet", index=False)
    return "Parquet"
