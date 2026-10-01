"""Kernaussage je Visual, regelbasiert aus den Daten des Visuals (D-623 Nachtrag, feat-109).

Eine Regel je Zweck; jede Zahl im Satz stammt aus der Tabelle, die das Visual zeichnet. Dieselben
Daten ergeben immer denselben Satz. Ohne passende Regel gibt es keine Aussage (None) — nie einen
leeren oder geratenen Satz.

    Kategorienvergleich, nicht additiv (Quote)  schwächster und stärkster Wert nach Richtung
    Kategorienvergleich, additiv (Beitrag)      größter Beitrag mit Anteil an der Summe
    Zeitvergleich mit Plan                      letzte Periode: Ist gegen Plan, Abstand
    Zeitreihe ohne Plan                         erste gegen letzte Periode, Veränderung

Ergebnis: {"rule", "segments": [{"text", "strong"}], "highlight": {"field", "values", "temporal"}}.
Zweite Fassung: key_message.ts (Browser, rechnet auf der gefilterten Tabelle nach); Gleichstand erzwingt
test_key_message.py über key_message_cases.json.
`segments` trennt Zahlen und Namen (fett) vom Fließtext, damit jede Oberfläche sie selbst setzt.
`highlight` geht unverändert an `render_target(params={"highlight": ...})`.
"""
from __future__ import annotations

import datetime as dt
import math
from typing import Any

MINUS = "−"


def _num(v: Any) -> "float | None":
    if isinstance(v, bool) or v is None or v == "":
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) else f


#: Höchstens eine Nachkommastelle, wie die Datenbeschriftung der Charts: der Satz nennt dieselbe Zahl,
#: die am Balken steht (Cockpit 01.10.2026: vorher „27,95 %“ im Satz). Gerundet wird wie Vega (`toFixed`
#: auf der Binärzahl): 27,95 wird 27,9.
MAX_PLACES = 1


def places(values: list[float], cap: int = MAX_PLACES) -> int:
    """Nachkommastellen, die die Daten führen (höchstens `cap`)."""
    out = 0
    for v in values:
        if not float(v).is_integer():
            out = max(out, min(cap, len(repr(float(v)).split(".")[1])))
    return out


def de_number(v: float, digits: int, signed: bool = False) -> str:
    """Zahl in deutscher Schreibweise: Tausenderpunkt, Dezimalkomma, echtes Minus."""
    s = f"{abs(v):,.{digits}f}".replace(",", " ").replace(".", ",").replace(" ", ".")
    if v < 0 and s.strip("0,.") != "":
        return MINUS + s
    return ("+" + s) if signed and v > 0 else s


def _with_unit(text: str, unit: str) -> str:
    return f"{text} {unit}" if unit else text


def _delta_unit(unit: str) -> str:
    """Abstand zweier Quoten in Prozentpunkten (IBCS: Δ in PP, nicht in %)."""
    return "PP" if unit == "%" else unit


def period_label(value: Any, weekly: bool = False) -> str:
    """ISO-Datum als „KW nn“ (Wochenreihe) oder „TT.MM.JJJJ“; alles andere unverändert."""
    try:
        d = dt.date.fromisoformat(str(value)[:10])
    except ValueError:
        return str(value)
    return f"KW {d.isocalendar()[1]:02d}" if weekly else d.strftime("%d.%m.%Y")


def _column(table: dict, name: str) -> list:
    names = [c["name"] for c in table.get("columns") or []]
    if name not in names:
        raise KeyError(f"Spalte {name!r} fehlt in der Tabelle ({names})")
    i = names.index(name)
    return [r[i] for r in table.get("rows") or []]


def _seg(*parts: "str | tuple[str]") -> list[dict]:
    """Fließtext als str, Hervorgehobenes als 1-Tupel."""
    return [{"text": p[0], "strong": True} if isinstance(p, tuple) else {"text": p, "strong": False}
            for p in parts]


#: Zusatz, wenn ein genannter Wert im Chart in der Restzeile steckt (Entscheidung Florian 01.10.2026, BO-007).
FOLDED = " (in „Übrige“)"


def _categories(table: dict, roles: dict, polarity: float, additive: bool, unit: str,
                top_n: "int | None") -> "dict | None":
    cat, val = roles["category"], roles["value"]
    pairs = [(c, v) for c, v in zip(_column(table, cat), map(_num, _column(table, val))) if v is not None]
    if len(pairs) < 2:
        return None
    n = places([v for _, v in pairs])
    # Sichtbar sind wie in render.with_top_n die schwächsten top_n nach Richtung; der Rest ist „Übrige“.
    ranked = sorted(pairs, key=lambda p: p[1], reverse=polarity < 0)
    shown = {id(p) for p in ranked[:top_n]} if top_n and len(pairs) > top_n else {id(p) for p in pairs}

    def where(p) -> str:
        return "" if id(p) in shown else FOLDED
    if additive:
        total = sum(v for _, v in pairs)
        biggest = max(pairs, key=lambda p: abs(p[1]))
        name, top = biggest
        # Gemischte Vorzeichen: Anteil an der Summe der Beträge, sonst stünde „−40, das sind −400 % der Summe“.
        mixed = any(v < 0 for _, v in pairs) and any(v > 0 for _, v in pairs)
        base = sum(abs(v) for _, v in pairs) if mixed else total
        if not base:
            return None
        share = round(100 * abs(top) / abs(base))
        return {"rule": "größter Beitrag",
                "segments": _seg("Größter Beitrag: ", (str(name),), where(biggest), " mit ",
                                 (_with_unit(de_number(top, n), unit),), ", das sind ", (f"{share}\u00a0%",),
                                 " der Summe der Beträge." if mixed else " der Summe."),
                "highlight": {"field": cat, "values": [name], "temporal": False}}
    (worst, wv), (best, bv) = ranked[0], ranked[-1]
    if wv == bv:
        return None
    return {"rule": "schwächster Wert",
            "segments": _seg("Am schwächsten: ", (str(worst),), where(ranked[0]), " mit ",
                             (_with_unit(de_number(wv, n), unit),), ", am stärksten: ", (str(best),), where(ranked[-1]),
                             " mit ", (_with_unit(de_number(bv, n), unit),), "."),
            "highlight": {"field": cat, "values": [worst], "temporal": False}}


def _time(table: dict, roles: dict, unit: str, weekly: bool) -> "dict | None":
    time, val = roles["time"], roles["value"]
    periods, actual = _column(table, time), [_num(v) for v in _column(table, val)]
    plan = [_num(v) for v in _column(table, roles["plan"])] if roles.get("plan") else None
    idx = [i for i, a in enumerate(actual) if a is not None and (plan is None or plan[i] is not None)]
    if not idx:
        return None
    last = idx[-1]
    du = _delta_unit(unit)
    if plan is not None:
        a, p = actual[last], plan[last]
        n = places([a, p])
        gap = a - p
        where = "über" if gap > 0 else "unter" if gap < 0 else "auf"
        tail = (" ", (_with_unit(de_number(abs(gap), n), du),), f" {where} Plan.") if gap else (" genau auf Plan.",)
        return {"rule": "letzte Periode gegen Plan",
                "segments": _seg(f"{period_label(periods[last], weekly)}: Ist ", (_with_unit(de_number(a, n), unit),),
                                 " gegen Plan ", (_with_unit(de_number(p, n), unit),), ",", *tail),
                "highlight": {"field": time, "values": [periods[last]], "temporal": True}}
    first = idx[0]
    if first == last:
        return None
    a0, a1 = actual[first], actual[last]
    n = places([a0, a1])
    span = f"{period_label(periods[first], weekly)} bis {period_label(periods[last], weekly)}: "
    if de_number(a1 - a0, n) in ("0", "0," + "0" * n):
        return {"rule": "Veränderung im Zeitraum",
                "segments": _seg(span, "unverändert bei ", (_with_unit(de_number(a1, n), unit),), "."),
                "highlight": {"field": time, "values": [periods[first], periods[last]], "temporal": True}}
    return {"rule": "Veränderung im Zeitraum",
            "segments": _seg(f"{period_label(periods[first], weekly)} bis {period_label(periods[last], weekly)}: ",
                             (_with_unit(de_number(a0, n), unit),), " auf ", (_with_unit(de_number(a1, n), unit),),
                             ", ", (_with_unit(de_number(a1 - a0, n, signed=True), du),), "."),
            "highlight": {"field": time, "values": [periods[first], periods[last]], "temporal": True}}


def key_message(table: dict, roles: dict, *, polarity: float = 1, additive: bool = False, unit: str = "",
                weekly: bool = False, top_n: "int | None" = None) -> "dict | None":
    """Kernaussage für die Tabelle eines Visuals.

    table     {"columns": [{"name"}...], "rows": [[...]...]} — dieselbe Tabelle, die das Visual zeichnet
    roles     {Rolle: Spalte} wie bei `render_target(bindings=)`: time/value/plan oder category/value
    polarity  1 = mehr ist besser, −1 = weniger ist besser (Richtung der Kennzahl)
    additive  Werte summieren sich (Beiträge), sonst Quote oder Stand
    top_n     so viele Kategorien zeigt das Chart, der Rest steckt in „Übrige“; genannte Werte von dort
              tragen den Zusatz „(in „Übrige“)“
    """
    if roles.get("time") and roles.get("value"):
        return _time(table, roles, unit, weekly)
    if roles.get("category") and roles.get("value"):
        return _categories(table, roles, polarity, additive, unit, top_n)
    return None


def highlight_keys(highlight: dict) -> list:
    """Werte für den Vega-Parameter `kernaussage_werte`: Zeitpunkte als ms (UTC), sonst unverändert."""
    if not highlight.get("temporal"):
        return list(highlight["values"])
    out = []
    for v in highlight["values"]:
        d = dt.date.fromisoformat(str(v)[:10])
        out.append(int(dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc).timestamp() * 1000))
    return out


def plain_text(message: dict) -> str:
    """Der Satz ohne Auszeichnung (Screenreader, Export, Tests)."""
    return "".join(s["text"] for s in message["segments"])
