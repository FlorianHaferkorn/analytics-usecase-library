"""ontologie_kern — Ontologie-Modell, Import-Profil und Turtle fuer Fabric IQ (D-593, D-617).

Der katalogunabhaengige Teil von ``meridian.semantics.rdf_owl``: die Datenklassen, die belegten
Import-Grenzen (Profil), die Turtle-Ausgabe und der Aufbau eines Modells **aus der
Geschaeftsobjekt-Schicht** (``business_object.schema.json``, Peer-Paar Meridian/ALUCA, D-608).

``rdf_owl`` baut sein Modell aus der Meridian-Organisation (Stern-Schemata, Beschreibungen) und
legt die Schicht darueber; dieses Modul baut es allein aus der Schicht. Damit kann ALUCA seine
Bibliothek als Ontologie liefern (I-21 W4.3), ohne einen zweiten Emitter: das Modul wird
gespiegelt (``tooling/superversion/vendor/meridian_dataarch/ontologie_kern.py``). Deshalb nur
Standardbibliothek.

Belege und Grenzen: siehe ``QUELLEN`` und den Modul-Docstring von ``rdf_owl``.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

GELESEN_AM = "2026-09-30"
QUELLEN = {
    "import": "https://learn.microsoft.com/fabric/iq/ontology/how-to-import-export",
    "entity_namen": "https://learn.microsoft.com/fabric/iq/ontology/how-to-create-entity-types",
    "definition": "https://learn.microsoft.com/rest/api/fabric/articles/item-management/definitions/ontology-definition",
    "agent": "https://learn.microsoft.com/fabric/iq/ontology/how-to-use-ontology-agent",
    "agent_anhaenge": "https://learn.microsoft.com/fabric/iq/ontology/resources-troubleshooting",
    "generate": "https://learn.microsoft.com/fabric/iq/ontology/concepts-generate",
}

# Grenzen aus Learn (Quellen oben) als Felder, nicht als Satz.
ENTITY_NAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9_-]{0,24}[A-Za-z0-9])?$")   # 1–26 Zeichen
PROPERTY_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,127}$")
MAX_BESCHREIBUNG = 4000
MAX_SYNONYM = 100
MAX_SYNONYME = 100
MAX_PROPERTIES_JE_ENTITY = 1000
MAX_ANHAENGE = 10
MAX_ANHANG_BYTES = 5 * 1024 * 1024
MAX_ANHANG_NAME = 60
KPI_ID_RE = re.compile(r"^KPI-[A-Z]+-\d{3}$")   # D-594: nummeriertes Schema

# Meridian/TMDL-Datentyp → XSD. Die Fabric-Seite (string, int64, double, dateTime, boolean,
# decimal) ist belegt; welches XSD-Literal der Import je Typ erkennt, ist ANNAHME, ungeprueft.
XSD_FUER_DATENTYP = {
    "String": "xsd:string",
    "Int64": "xsd:long",
    "Double": "xsd:double",
    "DateTime": "xsd:dateTime",
    "Boolean": "xsd:boolean",
    "Decimal": "xsd:decimal",
}
ERLAUBTE_RANGES = frozenset(XSD_FUER_DATENTYP.values())


@dataclass(frozen=True)
class Klasse:
    name: str
    label: str
    beschreibung: str
    tabelle: str
    art: str                      # "fakt" | "dimension"
    domaene: str = ""
    schluessel: str = ""
    synonyme: tuple[str, ...] = ()
    geschaeftsobjekt: str = ""    # BO-<NNN> (D-608), leer ohne Schicht


@dataclass(frozen=True)
class Eigenschaft:
    name: str
    label: str
    beschreibung: str
    klasse: str
    xsd: str
    spalte: str


@dataclass(frozen=True)
class Beziehung:
    name: str
    label: str
    beschreibung: str
    von: str
    nach: str
    von_spalte: str
    nach_spalte: str
    stern: str
    kardinalitaet: str = ""       # aus der Geschaeftsobjekt-Schicht (D-608)
    rolle: str = ""


@dataclass
class OntologieModell:
    org: str
    org_name: str
    basis_iri: str
    klassen: list[Klasse] = field(default_factory=list)
    eigenschaften: list[Eigenschaft] = field(default_factory=list)
    beziehungen: list[Beziehung] = field(default_factory=list)
    ausgelassen: list[dict[str, str]] = field(default_factory=list)
    schicht_befunde: list[str] = field(default_factory=list)


_ART_TEXT = {"master_data": "Stammobjekt", "transaction": "Bewegungsobjekt"}


# ─── Profil (Fabric-IQ-Import) ────────────────────────────────────────────────

def profil_befunde(modell: OntologieModell) -> list[str]:
    """Verstoesse gegen die belegten Import-Grenzen. Leer = importfaehig (soweit dokumentiert)."""
    befunde: list[str] = list(modell.schicht_befunde)
    namen = [k.name for k in modell.klassen] + [e.name for e in modell.eigenschaften] + \
            [b.name for b in modell.beziehungen]
    doppelt = sorted({n for n in namen if namen.count(n) > 1})
    if doppelt:
        befunde.append(f"nicht eindeutige Namen (IRIs): {doppelt}")
    klassen = {k.name for k in modell.klassen}
    je_klasse: dict[str, int] = {}
    for k in modell.klassen:
        if not ENTITY_NAME_RE.match(k.name):
            befunde.append(f"Entity-Name {k.name!r} verletzt 1–26 Zeichen [A-Za-z0-9_-]")
        if not k.label.strip():
            befunde.append(f"{k.name}: leeres Label")
        if len(k.beschreibung) > MAX_BESCHREIBUNG:
            befunde.append(f"{k.name}: Beschreibung {len(k.beschreibung)} > {MAX_BESCHREIBUNG}")
        if len(k.synonyme) > MAX_SYNONYME:
            befunde.append(f"{k.name}: {len(k.synonyme)} Synonyme > {MAX_SYNONYME}")
        befunde += [f"{k.name}: Synonym {s!r} > {MAX_SYNONYM} Zeichen"
                    for s in k.synonyme if len(s) > MAX_SYNONYM]
    typ_je_label: dict[str, set[str]] = {}
    for e in modell.eigenschaften:
        je_klasse[e.klasse] = je_klasse.get(e.klasse, 0) + 1
        typ_je_label.setdefault(e.label, set()).add(e.xsd)
        if not PROPERTY_NAME_RE.match(e.name):
            befunde.append(f"Property-Name {e.name!r} verletzt ^[A-Za-z][A-Za-z0-9_-]{{0,127}}$")
        if e.klasse not in klassen:
            befunde.append(f"{e.name}: Domain {e.klasse!r} ist keine Klasse")
        if e.xsd not in ERLAUBTE_RANGES:
            befunde.append(f"{e.name}: Range {e.xsd!r} nicht im belegten Typ-Satz")
        if len(e.beschreibung) > MAX_BESCHREIBUNG:
            befunde.append(f"{e.name}: Beschreibung > {MAX_BESCHREIBUNG}")
    befunde += [f"{k}: {n} Properties > {MAX_PROPERTIES_JE_ENTITY}"
                for k, n in je_klasse.items() if n > MAX_PROPERTIES_JE_ENTITY]
    befunde += [f"Eigenschaft {lbl!r} mit verschiedenen Typen {sorted(t)} (Generate-Konflikt)"
                for lbl, t in sorted(typ_je_label.items()) if len(t) > 1]
    for b in modell.beziehungen:
        if not PROPERTY_NAME_RE.match(b.name):
            befunde.append(f"Beziehungsname {b.name!r} verletzt das Namensmuster")
        for ende in (b.von, b.nach):
            if ende not in klassen:
                befunde.append(f"{b.name}: Ende {ende!r} ist keine Klasse")
    return befunde


# ─── Turtle ───────────────────────────────────────────────────────────────────

def _lit(text: str) -> str:
    esc = (text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
           .replace("\r", "\\r").replace("\t", "\\t"))
    return f'"{esc}"'


def emit_ttl(modell: OntologieModell, herkunft: str = "Meridian") -> str:
    """Deterministisches Turtle; nur die im Modul-Docstring genannten Terme."""
    z = [
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .",
        "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix skos: <http://www.w3.org/2004/02/skos/core#> .",
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
        f"@prefix m: <{modell.basis_iri}> .",
        "",
        f"<{modell.basis_iri.rstrip('#/')}> a owl:Ontology ;",
        f"    rdfs:label {_lit(f'{modell.org_name} — {herkunft}-Ontologie')} ;",
        f"    rdfs:comment {_lit(f'Erzeugt aus der {herkunft}-Ontologie der Organisation {modell.org} (D-593, ADR-0054). Nur Entity types, Eigenschaften und Beziehungen; Bindungen kommen über Generate from semantic model.')} .",
        "",
    ]
    for k in modell.klassen:
        z.append(f"m:{k.name} a owl:Class ;")
        z.append(f"    rdfs:label {_lit(k.label)} ;")
        for s in k.synonyme:
            z.append(f"    skos:altLabel {_lit(s)} ;")
        z.append(f"    rdfs:comment {_lit(k.beschreibung)} .")
        z.append("")
    for e in sorted(modell.eigenschaften, key=lambda x: x.name):
        z += [f"m:{e.name} a owl:DatatypeProperty ;",
              f"    rdfs:label {_lit(e.label)} ;",
              f"    rdfs:comment {_lit(e.beschreibung)} ;",
              f"    rdfs:domain m:{e.klasse} ;",
              f"    rdfs:range {e.xsd} .", ""]
    for b in sorted(modell.beziehungen, key=lambda x: x.name):
        z += [f"m:{b.name} a owl:ObjectProperty ;",
              f"    rdfs:label {_lit(b.label)} ;",
              f"    rdfs:comment {_lit(b.beschreibung)} ;",
              f"    rdfs:domain m:{b.von} ;",
              f"    rdfs:range m:{b.nach} .", ""]
    return "\n".join(z)


# ─── Modell aus der Geschaeftsobjekt-Schicht (D-617) ─────────────────────────

#: Property-Typ der Schicht (Fabric-IQ-Typen, ``business_object.schema.json``) → XSD. Dieselben
#: Literale wie ``XSD_FUER_DATENTYP``; welches der Import je Typ erkennt, ist ANNAHME, ungeprueft.
XSD_FUER_FABRIC_TYP = {
    "string": "xsd:string", "int64": "xsd:long", "double": "xsd:double",
    "dateTime": "xsd:dateTime", "boolean": "xsd:boolean", "decimal": "xsd:decimal",
}
_ART_FUER_KIND = {"transaction": "fakt", "master_data": "dimension"}


def _ident(text: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^A-Za-z0-9_]", "_", str(text))).strip("_")


def modell_aus_geschaeftsobjekten(doc: dict[str, Any], org: str, org_name: str, basis_iri: str,
                                  sprache: str = "de",
                                  kpi_namen: dict[str, str] | None = None) -> OntologieModell:
    """Geschaeftsobjekt-Schicht → Ontologie-Modell. Nichts wird erfunden.

    * Klasse je Objekt, IRI = gebundene Tabelle (wie „Generate from semantic model"); Label aus
      ``name[sprache]``, sonst die andere Sprache, sonst die Tabelle; die uebrigen Namen werden
      Synonyme. Kommentar: die Beschreibung der Schicht plus ID, Objektart und Kennzahlen (mit
      Namen, wenn ``kpi_namen`` sie kennt). Ohne Beschreibung steht nur dieser Zusatz da.
    * Eigenschaft je Attribut (``<tabelle>__<attribut>``), Typ aus ``XSD_FUER_FABRIC_TYP``,
      Kommentar = Beschreibung der Schicht, sonst Spalte und Typ.
    * Beziehung je Objekt-Beziehung (``<von>_<nach>``, bei mehreren Kanten zwischen denselben
      Tabellen mit Join-Spalte), Kommentar mit Join, Kardinalitaet und Rolle, soweit bekannt.
    """
    kpi_namen = kpi_namen or {}
    modell = OntologieModell(org=org, org_name=org_name, basis_iri=basis_iri)
    objekte = [o for o in doc.get("business_objects") or [] if (o.get("binding") or {}).get("table")]
    tabelle_je_id = {o["id"]: o["binding"]["table"] for o in objekte}
    for o in objekte:
        t = o["binding"]["table"]
        namen = {k: v for k, v in (o.get("name") or {}).items() if v}
        label = namen.get(sprache) or next(iter(v for _k, v in sorted(namen.items())), "") or t
        kpis = [f"{k} ({kpi_namen[k]})" if kpi_namen.get(k) else k for k in o.get("kpi_ids") or []]
        zusatz = f"Geschäftsobjekt {o['id']} ({_ART_TEXT.get(o.get('kind'), o.get('kind'))})"
        if kpis:
            zusatz += ", Kennzahlen " + ", ".join(kpis)
        text = f"{o['description']} {zusatz}." if o.get("description") else f"{zusatz}."
        keys = (o.get("keys") or {}).get("technical") or (o.get("keys") or {}).get("natural") or []
        modell.klassen.append(Klasse(
            name=t, label=label, beschreibung=text, tabelle=t,
            art=_ART_FUER_KIND.get(o.get("kind"), "dimension"), domaene=o.get("domain") or "",
            schluessel=keys[0] if keys else "", geschaeftsobjekt=o["id"],
            synonyme=tuple(dict.fromkeys(v for v in namen.values() if v != label))))
        for a in o.get("attributes") or []:
            typ = a.get("type") or "string"
            if typ not in XSD_FUER_FABRIC_TYP:
                raise ValueError(f"{t}.{a.get('name')}: Typ {typ!r} ohne belegte Abbildung")
            modell.eigenschaften.append(Eigenschaft(
                name=f"{t}__{_ident(a['name'])}", label=a["name"],
                beschreibung=a.get("description") or f"Spalte {a.get('column') or a['name']} ({typ}).",
                klasse=t, xsd=XSD_FUER_FABRIC_TYP[typ], spalte=a.get("column") or a["name"]))
    labels = {k.name: k.label for k in modell.klassen}
    kanten: dict[tuple[str, str], int] = {}
    for o in objekte:
        for r in o.get("relationships") or []:
            nach = tabelle_je_id.get(r.get("target"))
            if nach:
                kanten[(o["binding"]["table"], nach)] = kanten.get((o["binding"]["table"], nach), 0) + 1
    for o in objekte:
        von = o["binding"]["table"]
        for r in o.get("relationships") or []:
            nach = tabelle_je_id.get(r.get("target"))
            if not nach:
                modell.schicht_befunde.append(f"{o['id']}: Beziehungsziel {r.get('target')} fehlt")
                continue
            name = f"{von}_{nach}" + (f"__{_ident(r.get('from_column'))}"
                                      if kanten[(von, nach)] > 1 else "")
            text = (f"Geschäftsobjekt-Beziehung {von}[{r.get('from_column')}] → {nach}"
                    f"[{r.get('to_column') or '?'}]."
                    + (f" Kardinalität {r['cardinality']}." if r.get("cardinality") else "")
                    + (f" Rolle: {r['role']}." if r.get("role") else ""))
            modell.beziehungen.append(Beziehung(
                name=name, label=f"{labels.get(von, von)} – {labels.get(nach, nach)}",
                beschreibung=text, von=von, nach=nach, von_spalte=r.get("from_column") or "",
                nach_spalte=r.get("to_column") or "", stern="",
                kardinalitaet=r.get("cardinality") or "", rolle=r.get("role") or ""))
    modell.klassen.sort(key=lambda k: (k.art != "fakt", k.name))
    return modell
