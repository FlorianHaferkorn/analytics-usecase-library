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


def sql_anweisungen(text: str) -> list[str]:
    """Anweisungen einer Datei: Zeilenkommentare weg, auf `;` trennen -- ausser in Zeichenketten.

    Das `;` in `COMMENT 'Anzahl verletzender Zeilen; NULL wenn ...'` ist keine Trennung.
    Gemessen 02.09.2026: ohne diese Ruecksicht zerfiel `dq_historie.sql` in drei Teile,
    von denen zwei Syntaxfehler waren, die es in der Datei nicht gibt."""
    zeilen = []
    for ln in text.splitlines():
        out, q, i = [], False, 0
        while i < len(ln):
            c = ln[i]
            if c == "'":
                q = not q
            if not q and ln.startswith("--", i):
                break
            out.append(c)
            i += 1
        zeilen.append("".join(out))
    body = "\n".join(zeilen)
    teile, cur, q = [], [], False
    for c in body:
        if c == "'":
            q = not q
        if c == ";" and not q:
            teile.append("".join(cur))
            cur = []
        else:
            cur.append(c)
    teile.append("".join(cur))
    return [s.strip() for s in teile if s.strip()]


def _dialect(stack: str) -> dict:
    """Minimal per-stack SQL dialect knobs (fabric/databricks = Spark; snowflake = SF).

    Trägt den Stack mit: nicht jede Aussage im generierten SQL ist Syntax. Der Direct-Lake-Hinweis
    zur Serving-Schicht etwa gilt nur auf Fabric — er landete bisher als Kommentar auch in
    Snowflake-MERGEs und war dort einfach falsch (Inhalts-Paritäts-Sensor, SL-2607-3 Befund 2).
    """
    if stack == "snowflake":
        return {"ctas": "CREATE OR REPLACE TABLE", "using": "", "comment": "--", "stack": stack,
                "tblprops": "", "hash64": "HASH", "heute": "CURRENT_DATE()",
                "jetzt": "CURRENT_TIMESTAMP()"}
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
            "stack": stack, "hash64": "xxhash64", "heute": "current_date()",
            "jetzt": "current_timestamp()",
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


def doppelt_geladene_quellen(blueprint: dict) -> list[dict]:
    """Quelltabellen, die die Aufnahme unter mehreren Domaenen **zweimal** laedt (OQ-42, D-535).

    Gemessen am SAP-Szenario (23.09.2026): das IR fuehrt `mara` zweimal —
    `order_to_cash_mara` und `inventory_mm_mara`, zwei Kopier-Schritte aus demselben
    Quellsystem auf dieselbe Tabelle. Die synthetische Quelle legt sie einmal an; daher die
    Kettenbefunde, die OQ-42 der „Aufnahme, die nie laedt“ zuschrieb. Die Aufnahme laedt sie
    — doppelt. Zwei Kopien derselben Tabelle, zu verschiedenen Zeiten geladen, laufen
    auseinander, und das konforme Ziel darueber traegt dann zwei Fassungen desselben
    Schluessels.

    Erkannt wird die Namensform ``<domaene>_<tabelle>`` im selben ``source_system``: gleicher
    Rest nach dem Domaenenpraefix, verschiedene Domaenen. Quellen ohne diese Form werden nicht
    verglichen — lieber ein Befund zu wenig als einer, der auf einer Namensaehnlichkeit
    beruht, die nichts bedeutet.
    """
    gruppen: dict[tuple[str, str], list[tuple[str, str]]] = {}
    for e in blueprint.get("ingestion", []) or []:
        quelle, dom = e.get("source") or "", e.get("domain") or ""
        praefix = _ident(dom) + "_"
        if not dom or not _ident(quelle).startswith(praefix):
            continue
        rest = _ident(quelle)[len(praefix):]
        gruppen.setdefault((e.get("source_system") or "", rest), []).append((dom, quelle))
    return [{"quellsystem": sys_, "tabelle": rest,
             "quellen": sorted(q for _, q in eintraege),
             "domaenen": sorted({d for d, _ in eintraege})}
            for (sys_, rest), eintraege in sorted(gruppen.items())
            if len({d for d, _ in eintraege}) > 1]


def silber_tabellen(blueprint: dict, governed_catalog: dict | None = None,
                    schemas: bool = False) -> list[str]:
    """Die Silber-Tabellen, die die Emission **wirklich** anlegt — je Herkunftstabelle.

    Oeffentlich, weil sie einen zweiten Leser hat: `provision_lifecycle` pflegte
    `silver.<domaene>`, und diese Tabelle gibt es seit dem 12.08.2026 nicht mehr. Gemessen
    am SAP-Szenario unter Spark (18.09.2026): **8 der 21 Kettenbefunde** kamen aus dieser
    einen Zeile — `ALTER TABLE silver.order_to_cash` und `OPTIMIZE silver.order_to_cash`
    je Domaene.

    Damit ist es die dritte Fundstelle derselben Klasse (D-501, D-521): eine Entscheidung
    bindet die Datei, in der sie getroffen wurde. Deshalb steht die Auskunft jetzt **an
    einer** Stelle und wird gelesen, statt an jeder Stelle neu gebildet (D-505).

    Ohne Aussage des Katalogs zur Herkunft bleibt es beim Zuschnitt je Domaene — derselbe
    Grund wie im Vollaufbau: ein geratener Zuschnitt waere schlimmer als ein grober.
    """
    domains = sorted(blueprint.get("mesh", {}).get("domains", []),
                     key=lambda d: d.get("name", ""))
    raus: list[str] = []
    for d in domains:
        herkunft = _herkunft_je_domaene(blueprint, governed_catalog, d, domains)
        if herkunft:
            raus += [layer_ref("silver", _ident(q), schemas)
                     for qs in herkunft.values() for q in qs]
        else:
            raus.append(layer_ref("silver", _ident(d.get("name", "")), schemas))
    return sorted(set(raus))


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


#: Die Werte, die eine `DATA-SILVER-LOAD`-Antwort tragen kann (Optionen-Katalog in
#: `decision_proposals._OPTIONEN["DATA-SILVER-LOAD"]`). Hier genannt aus demselben Grund wie
#: `_DATA_INC_WERTE`: ein unbekannter Wert steht als Befund im Kopf, nicht still als Vorgabe.
_DATA_SILVER_LOAD_WERTE = ("vollaufbau", "append", "merge")


def _mit_cdf(tblprops: str) -> str:
    """Dieselben Tabelleneigenschaften plus Change Data Feed — auf Delta-Stacks.

    Ohne CDF auf **allen** Quellen aktualisiert Fabric eine Materialized Lake View nie
    inkrementell (MS Learn, *Optimal refresh*, abgerufen 23.09.2026). Snowflake kennt die
    Eigenschaft nicht; dort bleibt es beim leeren Wert.
    """
    if not tblprops.rstrip().endswith(")"):
        return tblprops
    return tblprops.rstrip()[:-1] + ", 'delta.enableChangeDataFeed' = 'true')"


def quellspalten(governed_catalog: dict | None, quelle: str) -> list[str]:
    """Die Spalten einer Quelltabelle, soweit der governte Katalog sie nennt.

    Der Katalog fuehrt sie bei mehreren Herkuenften je Quelle (`source_columns`); speist eine
    Quelle ein Produkt allein, sind dessen `columns` ihre Spalten. Gelesen wird nur, was ein
    Produkt liest — die Vereinigung ist deshalb eine **Untergrenze** der Tabelle, genug, um
    eine Aenderungsspalte zu finden, nicht genug fuer eine Projektion.
    """
    raus: set[str] = set()
    for t in (governed_catalog or {}).get("tables") or []:
        raus |= set(((t.get("source_columns") or {}).get(quelle)) or [])
        if list(t.get("sources") or []) == [quelle]:
            raus |= set(t.get("columns") or [])
    return sorted(raus)


def _spaltentyp(governed_catalog: dict | None, spalte: str) -> str:
    """Der logische Typ einer Spalte, sofern ein Gold-Produkt ihn fuehrt (`column_types`)."""
    for t in (governed_catalog or {}).get("tables") or []:
        typ = (t.get("column_types") or {}).get(spalte)
        if typ:
            return str(typ)
    return ""


#: Woher eine Angabe zur Quelltabelle stammt, in Worten fuer den Dateikopf (D-539).
_HERKUNFT_WORT = {"paket": "deklariert im Standardpaket",
                  "heuristik": "abgeleitet aus dem Spaltennamen — bestaetigen",
                  "kuratiert": "kuratiert"}


def _quelltabelle(governed_catalog: dict | None, quelle: str) -> dict:
    """Der Eintrag `source_tables[quelle]` des Katalogs (D-539) — leer, wenn es keinen gibt."""
    return ((governed_catalog or {}).get("source_tables") or {}).get(quelle) or {}


def _silber_watermark(governed_catalog: dict | None, quelle: str) -> str | None:
    """Die Aenderungs- oder Anlagespalte einer Quelle.

    Zuerst aus `source_tables` (mit Herkunft, D-539), sonst dieselbe Heuristik wie DATA-INC
    ueber die Spalten, die Gold-Produkte aus der Quelle lesen.
    """
    eintrag = _quelltabelle(governed_catalog, quelle)
    if eintrag.get("watermark"):
        return eintrag["watermark"]
    if eintrag.get("watermark_keine"):
        # Kuratiert: keine Aenderungsspalte. Ist die Tabelle unveraenderlich, traegt die
        # Anlagespalte (D-547) — sonst nichts, und die Heuristik fragt nicht nach.
        return eintrag.get("anlage") if eintrag.get("unveraenderlich") else None
    from core.dataarch_engine.blueprint.decision_proposals import _WATERMARK_HINTS, _rank
    wm = sorted(((_rank(c, _WATERMARK_HINTS), c) for c in quellspalten(governed_catalog, quelle)),
                key=lambda x: (-x[0], x[1]))
    return next((c for w, c in wm if w > 0), None)


#: Namensteile eines **Anlage**datums. Fuer `append` taugt es als Watermark; fuer `merge` nicht:
#: eine spaetere Aenderung an einer alten Zeile hat ein altes Anlagedatum und kommt nie an.
_ANLAGE_HINWEISE = ("erdat", "ersda", "created", "erstellt", "anlage")

QUELLMETADATEN_SCHEMA = "meridian/quellmetadaten/v1"
#: Silber-Ladeform je Quelltabelle, kuratiert (D-558): Hashvergleich mit Fabric-Stempel.
SILBER_HASHVERGLEICH = "hashvergleich"
#: Die Spalte, die Fabric bei jeder erkannten Aenderung in Silber setzt (D-558).
FABRIC_STEMPEL = "_geaendert_am"


def kuratiere_quelltabellen(governed_catalog: dict, kuratiert: dict) -> dict:
    """Kuratierte Angaben zu Quelltabellen in den Katalog uebernehmen — geprueft beim Schreiben.

    Die Lehre aus Analytixus (D-539): abgeleitete und bestaetigte Metadaten getrennt fuehren,
    und die Engine prueft, was hineinkommt — auch wenn ein Mensch oder ein Modell es liefert.
    Geprueft wird hier: das Schema, dass jede genannte Quelle im Katalog **existiert** (ein
    Tippfehler waere sonst eine Angabe, die nie greift, und nichts wird rot), und dass `key`
    eine Liste ist. Eine Spalte, die der Katalog nicht kennt, wird angenommen — Pakete fuehren
    nur einen Teil der Felder (`LAEDA` fehlt in `MARA`) —, aber als solche vermerkt.

    Form: ``{"schema": "meridian/quellmetadaten/v1", "quellen": {"<quelle>": {"key": [...],
    "watermark": "...", "von": "...", "am": "JJJJ-MM-TT"}}}``. Rueckgabe: ein neuer Katalog.
    """
    if (kuratiert or {}).get("schema") != QUELLMETADATEN_SCHEMA:
        raise ValueError(f"Quellmetadaten: schema muss {QUELLMETADATEN_SCHEMA!r} sein")
    vorhanden = dict((governed_catalog or {}).get("source_tables") or {})
    unbekannt = sorted(set(kuratiert.get("quellen") or {}) - set(vorhanden))
    if unbekannt:
        raise ValueError(f"Quellmetadaten nennen Quellen, die der Katalog nicht fuehrt: "
                         f"{', '.join(unbekannt)} (bekannt: {', '.join(sorted(vorhanden)) or '—'})")
    for quelle, angabe in sorted((kuratiert.get("quellen") or {}).items()):
        e = {**vorhanden[quelle]}
        wer = ", ".join(x for x in (angabe.get("von"), angabe.get("am")) if x)
        if "key" in angabe:
            if not isinstance(angabe["key"], list) or not all(isinstance(k, str) for k in angabe["key"]):
                raise ValueError(f"Quellmetadaten {quelle}: key muss eine Liste von Spaltennamen sein")
            e.update(key=list(angabe["key"]), key_herkunft="kuratiert", key_von=wer)
        if angabe.get("watermark"):
            e.update(watermark=str(angabe["watermark"]), watermark_herkunft="kuratiert",
                     watermark_von=wer)
        elif "watermark" in angabe:
            # Ausdruecklich **keine** Aenderungsspalte (D-544): die Tabelle hat keine verlaessliche
            # (EKKO-AEDAT ist laut DDIC ein Anlagedatum). Das ist eine Angabe, keine Luecke —
            # sie verdraengt auch die Heuristik, die sonst genau diese Falle wieder faende.
            e.pop("watermark", None)
            e.update(watermark_herkunft="kuratiert", watermark_von=wer, watermark_keine=True)
        for feld in ("hinweis", "beleg"):
            if angabe.get(feld):
                e[f"watermark_{feld}"] = str(angabe[feld])
        # D-547: eine **unveraenderliche** Tabelle (Buchungszeilen, Warenbewegungen, Historie)
        # braucht keine Aenderungsspalte — neue Zeilen erkennt man an der Anlage. Beides wird
        # ausdruecklich gesagt, nicht aus dem Namen geschlossen.
        if "unveraenderlich" in angabe:
            if not isinstance(angabe["unveraenderlich"], bool):
                raise ValueError(f"Quellmetadaten {quelle}: unveraenderlich muss true/false sein")
            e["unveraenderlich"] = angabe["unveraenderlich"]
        if angabe.get("anlage"):
            e.update(anlage=str(angabe["anlage"]), anlage_von=wer)
        if "silber" in angabe:
            # D-558: Silber per Hashvergleich — Fabric stempelt die Aenderung selbst. Braucht den
            # Schluessel der Quelltabelle (ohne ihn gibt es kein „dieselbe Zeile“) und einen
            # Vollauszug in Bronze (sonst waere jede fehlende Zeile eine Loeschung).
            if angabe["silber"] != SILBER_HASHVERGLEICH:
                raise ValueError(f"Quellmetadaten {quelle}: silber kennt nur "
                                 f"{SILBER_HASHVERGLEICH!r}, nicht {angabe['silber']!r}")
            if not (e.get("key") or []):
                raise ValueError(f"Quellmetadaten {quelle}: silber = {SILBER_HASHVERGLEICH} "
                                 f"braucht den Schluessel der Quelltabelle")
            e.update(silber=SILBER_HASHVERGLEICH, silber_von=wer)
        bekannt = set(e.get("columns") or [])
        fremd = sorted({*(angabe.get("key") or []),
                        *([angabe["watermark"]] if angabe.get("watermark") else []),
                        *([angabe["anlage"]] if angabe.get("anlage") else [])} - bekannt)
        if fremd:
            e["nicht_im_katalog"] = fremd
        vorhanden[quelle] = e
    tabellen = _kuratiere_gold(governed_catalog, kuratiert.get("gold") or {})
    return {**governed_catalog, "tables": tabellen,
            "source_tables": dict(sorted(vorhanden.items()))}


#: Die drei Formen, in denen Gold Geschichte haelt, die die Quelle nicht haelt (D-551..D-553).
GOLD_HISTORIENFORMEN = ("scd", "stichtag", "periode")
#: Technische Spalten der Typ-2-Historie. Deutsch wie der Rest der Lieferung.
SCD_SPALTEN = ("gueltig_ab", "gueltig_bis", "ist_aktuell")
STICHTAG_SPALTE = "stichtag"


def scd_bezuege(governed_catalog: dict | None, product: str,
                schemas: bool = True) -> list[dict]:
    """Die Fremdschluessel eines Faktums, die auf eine Dimension mit Typ-2-Historie zeigen (D-559).

    Je Bezug: Fremdschluesselspalte, Dimension, deren Schluesselspalte, der Ersatzschluessel der
    Historie, die neue Faktenspalte (`<fk>_sk`) und das Belegdatum — die Spalte, ueber die das
    Faktum an der Zeitachse haengt. Ohne Zeitachse gilt die aktuelle Version.
    """
    gc = governed_catalog or {}
    tabs = {t.get("name"): t for t in gc.get("tables") or []}
    # Die Zeitachse erkennt der Katalog an `generated` (eine erzeugte Datumsdimension, D-347) —
    # nicht am Namen: `provision_transforms` wird nach ALUCA gespiegelt, `sap_calendar` nicht.
    achsen = {n for n, t in tabs.items() if t.get("generated") and t.get("kind") == "dimension"}
    datum = next((r["from_column"] for r in gc.get("relationships") or []
                  if r.get("from_table") == product and r.get("to_table") in achsen), None)
    out = []
    for k in gc.get("fremdschluessel") or []:
        if k.get("from_table") != product:
            continue
        h = (tabs.get(k.get("to_table")) or {}).get("historisierung") or {}
        if h.get("form") != "scd":
            continue
        out.append({"fk": k["from_column"], "dim": k["to_table"], "dim_spalte": k["to_column"],
                    "sk": h["sk"], "spalte": f"{k['from_column']}_sk", "aktiv": k.get("aktiv", True),
                    "historie": layer_ref("gold", _ident(k["to_table"]) + "_historie", schemas),
                    "datum": datum})
    return sorted(out, key=lambda b: b["spalte"])


def _mit_ersatzschluesseln(select_sql: str, bezuege: list[dict], dl: dict) -> str:
    """Haengt je Bezug den Ersatzschluessel der zum Belegdatum gueltigen Version an (D-559).

    Halboffen wie die Historie: `gueltig_ab <= Beleg < gueltig_bis`, leer heisst offen. LEFT
    JOIN — ein Beleg ohne passende Version bleibt stehen, mit leerem Schluessel, statt zu
    verschwinden. Belegdatum und `gueltig_ab` muessen dieselbe Darstellung haben (SAP: DATS).
    """
    z = lambda x: zitiere(x, dl["stack"])                                   # noqa: E731
    spalten, joins = [], []
    for i, b in enumerate(bezuege, 1):
        h = f"h{i}"
        bed = [f"{h}.{z(b['dim_spalte'])} = f.{z(b['fk'])}"]
        if b.get("datum"):
            d = f"f.{z(b['datum'])}"
            bed += [f"({h}.gueltig_ab IS NULL OR {d} >= {h}.gueltig_ab)",
                    f"({h}.gueltig_bis IS NULL OR {d} < {h}.gueltig_bis)"]
        else:
            bed.append(f"{h}.ist_aktuell")
        joins.append(f"LEFT JOIN {b['historie']} AS {h}\n    ON " + "\n   AND ".join(bed))
        spalten.append(f"{h}.{b['sk']} AS {z(b['spalte'])}")
    return (f"SELECT f.*, {', '.join(spalten)}\nFROM (\n{_einruecken(select_sql, 4)}\n) AS f\n"
            + "\n".join(joins))


def _bezugs_kopf(bezuege: list[dict], c: str) -> list[str]:
    if not bezuege:
        return []
    return ([f"{c}", f"{c} ERSATZSCHLUESSEL ZUM BELEGDATUM (D-559): je Bezug die Version der "
                     f"Dimension, die am Belegdatum galt."]
            + [f"{c}   {b['spalte']} → {b['historie']}.{b['sk']} ueber {b['fk']}"
               + (f", Belegdatum {b['datum']}" if b.get("datum") else
                  ", keine Zeitachse — aktuelle Version")
               + ("" if b.get("aktiv", True) else " (inaktive Beziehung im Modell)")
               for b in bezuege]
            + [f"{c}   Ein spaeter erkannter Wechsel aendert bereits geladene Zeilen erst mit dem "
               f"naechsten Vollaufbau."])


def perioden_quellen(governed_catalog: dict | None, schemas: bool = True,
                     bp: dict | None = None) -> dict[str, dict]:
    """Quellen, deren Aufnahme sich auf ein Periodenfenster begrenzen laesst (D-557).

    Voraussetzung ist D-553: das Gold-Produkt haelt seine Perioden selbst (`periode`) und liest
    genau **eine** Quelle. Dann braucht die Aufnahme nur die Jahre ab dem juengsten in Gold —
    aeltere Perioden schreibt der MERGE ohnehin nicht mehr. Rueckgabe je Quelle: Gold-Tabelle,
    Jahres- und Monatsspalte, SAP-Tabellenname (falls der Katalog ihn fuehrt).

    Mit ``bp`` nur Quellen, die per **Kopie** aufgenommen werden (D-565): das Fenster ist eine
    Abfrage der Kopieraktivitaet. Bei Mirroring oder Shortcut gibt es keine, und ein Fenster-
    Notebook ohne Verbraucher waere ein ausgeliefertes Artefakt, das nie laeuft.
    """
    kopie = None
    if bp is not None:
        kopie = {e.get("source") for e in bp.get("ingestion") or []
                 if e.get("access_mode") == "copy"}
    out: dict[str, dict] = {}
    for t in (governed_catalog or {}).get("tables") or []:
        h = t.get("historisierung") or {}
        quellen = list(t.get("sources") or [])
        if h.get("form") != "periode" or len(quellen) != 1:
            continue
        if kopie is not None and quellen[0] not in kopie:
            continue
        e = _quelltabelle(governed_catalog, quellen[0])
        out[quellen[0]] = {"gold": layer_ref("gold", _ident(t["name"]), schemas),
                           "produkt": t["name"], "jahr": h["spalten"][0],
                           "monat": h["spalten"][1], "sap_tabelle": e.get("sap_tabelle") or ""}
    return out


def _kuratiere_gold(governed_catalog: dict, gold: dict) -> list[dict]:
    """Der `gold`-Block der kuratierten Metadaten: wie ein Gold-Produkt Geschichte haelt.

    Drei Formen, je Produkt hoechstens eine (D-551..D-553):

    - ``scd``: Dimension mit Typ-2-Historie. ``typ2`` nennt die Attribute, deren Aenderung eine
      neue Version erzeugt, ``typ1`` die, die ueberschrieben werden; ``befund`` haelt Attribute
      fest, die weder das eine noch das andere sein sollten (MEINS: eine geaenderte
      Basismengeneinheit ist ein Datenfehler, keine Geschichte).
    - ``stichtag``: Faktum, dessen Quelle nur den aktuellen Stand kennt (offene Posten). Jeder
      Lauf legt den Stand mit dem Tagesdatum ab.
    - ``periode``: Faktum mit Periodenspalten; nur die juengste geladene und neuere Perioden
      werden neu geschrieben, aeltere bleiben.

    Geprueft beim Schreiben, wie die Quellangaben: das Produkt muss im Katalog stehen, die Form
    muss zur Art passen, jede genannte Spalte muss eine Spalte des Produkts sein. Ein Tippfehler
    hier waere eine Historisierung, die nie greift — und die fehlende Geschichte faellt erst auf,
    wenn jemand nach ihr fragt.
    """
    tabellen = [dict(t) for t in (governed_catalog or {}).get("tables") or []]
    je_name = {t.get("name"): t for t in tabellen}
    unbekannt = sorted(set(gold) - set(je_name))
    if unbekannt:
        raise ValueError(f"Quellmetadaten (gold): unbekannte Produkte {', '.join(unbekannt)}")
    for name, angabe in sorted(gold.items()):
        t = je_name[name]
        formen = [f for f in GOLD_HISTORIENFORMEN if f in (angabe or {})]
        if len(formen) != 1:
            raise ValueError(f"Quellmetadaten (gold) {name}: genau eine von "
                             f"{', '.join(GOLD_HISTORIENFORMEN)} angeben (gefunden: "
                             f"{', '.join(formen) or 'keine'})")
        form, spec = formen[0], dict(angabe[formen[0]] or {})
        spalten = set(t.get("columns") or [])
        schluessel = [k for k in (t.get("key") or []) if k in spalten]
        wer = ", ".join(x for x in (angabe.get("von"), angabe.get("am")) if x)
        if form == "scd":
            if t.get("kind") != "dimension":
                raise ValueError(f"Quellmetadaten (gold) {name}: scd nur fuer Dimensionen")
            if not schluessel:
                raise ValueError(f"Quellmetadaten (gold) {name}: scd braucht einen Schluessel "
                                 f"im Katalog")
            typ2 = list(spec.get("typ2") or [])
            typ1 = list(spec.get("typ1") or [])
            befund = dict(spec.get("befund") or {})
            fremd = sorted((set(typ2) | set(typ1) | set(befund)) - spalten)
            if fremd:
                raise ValueError(f"Quellmetadaten (gold) {name}: Spalten nicht im Produkt: "
                                 f"{', '.join(fremd)}")
            if not typ2:
                raise ValueError(f"Quellmetadaten (gold) {name}: scd ohne typ2-Attribut ist Typ 1")
            doppelt = sorted(set(typ2) & set(typ1))
            if doppelt or set(schluessel) & (set(typ2) | set(typ1)):
                raise ValueError(f"Quellmetadaten (gold) {name}: ein Attribut ist Typ 1 und "
                                 f"Typ 2 zugleich oder Schluessel: "
                                 f"{', '.join(doppelt or sorted(set(schluessel) & (set(typ2) | set(typ1))))}")
            # Nicht genannte Nicht-Schluessel-Spalten sind Typ 1 — ausdruecklich vermerkt, damit
            # die Vorgabe sichtbar bleibt statt stillschweigend zu gelten.
            rest = sorted(spalten - set(schluessel) - set(typ2) - set(typ1))
            t["historisierung"] = {"form": "scd", "typ2": sorted(typ2),
                                   "typ1": sorted(set(typ1) | set(rest)),
                                   "typ1_vorgabe": rest, "befund": befund,
                                   "sk": f"{_ident(name)}_sk", "grund": spec.get("grund", ""),
                                   "von": wer}
        elif form == "stichtag":
            if t.get("kind") != "fact":
                raise ValueError(f"Quellmetadaten (gold) {name}: stichtag nur fuer Fakten")
            t["historisierung"] = {"form": "stichtag", "grund": spec.get("grund", ""),
                                   "von": wer}
        else:
            per = list(spec.get("spalten") or [])
            if len(per) != 2 or set(per) - spalten:
                raise ValueError(f"Quellmetadaten (gold) {name}: periode braucht genau zwei "
                                 f"Spalten des Produkts (Jahr, Monat), gefunden: {per}")
            if not schluessel or not set(per) <= set(schluessel):
                raise ValueError(f"Quellmetadaten (gold) {name}: die Periodenspalten muessen "
                                 f"Teil des Schluessels sein")
            t["historisierung"] = {"form": "periode", "spalten": per,
                                   "grund": spec.get("grund", ""), "von": wer}
    return tabellen


def _herkunft_zeile(governed_catalog: dict | None, quelle: str, feld: str) -> str:
    """„(deklariert im Standardpaket)“ o. ae. — oder leer, wenn der Katalog nichts sagt."""
    h = _quelltabelle(governed_catalog, quelle).get(f"{feld}_herkunft")
    if not h:
        return " (abgeleitet aus dem Spaltennamen — bestaetigen)" if feld == "watermark" else ""
    e = _quelltabelle(governed_catalog, quelle)
    von = e.get(f"{feld}_von")
    werte = e.get(feld) if isinstance(e.get(feld), list) else [e.get(feld)]
    fremd = [w for w in werte if w in (e.get("nicht_im_katalog") or [])]
    return (f" ({_HERKUNFT_WORT.get(h, h)}{', ' + von if von else ''}"
            f"{'; nicht im Katalog: ' + ', '.join(fremd) if fremd else ''})")


def _silber_hashvergleich(src: str, silver_tbl: str, bronze_tbl: str, e: dict, dl: dict,
                         wahl: str | None) -> str:
    """Silber per Hashvergleich: Fabric erkennt die Aenderung und setzt das Datum (D-558).

    Die Antwort auf Flos Frage vom 24.09.2026 fuer Tabellen **ohne** Aenderungsspalte: Bronze
    ist ein Vollauszug, Silber haelt den letzten Stand samt `_zeilenhash`. Je Lauf vergleicht
    der MERGE die Hashes je Schluessel; nur eine geaenderte oder neue Zeile bekommt
    `_geaendert_am = current_timestamp()`, eine verschwundene wird geloescht. Ab hier traegt die
    Kette eine Aenderungsspalte, die die Quelle nie hatte — Gold laedt darauf inkrementell.

    Preis: ein voller Vergleich je Lauf. Voraussetzungen: Bronze ist ein **Vollauszug** (sonst
    waere jede fehlende Zeile eine Loeschung) und traegt keine Lade-Metadaten, die sich je Lauf
    aendern (sonst waere jede Zeile geaendert). Ein **leerer** Auszug haelt vor dem MERGE an —
    `NOT MATCHED BY SOURCE` wuerde Silber sonst leeren (gemessen: Delta erlaubt die Pruefung
    nicht in der Klausel, deshalb als eigene Anweisung).
    """
    c, st = dl["comment"], dl["stack"]
    schluessel = list(e.get("key") or [])
    on = " AND ".join(f"t.{zitiere(k, st)} IS NOT DISTINCT FROM s.{zitiere(k, st)}"
                      for k in schluessel)
    quelle = (f"SELECT *, {dl['hash64']}(*) AS _zeilenhash, {dl['jetzt']}"
              f" AS {FABRIC_STEMPEL}\n    FROM {bronze_tbl}")
    kopf = (f"{c}\n{c} SILBER PER HASHVERGLEICH (kuratiert"
            f"{', ' + e['silber_von'] if e.get('silber_von') else ''}; D-558): '{src}' hat keine "
            f"verlaessliche\n"
            f"{c}   Aenderungsspalte — Fabric erkennt Aenderungen am Zeilenhash und stempelt "
            f"{FABRIC_STEMPEL}.\n"
            f"{c}   Schluessel: {' + '.join(schluessel)}. Neue und geaenderte Zeilen bekommen den "
            f"Stempel des Laufs,\n"
            f"{c}   verschwundene werden geloescht (Bronze ist ein Vollauszug). Unveraenderte "
            f"bleiben unberuehrt.\n"
            f"{c}   Gilt vor DATA-SILVER-LOAD{' = ' + wahl if wahl else ''} der Domaene: die "
            f"Angabe ist je Tabelle kuratiert.\n"
            f"{c}   Ein leerer Auszug haelt an, bevor der MERGE Silber leeren koennte.\n")
    return (kopf
            + f"CREATE TABLE IF NOT EXISTS {silver_tbl}{dl['using']}"
            f"{_mit_cdf(dl.get('tblprops', ''))} AS\n"
            f"{quelle.replace(chr(10) + '    ', chr(10))}\nWHERE 1 = 0\n;\n"
            f"SELECT assert_true((SELECT COUNT(*) FROM {bronze_tbl}) > 0,\n"
            f"    'Bronze {bronze_tbl} ist leer — der Hashvergleich wuerde Silber leeren')\n;\n"
            f"MERGE INTO {silver_tbl} AS t\n"
            f"USING (\n    {quelle}\n) AS s\n"
            f"ON {on}\n"
            f"WHEN MATCHED AND t._zeilenhash <> s._zeilenhash THEN UPDATE SET *\n"
            f"WHEN NOT MATCHED THEN INSERT *\n"
            f"WHEN NOT MATCHED BY SOURCE THEN DELETE\n;\n")


def _bronze_to_silver(d: dict, src: str, silver_tbl: str, contract_ref: str, dl: dict,
                      bronze_tbl: str = "", wahl: str | None = None,
                      governed_catalog: dict | None = None) -> str:
    """bronze → silver in der Ladeform, die `DATA-SILVER-LOAD` festlegt (D-533, D-534).

    **Vollaufbau** (Vorgabe): `CREATE OR REPLACE` — korrekt und idempotent, aber jeder Lauf
    ist fuer die Plattform eine Aenderung an allem, und jede Materialized Lake View darueber
    rechnet voll.

    **append**: Silber wird einmal leer angelegt (mit Change Data Feed) und je Lauf nur um
    neue Zeilen ergaenzt. Ausfuehrbar, sobald der Katalog eine Aenderungs- oder Anlagespalte
    der Quelle nennt; sonst bleibt der Platzhalter — absichtlich nicht parsebar, damit kein
    Vollabzug als „inkrementell“ ausgeliefert wird.

    **merge**: dasselbe Anlegen, dann `MERGE`. Der Schluessel ist der der **Quelltabelle**
    (`source_tables`, D-539: im Standardpaket deklariert oder kuratiert) — nie ein Gold-
    Schluessel, denn bei `makt` (Material + Sprache) laege der sofort daneben. Fehlt er,
    bleibt der Match-Key Platzhalter, bis der Datenvertrag ihn nennt.

    Der Kopf nennt fuer Schluessel und Watermark, **woher** sie stammen.
    """
    c = dl["comment"]
    bronze_tbl = bronze_tbl or f"bronze_{_ident(src)}"
    kopf = (f"{c} bronze → silver — conform + cleanse '{src}' for domain '{d['name']}'.\n"
            f"{c} Contract: {contract_ref}\n")
    _q = _quelltabelle(governed_catalog, src)
    if _q.get("silber") == SILBER_HASHVERGLEICH and dl.get("stack") != "snowflake":
        return kopf + _silber_hashvergleich(src, silver_tbl, bronze_tbl, _q, dl, wahl)
    mapping = (f"    {c} TODO(contract:{contract_ref}): map raw columns → conformed silver schema,\n"
               f"    {c} apply types, dedup, null/quality rules, business keys.\n")
    if wahl and wahl not in _DATA_SILVER_LOAD_WERTE:
        kopf += (f"{c} BEFUND: DATA-SILVER-LOAD = {wahl!r} ist kein bekannter Wert "
                 f"({', '.join(_DATA_SILVER_LOAD_WERTE)}); behandelt wie Vollaufbau.\n")
    if wahl not in ("append", "merge"):
        return (
            kopf
            + f"{dl['ctas']} {silver_tbl}{dl['using']}{dl.get('tblprops', '')} AS\n"
            f"SELECT\n"
            + mapping
            + f"    *\n"
            f"FROM {bronze_tbl}\n"
            f"{c} WHERE <incremental / quality predicate>\n"
            f";\n"
        )

    delta = dl.get("stack") != "snowflake"
    wm = _silber_watermark(governed_catalog, src)
    tagesgenau = _spaltentyp(governed_catalog, wm or "") == "date"
    kopf += (f"{c}\n{c} ENTSCHIEDEN: DATA-SILVER-LOAD = {wahl} (Antwortdatei → Profil "
             f"`entscheidungen`).\n"
             f"{c}   Silber wird angelegt, falls es fehlt, und danach nicht mehr ersetzt.\n")
    if delta:
        kopf += (f"{c}   Change Data Feed ist an. Inkrementell aktualisiert Fabric eine Sicht "
                 f"darueber nur,\n"
                 f"{c}   wenn der Zyklus auf ALLEN ihren Quellen append-only war "
                 f"(MS Learn, Optimal refresh).\n")
    if wahl == "append":
        kopf += f"{c}   Korrekturen und Loeschungen der Quelle kommen NICHT an.\n"
    else:
        kopf += (f"{c}   Ein Zyklus mit Aenderung laesst jede Sicht darueber voll rechnen. "
                 f"Loeschungen kommen\n"
                 f"{c}   nur mit Loeschkennzeichen der Quelle an — "
                 f"TODO(contract:{contract_ref}).\n")
    schluessel = [k for k in (_quelltabelle(governed_catalog, src).get("key") or []) if k]
    if wahl == "merge" and schluessel:
        kopf += (f"{c}   Match-Key : {' + '.join(schluessel)}"
                 f"{_herkunft_zeile(governed_catalog, src, 'key')}\n")
    if wm:
        kopf += (f"{c}   Watermark : {wm} > (SELECT MAX({wm}) FROM {silver_tbl}); "
                 f"leeres Silber laedt alles.\n"
                 f"{c}   Herkunft der Watermark{_herkunft_zeile(governed_catalog, src, 'watermark')}\n"
                 + (f"{c}   {_quelltabelle(governed_catalog, src)['watermark_hinweis']}\n"
                    if _quelltabelle(governed_catalog, src).get("watermark_hinweis") else ""))
        _q = _quelltabelle(governed_catalog, src)
        if _q.get("unveraenderlich") and wm == _q.get("anlage"):
            kopf += (f"{c}   Kuratiert unveraenderlich: Zeilen werden angelegt, nicht geaendert — "
                     f"neue erkennt man an {wm}.\n")
        elif wahl == "merge" and any(h in wm.lower() for h in _ANLAGE_HINWEISE):
            kopf += (f"{c}   BEFUND: {wm} ist ein Anlagedatum. Eine spaetere Aenderung an einer "
                     f"alten Zeile traegt ein\n"
                     f"{c}   altes Anlagedatum und kommt mit diesem MERGE nie an — fuer `merge` "
                     f"eine Aenderungsspalte kuratieren.\n")
        if tagesgenau:
            kopf += (f"{c}   {wm} ist tagesgenau: eine Zeile mit dem Datum des bisherigen "
                     f"Maximums, die erst nach\n"
                     f"{c}   dem letzten Lauf entsteht, kommt nicht an. Genauer wird es nur "
                     f"mit einem Zeitstempel.\n")
        filter_ = (f"WHERE (SELECT COUNT(*) FROM {silver_tbl}) = 0\n"
                   f"   OR {wm} > (SELECT MAX({wm}) FROM {silver_tbl})\n")
    elif _quelltabelle(governed_catalog, src).get("watermark_keine"):
        e = _quelltabelle(governed_catalog, src)
        kopf += (f"{c}   Kuratiert: '{src}' hat keine verlaessliche Aenderungsspalte"
                 f"{' (' + e['watermark_von'] + ')' if e.get('watermark_von') else ''}.\n"
                 + (f"{c}   {e['watermark_hinweis']}\n" if e.get("watermark_hinweis") else "")
                 + f"{c}   Der Platzhalter unten bleibt — Delta nur ueber Aenderungsbelege oder "
                 f"einen Delta-Extraktor.\n")
        filter_ = f"WHERE <watermark_col> > (SELECT MAX(<watermark_col>) FROM {silver_tbl})\n"
    else:
        kopf += (f"{c}   Der Katalog nennt fuer '{src}' keine Aenderungs- oder Anlagespalte; "
                 f"der Platzhalter\n"
                 f"{c}   unten bleibt, bis der Datenvertrag sie traegt.\n")
        filter_ = f"WHERE <watermark_col> > (SELECT MAX(<watermark_col>) FROM {silver_tbl})\n"
    anlegen = (f"CREATE TABLE IF NOT EXISTS {silver_tbl}{dl['using']}"
               f"{_mit_cdf(dl.get('tblprops', '')) if delta else ''} AS\n"
               f"SELECT * FROM {bronze_tbl} WHERE 1 = 0\n;\n")
    if wahl == "append":
        laden = (f"INSERT INTO {silver_tbl}\n"
                 f"SELECT\n" + mapping + f"    *\n"
                 f"FROM {bronze_tbl}\n" + filter_ + ";\n")
    else:
        if schluessel:
            paare = [f"t.{zitiere(k, dl['stack'])} = s.{zitiere(k, dl['stack'])}" for k in schluessel]
            on_klausel = "ON " + " AND ".join(paare) + "\n"
        else:
            on_klausel = (f"ON t.<business_key> = s.<business_key>   {c} "
                          f"TODO(contract:{contract_ref}): Schluessel der Quelltabelle\n")
        set_clause = "UPDATE SET *" if delta else f"UPDATE SET <cols>  {c} explicit column mapping"
        ins_clause = "INSERT *" if delta else "INSERT (<cols>) VALUES (<cols>)"
        laden = (f"MERGE INTO {silver_tbl} AS t\n"
                 f"USING (\n"
                 f"    SELECT *\n"
                 f"    FROM {bronze_tbl}\n"
                 + "".join(f"    {z}\n" for z in filter_.rstrip("\n").split("\n"))
                 + ") AS s\n"
                 + on_klausel
                 + f"WHEN MATCHED THEN {set_clause}\n"
                 f"WHEN NOT MATCHED THEN {ins_clause}\n"
                 f";\n")
    return kopf + anlegen + laden


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


def _kommentar_text(text: str) -> str:
    """Ein Beschreibungstext als Spark-SQL-Literalinhalt (siehe ``_spalten_kommentare``)."""
    return " ".join(str(text or "").split()).replace("\\", "\\\\").replace("'", "\u2019")


def _tabellen_kommentar(table: dict | None, dl: dict) -> str:
    """``COMMENT '…'`` in der CTAS-Klausel der Gold-Tabelle (I-21 W5.6 e, Tabellenebene).

    Quelle ist ausschliesslich ``description`` der Katalogtabelle (ALUCA: die Tabellen-
    ``description`` des Datenvertrags) — ohne sie keine Klausel, nichts wird erfunden. Learn
    dokumentiert fuer Fabric nur den Spaltenkommentar (``ALTER COLUMN … COMMENT``); die
    Tabellenklausel ist die ``CREATE TABLE … [COMMENT table_comment] … AS``-Syntax von Apache
    Spark (SQL-Referenz „CREATE TABLE", Klauseln in beliebiger Reihenfolge) — ANNAHME,
    ungeprueft am Tenant. Nicht Snowflake (dort ``COMMENT = '…'``, eigene Syntax).
    """
    if dl.get("stack") == "snowflake":
        return ""
    text = _kommentar_text((table or {}).get("description") or "")
    return f"\nCOMMENT '{text}'" if text else ""


def _spalten_kommentare(gold_tbl: str, table: dict | None, spalten: list[str], dl: dict) -> str:
    """``ALTER TABLE … ALTER COLUMN … COMMENT '…'`` je beschriebener Gold-Spalte (I-21 W5.6 e).

    Beschreibungen sind der Hebel fuer Katalog und Copilot. Quelle ist ausschliesslich
    ``column_descriptions`` des governten Katalogs (SAP: ``meaning`` aus dem Paket; Kalender:
    ``sap_calendar``) — eine Spalte ohne Beschreibung bekommt keine Anweisung, nichts wird
    erfunden. Syntax nach MS Learn *Schema evolution for Delta tables* (fabric/data-engineering/
    delta-lake-schema-evolution, gelesen 29.09.2026): ``ALTER TABLE sales ALTER COLUMN amount
    COMMENT '…'``. Nach dem ``CREATE OR REPLACE`` gesetzt, damit jeder Vollaufbau sie erneuert.
    Nur Spark (Fabric/Databricks); Snowflake hat eine eigene Syntax und ist hier nicht Ziel.

    Ein ``'`` im Text wird zum typografischen Apostroph: Spark SQL verkettet ``'a''b'`` zu
    ``ab`` statt zu escapen, und ``sql_anweisungen`` zaehlt Anfuehrungszeichen ohne Backslash.
    """
    if dl.get("stack") == "snowflake":
        return ""
    beschr = (table or {}).get("column_descriptions") or {}
    zeilen = []
    for sp in spalten:
        text = _kommentar_text(beschr.get(sp) or "")
        if text:
            zeilen.append(f"ALTER TABLE {gold_tbl} ALTER COLUMN {zitiere(sp, dl['stack'])} "
                          f"COMMENT '{text}';")
    if not zeilen:
        return ""
    return (f"{dl['comment']} Spaltenbeschreibungen aus dem governten Katalog "
            f"({len(zeilen)} von {len(spalten)}) — Katalog/Copilot lesen sie.\n"
            + "\n".join(zeilen) + "\n")


def _silver_to_gold(name: str, kind: str, silver_tbl: str | list[str], contract_ref: str,
                    dl: dict, gold_tbl: str = "", table: dict | None = None,
                    kopf_extra: list[str] | None = None,
                    wasserzeichen: dict | None = None,
                    bezuege: list[dict] | None = None) -> str:
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
            + "".join(f"{c} {z}\n" for z in (kopf_extra or []))
            + f"{dl['ctas']} {gold_tbl}{dl['using']}{dl.get('tblprops', '')}"
            + f"{_tabellen_kommentar(table, dl)} AS\n")

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
        if kind == "dimension" and ((table or {}).get("historisierung") or {}).get("form") != "scd":
            kopf.append(f"{c} TODO(contract:{contract_ref}): Ersatzschluessel und SCD-Behandlung "
                        f"ergaenzen, z. B. row_number() OVER (ORDER BY "
                        f"{', '.join(schluessel) or '<business_key>'}) AS {name}_sk.")
        auswahl = ",\n".join(f"    {_projektion(s, table, dl['stack'])}" for s in spalten)
        if wasserzeichen and wasserzeichen.get("spalte"):
            kopf.append(f"{c} {WASSERZEICHEN_SPALTE} = {wasserzeichen['spalte']} aus "
                        f"{wasserzeichen['quelle']} ({wasserzeichen['art']}, kuratiert) — "
                        f"technisch, fuer das inkrementelle Laden (D-549).")
            auswahl += (f",\n    {zitiere(wasserzeichen['spalte'], dl['stack'])} AS "
                        f"{WASSERZEICHEN_SPALTE}")
        roh_sql = "SELECT\n" + auswahl + f"\nFROM {silver_tbl}"
        quell_sql = roh_sql
        if bezuege:
            quell_sql = _mit_ersatzschluesseln(roh_sql, bezuege, dl)
            kopf += _bezugs_kopf(bezuege, c)
        kopf_h, ctas, anhang = _historie_anhang(name, gold_tbl, quell_sql, table, dl, wasserzeichen,
                                                [b["spalte"] for b in bezuege or []],
                                                roh_sql=roh_sql, bezuege=bezuege)
        if ctas != dl["ctas"]:
            head = head.replace(f"{dl['ctas']} {gold_tbl}", f"{ctas} {gold_tbl}", 1)
        return (head + "\n".join(kopf + kopf_h) + "\n" + quell_sql + "\n;\n" + anhang
                + _spalten_kommentare(gold_tbl, table, spalten, dl))

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


def _einruecken(sql: str, n: int) -> str:
    return "\n".join((" " * n + z) if z else z for z in sql.splitlines())


def _historie_anhang(name: str, gold_tbl: str, quell_sql: str, table: dict | None, dl: dict,
                     wasserzeichen: dict | None,
                     zusatz: list[str] | None = None, roh_sql: str = "",
                     bezuege: list[dict] | None = None) -> tuple[list[str], str, str]:
    """Gold als Historienhalter (D-551..D-553): was die Quelle nicht aufhebt, hebt Gold auf.

    Rueckgabe ``(kopfzeilen, ctas, anhang)``: Kommentarzeilen fuer den Dateikopf, das
    Schluesselwort des Hauptstatements (bei ``periode`` wird aus dem Neuaufbau eine
    Erstbefuellung) und die Statements, die hinter dem Hauptstatement laufen.

    Alle drei Formen sind **wiederholbar**: ein zweiter Lauf mit derselben Quelle aendert
    nichts. Das ist die Bedingung dafuer, dass sie im Vollaufbau stehen duerfen — der laeuft
    bei jeder Ladeform, auch wenn DATA-INC `watermark` sagt (der MERGE unter `incremental/`
    ist die Alternative fuer die Typ-1-Tabelle, nicht fuer die Historie).
    Und keine der drei ist ``CREATE OR REPLACE``: Historie, die ein Neuaufbau loescht, ist
    keine.
    """
    hist = (table or {}).get("historisierung") or {}
    form = hist.get("form")
    if not form:
        return [], dl["ctas"], ""
    c, st = dl["comment"], dl["stack"]
    z = lambda s: zitiere(s, st)                                        # noqa: E731
    spalten = sorted(set((table or {}).get("columns") or []))
    schluessel = [k for k in ((table or {}).get("key") or []) if k in spalten]
    mit_wz = bool(wasserzeichen and wasserzeichen.get("spalte"))
    props = f"{dl['using']}{dl.get('tblprops', '')}"
    neu = "CREATE TABLE IF NOT EXISTS"
    wer = f", {hist['von']};" if hist.get("von") else ""

    if form == "stichtag":
        ziel = f"{gold_tbl}_{STICHTAG_SPALTE}"
        liste = ", ".join(z(s) for s in spalten + list(zusatz or []))
        kopf = [f"{c}",
                f"{c} STICHTAGSABLAGE (kuratiert{wer}, D-552): {ziel} haelt je Lauf den Stand",
                f"{c}   dieser Tabelle mit {STICHTAG_SPALTE} = Tagesdatum. Die Quelle kennt nur den "
                f"aktuellen Stand —",
                f"{c}   ein ausgeglichener Posten ist dort weg; hier bleibt er im Stand seines "
                f"letzten Tages.",
                *([f"{c}   Grund: {hist['grund']}"] if hist.get("grund") else []),
                f"{c}   Wiederholbar: ein zweiter Lauf am selben Tag ersetzt den Tagesstand.",
                f"{c}   Das Semantikmodell liest die Ablage noch nicht (OQ-45) — sie haelt die "
                f"Geschichte ab Inbetriebnahme fest."]
        anhang = (f"{neu} {ziel}{props} AS\n"
                  f"SELECT {dl['heute']} AS {STICHTAG_SPALTE}, {liste}\n"
                  f"FROM {gold_tbl}\nWHERE 1 = 0\n;\n"
                  f"DELETE FROM {ziel} WHERE {STICHTAG_SPALTE} = {dl['heute']}\n;\n"
                  f"INSERT INTO {ziel} ({STICHTAG_SPALTE}, {liste})\n"
                  f"SELECT {dl['heute']}, {liste}\nFROM {gold_tbl}\n;\n")
        return kopf, dl["ctas"], anhang

    if form == "periode":
        jahr, monat = hist["spalten"]
        per = f"CAST({{p}}{z(jahr)} AS INT) * 100 + CAST({{p}}{z(monat)} AS INT)"
        ziel_spalten = spalten + ([WASSERZEICHEN_SPALTE] if mit_wz else []) + list(zusatz or [])
        on = " AND ".join(f"t.{z(k)} IS NOT DISTINCT FROM s.{z(k)}" for k in schluessel)
        kopf = [f"{c}",
                f"{c} PERIODENLADUNG (kuratiert{wer}, D-553): erster Lauf befuellt die Tabelle "
                f"ganz; danach",
                f"{c}   schreibt jeder Lauf nur die juengste geladene Periode ({jahr}/{monat}) und "
                f"neuere.",
                f"{c}   Aeltere Perioden bleiben stehen — auch wenn die Quelle sie nicht mehr "
                f"liefert. Das ist",
                f"{c}   die Voraussetzung, um die Aufnahme spaeter auf die letzten Perioden zu "
                f"begrenzen.",
                *([f"{c}   Grund: {hist['grund']}"] if hist.get("grund") else []),
                f"{c}   Gilt vor DATA-INC der Domaene: die Angabe ist je Tabelle kuratiert.",
                f"{c}   Neuaufbau nur bewusst: DROP TABLE {gold_tbl}, dann laufen lassen."]
        # Der Periodenfilter steht VOR dem Verbund mit der Historie (D-559). Dahinter las Delta
        # das Ziel in einer materialisierten Quelle und brach ab („Table does not support
        # reads“, gemessen 24.09.2026 an `fact_inventory_history`); davor laeuft es.
        gefiltert = (f"SELECT q.*\nFROM (\n{_einruecken(roh_sql or quell_sql, 4)}\n) AS q\n"
                     f"WHERE (SELECT COUNT(*) FROM {gold_tbl}) = 0\n"
                     f"   OR {per.format(p='q.')} >= (SELECT MAX({per.format(p='')}) "
                     f"FROM {gold_tbl})")
        if bezuege and roh_sql:
            gefiltert = _mit_ersatzschluesseln(gefiltert, bezuege, dl)
        anhang = (f"MERGE INTO {gold_tbl} AS t\nUSING (\n{_einruecken(gefiltert, 4)}\n) AS s\n"
                  f"ON {on}\n"
                  f"WHEN MATCHED THEN UPDATE SET "
                  + ", ".join(f"{z(s)} = s.{z(s)}" for s in ziel_spalten if s not in schluessel)
                  + f"\nWHEN NOT MATCHED THEN INSERT ({', '.join(z(s) for s in ziel_spalten)})\n"
                  f"    VALUES ({', '.join('s.' + z(s) for s in ziel_spalten)})\n;\n")
        return kopf, neu, anhang

    # form == "scd": Typ-2-Historie neben der Typ-1-Dimension.
    ziel = f"{gold_tbl}_historie"
    typ2, typ1, sk = hist["typ2"], hist["typ1"], hist["sk"]
    ab, bis, akt = SCD_SPALTEN
    gab = f"q.{WASSERZEICHEN_SPALTE}" if mit_wz else dl["heute"]
    quelle = (f"(\n    SELECT q.*, {gab} AS _gueltig_ab\n    FROM (\n"
              f"{_einruecken(quell_sql, 8)}\n    ) AS q\n)")
    mk = {k: f"_mk_{_ident(k)}" for k in schluessel}
    leer = "CASE WHEN false THEN s._gueltig_ab END"
    anders = lambda a, b: " OR ".join(f"{a}.{z(x)} IS DISTINCT FROM {b}.{z(x)}"  # noqa: E731
                                      for x in typ2)
    hash_ = lambda ab_: f"{dl['hash64']}({', '.join('s.' + z(k) for k in schluessel)}, {ab_})"  # noqa: E731
    erster = mk[schluessel[0]]
    neu_ab = f"CASE WHEN s.{erster} IS NULL THEN s._gueltig_ab END"
    kopf = [f"{c}",
            f"{c} TYP-2-HISTORIE (kuratiert{wer}, D-551): {ziel} fuehrt je Schluessel "
            f"({', '.join(schluessel)}) Versionen.",
            f"{c}   Neue Version bei Aenderung von: {', '.join(typ2)}.",
            f"{c}   Ueberschrieben in allen Versionen (Typ 1): {', '.join(typ1) or '—'}"
            + (f" (nicht genannt, Vorgabe Typ 1: {', '.join(hist['typ1_vorgabe'])})"
               if hist.get("typ1_vorgabe") else "") + ".",
            *[f"{c}   BEFUND {sp}: {txt}" for sp, txt in sorted((hist.get("befund") or {}).items())],
            *([f"{c}   Grund: {hist['grund']}"] if hist.get("grund") else []),
            f"{c}   {ab} = "
            + (f"{wasserzeichen['spalte']} aus {wasserzeichen['quelle']} (Aenderungsdatum der "
               f"Quelle)" if mit_wz else
               "Tagesdatum des Laufs (die Quelle hat keine Aenderungsspalte — Fabric stempelt "
               "den Erkennungstag)") + ";",
            f"{c}   halboffen [{ab}, {bis}); leer heisst offen. Erste Version eines Schluessels: "
            f"{ab} leer.",
            f"{c}   {sk} = {dl['hash64']}(Schluessel, {ab}) — stabil ueber Laeufe, ohne Sequenz.",
            f"{c}   Voraussetzung: die Aenderungsspalte ist bei jeder Aenderung gesetzt; ein "
            f"Schluessel, der",
            f"{c}   aus der Quelle verschwindet, bleibt aktuell (keine Loescherkennung).",
            f"{c}   Die Typ-1-Tabelle {gold_tbl} bleibt das, was das Semantikmodell liest; "
            f"Fakten mit {sk}",
            f"{c}   zum Belegdatum und die Umstellung der Beziehungen sind OQ-45."]
    auswahl = ",\n    ".join(f"s.{z(s)}" for s in spalten)
    anhang = (
        f"{neu} {ziel}{props} AS\n"
        f"SELECT\n    {hash_(leer)} AS {sk},\n    {auswahl},\n"
        f"    {leer} AS {ab},\n    {leer} AS {bis},\n    true AS {akt}\n"
        f"FROM {quelle} AS s\n;\n"
        f"MERGE INTO {ziel} AS t\nUSING (\n"
        f"    SELECT {', '.join(f's.{z(k)} AS {mk[k]}' for k in schluessel)}, s.*\n"
        f"    FROM {_einruecken(quelle, 4).lstrip()} AS s\n"
        f"    UNION ALL\n"
        f"    SELECT {', '.join(f'NULL AS {mk[k]}' for k in schluessel)}, s.*\n"
        f"    FROM {_einruecken(quelle, 4).lstrip()} AS s\n"
        f"    JOIN {ziel} AS h ON "
        + " AND ".join(f"h.{z(k)} = s.{z(k)}" for k in schluessel) + f" AND h.{akt}\n"
        f"    WHERE {anders('h', 's')}\n"
        f") AS s\n"
        f"ON " + " AND ".join(f"t.{z(k)} = s.{mk[k]}" for k in schluessel) + f" AND t.{akt}\n"
        f"WHEN MATCHED AND ({anders('t', 's')}) THEN\n"
        f"    UPDATE SET {bis} = s._gueltig_ab, {akt} = false\n"
        f"WHEN NOT MATCHED THEN INSERT ({sk}, {', '.join(z(s) for s in spalten)}, {ab}, {bis}, {akt})\n"
        f"    VALUES ({hash_(neu_ab)}, {', '.join('s.' + z(s) for s in spalten)}, {neu_ab}, "
        f"NULL, true)\n;\n")
    if typ1:
        anhang += (
            f"MERGE INTO {ziel} AS t\nUSING {quelle} AS s\n"
            f"ON " + " AND ".join(f"t.{z(k)} = s.{z(k)}" for k in schluessel)
            + " AND (" + " OR ".join(f"t.{z(x)} IS DISTINCT FROM s.{z(x)}" for x in typ1) + ")\n"
            "WHEN MATCHED THEN UPDATE SET "
            + ", ".join(f"{z(x)} = s.{z(x)}" for x in typ1) + "\n;\n")
    return kopf, dl["ctas"], anhang


#: Der Platzhalter fuer eine offene n:1-Zusammenfuehrung — eine Stelle statt drei getippter.
_ZUSAMMENFUEHRUNG_OFFEN = "<ZUSAMMENFUEHRUNG NICHT ENTSCHIEDEN: UNION ODER JOIN>"


#: Vorbelegung von `DATA-TEXTSPRACHE` (D-542): SAP-internes Sprachkennzeichen `E`. Die Wahl
#: bestimmt nur, welcher Text **zuerst** genommen wird — fehlt er in dieser Sprache, greift der
#: Rueckfall auf die naechste vorhandene. Kein Schluessel verliert dadurch seine Zeile.
TEXTSPRACHE_VORGABE = "E"


def _text_verbund_sql(governed_catalog: dict | None, product: str, herkunft: list[str],
                      schemas: bool, stack: str, sprache: str) -> tuple[str, list[str]] | None:
    """Die FROM-Quelle eines Gold-Produkts aus Kopf und Texttabelle(n) — oder ``None``.

    Greift nur, wenn der Katalog die Zusammenfuehrung **erklaert** (`zusammenfuehrung`,
    `text_verbund`, Herkunft `paket`) und genau diese Herkuenfte der Domaene gehoeren.

    Die Form ist ein LEFT JOIN je Texttabelle mit **einem** Text je Kopfschluessel: die
    gewaehlte Sprache zuerst, sonst die naechste vorhandene (``row_number() … = 1``). Ein
    INNER JOIN liesse Stammsaetze ohne Text verschwinden; ein Filter nur auf die Sprache
    liesse sie ohne Text stehen, obwohl einer da ist; ein Verbund ohne Rangfolge
    vervielfachte jede Zeile um die Zahl der Sprachen und braeche das deklarierte Grain.
    """
    kat_t = _catalog_table(governed_catalog, _ident(product)) or {}
    zf = kat_t.get("zusammenfuehrung") or {}
    if zf.get("art") != "text_verbund":
        return None
    beteiligt = {zf.get("kopf"), *(x.get("quelle") for x in zf.get("texte") or [])}
    if beteiligt != set(herkunft):
        return None
    je_quelle = kat_t.get("source_columns") or {}
    z = lambda s: zitiere(s, stack)  # noqa: E731
    befund = []
    if not re.fullmatch(r"[A-Za-z0-9]{1,2}", sprache or ""):
        # `je_sprache` aendert das Grain und ist nicht gebaut; alles andere ist kein SAP-
        # Sprachkennzeichen. Beides still in ein `CASE WHEN SPRAS = 'je_sprache'` zu schreiben,
        # ergaebe eine Rangfolge, die nie greift — und nichts wuerde rot.
        befund = [f"BEFUND: DATA-TEXTSPRACHE = {sprache!r} ist nicht gebaut bzw. kein "
                  f"Sprachkennzeichen; es gilt die Vorgabe '{TEXTSPRACHE_VORGABE}'."]
        sprache = TEXTSPRACHE_VORGABE
    wort = sprache.replace("'", "''")
    spalten = ["k.*"]
    joins = []
    for i, tx in enumerate(zf["texte"], 1):
        eigen = je_quelle.get(tx["quelle"])
        if eigen is None:
            return None
        spalten += [f"t{i}.{z(c)}" for c in eigen if c not in tx["auf"]]
        auf = " AND ".join(f"t{i}.{z(c)} = k.{z(c)}" for c in tx["auf"])
        joins.append(
            f"    LEFT JOIN (\n"
            f"        SELECT *, row_number() OVER (PARTITION BY {', '.join(z(c) for c in tx['auf'])}\n"
            f"            ORDER BY CASE WHEN {z(tx['sprache'])} = '{wort}' THEN 0 ELSE 1 END, "
            f"{z(tx['sprache'])}) AS _rang\n"
            f"        FROM {layer_ref('silver', _ident(tx['quelle']), schemas)}\n"
            f"    ) AS t{i} ON {auf} AND t{i}._rang = 1")
    sql = (f"(\n    SELECT {', '.join(spalten)}\n"
           f"    FROM {layer_ref('silver', _ident(zf['kopf']), schemas)} AS k\n"
           + "\n".join(joins) + "\n)")
    texte = ", ".join(tx["quelle"] for tx in zf["texte"])
    kopf = [f"Zusammenfuehrung erklaert im Standardpaket (D-542): Kopf {zf['kopf']}, "
            f"Text {texte} — Verbund, keine Vereinigung.",
            f"Ein Text je Schluessel: Sprache '{sprache}' zuerst (DATA-TEXTSPRACHE), sonst die "
            f"naechste vorhandene. LEFT JOIN — ein Stammsatz ohne Text bleibt stehen."]
    return sql, kopf + befund


def _konforme_quellen(blueprint: dict, governed_catalog: dict | None, product: str,
                      contributing: list[str], domains: list[dict],
                      schemas: bool, stack: str = "fabric",
                      sprache: str = TEXTSPRACHE_VORGABE) -> list[tuple[str, str, list[str] | None]]:
    """Je speisender Domaene: ``(domaene, FROM-Quelle, eigene Spalten oder None)``.

    **Eine** Aufloesung fuer den Vollaufbau und den MERGE eines konformen Ziels (D-536) —
    sonst lesen die beiden Ladeformen verschiedene Tabellen.

    Korrigiert dabei einen verdeckten Fehler (D-536): hatte eine Domaene fuer das Produkt
    **mehrere** Herkuenfte, las sie `silver.<domaene>` — eine Tabelle, die es seit dem
    12.08.2026 nicht mehr gibt (Silber je Herkunftstabelle). Gemessen am SAP-Szenario:
    `dim_material` las `silver.order_to_cash`; im Kettenlauf verdeckt, weil die Anweisung
    schon an der ersten fehlenden Tabelle scheiterte. Jetzt gilt dieselbe Regel wie im
    Einzelfall: formgleiche Herkuenfte werden vereinigt, formverschiedene bleiben die offene
    Zusammenfuehrung — absichtlich nicht ausfuehrbar.

    ``eigene Spalten`` stammen aus `source_columns`, wenn der Katalog sie fuer genau diese
    eine Herkunft fuehrt; dann projiziert der Aufrufer fehlende Zielspalten als ``NULL``.
    """
    kat_t = _catalog_table(governed_catalog, _ident(product)) or {}
    je_quelle = kat_t.get("source_columns") or {}
    # Erklaert der Katalog das Ziel als Kopf + Texttabelle (D-542), wird es **einmal** aus
    # diesen Quellen gebaut — gleich, welche Domaene sie aufnimmt. Wer Kopf und Text laedt, ist
    # eine Frage der Aufnahme (D-538, D-543); wie sie zusammengehoeren, sagt das Paket. Ohne
    # diese Regel zerfiele der Verbund, sobald Kopf und Text verschiedene Eigentuemer haben:
    # je Domaene ein Block, und die UNION stapelte Textzeilen unter Kopfzeilen.
    zf = kat_t.get("zusammenfuehrung") or {}
    if zf.get("art") == "text_verbund":
        beteiligt = [zf.get("kopf"), *(x.get("quelle") for x in zf.get("texte") or [])]
        verbund = _text_verbund_sql(governed_catalog, product, beteiligt, schemas, stack, sprache)
        if verbund and set(beteiligt) == set(kat_t.get("sources") or []):
            # Der Block steht bei der Domaene, die den Kopf aufnimmt; die anderen lesen mit.
            traeger = next((dom for dom in contributing
                            if zf.get("kopf") in _sources_for_domain(blueprint, _ident(dom))),
                           contributing[0])
            return [(dom, verbund[0], None, verbund[1]) if dom == traeger else (dom, None, None)
                    for dom in contributing]
    raus: list[tuple[str, str, list[str] | None]] = []
    for dom in contributing:
        d_dom = next((x for x in domains if x.get("name") == dom), {})
        eigene = _herkunft_je_domaene(blueprint, governed_catalog, d_dom, domains).get(
            _ident(product), [])
        if len(eigene) == 1:
            raus.append((dom, layer_ref("silver", _ident(eigene[0]), schemas),
                         je_quelle.get(eigene[0])))
        elif eigene:
            tabellen = [layer_ref("silver", _ident(q), schemas) for q in eigene]
            formen = {q: je_quelle[q] for q in eigene if q in je_quelle}
            verbund = _text_verbund_sql(governed_catalog, product, eigene, schemas, stack, sprache)
            if verbund:
                raus.append((dom, verbund[0], None, verbund[1]))
                continue
            von = _von_klausel(tabellen) if _formgleich(formen) else _ZUSAMMENFUEHRUNG_OFFEN
            raus.append((dom, von, None))
        elif _silber_herkunft(governed_catalog, d_dom).get(_ident(product)):
            # Der Katalog nennt Herkuenfte, und alle gehoeren einer anderen Domaene (D-538:
            # `MARA` nimmt Order-to-Cash auf, Inventory liest sie mit). Dann traegt diese
            # Domaene keinen eigenen Block bei — ihre Zeilen stehen schon in dem der
            # aufnehmenden. Ein Block auf `silver.<domaene>` laese eine Tabelle, die es nicht gibt.
            raus.append((dom, None, None))
        else:
            raus.append((dom, layer_ref("silver", _ident(dom), schemas), None))
    return raus


#: Die technische Spalte, die Gold fuer das inkrementelle Laden traegt (D-549): der Wert der
#: kuratierten Aenderungs- bzw. Anlagespalte der Kopfquelle. Sie steht im Vollaufbau UND im MERGE
#: — sonst bricht `UPDATE SET *` / `INSERT *` an einer Spalte, die das Ziel nicht kennt.
WASSERZEICHEN_SPALTE = "_wasserzeichen"


def gold_wasserzeichen(governed_catalog: dict | None, product: str,
                       herkunft: list[str]) -> dict | None:
    """Woran Gold neue und geaenderte Zeilen erkennt — aus den **kuratierten** Quellmetadaten.

    Gemessen 23.09.2026 (D-544): die Gold-Heuristik waehlte fuer `dim_purchasing_document`
    `AEDAT` aus EKKO — laut DDIC ein Anlagedatum — und fuer drei weitere Produkte `ERDAT`. Ein
    MERGE darauf erkennt Aenderungen an alten Belegen nie. Die Aenderungsspalte steht aber nicht
    in der Gold-Projektion, sondern in der Quelle; sie reist deshalb als technische Spalte mit.

    Kopfquelle ist die einzige Herkunft, bei einem erklaerten Verbund der Kopf (D-542). Gelesen
    werden nur kuratierte Angaben: eine Heuristik bleibt der bisherige Vorschlag im Kommentar.

    Rueckgabe ``{"spalte", "art", "quelle"}``, ``{"keine": True, …}`` oder ``None``.
    """
    kat_t = _catalog_table(governed_catalog, _ident(product)) or {}
    zf = kat_t.get("zusammenfuehrung") or {}
    kopf = zf.get("kopf") if zf.get("art") == "text_verbund" else (
        herkunft[0] if len(herkunft) == 1 else None)
    if not kopf:
        return None
    e = _quelltabelle(governed_catalog, kopf)
    if e.get("watermark") and e.get("watermark_herkunft") == "kuratiert":
        return {"spalte": e["watermark"], "art": "Aenderung", "quelle": kopf,
                "von": e.get("watermark_von", "")}
    if e.get("silber") == SILBER_HASHVERGLEICH:
        # D-558: die Quelle hat keine Aenderungsspalte, Silber stempelt sie per Hashvergleich.
        return {"spalte": FABRIC_STEMPEL, "art": "Aenderungsstempel von Fabric (Hashvergleich "
                "in Silber, D-558)", "quelle": kopf, "von": e.get("silber_von", "")}
    if e.get("watermark_keine") and e.get("unveraenderlich") and e.get("anlage"):
        return {"spalte": e["anlage"], "art": "Anlage, Tabelle unveraenderlich", "quelle": kopf,
                "von": e.get("anlage_von", "")}
    if e.get("watermark_keine"):
        return {"keine": True, "quelle": kopf, "hinweis": e.get("watermark_hinweis", "")}
    return None


def _konforme_projektion(spalten: list[str], eigene: list[str] | None, table: dict | None,
                         stack: str) -> str:
    """Die Projektion eines Blocks: fehlende Zielspalten einer Herkunft als ``NULL``.

    Gemessen am SAP-Katalog: `inventory_mm_mara` traegt 3 der 6 Spalten von `dim_material`.
    Ein Block, der die anderen drei trotzdem nennt, scheitert am Binder — erst, sobald die
    Tabelle ueberhaupt da ist.
    """
    if not spalten:
        return "*"
    return ",\n    ".join(
        _projektion(s, table, stack) if eigene is None or s in eigene
        else f"NULL AS {zitiere(s, stack)}" for s in spalten)


def _silver_to_gold_conformed(name: str, kind: str, sources: list[tuple],
                              contract_ref: str, dl: dict, gold_tbl: str = "",
                              table: dict | None = None,
                              wasserzeichen: dict | None = None) -> str:
    """Ein Gold-Ziel, das mehrere Domaenen speisen — als EIN Transform.

    ``UNION`` (nicht ``UNION ALL``): dieselbe Quelltabelle, die in zwei Domaenen landet,
    liefert identische Zeilen, und die faellt UNION heraus. Was UNION NICHT kann, ist
    entscheiden, welche Seite recht hat, wenn dieselbe Schluesselzeile verschiedene
    Attribute traegt — das ist eine Vorrangfrage und steht als TODO drin, statt hier
    geraten zu werden.

    ``sources`` kommt aus `_konforme_quellen`: je Domaene ``(name, block, eigene_spalten,
    kopfzeilen)``, ``block`` leer, wenn die Domaene die Aufnahme einer anderen mitliest.

    Derselbe Befund wurde zweimal geloest (Merge 24.09.2026): main setzte am 07.09.2026 fuer
    eine Domaene mit mehreren Herkuenften einen Platzhalter statt des erfundenen
    ``silver.order_to_cash``; wip liest seit D-536/D-542 die Herkuenfte selbst und fuehrt
    einen erklaerten Textverbund (MARA + MAKT) als EINEN Block. Behalten ist die wip-Fassung;
    der Platzhalter bleibt dort, wo die Zusammenfuehrung wirklich offen ist
    (`_ungeklaerte_zusammenfuehrung`).
    """
    c = dl["comment"]
    gold_tbl = gold_tbl or f"gold_{_ident(name)}"
    spalten = sorted(set((table or {}).get("columns") or []))
    schluessel = [k for k in ((table or {}).get("key") or []) if k in spalten]
    grain = (table or {}).get("grain") or ""

    kopf = [
        f"{c} silver → gold — konforme {kind} '{name}'.",
        f"{c} Contract: {contract_ref}",
        f"{c} Gespeist von {len(sources)} Domaenen: {', '.join(q[0] for q in sources)}.",
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
    if kind == "dimension" and schluessel and \
            ((table or {}).get("historisierung") or {}).get("form") != "scd":
        kopf.append(f"{c} TODO(contract:{contract_ref}): Ersatzschluessel und SCD-Behandlung "
                    f"ergaenzen, z. B. row_number() OVER (ORDER BY {', '.join(schluessel)}) "
                    f"AS {_ident(name)}_sk.")

    if not spalten:
        kopf.append(f"{c} TODO(contract:{contract_ref}): kein Katalogeintrag — Projektion ergaenzen.")
    wz = (f",\n    {zitiere(wasserzeichen['spalte'], dl['stack'])} AS {WASSERZEICHEN_SPALTE}"
          if wasserzeichen and wasserzeichen.get("spalte") else "")
    if wz:
        kopf.append(f"{c} {WASSERZEICHEN_SPALTE} = {wasserzeichen['spalte']} aus "
                    f"{wasserzeichen['quelle']} ({wasserzeichen['art']}, kuratiert) — technisch, "
                    f"fuer das inkrementelle Laden (D-549).")
    blocks = [f"SELECT\n    {_konforme_projektion(spalten, q[2] if len(q) > 2 else None, table, dl['stack'])}"
              f"{wz}\nFROM {q[1]}" for q in sources if q[1]]
    for q in sources:
        kopf += [f"{c} {z}" for z in (q[3] if len(q) > 3 else [])]
    mitgelesen = [q[0] for q in sources if not q[1]]
    if mitgelesen:
        kopf.append(f"{c} Ohne eigenen Block: {', '.join(mitgelesen)} — liest die Aufnahme einer "
                    f"anderen Domaene mit (eine Tabelle, eine Aufnahme).")
    quell_sql = "\nUNION\n".join(blocks)
    kopf_h, ctas, anhang = (_historie_anhang(name, gold_tbl, quell_sql, table, dl, wasserzeichen)
                            if spalten and blocks else ([], dl["ctas"], ""))
    return (f"{chr(10).join(kopf + kopf_h)}\n{ctas} {gold_tbl}{dl['using']}"
            f"{_tabellen_kommentar(table, dl)} AS\n"
            + quell_sql + "\n;\n" + anhang
            + (_spalten_kommentare(gold_tbl, table, spalten, dl) if blocks else ""))


def emit_transforms(blueprint: dict, stack: str = "fabric", schemas: bool = False,
                    governed_catalog: dict | None = None,
                    entscheidungen: dict | None = None) -> dict[str, str]:
    """Return the transform DAG as ``path → SQL`` (relative to a ``transforms/`` root).

    One ``silver_to_gold__<product>.sql`` per gold product; one
    ``bronze_to_silver__<source>.sql`` per ingested source **iff** bronze is materialised
    (``medallion.bronze.enabled``). Plus ``_MEDALLION_FLOW.md`` documenting the DAG.

    ``schemas`` targets a schema-enabled lakehouse: tables become ``gold.<name>`` / ``silver.<domain>``
    instead of ``gold_<name>`` / ``silver_<domain>`` in the default namespace.

    ``entscheidungen`` ist das Profilfeld aus dem Rueckweg (C-3). Gelesen wird hier
    `DATA-SILVER-LOAD` (D-534): es legt die Ladeform von Bronze → Silber fest. Ohne Antwort
    bleibt es beim Vollaufbau — dem Wert, mit dem die Vorlage vorbelegt ist.
    """
    from core.dataarch_engine.blueprint.decision_proposals import entscheidung_fuer

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
        silber_wahl = entscheidung_fuer(entscheidungen, "DATA-SILVER-LOAD", d["name"])
        text_sprache = (entscheidung_fuer(entscheidungen, "DATA-TEXTSPRACHE", d["name"])
                        or TEXTSPRACHE_VORGABE)
        if bronze_enabled:
            flow.append(f"Ladeform Bronze → Silber: **{silber_wahl or 'vollaufbau'}** "
                        f"(`DATA-SILVER-LOAD`{'' if silber_wahl else ', Vorbelegung'})")
            if herkunft:
                for quelle in sorted({q for qs in herkunft.values() for q in qs}):
                    rel = f"transforms/{ddir}/bronze_to_silver__{_ident(quelle)}.sql"
                    bronze_tbl = layer_ref("bronze", _ident(quelle), schemas)
                    ziel = layer_ref("silver", _ident(quelle), schemas)
                    out[rel] = _bronze_to_silver(d, quelle, ziel, c_ref, dl, bronze_tbl=bronze_tbl,
                                                 wahl=silber_wahl,
                                                 governed_catalog=governed_catalog)
                    flow.append(f"- {bronze_tbl} → `{ziel}`  ·  `{rel}`")
            else:
                for src in _sources_for_domain(blueprint, dident):
                    rel = f"transforms/{ddir}/bronze_to_silver__{_ident(src)}.sql"
                    bronze_tbl = layer_ref("bronze", _ident(src), schemas)
                    out[rel] = _bronze_to_silver(d, src, silver_tbl, c_ref, dl, bronze_tbl=bronze_tbl,
                                                 wahl=silber_wahl,
                                                 governed_catalog=governed_catalog)
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
            verbund = _text_verbund_sql(governed_catalog, product,
                                        herkunft.get(_ident(product), []), schemas, stack,
                                        text_sprache) if len(von) > 1 else None
            if verbund:
                out[rel] = _silver_to_gold(product, kind, verbund[0], c_ref, dl,
                                           gold_tbl=gold_tbl, table=kat_t or None,
                                           kopf_extra=verbund[1],
                                           wasserzeichen=gold_wasserzeichen(
                                               governed_catalog, product,
                                               herkunft.get(_ident(product), [])),
                                           bezuege=scd_bezuege(governed_catalog, product, schemas))
                flow.append(f"- Verbund {' + '.join(f'`{q}`' for q in von)} → {gold_tbl} "
                            f"({kind})  ·  `{rel}`")
                continue
            if len(von) > 1 and not _formgleich(je_quelle):
                out[rel] = _ungeklaerte_zusammenfuehrung(product, kind, gold_tbl, dl, von,
                                                         je_quelle, c_ref)
                flow.append(f"- *(Zusammenführung offen: UNION oder JOIN)* → {gold_tbl}  ·  `{rel}`")
                continue
            out[rel] = _silver_to_gold(product, kind, von[0] if len(von) == 1 else von, c_ref, dl,
                                       gold_tbl=gold_tbl,
                                       table=_catalog_table(governed_catalog, _ident(product)),
                                       wasserzeichen=gold_wasserzeichen(
                                           governed_catalog, product,
                                           herkunft.get(_ident(product), [])),
                                       bezuege=scd_bezuege(governed_catalog, product, schemas))
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
        # Mehrere Herkuenfte je Domaene bleiben beim Domaenenverweis: ob vereinigt oder
        # verbunden gehoert, ist dieselbe offene Fachfrage wie oben.
        sources = _konforme_quellen(blueprint, governed_catalog, product, contributing,
                                    domains, schemas, stack,
                                    entscheidung_fuer(entscheidungen, "DATA-TEXTSPRACHE", "")
                                    or TEXTSPRACHE_VORGABE)
        _echte = [q for q in sources if q[1]]
        out[rel] = _silver_to_gold_conformed(
            product, kind, sources, contract_ref, dl, gold_tbl=gold_tbl,
            table=_catalog_table(governed_catalog, _ident(product)),
            # Nur bei EINEM Block (erklaerter Verbund): mehrere Herkuenfte tragen nicht
            # dieselbe Aenderungsspalte, und eine halbe waere schlimmer als keine.
            wasserzeichen=gold_wasserzeichen(governed_catalog, product, [])
            if len(_echte) == 1 else None)
        flow.append(f"- {' + '.join(q[1] for q in sources if q[1])} → {gold_tbl} ({kind})  ·  `{rel}`")
    if _conformed:
        flow.append("")

    geteilt = {q: e for q, e in ((governed_catalog or {}).get("source_tables") or {}).items()
               if e.get("eigentuemer_regel")}
    if geteilt:
        flow += ["## Gemeinsam genutzte Quelltabellen — eine Aufnahme (D-538, D-543)", "",
                 "| Quelltabelle | Aufgenommen als | Regel | Mitgelesen von |", "|---|---|---|---|"]
        for q, e in sorted(geteilt.items()):
            regel = ("ausdrücklich festgelegt" if e["eigentuemer_regel"] == "vorgabe" else
                     "⚠️ Paketreihenfolge (Annahme) — festlegen mit `--sap-quell-eigentuemer`")
            flow.append(f"| `{e.get('sap_tabelle', '')}` | `{q}` | {regel} | "
                        f"{', '.join(e.get('mitgelesen_von') or []) or '—'} |")
        flow.append("")
    doppelt = doppelt_geladene_quellen(blueprint)
    if doppelt:
        flow += ["## Befund: dieselbe Quelltabelle wird mehrfach geladen (OQ-42)", "",
                 "Die Aufnahme lädt diese Tabellen je Domäne einmal — also mehrmals. Zwei Kopien, "
                 "zu verschiedenen Zeiten geladen, laufen auseinander; ein konformes Ziel darüber "
                 "trägt dann zwei Fassungen desselben Schlüssels. Richtig wäre **eine** Aufnahme "
                 "in der besitzenden Domäne, die anderen lesen sie als fremde Quelle.", "",
                 "| Quellsystem | Tabelle | Geladen als | Domänen |", "|---|---|---|---|"]
        flow += [f"| {x['quellsystem'] or '—'} | `{x['tabelle']}` | "
                 f"{', '.join(f'`{q}`' for q in x['quellen'])} | {', '.join(x['domaenen'])} |"
                 for x in doppelt]
        flow.append("")
    out["transforms/_MEDALLION_FLOW.md"] = "\n".join(flow) + "\n"
    return out


#: Die Werte, die eine `DATA-INC`-Antwort tragen kann (Optionen-Katalog in
#: `decision_proposals._OPTIONEN["DATA-INC"]`). Hier genannt, damit ein unbekannter Wert
#: als Befund im Kopf steht und nicht still wie „nicht entschieden" behandelt wird.
_DATA_INC_WERTE = ("watermark", "vollast", "cdc", "partition")


def _silver_to_gold_incremental(name: str, kind: str, silver_tbl: str | list[str], contract_ref: str,
                                dl: dict, gold_tbl: str = "", star: bool = True,
                                proposal: dict | None = None,
                                wahl: str | None = None,
                                formgleich: bool = True,
                                table: dict | None = None,
                                konform: list[tuple] | None = None,
                                zusatz_kopf: str = "",
                                wasserzeichen: dict | None = None,
                                bezuege: list[dict] | None = None) -> str:
    """Incremental (upsert) silver→gold as a MERGE scaffold — the delta-load counterpart of the
    full-rebuild ``_silver_to_gold``. Honest by construction: the merge *shape* comes from the IR
    (target gold table, kind), the match key + watermark predicate are domain policy → TODO(contract).
    Fail-safe by design — an un-filled predicate leaves the placeholder un-parseable, so nobody
    accidentally ships a full re-scan as if it were incremental."""
    c = dl["comment"]
    gold_tbl = gold_tbl or f"gold_{_ident(name)}"

    def _using(inner: str) -> str:
        # D-559: dieselben Ersatzschluessel wie im Vollaufbau — sonst fehlten dem MERGE die
        # Spalten, die der Vollaufbau in Gold angelegt hat, und `INSERT *` braeche ab.
        if not bezuege:
            return inner
        return _einruecken(_mit_ersatzschluesseln(inner.rstrip("\n"), bezuege, dl), 4) + "\n"

    # **Das Produkt liest aus SEINEN Herkuenften, nicht aus der Domaenentabelle.** Derselbe Satz
    # steht seit dem 12.08.2026 in `emit_transforms` -- und band nur dort (dieselbe Klasse wie
    # D-501). Gemessen am ausgelieferten SAP-Szenario (DuckDB, 18.09.2026): alle 5 Kettenbefunde
    # der Klasse `incremental` lauteten `Table with name order_to_cash does not exist` bzw.
    # `procurement_mm` -- der MERGE las die **Domaene** als Tabelle, und die gibt es nie.
    quellen = [silver_tbl] if isinstance(silver_tbl, str) else list(silver_tbl)
    # Mehrere Herkuenfte mit verschiedener Form: dann ist offen, ob vereinigt oder verbunden
    # gehoert. Der Vollaufbau waehlt hier keine der beiden, sondern sagt es (`_ungeklaerte_-
    # zusammenfuehrung`) -- der MERGE tut dasselbe, statt sich eine Quelle auszusuchen.
    unklar = len(quellen) > 1 and not formgleich and not konform
    quelle = (_ZUSAMMENFUEHRUNG_OFFEN if unklar
              else _von_klausel(quellen))
    # **Dieselbe Projektion wie der Vollaufbau.** `SELECT *` aus Silber liefert die Spalten der
    # Quelltabelle; Gold hat die des governten Katalogs. Gemessen am SAP-Szenario (18.09.2026,
    # nachdem die Quelle stimmte): `table fact_delivery has 18 columns but 22 values were
    # supplied` -- fuenf von fuenf MERGEs, die ueberhaupt bis zum Binder kamen. Der Fehler lag
    # unter dem Tabellennamen und wurde erst sichtbar, als der behoben war.
    spalten = sorted(set((table or {}).get("columns") or []))
    auswahl = ("    SELECT *\n" if not spalten else
               "    SELECT\n"
               + ",\n".join(f"        {_projektion(sp, table, dl['stack'])}" for sp in spalten)
               + "\n")
    if konform:
        # OQ-40 (b): ein konformes Ziel liest die Herkuenfte ALLER speisenden Domaenen, jede
        # schon projiziert, vereinigt mit UNION — dieselbe Form wie der Vollaufbau unter
        # `transforms/_conformed/`. Aussen stehen dann nur noch die Zielnamen.
        quelle = ("(\n" + "\n        UNION\n".join(
            "        SELECT\n        "
            + _konforme_projektion(spalten, q[2] if len(q) > 2 else None, table,
                                   dl["stack"]).replace("\n    ", "\n        ")
            # Die Aenderungsspalte muss IM Block stehen, sonst kennt die aeussere Auswahl
            # `_wasserzeichen` nicht. Gemessen 24.09.2026 (Spark): der erste ausfuehrbare
            # konforme MERGE (`dim_material`, D-554) brach mit UNRESOLVED_COLUMN ab — solange
            # er Platzhalter war, fiel das nicht auf.
            + (f",\n        {zitiere(wasserzeichen['spalte'], dl['stack'])} AS {WASSERZEICHEN_SPALTE}"
               if wasserzeichen and wasserzeichen.get("spalte") else "")
            + f"\n        FROM {q[1]}" for q in konform if q[1])
            + "\n    )")
        auswahl = ("    SELECT *\n" if not spalten else
                   "    SELECT\n"
                   + ",\n".join(f"        {zitiere(sp, dl['stack'])}" for sp in spalten) + "\n")
    set_clause = "UPDATE SET *" if star else f"UPDATE SET <cols>  {c} explicit column mapping (non-Delta dialect)"
    ins_clause = "INSERT *" if star else "INSERT (<cols>) VALUES (<cols>)"
    scd = ""
    hist = (table or {}).get("historisierung") or {}
    if kind == "dimension" and hist.get("form") == "scd":
        scd = (f"{c} SCD: dieser MERGE haelt die Typ-1-Tabelle aktuell. Die Typ-2-Historie "
               f"({gold_tbl}_historie, D-551)\n"
               f"{c}   pflegt der Vollaufbau dieses Produkts (`transforms/<domaene>/`) — "
               f"wiederholbar, ohne Neuaufbau.\n")
    elif kind == "dimension":
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
        + (f"{c} Quelle: {', '.join(quellen)}.\n" if len(quellen) > 1 and not unklar
           and not konform else "")
        + zusatz_kopf
        + (f"{c} OFFEN: '{name}' entsteht aus {len(quellen)} Herkuenften mit VERSCHIEDENER Form\n"
           f"{c}   ({', '.join(quellen)}). Ob vereinigt oder verbunden gehoert, entscheidet der\n"
           f"{c}   Fachbereich -- die Fassungen stehen im Vollaufbau unter `transforms/`.\n"
           f"{c}   Absichtlich nicht ausfuehrbar: eine gruene Zeile waere hier die teuerste Antwort.\n"
           if unklar else "")
        + serving
        + scd
        + "".join(z + "\n" for z in _bezugs_kopf(bezuege or [], c))
    )
    keys, wm = (proposal or {}).get("keys") or [], (proposal or {}).get("watermark")
    # D-549: kuratierte Quellmetadaten gehen der Gold-Heuristik vor. Die Aenderungs- bzw.
    # Anlagespalte der Kopfquelle reist als `_wasserzeichen` nach Gold; das Praedikat liest sie
    # in der Quelle und vergleicht mit dem Stand in Gold.
    wz_praedikat = ""
    if wasserzeichen and wasserzeichen.get("spalte"):
        w = zitiere(wasserzeichen["spalte"], dl["stack"])
        quellspalte = WASSERZEICHEN_SPALTE if konform else w
        auswahl = auswahl.rstrip("\n") + (
            f",\n        {WASSERZEICHEN_SPALTE}\n" if konform
            else f",\n        {w} AS {WASSERZEICHEN_SPALTE}\n")
        wm = WASSERZEICHEN_SPALTE
        wz_praedikat = f"{quellspalte} > (SELECT MAX({WASSERZEICHEN_SPALTE}) FROM {gold_tbl})"
        head += (f"{c}\n{c} WASSERZEICHEN (kuratiert, D-549): {wasserzeichen['spalte']} aus "
                 f"{wasserzeichen['quelle']} — {wasserzeichen['art']}"
                 f"{' (' + wasserzeichen['von'] + ')' if wasserzeichen.get('von') else ''}.\n"
                 f"{c}   Gold traegt sie als {WASSERZEICHEN_SPALTE}; der Vollaufbau schreibt dieselbe "
                 f"Spalte.\n")
    elif wasserzeichen and wasserzeichen.get("keine"):
        wm = None
        head += (f"{c}\n{c} KURATIERT (D-549): {wasserzeichen['quelle']} hat keine verlaessliche "
                 f"Aenderungsspalte und ist veraenderlich.\n"
                 + (f"{c}   {wasserzeichen['hinweis']}\n" if wasserzeichen.get("hinweis") else "")
                 + f"{c}   Ein Watermark-MERGE traegt hier nicht — DATA-INC = vollast oder "
                 f"Aenderungsbelege.\n")
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
            f"{c}   Watermark : {wz_praedikat or f'{wm} > (SELECT MAX({wm}) FROM {gold_tbl})'}; "
            f"leeres Gold laedt alles.\n"
            f"{c}   Loeschungen in der Quelle kommen ohne Loeschkennzeichen nicht an (Katalog-Option).\n"
        )
        if "OVER (" in quelle:
            # Gemessen 24.09.2026 (Spark 3.5.1 + Delta 3.2.0, `dim_material`): steht eine
            # Fensterfunktion in der Quelle (Textverbund, D-542), materialisiert Delta die
            # MERGE-Quelle — und eine Unterabfrage auf das ZIEL darin bricht mit „Table does
            # not support reads“. Ohne Fensterfunktion (alle anderen MERGEs) tritt es nicht auf.
            # Dann steht der Vergleich zeilenweise in der Klausel statt als Filter der Quelle:
            # die Quelle wird ganz gelesen, geschrieben wird nur, was neuer ist.
            head += (f"{c}   Vergleich zeilenweise in der WHEN-Klausel: die Quelle enthaelt eine "
                     f"Fensterfunktion, und Delta\n"
                     f"{c}   liest das Ziel in einer materialisierten Quelle nicht (gemessen, "
                     f"D-554).\n")
            body = (
                f"MERGE INTO {gold_tbl} AS t\n"
                f"USING (\n"
                + _using(f"{auswahl}    FROM {quelle}\n")
                + f") AS s\n"
                f"ON {on}\n"
                f"WHEN MATCHED AND (t.{wm} IS NULL OR s.{wm} > t.{wm}) THEN {set_clause}\n"
                f"WHEN NOT MATCHED THEN {ins_clause}\n"
                f";\n"
            )
            return head + body
        body = (
            f"MERGE INTO {gold_tbl} AS t\n"
            f"USING (\n"
            + _using(f"{auswahl}    FROM {quelle}\n"
                     f"    WHERE (SELECT COUNT(*) FROM {gold_tbl}) = 0\n"
                     f"       OR {wz_praedikat or f'{wm} > (SELECT MAX({wm}) FROM {gold_tbl})'}\n")
            + f") AS s\n"
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
        + _using(f"{auswahl}    FROM {quelle}\n"
                 f"    {c} TODO(contract:{contract_ref}): incremental predicate — only rows changed since last load, e.g.\n"
                 f"    {c}   WHERE <watermark_col> > (SELECT COALESCE(MAX(<watermark_col>), DATE'1900-01-01') FROM {gold_tbl})\n")
        + f") AS s\n"
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

    # Konforme Ziele (OQ-40, D-536): ein Gold-Produkt, das mehrere Domaenen speisen, bekommt
    # EINEN MERGE unter `_conformed/` — dieselbe Regel wie der Vollaufbau. Vorher schrieb jede
    # speisende Domaene ihren eigenen MERGE auf dasselbe Ziel, mit den Herkuenften nur ihrer
    # Domaene: zwei Ladelogiken fuer eine Tabelle, und welche gewinnt, hing an der Reihenfolge.
    _by_product: dict[str, list[str]] = {}
    for _d in domains:
        for _p in _d.get("data_products", []) or []:
            _by_product.setdefault(_p, []).append(_d["name"])
    _conformed = {p: sorted(doms) for p, doms in _by_product.items() if len(doms) > 1}

    out: dict[str, str] = {}
    entschieden: list[tuple[str, str]] = []
    tabellenform: list[tuple[str, str, str]] = []
    wahl_je_domaene: dict[str, str | None] = {}
    for d in domains:
        ddir = _dirslug(d["name"])
        silver_tbl = layer_ref("silver", _ident(d["name"]), schemas)
        # Der Datenvertrag der DOMAENE, nicht der des Mandanten. Vier andere Emitter
        # (`emit_transforms`, Warehouse, DQ, MLV) rufen `_domain_contract` seit dem
        # 12.08.2026; dieser hier las `medallion.silver.data_contract_ref` einmal fuer alle.
        # Gemessen am SAP-Szenario: **17 von 17** Dateien nannten
        # `order-to-cash.silver.odcs.yaml`, 12 davon unter einer fremden Domaene.
        c_ref = _domain_contract(d, contract_ref)
        # Herkunft je Produkt, mit demselben Zuschnitt wie im Vollaufbau: Quellen, die laut IR
        # einer anderen Domaene gehoeren, materialisiert diese hier nicht.
        herkunft = _herkunft_je_domaene(blueprint, governed_catalog, d, domains)
        # `entscheidungen` ist das Profilfeld aus dem Rueckweg (C-3): `DATA-INC·<domaene>` bei
        # mehreren Domaenen, `DATA-INC` bei einer — dieselbe ID, die der Ledger vergibt.
        wahl = entscheidung_fuer(entscheidungen, "DATA-INC", d["name"])
        wahl_je_domaene[d["name"]] = wahl
        if wahl:
            entschieden.append((d["name"], wahl))
        for product in sorted(d.get("data_products", [])):
            if product in _conformed:
                continue                          # EIN MERGE unter `_conformed/`, siehe unten
            kind = kinds.get(product, "fact")
            gold_tbl = layer_ref("gold", _ident(product), schemas)
            rel = f"transforms/incremental/{ddir}/silver_to_gold__{_ident(product)}.sql"
            form = ((_catalog_table(governed_catalog, _ident(product)) or {})
                    .get("historisierung") or {}).get("form")
            if form in ("stichtag", "periode"):
                # D-552/D-553: die Ladeform steht je Tabelle kuratiert im Vollaufbau
                # (Tagesstand bzw. Periodenladung) — ein MERGE daneben waere eine zweite
                # Ladelogik fuer dieselbe Tabelle. Vorher stand hier fuer `fact_ar_open_item`
                # ein Platzhalter-MERGE auf eine Aenderungsspalte, die BSID nicht hat.
                tabellenform.append((product, d["name"], form))
                continue
            if wahl == "vollast":
                # Kein MERGE-Artefakt: bei Vollast ist der Vollaufbau `transforms/<domaene>/`
                # die einzige Ladeform. Gemessen 02.09.2026: eine Verweisdatei aus Kommentaren
                # meldete der Dialekt-Validator als „no executable SQL" — ein Befund ohne
                # Fehler. Warum die Datei fehlt, sagt die Tabelle in INCREMENTAL_REFRESH.md.
                continue
            # Ohne Aussage des Katalogs zur Herkunft bleibt es beim Zuschnitt je Domaene —
            # derselbe Grund wie im Vollaufbau: ein geratener Zuschnitt waere schlimmer als
            # ein grober. Mit Aussage liest das Produkt seine eigenen Quellen.
            eigene = [layer_ref("silver", _ident(q), schemas)
                      for q in herkunft.get(_ident(product), [])]
            kat_t = _catalog_table(governed_catalog, _ident(product)) or {}
            verbund = _text_verbund_sql(
                governed_catalog, product, herkunft.get(_ident(product), []), schemas, stack,
                entscheidung_fuer(entscheidungen, "DATA-TEXTSPRACHE", d["name"])
                or TEXTSPRACHE_VORGABE) if len(eigene) > 1 else None
            out[rel] = _silver_to_gold_incremental(
                product, kind, [verbund[0]] if verbund else (eigene or [silver_tbl]), c_ref, dl,
                gold_tbl, star,
                proposal=_incremental_proposal(governed_catalog, product), wahl=wahl,
                formgleich=True if verbund else _formgleich(kat_t.get("source_columns") or {}),
                table=kat_t or None,
                zusatz_kopf="".join(f"{dl['comment']} {z}\n" for z in (verbund[1] if verbund else [])),
                wasserzeichen=gold_wasserzeichen(governed_catalog, product,
                                                 herkunft.get(_ident(product), [])),
                bezuege=scd_bezuege(governed_catalog, product, schemas))

    konforme_zeilen: list[str] = []
    for product, contributing in sorted(_conformed.items()):
        kind = kinds.get(product, "dimension")
        gold_tbl = layer_ref("gold", _ident(product), schemas)
        rel = f"transforms/incremental/_conformed/silver_to_gold__{_ident(product)}.sql"
        wahlen = {dom: wahl_je_domaene.get(dom) for dom in contributing}
        werte = set(wahlen.values())
        if werte == {"vollast"}:
            # Alle speisenden Domaenen laden voll: der konforme Vollaufbau ist die Ladeform.
            konforme_zeilen.append(f"| `{product}` | {', '.join(contributing)} | `vollast` "
                                   f"| kein MERGE — Vollaufbau unter `transforms/_conformed/` |")
            continue
        # Dieselbe Herkunftsaufloesung wie im Vollaufbau (`emit_transforms`), damit beide
        # Ladeformen dieselben Tabellen lesen.
        sources = _konforme_quellen(blueprint, governed_catalog, product, contributing,
                                    domains, schemas, stack,
                                    entscheidung_fuer(entscheidungen, "DATA-TEXTSPRACHE", "")
                                    or TEXTSPRACHE_VORGABE)
        c = dl["comment"]
        zusatz = (f"{c} Konformes Ziel, gespeist von {len(contributing)} Domaenen: "
                  f"{', '.join(contributing)}.\n"
                  f"{c} EIN MERGE fuer EIN Ziel — je Domaene ein eigener haette dieselbe Tabelle "
                  f"mit zwei Ladelogiken\n"
                  f"{c} beschrieben, und welche gewinnt, haengt an der Reihenfolge (OQ-40).\n")
        eindeutig = len(werte) == 1
        # D-554: laden die Domaenen verschieden und liest nur EINE einen eigenen Block (die
        # anderen lesen deren Aufnahme mit, D-538/D-543), dann gehoert die Ladeform der
        # aufnehmenden Domaene — sie besitzt die Quelle, also auch deren Aenderungsspalte.
        # Gemessen 24.09.2026 an `dim_material`: Order-to-Cash nimmt MARA auf (watermark),
        # Inventory liest mit (vollast); der MERGE blieb Platzhalter, obwohl nur eine Seite
        # ueberhaupt liest.
        _blockdomaenen = [q[0] for q in sources if q[1]]
        kopf_eigner = (_blockdomaenen[0] if not eindeutig and len(_blockdomaenen) == 1
                       and wahlen.get(_blockdomaenen[0]) else None)
        if eindeutig:
            wahl = next(iter(werte))
        elif kopf_eigner and wahlen[kopf_eigner] == "vollast":
            konforme_zeilen.append(f"| `{product}` | {', '.join(contributing)} | `vollast` "
                                   f"(aufnehmende Domäne {kopf_eigner}, D-554) "
                                   f"| kein MERGE — Vollaufbau unter `transforms/_conformed/` |")
            continue
        elif kopf_eigner:
            wahl = wahlen[kopf_eigner]
            je = ", ".join(f"{dom} = {w or 'offen'}" for dom, w in sorted(wahlen.items()))
            zusatz += (f"{c} ENTSCHIEDEN ueber die Aufnahme (D-554): die Domaenen antworten "
                       f"verschieden ({je}),\n"
                       f"{c}   aber nur {kopf_eigner} nimmt die Quelle auf — deren Antwort "
                       f"'{wahl}' gilt fuer '{product}'.\n")
        else:
            wahl = None
            je = ", ".join(f"{dom} = {w or 'offen'}" for dom, w in sorted(wahlen.items()))
            zusatz += (f"{c} BEFUND: die speisenden Domaenen haben DATA-INC verschieden beantwortet "
                       f"({je}).\n"
                       f"{c}   Ein Ziel hat eine Ladelogik; bis sie fuer '{product}' feststeht, "
                       f"bleiben die Platzhalter.\n")
        kat_t = _catalog_table(governed_catalog, _ident(product)) or {}
        if kat_t.get("key"):
            zusatz += (f"{c} TODO(contract:{contract_ref}): Vorrang festlegen, falls dieselbe "
                       f"Schluesselzeile je Domaene verschiedene\n"
                       f"{c}   Attribute traegt — UNION entfernt nur EXAKTE Dubletten, und zwei "
                       f"Quellzeilen je Schluessel\n"
                       f"{c}   brechen den MERGE ab (mehrere Quellzeilen fuer eine Zielzeile).\n")
        out[rel] = _silver_to_gold_incremental(
            product, kind, [q[1] for q in sources if q[1]], contract_ref, dl, gold_tbl, star,
            proposal=_incremental_proposal(governed_catalog, product), wahl=wahl,
            table=kat_t or None, konform=sources, zusatz_kopf=zusatz,
            wasserzeichen=gold_wasserzeichen(governed_catalog, product, [])
            if len([q for q in sources if q[1]]) == 1 else None)
        wirkung = (f"ein MERGE, `{wahl}`" if eindeutig and wahl else
                   f"ein MERGE, `{wahl}` — Antwort der aufnehmenden Domäne {kopf_eigner} (D-554)"
                   if kopf_eigner else
                   "ein MERGE, Platzhalter" + ("" if eindeutig else " — Antworten widersprechen sich"))
        je_dom = ", ".join(f"{dom}: `{w or 'offen'}`" for dom, w in sorted(wahlen.items()))
        konforme_zeilen.append(f"| `{product}` | {', '.join(contributing)} | {je_dom} | {wirkung} |")

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
    if tabellenform:
        _wort = {"stichtag": "Vollersatz der aktuellen Tabelle + Tagesstand in `<ziel>_stichtag` (D-552)",
                 "periode": "Erstbefüllung, danach jüngste Periode und neuere per MERGE (D-553)"}
        doc += [
            "",
            "## Ladeform je Tabelle kuratiert (kein MERGE in diesem Ordner)",
            "",
            "Diese Tabellen laden im Vollaufbau (`transforms/<domäne>/`) in einer eigenen, wiederholbaren Form — "
            "sie gilt vor der DATA-INC-Antwort der Domäne, weil sie je Tabelle kuratiert ist.",
            "",
            "| Ziel | Domäne | Form | Wirkung |",
            "|---|---|---|---|",
            *[f"| `{p}` | {dom} | `{f}` | {_wort[f]} |" for p, dom, f in tabellenform],
        ]
    if konforme_zeilen:
        doc += [
            "",
            "## Konforme Ziele (`_conformed/`, OQ-40)",
            "",
            "Ein Gold-Produkt, das mehrere Domänen speisen, hat **einen** MERGE mit den "
            "Herkünften aller Domänen — wie der Vollaufbau. Laden die Domänen verschieden, gilt "
            "die Antwort der Domäne, die die Quelle aufnimmt (D-554); lesen mehrere eigene "
            "Blöcke, bleibt der MERGE Platzhalter, bis für das Ziel eine Ladelogik feststeht.",
            "",
            "| Ziel | Domänen | DATA-INC | Wirkung |",
            "|---|---|---|---|",
            *konforme_zeilen,
        ]
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


def _warehouse_platzhalter_spalten(name: str, kind: str, contract_ref: str) -> str:
    """Kind-abhaengige Platzhalterspalten mit ``TODO(contract:…)``, wenn kein Katalog vorliegt."""
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
    return cols


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
    cols = _warehouse_platzhalter_spalten(name, kind, contract_ref)
    return (f"-- gold {kind} '{name}' as a Fabric Warehouse table (T-SQL / Warehouse endpoint).\n"
            f"-- Contract: {contract_ref}\n"
            + kopf
            + f"IF OBJECT_ID('{tbl}', 'U') IS NULL\n"
              f"CREATE TABLE {tbl} (\n{cols}\n);\n")


# --- D-605 Stufe 1: deklaratives SDK-Style-Projekt aus derselben Quelle -----------------------
#
# Die Skripte oben bleiben der Laufweg (``run_sql_ddl``). Das Projekt ist das Offline-Tor: ``dotnet
# build`` gegen das offizielle Fabric-DW-Modell (``Microsoft.SqlServer.Dacpacs.FabricDw``) prueft
# die Gold-DDL ohne Tenant (Learn ``fabric/data-warehouse/develop-warehouse-project``, gelesen
# 30.09.2026: nur SDK-Style-Projekte, DSP ``SqlDwUnifiedDatabaseSchemaProvider``). Deklarativ heisst:
# ``CREATE SCHEMA``/``CREATE TABLE`` ohne ``IF``-Waechter — DacFx vergleicht Modelle, nicht Stapel.
# Die Versionen sind Pins in ``research/upstream_pins.yaml`` (``nuget``), gemessen per nuget.org-API
# am 30.09.2026; der Drift-Sensor ``make check-upstream`` liest sie von dort.
WAREHOUSE_PROJEKT_DIR = "warehouse/sqlproj"
WAREHOUSE_PROJEKT_NAME = "GoldWarehouse"
SQL_SDK_VERSION = "2.3.0"               # Microsoft.Build.Sql, stabil seit 17.09.2026
FABRIC_DW_DACPAC_VERSION = "170.0.4"    # Microsoft.SqlServer.Dacpacs.FabricDw, seit 03.06.2026


def _warehouse_objekt(name: str, schemas: bool) -> tuple[str, str]:
    """``(schema, tabelle)`` — dieselbe Namensregel wie ``_warehouse_ddl``."""
    ref = layer_ref("gold", _ident(name), schemas)
    return tuple(ref.split(".", 1)) if schemas else ("dbo", ref)  # type: ignore[return-value]


def _sqlproj_xml(name: str) -> str:
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<!-- generated (D-605 Stufe 1) — Offline-Tor fuer die Gold-DDL; der Laufweg bleibt '
        'warehouse/<domaene>/gold_*.sql. Nicht von Hand aendern. -->\n'
        '<Project DefaultTargets="Build">\n'
        f'  <Sdk Name="Microsoft.Build.Sql" Version="{SQL_SDK_VERSION}" />\n'
        '  <PropertyGroup>\n'
        f'    <Name>{name}</Name>\n'
        '    <DSP>Microsoft.Data.Tools.Schema.Sql.SqlDwUnifiedDatabaseSchemaProvider</DSP>\n'
        '    <ModelCollation>1033, CI</ModelCollation>\n'
        '  </PropertyGroup>\n'
        '  <ItemGroup>\n'
        '    <PackageReference Include="Microsoft.SqlServer.Dacpacs.FabricDw" '
        f'Version="{FABRIC_DW_DACPAC_VERSION}" />\n'
        '  </ItemGroup>\n'
        '  <Target Name="BeforeBuild">\n'
        '    <Delete Files="$(BaseIntermediateOutputPath)\\project.assets.json" />\n'
        '  </Target>\n'
        '</Project>\n')


def emit_warehouse_project(blueprint: dict, schemas: bool = False,
                           governed_catalog: dict | None = None,
                           name: str = WAREHOUSE_PROJEKT_NAME) -> dict[str, str]:
    """Gold als deklaratives SDK-Style-Projekt (``path → content``) unter ``warehouse/sqlproj/``.

    Eine Datei je Objekt im Layout Schema/Objekttyp (``<schema>/Tables/<tabelle>.sql``), dazu
    ``Security/<schema>.sql`` fuer ein echtes Gold-Schema. Spalten aus derselben Quelle wie die
    Skripte (``_warehouse_columns`` bzw. ``_warehouse_platzhalter_spalten``) — ein Test stellt beide
    Ausgaben gegeneinander (Tabellen, Spalten, Typen, NULL-barkeit).
    """
    med = blueprint.get("medallion", {})
    contract_ref = med.get("silver", {}).get("data_contract_ref", "<silver-contract>")
    kinds = _gold_kinds(blueprint)
    out: dict[str, str] = {f"{WAREHOUSE_PROJEKT_DIR}/{name}.sqlproj": _sqlproj_xml(name)}
    if schemas:
        out[f"{WAREHOUSE_PROJEKT_DIR}/Security/gold.sql"] = "CREATE SCHEMA [gold];\n"
    for d in sorted(blueprint.get("mesh", {}).get("domains", []), key=lambda d: d.get("name", "")):
        c_ref = _domain_contract(d, contract_ref)
        for product in sorted(d.get("data_products", [])):
            kind = kinds.get(product, "fact")
            table = _catalog_table(governed_catalog, _ident(product))
            cols = (_warehouse_columns(table or {}, c_ref)
                    or _warehouse_platzhalter_spalten(product, kind, c_ref))
            schema, tabelle = _warehouse_objekt(product, schemas)
            out[f"{WAREHOUSE_PROJEKT_DIR}/{schema}/Tables/{tabelle}.sql"] = (
                f"-- gold {kind} '{product}' (Domaene {d['name']}). Contract: {c_ref}\n"
                f"CREATE TABLE [{schema}].[{tabelle}] (\n{cols}\n);\n")
    return out


def emit_warehouse_gold(blueprint: dict, schemas: bool = False,
                        governed_catalog: dict | None = None,
                        sqlproj: bool = False) -> dict[str, str]:
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
           "**Column descriptions are not emitted here** (I-21 W5.6 e): MS Learn *T-SQL surface "
           "area in Fabric Data Warehouse* (read 2026-09-29) documents neither `COMMENT` nor "
           "extended properties (`sp_addextendedproperty`) for Warehouse tables. Lakehouse gold "
           "carries them as `ALTER COLUMN … COMMENT` (documented for Delta tables).", "",
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
    if sqlproj:
        # D-605 Stufe 1: dieselbe Quelle, zweite Form. Nur unter Flag; Laufweg bleiben die Skripte.
        out.update(emit_warehouse_project(blueprint, schemas=schemas,
                                          governed_catalog=governed_catalog))
        doc += ["", "## Declarative SDK-style project (D-605 stage 1)", "",
                f"`{WAREHOUSE_PROJEKT_DIR}/{WAREHOUSE_PROJEKT_NAME}.sqlproj` — the same tables as "
                "declarative `CREATE TABLE` (no `IF` guards), one file per object. It is an "
                "**offline gate**, not a deploy path: `dotnet build` validates it against "
                f"`Microsoft.SqlServer.Dacpacs.FabricDw` {FABRIC_DW_DACPAC_VERSION} "
                f"(`Microsoft.Build.Sql` {SQL_SDK_VERSION}). Run "
                "`bash scripts/check_warehouse_sqlproj.sh <dir>`: exit 0 built, 1 build failed, "
                "2 not run (no .NET SDK) — 2 is not green."]
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
    # Die Platzhalter tragen seit 29.09.2026 KEINEN Test mehr: `dq/` ist jetzt ein lauffaehiges
    # dbt-Projekt, und ein Test auf eine Spalte, die es nicht gibt, endet dort mit ERROR
    # (gemessen mit dbt 1.12.5: `not_null_gold_fact_ledger__dimension_foreign_key_` ERROR). Ein
    # Tor, das immer rot ist, wird abgeschaltet. Der TODO bleibt sichtbar in der Beschreibung.
    elif kind == "fact":
        cols = [{"name": "<dimension_foreign_key>",
                 "description": f"TODO(contract:{contract_ref}): FK not_null + relationships test"}]
    else:  # aggregate
        cols = [{"name": "<group_key>",
                 "description": f"TODO(contract:{contract_ref}): grouping grain not_null"}]
    # Die Schnittspalten kommen ZUSAETZLICH, nie statt der Schluesseltests: sie stehen auf einer
    # anderen Achse (wer darf die Zeile sehen) als der Schluessel (haengt die Zeile richtig).
    vorhanden = {c.get("name") for c in cols}
    cols = cols + [t for t in _schnitt_spalten_tests(schnitt) if t["name"] not in vorhanden]
    return {"name": f"gold_{_ident(name)}",
            "description": f"gold {kind} '{name}' — runtime DQ gate (Contract: {contract_ref})",
            "columns": cols}


#: Name des Fabric-dbt-Jobs, der die DQ-Tore faehrt (W2.4). Ein Name, weil ein Job alle Domaenen
#: prueft — die Tore sind ein dbt-Projekt, nicht eins je Domaene.
DBT_DQ_JOB = "dbt_dq_gates"


def _dbt_projekt(modelle: list[tuple[str, str, str]]) -> dict[str, str]:
    """``dbt_project.yml`` + je Gold-Produkt ein **ephemeres** Modell, das die Tabelle nur liest.

    Anlass (29.09.2026, W2.4): ``dq/<domaene>/schema.yml`` beschrieb Tests fuer Modelle, die es
    in keinem dbt-Projekt gab. dbt haengt Tests nur an Knoten, die existieren; ein ``schema.yml``
    ohne Modell ist ein Patch ins Leere und ``dbt test`` meldet dann **nichts gefunden**, obwohl
    es nichts geprueft hat. Mit dem Job-Item (unten) waere genau das ein gruener Lauf gewesen.

    ``ephemeral`` legt nichts an: dbt setzt das Modell als CTE in jede Testabfrage ein. Die
    Gold-Tabelle bleibt Sache des Transform-Pfads; das dbt-Projekt prueft sie nur.
    """
    out = {"dq/dbt_project.yml": yaml.safe_dump({
        "name": "meridian_dq_gates", "version": "1.0.0", "config-version": 2,
        "profile": "meridian_dq_gates",
        # Die Modelle liegen neben ihren schema.yml in dq/<domaene>/. Nicht "." — dann liest dbt
        # auch dbt_project.yml als Schemadatei und bricht ab (gemessen 29.09.2026, dbt 1.12.5:
        # "The schema file at ./dbt_project.yml is invalid").
        "model-paths": sorted({o for o, _m, _t in modelle}),
        "models": {"meridian_dq_gates": {"+materialized": "ephemeral"}},
    }, sort_keys=False, allow_unicode=True)}
    for ordner, modell, tabelle in modelle:
        out[f"dq/{ordner}/{modell}.sql"] = (
            "-- generiert: liest die Gold-Tabelle nur, damit dbt die Tests aus schema.yml\n"
            "-- daran haengen kann (ephemeral: dbt legt nichts an).\n"
            "{{ config(materialized='ephemeral') }}\n"
            f"select * from {tabelle}\n")
    return out


def _dbt_job_item(name: str, workspace_token: str, lakehouse_token: str, schemas: bool,
                  select: list[str] | None = None) -> dict[str, str]:
    """Das Fabric-Item ``DataBuildToolJob`` (W2.4), das die DQ-Tore mit ``dbt test`` faehrt.

    Form nach MS Learn *DataBuildToolJob item definition* (abgerufen 29.09.2026): Teil
    ``dbtjob-content.json`` mit ``project`` / ``profile`` / ``command``; ``operation`` einer von
    ``run, build, show, seed, compile, test, snapshot``. **Nicht belegt** sind die Werte
    ``profileType``/``connectionSettings.type`` fuer das Lakehouse-Profil — die Seite zeigt nur
    ``DataWarehouse`` und ``PostgreSql``. ``Lakehouse`` ist hier eine ANNAHME, ungeprueft; ein
    falscher Wert scheitert laut beim Import, nicht still.
    """
    verbindung = {"type": "Lakehouse",
                  "properties": {"workspaceId": workspace_token, "artifactId": lakehouse_token}}
    inhalt = {
        "project": {"projectType": "Lakehouse", "folderPath": "Files/dq",
                    "connectionSettings": verbindung},
        "profile": {"profileType": "Lakehouse", "schema": "gold" if schemas else "dbo",
                    "connectionSettings": verbindung},
        "command": {"operation": "test", "arguments": {
            **({"select": ",".join(select)} if select else {}),
            "failFast": False, "threads": 4}},
    }
    platform = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/"
                   "platformProperties/2.0.0/schema.json",
        "metadata": {"type": "DataBuildToolJob", "displayName": name},
        "config": {"version": "2.0", "logicalId": "00000000-0000-0000-0000-000000000000"},
    }
    import json as _json
    return {
        f"dq/{name}.DataBuildToolJob/dbtjob-content.json":
            _json.dumps(inhalt, indent=2, ensure_ascii=False) + "\n",
        f"dq/{name}.DataBuildToolJob/.platform": _json.dumps(platform, indent=2) + "\n",
    }


def _dbt_job_doc(n_tests: int, jobs: list[tuple[str, str, int]]) -> list[str]:
    return [
        "", "## Ausfuehrung als Fabric-dbt-Job (W2.4)", "",
        f"{len(jobs)} Job(s) fahren `dbt test` auf diesem Projekt (`dbt_project.yml`, ein "
        f"ephemeres Modell je Gold-Produkt, {n_tests} Spaltentest(s) in den `schema.yml`), einer "
        "je Gold-Workspace. Quelle: MS Learn *dbt job in Microsoft Fabric*, *DataBuildToolJob "
        "item definition* (abgerufen 29.09.2026).",
        "",
        "| Job | Workspace | Modelle |", "|---|---|---|",
        *(f"| `{n}.DataBuildToolJob` | `{w}` | {k} |" for n, w, k in jobs),
        "",
        "| Punkt | Stand |", "|---|---|",
        "| Adapter | Fabric Lakehouse = `dbt-fabricspark` 1.12.2, dbt Core 1.11, "
        "Job-Laufzeit 1.0; Authentifizierung nur Microsoft Entra (OAuth) |",
        "| Projekt | liegt im Lakehouse unter `Files/dq` (dieser Ordner) — hochladen ist ein "
        "Deploy-Schritt |",
        "| `profileType`/`type` = `Lakehouse` | **ANNAHME, ungeprueft** — Learn zeigt nur "
        "`DataWarehouse` und `PostgreSql`; beim ersten Import pruefen (Tenant-gated) |",
        "| Freigabe | Mandanteneinstellung *dbt jobs* muss an sein; Learn fuehrt sie am 29.09.2026 "
        "noch als „(preview)“, die Pipeline-Aktivitaet ebenfalls — „GA Sep 2026“ ist dort nicht "
        "belegt |",
        "| Kosten | 2 CU-Stunden je Laufstunde (Learn *dbt job pricing*) |",
        "",
        "**Rot heisst rot.** `dbt test` endet mit Fehler, sobald ein Test Zeilen findet — der Job "
        "ist dann fehlgeschlagen. Ein Projekt ohne Modelle haette nichts geprueft und waere gruen "
        "gewesen; deshalb stehen die Modelle hier.",
    ]


def emit_dq_gates(blueprint: dict, schemas: bool = False,
                  column_tests: dict[str, list[dict]] | None = None,
                  stack: str | None = None,
                  lakehouse: str = "analytics_gold") -> dict[str, str]:
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
    Suppliers: the SAP pack (``sap_dq``), the introspected source (``provision_dq``, ingress) and
    the data contract's ``column_specs`` (``provision_dq.vertrags_spaltentests``, ALUCA A-20) and
    the catalog's star edges (``provision_dq.beziehungs_spaltentests``, W5.11).

    Seit 29.09.2026 (W2.4) ist ``dq/`` ein lauffaehiges dbt-Projekt (``dbt_project.yml`` + ein
    ephemeres Modell je Gold-Produkt), und ``stack="fabric"`` legt das Fabric-Item
    ``DataBuildToolJob`` dazu, das ``dbt test`` faehrt.
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
    dbt_modelle: list[tuple[str, str, str]] = []
    modell_namen: set[str] = set()
    je_domaene: dict[str, list[str]] = {}
    n_tests = 0
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
        for p in prods:
            m = f"gold_{_ident(p)}"
            if m not in modell_namen:
                modell_namen.add(m)
                dbt_modelle.append((_dirslug(d["name"]), m, layer_ref("gold", _ident(p), schemas)))
                je_domaene.setdefault(d["name"], []).append(m)
            n_tests += sum(len(c.get("tests") or []) for e in models if e["name"] == m
                           for c in e.get("columns") or [])
    out.update(_dbt_projekt(dbt_modelle))
    if stack == "fabric" and dbt_modelle:
        # Ein Job je Gold-Workspace: der Job verbindet genau ein Lakehouse, und jede Domaene
        # haelt ihr Gold im eigenen Workspace (`gold_workspace_of`). Ein Job fuer alle haette
        # die Tabellen der anderen Domaenen gar nicht gesehen.
        from core.dataarch_engine.blueprint.provision_apply import PLACEHOLDER_WORKSPACE, gold_workspace_of
        je_ws: dict[str, list[str]] = {}
        for dom, ms in sorted(je_domaene.items()):
            je_ws.setdefault(gold_workspace_of(blueprint, dom, fallback=PLACEHOLDER_WORKSPACE),
                             []).extend(ms)
        jobs: list[tuple[str, str, int]] = []
        for ws, ms in sorted(je_ws.items()):
            name = DBT_DQ_JOB if len(je_ws) == 1 else f"{DBT_DQ_JOB}__{_ident(ws)}"
            ws_token = ("<workspace-id>" if ws == PLACEHOLDER_WORKSPACE
                        else f"<{ws}-workspace-id>")
            lh_token = ("<lakehouse-id>" if ws == PLACEHOLDER_WORKSPACE
                        else f"<{ws}/{lakehouse}-lakehouse-id>")
            out.update(_dbt_job_item(name, ws_token, lh_token, schemas,
                                     select=None if len(je_ws) == 1 else sorted(ms)))
            jobs.append((name, ws, len(ms)))
        doc += _dbt_job_doc(n_tests, jobs)
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


#: Fabric-Laufzeiten, fuer die der MLV-Emitter eine Aussage hat (W2.2). Quelle: MS Learn
#: *Apache Spark runtimes in Fabric* und *Lifecycle*, abgerufen 29.09.2026.
MLV_LAUFZEITEN = {
    "1.3": {"spark": "3.5", "delta": "3.2", "stand": "EOSA, Support bis 30.09.2026, danach LTS "
            "bis März 2027", "mlv_belegt": True},
    "2.0": {"spark": "4.1", "delta": "4.2", "stand": "GA, Support bis 31.08.2028",
            "mlv_belegt": False},
}
#: Ausloeser des MLV-Refresh (D-529, Nachtrag W2.3).
MLV_AUSLOESER = ("zeitplan", "ereignis")


def emit_mlv(blueprint: dict, schemas: bool = True,
             governed_catalog: dict | None = None,
             entscheidungen: dict | None = None,
             runtime: str = "1.3",
             ausloeser: str = "zeitplan",
             refresh_hints: bool = False,
             pipeline_name: str = "medallion_orchestration") -> dict[str, str]:
    """Emit the medallion as **Materialized Lake Views** (declarative, SQL-only). Idea I-20.7.

    GA (Spark SQL), SQL-only. MS Learn *What's new archive*, gelesen 01.10.2026: "March 2026 ·
    Materialized Lake Views (Generally Available)"; preview ist nur noch das PySpark-Authoring, das
    hier nicht genutzt wird. Grammatik am 01.10.2026 gegen *Spark SQL reference for materialized
    lake views* nachgeprueft (Klauselfolge unveraendert). One ``CREATE OR REPLACE MATERIALIZED LAKE VIEW`` per gold
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
    * **Contract checks** — ``column_specs[].checks`` (ALUCA A-20) become additional ``CHECK``
      constraints with the same kind policy (``provision_dq.vertrags_constraints``); a check on a
      column outside the projection stays a TODO comment (never a constraint on a missing column).
    * **PARTITIONED BY** — emitted only for a real date-ish catalog column; otherwise the grain is noted
      as a partition TODO comment (grain is prose, not a column).
    * **TBLPROPERTIES** — deterministic provenance tags (generator/layer/kind), always valid.

    **Dependency management is automatic, the refresh is not** (D-529). Fabric orders the views by their
    SELECT refs and picks the refresh *strategy* (skip / incremental / full) — but a refresh only runs
    when something *triggers* it: a lineage schedule, the job scheduler REST API, a pipeline activity or
    a manual ``REFRESH … FULL``. Until 23.09.2026 this docstring, the SQL header and the apply plan all
    said "refresh automatic, no orchestration", and the delivery emitted no trigger: a delivered MLV set
    would have been built once and never refreshed, without anything failing. The emitter therefore
    writes ``mlv/refresh_schedule.json`` (request body for the lakehouse's RefreshMaterializedLakeViews
    schedule) and says in ``_MLV.md`` who triggers what. Non-SQL logic (ML/Python/API) is out of MLV
    scope → the doc points at the notebook fallback (``emit_notebooks``). Deterministic; emits only.

    Seit 29.09.2026 (Plan I-21):

    * ``runtime`` (W2.2) — ``"1.3"`` (Vorgabe) oder ``"2.0"``; steht im Dokument mit dem, was fuer
      die Laufzeit belegt ist und was nicht (``MLV_LAUFZEITEN``). Die DDL bleibt gleich.
    * ``ausloeser`` (W2.3, Nachtrag D-529) — ``"zeitplan"`` (Vorgabe) oder ``"ereignis"``: dann
      zusaetzlich ``mlv/refresh_event.json``, die Beschreibung eines ereignisgesteuerten
      Ausloesers (Preview, Einrichtung im Portal). ``refresh_schedule.json`` bleibt der
      reproduzierbare Rueckfall.
    * ``refresh_hints`` (W5.8) — schreibt fuer Dimensionen mit belegtem Schluessel
      ``REFRESH_HINT … UNIQUE (…)`` (Preview), damit Updates/Deletes inkrementell laufen koennen.
    """
    if runtime not in MLV_LAUFZEITEN:
        raise ValueError(f"runtime {runtime!r} unbekannt — erlaubt: {sorted(MLV_LAUFZEITEN)}")
    if ausloeser not in MLV_AUSLOESER:
        raise ValueError(f"ausloeser {ausloeser!r} unbekannt — erlaubt: {list(MLV_AUSLOESER)}")
    med = blueprint.get("medallion", {})
    contract_ref = med.get("silver", {}).get("data_contract_ref", "<silver-contract>")
    kinds = _gold_kinds(blueprint)
    grains = _gold_grains(blueprint)
    hints: list[str] = []
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
    doc = ["# Materialized Lake Views — declarative medallion (generated — SQL-only)", "",
           *schema_warning,
           "> **SQL-only** (Fabric Materialized Lake Views, generally available since March 2026 per MS "
           "Learn *What's new*; only PySpark authoring is still preview and is not used here). Non-SQL logic "
           "(ML/Python/API/cleansing beyond SQL) is out of scope → use the notebook transforms "
           "(`--emit-notebooks`) for those hops. MLV **dependency management** is automatic (the "
           "engine chains views by their SELECT refs) — **the refresh is not**: it runs only when a "
           "schedule, an API call or a pipeline activity triggers it. See *Refresh* below.",
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
                f"-- silver → gold '{product}' as a Materialized Lake View ({kind}).  SQL-only.",
                f"-- Contract: {c_ref}  ·  dependency order automatic; the REFRESH runs only when "
                f"triggered — see mlv/refresh_schedule.json and mlv/_MLV.md (D-529)."]
            _bez = scd_bezuege(governed_catalog, product, schemas)
            if _bez:
                preamble.append(
                    f"-- BEFUND (D-559): '{product}' traegt im Transform-Pfad "
                    f"{', '.join(b['spalte'] for b in _bez)} (Version der Dimension zum "
                    f"Belegdatum); das Semantikmodell bezieht sich darauf. Diese Sicht fuehrt die "
                    f"Spalten nicht — als Gold-Pfad passt sie nicht zum Modell.")
            _hform = ((kat or {}).get("historisierung") or {}).get("form")
            if _hform:
                # D-551..D-553: eine MLV ist eine Sicht auf den aktuellen Stand; Geschichte, die
                # die Quelle nicht haelt, kann sie nicht halten. Der Transform-Pfad tut es.
                preamble.append(
                    f"-- BEFUND (D-551..D-553): '{product}' haelt kuratiert Geschichte "
                    f"(`{_hform}`). Eine MLV kann das nicht — sie zeigt den aktuellen Stand. "
                    f"Die Historie entsteht nur im Transform-Pfad "
                    f"(`transforms/…/silver_to_gold__{pident}.sql`).")

            # --- #1 DQ constraint: active when the key is known, else a valid template comment ----------
            # Dazu die Pruefungen aus dem Datenvertrag (`column_specs`, Lieferant 3, ALUCA A-20),
            # uebersetzt an EINER Stelle (`provision_dq.vertrags_constraints`), mit derselben
            # Art-Politik: MS Learn — stehen DROP und FAIL in einer Sicht, gewinnt FAIL.
            from core.dataarch_engine.blueprint.provision_dq import vertrags_constraints
            vertrag_zeilen, vertrag_offen = vertrags_constraints(kat, pident, action, columns)
            preamble.extend(vertrag_offen)
            if key_col:
                zeilen = [f"    CONSTRAINT {pident}_{suffix}_not_null "
                          f"CHECK ({key_col} IS NOT NULL) ON MISMATCH {action}", *vertrag_zeilen]
                # W5.8: REFRESH_HINT nur fuer Dimensionen mit Katalogschluessel — dort ist er
                # der Schluessel der Tabelle, und `dq/` prueft ihn mit `unique`. Fabric prueft
                # die Eindeutigkeit selbst NICHT (MS Learn, 29.09.2026).
                if refresh_hints and kind == "dimension" and kat:
                    zeilen.insert(0, f"    REFRESH_HINT {pident}_key UNIQUE ({zitiere(key_col)})")
                    hints.append(f"`{mlv_name}` ({key_col})")
                constraint_cell = f"`… CHECK ({key_col} …) ON MISMATCH {action}`"
            else:
                zeilen = list(vertrag_zeilen)
                preamble.append(
                    f"-- TODO(contract:{c_ref}): add the DQ constraint once the key column is known — "
                    f"CONSTRAINT {pident}_{suffix}_not_null CHECK (<{kind}_key> IS NOT NULL) ON MISMATCH {action}")
                constraint_cell = f"template (no catalog key) · ON MISMATCH {action}"
            constraint_block = (" (\n" + ",\n".join(zeilen) + "\n)") if zeilen else ""
            if vertrag_zeilen:
                constraint_cell += f" + {len(vertrag_zeilen)} contract check(s)"

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
            # `delta.enableChangeDataFeed`: Voraussetzung dafuer, dass eine MLV, die auf DIESER
            # aufsetzt, inkrementell aktualisiert werden kann (MS Learn, *Optimal refresh*,
            # 23.09.2026: CDF auf **allen** Quellen, und die Quellen append-only im Zyklus).
            # Hier stand es nirgends in der Lieferung (D-529).
            tblprops = (f"\nTBLPROPERTIES ('generated_by' = 'meridian-dataarch', "
                        f"'medallion_layer' = 'gold', 'mlv_kind' = '{kind}', "
                        f"'delta.columnMapping.mode' = 'name', "
                        f"'delta.minReaderVersion' = '2', 'delta.minWriterVersion' = '5', "
                        f"'delta.enableChangeDataFeed' = 'true')")

            sql = ("\n".join(preamble) + "\n"
                   f"CREATE OR REPLACE MATERIALIZED LAKE VIEW {mlv_name}{constraint_block}{partition_clause}\n"
                   f"COMMENT 'gold {kind} {product} (generated)'"
                   f"{tblprops}\n"
                   f"AS\n{select_body}\n")
            out[f"mlv/{ddir}/{pident}.mlv.sql"] = sql
            doc.append(f"| {d['name']} | `{mlv_name}` | {kind} | {len(columns) or '—'} | "
                       f"{constraint_cell} | {partition_cell} |")
    # Ob eine Sicht je inkrementell laeuft, entscheidet das Schreibmuster ihrer Quelle — und
    # das legt `DATA-SILVER-LOAD` fest (D-534). Das Dokument nennt, was gewaehlt ist, statt
    # den Vollaufbau zu behaupten, den eine Antwort `append` laengst abgeloest hat.
    from core.dataarch_engine.blueprint.decision_proposals import entscheidung_fuer
    ladeformen = {d.get("name", ""): (entscheidung_fuer(entscheidungen, "DATA-SILVER-LOAD",
                                                        d.get("name", "")) or "vollaufbau")
                  for d in blueprint.get("mesh", {}).get("domains", []) or []}
    doc += _mlv_refresh_doc(ladeformen)
    doc += _mlv_ereignis_doc(ausloeser, pipeline_name)
    doc += _mlv_hint_doc(refresh_hints, hints)
    doc += _mlv_laufzeit_doc(runtime)
    out["mlv/_MLV.md"] = "\n".join(doc) + "\n"
    if ausloeser == "ereignis":
        out["mlv/refresh_event.json"] = _mlv_refresh_event(pipeline_name)
    # Der Ausloeser. Dieselbe Zeitplan-Gestalt wie `orchestration/schedule.json` (Werkzeug-
    # Wiederverwendung), eine Stunde nach dessen Vorgabe: die MLV liest Silber, und Silber
    # entsteht in der Pipeline. Zeitversatz ist eine Annahme, keine Kopplung — steht im Dokument.
    from core.dataarch_engine.blueprint.fabric_schedule import emit_schedule
    out["mlv/refresh_schedule.json"] = emit_schedule(time=MLV_REFRESH_UHRZEIT)
    return out


#: Eine Stunde nach der Pipeline-Vorgabe (`fabric_schedule.emit_schedule`: 02:00 UTC).
MLV_REFRESH_UHRZEIT = "03:00"


def _silber_ladeform_absatz(ladeformen: dict[str, str] | None) -> str:
    """Der Absatz „inkrementell nur unter zwei Bedingungen“ — mit dem, was gewaehlt ist."""
    bedingung = ("**Inkrementell nur unter zwei Bedingungen.** Change Data Feed auf **allen** "
                 "Quellen (`delta.enableChangeDataFeed = true` — die MLV hier setzen es für "
                 "nachgelagerte Sichten) **und** die Quellen sind im Zyklus append-only. ")
    werte = sorted(set((ladeformen or {}).values())) or ["vollaufbau"]
    if werte == ["vollaufbau"]:
        return (bedingung + "Silber entsteht in dieser Lieferung per `CREATE OR REPLACE TABLE` "
                "(Vollaufbau, `DATA-SILVER-LOAD`) — damit ist jeder Zyklus ein Ersetzen, und "
                "Fabric wählt den **Vollaufbau**. Inkrementell wird es erst mit append-only "
                "geladenem Silber; das ist eine Ladeentscheidung, keine Einstellung.")
    if werte == ["append"]:
        return (bedingung + "Silber wird in dieser Lieferung append-only geschrieben "
                "(`DATA-SILVER-LOAD = append`), mit Change Data Feed ab der Anlage. Damit ist "
                "Bedingung (2) je Zyklus erfüllt, solange niemand Silber von Hand ändert — "
                "ein einziges `UPDATE` oder `DELETE` im Zyklus, und Fabric rechnet voll.")
    je = ", ".join(f"{dom}: `{w}`" for dom, w in sorted((ladeformen or {}).items()))
    return (bedingung + f"Silber wird je Domäne verschieden geschrieben ({je}). Eine Sicht "
            "läuft nur dann inkrementell, wenn **jede** ihrer Quellen append-only geladen wird; "
            "eine Quelle im Vollaufbau oder mit MERGE-Änderungen zieht sie in den Vollaufbau.")


def _mlv_refresh_doc(ladeformen: dict[str, str] | None = None) -> list[str]:
    """Wer den MLV-Refresh ausloest — belegt, nicht angenommen (D-529).

    Grundlage: MS Learn, abgerufen 23.09.2026 (*Manage and refresh materialized lake views with
    APIs*, *Optimal refresh*, *Refresh Materialized Lake View activity*, *notebook utilities*,
    *Create Refresh Materialized Lake Views Schedule*). Dazu ein Befund aus einem Test-Tenant mit
    synthetischen Daten, kundenneutral festgehalten.
    """
    return [
        "",
        "## Refresh — wer löst ihn aus (D-529)",
        "",
        "Fabric ordnet die Sichten selbst und wählt bei jedem Lauf die Strategie (überspringen, "
        "inkrementell, voll). **Einen Lauf startet Fabric nicht von selbst.** Ohne Auslöser "
        "bleibt eine MLV auf dem Stand ihres `CREATE` — und nichts wird rot.",
        "",
        "| Auslöser | Eignung | Grenze |",
        "|---|---|---|",
        "| **Zeitplan über die Job-Scheduler-API** (`refresh_schedule.json` → "
        "`POST …/lakehouses/{lakehouseId}/jobs/refreshMaterializedLakeViews/schedules`) | "
        "**Vorgabe dieser Lieferung** — unterstützt Service Principal und Managed Identity | "
        "API im **Preview**; höchstens 20 Zeitpläne je Lakehouse, **ein** aktiver je Lineage |",
        "| Zeitplan in der Lineage-Ansicht (Portal) | Produktionsweg laut MS Learn | Handarbeit, "
        "nicht im Deployment reproduzierbar |",
        "| Pipeline-Aktivität *Refresh Materialized Lake View* | Kopplung an das Laden ohne "
        "Zeitversatz | **Kein Service Principal, keine Workspace-Identität** — widerspricht der "
        "nicht-persönlichen Betriebsidentität; aktualisiert immer **alle** MLV des Lakehouse |",
        "| `REFRESH MATERIALIZED LAKE VIEW … FULL` (Spark SQL) | Einmalig, zur Fehlersuche | "
        "Erzwingt Vollaufbau |",
        "| `notebookutils.lakehouse.refreshMlv` | Entwicklung und Test | Laut MS Learn nicht "
        "für Produktion — und erst ab **Spark 4.0** vorhanden; auf 3.5 fehlt die Funktion |",
        "",
        f"**Zeitversatz statt Kopplung.** `refresh_schedule.json` läuft täglich "
        f"{MLV_REFRESH_UHRZEIT} UTC, eine Stunde nach der Pipeline (`orchestration/schedule.json`, "
        "02:00 UTC). Dauert die Pipeline länger, liest der Refresh den alten Stand. Die Kopplung "
        "über die Pipeline-Aktivität gäbe es, aber nur unter einer persönlichen Identität.",
        "",
        _silber_ladeform_absatz(ladeformen),
        "",
        "**Aus einem Kundenprojekt, gemessen (15.–22.09.2026, D-530).** Der Refresh scheiterte "
        "zuerst mit `MLV_SCHEMA_NOT_FOUND` — *the default database is not defined* — über die "
        "Job-Scheduler-API, die Ausführungsdefinition und `REFRESH … FULL`, obwohl dieselbe "
        "Session das Schema per `SHOW TABLES` sah. **Die Ursache war der fehlende Lakehouse-"
        "Kontext beim Refresh, nicht die Laufzeit:** mit dem Ziel-Lakehouse als gebundenem "
        "Kontext (Aufruf je Stufe auf *dem* Lakehouse, das die Sichten trägt) wurden alle "
        "Sichten auf Spark 3.5 angelegt, abgefragt und voll aktualisiert, in Entwicklung, Test "
        "und Produktion. Ein Zwischenschluss („geht erst mit Spark 4.0“) war falsch — gezogen "
        "aus der Voraussetzung eines einzigen Hilfsaufrufs (`refreshMlv`) und auf alle Wege "
        "verallgemeinert. **Für die Lieferung heißt das:** den Zeitplan auf dem Lakehouse "
        "anlegen, das die Sichten trägt, einmal auslösen und den Job-Status lesen, nicht die "
        "Rückgabe `202`. Spaltennamen mit Leerzeichen brauchen eine Delta-taugliche Projektion "
        "(`columnMapping` + maskierte Namen — hier emittiert).",
        "",
        "**Wem der Zeitplan gehört (D-537).** Eigentümer eines Zeitplans ist, wer ihn angelegt "
        "oder zuletzt geändert hat; ein Zeitplan eines Nutzers läuft ab, wenn dieser 90 Tage "
        "nicht angemeldet war (MS Learn, *Job scheduler*, *Create Item Schedule*, abgerufen "
        "23.09.2026). Die Job-Scheduler-API nimmt Dienstprinzipal und verwaltete Identität an. "
        "Deshalb: unter der Betriebsidentität anlegen (`day2/`), den Eigentümer "
        "zurücklesen (Apply-Schritt `verify_schedule_owner`) und nach jeder Änderung im Portal "
        "erneut — wer dort speichert, wird Eigentümer. Eine Workspace-Identität ersetzt den "
        "Eigentümer nicht. In einem Kundenprojekt gehörten nach der Inbetriebnahme alle "
        "Zeitpläne (Laden und Sichten, drei Stufen) einer Person: technisch vollständig, im "
        "Betrieb an einem Konto hängend.",
    ]


def _mlv_refresh_event(pipeline_name: str) -> str:
    """``mlv/refresh_event.json`` — der ereignisgesteuerte Ausloeser als Beschreibung (W2.3).

    **Keine API-Nutzlast.** MS Learn (*Schedule a materialized lake view refresh*, abgerufen
    29.09.2026) beschreibt den Weg nur im Portal (*Manage schedules → New schedule → Refresh
    type: Event-triggered*); eine REST-Form fuer diese Art Zeitplan war dort nicht zu finden.
    Die Datei haelt deshalb fest, was im Portal einzustellen ist, damit es geprueft werden kann.
    """
    import json as _json
    return _json.dumps({
        "_comment": ("Ereignisgesteuerter MLV-Refresh (Preview). Einrichtung im Portal, nicht per "
                     "API — siehe mlv/_MLV.md, Abschnitt 'Ereignisgesteuert'. "
                     "refresh_schedule.json bleibt der reproduzierbare Rueckfall."),
        "refreshType": "Event-triggered",
        "status": "Preview",
        "eventSourceType": "Job events",
        "eventSource": {"itemType": "DataPipeline", "itemName": pipeline_name},
        "eventType": "<im Portal waehlen: erfolgreicher Abschluss der Pipeline>",
        "scope": "Refresh all materialized lake views",
        "abhaengigkeiten": ["FMLV Refresh (Notebook, automatisch angelegt)",
                            "Activator (automatisch angelegt)"],
        "nicht_unterstuetzt": ["Private Link"],
    }, indent=2, ensure_ascii=False) + "\n"


def _mlv_ereignis_doc(ausloeser: str, pipeline_name: str) -> list[str]:
    """Abschnitt zum ereignisgesteuerten Refresh (D-529, Nachtrag W2.3)."""
    kopf = ["", "## Ereignisgesteuert (Preview, D-529 Nachtrag)", ""]
    fakten = [
        "MS Learn (*Schedule a materialized lake view refresh*, abgerufen 29.09.2026): neben "
        "*Time-based* gibt es **Event-triggered (Preview)** — Quelle *Job events* (Abschluss eines "
        "Notebooks oder einer Pipeline) oder *OneLake events* (Daten landen in OneLake). Er haengt "
        "an zwei **automatisch angelegten Items** (*FMLV Refresh*-Notebook und Activator); wer sie "
        "aendert oder loescht, legt den Ausloeser still. **Private Link ist nicht im "
        "Preview-Umfang.** Eine REST-Form fuer diese Art Zeitplan war dort nicht zu finden — "
        "die Einrichtung ist Handarbeit.",
        "",
        "**Was das an D-529 aendert:** der Kopplungsgrund gegen den Zeitversatz faellt weg (ein "
        "Pipeline-Abschluss loest aus, keine persoenliche Identitaet wie bei der "
        "Pipeline-Aktivitaet). **Was es nicht aendert:** nicht reproduzierbar im Deployment, "
        "Preview, und unter welcher Identitaet Activator und *FMLV Refresh* laufen, ist nicht "
        "belegt (UNKLAR, Tenant-gated) — die Eigentuemerfrage aus D-537 stellt sich neu.",
    ]
    if ausloeser != "ereignis":
        return kopf + fakten + ["", "In dieser Lieferung **nicht gewaehlt** "
                                "(`ausloeser=\"zeitplan\"`)."]
    return kopf + fakten + [
        "",
        f"**Gewaehlt** (`ausloeser=\"ereignis\"`). `refresh_event.json` beschreibt, was im Portal "
        f"einzustellen ist: *Job events*, Quelle die Pipeline `{pipeline_name}`, Ereignis "
        "erfolgreicher Abschluss. `refresh_schedule.json` bleibt als reproduzierbarer Rueckfall "
        "in der Lieferung. Ob ein ereignisgesteuerter Ausloeser zu den Zeitplaenen zaehlt, von "
        "denen je Lineage nur einer aktiv sein darf, ist nicht belegt — **vor dem Aktivieren des "
        "Ereignisses den Zeitplan pausieren** und nach dem ersten Pipeline-Lauf den MLV-Lauf in "
        "*Recent runs* lesen, nicht die Einstellung.",
    ]


def _mlv_hint_doc(refresh_hints: bool, hints: list[str]) -> list[str]:
    """Abschnitt Refresh-Hints (W5.8 → W2.3)."""
    kopf = ["", "## Refresh-Hints (Preview)", "",
            "MS Learn (*Enable optimal refresh for deletes and updates*, abgerufen 29.09.2026): "
            "`REFRESH_HINT <name> UNIQUE (<spalten>)` erklaert die Zeilenidentitaet einer Sicht; "
            "damit laufen **Updates und Deletes** in den Quellen inkrementell statt voll. "
            "Voraussetzung CDF auf allen Quellen, hoechstens ein Hint je Sicht. **Fabric prueft "
            "die Eindeutigkeit nicht** — ein falscher Hint erzeugt still falsche Daten."]
    if not refresh_hints:
        return kopf + ["", "In dieser Lieferung **aus** (`refresh_hints=False`)."]
    ziele = ", ".join(hints) or "— (kein Dimensionsschluessel im Katalog)"
    return kopf + [
        "",
        f"**An** fuer {len(hints)} Sicht(en): {ziele}. Nur Dimensionen mit Katalogschluessel; "
        "`dq/` prueft denselben Schluessel mit `unique` — das ist die Eindeutigkeitspruefung, "
        "die Fabric nicht macht.",
        "",
        "ANNAHME, ungeprueft: dass `REFRESH_HINT` und `CONSTRAINT … CHECK` in **einer** Klammer "
        "stehen duerfen. Learn zeigt beide Formen nur getrennt; beim ersten `CREATE` pruefen "
        "(Tenant-gated).",
    ]


def _mlv_laufzeit_doc(runtime: str) -> list[str]:
    """Abschnitt Laufzeit (W2.2): was fuer 1.3 und 2.0 belegt ist — und was nicht."""
    lz = MLV_LAUFZEITEN[runtime]
    zeilen = [f"| {k} | {v['spark']} / {v['delta']} | {v['stand']} | "
              + ("ja (Quickstart setzt 1.3 voraus)" if v["mlv_belegt"]
                 else "nein — UNKLAR, Tenant-gated") + " |"
              for k, v in MLV_LAUFZEITEN.items()]
    return [
        "", "## Laufzeit", "",
        f"Gewaehlt: **Fabric Runtime {runtime}** (Spark {lz['spark']}, Delta {lz['delta']}; "
        f"{lz['stand']}).",
        "",
        "| Runtime | Spark / Delta | Stand (Learn, 29.09.2026) | MLV auf Learn belegt |",
        "|---|---|---|---|",
        *zeilen,
        "",
        "**Kompatibilitaet, gemessen 29.09.2026.** Runtime 2.0 legt Delta-Tabellen mit Reader 3 / "
        "Writer 7 und **Deletion Vectors** an (Learn *Delta Lake table format interoperability*). "
        "Der Spark-freie Lader (`deltalake==0.18.2`, delta-rs) scheitert an solchen Tabellen: "
        "Lesen `DeltaProtocolError` (*reader features {'deletionVectors'} … not yet supported*), "
        "Ueberschreiben mit pyarrow-Engine `DeltaProtocolError`, mit Rust-Engine "
        "`CommitFailedError` — gemessen lokal an einem Delta-Log mit diesem Protokoll. Der Lader "
        "darf deshalb nur Tabellen schreiben, die er selbst anlegt (Protokoll 1/2), nie eine, die "
        "Spark 2.0 angelegt hat.",
        "",
        "`notebookutils.lakehouse.refreshMlv` gibt es erst ab Spark 4.0 (siehe oben); fuer den "
        "Betrieb gilt ohnehin der Zeitplan. Die DDL dieser Lieferung ist fuer beide Laufzeiten "
        "dieselbe.",
    ]
