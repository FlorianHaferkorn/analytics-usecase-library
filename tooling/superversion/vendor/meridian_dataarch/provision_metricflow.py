"""provision_metricflow — bridge the neutral IR to the dbt Semantic Layer (MetricFlow). Idea #3.

The research names the open industry problem: **ODCS ↔ dbt-MetricFlow ↔ Fabric-Direct-Lake are three
separate as-code layers needing custom bridging** — and our IR is exactly that bridge. This emitter maps
the IR's gold layer to dbt ``semantic_models`` and (Golden-Thread) the governed catalog's measures to
dbt ``metrics`` — *referencing* the governed KPI definitions, never re-defining them.

Honest by construction: the IR gives gold products (name/kind/grain), not columns/measures — so without
a governed catalog the semantic models are well-formed skeletons with ``TODO(contract:…)`` where the
business entities/measures go. **With** a governed catalog (`meridian/governed-catalog/v1`), real
dimensions (from the table columns) and real metrics (from the governed measures, carrying their
``kpi_id`` in ``meta``) are emitted — the true bridge. Deterministic, emits only.
"""
from __future__ import annotations

from typing import Any

import yaml

from core.dataarch_engine.blueprint.provision_transforms import _dirslug, _gold_kinds, _ident


def _fuer_produkt(nach_tabelle: dict, product: str):
    """Den Katalogeintrag zu einem IR-Datenprodukt holen — unter BEIDEN gebraeuchlichen Namen.

    Ein SAP-Reverse-Katalog nennt die Tabelle `fact_malfunction`, ein generischer governter Katalog
    nennt sie `gold_fact_sales`. Die Spaltenaufloesung unten kannte beide Formen von Anfang an, die
    Mass-Aufloesung nur eine — gemessen 27.08.2026: bei praefigiertem Namen landete `amount` als
    DIMENSION und das echte Mass wurde durch ein TODO-Geruest ersetzt. Die Datei sah dabei
    vollstaendig aus. Eine Aufloesung, zwei Aufrufer, kein zweiter Weg mehr.
    """
    return nach_tabelle.get(_ident(f"gold_{_ident(product)}")) or nach_tabelle.get(_ident(product))


def _catalog_columns_by_table(gc: dict | None) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for t in (gc or {}).get("tables", []) or []:
        out[_ident(t.get("name", ""))] = sorted(set(t.get("columns", []) or []))
    return out


def _measure_columns_by_fact(gc: dict | None) -> dict[str, set[str]]:
    """Which physical columns on each gold fact are **measures** — so the semantic model declares them as
    ``measures`` (not dimensions) and the metrics reference them. Primary source: the catalog table's
    ``measure_columns`` (all pack measures, incl. ungoverned intermediates); fallback: the measure
    lineage (``fact.column`` refs) for catalogs that don't carry ``measure_columns``."""
    out: dict[str, set[str]] = {}
    for t in (gc or {}).get("tables", []) or []:
        cols = t.get("measure_columns")
        if cols:
            out.setdefault(_ident(t.get("name", "")), set()).update(cols)
    for m in (gc or {}).get("measures", []) or []:          # fallback + derived base cols
        for ref in m.get("lineage", []) or []:
            if "." in ref:
                fact, col = ref.split(".", 1)
                out.setdefault(_ident(fact), set()).add(col)
    return out


def _measure_entry(col: str, contract_ref: str, is_balance: bool) -> dict[str, Any]:
    """A semantic-model measure. Balances carry ``meta.additivity: balance`` + a semi-additive note —
    honest signalling: a balance is additive across non-time dimensions but NOT over time. A proper
    ``non_additive_dimension`` needs the as-of/posting date column, which is a per-system modelling
    choice (facts here often don't project one), so it is flagged rather than guessed."""
    desc = f"governed measure (Contract: {contract_ref})"
    if is_balance:
        desc += (" — BALANCE / semi-additive: additive across non-time dimensions, NOT over time; "
                 "set a non_additive_dimension on the as-of/posting date per system.")
    return {"name": col, "agg": "sum", "description": desc,
            "meta": {"additivity": "balance" if is_balance else "flow"}}


def _count_measures_by_fact(gc: dict | None) -> dict[str, list[dict]]:
    """gold fact → its **row-count** measures (D-344).

    Sie kommen nicht ueber `measure_columns` und auch nicht ueber die Lineage: eine Zaehlung hat
    keine Gold-Spalte, ihr Lineage-Verweis traegt deshalb keinen Punkt und wird von der
    Spalten-Schleife oben absichtlich uebersprungen. Der Katalog fuehrt sie an der Tabelle.
    """
    return {_ident(t.get("name", "")): list(t.get("count_measures") or [])
            for t in (gc or {}).get("tables", []) or []
            if t.get("count_measures")}


def _count_expr(f: dict | None) -> str:
    """Der SQL-Ausdruck, ueber den MetricFlow die Zeilen summiert.

    **ANNAHME, ungeprueft (D-344):** `docs.getdbt.com` ist aus dieser Umgebung nicht erreichbar
    (EGRESS_BLOCKED), die genaue Form von `agg: count` konnte deshalb nicht am Hersteller belegt
    werden. Gewaehlt ist die Form, deren Semantik feststeht: `agg: sum` ueber einen Ausdruck, der je
    Zeile 1 oder 0 liefert. Summe von Einsen ist eine Zeilenzahl — das gilt unabhaengig davon, was
    MetricFlow von `count` verlangt. Wird die Quelle erreichbar, ist dies die Stelle zum Nachziehen.
    """
    if not f:
        return "1"
    sp = f["sap_field"]
    wert = f.get("value")
    pred = {"not_empty": f"{sp} <> ''", "empty": f"{sp} = ''",
            "equals": f"{sp} = '{wert}'", "not_equals": f"{sp} <> '{wert}'"}.get(f.get("op", ""), "")
    return f"CASE WHEN {pred} THEN 1 ELSE 0 END" if pred else "1"


def _count_entry(cm: dict, contract_ref: str) -> dict[str, Any]:
    f = cm.get("filter")
    desc = f"governed row count (Contract: {contract_ref})"
    if f and f.get("why"):
        desc += f" — {f['why']}"
    return {"name": cm["name"], "agg": "sum", "expr": _count_expr(f), "description": desc,
            "meta": {"additivity": "flow", "grain": "row count"}}


def _semantic_model(name: str, kind: str, contract_ref: str, columns: list[str],
                    measure_cols: set[str] | None = None,
                    balance_cols: set[str] | None = None,
                    count_measures: list[dict] | None = None) -> dict[str, Any]:
    model = f"gold_{_ident(name)}"
    entities = [{"name": f"{_ident(name)}_key", "type": "primary"}]
    mcols = set(measure_cols or ())
    bcols = set(balance_cols or ())
    dim_cols = [c for c in columns if c not in mcols]        # measure columns are NOT dimensions
    if dim_cols:
        dimensions = [{"name": c, "type": "categorical"} for c in dim_cols]
    else:
        dimensions = [{"name": "<dimension>", "type": "categorical",
                       "description": f"TODO(contract:{contract_ref}): conformed dimensions"}]
    sm: dict[str, Any] = {
        "name": _ident(name),
        "description": f"gold {kind} '{name}' (Contract: {contract_ref})",
        "model": f"ref('{model}')",
        "entities": entities,
        "dimensions": dimensions,
    }
    zaehl = sorted(count_measures or [], key=lambda c: c.get("name", ""))
    if mcols or zaehl:                                      # real governed measures (agg default sum)
        sm["measures"] = ([_measure_entry(c, contract_ref, c in bcols) for c in sorted(mcols)]
                          + [_count_entry(c, contract_ref) for c in zaehl if c.get("name")])
    elif kind in ("fact", "aggregate"):                    # IR-only skeleton (no catalog)
        sm["measures"] = [{"name": f"{_ident(name)}_amount", "agg": "sum",
                           "description": f"TODO(contract:{contract_ref}): additive measures"}]
    return sm


def _metrics_from_catalog(gc: dict | None) -> list[dict[str, Any]]:
    """Governed measures → dbt metrics (Golden-Thread: reference the KPI, carry its id in ``meta``).

    A plain governed measure → a ``simple`` metric. A **composite** measure (one carrying
    ``derived_from`` = ``{op, measures:[base metric names], expr}`` — e.g. gross margin = net_sales −
    cogs, or DSO = receivables / (net_sales / 365)) → a real MetricFlow ``derived`` metric with an
    ``expr`` over its base metrics. Base metrics that have no governed KPI of their own (e.g. an
    intermediate like ``receivables``) are emitted as auxiliary ``simple`` metrics so the derived
    metric's references resolve."""
    measures = sorted((gc or {}).get("measures", []) or [], key=lambda x: x.get("measure_name", ""))
    simple: dict[str, dict[str, Any]] = {}
    derived: list[tuple[dict, str]] = []
    for m in measures:
        mname = _ident(m.get("measure_name", ""))
        if not mname:
            continue
        if m.get("derived_from"):
            derived.append((m, mname))
            continue
        simple[mname] = {"name": mname, "label": m.get("measure_name", ""), "type": "simple",
                         "type_params": {"measure": mname}, "meta": {"kpi_id": m.get("kpi_id", "")}}

    metrics: list[dict[str, Any]] = list(simple.values())
    for m, mname in derived:
        df = m["derived_from"]
        for base in df.get("measures", []):        # auxiliary simple metric per ungoverned operand
            if base not in simple:
                aux = {"name": base, "label": base, "type": "simple", "type_params": {"measure": base},
                       "meta": {"kpi_id": "intermediate (no governed KPI)"}}
                simple[base] = aux
                metrics.append(aux)
        metrics.append({
            "name": mname, "label": m.get("measure_name", ""), "type": "derived",
            "type_params": {"expr": df.get("expr", ""),
                            "metrics": [{"name": b} for b in df.get("measures", [])]},
            "meta": {"kpi_id": m.get("kpi_id", "")},
        })
    return metrics


def emit_metricflow(blueprint: dict, governed_catalog: dict | None = None) -> dict[str, str]:
    """Return the dbt Semantic Layer bridge as ``path → content`` (semantic_models.yml + metrics.yml)."""
    med = blueprint.get("medallion", {})
    contract_ref = med.get("silver", {}).get("data_contract_ref", "<silver-contract>")
    kinds = _gold_kinds(blueprint)
    cols_by_table = _catalog_columns_by_table(governed_catalog)
    measure_cols_by_fact = _measure_columns_by_fact(governed_catalog)
    balance_by_fact = {_ident(t.get("name", "")): set(t.get("balance_measures") or [])
                       for t in (governed_catalog or {}).get("tables", []) or []}
    counts_by_fact = _count_measures_by_fact(governed_catalog)

    semantic_models: list[dict[str, Any]] = []
    for d in sorted(blueprint.get("mesh", {}).get("domains", []), key=lambda d: d.get("name", "")):
        for product in sorted(d.get("data_products", [])):
            kind = kinds.get(product, "fact")
            columns = _fuer_produkt(cols_by_table, product) or []
            measure_cols = _fuer_produkt(measure_cols_by_fact, product) or set()
            balance_cols = _fuer_produkt(balance_by_fact, product) or set()
            zaehl = _fuer_produkt(counts_by_fact, product) or []
            semantic_models.append(_semantic_model(product, kind, contract_ref, columns,
                                                   measure_cols, balance_cols, zaehl))

    # metrics: real ones from the governed catalog; else one skeleton per fact (Golden-Thread honest).
    metrics = _metrics_from_catalog(governed_catalog)
    if not metrics:
        for sm in semantic_models:
            if "measures" in sm:
                metrics.append({"name": f"total_{sm['name']}", "label": f"Total {sm['name']}",
                                "type": "simple", "type_params": {"measure": sm["measures"][0]["name"]},
                                "meta": {"kpi_id": f"TODO(contract:{contract_ref})"}})

    grounded = "governed catalog" if governed_catalog else "IR skeleton (no catalog → TODO markers)"
    doc = ["# dbt Semantic Layer bridge (generated — MetricFlow / idea #3)", "",
           f"IR gold → dbt `semantic_models`; governed measures → dbt `metrics`. Grounding: **{grounded}**.",
           "", "**Golden-Thread**: metrics *reference* the governed KPI definitions (their `kpi_id` in "
           "`meta`), never re-define meaning. Bridges ODCS ↔ MetricFlow ↔ Direct-Lake over the neutral IR.",
           "", f"Semantic models: **{len(semantic_models)}**  ·  Metrics: **{len(metrics)}**", ""]
    return {
        "metricflow/semantic_models.yml": yaml.safe_dump(
            {"semantic_models": semantic_models}, sort_keys=False, allow_unicode=True),
        "metricflow/metrics.yml": yaml.safe_dump({"metrics": metrics}, sort_keys=False, allow_unicode=True),
        "metricflow/_METRICFLOW.md": "\n".join(doc) + "\n",
    }
