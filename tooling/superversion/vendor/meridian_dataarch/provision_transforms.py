"""provision_transforms — emit deterministic bronze→silver→gold transform stubs.

Third live-provisioning helper (ADR-0015 follow-up), sibling to ``provision_fabric``
and ``provision_cicd``. Materialises the *data plane*: from a blueprint it emits the
medallion transform DAG as deterministic, dialect-correct SQL scaffolds — one file per
layer hop, correct table names and medallion flow, kind-aware gold shape (fact /
dimension / aggregate).

Honest by construction: the emitter knows the *structure* (layers, domains, product
names + kinds, which sources feed which domain) from the IR, but **not** the business
logic (join keys, cleansing rules) — that lives in the silver data contract, not the
blueprint. So each transform is a real, runnable-shaped skeleton with explicit
``-- TODO(contract:<ref>)`` markers where the domain logic goes, never invented logic.

Mit einem governten Katalog steht in silver→gold die ECHTE Spaltenprojektion statt
``SELECT *``. Bis 31.07.2026 war dieser Emitter der einzige, der den Katalog nicht las,
waehrend der MLV-Emitter daneben aus demselben Katalog die Spalten auflistete — dieselbe
Lieferung mit zwei Wahrheiten. Was der Katalog nicht hergibt (Ersatzschluessel, SCD),
bleibt TODO.

It honours the medallion layers it's given: ``bronze.enabled=false`` (outsourced /
single-copy-shortcut, e.g. an Aurora single-copy layout) emits no bronze→silver hop,
only silver→gold; ``no_layer_skip`` is reflected in the emitted flow.

This module **does not execute** anything — it only emits text.
"""
from __future__ import annotations

import re

import yaml

from core.dataarch_engine.blueprint.naming import layer_ref
from core.dataarch_engine.blueprint.provision_governance import (
    UNBEKANNTES_MITGLIED,
    schnittspalten,
)
from core.dataarch_engine.blueprint.stack_capabilities import gap_doc_for

_NONWORD_RE = re.compile(r"[^a-z0-9]+")


def _dirslug(name: str) -> str:
    """Hyphenated slug for filesystem paths, e.g. 'Commercial & Sales' → 'commercial-sales'."""
    return _NONWORD_RE.sub("-", (name or "").lower()).strip("-")


def _ident(name: str) -> str:
    """SQL-safe identifier (underscores), e.g. 'commercial-sales_erp' → 'commercial_sales_erp'."""
    return _NONWORD_RE.sub("_", (name or "").lower()).strip("_")


_EINFACHER_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def zitiere(spalte: str, stack: str = "fabric") -> str:
    """Spaltenname so, dass er im Zieldialekt auch wirklich parst.

    Quellspalten heissen, wie sie heissen. Im Kundenmandant-Bestand sind das `Project Code`,
    `Cost Code & Description`, `Year - Month` -- belegt ueber `sourceColumn` in der TMDL, das
    sind keine Anzeigenamen, sondern die Spalten des SQL Servers. Ungeschuetzt in eine
    Projektion geschrieben ergibt das `SELECT Cost Code & Description, ...` und damit einen
    Syntaxfehler, den kein Dialekt verzeiht.

    Gemessen 12.08.2026 an `silver_to_gold__fact_vertrag.sql`: 37 Spalten, davon 13 mit
    Leerzeichen oder `&`. Die Datei sah vollstaendig aus und war nicht ausfuehrbar.

    Einfache Namen bleiben unangetastet -- sonst waere jede bestehende Ausgabe unnoetig
    anders, und ein Diff gegen frueher wuerde nichts mehr aussagen.
    """
    s = spalte or ""
    if _EINFACHER_NAME.match(s):
        return s
    if stack == "snowflake":
        return '"' + s.replace('"', '""') + '"'
    return "`" + s.replace("`", "``") + "`"      # fabric/databricks: Spark SQL


def _dialect(stack: str) -> dict:
    """Minimal per-stack SQL dialect knobs (fabric/databricks = Spark; snowflake = SF).

    Trägt den Stack mit: nicht jede Aussage im generierten SQL ist Syntax. Der Direct-Lake-Hinweis
    zur Serving-Schicht etwa gilt nur auf Fabric — er landete bisher als Kommentar auch in
    Snowflake-MERGEs und war dort einfach falsch (Inhalts-Paritäts-Sensor, SL-2607-3 Befund 2).
    """
    if stack == "snowflake":
        return {"ctas": "CREATE OR REPLACE TABLE", "using": "", "comment": "--", "stack": stack,
                "tblprops": ""}
    # fabric + databricks: Spark SQL over Delta
    #
    # `columnMapping` gehoert an JEDE Delta-Tabelle, die aus einer fremden Projektion entsteht.
    # Delta verbietet ' ,;{}()=' in Spaltennamen, und Quellspalten heissen nun einmal, wie sie
    # heissen -- `Project Code`, `Cost Code & Description`. Ohne die Eigenschaft scheitert das
    # CTAS, und zwar nicht an unserer Logik, sondern an der Zieltabelle.
    #
    # Gemessen 12.08.2026 an einem echten Durchlauf: 9 von 14 `bronze_to_silver` brachen mit
    # DELTA_INVALID_CHARACTERS_IN_COLUMN_NAMES ab. Die QUELLE hatte die Eigenschaft, das mit
    # `SELECT *` erzeugte Ziel nicht -- der Emitter vererbte sie nicht mit.
    return {"ctas": "CREATE OR REPLACE TABLE", "using": "\nUSING DELTA", "comment": "--",
            "stack": stack,
            "tblprops": ("\nTBLPROPERTIES ('delta.columnMapping.mode' = 'name',"
                         " 'delta.minReaderVersion' = '2', 'delta.minWriterVersion' = '5')")}


def _gold_kinds(blueprint: dict) -> dict[str, str]:
    return {p["name"]: p.get("kind", "fact")
            for p in blueprint.get("medallion", {}).get("gold", {}).get("data_products", [])}


def _sources_for_domain(blueprint: dict, domain_ident: str) -> list[str]:
    """Sources owned by a domain — by the EXPLICIT ``domain`` the IR carries.

    The old implementation matched a ``<domain-slug>_`` name prefix. That silently dropped every
    source whose name did not follow the convention (e.g. ``ppp_quelle_a_sql`` in domain
    ``PPP Project Controlling``): no bronze→silver transform was emitted and nothing warned. The IR
    now states the owner, so it is read, not guessed. The prefix match remains only as a fallback for
    IRs produced before the field existed."""
    ing = blueprint.get("ingestion", [])
    explicit = sorted(e["source"] for e in ing if _ident(e.get("domain", "")) == domain_ident)
    if explicit:
        return explicit
    if any(e.get("domain") for e in ing):      # IR carries owners → an empty result is the truth
        return []
    return sorted(e["source"] for e in ing     # legacy IR without `domain`: fall back to the prefix
                  if _ident(e.get("source", "")).startswith(domain_ident + "_"))


def unassigned_sources(blueprint: dict) -> list[str]:
    """Sources the IR cannot attribute to any domain — surfaced instead of vanishing."""
    doms = {_ident(d.get("name", "")) for d in blueprint.get("mesh", {}).get("domains", [])}
    return sorted(e.get("source", "") for e in blueprint.get("ingestion", [])
                  if _ident(e.get("domain", "")) not in doms)


def _generator_fuer(blueprint: dict, produkt: str) -> dict | None:
    """Die `generated`-Angabe dieses Gold-Produkts, sofern eine deklariert ist."""
    for p in (blueprint.get("medallion", {}).get("gold", {}).get("data_products") or []):
        if p.get("name") == produkt and p.get("generated"):
            return p["generated"]
    return None


def _silber_herkunft(governed_catalog: dict | None, d: dict) -> dict[str, list[str]]:
    """``{gold_produkt_ident: [herkunftstabelle, ...]}`` fuer die Produkte DIESER Domaene.

    Leer, wenn kein governter Katalog vorliegt oder er keine `sources` traegt -- dann bleibt es
    beim Zuschnitt je Domaene. Lieber ein grober Zuschnitt als ein geratener: ohne Katalog
    weiss niemand, welche Quelle zu welchem Produkt gehoert.
    """
    if not governed_catalog:
        return {}
    produkte = {_ident(p) for p in d.get("data_products", [])}
    raus: dict[str, list[str]] = {}
    for t in governed_catalog.get("tables") or []:
        ident = _ident(t.get("name") or "")
        quellen = [q for q in (t.get("sources") or []) if q]
        if ident in produkte and quellen:
            raus[ident] = quellen
    return raus


def _herkunft_je_domaene(blueprint: dict, governed_catalog: dict | None, d: dict,
                         domains: list[dict]) -> dict[str, list[str]]:
    """`_silber_herkunft` dieser Domaene, ohne Quellen, die laut IR einer ANDEREN gehoeren.

    Gemessen 02.09.2026 (Plan 0008, B-4): `dim_material` ist konform (Order-to-Cash und
    Inventory), und der Katalog nennt drei Herkuenfte -- `order_to_cash_mara`,
    `order_to_cash_makt`, `inventory_mm_mara`. Jede der beiden Domaenen emittierte alle drei:
    sechs `bronze_to_silver__*` fuer drei Ziele, je zwei Dateien mit demselben
    `CREATE OR REPLACE`. Die Domaene materialisiert nur, was ihr gehoert; eine Quelle ohne
    erklaerten Eigentuemer (Kataloge ohne IR-Bezug) bleibt, wo der Katalog sie nennt.
    """
    herkunft = _silber_herkunft(governed_catalog, d)
    if not herkunft:
        return herkunft
    dident = _ident(d.get("name", ""))
    eigene = set(_sources_for_domain(blueprint, dident))
    fremd = {s for od in domains if _ident(od.get("name", "")) != dident
             for s in _sources_for_domain(blueprint, _ident(od.get("name", "")))} - eigene
    raus = {p: [q for q in qs if q not in fremd] for p, qs in herkunft.items()}
    return {p: qs for p, qs in raus.items() if qs}


def _formgleich(spalten_je_quelle: dict[str, list[str]] | None) -> bool:
    """Haben alle Herkuenfte DIESELBE Spaltenmenge?

    Nur dann ist ein ``UNION ALL`` ueberhaupt wohlgeformt -- und nur dann ist die Vermutung
    plausibel, dass hier wirklich vereinigt und nicht verbunden gehoert. Zwei Tabellen mit
    identischen Spalten sind typisch dieselbe Entitaet aus zwei Ladewegen; zwei mit
    verschiedenen sind typisch Kopf und Position, und die gehoeren verbunden.
    """
    if not spalten_je_quelle or len(spalten_je_quelle) < 2:
        return True
    mengen = [frozenset(v) for v in spalten_je_quelle.values()]
    return all(m == mengen[0] for m in mengen)


def _von_klausel(silver_tbl: str | list[str]) -> str:
    """Die FROM-Quelle: eine Tabelle, oder bei n:1 ein ``UNION ALL`` ueber alle Herkuenfte.

    `UNION ALL`, nicht `UNION`: `UNION` entfernt Dubletten, und ob zwei gleiche Zeilen aus
    verschiedenen Quellen eine Dublette oder zwei echte Vorgaenge sind, entscheidet der
    Fachbereich -- nicht der Emitter. Stillschweigend zu deduplizieren waere eine Aussage
    ueber die Daten, die hier niemand treffen darf.
    """
    if isinstance(silver_tbl, str):
        return silver_tbl
    if len(silver_tbl) == 1:
        return silver_tbl[0]
    inner = "\n    UNION ALL\n".join(f"    SELECT * FROM {t}" for t in silver_tbl)
    return "(\n" + inner + "\n)"


def _ungeklaerte_zusammenfuehrung(name: str, kind: str, gold_tbl: str, dl: dict,
                                  quellen: list[str], spalten_je_quelle: dict[str, list[str]],
                                  contract_ref: str) -> str:
    """Mehrere Herkuenfte mit VERSCHIEDENER Form -- vereinigen oder verbinden ist offen.

    Gemessen 12.08.2026: `fact_vertrag` entsteht aus `con` (20 Spalten), `roc` (6) und
    `roclin` (11). Ein `UNION ALL` darueber scheitert an der Spaltenzahl -- und das ist der
    gnaedige Fall. Passten die Formen zufaellig, wuerde es durchlaufen und Vertragskoepfe
    unter Vertragspositionen schreiben: ein Ergebnis, das von einem richtigen nicht zu
    unterscheiden waere.

    Die Datei bleibt deshalb absichtlich unausfuehrbar und traegt beides bei sich: die
    ausgerichtete Vereinigung als Vorschlag und die gemeinsamen Spalten als Kandidaten fuer
    den Verbund. Was davon gilt, entscheidet der Fachbereich, nicht der Emitter.
    """
    c = dl["comment"]
    alle = sorted({s for v in spalten_je_quelle.values() for s in v})
    gemeinsam = sorted(set.intersection(*(set(v) for v in spalten_je_quelle.values())))

    zeilen = [
        f"{c} OFFEN — '{name}' ({kind}) entsteht aus {len(quellen)} Herkuenften mit",
        f"{c} VERSCHIEDENER Form. Ob hier vereinigt oder verbunden gehoert, steht nicht fest:",
        f"{c}",
    ]
    for q in quellen:
        n = len(spalten_je_quelle.get(q.split(".")[-1], []))
        zeilen.append(f"{c}   {q:<40} {n:>3} Spalte(n)")
    zeilen += [
        f"{c}",
        f"{c} Gleiche Spaltenzahl waere ein Hinweis auf dieselbe Entitaet aus zwei Ladewegen",
        f"{c} (dann: UNION). Verschiedene Spaltenzahlen sind typisch Kopf und Position",
        f"{c} (dann: JOIN ueber den gemeinsamen Schluessel).",
        f"{c}",
        f"{c} Gemeinsame Spalten — Kandidaten fuer den Verbund:",
        f"{c}   {', '.join(gemeinsam) if gemeinsam else '(keine — dann ist UNION erst recht fraglich)'}",
        f"{c}",
        f"{c} TODO(contract:{contract_ref}): entscheiden und EINE der beiden Fassungen einsetzen.",
        f"{c}",
        f"{c} (a) Vereinigung, spaltengleich ausgerichtet:",
    ]
    for q in quellen:
        eigen = set(spalten_je_quelle.get(q.split(".")[-1], []))
        proj = ", ".join(zitiere(s, dl["stack"]) if s in eigen
                         else f"NULL AS {zitiere(s, dl['stack'])}" for s in alle)
        zeilen.append(f"{c}     SELECT {proj} FROM {q}")
    zeilen += [
        f"{c}",
        f"{c} (b) Verbund ueber die gemeinsamen Spalten — Reihenfolge und Art (INNER/LEFT)",
        f"{c}     haengen daran, welche Tabelle den Kopf traegt.",
        f"{c}",
        f"{c} Absichtlich nicht ausfuehrbar: eine gruene Zeile waere hier die teuerste Antwort.",
        f"{dl['ctas']} {gold_tbl}{dl['using']} AS",
        f"SELECT * FROM <ZUSAMMENFUEHRUNG NICHT ENTSCHIEDEN: UNION ODER JOIN>",
        ";",
    ]
    return "\n".join(zeilen) + "\n"


def _domain_contract(d: dict, fallback: str) -> str:
    """Der Silber-Vertrag DIESER Domaene, sonst der globale.

    Bei mehreren Paketen in einem Lauf trug das IR nur einen Vertrag oben, und jedes generierte
    SQL verwies darauf — auch die Tabellen der anderen Domaenen. Eine falsche Referenz in einem
    Lieferartefakt ist schlimmer als keine: sie fuehrt jemanden zielsicher an die falsche Stelle.
    """
    return d.get("data_contract_ref") or fallback


def _bronze_to_silver(d: dict, src: str, silver_tbl: str, contract_ref: str, dl: dict,
                      bronze_tbl: str = "") -> str:
    bronze_tbl = bronze_tbl or f"bronze_{_ident(src)}"
    return (
        f"{dl['comment']} bronze → silver — conform + cleanse '{src}' for domain '{d['name']}'.\n"
        f"{dl['comment']} Contract: {contract_ref}\n"
        f"{dl['ctas']} {silver_tbl}{dl['using']}{dl.get('tblprops', '')} AS\n"
        f"SELECT\n"
        f"    {dl['comment']} TODO(contract:{contract_ref}): map raw columns → conformed silver schema,\n"
        f"    {dl['comment']} apply types, dedup, null/quality rules, business keys.\n"
        f"    *\n"
        f"FROM {bronze_tbl}\n"
        f"{dl['comment']} WHERE <incremental / quality predicate>\n"
        f";\n"
    )


def _erzeugt(name: str, gold_tbl: str, dl: dict, gen: dict) -> str:
    """Ein Gold-Produkt ohne Quelle, weil es keine haben KANN.

    Eine Datumsdimension entsteht aus einem Bereich, nicht aus einer Tabelle. Bisher behandelte
    der Emitter sie wie jedes andere Produkt, zeigte auf eine Silber-Tabelle, die es nicht gibt,
    und scheiterte mit TABLE_OR_VIEW_NOT_FOUND -- gemessen 12.08.2026 an `dim_datum`, wo der
    Bauplan ausdruecklich "erzeugt" sagt.

    Der Bereich ist eine Eingabe, keine Annahme. Die Vorgaben decken den ueblichen Fall ab und
    stehen im Kommentar, damit niemand raten muss, was gilt.
    """
    c = dl["comment"]
    von = (gen.get("from") or "2020-01-01").strip()
    bis = (gen.get("to") or "2035-12-31").strip()
    return (
        f"{c} ERZEUGT — '{name}' hat keine Quelle, weil es keine haben kann.\n"
        f"{c} Bereich {von} bis {bis} (aus den Eingaben, nicht geraten).\n"
        f"{c} Eine zentrale Datumsdimension ersetzt die automatischen Datumstabellen der\n"
        f"{c} Bestandsmodelle. Wird eine zweite erzeugt, ist genau das wieder da.\n"
        f"{dl['ctas']} {gold_tbl}{dl['using']}{dl.get('tblprops', '')} AS\n"
        f"SELECT\n"
        f"    CAST(datum AS DATE)                        AS datum,\n"
        f"    YEAR(datum)                                AS jahr,\n"
        f"    MONTH(datum)                               AS monat,\n"
        f"    DAY(datum)                                 AS tag,\n"
        f"    QUARTER(datum)                             AS quartal,\n"
        f"    WEEKOFYEAR(datum)                          AS kalenderwoche,\n"
        f"    DAYOFWEEK(datum)                           AS wochentag,\n"
        f"    DATE_FORMAT(datum, 'yyyy-MM')              AS jahr_monat,\n"
        f"    CASE WHEN DAYOFWEEK(datum) IN (1, 7) THEN true ELSE false END AS ist_wochenende\n"
        f"FROM (\n"
        f"    SELECT EXPLODE(SEQUENCE(DATE '{von}', DATE '{bis}', INTERVAL 1 DAY)) AS datum\n"
        f")\n"
        f";\n"
    )


def _ohne_quelle(name: str, kind: str, gold_tbl: str, dl: dict) -> str:
    """Kein Quellobjekt, keine Erzeugungsangabe -- dann sagt die Datei das, statt zu scheitern.

    Vorher zeigte so ein Produkt auf die Domaenen-Silbertabelle und brach mit
    TABLE_OR_VIEW_NOT_FOUND ab. Die Fehlermeldung nannte einen Tabellennamen und verschwieg
    die Ursache: es fehlt eine ENTSCHEIDUNG, keine Tabelle. Ein Lauf soll an der richtigen
    Stelle anhalten und den richtigen Grund nennen.
    """
    c = dl["comment"]
    return (
        f"{c} OFFEN — '{name}' ({kind}) hat weder eine zugeordnete Quelle noch eine\n"
        f"{c} Erzeugungsangabe. Das ist keine Luecke im Werkzeug, sondern eine offene\n"
        f"{c} Festlegung. Drei Moeglichkeiten, und sie sind nicht austauschbar:\n"
        f"{c}\n"
        f"{c}   1. Die Quelle fehlt in der Zuordnung  -> Zuordnungsdatei ergaenzen.\n"
        f"{c}   2. Das Produkt wird erzeugt           -> `generated` in den Eingaben setzen.\n"
        f"{c}   3. Es ist eine TEILMENGE eines Produkts, das schon eine andere Quelle hat\n"
        f"{c}      -> das ist Modellierung in Silber->Gold, keine Zuordnung.\n"
        f"{c}\n"
        f"{c} Absichtlich nicht ausfuehrbar: ein Platzhalter, der durchlaeuft, waere von\n"
        f"{c} einem richtigen Ergebnis nicht zu unterscheiden.\n"
        f"{dl['ctas']} {gold_tbl}{dl['using']} AS\n"
        f"SELECT * FROM <QUELLE ODER GENERATOR NICHT DEKLARIERT>\n"
        f";\n"
    )


def _projektion(spalte: str, table: dict | None, stack: str) -> str:
    """Eine Spalte der Gold-Projektion — mit Alias, wenn sie in Silber anders heisst.

    Massspalten tragen den **Mass**-Namen (`receivables`), Silber traegt das **SAP**-Feld (`DMBTR`);
    der Katalog fuehrt die Zuordnung als `measure_sources`. Ohne den Alias stand hier
    `SELECT receivables FROM silver_fin`, und die Anweisung lief in keinem Ziel — gemessen
    31.08.2026 gegen `pack_to_odcs_silver`, der `receivables` null mal nennt. Sichtbar wurde es
    erst, als zwei Masse dasselbe Quellfeld lasen; die Luecke war vorher schon in jeder Projektion.
    """
    quelle = ((table or {}).get("measure_sources") or {}).get(spalte)
    zitiert = zitiere(spalte, stack)
    return f"{zitiere(quelle, stack)} AS {zitiert}" if quelle and quelle != spalte else zitiert


def _silver_to_gold(name: str, kind: str, silver_tbl: str | list[str], contract_ref: str,
                    dl: dict, gold_tbl: str = "", table: dict | None = None) -> str:
    c = dl["comment"]
    gold_tbl = gold_tbl or f"gold_{_ident(name)}"
    # `silver_tbl` darf eine Liste sein: dann entsteht ein Produkt aus mehreren Herkuenften
    # (n:1) und die Quelle ist ein UNION ALL. Der Einzelfall bleibt unveraendert eine Tabelle.
    quellen = [silver_tbl] if isinstance(silver_tbl, str) else list(silver_tbl)
    silver_tbl = _von_klausel(silver_tbl)
    head = (f"{c} silver → gold — build {kind} '{name}'.\n"
            f"{c} Contract: {contract_ref}\n"
            + (f"{c} Zusammenfuehrung aus {len(quellen)} Herkuenften: "
               f"{', '.join(quellen)}.\n"
               f"{c} UNION ALL, nicht UNION — ob zwei gleiche Zeilen aus verschiedenen Quellen\n"
               f"{c} eine Dublette oder zwei Vorgaenge sind, entscheidet der Fachbereich.\n"
               if len(quellen) > 1 else "")
            + f"{dl['ctas']} {gold_tbl}{dl['using']}{dl.get('tblprops', '')} AS\n")

    # Mit governtem Katalog steht hier die ECHTE Projektion. Bis 31.07.2026 lieferte dieser
    # Emitter als einziger noch `SELECT *` plus TODO, obwohl der MLV-Emitter daneben aus demselben
    # Katalog die Spalten auflistete — dieselbe Lieferung, zwei Wahrheiten. Was der Katalog nicht
    # hergibt, bleibt TODO: die Ersatzschluessel-Vergabe und die SCD-Behandlung einer Dimension
    # sind Modellierung und stehen nicht im Paket.
    spalten = sorted(set((table or {}).get("columns") or []))
    if spalten:
        schluessel = [k for k in ((table or {}).get("key") or []) if k in spalten]
        grain = (table or {}).get("grain") or ""
        wort = "Spalte" if len(spalten) == 1 else "Spalten"
        kopf = [f"{c} Projektion aus dem governten Katalog — {len(spalten)} {wort}, "
                f"Grain: {grain or 'nicht deklariert'}."]
        if schluessel:
            kopf.append(f"{c} Deklarierter Schluessel: {', '.join(schluessel)}.")
        if kind == "dimension":
            kopf.append(f"{c} TODO(contract:{contract_ref}): Ersatzschluessel und SCD-Behandlung "
                        f"ergaenzen, z. B. row_number() OVER (ORDER BY "
                        f"{', '.join(schluessel) or '<business_key>'}) AS {name}_sk.")
        auswahl = ",\n".join(f"    {_projektion(s, table, dl['stack'])}" for s in spalten)
        return head + "\n".join(kopf) + "\nSELECT\n" + auswahl + f"\nFROM {silver_tbl}\n;\n"

    # honest, runnable-shaped skeleton: the modeled projection lives in a TODO *comment* (with a concrete
    # example), the executable statement stays valid SQL (`SELECT *`) — never an un-parseable placeholder.
    if kind == "dimension":
        body = (
            "SELECT\n"
            f"    {c} TODO(contract:{contract_ref}): surrogate key + conformed attributes (SCD as required), e.g.:\n"
            f"    {c}   row_number() OVER (ORDER BY <business_key>) AS {name}_sk, <business_key>, <attributes>\n"
            "    *\n"
            f"FROM {silver_tbl}\n;\n")
    elif kind == "aggregate":
        body = (
            "SELECT\n"
            f"    {c} TODO(contract:{contract_ref}): grouping grain + rolled-up measures, e.g.:\n"
            f"    {c}   <group_by_keys>, SUM(<measure>) AS <measure_sum>  (with GROUP BY <group_by_keys>)\n"
            "    *\n"
            f"FROM {silver_tbl}\n;\n")
    else:  # fact
        body = (
            "SELECT\n"
            f"    {c} TODO(contract:{contract_ref}): fact grain, dimension foreign keys, additive measures, e.g.:\n"
            f"    {c}   <dimension_foreign_keys>, <measures>  (JOIN <conformed dimensions> ON <keys>)\n"
            "    *\n"
            f"FROM {silver_tbl}\n;\n")
    return head + body


def _silver_to_gold_conformed(name: str, kind: str, sources: list[tuple[str, list[str]]],
                              contract_ref: str, dl: dict, gold_tbl: str = "",
                              table: dict | None = None) -> str:
    """Ein Gold-Ziel, das mehrere Domaenen speisen — als EIN Transform.

    ``UNION`` (nicht ``UNION ALL``): dieselbe Quelltabelle, die in zwei Domaenen landet,
    liefert identische Zeilen, und die faellt UNION heraus. Was UNION NICHT kann, ist
    entscheiden, welche Seite recht hat, wenn dieselbe Schluesselzeile verschiedene
    Attribute traegt — das ist eine Vorrangfrage und steht als TODO drin, statt hier
    geraten zu werden.

    ``sources`` traegt je Domaene **alle** Herkunftstabellen, nicht eine.

    Gemessen 07.09.2026 am SAP-Szenario mit materialisierter Bronze: hat eine Domaene
    mehrere Herkuenfte, setzte der Aufrufer frueher ersatzweise ``silver.<domaene>`` ein.
    Diese Tabelle gibt es bei aufgeschluesseltem Silber nicht — der Lauf lieferte
    ``TABLE_OR_VIEW_NOT_FOUND: silver.order_to_cash`` fuer ``dim_material``, weil Order To
    Cash das Produkt aus **zwei** Tabellen speist (``order_to_cash_makt`` und
    ``order_to_cash_mara``). Ein erfundener Name ist keine offengelassene Entscheidung,
    sondern eine kaputte Referenz: der Ausfuehrer meldet ihn als ``kette`` (ein Loch in der
    Lieferung) statt als ``platzhalter`` (eine offene Entscheidung), und damit verwischt
    genau die Unterscheidung, auf der das Werkzeug steht.

    Deshalb bekommt eine Domaene mit mehreren Herkuenften denselben ausdruecklichen
    Platzhalter, den ``_silver_to_gold_ungeklaert`` schon fuer denselben Fall innerhalb
    einer Domaene setzt. Die Kandidaten stehen im Kopf, damit die Entscheidung getroffen
    werden kann, ohne den Blueprint zu lesen.
    """
    c = dl["comment"]
    gold_tbl = gold_tbl or f"gold_{_ident(name)}"
    spalten = sorted(set((table or {}).get("columns") or []))
    schluessel = [k for k in ((table or {}).get("key") or []) if k in spalten]
    grain = (table or {}).get("grain") or ""

    kopf = [
        f"{c} silver → gold — konforme {kind} '{name}'.",
        f"{c} Contract: {contract_ref}",
        f"{c} Gespeist von {len(sources)} Domaenen: {', '.join(d for d, _ in sources)}.",
        *[f"{c}   {d}: {', '.join(t) if t else '(keine Herkunft im Katalog)'}"
          for d, t in sources],
        f"{c} EIN Ziel, EIN Transform — je Domaene ein eigenes CREATE OR REPLACE haette",
        f"{c} dieselbe Tabelle ueberschrieben, ohne dass etwas rot wird.",
    ]
    if spalten:
        wort = "Spalte" if len(spalten) == 1 else "Spalten"
        kopf.append(f"{c} Projektion aus dem governten Katalog — {len(spalten)} {wort}, "
                    f"Grain: {grain or 'nicht deklariert'}.")
    if schluessel:
        kopf.append(f"{c} Deklarierter Schluessel: {', '.join(schluessel)}.")
        kopf.append(f"{c} TODO(contract:{contract_ref}): Vorrang festlegen, falls dieselbe "
                    f"Schluesselzeile je Domaene verschiedene Attribute traegt — UNION "
                    f"entfernt nur EXAKTE Dubletten.")
    if kind == "dimension" and schluessel:
        kopf.append(f"{c} TODO(contract:{contract_ref}): Ersatzschluessel und SCD-Behandlung "
                    f"ergaenzen, z. B. row_number() OVER (ORDER BY {', '.join(schluessel)}) "
                    f"AS {_ident(name)}_sk.")

    proj = (",\n    ".join(_projektion(s, table, dl["stack"]) for s in spalten)) if spalten else "*"
    if not spalten:
        kopf.append(f"{c} TODO(contract:{contract_ref}): kein Katalogeintrag — Projektion ergaenzen.")

    # Genau eine Herkunft je Domaene laesst sich schreiben. Mehrere sind eine Fachfrage
    # (vereinigen oder verbinden), und die wird hier nicht geraten — siehe Docstring.
    mehrdeutig = [d for d, t in sources if len(t) != 1]
    if mehrdeutig:
        kopf += [
            f"{c}",
            f"{c} Absichtlich nicht ausfuehrbar: {', '.join(mehrdeutig)} speist dieses Ziel aus",
            f"{c} mehr als einer Tabelle. Ob die vereinigt oder verbunden gehoeren, haengt daran,",
            f"{c} welche den Kopf traegt — das ist eine Fachfrage. Ein erfundener Tabellenname",
            f"{c} waere hier die teuerste Antwort, weil er wie eine Lieferluecke aussieht.",
            f"{c} TODO(contract:{contract_ref}): je genannter Domaene EINE Fassung einsetzen.",
        ]
    blocks = []
    for dom, tbls in sources:
        if len(tbls) == 1:
            blocks.append(f"SELECT\n    {proj}\nFROM {tbls[0]}")
        else:
            # WOERTLICH derselbe Token wie in `_silver_to_gold_ungeklaert`, nicht eine zweite
            # Fassung davon. Der Ausfuehrer erkennt Platzhalter ueber `<[A-Za-z_ :]+>`; ein
            # Text mit Komma, Punkt oder Gedankenstrich faellt durch das Raster und wird als
            # `dialekt` gezaehlt — gemessen 07.09.2026 am ersten Versuch, der die Kandidaten
            # in die Klammer schrieb. Eine offene Entscheidung als Dialektgrenze zu zaehlen
            # ist derselbe Fehler wie sie als Lieferluecke zu zaehlen, nur andersherum.
            # Welche Domaene es betrifft und welche Tabellen in Frage kommen, steht im Kopf.
            blocks.append(f"SELECT\n    {proj}\nFROM "
                          f"<ZUSAMMENFUEHRUNG NICHT ENTSCHIEDEN: UNION ODER JOIN>")
    return (f"{chr(10).join(kopf)}\n{dl['ctas']} {gold_tbl}{dl['using']} AS\n"
            + "\nUNION\n".join(blocks) + "\n;\n")


def emit_transforms(blueprint: dict, stack: str = "fabric", schemas: bool = False,
                    governed_catalog: dict | None = None) -> dict[str, str]:
    """Return the transform DAG as ``path → SQL`` (relative to a ``transforms/`` root).

    One ``silver_to_gold__<product>.sql`` per gold product; one
    ``bronze_to_silver__<source>.sql`` per ingested source **iff** bronze is materialised
    (``medallion.bronze.enabled``). Plus ``_MEDALLION_FLOW.md`` documenting the DAG.

    ``schemas`` targets a schema-enabled lakehouse: tables become ``gold.<name>`` / ``silver.<domain>``
    instead of ``gold_<name>`` / ``silver_<domain>`` in the default namespace.
    """
    dl = _dialect(stack)
    med = blueprint.get("medallion", {})
    bronze_enabled = bool(med.get("bronze", {}).get("enabled", False))
    contract_ref = med.get("silver", {}).get("data_contract_ref", "<silver-contract>")
    kinds = _gold_kinds(blueprint)
    domains = sorted(blueprint.get("mesh", {}).get("domains", []), key=lambda d: d.get("name", ""))

    # Gold-Produkt -> beitragende Domaenen. Alles mit mehr als einer ist konform und
    # wird unten EINMAL gebaut statt je Domaene einmal.
    _by_product: dict[str, list[str]] = {}
    for _d in domains:
        for _p in _d.get("data_products", []) or []:
            _by_product.setdefault(_p, []).append(_d["name"])
    _conformed = {p: sorted(doms) for p, doms in _by_product.items() if len(doms) > 1}

    out: dict[str, str] = {}
    flow: list[str] = [
        "# Medallion transform DAG (generated — ADR-0015)",
        "",
        f"Stack: **{stack}**  ·  Bronze materialised: **{bronze_enabled}**  ·  "
        f"Layer-skip forbidden: **{med.get('no_layer_skip', True)}**",
        "",
        f"Silver data contract: `{contract_ref}`",
        "",
    ]
    if not bronze_enabled:
        flow.append("> Bronze is outsourced (single-copy / shortcut / mirror) — no bronze→silver "
                    "materialisation is emitted; ingestion lands conformable data directly.")
        flow.append("")

    for d in domains:
        ddir = _dirslug(d["name"])
        dident = _ident(d["name"])
        c_ref = _domain_contract(d, contract_ref)
        silver_tbl = layer_ref("silver", dident, schemas)
        flow.append(f"## {d['name']}  (`{silver_tbl}`)")
        # Silber je HERKUNFTSTABELLE, sobald der governte Katalog sie kennt -- sonst je Domaene.
        #
        # Eine Silber-Tabelle je Domaene war nie eine Entscheidung, sondern die Folge davon, dass
        # die Herkunft nirgends maschinenlesbar stand. Der Schaden war handfest: bei einem Kundenmandanten
        # schrieben drei `bronze_to_silver__*` mit `CREATE OR REPLACE` auf dasselbe
        # `silver.controlling`, die letzte gewann, die ersten beiden waren weg -- und nichts
        # wurde rot. Gemessen 12.08.2026.
        #
        # Ohne Katalog bleibt es beim alten Zuschnitt: dann WEISS niemand, welche Quelle zu
        # welchem Produkt gehoert, und ein geratener Zuschnitt waere schlimmer als ein grober.
        herkunft = _herkunft_je_domaene(blueprint, governed_catalog, d, domains)
        if bronze_enabled:
            if herkunft:
                for quelle in sorted({q for qs in herkunft.values() for q in qs}):
                    rel = f"transforms/{ddir}/bronze_to_silver__{_ident(quelle)}.sql"
                    bronze_tbl = layer_ref("bronze", _ident(quelle), schemas)
                    ziel = layer_ref("silver", _ident(quelle), schemas)
                    out[rel] = _bronze_to_silver(d, quelle, ziel, c_ref, dl, bronze_tbl=bronze_tbl)
                    flow.append(f"- {bronze_tbl} → `{ziel}`  ·  `{rel}`")
            else:
                for src in _sources_for_domain(blueprint, dident):
                    rel = f"transforms/{ddir}/bronze_to_silver__{_ident(src)}.sql"
                    bronze_tbl = layer_ref("bronze", _ident(src), schemas)
                    out[rel] = _bronze_to_silver(d, src, silver_tbl, c_ref, dl, bronze_tbl=bronze_tbl)
                    flow.append(f"- {bronze_tbl} → `{silver_tbl}`  ·  `{rel}`")
        for product in sorted(d.get("data_products", [])):
            if product in _conformed:
                flow.append(f"- `{silver_tbl}` → {layer_ref('gold', _ident(product), schemas)} "
                            f"({kinds.get(product, 'fact')})  ·  speist die konforme Dimension, "
                            f"s. `transforms/_conformed/silver_to_gold__{_ident(product)}.sql`")
                continue
            kind = kinds.get(product, "fact")
            gold_tbl = layer_ref("gold", _ident(product), schemas)
            rel = f"transforms/{ddir}/silver_to_gold__{_ident(product)}.sql"
            # Erzeugte Produkte und solche ohne Zuordnung sind KEINE Silber-Projektionen.
            # Sie hier abzufangen, statt sie auf eine Tabelle zeigen zu lassen, die es nicht
            # gibt, ist der Unterschied zwischen "sagt was fehlt" und "scheitert an einem
            # Tabellennamen, der nichts erklaert".
            gen = _generator_fuer(blueprint, product)
            if gen:
                out[rel] = _erzeugt(product, gold_tbl, dl, gen)
                flow.append(f"- *(erzeugt)* → {gold_tbl} ({kind})  ·  `{rel}`")
                continue
            # `herkunft` ist nur dann eine Aussage, wenn der Katalog UEBERHAUPT von Herkunft
            # spricht. Ein Katalog ohne ein einziges `sources` ist aelter oder von einem
            # anderen Erzeuger -- er schweigt zur Herkunft, er verneint sie nicht. Diesen
            # Unterschied zu verwischen hiesse, aus einer fehlenden Angabe einen Befund zu
            # machen: genau der Fehler, den dieser Lauf mehrfach zutage gefoerdert hat.
            if herkunft and not herkunft.get(_ident(product)):
                out[rel] = _ohne_quelle(product, kind, gold_tbl, dl)
                flow.append(f"- *(ohne Quelle — offene Festlegung)* → {gold_tbl}  ·  `{rel}`")
                continue
            # Das Produkt liest aus SEINEN Quellen, nicht aus der Domaenentabelle. Bei n:1
            # (fact_vertrag aus con, roc, roclin) ist die Quelle ein UNION ALL -- das ist die
            # Zusammenfuehrung, die der Bauplan meint, und sie steht jetzt im SQL statt in
            # einer Fussnote.
            quellen = [layer_ref("silver", _ident(q), schemas)
                       for q in herkunft.get(_ident(product), [])]
            von = quellen or [silver_tbl]
            # Mehrere Herkuenfte mit verschiedener Form: dann ist offen, ob vereinigt oder
            # verbunden gehoert -- und die Datei sagt das, statt eine der beiden zu waehlen.
            kat_t = _catalog_table(governed_catalog, _ident(product)) or {}
            je_quelle = kat_t.get("source_columns") or {}
            if len(von) > 1 and not _formgleich(je_quelle):
                out[rel] = _ungeklaerte_zusammenfuehrung(product, kind, gold_tbl, dl, von,
                                                         je_quelle, c_ref)
                flow.append(f"- *(Zusammenführung offen: UNION oder JOIN)* → {gold_tbl}  ·  `{rel}`")
                continue
            out[rel] = _silver_to_gold(product, kind, von[0] if len(von) == 1 else von, c_ref, dl,
                                       gold_tbl=gold_tbl,
                                       table=_catalog_table(governed_catalog, _ident(product)))
            flow.append(f"- {' + '.join(f'`{q}`' for q in von)} → {gold_tbl} ({kind})  ·  `{rel}`")
        flow.append("")

    # Konforme Dimensionen: ein Gold-Ziel, das mehrere Domaenen speisen, wird EINMAL gebaut.
    #
    # Vorher lief die Schleife oben pro Domaene, und zwei Domaenen mit demselben Gold-Produkt
    # erzeugten zwei Dateien mit je einem `CREATE OR REPLACE TABLE gold.<x>` — wer zuletzt
    # laeuft, gewinnt, ohne dass irgendetwas rot wird (gemessen 03.08.2026 an `dim_material`,
    # das order_to_cash und inventory_mm beide aus MARA bauen). Der governte Katalog fuehrt
    # das Ziel laengst als EINE Tabelle mit einem Schluessel; verdoppelt hat es nur der Emitter.
    if _conformed:
        flow.append("## Konforme Dimensionen (mehrere Domaenen, ein Ziel)")
        flow.append("")
    for product, contributing in sorted(_conformed.items()):
        kind = kinds.get(product, "dimension")
        gold_tbl = layer_ref("gold", _ident(product), schemas)
        rel = f"transforms/_conformed/silver_to_gold__{_ident(product)}.sql"
        # Bei aufgeschluesseltem Silber liest die konforme Dimension aus der Herkunftstabelle
        # der jeweiligen Domaene, nicht aus `silver.<domaene>` -- die gibt es dann nicht.
        # Mehrere Herkuenfte je Domaene sind eine offene Fachfrage und gehen als Liste
        # weiter; der Emitter setzt dafuer einen Platzhalter statt eines erfundenen Namens
        # (gemessen 07.09.2026: `silver.order_to_cash` existierte nie, siehe Docstring dort).
        sources = []
        for dom in contributing:
            d_dom = next((x for x in domains if x.get("name") == dom), {})
            eigene = _herkunft_je_domaene(blueprint, governed_catalog, d_dom, domains).get(_ident(product), [])
            sources.append((dom, [layer_ref("silver", _ident(e), schemas) for e in eigene]))
        out[rel] = _silver_to_gold_conformed(
            product, kind, sources, contract_ref, dl, gold_tbl=gold_tbl,
            table=_catalog_table(governed_catalog, _ident(product)))
        flow.append(f"- {' + '.join(t[0] if len(t) == 1 else f'{d} (Zusammenfuehrung offen)' for d, t in sources)}"
                    f" → {gold_tbl} ({kind})  ·  `{rel}`")
    if _conformed:
        flow.append("")

    out["transforms/_MEDALLION_FLOW.md"] = "\n".join(flow) + "\n"
    return out


#: Die Werte, die eine `DATA-INC`-Antwort tragen kann (Optionen-Katalog in
#: `decision_proposals._OPTIONEN["DATA-INC"]`). Hier genannt, damit ein unbekannter Wert
#: als Befund im Kopf steht und nicht still wie „nicht entschieden" behandelt wird.
_DATA_INC_WERTE = ("watermark", "vollast", "cdc", "partition")


def _silver_to_gold_incremental(name: str, kind: str, silver_tbl: str, contract_ref: str, dl: dict,
                                gold_tbl: str = "", star: bool = True,
                                proposal: dict | None = None,
                                wahl: str | None = None) -> str:
    """Incremental (upsert) silver→gold as a MERGE scaffold — the delta-load counterpart of the
    full-rebuild ``_silver_to_gold``. Honest by construction: the merge *shape* comes from the IR
    (target gold table, kind), the match key + watermark predicate are domain policy → TODO(contract).
    Fail-safe by design — an un-filled predicate leaves the placeholder un-parseable, so nobody
    accidentally ships a full re-scan as if it were incremental."""
    c = dl["comment"]
    gold_tbl = gold_tbl or f"gold_{_ident(name)}"
    set_clause = "UPDATE SET *" if star else f"UPDATE SET <cols>  {c} explicit column mapping (non-Delta dialect)"
    ins_clause = "INSERT *" if star else "INSERT (<cols>) VALUES (<cols>)"
    scd = ""
    if kind == "dimension":
        scd = (f"{c} SCD: this MERGE is Type-1 (overwrite). For Type-2 history, instead close the current\n"
               f"{c}   version (set <valid_to>) and INSERT a new row — TODO(contract:{contract_ref}).\n")
    # Direct Lake ist ein Fabric-Serving-Konzept. Auf anderen Stacks wäre der Hinweis eine
    # Anweisung zu einer Technik, die es dort nicht gibt.
    serving = (f"{c} Direct Lake: the semantic model auto-frames the latest Delta after each MERGE — do NOT set\n"
               f"{c}   an Import-mode incremental-refresh policy (RangeStart/RangeEnd) on a Direct Lake model.\n"
               ) if dl.get("stack") == "fabric" else ""
    head = (
        f"{c} silver → gold (INCREMENTAL upsert) — build {kind} '{name}'.\n"
        f"{c} Contract: {contract_ref}\n"
        + serving
        + scd
    )
    keys, wm = (proposal or {}).get("keys") or [], (proposal or {}).get("watermark")
    # Die Bestaetigung, auf die der Kommentar unten wartet (C-3, 02.09.2026): traegt das Profil
    # `entscheidungen.DATA-INC[·<domaene>] = watermark` und nennt der Katalog Schluessel und
    # Aenderungsspalte, wird der Vorschlag zur ausfuehrbaren Anweisung. Genau das ist der
    # Unterschied zwischen „vorgedacht" und „gebaut": vorher blieben 22 `<business_key>`-
    # Platzhalter stehen, obwohl die Antwort in der Datei lag (Szenario `sap_mittelstand`).
    if wahl == "watermark" and keys and wm:
        on = " AND ".join(f"t.{k} = s.{k}" for k in keys)
        head += (
            f"{c}\n"
            f"{c} ENTSCHIEDEN: DATA-INC = watermark (Antwortdatei → Profil `entscheidungen`).\n"
            f"{c}   Match-Key : {' + '.join(keys)}\n"
            f"{c}   Watermark : {wm} > (SELECT MAX({wm}) FROM {gold_tbl}); leeres Gold laedt alles.\n"
            f"{c}   Loeschungen in der Quelle kommen ohne Loeschkennzeichen nicht an (Katalog-Option).\n"
        )
        body = (
            f"MERGE INTO {gold_tbl} AS t\n"
            f"USING (\n"
            f"    SELECT *\n"
            f"    FROM {silver_tbl}\n"
            f"    WHERE (SELECT COUNT(*) FROM {gold_tbl}) = 0\n"
            f"       OR {wm} > (SELECT MAX({wm}) FROM {gold_tbl})\n"
            f") AS s\n"
            f"ON {on}\n"
            f"WHEN MATCHED THEN {set_clause}\n"
            f"WHEN NOT MATCHED THEN {ins_clause}\n"
            f";\n"
        )
        return head + body
    if wahl:
        if wahl == "watermark":
            fehlt = " und ".join(x for x, ok in (("Match-Key", bool(keys)),
                                                 ("Aenderungsspalte", bool(wm))) if not ok)
            head += (f"{c}\n{c} ENTSCHIEDEN: DATA-INC = watermark — aber der Katalog nennt "
                     f"{fehlt or 'nichts Fehlendes'} nicht; die Platzhalter unten bleiben, bis der "
                     f"Datenvertrag sie traegt.\n")
        elif wahl == "cdc":
            head += (f"{c}\n{c} ENTSCHIEDEN: DATA-INC = cdc. Der MERGE liest den CDC-Feed bzw. die "
                     f"gespiegelte Tabelle statt einer Watermark; Feed-Spalten und Loeschkennzeichen "
                     f"sind Quellwissen — die Platzhalter unten bleiben, bis der Konnektor sie nennt.\n")
        elif wahl == "partition":
            head += (f"{c}\n{c} ENTSCHIEDEN: DATA-INC = partition. Statt MERGE ein INSERT OVERWRITE je "
                     f"Periode; die Partitionsspalte ist Vertragswissen (TODO(contract:{contract_ref})) — "
                     f"die Platzhalter unten bleiben, bis sie im Datenvertrag steht.\n")
        else:
            head += (f"{c}\n{c} BEFUND: DATA-INC = {wahl!r} ist kein bekannter Wert "
                     f"({', '.join(_DATA_INC_WERTE)}); behandelt wie nicht entschieden.\n")
    # A pre-thought proposal for the two open decisions (match key + watermark), derived from the
    # governed catalog. Deliberately a COMMENT: the executable statement stays fail-safe with
    # un-parseable placeholders, so a proposal can never silently go live unconfirmed.
    if proposal:
        head += (
            f"{c}\n"
            f"{c} VORSCHLAG (zu bestätigen, ersetzt die Platzhalter unten — nichts läuft ungeprüft):\n"
            f"{c}   Match-Key : {' + '.join(keys) if keys else '<kein Schlüssel im Katalog erkennbar>'}\n"
            + (f"{c}   Watermark : {wm} > (SELECT MAX({wm}) FROM {gold_tbl})\n" if wm else
               f"{c}   Watermark : keine Änderungsspalte im Modell — im Silver '_loaded_at' ergänzen\n"
               f"{c}               oder CDC/Mirroring an der Quelle nutzen\n")
        )
    body = (
        f"MERGE INTO {gold_tbl} AS t\n"
        f"USING (\n"
        f"    SELECT *\n"
        f"    FROM {silver_tbl}\n"
        f"    {c} TODO(contract:{contract_ref}): incremental predicate — only rows changed since last load, e.g.\n"
        f"    {c}   WHERE <watermark_col> > (SELECT COALESCE(MAX(<watermark_col>), DATE'1900-01-01') FROM {gold_tbl})\n"
        f") AS s\n"
        f"ON t.<business_key> = s.<business_key>   {c} TODO(contract:{contract_ref}): match key(s)\n"
        f"WHEN MATCHED THEN {set_clause}\n"
        f"WHEN NOT MATCHED THEN {ins_clause}\n"
        f";\n"
    )
    return head + body


def _incremental_proposal(gc: dict | None, product: str) -> dict | None:
    """Per-table match-key + watermark proposal from the governed catalog (Tool-Reuse: the same
    column-evidence heuristics the decision-proposal engine uses). None without a catalog."""
    if not gc:
        return None
    tbl = next((t for t in gc.get("tables", []) if t.get("name") == product), None)
    if not tbl:
        return None
    from core.dataarch_engine.blueprint.decision_proposals import _WATERMARK_HINTS, _rank, match_keys
    cols = tbl.get("columns") or []
    wm = sorted(((_rank(c, _WATERMARK_HINTS), c) for c in cols), key=lambda x: (-x[0], x[1]))
    return {"keys": match_keys(tbl), "watermark": next((c for w, c in wm if w > 0), None)}


def emit_incremental_load(blueprint: dict, stack: str = "fabric", schemas: bool = False,
                          governed_catalog: dict | None = None,
                          entscheidungen: dict | None = None) -> dict[str, str]:
    """Return the incremental (delta-load) transform set: one MERGE/upsert ``silver_to_gold`` per gold
    product under ``transforms/incremental/`` + ``transforms/INCREMENTAL_REFRESH.md`` — the layer
    decision for *where* incremental lives. Grounded in MS Learn (2026-07): Dataflow Gen2 incremental
    refresh, Direct Lake framing. The full-rebuild ``emit_transforms`` stays the idempotent default;
    this is the additive delta path for real data volumes."""
    dl = _dialect(stack)
    star = stack != "snowflake"
    kinds = _gold_kinds(blueprint)
    med = blueprint.get("medallion", {})
    contract_ref = med.get("silver", {}).get("data_contract_ref", "<silver-contract>")
    domains = sorted(blueprint.get("mesh", {}).get("domains", []), key=lambda d: d.get("name", ""))

    from core.dataarch_engine.blueprint.decision_proposals import entscheidung_fuer

    out: dict[str, str] = {}
    entschieden: list[tuple[str, str]] = []
    for d in domains:
        ddir = _dirslug(d["name"])
        silver_tbl = layer_ref("silver", _ident(d["name"]), schemas)
        # `entscheidungen` ist das Profilfeld aus dem Rueckweg (C-3): `DATA-INC·<domaene>` bei
        # mehreren Domaenen, `DATA-INC` bei einer — dieselbe ID, die der Ledger vergibt.
        wahl = entscheidung_fuer(entscheidungen, "DATA-INC", d["name"])
        if wahl:
            entschieden.append((d["name"], wahl))
        for product in sorted(d.get("data_products", [])):
            kind = kinds.get(product, "fact")
            gold_tbl = layer_ref("gold", _ident(product), schemas)
            rel = f"transforms/incremental/{ddir}/silver_to_gold__{_ident(product)}.sql"
            if wahl == "vollast":
                # Kein MERGE-Artefakt: bei Vollast ist der Vollaufbau `transforms/<domaene>/`
                # die einzige Ladeform. Gemessen 02.09.2026: eine Verweisdatei aus Kommentaren
                # meldete der Dialekt-Validator als „no executable SQL" — ein Befund ohne
                # Fehler. Warum die Datei fehlt, sagt die Tabelle in INCREMENTAL_REFRESH.md.
                continue
            out[rel] = _silver_to_gold_incremental(
                product, kind, silver_tbl, contract_ref, dl, gold_tbl, star,
                proposal=_incremental_proposal(governed_catalog, product), wahl=wahl)

    doc = [
        "# Incremental / delta-load — where it lives (generated, grounded MS Learn 2026-07)",
        "",
        "Full-rebuild transforms (`transforms/*.sql`) are the safe idempotent default. For real data",
        "volumes, load **incrementally** — pick the layer, don't scatter it:",
        "",
        "| Layer | Mechanism | Use when |",
        "|---|---|---|",
        "| **Transform / pipeline (recommended for gold Delta)** | `MERGE`/upsert on a watermark — the "
        "`transforms/incremental/*.sql` here (Spark SQL / T-SQL over Delta) | Code-first team; full control "
        "over match keys, SCD, late-arriving data. |",
        "| **Dataflow Gen2 incremental refresh** | first-class, table-level; needs a **DateTime** filter "
        "column; update method `replace`; bucketed | Low-code team building the silver/gold in a dataflow. |",
        "| **Semantic model** | **Direct Lake needs NO incremental-refresh policy** — RangeStart/RangeEnd "
        "gehören zum **Import**-Fallback. Es braucht aber sehr wohl eine **Rahmung** (framing): der "
        "Schalter „Keep your Direct Lake data up to date“ trägt den Dauerbetrieb, nicht die "
        "Auslieferung — programmatisch angelegte Tabellen müssen vor der ersten Abfrage gerahmt "
        "werden, und nach einem nicht behebbaren Fehler setzt Power BI die automatische "
        "Aktualisierung aus | Serving layer — Rahmungsschritt siehe `orchestration/_ORCHESTRATION.md`. |",
        "",
        "## MERGE scaffolds (this folder)",
        "",
        "Each `silver_to_gold__<product>.sql` is a real MERGE shape; the **match key** and the **watermark",
        "predicate** are domain policy (`TODO(contract)`), left as placeholders on purpose so an un-authored",
        "rule can't silently ship as a full re-scan. Dimensions carry an SCD-Type-1 vs Type-2 note.",
        "",
        "## Dataflow Gen2 caveats (grounded — if you take the low-code path)",
        "",
        "- Needs an **unchanging DateTime** filter column (a *date-modified* field causes duplicate-value refresh failures).",
        "- Only update method is `replace` (per bucket); data older than the first bucket is untouched.",
        "- Buckets: **≤ 50 per query, ≤ 150 per dataflow**; schema must be **fixed** (not dynamic).",
        "- Lakehouse destination: **avoid other writers** (Spark) on the same table; `OPTIMIZE`/`REORG` not "
        "supported on incremental tables; data gateway ≥ **May 2025 (3000.270)**.",
        "- Don't switch a table from full→incremental with overlapping data already in the destination.",
    ]
    # Auf fremden Stacks ist die Fabric-Antwort ("Direct Lake braucht keine Refresh-Policy") ohne
    # Gegenstand; Snowflake stellt sogar eine echte Entwurfsentscheidung an den Anfang
    # (Dynamic Tables vs. Streams+Tasks — MERGE/SCD-2 nur mit letzterem).
    if entschieden:
        doc += [
            "",
            "## Entschieden (Antwortdatei → Profil `entscheidungen`)",
            "",
            "| Domäne | DATA-INC | Wirkung in diesem Ordner |",
            "|---|---|---|",
        ]
        wirkung = {
            "watermark": "MERGE mit Match-Key und Watermark aus dem Katalog — ausführbar, sobald "
                         "der Katalog beide nennt; sonst bleiben die Platzhalter mit Befund",
            "vollast": "kein MERGE-Artefakt in diesem Ordner; der Vollaufbau unter "
                       "`transforms/<domäne>/` ist die Ladeform, jeder Lauf schreibt Gold neu",
            "cdc": "Platzhalter bleiben; der Feed ist Quellwissen",
            "partition": "Platzhalter bleiben; die Partitionsspalte ist Vertragswissen",
        }
        doc += [f"| {name} | `{wahl}` | {wirkung.get(wahl, 'unbekannter Wert, wie nicht entschieden')} |"
                for name, wahl in entschieden]
    _note = gap_doc_for(blueprint, "incremental", "Inkrementelles Laden")
    out["transforms/INCREMENTAL_REFRESH.md"] = _note or ("\n".join(doc) + "\n")
    return out


# --------------------------------------------------------------------------------------------------
# Low-code path: the same medallion DAG expressed as Power Query M (Dataflows Gen2) instead of SQL.
# For the GUI/low-code customer persona (ADR-0051 §6, recommend_profile transform=dataflows-gen2):
# a technical team gets the SQL/notebook path above; a low-code team gets these M query scaffolds.
# Honest scope: this emits the *Power Query M* (the transform logic) — the actual Fabric `.Dataflow`
# item wrapper (`.platform`, `queryMetadata.json`, the mashup document) is portal- / Fabric-git- /
# fabric-cicd-owned and is NOT fabricated here. Paste each query into a Dataflow Gen2 in the portal,
# or seed a git-integrated dataflow's mashup. Same honesty as the SQL scaffolds: structure from the IR,
# business logic left as explicit TODO(contract:<ref>) markers, never invented.
# --------------------------------------------------------------------------------------------------
def _bronze_to_silver_m(src: str, silver_ref: str, contract_ref: str) -> str:
    return (
        f"// bronze → silver — conform + cleanse '{src}'.\n"
        f"// Contract: {contract_ref}\n"
        f"// VERIFY: bind Source to the bronze '{src}' data source "
        f"(Lakehouse.Contents / Sql.Database / a Fabric connector).\n"
        "let\n"
        "    Source = null,\n"
        f"    // TODO(contract:{contract_ref}): map raw columns → conformed silver schema; "
        "types, dedup, null/quality rules, business keys.\n"
        f"    Silver = Source   // target: {silver_ref}\n"
        "in\n"
        "    Silver\n"
    )


def _silver_to_gold_m(name: str, kind: str, silver_ref: str, contract_ref: str) -> str:
    todo = {
        "dimension": "surrogate key + conformed attributes (SCD as required)",
        "aggregate": "grouping grain + rolled-up measures (Table.Group)",
    }.get(kind, "fact grain, dimension foreign keys, additive measures")
    return (
        f"// silver → gold — build {kind} '{name}'.\n"
        f"// Contract: {contract_ref}\n"
        f"// VERIFY: bind Source to the silver table `{silver_ref}` "
        "(Lakehouse.Contents / Sql.Database / a Fabric connector).\n"
        "let\n"
        "    Source = null,\n"
        f"    // TODO(contract:{contract_ref}): {todo}.\n"
        f"    Gold = Source   // {kind}: {name}\n"
        "in\n"
        "    Gold\n"
    )


def emit_dataflows_gen2(blueprint: dict, stack: str = "fabric", schemas: bool = False) -> dict[str, str]:
    """Return the medallion DAG as Power Query M (Dataflows Gen2 low-code path), ``path → M content``.

    One ``<product>.pq`` per gold product (silver→gold); one ``bronze_to_silver__<source>.pq`` per
    ingested source **iff** bronze is materialised — mirroring ``emit_transforms`` but in M, for the
    GUI/low-code persona. Plus ``_DATAFLOWS_GEN2.md`` documenting the DAG **and the honest boundary**
    (the Fabric `.Dataflow` item wrapper is portal/CLI-owned, not emitted here).
    """
    med = blueprint.get("medallion", {})
    bronze_enabled = bool(med.get("bronze", {}).get("enabled", False))
    contract_ref = med.get("silver", {}).get("data_contract_ref", "<silver-contract>")
    kinds = _gold_kinds(blueprint)
    domains = sorted(blueprint.get("mesh", {}).get("domains", []), key=lambda d: d.get("name", ""))

    out: dict[str, str] = {}
    doc: list[str] = [
        "# Dataflows Gen2 — low-code transform DAG (generated — ADR-0051 §6)",
        "",
        f"Stack: **{stack}**  ·  Bronze materialised: **{bronze_enabled}**  ·  "
        f"Silver data contract: `{contract_ref}`",
        "",
        "The **low-code / GUI** alternative to the SQL/notebook transforms: one Power Query **M** query "
        "per layer hop. **Honest boundary** — these `.pq` files are the *transform logic only*; the "
        "Fabric `.Dataflow` item wrapper (`.platform`, `queryMetadata.json`, the mashup document) is "
        "authored by the portal / Fabric git integration / fabric-cicd and is **not** fabricated here. "
        "Paste each query into a Dataflow Gen2, or seed a git-integrated dataflow's mashup.",
        "",
        "| Domain | Hop | Query |", "|---|---|---|",
    ]
    if not bronze_enabled:
        pre = ("\n> Bronze is outsourced (single-copy / shortcut / mirror) — no bronze→silver query "
               "is emitted; ingestion lands conformable data directly.\n")
    else:
        pre = ""

    for d in domains:
        ddir = _dirslug(d["name"])
        dident = _ident(d["name"])
        silver_ref = layer_ref("silver", dident, schemas)
        if bronze_enabled:
            for src in _sources_for_domain(blueprint, dident):
                rel = f"dataflows/{ddir}/bronze_to_silver__{_ident(src)}.pq"
                out[rel] = _bronze_to_silver_m(src, silver_ref, contract_ref)
                doc.append(f"| {d['name']} | bronze→silver | `{rel}` |")
        for product in sorted(d.get("data_products", [])):
            kind = kinds.get(product, "fact")
            rel = f"dataflows/{ddir}/{_ident(product)}.pq"
            out[rel] = _silver_to_gold_m(product, kind, silver_ref, contract_ref)
            doc.append(f"| {d['name']} | silver→gold ({kind}) | `{rel}` |")

    out["dataflows/_DATAFLOWS_GEN2.md"] = "\n".join(doc) + "\n" + pre
    return out


# Deklarierter logischer Typ -> T-SQL-Typ fuer das Fabric Warehouse. Die LAENGE einer
# Zeichenkette steht nicht im governten Katalog — sie gehoert in den Silber-Vertrag. VARCHAR(255)
# ist die dokumentierte Vorgabe und als solche im DDL benannt, nicht als Messung ausgegeben.
_LOGICAL_TO_TSQL = {"date": "DATE", "number": "DECIMAL(38,4)", "integer": "BIGINT",
                    "boolean": "BIT", "string": "VARCHAR(255)"}


def _warehouse_columns(table: dict, contract_ref: str) -> str | None:
    """Echte T-SQL-Spalten aus dem governten Katalog, oder None ohne Katalog.

    Bis 31.07.2026 stand hier fuer jedes Faktum `dim_fk_1 BIGINT, measure_1 DECIMAL` — erfundene
    Spaltennamen mit erfundenen Typen. Das ist schlimmer als ein leeres Geruest: es sieht aus wie
    ein Modell und ist keins. Die Schluesselteile bekommen NOT NULL, weil der Katalog sie als
    Schluessel FUEHRT; alles andere bleibt NULL-bar, weil darueber nichts deklariert ist.
    """
    spalten = sorted(set(table.get("columns") or []))
    if not spalten:
        return None
    typen = table.get("column_types") or {}
    schluessel = set(table.get("key") or [])
    breite = max(len(c) for c in spalten)
    zeilen = [f"    -- Projektion aus dem governten Katalog. Zeichenkettenlaengen sind eine "
              f"Vorgabe (VARCHAR(255)) und keine Messung —",
              f"    -- die tatsaechlichen Laengen stehen im Silber-Vertrag {contract_ref}."]
    for c in spalten:
        typ = _LOGICAL_TO_TSQL.get(str(typen.get(c, "")).lower(), "VARCHAR(255)")
        null = "NOT NULL" if c in schluessel else "    NULL"
        zeilen.append(f"    {c.ljust(breite)}  {typ.ljust(13)} {null},")
    zeilen[-1] = zeilen[-1].rstrip(",")
    return "\n".join(zeilen)


def _warehouse_kopf(schemas: bool) -> str:
    """Das Schema anlegen, falls die Schicht ein echtes SQL-Schema ist.

    Jede DDL-Datei ist ein eigener Apply-Schritt und wird allein ausgefuehrt -- sie muss also
    selbst dafuer sorgen, dass ihr Schema existiert. `CREATE SCHEMA` muss in T-SQL die erste
    Anweisung ihres Stapels sein, deshalb ueber `EXEC`.
    """
    return "IF SCHEMA_ID('gold') IS NULL EXEC('CREATE SCHEMA gold');\n" if schemas else ""


def _warehouse_ddl(name: str, kind: str, contract_ref: str, schemas: bool = False,
                   table: dict | None = None) -> str:
    """T-SQL CREATE TABLE for a gold product in a Fabric Warehouse (Warehouse-endpoint gold pattern).

    ``schemas`` wie ueberall sonst: ein schema-aktiviertes Ziel traegt die Medaillon-Schicht als
    echtes SQL-Schema (``gold.dim_x``), sonst als Namenspraefix im Standard-Namensraum
    (``dbo.gold_dim_x``). Der Parameter kam schon von `cli.py` herein, wurde hier aber nicht
    benutzt -- die Folge war eine Lieferung, die `enableSchemas=true` setzt und dann `dbo`
    beschreibt. Gemessen 12.08.2026 am Kundenmandant-Lauf, im Widerspruch zur eigenen Begruendung
    in `provision.sh` und zur MLV-Familie, die es richtig macht.
    """
    tbl = layer_ref("gold", _ident(name), schemas)
    if not schemas:
        tbl = f"dbo.{tbl}"
    kopf = _warehouse_kopf(schemas)
    aus_katalog = _warehouse_columns(table or {}, contract_ref)
    if aus_katalog is not None:
        grain = (table or {}).get("grain") or ""
        return (f"-- gold {kind} '{name}' as a Fabric Warehouse table (T-SQL / Warehouse endpoint).\n"
                f"-- Contract: {contract_ref}\n"
                + (f"-- Grain: {grain}\n" if grain else "")
                + kopf
                + f"IF OBJECT_ID('{tbl}', 'U') IS NULL\n"
                  f"CREATE TABLE {tbl} (\n{aus_katalog}\n);\n")
    if kind == "dimension":
        cols = (f"    {name}_sk    BIGINT       NOT NULL,   -- surrogate key\n"
                "    -- TODO(contract:%s): conformed business key + attributes (SCD as required)\n"
                "    business_key VARCHAR(200) NOT NULL,\n"
                "    attribute_1  VARCHAR(4000) NULL" % contract_ref)
    elif kind == "aggregate":
        cols = (f"    -- TODO(contract:{contract_ref}): grouping grain + rolled-up measures\n"
                "    group_key    VARCHAR(200) NOT NULL,\n"
                "    measure_sum  DECIMAL(38,4) NULL")
    else:  # fact
        cols = (f"    -- TODO(contract:{contract_ref}): fact grain, dimension foreign keys, additive measures\n"
                "    dim_fk_1     BIGINT       NULL,\n"
                "    measure_1    DECIMAL(38,4) NULL")
    return (f"-- gold {kind} '{name}' as a Fabric Warehouse table (T-SQL / Warehouse endpoint).\n"
            f"-- Contract: {contract_ref}\n"
            + kopf
            + f"IF OBJECT_ID('{tbl}', 'U') IS NULL\n"
              f"CREATE TABLE {tbl} (\n{cols}\n);\n")


def emit_warehouse_gold(blueprint: dict, schemas: bool = False,
                        governed_catalog: dict | None = None) -> dict[str, str]:
    """Return gold as **Fabric Warehouse** T-SQL DDL (``path → content``) — the Warehouse-endpoint pattern.

    The alternative to lakehouse-Delta gold (research §4 deployment-patterns: Bronze/Silver-Lakehouse +
    Gold-Warehouse, chosen by team preference). One ``CREATE TABLE`` per gold product in the warehouse's
    ``dbo`` schema, kind-aware, with ``TODO(contract:<ref>)`` markers where the domain columns go —
    honest by construction (the IR knows the products + kinds, not the business columns).
    """
    med = blueprint.get("medallion", {})
    contract_ref = med.get("silver", {}).get("data_contract_ref", "<silver-contract>")
    kinds = _gold_kinds(blueprint)
    out: dict[str, str] = {}
    doc = ["# Gold as Fabric Warehouse (generated — T-SQL / Warehouse endpoint)", "",
           "Warehouse-endpoint gold (research §4 deployment-pattern: Bronze/Silver-Lakehouse + "
           "Gold-Warehouse). One `CREATE TABLE` per gold product; populate via CTAS/`COPY INTO` from "
           "silver. **Honest boundary**: the IR gives product + kind, not the business columns "
           "(those live in the silver data contract → `TODO(contract:…)`).", "",
           "| Domain | Product | Kind | DDL |", "|---|---|---|---|"]
    for d in sorted(blueprint.get("mesh", {}).get("domains", []), key=lambda d: d.get("name", "")):
        c_ref = _domain_contract(d, contract_ref)
        ddir = _dirslug(d["name"])
        for product in sorted(d.get("data_products", [])):
            kind = kinds.get(product, "fact")
            rel = f"warehouse/{ddir}/gold_{_ident(product)}.sql"
            out[rel] = _warehouse_ddl(product, kind, c_ref, schemas=schemas,
                                      table=_catalog_table(governed_catalog, _ident(product)))
            doc.append(f"| {d['name']} | `{product}` | {kind} | `{rel}` |")
    out["warehouse/_WAREHOUSE_GOLD.md"] = "\n".join(doc) + "\n"
    return out


def _schnitt_spalten_tests(schnitt: tuple[str, ...]) -> list[dict]:
    """``not_null`` auf jede Schnittspalte — das Tor gegen die stille Berechtigungsluecke.

    **Gemessener Anlass 14.08.2026 (Kundenmandant, erster DQ-Lauf).** 562 Faktenzeilen fanden kein
    Projekt, ihre Vorfahrenspalten blieben leer, und ein Praedikat ``[org_niederlassung] =
    'Muenchen'`` trifft NULL nicht. Die Zeilen waren fuer jede Rolle unsichtbar. Das ist die
    teuerste Sorte Fehler, weil sie wie eine korrekte Berechtigung aussieht: wer zu wenig
    sieht, vermutet den Schnitt und nicht die Beladung.

    Der Fremdschluessel-Test daneben faengt das **nicht**. Er prueft die Verbindung zur
    Dimension; die Schnittspalten sind daraus abgeleitete Kopien auf der Faktenzeile, und
    genau die faellt aus, wenn die Verbindung ins Leere geht.
    """
    return [{"name": s,
             "description": (f"Schnittspalte der Zeilensicherheit — nie NULL, Waisen tragen "
                             f"'{UNBEKANNTES_MITGLIED}'. Eine leere Schnittspalte ist fuer "
                             f"jede Rolle unsichtbar."),
             "tests": ["not_null"]}
            for s in schnitt]


def _dq_model_entry(name: str, kind: str, contract_ref: str, columns: list[dict] | None = None,
                    schnitt: tuple[str, ...] = ()) -> dict:
    """dbt schema.yml model entry with kind-aware structural tests (runtime DQ gate per gold product).

    ``columns`` — when a caller can supply the CONCRETE column tests (e.g. the SAP standard pack knows the
    real keys + FK→dim relationships), pass them and the TODO placeholder is replaced with real tests.
    Otherwise the honest placeholder stands (the IR knows product + kind, not the business columns)."""
    if columns:
        cols = columns
    elif kind == "dimension":
        cols = [{"name": f"{name}_sk", "description": "surrogate key", "tests": ["not_null", "unique"]}]
    elif kind == "fact":
        cols = [{"name": "<dimension_foreign_key>",
                 "description": f"TODO(contract:{contract_ref}): FK not_null + relationships test",
                 "tests": ["not_null"]}]
    else:  # aggregate
        cols = [{"name": "<group_key>",
                 "description": f"TODO(contract:{contract_ref}): grouping grain not_null",
                 "tests": ["not_null"]}]
    # Die Schnittspalten kommen ZUSAETZLICH, nie statt der Schluesseltests: sie stehen auf einer
    # anderen Achse (wer darf die Zeile sehen) als der Schluessel (haengt die Zeile richtig).
    vorhanden = {c.get("name") for c in cols}
    cols = cols + [t for t in _schnitt_spalten_tests(schnitt) if t["name"] not in vorhanden]
    return {"name": f"gold_{_ident(name)}",
            "description": f"gold {kind} '{name}' — runtime DQ gate (Contract: {contract_ref})",
            "columns": cols}


def emit_dq_gates(blueprint: dict, schemas: bool = False,
                  column_tests: dict[str, list[dict]] | None = None) -> dict[str, str]:
    """Emit **runtime** data-quality gates for the strecke as dbt-style ``schema.yml`` tests.

    One ``dq/<domain>/schema.yml`` per domain (dbt ``version: 2`` models + kind-aware structural tests:
    dimension surrogate keys not_null+unique, fact FKs not_null) — the portable, industry-standard way
    to gate the strecke at **runtime**, not just at build. Honest by construction: the IR gives the
    product + kind + a surrogate/placeholder column, not the business columns → ``TODO(contract:…)``
    where the domain rules go. Ties into `emit_metricflow`/dbt; distinct from the governance-domain DQ
    (`provision_governance` ``data_quality.json``), which is policy, not per-hop model tests.

    ``column_tests`` — an optional ``{product_name: [dbt-column-dict]}`` of CONCRETE tests a caller can
    supply when it actually knows the columns (e.g. the SAP standard pack → real key not_null+unique and
    FK not_null + ``relationships`` to the referenced dim). Where present, real tests replace the
    ``TODO(contract:…)`` placeholder for that product; absent products keep the honest placeholder.
    """
    med = blueprint.get("medallion", {})
    contract_ref = med.get("silver", {}).get("data_contract_ref", "<silver-contract>")
    kinds = _gold_kinds(blueprint)
    ctests = column_tests or {}
    concrete = any(p in ctests for d in blueprint.get("mesh", {}).get("domains", [])
                   for p in d.get("data_products", []))
    out: dict[str, str] = {}
    doc = ["# Runtime DQ gates (generated — dbt schema.yml tests)", "",
           "Per-gold-product structural tests to gate the strecke at **runtime** (not just build). "
           "`dbt test` / a dbt-compatible runner enforces them. **Honest boundary**: structural tests "
           "the IR can know (surrogate-key not_null+unique, fact-FK not_null); business rules live in the "
           "silver data contract → `TODO(contract:…)`."
           + (" Products with a **concrete** column set (e.g. from the SAP standard pack) carry real "
              "key/FK/`relationships` tests instead of the placeholder. Composite keys get per-column "
              "`not_null` only — a combined-uniqueness check needs the `dbt_utils` package, kept out to "
              "stay tool-free; add `dbt_utils.unique_combination_of_columns` if that package is present."
              if concrete else ""),
           "",
           "**Row-security cut columns are gated too** (measured 2026-08-14): every protected product "
           f"gets `not_null` on each cut column, because a NULL there is a *silent authorization hole* — "
           f"`[col] = 'value'` never matches NULL, so the row is invisible to every role and looks like "
           f"a missing permission. Orphans carry the explicit unknown member `{UNBEKANNTES_MITGLIED}`, "
           "never NULL. The FK test does not cover this: the cut columns are ancestor copies on the "
           "fact row, and they are exactly what goes empty when the FK finds nothing.",
           "", "| Domain | schema.yml | Products |", "|---|---|---|"]
    for d in sorted(blueprint.get("mesh", {}).get("domains", []), key=lambda d: d.get("name", "")):
        c_ref = _domain_contract(d, contract_ref)
        prods = sorted(d.get("data_products", []))
        if not prods:
            continue
        # Nur die geschuetzten Produkte bekommen das Schnittspalten-Tor. Ein Produkt ausserhalb
        # von `protected_products` traegt die Spalten gar nicht, und ein `not_null` auf eine
        # Spalte, die es nicht gibt, laesst den Lauf aus dem falschen Grund scheitern.
        schnitt = schnittspalten(d)
        geschuetzt = set(d.get("row_security", {}).get("protected_products")
                         or (prods if schnitt else []))
        models = [_dq_model_entry(p, kinds.get(p, "fact"), c_ref, ctests.get(p),
                                  schnitt=schnitt if p in geschuetzt else ())
                  for p in prods]
        rel = f"dq/{_dirslug(d['name'])}/schema.yml"
        out[rel] = yaml.safe_dump({"version": 2, "models": models}, sort_keys=False, allow_unicode=True)
        doc.append(f"| {d['name']} | `{rel}` | {', '.join(f'`{p}`' for p in prods)} |")
    out["dq/_DQ_GATES.md"] = "\n".join(doc) + "\n"
    return out


# per-kind DQ policy: (constraint-name suffix, ON MISMATCH action). A bad dimension/aggregate row must
# stop the refresh (FAIL); a bad fact row is droppable (DROP) — a fact is an event stream, not a key table.
_MLV_POLICY = {"dimension": ("sk", "FAIL"), "fact": ("fk", "DROP"), "aggregate": ("grp", "FAIL")}
_MLV_KEY_SUFFIXES = ("_sk", "_fk", "_key", "_id")


def _gold_grains(blueprint: dict) -> dict[str, str]:
    return {p["name"]: p.get("grain", "")
            for p in blueprint.get("medallion", {}).get("gold", {}).get("data_products", [])}


def _mlv_catalog_columns(governed_catalog: dict | None, product_ident: str) -> list[str]:
    """Columns for a gold product from the governed catalog (try ``gold_<p>`` then ``<p>``). [] if none."""
    tables = {_ident(t.get("name", "")): sorted(set(t.get("columns", []) or []))
              for t in (governed_catalog or {}).get("tables", []) or []}
    return tables.get(f"gold_{product_ident}") or tables.get(product_ident) or []


def _catalog_table(governed_catalog: dict | None, product_ident: str) -> dict:
    """Der ganze Katalogeintrag zu einem Gold-Produkt (leer, wenn keiner da ist).

    ``_mlv_catalog_columns`` gab nur die Spaltennamen zurueck, und alles Weitere wurde danach aus
    Namen GERATEN. Der Katalog fuehrt seit dem 31.07.2026 aber `key` (deklariert, mit Herkunft)
    und `column_types` — beides ist besser als jede Endungsheuristik.
    """
    for t in (governed_catalog or {}).get("tables", []) or []:
        if _ident(t.get("name", "")) in (product_ident, f"gold_{product_ident}"):
            return t
    return {}


def _mlv_key_column(name_ident: str, kind: str, columns: list[str],
                    table: dict | None = None, katalog_vorhanden: bool = False) -> str | None:
    """Die DQ-Ankerspalte, oder None wenn sie ohne Vertrag nicht bekannt sein kann.

    Der DEKLARIERTE Schluessel aus dem Katalog geht vor. Er ist der Grund, warum die Pakete ihn
    ueberhaupt fuehren: `fact_gl_line` hat den Schluessel (RLDNR, RBUKRS, BELNR, GJAHR, DOCLN),
    und keine Endung darin sagt "Schluessel". Die Heuristik fand ihn nicht und liess die
    Bedingung als Kommentar stehen — an einem Modell, das den Schluessel deklariert danebenhaengen
    hatte.
    """
    schluessel = list((table or {}).get("key") or [])
    if schluessel:
        # Die Bedingung prueft auf NOT NULL; dafuer genuegt der erste Schluesselteil, und er ist
        # der stabilste. Ein CHECK ueber alle Teile waere strenger, aber MLV-Bedingungen sind
        # einspaltig formuliert.
        return schluessel[0]
    if kind == "dimension":
        sk = f"{name_ident}_sk"
        if sk in columns:
            return sk
        if not columns and not katalog_vorhanden:
            # Gar kein Katalog: die Projektion ist ohnehin `SELECT *`, der Ersatzschluessel
            # koennte in Silber existieren. Die Konvention ist dann eine vertretbare Vermutung.
            return sk
        if not columns:
            # Katalog vorhanden, aber dieses Produkt steht nicht darin -- wir wissen NICHTS
            # ueber seine Spalten. Eine leere Liste ist kein Beleg dafuer, dass der
            # Ersatzschluessel existiert. Gemessen 13.08.2026 an `dim_datum`,
            # `dim_organisation` und `dim_strategie`: alle drei bekamen eine aktive
            # Bedingung auf eine Spalte, die niemand erzeugt.
            return None
        # KEIN Rueckfall auf `<name>_sk`, wenn er nicht in der Projektion steht.
        #
        # Bis 13.08.2026 gab dieser Zweig `sk` auch dann zurueck, wenn ihn niemand erzeugt --
        # der Ersatzschluessel entsteht erst in der Silber->Gold-Modellierung, und der
        # Transform-Emitter fuehrt ihn selbst als TODO. Die MLV pruefte damit auf eine Spalte,
        # die es nicht gibt: MLV_CONSTRAINT_SCHEMA_VIOLATION an vier von zwoelf Sichten, und
        # zwar genau an denen, die sonst gelaufen waeren.
        #
        # `None` heisst hier nicht "kein Schluessel", sondern "noch nicht bekannt" -- der
        # Aufrufer macht daraus einen TODO-Kommentar statt einer Bedingung. Eine Pruefung auf
        # eine erfundene Spalte ist schlimmer als keine Pruefung.
        return next((c for c in columns if c.endswith(("_sk", "_id", "_key"))), None)
    # fact / aggregate ohne Katalog: nur ein Vertrag koennte den Schluessel ehrlich benennen
    return next((c for c in columns if c.endswith(_MLV_KEY_SUFFIXES)), None)


def _mlv_partition_column(columns: list[str], table: dict | None = None) -> str | None:
    """Die Partitionsspalte — aus dem DEKLARIERTEN Typ, nicht aus dem Spaltennamen.

    Die alte Namensheuristik suchte nach "date" in der Spalte. Bei SAP-Feldnamen scheitert das
    systematisch: BUDAT, BLDAT, ERDAT, AUSVN und LTRMI sind Datumsspalten und enthalten das Wort
    nicht. Der Katalog fuehrt `column_types` mit dem deklarierten logischen Typ; das ist dieselbe
    Luecke, die schon einmal ein Datum als String ins Semantikmodell gebracht hat.
    """
    typen = (table or {}).get("column_types") or {}
    datum = [c for c in columns if str(typen.get(c, "")).lower() == "date"]
    if datum:
        return sorted(datum)[0]
    for c in columns:
        lc = c.lower()
        if "date" in lc or lc in ("year", "month", "day") or lc.endswith(("_year", "_month", "_day")):
            return c
    return None


def _mlv_constraint(name: str, kind: str) -> tuple[str, str]:
    """Back-compat kind-aware constraint (convention keys). Prefer the catalog-aware path in ``emit_mlv``."""
    suffix, action = _MLV_POLICY.get(kind, _MLV_POLICY["fact"])
    col = f"{name}_sk" if kind == "dimension" else f"{name}_{suffix}"
    return (f"    CONSTRAINT {name}_{suffix}_not_null CHECK ({col} IS NOT NULL) ON MISMATCH {action}", col)


def emit_mlv(blueprint: dict, schemas: bool = True,
             governed_catalog: dict | None = None) -> dict[str, str]:
    """Emit the medallion as **Materialized Lake Views** (declarative, SQL-only). Idea I-20.7.

    PREVIEW / SQL-only, honestly flagged. One ``CREATE OR REPLACE MATERIALIZED LAKE VIEW`` per gold
    product per the official MLV grammar (MS Learn):
    ``CREATE … VIEW name (CONSTRAINT … CHECK … ON MISMATCH DROP|FAIL) [PARTITIONED BY(…)] COMMENT …
    TBLPROPERTIES(…) AS SELECT …``.

    Honest by construction and **always valid SQL**:

    * **DQ constraint** — kind-aware (dimension SK/FAIL · fact FK/DROP · aggregate group/FAIL). The key
      column is taken from ``governed_catalog`` when supplied, else the dimension SK convention; when the
      key genuinely can't be known (fact/aggregate, no catalog) the constraint is emitted as a **template
      comment** above the statement rather than an un-parseable ``<placeholder>`` inside a ``CHECK``.
    * **Projection** — with a ``governed_catalog`` the ``SELECT`` lists the real columns; without one it
      stays ``SELECT *`` + a ``TODO(contract)`` marker (never invents columns).
    * **PARTITIONED BY** — emitted only for a real date-ish catalog column; otherwise the grain is noted
      as a partition TODO comment (grain is prose, not a column).
    * **TBLPROPERTIES** — deterministic provenance tags (generator/layer/kind), always valid.

    MLV dependency management + refresh is automatic (the engine chains views by their SELECT refs) — so
    the emitter emits **no** orchestration DAG. Non-SQL logic (ML/Python/API) is out of MLV scope → the
    doc points at the notebook fallback (``emit_notebooks``). Deterministic; emits only.
    """
    med = blueprint.get("medallion", {})
    contract_ref = med.get("silver", {}).get("data_contract_ref", "<silver-contract>")
    kinds = _gold_kinds(blueprint)
    grains = _gold_grains(blueprint)
    grounded = "governed catalog" if governed_catalog else "IR skeleton (no catalog → SELECT * + TODO)"
    out: dict[str, str] = {}
    # Materialized Lake Views REQUIRE a schema-enabled lakehouse (MS Learn: "Features like
    # materialized lake views require schema-enabled lakehouses"). Emitting them against a flat
    # dbo lakehouse produces DDL that simply cannot run there — and nothing in the DDL says so,
    # which is the worst kind of failure: it reads as finished work and dies at deploy time.
    schema_warning = ([] if schemas else [
        "> ⚠️ **These views cannot run in the target lakehouse as configured.** Materialized Lake "
        "Views require a **schema-enabled** lakehouse; this set was emitted with the flat `dbo` "
        "layout (`--no-lakehouse-schemas`). Either enable schemas (the default) or use the "
        "notebook/SQL transforms (`--emit-transforms`) instead — those work in both layouts.", ""])
    doc = ["# Materialized Lake Views — declarative medallion (generated — PREVIEW, SQL-only)", "",
           *schema_warning,
           "> **PREVIEW & SQL-only** (Fabric Materialized Lake Views): region-limited; the grammar may "
           "change before GA (tracked by `make check-upstream` feature-watch → I-20.7). Non-SQL logic "
           "(ML/Python/API/cleansing beyond SQL) is out of scope → use the notebook transforms "
           "(`--emit-notebooks`) for those hops. MLV **dependency management + refresh is automatic** "
           "(the engine chains views by their SELECT refs) — no separate orchestration DAG is emitted.",
           "", f"Silver data contract: `{contract_ref}`  ·  grounded in: **{grounded}**", "",
           "| Domain | MLV | Kind | Cols | DQ constraint | Partition |", "|---|---|---|---|---|---|"]
    for d in sorted(blueprint.get("mesh", {}).get("domains", []), key=lambda d: d.get("name", "")):
        c_ref = _domain_contract(d, contract_ref)
        ddir = _dirslug(d["name"])
        dident = _ident(d["name"])
        silver_tbl = layer_ref("silver", dident, schemas)
        # Dieselbe Herkunftsfrage wie im Transform-Emitter: eine MLV, die aus
        # `silver.<domaene>` liest, liest aus einer Tabelle, die es bei aufgeschluesseltem
        # Silber nicht gibt. Gemessen 12.08.2026: alle zwoelf MLV zeigten dorthin.
        herkunft = _silber_herkunft(governed_catalog, d)
        for product in sorted(d.get("data_products", [])):
            pident = _ident(product)
            kind = kinds.get(product, "fact")
            suffix, action = _MLV_POLICY.get(kind, _MLV_POLICY["fact"])
            mlv_name = layer_ref("gold", pident, schemas)
            # Die Quelle DIESES Produkts. Mehrere Herkuenfte werden hier NICHT vereinigt --
            # ob vereinigt oder verbunden gehoert, ist dieselbe offene Fachfrage wie im
            # Transform-Pfad, und eine MLV ist der falsche Ort, sie stillschweigend zu
            # beantworten. Dann bleibt es beim Domaenenverweis plus TODO.
            eigene = [layer_ref("silver", _ident(q), schemas)
                      for q in herkunft.get(pident, [])]
            von = eigene[0] if len(eigene) == 1 else silver_tbl
            columns = _mlv_catalog_columns(governed_catalog, pident)
            kat = _catalog_table(governed_catalog, pident)
            key_col = _mlv_key_column(pident, kind, columns, kat,
                                      katalog_vorhanden=bool(governed_catalog))

            preamble = [
                f"-- silver → gold '{product}' as a Materialized Lake View ({kind}).  PREVIEW / SQL-only.",
                f"-- Contract: {c_ref}  ·  refresh + dependency mgmt automatic (no orchestration)."]

            # --- #1 DQ constraint: active when the key is known, else a valid template comment ----------
            if key_col:
                constraint_block = (f" (\n    CONSTRAINT {pident}_{suffix}_not_null "
                                    f"CHECK ({key_col} IS NOT NULL) ON MISMATCH {action}\n)")
                constraint_cell = f"`… CHECK ({key_col} …) ON MISMATCH {action}`"
            else:
                constraint_block = ""
                preamble.append(
                    f"-- TODO(contract:{c_ref}): add the DQ constraint once the key column is known — "
                    f"CONSTRAINT {pident}_{suffix}_not_null CHECK (<{kind}_key> IS NOT NULL) ON MISMATCH {action}")
                constraint_cell = f"template (no catalog key) · ON MISMATCH {action}"

            # --- #3 partition: real date-ish catalog column, else the grain as a TODO comment ----------
            part_col = _mlv_partition_column(columns, kat)
            grain = grains.get(product, "")
            if part_col:
                # Maskieren wie in der Projektion. Die Partitionsklausel wurde beim
                # `zitiere`-Durchgang uebersehen: `PARTITIONED BY (Month-Year-Date)` ist ein
                # Syntaxfehler, waehrend zwei Zeilen tiefer `` `Month-Year-Date` `` korrekt
                # steht. Gemessen 13.08.2026 an `fact_phase`: ParseException.
                partition_clause = f"\nPARTITIONED BY ({zitiere(part_col)})"
                partition_cell = f"`{part_col}`"
            else:
                if grain:
                    preamble.append(f"-- TODO: PARTITIONED BY (<column>) — grain '{grain}' has no resolved "
                                    f"partition column (supply one via the governed catalog).")
                partition_clause = ""
                partition_cell = f"grain '{grain}'" if grain else "—"

            # --- #2 projection: real columns from the catalog, else SELECT * + TODO ---------------------
            if columns:
                # MLV gibt es nur auf Fabric/Spark -- `zitiere` nimmt dort Backticks, das ist
                # die Vorgabe. Ein `stack`-Parameter waere hier eine Wahl, die es nicht gibt.
                select_body = ("SELECT\n"
                               + ",\n".join(f"    {zitiere(c)}" for c in columns)
                               + f"\nFROM {von};")
            else:
                select_body = (f"SELECT\n    -- TODO(contract:{c_ref}): {kind} columns, keys, "
                               f"measures from the silver contract\n    *\nFROM {von};")
            if len(eigene) > 1:
                preamble.append(
                    f"-- TODO(contract:{c_ref}): '{product}' entsteht aus {len(eigene)} Herkuenften "
                    f"({', '.join(eigene)}). Ob vereinigt oder verbunden gehoert, ist offen — "
                    f"siehe `transforms/…/silver_to_gold__{pident}.sql`. Bis dahin verweist diese "
                    f"Sicht auf die Domaenentabelle und ist nicht lauffaehig.")

            # --- #3 tblproperties: deterministic provenance tags (always valid) -------------------------
            #
            # `columnMapping` gehoert auch hierher: eine MLV materialisiert als Delta-Tabelle,
            # und Delta verbietet ' ,;{}()=' in Spaltennamen. Gemessen 13.08.2026 an
            # `fact_strategie`: MLV_RUNTIME_ERROR / DELTA_INVALID_CHARACTERS_IN_COLUMN_NAMES,
            # obwohl die Projektion die Namen korrekt maskiert -- die Maskierung macht den
            # Namen zitierfaehig, nicht die ZIELtabelle aufnahmefaehig. Das sind zwei Dinge.
            tblprops = (f"\nTBLPROPERTIES ('generated_by' = 'meridian-dataarch', "
                        f"'medallion_layer' = 'gold', 'mlv_kind' = '{kind}', "
                        f"'delta.columnMapping.mode' = 'name', "
                        f"'delta.minReaderVersion' = '2', 'delta.minWriterVersion' = '5')")

            sql = ("\n".join(preamble) + "\n"
                   f"CREATE OR REPLACE MATERIALIZED LAKE VIEW {mlv_name}{constraint_block}{partition_clause}\n"
                   f"COMMENT 'gold {kind} {product} (generated, MLV preview)'"
                   f"{tblprops}\n"
                   f"AS\n{select_body}\n")
            out[f"mlv/{ddir}/{pident}.mlv.sql"] = sql
            doc.append(f"| {d['name']} | `{mlv_name}` | {kind} | {len(columns) or '—'} | "
                       f"{constraint_cell} | {partition_cell} |")
    out["mlv/_MLV.md"] = "\n".join(doc) + "\n"
    return out
