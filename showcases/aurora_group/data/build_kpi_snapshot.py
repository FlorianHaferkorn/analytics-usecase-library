#!/usr/bin/env python3
"""Aggregate the Aurora gold facts into a KPI-values snapshot for ActionReady Studio.

Studio reads governed metadata from core/ live, but report/dashboard numbers were
hard-coded zeros/stubs (Studio audit Gap 1/3: showcases/aurora_group is not wired
in). This tool computes the real commercial KPI values from the gold fact tables
(DuckDB over the partitioned parquet) and writes a static JSON snapshot that the
Studio loader consumes -- no DuckDB/parquet reader needed at Studio runtime.

Usage:
    python showcases/aurora_group/data/build_kpi_snapshot.py
    # writes studio/data/aurora_kpi_snapshot.json

Only the files the ``_delta_log`` marks active are read (29.09.2026). The former
``**/*.parquet`` glob also read part-files that later commits had ``remove``d: measured
on fact_sales, 298 parquet files / 28.7M rows on disk versus 60 active files / 9.35M
rows, which inflated every summed KPI. The log replay is reused from
``scripts/check_showcase_delta.py`` (same reader as ``check_data_model.py`` and
``slice_gold.py``), not rebuilt here.
"""

from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

import duckdb

_REPO = Path(__file__).resolve().parents[3]
_GOLD = _REPO / "showcases" / "aurora_group" / "data" / "gold" / "facts" / "fact_sales"
_OUT = _REPO / "studio" / "data" / "aurora_kpi_snapshot.json"
_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _active_paths(log_dir: Path) -> list[str]:
    spec = importlib.util.spec_from_file_location(
        "check_showcase_delta", _REPO / "scripts" / "check_showcase_delta.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod._active_paths(str(log_dir))


def active_files(table: Path) -> list[Path]:
    """Parquet files the Delta log marks active; without a log, every parquet file.

    Delta stores ``add.path`` as a URI: deltalake >= 1.6.6 writes ``Fiscal%20Year=...``
    while the directory on disk stays ``Fiscal Year=...`` (1.6.2 writes it unencoded).
    Both spellings are accepted; an active file missing on disk is an error, never a
    silent drop -- a smaller sum would look like a valid KPI value.
    """
    log = table / "_delta_log"
    if not log.is_dir():
        return sorted(table.rglob("*.parquet"))
    files, missing = [], []
    for rel in _active_paths(log):
        p = table / rel
        if not p.exists():
            p = table / unquote(rel)
        (files if p.exists() else missing).append(p)
    if missing:
        raise FileNotFoundError(
            f"{len(missing)} active file(s) from {log} missing on disk, e.g. {missing[0]}")
    return sorted(files, key=lambda p: p.relative_to(table).as_posix())


def _glob() -> str:
    files = ", ".join("'" + p.as_posix().replace("'", "''") + "'" for p in active_files(_GOLD))
    return f"read_parquet([{files}], hive_partitioning=true)"


def _monthly(con: duckdb.DuckDBPyConnection) -> list[dict]:
    rows = con.sql(f"""
        SELECT "Fiscal Year" AS fy, "Fiscal Month" AS fm,
               SUM("Net Sales Amount")          AS net_sales,
               SUM("Cost of Goods Sold Amount") AS cogs,
               SUM("Plan Sales Amount")         AS plan_sales,
               SUM("Last Year Sales Amount")    AS ly_sales
        FROM {_glob()}
        GROUP BY 1, 2
        ORDER BY fy, fm
    """).fetchall()
    out = []
    for fy, fm, net, cogs, plan, ly in rows:
        net, cogs, plan, ly = (float(x or 0) for x in (net, cogs, plan, ly))
        out.append({
            "fy": int(fy), "fm": int(fm), "label": _MONTHS[(int(fm) - 1) % 12],
            "net_sales": net, "cogs": cogs, "plan_sales": plan, "ly_sales": ly,
            "gm_amount": net - cogs,
            "gm_pct": (net - cogs) / net * 100 if net else 0.0,
            "vs_plan_pct": (net - plan) / plan * 100 if plan else 0.0,
            "vs_ly_pct": (net - ly) / ly * 100 if ly else 0.0,
        })
    return out


def _kpi(months: list[dict], field: str, unit: str, target_field: str | None = None) -> dict:
    latest, prev = months[-1], (months[-2] if len(months) > 1 else months[-1])
    trend = [{"period": m["label"], "value": round(m[field], 2)} for m in months[-12:]]
    return {
        "value": round(latest[field], 2),
        "previousValue": round(prev[field], 2),
        "target": round(latest[target_field], 2) if target_field else round(latest[field], 2),
        "unit": unit,
        "trend": trend,
    }


def build_snapshot() -> dict:
    con = duckdb.connect()
    con.sql("SET enable_progress_bar=false")
    months = _monthly(con)
    latest = months[-1]
    kpis = {
        "KPI-COM-005": _kpi(months, "net_sales", "EUR", "plan_sales"),
        "KPI-COM-013": _kpi(months, "gm_pct", "%"),
        "KPI-FIN-011": _kpi(months, "cogs", "EUR"),
        "KPI-COM-009": _kpi(months, "vs_plan_pct", "%"),
        "KPI-COM-008": _kpi(months, "vs_ly_pct", "%"),
    }
    return {
        "_meta": {
            "source": "showcases/aurora_group/data/gold/facts/fact_sales",
            "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "latestPeriod": f"FY{latest['fy']}-M{latest['fm']:02d}",
            "note": "Generated by build_kpi_snapshot.py from Aurora gold; consumed by Studio.",
        },
        "kpis": kpis,
    }


def main() -> int:
    snapshot = build_snapshot()
    _OUT.parent.mkdir(parents=True, exist_ok=True)
    _OUT.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    meta = snapshot["_meta"]
    gm = snapshot["kpis"]["KPI-COM-013"]["value"]
    ns = snapshot["kpis"]["KPI-COM-005"]["value"]
    print(f"Wrote {_OUT} ({meta['latestPeriod']}): Net Sales {ns:,.0f} EUR, Gross Margin % {gm}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
