---
last-reviewed: 2026-07-08
shelf-life-days: 90
---
# R3.2 — Inspector V2 + BPA in CI

> Umsetzt `UMSETZUNGSPLAN_REPORT_EXZELLENZ.md` Cut C3 / Task R3.2. Baut direkt auf
> R3.1 (`r3-1-tooling-audit-and-theme-decision.md`) auf: R3.1 hat drei
> konkurrierende PBIR-Validatoren gefunden, davon einer (`pbir-cli`) proprietär,
> Windows-only und aus dieser Sandbox weder installier- noch einsehbar. R3.2
> sucht bewusst ein Tool, das die im Plan geforderten Eigenschaften erfüllt
> (PBIR-fähig, eigene JSON-Logic-Regeln, CI-Gate, JSON-Artifact) **und** real
> verifizierbar ist.

## 1. Tool-Wahl: fab-inspector (vormals „PBI-Inspector V2")

Der Plan nennt explizit „PBI-Inspector V2 (PBIR-fähig)" und JSON-Logic-Regeln
für Theme-Compliance/max-Visuals/kein-vertikales-Scrollen — das ist eine
präzise Beschreibung von **NatVanG/PBI-Inspector V2**, das seit Version 2.0
PBIR unterstützt und seither zu **NatVanG/fab-inspector** weiterentwickelt
wurde (aktuell v3.4.0, Stand dieser Session). Kernfakten (verifiziert per
GitHub-Recherche, Details siehe Referenzen):

- **Cross-platform**: .NET-8-CLI, offizielle Release-Assets für
  `win-x64`, `linux-x64`, `osx-x64`, `osx-arm64` — im Gegensatz zu `pbir-cli`
  (nur `win_amd64`-Wheel) hier real auf jedem CI-Runner-OS lauffähig.
  Verifiziert: `.NET 8.0` SDK ist in dieser Sandbox bereits vorhanden
  (`dotnet` binary gefunden).
- **Open Source, MIT-Lizenz** — Regelwerk und Engine sind einsehbar, anders
  als `pbir-cli`s Closed-Source-Binary.
- **JSON-Logic-Regel-Engine** (Greg Dennis' JsonLogic.NET) — exakt das vom
  Plan geforderte Format. Das mitgelieferte `Rules/Base-rules.json` enthält
  bereits produktionsreife Regeln mit genau den drei vom Plan genannten
  Themen: `REDUCE_VISUALS_ON_PAGE`, `ENSURE_PAGES_DO_NOT_SCROLL_VERTICALLY`,
  `ENSURE_THEME_COLOURS` — starker Hinweis, dass der Plan-Autor exakt dieses
  Tool im Kopf hatte, als „`pbir bpa --fail-on error`" geschrieben wurde
  (kein Tool mit einem Befehl namens `bpa` existiert; das war eine
  Annäherung vor Kenntnis der echten CLI-Syntax `fab-inspector -fabricitem
  ... -rules ... -formats ...`).
- **`logType: error|warning(default)`** pro Regel — das ist der reale
  Mechanismus hinter der Plan-Formulierung „`--fail-on error`": Regeln mit
  `logType: "error"` lassen den Prozess mit einem Fehler-Exitcode enden,
  `warning`-Regeln nicht (Dokumentation bestätigt das Feld, nicht explizit
  den Exitcode-Mechanismus selbst — siehe „Grenzen dieser Session" unten).

**Nicht gewählt:** die ursprüngliche `PBI-Inspector`-V1-Codebasis (nur
`.pbix`, kein PBIR) und `pbir-cli` (bereits in R3.1 als das tatsächliche,
aber unverifizierbare CI-Gate identifiziert — bleibt unangetastet, siehe
`r3-1-tooling-audit-and-theme-decision.md` Abschnitt 2).

## 2. Eigene Regeln — adaptiert, nicht übernommen

`products/fabric/powerbi/tooling/validation/fab-inspector-rules.json` enthält
drei Regeln, 1:1 aus `fab-inspector`s eigenem `Base-rules.json` übernommene
JsonLogic-Struktur, aber mit auf dieses Repo zugeschnittenen Parametern und
explizit `logType: "error"` (im Original nicht gesetzt, Default ist
`warning`):

| Regel-ID | Herkunft | Anpassung |
|---|---|---|
| `ALUCA_MAX_VISUALS_PER_PAGE` | `REDUCE_VISUALS_ON_PAGE` | Schwelle unverändert bei 20 (kein Hinweis auf abweichenden Bedarf gefunden). |
| `ALUCA_NO_VERTICAL_SCROLL` | `ENSURE_PAGES_DO_NOT_SCROLL_VERTICALLY` | Schwelle 720px → **1080px**, unsere feste 1920x1080-Canvas (`structural_validator.DEFAULT_PAGE_HEIGHT`). Bewusst redundant zu `PageSize`/`VisualWithinPage` (Tier 0, Python) — Verteidigung in der Tiefe über eine zweite, unabhängige Engine, kein neuer Constraint. |
| `ALUCA_THEME_VISUALS_NO_HARDCODED_HEX` | `ENSURE_THEME_COLOURS` | Unverändert übernommen (Textbox-Ausnahme war bereits im Original enthalten). Ergänzt `check_report_theme_compliance.py`s eigenen (aktuell nicht-blockierenden) Hex-Scan um ein zweites, unabhängig implementiertes Signal. |

**Vorab-Verifikation gegen den echten `dist/`-Baum (2026-07-08, Python-Skript,
da das Binary in dieser Sandbox nicht ausführbar ist — s. u.):**

- Maximal 4 sichtbare, nicht-dekorative Visuals auf einer Seite (weit unter
  der Schwelle 20) — `COM-001_Sales_Performance.Report/.../Page_COM001_Overview`.
- 0 Seiten mit `height != 1080`.
- 0 Visuals (Textbox ausgenommen) mit Hex-Farbliteral —
  `check_report_theme_compliance.py` bestätigt unabhängig `0 error(s), 0
  warning(s)` repo-weit.

Alle drei Regeln sind also **heute bereits grün** und können gefahrlos als
`logType: "error"` (blockierend) scharf geschaltet werden — anders als beim
Theme-Namens-Vorfall in R3.1 wurde hier **vor** dem Schärfen gegen die
echten Daten verifiziert, nicht nur gegen die Doku eines Drittanbieters.

## 3. CI-Wiring

- `.tools/fab-inspector.lock` — Versions-Pin `v3.4.0`, `win-x64`, SHA-256
  zunächst `placeholder_update_after_download` (identisches Bootstrap-Muster
  wie `pbi-tools.lock`; nach dem ersten echten CI-Download den echten Hash
  eintragen).
- `.github/workflows/stage1.yml`, Job `stage1` (windows-latest): neuer Schritt
  **„Install fab-inspector CLI"** lädt das gepinnte Release, prüft den Hash
  (warnt statt hart zu blocken, solange der Platzhalter drinsteht), entpackt
  nach `.tools/fab-inspector/`, findet die `.exe` dynamisch (Name aus dem
  Build-Workflow des Tools nicht mit Sicherheit bekannt) und setzt
  `$env:FAB_INSPECTOR_EXE` für den nachfolgenden `run_fabric_checks.ps1`-Lauf.
- `run_fabric_checks.ps1` ruft `check_fab_inspector.ps1` auf (gleiches Muster
  wie die bestehenden `check_*.ps1`-Aufrufe); das Skript bricht den Gate bei
  `logType:error`-Verstößen ab (`$failed++`), skipt aber graceful, wenn das
  Binary fehlt (lokale Entwicklung ohne Internetzugriff).
- Neuer Artifact-Upload-Schritt **„Upload fab-inspector BPA report"** lädt
  `internal/metrics/runs/fab_inspector/` hoch (ein JSON pro Report-Ordner) —
  erfüllt „Report-Artifact als Artifact abrufbar" aus der Plan-Zeile.

## 4. Grenzen dieser Session — was NICHT lokal verifiziert werden konnte

Diese Sandbox hat **keinen Internetzugriff auf beliebige GitHub-Release-Assets**
(nur auf das gescopte Repo via GitHub-MCP; direkte `curl`/`Invoke-WebRequest`
gegen `github.com/.../releases/download/...` liefert HTTP 403 vom
Umgebungs-Proxy). Das bedeutet konkret:

- Das `fab-inspector`-Binary konnte **nicht heruntergeladen oder ausgeführt**
  werden — CLI-Flags, Regel-Engine-Verhalten und insbesondere der
  **Exitcode-Mechanismus für `logType:error`** stammen aus der Tool-eigenen
  Dokumentation (`docs/cli-reference.md`, `docs/rules-guide.md`,
  `Rules/Base-rules.json`), nicht aus einem eigenen Testlauf.
- Der exakte Name der `.exe` innerhalb von `win-x64-FabInspCLI.zip` ist aus
  dem Build-Workflow nicht mit Sicherheit ableitbar — `check_fab_inspector.ps1`
  und der CI-Installationsschritt suchen deshalb **dynamisch** per
  `Get-ChildItem -Filter *.exe` statt einen Namen hart zu kodieren.
- **Konsequenz, aus der R3.1-Lehre gezogen:** dieser Schritt wird nach dem
  Merge über einen echten CI-Lauf verifiziert (PR-Watch aktiv), nicht als
  „fertig getestet" behauptet. Schlägt die Installation oder ein Rule-Lauf in
  CI unerwartet fehl, ist das der erwartete nächste Diagnose-Schritt, kein
  Rückfall in den Theme-Namens-Fehler (dort wurde eine unverifizierte Annahme
  committed *und* als erledigt dokumentiert, ohne auf den echten CI-Lauf zu
  warten).

## 5. Offen für R3.3/R3.4

- SHA-256 in `fab-inspector.lock` nach erstem echten CI-Download eintragen.
- Sobald `pbir-cli`s echte Theme-Namens-Regel auf einem Windows-Rechner
  verifiziert ist (R3.1, Abschnitt 2), erneut prüfen, ob `fab-inspector`
  dieselbe Konvention akzeptiert oder eine vierte Meinung beisteuert.
- R3.3 (Scorecard-Gate) kann die drei `ALUCA_*`-Regeln als weitere
  Knock-out-Kriterien referenzieren.
- Der Tier-1-Oracle (`MicrosoftReportAuthorBackend`, R3.1) bleibt bewusst
  advisory/non-blocking (700+ Alt-Funde noch nicht trianiert) — unabhängig
  von `fab-inspector`, das als drittes, jetzt blockierendes Signal
  hinzukommt.

## Referenzen

| Quelle | Bezug |
|---|---|
| [NatVanG/fab-inspector](https://github.com/NatVanG/fab-inspector) | Tool-Repo, MIT, aktuell v3.4.0 |
| [NatVanG/PBI-Inspector](https://github.com/NatVanG/PBI-Inspector) | Vorgänger (nur `.pbix`, kein PBIR) |
| `products/fabric/powerbi/tooling/validation/fab-inspector-rules.json` | Eigene Regeln (Abschnitt 2) |
| `products/fabric/powerbi/tooling/validation/check_fab_inspector.ps1` | Runner-Skript |
| `.tools/fab-inspector.lock`, `.tools/README.md` | Versions-Pin, Installationsanleitung |
| `docs/architecture/r3-1-tooling-audit-and-theme-decision.md` | Vorarbeit: 3-Tool-Konflikt, warum `pbir-cli` nicht erneut angefasst wurde |
| `UMSETZUNGSPLAN_REPORT_EXZELLENZ.md` §6 Ledger | R3.2-Zeile |
