#!/usr/bin/env python3
"""Deterministische, gedeckelte Scheibe der Aurora-Gold-Schicht (AP-3, 24.09.2026).

Warum es das gibt: ein Lauf gegen einen Fabric-Workspace braucht Daten, und die Gold-Schicht
hat 1,7 GB (gemessen 24.09.2026; davon 1,5 GB `fact_sales` mit 28,7 Mio. Zeilen). Ein
Sandbox-Lauf laedt nie das Ganze, sondern diese Scheibe (UMSETZUNGSPLAN_AGENTIC_LOOP.md §5).

Was die Scheibe erhaelt:

* **Schema wie Power BI es sieht.** Jede aktive Datei wird einzeln gelesen, ohne Hive-
  Partitionsspalten aus dem Pfad -- genau das, was `Parquet.Document` in `fn_DeltaCurrentFiles`
  bekommt. Aktiv heisst: laut `_delta_log` zuletzt `add` (Logik aus
  `scripts/check_showcase_delta.py`, nicht nachgebaut).
* **Dimensionen vollstaendig** (1,5 MB), damit jede Fremdschluesselbeziehung aufloest.
* **Fakten im Zeitfenster**: je Tabelle die letzten `--months` Monate vor ihrem **eigenen**
  spaetesten `DateKey`. 15 Monate decken Vorjahr, Trend und die 90-Tage-Basisfenster der
  Action-Codes. Je Tabelle, nicht global, und das ist gemessen: 40 Fakten enden am 31.12.2024,
  aber `fact_customer_value` endet im November 2020 -- ein globales Fenster liess sie leer, und
  COM-003 (CLV) haette im Sandbox nichts gezeigt (24.09.2026).
* **Keine Tabelle wird leer**, die an der Quelle Zeilen hat. Sonst Exit 1.
* **Zeilendeckel je Fakt**: liegt eine Tabelle danach noch ueber `--max-rows`, bleibt jede
  n-te Zeile nach einem stabilen Hash der ganzen Zeile. Gleiche Eingabe, gleiche Auswahl.
  Summen schrumpfen dabei um den Faktor n; Vergleiche (AP-4) rechnen gegen dieselbe Scheibe.
* **Gesamtdeckel** `--cap-mb`: ueberschritten heisst Exit 1, und das Manifest sagt es.

Ausgabe: je Tabelle eine Datei `<out>/<dimensions|facts>/<tabelle>/part-00000.parquet` ohne
`_delta_log` (die Funktion nimmt dann alle Dateien) plus `_slice_manifest.json` mit Parametern,
Zeilenzahlen und SHA-256 je Datei.

    python showcases/aurora_group/data/scripts/slice_gold.py --out /tmp/gold_slice
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[4]
GOLD = REPO / "showcases" / "aurora_group" / "data" / "gold"
BEREICHE = ("dimensions", "facts")
DATUM = "DateKey"


def _delta():
    spec = importlib.util.spec_from_file_location("check_showcase_delta",
                                                  REPO / "scripts" / "check_showcase_delta.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def aktive_dateien(tabelle: Path) -> list[Path]:
    """Die Dateien, die Power BI laedt: laut Log aktiv, sonst alle Parquet-Dateien."""
    log = tabelle / "_delta_log"
    if log.is_dir():
        pfade = [tabelle / p for p in _delta()._active_paths(str(log))]
    else:
        pfade = [p for p in tabelle.rglob("*.parquet") if "_delta_log" not in p.parts]
    return sorted(pfade, key=lambda p: p.relative_to(tabelle).as_posix())


def lesen(tabelle: Path, ab: int | None = None) -> pa.Table | None:
    """Aktive Dateien einzeln lesen; mit `ab` wird je Datei auf `DateKey >= ab` gefiltert, damit
    `fact_sales` (28,7 Mio. Zeilen) nie ganz im Speicher liegt."""
    dateien = [p for p in aktive_dateien(tabelle) if p.is_file()]
    if not dateien:
        return None
    teile = []
    for p in dateien:
        t = pq.read_table(str(p), partitioning=None)
        if ab is not None and DATUM in t.column_names:
            t = t.filter(pc.greater_equal(t[DATUM], ab))
        teile.append(t)
    return pa.concat_tables(teile, promote_options="default")


def max_datekey(tabelle: Path) -> int | None:
    werte = []
    for _ in (tabelle,):
        for p in aktive_dateien(tabelle):
            if p.is_file() and DATUM in pq.read_schema(str(p)).names:
                m = pc.max(pq.read_table(str(p), columns=[DATUM], partitioning=None)[DATUM]).as_py()
                if m is not None:
                    werte.append(m)
    return max(werte, default=None)


def fensteranfang(max_datekey: int, monate: int) -> int:
    jahr, monat = divmod(max_datekey // 100, 100)
    index = jahr * 12 + (monat - 1) - (monate - 1)
    return (index // 12) * 10000 + (index % 12 + 1) * 100 + 1


def ausduennen(tab: pa.Table, max_rows: int) -> tuple[pa.Table, int]:
    """Jede n-te Zeile nach stabilem Zeilen-Hash. n=1 heisst: nichts ausgeduennt."""
    if tab.num_rows <= max_rows:
        return tab, 1
    import pandas as pd
    n = math.ceil(tab.num_rows / max_rows)
    h = pd.util.hash_pandas_object(tab.to_pandas(), index=False).to_numpy()
    return tab.filter(pa.array(h % n == 0)), n


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def schneiden(gold: Path, out: Path, *, monate: int = 15, max_rows: int = 150_000,
              cap_mb: float = 50.0) -> dict:
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"Ziel ist nicht leer: {out} -- die Scheibe ueberschreibt nichts")
    tabellen = {b: sorted(p for p in (gold / b).iterdir() if p.is_dir()) for b in BEREICHE
                if (gold / b).is_dir()}
    eintraege = []
    for bereich, name, pfad in sorted((b, t.name, t) for b, ts in tabellen.items() for t in ts):
        zeilen_ein = sum(pq.read_metadata(str(p)).num_rows for p in aktive_dateien(pfad) if p.is_file())
        max_dk = max_datekey(pfad) if bereich == "facts" else None
        anfang = fensteranfang(max_dk, monate) if max_dk else None
        tab = lesen(pfad, anfang)
        if tab is None:
            continue
        n = 1
        if bereich == "facts":
            tab, n = ausduennen(tab, max_rows)
        ziel = out / bereich / name / "part-00000.parquet"
        ziel.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(tab, str(ziel), compression="snappy")
        eintraege.append({"tabelle": f"{bereich}/{name}", "zeilen_ein": zeilen_ein,
                          "zeilen_aus": tab.num_rows, "jede_n_te": n,
                          "fenster": {"max_datekey": max_dk, "anfang": anfang},
                          "bytes": ziel.stat().st_size, "sha256": _sha(ziel)})

    gesamt = sum(e["bytes"] for e in eintraege)
    leer_geworden = [e["tabelle"] for e in eintraege if e["zeilen_ein"] and not e["zeilen_aus"]]
    manifest = {"parameter": {"monate": monate, "max_rows": max_rows, "cap_mb": cap_mb},
                "gesamt_bytes": gesamt, "cap_ueberschritten": gesamt > cap_mb * 1024 * 1024,
                "leer_geworden": leer_geworden, "tabellen": eintraege}
    (out / "_slice_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False)
                                              + "\n", encoding="utf-8", newline="\n")
    return manifest


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--gold", type=Path, default=GOLD)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--months", type=int, default=15)
    ap.add_argument("--max-rows", type=int, default=150_000)
    ap.add_argument("--cap-mb", type=float, default=50.0)
    a = ap.parse_args(argv)
    m = schneiden(a.gold, a.out, monate=a.months, max_rows=a.max_rows, cap_mb=a.cap_mb)
    mb = m["gesamt_bytes"] / 1024 / 1024
    print(f"[slice-gold] {len(m['tabellen'])} Tabellen, {mb:.1f} MB, {a.months} Monate je Fakt, "
          f"{sum(e['jede_n_te'] > 1 for e in m['tabellen'])} ausgeduennt")
    if m["leer_geworden"]:
        print(f"[slice-gold] an der Quelle gefuellt, in der Scheibe leer: {m['leer_geworden']}",
              file=sys.stderr)
        return 1
    if m["cap_ueberschritten"]:
        groesste = sorted(m["tabellen"], key=lambda e: -e["bytes"])[:5]
        print(f"[slice-gold] Deckel {a.cap_mb} MB ueberschritten; groesste Tabellen:", file=sys.stderr)
        for e in groesste:
            print(f"  {e['tabelle']}: {e['bytes'] / 1024 / 1024:.1f} MB", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
