#!/usr/bin/env python3
"""check_data_model.py — data-model best-practice gate (Kimball hygiene).

`check_validate_data_contracts.py` proves the contract YAML is *structurally* valid
(has a grain, names, …). It does NOT prove the model is *well modelled*. This gate adds
the missing layer: it reads the domain data contracts (and, where present, the Aurora
gold parquet) and flags the modelling-defect classes that otherwise only a careful human
review catches — the exact classes that slipped past every gate in the 2026-07 gap-fill
work (multi-grain snapshot, degenerate key, non-conformed dimension, wrong-grain PPV).

Hard findings (exit 1 always):
  • MISSING-GRAIN   — a fact without a declared `grain`.
  • DANGLING-REF    — a column `ref: dim_x` where `dim_x` is declared in no contract.
  • NON-CONFORMED   — the same dimension NAME declared in ≥2 contracts with a DIFFERENT
                      key column (a "supplier" that is `SupplierKey` here and `VendorKey`
                      there is not one conformed dimension).
  • ORPHAN-FK       — (gold present) a fact FK value absent from the referenced dim PK.

Advisory findings (exit 1 only with --strict):
  • DEGENERATE-KEY  — (gold) a fact FK column 1:1 derivable from another FK on the same
                      fact (e.g. CostCenterKey functionally determined by OrgKey) — it
                      belongs on the dimension, not the fact.

Deliberately NOT flagged: a fact holding rows at several org levels. In this model that
is the correct ragged-hierarchy snapshot pattern (each node holds its own disjoint
staff/rows and rolls up cleanly); a blanket flag would fire on almost every fact and
train reviewers to ignore the gate. Whether a parent row double-counts its children is a
measure-semantics question this static check cannot answer, so it is left out on purpose.

Usage:
    python tooling/validation/check_data_model.py            # hard findings fail; advisories print
    python tooling/validation/check_data_model.py --strict   # advisories fail too
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    print("ERROR: pyyaml not installed.", file=sys.stderr)
    sys.exit(1)

REPO = Path(__file__).resolve().parents[2]

# Tool-Reuse: den Delta-Log-Replay gibt es schon, er wird nicht nachgebaut. `scripts/` ist
# kein Paket, deshalb ueber den Pfad geladen statt importiert.
sys.path.insert(0, str(REPO / "scripts"))
from check_showcase_delta import _active_paths  # noqa: E402

CONTRACTS = REPO / "core" / "data_contracts" / "domains"
GOLD = REPO / "showcases" / "aurora_group" / "data" / "gold"

# advisory groupby checks are skipped above this row count (kept fast on 10M+ facts)
_ADVISORY_ROW_CAP = 3_000_000


# ---------------------------------------------------------------------------
# parsing (pure — unit-testable without disk)
# ---------------------------------------------------------------------------

def _key_of(dim: dict) -> Optional[str]:
    cols = dim.get("columns") or []
    for c in cols:
        if isinstance(c, dict) and c.get("role") == "key":
            return c.get("name")
    return cols[0].get("name") if cols and isinstance(cols[0], dict) else None


def parse_model(contracts_dir: Path) -> dict[str, Any]:
    """Return {'facts': [...], 'dims': [...]} parsed from every domain contract.

    fact = {domain, name, grain, refs: [(column, dim_name)], keys: [column,…]}
    dim  = {domain, name, key}

    Only definitions: a conformed reference (``conformed_from``, Bus-Matrix 29.09.2026) is the
    owner's table, not a second declaration — whether it resolves is the contract validator's job.
    """
    facts, dims = [], []
    for f in sorted(contracts_dir.glob("*.yaml")):
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        domain = data.get("domain", f.stem)
        for d in (data.get("dimension") or []):
            if isinstance(d, dict) and d.get("name") and "conformed_from" not in d:
                dims.append({"domain": domain, "name": d["name"], "key": _key_of(d)})
        for fc in (data.get("fact") or []):
            if not (isinstance(fc, dict) and fc.get("name")) or "conformed_from" in fc:
                continue
            refs, keys = [], []
            for c in (fc.get("columns") or []):
                if not isinstance(c, dict):
                    continue
                if c.get("ref"):
                    refs.append((c["name"], c["ref"]))
                if c.get("ref") or c.get("role") == "key":
                    keys.append(c["name"])
            facts.append({"domain": domain, "name": fc["name"], "grain": fc.get("grain"),
                          "refs": refs, "keys": keys})
    return {"facts": facts, "dims": dims}


# ---------------------------------------------------------------------------
# contract-only checks (pure)
# ---------------------------------------------------------------------------

def check_grain(model: dict) -> list[str]:
    return [f"MISSING-GRAIN  {f['domain']}/{f['name']}: fact has no `grain`"
            for f in model["facts"] if not (f.get("grain") or "").strip()]


def check_dangling_refs(model: dict) -> list[str]:
    dim_names = {d["name"] for d in model["dims"]}
    out = []
    for f in model["facts"]:
        for col, dim in f["refs"]:
            if dim not in dim_names:
                out.append(f"DANGLING-REF   {f['domain']}/{f['name']}.{col} → `{dim}` (declared in no contract)")
    return out


def check_conformance(model: dict) -> list[str]:
    by_name: dict[str, set] = {}
    where: dict[str, set] = {}
    for d in model["dims"]:
        by_name.setdefault(d["name"], set()).add(d["key"])
        where.setdefault(d["name"], set()).add(d["domain"])
    out = []
    for name, keys in sorted(by_name.items()):
        if len(keys) > 1:
            out.append(f"NON-CONFORMED  dim `{name}` declared with different keys "
                       f"{sorted(k for k in keys if k)} across {sorted(where[name])} "
                       f"— one conformed dimension must have one key")
    return out


# ---------------------------------------------------------------------------
# gold-gated checks
# ---------------------------------------------------------------------------

def _gold_dir(name: str) -> Optional[Path]:
    for sub in ("facts", "dimensions"):
        p = GOLD / sub / name
        if p.exists() and list(p.rglob("*.parquet")):
            return p
    return None


def _files(path: Path) -> list[Path]:
    """Die parquet-Dateien, die Delta tatsaechlich ausliefert — nicht alles, was herumliegt.

    Vorher stand hier ein blankes ``rglob``. Das las auch die Dateien, die der ``_delta_log``
    laengst per ``remove`` verabschiedet hat, also Daten, die keine Abfrage je zu sehen bekommt.
    Der Fehler ging in beide Richtungen: gemessen am 11.08.2026 trug ``dim_product`` an der
    Merge-Basis drei solche Leichen mit den ProductKeys 4997–5000, und genau die haben die
    ORPHAN-FK-Pruefung **gruen** gehalten — die Fakten fuehren dieselben Schluessel in 238 ebenso
    verwaisten Dateien. Nach dem Vacuum aus #424 fiel die Maske auf der Dimensionsseite weg, und
    dasselbe Datenpaar meldete drei harte Befunde. Weder das Gruen davor noch das Rot danach
    beschrieb die aktiven Daten: dort endete der hoechste ProductKey auf beiden Seiten bei 4996.
    (Die Lucke selbst ist inzwischen an der Wurzel geschlossen — der Generator verlor vier
    Produkte an eine Ganzzahldivision; ``dim_product`` traegt wieder 5000 Schluessel.)

    Log gegen Platte ist nicht Aufgabe dieses Gates — das prueft ``scripts/check_showcase_delta.py``
    und sagt in seiner eigenen Ausgabe, dass die fachliche FK-Pruefung hier liegt. Deshalb
    Tool-Reuse statt zweitem Leser: dessen ``_active_paths`` wird aufgerufen, nicht nachgebaut.
    Ohne ``_delta_log`` (reines parquet-Verzeichnis) bleibt es beim rglob.
    """
    log = path / "_delta_log"
    if not log.is_dir():
        return sorted(path.rglob("*.parquet"))
    aktiv = [path / rel for rel in _active_paths(str(log))]
    return sorted(p for p in aktiv if p.exists())


def _num_rows(path: Path) -> int:
    """Total rows from parquet footers only (instant — no data read)."""
    import pyarrow.parquet as pq
    return sum(pq.ParquetFile(f).metadata.num_rows for f in _files(path))


def _unique(path: Path, col: str) -> Optional[set]:
    """Union of distinct values of one column, read column-only per file (low memory)."""
    import pyarrow.compute as pc
    import pyarrow.parquet as pq
    vals: set = set()
    for f in _files(path):
        t = pq.ParquetFile(f)
        if col not in t.schema_arrow.names:
            return None
        tbl = pq.read_table(f, columns=[col])
        vals.update(pc.unique(tbl.column(col)).to_pylist())
    vals.discard(None)
    return vals


def _read_small(path: Path, columns: list[str]):
    """pandas frame of the given columns — only for row-capped advisory checks."""
    import pandas as pd
    import pyarrow.parquet as pq
    present = set(pq.ParquetFile(_files(path)[0]).schema_arrow.names)
    use = [c for c in columns if c in present]
    if len(use) != len(columns):
        return None
    return pd.concat([pd.read_parquet(f, columns=use) for f in _files(path)], ignore_index=True)


def check_referential_integrity(model: dict) -> list[str]:
    dim_key = {d["name"]: d["key"] for d in model["dims"]}
    out = []
    for f in model["facts"]:
        fdir = _gold_dir(f["name"])
        if fdir is None:
            continue
        for col, dim in f["refs"]:
            ddir = _gold_dir(dim)
            key = dim_key.get(dim)
            if ddir is None or not key:
                continue
            fv = _unique(fdir, col)
            dv = _unique(ddir, key)
            if fv is None or dv is None:
                continue
            orphans = fv - dv
            if orphans:
                ex = sorted(orphans, key=lambda x: (str(type(x)), x))[:3]
                out.append(f"ORPHAN-FK      {f['domain']}/{f['name']}.{col} → {dim}[{key}]: "
                           f"{len(orphans)} value(s) not in dim (e.g. {ex})")
    return out


def check_degenerate_keys(model: dict) -> list[str]:
    out = []
    for f in model["facts"]:
        # only FK columns (ref → dim) count; a fact's own surrogate row-key (role: key,
        # e.g. OpportunityID) trivially determines every column and is not a degeneracy.
        ref_cols = [c for c, _ in f["refs"]]
        fdir = _gold_dir(f["name"])
        if fdir is None or len(ref_cols) < 2 or _num_rows(fdir) > _ADVISORY_ROW_CAP:
            continue
        df = _read_small(fdir, ref_cols)
        if df is None or len(df) == 0:
            continue
        for a in ref_cols:
            for b in ref_cols:
                if a == b or df[a].nunique() <= 1 or df[b].nunique() <= 1:
                    continue
                if df[b].nunique() >= df[a].nunique():
                    continue  # b must be the coarser (derivable) key
                if int(df.groupby(a)[b].nunique().max()) == 1:
                    out.append(f"DEGENERATE-KEY {f['domain']}/{f['name']}.{b} is 1:1 derivable from "
                               f"{a} — move it onto the dimension, don't carry it on the fact")
    return out


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------

_HARD = (check_grain, check_dangling_refs, check_conformance, check_referential_integrity)
_ADVISORY = (check_degenerate_keys,)


def run(model: Optional[dict] = None, with_gold: bool = True) -> tuple[list[str], list[str]]:
    model = model or parse_model(CONTRACTS)
    hard, advisory = [], []
    for chk in _HARD:
        if chk is check_referential_integrity and not with_gold:
            continue
        hard += chk(model)
    if with_gold:
        for chk in _ADVISORY:
            advisory += chk(model)
    return hard, advisory


def main() -> int:
    ap = argparse.ArgumentParser(description="Data-model best-practice gate (Kimball hygiene)")
    ap.add_argument("--strict", action="store_true", help="advisory findings also fail")
    ap.add_argument("--no-gold", action="store_true", help="contract-only checks (skip parquet)")
    args = ap.parse_args()

    hard, advisory = run(with_gold=not args.no_gold)
    for m in hard:
        print(f"  ✗ {m}")
    for m in advisory:
        print(f"  ℹ {m}")
    n_fact = len(parse_model(CONTRACTS)["facts"])
    print(f"\ncheck_data_model: {n_fact} facts · {len(hard)} hard finding(s) · {len(advisory)} advisory.")
    if hard or (args.strict and advisory):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
