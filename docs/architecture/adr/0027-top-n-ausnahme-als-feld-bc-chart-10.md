# ADR-0027 — Top-N-Ausnahme als Feld (BC-CHART-10)

| Feld | Wert |
|---|---|
| Status | **Accepted** (24.10.2026, Freigabe Florian Haferkorn); umgesetzt in Schema, Checker, Tests und XD-002 |
| Entscheider | Florian Haferkorn |
| Kontext | `internal/evidence_grain_audit_results.md` (Urteile je Use Case, 24.10.2026); Kommentar in `core/usecases/core/XD-001_Service_Level_Performance/UseCase_Bracket.yaml` („eine Ausnahme braucht ein Feld“) |
| Betrifft | `tooling/generator/schemas/usecase_bracket.schema.json` (`component_300s`) · `tooling/validation/check_evidence_sort.py` · `tooling/tests/test_evidence_sort.py` · `products/fabric/powerbi/tooling/page_scaffold_generator/config_loader.py` (`detail_matrix_top_n`) |
| Bezug | Boutique-Rubrik BC-CHART-10 (Knock-out, `tooling/report_quality/boutique_scorecard.py`), GOI §1 „Maschinenform vor Prosaform“ |

## 1. Kontext

BC-CHART-10 verlangt für jede Evidenztabelle `sort_by` und `top_n` als positive ganze Zahl. Das
Schema verlangt `top_n` bei `intent_rules_version: 2`. Der Checker steht heute bei 24/24.

Die Körnungsprüfung vom 24.10.2026 hat zwei Fälle gemessen, in denen das Top-N nichts leistet
oder schadet:

| Fall | Use Cases | Messung (Quelle) | Wirkung des Top-20 |
|---|---|---|---|
| kleine Körnung | XD-001, XD-002 | XD-001: keine Spalte über 10 Werte (fact_support_cases); XD-002: 4 Queues, 32 Zeilen | filtert nichts |
| Zwischensummen | SCM-003 (Urteil `matrix`) | ABC/XYZ > ProductCode 7/5000/0, 40 SKUs in 5 Zellen (fact_forecast) | verfälscht die Clustersummen |

COM-001, COM-006 und SCM-002 liegen ebenfalls bei 15 Zeilen (gemessen, Audit-Tabelle). Am
24.10.2026 hatte b66d70bf `top_n` für XD-001/002 gestrichen; der Knock-out fiel auf 96,8 %, der
Commit wurde in ddb6b6eb zurückgenommen. Heute steht deshalb in zwei Brackets ein `top_n: 20`,
das laut eigenem Kommentar wirkungslos ist. Die Begründung steht nur in Prosa und kann veralten,
ohne dass ein Test es merkt.

## 2. Optionen

| Option | Form | Vorteil | Nachteil |
|---|---|---|---|
| (a) Status quo | `top_n: 20` plus Kommentar | keine Änderung | wirkungsloses Feld, Begründung nicht prüfbar, bei Matrix falsche Summen |
| (b) `top_n_ausnahme` mit Klasse und Zähler | Feld statt `top_n`, Klasse aus Enum, gemessene Zeilenzahl, Datum | Test prüft die Klasse gegen die Messung; Knock-out bleibt hart | ein Feld mehr im Schema; Messung muss nachgezogen werden |
| (c) `top_n: null` plus Freitextgrund | null erlaubt, `top_n_grund: str` | klein | Grund wieder Prosa, nicht falsifizierbar |

## 3. Entscheidung: Option (b)

`component_300s` trägt **entweder** `top_n` **oder** `top_n_ausnahme`, nie beides:

```yaml
component_300s:
  sort_by: {measure: KPI-SVC-003, direction: ascending}
  top_n_ausnahme:
    klasse: kleine_koernung        # Enum: kleine_koernung | matrix_zwischensummen
    gemessene_zeilen: 32           # Zeilen der Evidenztabelle im ungefilterten Kontext
    gemessen_am: '2026-10-24'
    quelle: fact_support_cases (Gold, pandas)
```

Regeln, die der Checker auswertet (keine davon liest Prosa):

1. `klasse: kleine_koernung` gilt nur bei `gemessene_zeilen <= 50` (Obergrenze aus
   `Design_Spec_3_30_300.md`, Detail-Matrix 50–100; die untere Kante, damit die Ausnahme nicht
   für große Tabellen greift).
2. `klasse: matrix_zwischensummen` gilt nur bei `visual_type: matrix`.
3. `gemessen_am` ist ein ISO-Datum; älter als 180 Tage = Warnung (nicht rot), damit die Messung
   nachgezogen wird.
4. `sort_by` bleibt Pflicht. Die Ausnahme betrifft nur die Zeilengrenze, nicht die Reihenfolge.

Der Knock-out zählt eine gültige Ausnahme als erfüllt; eine ungültige ist rot wie ein fehlendes
`top_n`. Damit bleibt der Scorecard-Wert bei 100 %, ohne dass ein Feld etwas vorgibt, was es nicht tut.

## 4. Umsetzung (24.10.2026)

**Schema** (`usecase_bracket.schema.json`, `component_300s.properties`):

```json
"top_n_ausnahme": {
  "type": "object",
  "additionalProperties": false,
  "required": ["klasse", "gemessene_zeilen", "gemessen_am", "quelle"],
  "properties": {
    "klasse": {"enum": ["kleine_koernung", "matrix_zwischensummen"]},
    "gemessene_zeilen": {"type": "integer", "minimum": 0},
    "gemessen_am": {"type": "string", "format": "date"},
    "quelle": {"type": "string", "minLength": 1}
  }
}
```

Im `intent_rules_version: 2`-Zweig wird `"required": ["sort_by", "top_n", "highlight_rule"]` zu
`["sort_by", "highlight_rule"]` plus `"oneOf": [{"required": ["top_n"]}, {"required": ["top_n_ausnahme"]}]`.

**Checker** (`check_evidence_sort.classify_evidence`), nach der `direction`-Prüfung:

```python
ausnahme = c300.get("top_n_ausnahme")
if ausnahme is not None:
    if top_n is not None:
        return False, "top_n and top_n_ausnahme both set"
    return _pruefe_ausnahme(ausnahme, c300.get("visual_type", "table"))
```

`_pruefe_ausnahme` setzt die Regeln 1–3 aus §3 um und gibt `(True, "")` oder `(False, grund)` zurück.

**Tests** (`tooling/tests/test_evidence_sort.py`):

- gültige `kleine_koernung` mit 32 Zeilen → True
- `kleine_koernung` mit 51 Zeilen → False, Grund nennt die Grenze
- `matrix_zwischensummen` bei `visual_type: table` → False
- `top_n` und `top_n_ausnahme` zugleich → False
- `_BASELINE_COVERED` bleibt unverändert (Ausnahme zählt als abgedeckt)

**Generator** (`config_loader.py`, Zeile ~1374): bei `top_n_ausnahme` bleibt
`detail_matrix_top_n = None`; das ist heute schon der Pfad ohne Top-N-Filter, es braucht keinen
neuen Zweig.

## 5. Betroffene Brackets (Stand nach Umsetzung)

| Use Case | heute | danach |
|---|---|---|
| XD-001 | `top_n: 20` (wirkungslos) | `kleine_koernung`, 20: Körnung auf die Entscheidungsfrage geschnitten (Channel x Queue x IssueType; Org gestrichen, Severity hängt 1:1 an IssueType, dim_issue_type 5 Zeilen). Vorher 200 Zeilen; ein Top-N-Feld hätte die Kreuzklassifikation nicht begrenzt (je Spalte höchstens 10 Werte) |
| XD-002 | `top_n: 20` (wirkungslos, 32 Zeilen) | `kleine_koernung`, 32 (8 Orgs x 4 Queues, fact_workforce_management, Gold, pandas); Top-N-Filter aus der Detail_Matrix entfernt |
| SCM-003 | `top_n: 20`, Urteil `matrix` noch nicht umgesetzt | Kreuztabelle, `matrix_zwischensummen` |
| COM-001 | `top_n: 20` bei 15 Zeilen | zuerst `kleine_koernung` 15 (Region x Category); seit 24.10.2026 Kreuztabelle Region > Country > Store, `matrix_zwischensummen`, 99 Store-Zeilen (5 Regionen, 15 Länder, fact_sales, Gold, pandas) |
| COM-006, SCM-002 | `top_n: 20` bei 15 Zeilen | `kleine_koernung`, je 15 (Customer x Mode); Top-N-Filter aus den erzeugten Detail_Matrix entfernt (COM-006 hat keinen Report) |

## 6. Was diese Entscheidung bewusst nicht tut

- Keine Ausnahme für große Tabellen: wer mehr als 50 Zeilen hat, braucht ein Top-N.
- Der Strukturcheck greift nicht auf Gold zu; die Messung ist ein Feld mit Datum. **Nachgezogen
  24.10.2026:** `python tooling/validation/check_evidence_sort.py --gold` zählt `gemessene_zeilen`
  nach. Pflichtfeld `fakt` nennt die Faktentabelle; die Spalten kommen aus der Auflösung des
  Generators (dieselben wie in der erzeugten Detail_Matrix), die Schlüssel aus `core/data_contracts`,
  die Dateien laut `_delta_log`. Exit 0 alle gleich, 1 Abweichung, 2 nicht geprüft (Gold fehlt,
  Schlüssel unklar). Gemessen 24.10.2026: 6/6 gleich (COM-001 15, seit der Kreuztabelle 99, COM-006 15, SCM-002 15,
  SCM-003 40, XD-001 20, XD-002 32). Test `test_every_top_n_ausnahme_matches_gold`, ohne Gold
  übersprungen mit Grund, nie grün.
