# ADR-0028 — Forecast als Auslöser-Typ der Action Codes

| Feld | Wert |
|---|---|
| Status | **Accepted** (30.10.2026, Freigabe Florian Haferkorn: „Typ Forecast in ALUCA“); umgesetzt in Schema, Codegen-Schutz und Tests, noch kein Action Code mit dem Typ |
| Entscheider | Florian Haferkorn |
| Kontext | Meridian-Studio-Mock „Familie Minimal“ (Freelancing-Repo, PR #798, E9): der Feed zeigt je Auslöser die Kennziffer des Auslösers; für eine Prognose gab es in ALUCA keinen Auslöser, aus dem sie kommen könnte (BO-NEU-minimal-4 dort) |
| Betrifft | `tooling/generator/schemas/action_code.schema.json` (`trigger.type`, `trigger.forecast`) · `tooling/codegen/action_trigger_dax.py` · `tooling/tests/test_action_code_trigger_form.py` · `tooling/tests/test_action_trigger_dax.py` · `core/action_codes/Commercial/C-M2.3.yaml` (Schwellen, `value_status`) |
| Bezug | GOI §1 „Maschinenform vor Prosaform“; ADR-0027 (Ausnahme als Feld) |

## 1. Kontext

Gemessen am 30.10.2026 auf `origin/main` 0f4f893 (Zählung über `core/action_codes/*/*.yaml`):
`trigger.type` ist 56 × Deviation, 2 × Pattern, je 1 × CompositeDeviation, LifecycleDeviation,
Webhook. Das Schema führte den Typ als freien String; ein Tippfehler fiel keinem Test auf.
Alle Typen prüfen den Ist-Wert. Eine Regel „die Prognose zum Monatsende unterschreitet das
Ziel“ ist damit nicht ausdrückbar; sie stünde als Deviation auf dem Ist-Wert und prüfte
etwas anderes.

Zweites Freitextfeld: `threshold.value_status` stand in 9 Schwellen (C-E1.1, C-M2.3, E-S1.1),
immer `open`, ohne Prüfung gegen `value`.

## 2. Optionen

| Option | Form | Vorteil | Nachteil |
|---|---|---|---|
| (a) Status quo | Prognose als Deviation, Prosa in `gating_rules` | keine Änderung | prüft den Ist-Wert, Prosa nicht falsifizierbar |
| (b) Typ `Forecast` mit Block `trigger.forecast` | Enum für `trigger.type`; Horizont, Prognose-Measure, Vergleichswert (Punkt oder Bandrand) als Felder | Schema verlangt den Block genau beim Typ; Stufen bleiben L1–L3 wie bei Deviation | Codegen muss den Typ kennen; ein Feld mehr |
| (c) Prognose als eigene KPI im Katalog | `KPI-…-FC` je Ziel-KPI, Auslöser bleibt Deviation | kein neuer Typ | verdoppelt KPIs, Golden Thread trägt dieselbe Bedeutung zweimal |

## 3. Entscheidung: Option (b)

- `trigger.type` ist ein Enum: `Deviation`, `Pattern`, `CompositeDeviation`,
  `LifecycleDeviation`, `Webhook`, `Forecast`.
- `trigger.forecast` ist Pflicht bei `Forecast` und verboten sonst. Felder: `horizon`
  (`length` ≥ 1, `unit` periods/days/weeks/months), `forecast_measure` (Measure, das die
  Prognose zum Horizont liefert), `compare` (`point`, `band_lower`, `band_upper`) und `band`
  (`prediction_interval`, `level` in (0,1)), Pflicht bei einem Bandrand.
- Die Stufen L1–L3 bleiben unverändert und vergleichen den gewählten Prognosewert.
- `action_trigger_dax.py` erzeugt für `Forecast` keinen Ausdruck, sondern meldet einen Fehler:
  den Ist-Wert gegen die Schwelle zu stellen, sähe aus wie ein Ausdruck und prüfte etwas
  anderes. Die Ableitung aus `forecast_measure` folgt, wenn der erste Action Code den Typ führt.
- `threshold.value_status` hat drei Werte: `open` (Wert `null`), `assumed` (Wert gesetzt,
  Datei trägt `ANNAHME, ungeprueft`) und `set` (vom Owner bestätigt). Der Test prüft Status
  gegen Wert.

## 4. Folgen

- Alle 60 Action Codes (ohne Decision Spines, dieselbe Auswahl wie Stage 1) bestehen das
  verschärfte Schema; gemessen mit `test_every_action_code_passes_the_schema`.
- C-M2.3 trägt angenommene Schwellen −2 / −4 / −6 % gegen die Basis (`value_status: assumed`),
  vorher `null`. Der Code bleibt `draft`; KPI-COM-033 hat weiter kein Measure, kein Modell
  wertet die Schwellen aus.
- Offen: DAX-Ableitung für `Forecast`; ein erster Action Code mit dem Typ.

## 5. Nachtrag 30.10.2026: Bandränder als eigene Measures, Ableitung, C-M2.4 (Florian)

- **Entscheidung:** Die Ränder des Prognoseintervalls kommen aus eigenen Measures
  (`band.lower_measure`, `band.upper_measure`, beide Pflicht in `band`). Verworfen: nur
  Punktprognose (der Feed-Eintrag „Spanne berührt Schwelle“ hätte keine Quelle) und
  Aufschub bis zum ersten Kunden.
- **Ableitung:** `action_trigger_dax.py` vergleicht bei `Forecast` das Measure aus `compare`
  (`forecast_measure`, `lower_measure` oder `upper_measure`) mit den Stufen; die Basis bleibt
  der Ist-Verlauf der KPI. Fehlt das Measure im Modell, ist das ein Fehler. Persistenz wird
  bei `Forecast` nicht ausgewertet und gemeldet: frühere Prognosestände liegen nicht im Modell.
- **C-M2.4** Private Label Share Forecast Warning: KPI-COM-033, Horizont 1 Monat, unterer Rand
  des 80-%-Intervalls gegen −2 / −4 / −6 % zur Basis (wie C-M2.3, `assumed`), `draft`, solange
  die drei Prognose-Measures fehlen; verdrahtet in COM-IND-R002.
- **Schwellen als Annahme** auch für C-E1.1 (−3 / −6 / −10 % zur Basis) und E-S1.1 (+5 / +10 /
  +20 % über dem Ziel). Damit trägt keine Schwelle im Bestand mehr `value_status: open`.
- **Befund, nicht behoben:** E-S1.1 hat `basis: target` mit `unit: '%'` und meint eine Toleranz
  über dem Ziel. Die Ableitung liest `basis: target` ohne `reference` als Pegel der KPI
  (`[M] > 5`, tCO2e). Heute folgenlos (kein ESG-Modell); vor dem ersten ESG-Modell klären.

## 6. Nachtrag 30.10.2026: `reference: target` (Florian)

- **Entscheidung:** Der Befund aus §5 wird mit einem neuen `reference: target` gelöst, analog zu
  `reference: baseline`. Die Schwelle ist dann eine Abweichung vom Ziel. `basis: target` ohne
  `reference` bleibt ein Pegel. Verworfen wurden: `basis: target` immer als Abweichung lesen (das
  bricht die Pegel-Lesart vom 23.09.2026) und den Befund offen lassen.
- **Ziel-Measure:** Das Ziel ist die Plan-KPI des Katalogs, also das Feld `plan_kpi_ref` der
  Trigger-KPI, das schon `comparison_measures.py` nutzt. So entsteht kein zweiter Ort für Ziele.
  Fehlt die Plan-KPI oder hat sie im Modell kein Measure, ist das ein Fehler, keine Annahme.
- **Ableitung:** `unit: '%' | pct` wird relativ gerechnet (`[M] > Ziel * 1,05`, bei `lt` mit
  `Ziel * 0,95`), jede andere Einheit additiv (`[M] > Ziel + v`). Ohne Ziel-Daten feuert die
  Stufe nicht (`NOT ISBLANK`). Die Persistenz-Vormonate werten das Ziel im verschobenen Monat aus.
- **E-S1.1** trägt `reference: target` in L1–L3. Offen ist die Plan-KPI zu KPI-ESG-001: der
  Katalog führt keine, und `fact_emissions[Target Emissions tCO2e]` steht nur im Datenvertrag.
  Solange sie fehlt, bricht die Ableitung für E-S1.1 ab. Heute bleibt das folgenlos, weil es
  kein ESG-Modell gibt.

## 7. Nachtrag 30.10.2026: KPI-COM-033 rechenbar, Prognose offen

- `dim_product` trägt `Private Label Flag` (Vertrag `commercial_sales`), KPI-COM-033 hat das
  Measure „Private Label Penetration %“ im Commercial-Modell (Op `sum_filtered`). C-M2.3 bleibt
  `draft`, weil die Schwellen Annahmen sind (eigene Qualitätsregel des Codes).
- C-M2.4 bleibt `draft`: die drei Prognose-Measures fehlen weiter. Das Verfahren (Punkt und
  80-%-Intervall) ist eine fachliche Entscheidung und liegt Florian als Frage vor; das Repo hat
  kein Prognosemuster mit Intervall (`fact_forecast` in SupplyChain/Growth trägt nur
  Punktprognosen aus einem Planungssystem).

- KPI-ESG-001 ist mit derselben Operation rechenbar (Summe Scope 1 + Scope 2). Die Plan-KPI aus
  §6 fehlt weiter; die Ableitung für E-S1.1 bricht deshalb weiter ab, ohne ESG-Modell folgenlos.

### 7.1 Nachtrag 30.10.2026: Prognoseverfahren und Erzeugungsweg (Florian)

- **Verfahren (Entscheidung Florian):** Horizont ein Monat. Punkt = Mittel der Monatswerte der
  letzten drei Monate (alle drei mit Wert, sonst leer). 80-%-Band = Punkt + 10. bzw. 90.
  Perzentil (`PERCENTILEX.INC`) der historischen Ein-Monats-Fehler e(k) = Wert(k) − Mittel der
  drei Monate davor, über die letzten 24 Monate, mindestens 12 Fehler (sonst leer). Die Quantile
  folgen aus `band.level` ((1 ∓ level) / 2).
- **Erzeugungsweg:** `tooling/codegen/forecast_measures.py`, nach dem Muster von
  `comparison_measures.py` (Modell-Measures außerhalb des KPI-Katalogs, Annotation
  `ALUCA_Generated = "forecast_measures"`, Prüfmodus und `--write`, Stufe S1 der agentischen
  Schleife vor `action_trigger_dax`). Quelle sind die Forecast-Ausloeser der Action Codes, nicht
  der Katalog. Begründung: die KPI-DSL kennt weder Monatsverschiebung noch Perzentil, und eine
  Prognose ist keine eigene KPI (Option c aus §2 verworfen); ein Katalog-Eintrag hätte drei
  KPIs ohne eigene Bedeutung erzeugt.
- **Folge:** `action_trigger_dax` kann C-M2.4 erzeugen (Test `test_forecast_measures.py`).
  Persistenz eines Forecast-Ausloesers wertet es nicht aus (`nicht_ausgewertet: persistence`).
  C-M2.4 hat noch kein `Action_C-M2.4_Text`-Measure im Modell: das entsteht erst mit einem Bericht,
  der den Code zeigt. Beide Codes bleiben `draft`, die Schwellen `value_status: assumed`.
- **Nachgerechnet** (Showdaten nach dem Eigenmarken-Trend, Python gegen DuckDB, max. Abweichung
  1e-12 pp; DAX nicht gegen eine Engine gelaufen): CE, Auswahl Nov 2024: Unterrand 21,81 % gegen
  Basis 22,48 % (Quote 0,9705) → C-M2.4 L1, einen Monat vor C-M2.3 L1 (Dez 2024). CE Dez 2024:
  Quote 0,9541 → L2. Fashion, Home & Living, gesamt: keine Stufe.
- **Backtest** (dieselbe Python-Referenz, 45 Ein-Monats-Prognosen je Reihe, Ziele 2021-04 bis
  2024-12): Anteil der Istwerte im 80-%-Band CE 0,667, Fashion 0,800, Home & Living 0,800,
  gesamt 0,711. CE liegt unter 0,8, weil das Band aus Fehlern vor dem Trend kommt. Showdaten,
  keine Kundenkalibrierung.
