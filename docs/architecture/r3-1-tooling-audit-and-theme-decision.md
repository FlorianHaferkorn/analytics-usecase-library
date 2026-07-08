---
last-reviewed: 2026-07-08
shelf-life-days: 90
---
# R3.1 — Tooling-Audit + Rückbau-Entscheidung

> Umsetzt `UMSETZUNGSPLAN_REPORT_EXZELLENZ.md` Cut C3 / Task R3.1. Entstanden aus
> Funden während R1.6-Vorbereitung (2026-07-08): der offizielle Tier-1-Oracle
> (`powerbi-report-author`) wurde zum ersten Mal in dieser Session tatsächlich
> ausgeführt statt nur referenziert — mit erheblichen, teils überraschenden
> Ergebnissen. **Nachtrag noch am selben Tag:** der in Abschnitt 2 zunächst als
> „entschieden" markierte Theme-Namens-Konflikt stellte sich als Drei-Wege-
> Konflikt heraus (ein drittes, bislang unentdecktes CI-gate-relevantes Tool,
> `pbir-cli`, widerspricht dem npm-Oracle) und wurde zurückgerollt — siehe
> Abschnitt 2 für den vollen Verlauf statt eine geschönte Zusammenfassung.

---

## 1. ADR-0001-Status korrigiert

ADR-0001s eigener Status-Header sagte „deferred — framework not adopted for
the current direction" (Stand 2026-06-15). Das ist **nicht mehr aktuell**:
PR #321 (`feat(pbi-quality): pluggable validation backends + capability tiers
(ADR-0001 impl, salvaged)`, gemerged 2026-06-16, einen Tag nach dem
„deferred"-Update) hat die Backend-/Tier-Architektur tatsächlich in `main`
zurückgeholt — `tooling/report_quality/backends.py` mit `NativeBackend` (Tier 0)
und `MicrosoftReportAuthorBackend` (Tier 1) existiert real im Baum, korrekt
hinter `PBI_QUALITY_ALLOW_EXTERNAL` gated, exakt wie in ADR-0001 entworfen.

**Was fehlte:** `tooling/report_quality/cli.py` (der Einstiegspunkt, den
`report_quality.cli --summary` und `pbi-quality validate` tatsächlich aufrufen)
importierte `backends.py` nie. `pbi-quality doctor` zeigte den aktiven Tier
korrekt an, aber die Tier-1-Funde flossen nie in die zurückgegebene
Violations-Liste ein — die Salvage-PR hat die Scaffolding gemerged, aber die
Verdrahtung in Schritt 2 von ADR-0001s „Implementation notes" nie
abgeschlossen. **Folge:** jede „0 critical/warning/info"-Aussage von
`report_quality.cli --summary` in dieser gesamten Session (R1.1–R1.6-Vorarbeit)
galt korrekt für die Tier-0-Prüfung, aber niemand hatte den Tier-1-Pfad je
tatsächlich mit `PBI_QUALITY_ALLOW_EXTERNAL=1` angestoßen, um das zu bemerken.

**Entscheidung:** Verdrahtung nachgezogen (`tooling/report_quality/cli.py`,
diese Session) — `MicrosoftReportAuthorBackend().validate(dist_root)` wird nun
in `validate()` aufgerufen. Die Klasse übernimmt Gating/Graceful-Skip
vollständig selbst, daher ist das Default-Verhalten (Flag nicht gesetzt)
unverändert (verifiziert: weiterhin 0/0/0 ohne Flag). ADR-0001s Status-Header
sollte bei nächster Gelegenheit auf „Accepted (salvaged via #321, CLI-Pfad
verdrahtet #373)" aktualisiert werden — hier dokumentiert statt separat
editiert, um den ADR-Verlauf nicht nachträglich umzuschreiben.

## 2. Theme-Namens-Konflikt (#7) — NICHT entschieden: drei Tools, drei Meinungen

**Korrektur (2026-07-08, nach Push):** dieser Abschnitt behauptete ursprünglich,
der Konflikt sei zugunsten des offiziellen npm-Oracle entschieden — das war
voreilig und wurde durch einen roten CI-Lauf sofort widerlegt. Der tatsächliche
Befund ist ein **Drei-Wege-Konflikt**, nicht zwei:

| Quelle | Forderung |
|---|---|
| `check_report_theme_compliance.py` (eigen) | `customTheme.name` **ohne** `.json` |
| `@microsoft/powerbi-report-authoring-cli` (npm, lokal installiert & getestet) | `customTheme.name` **mit** `.json`, muss exakt dem `resourcePackages`-Item entsprechen |
| **`pbir-cli`** (PyPI, proprietäres Windows-Binary — **das tatsächliche CI-Gate dieses Repos**, `run_fabric_checks.ps1` → `pbir-cli validate --qa`) | `customTheme.name` **ohne** `.json` — widerspricht dem npm-Tool direkt |

`pbir-cli` wurde in dieser Session zunächst übersehen, weil die npm-CLI-Recherche
den Fokus auf die R1.6-Vorbereitung dominierte. Der Fix wurde ausschließlich auf
Basis der npm-CLI vorgenommen (`de31a75`, `02d5407`) und dabei **das eigentliche
CI-Gate ignoriert** — Ergebnis: „Stage 1 checks" fiel auf jedem Push seit
`de31a75` rot (verifiziert per CI-Historie: `a677da2` grün, jeder Commit danach
rot), weil `pbir-cli --qa` exakt die durch den Fix hergestellte Konvention
ablehnt.

**Korrekturmaßnahme (`8f2dbfa`):** `git revert --no-commit de31a75 02d5407`,
danach die davon unabhängige Tier-1-Verdrahtung in `cli.py` erneut angewendet.
Alle 59 theme-bezogenen Dateien sind wieder exakt auf dem `a677da2`-Stand
(bare-stem-Konvention, bekannt CI-grün).

**Warum nicht einfach die `pbir-cli`-Konvention übernehmen und fertig?**
`pbir-cli` ist ein **proprietäres, Windows-only Binary** (PyPI-Wheel
`pbir_cli-*-win_amd64`) — aus dieser Linux-Sandbox weder installierbar noch
im Quelltext einsehbar. Die genaue Regel („warum genau lehnt es `.json` ab,
und unter welchen Bedingungen wäre `.json` doch akzeptabel") lässt sich von
hier aus nicht verifizieren, nur die Tatsache, dass die bare-stem-Konvention
funktioniert. Eine erneute Änderung ohne echten Windows-Testlauf würde exakt
denselben Fehler wiederholen.

**Status: bewusst unentschieden, nicht „gefixt".** Empfehlung: R3.2 (Inspector
V2 + BPA in CI) ist der richtige Ort, um `pbir-cli`s tatsächliches Verhalten
mit einem echten Windows-Runner/-Rechner zu verifizieren, bevor die
`.json`-Frage erneut angefasst wird. Bis dahin gilt: bare-stem-Konvention ist
die einzige verifiziert-grüne, nicht anfassen.

## 3. Überlappungs-Audit — eigene Checks vs. offizieller Oracle

Direkter Lauf von `powerbi-report-author validate --no-schema` gegen den
gesamten `dist/`-Baum (`PBI_QUALITY_ALLOW_EXTERNAL=1 python3 -m
tooling.report_quality.cli --json`, 2026-07-08):

| Befund-Code | Anzahl | Deckungsgleich mit eigener Prüfung? |
|---|---|---|
| `PBIR_THEME_VISUAL_PROP_UNKNOWN` | 527 | **Nein — blinder Fleck.** Eigene Prüfung kennt keine Theme-`visualStyles`-Property-Validierung. |
| `PBIR_FORMATTING_OBJECT_UNKNOWN` | 103 | Nein — blinder Fleck (Formatierungsobjekt-Namen pro Visual-Typ). |
| `PBIR_THEME_VISUAL_PROP_ENUM_INVALID` | 34 | Nein — blinder Fleck. |
| `PBIR_SLICER_HEIGHT_BELOW_FLOOR` | 19 | Teilweise — eigene Prüfung kennt Mindesthöhen nicht. |
| `PBIR_VISUAL_TYPE_UNKNOWN` | 16 | **Falsch-positiv** (s. u.) — kein blinder Fleck, sondern eine Lücke im Oracle. |
| `PBIR_ROLE_MAX_EXCEEDED` | 13 | Nein — blinder Fleck (Rollen-Obergrenzen pro Visual-Typ). |
| `PBIR_FORMATTING_PROP_UNKNOWN` | 1 | Nein — blinder Fleck. |

**Umgekehrt:** die eigene Prüfung deckt Golden-Thread-Bindung (Measure↔KPI),
Bracket↔PBIR-Konsistenz und generierte-Inhalt-Validierung ab — Dinge, die der
Oracle strukturell nicht sehen kann (er kennt kein TMDL, keine Brackets).

**Schlussfolgerung, wie in ADR-0001 selbst schon vorgesehen: die beiden
Prüfungen sind komplementär, nicht redundant.** Kein Rückbau angezeigt — im
Gegenteil, der Oracle deckt eine ganze Klasse von Fehlern auf, die die eigene
Prüfung strukturell nie finden konnte (s. Abschnitt 4).

**`PBIR_VISUAL_TYPE_UNKNOWN` — Fehlalarm, dokumentiert statt „gefixt":**
einziger Treffer ist `smartNarrativeVisual` — ein echter, offiziell
unterstützter Power-BI-Visual-Typ, der schlicht in der Metadaten-Version
dieses CLI-Releases (57 Visual-Typen laut `doctor`) fehlt. Genau der von
ADR-0001 selbst benannte Kostenpunkt: „the metadata snapshot can lag the
latest CLI." Kein Handlungsbedarf, nur zur Kenntnis für R3.2 (Inspector V2
könnte hier vollständiger sein).

**PBI-Inspector V2** (im Plan als weitere Vergleichsgröße genannt): in dieser
Session nicht evaluiert — Zeit ging vollständig in den bereits vorhandenen,
lokal installierten Oracle. Für R3.2 offen.

## 4. Neue reale Funde — Triage (was jetzt gefixt ist, was bewusst offen bleibt)

| Befund | Umfang | Status |
|---|---|---|
| `dataLabels` statt `labels` (clusteredBarChart/-ColumnChart) | repo-weit (COM-001-Alt-Baseline + alle Main_3-Slots) | **Teilweise gefixt:** COM-002 in R1.4 dieser Session korrigiert. Restliche Reports offen — Kandidat für R2.4-Rollout (Generator-Fix + Batch-Anwendung, nicht Einzeldatei-Patches). |
| `calloutValue` statt `value` (cardVisual) | repo-weit (jede KPI-Card) | **Offen, bewusst nicht gefixt.** Betrifft jede Card in jedem Report — Generator-Fix + Re-Regenerierung nötig, kein Hotfix. An R2.4/R3.4 übergeben. |
| `text.text`-Property (textbox) | repo-weit (jede Textbox: Header, ActionPanel, alte Smart_Narrative) | **Offen, bewusst nicht gefixt.** Widerspricht dem Oracle, ist aber der einzige real beobachtete, produktiv genutzte Generator-Pattern (`page_builder.py`) — keine funktionierende Alternative gefunden oder verifiziert. Vor jeder Änderung: echte Desktop-Bestätigung nötig (R1.6/R4.1), da eine falsche „Korrektur" hier das R1.1-Schema-Problem wiederholen würde. |
| Waterfall-Chart: mehrere Measures in `Y`-Rolle (max 1) | **repo-weit, alle 13 Reports mit PVM-Bridge** (nicht nur COM-002/Main_2, das in R1.6 bereits als Einzelfall vermerkt wurde) | **Offen, priorisierter Fund.** Ein echter Waterfall braucht 1 Measure + eine Category-Achse für die Bridge-Stufen; die aktuelle Konstruktion (N Measures, keine Category) ist strukturell ungültig laut offiziellem Rollen-Modell. Verdient einen eigenen Task (Main_2-Neubau über alle Reports), keinen Einzel-Patch. |
| Theme-JSON-Properties (`visualStyles.*`) — 527+34 Funde | 2 Theme-Dateien (Aurora Group, Brand Rose), repo-weit dupliziert über alle 17 Reports | **Offen, groß, priorisierter Fund.** Deutet auf ein grundlegend veraltetes/nicht-schema-konformes Theme-JSON hin (viele `visualStyles`-Properties wie `dropShadow.Options`, `title.fontFace` unbekannt). Verdient einen eigenen Theme-Audit-Task, nicht Teil von R3.1. |
| Dropdown-Slicer < 76px Mindesthöhe | repo-weit (jeder Overview-Slicer) | **Offen.** Bereits in R1.6-Ledger vermerkt. Layout-Grid-System-Fix, Kandidat für R2.4. |

**Prinzip für alle „Offen"-Zeilen:** keine unilaterale Einzeldatei-Reparatur
für repo-weite Muster — das würde Inkonsistenz zwischen frisch gefixten und
noch nicht regenerierten Reports erzeugen. Diese Funde gehören in den
Generator (R2.3/R2.4-Rollout) oder einen eigenen Task, nicht in Ad-hoc-Patches.

## 5. Empfehlung für R3.2/R3.3

- **R3.2 (Inspector V2 + BPA in CI):** Tier-1-Oracle als **advisory** (nicht
  blockierend) CI-Artefakt einbinden — `PBI_QUALITY_ALLOW_EXTERNAL=1` im
  CI-Workflow setzen, Ergebnis als JSON-Artifact hochladen, aber `exit 0`
  erzwingen bis die 700+ Alt-Funde triagiert sind. Erst nach Abschluss der
  Theme- und Waterfall-Aufräumarbeiten (s. o.) auf „blockierend" umstellen.
  **Zusätzlich, mit Priorität vor der `.json`-Frage:** `pbir-cli`s exakte
  Theme-Namens-Regel auf einem echten Windows-Rechner/-Runner verifizieren
  (Quelltext nicht einsehbar, Sandbox kann das Binary nicht installieren) —
  erst danach Konflikt #7 erneut angehen.
- **R3.3 (Scorecard-Gate):** die vier priorisierten Funde aus Abschnitt 4
  eignen sich als konkrete Knock-out-Kandidaten, sobald behoben.

## Referenzen

| Dokument | Bezug |
|---|---|
| `adr/0001-pluggable-validation-backends-and-capability-tiers.md` | Ursprungs-ADR, Status-Korrektur in Abschnitt 1 |
| `docs/references/powerbi-report-author-cli.md` | Spike-Notizen zur Oracle-CLI (vor dieser Session) |
| `products/fabric/powerbi/tooling/run_fabric_checks.ps1` | Ruft `pbir-cli validate --qa` auf — das tatsächliche CI-Gate, s. Abschnitt 2 |
| `docs/architecture/quality-tooling-map.md:26` | Bestehender Verweis auf `pbir-cli --qa` im `fabric_gate` |
| `UMSETZUNGSPLAN_REPORT_EXZELLENZ.md` §6 Ledger | R1.6-Vorbefund, R3.1-Zeile |
| `quality-tooling-map.md` | Sollte nach diesem Dokument aktualisiert werden (Tier-1 jetzt verdrahtet) |
