"""storage_mode — Speichermodus der Semantikmodelle je Mandant (D-590, I-21 E-1).

Eine Stelle fuer drei Dinge, die vorher verteilt oder gar nicht standen:

1. **Das Feld.** ``medallion.platinum.storage_mode`` im Bauplan (Schema-Peer-Paar mit ALUCA).
   Zwei Werte: ``direct_lake_onelake`` und ``import``.
2. **Die Vorgabe, wenn das Feld fehlt.** ``direct_lake_onelake``, wenn der Mandant eine
   Fabric-Kapazitaet hat, sonst ``import`` (D-590). Die Regel steht nur hier; Generatoren
   rufen ``resolve_storage_mode`` und leiten nichts selbst aus ``platform`` ab.
3. **Die Grenze von Direct Lake bei berechneten Spalten.** Direct Lake on OneLake kennt sie
   nur mit Ausdruckskontext *User Context*, unmaterialisiert und nie als Beziehungsschluessel
   (Learn ``power-bi/transform-model/desktop-calculated-columns`` → Materialization and
   performance; ``fabric/fundamentals/direct-lake-overview`` → Compare storage mode
   capabilities, beide gelesen 30.09.2026). Ein Modell, das materialisierte Hilfsspalten oder
   berechnete Schluessel braucht, bricht im Direct-Lake-Modus ab, statt still Import-Tabellen
   beizumischen.

**Warum kein drittes Enum ``direct_lake_sql``.** Direct Lake on SQL ist laut Learn (gelesen
30.09.2026) nicht abgekuendigt und weiter eine der zwei Direct-Lake-Varianten. Kein Generator
beider Repos emittiert es aus dem Bauplan, und ein Wert, den kein Generator erzeugt, waere eine
Zusage ohne Halter. Wer es braucht (SQL-Views mit DirectQuery-Rueckfall, Snowflake-Datenbank als
Quelle), nimmt es als eigenen D-Eintrag auf.

Reine Funktionen, nur Standardbibliothek: das Modul wird nach ALUCA gespiegelt
(``aluca_spiegelmenge.json``) und darf kein nicht gespiegeltes Modul importieren (D-541).
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

DIRECT_LAKE_ONELAKE = "direct_lake_onelake"
IMPORT = "import"
STORAGE_MODES: tuple[str, ...] = (DIRECT_LAKE_ONELAKE, IMPORT)

#: Ort des Feldes im Bauplan (fuer Meldungen und Doku, nicht zum Nachbauen des Zugriffs).
FIELD = "medallion.platinum.storage_mode"

#: TOM ``ExpressionContext.UserContext`` in TMDL-Schreibweise (Learn, ExpressionContext Enum).
USER_CONTEXT = "userContext"


class StorageModeError(ValueError):
    """Ungueltiger Speichermodus oder ein Modell, das der gewaehlte Modus nicht tragen kann."""


def declared_storage_mode(blueprint: Mapping[str, Any] | None) -> str | None:
    """Der im Bauplan gesetzte Wert, ``None`` wenn das Feld fehlt. Unbekannte Werte brechen ab."""
    platinum = ((blueprint or {}).get("medallion") or {}).get("platinum") or {}
    wert = platinum.get("storage_mode")
    if wert is None:
        return None
    if wert not in STORAGE_MODES:
        raise StorageModeError(
            f"{FIELD} = {wert!r} ist kein Speichermodus; erlaubt: {', '.join(STORAGE_MODES)}")
    return str(wert)


def has_fabric_capacity(blueprint: Mapping[str, Any] | None) -> bool:
    """Hat der Mandant eine Fabric-Kapazitaet? Grundlage der Vorgabe (D-590).

    * ``platform.stack == "fabric"``: ja. Lakehouse und Warehouse laufen nur auf einer
      Fabric-Kapazitaet; der Bauplan fuehrt dann immer mindestens einen Kapazitaetseintrag,
      notfalls als Zielbild (``blueprint._kapazitaeten``).
    * anderer Stack: nur, wenn eine Kapazitaet benannt oder mit SKU versehen ist
      (``capacity``, ``capacity_sku`` oder ein ``capacities``-Eintrag mit ``name``/``sku``).
      Ein reiner Zielbild-Eintrag zaehlt dort nicht — er sagt, dass eine Entscheidung aussteht.
    """
    platform = (blueprint or {}).get("platform") or {}
    if platform.get("stack") == "fabric":
        return True
    if str(platform.get("capacity") or "").strip() or str(platform.get("capacity_sku") or "").strip():
        return True
    return any(isinstance(k, Mapping) and (k.get("name") or k.get("sku"))
               for k in platform.get("capacities") or [])


def resolve_storage_mode(blueprint: Mapping[str, Any] | None) -> str:
    """Der Speichermodus des Mandanten: das Feld, sonst die Vorgabe aus ``has_fabric_capacity``."""
    gesetzt = declared_storage_mode(blueprint)
    if gesetzt is not None:
        return gesetzt
    return DIRECT_LAKE_ONELAKE if has_fabric_capacity(blueprint) else IMPORT


def storage_mode_source(blueprint: Mapping[str, Any] | None) -> str:
    """Woher der Modus kommt — fuer Statuszeilen, damit eine Vorgabe nicht wie eine Angabe aussieht."""
    if declared_storage_mode(blueprint) is not None:
        return f"gesetzt ({FIELD})"
    if has_fabric_capacity(blueprint):
        return "Vorgabe: Fabric-Kapazitaet vorhanden (D-590)"
    return "Vorgabe: keine Fabric-Kapazitaet (D-590)"


def direct_lake_violations(tables: Iterable[Mapping[str, Any]],
                           relationships: Iterable[tuple[str, str, str, str]] = ()) -> list[str]:
    """Was ein Modell im Direct-Lake-on-OneLake-Modus nicht tragen kann.

    ``tables``: je Tabelle ``{"name": str, "columns": [{"name", "expression",
    "expression_context"}]}``. Eine Spalte mit nichtleerem ``expression`` ist berechnet.
    ``relationships``: ``(from_table, from_column, to_table, to_column)``.

    Zwei Befunde, beide aus Learn (Modul-Docstring):
    * berechnete Spalte ohne ``expression_context == "userContext"`` — sie waere materialisiert,
      und das gibt es in Direct Lake nicht;
    * berechnete Spalte als Beziehungsschluessel — auch mit User Context nicht, weil sie nicht
      materialisiert wird.
    """
    rel_keys: set[tuple[str, str]] = set()
    for ft, fc, tt, tc in relationships:
        rel_keys.add((ft, fc))
        rel_keys.add((tt, tc))
    out: list[str] = []
    for t in tables:
        tname = str(t.get("name") or "")
        for c in t.get("columns") or []:
            if not str(c.get("expression") or "").strip():
                continue
            cname = str(c.get("name") or "")
            if (tname, cname) in rel_keys:
                out.append(f"{tname}[{cname}]: berechnete Spalte als Beziehungsschluessel")
            elif c.get("expression_context") != USER_CONTEXT:
                out.append(f"{tname}[{cname}]: materialisierte berechnete Spalte "
                           "(Ausdruckskontext nicht userContext)")
    return out


def check_storage_mode(mode: str, tables: Iterable[Mapping[str, Any]],
                       relationships: Iterable[tuple[str, str, str, str]] = ()) -> None:
    """Abbruch mit klarer Meldung, wenn ``mode`` das Modell nicht tragen kann. Import traegt alles."""
    if mode not in STORAGE_MODES:
        raise StorageModeError(f"Speichermodus {mode!r} unbekannt; erlaubt: {', '.join(STORAGE_MODES)}")
    if mode != DIRECT_LAKE_ONELAKE:
        return
    befunde = direct_lake_violations(tables, relationships)
    if befunde:
        raise StorageModeError(
            f"Speichermodus {DIRECT_LAKE_ONELAKE} traegt dieses Modell nicht "
            f"({len(befunde)} Befund(e)):\n  " + "\n  ".join(befunde)
            + f"\nDirect Lake on OneLake kennt berechnete Spalten nur mit Ausdruckskontext "
              f"User Context, unmaterialisiert und nicht in Beziehungen. Entweder die Spalten in "
              f"Gold materialisieren oder {FIELD} = {IMPORT} setzen. Ein stilles Beimischen von "
              f"Import-Tabellen findet nicht statt.")
