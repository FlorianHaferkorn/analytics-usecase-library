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
