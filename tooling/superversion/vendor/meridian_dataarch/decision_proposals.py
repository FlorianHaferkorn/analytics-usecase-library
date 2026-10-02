"""decision_proposals — for every open point, a pre-thought proposal instead of a bare TODO.

The Baukasten is honest about what it cannot derive (RLS predicates, sensitive columns, retention
periods, …). Naming a gap is necessary but not sufficient: the workshop should be a **confirm/adjust**
exercise, not a derive-from-scratch one. So for each open decision this module derives a *concrete
proposal* from what we DO know — the governed catalog's columns, the declared relationships, the domain
structure — plus the rationale, the alternatives and who decides.

Convention (Tool-Reuse): follows ``handover_recommend`` — a pure ``propose_*`` function returning a
recommendation record, plus a ``*_markdown`` renderer producing the auditable deliverable (the WHY, not
just the WHAT). Existing recommenders are **called**, not re-implemented: capacity sizing comes from
``capacity_recommend``, the tenant-setting list from ``admin_settings``.

Honesty rule (unchanged): a proposal is never presented as a fact. Every record carries a
``confidence`` and is rendered as "Vorschlag — zu bestätigen". Where the evidence is too thin to
propose anything, the record says so instead of inventing one.

Ohne governten Katalog schweigen fuenf Vorschlaege — das ist Absicht, kein Loch
------------------------------------------------------------------------------
Gemessen 08.08.2026, weil genau diese Beobachtung wie ein Defekt aussah und keiner ist:

===================  ==================  ==================
Punkt                ohne Katalog        mit Katalog
===================  ==================  ==================
SEC-RLS              kein Vorschlag      Vorschlag
SEC-CLS              kein Vorschlag      Vorschlag
DATA-INC             kein Vorschlag      Vorschlag
DATA-CONTRACT        kein Vorschlag      Vorschlag (vorbelegt)
AI-EVAL              kein Vorschlag      Vorschlag
-------------------  ------------------  ------------------
**Summe**            9 von 14            14 von 15
===================  ==================  ==================

Diese fuenf sind **modellgetrieben**: sie lesen Spalten, Beziehungen und Kennzahlen. Ein leerer
Katalog liefert nichts zu lesen, also gibt es nichts ehrlich vorzuschlagen — ein RLS-Praedikat
ohne Kenntnis der Organisationsstruktur waere geraten. Der Satz „kein Vorschlag" ist hier die
richtige Ausgabe und nicht die fehlende.

Woran es konkret haengt (jeweils die Bedingung, die den Vorschlag ausloest):

* ``SEC-RLS`` / ``SEC-CLS`` — Spaltennamen im Katalog (Org-Spalte bzw. personenbezogene Spalte)
* ``DATA-INC`` — eine Tabelle mit ``kind: "fact"`` **oder** ``measure_columns``. Ohne die
  Kennzeichnung greift ``_facts()`` nicht, und der Punkt schweigt trotz vorhandener
  Aenderungsspalte. Das hat beim Nachmessen zuerst wie ein Defekt ausgesehen.
* ``DATA-CONTRACT`` — ``relationships`` im Katalog (die Join-Schluessel sind der Vertrag)
* ``AI-EVAL`` — ``measures`` im Katalog (die Kennzahlen sind das Fragen-Geruest)

Praktische Folge fuer die Lieferung: ein Kunde **mit** governtem Modell bekommt zu jeder
Entscheidung einen Vorschlag, ein Kunde **ohne** bekommt fuenf ehrliche Luecken. Genau das
trennt die Intake-Frage ``has_governed_usecases`` (top-down vs. bottom-up), und deshalb ist sie
die erste im Fragebogen.

Deterministic; emits only, never executes.
"""
from __future__ import annotations

import json
import re
from typing import Any

# --- column-name evidence (lowercase substring → weight). Higher weight = stronger candidate. -------
# Org-scoping columns: the natural axis for row-level security in a corporate model.
_SCOPE_HINTS = {
    "company_code": 10, "bukrs": 10, "gesellschaft": 10, "legal_entity": 10,
    "business_unit": 9, "division": 9, "bereich": 9, "segment": 8,
    "region": 8, "country": 8, "land": 7, "zone": 7,
    "department": 7, "abteilung": 7, "cost_center": 7, "kostenstelle": 7,
    "plant": 6, "werk": 6, "site": 6, "standort": 6, "branch": 6,
    "org": 5, "mandant": 5, "tenant": 5, "project": 4, "projekt": 4,
}
# Columns that usually must not be shown to everyone.
_SENSITIVE_HINTS = {
    # personal data (DSGVO)
    "email": "personenbezogen", "e_mail": "personenbezogen", "mail": "personenbezogen",
    "phone": "personenbezogen", "telefon": "personenbezogen", "mobile": "personenbezogen",
    "address": "personenbezogen", "adresse": "personenbezogen", "street": "personenbezogen",
    "birth": "personenbezogen", "geburt": "personenbezogen", "iban": "personenbezogen",
    "ssn": "personenbezogen", "sozialversicherung": "personenbezogen",
    "employee_name": "personenbezogen", "mitarbeiter": "personenbezogen",
    "user_principal": "personenbezogen", "upn": "personenbezogen",
    "salary": "personenbezogen", "gehalt": "personenbezogen", "lohn": "personenbezogen",
    # commercially sensitive
    "margin": "wirtschaftlich sensibel", "marge": "wirtschaftlich sensibel",
    "cost_price": "wirtschaftlich sensibel", "ek_preis": "wirtschaftlich sensibel",
    "einkaufspreis": "wirtschaftlich sensibel", "deckungsbeitrag": "wirtschaftlich sensibel",
    "profit": "wirtschaftlich sensibel", "discount": "wirtschaftlich sensibel",
    "rabatt": "wirtschaftlich sensibel", "kondition": "wirtschaftlich sensibel",
}
# Change-tracking columns: the natural watermark for an incremental load.
_WATERMARK_HINTS = {
    "changed_on": 10, "last_modified": 10, "modified_at": 10, "updated_at": 10, "geaendert_am": 10,
    "aedat": 9, "laeda": 9, "erdat": 7,                     # SAP change/create dates
    "load_ts": 8, "loaded_at": 8, "ingested_at": 8, "_ts": 6,
    "modified": 6, "updated": 6, "changed": 6,
}


# Where a candidate column SITS decides how much its name is worth. A `country` on dim_supplier is a
# subject attribute (the supplier's home country), not an axis that governs who may see which rows —
# keying RLS on it sends the workshop down a wrong path. Placement therefore weights the name score.
_ORG_DIMS = ("division", "department", "company", "organisation", "organization", "org_",
             "region", "zone", "plant", "werk", "site", "standort", "branch", "cost_center",
             "kostenstelle", "legal_entity", "business_unit", "bereich", "gesellschaft")
_ENTITY_DIMS = ("supplier", "vendor", "lieferant", "customer", "kunde", "material", "product",
                "produkt", "artikel", "article", "item", "machine", "maschine", "asset",
                "equipment", "partner", "account", "contract", "vertrag")
_PLACEMENT_WEIGHT = {"fact": 1.0, "org_dim": 1.0, "other_dim": 0.7, "entity_dim": 0.25}

_NONWORD_RE = re.compile(r"[^a-z0-9]+")


def _cols(gc: dict, source_schema: dict | None = None) -> list[tuple[str, str]]:
    """All ``(table, column)`` pairs in the governed catalog **and** in the introspected source.

    Warum die zweite Quelle (gemessener Anlass 16.08.2026): ``--source-schema-results`` traegt
    das, was der Kunde uns auf unsere eigene Bitte hin zurueckgeschickt hat — die echten
    Spalten seiner Quellsysteme. ``watermark_candidates``/``key_candidates`` lesen sie seit
    jeher, aber sie endeten in ``provision_dq`` und ``provision_source_schema``. Die
    Entscheidungsvorlage kannte nur den governten Katalog und schrieb deshalb „kein
    Vorschlag", obwohl die Aenderungsspalte in der Antwort des Kunden stand.

    Die Herkunft bleibt am Namen ablesbar (``<quelle>.<tabelle>``), damit im Beleg steht, ob
    ein Kandidat aus dem Modell kommt oder aus der Quelle. Ein Kandidat aus der Quelle ist
    schwaecher: er sagt, was **da** ist, nicht was fachlich gilt.
    """
    aus_katalog = [(t["name"], c) for t in gc.get("tables", []) for c in (t.get("columns") or [])]
    return aus_katalog + _quell_cols(source_schema)


def _quell_cols(source_schema: dict | None) -> list[tuple[str, str]]:
    """``{quelle: [ODCS-Objekt]}`` → ``[(``<quelle>.<tabelle>``, Spalte)]``, deterministisch."""
    out: list[tuple[str, str]] = []
    for quelle, objs in sorted((source_schema or {}).items()):
        for obj in objs or []:
            tabelle = str(obj.get("name") or "")
            for prop in obj.get("properties") or []:
                name = str(prop.get("name") or "")
                if tabelle and name:
                    out.append((f"{quelle}.{tabelle}", name))
    return out


def _quell_schnitt(bp: dict, source_schema: dict | None, domain: dict) -> dict:
    """Die Quellen, die in diese Domaene laden. ``bp["ingestion"]`` fuehrt die Zuordnung."""
    if not source_schema:
        return {}
    name = domain.get("name")
    quellen = {str(e.get("source") or "") for e in bp.get("ingestion", []) or []
               if e.get("domain") == name}
    return {q: t for q, t in source_schema.items() if q in quellen}


def _placement(gc: dict, table: str) -> str:
    """Classify where a column sits: on a fact, on an org dimension, on an entity dimension, else other."""
    t = next((x for x in gc.get("tables", []) if x.get("name") == table), None)
    if t is None:
        return "other_dim"
    if t.get("kind") == "fact" or t.get("measure_columns"):
        return "fact"
    n = (table or "").lower()
    if any(h in n for h in _ORG_DIMS):
        return "org_dim"
    if any(h in n for h in _ENTITY_DIMS):
        return "entity_dim"
    return "other_dim"


def _domain_catalog(gc: dict, domain: dict) -> dict:
    """The slice of the governed catalog owned by one domain — a customer has many use cases, and
    RLS/CLS/incremental are decided per domain, not once for the whole tenant.

    Domains are not islands: a join that LEAVES the domain (its fact referencing a dimension another
    domain owns) is kept, because the consuming domain must know about it — dropping it would hide a
    real dependency from that domain's silver contract."""
    products = set(domain.get("data_products") or [])
    if not products:
        return gc
    tables = [t for t in gc.get("tables", []) if t.get("name") in products]
    names = {t["name"] for t in tables}
    return {
        "tables": tables,
        "measures": [m for m in gc.get("measures", [])
                     if any(str(l).split(".", 1)[0] in names for l in (m.get("lineage") or []))],
        # the owning (from) side decides: outgoing cross-domain joins stay visible to the consumer
        "relationships": [r for r in gc.get("relationships", []) if r.get("from_table") in names],
    }


# --- cross-domain: data is shared, consumed and authorised ACROSS domains ---------------------------

def _owner_index(bp: dict) -> dict[str, str]:
    """table → the domain that owns it (first domain listing it as a data product)."""
    owner: dict[str, str] = {}
    for d in sorted(bp.get("mesh", {}).get("domains", []), key=lambda x: x.get("name", "")):
        for p in d.get("data_products") or []:
            owner.setdefault(p, d.get("name", ""))
    return owner


def _cross_domain_facts(bp: dict, gc: dict) -> dict:
    """What actually crosses a domain boundary: shared objects, joins and measures."""
    owner = _owner_index(bp)
    xd_rels, consumers = [], {}
    for r in sorted((gc.get("relationships") or []),
                    key=lambda r: (str(r.get("from_table")), str(r.get("to_table")))):
        fo, to = owner.get(r.get("from_table")), owner.get(r.get("to_table"))
        if fo and to and fo != to:
            xd_rels.append(r)
            consumers.setdefault(r["to_table"], set()).add(fo)
    xd_measures = []
    for m in gc.get("measures", []):
        owners = {owner.get(str(l).split(".", 1)[0]) for l in (m.get("lineage") or [])}
        owners.discard(None)
        if len(owners) > 1:
            xd_measures.append((m.get("measure_name"), sorted(owners)))
    return {"owner": owner, "xd_rels": xd_rels,
            "shared": {t: sorted(v) for t, v in sorted(consumers.items())},
            "xd_measures": xd_measures}


def propose_cross_domain(bp: dict, gc: dict) -> list[dict]:
    """Decisions that only exist BETWEEN domains — ownership of shared objects, how consumers reach
    them, and the authorisation traps that appear when one user holds roles in several domains."""
    f = _cross_domain_facts(bp, gc)
    shared, xd_rels, xd_ms = f["shared"], f["xd_rels"], f["xd_measures"]
    if not shared and not xd_ms:
        return [_rec("XD-NONE", "Domänenübergreifende Nutzung",
                     "Werden Daten über Domänengrenzen geteilt?", None,
                     "keine domänenübergreifenden Beziehungen oder Kennzahlen im Katalog gefunden",
                     "keine", ["Sobald eine Domäne eine fremde Dimension mitnutzt, hier erneut prüfen"],
                     "Data Governance Board",
                     "Nichts — solange die Domänen tatsächlich unabhängig bleiben")]

    lines = "; ".join(f"`{t}` (Eigentümer **{f['owner'].get(t, '?')}**, genutzt von {', '.join(c)})"
                      for t, c in shared.items())
    out = [
        _rec("XD-OWNER", "Eigentum an geteilten Objekten",
             "Wem gehört eine Dimension, die mehrere Domänen nutzen?",
             (f"Genau **ein** besitzende Domäne je Objekt, alle anderen lesen nur — {lines}. "
              "Vorschlag: Der Eigentümer pflegt Schema und Schlüssel und ist der einzige Schreiber; "
              "Konsumenten bekommen **Read** (keine Kopie, kein Fork). Änderungen am Schlüssel oder am "
              "Grain sind Breaking Changes und laufen über den Vertrag, nicht über Zuruf. Genau **eine** "
              "Zertifizierung für das Objekt — nicht je Domäne eine eigene Variante."),
             f"{len(shared)} Objekt(e) domänenübergreifend genutzt",
             "hoch",
             ["Kopie je Domäne (schnell, führt aber zu divergierenden Stammdaten)",
              "Gemeinsame 'Shared'-Domäne, die alle konformierten Dimensionen besitzt"],
             "Data Governance Board (Eigentum) + die betroffenen Data Owner",
             "Zwei Domänen pflegen dieselbe Dimension unterschiedlich — Zahlen weichen ab, "
             "ohne dass jemand den Fehler findet", status="vorbelegt"),
        _rec("XD-ACCESS", "Zugriffsweg auf geteilte Objekte",
             "Wie erreicht eine Domäne die Daten einer anderen?",
             ("**Shortcut statt Kopie** (Zero-Copy): der Konsument verlinkt das Objekt aus dem "
              "Eigentümer-Workspace, statt es zu duplizieren — eine Wahrheit, kein Sync-Job, keine "
              "Drift. Berechtigung bleibt beim Eigentümer. Konkret betroffen: "
              + ", ".join(f"`{t}`" for t in shared) + ". "
              "Kopie nur, wenn der Konsument die Daten fachlich verändern muss — dann ist es aber ein "
              "**eigenes** Produkt mit eigenem Namen, keine zweite Version derselben Dimension."),
             f"{len(xd_rels)} domänenübergreifende Beziehung(en)",
             "hoch",
             ["Kopie per Pipeline (Drift-Risiko, doppelte Kosten)",
              "Zugriff über den SQL-Endpunkt statt Shortcut (nur SQL-Konsumenten)"],
             "Plattform-Verantwortliche:r + Eigentümer-Domäne",
             "Jede Domäne baut ihre eigene Kopie — Kosten und Abweichungen steigen still", status="vorbelegt"),
        _rec("XD-AUTH", "Berechtigung über Domänengrenzen",
             "Was sieht jemand, der in mehreren Domänen berechtigt ist?",
             ("**Zwei Fallen, beide bauartbedingt:** (1) OneLake-Rollen kombinieren per **Vereinigung** "
              "(least-restrictive). Wer in Vertrieb und Finanzen Rollen hat, sieht die *Summe* — eine "
              "Einschränkung in der einen Domäne wird durch die andere aufgehoben. (2) Liegt für "
              "dieselbe Tabelle **RLS in Rolle A und CLS in Rolle B**, schlägt die Abfrage fehl. "
              "Vorschlag: Für jedes geteilte Objekt genau **eine** Rolle definieren, die RLS und CLS "
              "gemeinsam trägt, und sie beim **Eigentümer** führen — nicht je Konsument nachbauen. "
              "Vor Rollout mit einer Testidentität prüfen, die absichtlich in mehreren Domänen liegt."),
             "OneLake-Rollenlogik (Vereinigung) + die Single-Role-Bedingung für RLS+CLS",
             "hoch",
             ["Getrennte Workspaces je Domäne ohne geteilte Objekte (einfachste, aber teuerste Trennung)",
              "Berechtigung nur im Semantic Model statt in OneLake (gilt dann nicht für andere Engines)"],
             "Security + Data Governance Board",
             "Nutzer sehen mehr als vorgesehen, oder Abfragen brechen unerklärlich ab", status="vorbelegt"),
    ]
    if xd_rels:
        out.append(_rec(
            "XD-JOIN", "Verträge an der Domänengrenze",
            "Wer garantiert die Schlüssel, über die Domänen verbunden sind?",
            ("Jede kreuzende Beziehung ist eine **Schnittstelle** und braucht einen Vertrag: "
             + "; ".join(f"`{r['from_table']}.{r['from_column']}` → `{r['to_table']}` "
                         f"({f['owner'].get(r['from_table'])} → {f['owner'].get(r['to_table'])})"
                         for r in xd_rels)
             + ". Vorschlag: Schlüsselstabilität und Grain im ODCS-Vertrag der **besitzenden** Domäne "
               "festschreiben, Konsumenten als Abonnenten eintragen und Schemaänderungen über das "
               "Contract-Gate laufen lassen — dann bricht ein Umbau in Domäne A den Report in "
               "Domäne B nicht unbemerkt."),
            f"{len(xd_rels)} Beziehung(en) kreuzen die Domänengrenze",
            "hoch",
            ["Informelle Absprache ohne Vertrag (bricht beim ersten Umbau)",
             "Konsument dupliziert die Dimension und entkoppelt sich bewusst"],
            "Data Owner beider Domänen",
            "Ein Schemawechsel in der besitzenden Domäne bricht still die Reports der anderen"))
    if xd_ms:
        out.append(_rec(
            "XD-MEASURE", "Domänenübergreifende Kennzahlen",
            "Wem gehört eine Kennzahl, die Fakten mehrerer Domänen verbindet?",
            ("Betroffen: " + "; ".join(f"**{n}** ({' + '.join(o)})" for n, o in xd_ms)
             + ". Vorschlag: Solche Kennzahlen gehören **nicht** in eines der beteiligten Fach-Modelle, "
               "sondern in ein übergreifendes Modell mit eigenem Eigentümer — sonst definieren zwei "
               "Domänen dieselbe Zahl unterschiedlich. Definition einmalig im KPI-Katalog festhalten, "
               "beide Quell-Domänen als Abhängigkeit eintragen."),
            f"{len(xd_ms)} Kennzahl(en) mit Lineage über mehrere Domänen",
            "hoch",
            ["Kennzahl in beiden Domänen doppelt pflegen (garantierte Abweichung)",
             "Kennzahl nur im Report berechnen (nicht governt, nicht wiederverwendbar)"],
            "Data Governance Board + beide Data Owner",
            "Dieselbe Kennzahl bekommt je Domäne einen anderen Wert"))
    return out


def _rank(col: str, hints: dict) -> int:
    c = col.lower()
    return max((w for h, w in hints.items() if h in c), default=0)


def _facts(gc: dict) -> list[dict]:
    return [t for t in gc.get("tables", []) if t.get("kind") == "fact" or t.get("measure_columns")]


def match_keys(table: dict) -> list[str]:
    """Der Match-Key eines MERGE: der **deklarierte** Schluessel des Katalogs, sonst die
    `_key`-Namensregel.

    Gemessen 02.09.2026 am Szenario `sap_mittelstand`: alle 22 Tabellen des SAP-Katalogs
    tragen `key` (BUKRS+BELNR+GJAHR, VBELN+POSNR, …), keine einzige Spalte endet auf `_key` —
    die Namensregel allein liess 17 MERGEs mit `<business_key>` stehen, obwohl die Antwort
    `watermark` im Profil lag und der Schluessel im Katalog. Der MLV-Emitter liest `key`
    bereits (`schluessel = table.get("key")`); dieselbe Quelle gehoert auch hierher (Tool-Reuse).
    """
    key = table.get("key") or []
    if isinstance(key, str):
        key = [key]
    keys = [str(k) for k in key]
    if keys:
        return keys
    return [c for c in (table.get("columns") or []) if str(c).lower().endswith("_key")]


def _domain_names(bp: dict) -> list[str]:
    return sorted(d.get("name", "") for d in bp.get("mesh", {}).get("domains", []))


#: Ermittlungswege je Entscheidung — nach ID, nicht am Aufrufort.
#:
#: Grund fuer die Tabelle statt eines Arguments an jeder Stelle: die fuenf modellgetriebenen
#: Entscheidungen haben **zwei** `_rec`-Aufrufe (mit governtem Katalog und ohne). Der Weg zur
#: Antwort ist in beiden Faellen derselbe; ihn zweimal zu tippen heisst, ihn beim naechsten Mal
#: an einer Stelle zu aendern. Genau die Sorte Drift, die dieses Repo an anderer Stelle schon
#: gekostet hat.
_ERMITTLUNGSWEGE: dict[str, dict[str, str]] = {
    "SEC-RLS": {
        "wo": "Die heutige Berichtslandschaft: gibt es bereits getrennte Berichte je Region, "
              "Gesellschaft oder Bereich, oder eine Zeilensicherheit im bestehenden Modell? "
              "Was heute getrennt ausgeliefert wird, IST der Schnitt — er steht nur nirgends "
              "geschrieben.",
        "wen": "Data Owner der Domäne gemeinsam mit der Person, die die Berichte heute "
               "verteilt. Die Verteilliste ist oft präziser als jedes Konzept.",
        "wenn_unklar": "Wir schlagen den Schnitt selbst vor, sobald das Gold-Modell steht — die "
                       "Organisationsachse kommt aus dem Modell (`--governed-catalog`). Bis "
                       "dahin gehört die Frage nicht auf den Kundenbogen, weil wir sie gerade "
                       "selbst beantworten.",
    },
    "SEC-CLS": {
        "wo": "Das Verzeichnis der Verarbeitungstätigkeiten nach Art. 30 DSGVO und ein "
              "bestehendes Berechtigungskonzept. Beide benennen personenbezogene Felder "
              "bereits, meist vollständiger als eine Frage im Termin.",
        "wen": "Datenschutzbeauftragte oder Datenschutzbeauftragter gemeinsam mit dem Data "
               "Owner. Ohne den Datenschutz ist die Antwort eine Meinung.",
        "wenn_unklar": "Wir schlagen die Kandidaten aus dem Gold-Modell vor (Namen, Adressen, "
                       "Personalnummern, Gehalt) und lassen bestätigen. Ein Vorschlag, dem "
                       "widersprochen wird, klärt die Frage schneller als eine offene Frage.",
    },
    "DATA-INC": {
        "wo": "Die Tabellenstruktur im Quellsystem, nicht das Gespräch: gibt es eine "
              "Aenderungsspalte (`LAST_UPDATE`, in SAP `AEDAT`/`AEZEIT`) oder ein Change-Log? "
              "Ein Blick ins Datenmodell beantwortet die Frage in Minuten.",
        "wen": "Die Administration des Quellsystems oder dessen Hersteller — nicht der "
               "Fachbereich, der die Spalte nie gesehen hat.",
        "wenn_unklar": "Voll laden und die Aenderungserkennung nachrüsten, sobald die Spalte "
                       "benannt ist. Folge: längere Ladezeiten und höherer Verbrauch, aber "
                       "kein falscher Datenstand. Der umgekehrte Fehler ist teurer.",
    },
    "DATA-SILVER-LOAD": {
        "wo": "Die Datenmengen je Quelltabelle und das Ladefenster: wie viele Zeilen kommen je "
              "Lauf hinzu, wie viele werden geändert oder gelöscht? Die Antwort steht in den "
              "Protokollen des bestehenden Ladeprozesses, nicht im Gespräch.",
        "wen": "Data Engineering Lead gemeinsam mit dem Betrieb der Quelle — wer weiß, ob "
               "Datensätze nachträglich korrigiert werden.",
        "wenn_unklar": "Vollaufbau beibehalten. Er ist korrekt und idempotent; jede Sicht "
                       "rechnet dann bei jedem Lauf voll. Umgestellt wird, sobald die "
                       "Laufzeit es verlangt — gemessen, nicht geschätzt.",
    },
    "DATA-CONTRACT": {
        "wo": "Bestehende Schnittstellenbeschreibungen und Uebergabevereinbarungen zwischen "
              "IT und Fachbereich. Wo es keine gibt, sagt das Fehlen selbst etwas über den "
              "Reifegrad und gehört ins Assessment.",
        "wen": "Data Owner und Data Engineering gemeinsam; einer allein beschreibt entweder "
               "die Bedeutung oder die Technik, nie beides.",
        "wenn_unklar": "Wir leiten den Vertrag aus dem Gold-Modell ab und legen ihn zur "
                       "Freigabe vor. Die Freigabe ist die Entscheidung, der Entwurf ist "
                       "unsere Arbeit.",
    },
    "AI-EVAL": {
        "wo": "Fragen, die der Fachbereich heute per Mail an die BI stellt. Zwanzig davon mit "
              "ihrer damaligen Antwort sind ein Prüfsatz — und zwar ein echter, weil ihn "
              "niemand für den Test erfunden hat.",
        "wen": "Der Fachbereich, der den Agenten später nutzt. Ein Prüfsatz aus der IT misst "
               "die IT.",
        "wenn_unklar": "Wir bilden den Prüfsatz aus dem Gold-Modell (je Kennzahl eine Frage) "
                       "und lassen die erwarteten Antworten bestätigen. Ohne jeden Prüfsatz "
                       "geht der Agent ohne Qualitätsnachweis produktiv — das ist kein "
                       "Rückfall, sondern ein Befund, und er steht so im Ledger.",
    },
    "NET-OUTBOUND": {
        "wo": "Die Liste der Quellsysteme mit ihren Endpunkten steht bereits im Blueprint. "
              "Dagegen die bestehenden Firewall-Freigaben des heutigen BI-Systems halten — "
              "was heute erreichbar ist, ist der belastbarste Ausgangspunkt.",
        "wen": "Informationssicherheit gemeinsam mit den Eignern der Quellsysteme. Die "
               "Plattformrolle kann die Freigabe weder erteilen noch verantworten.",
        "wenn_unklar": "Die Sperre erst **nach** der ersten erfolgreichen Beladung scharf "
                       "schalten und die dabei beobachteten Ziele als Ausnahmeliste "
                       "vorschlagen. Folge: ein zusätzlicher Schritt am Aufbautag statt einer "
                       "fehlgeschlagenen Beladung ohne Netzprotokoll.",
    },
    "OPS-USERDATA": {
        "wo": "Eine bestehende Betriebsvereinbarung zur Leistungs- und Verhaltenskontrolle. "
              "Wo Personalvertretung existiert, gibt es sie fast immer — und sie beantwortet "
              "die Frage härter, als der Betrieb es könnte.",
        "wen": "Datenschutz und Betriebsrat, nicht die Plattformrolle. Wer den Schalter "
               "bedient, entscheidet ihn nicht.",
        "wenn_unklar": "Den Personenbezug ausgeschaltet lassen und die Auswertung auf "
                       "Kapazität und Artefakt beschränken. Folge: Lastspitzen bleiben "
                       "sichtbar, ihre Verursacher nicht. Einschalten geht später, "
                       "rückwirkend löschen nicht.",
    },
}


#: Die Kundenfassung einer Entscheidung. ``warum`` steht bei **allen** siebzehn, und das ist
#: der Punkt: bis heute fuellte der Ledger ``hinweis`` und ``folge`` beide aus ``if_undecided``,
#: und der Renderer unterdrueckt ``hinweis`` bei Gleichheit. „Warum wir fragen" war damit fuer
#: Entscheidungen strukturell unmoeglich — der Deckel fiel auf „Wer entscheidet" zurueck.
#:
#: ``frage`` und ``folge`` stehen nur dort, wo der Fachsatz einen Kunden nicht erreicht. Sechs
#: von siebzehn: „Woran erkennt der MERGE geaenderte Zeilen?" ist eine Frage an einen
#: Dateningenieur, nicht an den Fachbereich, der die Antwort besitzt. Die uebrigen elf sind
#: schon in ihrer Fachfassung beantwortbar und bekommen keine zweite — zwei Wortlaute derselben
#: Frage laufen auseinander, sobald einer von beiden gepflegt wird.
#:
#: Wie ``_ERMITTLUNGSWEGE`` nach ``id`` geschluesselt, aus demselben Grund: die fuenf
#: modellgetriebenen Entscheidungen haben **zwei** ``_rec``-Aufrufstellen, je nachdem ob ein
#: governter Katalog vorlag. Am Aufrufort gepflegt waere die Haelfte davon still leer.
_KUNDENFASSUNG: dict[str, dict[str, str]] = {
    "SEC-RLS": {
        "warum": "Ohne einen erklärten Schnitt sieht jede Rolle alle Zeilen der freigegebenen "
                 "Tabellen. Das fällt erst auf, wenn die erste Entra-Gruppe gefüllt wird, und "
                 "dann sieht jemand Zahlen, die ihn nichts angehen.",
    },
    "SEC-CLS": {
        "warum": "Gehalt, Bankverbindung und Geburtsdatum liegen im Modell genauso da wie die "
                 "Umsatzspalte. Wer sie nicht benennt, gibt sie mit frei.",
    },
    "DATA-INC": {
        "frage": "Woran erkennen wir in Ihren Quelldaten, dass ein Datensatz sich geändert hat?",
        "folge": "Wir laden die Tabelle bei jedem Lauf komplett neu. Das ist korrekt und wird "
                 "mit wachsender Datenmenge langsam und teuer.",
        "warum": "Ein inkrementeller Lauf braucht ein Feld, an dem er Änderungen erkennt: ein "
                 "Änderungsdatum, eine Versionsnummer, ein Löschkennzeichen. Fehlt es, bleibt "
                 "nur der Komplettabzug.",
    },
    "DATA-SILVER-LOAD": {
        "frage": "Werden Ihre Daten bei jedem Lauf komplett neu aufgebaut, oder nur um das "
                 "ergänzt, was neu hinzugekommen ist?",
        "folge": "Wir bauen die bereinigte Stufe bei jedem Lauf komplett neu auf. Das ist "
                 "korrekt. Die Auswertungsstufe rechnet dann jedes Mal vollständig nach.",
        "warum": "Nur wenn die bereinigte Stufe ausschließlich ergänzt wird, kann die "
                 "Auswertungsstufe nur die Änderungen nachrechnen. Ein vollständiger Neuaufbau "
                 "ist aus Sicht der Plattform eine Änderung an allem.",
    },
    "DATA-CONTRACT": {
        "frage": "Nach welchen Schlüsseln lassen sich Ihre Quellsysteme zusammenführen?",
        "folge": "Jede Quelle bleibt für sich stehen. Auswertungen über Systemgrenzen hinweg "
                 "sind dann nicht möglich.",
        "warum": "Zwei Systeme führen denselben Kunden unter zwei Nummern. Welche davon gilt, "
                 "und woran die beiden Sätze als derselbe Kunde erkennbar sind, weiss nur "
                 "jemand aus dem Fachbereich.",
    },
    "AI-EVAL": {
        "warum": "Ein Assistent, dessen Antworten niemand gegen eine bekannte Wahrheit prüft, "
                 "wird trotzdem benutzt. Die falsche Antwort fällt dann im Termin auf, nicht "
                 "im Test.",
    },
    "GOV-DOMAIN": {
        "frage": "Welche Gruppe besitzt fachlich welche Domäne, und wer darf Arbeitsbereiche "
                 "darin anlegen?",
        "folge": "Wir legen die Domänen an und tragen die Rollen nach dem Namensschema ein. "
                 "Solange keine Gruppe benannt ist, hat die Domäne keinen Eigentümer und "
                 "Tenant-Einstellungen bleiben zentral.",
        "warum": "Die Domäne ist die einzige Stelle, an der eine Einstellung für einen "
                 "Fachbereich anders gelten kann als für den Rest des Hauses. Wer sie der IT "
                 "gibt, hat die Delegation gebaut und nicht genutzt.",
    },
    "SEC-SHARE": {
        "frage": "Wer darf Inhalte aus der Plattform nach außen geben — an Gäste, an Microsoft "
                 "365, über einen Link für alle, ins offene Netz?",
        "folge": "Wir schalten alle sechs Wege ab und öffnen einzeln, was Sie benennen. Ohne "
                 "Ihre Antwort bleibt es geschlossen — bis auf den einen, der ab Werk an ist "
                 "und den wir deshalb ausdrücklich ausschalten.",
        "warum": "Die Voreinstellungen von Fabric bevorzugen Bedienbarkeit vor Strenge. Der "
                 "Schalter für Microsoft 365 ist ab Werk an und schickt Berichts-, Seiten- und "
                 "Spaltennamen aus dem Haus, ohne dass jemand etwas tut.",
    },
    "SEC-ROLES": {
        "folge": "Wir binden die Rollen nach dem Vorschlag: Konsumenten lesend, Bearbeitende "
                 "mit Schreibrecht. Welche Gruppe dahintersteht, bleibt offen, bis Sie sie "
                 "nennen.",
        "warum": "Zeilensicherheit greift nur in der Viewer-Rolle. Wer einen Berichtsempfänger "
                 "als Member einträgt, damit er alles sieht, hat genau das erreicht: er sieht "
                 "alles, auch was gefiltert werden sollte.",
    },
    "GOV-RET": {
        "warum": "Aufbewahrungsfristen und Personenbezug entscheiden, was gelöscht werden muss "
                 "und was gelöscht werden darf. Beides ist eine Rechtsfrage, keine technische.",
    },
    "OPS-ALERT": {
        "folge": "Wir richten die Alarme auf Rollen-Postfächer ein. Welche Adressen dahinter "
                 "liegen, bleibt offen; bis dahin läuft die Meldung ins Leere.",
        "warum": "Eine Meldung ohne Empfänger ist eine Meldung, die niemand liest. Der "
                 "Ausfall fällt dann auf, wenn ein Bericht leer bleibt.",
    },
    "GOV-END": {
        "folge": "Wir zeichnen das Modell aus, das die governten Kennzahlen trägt. Alle "
                 "übrigen bleiben ohne Auszeichnung.",
        "warum": "Wenn zwei Modelle dieselbe Kennzahl tragen, entscheidet die Auszeichnung, "
                 "welche Zahl im Zweifel gilt. Ohne sie entscheidet der Zufall, welchen Bericht "
                 "jemand zuerst geöffnet hat.",
    },
    "PLAT-CAP": {
        "folge": "Wir planen mit der kleinsten Kapazität und messen im Betrieb nach. "
                 "Beschaffen müssen Sie sie selbst; ohne sie beginnt kein Aufbau.",
        "warum": "Die Kapazität setzt die Obergrenze für Datenmenge und gleichzeitige Nutzung. "
                 "Sie lässt sich später ändern, aber jeder Wechsel geht über die "
                 "Beschaffung.",
    },
    "PLAT-TENANT": {
        "folge": "Wir liefern die Prüfliste der nötigen Schalter mit. Setzen kann sie nur Ihre "
                 "Fabric-Administration.",
        "warum": "Mehrere dieser Schalter stehen mandantenweit und nicht im Projekt. Steht einer "
                 "falsch, scheitert der Aufbau an einer Stelle, die wie ein Fehler in unserer "
                 "Lieferung aussieht.",
    },
    "PLAT-NET": {
        "warum": "Die Netzanbindung ist die am schwersten zu drehende Festlegung der ganzen "
                 "Plattform. Sie wird früh getroffen und spät bemerkt.",
    },
    "NET-OUTBOUND": {
        "warum": "Wird der ausgehende Verkehr geblockt, ohne dass die nötigen Ziele benannt "
                 "sind, brechen Dienste ab, die vorher liefen. Die Freigabeliste ist billiger "
                 "vor dem Blocken als danach.",
    },
    "OPS-USERDATA": {
        "warum": "Die Auswertung kann zeigen, wer eine teure Abfrage ausgelöst hat. Ob sie das "
                 "darf, ist eine Frage an Ihre Mitbestimmung und Ihren Datenschutz.",
    },
    "PLAT-LHSCHEMA": {
        "frage": "Sollen die Tabellen in getrennten Bereichen je Verarbeitungsstufe liegen?",
        "folge": "Wir legen sie in getrennten Bereichen an. Das ist der ausdrückliche "
                 "Standardweg der Plattform.",
        "warum": "Getrennte Bereiche machen Rechte je Stufe vergebbar. Flach abgelegt tragen "
                 "die Tabellen ihre Stufe nur noch im Namen, und Rechte gelten dann für alle "
                 "zusammen.",
    },
    "PLAT-LHTOPO": {
        "frage": "Soll jede Verarbeitungsstufe ihren eigenen Speicherbereich bekommen, oder "
                 "tragen alle Stufen einer Fachdomäne einen gemeinsamen?",
        "folge": "Eine Domäne bekommt einen Speicherbereich, der alle Stufen als getrennte "
                 "Bereiche trägt.",
        "warum": "Der Schnitt entscheidet, wie fein sich Rechte und Betriebsaufgaben verteilen "
                 "lassen. Er lässt sich später ändern, aber jeder Umzug zieht Berichte und "
                 "Verbindungen mit.",
    },
    "PLAT-TRANSFORM": {
        "frage": "Sollen die Übergänge zwischen den Stufen automatisch nachgeführt werden, "
                 "oder als eigene Abläufe gesteuert?",
        "folge": "Wir deklarieren die Übergänge, die Plattform führt sie selbst nach.",
        "warum": "Deklarierte Übergänge sind weniger zu betreiben. Eigene Abläufe geben mehr "
                 "Kontrolle über Reihenfolge und Zeitpunkt, und sie brauchen jemanden, der sie "
                 "betreibt.",
    },
    # I-21 (FabCon Europe 2026, 30.09.2026): die fuenf Entscheidungen aus Kundeninput.
    "SEC-MIRROR": {
        "warum": "Eine gespiegelte Datenbank kommt ohne ihre Zeilen- und Spaltenrechte in der "
                 "Plattform an. Wer das nicht weiß, gibt geschützte Zeilen an jeden Leser frei.",
    },
    "OPS-MONITORING": {
        "frage": "Soll der Betrieb aller Arbeitsbereiche an einer Stelle überwacht werden, und "
                 "darf eine KI Auffälligkeiten dort selbst untersuchen?",
        "folge": "Wir legen keine Überwachung an, bis Sie antworten. Fehler fallen dann erst "
                 "auf, wenn ein Bericht leer bleibt.",
        "warum": "Zwei Einstellungen gibt es nur bei der Anlage, und eine KI-Funktion ist ab "
                 "Werk an. Was dort einmal steht, bleibt.",
    },
    "PLAT-OVERAGE": {
        "frage": "Soll die Plattform bei Lastspitzen Rechenleistung zukaufen, und bis zu welcher "
                 "Grenze?",
        "folge": "Die Kapazität kauft ab Werk zu, mit der Grenze von Microsoft. Die Kosten "
                 "dafür sehen Sie erst auf der Rechnung.",
        "warum": "Neue Kapazitäten kaufen ab Werk zu, zum dreifachen Preis. Ohne Entscheidung "
                 "zahlen Sie Lastspitzen, die niemand bestellt hat.",
    },
    "OUT-REPORT": {
        "frage": "Sollen Nutzer im Bericht nur lesen, oder auch Werte eingeben und "
                 "zurückschreiben?",
        "folge": "Wir bauen reine Berichte. Eingaben und Rückschreiben kommen später als eigene "
                 "Anwendung dazu.",
        "warum": "Eingaben brauchen eine andere Art von Anwendung als ein Bericht. Sie ist nicht "
                 "in jeder Region verfügbar und verlangt eine eigene Datenbank.",
    },
    "AI-DE-COPILOT": {
        "frage": "Darf ein KI-Assistent beim Bau der Datenstrecken mitarbeiten, und in welchen "
                 "Umgebungen?",
        "folge": "Der Assistent bleibt ausgeschaltet. Wir bauen die Datenstrecken wie bisher.",
        "warum": "Der Assistent schreibt Code, der wie jeder andere geprüft werden muss. Ob er "
                 "Daten außerhalb Ihrer Region verarbeiten darf, regelt Ihre KI-Richtlinie.",
    },
    "GOV-CATALOG": {
        "frage": "Gehört Microsoft Purview zum Projekt, und wenn ja, welche Teile davon?",
        "folge": "Wir verwalten Ihre Daten im Katalog von Fabric. Purview lässt sich später "
                 "anschließen, ohne dass wir etwas umbauen.",
        "warum": "Purview kostet eigene Lizenzen und braucht Rechte, die nur Ihre Verwaltung "
                 "vergeben kann. Der Katalog von Fabric ist ohne beides da.",
    },
}


#: Wann die Entscheidung weh tut. Ein **menschliches Urteil**, deshalb hier eingetragen und
#: nicht abgeleitet: `erscheint_in` bleibt bei Entscheidungen leer, weil der Artefaktbezug dort
#: nicht entsteht, und ohne ihn faellt der Ledger auf „nicht ableitbar" zurueck. Fuer „Welche
#: Spalten duerfen nicht alle sehen?" ist das nachweislich falsch — die Antwort muss vor dem
#: Produktivstart stehen, nicht irgendwann.
#:
#: Nur die acht ``offen``en stehen hier. Eine ``vorbelegt``e Entscheidung blockiert nichts: sie
#: ist bereits angewandt, der Kunde kann widersprechen, und tut er es nicht, gilt der Vorschlag.
#: Der Ledger vergibt ihr darum ohnehin keine Stufe.
#:
#: Die Werte stehen als Literale und nicht als Import aus ``open_points``: dieses Modul wird
#: byte-identisch nach ALUCA gespiegelt (SHARED_SUBSTANCE Klasse A), ``open_points`` nicht. Ein
#: Import waere dort ein Ladefehler. Gegen die Drift, die Literale sonst erzeugen, steht ein
#: Test — `test_die_faelligkeitsstufen_sind_die_des_ledgers`.
_FAELLIGKEIT: dict[str, str] = {
    "DATA-INC": "blockiert den Aufbau",
    # D-533: laut Ledger eines Kundenprojekts gehoert die Frage "vor den ersten produktiven
    # Gold-Lauf, nicht danach" -- der Wechsel des Schreibmusters fasst Bronze und Silber an.
    "DATA-SILVER-LOAD": "vor Produktivsetzung",
    "DATA-CONTRACT": "blockiert den Aufbau",
    "NET-OUTBOUND": "blockiert den Aufbau",
    "SEC-RLS": "vor Produktivsetzung",
    "SEC-CLS": "vor Produktivsetzung",
    "GOV-RET": "vor Produktivsetzung",
    "AI-EVAL": "vor Produktivsetzung",
    "OPS-USERDATA": "vor Produktivsetzung",
    # 20.08.2026, BK-Z06: die Freigabe-Politik ist keine Aufbau-Frage — die Plattform laeuft mit
    # jedem dieser Schalter. Sie ist eine Produktivsetzungs-Frage, und zwar mit Vorlauf: MS nennt
    # fuer #24 bis zu 24 Stunden bis zur Wirkung. Wer sie am Umsetzungstag umlegt, hat sie nicht
    # rechtzeitig umgelegt.
    "SEC-SHARE": "vor Produktivsetzung",
    # I-21 (30.09.2026): die Ueberwachung und das Report-Ziel bestimmen, was gebaut wird; zwei
    # Schalter der Ueberwachung gibt es nur bei der Anlage.
    "OPS-MONITORING": "blockiert den Aufbau",
    "OUT-REPORT": "blockiert den Aufbau",
    "SEC-MIRROR": "vor Produktivsetzung",
    "PLAT-OVERAGE": "vor Produktivsetzung",
    # Ohne Antwort bleibt der Assistent aus; das blockiert nichts, gehoert aber vor den
    # produktiven Betrieb, weil erst dort Code aus zwei Quellen zusammenkommt.
    "AI-DE-COPILOT": "vor Produktivsetzung",
    # D-620 (01.10.2026): Purview ist ein Andock-Modul. Ohne Antwort traegt der OneLake catalog;
    # Labels und DLP muessen vor dem ersten produktiven Modell stehen, sonst sind sie nachzuziehen.
    "GOV-CATALOG": "vor Produktivsetzung",
}


#: Die Optionen je Entscheidung — D-351 (02.09.2026, Flo: „Sämtliche Entscheidungen sollten in
#: einer Art und Weise dargestellt werden, so dass ein User geführt auch jede dieser treffen kann
#: und immer deren Implikationen, Limitierungen, Vor- und Nachteile kennt und einsehen kann“).
#:
#: Nach ``id`` geschluesselt wie ``_KUNDENFASSUNG``, aus demselben Grund: die modellgetriebenen
#: Entscheidungen haben zwei ``_rec``-Aufrufstellen, und am Aufrufort gepflegt waere die Haelfte
#: still leer. Der Vorschlag selbst bleibt in ``proposal`` und traegt die Belege dieses Kunden;
#: die Optionen hier sind die **Landkarte**, auf der der Vorschlag ein Punkt ist.
#:
#: Je Option: ``wert`` (stabiler Schluessel, wird zur Antwort), ``text`` (die Option in einem
#: Satz), ``vorteile`` / ``nachteile`` (je Liste), ``limitierungen`` (Liste aus
#: ``{text, quelle}`` — eine Grenze ohne Quelle ist eine Meinung), ``implikation`` (was danach
#: gilt, in einem Satz) und ``empfohlen`` (genau eine Option je Entscheidung mit Vorschlag;
#: keine bei denen, die bewusst keinen Vorschlag tragen — `NET-OUTBOUND`, `OPS-USERDATA`,
#: `DATA-CLUSTER`, `PLAT-TIER`, `XD-NONE`).
#:
#: Quellenvokabular: ``MS Learn: <pfad>`` fuer dokumentierte Plattformgrenzen, ``BK-xxx`` fuer den
#: Betriebskanon, ``eigene Messung <datum>`` fuer Gemessenes, ``eigene Einschaetzung`` fuer
#: Erfahrungswerte — die letzte Kategorie ist als solche erkennbar und nicht als Beleg getarnt.
_OPTIONEN: dict[str, list[dict[str, Any]]] = {
    "SEC-RLS": [
        {"wert": "dynamisch", "empfohlen": True,
         "text": "Dynamisches RLS über eine Zuordnungstabelle (Nutzer → Bereich)",
         "vorteile": ["Eine Rolle für alle Bereiche; neue Bereiche brauchen nur eine Zeile in der Zuordnung",
                      "Die Zuordnung ist Daten und kann vom Fachbereich gepflegt werden"],
         "nachteile": ["Die Zuordnungstabelle ist ein eigenes Pflegeobjekt mit eigenem Eigentümer",
                       "Fehler in der Zuordnung fallen erst beim betroffenen Nutzer auf"],
         "limitierungen": [{"text": "RLS wirkt nur für Viewer; Admin/Member/Contributor umgehen jeden Zeilenfilter",
                            "quelle": "MS Learn: fabric/security/service-admin-row-level-security"},
                           {"text": "Direct Lake fällt bei Objekt- oder Zeilensicherheit auf dem SQL-Endpunkt in DirectQuery zurück",
                            "quelle": "MS Learn: fabric/fundamentals/direct-lake-overview"}],
         "implikation": "Die Zuordnungstabelle wird Teil der Lieferung, mit Owner und Ladeweg."},
        {"wert": "statisch",
         "text": "Eine statische Rolle je Ausprägung des Bereichs",
         "vorteile": ["Ohne Zuordnungstabelle sofort einsatzfähig", "Leicht nachzuvollziehen: Rolle = Bereich"],
         "nachteile": ["Rollen-Wildwuchs ab wenigen Bereichen", "Jeder neue Bereich ist eine Modelländerung und ein Deployment"],
         "limitierungen": [{"text": "Rollen werden je Modell gepflegt; über mehrere Modelle hinweg laufen sie auseinander",
                            "quelle": "eigene Einschaetzung"}],
         "implikation": "Jede Bereichsänderung läuft über Entwicklung und Deployment statt über Daten."},
        {"wert": "kein_rls",
         "text": "Kein RLS; Trennung ausschließlich über getrennte Workspaces oder Modelle",
         "vorteile": ["Keine Filterlogik im Modell, keine Testidentitäten nötig"],
         "nachteile": ["Jede Trennung ist eine Kopie des Modells", "Übergreifende Auswertungen werden unmöglich oder doppelt"],
         "limitierungen": [{"text": "Workspace-Rollen kennen keine Zeilen; wer das Modell sieht, sieht alle Zeilen",
                            "quelle": "MS Learn: fabric/fundamentals/roles-workspaces"}],
         "implikation": "Die Zahl der Modelle wächst mit der Zahl der Bereiche."},
    ],
    "SEC-CLS": [
        {"wert": "ausblenden", "empfohlen": True,
         "text": "Sensible Spalten deklarieren und für nicht berechtigte Rollen ausblenden (CLS/OLS)",
         "vorteile": ["Eine Tabelle, eine Wahrheit; die Spalte bleibt für Berechtigte nutzbar",
                      "Die Deklaration ist versioniert und prüfbar"],
         "nachteile": ["Jede neue sensible Spalte muss deklariert werden, sonst ist sie sichtbar"],
         "limitierungen": [{"text": "OneLake-Sicherheit: RLS und CLS auf derselben Tabelle müssen in einer Rolle stehen, sonst schlägt die Abfrage fehl",
                            "quelle": "MS Learn: fabric/onelake/security/get-started-security"},
                           {"text": "Measures, die eine ausgeblendete Spalte lesen, liefern für die Rolle einen Fehler statt einen Wert",
                            "quelle": "MS Learn: power-bi/enterprise/service-admin-ols"}],
         "implikation": "Die Liste sensibler Spalten wird Teil des Datenvertrags und wird bei jeder Schemaänderung geprüft."},
        {"wert": "nicht_materialisieren",
         "text": "Sensible Spalten gar nicht ins Gold-Modell übernehmen",
         "vorteile": ["Stärkster Schutz: was nicht da ist, kann niemand sehen", "Kürzere Aufbewahrungsfrist entfällt für das Auswertungsmodell"],
         "nachteile": ["Auswertungen, die die Spalte fachlich brauchen, sind nicht möglich",
                       "Ein späterer Bedarf heißt Modelländerung und Neuladen"],
         "limitierungen": [{"text": "Gilt nur für Gold; in Bronze und Silber liegt die Spalte weiter, dort greift die Aufbewahrung",
                            "quelle": "BK-D05"}],
         "implikation": "Personenbezug endet an der Silber-Grenze; das Löschkonzept betrifft nur die unteren Schichten."},
        {"wert": "nur_label",
         "text": "Sichtbar lassen und nur über ein Sensitivity-Label kennzeichnen",
         "vorteile": ["Kein Eingriff ins Modell", "Das Label wandert mit Export und Download mit"],
         "nachteile": ["Schwächster Schutz: das Label kennzeichnet, es verbirgt nichts"],
         "limitierungen": [{"text": "Ein Label erzwingt keine Zugriffsbeschränkung im Modell; Schutz entsteht erst über Schutzrichtlinien in Purview",
                            "quelle": "MS Learn: fabric/governance/information-protection-overview"}],
         "implikation": "Die Verantwortung liegt beim Leser, nicht bei der Plattform."},
    ],
    "DATA-INC": [
        {"wert": "watermark", "empfohlen": True,
         "text": "Inkrementell über Match-Key und Änderungsspalte (MERGE mit Watermark)",
         "vorteile": ["Laufzeit und CU-Kosten wachsen mit den Änderungen, nicht mit dem Bestand",
                      "Standardmuster, das der Transform-Emitter bereits schreibt"],
         "nachteile": ["Löschungen in der Quelle kommen ohne Löschkennzeichen nicht an",
                       "Eine unzuverlässige Änderungsspalte erzeugt stille Lücken"],
         "limitierungen": [{"text": "Eine Materialized Lake View kennt kein DML; ein MERGE-Hop läuft als Pipeline oder Notebook",
                            "quelle": "MS Learn: fabric/data-engineering/materialized-lake-views/overview"}],
         "implikation": "Die Änderungsspalte wird Teil des Datenvertrags; ihre Verlässlichkeit ist eine Zusage der Quelle."},
        {"wert": "vollast",
         "text": "Vollast beibehalten: bei jedem Lauf den ganzen Bestand laden",
         "vorteile": ["Einfachste Variante, keine Schlüssel- oder Watermark-Frage", "Löschungen kommen automatisch an"],
         "nachteile": ["Kosten und Laufzeit wachsen mit dem Bestand", "Das Ladefenster wird irgendwann zu klein"],
         # D-622 (01.10.2026): quantifiziert mit Learn direct-lake-understand-storage (gelesen
         # 01.10.2026). Vorher nur „löst ein Neuladen aus (Framing)“.
         "limitierungen": [{"text": "Bei Direct Lake löscht ein Overwrite das Delta-Log: \"Direct Lake can't use incremental framing and must reload all the data, dictionaries, and join indexes\" — jede Vollast lädt das Modell ganz neu",
                            "quelle": "MS Learn: fabric/fundamentals/direct-lake-understand-storage"}],
         "implikation": "Tragfähig bis zur ersten Beladung, die das Fenster sprengt; dann wird diese Entscheidung neu getroffen."},
        {"wert": "cdc",
         "text": "Änderungserfassung an der Quelle (CDC oder Mirroring) statt Watermark im Transform",
         "vorteile": ["Löschungen und Zwischenstände kommen vollständig an", "Kein eigener Ladejob für Bronze"],
         "nachteile": ["Setzt voraus, dass die Quelle CDC bzw. Mirroring anbietet", "Bindet an den Konnektor des Herstellers"],
         "limitierungen": [{"text": "Fabric Mirroring gibt es nur für die dokumentierten Quellen (u. a. Azure SQL, Snowflake, Cosmos DB, SQL Server); SAP gehört nicht dazu",
                            "quelle": "MS Learn: fabric/database/mirrored-database/overview"}],
         "implikation": "Die Quellseite entscheidet mit; ohne CDC-Fähigkeit fällt die Option weg."},
        {"wert": "partition",
         "text": "Partition-Overwrite je Periode statt zeilenweisem MERGE",
         "vorteile": ["Kein Match-Key nötig", "Korrekturen einer Periode sind ein Neuschreiben der Partition"],
         "nachteile": ["Späte Änderungen in alten Perioden erzwingen deren Neuladen",
                       "Die Periode muss in der Quelle stabil bestimmbar sein"],
         "limitierungen": [{"text": "Partitionierte Tabellen sind von Liquid Clustering ausgeschlossen",
                            "quelle": "MS Learn: fabric/data-engineering/delta-optimization-and-v-order"},
                           {"text": "Bei Direct Lake ersetzt ein Partition-Overwrite die Parquet-Dateien der Periode; inkrementelles Framing bleibt nur für unberührte Partitionen (\"Avoid destructive update patterns on large Delta tables\")",
                            "quelle": "MS Learn: fabric/fundamentals/direct-lake-understand-storage"}],
         "implikation": "Das Partitionsschema wird Teil des Datenvertrags."},
        # D-622 (01.10.2026): append-freundliche Gold-Fakten bei Direct Lake. Nie Vorgabe —
        # korrekt nur bei append-only Quellen.
        {"wert": "append",
         "text": "Append-only für Fakten: je Lauf nur neue Zeilen per INSERT (Watermark), nie überschreiben",
         "vorteile": ["Bei Direct Lake bleibt das inkrementelle Framing erhalten: \"Append-only patterns don't affect existing Parquet files\"",
                      "Kein Match-Key nötig"],
         "nachteile": ["Korrekturen und Löschungen der Quelle kommen nie an",
                       "Nur für Fakten; Dimensionen bleiben MERGE oder Vollaufbau"],
         "limitierungen": [{"text": "Korrekt nur, wenn die Quelle append-only ist (Buchungen, Ereignisse); eine geänderte Zeile wird doppelt oder gar nicht geladen",
                            "quelle": "MS Learn: fabric/fundamentals/direct-lake-understand-storage"}],
         "implikation": "Die Emission schreibt je Fakt INSERT INTO … SELECT … WHERE <Watermark> > (SELECT MAX(…)); ohne Änderungsspalte im Katalog bleibt das Prädikat TODO(contract)."},
    ],
    "DATA-CONTRACT": [
        {"wert": "aus_beziehungen", "empfohlen": True,
         "text": "Vertrag aus den deklarierten Beziehungen vorbefüllen, nur die offenen Punkte im Workshop klären",
         "vorteile": ["Der Workshop bestätigt statt herzuleiten", "ODCS-Datei entsteht aus dem Katalog, nicht aus Prosa"],
         "nachteile": ["Beziehungen, die der Katalog nicht kennt, fehlen auch im Vertrag"],
         "limitierungen": [{"text": "Typisierung, Dedup-Regel, Null-Regeln und spät eintreffende Zeilen stehen in keiner ableitbaren Quelle",
                            "quelle": "eigene Messung 08.08.2026 (propose_silver_contract)"}],
         "implikation": "Die vier offenen Vertragspunkte werden Termin-T3-Fragen."},
        {"wert": "von_null",
         "text": "Vertrag komplett im Fachworkshop von Null erheben",
         "vorteile": ["Keine Vorannahme aus dem Katalog", "Der Fachbereich trägt den Vertrag vollständig"],
         "nachteile": ["Langsamer; ein Workshop für etwas, das zur Hälfte schon feststeht"],
         "limitierungen": [{"text": "Ohne Vertrag bleiben die Transform-Skelette bei SELECT * mit Platzhaltern", "quelle": "BK-D02"}],
         "implikation": "Der Umsetzungstag verschiebt sich hinter den Workshop."},
        {"wert": "ohne_vertrag",
         "text": "Ohne formalen Vertrag starten und im Betrieb nachziehen",
         "vorteile": ["Schnellster Start"],
         "nachteile": ["Stille Qualitätsfehler: niemand hat Schlüssel und Regeln zugesagt", "Nachziehen im Betrieb kostet Neuladen"],
         "limitierungen": [{"text": "Das Contract-Gate der Lieferung hat dann nichts zu prüfen", "quelle": "BK-D02"}],
         "implikation": "Die Qualitätsverantwortung liegt beim Leser der Auswertung."},
    ],
    "AI-EVAL": [
        {"wert": "aus_katalog", "empfohlen": True,
         "text": "Ground-Truth-Fragen aus den governten Kennzahlen ableiten und gegen das Modell prüfen",
         "vorteile": ["Jede Frage hat eine berechenbare richtige Antwort", "Die Prüfung läuft wiederholbar vor jedem Release"],
         "nachteile": ["Deckt nur ab, was der Katalog kennt"],
         "limitierungen": [{"text": "Ohne governten Katalog gibt es keine Kennzahlen, aus denen Fragen entstehen können",
                            "quelle": "eigene Messung 08.08.2026 (propose_ground_truth)"}],
         "implikation": "Der Katalog ist Voraussetzung; die Fragenliste wird mit ihm versioniert."},
        {"wert": "fachbereich",
         "text": "Fragen mit dem Fachbereich sammeln und die Antworten von Hand bestätigen",
         "vorteile": ["Fragen, die wirklich gestellt werden", "Kein Katalog nötig"],
         "nachteile": ["Die richtige Antwort ist ein Urteil, keine Berechnung", "Muss bei jeder Modelländerung neu bestätigt werden"],
         "limitierungen": [{"text": "Handbestätigte Antworten altern still mit dem Modell", "quelle": "eigene Einschaetzung"}],
         "implikation": "Ein Termin je Release für die Bestätigung."},
        {"wert": "ohne_nachweis",
         "text": "Ohne Qualitätsnachweis produktiv setzen",
         "vorteile": ["Kein Vorlauf"],
         "nachteile": ["Die falsche Antwort fällt im Termin auf, nicht im Test"],
         "limitierungen": [{"text": "Data-Agent-Antworten sind ohne Prüfung nicht reproduzierbar belegt", "quelle": "BK-A02"}],
         "implikation": "Der Assistent bleibt ein Vorschlag ohne Zusage."},
    ],
    "XD-NONE": [
        {"wert": "unabhaengig",
         "text": "Die Domänen bleiben unabhängig; keine geteilten Objekte",
         "vorteile": ["Keine Eigentumsfrage, keine Vereinigungsfalle bei Rollen"],
         "nachteile": ["Übergreifende Auswertungen sind nicht vorgesehen"],
         "limitierungen": [{"text": "Gilt nur, solange keine Domäne eine fremde Dimension nutzt", "quelle": "eigene Messung (Katalog ohne Domänenkreuzung)"}],
         "implikation": "Bei der ersten fremden Dimension werden XD-OWNER bis XD-JOIN fällig."},
        {"wert": "shared_domaene",
         "text": "Vorsorglich eine gemeinsame Domäne für konformierte Dimensionen anlegen",
         "vorteile": ["Ein Ort für Stammdaten, bevor Kopien entstehen"],
         "nachteile": ["Eine Domäne ohne Inhalt und ohne Eigentümer"],
         "limitierungen": [{"text": "Eine leere Domäne bekommt weder Endorsement noch Owner; der Katalog zeigt sie trotzdem", "quelle": "eigene Einschaetzung"}],
         "implikation": "Ein Eigentümer für die gemeinsame Domäne ist zu benennen, bevor sie Inhalt hat."},
    ],
    "XD-OWNER": [
        {"wert": "ein_eigentuemer", "empfohlen": True,
         "text": "Genau eine besitzende Domäne je Objekt, alle anderen lesen",
         "vorteile": ["Eine Wahrheit, eine Zertifizierung", "Schlüsseländerungen laufen über einen Vertrag"],
         "nachteile": ["Der Eigentümer trägt die Pflege für alle Konsumenten"],
         "limitierungen": [{"text": "Ein Objekt kann nur in einem Workspace liegen; Konsumenten erreichen es über Shortcut",
                            "quelle": "MS Learn: fabric/onelake/onelake-shortcuts"}],
         "implikation": "Der Eigentümer wird im ODCS-Vertrag des Objekts benannt."},
        {"wert": "kopie_je_domaene",
         "text": "Jede Domäne pflegt ihre eigene Kopie",
         "vorteile": ["Keine Abstimmung zwischen Domänen nötig"],
         "nachteile": ["Divergierende Stammdaten; Zahlen weichen ab, ohne dass jemand den Fehler findet"],
         "limitierungen": [{"text": "Zwei Kopien bekommen zwei Endorsements; welche gilt, sagt die Plattform nicht", "quelle": "MS Learn: fabric/governance/endorsement-overview"}],
         "implikation": "Ein Abgleichjob zwischen den Kopien wird nötig."},
        {"wert": "shared_domaene",
         "text": "Eine gemeinsame Domäne besitzt alle konformierten Dimensionen",
         "vorteile": ["Ein Ort für alle Stammdaten"],
         "nachteile": ["Eine Domäne ohne Fachbereich dahinter braucht einen künstlichen Eigentümer"],
         "limitierungen": [{"text": "Domänen-Rollen brauchen eine Entra-Gruppe; für eine Querschnittsdomäne gibt es sie selten", "quelle": "BK-W02"}],
         "implikation": "Eine Governance-Rolle für Stammdaten ist zu besetzen."},
    ],
    "XD-ACCESS": [
        {"wert": "shortcut", "empfohlen": True,
         "text": "Shortcut auf das Objekt im Eigentümer-Workspace (Zero-Copy)",
         "vorteile": ["Keine Kopie, kein Sync-Job, keine Drift", "Berechtigung bleibt beim Eigentümer"],
         "nachteile": ["Der Konsument kann das Objekt nicht verändern"],
         "limitierungen": [{"text": "Ein schema-aktiviertes Lakehouse lässt sich nicht per Workspace-Sharing teilen; Shortcuts sind der Weg",
                            "quelle": "MS Learn: fabric/data-engineering/lakehouse-schemas"}],
         "implikation": "Jeder Konsument wird als Shortcut-Ziel im Apply-Plan geführt."},
        {"wert": "kopie_pipeline",
         "text": "Kopie per Pipeline in den Konsumenten-Workspace",
         "vorteile": ["Der Konsument darf verändern"],
         "nachteile": ["Drift-Risiko, doppelte Speicherkosten, ein Sync-Job mehr"],
         "limitierungen": [{"text": "Eine Kopie ist ein eigenes Produkt und braucht einen eigenen Namen, sonst gibt es zwei Versionen derselben Dimension", "quelle": "eigene Einschaetzung"}],
         "implikation": "Die Kopie bekommt Eigentümer, Vertrag und Ladeplan."},
        {"wert": "sql_endpunkt",
         "text": "Zugriff über den SQL-Endpunkt statt Shortcut",
         "vorteile": ["Für reine SQL-Konsumenten ohne Lakehouse-Objekt"],
         "nachteile": ["Nur SQL-Konsumenten; Spark und Direct Lake bleiben außen vor"],
         "limitierungen": [{"text": "Der SQL-Endpunkt ist Lesezugriff auf Delta-Tabellen; er ersetzt kein Objekt im Konsumenten-Workspace",
                            "quelle": "MS Learn: fabric/data-engineering/lakehouse-sql-analytics-endpoint"}],
         "implikation": "Berechtigung läuft über SQL-Rollen, nicht über OneLake."},
    ],
    "XD-AUTH": [
        {"wert": "eine_rolle_beim_eigentuemer", "empfohlen": True,
         "text": "Eine Rolle je geteiltem Objekt, die RLS und CLS gemeinsam trägt, beim Eigentümer geführt",
         "vorteile": ["Die RLS/CLS-Falle ist ausgeschlossen", "Ein Ort für die Berechtigung"],
         "nachteile": ["Der Eigentümer verwaltet Berechtigungen fremder Konsumenten"],
         "limitierungen": [{"text": "OneLake-Rollen kombinieren per Vereinigung; wer in mehreren Domänen Rollen hat, sieht die Summe",
                            "quelle": "MS Learn: fabric/onelake/security/get-started-security"}],
         "implikation": "Vor Rollout wird mit einer Testidentität in mehreren Domänen geprüft."},
        {"wert": "getrennte_workspaces",
         "text": "Getrennte Workspaces je Domäne ohne geteilte Objekte",
         "vorteile": ["Einfachste Trennung"],
         "nachteile": ["Teuerste Trennung: keine geteilten Dimensionen, also Kopien"],
         "limitierungen": [{"text": "Widerspricht XD-ACCESS Shortcut; eine der beiden Entscheidungen fällt dann weg", "quelle": "eigene Einschaetzung"}],
         "implikation": "XD-OWNER wird zu Kopie je Domäne."},
        {"wert": "nur_semantic_model",
         "text": "Berechtigung nur im Semantic Model statt in OneLake",
         "vorteile": ["Bekanntes Power-BI-Muster, keine OneLake-Rollen"],
         "nachteile": ["Gilt nicht für Spark, SQL-Endpunkt oder Notebooks"],
         "limitierungen": [{"text": "Modell-RLS schützt nur Abfragen durch das Modell; der Lakehouse-Zugriff bleibt ungeschützt",
                            "quelle": "MS Learn: fabric/security/security-overview"}],
         "implikation": "Jede andere Engine braucht eine eigene Regelung."},
    ],
    "XD-JOIN": [
        {"wert": "odcs_vertrag", "empfohlen": True,
         "text": "Schlüsselstabilität und Grain im ODCS-Vertrag der besitzenden Domäne festschreiben",
         "vorteile": ["Ein Umbau in Domäne A bricht Domäne B nicht unbemerkt", "Konsumenten sind als Abonnenten sichtbar"],
         "nachteile": ["Jede Schemaänderung läuft über das Contract-Gate"],
         "limitierungen": [{"text": "ODCS beschreibt den Vertrag; die Durchsetzung ist das Gate der Lieferung, nicht die Plattform",
                            "quelle": "BK-D02"}],
         "implikation": "Die kreuzenden Beziehungen werden im Vertrag der besitzenden Domäne geführt."},
        {"wert": "informell",
         "text": "Informelle Absprache ohne Vertrag",
         "vorteile": ["Kein Prozess"],
         "nachteile": ["Bricht beim ersten Umbau"],
         "limitierungen": [{"text": "Das Contract-Gate hat dann nichts zu prüfen", "quelle": "BK-D02"}],
         "implikation": "Der Konsument erfährt von Änderungen durch den Fehler."},
        {"wert": "entkoppeln",
         "text": "Der Konsument dupliziert die Dimension und entkoppelt sich bewusst",
         "vorteile": ["Unabhängig vom Eigentümer"],
         "nachteile": ["Divergenz, doppelte Kosten"],
         "limitierungen": [{"text": "Widerspricht XD-OWNER ein Eigentümer", "quelle": "eigene Einschaetzung"}],
         "implikation": "XD-OWNER wird für dieses Objekt neu entschieden."},
    ],
    "XD-MEASURE": [
        {"wert": "uebergreifendes_modell", "empfohlen": True,
         "text": "Übergreifende Kennzahl in einem eigenen Modell mit eigenem Eigentümer",
         "vorteile": ["Eine Definition, beide Quell-Domänen als Abhängigkeit"],
         "nachteile": ["Ein weiteres Modell mit Betrieb und Eigentümer"],
         "limitierungen": [{"text": "Ein Direct-Lake-Modell liest aus einem Lakehouse; Tabellen mehrerer Lakehouses laufen über Shortcuts",
                            "quelle": "MS Learn: fabric/fundamentals/direct-lake-overview"}],
         "implikation": "Die Kennzahl steht einmal im KPI-Katalog, das Modell wird Konsument beider Domänen."},
        {"wert": "doppelt",
         "text": "Kennzahl in beiden Domänen pflegen",
         "vorteile": ["Keine Abstimmung"],
         "nachteile": ["Garantierte Abweichung"],
         "limitierungen": [{"text": "Der Golden Thread verlangt eine Definition je Kennzahl", "quelle": "Golden Thread des governten Kennzahlenkatalogs"}],
         "implikation": "Zwei Zahlen für dieselbe Frage."},
        {"wert": "nur_im_report",
         "text": "Kennzahl nur im Bericht berechnen",
         "vorteile": ["Schnell"],
         "nachteile": ["Nicht governt, nicht wiederverwendbar"],
         "limitierungen": [{"text": "Berichtsmaße sind für andere Berichte unsichtbar", "quelle": "MS Learn: power-bi/transform-model/desktop-measures"}],
         "implikation": "Die Kennzahl existiert nur dort, wo sie zuerst gebraucht wurde."},
    ],
    "SEC-ROLES": [
        {"wert": "least_privilege", "empfohlen": True,
         "text": "Least Privilege: Konsumenten Viewer, Entwickler Contributor, Admin minimal, immer Entra-Gruppen",
         "vorteile": ["RLS wirkt (nur für Viewer erzwungen)", "Überlebt Personalwechsel"],
         "nachteile": ["Gruppenpflege liegt beim Entra-Team"],
         "limitierungen": [{"text": "RLS wird nur für Viewer erzwungen; höhere Rollen halten implizit Write",
                            "quelle": "MS Learn: fabric/fundamentals/roles-workspaces"},
                           {"text": "Überlappende Gruppen: die höchste Rolle gewinnt", "quelle": "MS Learn: fabric/fundamentals/roles-workspaces"}],
         "implikation": "Je Domäne und Rolle eine Gruppe; die objectIds holt lookup/nachschlagen.sh."},
        {"wert": "personen",
         "text": "Rollen direkt an Personen vergeben",
         "vorteile": ["Schnell, kein Entra-Antrag"],
         "nachteile": ["Bricht bei jedem Wechsel", "Kein Überblick, wer was darf"],
         "limitierungen": [{"text": "Workspace-Rollen an Personen sind nicht über Zugriffsprüfungen (Access Reviews) steuerbar", "quelle": "eigene Einschaetzung"}],
         "implikation": "Jeder Personalwechsel ist ein Ticket an die Plattform."},
        {"wert": "alle_member",
         "text": "Alle Konsumenten als Member",
         "vorteile": ["Bequem, niemand fragt nach Rechten"],
         "nachteile": ["Hebelt RLS und CLS vollständig aus"],
         "limitierungen": [{"text": "Member halten Write und umgehen jeden Zeilenfilter", "quelle": "MS Learn: fabric/security/service-admin-row-level-security"}],
         "implikation": "SEC-RLS und SEC-CLS sind dann wirkungslos."},
        {"wert": "app_verteilung",
         "text": "Zugriff ausschließlich über App-Verteilung statt Workspace-Rollen",
         "vorteile": ["Konsumenten sehen nur die App, nicht den Workspace"],
         "nachteile": ["Nur für Berichtskonsumenten; kein Zugriff auf Lakehouse oder SQL"],
         "limitierungen": [{"text": "App-Zielgruppen berechtigen Berichte, keine Daten; für Spark oder SQL braucht es OneLake-Rollen",
                            "quelle": "MS Learn: power-bi/consumer/end-user-apps"}],
         "implikation": "Zwei Berechtigungswege: App für Berichte, OneLake für Daten."},
    ],
    "GOV-DOMAIN": [
        {"wert": "fachbereich", "empfohlen": True,
         "text": "Domain-Admin beim fachlichen Dateneigentümer, Contributor bei den Workspace-Anlegern, beides Entra-Gruppen",
         "vorteile": ["Delegation wird genutzt, nicht nur gebaut", "Die Domäne hat einen Verantwortlichen im Katalog"],
         "nachteile": ["Der Fachbereich übernimmt eine Plattformrolle"],
         "limitierungen": [{"text": "Domain-Admins setzt nur ein Fabric-Administrator; ein Domain-Admin vergibt Contributors, keine Admins",
                            "quelle": "MS Learn: fabric/governance/domains"},
                           {"text": "Der Contributor braucht zusätzlich die Workspace-Admin-Rolle, sonst läuft die Zuordnung ins Leere",
                            "quelle": "MS Learn: fabric/governance/domains"}],
         "implikation": "Je Domäne eine Admin- und eine Contributor-Gruppe, in kleinen Häusern dieselbe."},
        {"wert": "it",
         "text": "Domain-Admin an die IT geben",
         "vorteile": ["Schnell besetzt"],
         "nachteile": ["Macht die Delegation wirkungslos: Tenant-Einstellungen bleiben zentral"],
         "limitierungen": [{"text": "Domänen-Einstellungen überschreiben Tenant-Einstellungen nur, wenn jemand sie je Domäne setzt",
                            "quelle": "MS Learn: fabric/governance/domains-best-practices"}],
         "implikation": "Die Domäne ist eine Sortierhilfe."},
        {"wert": "keine_rollen",
         "text": "Keine Domain-Rollen setzen",
         "vorteile": ["Kein Antrag"],
         "nachteile": ["Niemand verantwortet die Auffindbarkeit im Katalog"],
         "limitierungen": [{"text": "Ohne Domain-Admin keine domänenspezifischen Einstellungen", "quelle": "MS Learn: fabric/governance/domains"}],
         "implikation": "Alles bleibt Tenant-weit."},
    ],
    "GOV-RET": [
        {"wert": "zwei_fristen", "empfohlen": True,
         "text": "Zwei Fristen: handels-/steuerrechtlich für Belegdaten, zweckgebunden kurz für Personenbezug",
         "vorteile": ["Rechtlich unterscheidbar begründet", "Löschung ist physisch (DELETE und VACUUM)"],
         "nachteile": ["Zwei Löschläufe, zwei Fristen zu pflegen"],
         "limitierungen": [{"text": "VACUUM entfernt Dateien erst nach der Aufbewahrungsschwelle der Tabelle; Time Travel verlängert die Sichtbarkeit",
                            "quelle": "MS Learn: fabric/data-engineering/lakehouse-table-maintenance"},
                           {"text": "Kein Rechtsrat; die Fristen bestätigt Legal", "quelle": "BK-D05"}],
         "implikation": "retention_policy.json trägt zwei Einträge; Legal bestätigt beide."},
        {"wert": "einheitlich",
         "text": "Eine einheitliche Frist für alles",
         "vorteile": ["Einfach"],
         "nachteile": ["Datenschutzrechtlich schwach: Personenbezug liegt so lange wie Belege"],
         "limitierungen": [{"text": "Zweckbindung verlangt eine Frist je Zweck, nicht je Tabelle", "quelle": "Retention-Konzept (Compliance), Art. 5 DSGVO"}],
         "implikation": "Der Datenschutzbeauftragte muss die lange Frist für Personenbezug begründen."},
        {"wert": "pseudonym",
         "text": "Pseudonymisierung im Silber statt kurzer Frist im Gold",
         "vorteile": ["Gold ohne Personenbezug; die kurze Frist entfällt dort"],
         "nachteile": ["Pseudonymisierung ist ein eigener Transformationsschritt mit Schlüsselverwaltung"],
         "limitierungen": [{"text": "Pseudonymisierte Daten bleiben personenbezogen, solange der Schlüssel existiert", "quelle": "Art. 4 Nr. 5 DSGVO"}],
         "implikation": "Der Schlüsseltresor wird Teil der Lieferung."},
        {"wert": "kundenkonzept",
         "text": "Fristen aus dem bestehenden Löschkonzept des Kunden übernehmen",
         "vorteile": ["Keine neue Rechtsprüfung"],
         "nachteile": ["Das Konzept kennt die Plattform nicht; Schichten und Kopien fehlen darin"],
         "limitierungen": [{"text": "Ein Löschkonzept je Quellsystem sagt nichts über Bronze-Kopien", "quelle": "BK-D05"}],
         "implikation": "Das Konzept wird um die Plattformschichten ergänzt."},
    ],
    "OPS-ALERT": [
        {"wert": "rollenpostfach", "empfohlen": True,
         "text": "Rollen-Postfächer je Plattform und Domäne, zweistufige Eskalation, E-Mail und Teams",
         "vorteile": ["Überlebt Personalwechsel", "Ein Ausfall hängt nicht an einem Kanal"],
         "nachteile": ["Postfächer müssen angelegt und besetzt werden"],
         "limitierungen": [{"text": "Capacity-Alarme gehen an die in der Kapazität hinterlegten Empfänger; Domänen-Verteiler brauchen eigene Regeln",
                            "quelle": "MS Learn: fabric/enterprise/capacity-notifications"}],
         "implikation": "Zwei Verteiler je Domäne plus ein Plattform-Postfach werden angelegt."},
        {"wert": "personen",
         "text": "Einzelpersonen direkt eintragen",
         "vorteile": ["Sofort einsatzfähig"],
         "nachteile": ["Bricht bei Urlaub und Wechsel"],
         "limitierungen": [{"text": "Fabric-Benachrichtigungen kennen keine Vertretungsregel", "quelle": "eigene Einschaetzung"}],
         "implikation": "Jeder Wechsel ist eine Konfigurationsänderung."},
        {"wert": "zentral",
         "text": "Ein zentraler Verteiler ohne Domänen-Split",
         "vorteile": ["Weniger Rauschen, eine Adresse"],
         "nachteile": ["Unschärfere Zuordnung; der Fachbereich erfährt nichts"],
         "limitierungen": [{"text": "Fachliche Datenqualitätsalarme erreichen den Data Owner nicht", "quelle": "BK-B07"}],
         "implikation": "Der Betrieb filtert und leitet weiter."},
    ],
    "GOV-END": [
        {"wert": "certified_spaeter", "empfohlen": True,
         "text": "Certified nur für die verbindliche Quelle, erst nach dem ersten sauberen Betriebszyklus; Rest Promoted",
         "vorteile": ["Certified heißt geprüft", "Nutzer erkennen die verbindliche Quelle"],
         "nachteile": ["Bis dahin trägt kein Modell das Siegel"],
         "limitierungen": [{"text": "Certified setzt eine admin-autorisierte Sicherheitsgruppe im Tenant-Setting voraus",
                            "quelle": "MS Learn: fabric/governance/endorsement-overview"}],
         "implikation": "Ein Termin nach dem ersten Betriebsmonat setzt das Siegel."},
        {"wert": "nur_promoted",
         "text": "Alles nur Promoted",
         "vorteile": ["Kein Zertifizierungsprozess"],
         "nachteile": ["Kein Modell ist erkennbar verbindlich"],
         "limitierungen": [{"text": "Promoted kann jeder Owner setzen; es sagt nichts über Prüfung", "quelle": "MS Learn: fabric/governance/endorsement-overview"}],
         "implikation": "Die verbindliche Quelle steht nur in der Doku."},
        {"wert": "certified_sofort",
         "text": "Certified sofort mit Go-Live",
         "vorteile": ["Schneller sichtbar"],
         "nachteile": ["Zertifiziert einen ungetesteten Stand"],
         "limitierungen": [{"text": "Certified ist ein Vertrauenssignal ohne technische Prüfung", "quelle": "MS Learn: fabric/governance/endorsement-overview"}],
         "implikation": "Ein Fehler im ersten Monat trägt das Siegel."},
    ],
    "PLAT-CAP": [
        {"wert": "f2_messen", "empfohlen": True,
         "text": "Mit F2 starten, Peak-CU messen und bei Bedarf hochziehen",
         "vorteile": ["Kein Vorab-Raten", "Skalieren im laufenden Betrieb"],
         "nachteile": ["Drosselung in der ersten Zeit möglich"],
         "limitierungen": [{"text": "Microsoft veröffentlicht keine Nutzer-zu-SKU-Formel", "quelle": "MS Learn: fabric/enterprise/plan-capacity"},
                           {"text": "Free-Consumer brauchen F64 oder höher", "quelle": "MS Learn: fabric/enterprise/licenses"}],
         "implikation": "Die Capacity-Metrics-App wird ab Tag 1 beobachtet; F64 ist eine Zielgruppenfrage vor dem Rollout."},
        {"wert": "f64",
         "text": "Direkt F64",
         "vorteile": ["Free-Consumer und Headroom sofort abgedeckt"],
         "nachteile": ["Teuerste Einstiegsstufe"],
         "limitierungen": [{"text": "Reservierung bindet ein Jahr; Pay-as-you-go ist stündlich kündbar", "quelle": "MS Learn: fabric/enterprise/buy-subscription"}],
         "implikation": "Billing-Commitment wird sofort fällig."},
        {"wert": "f2_minimum",
         "text": "F2 als Dauerlösung",
         "vorteile": ["Günstigste Stufe"],
         "nachteile": ["Bei mehr als sporadischer Nutzung zu knapp"],
         "limitierungen": [{"text": "Direct Lake fällt oberhalb der SKU-Grenzen für Zeilen und Modellgröße in DirectQuery zurück",
                            "quelle": "MS Learn: fabric/fundamentals/direct-lake-overview"}],
         "implikation": "Die Plattform drosselt, bevor jemand es plant."},
    ],
    "PLAT-TENANT": [
        {"wert": "vorab", "empfohlen": True,
         "text": "Alle benötigten Schalter vor dem Kickoff setzen und per Readiness-Check verifizieren",
         "vorteile": ["Am Umsetzungstag blockiert kein Schalter"],
         "nachteile": ["Ein Termin mit dem Fabric-Admin vor dem Start"],
         "limitierungen": [{"text": "Manche Tenant-Einstellungen wirken erst nach bis zu 24 Stunden", "quelle": "MS Learn: fabric/admin/about-tenant-settings"}],
         "implikation": "Die Prüfliste aus readiness/ wird Torbedingung vor P5."},
        {"wert": "bei_bedarf",
         "text": "Schalter erst bei Bedarf setzen",
         "vorteile": ["Kein Vorlauf"],
         "nachteile": ["Bremst mitten in der Umsetzung"],
         "limitierungen": [{"text": "24-Stunden-Wirkung macht aus jedem fehlenden Schalter einen verlorenen Tag", "quelle": "MS Learn: fabric/admin/about-tenant-settings"}],
         "implikation": "Der Umsetzungstag verlängert sich um jede Wartezeit."},
        {"wert": "delegiert",
         "text": "Delegation an Domänen-Admins statt zentraler Freigabe",
         "vorteile": ["Der Fachbereich entscheidet für seinen Bereich"],
         "nachteile": ["Nicht alle Einstellungen sind delegierbar"],
         "limitierungen": [{"text": "Nur die als delegierbar markierten Einstellungen lassen sich je Domäne setzen", "quelle": "MS Learn: fabric/governance/domains"}],
         "implikation": "Zentrale und delegierte Schalter werden getrennt geführt."},
    ],
    "PLAT-NET": [
        {"wert": "oeffentlich_twa", "empfohlen": True,
         "text": "Öffentliche Endpunkte plus Trusted Workspace Access für Azure-Quellen",
         "vorteile": ["Voller Funktionsumfang", "Speicher hinter Firewall bleibt aus benannten Workspaces lesbar"],
         "nachteile": ["Kein privater Netzpfad für Nutzer"],
         "limitierungen": [{"text": "Trusted Workspace Access setzt eine F-SKU voraus, kein Trial",
                            "quelle": "MS Learn: fabric/security/security-trusted-workspace-access"}],
         "implikation": "Die Gateway-Frage stellt sich erst beim ersten lokalen Quellsystem."},
        {"wert": "private_link_tenant",
         "text": "Private Link auf Tenant-Ebene",
         "vorteile": ["Maximale Abschottung"],
         "nachteile": ["Höchster Funktionsverlust; nachträglich nur mit Neuaufbau zu drehen"],
         "limitierungen": [{"text": "Kostet u. a. Publish-to-Web, Export, E-Mail-Abonnements, Copilot, Capacity-Metrics-App und tenantübergreifende Shortcuts",
                            "quelle": "MS Learn: fabric/security/security-private-links-overview"}],
         "implikation": "Die Liste der verlorenen Funktionen wird vor der Entscheidung mit dem Fachbereich abgeglichen."},
        {"wert": "private_link_workspace",
         "text": "Private Link nur auf Workspace-Ebene",
         "vorteile": ["Feiner: nur Workspaces mit echter Anforderung"],
         "nachteile": ["Zwei Netzpfade zu betreiben"],
         "limitierungen": [{"text": "Workspace-Level Private Link gilt nur für die dokumentierten Item-Typen",
                            "quelle": "MS Learn: fabric/security/security-workspace-level-private-links-overview"}],
         "implikation": "Je Workspace wird der Netzpfad im Apply-Plan geführt."},
        {"wert": "ip_firewall",
         "text": "IP-Firewall-Regeln je Workspace",
         "vorteile": ["Läuft auch auf Trial; bis 256 Regeln"],
         "nachteile": ["Schützt nur den eingehenden Pfad"],
         "limitierungen": [{"text": "Bis zu 256 Regeln je Workspace", "quelle": "MS Learn: fabric/security/workspace-ip-firewall"}],
         "implikation": "Die Regelliste wird Teil des Apply-Plans."},
    ],
    "NET-OUTBOUND": [
        {"wert": "nur_quellen",
         "text": "Nur die erklärten Quellsysteme freigeben",
         "vorteile": ["Engste Liste, kleinste Angriffsfläche"],
         "nachteile": ["Jede neue Quelle braucht einen Antrag"],
         "limitierungen": [{"text": "Outbound Access Protection blockiert auch Paketquellen; Spark-Umgebungen mit eigenen Bibliotheken scheitern",
                            "quelle": "MS Learn: fabric/security/security-outbound-access-protection-overview"}],
         "implikation": "Der Antragsweg für neue Ziele wird Teil des Betriebshandbuchs."},
        {"wert": "plus_paketquellen",
         "text": "Zusätzlich die Paketquellen der Entwicklung freigeben (PyPI, Maven, npm)",
         "vorteile": ["Spark-Umgebungen bleiben baubar"],
         "nachteile": ["Drei öffentliche Ziele mehr"],
         "limitierungen": [{"text": "Freigaben gelten je Workspace, nicht je Nutzer", "quelle": "MS Learn: fabric/security/security-outbound-access-protection-overview"}],
         "implikation": "Die Entwicklungs-Workspaces bekommen eine andere Liste als Produktion."},
        {"wert": "beobachten",
         "text": "Sperre zunächst im Berichtsmodus, Liste aus dem gemessenen Verkehr bilden",
         "vorteile": ["Keine Überraschung beim ersten Ladelauf"],
         "nachteile": ["Bis zur Scharfschaltung ist nichts geschützt"],
         "limitierungen": [{"text": "Ein reiner Beobachtungsmodus ist nicht dokumentiert; gemessen wird über Verbindungsfehler nach dem Einschalten",
                            "quelle": "eigene Einschaetzung"}],
         "implikation": "Ein Datum für die Scharfschaltung wird festgelegt."},
    ],
    "SEC-SHARE": [
        {"wert": "geschlossen", "empfohlen": True,
         "text": "Alle sechs Wege nach außen geschlossen, Öffnung als benannte Ausnahme",
         "vorteile": ["Nichts verlässt die Plattform, was niemand gewählt hat"],
         "nachteile": ["Jede Freigabe nach außen ist ein Antrag"],
         "limitierungen": [{"text": "Ein Wechsel wirkt erst nach bis zu 24 Stunden", "quelle": "MS Learn: fabric/admin/service-admin-portal-export-sharing"}],
         "implikation": "Die Freigabe an Microsoft 365 ist ab Werk an und wird aktiv ausgeschaltet."},
        {"wert": "gast_offen",
         "text": "Gastzugriff öffnen, Rest geschlossen",
         "vorteile": ["Üblich bei Projekten mit Dienstleistern"],
         "nachteile": ["Gäste im Tenant"],
         "limitierungen": [{"text": "Gastzugriff verlangt drei Schalter und eine Sicherheitsgruppe", "quelle": "MS Learn: fabric/admin/service-admin-portal-export-sharing"}],
         "implikation": "Eine Gast-Sicherheitsgruppe mit Eigentümer wird benannt."},
        {"wert": "m365_an",
         "text": "Freigabe an Microsoft 365 anlassen",
         "vorteile": ["Berichte werden über die Microsoft-365-Suche gefunden"],
         "nachteile": ["Berichts-, Seiten-, Spalten- und Measure-Namen liegen dann dort"],
         "limitierungen": [{"text": "Metadaten werden ohne Zutun gemeldet; der Unterschalter für regionsübergreifende Freigabe verlässt die Region",
                            "quelle": "MS Learn: fabric/admin/service-admin-portal-export-sharing"}],
         "implikation": "Datenschutz bewertet die Metadaten als Datenabfluss."},
        {"wert": "werkswert",
         "text": "Alles auf Auslieferungswert lassen",
         "vorteile": ["Kein Eingriff"],
         "nachteile": ["Die Freigabe an Microsoft 365 ist dann an, ohne dass jemand sie gewählt hat"],
         "limitierungen": [{"text": "Auslieferungswerte sind auf Auffindbarkeit optimiert, nicht auf Zurückhaltung", "quelle": "BK-Z06"}],
         "implikation": "Die Entscheidung ist gefallen, nur nicht getroffen."},
    ],
    "OPS-USERDATA": [
        {"wert": "an",
         "text": "Anlassen: die Auswertung nennt Personen",
         "vorteile": ["Verursacher teurer Abfragen sofort sichtbar"],
         "nachteile": ["Mitbestimmungspflichtig; Personenbezug in einer Betriebsauswertung"],
         "limitierungen": [{"text": "Leistungs- und Verhaltenskontrolle ist mitbestimmungspflichtig", "quelle": "§ 87 Abs. 1 Nr. 6 BetrVG"}],
         "implikation": "Betriebsrat und Datenschutz vor dem Einschalten der App."},
        {"wert": "aus",
         "text": "Ausschalten: die Auswertung nennt nur Elemente und Kapazitäten",
         "vorteile": ["Teure Abfragen bleiben sichtbar, ihr Urheber nicht"],
         "nachteile": ["Die Rückfrage an den Verursacher läuft über den Item-Owner"],
         "limitierungen": [{"text": "Der Schalter „Show user data in Capacity Metrics“ wirkt tenantweit", "quelle": "BK-B02"}],
         "implikation": "Betriebliche Nachfragen laufen über Item-Owner statt über Personen."},
        {"wert": "an_begrenzt",
         "text": "Anlassen und den Zugang zur App auf einen benannten Kreis begrenzen",
         "vorteile": ["Personenbezug nur für den Betrieb sichtbar"],
         "nachteile": ["Bleibt mitbestimmungspflichtig"],
         "limitierungen": [{"text": "Die App ist ein Workspace-Item; der Kreis ist eine Workspace-Rolle", "quelle": "MS Learn: fabric/enterprise/metrics-app"}],
         "implikation": "Eine Betriebsvereinbarung für den benannten Kreis."},
    ],
    "PLAT-LHSCHEMA": [
        {"wert": "schemas", "empfohlen": True,
         "text": "Schema-aktiviertes Lakehouse (bronze/silver/gold als Schemas)",
         "vorteile": ["Die Schicht steht im Namensraum, Berechtigung je Schema", "dbo lässt sich per Schema-Shortcut nachbilden, umgekehrt nicht"],
         "nachteile": ["Zwei dokumentierte Grenzen beim Teilen"],
         "limitierungen": [{"text": "Kein Werkzeug, ein Lakehouse ohne Schemas nachträglich umzustellen", "quelle": "MS Learn: fabric/data-engineering/lakehouse-schemas"},
                           {"text": "Nicht per Workspace-Sharing teilbar; externe ADLS-Tabellen nur über Shortcuts", "quelle": "MS Learn: fabric/data-engineering/lakehouse-schemas"}],
         "implikation": "Wird bei der Anlage entschieden; Materialized Lake Views setzen es voraus."},
        {"wert": "flach",
         "text": "Flach unter dbo (gold_fact_x)",
         "vorteile": ["Per Workspace-Sharing direkt teilbar"],
         "nachteile": ["Die Schicht steckt im Präfix", "MLV nicht möglich"],
         "limitierungen": [{"text": "Materialized Lake Views verlangen ein schema-aktiviertes Lakehouse",
                            "quelle": "MS Learn: fabric/data-engineering/materialized-lake-views/overview"}],
         "implikation": "PLAT-TRANSFORM wird zu Pipelines."},
    ],
    "PLAT-LHTOPO": [
        {"wert": "je_domaene", "empfohlen": True,
         "text": "Ein Lakehouse je Domäne, Schichten als Schemas",
         "vorteile": ["Eigentum, Endorsement und Berechtigung hängen an der Domäne", "Das MLV-Tutorial von Microsoft zeigt diese Form"],
         "nachteile": ["Weicht von der MS-Empfehlung zur Schichttrennung ab"],
         "limitierungen": [{"text": "MS Learn empfiehlt eine Schicht je Lakehouse und je Workspace",
                            "quelle": "MS Learn: fabric/onelake/onelake-medallion-lakehouse-architecture"}],
         "implikation": "Bronze und Gold teilen sich Kapazitäts- und Kostenzuordnung der Domäne."},
        {"wert": "je_schicht",
         "text": "Ein Lakehouse je Schicht im selben Workspace",
         "vorteile": ["Layer-Trennung ohne Workspace-Zersplitterung"],
         "nachteile": ["Domänenschnitt wird im Workspace unsichtbar"],
         "limitierungen": [{"text": "Berechtigung je Lakehouse, nicht je Domäne", "quelle": "MS Learn: fabric/onelake/security/get-started-security"}],
         "implikation": "Domänentrennung muss über OneLake-Rollen nachgebildet werden."},
        {"wert": "workspace_je_schicht",
         "text": "Ein Workspace je Schicht (MS-Empfehlung)",
         "vorteile": ["Stärkste Trennung; Rohdaten-Zugriff eigenständig verantwortet"],
         "nachteile": ["Jede Domäne verteilt sich über drei Workspaces; Eigentum zersplittert"],
         "limitierungen": [{"text": "Domänen-Zuordnung geschieht je Workspace; drei Workspaces je Domäne", "quelle": "MS Learn: fabric/governance/domains"}],
         "implikation": "Dreimal so viele Workspaces, Rollen und Deployments."},
        {"wert": "gold_warehouse",
         "text": "Bronze und Silber als Lakehouse, Gold als Warehouse",
         "vorteile": ["T-SQL-Serving mit vollem DML"],
         "nachteile": ["Zwei Item-Typen, zwei Werkzeugketten"],
         "limitierungen": [{"text": "Warehouse kennt keine Materialized Lake Views; Direct Lake auf Warehouse hat eigene Grenzen",
                            "quelle": "MS Learn: fabric/data-warehouse/data-warehousing"}],
         "implikation": "PLAT-TRANSFORM wird zu T-SQL-Pipelines für Gold."},
    ],
    "DATA-TEXTSPRACHE": [
        {"wert": "E", "empfohlen": True,
         "text": "Englisch zuerst (SAP-Kennzeichen E), sonst die nächste vorhandene Sprache",
         "vorteile": ["SAP liefert Standardtexte mindestens englisch",
                      "Kein Stammsatz verliert seinen Text, solange irgendeine Sprache gepflegt ist"],
         "nachteile": ["Deutschsprachige Fachbereiche sehen englische Bezeichnungen, wo beide gepflegt sind"],
         "limitierungen": [{"text": "Texttabellen wie MAKT und SKAT führen je Sprache eine Zeile; ohne Rangfolge vervielfacht der Verbund jede Kopfzeile",
                            "quelle": "SAP DDIC (se80.co.uk): Schlüssel MAKT = MANDT, MATNR, SPRAS; SKAT = SPRAS, KTOPL, SAKNR"}],
         "implikation": "Gold trägt einen Text je Schlüssel; die Spalte SPRAS zeigt, aus welcher Sprache er stammt."},
        {"wert": "D",
         "text": "Deutsch zuerst (SAP-Kennzeichen D), sonst die nächste vorhandene Sprache",
         "vorteile": ["Bezeichnungen in der Sprache, in der die meisten Stammdaten im Mittelstand gepflegt werden"],
         "nachteile": ["Wo nur englische Standardtexte existieren, erscheinen sie trotzdem — die Sprache mischt sich"],
         "limitierungen": [{"text": "Die Rangfolge wählt je Schlüssel; eine einheitliche Sprache ist nur so gut wie die Pflege der Texte",
                            "quelle": "SAP DDIC (se80.co.uk): MAKT/SKAT als Texttabellen mit Sprachschlüssel"}],
         "implikation": "Gleicher Verbund, andere Rangfolge; ändert keine Tabelle und keinen Schlüssel."},
        {"wert": "je_sprache",
         "text": "Alle Sprachen in Gold, Sprache als Teil des Schlüssels",
         "vorteile": ["Mehrsprachige Berichte über Übersetzungen des Semantikmodells"],
         "nachteile": ["Ändert das deklarierte Grain; jede Beziehung auf die Dimension braucht die Sprache mit"],
         "limitierungen": [{"text": "Das Paket deklariert das Grain je Stammsatz, nicht je Sprache",
                            "quelle": "SAP-Standardpaket: grain \"one row per material (client level)\""}],
         "implikation": "Die Emission baut das heute nicht; eine solche Antwort ändert das Modell, nicht nur die Rangfolge."},
    ],
    "DATA-SILVER-LOAD": [
        {"wert": "vollaufbau", "empfohlen": True,
         "text": "Vollaufbau: Silber je Lauf vollständig per CREATE OR REPLACE",
         "vorteile": ["Idempotent: ein wiederholter Lauf ergibt dasselbe Ergebnis",
                      "Korrekturen und Löschungen in der Quelle kommen ohne Zusatzlogik an",
                      "Das, was die Lieferung heute emittiert"],
         "nachteile": ["Jede nachgelagerte MLV rechnet bei jedem Lauf voll",
                       "Laufzeit und CU-Verbrauch wachsen mit dem Bestand"],
         "limitierungen": [{"text": "Ein Überschreiben der Quelle gilt für die Aktualisierung der Sichten als Änderung an allen Zeilen. Inkrementell wird nie gewählt",
                            "quelle": "MS Learn: fabric/data-engineering/materialized-lake-views/refresh-materialized-lake-view"}],
         "implikation": "Change Data Feed auf Silber bringt nichts; die MLV-Aktualisierung ist immer voll."},
        {"wert": "append",
         "text": "Append-only: je Lauf nur hinzugekommene Zeilen anfügen, Change Data Feed an",
         "vorteile": ["Nachgelagerte MLV können inkrementell aktualisiert werden",
                      "Kosten wachsen mit den neuen Zeilen, nicht mit dem Bestand"],
         "nachteile": ["Korrekturen und Löschungen der Quelle kommen nicht an",
                       "Braucht eine verlässliche Watermark je Quelle (DATA-INC)"],
         "limitierungen": [{"text": "Inkrementell nur, wenn CDF auf allen Quellen aktiv ist und der Zyklus append-only war",
                            "quelle": "MS Learn: fabric/data-engineering/materialized-lake-views/refresh-materialized-lake-view"}],
         "implikation": "Die Emission legt Silber einmal leer mit CDF an und fügt je Lauf per INSERT nur neue Zeilen an; ausführbar, sobald der Katalog eine Änderungs- oder Anlagespalte der Quelle nennt."},
        {"wert": "merge",
         "text": "MERGE mit Change Data Feed: Änderungen und Löschungen einarbeiten",
         "vorteile": ["Korrekturen der Quelle kommen an",
                      "Laufzeit wächst mit den Änderungen"],
         "nachteile": ["Ohne REFRESH_HINT lässt ein Zyklus mit Änderung oder Löschung die MLV voll rechnen",
                       "Braucht Match-Key und Löschkennzeichen je Quelle"],
         # Bis 01.10.2026 stand hier „erzwingen den Vollaufbau, auch mit CDF“. MS Learn *Enable
         # optimal refresh for deletes and updates* (optimal-refresh-handling-deletes-updates,
         # gelesen 01.10.2026): mit `REFRESH_HINT … UNIQUE (…)` laufen Updates und Deletes
         # inkrementell (Preview, nur CDF auf allen Quellen vorausgesetzt).
         "limitierungen": [{"text": "Updates oder Deletes im Zyklus laufen nur mit REFRESH_HINT inkrementell (Preview, Fabric prüft die Eindeutigkeit nicht); ohne Hint Vollaufbau der MLV, auch mit CDF",
                            "quelle": "MS Learn: fabric/data-engineering/materialized-lake-views/optimal-refresh-handling-deletes-updates"}],
         "implikation": "Die Emission legt Silber einmal leer mit CDF an und schreibt per MERGE; der Schlüssel der Quelltabelle bleibt Platzhalter, bis der Datenvertrag ihn nennt."},
    ],
    "PLAT-TRANSFORM": [
        {"wert": "mlv_standard", "empfohlen": True,
         "text": "MLV als Standard, Pipeline dort, wo MLV es nachweislich nicht kann",
         "vorteile": ["Abhängigkeitsreihenfolge, Refresh-Strategie, Lineage und DQ-Regeln kommen mit — ausgelöst werden muss der Refresh trotzdem (Zeitplan, D-529)", "Direct Lake über Views nur mit MLV ohne Import"],
         "nachteile": ["Zwei Mechanismen nebeneinander"],
         "limitierungen": [{"text": "MLV kennt kein DML, keine UDFs, kein Time Travel, keine temporären Views; Session-Properties greifen im geplanten Refresh nicht",
                            "quelle": "MS Learn: fabric/data-engineering/materialized-lake-views/overview"},
                           {"text": "Setzt schema-aktiviertes Lakehouse und Runtime 1.3 voraus", "quelle": "MS Learn: fabric/data-engineering/materialized-lake-views/overview"}],
         "implikation": "Jeder Hop mit Upsert läuft als Pipeline; alle anderen als MLV."},
        {"wert": "pipelines",
         "text": "Durchgängig Pipelines und Notebooks",
         "vorteile": ["Volle Kontrolle über Retry und Backfill"],
         "nachteile": ["Was man baut, betreibt man; Lineage und Abhängigkeiten selbst pflegen"],
         "limitierungen": [{"text": "Direct Lake kann über einer nicht materialisierten View keine Tabelle bilden",
                            "quelle": "MS Learn: fabric/fundamentals/direct-lake-overview"}],
         "implikation": "Ein Orchestrierungsplan mit Abhängigkeitsgraph gehört zur Lieferung."},
        {"wert": "nur_mlv",
         "text": "Durchgängig MLV",
         "vorteile": ["Ein Mechanismus"],
         "nachteile": ["Nur bei reinem Append oder Replace möglich"],
         "limitierungen": [{"text": "Kein MERGE, kein CDC, kein SCD-2", "quelle": "MS Learn: fabric/data-engineering/materialized-lake-views/overview"}],
         "implikation": "DATA-INC wird zu Vollast oder Partition-Overwrite."},
    ],
    "DATA-CLUSTER": [
        {"wert": "spaeter",
         "text": "Ohne Clustering starten und nach den ersten echten Abfragen nachziehen",
         "vorteile": ["Die Spalten folgen aus gemessenem Verhalten, nicht aus Vermutung"],
         "nachteile": ["Bis dahin lesen Direct Lake und SQL mehr Dateien als nötig"],
         "limitierungen": [{"text": "Liquid Clustering: Silber empfohlen, Gold erforderlich", "quelle": "MS Learn: fabric/data-engineering/delta-optimization-and-v-order"}],
         "implikation": "Ein Messfenster nach Go-Live liefert die Spalten."},
        {"wert": "zorder",
         "text": "Bei partitionierten Tabellen Z-Order statt Liquid Clustering",
         "vorteile": ["Funktioniert mit Partitionen"],
         "nachteile": ["Muss nach jedem Schreiben neu laufen"],
         "limitierungen": [{"text": "Liquid Clustering greift bei partitionierten Tabellen nicht", "quelle": "MS Learn: fabric/data-engineering/delta-optimization-and-v-order"}],
         "implikation": "OPTIMIZE ZORDER wird Teil des Wartungsplans."},
    ],
    "PLAT-TIER": [
        {"wert": "aus_vertrag",
         "text": "Stufe aus dem bestehenden Vertrag übernehmen",
         "vorteile": ["Eine Tatsache, keine Wahl"],
         "nachteile": ["Fähigkeiten, die die Stufe nicht hat, bleiben unerreichbar"],
         "limitierungen": [{"text": "Replication, Private Connectivity und lange Time-Travel-Fenster hängen an der Stufe",
                            "quelle": "stack_capabilities.tiers_for"}],
         "implikation": "Die Fähigkeits-Hinweise der Lieferung werden gegen die Stufe geprüft."},
        {"wert": "hochstufen",
         "text": "Für die Lieferung eine höhere Stufe beschaffen",
         "vorteile": ["Alle benannten Mechanismen zusagbar"],
         "nachteile": ["Vertragsgegenstand, Mehrkosten"],
         "limitierungen": [{"text": "Eine Stufenänderung ist ein Einkaufsvorgang, kein Schalter", "quelle": "eigene Einschaetzung"}],
         "implikation": "Einkauf entscheidet vor P5."},
    ],
    # I-21 (FabCon Europe 2026, 30.09.2026) -------------------------------------------------
    "SEC-MIRROR": [
        {"wert": "onelake_rollen", "empfohlen": True,
         "text": "Spiegeln und die Rechte der Quelle als OneLake-Security-Rollen nachbilden",
         "vorteile": ["Der Spiegel bleibt aktuell, ohne eigene Ladestrecke",
                      "Zeilen- und Spaltenfilter wirken für jeden Leser über OneLake"],
         # Bis 01.10.2026 stand hier „Rollen auf gespiegelten Items sind Preview“. MS Learn
         # (whats-new-archive, gelesen 01.10.2026): OneLake security GA seit Mai 2026;
         # onelake/security/data-access-control-model (gelesen 01.10.2026): gespiegelte
         # Datenbanken/Kataloge nur Read, ReadWrite nur im Lakehouse und ohne RLS/CLS.
         "nachteile": ["Die Rechte existieren zweimal, in der Quelle und in Fabric",
                       "Auf gespiegelten Items nur Leserollen (Read); Schreiben vor dem Lesen geht dort nicht"],
         "limitierungen": [{"text": "Mirroring übernimmt Zeilen-, Spaltenrechte und Maskierung der Quelle nicht",
                            "quelle": "MS Learn: fabric/mirroring/azure-sql-database-how-to-data-security"},
                           {"text": "OneLake Security ist GA (Mai 2026); Rollen auf gespiegelten Datenbanken und Katalogen erlauben nur Read, ReadWrite gibt es nur im Lakehouse und dort ohne RLS/CLS",
                            "quelle": "MS Learn: fabric/onelake/security/data-access-control-model"}],
         "implikation": "Je Quelle mit Rechten ein Arbeitspaket Rechte-Nachbau und ein Abnahmetest mit einem Leser ohne Rolle."},
        {"wert": "kopie",
         "text": "In ein gesteuertes Lakehouse kopieren und dort absichern",
         "vorteile": ["Lesen und Schreiben in OneLake, Transformation vor dem ersten Lesen"],
         "nachteile": ["Eine Ladestrecke mehr; der Stand hängt am Ladezyklus"],
         "limitierungen": [{"text": "Copy verlangt nach P1 eine Begründung (Leistung, Isolation, Compliance)",
                            "quelle": "architecture_blueprint.schema.json ingestion[].rationale"}],
         "implikation": "access_mode wird copy statt mirror."},
        {"wert": "teilweise",
         "text": "Nur Tabellen ohne schutzbedürftige Inhalte spiegeln, den Rest kopieren",
         "vorteile": ["Spiegel dort, wo er nichts preisgibt"],
         "nachteile": ["Zwei Ladewege für eine Quelle"],
         "limitierungen": [{"text": "Die Auswahl eines Spiegels greift je Tabelle, nicht je Spalte",
                            "quelle": "eigene Einschaetzung"}],
         "implikation": "Je Tabelle steht fest, ob sie gespiegelt oder kopiert wird."},
    ],
    "OPS-MONITORING": [
        {"wert": "eigene_kapazitaet", "empfohlen": True,
         "text": "Ein zentrales Monitoring-Eventhouse in einem eigenen Workspace auf einer eigenen, kleinen Kapazität",
         "vorteile": ["Eine Stelle für Abfragen und Alarme über alle Workspaces",
                      "Drosselung einer Arbeitskapazität trifft die Überwachung nicht, und die Überwachung belastet keine Arbeitskapazität"],
         "nachteile": ["Eine Kapazität mehr in der Rechnung (kleinste F-SKU genügt meist)"],
         "limitierungen": [{"text": "Learn empfiehlt, den Workspace mit dem zentralen Monitoring-Eventhouse auf eine eigene Kapazität zu isolieren",
                            "quelle": "MS Learn: fabric/fundamentals/enable-workspace-monitoring#recommended-architecture"},
                           {"text": "Den eigenen Endpoint gibt es nur bei der Anlage des Monitoring-Items",
                            "quelle": "MS Learn: fabric/fundamentals/enable-workspace-monitoring"},
                           {"text": "Ein aktivierter Operations Agent lässt sich nicht abschalten",
                            "quelle": "MS Learn: fabric/fundamentals/enable-workspace-monitoring"}],
         "implikation": "Monitoring-Kapazität, Workspace und Eventhouse stehen im Bauplan; KI-Untersuchungen folgen der KI-Richtlinie."},
        {"wert": "nicht_prod",
         "text": "Ein zentrales Monitoring-Eventhouse in einem eigenen Workspace auf der Nicht-Produktionskapazität",
         "vorteile": ["Keine weitere Kapazität", "Die Ingestion belastet nicht die Produktionskapazität (D-596)"],
         "nachteile": ["Ist Dev/Test gedrosselt, werden Berichte und Activator-Alarme auf den Monitoring-Daten mitgedrosselt; Ingestion und Abfragen laufen weiter"],
         "limitierungen": [{"text": "Den eigenen Endpoint gibt es nur bei der Anlage des Monitoring-Items",
                            "quelle": "MS Learn: fabric/fundamentals/enable-workspace-monitoring"},
                           {"text": "Ein aktivierter Operations Agent lässt sich nicht abschalten",
                            "quelle": "MS Learn: fabric/fundamentals/enable-workspace-monitoring"}],
         "implikation": "Alarme aus der Überwachung sind so verlässlich wie die Dev/Test-Kapazität."},
        {"wert": "je_workspace",
         "text": "Monitoring je Workspace",
         "vorteile": ["Jeder Workspace-Eigentümer sieht nur seinen Betrieb"],
         "nachteile": ["Keine übergreifende Sicht; Alarme je Workspace gepflegt"],
         "limitierungen": [{"text": "Workspace-Monitoring wird je Workspace aktiviert",
                            "quelle": "MS Learn: fabric/fundamentals/enable-workspace-monitoring"}],
         "implikation": "Auswertungen über Workspaces hinweg brauchen eine eigene Zusammenführung."},
        {"wert": "monitor_hub",
         "text": "Kein Monitoring-Item, nur Monitor hub und Capacity Metrics",
         "vorteile": ["Keine zusätzliche Ingestion, nichts Unumkehrbares"],
         "nachteile": ["Kurze Historie, keine eigenen Abfragen"],
         "limitierungen": [{"text": "Monitor hub zeigt Aktivitäten nur über ein begrenztes Zeitfenster",
                            "quelle": "MS Learn: fabric/admin/monitoring-hub"}],
         "implikation": "Fehleranalysen beginnen beim Alarm, nicht in einer Abfrage."},
    ],
    "PLAT-OVERAGE": [
        {"wert": "schwelle_prod", "empfohlen": True,
         "text": "Overage nur auf der Produktionskapazität, Schwelle unter einem Drittel der Tages-CU-Stunden; Nicht-Produktion aus",
         "vorteile": ["Produktion wird bei Spitzen nicht gedrosselt",
                      "Die Schwelle begrenzt den Zukauf je 24 Stunden"],
         "nachteile": ["Zugekaufte CU kosten den dreifachen PAYG-Satz"],
         "limitierungen": [{"text": "Overage ist bei neuen F-Kapazitäten ab Werk an (Schwelle 25 %)",
                            "quelle": "MS Learn: fabric/enterprise/capacity-overage-overview"},
                           {"text": "Die Schwelle ist keine harte Kostengrenze: Prüfung alle fünf Minuten, laufende Operationen werden weiter abgerechnet",
                            "quelle": "MS Learn: fabric/enterprise/capacity-overage-overview"}],
         "implikation": "platform.capacities[].overage ist je Kapazität gesetzt; P4 der Conformance meldet nichts mehr."},
        {"wert": "aus",
         "text": "Overage überall aus, Drosselung wird akzeptiert",
         "vorteile": ["Keine Kosten über die SKU hinaus"],
         "nachteile": ["Spitzen werden gedrosselt; Berichte und Läufe warten"],
         "limitierungen": [{"text": "Drosselung trifft interaktive Nutzung, sobald die Glättung aufgebraucht ist",
                            "quelle": "MS Learn: fabric/enterprise/throttling"}],
         "implikation": "Surge Protection und Alarme tragen die Last allein."},
        {"wert": "groesser",
         "text": "Größere SKU statt Overage",
         "vorteile": ["Planbare Kosten, die Reserve ist dauerhaft da"],
         "nachteile": ["Bezahlt die Spitze auch in ruhigen Stunden"],
         "limitierungen": [{"text": "Eine Kapazität wird nach bereitgestellter Größe abgerechnet, nicht nach Last",
                            "quelle": "architecture_blueprint.schema.json platform.sizing.hours_per_week"}],
         "implikation": "Die SKU-Empfehlung steigt um eine Stufe."},
    ],
    "OUT-REPORT": [
        {"wert": "pbir",
         "text": "Power-BI-Bericht (PBIR) für die Analyse",
         "vorteile": ["GA und in allen Fabric-Regionen verfügbar", "Versionierbar im Git-Format"],
         "nachteile": ["Keine Eingaben, kein Rückschreiben"],
         "limitierungen": [{"text": "Rückschreiben aus einem Bericht braucht eine eigene Anwendung",
                            "quelle": "eigene Einschaetzung"}],
         "implikation": "Der Report-Emitter bleibt PBIR."},
        {"wert": "app",
         "text": "Fabric App mit Eingaben, Rückschreiben und Workflows",
         "vorteile": ["Eingabe und Auswertung in einer Oberfläche"],
         "nachteile": ["Preview", "Braucht eine Fabric SQL Database für das Rückschreiben"],
         "limitierungen": [{"text": "Fabric Apps sind nicht in jeder Region verfügbar, etwa nicht in North Europe",
                            "quelle": "MS Learn: fabric/admin/region-availability"},
                           {"text": "Der Weg über Pro/PPU ohne Kapazität ist angekündigt, aber nicht dokumentiert",
                            "quelle": "eigene Einschaetzung"}],
         "implikation": "Ausgabe-Ziel fabric_app (D-583) und eine SQL Database je Anwendung."},
        {"wert": "beides", "empfohlen": True,
         "text": "PBIR für die Analyse, Fabric App nur für die Eingabe (D-583: zwei gleichrangige Ziele)",
         "vorteile": ["Jede Oberfläche tut, wofür sie gebaut ist"],
         "nachteile": ["Zwei Artefakttypen im Betrieb"],
         "limitierungen": [{"text": "Fabric Apps sind nicht in jeder Region verfügbar",
                            "quelle": "MS Learn: fabric/admin/region-availability"}],
         "implikation": "Beide Ausgaben laufen; Konsumenten brauchen nur Read."},
    ],
    "AI-DE-COPILOT": [
        {"wert": "nicht_prod", "empfohlen": True,
         "text": "Nur in Entwicklung und Test; Ergebnisse über den normalen Release-Weg",
         "vorteile": ["Schneller in der Entwicklung; Produktion bleibt im Release-Prozess"],
         "nachteile": ["CU-Verbrauch auf der Nicht-Produktionskapazität"],
         "limitierungen": [{"text": "Copilot und die Verarbeitung außerhalb der Geo sind Tenant-Schalter",
                            "quelle": "MS Learn: fabric/fundamentals/copilot-fabric-overview"},
                           {"text": "Der Data engineering agent läuft nicht in Workspaces mit Outbound Access Protection",
                            "quelle": "MS Learn: fabric/data-engineering/data-engineering-agent-get-started"}],
         "implikation": "Tenant-Schalter in der Admin-Liste; Copilot-CU auf der Nicht-Produktionskapazität eingeplant."},
        {"wert": "aus",
         "text": "Nicht verwenden",
         "vorteile": ["Keine KI-Verarbeitung, keine Tenant-Freigabe nötig"],
         "nachteile": ["Kein Beschleuniger in der Entwicklung"],
         "limitierungen": [{"text": "Der Data engineering agent ist Preview",
                            "quelle": "MS Learn: fabric/data-engineering/data-engineering-agent-get-started"}],
         "implikation": "Nichts zu tun."},
        {"wert": "ueberall",
         "text": "Auch in Produktions-Workspaces",
         "vorteile": ["Auch Betriebskorrekturen mit Assistenz"],
         "nachteile": ["Code entsteht an der Release-Kontrolle vorbei"],
         "limitierungen": [{"text": "Erzeugter Code durchläuft nur die Prüfungen, die im Prozess stehen",
                            "quelle": "eigene Einschaetzung"}],
         "implikation": "Änderungen in Produktion brauchen eine nachträgliche Prüfung."},
    ],
    "GOV-CATALOG": [
        {"wert": "nein", "empfohlen": True,
         "text": "OneLake catalog trägt die Governance (Domänen, Endorsement, Beschreibungen, Lineage); Purview nicht im Umfang",
         "vorteile": ["Keine Zusatzlizenz, keine Tenant-Rechte außerhalb von Fabric",
                      "Der Andockpunkt bleibt dokumentiert (governance/purview/_PURVIEW.md)"],
         "nachteile": ["Keine Sensitivity Labels, keine DLP, kein Audit über Fabric hinaus"],
         "limitierungen": [{"text": "Der OneLake catalog zeigt nur Fabric-Elemente; Quellen außerhalb von Fabric erscheinen dort nicht",
                            "quelle": "MS Learn: fabric/governance/onelake-catalog-overview"}],
         "implikation": "governance.purview.im_umfang = nein; es entsteht nur _PURVIEW.md mit den Andockpunkten."},
        {"wert": "teilweise",
         "text": "Labels und DLP für Power BI und Fabric, der Rest bleibt im OneLake catalog",
         "vorteile": ["Schutz sensibler Daten an Bericht und Export",
                      "Kein eigenes Purview-Konto für die Data Map nötig"],
         "nachteile": ["Microsoft 365 E5 oder ein Compliance-Zusatz je Nutzer",
                       "Fabric-Admin-Konto für das Massen-Labeling"],
         "limitierungen": [{"text": "Standard- und Pflichtlabel greifen nicht bei Veröffentlichung durch einen Dienstprinzipal",
                            "quelle": "MS Learn: fabric/governance/service-security-sensitivity-label-mandatory-label-policy"},
                           {"text": "DLP prüft keine Modelle, die ein Dienstprinzipal veröffentlicht oder besitzt",
                            "quelle": "MS Learn: purview/dlp-powerbi-get-started"}],
         "implikation": "governance.purview.bausteine = [labels, dlp]; Skripte unter governance/purview/labels und dlp."},
        {"wert": "voll",
         "text": "Purview vollständig: Labels, DLP, Data Map, Unified Catalog, Audit",
         "vorteile": ["Ein Katalog über Fabric und Fremdquellen", "Audit und Datenprodukte an einer Stelle"],
         "nachteile": ["Purview-Konto, Lizenzen und Pflege einer zweiten Domänenstruktur"],
         "limitierungen": [{"text": "Fabric-Domänen lassen sich nicht 1:1 auf Purview-Domänen abbilden (Data Map: höchstens fünf Plattform-Domänen); Governance-Domänen werden getrennt gepflegt",
                            "quelle": "MS Learn: purview/data-gov-best-practices-domains-and-gov-domains"},
                           {"text": "Fabric-Elemente außer Power BI werden bei Private Link auf Tenant- oder Workspace-Ebene nicht gescannt",
                            "quelle": "MS Learn: purview/register-scan-fabric-tenant"}],
         "implikation": "governance.purview.bausteine mit allen Bausteinen; die Domänen werden zweimal gepflegt."},
    ],
}


def _optionen_fuer(id_: str) -> list[dict[str, Any]]:
    """Tiefe Kopie der Optionen, damit kein Aufrufer den Katalog veraendert."""
    return [{**o, "vorteile": list(o.get("vorteile", [])), "nachteile": list(o.get("nachteile", [])),
             "limitierungen": [dict(lim) for lim in o.get("limitierungen", [])]}
            for o in _OPTIONEN.get(id_, [])]


def _rec(id_: str, topic: str, gap: str, proposal: str | None, derived_from: str,
         confidence: str, alternatives: list[str], decider: str, if_undecided: str,
         status: str = "offen", markers: tuple[str, ...] = (),
         ermittlung: dict[str, str] | None = None) -> dict:
    """``status`` is the lever that shrinks the workshop:

    * ``vorbelegt`` — a defensible house default is **already applied**; the customer only has to
      object. Used where a standard exists that is safe by construction (least privilege) or where the
      platform dictates the answer anyway (tenant settings, capacity ladder).
    * ``offen`` — genuinely needs a customer answer: their policy, their legal position, their
      identifiers. No default can stand in for it without inventing facts.

    ``ermittlung`` (17.08.2026, Flo: „Nicht jede Frage kann er ohne weiteres beantworten") —
    der Weg zur Antwort, in denselben drei Feldern wie bei den Intake-Fragen
    (``named_profiles.ERMITTLUNG_FELDER``): ``wo`` · ``wen`` · ``wenn_unklar``. Kein zweites
    Vokabular, weil beide im selben Ledger landen und derselbe Mensch sie liest.

    Wer ihn **nicht** braucht: eine ``vorbelegt``e Entscheidung. Dort ist der Vorschlag selbst
    der Weg — der Kunde bestaetigt oder widerspricht, und ``if_undecided`` sagt, was gilt, wenn
    er nichts tut. Gemessen 17.08.2026 blieben damit genau **sieben** Entscheidungen ohne jede
    Methode uebrig; es sind dieselben sieben, die Flo am Arbeitsblatt als unverstaendlich
    markiert hatte (Karten 22–28). Das ist kein Zufall: eine Frage ohne Vorschlag und ohne Weg
    ist ein leeres Textfeld mit einer Ueberschrift.
    """
    return {"id": id_, "topic": topic, "gap": gap, "proposal": proposal,
            "derived_from": derived_from, "confidence": confidence, "status": status,
            "alternatives": alternatives, "decider": decider, "if_undecided": if_undecided,
            "ermittlung": dict(ermittlung or _ERMITTLUNGSWEGE.get(id_, {})),
            # Die Kundenfassung und die Faelligkeit. Beide nach `id` nachgeschlagen statt am
            # Aufrufort gesetzt — siehe die Notiz an `_KUNDENFASSUNG` zu den doppelten
            # Aufrufstellen der modellgetriebenen Entscheidungen.
            "kunde": dict(_KUNDENFASSUNG.get(id_, {})),
            "faelligkeit": _FAELLIGKEIT.get(id_, ""),
            # Die Optionen-Landkarte (D-351): Vor-/Nachteile, Limitierungen mit Quelle,
            # Implikation je Option; `empfohlen` markiert den Punkt, an dem der Vorschlag steht.
            "optionen": _optionen_fuer(id_),
            # `markers`: die `TODO(...)`-Marken im Lieferumfang, die GENAU diese Entscheidung
            # auflöst. Damit wird aus einer thematischen Zuordnung eine prüfbare — DoD-Kriterium
            # PE-05 kann so mechanisch statt per Urteil prüfen, dass kein Platzhalter stumm ist.
            "markers": list(markers)}


def propose_domain_roles(bp: dict) -> dict:
    """Wer die Domaene besitzt — BK-W02, und die einzige Frage, die das Skript nicht loesen kann.

    Der **Name** beider Gruppen ist abgeleitet (``provision_governance.entra_gruppenname``, Schema
    aus BK-W04), die **objectId** holt der Nachschlage-Sammler. Was keine Maschine hergibt, ist die
    Besetzung: welche Gruppe der fachliche Eigentuemer ist. Deshalb ``vorbelegt`` und nicht
    ``offen`` — die Struktur steht, der Kunde nennt nur, wer dahintersteht oder widerspricht dem
    Zuschnitt.

    Zwei Punkte, die MS Learn ausdruecklich sagt und die von aussen wie Erfolg aussehen, wenn man
    sie uebergeht (learn.microsoft.com/fabric/governance/domains, geprueft 20.08.2026): Domain-
    Admins kann **nur ein Fabric-Administrator** setzen, und ein Domain-Contributor kann einen
    Workspace nur dann zuordnen, wenn er in **diesem Workspace zugleich Admin** ist.
    """
    doms = _domain_names(bp)
    beispiel = _NONWORD_RE.sub("-", (doms[0].lower() if doms else "domaene")).strip("-")
    return _rec(
        "GOV-DOMAIN", "Domänen-Eigentümer und Domänen-Mitwirkende",
        "Wer ist Domain-Admin und wer Domain-Contributor je Fabric-Domäne?",
        ("**Vorbelegt nach dem Namensschema** — bitte nur widersprechen, wenn der Zuschnitt "
         "fachlich nicht passt:\n"
         f"- **Domain-Admin → `fab-{beispiel}-domain-admin`**, besetzt mit dem fachlichen "
         "Dateneigentümer der Domäne, nicht mit der IT. Er überschreibt Tenant-Einstellungen "
         "für seinen Bereich und verantwortet die Auffindbarkeit im OneLake-Katalog.\n"
         f"- **Domain-Contributor → `fab-{beispiel}-domain-contributor`**, besetzt mit denen, die "
         "Arbeitsbereiche in die Domäne hängen dürfen.\n"
         "- **Beides Entra-Gruppen, nie Personen** (wie bei den Workspace-Rollen). In einer "
         "kleinen Organisation darf es dieselbe Gruppe für beide Rollen sein — dann bleibt es "
         "trotzdem eine Gruppe.\n"
         "- **Domain-Admins setzt nur ein Fabric-Administrator.** Ein Domain-Admin darf danach "
         "Contributors vergeben, aber keine weiteren Admins.\n"
         "- **Der Contributor braucht die Workspace-Admin-Rolle dazu**, sonst läuft die "
         "Zuordnung ins Leere, ohne einen Fehler zu melden.\n"
         "**Offen bleibt nur:** welche Gruppe das je Domäne ist. Die objectId holt "
         "`lookup/nachschlagen.sh`, sobald die Gruppe existiert."),
        "Namensschema aus BK-W04 + learn.microsoft.com/fabric/governance/domains-best-practices",
        "hoch",
        ["Domain-Admin an die IT geben (schnell, macht die Delegation wirkungslos)",
         "Keine Domain-Rollen setzen (Domäne bleibt eine Sortierhilfe ohne Wirkung)",
         "Eine Gruppe für beide Rollen (in kleinen Organisationen vertretbar)"],
        "Fachbereichsleitung je Domäne (Besetzung) — der Zuschnitt ist vorbelegt",
        "Ohne Domain-Admin bleiben Tenant-Einstellungen zentral, und niemand verantwortet die "
        "Auffindbarkeit der Domäne im Katalog",
        status="vorbelegt")


def propose_workspace_roles(bp: dict) -> dict:
    """Workspace RBAC as an APPLIED least-privilege default, not a question.

    Grounded (MS Learn 2026-07: *Roles in workspaces*, *Give users access to workspaces*, *Best
    practices for OneLake security*, *Security considerations for Fabric workloads*). The decisive
    detail most implementations get wrong: **RLS is only enforced for the Viewer role** — Admin,
    Member and Contributor implicitly hold Write and therefore bypass every row filter. So a consumer
    placed in Member "so they can see everything" silently defeats the entire security model."""
    doms = _domain_names(bp)
    return _rec(
        "SEC-ROLES", "Workspace-Rollen und Entra-Gruppen",
        "Wer bekommt welche Rolle im Workspace?",
        ("**Vorbelegt nach Least Privilege** — bitte nur widersprechen, wenn es fachlich nicht passt:\n"
         "- **Konsumenten → Viewer.** Nicht bequemlichkeitshalber Member: RLS wird **nur für Viewer "
         "erzwungen**; Admin/Member/Contributor halten implizit Write und umgehen jeden Zeilenfilter.\n"
         "- **Entwickler/Betrieb → Contributor**, und nur solange sie aktiv an der Lösung arbeiten.\n"
         "- **Admin/Member → so wenige wie möglich** (Rechteverwaltung, Sharing, OneLake-Rollen).\n"
         "- **Immer Entra-Sicherheitsgruppen, nie Einzelpersonen** — je Domäne und Rolle eine Gruppe"
         + (f", z. B. `sg-fabric-{_NONWORD_RE.sub('-', doms[0].lower()).strip('-')}-viewer`" if doms else "")
         + ". Überlappende Gruppen: die **höchste** Rolle gewinnt — deshalb Konsumenten nie zusätzlich "
           "in eine Contributor-Gruppe legen.\n"
         "- **Braucht jemand nur EIN Artefakt**, kein Workspace-Rolle vergeben, sondern das Item "
         "**teilen** (Item-Permission) — sonst sieht er den ganzen Workspace.\n"
         "- **Dienste/Automation → Service Principal** bzw. Workspace-Identity, keine persönlichen "
         "Konten und keine eingebetteten Zugangsdaten.\n"
         "- **DefaultReader-Rolle in OneLake entfernen**, sobald eigene Rollen existieren — sonst "
         "behalten die Nutzer trotz feiner Rollen vollen Lesezugriff.\n"
         "**Offen bleibt nur:** die konkreten Entra-Gruppen-IDs (`<VERIFY>` in `governance.sh`)."),
        "MS-Learn-Rollenmodell + Least-Privilege-Leitlinie; die Rollenmatrix selbst ist plattformseitig fix",
        "hoch",
        ["Rollen direkt an Personen vergeben (schnell, bricht bei jedem Wechsel)",
         "Alle Konsumenten in Member (bequem — hebelt RLS vollständig aus)",
         "Zugriff ausschließlich über App-Verteilung statt Workspace-Rollen"],
        "Security / Entra-Team (Gruppen) — Rollenzuschnitt ist vorbelegt",
        "Ohne Gruppen-Bindung greift keine Berechtigung; werden Konsumenten in Member gelegt, "
        "ist RLS/CLS wirkungslos",
        status="vorbelegt")


# --- individual proposals ---------------------------------------------------------------------------

def propose_rls(gc: dict, source_schema: dict | None = None) -> dict:
    """The row-filter predicate. Derived from the best org-scoping column in the model."""
    scored = []
    for t, c in _cols(gc, source_schema):
        w = _rank(c, _SCOPE_HINTS)
        if w:
            place = _placement(gc, t)
            scored.append((w * _PLACEMENT_WEIGHT[place], w, place, t, c))
    cands = sorted(scored, key=lambda x: (-x[0], x[3], x[4]))
    best = (cands[0][3], cands[0][4]) if cands else None
    if not best:
        return _rec("SEC-RLS", "RLS-Prädikat (Zeilen-Sichtbarkeit)",
                    "Welche Zeilen darf welche Nutzergruppe sehen?", None,
                    "keine Org-Spalte (Bereich/Gesellschaft/Region/…) im Modell gefunden",
                    "keine", ["Sichtbarkeit über Workspace-Trennung statt RLS",
                              "eine Scoping-Spalte im Gold-Modell ergänzen"],
                    "Data Owner + Security",
                    "Ohne einen erklärten Schnitt entsteht keine Zeilenbedingung, und die Rolle sieht alle Zeilen "
        "der freigegebenen Tabellen. Das trägt nur, solange die Entra-Gruppe leer ist")
    tbl, col = best
    score, raw, place = cands[0][0], cands[0][1], cands[0][2]
    others = sorted({c for _s, _w, _p, _t, c in cands if c != col})[:3]
    # A hit that only sits on an entity dimension is most likely a subject attribute, not a security
    # axis — say so and cap the confidence instead of selling a wrong axis as reliable.
    weak = place == "entity_dim"
    caveat = ("  **Achtung:** Der Treffer sitzt auf der Entitäts-Dimension "
              f"`{tbl}` — dort ist `{col}` vermutlich ein Sachattribut (Eigenschaft des Objekts) und "
              "KEINE Organisationsachse. Vor Übernahme fachlich prüfen; ggf. fehlt dem Modell eine "
              "echte Scoping-Spalte." if weak else "")
    return _rec(
        "SEC-RLS", "RLS-Prädikat (Zeilen-Sichtbarkeit)",
        "Welche Zeilen darf welche Nutzergruppe sehen?",
        f"Scoping über `{col}`: Mapping-Tabelle `sec_user_scope(user_upn, {col})` anlegen und "
        f"filtern mit\n"
        f"`select * from {tbl} where {col} in "
        f"(select {col} from sec_user_scope where user_upn = USER_NAME())`\n"
        f"— dynamisch, ohne Rolle pro Bereich. DAX-Äquivalent im Semantic Model: "
        f"`[{col}] IN CALCULATETABLE(VALUES(sec_user_scope[{col}]), "
        f"sec_user_scope[user_upn] = USERPRINCIPALNAME())`." + caveat,
        f"Spalte `{tbl}.{col}` als Org-Scoping-Achse erkannt (Platzierung: {place}, Namens-Gewicht {raw})"
        + (f"; Alternativen im Modell: {', '.join(others)}" if others else ""),
        "niedrig" if weak else ("hoch" if score >= 8 else "mittel"),
        [f"statische Rolle je Ausprägung von `{col}` (einfacher, aber Rollen-Wildwuchs)",
         "kein RLS — Trennung rein über getrennte Workspaces/Modelle"] +
        ([f"Scoping über `{o}` statt `{col}`" for o in others[:1]] if others else []),
        "Data Owner der Domäne (fachlich) + Security (technisch)",
        "Ohne einen erklärten Schnitt entsteht keine Zeilenbedingung, und die Rolle sieht alle Zeilen "
        "der freigegebenen Tabellen. Das trägt nur, solange die Entra-Gruppe leer ist")


def propose_cls(gc: dict, source_schema: dict | None = None) -> dict:
    """Sensitive columns to hide. Derived from column-name patterns (personal / commercial)."""
    hits: dict[str, list[str]] = {}
    for t, c in _cols(gc, source_schema):
        for h, why in _SENSITIVE_HINTS.items():
            if h in c.lower():
                hits.setdefault(why, []).append(f"{t}.{c}")
                break
    if not hits:
        return _rec("SEC-CLS", "Sensible Spalten (CLS/OLS)",
                    "Welche Spalten dürfen nicht alle sehen?", None,
                    "keine Spaltennamen mit typischen Sensibilitäts-Mustern gefunden",
                    "keine", ["Klassifikation im Fachbereich erheben (Spalten-Review)"],
                    "Data Owner + Datenschutzbeauftragte:r",
                    "Alle Spalten bleiben für jede berechtigte Rolle sichtbar")
    flat = sorted({c for v in hits.values() for c in v})
    detail = "; ".join(f"**{why}**: {', '.join(sorted(set(cols)))}" for why, cols in sorted(hits.items()))
    return _rec(
        "SEC-CLS", "Sensible Spalten (CLS/OLS)",
        "Welche Spalten dürfen nicht alle sehen?",
        f"Diese {len(flat)} Spalte(n) als sensibel deklarieren und über `--sensitivity` ausblenden: "
        f"{detail}. OneLake-CLS zeigt dann nur das Komplement; im Semantic Model werden sie per "
        f"`metadataPermission: none` verborgen.",
        "Spaltennamen-Muster im governten Katalog (personenbezogen / wirtschaftlich sensibel)",
        "mittel",
        ["Spalten im Gold-Modell gar nicht materialisieren (stärkster Schutz)",
         "Sichtbar lassen und nur über Sensitivity-Label kennzeichnen (schwächster Schutz)"],
        "Datenschutzbeauftragte:r (personenbezogen) + Data Owner (wirtschaftlich)",
        "Auch sensible Spalten bleiben für jede berechtigte Rolle sichtbar")


def _aus_quelle(source_schema: dict | None) -> dict | None:
    """Der Vorschlag fuer DATA-INC aus der **Introspektion**, wenn der Katalog schweigt.

    Ehrlich schwaecher als der Katalog-Weg und deshalb getrennt: die Quelle sagt, welche
    Spalten es gibt, nicht welche Tabelle fachlich die Fakten traegt. Deshalb wird hier
    nichts zur Fakten-Tabelle erklaert — es werden die Kandidaten je Tabelle genannt, und die
    Bestaetigung des Grains bleibt offen. Konfidenz „mittel", nie „hoch".
    """
    from core.dataarch_engine.blueprint.source_schema import key_candidates, watermark_candidates

    zeilen = []
    for quelle, objs in sorted((source_schema or {}).items()):
        for obj in sorted(objs or [], key=lambda o: str(o.get("name") or "")):
            wm = watermark_candidates(obj)
            keys = key_candidates(obj)
            if not wm and not keys:
                continue
            zeilen.append((f"{quelle}.{obj.get('name')}", keys[:2], wm[:2]))
    if not zeilen:
        return None
    text = "; ".join(
        f"`{t}` — Schlüssel {', '.join(f'`{k}`' for k in ks) or '—'}, "
        f"Änderungsspalte {', '.join(f'`{w}`' for w in ws) or '—'}"
        for t, ks, ws in zeilen)
    mit_wm = sum(1 for _t, _k, ws in zeilen if ws)
    return {"text": text, "tabellen": len(zeilen), "mit_wm": mit_wm}


def propose_incremental(gc: dict, source_schema: dict | None = None) -> dict:
    """Match key + watermark for the MERGE upsert."""
    facts = _facts(gc)
    if not facts:
        aus_quelle = _aus_quelle(source_schema)
        if aus_quelle:
            return _rec(
                "DATA-INC", "Inkrementelles Laden (Match-Key + Watermark)",
                "Woran erkennt der MERGE geänderte Zeilen?",
                ("Aus der Introspektion Ihrer Quellsysteme, nicht aus einem Modell: "
                 + aus_quelle["text"] + ". Zu bestätigen bleibt das **Grain** — welche "
                 "Spaltenkombination eine Zeile fachlich eindeutig macht. Die Änderungsspalte "
                 "ist damit belegt, der Match-Key ein Vorschlag."),
                f"Introspektion von {aus_quelle['tabellen']} Tabelle(n), "
                f"{aus_quelle['mit_wm']} davon mit Änderungsspalte",
                "mittel",
                ["Vollast beibehalten, solange die Datenmenge klein ist",
                 "CDC/Mirroring an der Quelle statt Watermark im Transform"],
                "Data Engineering + Quellsystem-Owner",
                "Der MERGE-Platzhalter bleibt unausgefüllt, es läuft weiter Vollast",
                markers=("contract",))
        return _rec("DATA-INC", "Inkrementelles Laden (Match-Key + Watermark)",
                    "Woran erkennt der MERGE geänderte Zeilen?", None,
                    "keine Fakten-Tabelle im Katalog, keine Introspektion der Quelle", "keine",
                    ["Vollast beibehalten, solange die Datenmenge klein ist"],
                    "Data Engineering + Quellsystem-Owner",
                    "Der MERGE-Platzhalter bleibt unausgefüllt, es läuft weiter Vollast",
                    markers=("contract",))
    f = sorted(facts, key=lambda t: t["name"])[0]
    cols = f.get("columns") or []
    keys = match_keys(f)
    wm = sorted(((_rank(c, _WATERMARK_HINTS), c) for c in cols), key=lambda x: (-x[0], x[1]))
    wm_col = next((c for w, c in wm if w > 0), None)
    have_wm = wm_col is not None
    return _rec(
        "DATA-INC", "Inkrementelles Laden (Match-Key + Watermark)",
        "Woran erkennt der MERGE geänderte Zeilen?",
        (f"**Match-Key** `{f['name']}`: {' + '.join(keys) if keys else '<fachlicher Geschäftsschlüssel>'}"
         f" (das Grain der Tabelle).\n"
         f"**Watermark**: " +
         (f"`{wm_col}` — nur Zeilen mit `{wm_col} > (select max({wm_col}) from gold_{f['name']})` laden."
          if have_wm else
          "keine Änderungsspalte im Modell. Vorschlag: im Silver eine technische Ladespalte "
          "`_loaded_at` ergänzen (Ingest-Zeitstempel) und darauf filtern — oder, wenn die Quelle es "
          "hergibt, CDC/Mirroring nutzen statt Watermark-Logik.")),
        f"Fakten-Tabelle `{f['name']}`: Schlüsselspalten {keys or '—'}"
        + (f", Änderungsspalte `{wm_col}` erkannt" if have_wm else ", keine Änderungsspalte erkannt"),
        "hoch" if (keys and have_wm) else "mittel" if keys else "niedrig",
        ["Vollast beibehalten (einfachste Variante, teuer ab realer Datenmenge)",
         "CDC/Mirroring an der Quelle statt Watermark im Transform",
         "Partition-Overwrite je Periode statt zeilenweisem MERGE",
         # D-622: bei Direct Lake (MS Learn direct-lake-understand-storage, gelesen 01.10.2026)
         "Append-only für Fakten (INSERT mit Watermark): erhält bei Direct Lake das inkrementelle "
         "Framing — nur korrekt, wenn die Quelle append-only ist (D-622)"],
        "Data Engineering + Quellsystem-Owner",
        "Der MERGE-Platzhalter bleibt unausgefüllt, es läuft weiter Vollast (CU-Kosten und Laufzeit)",
        # Schlüssel UND Änderungsspalte im Modell → die Strategie steht, nur bestätigen.
        # Fehlt eine von beiden, ist es eine echte Frage an das Quellsystem.
        status="vorbelegt" if (keys and have_wm) else "offen",
        markers=("contract",))


def propose_silver_contract(gc: dict) -> dict:
    """The silver data contract — partly derivable: the join keys ARE declared as relationships."""
    rels = gc.get("relationships") or []
    if not rels:
        return _rec("DATA-CONTRACT", "Silver-Datenvertrag", "Wie wird konformiert und verknüpft?",
                    None, "keine Beziehungen im Katalog deklariert", "keine",
                    ["Vertrag im Fachworkshop erheben"], "Data Owner + Data Engineering",
                    "Die Transform-Skelette bleiben `SELECT *` mit TODO-Markern",
                    markers=("contract:",))
    joins = "; ".join(f"`{r['from_table']}.{r['from_column']}` → `{r['to_table']}.{r['to_column']}`"
                      for r in rels[:6])
    more = f" (+{len(rels) - 6} weitere)" if len(rels) > 6 else ""
    return _rec(
        "DATA-CONTRACT", "Silver-Datenvertrag", "Wie wird konformiert und verknüpft?",
        f"Die **Join-Schlüssel stehen bereits fest** — aus den deklarierten Beziehungen: {joins}{more}. "
        f"Offen bleiben nur: Typisierung, Dedup-Regel je Geschäftsschlüssel, Null-/Qualitätsregeln und "
        f"Umgang mit spät eintreffenden Zeilen. Vorschlag: den Vertrag als ODCS-Datei aus diesen "
        f"Beziehungen vorbefüllen (`--emit-odcs`) und im Workshop nur die vier offenen Punkte klären.",
        f"{len(rels)} deklarierte Beziehung(en) im governten Katalog",
        "hoch",
        ["Vertrag komplett im Fachworkshop von Null erheben (langsamer)",
         "Ohne formalen Vertrag starten und im Betrieb nachziehen (Risiko: stille Qualitätsfehler)"],
        "Data Owner (fachlich) + Data Engineering (technisch)",
        "Die Transform-Skelette bleiben `SELECT *` mit TODO-Markern",
        # the joins ARE fixed by the declared relationships — only four points genuinely remain
        status="vorbelegt", markers=("contract:",))


def propose_retention(bp: dict, gc: dict, source_schema: dict | None = None) -> dict:
    """Retention periods — a legally-framed default proposal, explicitly to be confirmed."""
    personal = sorted({f"{t}.{c}" for t, c in _cols(gc, source_schema)
                       for h, why in _SENSITIVE_HINTS.items()
                       if h in c.lower() and why == "personenbezogen"})
    return _rec(
        "GOV-RET", "Aufbewahrungsfristen + Personenbezug",
        "Wie lange bleiben die Daten liegen, und was ist personenbezogen?",
        ("Zwei Fristen statt einer. Rechtlich zu bestätigen, und es ist kein Rechtsrat. "
         "Nicht personenbezogene Auswertungsdaten mit Beleg- oder Handelsbezug richten wir an "
         "Ihren handels- und steuerrechtlichen Fristen aus, in Deutschland typisch zehn Jahre, "
         "und entfernen sie danach per `DELETE` und `VACUUM` physisch. Personenbezogene "
         "Spalten bekommen eine zweckgebundene, kürzere Frist und ein Löschkonzept. "
         + (f"Kandidaten aus dem Modell: {', '.join(personal)}. "
            if personal else "Im Modell wurden keine offensichtlich personenbezogenen Spalten erkannt. ")
         + "Am einfachsten bleibt, personenbezogene Spalten gar nicht erst ins Gold zu "
           "materialisieren oder sie zu pseudonymisieren. Dann entfällt die kurze Frist für "
           "das Auswertungsmodell."),
        "Spaltennamen-Muster + die Struktur des Aufbewahrungs-Configs",
        "mittel",
        ["Einheitliche Frist für alles (einfach, aber datenschutzrechtlich schwach)",
         "Pseudonymisierung im Silver statt kurzer Frist im Gold",
         "Fristen aus dem bestehenden Löschkonzept des Kunden übernehmen"],
        "Datenschutzbeauftragte:r + Legal (verbindlich), Data Owner (fachlich)",
        "`retention_policy.json` bleibt mit `<VERIFY>` stehen, und es wird nichts gelöscht")


def propose_lakehouse_topology(bp: dict) -> dict:
    """Ein Lakehouse je Schicht — oder eine Domäne mit den Schichten als Schemas?

    Die Frage ist von `PLAT-LHSCHEMA` verschieden und wurde bisher stillschweigend beantwortet: der
    Baukasten legt ein Lakehouse je Domäne an und benutzt die Schemas als Schichten. MS Learn
    empfiehlt in *Understand medallion lakehouse architecture* ausdrücklich das andere: „Keep each
    layer separated in its own lakehouse or warehouse" und sogar „create each lakehouse in its own,
    separate workspace". Eine Abweichung von einer dokumentierten Empfehlung ist vertretbar — sie
    unbenannt zu lassen ist es nicht.
    """
    domains = _domain_names(bp)
    n = len(domains)
    return _rec(
        "PLAT-LHTOPO", "Lakehouse-Topologie (Schicht vs. Domäne)",
        "Bekommt jede Medaillon-Schicht ihr eigenes Lakehouse (ggf. eigenen Workspace), oder trägt "
        "ein Lakehouse je Domäne alle Schichten als Schemas?",
        ("**Vorbelegt: ein Lakehouse je Domäne, Schichten als Schemas** — mit der ausdrücklichen "
         "Notiz, dass MS Learn das Gegenteil empfiehlt (*„Keep each layer separated in its own "
         "lakehouse or warehouse“*, *„create each lakehouse in its own, separate workspace“*).\n\n"
         "Warum hier trotzdem so vorbelegt: der Schnitt, der bei diesem Kunden Governance trägt, "
         f"ist die **Domäne** ({n} Stück: {', '.join(domains) if domains else '—'}), nicht die "
         "Schicht. Eigentum, Endorsement und Berechtigung hängen an der Domäne; ein zusätzlicher "
         "Schicht-Schnitt auf Workspace-Ebene würde jede Domäne über drei Workspaces verteilen und "
         "das Eigentum zersplittern. Dazu kommt die harte Kopplung: **Materialized Lake Views setzen "
         "ein schema-aktiviertes Lakehouse voraus**, und MS' eigenes MLV-Tutorial fährt diese "
         "Form — ein `SalesLakehouse` mit bronze/silver/gold als Schemas.\n\n"
         "**Wann die andere Variante gewinnt** (dann umstellen, und zwar *vor* der Anlage):\n"
         "- die Schicht ist der Governance-Schnitt — Rohdaten-Zugriff soll organisatorisch anders "
         "verantwortet sein als das kuratierte Gold (regulierte Branchen, getrennte Betriebsteams);\n"
         "- Bronze wächst so, dass es eigene Kapazitäts-/Kostenzuordnung braucht;\n"
         "- Gold soll als **Warehouse** statt Lakehouse laufen (MS' Muster 2) — dann ist die Trennung "
         "ohnehin erzwungen, weil es zwei Item-Typen sind;\n"
         "- mehrere Domänen sollen aus **einem** gemeinsamen Bronze lesen, statt je Domäne zu landen."),
        "MS Learn (Medallion-Architektur: Layer-Trennung + Workspace-Empfehlung; MLV-Tutorial: "
        "Schichten als Schemas in einem Lakehouse) vs. dem Domänen-Schnitt in `mesh.domains`",
        "mittel",
        ["Ein Lakehouse je Schicht im selben Workspace (Kompromiss: Layer-Trennung ohne "
         "Workspace-Zersplitterung)",
         "Ein Workspace je Schicht (MS-Empfehlung; stärkste Trennung, teuerste Domänen-Zuordnung)",
         "Bronze+Silver als Lakehouse, Gold als Warehouse (MS-Muster 2) — wenn T-SQL-Serving "
         "gefordert ist"],
        "Data Platform Lead (verbindlich), Domain Owner (Eigentumsschnitt)",
        "Es bleibt bei einem Lakehouse je Domäne mit Schicht-Schemas — änderbar nur vor der Anlage, "
        "danach kostet es eine Datenbewegung",
        status="vorbelegt")


def propose_transform_engine(bp: dict) -> dict:
    """Materialized Lake Views oder gebaute Transform-Pipelines?

    Beide Emissionswege existieren im Baukasten (`--emit-mlv`, `--emit-transforms`) und waren bisher
    zwei gleichwertige Flags ohne Kriterium. Die Grenze ist aber nicht Geschmack, sondern eine
    dokumentierte Fähigkeitslücke.
    """
    products = sorted({p for d in bp.get("mesh", {}).get("domains", []) or []
                       for p in d.get("data_products", []) or []})
    incremental = bool((bp.get("medallion", {}).get("silver", {}) or {}).get("incremental"))
    return _rec(
        "PLAT-TRANSFORM", "Transformations-Engine (MLV vs. Pipeline)",
        "Werden die Schicht-Übergänge als Materialized Lake Views deklariert oder als gebaute "
        "Pipelines/Notebooks orchestriert?",
        ("**Vorbelegt: MLV als Standard, Pipeline dort, wo MLV es nachweislich nicht kann.** MLVs "
         "bringen Abhängigkeitsreihenfolge, Refresh-Strategie (inkrementell/voll/keine), Lineage "
         "und Datenqualitätsregeln mit. **Den Lauf selbst starten sie nicht** — dafür braucht es "
         "einen Zeitplan (`mlv/refresh_schedule.json`, D-529). Was man selbst baut, muss man "
         "selbst betreiben.\n\n"
         "**Die harte Grenze ist dokumentiert, nicht Geschmack:** eine MLV kennt **kein DML** — kein "
         "`INSERT`, `UPDATE`, `DELETE`. Ihre Daten entstehen ausschließlich aus dem `SELECT` der "
         "Definition. Alles, was ein *Zusammenführen mit dem Bestand* braucht, fällt damit raus:\n"
         "- **`MERGE`/Upsert, CDC, SCD-2** — der klassische Delta-Load gegen eine bestehende Tabelle;\n"
         "- **Nachträgliche Korrekturen** einzelner Zeilen (Storno, DSGVO-Löschung im Ziel);\n"
         "- Logik, die **UDFs** braucht, **Time Travel** (`VERSION AS OF`) liest oder über temporäre "
         "Views geht — alle drei sind in der MLV-Definition ausgeschlossen;\n"
         "- Schritte, die **Session-Spark-Properties** setzen: die greifen im geplanten Refresh nicht.\n\n"
         + (f"**Für diesen Blueprint relevant:** die Silver-Schicht ist auf inkrementelle Beladung "
            "gestellt. Inkrementell im Sinne von *Upsert gegen den Bestand* ist genau der Fall, den "
            "eine MLV nicht abbildet — dieser Hop gehört in eine Pipeline, die Gold-Aggregate darüber "
            "können MLVs bleiben.\n\n" if incremental else "")
         + "**Voraussetzungen** (sonst ist die Frage entschieden): schema-aktiviertes Lakehouse und "
           "Fabric Runtime 1.3. Schemanamen dürfen nicht durchgängig groß geschrieben sein.\n\n"
           "**Ein Vorteil, der leicht übersehen wird:** Direct Lake on OneLake kann über einer "
           "*nicht* materialisierten SQL-View gar keine Tabelle bilden — über einer MLV schon, weil "
           "dabei echte Delta-Tabellen entstehen. Wer Gold über Views definieren will und Direct Lake "
           "fahren will, hat mit MLV den einzigen Weg, der ohne Import-Modus auskommt."
         + (f"\n\nBetroffene Gold-Produkte: {', '.join(f'`{p}`' for p in products)}."
            if products else "")),
        "MS Learn (MLV-Grammatik + *Current limitations*: kein DML/UDF/Time-Travel/Temp-Views; "
        "Direct-Lake-Grenzen zu nicht-materialisierten Views) + `medallion.silver.incremental`",
        "hoch" if incremental else "mittel",
        ["Durchgängig Pipelines/Notebooks — wenn das Team Spark-Betrieb ohnehin fährt und volle "
         "Kontrolle über Retry/Backfill will",
         "Durchgängig MLV — nur wenn wirklich kein Hop ein Upsert braucht (reines Append/Replace)",
         "Gemischt je Hop: Ingress+Silver als Pipeline (Upsert), Gold-Aggregate als MLV"],
        "Data Engineering Lead (verbindlich), Data Platform Lead (Betriebsmodell)",
        "Beide Emissionen bleiben nebeneinander stehen (`--emit-mlv`, `--emit-transforms`) — der "
        "Betrieb entscheidet dann ungeplant, welche der beiden tatsächlich läuft",
        status="vorbelegt")


def propose_silver_load(bp: dict) -> dict:
    """Silber als Vollaufbau, append-only oder MERGE? (D-533, OQ-43)

    Die Frage stand nirgends, und sie entscheidet, ob eine Materialized Lake View je
    inkrementell aktualisiert werden kann: laut MS Learn nur mit Change Data Feed auf **allen**
    Quellen **und** append-only im Zyklus -- oder, mit `REFRESH_HINT … UNIQUE` auf der Sicht
    (Preview), auch bei Updates und Deletes (MS Learn optimal-refresh-handling-deletes-updates,
    gelesen 01.10.2026). Die Lieferung schreibt Silber per
    `CREATE OR REPLACE` -- jeder Lauf ist fuer die Plattform eine Aenderung an allem.
    `DATA-INC` beantwortet eine andere Frage (wie Gold nachlaedt), deshalb eine eigene.

    Vorbelegt mit dem, was die Emission heute tut. Eine Vorbelegung, die die Emission nicht
    einhaelt, waere dieselbe Behauptung wie der "automatische" Refresh aus D-529.
    """
    return _rec(
        "DATA-SILVER-LOAD", "Schreibmuster der Silber-Schicht (Vollaufbau, append-only, MERGE)",
        "Wird Silber bei jedem Lauf neu aufgebaut, nur ergänzt, oder per MERGE nachgeführt?",
        ("**Vorbelegt: Vollaufbau** — das, was die Lieferung heute schreibt (`CREATE OR "
         "REPLACE TABLE silver.<herkunft>`). Korrekt und idempotent; Korrekturen und Löschungen "
         "der Quelle kommen ohne Zusatzlogik an.\n\n"
         "**Der Preis, den diese Wahl hat:** jede Materialized Lake View darüber rechnet bei "
         "jedem Lauf voll. Inkrementell aktualisiert Fabric nur, wenn Change Data Feed auf "
         "**allen** Quellen aktiv ist **und** der Zyklus append-only war; ein Überschreiben ist "
         "eine Änderung an allem. Ein MERGE mit Änderung oder Löschung läuft nur dann "
         "inkrementell, wenn die Sicht einen `REFRESH_HINT … UNIQUE` trägt (Preview), sonst "
         "voll.\n\n"
         "**Wann umstellen:** wenn die gemessene Laufzeit der vollen Aktualisierung das "
         "Ladefenster sprengt — nicht vorher. Eine Antwort `append` oder `merge` baut die "
         "Emission: Silber wird einmal leer mit Change Data Feed angelegt und danach nur "
         "ergänzt bzw. per MERGE nachgeführt; was der Katalog nicht nennt (Änderungsspalte, "
         "Schlüssel der Quelltabelle), bleibt Platzhalter."),
        "MS Learn (*Optimal refresh for materialized lake views*, abgerufen 23.09.2026: CDF auf "
        "allen Quellen, append-only im Zyklus; *Enable optimal refresh for deletes and updates*, "
        "gelesen 01.10.2026: mit REFRESH_HINT auch Updates/Deletes, Preview) + Schreibmuster "
        "des Transform-Emitters",
        "mittel",
        ["append — nur neue Zeilen, CDF an; Korrekturen der Quelle kommen nicht an",
         "merge — Änderungen einarbeiten; ein Zyklus mit Update/Delete rechnet die MLV ohne "
         "REFRESH_HINT voll, mit Hint inkrementell (Preview)"],
        "Data Engineering Lead (verbindlich), Data Platform Lead (Kosten und Ladefenster)",
        "Vollaufbau bleibt stehen, ohne dass jemand ihn gewählt hat — und die Zusage "
        "„inkrementell mit Change Data Feed“ steht im Angebot, ohne dass die Lieferung sie trägt",
        status="vorbelegt")


def propose_text_language(gc: dict) -> dict | None:
    """In welcher Sprache stehen Stammdatentexte in Gold? (D-542) — nur, wenn es Texttabellen gibt.

    Seit D-542 loest die Emission die Zusammenfuehrung aus Kopf und Texttabelle selbst auf,
    weil das Standardpaket sie erklaert (`gold.role = text-attribute`). Offen bleibt genau eine
    Frage: welcher Text zuerst, wenn mehrere Sprachen gepflegt sind. Ohne Texttabelle im
    Katalog gibt es diese Frage nicht — dann steht sie auch nicht im Bogen.
    """
    betroffen = sorted(t["name"] for t in gc.get("tables") or []
                       if (t.get("zusammenfuehrung") or {}).get("art") == "text_verbund")
    if not betroffen:
        return None
    return _rec(
        "DATA-TEXTSPRACHE", "Sprache der Stammdatentexte in Gold",
        "Welcher Text steht in Gold, wenn eine Bezeichnung in mehreren Sprachen gepflegt ist?",
        (f"**Vorbelegt: `E` zuerst, sonst die nächste vorhandene Sprache.** Betrifft "
         f"{', '.join(f'`{b}`' for b in betroffen)}. Die Emission verbindet Kopf- und Texttabelle "
         "mit einem LEFT JOIN und nimmt je Schlüssel **einen** Text: die gewählte Sprache "
         "zuerst. Kein Stammsatz verschwindet, weil ein Text fehlt, und keiner verdoppelt sich, "
         "weil zwei gepflegt sind — das deklarierte Grain bleibt."),
        "SAP-Standardpaket (`gold.role = text-attribute`, Schlüssel der Texttabelle = Kopf + "
        "Sprache) + Emission D-542",
        "hoch",
        ["D — Deutsch zuerst", "je_sprache — alle Sprachen, Sprache im Schlüssel (ändert das Grain)"],
        "Fachbereich Berichtswesen (verbindlich), Data Engineering Lead (Umsetzung)",
        "Englische Bezeichnungen dort, wo beide Sprachen gepflegt sind — sichtbar in jedem Bericht",
        status="vorbelegt")


def propose_lakehouse_schemas(bp: dict) -> dict:
    """Schema-enabled lakehouse — the one layout choice that cannot be undone later."""
    external = bool(bp.get("sharing"))
    return _rec(
        "PLAT-LHSCHEMA", "Lakehouse mit Schemas",
        "Liegen die Tabellen in echten Medaillon-Schemas (`gold.fact_x`) oder flach unter `dbo` "
        "(`gold_fact_x`)?",
        ("**Vorbelegt: schema-aktiviert** (`gold.` / `silver.` / `bronze.`). Der Grund ist nicht "
         "Ästhetik, sondern Unumkehrbarkeit: Fabric hat **kein Werkzeug**, ein Lakehouse ohne "
         "Schemas nachträglich auf Schemas umzustellen, ohne Daten zu bewegen. Die Entscheidung "
         "fällt bei der Anlage — hinterher kostet sie eine Migration. Von zwei Optionen, die sonst "
         "ähnlich gut sind, ist die zu wählen, die man später noch ändern kann; hier ist das die "
         "schema-aktivierte, weil `dbo` sich per Schema-Shortcut nachbilden lässt, umgekehrt aber "
         "nicht.\n\n"
         "Fachlich kommt hinzu: die Schicht steht dann im Namensraum statt im Präfix, "
         "Berechtigungen lassen sich je Schema vergeben, und die Domänentrennung bleibt dort, wo "
         "sie hingehört — auf Workspace-Ebene. Ein zweiter Domänen-Schnitt im Schema würde sie "
         "doppeln.\n\n"
         "**Zwei dokumentierte Grenzen**, die dagegen sprechen können: ein schema-aktiviertes "
         "Lakehouse lässt sich **nicht** per Workspace-Sharing direkt teilen (Workaround: "
         "Shortcuts), und externe ADLS-Tabellen werden nicht direkt unterstützt (ebenfalls "
         "Shortcuts)."
         + (" **Achtung — dieser Blueprint hat eine `sharing`-Sektion**, also ist die erste Grenze "
            "hier real und gehört geprüft." if external else "")),
        "Fabric-Doku zu Lakehouse-Schemas (Limitationen + fehlendes Migrationswerkzeug)",
        "hoch",
        ["Flach unter `dbo` bleiben (`--no-lakehouse-schemas`) — nur mit Grund, etwa wenn das "
         "Lakehouse per Workspace-Sharing geteilt werden muss",
         "Schemas aktivieren, geteilte Zugriffe über Shortcuts lösen"],
        "Data Platform Lead (verbindlich), Data Owner (Sharing-Bedarf)",
        "Umstellung nach der Anlage bedeutet Daten bewegen — deshalb vor der ersten Provisionierung "
        "entscheiden",
        status="vorbelegt",
    )


def propose_alerts(bp: dict) -> dict:
    """Alert recipients — a role-mailbox structure rather than personal addresses."""
    doms = _domain_names(bp)
    return _rec(
        "OPS-ALERT", "Alarm-Empfänger", "Wer wird bei Fehlern und Drosselung benachrichtigt?",
        ("**Rollen-Postfächer statt Personen** (überlebt Personalwechsel): "
         "`fabric-platform-oncall@<kunde>` für Job-/Pipeline-Fehler und Capacity-Drosselung"
         + (f"; je Domäne zusätzlich ein fachlicher Verteiler, z. B. "
            + ", ".join(f"`{re.sub(r'[^a-z0-9]+', '-', d.lower()).strip('-')}-data@<kunde>`"
                        for d in doms[:3]) + "."
            if doms else ".")
         + " Eskalation zweistufig: Erst-Alarm an die Plattform-Rolle, bei ausbleibender Quittierung "
           "an den Data Owner. Kanal: E-Mail **und** Teams, damit ein Ausfall nicht am Kanal hängt."),
        f"{len(doms)} Domäne(n) im Blueprint",
        "hoch",
        ["Einzelpersonen direkt eintragen (schnell, aber bricht bei Wechsel)",
         "Nur ein zentraler Verteiler ohne Domänen-Split (weniger Rauschen, unschärfere Zuordnung)"],
        "Betriebsverantwortliche:r + Data Owner",
        "Empfänger bleiben `<VERIFY>` — Alarme werden konfiguriert, aber niemand bekommt sie",
        status="vorbelegt")


def propose_endorsement(bp: dict, gc: dict) -> dict:
    """Which domain gets Certified vs Promoted — portal-only, but the decision can be pre-thought."""
    doms = _domain_names(bp)
    lead = doms[0] if doms else "die führende Domäne"
    return _rec(
        "GOV-END", "Endorsement (Promoted / Certified)",
        "Welches Modell ist die verbindliche Quelle?",
        (f"**Certified** nur für das Modell, das wirklich die verbindliche Quelle ist — Vorschlag: "
         f"„{lead}“, weil es die governten Kennzahlen trägt. "
         "Alle übrigen Domänen starten als **Promoted**. Certified erst *nach* dem ersten sauberen "
         "Betriebszyklus setzen (Qualitätsgates grün, Owner benannt), sonst zertifiziert man einen "
         "ungetesteten Stand. Voraussetzung: eine admin-autorisierte Sicherheitsgruppe im Tenant-Setting."),
        f"{len(doms)} Domäne(n); Endorsement-Wunsch aus dem Blueprint",
        "mittel",
        ["Alles nur Promoted lassen (kein Zertifizierungsprozess nötig)",
         "Certified sofort mit Go-Live (schneller, aber ohne Betriebsnachweis)"],
        "Data Governance Board / Fabric-Admin (setzt es im Portal)",
        "Kein Endorsement — Nutzer erkennen nicht, welches Modell verbindlich ist",
        status="vorbelegt")


def propose_capacity(bp: dict) -> dict:
    """Capacity sizing — reuses the existing recommender rather than re-deriving."""
    try:
        from core.dataarch_engine.blueprint.capacity_recommend import recommend_capacity
        rec = recommend_capacity({}) or {}
        sku = rec.get("recommended_sku") or "F4"
    except Exception:                                    # recommender optional/soft
        sku = "F4"
    return _rec(
        "PLAT-CAP", "Capacity-Größe (F-SKU)", "Welche Kapazität wird beschafft?",
        (f"Mit **{sku}** starten und messen statt vorab hochzurechnen — Fabric erlaubt Skalieren im "
         "laufenden Betrieb, und Microsoft veröffentlicht keine Nutzer→SKU-Formel. Peak-CU über die "
         "Capacity-Metrics-App beobachten und bei Bedarf hochziehen. **Separat davon** die Frage der "
         "Report-Zielgruppe: sollen Nutzer *ohne* Power-BI-Pro-Lizenz konsumieren, ist **F64** nötig — "
         "das ist eine Zielgruppen-/Kostenentscheidung, keine Performance-Frage, und lässt sich kurz "
         "vor dem Rollout nachziehen."),
        "capacity_recommend (Constraint-Floor) + die Lizenz-Logik für Free-Consumer",
        "hoch",
        ["Direkt F64 kaufen (teurer, aber Free-Consumer und Headroom sofort abgedeckt)",
         "F2 als absolutes Minimum (bei mehr als sporadischer Nutzung zu knapp)"],
        "Einkauf + Plattform-Verantwortliche:r",
        "Kein Deployment möglich — Capacity ist Voraussetzung für alles Weitere",
        status="vorbelegt")


def propose_tenant_settings(bp: dict) -> dict:
    """Tenant settings — reuses admin_settings rather than listing them again here."""
    try:
        from core.dataarch_engine.blueprint import admin_settings as _adm
        req = _adm.required_settings(["base", "cicd_git", "xmla_rw"])
        n = len(req)
    except Exception:
        n = 0
    return _rec(
        "PLAT-TENANT", "Tenant-Einstellungen",
        "Welche Schalter müssen im Fabric-Admin gesetzt sein?",
        (f"Die benötigten Schalter stehen bereits fest{f' ({n} Stück)' if n else ''} und sind in "
         "`readiness/` als Prüfliste emittiert — u. a. XMLA-Read/Write, Git-Integration und die "
         "Service-Principal-Freigabe für die Admin-APIs. Vorschlag: **vor** dem Kickoff durch den "
         # Keine Aufwandsangabe. Bis 18.08.2026 stand hier „Aufwand ~0,5 PT" — eine
         # Schaetzung in kundenseitigem Text, und damit genau das, was ADR-0019 §2.4
         # ausschliesst. Gefunden hat es der Cockpit-Test `test_das_cockpit_nennt_keine_dauern`,
         # nicht ein Lesen: der Satz stand seit Monaten im Fragebogen.
         "Fabric-Admin setzen lassen und mit dem Readiness-Check verifizieren — "
         "dann blockiert am Umsetzungstag kein Schalter."),
        "admin_settings.required_settings über die genutzten Capabilities",
        "hoch",
        ["Schalter erst bei Bedarf setzen (bremst mitten in der Umsetzung)",
         "Delegation an Domänen-Admins statt zentraler Freigabe"],
        "Fabric-Admin (Tenant) — vorbereitet durch uns",
        "Deployment schlägt mitten im Lauf fehl (fehlende XMLA-/Git-/SPN-Rechte)",
        status="vorbelegt")


def propose_user_data_visibility(bp: dict) -> dict:
    """Der Tenant-Schalter „Show user data in Capacity Metrics\", als Entscheidung statt als Fussnote.

    Er haengt an `BK-B02` und ist der einzige Punkt der Ueberwachung, an dem nicht die Technik
    entscheidet. Die App zeigt mit ihm, **welche Person** welchen Bericht wie teuer ausgefuehrt hat;
    im deutschen Markt ist das eine Mitbestimmungsfrage und keine Einstellung.

    `status="offen"` mit Absicht: eine Vorbelegung waere hier eine Aussage ueber das
    Mitbestimmungsrecht des Kunden, und die steht uns nicht zu.
    """
    return _rec(
        "OPS-USERDATA", "Personenbezug in der Capacity Metrics App",
        "Darf die Kapazitätsauswertung zeigen, welche Person eine Abfrage ausgelöst hat?",
        None,
        "BK-B02 (Capacity Metrics App) — der Tenant-Schalter „Show user data in Capacity Metrics\"",
        "hoch",
        ["An lassen — die Auswertung nennt Personen; Verursacher teurer Abfragen sind sofort "
         "sichtbar, die Auswertung ist damit mitbestimmungspflichtig",
         "Aus schalten — die Auswertung nennt nur Elemente und Kapazitäten; teure Abfragen "
         "bleiben sichtbar, ihr Urheber nicht",
         "An lassen und den Zugang zur App auf einen benannten Kreis begrenzen"],
        "Datenschutz und Betriebsrat des Kunden, nicht die Plattformrolle",
        ("Der Schalter steht auf dem Auslieferungswert, und niemand hat ihn geprüft. Fällt es "
         "später auf, ist die Auswertung schon gelaufen."),
        status="offen")


def propose_sharing_policy(bp: dict) -> dict:
    """Wie weit die Plattform nach aussen offen ist — BK-Z06, und der einzige Fall im Katalog,
    in dem der Auslieferungswert **an** ist.

    Bis 20.08.2026 nannte `apply/TENANT_SETUP.md` die beiden Schalter fuer External Data Sharing
    (#11/#19) und sonst nichts; die uebrigen vier standen im Betriebskanon als Vorgabe und in
    keiner Lieferung. Der Katalog fuehrt sie jetzt (#24–#29), und diese Entscheidung erhebt die
    Politik dazu — der Kanon-Punkt verlangt genau das: *„je Schalter einzeln und mit Vermerk im
    Ledger"*.

    `vorbelegt` statt `offen`, weil der geschlossene Zustand als Haltung vertretbar ist und der
    offene nicht: wer nichts entscheidet, hat die Voreinstellung uebernommen, und die ist bei #24
    ab Werk **an** (learn.microsoft.com/fabric/admin/admin-share-power-bi-metadata-microsoft-365-
    services, geprueft 20.08.2026: „The … tenant setting is on by default").
    """
    return _rec(
        "SEC-SHARE", "Freigabe nach außen",
        "Welche Wege aus der Plattform heraus bleiben offen — Gastzugriff, Links für alle, "
        "Freigabe an Microsoft 365, öffentliche Veröffentlichung?",
        ("**Vorbelegt: geschlossen.** Wir schalten die sechs Wege nach außen ab und öffnen "
         "einzeln, was Sie brauchen:\n"
         "- **Freigabe an Microsoft 365 — der wichtigste, weil er ab Werk an ist.** Fabric "
         "meldet von sich aus Berichtsnamen, Seitennamen, Spalten- und Measure-Namen sowie "
         "Zugriffslisten an Microsoft 365, ohne dass jemand etwas tut. Der Unter-Schalter für "
         "regionsübergreifende Freigabe lässt diese Angaben zusätzlich die Region verlassen; er "
         "bleibt in jedem Fall aus.\n"
         "- **Gastzugriff** (drei Schalter: Zugang, Einladung über Freigabe-Dialoge, "
         "Weiterverwendung von Modellen im fremden Tenant) — aus, bis Sie einen Fall dafür "
         "nennen. Ist er nötig, dann über eine benannte Sicherheitsgruppe und eine geplante "
         "Einladung.\n"
         "- **„Jeder in der Organisation mit dem Link\"** — aus. Geteilt wird danach an "
         "bestimmte Personen oder an die, die ohnehin Zugriff haben.\n"
         "- **Veröffentlichung im Web** — aus. Das ist die einzige Freigabe, die ohne Anmeldung "
         "gelesen wird.\n"
         "**Offen bleibt nur:** welchen dieser Wege Sie brauchen und für wen. Ein Wechsel wirkt "
         "erst nach bis zu 24 Stunden, ist also kein Handgriff für den Umsetzungstag."),
        "BK-Z06 + admin_settings #24–#29 (learn.microsoft.com/fabric/admin/"
        "service-admin-portal-export-sharing)",
        "hoch",
        ["Alles geschlossen (Vorschlag) — Freigabe nach außen läuft über benannte Ausnahmen",
         "Gastzugriff öffnen, Rest geschlossen — üblich bei gemeinsamen Projekten mit "
         "Dienstleistern",
         "Freigabe an Microsoft 365 anlassen — Berichte werden über die Microsoft-365-Suche "
         "gefunden; die Metadaten liegen dann dort",
         "Alles auf Auslieferungswert lassen — dann ist die Freigabe an Microsoft 365 an, ohne "
         "dass jemand sie gewählt hat"],
        "Informationssicherheit und Datenschutz des Kunden, nicht die Plattformrolle",
        "Die Schalter stehen auf dem Auslieferungswert. Der Weg nach Microsoft 365 ist damit "
        "offen, und niemand hat ihn gewählt",
        status="vorbelegt")


def propose_outbound_exceptions(bp: dict) -> dict:
    """Die Ausnahmeliste der ausgehenden Sperre — die eine Haelfte von `BK-N03`, die uns nicht gehoert.

    Die Sperre selbst liefern wir (Politik-Rumpf, Vorbedingungen, Freigabewege je Workload). Welche
    Ziele danach wieder freigegeben werden, haengt an den Systemen des Kunden und wird nicht
    erfunden — bis 17.08.2026 stand das nur als Satz in der Luecke und wurde nirgends gefragt.
    """
    ziele = sorted({(e.get("source_system") or "").strip()
                    for e in bp.get("ingestion", []) or []} - {""})
    beispiel = (f" Aus dieser Lieferung sind mindestens die Quellen {', '.join(ziele)} betroffen — "
                "sie werden nach dem Blocken nicht mehr erreicht, solange sie nicht auf der Liste "
                "stehen." if ziele else
                " Diese Lieferung hat keine erklärte Quelle; die Liste beginnt leer und wächst mit "
                "dem ersten Quellsystem.")
    return _rec(
        "NET-OUTBOUND", "Ausnahmen der ausgehenden Sperre",
        "Welche Ziele darf die Plattform nach dem Blocken des ausgehenden Verkehrs noch erreichen?",
        None,
        "BK-N03 (Outbound Access Protection) — `connectivity/outbound_access_protection.json`",
        "hoch",
        ["Nur die erklärten Quellsysteme freigeben (engste Liste, jede neue Quelle braucht einen "
         "Antrag)",
         "Zusätzlich die Paketquellen der Entwicklung freigeben (PyPI, Maven, npm) — sonst "
         "scheitern Spark-Umgebungen mit eigenen Bibliotheken",
         "Sperre vorerst nur im Berichtsmodus fahren und die Liste aus dem gemessenen Verkehr "
         "bilden"],
        "Informationssicherheit des Kunden, gemeinsam mit den Eignern der Quellsysteme",
        ("Die Sperre wird scharf geschaltet und die erste Beladung schlägt fehl, ohne dass der "
         "Fehler nach einem Netzproblem aussieht." + beispiel),
        status="offen")


def propose_network_stance(bp: dict) -> dict:
    """Die Netzanbindung — als Entscheidung, nicht als Optionenliste.

    Bis 16.08.2026 stand die Netzanbindung nur als Beschreibung in `connectivity/_CONNECTIVITY.md`:
    vier Wege nebeneinander, keiner davon gewaehlt. Damit war sie die einzige Plattform-Entscheidung
    ohne Vorlage — und sie ist die am schwersten zu drehende: Private Link schaltet einzelne
    Fabric-Faehigkeiten ab, und rueckwaerts heisst „die Anbindung aller Quellen neu bauen".

    `status="vorbelegt"` mit voller Absicht, aber mit einer Besonderheit im `decider`: hier ist die
    Uebersteuerung der Normalfall. Datenschutz- oder Konzernvorgaben entscheiden das, nicht wir; die
    Vorlage sagt nur, was gilt, wenn niemand etwas verlangt.
    """
    lokal = [e for e in bp.get("ingestion", []) or []
             if (e.get("access_mode") == "mirror" or e.get("private") is True
                 or any(h in (e.get("source_system") or "").lower()
                        for h in ("on-prem", "on prem", "onprem", "gateway")))]
    gateway_satz = (
        f" Diese Lieferung hat **{len(lokal)} Quelle(n) hinter der Firewall**. Genau da wird die "
        "Frage scharf: **das On-premises-Data-Gateway laesst sich mit aktiviertem Private Link nicht "
        "einmal registrieren.** Wer beides will, braucht das VNet-Data-Gateway. Das ist eine andere "
        "Beschaffung, kein Schalter." if lokal else
        " Diese Lieferung hat keine Quelle hinter der Firewall, die Gateway-Frage stellt sich also "
        "heute nicht. Sie stellt sich beim ersten lokalen Quellsystem.")
    return _rec(
        "PLAT-NET", "Netzanbindung (öffentlich / Private Link)",
        "Wie erreichen Nutzer und Dienste die Plattform, und wie erreicht die Plattform die Quellen?",
        ("Vorschlag: **öffentliche Endpunkte plus Trusted Workspace Access** für Azure-Quellen. "
         "Trusted Workspace Access lässt einen Speicher hinter geschlossener Firewall trotzdem aus "
         "genannten Workspaces lesen, über das Microsoft-Backbone. Das ist der Sicherheitsgewinn ohne "
         "den Preis von Private Link. **Private Link wird nur auf belegte Anforderung gebaut.** Er "
         "kostet unter anderem Publish-to-Web, PDF- und PowerPoint-Export, E-Mail-Abonnements, Copilot, "
         "die Capacity-Metrics-App und tenantübergreifende Verknüpfungen. Nachträglich lässt er sich "
         "nur mit Neuaufbau der Quellanbindung drehen." + gateway_satz),
        "MS Learn: security-private-links-overview (Grenzen je Erlebnis) + security-trusted-workspace-"
        "access (F-SKU-Pflicht, kein Trial), beide geprueft 16.08.2026",
        "hoch",
        ["Private Link auf Tenant-Ebene (maximale Abschottung, höchster Funktionsverlust)",
         "Private Link nur auf Workspace-Ebene (feiner, nur die Workspaces mit echter Anforderung)",
         "IP-Firewall-Regeln je Workspace (bis 256 Regeln, läuft auch auf Trial)"],
        "Informationssicherheit / Konzern-IT — hier entscheidet die Vorgabe des Kunden, nicht wir",
        ("Die Anbindung wird zweimal gebaut: einmal öffentlich, und nach der ersten Prüfung durch "
         "die Sicherheit noch einmal privat."),
        status="vorbelegt")


# -- I-21: Entscheidungen aus Kundeninput nach der FabCon Europe 2026 (30.09.2026) -----------
#
# Fuenf Plattformfragen, deren Antwort sich mit den Meldungen der FabCon verschoben hat. Jede
# liest nur Felder, die der Bauplan schon fuehrt; was er nicht fuehrt (KI-Richtlinie,
# Eingaben im Bericht, Lizenzbasis), steht als Frage in der Vorlage und wird nicht vermutet
# (D-340). Ein Entscheidungsmodell mit eigenen Eingabefeldern daneben waere eine zweite
# Wahrheit neben dem Bauplan gewesen; deshalb sitzen die Regeln hier.

# Fabric-App-Regionen: eine Quelle, `stack_capabilities.FEATURE_NICHT_IN["fabric_apps"]`. Bis
# 01.10.2026 stand hier eine eigene Sperrliste mit genau `germanywestcentral` -- zwei Tage nach
# dem Lesen war sie falsch (Learn hat die Region am 29.09. abends freigegeben), und nichts las sie
# gegen die Tabelle daneben.


def _regionen(bp: dict) -> set[str]:
    """Alle Zielregionen des Bauplans, normalisiert (`Germany West Central` -> `germanywestcentral`)."""
    plat = bp.get("platform") or {}
    roh = [(plat.get("sizing") or {}).get("region")]
    roh += [c.get("region") for c in plat.get("capacities") or [] if isinstance(c, dict)]
    return {str(r).lower().replace(" ", "") for r in roh if r}


def propose_mirror_security(bp: dict) -> dict:
    """Rechte gespiegelter Quellen. Mirroring nimmt RLS, CLS und Maskierung der Quelle nicht mit.

    Wie `PLAT-NET` immer da, auch ohne Spiegel: dann vorbelegt mit dem Satz, der beim ersten
    Spiegel gilt. Eine Entscheidung, die nur bei Bedarf erscheint, fehlt genau in dem Workshop,
    in dem jemand den ersten Spiegel vorschlaegt.
    """
    gespiegelt = [e for e in bp.get("ingestion", []) or [] if e.get("access_mode") == "mirror"]
    vertraulich = [e for e in gespiegelt if e.get("sensitivity") in ("confidential", "restricted")]
    namen = ", ".join(f"`{e.get('source')}`" for e in (vertraulich or gespiegelt))
    if not gespiegelt:
        vorschlag = ("Diese Lieferung spiegelt keine Quelle, die Frage stellt sich heute nicht. Beim "
                     "ersten Spiegel gilt: **die Rechte der Quelle als OneLake-Security-Rollen neu "
                     "aufbauen**, weil Mirroring sie nicht mitnimmt.")
        status, konfidenz = "vorbelegt", "hoch"
    else:
        vorschlag = (f"**Die Rechte als OneLake-Security-Rollen neu aufbauen** für {namen}. Mirroring "
                     "übernimmt Zeilen- und Spaltenrechte sowie die Maskierung der Quelle nicht; ohne "
                     "Neuaufbau liest jeder Leser des gespiegelten Items alle Zeilen. OneLake "
                     "Security ist GA seit Mai 2026; Rollen auf gespiegelten Datenbanken und "
                     "Katalogen erlauben nur Read. ReadWrite gibt es nur im Lakehouse, und eine "
                     "ReadWrite-Rolle darf kein RLS/CLS tragen. Wer vor dem Lesen schreiben oder "
                     "transformieren muss, kopiert stattdessen in ein gesteuertes Lakehouse."
                     + ("" if vertraulich else
                        " Keine gespiegelte Quelle ist als vertraulich markiert; ob sie Rechte trägt, "
                        "weiß nur ihr Eigentümer."))
        status, konfidenz = "offen", ("hoch" if vertraulich else "mittel")
    return _rec(
        "SEC-MIRROR", "Rechte bei gespiegelten Quellen",
        "Tragen die gespiegelten Quellen Zeilen-, Spaltenrechte oder Maskierung, und wie gelten sie "
        "in Fabric?",
        vorschlag,
        f"{len(gespiegelt)} Quelle(n) mit access_mode `mirror`, davon {len(vertraulich)} vertraulich; "
        "MS Learn: mirroring/azure-sql-database-how-to-data-security, onelake/security/"
        "data-access-control-model (gelesen 01.10.2026)",
        konfidenz,
        ["In ein gesteuertes Lakehouse kopieren und dort absichern (Kopie statt Spiegel)",
         "Nur Tabellen ohne schutzbedürftige Inhalte spiegeln, den Rest kopieren"],
        "Quelleigentümer:in + Informationssicherheit",
        "Jeder Leser des gespiegelten Items sieht alle Zeilen, auch die, die die Quelle schützt.",
        status=status)


def propose_monitoring_topology(bp: dict) -> dict:
    """Workspace-Monitoring: wo die Betriebsdaten landen, und ob eine KI darin sucht.

    `offen` trotz Vorschlag, weil zwei Festlegungen nur bei der Anlage moeglich sind (eigener
    Endpoint; der Operations Agent laesst sich nach Aktivierung nicht abschalten) und die
    KI-Untersuchungen ab Werk an sind. Eine Vorbelegung haette hier eine KI-Richtlinie des
    Kunden unterstellt.
    """
    # D-596: eine Kapazitaet mit Stufen, aber ohne `prod`, ist die Nicht-Produktionskapazitaet.
    # 01.10.2026: Learn empfiehlt eine eigene Kapazitaet fuer das zentrale Monitoring-Eventhouse;
    # die Nicht-Produktionskapazitaet ist die guenstigere Alternative mit benanntem Nachteil.
    getrennt = any(isinstance(c, dict) and c.get("stages") and "prod" not in c["stages"]
                   for c in (bp.get("platform") or {}).get("capacities") or [])
    alternative = ("die vorhandene Nicht-Produktionskapazität" if getrennt else
                   "die Nicht-Produktionskapazität, sobald es sie gibt (D-596)")
    from core.dataarch_engine.blueprint.kapazitaet_stufen import monitoring_kapazitaet
    mon = monitoring_kapazitaet(bp)
    benannt = (f" Der Bauplan nennt sie bereits: `{mon.get('name') or 'ohne Namen'}`"
               f"{' (' + str(mon['sku']) + ')' if mon.get('sku') else ''}." if mon else
               " Im Bauplan als Kapazität mit `purpose: monitoring` eintragen.")
    return _rec(
        "OPS-MONITORING", "Workspace-Monitoring (vor der Anlage entscheiden)",
        "Zentrales oder dezentrales Workspace-Monitoring, KI-Untersuchungen an oder aus, eigener "
        "Endpoint?",
        ("**Ein zentrales Monitoring-Eventhouse** in einem eigenen Workspace auf einer **eigenen, "
         "kleinen Kapazität**, wie Learn es empfiehlt: Drosselung einer Arbeitskapazität trifft die "
         "Überwachung dann nicht, und die Überwachung belastet keine Arbeitskapazität."
         + benannt + " Günstiger ist "
         f"{alternative}; dann werden Berichte und Activator-Alarme auf den Monitoring-Daten "
         "mitgedrosselt, wenn Dev/Test gedrosselt ist (Ingestion und Abfragen laufen weiter). "
         "Alarme an die Rollen-Postfächer aus OPS-ALERT. **Vor der Anlage** entscheiden: den eigenen Endpoint "
         "gibt es nur bei der Anlage, ein aktivierter Operations Agent lässt sich nicht "
         "abschalten, und die KI-Untersuchungen sind ab Werk an. Sie bleiben aus, bis die "
         "KI-Richtlinie des Kunden sie freigibt. Activator-Alarme je Jobtyp kosten CU; nur die "
         "Jobtypen wählen, auf die jemand reagiert."),
        "MS Learn: fundamentals/enable-workspace-monitoring (Recommended architecture, gelesen "
        "01.10.2026), fundamentals/workspace-monitoring-overview (Verhalten bei Drosselung), "
        "admin/monitoring-hub-alerts; D-596 Kapazität je Umgebung",
        "mittel",
        ["Zentrales Eventhouse auf der Nicht-Produktionskapazität (keine weitere Kapazität, "
         "Berichte und Alarme darauf werden mit Dev/Test gedrosselt)",
         "Monitoring je Workspace (jeder Eigentümer sieht nur seinen Betrieb)",
         "Kein Monitoring-Item, nur Monitor hub und Capacity Metrics"],
        "Plattform-Verantwortliche:r + KI-Verantwortliche:r des Kunden",
        "Es wird kein Monitoring-Item angelegt. Fehler fallen im Monitor hub auf, ohne eigene "
        "Abfragen und ohne Historie über dessen Fenster hinaus.",
        status="offen")


def propose_overage(bp: dict) -> dict:
    """Capacity Overage je Kapazitaet. Ab Werk an, zum dreifachen PAYG-Satz.

    Vorbelegt erst, wenn jede benannte Kapazitaet `overage` fuehrt - dann ist entschieden,
    und die Vorlage sagt nur noch, was gilt. Das Feld und die P4-Warnung gibt es seit W1.1.
    """
    caps = [c for c in (bp.get("platform") or {}).get("capacities") or []
            if isinstance(c, dict) and c.get("name")]
    offen = [c["name"] for c in caps if not c.get("overage")]
    if caps and not offen:
        stand = ", ".join(f"`{c['name']}`: {c['overage'].get('state')}" for c in caps)
        vorschlag, status = f"**Festgelegt je Kapazität:** {stand}.", "vorbelegt"
    else:
        vorschlag = (
            "**Overage nur auf der Produktionskapazität, mit Schwelle unter einem Drittel der "
            "Tages-CU-Stunden** (SKU-CU x 24 / 3); auf der Nicht-Produktionskapazität aus. "
            "Overage ist bei neuen F-Kapazitäten ab Werk an (Schwelle 25 %) und kauft zum "
            "dreifachen PAYG-Satz zu. Die Schwelle ist keine harte Kostengrenze: geprüft wird alle "
            "fünf Minuten, laufende Operationen werden weiter abgerechnet."
            + (f" Ohne Festlegung: {', '.join(f'`{n}`' for n in offen)}." if offen else ""))
        status = "offen"
    return _rec(
        "PLAT-OVERAGE", "Capacity Overage je Kapazität",
        "Kauft die Kapazität bei Lastspitzen CU zu, und bis zu welcher Schwelle?",
        vorschlag,
        "platform.capacities[].overage (I-21 W1.1); MS Learn: enterprise/capacity-overage-overview "
        "(gelesen 29.09.2026)",
        "hoch",
        ["Overage überall aus, Drosselung wird akzeptiert",
         "Größere SKU statt Overage (planbar, bezahlt die Spitze dauerhaft)"],
        "Einkauf + Plattform-Verantwortliche:r",
        "Overage bleibt ab Werk an (Schwelle 25 %). Lastspitzen werden zum dreifachen PAYG-Satz "
        "zugekauft, ohne dass es jemand bestellt hat.",
        status=status)


#: Ab dieser F-SKU lesen Berichtskonsumenten ohne eigene Pro-Lizenz (Learn
#: `enterprise/licenses`: Inhalte auf F64 und groesser sind fuer Free-Nutzer lesbar). Autoren
#: brauchen Pro immer. Dieselbe Grenze fuehrt ALUCA als `capacity.FREE_VIEWER_MIN_SKU`.
FREE_VIEWER_MIN_F = 64


def _produktions_sku(bp: dict) -> str | None:
    """Die SKU, auf der Produktion laeuft: eine Kapazitaet mit `prod` in `stages` oder ohne
    Stufenangabe (D-596), sonst `platform.capacity_sku`. Bei mehreren die groesste."""
    plat = bp.get("platform") or {}
    kandidaten = [c.get("sku") for c in plat.get("capacities") or []
                  if isinstance(c, dict) and c.get("sku")
                  and (not c.get("stages") or "prod" in c["stages"])]
    if not kandidaten and plat.get("capacity_sku"):
        kandidaten = [plat["capacity_sku"]]
    rang = [(int(m.group(1)), str(k)) for k in kandidaten
            if (m := re.fullmatch(r"[Ff](\d+)", str(k).strip()))]
    return max(rang)[1].upper() if rang else None


def _lizenz_satz(bp: dict) -> str:
    sku = _produktions_sku(bp)
    if sku is None:
        return (" **Lizenz:** Die Produktionskapazität ist nicht benannt. Unter F64 braucht jede "
                "Person, die einen Bericht liest, Power BI Pro oder PPU; ab F64 lesen "
                "Konsumenten ohne eigene Lizenz.")
    if int(sku[1:]) >= FREE_VIEWER_MIN_F:
        return (f" **Lizenz:** Auf {sku} lesen Konsumenten ohne eigene Lizenz; Autoren brauchen "
                "Power BI Pro.")
    return (f" **Lizenz:** Auf {sku} braucht jede Person, die einen Bericht liest, Power BI Pro "
            "oder PPU. Ab F64 entfällt das; bei vielen Lesern ist das die Rechnung, die "
            "PLAT-CAP entscheidet.")


def propose_report_target(bp: dict) -> dict:
    """Report-Ziel: PBIR, Fabric App oder beides. Region und Lizenzbasis entscheiden mit."""
    from core.dataarch_engine.blueprint.stack_capabilities import feature_in_region
    regionen = _regionen(bp)
    gesperrt = sorted(r for r in regionen if feature_in_region("fabric_apps", r) == "fehlt")
    if gesperrt:
        vorschlag = (f"**PBIR.** Fabric Apps sind in {', '.join(gesperrt)} laut Learn nicht "
                     "verfügbar. Braucht der Kunde Eingaben oder Rückschreiben, ist die Region "
                     "selbst die Entscheidung." + _lizenz_satz(bp))
        konfidenz = "hoch"
    else:
        vorschlag = ("**PBIR für die Analyse**, eine Fabric App nur dort, wo Nutzer Werte eingeben "
                     "oder zurückschreiben (Rückschreiben in eine Fabric SQL Database, keine anonyme "
                     "Rolle). Fabric Apps sind Preview; der Weg über Pro/PPU ohne Kapazität ist "
                     "angekündigt, aber nicht dokumentiert."
                     + ("" if regionen else
                        " Die Zielregion steht nicht im Bauplan; vor einer App klären.")
                     + _lizenz_satz(bp))
        konfidenz = "mittel"
    return _rec(
        "OUT-REPORT", "Report-Ziel: PBIR, Fabric App oder beides",
        "Brauchen Nutzer Eingaben, Rückschreiben oder Workflows im Bericht, und auf welcher "
        "Lizenzbasis?",
        vorschlag,
        "platform.sizing.region / platform.capacities[].region, Produktions-SKU aus "
        "platform.capacities[].sku (D-596) bzw. platform.capacity_sku; MS Learn: "
        "admin/region-availability (gelesen 01.10.2026), "
        "power-bi/create-reports/fabric-apps-analytics, enterprise/licenses (gelesen 29.09.2026)",
        konfidenz,
        ["Fabric App mit Eingaben, Rückschreiben und Workflows (Preview, nicht in jeder Region)",
         "PBIR für die Analyse, Fabric App nur für die Eingabe"],
        "Fachbereich (Eingaben ja oder nein) + Einkauf (Lizenzbasis)",
        "Wir bauen reine Berichte. Eingaben und Rückschreiben kommen später als eigene Anwendung "
        "dazu.",
        status="offen")


def propose_de_copilot(bp: dict) -> dict:
    """KI-Assistenz im Data Engineering: Data engineering agent (Project Osmos, Preview).

    Auf Learn seit September 2026 (`data-engineering/data-engineering-agent-get-started`),
    auf der FabCon Europe 2026 vorgestellt. Die Messung gegen die Meridian-Emitter ist W2.5;
    bis dahin ist die Empfehlung eine Grenze (nicht in Produktion), keine Bewertung.

    Kundeninput ist `platform.ai_zugang` (D-606): fehlt `fabric_copilot` in einer angegebenen
    Liste, ist der Weg nicht freigegeben und die Empfehlung heisst "nicht verwenden". Ohne
    Angabe (oder `unbekannt`) bleibt die Hausempfehlung stehen, und die Freigabe ist die
    Vorbedingung.
    """
    werte = {str(w) for w in (bp.get("platform") or {}).get("ai_zugang") or []}
    grenze = ("Code, den der Agent erzeugt, durchläuft dieselben Prüfungen wie handgeschriebener: "
              "Tests, Review, CI/CD. In Workspaces mit Outbound Access Protection läuft der Agent "
              "laut Learn nicht. **Der Agent ist Preview**; ob sein Ergebnis unseren Standards "
              "entspricht, messen wir vor einer Freigabe.")
    if werte and werte != {"unbekannt"} and "fabric_copilot" not in werte:
        vorschlag = ("**Nicht verwenden.** `platform.ai_zugang` gibt Fabric Copilot nicht frei "
                     f"({', '.join(sorted(werte))}); der Data engineering agent ist ein Copilot-Weg.")
        konfidenz = "hoch"
    else:
        vorschlag = ("**Nur in Entwicklung und Test**, auf der Nicht-Produktionskapazität (D-596). "
                     + grenze
                     + ("" if "fabric_copilot" in werte else
                        " **Vorbedingung:** der KI-Zugangsweg `fabric_copilot` (D-606) ist noch "
                        "nicht freigegeben; ohne ihn bleibt der Agent aus."))
        konfidenz = "hoch" if "fabric_copilot" in werte else "mittel"
    return _rec(
        "AI-DE-COPILOT", "KI-Assistenz im Data Engineering (Project Osmos)",
        "Darf der Data engineering agent beim Bau der Datenstrecken mitarbeiten, und in welchen "
        "Umgebungen?",
        vorschlag,
        "platform.ai_zugang (D-606); MS Learn: data-engineering/data-engineering-agent-get-started "
        "(Preview, gelesen 29.09.2026), fundamentals/copilot-fabric-overview",
        konfidenz,
        ["Nicht verwenden", "Auch in Produktions-Workspaces (an der Release-Kontrolle vorbei)"],
        "KI-Verantwortliche:r + Datenschutz des Kunden",
        "Der Assistent bleibt aus. Gebaut wird wie bisher.",
        status="offen")


def propose_purview(bp: dict) -> dict:
    """Purview als Andock-Modul (D-620): der OneLake catalog ist die Vorgabe.

    Liest `governance.purview` direkt und nicht ueber `provision_purview`: dieses Modul wird
    byte-identisch nach ALUCA gespiegelt, und die Vorlage soll nicht an einem zweiten Modul
    haengen. Fehlt das Feld oder steht `nein`, ist die Hausvorgabe angewandt (vorbelegt);
    `unbekannt` ist die offene Kundenfrage; `ja` nennt die gewaehlten Bausteine.
    """
    pv = (bp.get("governance") or {}).get("purview") or {}
    stand = pv.get("im_umfang") or "nein"
    teile = [b for b in pv.get("bausteine") or []]
    if stand == "ja":
        vorschlag = ("**Purview im Umfang:** "
                     + (", ".join(f"`{b}`" for b in teile) if teile else "keine Bausteine benannt")
                     + ". Die Pakete liegen unter `governance/purview/`; der OneLake catalog bleibt "
                     "die Oberfläche für Fabric-Elemente.")
        status, konfidenz = "vorbelegt" if teile else "offen", "hoch" if teile else "mittel"
    elif stand == "unbekannt":
        vorschlag = ("**OneLake catalog trägt die Governance**, Purview dockt bei Bedarf an. Ob ein "
                     "Purview-Konto oder E5-Lizenzen vorhanden sind, steht nicht im Bauplan.")
        status, konfidenz = "offen", "mittel"
    else:
        vorschlag = ("**OneLake catalog trägt die Governance** (Domänen, Endorsement, "
                     "Beschreibungen, Lineage); Purview ist nicht im Umfang. Die Andockpunkte stehen "
                     "in `governance/purview/_PURVIEW.md`.")
        status, konfidenz = "vorbelegt", "hoch"
    return _rec(
        "GOV-CATALOG", "Purview als Andock-Modul",
        "Gehört Microsoft Purview zum Umfang, und welche Bausteine (Labels, DLP, Data Map, "
        "Unified Catalog, Audit)?",
        vorschlag,
        "governance.purview (D-620); MS Learn: fabric/governance/onelake-catalog-overview, "
        "purview/dlp-powerbi-get-started (gelesen 01.10.2026)",
        konfidenz,
        ["Labels und DLP für Power BI und Fabric", "Purview vollständig mit Data Map und Unified Catalog"],
        "Governance-Verantwortliche:r + Einkauf (Lizenzen)",
        "Der OneLake catalog trägt die Governance; Purview lässt sich später ohne Umbau anschließen.",
        status=status)


def propose_ground_truth(gc: dict) -> dict:
    """Evaluation ground truth for the Data Agent — derivable as question skeletons."""
    ms = [m["measure_name"] for m in gc.get("measures", []) if m.get("measure_name")][:4]
    if not ms:
        return _rec("AI-EVAL", "Ground-Truth für die Agent-Bewertung",
                    "Woran misst man, ob der Data Agent richtig antwortet?", None,
                    "keine governten Kennzahlen im Katalog", "keine",
                    ["Fragen mit dem Fachbereich sammeln"], "Data Owner + Fachbereich",
                    "Der Agent wird ohne Qualitätsnachweis produktiv gesetzt")
    dims = [t["name"] for t in gc.get("tables", []) if t.get("kind") == "dimension"][:3]
    ex = f"„Wie hoch ist {ms[0]}" + (f" je {dims[0]}?“" if dims else "?“")
    return _rec(
        "AI-EVAL", "Ground-Truth für die Agent-Bewertung",
        "Woran misst man, ob der Data Agent richtig antwortet?",
        (f"Fragen-Gerüst aus den governten Kennzahlen × Dimensionen vorbefüllen — z. B. {ex} "
         f"(Kennzahlen: {', '.join(ms)}). Die **Fragen** generieren wir, die **erwarteten Antworten** "
         f"muss der Fachbereich einmalig bestätigen; danach läuft die Bewertung automatisch. "
         f"Vorschlag: 15–25 Fragen, die die häufigsten Report-Fragen abdecken — das reicht für einen "
         f"belastbaren Qualitätswert."),
        f"{len(gc.get('measures', []))} governte Kennzahl(en) im Katalog",
        "mittel",
        ["Ohne Bewertung live gehen (kein Qualitätsnachweis)",
         "Nur stichprobenhaft manuell prüfen (nicht reproduzierbar)"],
        "Fachbereich (Antworten) + Data Owner (Freigabe)",
        "Der Agent wird ohne Qualitätsnachweis produktiv gesetzt")


# --- aggregation + rendering ------------------------------------------------------------------------

def propose_clustering_columns(bp: dict, gc: dict) -> dict | None:
    """Liquid-Clustering-**Spalten** je großer Tabelle — offen, weil nur der Kunde sie kennt.

    Wichtige Trennung, die eine Recherche gegen `learn.microsoft.com/fabric/fundamentals/
    table-maintenance-optimization` (30.07.2026) erzwungen hat: die **Technik** ist dort
    dokumentierte Empfehlung (Silber „Yes", Gold „Required for optimal file skipping") und gehört
    damit ausgesagt, nicht gefragt. Die **Spalten** sind das Gegenteil — sie folgen aus den
    Filterprädikaten der echten Abfragen, und die kennt nur der Fachbereich. Sie zu raten würde die
    Tabelle für ein Zugriffsmuster reorganisieren, das niemand hat.

    Nur auf Stacks mit Delta-Wartung sinnvoll; auf Snowflake übernimmt Automatic Clustering.
    """
    stack = str((bp.get("platform") or {}).get("stack") or "fabric")
    if stack not in ("fabric", "databricks"):
        return None
    tables = sorted({str(t.get("name")) for t in (gc.get("tables") or []) if t.get("name")})
    if not tables:
        return None
    return _rec(
        "DATA-CLUSTER", "Liquid-Clustering-Spalten",
        ("Nach welchen Spalten filtern die echten Abfragen? Danach richtet sich das Clustering "
         f"({len(tables)} Tabelle(n) betroffen)."),
        None,
        ("die Technik ist belegt (MS Learn: Silber empfohlen, Gold erforderlich), die Spalten stehen "
         "in keiner ableitbaren Quelle — sie folgen aus dem Abfrageverhalten"),
        "keine",
        ["ohne Clustering starten und nach ersten echten Abfragen nachziehen",
         "bei partitionierten Tabellen stattdessen Z-Order (Liquid Clustering greift dort nicht)"],
        "Data Owner (Abfrageverhalten) + Data Engineering",
        ("Die Tabellen bleiben ohne Clustering — zulässig, aber Direct-Lake- und SQL-Abfragen lesen "
         "mehr Dateien als nötig."),
        markers=("decide",),
    )

def propose_platform_tier(bp: dict) -> dict | None:
    """Editions-/Plan-Stufe des Zielstacks — die Achse, an der auf Nicht-Fabric fast alles hängt.

    Bewusst **kein** Vorschlag und **nicht** vorbelegt: eine Stufe ist eine Tatsache über die
    Kundenumgebung (und ein Vertragsgegenstand), die sich aus keinem Modell ableiten lässt. Der
    Hausstandard-Trick, mit dem andere Punkte vorbelegt werden, wäre hier eine Behauptung.

    Auf Fabric entfällt der Punkt: dort ist die Kapazität die Achse (siehe ``PLAT-CAP``).
    """
    from core.dataarch_engine.blueprint.stack_capabilities import tiers_for

    platform = bp.get("platform") or {}
    stack = str(platform.get("stack") or "fabric")
    valid = tiers_for(stack)
    if not valid:
        return None
    assigned = str(platform.get("tier") or "").strip().lower()
    if assigned:
        return None                     # beantwortet — nichts mehr zu entscheiden
    return _rec(
        "PLAT-TIER", f"Editions-/Plan-Stufe ({stack})",
        gap=(f"Die Stufe ist unbekannt. Sie entscheidet, welche Mechanismen überhaupt verfügbar "
             f"sind — auf Snowflake hängen Replication/Failover und Private Connectivity an Business "
             f"Critical, Time Travel über 1 Tag an Enterprise, Zeilen-/Spalten-Sicherheit an "
             f"Enterprise; auf Databricks hängt Predictive Optimization am Premium-Plan. Solange die "
             f"Stufe fehlt, machen die Fähigkeits-Hinweise der Lieferung keine Zusage."),
        proposal=None,
        derived_from="platform.stack (die Stufe selbst steht in keiner ableitbaren Quelle)",
        confidence="keine",
        alternatives=[f"`{v}`" for v in valid],
        decider="Plattform-Verantwortliche:r + Einkauf (Vertragsgegenstand)",
        if_undecided=("Die Lieferung bleibt bei benannten Mechanismen ohne Zusage; RPO/RTO, privater "
                      "Netzpfad und Wartungsmodell sind dann nicht zusagbar."),
    )

#: Der Trenner, mit dem `propose_all` eine Entscheidung je Domaene aufspannt.
FANOUT_TRENNER = "\u00b7"

#: Die fuenf Vorlagen, die das Gold-Modell lesen — als Liste, nicht als Merksatz.
#:
#: Bis 18.08.2026 stand diese Menge an drei Stellen: im Fliesstext des Modul-Docstrings oben,
#: als lokale Variable `per_domain` in `propose_all` und als handgetippte Konstante
#: `_MODELLGETRIEBEN` im Test. Drei Kopien einer Menge, die waechst, sobald jemand eine sechste
#: modellgetriebene Vorlage schreibt — und zwei davon haetten es nicht gemerkt.
#:
#: `propose_all` liest jetzt diese Liste, `modellgetriebene_ids()` leitet die IDs daraus ab,
#: und der Ledger fragt beide, statt eine vierte Kopie anzulegen.
MODELLGETRIEBENE_VORLAGEN = (propose_rls, propose_cls, propose_incremental,
                             propose_silver_contract, propose_ground_truth)

#: Von diesen liest ein Teil zusaetzlich die Quell-Introspektion und nimmt deshalb zwei
#: Argumente. Die Unterscheidung gehoert neben die Liste, sonst ruft der naechste Aufrufer
#: falsch auf.
_MIT_QUELLE = (propose_rls, propose_cls, propose_incremental)


def modellgetriebene_ids() -> frozenset[str]:
    """Die Basis-IDs der modellgetriebenen Vorlagen — gefragt statt getippt.

    Die ID steht im `_rec`-Aufruf jeder Vorlage; sie hier noch einmal aufzuschreiben hiesse,
    eine Umbenennung an zwei Stellen nachziehen zu muessen. Stattdessen wird jede Vorlage
    einmal mit leerem Katalog aufgerufen — deterministisch, ohne Seiteneffekt, und genau der
    Lauf, den `propose_all` ohnehin macht.

    „Basis"-ID, weil `propose_all` bei mehreren Domaenen auf `SEC-RLS·sales` faechert. Wer die
    Zugehoerigkeit pruefen will, schneidet am Trenner ab — siehe `wartet_auf_modell`.
    """
    return frozenset(
        (fn({}, None) if fn in _MIT_QUELLE else fn({}))["id"]
        for fn in MODELLGETRIEBENE_VORLAGEN
    )


def basis_id(decision_id: str) -> str:
    """`SEC-RLS·sales` → `SEC-RLS`. Eine Stelle, weil der Trenner sonst mitwandert."""
    return str(decision_id).split(FANOUT_TRENNER, 1)[0]


def domain_slug(name: str) -> str:
    """`Order to Cash` → `order-to-cash`: das Domaenenstueck der aufgefaecherten ID.

    Oeffentlich seit C-3 (02.09.2026), weil die Emission dieselbe ID bilden muss wie
    `propose_all`, um eine Entscheidungsantwort (`DATA-INC·order-to-cash`) ihrer Domaene
    zuzuordnen. Zwei Slug-Regeln an zwei Stellen waeren die naechste stille Abweichung.
    """
    return _NONWORD_RE.sub("-", (name or "").lower()).strip("-")


def entscheidung_fuer(entscheidungen: dict | None, basis: str, domain_name: str) -> str | None:
    """Der gewaehlte Wert einer Entscheidung fuer diese Domaene — oder ``None``.

    Liest zuerst die aufgefaecherte ID (`<basis>·<slug>`), dann die Basis-ID (ein Lauf mit
    einer Domaene faechert nicht). Die Ledger-ID ist der Vertrag; wer hier einen dritten
    Schluessel einfuehrt, bricht den Rueckweg aus der Antwortdatei.
    """
    if not entscheidungen:
        return None
    for key in (f"{basis}{FANOUT_TRENNER}{domain_slug(domain_name)}", basis):
        wert = entscheidungen.get(key)
        if wert not in (None, ""):
            return str(wert)
    return None


def wartet_auf_modell(p: dict) -> bool:
    """Diese Entscheidung schweigt, weil das Gold-Modell fehlt — nicht, weil es nichts zu sagen gibt.

    Der Unterschied ist der ganze Zweck der Funktion. `NET-OUTBOUND` und `OPS-USERDATA` tragen
    ebenfalls keinen Vorschlag, und zwar dauerhaft: ihr Inhalt steckt in den Alternativen, kein
    Modell der Welt aendert daran etwas. `PLAT-TIER` traegt sogar `confidence: "keine"` und ist
    trotzdem eine Kundentatsache (ein Vertragsgegenstand) — der Hausstandard-Trick waere dort
    eine Behauptung.

    Gemessen 18.08.2026, deshalb steht hier die Zugehoerigkeit und nicht `confidence == "keine"`:
    auf Fabric waehlt die Konfidenz zufaellig genau die fuenf richtigen, auf Snowflake und
    Databricks nimmt sie `PLAT-TIER` mit, und `DATA-CONTRACT` behaelt sie dort **auch mit**
    Katalog. Ein Praedikat, das auf einem Stack stimmt und auf zweien nicht, ist keins.
    """
    return basis_id(p.get("id", "")) in modellgetriebene_ids() and not p.get("proposal")


def propose_all(bp: dict, governed_catalog: dict | None = None,
                source_schema: dict | None = None) -> list[dict]:
    """Every open decision with its pre-thought proposal, deterministic order.

    A customer has many use cases, and the model-driven decisions (RLS axis, sensitive columns,
    incremental strategy, silver contract, agent ground truth) are genuinely decided **per domain** —
    Sales may scope by region while Finance scopes by company code. So with more than one domain those
    fan out to one record per domain (``SEC-RLS·<domain>``), each derived from that domain's slice of
    the catalog. The platform decisions (capacity, tenant settings, alerts, endorsement, retention)
    stay tenant-wide, because that is what they actually are.

    ``source_schema`` ist die zweite Tatsachenquelle: die Introspektionsergebnisse, um die wir
    den Kunden per ``--source-schema-results`` bitten. Drei der modellgetriebenen Vorlagen
    lesen sie mit (RLS, CLS, inkrementelles Laden); je Domaene bekommt jede nur die Quellen,
    die in diese Domaene laden. Ohne die Zuleitung stand in der Vorlage „kein Vorschlag",
    waehrend die Antwort des Kunden im selben Lauf auf der Platte lag."""
    gc = governed_catalog or {}
    domains = sorted(bp.get("mesh", {}).get("domains", []), key=lambda d: d.get("name", ""))
    #: Vorlagen, die neben dem Katalog auch die Quell-Introspektion lesen. Die uebrigen
    #: (Silber-Vertrag, Agent-Pruefgrundlage) haengen an Beziehungen und Kennzahlen — die
    #: gibt INFORMATION_SCHEMA nicht her, und sie zu behaupten waere geraten.
    mit_quelle = _MIT_QUELLE
    per_domain = list(MODELLGETRIEBENE_VORLAGEN)
    out: list[dict] = []
    if len(domains) > 1 and gc.get("tables"):
        for d in domains:
            dgc = _domain_catalog(gc, d)
            slug = domain_slug(d.get("name") or "")
            dq = _quell_schnitt(bp, source_schema, d)
            if not dgc.get("tables"):
                # **Der Riss aus OQ-39, geschlossen** (D-516). Hier stand `continue`: eine
                # Domaene, zu der der governte Katalog keine Tabelle fuehrt, bekam keine
                # einzige modellgetriebene Entscheidung. **Die Emission schreibt fuer sie
                # aber trotzdem `silver_to_gold`-SQL mit `<business_key>` und
                # `<watermark_col>`** — gemessen am Commercial-Fixture: `finance` trug
                # Platzhalter und hatte keine Frage.
                #
                # Aufgefaechert wird deshalb `DATA-INC` **auch ohne Katalogtabelle**, und
                # zwar in seiner Fassung „kein Vorschlag": die Frage steht, der Vorschlag
                # fehlt, und das ist die Wahrheit. Ein Platzhalter erzeugt seine Frage.
                #
                # **Nur `DATA-INC`, nicht alle fuenf.** Ob RLS, CLS, Silber-Vertrag und
                # Pruefgrundlage ohne Katalog ebenfalls Artefakte mit Platzhaltern
                # erzeugen, ist **nicht gemessen** — und eine Faecherung auf Verdacht
                # waere dieselbe Behauptung mit anderem Vorzeichen (OQ-39 bleibt dafuer
                # offen).
                r = propose_incremental(dgc, dq)
                r["id"] = f"{r['id']}{FANOUT_TRENNER}{slug}"
                r["topic"] = f"{r['topic']} — {d.get('name')}"
                out.append(r)
                continue
            for fn in per_domain:
                r = fn(dgc, dq) if fn in mit_quelle else fn(dgc)
                r["id"] = f"{r['id']}{FANOUT_TRENNER}{slug}"
                r["topic"] = f"{r['topic']} — {d.get('name')}"
                out.append(r)
    else:
        out.extend(fn(gc, source_schema) if fn in mit_quelle else fn(gc) for fn in per_domain)
    if len(domains) > 1 and gc.get("tables"):
        out.extend(propose_cross_domain(bp, gc))   # domains are not islands
    out.extend([propose_workspace_roles(bp), propose_domain_roles(bp),
                propose_retention(bp, gc, source_schema),
                propose_alerts(bp),
                propose_endorsement(bp, gc), propose_capacity(bp), propose_tenant_settings(bp),
                propose_network_stance(bp), propose_outbound_exceptions(bp),
                propose_sharing_policy(bp),
                propose_user_data_visibility(bp),
                propose_lakehouse_schemas(bp), propose_lakehouse_topology(bp),
                propose_transform_engine(bp), propose_silver_load(bp),
                # I-21 (FabCon Europe 2026, 30.09.2026)
                propose_mirror_security(bp), propose_monitoring_topology(bp),
                propose_overage(bp), propose_report_target(bp), propose_de_copilot(bp),
                propose_purview(bp)])
    _tier = propose_platform_tier(bp)      # nur auf Stacks mit Stufen-Achse und nur solange offen
    if _tier:
        out.append(_tier)
    _cluster = propose_clustering_columns(bp, gc)
    if _cluster:
        out.append(_cluster)
    _sprache = propose_text_language(gc)
    if _sprache:
        out.append(_sprache)
    return out


def decisions_markdown(proposals: list[dict]) -> str:
    """The workshop decision template: every open point with a proposal ready to confirm or adjust."""
    withp = [p for p in proposals if p.get("proposal")]
    pre = [p for p in proposals if p.get("status") == "vorbelegt"]
    open_ = [p for p in proposals if p.get("status") != "vorbelegt"]
    lines = [
        "# Entscheidungsvorlage — vorbelegt und wirklich offen", "",
        f"**{len(proposals)} Entscheidungen**, davon **{len(pre)} bereits vorbelegt** (Hausstandard bzw. "
        f"Least Privilege — nur bei Widerspruch anfassen) und **{len(open_)} wirklich offen**. "
        f"{len(withp)} tragen einen konkreten Vorschlag. Jeder Vorschlag ist aus dem abgeleitet, was das "
        "governte Modell hergibt — er ist **zu bestätigen oder anzupassen**, nie eine gesetzte Tatsache. "
        "Ziel: der Workshop bestätigt, statt herzuleiten.", "",
        f"## Vorbelegt — nur bei Widerspruch anfassen ({len(pre)})", "",
        "| ID | Thema | Konfidenz | Entscheider |", "|---|---|---|---|",
    ]
    for p in pre:
        lines.append(f"| `{p['id']}` | {p['topic']} | {p['confidence']} | {p['decider']} |")
    lines += ["", f"## Wirklich offen — hier brauchen wir eine Antwort ({len(open_)})", "",
              "| ID | Thema | Vorschlag vorhanden | Konfidenz | Entscheider |", "|---|---|---|---|---|"]
    for p in open_:
        lines.append(f"| `{p['id']}` | {p['topic']} | {'ja' if p.get('proposal') else '**nein**'} "
                     f"| {p['confidence']} | {p['decider']} |")
    lines.append("")
    for p in proposals:
        lines += [f"## {p['id']} — {p['topic']}", "",
                  f"**Offene Frage:** {p['gap']}", ""]
        if p.get("proposal"):
            lines += [f"**Vorschlag (zu bestätigen):** {p['proposal']}", "",
                      f"*Hergeleitet aus:* {p['derived_from']}  ·  *Konfidenz:* **{p['confidence']}**", ""]
        else:
            lines += ["**Kein Vorschlag ableitbar.** " + p["derived_from"] +
                      " — hier muss der Workshop wirklich von vorn erheben.", ""]
        if p.get("alternatives"):
            lines += ["**Alternativen:**", ""] + [f"- {a}" for a in p["alternatives"]] + [""]
        if p.get("markers"):
            # Sichtbar machen, WELCHE Platzhalter diese Entscheidung auflöst. Vorher war die
            # Zuordnung nur thematisch — jetzt steht sie da und ist prüfbar (DoD PE-05).
            lines += ["**Löst diese Platzhalter auf:** " +
                      " · ".join(f"`TODO({m})`" for m in p["markers"]), ""]
        lines += [f"**Entscheider:** {p['decider']}", "",
                  f"**Wenn nicht entschieden:** {p['if_undecided']}", ""]
    return "\n".join(lines).rstrip() + "\n"


def emit_decisions(bp: dict, governed_catalog: dict | None = None,
                   source_schema: dict | None = None) -> dict[str, str]:
    """Return the decision-template artifact set (path → content)."""
    proposals = propose_all(bp, governed_catalog, source_schema)
    return {
        "decisions/ENTSCHEIDUNGSVORLAGE.md": decisions_markdown(proposals),
        "decisions/proposals.json": json.dumps(
            {"schema": "meridian/decision-proposals/v1", "proposals": proposals},
            indent=2, ensure_ascii=False) + "\n",
    }
