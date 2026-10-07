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


def _vorzeichen_expr(col: str, sb: dict | None) -> str:
    """Die Spalte mit Vorzeichen je Zeile (D-674): zeilenweises SQL, in einem Mass-`expr` ausdrueckbar."""
    if not sb:
        return col
    neg = ", ".join(f"'{w}'" for w in sb["negative"])
    aus = ", ".join(f"'{w}'" for w in sb.get("exclude") or [])
    return (f"CASE WHEN {sb['sap_field']} IN ({neg}) THEN -{col} "
            + (f"WHEN {sb['sap_field']} IN ({aus}) THEN 0 " if aus else "") + f"ELSE {col} END")


def _measure_entry(col: str, contract_ref: str, is_balance: bool,
                   filt: dict | None = None, vorzeichen: dict | None = None) -> dict[str, Any] | None:
    """A semantic-model measure. Balances carry ``meta.additivity: balance`` + a semi-additive note —
    honest signalling: a balance is additive across non-time dimensions but NOT over time. A proper
    ``non_additive_dimension`` needs the as-of/posting date column, which is a per-system modelling
    choice (facts here often don't project one), so it is flagged rather than guessed.

    Traegt das Mass einen Filter (D-345), summiert es nur die Zeilen, die ihn erfuellen — dieselbe
    `CASE WHEN`-Form wie die Zaehlung, nur ueber der Spalte statt ueber 1. Ist der Filter zeilenweise
    **nicht** ausdrueckbar, gibt die Funktion `None` zurueck: die volle Summe unter dem Namen der
    eingeschraenkten waere in jeder Anzeige richtig und in jeder Zahl falsch.
    """
    if filt and not _sql_pred(filt):
        return None
    desc = f"governed measure (Contract: {contract_ref})"
    if is_balance:
        desc += (" — BALANCE / semi-additive: additive across non-time dimensions, NOT over time; "
                 "set a non_additive_dimension on the as-of/posting date per system.")
    if filt:
        desc += f" — nur Zeilen mit {_sql_pred(filt)}: {filt.get('why') or 'gefiltert'}"
    eintrag: dict[str, Any] = {"name": col, "agg": "sum", "description": desc,
                               "meta": {"additivity": "balance" if is_balance else "flow"}}
    wert = _vorzeichen_expr(col, vorzeichen)
    if filt:
        eintrag["expr"] = f"CASE WHEN {_sql_pred(filt)} THEN {wert} ELSE 0 END"
        eintrag["meta"]["filter"] = _sql_pred(filt)
    elif vorzeichen:
        eintrag["expr"] = wert
    if vorzeichen:
        eintrag["meta"]["vorzeichen"] = vorzeichen.get("why") or vorzeichen["sap_field"]
    return eintrag


def _nicht_ausdrueckbar(measure_filters: dict | None) -> set[str]:
    """Die Masse einer Tabelle, deren Filter zeilenweise nicht darstellbar ist (D-345).

    Ein Stichtagsfilter braucht den Filterkontext und eine zweite Tabelle; ein Mass-`expr` in
    MetricFlow hat beides nicht. Solche Masse fallen hier heraus — samt der Metrik, die sie
    referenziert, sonst zeigt die Metrik auf ein Mass, das es in der Datei nicht gibt.
    """
    return {c for c, f in (measure_filters or {}).items() if f and not _sql_pred(f)}


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
    pred = _sql_pred(f)
    return f"CASE WHEN {pred} THEN 1 ELSE 0 END" if pred else "1"


def _sql_pred(f: dict | None) -> str:
    """Der Filter eines Masses als zeilenweises SQL-Praedikat. Leer, wenn keiner oder unbekannt.

    Ein Mass-`expr` in MetricFlow ist zeilenweises SQL gegen das eigene Modell. Alles, was den
    Filterkontext oder eine zweite Tabelle braucht, ist hier deshalb **nicht** ausdrueckbar und darf
    auch nicht genaehert werden (D-345).
    """
    if not f:
        return ""
    sp = f["sap_field"]
    wert = f.get("value")
    if f.get("op") in ("not_empty", "empty"):
        sp = f"TRIM({sp})"          # Leerzeichen-Kennzeichen zaehlt als leer (02.10.2026, wie DAX)
    if f.get("op") == "in_list":
        # Wert in Liste (D-676): ausdrueckbar, sobald die Liste aufgeloest ist; ein offener Kundenwert
        # ist hier leer, und das Mass faellt heraus wie ein nicht ausdrueckbarer Filter.
        return f"{sp} IN ({', '.join(repr(str(w)) for w in f['values'])})" if f.get("values") else ""
    return {"not_empty": f"{sp} <> ''", "empty": f"{sp} = ''",
            "equals": f"{sp} = '{wert}'", "not_equals": f"{sp} <> '{wert}'"}.get(f.get("op", ""), "")


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
                    count_measures: list[dict] | None = None,
                    measure_filters: dict | None = None,
                    ohne: set[str] | None = None,
                    vorzeichen: dict | None = None) -> dict[str, Any]:
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
    # Eine Zaehlung mit nicht ausdrueckbarem Filter (Zugehoerigkeit, D-666) faellt heraus: `1` statt
    # des Praedikats zaehlte jede Zeile.
    zaehl = sorted((c for c in count_measures or [] if not c.get("filter") or _sql_pred(c["filter"])),
                   key=lambda c: c.get("name", ""))
    mf = measure_filters or {}
    vz = vorzeichen or {}
    gefiltert = [e for e in (_measure_entry(c, contract_ref, c in bcols, mf.get(c), vz.get(c))
                             for c in sorted(mcols - set(ohne or ()))) if e is not None]
    if gefiltert or zaehl:                                  # real governed measures (agg default sum)
        sm["measures"] = gefiltert + [_count_entry(c, contract_ref) for c in zaehl if c.get("name")]
    elif not mcols and kind in ("fact", "aggregate"):      # IR-only skeleton (no catalog)
        sm["measures"] = [{"name": f"{_ident(name)}_amount", "agg": "sum",
                           "description": f"TODO(contract:{contract_ref}): additive measures"}]
    # Kein Geruest, wenn der Katalog Masse kannte und alle an einem nicht ausdrueckbaren Filter
    # ausgefallen sind (D-345): ein TODO-Mass behauptete dort einen fehlenden Katalog, und der Grund
    # waere genau der Filter, den wir bewusst nicht naehern.
    return sm


def _liest_ausgelassene_spalte(m: dict, fehlt: set[str]) -> bool:
    """Ob eine Metrik auf eine ausgelassene Gold-Spalte zeigt.

    Der Name des Semantikmodell-Masses ist die **Spalte**, der Name der Metrik ist das bereinigte
    `measure_name`. Im Regelfall sind beide gleich (`_gold_measure_column` bildet die Spalte aus dem
    Massnamen), aber verlassen darf man sich darauf nicht: faellt die Spalte weg und die Metrik nicht,
    zeigt ein `type: simple` auf ein Mass, das die Datei nicht enthaelt. Die Lineage sagt es genau.
    """
    return any(ref.split(".", 1)[1] in fehlt for ref in (m.get("lineage") or []) if "." in ref)


def _metrics_from_catalog(gc: dict | None, ohne: set[str] | None = None) -> list[dict[str, Any]]:
    """Governed measures → dbt metrics (Golden-Thread: reference the KPI, carry its id in ``meta``).

    A plain governed measure → a ``simple`` metric. A **composite** measure (one carrying
    ``derived_from`` = ``{op, measures:[base metric names], expr}`` — e.g. gross margin = net_sales −
    cogs, or DSO = receivables / (net_sales / 365)) → a real MetricFlow ``derived`` metric with an
    ``expr`` over its base metrics. Base metrics that have no governed KPI of their own (e.g. an
    intermediate like ``receivables``) are emitted as auxiliary ``simple`` metrics so the derived
    metric's references resolve.

    ``ohne`` nennt die Masse, die die Semantikmodelle nicht emittiert haben (D-345, zeilenweise nicht
    ausdrueckbarer Filter). Deren Metriken fallen mit — eine Metrik auf ein Mass, das die Datei nicht
    enthaelt, ist kein Hinweis auf die Luecke, sondern ein Ladefehler."""
    fehlt = set(ohne or ())
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
        if mname in fehlt or _liest_ausgelassene_spalte(m, fehlt):
            continue
        simple[mname] = {"name": mname, "label": m.get("measure_name", ""), "type": "simple",
                         "type_params": {"measure": mname}, "meta": {"kpi_id": m.get("kpi_id", "")}}

    metrics: list[dict[str, Any]] = list(simple.values())
    abgeleitet = {mname for _m, mname in derived}
    # Kennzahlverweise (D-664): eine Ableitung faellt, wenn eine Zielkennzahl fehlt — auch eine
    # abgeleitete, die selbst gefallen ist. Bis zum Fixpunkt, weil Verweise sich ketten.
    # Eine Seite auf Jahresbasis (D-675, Monatsmittel mal 12) ist kein Ausdruck ueber Metriken; sie
    # faellt von Anfang an, und mit ihr, was auf sie verweist (CCC auf DSO).
    gefallen: set[str] = jahresbasis_metriken(gc)
    while True:
        neu = {mname for m, mname in derived if mname not in gefallen
               and (fehlt | gefallen).intersection(m["derived_from"].get("measures", []))}
        if not neu:
            break
        gefallen |= neu
    for m, mname in derived:
        df = m["derived_from"]
        if mname in gefallen:
            continue                                # eine Komponente fehlt, das Verhaeltnis auch
        for base in df.get("measures", []):        # auxiliary simple metric per ungoverned operand
            if base not in simple and base not in abgeleitet:
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


def jahresbasis_metriken(gc: dict | None) -> set[str]:
    """Abgeleitete Kennzahlen mit einer Seite auf Jahresbasis (D-675). Ihr Nenner ist ein Mittel ueber
    Kalendermonate; ein MetricFlow-`derived`-Ausdruck rechnet ueber Metrikwerte im Abfragegrain und
    kennt diese Mittelung nicht. Genaehert wird nicht."""
    return {_ident(m.get("measure_name", "")) for m in (gc or {}).get("measures", []) or []
            if (m.get("derived_from") or {}).get("annualize")}


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
    filters_by_fact = {_ident(t.get("name", "")): dict(t.get("measure_filters") or {})
                       for t in (governed_catalog or {}).get("tables", []) or []}
    perioden_by_fact = {_ident(t.get("name", "")): set(t.get("period_averages") or {})
                        for t in (governed_catalog or {}).get("tables", []) or []}
    zeilen_by_fact = {_ident(t.get("name", "")): list(t.get("row_measures") or [])
                      for t in (governed_catalog or {}).get("tables", []) or []}
    vorzeichen_by_fact = {_ident(t.get("name", "")): dict(t.get("measure_signs") or {})
                          for t in (governed_catalog or {}).get("tables", []) or []}

    semantic_models: list[dict[str, Any]] = []
    ausgelassen: set[str] = set()                   # Masse mit nicht ausdrueckbarem Filter (D-345)
    for d in sorted(blueprint.get("mesh", {}).get("domains", []), key=lambda d: d.get("name", "")):
        for product in sorted(d.get("data_products", [])):
            kind = kinds.get(product, "fact")
            columns = _fuer_produkt(cols_by_table, product) or []
            measure_cols = _fuer_produkt(measure_cols_by_fact, product) or set()
            balance_cols = _fuer_produkt(balance_by_fact, product) or set()
            zaehl = _fuer_produkt(counts_by_fact, product) or []
            m_filter = _fuer_produkt(filters_by_fact, product) or {}
            ausgelassen |= _nicht_ausdrueckbar(m_filter)
            # Mittel ueber Perioden (D-663) und Rechnung je Zeile (D-665) sind kein `agg: sum` ueber
            # einer Spalte; MetricFlow bekommt sie nicht genaehert, sondern gar nicht.
            perioden = _fuer_produkt(perioden_by_fact, product) or set()
            ausgelassen |= perioden
            ausgelassen |= {c.get("name") for c in _fuer_produkt(zeilen_by_fact, product) or []}
            ausgelassen |= {c.get("name") for c in zaehl if c.get("filter") and not _sql_pred(c["filter"])}
            semantic_models.append(_semantic_model(product, kind, contract_ref, columns,
                                                   measure_cols, balance_cols, zaehl, m_filter,
                                                   ohne=perioden,
                                                   vorzeichen=_fuer_produkt(vorzeichen_by_fact, product)))

    # metrics: real ones from the governed catalog; else one skeleton per fact (Golden-Thread honest).
    metrics = _metrics_from_catalog(governed_catalog, ausgelassen)
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
    if ausgelassen:
        doc += ["**Nicht emittiert** (D-345): " + ", ".join(f"`{m}`" for m in sorted(ausgelassen))
                + ". Ihr Filter braucht den Filterkontext oder eine zweite Tabelle; ein Mass-`expr` "
                  "hat beides nicht. Diese Kennzahlen stehen im semantischen Modell von Power BI und "
                  "hier bewusst nirgends — eine Naeherung saehe in jeder Anzeige richtig aus.", ""]
    if jahresbasis_metriken(governed_catalog):
        doc += ["**Nicht emittiert, Jahresbasis** (D-675): "
                + ", ".join(f"`{m}`" for m in sorted(jahresbasis_metriken(governed_catalog)))
                + ". Ihr Umsatz- bzw. Wareneinsatz-Nenner ist das Monatsmittel mal 12 (ALUCA "
                  "`avgx_over_key(CalendarYearMonth) * 12`); ein `derived`-Ausdruck kennt diese Mittelung "
                  "nicht. Verweise darauf (CCC) fallen mit. Sie stehen im semantischen Modell von Power BI.", ""]
    return {
        "metricflow/semantic_models.yml": yaml.safe_dump(
            {"semantic_models": semantic_models}, sort_keys=False, allow_unicode=True),
        "metricflow/metrics.yml": yaml.safe_dump({"metrics": metrics}, sort_keys=False, allow_unicode=True),
        "metricflow/_METRICFLOW.md": "\n".join(doc) + "\n",
    }
