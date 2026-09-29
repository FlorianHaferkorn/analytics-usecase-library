"""provision_dq — ingress DQ gates from the introspected source schema.

``provision_transforms.emit_dq_gates`` is already the one DQ surface in this repo (dbt
``schema.yml`` tests per gold product) and takes a ``column_tests`` supplier. So far it had
exactly one supplier: the SAP standard pack, which knows real keys and FKs. Every other
customer got the honest ``TODO(contract:…)`` placeholder, because the plain IR does not know
business columns.

The source-schema reader changed that — it now returns real columns, real nullability and
key/watermark candidates. This module is **supplier number two**, not a second DQ engine.

**Why ingress and not gold.** What introspection describes is the *source* (`dbo.Orders`),
not the gold product (`fact_orders`). Nothing in the IR records which source table becomes
which gold product, and mapping `Orders → fact_orders` by name similarity is the same guess
this Baukasten refuses elsewhere. Source knowledge therefore lands where it is actually
about: the **ingress** — does what arrived still match what the source declared? That is a
different and equally missing gate: today a source can silently drop a column or start
sending NULLs in a mandatory field, and nothing notices until a report looks wrong.

**What is factual vs proposed.** Nullability comes from the source catalogue and is a fact,
so ``not_null`` tests are emitted. Keys are *candidates* — `INFORMATION_SCHEMA.COLUMNS`
carries no key information — so a ``unique`` test is emitted only for a **confirmed** key.
An unconfirmed candidate becomes ``TODO(confirm:…)``: a uniqueness test on a guessed key
either passes meaninglessly or blocks a pipeline on a guess, and neither is worth having.

Finally this consumes ``medallion.silver.quality_threshold`` — a field the IR has always
declared and no emitter has ever read.

**Supplier number three** (ALUCA-Ledger A-20, 29.09.2026) lives at the end of this module: the
data contract's own ``column_specs`` (governed catalog) → dbt column tests for ``emit_dq_gates``
and ``CHECK`` constraints for ``emit_mlv`` — translated here, once, not in a second DQ engine.
"""
from __future__ import annotations

from typing import Any

import yaml

from core.dataarch_engine.blueprint.source_schema import key_candidates, watermark_candidates

# Share of rows that must pass for silver to accept a load, when the IR says nothing.
_DEFAULT_THRESHOLD = 1.0


def quality_threshold(bp: dict[str, Any]) -> float:
    """The silver acceptance threshold from the IR, defaulting to "everything must pass".

    Defaulting to 1.0 rather than a lenient value is deliberate: a threshold nobody set
    should not silently permit bad rows.
    """
    raw = bp.get("medallion", {}).get("silver", {}).get("quality_threshold")
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return _DEFAULT_THRESHOLD
    return value if 0.0 <= value <= 1.0 else _DEFAULT_THRESHOLD


def ingress_tests(schema_objects: list[dict[str, Any]],
                  confirmed_keys: dict[str, list[str]] | None = None) -> dict[str, list[dict]]:
    """``{table → [dbt column-test dicts]}`` from an introspected source schema.

    Factual tests only. ``confirmed_keys`` maps a table to the key columns someone actually
    confirmed; only those get ``unique``.
    """
    confirmed_keys = confirmed_keys or {}
    out: dict[str, list[dict]] = {}

    for obj in schema_objects:
        table = str(obj.get("name") or "")
        if not table:
            continue
        confirmed = list(confirmed_keys.get(table) or [])
        columns: list[dict[str, Any]] = []

        for prop in obj.get("properties") or []:
            name = str(prop.get("name") or "")
            if not name:
                continue
            tests: list[Any] = []
            # NOT NULL in the source catalogue is a fact, not an inference.
            if prop.get("required") is True:
                tests.append("not_null")
            if name in confirmed:
                # Only a single-column confirmed key can carry `unique` without dbt_utils;
                # a composite key needs unique_combination_of_columns, kept out to stay
                # tool-free (same boundary emit_dq_gates already documents).
                if len(confirmed) == 1:
                    tests.append("unique")
            if tests:
                columns.append({"name": name, "data_tests": tests})

        proposals = [k for k in key_candidates(obj) if k not in confirmed]
        if proposals:
            columns.append({
                "name": f"TODO(confirm:key)",
                "description": "Key candidates from column naming, unconfirmed: "
                               + ", ".join(proposals)
                               + ". A uniqueness test on a guessed key either passes "
                                 "meaninglessly or blocks the pipeline on a guess — confirm "
                                 "the key, then re-emit.",
            })

        if columns:
            out[table] = columns
    return out


def freshness_proposals(schema_objects: list[dict[str, Any]]) -> dict[str, list[str]]:
    """``{table → watermark candidates}`` — the basis for a freshness gate, unconfirmed.

    dbt's ``source freshness`` needs a ``loaded_at_field``; no catalogue says which timestamp
    that is, so this stays a proposal rather than an emitted check.
    """
    out = {}
    for obj in schema_objects:
        table = str(obj.get("name") or "")
        candidates = watermark_candidates(obj)
        if table and candidates:
            out[table] = candidates
    return out


def _readme(source: str, tests: dict[str, list[dict]],
            freshness: dict[str, list[str]], threshold: float) -> str:
    factual = sum(
        1 for cols in tests.values() for c in cols
        if not str(c["name"]).startswith("TODO(")
    )
    open_keys = sum(
        1 for cols in tests.values() for c in cols
        if str(c["name"]).startswith("TODO(")
    )

    lines = [
        f"# Ingress DQ gates — `{source}`",
        "",
        "Does what arrived still match what the source declared? Today a source can silently",
        "drop a column or start sending NULLs in a mandatory field, and nothing notices until",
        "a report looks wrong.",
        "",
        "These tests are generated from the source's own catalogue (`INFORMATION_SCHEMA` /",
        "OpenAPI) — so they assert what the source *promised*, not what we assumed.",
        "",
        "## What is emitted, and what is not",
        "",
        f"- **{factual} factual test(s)** — `not_null` where the source declares NOT NULL, and",
        "  `unique` only where a key was **confirmed**.",
        f"- **{open_keys} table(s) with unconfirmed key candidates** — emitted as",
        "  `TODO(confirm:key)`. `INFORMATION_SCHEMA.COLUMNS` carries no key information, and a",
        "  uniqueness test on a guessed key either passes meaninglessly or blocks a pipeline on",
        "  a guess.",
        "",
        "## Silver acceptance threshold",
        "",
        f"`medallion.silver.quality_threshold` = **{threshold:.2%}** of rows must pass.",
    ]
    if threshold == _DEFAULT_THRESHOLD:
        lines.append("")
        lines.append("This is the default — the IR did not set one. Defaulting to *everything must")
        lines.append("pass* is deliberate: a threshold nobody chose should not silently admit bad rows.")

    if freshness:
        lines += [
            "",
            "## Freshness (proposed, not emitted)",
            "",
            "dbt's `source freshness` needs a `loaded_at_field`. No catalogue says which timestamp",
            "that is, so these stay proposals:",
            "",
        ]
        lines += [f"- `{t}`: {', '.join(f'`{c}`' for c in cols)}" for t, cols in sorted(freshness.items())]

    lines += [
        "",
        "## Relationship to the gold gates",
        "",
        "This is the **ingress** half. Per-gold-product tests live in `dq/` "
        "(`provision_transforms.emit_dq_gates`) — one DQ surface, two suppliers: the SAP standard",
        "pack and this one. Source knowledge deliberately does not become gold tests: nothing in",
        "the IR records which source table becomes which gold product, and mapping them by name",
        "similarity would be a guess.",
    ]
    return "\n".join(lines) + "\n"


def emit_ingress_dq(bp: dict[str, Any],
                    schemas_by_source: dict[str, list[dict[str, Any]]],
                    confirmed_keys: dict[str, dict[str, list[str]]] | None = None
                    ) -> dict[str, str]:
    """Return the ingress-DQ artifact set (path → content).

    ``schemas_by_source`` maps a source name to its introspected schema objects (what
    ``source_schema.from_information_schema`` / ``from_openapi`` return). Sources that were
    never introspected are simply absent — they get no invented tests.
    """
    if not schemas_by_source:
        return {}

    confirmed_keys = confirmed_keys or {}
    threshold = quality_threshold(bp)
    out: dict[str, str] = {}
    covered: list[str] = []

    for source in sorted(schemas_by_source):
        objects = schemas_by_source[source] or []
        tests = ingress_tests(objects, confirmed_keys.get(source))
        if not tests:
            continue
        models = [{"name": table, "columns": cols} for table, cols in sorted(tests.items())]
        out[f"dq_ingress/{source}/schema.yml"] = yaml.safe_dump(
            {"version": 2, "models": models}, sort_keys=False, allow_unicode=True
        )
        out[f"dq_ingress/{source}/_INGRESS_DQ.md"] = _readme(
            source, tests, freshness_proposals(objects), threshold
        )
        covered.append(source)

    if not covered:
        return {}

    declared = sorted(str(e.get("source")) for e in bp.get("ingestion", []) or [] if e.get("source"))
    missing = [s for s in declared if s not in covered]
    index = [
        "# Ingress DQ gates",
        "",
        f"{len(covered)} of {len(declared)} declared source(s) have ingress tests.",
        "",
    ]
    index += [f"- `{s}` → `dq_ingress/{s}/schema.yml`" for s in covered]
    if missing:
        index += [
            "",
            "## Without ingress tests",
            "",
            "These sources were never introspected, so there is nothing factual to assert about",
            "them. No tests are invented for them:",
            "",
        ]
        index += [f"- `{s}`" for s in missing]
        index += ["", "Run their introspection query (`source_schema/queries/`) and re-emit."]
    out["dq_ingress/_INDEX.md"] = "\n".join(index) + "\n"
    return out


# ═══════════════════════════════════════════════════════════════════════════════════════════
# Lieferant 3: der Datenvertrag selbst (`column_specs` im governed catalog, ALUCA-Ledger A-20)
# ═══════════════════════════════════════════════════════════════════════════════════════════
#
# ALUCAs Datenvertraege tragen seit A-20 strukturierte Pruefungen je Spalte. Sie kommen ueber
# denselben Weg wie die Spaltennamen (`meridian/governed-catalog/v1`, je Tabelle
# `column_specs: [{name, type, nullable, ref, unknown_member, checks, target_state}]`) und
# werden HIER, an einer Stelle, in die zwei Formen uebersetzt, die die vorhandenen Emitter
# schon sprechen. Kein zweiter DQ-Ausfuehrer:
#
#   * `vertrags_spaltentests`  → dbt-Spaltentests fuer `emit_dq_gates(column_tests=…)`
#     (not_null, relationships, accepted_values). Bereiche gehen NICHT nach dbt: dbt-core hat
#     keinen generischen Bereichstest, und `emit_dq_gates` bleibt bewusst ohne `dbt_utils`.
#   * `vertrags_constraints`   → `CONSTRAINT … CHECK (…) ON MISMATCH …` fuer `emit_mlv`.
#   * `pruef_praedikat`        → das SQL-Praedikat einer Pruefung; dieselbe Funktion speist
#     die MLV-Bedingung und die ODCS-`quality`-Regel (`odcs.to_odcs`), damit es genau eine
#     Uebersetzung gibt.
#
# NULL-Semantik, ausdruecklich statt dem Dialekt ueberlassen: ohne `when_present` ist NULL ein
# Verstoss, mit `when_present: true` wird nur der Nicht-NULL-Wert geprueft. Jedes Praedikat ist
# damit zweiwertig (nie NULL) — ob eine Engine ein NULL-Ergebnis als Treffer oder Verstoss
# wertet, spielt keine Rolle mehr. MS Learn nennt die NULL-Behandlung von MLV-Bedingungen
# nicht (*Data quality in materialized lake views*, abgerufen 29.09.2026).
#
# `showcase` (je Tabelle) aendert hier nichts: es beschreibt die Showcase-Abdeckung in ALUCA,
# nicht das Kundenschema. `target_state: true` heisst Zielbild — keine Pruefung, aber als
# `TODO(target_state:…)` sichtbar.

#: Vergleichsoperatoren mit einem Zahlenwert → SQL-Operator.
_VERGLEICH = {"gte": ">=", "gt": ">", "lte": "<=", "lt": "<"}
#: Spaltenvergleiche → SQL-Operator.
_SPALTENVERGLEICH = {"gte_column": ">=", "lte_column": "<="}
PRUEF_OPERATOREN = (*_VERGLEICH, "between", "in", *_SPALTENVERGLEICH)


def _spark_zitat(spalte: str) -> str:
    from core.dataarch_engine.blueprint.provision_transforms import zitiere
    return zitiere(spalte)


def _literal(wert: Any) -> str:
    """SQL-Literal. Zahlen bleiben Zahlen, alles andere wird eine Zeichenkette."""
    if isinstance(wert, bool):
        return "TRUE" if wert else "FALSE"
    if isinstance(wert, (int, float)):
        return repr(wert)
    return "'" + str(wert).replace("'", "''") + "'"


def pruef_operator(check: dict[str, Any]) -> str:
    """Der eine Operator-Schluessel einer Pruefung; ``ValueError`` bei null oder mehreren."""
    if not isinstance(check, dict):
        raise ValueError(f"Pruefung ist kein Objekt: {check!r}")
    ops = [k for k in check if k != "when_present"]
    if len(ops) != 1 or ops[0] not in PRUEF_OPERATOREN:
        raise ValueError(f"Pruefung braucht genau einen Schluessel aus {PRUEF_OPERATOREN}, "
                         f"hat {ops}")
    return ops[0]


def pruef_spalten(spalte: str, check: dict[str, Any]) -> list[str]:
    """Die Spalten, die eine Pruefung liest (die eigene, bei Spaltenvergleichen auch die andere)."""
    op = pruef_operator(check)
    return [spalte, str(check[op])] if op in _SPALTENVERGLEICH else [spalte]


def pruef_praedikat(spalte: str, check: dict[str, Any], zitat=None,
                    spalte_sql: str | None = None) -> str:
    """Das zweiwertige SQL-Praedikat einer Pruefung — WAHR heisst: die Zeile haelt.

    ``zitat`` maskiert Spaltennamen (Vorgabe: Spark-Backticks wie ``provision_transforms.zitiere``);
    ``spalte_sql`` ersetzt die gerenderte eigene Spalte (ODCS: ``{property}``).
    """
    zitat = zitat or _spark_zitat
    op = pruef_operator(check)
    wert = check[op]
    c = spalte_sql if spalte_sql is not None else zitat(spalte)
    nullbar = [c]
    if op in _VERGLEICH:
        if isinstance(wert, bool) or not isinstance(wert, (int, float)):
            raise ValueError(f"'{op}' erwartet eine Zahl, hat {wert!r}")
        kern = f"{c} {_VERGLEICH[op]} {_literal(wert)}"
    elif op == "between":
        if (not isinstance(wert, (list, tuple)) or len(wert) != 2
                or any(isinstance(w, bool) or not isinstance(w, (int, float)) for w in wert)):
            raise ValueError(f"'between' erwartet [a, b] aus Zahlen, hat {wert!r}")
        kern = f"{c} BETWEEN {_literal(wert[0])} AND {_literal(wert[1])}"
    elif op == "in":
        werte = [w for w in (wert or []) if w is not None]
        if not werte:
            raise ValueError(f"'in' erwartet eine nicht-leere Liste, hat {wert!r}")
        kern = f"{c} IN ({', '.join(_literal(w) for w in werte)})"
    else:
        if not isinstance(wert, str) or not wert:
            raise ValueError(f"'{op}' erwartet einen Spaltennamen, hat {wert!r}")
        andere = zitat(wert)
        # Vertragssemantik (ALUCA core/data_contracts/domains/README.md): ein NULL auf der
        # Vergleichsseite ist nicht auswertbar und zaehlt nicht als Verstoss — unabhaengig von
        # `when_present`, das nur die eigene Spalte betrifft.
        kern = f"({andere} IS NULL OR {c} {_SPALTENVERGLEICH[op]} {andere})"
    if check.get("when_present") is True:
        return "(" + " OR ".join(f"{n} IS NULL" for n in nullbar) + f" OR {kern})"
    return "(" + " AND ".join(f"{n} IS NOT NULL" for n in nullbar) + f" AND {kern})"


def _katalog_tabelle(governed_catalog: dict | None, name: str) -> dict:
    """Katalogeintrag zu einem Tabellen-/Produktnamen (``name`` oder ``gold_<name>``)."""
    for t in (governed_catalog or {}).get("tables") or []:
        tn = str(t.get("name") or "")
        if tn in (name, f"gold_{name}") or (tn.startswith("gold_") and tn[5:] == name):
            return t
    return {}


def ref_ziel(governed_catalog: dict | None, spalte: str, ref: str) -> tuple[str, str | None]:
    """``(Dimension, Schluesselspalte | None)`` zu einem ``ref``.

    Reihenfolge, von belegt zu hergeleitet: ausdrueckliches ``dim.spalte`` → der deklarierte
    einspaltige ``key`` der Dimension → dieselbe Spalte gibt es in der Dimension (ALUCA-
    Konvention ``DateKey`` → ``dim_date.DateKey``). Sonst ``None``: kein erfundenes Ziel.
    """
    ref = str(ref or "")
    tabelle, _, feld = ref.partition(".")
    dim = _katalog_tabelle(governed_catalog, tabelle)
    if feld:
        return tabelle, feld
    key = [k for k in (dim.get("key") or []) if k]
    if len(key) == 1:
        return tabelle, key[0]
    spalten = set(dim.get("columns") or []) | {
        s.get("name") for s in dim.get("column_specs") or [] if isinstance(s, dict)}
    return tabelle, (spalte if spalte in spalten else None)


def _gold_ident(name: str) -> str:
    from core.dataarch_engine.blueprint.provision_transforms import _ident
    return _ident(name)


def vertrags_spaltentests(governed_catalog: dict | None) -> dict[str, list[dict]]:
    """``{Tabelle → [dbt-Spaltentests]}`` aus den ``column_specs`` — Lieferant 3 fuer ``emit_dq_gates``.

    * ``nullable: false`` oder ``unknown_member`` → ``not_null`` (``unknown_member`` heisst
      „nie NULL, <wert> = unbekannt“ — dieselbe Regel wie die Schnittspalten).
    * ``ref`` → ``not_null`` bleibt Sache von ``nullable``; dazu ``relationships`` zur Dimension,
      wenn das Ziel belegbar ist (``ref_ziel``), sonst ein sichtbares TODO statt eines Ziels.
    * ``checks: [{in: …}]`` → ``accepted_values`` (ohne ``when_present`` zusaetzlich ``not_null``,
      weil dbt NULL in ``accepted_values`` durchlaesst).
    * Bereichs-/Spaltenvergleiche → kein dbt-Test (kein ``dbt_utils``), Hinweis auf ``mlv/``.
    * ``target_state: true`` → ``TODO(target_state:<spalte>)``, keine Pruefung.
    * ein unlesbarer Pruefeintrag → ``TODO(contract-check:<spalte>)`` mit dem Grund.
    Schluessel sind Katalognamen; ein ``gold_``-Praefix wird zusaetzlich ohne gefuehrt.
    """
    out: dict[str, list[dict]] = {}
    for t in (governed_catalog or {}).get("tables") or []:
        specs = [s for s in t.get("column_specs") or [] if isinstance(s, dict) and s.get("name")]
        if not specs:
            continue
        key = [k for k in (t.get("key") or []) if k]
        eintraege: list[dict] = []
        for s in specs:
            # physische Spalte: `source_column` (Vertrag trennt Modellname und Gold-Spalte), sonst name
            name = str(s.get("source_column") or s["name"])
            if s.get("target_state") is True:
                eintraege.append({"name": f"TODO(target_state:{name})",
                                  "description": "Zielbild laut Datenvertrag — noch keine Pruefung."})
                continue
            tests: list[Any] = []
            notizen: list[str] = []
            if s.get("nullable") is False or "unknown_member" in s:
                tests.append("not_null")
            if "unknown_member" in s:
                notizen.append(f"nie NULL; {s['unknown_member']!r} = unbekannt")
            if len(key) == 1 and key[0] == name:
                tests.append("unique")
            if s.get("ref"):
                dim, feld = ref_ziel(governed_catalog, name, s["ref"])
                if feld:
                    tests.append({"relationships": {"to": f"ref('gold_{_gold_ident(dim)}')",
                                                    "field": feld}})
                else:
                    notizen.append(f"TODO(contract:ref): Schluessel von '{dim}' nicht belegt — "
                                   "kein relationships-Test")
            for check in s.get("checks") or []:
                try:
                    op = pruef_operator(check)
                    pruef_praedikat(name, check)             # dieselbe Validierung wie MLV
                except ValueError as e:
                    notizen.append(f"TODO(contract-check:{name}): {e}")
                    continue
                if op == "in":
                    if check.get("when_present") is not True and "not_null" not in tests:
                        tests.append("not_null")
                    tests.append({"accepted_values": {"values": list(check["in"])}})
                else:
                    notizen.append(f"{op} → MLV-Bedingung (mlv/), kein dbt-Test ohne dbt_utils")
            if tests or notizen:
                e: dict[str, Any] = {"name": name}
                if notizen:
                    e["description"] = "Datenvertrag: " + "; ".join(notizen)
                if tests:
                    e["tests"] = tests
                eintraege.append(e)
        if eintraege:
            tn = str(t.get("name"))
            out[tn] = eintraege
            if tn.startswith("gold_"):
                out.setdefault(tn[5:], eintraege)
    return out


def katalog_kanten(governed_catalog: dict | None,
                   quellen: tuple[str, ...] = ("relationships",)) -> list[dict[str, Any]]:
    """Die Sternkanten, die der governte Katalog **ausdruecklich** fuehrt — an einer Stelle.

    Je Kante ``{from_table, from_column, to_table, to_column, aktiv}``. Nur Kanten, deren beide
    Seiten als echte Spalten im Katalog stehen; Selbstbezug und Dubletten fallen weg, und je
    Tabellenpaar ist genau eine Kante aktiv (Power BI kennt nur einen aktiven Pfad). Nichts wird
    geraten: eine Kante mit fehlender Seite faellt stillschweigend heraus.

    Bis 29.09.2026 stand diese Regel nur in ``sap_tmdl._rels_from_catalog``. Die DQ-Tore
    brauchen sie auch (W5.11), aber ``provision_dq`` ist nach ALUCA gespiegelt und darf
    ``sap_tmdl`` nicht importieren (D-541). Deshalb liegt sie hier, und ``sap_tmdl`` liest
    sie von hier — eine Regel, zwei Leser.

    ``quellen`` — welche Katalogfelder gelesen werden: ``relationships`` (deklariert, auch die
    Kalenderkanten) und/oder ``fremdschluessel`` (SAP-Sternkanten, D-559).
    """
    gc = governed_catalog or {}
    cols = {t.get("name"): set(t.get("columns") or []) for t in gc.get("tables") or []}
    roh = [r for q in quellen for r in (gc.get(q) or []) if isinstance(r, dict)]
    out: list[dict[str, Any]] = []
    gesehen: set[tuple] = set()
    aktive_paare: set[tuple[str, str]] = set()
    for r in sorted(roh, key=lambda r: (str(r.get("from_table")), str(r.get("from_column")),
                                        str(r.get("to_table")), str(r.get("to_column")))):
        ft, fc, tt, tc = (r.get("from_table"), r.get("from_column"), r.get("to_table"),
                          r.get("to_column"))
        if not all((ft, fc, tt, tc)) or ft == tt:
            continue
        if ft not in cols or fc not in cols[ft] or tc not in cols.get(tt, set()):
            continue
        k = (ft, fc, tt, tc)
        if k in gesehen:
            continue
        gesehen.add(k)
        out.append({"from_table": ft, "from_column": fc, "to_table": tt, "to_column": tc,
                    "aktiv": (ft, tt) not in aktive_paare})
        aktive_paare.add((ft, tt))
    return out


def beziehungs_spaltentests(governed_catalog: dict | None,
                            basis: dict[str, list[dict]] | None = None,
                            modelle: set[str] | None = None) -> dict[str, list[dict]]:
    """dbt-``relationships``-Tests aus den Sternkanten des Katalogs — fuer **jeden** Blueprint (W5.11).

    Gemessen 29.09.2026: ``emit_dq_gates`` schrieb fuer ein Faktum ohne SAP-Paket nur
    ``not_null`` auf den Platzhalter ``<dimension_foreign_key>``, obwohl der Katalog die Kanten
    kannte. Ein echter ``relationships``-Test entstand allein im SAP-Pfad (``sap_dq``). Dieser
    Lieferant liest dieselben Kanten (``katalog_kanten``: ``relationships`` + ``fremdschluessel``)
    und schreibt je Fremdschluessel ``not_null`` + ``relationships`` in derselben Form wie
    ``sap_dq`` — dieselbe DQ-Flaeche, kein zweites Silo.

    ``basis`` — die Tests anderer Lieferanten (z. B. ``vertrags_spaltentests``); sie werden
    zusammengefuehrt, nicht ersetzt: eine Spalte mit Vertragstests bekommt den Beziehungstest
    dazu, sofern sie noch keinen hat. ``modelle`` — die Gold-Produkte, die in dieser Lieferung
    dbt-Modelle sind. Zeigt eine Kante auf eine Tabelle ausserhalb, entsteht **kein** Test auf
    ein Modell, das es nicht gibt (dbt bricht sonst beim Kompilieren ab), sondern ein
    sichtbarer Hinweis an der Spalte.
    """
    out: dict[str, list[dict]] = {k: [dict(e) for e in v] for k, v in (basis or {}).items()}
    for k in katalog_kanten(governed_catalog, ("relationships", "fremdschluessel")):
        ft, fc, tt, tc = k["from_table"], k["from_column"], k["to_table"], k["to_column"]
        ziel_ok = modelle is None or tt in modelle or _gold_ident(tt) in {
            _gold_ident(m) for m in modelle}
        eintraege = out.setdefault(ft, [])
        e = next((x for x in eintraege if x.get("name") == fc), None)
        if e is None:
            e = {"name": fc, "description": f"FK -> {tt}"}
            eintraege.append(e)
        tests = list(e.get("tests") or [])
        if not ziel_ok:
            hinweis = (f"TODO(relationships): Ziel '{tt}' ist kein dbt-Modell dieser "
                       "Lieferung — kein relationships-Test")
            e["description"] = "; ".join(x for x in (e.get("description"), hinweis) if x)
            continue
        if "not_null" not in tests:
            tests.insert(0, "not_null")
        if not any(isinstance(t, dict) and "relationships" in t for t in tests):
            tests.append({"relationships": {"to": f"ref('gold_{_gold_ident(tt)}')",
                                            "field": tc}})
        e["tests"] = tests
    return {k: v for k, v in out.items() if v}


def vertrags_constraints(table: dict | None, produkt_ident: str, aktion: str,
                         spalten: list[str] | None = None) -> tuple[list[str], list[str]]:
    """``(CONSTRAINT-Zeilen, TODO-Kommentare)`` fuer eine MLV aus den ``column_specs`` ihrer Tabelle.

    Syntax nach MS Learn *Spark SQL reference for materialized lake views* und *Data quality in
    materialized lake views* (abgerufen 29.09.2026): ``CONSTRAINT <name> CHECK (<bool>) ON
    MISMATCH DROP|FAIL``, mehrere Bedingungen erlaubt; ohne Angabe gilt ``FAIL``, und stehen
    DROP und FAIL in einer Sicht, gewinnt FAIL. ``aktion`` kommt deshalb vom Aufrufer (dieselbe
    Art-Politik wie die Schluesselbedingung), damit eine Sicht nicht gemischt wird.

    Eine Bedingung auf eine Spalte, die die Projektion ``spalten`` nicht fuehrt, wird nicht
    aktiv geschrieben — MLV_CONSTRAINT_SCHEMA_VIOLATION war genau dieser Fehler (13.08.2026).
    """
    zeilen: list[str] = []
    offen: list[str] = []
    vergeben: set[str] = set()
    projektion = set(spalten or [])
    for s in (table or {}).get("column_specs") or []:
        if not isinstance(s, dict) or not s.get("name"):
            continue
        name = str(s.get("source_column") or s["name"])   # physische Spalte, s. o.
        checks = s.get("checks") or []
        if s.get("target_state") is True:
            if checks:
                offen.append(f"-- TODO(target_state:{name}): {len(checks)} Pruefung(en) im Zielbild, "
                             "noch nicht aktiv.")
            continue
        for check in checks:
            try:
                op = pruef_operator(check)
                praedikat = pruef_praedikat(name, check)
            except ValueError as e:
                offen.append(f"-- TODO(contract-check:{name}): {e}")
                continue
            fehlt = [c for c in pruef_spalten(name, check) if projektion and c not in projektion]
            if fehlt:
                offen.append(f"-- TODO(contract-check:{name}): {op} liest {', '.join(fehlt)} — "
                             f"nicht in der Projektion, Bedingung nicht aktiv: CHECK {praedikat}")
                continue
            basis = f"{produkt_ident}_{_gold_ident(name) or 'spalte'}_{op}"
            cname, n = basis, 2
            while cname in vergeben:
                cname, n = f"{basis}_{n}", n + 1
            vergeben.add(cname)
            zeilen.append(f"    CONSTRAINT {cname} CHECK {praedikat} ON MISMATCH {aktion}")
    return zeilen, offen
