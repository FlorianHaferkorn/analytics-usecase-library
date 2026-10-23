"""
sap_calendar — die Zeitachse des Sternschemas: erzeugt statt aus SAP gezogen.

Bis 31.07.2026 hatte das generierte Gold-Modell keine Kalendertabelle. Die Fakten trugen seit
der Kopfvererbung zwar Datumsspalten, aber es gab nichts, woran sie haengen. Der Regelkatalog
meldete das (SM004, kritisch) und hatte recht: ohne dedizierte Datumsdimension gibt es keine
Zeitintelligenz und streng genommen kein Sternschema, weil eine Achse fehlt.

Vier Bedingungen an eine Datumstabelle, alle belegt
--------------------------------------------------
Microsoft nennt sie ausdruecklich (`learn.microsoft.com/power-bi/guidance/model-date-tables`):
die Datumsspalte ist vom Typ Datum, **eindeutig**, **ohne Leerwerte**, **luecken los** und
**deckt volle Jahre ab**. Die ersten drei fallen bei einer erzeugten Sequenz von selbst an; die
vierte ist eine Bedingung an den *Bereich* und wird hier geprueft, nicht gehofft.

Warum erzeugt und nicht aus SAP
-------------------------------
SAP hat keine Kalendertabelle, die diese vier Bedingungen erfuellt. Was es gibt (Fabrikkalender,
T009/T009B fuer die Geschaeftsjahresvariante) sind Konfigurationstabellen mit anderem Zweck.
Microsoft empfiehlt fuer die Datumstabelle ohnehin die Erzeugung. Deshalb ist diese Tabelle die
einzige im Gold-Modell **ohne** SAP-Herkunft — und damit auch die einzige, deren SQL kein
`TODO(contract:)` traegt, sondern ausfuehrbar ist.

Warum sie physisch in der Lakehouse-Schicht liegt
-------------------------------------------------
Microsofts eigenes Kalender-Beispiel baut eine **berechnete** Tabelle (`partition = calculated`,
`CALENDAR(...)`). Das geht hier nicht: das Modell wird im Direct-Lake-Modus ausgeliefert, und
Direct Lake on SQL unterstuetzt berechnete Tabellen nicht (Direct Lake on OneLake erst in der
Vorschau) — `learn.microsoft.com/fabric/fundamentals/direct-lake-overview`. Die Kalendertabelle
muss also als Delta-Tabelle in Gold materialisiert werden. Dass eine eigene Datumstabelle
markiert und ueber Datumsspalten verbunden wird, ist in beiden Direct-Lake-Varianten
ausdruecklich unterstuetzt.

Was hier NICHT entschieden wird
-------------------------------
Welches Datum eines Faktums die fuehrende Achse ist. Eine Rechnungszeile hat Belegdatum und
Buchungsdatum, eine Einteilung ein aktuelles und ein urspruenglich zugesagtes Lieferdatum. Diese
Wahl ist Fachlichkeit und keine Ableitung — sie steht als ``date_axis`` mit Begruendung im Paket
und wird hier nur gelesen. Ohne Deklaration entsteht keine Beziehung.

Die Geschaeftsjahresvariante (Perioden, verschobener Jahresanfang) bleibt bewusst aussen vor: sie
haengt an T009/T009B je Buchungskreis und ist ohne Systemzugriff nicht ableitbar. Der Kalender
traegt deshalb Kalenderjahre; die Fiskalspalten sind eine benannte Luecke, keine geratene Spalte.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from core.dataarch_engine.blueprint.fristregel import PROGNOSEHORIZONT_MONATE
from core.dataarch_engine.blueprint.naming import layer_ref
from core.dataarch_engine.blueprint.provision_notebooks import ERZEUGT_ORDNER

CALENDAR_TABLE = "dim_date"
DATE_COLUMN = "Date"
#: Wert von ``erzeugung.art`` am Katalogeintrag (D-819).
ERZEUGUNG_KALENDER = "kalender"

# Voreinstellung des Bereichs. Volle Jahre (1. Januar bis 31. Dezember) ist Bedingung, nicht Stil.
DEFAULT_FROM_YEAR = 2015
DEFAULT_TO_YEAR = 2035

_MONTHS = ["January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"]
_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Spalte -> (logischer Typ, Beschreibung, Sortierspalte)
_COLUMNS: list[tuple[str, str, str, str]] = [
    ("Date", "date", "Kalendertag — der Schluessel der Dimension", ""),
    ("Year", "integer", "Kalenderjahr", ""),
    ("Quarter", "integer", "Quartal 1-4", ""),
    ("QuarterName", "string", "Quartal als '2026-Q3'", ""),
    ("Month", "integer", "Monat 1-12", ""),
    ("MonthName", "string", "Monatsname (englisch, sortiert nach Month)", "Month"),
    ("YearMonth", "string", "Jahr und Monat als '2026-07'", ""),
    ("Day", "integer", "Tag im Monat", ""),
    ("DayOfWeek", "integer", "Wochentag nach ISO — 1 = Montag", ""),
    ("DayName", "string", "Wochentagsname (englisch, sortiert nach DayOfWeek)", "DayOfWeek"),
    ("ISOWeek", "integer", "Kalenderwoche nach ISO 8601", ""),
    ("IsWeekend", "boolean", "Samstag oder Sonntag", ""),
]


def calendar_columns() -> list[str]:
    return [c[0] for c in _COLUMNS]


# --------------------------------------------------------------------------- die Deklaration lesen
def date_axes(packs: list[dict] | None) -> list[dict[str, Any]]:
    """Die deklarierten Zeitachsen: je Faktum hoechstens eine, in Paket-/Objektreihenfolge.

    Gelesen, nicht abgeleitet. Ein Faktum ohne ``date_axis`` bekommt keine Kante — lieber ein
    sichtbar fehlendes Faktum als eine geratene Achse.
    """
    achsen: list[dict[str, Any]] = []
    for p in packs or []:
        for obj in p.get("objects") or []:
            gold = obj.get("gold") or {}
            axis = obj.get("date_axis")
            if not axis or gold.get("kind") not in ("fact", "aggregate"):
                continue
            achsen.append({"fact": gold.get("name"), "object": obj.get("id"),
                           "field": axis.get("field"), "rationale": axis.get("rationale", ""),
                           "alternatives": list(axis.get("alternatives") or [])})
    return sorted(achsen, key=lambda a: (str(a["fact"]), str(a["field"])))


def facts_without_axis(packs: list[dict] | None) -> list[dict[str, Any]]:
    """Fakten ohne Zeitachse, mit dem Grund. Nicht jeder Fall ist ein Defekt: ein Bestandsstand
    (MBEW) ist eine Momentaufnahme und hat kein Ereignisdatum. Wer die Faelle nicht trennt, liest
    dieselbe Zeile einmal als Eigenschaft und einmal als Luecke."""
    offen: list[dict[str, Any]] = []
    for p in packs or []:
        for obj in p.get("objects") or []:
            gold = obj.get("gold") or {}
            if gold.get("kind") not in ("fact", "aggregate") or obj.get("date_axis"):
                continue
            datumsspalten = [c.get("sap_field") for c in obj.get("columns") or []
                             if c.get("logical_type") == "date"]
            offen.append({"fact": gold.get("name"), "object": obj.get("id"),
                          "date_columns": datumsspalten,
                          "reason": obj.get("no_date_axis", "")})
    return sorted(offen, key=lambda o: str(o["fact"]))


# --------------------------------------------------------------------------- Katalog + Beziehungen
def calendar_catalog_table(domain: str = "Conformed",
                           axes: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Der Eintrag fuer den governten Katalog. ``generated`` unterscheidet ihn von jeder anderen
    Gold-Tabelle: es gibt keine Silber-Quelle und keine SAP-Herkunft, die man nachschlagen koennte.

    ``erzeugung`` (D-819) traegt, woraus der Bereich zur Laufzeit entsteht: die gebundenen Achsen. Daraus
    schreibt ``erzeugte_transforms`` den Gold-Schritt der Ladung."""
    return {
        "name": CALENDAR_TABLE,
        "kind": "dimension",
        "domain": domain,
        "generated": True,
        "erzeugung": {"art": ERZEUGUNG_KALENDER,
                      "achsen": [{"fact": a["fact"], "field": a["field"]} for a in axes or []
                                 if a.get("fact") and a.get("field")]},
        "grain": "one row per calendar day",
        "columns": calendar_columns(),
        "column_types": {n: t for n, t, _d, _s in _COLUMNS},
        "measure_columns": [],
        "balance_measures": [],
        "source_key": [DATE_COLUMN],
        "key": [DATE_COLUMN],
        "column_descriptions": {n: d for n, _t, d, _s in _COLUMNS},
        "sort_by": {n: s for n, _t, _d, s in _COLUMNS if s},
    }


def calendar_relationships(axes: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Je deklarierter Achse eine Kante Faktum → Kalender."""
    return [{"from_table": a["fact"], "from_column": a["field"],
             "to_table": CALENDAR_TABLE, "to_column": DATE_COLUMN}
            for a in axes if a.get("fact") and a.get("field")]


def dropped_axes(axes: list[dict[str, Any]], tables: list[dict]) -> list[dict[str, Any]]:
    """Deklarierte Achsen, deren Spalte die Projektion nicht ueberlebt hat.

    Das passiert, wenn das Feld unter ``high_confidence_only`` faellt: die Achse steht im Paket,
    die Spalte fehlt im Gold, und die Beziehung kann nicht entstehen. Ein stiller Skip waere hier
    das Schlimmste — das Faktum haette dann keine Zeitachse, und nichts im Ergebnis wuerde das
    sagen. Genau so ist es am 31.07.2026 mit `fact_gl_line.BUDAT` passiert; aufgefallen ist es
    nur, weil ein Test die Zahl der Kanten gegen die Zahl der Achsen gehalten hat.
    """
    spalten = {t["name"]: set(t.get("columns") or []) for t in tables}
    return [{**a, "why": ("Spalte nicht in der Gold-Projektion — vermutlich unter "
                          "`high_confidence_only` gefallen. Feld am Zielsystem bestaetigen, "
                          "Konfidenz im Paket anheben, dann entsteht die Kante.")}
            for a in axes
            if a.get("fact") and a.get("field")
            and a["field"] not in spalten.get(a["fact"], set())]


# --------------------------------------------------------------------------- der ausfuehrbare Teil
def _range(from_year: int, to_year: int) -> tuple[date, date]:
    if to_year < from_year:
        raise ValueError(f"Kalenderbereich laeuft rueckwaerts: {from_year}..{to_year}")
    return date(from_year, 1, 1), date(to_year, 12, 31)


def _case(expr: str, werte: list[str], ab: int = 1) -> str:
    zweige = " ".join(f"WHEN {ab + i} THEN '{w}'" for i, w in enumerate(werte))
    return f"CASE {expr} {zweige} END"


def _zitiere_datum(stack: str) -> str:
    """Die Datumsspalte der Dimension als Bezeichner: Snowflake legt sie in Anfuehrungszeichen an."""
    return f'"{DATE_COLUMN}"' if stack == "snowflake" else f"`{DATE_COLUMN}`"


def _achsdatum(spalte: str, stack: str) -> str:
    """Ein Achsenwert als Datum. Das SAP-Gold traegt Datumsfelder als DATS-Text ``JJJJMMTT`` (gemessen 21.10.2026
    am Stratus-Gold: 19 von 19 Achsen VARCHAR); ein Datum oder Zeitstempel kommt so durch. Ohne Umwandlung
    scheitert ``ADD_MONTHS`` am Text, und ein Vergleich mit einem Datum ergibt in Spark NULL statt eines Befunds."""
    text = f"TO_VARCHAR({spalte})" if stack == "snowflake" else f"CAST({spalte} AS STRING)"
    fmt = "YYYYMMDD" if stack == "snowflake" else "yyyyMMdd"
    return f"CASE WHEN LENGTH({text}) = 8 THEN TO_DATE({text}, '{fmt}') ELSE CAST({spalte} AS DATE) END"


def _achsfilter(spalte: str, stack: str) -> str:
    """Belegte Achsenwerte: SAP schreibt ein leeres Datum als ``00000000``, das kein Tag ist."""
    text = f"TO_VARCHAR({spalte})" if stack == "snowflake" else f"CAST({spalte} AS STRING)"
    return f"{spalte} IS NOT NULL AND {text} NOT IN ('', '00000000')"


def _bereich_cte(axes: list[dict[str, Any]], stack: str, from_year: int, to_year: int,
                 schemas: bool) -> list[str]:
    """``achsen`` und ``bereich`` (D-819): der Kalender reicht vom 1. Januar des fruehesten Achsenwerts bis zum
    31. Dezember des Jahres, in dem der spaeteste Achsenwert plus Horizont liegt — dieselbe Regel wie
    ``fristregel.kalender_ende``. Ohne Achse oder ohne Werte gilt der Rueckfallbereich."""
    von, bis = _range(from_year, to_year)
    make = "DATE_FROM_PARTS" if stack == "snowflake" else "MAKE_DATE"
    lit = (lambda d: f"TO_DATE('{d.isoformat()}')") if stack == "snowflake" else (lambda d: f"DATE '{d.isoformat()}'")
    if not axes:
        return [f"WITH bereich AS (SELECT {lit(von)} AS von, {lit(bis)} AS bis)"]
    teile = [f"    SELECT MIN({_achsdatum(a['field'], stack)}) AS erster, MAX({_achsdatum(a['field'], stack)}) AS letzter "
             f"FROM {layer_ref('gold', a['fact'], schemas)} WHERE {_achsfilter(a['field'], stack)}" for a in axes]
    return (["WITH achsen AS ("] + ["\n    UNION ALL\n".join(teile)] + ["), bereich AS ("] + [
        f"    SELECT COALESCE({make}(YEAR(MIN(erster)), 1, 1), {lit(von)}) AS von,",
        f"           COALESCE({make}(YEAR(ADD_MONTHS(MAX(letzter), {PROGNOSEHORIZONT_MONATE})), 12, 31), "
        f"{lit(bis)}) AS bis",
        "    FROM achsen", ")"])


def calendar_sql(stack: str = "fabric", from_year: int = DEFAULT_FROM_YEAR,
                 to_year: int = DEFAULT_TO_YEAR, gold_table: str = "gold_dim_date",
                 axes: list[dict[str, Any]] | None = None, schemas: bool = False) -> str:
    """Der Kalender als ausfuehrbares SQL — volle Jahre, luecken los, eindeutig by construction.

    Kein Platzhalter: diese Tabelle haengt an keinem Kundensystem, also gibt es nichts zu mappen.
    Den Bereich rechnet das SQL zur Laufzeit aus den deklarierten Achsen (D-819); ``from_year`` und
    ``to_year`` sind nur noch der Rueckfall ohne Achse oder ohne Werte. Zur Bauzeit gibt es keine Daten —
    deshalb steht die Regel im SQL und nicht ihr Ergebnis. Der Kalender laeuft als letzter Gold-Schritt jeder
    Ladung; ``coverage_sql`` misst danach gegen die erzeugte Tabelle.
    """
    von, bis = _range(from_year, to_year)
    kommentar = "--"
    kopf = [
        f"{kommentar} dim_date — die Zeitachse des Sternschemas. ERZEUGT, nicht aus SAP gezogen.",
        f"{kommentar} Bereich zur Laufzeit (D-819): 1. Januar des fruehesten Achsenwerts bis 31. Dezember des Jahres,",
        f"{kommentar} in dem der spaeteste Achsenwert plus {PROGNOSEHORIZONT_MONATE} Monate liegt. Ohne Werte "
        f"{von.isoformat()} bis {bis.isoformat()}.",
        f"{kommentar} Volle Jahre, eindeutig, leerwertfrei, luecken los (Microsofts Datumstabellen-Leitfaden).",
        f"{kommentar} Physisch materialisiert, weil Direct Lake berechnete Tabellen nicht traegt.",
        f"{kommentar} Laeuft nach allen anderen Gold-Schritten; coverage.sql misst danach gegen diese Tabelle.",
        "",
    ]
    cte = _bereich_cte(axes or [], stack, from_year, to_year, schemas)

    if stack == "snowflake":
        # GENERATOR nimmt keine Zeilenzahl zur Laufzeit: 100 Jahre ab Beginn, gefiltert auf das Ende.
        # ROW_NUMBER statt SEQ4 allein: SEQ4 garantiert keine lueckenlose Folge.
        rumpf = [
            f"CREATE OR REPLACE TABLE {gold_table} AS",
            *cte,
            "SELECT",
            f"    d AS \"Date\",",
            "    YEAR(d) AS \"Year\",",
            "    QUARTER(d) AS \"Quarter\",",
            "    YEAR(d) || '-Q' || QUARTER(d) AS \"QuarterName\",",
            "    MONTH(d) AS \"Month\",",
            f"    {_case('MONTH(d)', _MONTHS)} AS \"MonthName\",",
            "    TO_CHAR(d, 'YYYY-MM') AS \"YearMonth\",",
            "    DAY(d) AS \"Day\",",
            "    DAYOFWEEKISO(d) AS \"DayOfWeek\",",
            f"    {_case('DAYOFWEEKISO(d)', _DAYS)} AS \"DayName\",",
            "    WEEKISO(d) AS \"ISOWeek\",",
            "    DAYOFWEEKISO(d) >= 6 AS \"IsWeekend\"",
            "FROM (",
            "    SELECT DATEADD(day, ROW_NUMBER() OVER (ORDER BY SEQ4()) - 1, b.von) AS d, b.bis",
            "    FROM bereich b, TABLE(GENERATOR(ROWCOUNT => 36525))",
            ")",
            "WHERE d <= bis",
            ";",
        ]
    else:                                        # fabric + databricks: Spark SQL ueber Delta
        rumpf = [
            f"CREATE OR REPLACE TABLE {gold_table}",
            "USING DELTA AS",
            *cte,
            "SELECT",
            "    d AS Date,",
            "    YEAR(d) AS Year,",
            "    QUARTER(d) AS Quarter,",
            "    CONCAT(CAST(YEAR(d) AS STRING), '-Q', CAST(QUARTER(d) AS STRING)) AS QuarterName,",
            "    MONTH(d) AS Month,",
            f"    {_case('MONTH(d)', _MONTHS)} AS MonthName,",
            "    DATE_FORMAT(d, 'yyyy-MM') AS YearMonth,",
            "    DAY(d) AS Day,",
            # WEEKDAY liefert 0 = Montag; + 1 ergibt die ISO-Zaehlung. DAYOFWEEK waere 1 = Sonntag
            # und damit eine andere Woche — der Unterschied faellt erst im Bericht auf.
            "    WEEKDAY(d) + 1 AS DayOfWeek,",
            f"    {_case('WEEKDAY(d) + 1', _DAYS)} AS DayName,",
            "    WEEKOFYEAR(d) AS ISOWeek,",
            "    WEEKDAY(d) >= 5 AS IsWeekend",
            "FROM (",
            "    SELECT EXPLODE(SEQUENCE(von, bis, INTERVAL 1 DAY)) AS d FROM bereich",
            ")",
            ";",
        ]
    return "\n".join(kopf + rumpf) + "\n"


def coverage_sql(axes: list[dict[str, Any]], stack: str = "fabric",
                 from_year: int = DEFAULT_FROM_YEAR, to_year: int = DEFAULT_TO_YEAR,
                 schemas: bool = False) -> str:
    """Misst, ob der erzeugte Kalender die Fakten wirklich abdeckt — gegen die Tabelle, nicht gegen Literale.

    Der Bereich waechst seit D-819 zur Laufzeit mit. Abdecken muss er trotzdem nicht: ein Kalender, der vor den
    Fakten lief, oder eine Achse, die nach dem Kalender Daten bekam, faellt in Power BI nicht auf — die Beziehung
    greift ins Leere, die Zeile verschwindet aus jeder nach Zeit gefilterten Auswertung. Deshalb liefert die
    Messung Zeilen genau dann, wenn etwas fehlt. ``from_year``/``to_year`` bleiben fuer die Signatur stehen.
    """
    _range(from_year, to_year)
    kommentar = "--"
    zeilen = [
        f"{kommentar} Deckungspruefung dim_date — liefert Zeilen NUR bei Befund.",
        f"{kommentar} Erwartung: leer. Gemessen gegen MIN/MAX der erzeugten Tabelle (D-819). Jede Zeile nennt ein",
        f"{kommentar} Faktum, dessen Zeitachse aus dem Kalender faellt (befund ausserhalb), oder einen Kalender, der",
        f"{kommentar} keine {PROGNOSEHORIZONT_MONATE} Monate ueber den letzten Tag der Achse (Datenstand) "
        "hinausreicht (befund horizont,",
        f"{kommentar} D-802), oder einen leeren Kalender (befund kalender_leer).",
        "",
    ]
    if not axes:
        zeilen.append(f"{kommentar} Kein Faktum deklariert eine Zeitachse — nichts zu pruefen.")
        return "\n".join(zeilen) + "\n"

    datum = _zitiere_datum(stack)
    teile = [f"SELECT '{CALENDAR_TABLE}' AS fact, '{DATE_COLUMN}' AS axis, 'kalender_leer' AS befund,\n"
             f"       CAST(NULL AS DATE) AS min_date, CAST(NULL AS DATE) AS max_date,\n"
             f"       0 AS rows_outside\n"
             f"FROM kalender\n"
             f"WHERE von IS NULL"]
    for a in axes:
        # Derselbe Name wie im Transform-Emitter: `gold.<fakt>` im Schema-Lakehouse, sonst
        # `gold_<fakt>`. Gemessen 02.09.2026 (B-4): das feste `gold_` zeigte bei eingeschalteten
        # Schemas auf eine Tabelle, die kein anderer Teil der Lieferung anlegt.
        gold = layer_ref("gold", a["fact"], schemas)
        wert, belegt = _achsdatum(f"f.{a['field']}", stack), _achsfilter(f"f.{a['field']}", stack)
        teile.append(
            f"SELECT '{a['fact']}' AS fact, '{a['field']}' AS axis, 'ausserhalb' AS befund,\n"
            f"       MIN({wert}) AS min_date, MAX({wert}) AS max_date,\n"
            f"       COUNT(*) AS rows_outside\n"
            f"FROM {gold} AS f CROSS JOIN kalender AS k\n"
            f"WHERE {belegt}\n"
            # NOT BETWEEN statt zweier Vergleiche: `x < a OR x > b` in einer Zeile sieht fuer die
            # Platzhalter-Heuristik von `sql_validate` aus wie ein `<...>`-Platzhalter.
            f"  AND {wert} NOT BETWEEN k.von AND k.bis\n"
            f"HAVING COUNT(*) > 0")
        # Horizont (D-802): dieselbe Regel wie ``fristregel.kalender_reicht`` — Datenstand plus Horizont <= Ende.
        teile.append(
            f"SELECT '{a['fact']}' AS fact, '{a['field']}' AS axis, 'horizont' AS befund,\n"
            f"       MIN({wert}) AS min_date, MAX({wert}) AS max_date,\n"
            f"       0 AS rows_outside\n"
            f"FROM {gold} AS f CROSS JOIN kalender AS k\n"
            f"WHERE {belegt}\n"
            f"HAVING ADD_MONTHS(MAX({wert}), {PROGNOSEHORIZONT_MONATE}) > MAX(k.bis)")
    zeilen.append(f"WITH kalender AS (SELECT MIN({datum}) AS von, MAX({datum}) AS bis "
                  f"FROM {layer_ref('gold', CALENDAR_TABLE, schemas)})")
    zeilen.append("\nUNION ALL\n".join(teile))
    zeilen.append(";")
    return "\n".join(zeilen) + "\n"


# --------------------------------------------------------------------------- Leitdokument
def calendar_markdown(axes: list[dict[str, Any]], offen: list[dict[str, Any]],
                      from_year: int = DEFAULT_FROM_YEAR, to_year: int = DEFAULT_TO_YEAR,
                      verloren: list[dict[str, Any]] | None = None) -> str:
    von, bis = _range(from_year, to_year)
    z = [
        "# Zeitachse — dim_date (erzeugt)", "",
        "Der Bereich waechst zur Laufzeit mit den Daten (D-819): vom 1. Januar des fruehesten Werts der",
        "deklarierten Achsen bis zum 31. Dezember des Jahres, in dem der spaeteste Wert plus",
        f"{PROGNOSEHORIZONT_MONATE} Monate liegt — dieselbe Regel wie `fristregel.kalender_ende`. Ohne Achse oder",
        f"ohne Werte gilt {von.isoformat()} bis {bis.isoformat()}. Der Kalender laeuft in jeder Ladung als letzter",
        "Gold-Schritt (`transforms/_erzeugt/silver_to_gold__dim_date.sql`).", "",
        "Eindeutig, ohne Leerwerte und luecken los folgt aus der erzeugten Sequenz; volle Jahre folgt aus",
        "der Regel. Alle vier Bedingungen stehen so in Microsofts Leitfaden fuer Datumstabellen.", "",
        "Die Tabelle wird als Delta-Tabelle in Gold materialisiert, nicht als berechnete Tabelle im",
        "Modell: Direct Lake on SQL traegt keine berechneten Tabellen. Eine eigene, markierte",
        "Datumstabelle mit Beziehungen ueber Datumsspalten ist dagegen ausdruecklich unterstuetzt.", "",
        "## Deklarierte Zeitachsen", "",
        "Welches Datum ein Faktum fuehrt, ist eine fachliche Wahl und steht als `date_axis` im Paket.",
        "Ohne Deklaration entsteht keine Beziehung — ein Faktum ohne Achse ist sichtbar, ein geratenes",
        "Datum waere es nicht.", "",
        "| Faktum | Achse | Warum diese | Weitere Datumsfelder |", "|---|---|---|---|",
    ]
    for a in axes:
        alt = ", ".join(f"`{x}`" for x in a.get("alternatives") or []) or "—"
        z.append(f"| `{a['fact']}` | `{a['field']}` | {a.get('rationale') or '—'} | {alt} |")
    if not axes:
        z.append("| — | — | — | — |")

    if verloren:
        z += ["", "## Deklarierte Achsen ohne Kante (Befund)", "",
              "Diese Achsen stehen im Paket, aber ihre Spalte hat die Gold-Projektion nicht",
              "ueberlebt. Das Faktum laeuft dadurch ohne Zeitachse, und ohne diese Tabelle wuerde",
              "das nirgends stehen.", "",
              "| Faktum | Achse | Warum |", "|---|---|---|"]
        for d in verloren:
            z.append(f"| `{d['fact']}` | `{d['field']}` | {d.get('why', '')} |")

    z += ["", "## Fakten ohne Zeitachse", ""]
    if offen:
        z += ["| Faktum | Datumsspalten | Grund |", "|---|---|---|"]
        for o in offen:
            spalten = ", ".join(f"`{c}`" for c in o.get("date_columns") or []) or "keine"
            z.append(f"| `{o['fact']}` | {spalten} | {o.get('reason') or 'offen'} |")
        z += ["", "Ein Faktum ohne Datumsspalte ist nicht zwingend ein Defekt — ein Bestandsstand ist",
              "eine Momentaufnahme. Ein Faktum **mit** Datumsspalten und ohne Achse dagegen schon:",
              "dann liegt die Zeit vor und wird nicht genutzt."]
    else:
        z.append("Keine — jedes Faktum traegt eine deklarierte Achse.")

    z += ["", "## Was der Kalender nicht kann", "",
          "Geschaeftsjahr und Buchungsperiode fehlen. Sie haengen an der Geschaeftsjahresvariante",
          "(T009/T009B) je Buchungskreis und sind ohne Systemzugriff nicht ableitbar. Erst mit der",
          "Variante des Kunden kommen `FiscalYear` und `FiscalPeriod` dazu; bis dahin rechnet das",
          "Modell auf Kalenderjahren, und das steht hier, statt still zu passieren.", "",
          "Monats- und Wochentagsnamen sind englisch und im SQL fest verdrahtet statt ueber",
          "`date_format` erzeugt — sonst haengt der Inhalt an der Locale der ausfuehrenden Sitzung",
          "und aendert sich zwischen zwei Laeufen. Eine Uebersetzung ist eine Lieferentscheidung.", "",
          "## Deckung", "",
          "`coverage.sql` prueft nach dem Kalender, ob Faktenzeilen ausserhalb der erzeugten Tabelle liegen",
          "(gemessen an deren MIN/MAX, nicht an einer Annahme). Es liefert Zeilen nur im Befundfall; leer ist",
          f"gruen. Zweiter Befund (`horizont`, D-802): der Kalender endet weniger als {PROGNOSEHORIZONT_MONATE} Monate",
          "nach dem letzten Tag einer Achse — dann lief er vor den Fakten. Dritter (`kalender_leer`): die",
          "Tabelle ist leer.", ""]
    return "\n".join(z) + "\n"


def emit_calendar(packs: list[dict] | None, stack: str = "fabric",
                  from_year: int = DEFAULT_FROM_YEAR, to_year: int = DEFAULT_TO_YEAR,
                  prefix: str = "calendar",
                  tables: list[dict] | None = None, schemas: bool = False) -> dict[str, str]:
    """Der Kalenderteil der Lieferung als ``Pfad → Inhalt``: Deckung und Leitdokument.

    Den Kalender selbst schreibt seit D-821 nur noch ``erzeugte_transforms`` als Gold-Schritt der Ladung; die
    gleichlautende Uebergabedatei ``calendar/dim_date.sql`` war dasselbe SQL ein zweites Mal."""
    achsen = date_axes(packs)
    verloren = dropped_axes(achsen, tables) if tables is not None else []
    gebunden = [a for a in achsen
                if (a["fact"], a["field"]) not in {(d["fact"], d["field"]) for d in verloren}]
    return {
        f"{prefix}/coverage.sql": coverage_sql(gebunden, stack, from_year, to_year, schemas=schemas),
        f"{prefix}/_ZEITACHSE.md": calendar_markdown(achsen, facts_without_axis(packs),
                                                     from_year, to_year, verloren),
    }


def erzeugte_transforms(governed_catalog: dict | None, stack: str = "fabric",
                        schemas: bool = False) -> dict[str, str]:
    """Der Kalender als Gold-Schritt der Ladung (D-819): ``Pfad unter render/<stack>/ → SQL``.

    Nur wenn der Katalog den Kalender mit ``erzeugung.art = kalender`` fuehrt. Die einzige Ablage des
    Kalender-SQL (D-821); ``emit_calendar`` schreibt daneben nur Deckung und Leitdokument."""
    for t in (governed_catalog or {}).get("tables") or []:
        e = t.get("erzeugung") or {}
        if t.get("name") == CALENDAR_TABLE and e.get("art") == ERZEUGUNG_KALENDER:
            return {f"{ERZEUGT_ORDNER}/silver_to_gold__{CALENDAR_TABLE}.sql":
                    calendar_sql(stack, gold_table=layer_ref("gold", CALENDAR_TABLE, schemas),
                                 axes=list(e.get("achsen") or []), schemas=schemas)}
    return {}


def erzeugt_abschnitt(erzeugt: dict[str, str], schemas: bool = False) -> str:
    """Der Abschnitt fuer ``_MEDALLION_FLOW.md``: die Gold-Schritte aus ``erzeugte_transforms``.

    Ohne ihn zeigte der Flussplan der Lieferung jede Gold-Tabelle ausser dem Kalender, obwohl die Pipeline ihn
    seit D-819 in jeder Ladung als letzten Gold-Schritt faehrt."""
    if not erzeugt:
        return ""
    z = ["## Erzeugte Gold-Schritte (ohne Silber-Quelle, D-819)", "",
         "Laufen nach allen anderen Gold-Schritten; die Spanne rechnet das SQL zur Laufzeit aus den deklarierten "
         "Achsen.", ""]
    for rel in sorted(erzeugt):
        name = rel.rsplit("__", 1)[-1].removesuffix(".sql")
        z.append(f"- *(erzeugt)* → {layer_ref('gold', name, schemas)} (dimension)  ·  `{rel}`")
    return "\n".join(z) + "\n\n"

