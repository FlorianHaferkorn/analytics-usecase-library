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
    "DATA-CONTRACT": "blockiert den Aufbau",
    "NET-OUTBOUND": "blockiert den Aufbau",
    "SEC-RLS": "vor Produktivsetzung",
    "SEC-CLS": "vor Produktivsetzung",
    "GOV-RET": "vor Produktivsetzung",
    "AI-EVAL": "vor Produktivsetzung",
    "OPS-USERDATA": "vor Produktivsetzung",
}


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
            # `markers`: die `TODO(...)`-Marken im Lieferumfang, die GENAU diese Entscheidung
            # auflöst. Damit wird aus einer thematischen Zuordnung eine prüfbare — DoD-Kriterium
            # PE-05 kann so mechanisch statt per Urteil prüfen, dass kein Platzhalter stumm ist.
            "markers": list(markers)}


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
    keys = [c for c in cols if c.lower().endswith("_key")]
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
         "Partition-Overwrite je Periode statt zeilenweisem MERGE"],
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
        f"Umgang mit spät eintreffenden Zeilen. Vorschlag: den Vertrag als ODCS-Datei aus genau diesen "
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
         "ein schema-aktiviertes Lakehouse voraus**, und MS' eigenes MLV-Tutorial fährt genau diese "
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
         "nehmen einem die Orchestrierung ab: Abhängigkeitsreihenfolge, Refresh-Entscheidung "
         "(inkrementell/voll/keine), Lineage und Datenqualitätsregeln kommen mit. Was man selbst "
         "baut, muss man selbst betreiben.\n\n"
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
        f" Diese Lieferung hat **{len(lokal)} Quelle(n) hinter der Firewall** — und genau da wird die "
        "Frage scharf: **das On-premises-Data-Gateway laesst sich mit aktiviertem Private Link nicht "
        "einmal registrieren.** Wer beides will, braucht das VNet-Data-Gateway; das ist eine andere "
        "Beschaffung, kein Schalter." if lokal else
        " Diese Lieferung hat keine Quelle hinter der Firewall, die Gateway-Frage stellt sich also "
        "heute nicht. Sie stellt sich beim ersten lokalen Quellsystem.")
    return _rec(
        "PLAT-NET", "Netzanbindung (öffentlich / Private Link)",
        "Wie erreichen Nutzer und Dienste die Plattform, und wie erreicht die Plattform die Quellen?",
        ("Vorschlag: **öffentliche Endpunkte plus Trusted Workspace Access** für Azure-Quellen. "
         "Trusted Workspace Access lässt einen Speicher hinter geschlossener Firewall trotzdem aus "
         "genannten Workspaces lesen, über das Microsoft-Backbone — der Sicherheitsgewinn ohne den "
         "Preis von Private Link. **Private Link wird nicht vorsorglich gebaut**, sondern nur auf "
         "belegte Anforderung: er kostet unter anderem Publish-to-Web, PDF-/PowerPoint-Export, "
         "E-Mail-Abonnements, Copilot, die Capacity-Metrics-App und tenantübergreifende Verknüpfungen "
         "— und er ist nachträglich nur mit Neuaufbau der Quellanbindung zu drehen." + gateway_satz),
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
            if not dgc.get("tables"):
                continue
            slug = _NONWORD_RE.sub("-", (d.get("name") or "").lower()).strip("-")
            dq = _quell_schnitt(bp, source_schema, d)
            for fn in per_domain:
                r = fn(dgc, dq) if fn in mit_quelle else fn(dgc)
                r["id"] = f"{r['id']}{FANOUT_TRENNER}{slug}"
                r["topic"] = f"{r['topic']} — {d.get('name')}"
                out.append(r)
    else:
        out.extend(fn(gc, source_schema) if fn in mit_quelle else fn(gc) for fn in per_domain)
    if len(domains) > 1 and gc.get("tables"):
        out.extend(propose_cross_domain(bp, gc))   # domains are not islands
    out.extend([propose_workspace_roles(bp), propose_retention(bp, gc, source_schema),
                propose_alerts(bp),
                propose_endorsement(bp, gc), propose_capacity(bp), propose_tenant_settings(bp),
                propose_network_stance(bp), propose_outbound_exceptions(bp),
                propose_user_data_visibility(bp),
                propose_lakehouse_schemas(bp), propose_lakehouse_topology(bp),
                propose_transform_engine(bp)])
    _tier = propose_platform_tier(bp)      # nur auf Stacks mit Stufen-Achse und nur solange offen
    if _tier:
        out.append(_tier)
    _cluster = propose_clustering_columns(bp, gc)
    if _cluster:
        out.append(_cluster)
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
