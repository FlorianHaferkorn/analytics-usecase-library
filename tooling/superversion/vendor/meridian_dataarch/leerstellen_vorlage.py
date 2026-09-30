"""Leerstellen der Geschaeftsobjekt-Schicht als Vorlage — und zurueck (D-610, I-21 W4.6).

Die Schicht (Schema ``business_object.schema.json``, Peer-Paar Meridian/ALUCA) laesst ``null``,
wo keine Quelle einen Wert traegt. Geschaetzt wird nicht; die Werte kommen von dem, der sie
kennt (Fachbereich des Kunden, Kurator:in der Bibliothek). Dieses Modul macht daraus eine
Vorlage — **eine Zeile je Leerstelle**, vorbelegt mit dem, was bekannt ist (Kontext), die Spalte
``wert`` leer — und liest die ausgefuellte Vorlage wieder ein.

Regeln der Uebernahme (``uebernehme``):

* nur Zeilen mit ``wert``; eine leere Zeile bleibt Leerstelle;
* nur in ``null``-Felder: ein belegter Wert (abgeleitet oder schon kuratiert) wird nie
  ueberschrieben — der Befund nennt ihn;
* Werte werden gegen die Schema-Aufzaehlungen und gegen die Spalten des Objekts geprueft;
  ``personal_data`` nimmt ``nein`` oder ``ja:<kategorie>`` (``ja`` verlangt die Kategorie, Schema
  ``if/then``);
* jeder Befund bricht die ganze Uebernahme ab (alles oder nichts).

Kuratierte Werte ueberleben das naechste ``--schreiben``/``--write`` ueber das bestehende
Zusammenfuehren (Ableitung ``null`` → Bestandswert gilt).

Bewusst nur Standardbibliothek: das Modul wird nach ALUCA gespiegelt
(``tooling/superversion/vendor/meridian_dataarch/``) und von beiden Generatoren benutzt.
"""
from __future__ import annotations

import copy
import csv
import io
import re
from typing import Any

#: Spalten der Vorlage, in dieser Reihenfolge.
SPALTEN = ("objekt_id", "tabelle", "feld", "zustaendig", "erlaubte_werte", "kontext", "wert")

#: Wer den Wert kennt: ``fachlich`` = Fachbereich, ``technisch`` = Datenplattform-Team.
ZUSTAENDIG = {
    "name.de": "fachlich", "name.en": "fachlich", "description": "fachlich", "grain": "fachlich",
    "domain": "fachlich", "keys.technical": "technisch", "keys.natural": "fachlich",
    "binding.schema": "technisch", "binding.layer": "technisch",
    "attribute.description": "fachlich", "attribute.personal_data": "fachlich",
    "relationship.cardinality": "technisch", "relationship.role": "fachlich",
    "relationship.to_column": "technisch",
}

KATEGORIEN = ("contact_data", "identification_data", "financial_data", "behavioural_data",
              "performance_data", "health_data", "special_category_art9")
KARDINALITAETEN = ("many-to-one", "one-to-one", "one-to-many", "many-to-many")
SCHICHTEN = ("bronze", "silver", "gold")

_ATTR_RE = re.compile(r"^attributes\[(?P<name>.+)\]\.(?P<feld>description|personal_data)$")
_REL_RE = re.compile(r"^relationships\[(?P<ziel>[^/\]]+)/(?P<von>.+)\]\.(?P<feld>cardinality|role|to_column)$")


def _erlaubt(art: str, o: dict[str, Any]) -> str:
    spalten = " | ".join(a.get("column") or a.get("name") for a in o.get("attributes") or [])
    return {
        "keys.technical": f"Spalten, mit | getrennt: {spalten}",
        "keys.natural": f"Spalten, mit | getrennt: {spalten}",
        "binding.layer": " | ".join(SCHICHTEN),
        "attribute.personal_data": "nein | ja:<" + " | ".join(KATEGORIEN) + ">",
        "relationship.cardinality": " | ".join(KARDINALITAETEN),
    }.get(art, "Text")


def _objekt_kontext(o: dict[str, Any]) -> str:
    teile = [f"Art: {o.get('kind')}"]
    name = o.get("name") or {}
    if name.get("en"):
        teile.append(f"Name en: {name['en']}")
    if name.get("de"):
        teile.append(f"Name de: {name['de']}")
    if o.get("description"):
        teile.append(f"Beschreibung: {o['description']}")
    return "; ".join(teile)


def zeilen(doc: dict[str, Any]) -> list[dict[str, str]]:
    """Eine Zeile je Leerstelle, in Objekt- und Feldreihenfolge (deterministisch).

    Dieselbe Zaehlregel wie ``leerstellen``/``gaps`` der Generatoren: ``grain`` nur bei
    Bewegungsobjekten. Die Zeilenzahl ist also die Summe dieser Zaehler (Test).
    """
    je_id = {o.get("id"): o for o in doc.get("business_objects") or []}
    out: list[dict[str, str]] = []

    def zeile(o: dict[str, Any], feld: str, art: str, kontext: str) -> None:
        out.append({"objekt_id": o["id"], "tabelle": (o.get("binding") or {}).get("table") or "",
                    "feld": feld, "zustaendig": ZUSTAENDIG[art], "erlaubte_werte": _erlaubt(art, o),
                    "kontext": kontext, "wert": ""})

    for o in doc.get("business_objects") or []:
        ok = _objekt_kontext(o)
        for f in ("name.de", "name.en"):
            if (o.get("name") or {}).get(f.split(".")[1]) is None:
                zeile(o, f, f, ok)
        if o.get("description") is None:
            zeile(o, "description", "description", ok)
        if o.get("kind") == "transaction" and o.get("grain") is None:
            zeile(o, "grain", "grain", ok)
        if o.get("domain") is None:
            zeile(o, "domain", "domain", ok)
        for f in ("keys.technical", "keys.natural", "binding.schema", "binding.layer"):
            a, b = f.split(".")
            if (o.get(a) or {}).get(b) is None:
                zeile(o, f, f, ok)
        for at in o.get("attributes") or []:
            kurz = f"Objekt {(o.get('name') or {}).get('en') or (o.get('binding') or {}).get('table')}"
            ak = f"{kurz}; Attribut {at.get('name')} ({at.get('type')}), Spalte {at.get('column')}"
            if at.get("description") is not None:
                ak += f"; Beschreibung: {at['description']}"
            for f in ("description", "personal_data"):
                if at.get(f) is None:
                    zeile(o, f"attributes[{at['name']}].{f}", f"attribute.{f}", ak)
        for r in o.get("relationships") or []:
            ziel = je_id.get(r.get("target")) or {}
            rk = (f"Beziehung {o.get('binding', {}).get('table')}.{r.get('from_column')} -> "
                  f"{(ziel.get('binding') or {}).get('table')} ({r.get('target')})")
            for f in ("cardinality", "role", "to_column"):
                if r.get(f) is None:
                    zeile(o, f"relationships[{r['target']}/{r['from_column']}].{f}",
                          f"relationship.{f}", rk)
    return out


def als_csv(rows: list[dict[str, str]]) -> str:
    """CSV mit Kopfzeile, UTF-8 ohne BOM, ``\\n``-Zeilenenden (stabil im Diff)."""
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=SPALTEN, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def _spalten(o: dict[str, Any]) -> set[str]:
    return {a.get("column") or a.get("name") for a in o.get("attributes") or []}


def _wert(art: str, roh: str, o: dict[str, Any]) -> tuple[Any, str | None]:
    """(Wert, Befund). ``art`` ist der Zustaendig-Schluessel des Feldes."""
    if art in ("keys.technical", "keys.natural"):
        liste = [s.strip() for s in roh.split("|") if s.strip()]
        fremd = [s for s in liste if s not in _spalten(o)]
        return (liste, None) if liste and not fremd else (None, f"Spalte(n) nicht im Objekt: {fremd or roh!r}")
    if art == "binding.layer":
        return (roh, None) if roh in SCHICHTEN else (None, f"Schicht {roh!r} nicht in {SCHICHTEN}")
    if art == "relationship.cardinality":
        return (roh, None) if roh in KARDINALITAETEN else (None, f"Kardinalitaet {roh!r} unbekannt")
    return roh, None


def uebernehme(doc: dict[str, Any], csv_text: str) -> tuple[dict[str, Any], list[str], int]:
    """(neues Dokument, Befunde, Anzahl uebernommener Werte). Befunde ≠ leer → nichts uebernehmen."""
    neu = copy.deepcopy(doc)
    je_id = {o.get("id"): o for o in neu.get("business_objects") or []}
    befunde: list[str] = []
    n = 0
    leser = csv.DictReader(io.StringIO(csv_text))
    fehlend = [s for s in ("objekt_id", "feld", "wert") if s not in (leser.fieldnames or [])]
    if fehlend:
        return doc, [f"Vorlage ohne Spalte(n) {fehlend}"], 0
    for nr, z in enumerate(leser, start=2):
        roh = (z.get("wert") or "").strip()
        if not roh:
            continue
        wo = f"Zeile {nr} ({z.get('objekt_id')} {z.get('feld')})"
        o = je_id.get(z.get("objekt_id"))
        if o is None:
            befunde.append(f"{wo}: Objekt unbekannt")
            continue
        feld = z.get("feld") or ""
        if m := _ATTR_RE.match(feld):
            ziel = next((a for a in o.get("attributes") or [] if a.get("name") == m["name"]), None)
            schluessel, art = m["feld"], f"attribute.{m['feld']}"
        elif m := _REL_RE.match(feld):
            ziel = next((r for r in o.get("relationships") or []
                         if r.get("target") == m["ziel"] and r.get("from_column") == m["von"]), None)
            schluessel, art = m["feld"], f"relationship.{m['feld']}"
        elif feld in ("name.de", "name.en", "keys.technical", "keys.natural", "binding.schema",
                      "binding.layer"):
            a, schluessel = feld.split(".")
            ziel, art = o.setdefault(a, {}), feld
        elif feld in ("description", "grain", "domain"):
            ziel, schluessel, art = o, feld, feld
        else:
            befunde.append(f"{wo}: Feld unbekannt")
            continue
        if ziel is None:
            befunde.append(f"{wo}: Attribut/Beziehung nicht im Objekt")
            continue
        if ziel.get(schluessel) is not None:
            befunde.append(f"{wo}: schon belegt ({ziel[schluessel]!r}) — wird nicht ueberschrieben")
            continue
        if art == "attribute.personal_data":
            teil = [s.strip() for s in roh.split(":", 1)]
            if teil[0].lower() == "nein" and len(teil) == 1:
                ziel["personal_data"], ziel["personal_data_category"] = False, None
            elif teil[0].lower() == "ja" and len(teil) == 2 and teil[1] in KATEGORIEN:
                ziel["personal_data"], ziel["personal_data_category"] = True, teil[1]
            else:
                befunde.append(f"{wo}: erwartet nein oder ja:<Kategorie>, nicht {roh!r}")
                continue
        elif art == "relationship.to_column" and roh not in _spalten(je_id.get(ziel.get("target")) or {}):
            befunde.append(f"{wo}: Spalte {roh!r} nicht im Zielobjekt {ziel.get('target')}")
            continue
        else:
            wert, fehler = _wert(art, roh, o)
            if fehler:
                befunde.append(f"{wo}: {fehler}")
                continue
            ziel[schluessel] = wert
        n += 1
    return (doc, befunde, 0) if befunde else (neu, [], n)
