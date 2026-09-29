# PBIR-CLI 0.4.0 — Re-Validierung und Pin-Entscheid

**Stand:** 29.09.2026 · **Anlass:** Pin-Drift-Sensor (Meridian `scripts/check_upstream_freshness.py`)
meldet `@microsoft/powerbi-report-authoring-cli` Pin 0.1.1 → latest 0.4.0 (HIGH) · Initiative
I-21 W0.4 · Entscheidung Meridian D-580 · **Ergebnis: bestanden, Pin 0.4.0 in beiden Repos.**
Vorgänger: [`pbir_cli_014_triage.md`](pbir_cli_014_triage.md) (0.1.4, 694 Befunde, nicht bestanden).

## Methode

Beide Fassungen lokal nebeneinander installiert (`npm install @microsoft/powerbi-report-authoring-cli@<v>`
in getrennte Verzeichnisse), dann `powerbi-report-author validate <Report>` über jeden Report.
Errors wurden mit derselben Platzhalter-Unterdrückung gezählt, die Meridians
`scripts/check_pbir.py` anwendet (Gruppe C der 0.1.4-Triage, `visualStyles.*.*`). Verglichen wurde
nicht nur die Zahl, sondern die **Menge** der Befunde als Tupel (Report, Regel, Pfad, Meldung).
Zusätzlich ohne Schema-Abruf (`--no-schema`, neu in 0.4.0) gegengemessen.

## Ergebnis je Korpus

| Korpus | Fassung | Error-Befunde | davon unterdrückt (Platzhalter) | Warnings |
|---|---|---:|---:|---:|
| ALUCA `products/fabric/powerbi/dist/*.Report` (17) | 0.1.1 | 236 | 187 | 87 |
| dto. | 0.4.0 | **236** | 187 | 203 (67 mit `--no-schema`) |
| Meridian Aurora `dist/*.Report` (10) | 0.1.1 | 0 | 0 | 50 |
| dto. | 0.4.0, vor Fix | 10 | 0 | 80 |
| dto. | 0.4.0, nach Fix | **0** | 0 | 90 |

**ALUCA:** Die 236 Error-Befunde sind unter beiden Fassungen **dieselbe Menge** (Mengendifferenz
0 in beide Richtungen). Roh (ohne Unterdrückung) meldet jeder Report 23 oder 25 Errors — die
Ratsche `BASELINE_ERRORS = 25` in `tooling/tests/test_dist_validator_ratchet.py` hält, der Test
lief mit 0.4.0 und ist grün. Die Regeln bleiben `PBIR_THEME_VISUAL_PROP_UNKNOWN` (136),
`PBIR_FORMATTING_OBJECT_UNKNOWN` (85), `PBIR_FORMATTING_PROP_UNKNOWN` (15) — der Theme-Bestand aus
der 0.1.4-Triage, keine neue Klasse.

**Meridian:** 0.4.0 meldet je Report einen neuen Error `PBIR_JSON_FILE_NO_SCHEMA` — die `.pbip`
trug kein `$schema`. Ursache war der Erzeuger (`meridian/tool-layers/fabric/generators/report_pages.py::_write_pbip`),
nicht das Artefakt; die beiden anderen PBIP-Erzeuger schrieben `$schema` bereits. Erzeuger
korrigiert, dist neu erzeugt, 10 → 0.

## Neue Warnings (blockieren nicht)

| Regel | Vorkommen ALUCA | Sachlage |
|---|---:|---|
| `PBIR_PBIP_REPORT_PATH_MISMATCH` | 17 | Die ALUCA-`.pbip` liegen im `.Report`-Ordner und zeigen mit `"path": "."` auf sich selbst. Offen: Layout prüfen, ob Desktop das so öffnet (L10, Desktop-gated). |
| `PBIR_DRILLTHROUGH_FILTER_MISSING` | 16 | Drillthrough-Seite ohne Drillthrough-Filter. Einzeln zu prüfen. |
| `PBIR_DRILLTHROUGH_PARAMETER_MISSING` | 16 | dto. |
| `PBIR_DRILLTHROUGH_BACK_BUTTON_MISSING` | 16 | Rück-Schaltfläche fehlt. Kandidat für den Seiten-Generator. |
| `PBIR_FILTER_SOURCE_UNKNOWN` | 2 | schon unter 0.1.1 |

## Weitere Unterschiede 0.1.1 → 0.4.0

- Unterbefehl `doctor` entfallen; neu `text`, `preview`, `scaffold`, `pack`, `unpack`. Kein Aufrufer
  in beiden Repos nutzt `doctor` (grep).
- Die Item-Hülle wird geprüft: fehlendes `.platform` (`PBIR_PLATFORM_MISSING`) und fehlendes
  `definition.pbir` (`PBIR_DEFINITION_PBIR_MISSING`) sind Errors. Meridian-Fixture `BrownfieldMini`
  bekam ein `.platform`; der Test des reinen Report-Emitters zieht genau diese Hülle ab.
- Rollen-Metadaten (`refresh_authoring_metadata.py`, Snapshot neu erzeugt): einzige Änderung
  `hundredPercentStackedBarChart` — Pflichtrollen `{Category, Y}` → `{Y}`. Der Generator behält
  Category als Pflicht (lokale Politik in `visual_validator._LOCAL_ROLE_POLICY`), damit sich seine
  Ausgabe nicht ändert; der Drift-Test prüft beides.

## Pin-Entscheid

Pin **0.4.0** in beiden Repos (Meridian `scripts/check_pbir.py`, Session-Start, `smoke.yml`,
`pbip-validate.yml`, `bootstrap_env.ps1`; ALUCA `.github/workflows/superversion.yml`). Kriterium
aus dem Plan („zu viele Befunde → Pin bleibt") greift nicht: kein neuer Error-Befund in ALUCA,
in Meridian eine Klasse mit einem Erzeuger-Fix.

Nicht gemessen: ein CI-Lauf auf einem echten Runner — **ANNAHME, ungeprueft**, bis zum ersten
Lauf nach `gh pr ready`.
