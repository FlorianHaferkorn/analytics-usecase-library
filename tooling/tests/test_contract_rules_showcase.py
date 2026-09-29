"""
test_contract_rules_showcase.py — Nachweis: die strukturierten Vertragsregeln halten auf Aurora-Gold.

A-23 (29.09.2026). Führt ``nullable``, ``ref``, ``unknown_member`` und ``checks`` aller
Domänenverträge per duckdb gegen die aktiven Delta-Dateien der Aurora-Gold-Tabellen aus.
Das ist ein **Nachweis für die Verträge**, kein Produkt-DQ-Ausführer: die Ausführung beim Kunden
gehört in Meridian (``emit_dq_gates``/``emit_mlv`` lesen die Felder über den governed catalog).

Zählung je Regel (die Zähler stehen in der Test-ID und im Output, damit "nichts gefunden" nie
als "alles geprüft" gelesen wird):

* ``geprueft``          Tabelle und Spalte(n) sind im Showcase, die Regel lief.
* ``nicht_im_showcase`` Tabelle ``showcase: false``, Spalte ``target_state: true`` oder die
                        referenzierte Dimension ist nicht im Showcase.
* ``spalte_fehlt``      Tabelle im Showcase, Spalte nicht in Gold. Erlaubt nur für die exakt
                        benannten Fälle in ``BEKANNT_OHNE_GOLD`` (Sperrklinke).

Semantik: fehlt ``nullable: true``, darf die Spalte nicht NULL sein. ``checks`` werten NULL als
Verstoß, außer ``when_present: true``; bei ``*_column`` ist ein NULL auf der Vergleichsseite
nicht auswertbar und zählt nicht als Verstoß. ``unknown_member`` verlangt die Platzhalterzeile
in der referenzierten Dimension.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
CONTRACTS = REPO / "core" / "data_contracts" / "domains"
GOLD = REPO / "showcases" / "aurora_group" / "data" / "gold"

# Vertragsspalten ohne Gold-Spalte — Sperrklinke, exakte Menge. Seit 29.09.2026 leer: die zehn
# A-24-Luecken schloss der Gold-Generator, die zwei Namensfragen (`fact_sales.Sales Units`,
# `fact_inventory.Inventory Amount`) entschied Florian nach Best Practice — der Vertrag nennt die
# physische Gold-Spalte (`Quantity`, `Average Inventory Amount`), der fachliche Name ist Synonym.
# Jede neue Luecke macht den Test rot.
BEKANNT_OHNE_GOLD: set[tuple[str, str]] = set()

_OPS = {"gte": ">=", "gt": ">", "lte": "<=", "lt": "<", "gte_column": ">=", "lte_column": "<="}


def _q(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _lit(v) -> str:
    return repr(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else "'" + str(v).replace("'", "''") + "'"


def _gold_tables() -> dict[str, Path]:
    out = {}
    for sub in ("dimensions", "facts"):
        base = GOLD / sub
        if base.is_dir():
            for p in sorted(base.iterdir()):
                if p.is_dir() and any(p.rglob("*.parquet")):
                    out[p.name] = p
    return out


def _rules() -> list[dict]:
    """Every structured rule of every contract, deduplicated over (table, column, rule)."""
    keys, rules, seen = {}, [], set()
    docs = [yaml.safe_load(p.read_text(encoding="utf-8")) for p in sorted(CONTRACTS.glob("*.yaml"))]
    for doc in docs:
        for dim in doc.get("dimension") or []:
            for c in dim.get("columns") or []:
                if c.get("role") == "key":
                    keys[dim["name"]] = c["name"]
    showcase = collections.defaultdict(lambda: True)
    for doc in docs:
        for kind in ("dimension", "fact"):
            for t in doc.get(kind) or []:
                if t.get("showcase") is False:
                    showcase[t["name"]] = False
    for doc in docs:
        for kind in ("dimension", "fact"):
            for t in doc.get(kind) or []:
                for c in t.get("columns") or []:
                    # Gegen Gold zaehlt die physische Spalte: source_column, sonst der Name.
                    base = {"table": t["name"], "column": c.get("source_column", c["name"]), "showcase": showcase[t["name"]],
                            "target_state": bool(c.get("target_state"))}
                    found = []
                    if c.get("nullable") is not True:
                        found.append({"rule": "not_null"})
                    if c.get("ref"):
                        found.append({"rule": "ref", "dim": c["ref"], "key": keys.get(c["ref"], c["name"]),
                                      "dim_showcase": showcase[c["ref"]]})
                    if "unknown_member" in c:
                        found.append({"rule": "unknown_member", "dim": c["ref"],
                                      "key": keys.get(c["ref"], c["name"]), "value": c["unknown_member"],
                                      "dim_showcase": showcase[c["ref"]]})
                    for chk in c.get("checks") or []:
                        found.append({"rule": "check", "check": chk})
                    for r in found:
                        r = {**base, **r}
                        ident = json.dumps(r, sort_keys=True, default=str)
                        if ident not in seen:
                            seen.add(ident)
                            rules.append(r)
    return rules


def _predicate(r: dict) -> str:
    """SQL condition that is TRUE for a violating row (single-table rules)."""
    col = _q(r["column"])
    if r["rule"] == "not_null":
        return f"{col} is null"
    chk = dict(r["check"])
    when_present = chk.pop("when_present", False)
    ((kind, val),) = chk.items()
    null_part = "false" if when_present else f"{col} is null"
    if kind in ("gte", "gt", "lte", "lt"):
        bad = f"not ({col} {_OPS[kind]} {val})"
    elif kind == "between":
        bad = f"not ({col} between {val[0]} and {val[1]})"
    elif kind == "in":
        bad = f"cast({col} as varchar) not in ({', '.join(_lit(str(v)) for v in val)})"
    else:  # gte_column / lte_column
        bad = f"{_q(val)} is not null and not ({col} {_OPS[kind]} {_q(val)})"
    return f"({null_part}) or ({col} is not null and {bad})"


def _columns_needed(r: dict) -> list[str]:
    cols = [r["column"]]
    if r["rule"] == "check":
        for k in ("gte_column", "lte_column"):
            if k in r["check"]:
                cols.append(r["check"][k])
    return cols


def _run():
    duckdb = pytest.importorskip("duckdb", reason="duckdb fehlt (requirements.txt)")
    sys.path.insert(0, str(REPO / "tooling" / "validation"))
    from check_data_model import _files  # Tool-Reuse: Delta-Replay über check_showcase_delta

    gold = _gold_tables()
    con = duckdb.connect()
    schema = {}
    for name, path in gold.items():
        files = [str(f) for f in _files(path)]
        if not files:
            continue
        lst = ", ".join(_lit(f) for f in files)
        con.execute(f"create view {_q(name)} as select * from read_parquet([{lst}], "
                    f"hive_partitioning=true, union_by_name=true)")
        schema[name] = {row[0] for row in con.execute(f"describe {_q(name)}").fetchall()}

    count = collections.Counter()
    missing, violations, per_table = set(), [], collections.defaultdict(list)
    for r in _rules():
        t = r["table"]
        if not r["showcase"] or r["target_state"] or (r["rule"] in ("ref", "unknown_member") and not r["dim_showcase"]):
            count["nicht_im_showcase"] += 1
            continue
        absent = [c for c in _columns_needed(r) if c not in schema.get(t, ())]
        if t not in schema or absent:
            count["spalte_fehlt"] += 1
            missing.update((t, c) for c in (absent or [r["column"]]))
            continue
        if r["rule"] in ("ref", "unknown_member"):
            dim, key = r["dim"], r["key"]
            if dim not in schema or key not in schema[dim]:
                count["spalte_fehlt"] += 1
                missing.add((dim, key))
                continue
            if r["rule"] == "ref":
                sql = (f"select count(*) from {_q(t)} f where f.{_q(r['column'])} is not null and not exists "
                       f"(select 1 from {_q(dim)} d where d.{_q(key)} = f.{_q(r['column'])})")
            else:
                sql = f"select 1 - least(count(*), 1) from {_q(dim)} where {_q(key)} = {_lit(r['value'])}"
            n = con.execute(sql).fetchone()[0]
            count["geprueft"] += 1
            if n:
                violations.append((r, n))
            continue
        per_table[t].append(r)

    for t, rs in per_table.items():
        exprs = ", ".join(f"count(*) filter (where {_predicate(r)})" for r in rs)
        counts = con.execute(f"select {exprs} from {_q(t)}").fetchone()
        for r, n in zip(rs, counts):
            count["geprueft"] += 1
            if n:
                violations.append((r, n))
    return count, violations, missing


@pytest.fixture(scope="module")
def ergebnis():
    if not GOLD.is_dir() or not _gold_tables():
        pytest.skip(f"Aurora-Gold fehlt ({GOLD.relative_to(REPO)}): Showcase-Daten nicht im Checkout, "
                    "Vertragsregeln nicht gegen Daten geprüft")
    return _run()


def test_contract_rules_hold_on_aurora_gold(ergebnis):
    count, violations, missing = ergebnis
    total = sum(count.values())
    print(f"\nVertragsregeln gegen Aurora-Gold: {total} Regeln · geprueft={count['geprueft']} · "
          f"nicht_im_showcase={count['nicht_im_showcase']} · spalte_fehlt={count['spalte_fehlt']} "
          f"(bekannt: {sorted(missing)}) · verletzt={len(violations)}")
    assert count["geprueft"] > 0, "nichts gelaufen — ein Tor muss 'nicht gelaufen' von 'nichts gefunden' trennen"
    assert missing == BEKANNT_OHNE_GOLD, (
        f"Vertragsspalten ohne Gold weichen ab — neu: {sorted(missing - BEKANNT_OHNE_GOLD)}, "
        f"behoben (hier streichen): {sorted(BEKANNT_OHNE_GOLD - missing)}")
    msg = "\n".join(f"  {r['table']}.{r['column']} {r['rule']} {r.get('check', r.get('dim', ''))}: {n} Zeilen"
                    for r, n in violations)
    assert not violations, f"{len(violations)} Vertragsregel(n) verletzt:\n{msg}"


def test_rules_catch_a_seeded_violation(ergebnis):
    """Gegenprobe: dieselbe Prädikat-Erzeugung meldet eine absichtlich falsche Regel."""
    import duckdb

    con = duckdb.connect()
    con.execute("create table t as select * from (values (1, 5), (null, 3), (7, 2)) v(a, b)")
    def n(rule):
        return con.execute(f"select count(*) filter (where {_predicate(rule)}) from t").fetchone()[0]
    base = {"table": "t", "column": "a"}
    assert n({**base, "rule": "not_null"}) == 1
    assert n({**base, "rule": "check", "check": {"lte": 5}}) == 2                       # 7 und NULL
    assert n({**base, "rule": "check", "check": {"lte": 5, "when_present": True}}) == 1
    assert n({**base, "rule": "check", "check": {"between": [2, 6], "when_present": True}}) == 2
    assert n({**base, "rule": "check", "check": {"in": [1], "when_present": True}}) == 1
    assert n({**base, "rule": "check", "check": {"lte_column": "b", "when_present": True}}) == 1
