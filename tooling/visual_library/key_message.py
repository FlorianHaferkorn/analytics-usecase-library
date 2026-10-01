"""Kernaussage je Visual, regelbasiert aus den Daten des Visuals (D-623 Nachtrag, feat-109).

Eine Regel je Zweck; jede Zahl im Satz stammt aus der Tabelle, die das Visual zeichnet. Dieselben
Daten ergeben immer denselben Satz. Ohne passende Regel gibt es keine Aussage (None) — nie einen
leeren oder geratenen Satz.

    Kategorienvergleich, nicht additiv (Quote)  schwächster und stärkster Wert nach Richtung
    Kategorienvergleich, additiv (Beitrag)      größter Beitrag mit Anteil an der Summe
    Zeitvergleich mit Plan                      letzte Periode: Ist gegen Plan, Abstand
    Zeitreihe ohne Plan                         erste gegen letzte Periode, Veränderung
    Verteilung (purpose distribution)           Median und mittlere Hälfte, Ausreißer je Kategorie
    Zusammenhang (roles x, y)                   Korrelation r mit Stärke und Richtung

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


def en_number(v: float, digits: int, signed: bool = False) -> str:
    """Zahl in englischer Schreibweise: Tausenderkomma, Dezimalpunkt, echtes Minus."""
    s = f"{abs(v):,.{digits}f}"
    if v < 0 and s.strip("0,.") != "":
        return MINUS + s
    return ("+" + s) if signed and v > 0 else s


#: Sprachen der Kernaussage; `lang` wählt die Texte, `rule` bleibt sprachunabhängig (Schlüssel).
LANGS = ("de", "en")

#: Alle Satzbausteine je Sprache; key_message.ts führt dieselbe Tabelle.
TEXTS: dict[str, dict[str, str]] = {
    "de": {
        "week": "KW", "pp": "PP", "folded": " (in „Übrige“)",
        "weakest": "Am schwächsten: ", "strongest": ", am stärksten: ", "at": " mit ",
        "biggest": "Größter Beitrag: ", "share": ", das sind ", "of_total": " der Summe.",
        "of_abs_total": " der Summe der Beträge.",
        "actual": ": Ist ", "vs_plan": " gegen Plan ", "above": "über", "below": "unter", "plan_end": " Plan.",
        "on_plan": " genau auf Plan.", "to": " bis ", "unchanged": "unverändert bei ", "from_to": " auf ",
        "median": "Median ", "middle": ", die mittlere Hälfte liegt zwischen ", "and": " und ",
        "notable": " Auffällig: ",
        "corr": "Zusammenhang zwischen ", "points": " Punkte.",
        "weak": "schwach", "moderate": "mittel", "strong": "stark", "positive": "positiv", "negative": "negativ",
    },
    "en": {
        "week": "Week", "pp": "pp", "folded": " (in “Other”)",
        "weakest": "Weakest: ", "strongest": ", strongest: ", "at": " at ",
        "biggest": "Largest contribution: ", "share": ", i.e. ", "of_total": " of the total.",
        "of_abs_total": " of the sum of absolute values.",
        "actual": ": actual ", "vs_plan": " vs. plan ", "above": "above", "below": "below", "plan_end": " plan.",
        "on_plan": " exactly on plan.", "to": " to ", "unchanged": "unchanged at ", "from_to": " to ",
        "median": "Median ", "middle": ", middle half between ", "and": " and ",
        "notable": " Notable: ",
        "corr": "Correlation between ", "points": " points.",
        "weak": "weak", "moderate": "moderate", "strong": "strong", "positive": "positive", "negative": "negative",
    },
}


def _lang(lang: str) -> str:
    if lang not in LANGS:
        raise ValueError(f"Sprache {lang!r} unbekannt (erlaubt: {', '.join(LANGS)})")
    return lang


def fmt_number(v: float, digits: int, signed: bool = False, lang: str = "de") -> str:
    """Zahl in der Schreibweise der Sprache (`de_number` bzw. `en_number`)."""
    return (en_number if _lang(lang) == "en" else de_number)(v, digits, signed)


def _with_unit(text: str, unit: str, lang: str = "de") -> str:
    """Einheit mit geschütztem Leerzeichen; Englisch setzt „%“ ohne Abstand („33.6%“)."""
    if not unit:
        return text
    return f"{text}{unit}" if lang == "en" and unit == "%" else f"{text}\u00a0{unit}"


def _delta_unit(unit: str, lang: str = "de") -> str:
    """Abstand zweier Quoten in Prozentpunkten (IBCS: Δ in PP, nicht in %)."""
    return TEXTS[lang]["pp"] if unit == "%" else unit


def period_label(value: Any, weekly: bool = False, lang: str = "de") -> str:
    """ISO-Datum als „KW nn“/„Week nn“ (Wochenreihe) oder „TT.MM.JJJJ“/„JJJJ-MM-TT“; sonst unverändert."""
    try:
        d = dt.date.fromisoformat(str(value)[:10])
    except ValueError:
        return str(value)
    if weekly:
        return f"{TEXTS[lang]['week']} {d.isocalendar()[1]:02d}"
    return d.isoformat() if lang == "en" else d.strftime("%d.%m.%Y")


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
#: Je Sprache in TEXTS[lang]["folded"]; FOLDED bleibt die deutsche Fassung.
FOLDED = TEXTS["de"]["folded"]


def _categories(table: dict, roles: dict, polarity: float, additive: bool, unit: str,
                top_n: "int | None", lang: str) -> "dict | None":
    T = TEXTS[lang]
    cat, val = roles["category"], roles["value"]
    pairs = [(c, v) for c, v in zip(_column(table, cat), map(_num, _column(table, val))) if v is not None]
    if len(pairs) < 2:
        return None
    n = places([v for _, v in pairs])

    def fmt(v: float) -> str:
        return _with_unit(fmt_number(v, n, lang=lang), unit, lang)
    # Sichtbar sind wie in render.with_top_n die schwächsten top_n nach Richtung; der Rest ist „Übrige“.
    ranked = sorted(pairs, key=lambda p: p[1], reverse=polarity < 0)
    shown = {id(p) for p in ranked[:top_n]} if top_n and len(pairs) > top_n else {id(p) for p in pairs}

    def where(p) -> str:
        return "" if id(p) in shown else T["folded"]
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
                "segments": _seg(T["biggest"], (str(name),), where(biggest), T["at"], (fmt(top),), T["share"],
                                 (_with_unit(str(share), "%", lang),),
                                 T["of_abs_total"] if mixed else T["of_total"]),
                "highlight": {"field": cat, "values": [name], "temporal": False}}
    (worst, wv), (best, bv) = ranked[0], ranked[-1]
    if wv == bv:
        return None
    return {"rule": "schwächster Wert",
            "segments": _seg(T["weakest"], (str(worst),), where(ranked[0]), T["at"], (fmt(wv),),
                             T["strongest"], (str(best),), where(ranked[-1]), T["at"], (fmt(bv),), "."),
            "highlight": {"field": cat, "values": [worst], "temporal": False}}


def _time(table: dict, roles: dict, unit: str, weekly: bool, lang: str) -> "dict | None":
    T = TEXTS[lang]
    time, val = roles["time"], roles["value"]
    periods, actual = _column(table, time), [_num(v) for v in _column(table, val)]
    plan = [_num(v) for v in _column(table, roles["plan"])] if roles.get("plan") else None
    idx = [i for i, a in enumerate(actual) if a is not None and (plan is None or plan[i] is not None)]
    if not idx:
        return None
    last = idx[-1]
    du = _delta_unit(unit, lang)

    def label(i: int) -> str:
        return period_label(periods[i], weekly, lang)

    def fmt(v: float, u: str = unit, signed: bool = False) -> str:
        return _with_unit(fmt_number(v, n, signed, lang), u, lang)
    if plan is not None:
        a, p = actual[last], plan[last]
        n = places([a, p])
        gap = a - p
        tail = ((" ", (fmt(abs(gap), du),), f" {T['above'] if gap > 0 else T['below']}{T['plan_end']}") if gap
                else (T["on_plan"],))
        return {"rule": "letzte Periode gegen Plan",
                "segments": _seg(f"{label(last)}{T['actual']}", (fmt(a),), T["vs_plan"], (fmt(p),), ",", *tail),
                "highlight": {"field": time, "values": [periods[last]], "temporal": True}}
    first = idx[0]
    if first == last:
        return None
    a0, a1 = actual[first], actual[last]
    n = places([a0, a1])
    span = f"{label(first)}{T['to']}{label(last)}: "
    if de_number(a1 - a0, n) in ("0", "0," + "0" * n):
        return {"rule": "Veränderung im Zeitraum",
                "segments": _seg(span, T["unchanged"], (fmt(a1),), "."),
                "highlight": {"field": time, "values": [periods[first], periods[last]], "temporal": True}}
    return {"rule": "Veränderung im Zeitraum",
            "segments": _seg(span, (fmt(a0),), T["from_to"], (fmt(a1),), ", ", (fmt(a1 - a0, du, True),), "."),
            "highlight": {"field": time, "values": [periods[first], periods[last]], "temporal": True}}


def quantile(sorted_values: list[float], q: float) -> float:
    """Quantil mit linearer Interpolation (wie numpy „linear“); identisch in key_message.ts."""
    pos = (len(sorted_values) - 1) * q
    lo = int(pos)
    frac = pos - lo
    if lo + 1 >= len(sorted_values):
        return sorted_values[lo]
    return sorted_values[lo] + (sorted_values[lo + 1] - sorted_values[lo]) * frac


def _distribution(table: dict, roles: dict, unit: str, lang: str) -> "dict | None":
    T = TEXTS[lang]
    val, cat = roles["value"], roles.get("category")
    vals = [_num(v) for v in _column(table, val)]
    cats = _column(table, cat) if cat else [None] * len(vals)
    pairs = [(c, v) for c, v in zip(cats, vals) if v is not None]
    if len(pairs) < 4:
        return None
    s = sorted(v for _, v in pairs)
    q1, med, q3 = quantile(s, 0.25), quantile(s, 0.5), quantile(s, 0.75)
    n = places([v for _, v in pairs])

    def fmt(v: float) -> str:
        return _with_unit(fmt_number(v, n, lang=lang), unit, lang)
    fence = 1.5 * (q3 - q1)
    out = [p for p in pairs if p[1] < q1 - fence or p[1] > q3 + fence] if cat else []
    seg = [T["median"], (fmt(med),), T["middle"], (fmt(q1),), T["and"], (fmt(q3),), "."]
    if out:
        far = max(out, key=lambda p: abs(p[1] - med))
        seg += [T["notable"], (str(far[0]),), T["at"], (fmt(far[1]),), "."]
    return {"rule": "Verteilung", "segments": _seg(*seg),
            "highlight": {"field": cat or val, "values": [c for c, _ in out] if cat else [], "temporal": False}}


def _strength(r: float, lang: str = "de") -> str:
    a = abs(r)
    return TEXTS[lang]["weak" if a < 0.3 else "moderate" if a < 0.7 else "strong"]


def _correlation(table: dict, roles: dict, lang: str) -> "dict | None":
    T = TEXTS[lang]
    xs, ys = [_num(v) for v in _column(table, roles["x"])], [_num(v) for v in _column(table, roles["y"])]
    pts = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(pts) < 3:
        return None
    mx = sum(x for x, _ in pts) / len(pts)
    my = sum(y for _, y in pts) / len(pts)
    sxy = sum((x - mx) * (y - my) for x, y in pts)
    sxx = sum((x - mx) ** 2 for x, _ in pts)
    syy = sum((y - my) ** 2 for _, y in pts)
    if not sxx or not syy:
        return None
    r = sxy / math.sqrt(sxx * syy)
    richtung = T["positive"] if r > 0 else T["negative"]
    return {"rule": "Zusammenhang",
            "segments": _seg(f"{T['corr']}{roles['x']}{T['and']}{roles['y']}: r = ", (fmt_number(r, 2, lang=lang),),
                             f" ({_strength(r, lang)}, {richtung}), ", (str(len(pts)),), T["points"]),
            "highlight": {"field": roles["x"], "values": [], "temporal": False}}


def key_message(table: dict, roles: dict, *, polarity: float = 1, additive: bool = False, unit: str = "",
                weekly: bool = False, top_n: "int | None" = None, purpose: "str | None" = None,
                lang: str = "de") -> "dict | None":
    """Kernaussage für die Tabelle eines Visuals.

    table     {"columns": [{"name"}...], "rows": [[...]...]} — dieselbe Tabelle, die das Visual zeichnet
    roles     {Rolle: Spalte} wie bei `render_target(bindings=)`: time/value/plan oder category/value
    polarity  1 = mehr ist besser, −1 = weniger ist besser (Richtung der Kennzahl)
    additive  Werte summieren sich (Beiträge), sonst Quote oder Stand
    purpose   Zweck des Visuals (Visual Library); `distribution` wählt die Verteilungsregel
    top_n     so viele Kategorien zeigt das Chart, der Rest steckt in „Übrige“; genannte Werte von dort
              tragen den Zusatz „(in „Übrige“)“ bzw. „(in “Other”)“
    lang      Sprache des Satzes: "de" (Vorgabe) oder "en"; anderes wirft ValueError. `rule` bleibt deutsch
              (Schlüssel, kein Text).
    """
    _lang(lang)
    if roles.get("time") and roles.get("value"):
        return _time(table, roles, unit, weekly, lang)
    if roles.get("x") and roles.get("y"):
        return _correlation(table, roles, lang)
    if roles.get("value") and purpose == "distribution":
        return _distribution(table, roles, unit, lang)
    if roles.get("category") and roles.get("value"):
        return _categories(table, roles, polarity, additive, unit, top_n, lang)
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
