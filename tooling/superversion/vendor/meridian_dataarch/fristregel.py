"""Fristenregel der Datenaktualität: Ladetakt plus Toleranz (Entscheidung Florian 16.10.2026, D-786).

Der reine Teil von ``core/dataarch_engine/blueprint/ladetakt.py``: Regel aus dem Data Contract lesen, Ende der Frist
rechnen, Kurztext. Nur Standardbibliothek, kein Paketimport: Meridian liefert dieses Modul **byte-gleich** als
``meridian/semantics/fristregel.py`` mit aus (ADR-0016, Lieferung ohne übriges ``core``; Kern unabhängig von Meridian,
ADR-0036). Kanonisch ist die Fassung unter ``core/``; ``core/dataarch_engine/tests/test_ladetakt.py`` hält beide
gleich, ``python3 core/dataarch_engine/blueprint/fristregel.py --kopieren`` schreibt die Kopie.

Felder, Rechnung und Ableitung beschreibt ``ladetakt.py``.
"""
from __future__ import annotations

import datetime as _dt
from typing import Any

#: ODCS ``property`` des Takts (Spezifikation „Valid Values for SLA Properties“: ``frequency``, Synonym ``fy``).
FREQUENZ = ("frequency", "fy")
#: ODCS ``property`` der Uhrzeit, ab der die Daten einer Periode vorliegen (BO-406). Wert wie im Beispiel der
#: Spezifikation ``09:00-08:00`` (Fenster) oder ``06:00``; zählt nur der Beginn. ANNAHME: UTC, die Spezifikation nennt
#: keine Zeitzone.
UHRZEIT = ("timeofavailability",)
#: ``unit`` des Takts → kanonische Einheit.
TAKT_EINHEIT = {"h": "h", "hr": "h", "hour": "h", "hours": "h", "d": "d", "day": "d", "days": "d",
                "w": "w", "wk": "w", "week": "w", "weeks": "w", "mo": "mo", "month": "mo", "months": "mo"}
#: ``toleranceUnit`` → kanonische Einheit (``bd`` = Arbeitstage nach dem Kalender).
TOLERANZ_EINHEIT = {"h": "h", "hour": "h", "hours": "h", "d": "d", "day": "d", "days": "d",
                    "bd": "bd", "businessday": "bd", "businessdays": "bd", "mo": "mo", "month": "mo", "months": "mo"}
#: Namen der ``customProperties`` am Takt-Eintrag.
CP_TOLERANZ, CP_TOLERANZ_EINHEIT = "tolerance", "toleranceUnit"
#: Vorbelegung der Toleranz je Takt aus der Literatur (Entscheidung Florian 17.10.2026, Nachtrag D-786; Quellen und
#: Kennzeichnung zitiert/hergeleitet in ``docs/research/2026-10-17_toleranz-je-ladetakt.md``): stündlich 1 h
#: (Schwelle 2 h), täglich 6 h (Schwelle 30 h), monatlich bis zum 6. Arbeitstag, quartalsweise bis zum 10. Arbeitstag
#: nach Periodenende, jährlich 3 Monate (Ende des 3. Monats, § 264 HGB). Wöchentlich bleibt Leerstelle (keine Quelle).
#: Die Vorbelegung gilt erst mit Freigabe des Kunden je Takt (``toleranz_je_takt`` im Mandanten, Tor ``check-ladetakt``).
TOLERANZ_VORGABE: dict[tuple[float, str], tuple[float, str]] = {
    (1, "h"): (1, "h"), (1, "d"): (6, "h"), (1, "mo"): (6, "bd"), (3, "mo"): (10, "bd"), (12, "mo"): (3, "mo")}
#: Rückfall des Arbeitskalenders: Montag bis Freitag (ISO-Wochentage 1..5) ohne Feiertage. Seit D-802 setzt jeder
#: Mandant seinen Kalender (Tor ``check-ladetakt``, Klasse ``arbeitskalender_fehlt``); der Rückfall bleibt für Regeln
#: ohne Mandant.
KALENDER_VORGABE: dict[str, list] = {"werktage": [1, 2, 3, 4, 5], "feiertage": []}
#: Kanonische Takte als Wort (Parameter im Szenario, Messspalte der Ableitung).
TAKT_WORT = {"stuendlich": (1, "h"), "taeglich": (1, "d"), "woechentlich": (1, "w"), "monatlich": (1, "mo"),
             "quartalsweise": (3, "mo"), "jaehrlich": (12, "mo")}


def _zahl(v: Any) -> float | None:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    return float(v) if v > 0 else None


def _wort(v: Any) -> str:
    return str(v or "").strip().lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")


#: Arbeitstage als Python-``weekday()`` (0 = Montag); Vorgabe Montag bis Freitag.
WERKTAGE_MO_FR = frozenset({0, 1, 2, 3, 4})


def arbeitstag_nach(start, arbeitstage: float, feiertage: frozenset = frozenset(),
                    werktage: frozenset = WERKTAGE_MO_FR):
    """Das Datum, an dem ein Paket endet, das am ``start`` beginnt und ``arbeitstage`` braucht.

    Der Starttag zaehlt als erster Arbeitstag (Band 5 AT ab Montag endet am Freitag).
    Ein angebrochener Tag zaehlt ganz (aufgerundet). Tage ausserhalb ``werktage`` (Vorgabe
    Montag bis Freitag) und uebergebene Feiertage werden uebersprungen, auch als Starttag.
    """
    import math
    from datetime import timedelta

    if start is None:
        return None
    if not werktage:
        raise ValueError("arbeitstag_nach: der Kalender hat keinen Arbeitstag")
    tag = start
    while tag.weekday() not in werktage or tag in feiertage:
        tag += timedelta(days=1)
    rest = max(int(math.ceil(float(arbeitstage) - 1e-9)), 1) - 1
    while rest > 0:
        tag += timedelta(days=1)
        if tag.weekday() in werktage and tag not in feiertage:
            rest -= 1
    return tag


# ── Kalender ───────────────────────────────────────────────────────────────────────────────────────────────────
def kalender(roh: dict | None = None) -> dict[str, Any]:
    """Arbeitskalender in kanonischer Form; ohne Angabe die Vorgabe Montag bis Freitag ohne Feiertage.

    ``geschaeftsjahr_beginn`` (Monat 1..12, BO-408) steht nur im Ergebnis, wenn der Mandant es setzt; fehlt es, beginnen
    Monatsblöcke (Quartal, Jahr) im Januar wie bisher."""
    if not isinstance(roh, dict):
        return {"werktage": list(KALENDER_VORGABE["werktage"]), "feiertage": []}
    werk = sorted({int(t) for t in roh.get("werktage") or KALENDER_VORGABE["werktage"] if int(t) in range(1, 8)})
    feier = sorted({str(f)[:10] for f in roh.get("feiertage") or []})
    if not werk:
        raise ValueError("Arbeitskalender ohne Arbeitstag")
    out: dict[str, Any] = {"werktage": werk, "feiertage": feier}
    gj = roh.get("geschaeftsjahr_beginn")
    if gj is not None:
        if isinstance(gj, bool) or not isinstance(gj, int) or gj not in range(1, 13):
            raise ValueError(f"geschaeftsjahr_beginn muss ein Monat 1..12 sein, nicht {gj!r}")
        out["geschaeftsjahr_beginn"] = gj
    return out


def uhrzeit(vertrag: dict) -> int | None:
    """Minuten nach Mitternacht (UTC), ab denen eine Periode geliefert ist: Beginn von ODCS ``timeOfAvailability``.

    Ohne Eintrag None (die Lieferung gilt zum Periodenende, wie vor BO-406). Ein unlesbarer Wert ist ein Fehler, kein
    stiller Rückfall."""
    for e in vertrag.get("slaProperties") or []:
        if isinstance(e, dict) and _wort(e.get("property")) in UHRZEIT:
            roh = str(e.get("value") or "").strip()
            beginn = roh.split("-")[0].strip()
            try:
                h, m = (int(x) for x in beginn.split(":"))
            except ValueError:
                raise ValueError(f"timeOfAvailability unlesbar: {roh!r} (erwartet HH:MM oder HH:MM-HH:MM)") from None
            if not (0 <= h < 24 and 0 <= m < 60):
                raise ValueError(f"timeOfAvailability außerhalb des Tages: {roh!r}")
            return h * 60 + m
    return None


def _kalender_args(kal: dict) -> tuple[frozenset, frozenset]:
    feier = frozenset(_dt.date.fromisoformat(f) for f in kal.get("feiertage") or [])
    return feier, frozenset(int(t) - 1 for t in kal.get("werktage") or KALENDER_VORGABE["werktage"])


# ── Regel aus dem Vertrag ──────────────────────────────────────────────────────────────────────────────────────
def takt_eintrag(vertrag: dict) -> dict | None:
    """Der ODCS-Eintrag ``frequency`` in ``slaProperties`` (Groß/Klein egal, Synonym ``fy``); sonst None."""
    for e in vertrag.get("slaProperties") or []:
        if isinstance(e, dict) and _wort(e.get("property")) in FREQUENZ:
            return e
    return None


def _custom(eintrag: dict, name: str) -> Any:
    for c in eintrag.get("customProperties") or []:
        if isinstance(c, dict) and str(c.get("property") or "").lower() == name.lower():
            return c.get("value")
    return None


def regel(vertrag: dict, kal: dict | None = None) -> tuple[dict | None, str | None]:
    """(Regel, Grund ihres Fehlens bzw. Hinweis) für einen Data Contract.

    Vorrang hat der Takt mit Toleranz (``art: takt``). Fehlt er oder seine Toleranz, greift eine vereinbarte feste
    Stundenzahl (``sla_freshness_hours``, ``art: stunden``, rückwärtskompatibel); der zweite Wert nennt dann, warum
    der Takt nicht trägt. Ohne beides (None, Grund)."""
    hinweis = None
    e = takt_eintrag(vertrag)
    if e is not None:
        tw, te = _zahl(e.get("value")), TAKT_EINHEIT.get(_wort(e.get("unit")))
        ow, oe = _zahl(_custom(e, CP_TOLERANZ)), TOLERANZ_EINHEIT.get(_wort(_custom(e, CP_TOLERANZ_EINHEIT)))
        if tw is None or te is None:
            hinweis = f"Takt unlesbar (value {e.get('value')!r}, unit {e.get('unit')!r})"
        elif ow is None or oe is None:
            hinweis = "Takt ohne Toleranz (Leerstelle)"
        else:
            r = {"art": "takt", "takt": {"wert": tw, "einheit": te}, "toleranz": {"wert": ow, "einheit": oe},
                 "kalender": kalender(kal)}
            minuten = uhrzeit(vertrag)
            if minuten is not None:
                r["uhrzeit_minuten"] = minuten
            return r, None
    h = _zahl(vertrag.get("sla_freshness_hours"))
    if h is not None:
        return {"art": "stunden", "stunden": h}, hinweis
    return None, hinweis or "weder Takt noch sla_freshness_hours vereinbart"


# ── Rechnung ───────────────────────────────────────────────────────────────────────────────────────────────────
def _monate_spaeter(t: _dt.datetime, n: int) -> _dt.datetime:
    """``n`` Kalendermonate später; ein Tag, den der Zielmonat nicht hat, wird sein letzter (31.01. + 1 → 28.02.)."""
    import calendar

    m = t.month - 1 + n
    jahr, monat = t.year + m // 12, m % 12 + 1
    return t.replace(year=jahr, month=monat, day=min(t.day, calendar.monthrange(jahr, monat)[1]))


def _periodenende(stand: _dt.date, wert: float, einheit: str, *, gj_beginn: int = 1,
                  uhrzeit_minuten: int = 0) -> tuple[_dt.datetime, _dt.datetime]:
    """(erwartete Lieferung der Periode des Stands, erwartete Lieferung der nächsten Periode), UTC.

    ``gj_beginn`` (BO-408): Monat, in dem das Geschäftsjahr beginnt; Monatsblöcke (Quartal, Jahr) zählen ab ihm.
    ``uhrzeit_minuten`` (BO-406): die Lieferung kommt so viele Minuten nach dem Ende des letzten Tages der Periode
    (ODCS ``timeOfAvailability``); bei Stundentakten ohne Wirkung."""
    if einheit == "h":
        tag_ende = _dt.datetime(stand.year, stand.month, stand.day, tzinfo=_dt.timezone.utc) + _dt.timedelta(days=1)
        return tag_ende, tag_ende + _dt.timedelta(hours=wert)
    ende, naechste = _periodenende_tag(stand, wert, einheit, gj_beginn)
    versatz = _dt.timedelta(minutes=uhrzeit_minuten)
    return ende + versatz, naechste + versatz


def _periodenende_tag(stand: _dt.date, wert: float, einheit: str, gj_beginn: int) -> tuple[_dt.datetime, _dt.datetime]:
    tag_ende = _dt.datetime(stand.year, stand.month, stand.day, tzinfo=_dt.timezone.utc) + _dt.timedelta(days=1)
    if einheit == "d":
        return tag_ende, tag_ende + _dt.timedelta(days=wert)
    if einheit == "w":
        ende = tag_ende + _dt.timedelta(days=6 - stand.weekday())
        return ende, ende + _dt.timedelta(days=7 * wert)
    n = int(wert)
    if n != wert or n < 1:
        raise ValueError(f"Monatstakt muss eine ganze Zahl sein, nicht {wert}")
    gj_jahr = stand.year if stand.month >= gj_beginn else stand.year - 1
    block = (stand.month - gj_beginn) % 12 // n
    ende = _monate_spaeter(_dt.datetime(gj_jahr, gj_beginn, 1, tzinfo=_dt.timezone.utc), (block + 1) * n)
    return ende, _monate_spaeter(ende, n)


#: Obergrenze einer Frist, die über das darstellbare Datum hinausreicht (z. B. 10^9 Stunden): veraltet nie.
NIE = _dt.datetime(9999, 12, 31, 23, 59, 59, tzinfo=_dt.timezone.utc)


def frist_ende(stand: str | _dt.date | None, r: dict | None) -> _dt.datetime | None:
    """Zeitpunkt (UTC), ab dem ein Stand als veraltet gilt; ohne Stand oder Regel None, jenseits des darstellbaren
    Datums :data:`NIE`."""
    if not stand or not r:
        return None
    try:
        return _frist_ende(stand, r)
    except OverflowError:
        return NIE


def _frist_ende(stand: str | _dt.date, r: dict) -> _dt.datetime:
    s = stand if isinstance(stand, _dt.date) else _dt.date.fromisoformat(str(stand)[:10])
    if r["art"] == "stunden":
        return (_dt.datetime(s.year, s.month, s.day, tzinfo=_dt.timezone.utc)
                + _dt.timedelta(days=1, hours=float(r["stunden"])))
    _, naechste = _periodenende(s, float(r["takt"]["wert"]), r["takt"]["einheit"],
                                gj_beginn=int((r.get("kalender") or {}).get("geschaeftsjahr_beginn") or 1),
                                uhrzeit_minuten=int(r.get("uhrzeit_minuten") or 0))
    tw, te = float(r["toleranz"]["wert"]), r["toleranz"]["einheit"]
    if te == "h":
        return naechste + _dt.timedelta(hours=tw)
    if te == "d":
        return naechste + _dt.timedelta(days=tw)
    if te == "mo":
        if int(tw) != tw:
            raise ValueError(f"Toleranz in Monaten muss eine ganze Zahl sein, nicht {tw}")
        return _monate_spaeter(naechste, int(tw))
    feier, werk = _kalender_args(r.get("kalender") or KALENDER_VORGABE)
    tag = arbeitstag_nach(naechste.date(), tw, feier, werk)
    return _dt.datetime(tag.year, tag.month, tag.day, tzinfo=_dt.timezone.utc) + _dt.timedelta(days=1)


def frist_bis(stand: str | _dt.date | None, r: dict | None) -> str | None:
    """:func:`frist_ende` als ISO-Zeitpunkt ``JJJJ-MM-TTThh:mm:ssZ`` (für Oberflächen)."""
    t = frist_ende(stand, r)
    return t.strftime("%Y-%m-%dT%H:%M:%SZ") if t else None


def veraltet(stand: str | _dt.date | None, r: dict | None, jetzt: _dt.datetime) -> bool:
    """Ist der Stand zum Zeitpunkt ``jetzt`` älter als die Frist? Ohne Stand oder Regel nie."""
    t = frist_ende(stand, r)
    return t is not None and jetzt > t


# ── Anzeige ────────────────────────────────────────────────────────────────────────────────────────────────────
_TAKT_TEXT = {("de", 1, "h"): "stündlich", ("de", 1, "d"): "täglich", ("de", 1, "w"): "wöchentlich",
              ("de", 1, "mo"): "monatlich", ("de", 3, "mo"): "quartalsweise", ("de", 12, "mo"): "jährlich",
              ("en", 1, "h"): "hourly", ("en", 1, "d"): "daily", ("en", 1, "w"): "weekly",
              ("en", 1, "mo"): "monthly", ("en", 3, "mo"): "quarterly", ("en", 12, "mo"): "yearly"}
_EINHEIT_TEXT = {"de": {"h": "h", "d": "Tage", "w": "Wochen", "mo": "Monate"},
                 "en": {"h": "h", "d": "days", "w": "weeks", "mo": "months"}}


def _g(x: float) -> str:
    return f"{x:g}"


def bezeichnung_takt(takt: tuple[float, str], lang: str = "de") -> str:
    """„täglich“, „monatlich“, „alle 2 Tage“ …"""
    lang = "en" if lang == "en" else "de"
    tw, te = float(takt[0]), takt[1]
    return _TAKT_TEXT.get((lang, tw, te)) or (f"alle {_g(tw)} {_EINHEIT_TEXT['de'][te]}" if lang == "de"
                                              else f"every {_g(tw)} {_EINHEIT_TEXT['en'][te]}")


def bezeichnung_toleranz(toleranz: tuple[float, str], lang: str = "de") -> str:
    """„6 h“, „2 Tage“, „3 Monate“, „bis 6. Arbeitstag nach Periodenende“."""
    ow, oe = float(toleranz[0]), toleranz[1]
    if oe == "bd":
        return (f"bis {_g(ow)}. Arbeitstag nach Periodenende" if lang != "en"
                else f"by business day {_g(ow)} after period end")
    if oe == "mo":
        return f"{_g(ow)} " + ("months" if lang == "en" else "Monate")
    return f"{_g(ow)} " + ("h" if oe == "h" else ("days" if lang == "en" else "Tage"))


def bezeichnung(r: dict | None, lang: str = "de") -> str | None:
    """Kurztext der Regel: „täglich + 6 h“, „monatlich, bis 6. Arbeitstag nach Periodenende“, „48 h“."""
    if not r:
        return None
    if r["art"] == "stunden":
        return f"{_g(float(r['stunden']))} h"
    takt = bezeichnung_takt((r["takt"]["wert"], r["takt"]["einheit"]), lang)
    tol = (r["toleranz"]["wert"], r["toleranz"]["einheit"])
    return f"{takt}, {bezeichnung_toleranz(tol, lang)}" if tol[1] == "bd" else f"{takt} + {bezeichnung_toleranz(tol, lang)}"


# ── ODCS-Eintrag und Ableitung ─────────────────────────────────────────────────────────────────────────────────
def sla_eintrag(takt: tuple[float, str], toleranz: tuple[float, str] | None, *, element: str | None = None,
                description: str | None = None) -> dict:
    """ODCS-v3.2-``slaProperties``-Eintrag des Takts; ohne Toleranz (Leerstelle) ohne ``customProperties``."""
    w, e = takt
    e2: dict[str, Any] = {"property": "frequency", "value": int(w) if float(w).is_integer() else w, "unit": e}
    if element:
        e2["element"] = element
    if toleranz is not None:
        ow, oe = toleranz
        e2["customProperties"] = [{"property": CP_TOLERANZ, "value": int(ow) if float(ow).is_integer() else ow},
                                  {"property": CP_TOLERANZ_EINHEIT, "value": oe}]
    if description:
        e2["description"] = description
    return e2


# ── Kalenderbereich der Datumstabelle (D-802) ──────────────────────────────────────────────────────────────────
#: Mindesthorizont der Datumstabelle über den Datenstand hinaus, in Monaten (Entscheidung Florian 19.10.2026). Plan,
#: Prognose und das Ende einer Frist liegen nach dem Datenstand; endet der Kalender früher, fallen sie aus jeder
#: zeitgefilterten Auswertung.
PROGNOSEHORIZONT_MONATE = 12


def als_datum(v: Any) -> _dt.date:
    """Datum aus ``date``/``datetime``, ``JJJJMMTT`` (DateKey) oder ``JJJJ-MM-TT``."""
    if isinstance(v, _dt.datetime):
        return v.date()
    if isinstance(v, _dt.date):
        return v
    s = str(v)
    if s.isdigit() and len(s) == 8:
        return _dt.date(int(s[:4]), int(s[4:6]), int(s[6:8]))
    return _dt.date.fromisoformat(s[:10])


def horizont_ende(datenstand: Any, horizont_monate: int = PROGNOSEHORIZONT_MONATE) -> _dt.date:
    """Der Tag, bis zu dem der Kalender mindestens reichen muss: Datenstand plus ``horizont_monate``."""
    d = als_datum(datenstand)
    return _monate_spaeter(_dt.datetime(d.year, d.month, d.day), int(horizont_monate)).date()


def kalender_ende(datenstand: Any, fakt_ende: Any = None, horizont_monate: int = PROGNOSEHORIZONT_MONATE) -> _dt.date:
    """Letzter Tag der Datumstabelle: 31.12. des Jahres, in dem der spätere von Datenstand plus Horizont und letztem
    Faktentag (z. B. Plan bis Jahresende) liegt. Volle Jahre sind eine Bedingung an Datumstabellen
    (learn.microsoft.com/power-bi/guidance/model-date-tables), darum das Jahresende statt des Tages selbst."""
    ziel = horizont_ende(datenstand, horizont_monate)
    if fakt_ende is not None:
        ziel = max(ziel, als_datum(fakt_ende))
    return _dt.date(ziel.year, 12, 31)


def kalender_reicht(ende: Any, datenstand: Any, horizont_monate: int = PROGNOSEHORIZONT_MONATE) -> bool:
    """Reicht ein Kalender, der am ``ende`` endet, ``horizont_monate`` über den Datenstand hinaus?"""
    return als_datum(ende) >= horizont_ende(datenstand, horizont_monate)


# ── Feiertage je Region (Arbeitskalender, D-802) ───────────────────────────────────────────────────────────────
def ostersonntag(jahr: int) -> _dt.date:
    """Ostersonntag im gregorianischen Kalender (anonymer gregorianischer Algorithmus, Meeus)."""
    a, b, c = jahr % 19, jahr // 100, jahr % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l_ = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l_) // 451
    monat, tag = divmod(h + l_ - 7 * m + 114, 31)
    return _dt.date(jahr, monat, tag + 1)


def _koningsdag(jahr: int) -> _dt.date:
    """27. April; fällt er auf einen Sonntag, der 26. April (NL, seit 2014)."""
    t = _dt.date(jahr, 4, 27)
    return t - _dt.timedelta(days=1) if t.weekday() == 6 else t


#: Feiertagsregeln je Region: (Name, fester Tag ``(Monat, Tag)`` | Abstand zu Ostersonntag in Tagen | Funktion).
#: Eine Region erbt die Regeln ihres Landes (``DE-BW`` = ``DE`` plus Landesfeiertage). Gegen die Quellen geprüft am
#: 22.10.2026 (BO-458, Belege in ``test_ladetakt_tor.py::test_feiertagsregeln_gegen_den_gesetzestext``):
#: DE = die neun Feiertage, die in allen Ländern gelten (3. Oktober kraft Bundesrecht, Einigungsvertrag Art. 2 Abs. 2;
#: die übrigen acht nach den Feiertagsgesetzen der Länder; Zählung BT-Drucksache 20/3615); DE-BW Feiertagsgesetz BW
#: § 1 (Erscheinungsfest 6. Januar, Fronleichnam, Allerheiligen zusätzlich); NL Algemene termijnenwet Art. 3 Abs. 1
#: und Abs. 2 (Goede Vrijdag ist für Fristen gleichgestellt).
FEIERTAGSREGELN: dict[str, tuple[tuple[str, Any], ...]] = {
    "DE": (("Neujahr", (1, 1)), ("Karfreitag", -2), ("Ostermontag", 1), ("Tag der Arbeit", (5, 1)),
           ("Christi Himmelfahrt", 39), ("Pfingstmontag", 50), ("Tag der Deutschen Einheit", (10, 3)),
           ("1. Weihnachtstag", (12, 25)), ("2. Weihnachtstag", (12, 26))),
    "DE-BW": (("Erscheinungsfest", (1, 6)), ("Fronleichnam", 60), ("Allerheiligen", (11, 1))),
    "NL": (("Nieuwjaarsdag", (1, 1)), ("Goede Vrijdag", -2), ("Tweede Paasdag", 1), ("Koningsdag", _koningsdag),
           ("Bevrijdingsdag", (5, 5)), ("Hemelvaartsdag", 39), ("Tweede Pinksterdag", 50),
           ("Eerste Kerstdag", (12, 25)), ("Tweede Kerstdag", (12, 26))),
}


def feiertage(region: str, von: int, bis: int) -> list[str]:
    """Feiertage der ``region`` (``DE``, ``DE-BW``, ``NL``) von Jahr ``von`` bis ``bis`` als ``JJJJ-MM-TT``, sortiert."""
    land = str(region).split("-")[0]
    if region not in FEIERTAGSREGELN or land not in FEIERTAGSREGELN:
        raise ValueError(f"Region {region!r} unbekannt, bekannt: {sorted(FEIERTAGSREGELN)}")
    if int(bis) < int(von):
        raise ValueError(f"Jahre laufen rückwärts: {von}..{bis}")
    regeln = FEIERTAGSREGELN[land] + (FEIERTAGSREGELN[region] if region != land else ())
    tage: set[_dt.date] = set()
    for jahr in range(int(von), int(bis) + 1):
        ostern = ostersonntag(jahr)
        for _name, r in regeln:
            if isinstance(r, tuple):
                tage.add(_dt.date(jahr, *r))
            elif isinstance(r, int):
                tage.add(ostern + _dt.timedelta(days=r))
            else:
                tage.add(r(jahr))
    return sorted(t.isoformat() for t in tage)


# ── Lieferkopie ────────────────────────────────────────────────────────────────────────────────────────────────
#: Pfad der Lieferkopie relativ zur Repo-Wurzel.
KOPIE = "meridian/semantics/fristregel.py"


def main(argv: list[str] | None = None) -> int:
    """``--kopieren`` schreibt die Lieferkopie :data:`KOPIE` (nur in der Fassung unter ``core/`` sinnvoll)."""
    import argparse
    from pathlib import Path

    ap = argparse.ArgumentParser(description="Fristenregel (D-786): Lieferkopie für Meridian schreiben.")
    ap.add_argument("--kopieren", action="store_true", help=f"{KOPIE} aus dieser Datei schreiben")
    a = ap.parse_args(argv)
    if not a.kopieren:
        ap.print_help()
        return 0
    quelle = Path(__file__).resolve()
    if quelle.parts[-4:-1] != ("core", "dataarch_engine", "blueprint"):
        print("[fristregel] das ist die Lieferkopie; die Fassung unter core/dataarch_engine/blueprint/ aufrufen")
        return 2
    ziel = quelle.parents[3] / KOPIE
    ziel.write_bytes(quelle.read_bytes())
    print(f"[fristregel] {KOPIE} geschrieben")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
