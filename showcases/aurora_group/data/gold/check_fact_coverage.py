"""
Check all fact tables in gold/facts for row count, date coverage (2020-2024), and layout.
Run from repo root: py showcases/aurora_group/data/gold/check_fact_coverage.py

Output: rows, date column, min/max date, unique dates, parquet file count, and flags
(SPARSE = very few rows for a dated fact; MULTI = multiple parquets so M must use Table.Combine).
"""
import pandas as pd
from pathlib import Path

gold = Path(__file__).resolve().parent
facts_dir = gold / "facts"
FACTS_START = 20200101
FACTS_END = 20241231

# Facts that should have rich daily/monthly data (not just a few hundred rows)
# Note: fact_cash_flow is monthly org-level summary (20 orgs × 60 months = 1,200 rows is reasonable)
RICH_FACTS = frozenset({
    "fact_ops", "fact_quality", "fact_support_cases", "fact_workforce_management",
    "fact_accounts_payable", "fact_accounts_receivable", "fact_cash_position",
    "fact_inventory", "fact_cogs", "fact_fulfillment", "fact_stockout", "fact_forecast",
    "fact_experience", "fact_sales", "fact_working_capital",
})

# Date-partitioned facts that are expected to be written as Delta Lake (when deltalake is installed)
# fact_promo is intentionally Parquet (no date dimension). Dimensions are Parquet.
DELTA_EXPECTED_FACTS = frozenset({
    "fact_sales", "fact_accounts_payable", "fact_accounts_receivable", "fact_cash_position",
    "fact_cash_flow", "fact_inventory", "fact_cogs", "fact_fulfillment", "fact_stockout",
    "fact_forecast", "fact_ops", "fact_ops_failures", "fact_maintenance", "fact_quality",
    "fact_experience",
})

# Date columns to check (first found wins)
DATE_COLUMNS = ["DateKey", "MonthEnd DateKey", "Start DateKey", "date_key"]

def find_parquet_files(fact_path: Path) -> list[Path]:
    """All parquet files under fact_path (recursive)."""
    return sorted(fact_path.rglob("*.parquet"))

def is_delta_format(fact_path: Path) -> bool:
    """Check if fact is stored in Delta Lake format (has _delta_log folder)."""
    delta_log_path = fact_path / "_delta_log"
    return delta_log_path.exists() and delta_log_path.is_dir()

def load_fact(fact_path: Path) -> tuple[pd.DataFrame | None, int]:
    """Load single or multiple parquet files into one DataFrame. Returns (df, file_count)."""
    files = find_parquet_files(fact_path)
    if not files:
        return None, 0
    try:
        if len(files) == 1:
            return pd.read_parquet(files[0]), 1
        return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True), len(files)
    except Exception as e:
        print(f"  Error loading: {e}")
        return None, len(files)

def get_date_col(df: pd.DataFrame) -> str | None:
    for c in DATE_COLUMNS:
        if c in df.columns:
            return c
    return None

def main():
    print("Fact table coverage check (2020-2024 expected)")
    print("=" * 85)
    if not facts_dir.is_dir():
        print(f"Facts dir not found: {facts_dir}")
        return

    results = []
    for fact_name in sorted(d.name for d in facts_dir.iterdir() if d.is_dir() and not d.name.startswith("_")):
        fact_path = facts_dir / fact_name
        is_delta = is_delta_format(fact_path)
        df, n_files = load_fact(fact_path)
        if df is None:
            fmt = "Delta" if is_delta else "Parquet"
            results.append((fact_name, 0, None, None, None, "no parquet or load error", n_files, fmt))
            continue
        n = len(df)
        fmt = "Delta" if is_delta else "Parquet"
        date_col = get_date_col(df)
        if date_col is None:
            dt_cols = [c for c in df.columns if "date" in c.lower() or "datetime" in c.lower()]
            if dt_cols:
                dc = dt_cols[0]
                vals = pd.to_datetime(df[dc], errors="coerce").dropna()
                if len(vals) > 0:
                    min_ts, max_ts = vals.min(), vals.max()
                    results.append((fact_name, n, None, str(min_ts.date()), str(max_ts.date()), f"column {dc}", n_files, fmt))
                else:
                    results.append((fact_name, n, None, "-", "-", "no valid dates", n_files, fmt))
            else:
                results.append((fact_name, n, None, "-", "-", "no date column", n_files, fmt))
            continue
        vals = df[date_col].dropna()
        if len(vals) == 0:
            results.append((fact_name, n, date_col, "-", "-", "empty date", n_files, fmt))
            continue
        try:
            min_d = int(vals.min())
            max_d = int(vals.max())
        except (TypeError, ValueError):
            min_d = str(vals.min())[:10]
            max_d = str(vals.max())[:10]
        unique_dates = df[date_col].nunique()
        results.append((fact_name, n, date_col, min_d, max_d, unique_dates if isinstance(min_d, int) else "-", n_files, fmt))

    # Print table with file count, format, and flags
    print(f"{'Fact':35} {'Rows':>12} {'DateCol':18} {'Min':12} {'Max':12} {'N dates':>8}  {'Files':>6}  {'Format':>8}  Notes")
    print("-" * 100)
    for r in results:
        name, n, col, lo, hi, extra, n_files, fmt = r
        date_ok = isinstance(lo, int) and isinstance(hi, int) and FACTS_START <= lo and hi <= FACTS_END
        sparse = name in RICH_FACTS and n < 2000 and isinstance(extra, (int, float)) and extra == 60
        multi = n_files > 1
        notes = []
        if not date_ok and isinstance(extra, str) and "column" not in extra and extra != "no date column":
            notes.append("DATE")
        if sparse:
            notes.append("SPARSE")
        if multi:
            notes.append("MULTI")
        if name in DELTA_EXPECTED_FACTS and fmt == "Parquet":
            notes.append("EXPECT_DELTA")
        note_str = ",".join(notes) if notes else "OK"
        print(f"{name:35} {n:>12,} {str(col):18} {str(lo):12} {str(hi):12} {str(extra):>8}  {n_files:>6}  {fmt:>8}  {note_str}")
    print("=" * 100)
    print("SPARSE = few rows for a fact that should have full 2020-2024 (re-run supply_chain or operations).")
    print("MULTI  = multiple parquet files; semantic model must use Table.Combine (e.g. fact_sales, fact_experience).")
    print("Format = Delta Lake (partitioned) or Parquet (single file). Delta facts use Table.Combine in TMDL.")
    print("EXPECT_DELTA = fact is date-partitioned and should be Delta; install deltalake==1.6.2 and regenerate (see README).")

if __name__ == "__main__":
    main()
