# Umsetzungsplan — Agentische Report-Entwicklung als deterministische Schleife

**Stand 29.09.2026 · Status: in Arbeit (AP-2, AP-3, AP-4, AP-11 ohne Tenant umgesetzt, AP-8 gesichtet, AP-1 ALUCA-Konfiguration gemessen) · Übergabe an Cowork (Flos Rechner)**

Anlass: Flo hat am 24.09.2026 eine Zusammenfassung des Videos „Agentic development of Power BI
reports and semantic models" (https://youtu.be/zalHX6SLp6w) eingebracht. Das Video selbst wurde
hier **nicht** angesehen; Grundlage sind Flos Zusammenfassung, der Bestand beider Repos und
Microsoft Learn (abgefragt 24.09.2026, Quellen unten).

## 1 · Leitsatz

Das Video beschreibt eine **Dialogschleife**: der Agent ändert einen Bericht, man schaut ihn im
Service an, der Agent bessert nach. Wir übernehmen die Schleife, aber nicht den Dialog als
Arbeitsweise:

1. **Der Agent entscheidet nur, wo Urteil gebraucht wird**: Anforderungen in ein Bracket
   übersetzen, ein gerendertes Bild kritisieren, eine Korrektur vorschlagen.
2. **Alles andere ist ein Kommando mit Exit-Code**: erzeugen, prüfen, veröffentlichen, rendern,
   vergleichen, abräumen. Vokabular wie in den Spiegel-Sensoren: `0` ok, `1` Befund,
   `2` nicht prüfbar.
3. **Eine Korrektur landet nie in `dist/`**, sondern im Bracket, im Generator oder als Regel
   (Rückflusspflicht). Die `--check`-Modi der Generatoren erzwingen das schon heute.
4. **Wiederkehrende Befunde werden Regeln.** Was ein Agent zweimal falsch macht, prüft danach
   ein Test und nicht mehr der Agent.

Der eigentliche Gewinn für uns: **Rendern im Power BI Service statt in Desktop.** Das löst die
Desktop-Blocker der offenen Punkte R6.1, R6.2, R6.3, R4.1/R4.2 und R1.6
(`UMSETZUNGSPLAN_REPORT_EXZELLENZ.md`) und läuft auf Linux und in CI.

## 2 · Bestand (gemessen 24.09.2026; drei Zeilen nachgemessen 29.09.2026)

| Baustein | Wo | Stand |
|---|---|---|
| Deterministische Spezifikation (Bracket, KPI-Katalog, Action-Codes, Ziele) | ALUCA `core/`, `tooling/codegen/` | fertig, mit `--check` |
| PBIR-/TMDL-Generator | ALUCA `products/fabric/powerbi/tooling/page_scaffold_generator/`, `tooling/codegen/` | fertig, 15 von 17 Reports. **Nachtrag 29.09.2026:** das ist der deprecated Prototyp-Renderer (`generate_full_report.py` nur mit `--allow-deprecated-prototype`, aufgerufen aus `generate_phase5_reports.ps1`); der offizielle Superversion-Emit `tooling/superversion/targets/pbir.py` schreibt nicht nach `dist/`. Zwei Pfade, Ledger A-18 in `../architecture/_INDEX.md` |
| Strukturprüfungen | ALUCA `tooling/quality/run_quality_gate.ps1`, `tooling/report_quality/report_scorecard.py`; Meridian `make check-pbir` (`powerbi-report-author` 0.1.1) | fertig. **Nachtrag 29.09.2026:** auch ALUCA `superversion.yml` installiert die CLI gepinnt 0.1.1 und prüft den Emit blockierend (`e2e_smoke --require-cli`); lokal gemessen 0 Errors für COM-001, die 17 `dist/`-Reports 23 bis 25 Errors je Report (Ratsche, `premium-acceptance-F0-F6.md` F1). npm führt inzwischen 0.4.0 (`npm view`, 29.09.2026); der Pin ist bewusst |
| Manueller Render-Ablauf | ALUCA `RENDER_GATED_RUNBOOK.md` (Windows-Laptop-Sitzung, 7 Schritte) | Checkliste, keine Pipeline |
| Desktop-Screenshots | ALUCA `products/fabric/powerbi/tooling/desktop_bridge_screenshot.ps1` (R4.1) | gebaut, vom Maintainer nie erfolgreich ausgeführt |
| Export über die echte Power-BI-Engine | Meridian `products/pbi_visual_regression/fabric_export.py`, `bootstrap_fabric.py`, CLI `fabric-render`, `bootstrap-fabric`; Workflow `visual-fabric.yml` | gebaut; **30 von 30 Läufen rot**, die letzten nach ~4 s im Limit-Fenster, ob die Secrets gesetzt sind, ist offen |
| Headless-Renderer + Pixelvergleich | Meridian `products/pbi_visual_regression/` (`capture`, `verify`) | fertig, Baselines je Plattform |
| LLM-Judge | ALUCA `products/fabric/powerbi/tooling/judge/llm_judge_prompt_v1.md`, `tooling/report_quality/boutique_scorecard` | Prompt versioniert, nie über echte Bilder gelaufen |
| Modeling-MCP | ALUCA `.mcp.json` (seit 29.09.2026; `.cursor/` ist abgeschafft) | npm `@microsoft/powerbi-modeling-mcp@1.0.0` gepinnt; startet unter Linux, lädt 3 von 5 dist-Modellen (AP-1). Vorher: Windows-Exe 0.1.9 von Hand entpackt |

## 3 · Was Microsoft dazu offiziell anbietet (Learn, 24.09.2026)

- **Power BI Agentic**, Plugin `powerbi-authoring` im Marktplatz „Skills for Fabric"
  (https://github.com/microsoft/skills-for-fabric): Skills für Modell-Authoring, Report-Authoring,
  Report-Design, Report-Planner und Report-Management. Claude Code ist ausdrücklich unterstützt.
  https://learn.microsoft.com/power-bi/developer/agentic/power-bi-agentic-overview
- **Power BI Authoring MCP server**: gehosteter Endpunkt
  `https://api.fabric.microsoft.com/v1/mcp/powerbi/authoring` (keine Installation, kein Windows
  nötig) oder lokal `npx @microsoft/powerbi-modeling-mcp` (zusätzlich Desktop, PBIP-Ordner,
  Service Principal). https://learn.microsoft.com/power-bi/developer/mcp/power-bi-authoring-mcp
- **Report-Management-Skill**: Berichte aus PBIR über die Fabric-REST-API anlegen und
  aktualisieren (`/v1/workspaces/{id}/reports`, `updateDefinition`).
- **Desktop Bridge CLI** (`@microsoft/powerbi-desktop-bridge-cli`, bei uns D-237): Windows,
  `screenshot-all` je Seite.

Official-First (Freelancing `CLAUDE.md`) heißt: Tabular Editor 3 plus Windows-VM-Tunnel aus dem
Video übernehmen wir **nicht**; Microsoft deckt dasselbe offiziell ab. Nicht gemessen ist bisher,
ob der gehostete MCP mit unserem Tenant und aus einer Cloud-Sitzung funktioniert.

## 4 · Zielbild: acht Stufen

| Stufe | Eingabe → Ausgabe | Deterministisch | Agent | Tor |
|---|---|---|---|---|
| S0 Spezifikation | Anforderung → Bracket | Schema, Golden Thread, Katalogbezug | Bracket-Entwurf aus Gespräch/Notiz | Schema + `check_index --strict` |
| S1 Modell | Katalog → TMDL | Codegen, TMDL-Hooks, BPA, Offline-TOM | — | bestehende Gates |
| S2 Bericht | Bracket → PBIR | Generator, Scorecard, Design-Regeln, `powerbi-report-author validate` | — | bestehende Gates |
| S3 Veröffentlichen | PBIP → Sandbox-Workspace | Anlegen, Deploy, Datenscheibe laden | — | Exit 2, wenn eine Leitplanke fehlt |
| S4 Laufzeit | Modell im Service → DAX-Ergebnis | generierte DAX-Abfragen je Measure | — | kein Fehler, erwartete Leerstellen benannt |
| S5 Rendern | Bericht → PNG je Seite | Export über die Service-Engine; optional Desktop Bridge | — | jede Seite hat ein Bild |
| S6 Prüfen | PNG → Befunde | Pixelvergleich, Leer-/Fehler-Erkennung | Judge (Prompt v1), nur beratend | Befunde als JSON |
| S7 Abräumen | Workspace → gelöscht | Löschen, Nachweis | — | Workspace-ID aus dem Manifest weg |

Rückfluss: Befunde aus S4 bis S6 werden triagiert. Behoben wird in S0 bis S2 oder durch eine neue
Regel, nie im gerenderten Artefakt.

## 5 · Leitplanken für jeden Tenant-Lauf

- **Eigener Workspace je Lauf.** Fester Präfix (`zz-aluca-sandbox-`) plus Lauf-ID, keine
  Kundennamen. Die ID steht im Lauf-Manifest. Jede schreibende Operation prüft, dass sie genau
  diese ID trifft, und bricht sonst ab. Andere Workspaces werden weder gelesen noch geändert.
- **Nur synthetische Aurora-Daten, gedeckelt.** Die Gold-Schicht hat 1,7 GB. Sie wird nie
  vollständig geladen; S3 lädt eine deterministische Scheibe (siehe AP-3) mit hartem Deckel, der
  vor dem Upload gemessen wird.
- **Budget je Lauf.** Höchstzahl an Exporten und Abfragen, Gesamt-Timeout, kein geplanter Refresh.
- **Trockenlauf ist Standard.** Schreibende Stufen brauchen `--apply`.
- **Zugangsdaten nur als Umgebungsvariable** (`FABRIC_TENANT_ID`, `FABRIC_CLIENT_ID`,
  `FABRIC_CLIENT_SECRET`), nie in Dateien, Manifesten oder Logs.
- **Aus dem Tenant kommt nichts ins Repo** außer den PNGs der synthetischen Berichte und den
  Befund-JSONs. Kundenmaterial ist ohnehin ausgeschlossen (Kundendaten-Regel im Freelancing-Repo).

## 6 · Arbeitspakete für Cowork

Reihenfolge nach Abhängigkeit. Jedes Paket nennt, wo gebaut wird (Tool-Reuse-Pflicht: erweitern
statt neu), was „fertig" heißt, und wie es geprüft wird. Pakete mit ⊞ brauchen Windows oder
Desktop, Pakete mit ☁ einen Tenant.

### AP-0 · Vorbedingungen (Flo)
- Tenant festlegen (E1) und die Erlaubnis klären.
- Service Principal mit Recht zum Anlegen von Workspaces (Tenant-Einstellung „Service principals
  can create workspaces"), Zuweisung zu einer Kapazität (Export-To-File braucht Kapazität).
- Netzfreigaben für Cloud-Sitzungen: `api.fabric.microsoft.com`, `api.powerbi.com`
  (`login.microsoftonline.com` ist bereits erreichbar, gemessen 24.09.2026).
- **Fertig, wenn** `python -m products.pbi_visual_regression.cli bootstrap-fabric` im
  Freelancing-Repo alle Schritte bis „Workspace erreichbar" mit PASS meldet.

### AP-1 · Offizielle Werkzeuge einbinden und pinnen
- `powerbi-authoring`-Plugin für Claude Code/Cowork installieren.
- ALUCA `.cursor/mcp.json` auf `npx @microsoft/powerbi-modeling-mcp@<Version>` umstellen und
  `.cursor/MCP_SETUP.md` nachziehen; dieselbe Konfiguration als `.mcp.json` für Claude Code.
  **Nachtrag 29.09.2026:** `.cursor/` gibt es nicht mehr (25.09.2026); Ziel ist damit nur noch
  `.mcp.json` plus die Setup-Doku unter `products/fabric/powerbi/docs/references/`.
- Pins in Freelancing `research/upstream_pins.yaml` aufnehmen (MCP-Paket, Skills-Commit), damit
  `make check-upstream` (D-238) Drift meldet.
- Entscheidung als D-Nummer (Meridian) und ADR-Zeile (ALUCA) festhalten (E6).
- **Fertig, wenn** der MCP lokal einen PBIP-Ordner aus `products/fabric/powerbi/dist/` öffnet und
  Tabellen und Measures auflistet, und `make check-upstream` die neuen Pins kennt.
- **Stand 29.09.2026 (ALUCA-Teil, gemessen unter Linux):** `.cursor/` gibt es nicht mehr
  (Commit `8abea425`), die Konfiguration steht nur noch in `.mcp.json` (Claude-Code-Projektformat,
  `npx -y @microsoft/powerbi-modeling-mcp@1.0.0 --start`). Version gemessen mit
  `npm view @microsoft/powerbi-modeling-mcp version` → `1.0.0`. Gemessen mit einem stdio-JSON-RPC-
  Client (Linux x86_64, Node 22.22.2): `initialize` antwortet nach 2,3 s, `tools/list` liefert
  21 Werkzeuge; `ConnectFolder` + `table_operations List` + `measure_operations List` laden
  **3 von 5** dist-Modellen — Commercial 19 Tabellen/54 Measures/22 Beziehungen, Finance
  23/69/30, Operations 16/53/15; Gegenprobe über die TMDL-Dateien (Tabellendateien,
  `measure`- und `relationship`-Zeilen gezählt) ergibt dieselben Zahlen. **Experience und
  SupplyChain scheitern** mit `'database.tmdl' not found`: beiden `definition/`-Ordnern fehlt die
  Datei, die die drei anderen tragen — offen, gehört in den Generator, nicht von Hand nach `dist/`.
  Ohne angenommene EULA antwortet jedes Werkzeug mit einem Fehler; `.mcp.json` nimmt sie bewusst
  **nicht** an (Entscheidung des Nutzers: `accept_eula`-Werkzeug oder
  `PBI_MODELING_MCP_ACCEPT_EULA=true` lokal). Nicht gemessen: Desktop-Verbindung (Windows),
  DAX-Abfragen (brauchen eine laufende Engine), `ConnectFabric` (Tenant). Details:
  `products/fabric/powerbi/docs/references/powerbi-modeling-mcp-setup.md`. **Offen:** Plugin
  `powerbi-authoring`, Pin im Freelancing-`research/upstream_pins.yaml` (dort steht das Paket mit
  `track: true`, aber ohne Version und mit der Notiz „nur Desktop, Windows“ — nachziehen),
  D-Nummer/ADR-Zeile (E6), `database.tmdl` für Experience und SupplyChain.

### AP-2 · Sandbox-Lebenszyklus als Kommando ☁
- Heimat: ALUCA `products/fabric/orchestrator/` (E4, 24.09.2026), Spiegel nach Meridian.
- Befehle `up`, `deploy`, `down` in `sandbox.py`. Deploy über `fabric_release.py` (E3).
- Lauf-Manifest (JSON): Lauf-ID, Workspace-ID, Eingabe-Hashes, Werkzeug-Pins, Zeiten.
- `sandbox-down` löscht nur die Workspace-ID aus dem Manifest und belegt die Löschung durch
  einen anschließenden Lesefehler (404).
- **Fertig, wenn** Unit-Tests mit gemocktem HTTP alle drei Befehle und die Leitplanken aus §5
  abdecken (falsche ID → Abbruch, fehlendes `--apply` → keine Schreibung) und ein echter Lauf
  up → deploy → down ohne Rest endet.

- **Stand 24.09.2026, ohne Tenant umgesetzt:** `products/fabric/orchestrator/sandbox.py` trägt
  nur die Leitplanken (Manifest, Präfix, Rücklese-Guard, 404-Nachweis, Budget). Token,
  REST-Aufrufe mit Retry und Workspace-Anlage und -Löschung kommen aus `orchestrator.py`, der
  Deploy aus `fabric_release.py`. Vor jeder Schreibung wird der Workspace zurückgelesen; weichen
  ID oder Name vom Manifest ab, bricht der Befehl ab, bevor etwas gesendet wird.
  - Tests: 14 gegen gefälschte Orchestrator-Bausteine, laufen ohne `msal` auch in der CI. Ein
    AST-Test hält fest, dass `orchestrator.py` und `fabric_release.py` die genutzten Methoden
    weiter anbieten. Ein fünfzehnter fährt den echten `FabricApiClient` mit ersetztem
    `requests.request` (Kette POST, GET, DELETE, GET mit echtem 404); er braucht `msal` und
    wird in der CI sichtbar übersprungen. Gegenprobe: Rücklese-Guard, 404-Prüfung oder
    „jeder Fehler gilt als weg“ mutiert → je der zuständige Test rot.
  - **Korrektur zum ersten Stand:** die erste Fassung lag in Meridian und baute Token,
    REST-Client, Workspace-Anlage und `fabric-cicd`-Deploy ein zweites Mal. Gefunden über die
    Klasse-A-Tabelle in `SHARED_SUBSTANCE.md`, die `orchestrator.py` und `fabric_release.py`
    als ALUCA-Bestand führt. Tool-Reuse-Befund, vor dem Bau übersehen; daraus E4 neu.
  - Spiegel nach Meridian (`core/dataarch_engine/vendor/aluca`) folgt, sobald die Datei auf
    `main` liegt. Dort liegt `orchestrator.py` im selben Ordner, `fabric_release.py` nicht:
    der gespiegelte Deploy-Schritt ist in Meridian bis dahin nicht lauffähig.
  - **Befund für E3 (Microsoft Learn, gelesen 24.09.2026):** ein Bericht über die rohe
    Items-API braucht eine `byConnection`-Referenz, unsere PBIPs tragen `byPath`.
    `fabric-cicd` deployt PBIP (Modell vor Bericht) ohne diese Umschreibung. Entschieden in E3.
  - **Befund zu „ohne Rest“:** ein gelöschter Workspace bleibt für die Aufbewahrungsfrist
    (Vorgabe 7 Tage) durch Admins wiederherstellbar. `sandbox-down` belegt per 404 „weg aus der
    API“, nicht „endgültig gelöscht“. Dass die API 404 liefert, ist **ANNAHME, ungeprüft** bis
    zum ersten Lauf.
  - Offen: echter Lauf up → deploy → down.

### AP-3 · Datenanbindung für den Service ☁
- Befund: die Modelle lesen über `fn_DeltaCurrentFiles` mit `Folder.Files` einen lokalen Pfad.
  Im Service geht das nur mit Gateway.
- Anpassung im Codegen: Quelle als Parameter (lokaler Ordner oder OneLake-Pfad). Beide Varianten
  kommen aus demselben Generator, `--check` bleibt idempotent.
- Deterministische Datenscheibe: ein Skript neben `showcases/aurora_group/data/gold/`, das mit
  festem Seed einen Zeitraum und eine Auswahl an Organisationen schneidet, mit Größendeckel
  (Vorschlag 50 MB, E2). Zieltabelle leer lassen wie im Demo (`fact_target`, begründete Ausnahme).
- **Fertig, wenn** dieselbe PBIP-Quelle lokal und im Sandbox-Workspace lädt und die Scheibe zweimal
  hintereinander byte-gleich entsteht.

- **Stand 24.09.2026, ohne Tenant umgesetzt:**
  - Quelle als Parameter: `tooling/codegen/gold_source.py` (`--check`/`--write`, idempotent)
    schreibt in alle fünf Modelle `GoldSourceKind` (Vorgabe `folder`, lokal unverändert) und
    `GoldContainerUrl`. Bei `onelake` listet `AzureStorage.DataLake` den Workspace-Container
    und filtert auf den Tabellenordner, weil Microsoft Learn Unterordner-URLs für den
    ADLS-Konnektor in Desktop und Power Query Online als nicht unterstützt nennt. **ANNAHME,
    ungeprüft:** gleiche Spalten wie `Folder.Files`; belegt erst im ersten Sandbox-Lauf.
  - Datenscheibe: `showcases/aurora_group/data/scripts/slice_gold.py`. Gemessen 24.09.2026
    gegen die echte Gold-Schicht: 65 Tabellen, 26,3 MB (Deckel 50 MB), 13 s, sieben Fakten
    ausgedünnt (`fact_sales` 9,35 Mio. aktive Zeilen → 142.000, jede 17.), zwei Läufe in
    getrennten Prozessen byte-gleich. Fenster je Tabelle, weil ein globales Fenster
    `fact_customer_value` leer ließ (endet 11/2020, COM-003). Alle 43 Tabellen, die die Modelle
    lesen, sind enthalten.
  - Offen für den Tenant: Scheibe in ein Lakehouse laden, Parameter setzen, einmal laden.

### AP-4 · DAX-Laufzeitprüfung (S4) ☁
- Deterministisch aus den Generatoren ableiten: je erzeugter Measure (`action_trigger_dax`,
  `comparison_measures`, Katalog-Measures) eine `EVALUATE`-Abfrage je Monat.
- Ausführen über die Execute-Queries-REST-API oder den Authoring-MCP (E6).
- Erwartungen: kein Fehler; leer nur dort, wo die Leere begründet ist (etwa `fact_target`);
  Datentyp passend zum `formatString`.
- **Belegpflicht:** für drei KPIs dieselbe Zahl unabhängig aus den Parquet-Dateien nachrechnen
  (pandas) und die Abweichung ausweisen. Achtung vor den bekannten stillen Fehlern (mehrere
  Measures in einer `SUMMARIZECOLUMNS`, `FILTER(<ganze Tabelle>)` in `CALCULATE`).
- **Fertig, wenn** der offene Punkt „DAX-Laufzeit der neuen Measures" in R6.1 mit Zahl und
  Methode abgehakt werden kann.

- **Stand 24.09.2026, ohne Tenant umgesetzt:** `tooling/codegen/dax_smoke.py`. `plan` schreibt
  für alle 278 Measures je zwei Abfragen und eine Erwartungsklasse nach
  `products/fabric/powerbi/dax_smoke/` (`--check` idempotent): 180 `zahl`, 70 `text`,
  28 `leer_begruendet` (alle an `fact_target`, auch über andere Measures). `gegenprobe` rechnet 23
  Summen aus der Datenscheibe mit pandas, `run` fragt über die Execute-Queries-REST-API ab
  (Token nur aus `POWERBI_ACCESS_TOKEN`, Budget), `bewerten` stellt beides nebeneinander.
  **Erster Befund schon ohne Tenant:** die Gegenprobe fand `fact_sales[Sales Units]` im
  SupplyChain-Modell ohne Quellspalte; die Prüfung aller 486 Quellspalten ergab 20 solche Lücken
  in vier Modellen (`KNOWN_ERRORS_AND_FIXES.md`). Sie sind als Sperrklinke festgehalten; die
  Zuordnung (umbenennen oder im Gold ergänzen) ist eine Entscheidung (E8).

### AP-5 · Rendern über die Service-Engine (S5) ☁ (⊞ optional)
- `fabric_export.py` für die in AP-2 veröffentlichten Berichte nutzen; Seitenliste aus `pages.json`.
- Dateinamen deterministisch: `<use_case>/<page_name>.png`.
- Optional als zweite Engine: Desktop Bridge `screenshot-all` (⊞). Weichen beide Bilder
  voneinander ab, ist das ein Befund über eine der beiden Engines, kein Bildfehler.
- Erster Umfang: drei Berichte, die die offenen Punkte tragen (OPS-001, COM-003, SCM-001).
- **Fertig, wenn** jede Seite der drei Berichte ein Bild hat und ein zweiter Lauf dieselben
  Seiten liefert.

### AP-6 · Deterministische Bildprüfungen (S6, erster Teil)
- Heimat: Meridian `products/pbi_visual_regression/` (`verify`, Pixelvergleich).
- Baseline-Plattform „Fabric-Service" neben `Windows-AMD64/` und `Darwin-arm64/`.
- Neue Prüfungen: leere Visual-Fläche, Fehlersymbol eines Visuals, abgeschnittene Kopfzeile
  (Band der oberen 56 px, R6.2).
- **Fertig, wenn** jede neue Prüfung einen Gegenfall hat, der sie rot macht (erst den Fehler
  nachweisen, dann das Urteil).

- **Stand 24.09.2026, ohne Tenant umgesetzt** (Meridian, `products/pbi_visual_regression/image_checks.py`,
  CLI `check-image`): leere Datenvisuals, Kopfzeilentext am Rand (unten oder rechts), Fehlerzustand
  per Referenzausschnitt; ohne Ausschnitt „nicht prüfbar“. 7 Tests, je Prüfung Fall und Gegenfall;
  Gegenprobe über entschärfte Schwellen je rot. Die Fehlalarm-Rate an echten Seiten ist **ANNAHME,
  ungeprüft**: im Bestand liegt kein Service-Export, und die Baselines des hauseigenen Renderers
  sind scrollende HTML-Layouts (1920×2064), keine 1:1-Seiten. Messung und Referenzausschnitt in AP-5.

### AP-7 · LLM-Judge über echte Bilder (S6, zweiter Teil)
- Prompt `llm_judge_prompt_v1.md` unverändert, Modell per Umgebungsvariable.
- Ausgabe strukturiert (JSON je Seite: Regel, Befund, Sicherheit).
- Beratend, nicht blockierend (E5). Der Judge ändert keine Datei.
- **Belegpflicht:** zweimal dieselben Bilder bewerten lassen und die Übereinstimmung ausweisen,
  bevor ein Judge-Befund als Befund zählt.
- **Fertig, wenn** R4.2 mit echten Bildern gelaufen ist und die Übereinstimmung gemessen ist.

### AP-8 · Rückfluss in Regeln
- Erste Kandidaten aus dem Video, jeweils gegen unseren Bestand prüfen, bevor etwas gebaut wird:
  - drei Formatierungsebenen (Theme-Wildcard, Visual-Default, Visual-Formatierung) mit fester
    Vorrangregel,
  - Tabelle Alltagssprache → Eigenschaftsname (etwa Balkenfarbe → `dataPoint.fill`) in der
    Visual Library, belegt gegen den offiziellen Visual-Katalog,
  - bedingte Formatierung auf Kategorie-Achsenbeschriftungen als Anti-Pattern (laut Video
    rendert sie nicht; **ANNAHME, ungeprüft**, erst in AP-5 nachweisen).
- Die in R6.1/R6.3 zurückgestellten Formen (Spaltenfärbung, Referenzlinie) werden nach dem
  ersten gerenderten Nachweis als Generatorfunktion gebaut, nicht vorher.
- **Fertig, wenn** jede neue Regel einen Test mit Gegenprobe hat und in
  `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md` steht.

- **Bestandsprüfung 24.09.2026** (gezählt, nicht geschätzt; Gegenprobe der tragenden Zahlen
  im selben Arbeitsschritt):
  - **Drei Formatierungsebenen: teilweise, nur dokumentiert.** Die Vorrangregel steht in
    `products/fabric/powerbi/docs/references/pbir-theme.md` („Three-Level Inheritance“), und
    `KNOWN_ERRORS_AND_FIXES.md` hält fest, dass Visual-Objekte property-weise mit dem Theme
    verschmelzen. Kein Code unterscheidet Dopplung von Widerspruch:
    `check_report_theme_compliance.py` zählt Überschreibungen nach fester Liste, liest das
    Theme aber nicht. Nächster Schritt: dort das aktive Theme auflösen und jede Überschreibung
    als doppelt, widersprechend oder neu einstufen, erst beratend.
  - **Alltagssprache → Property: Maschine da, Tabelle fehlt.** `tooling/visual_library/`
    friert Property-Namen des offiziellen Katalogs ein (12 Visual-Typen), ohne Anzeigenamen. Der
    Katalog selbst trägt sie: 560 von 629 Objekten und 7006 von 7455 Properties haben einen
    `displayName` (gemessen gegen `capabilities.json`, Pin 0.1.1, 60 Einträge). Beispiel
    `clusteredBarChart`: `dataPoint` = „Data colors“, `fill` = „Color“. Grenzen: nur Englisch,
    „Color“ ist ohne Objektpfad mehrdeutig, und `categoryAxis` heißt beim Balken „Y axis“, bei
    der Säule „X axis“. Nächster Schritt: `catalog_facts.py` friert die Anzeigenamen mit ein;
    eine dünne Synonymschicht in der Visual Library, deren jeder Eintrag im Test gegen
    `catalog_facts.json` aufgelöst wird.
  - **Bedingte Formatierung auf Achsenbeschriftungen: keine Regel, und eine Doku sagt das
    Gegenteil.** `docs/references/pbir-conditional-formatting.md` führt `labelColor` als
    unterstützt. Im Bestand kommt der Fall nicht vor: 0 datengebundene Achsen in 231
    `visual.json` des `dist/`. Ein Guard hätte heute nichts zu fangen. Deshalb erst in AP-5
    rendern, dann Regel, Gegenbeispiel-Fixture und Doku-Korrektur in einem Schritt.
  - Spaltenfärbung und Referenzlinie bleiben unverändert zurückgestellt (R6.1/R6.3).
- **Stand 24.09.2026, Alltagssprache → Property umgesetzt:** `catalog_facts.py` friert jetzt auch
  die Anzeigenamen des offiziellen Katalogs ein (`anzeige` je Visualtyp für die genutzten und die
  alltäglichen Objekte, `vco_anzeige` für Titel, Hintergrund, Rahmen ...), rein additiv.
  `visual_library/_format_synonyme.yaml` hält 20 Einträge (Begriffe deutsch und englisch →
  Objekt und Eigenschaft); `resolve.format_begriff(begriff, visual_type)` liefert Objekt,
  Eigenschaft und den Pfad im Format-Bereich, z. B. „achsenbeschriftung kleiner“ beim Balken →
  `categoryAxis.fontSize` → „Y axis › Text size“, bei der Säule „X axis › Text size“.
  `test_format_synonyme.py` löst jeden Eintrag gegen den Auszug auf. Dabei gefunden: die
  Visual-Library-Tests liefen in der CI nie (0 gesammelt, `KNOWN_ERRORS_AND_FIXES.md`).
- **Stand 24.09.2026, Formatierungsebenen umgesetzt (beratend):** `check_report_theme_compliance.py`
  stuft jede Überschreibung mit festem Wert gegen das aktive Theme ein (Vorrang visual.json vor
  Visualtyp-Ebene vor Wildcard; das aktive Theme löst `check_palette_monochrome.aktives_theme`
  auf). Gemessen über die 17 Berichte in `dist/`: 199 doppelt (entfernbar), 15 widersprechend,
  276 neu, 1 datengebunden, 32 je Serie gezielt. Stichprobe von Hand: COM-001 `Main_3`
  `labels.labelPosition` `OutsideEnd` gegen Theme `Auto` (widersprechend), `Main_1`
  `title.show` `true` wie Theme (doppelt). Die 199 Dopplungen aus dem Generator zu entfernen ist
  ein eigener Schritt; der Checker bleibt ohne `--strict-warnings` beratend.

### AP-9 · Ein Einstieg für die ganze Schleife
- Ein Kommando über S0 bis S7 mit `--stages`, Trockenlauf als Standard, `--apply` für den Tenant,
  Exit 0/1/2, Befund-JSON und Manifest als Ergebnis. Heimat nach E4.
- Ein Skill für den Agenten-Teil (ALUCA `docs/agent/skills/`): wann der Agent handeln darf
  (S0-Entwurf, S6-Kritik, Korrekturvorschlag als Diff gegen Bracket/Generator/Regel), und dass er
  `dist/` nie direkt ändert.
- **Fertig, wenn** ein Lauf für OPS-001 von der Spezifikation bis zum Abräumen ohne Handgriff
  durchläuft und das Manifest alle Eingaben und Pins nennt.

- **Stand 24.09.2026, ohne Tenant umgesetzt:** `python -m tooling.agentic_loop.schleife --use-case
  <UC> --run-id <id> [--stages …] [--apply]` in ALUCA. Die Schleife ruft nur vorhandene Werkzeuge
  auf (S0 Drift-Gate und Use-Case-Qualität, S1 die fünf Codegen-Prüfungen, S2 `report_quality`,
  S3 Bereitstellung plus `sandbox.py`, S6 Meridians `check-image` als eigener Prozess, S7
  `sandbox.py down`). Tenant-Schritte laufen nur mit `--apply` und gesetzten Zugangsdaten.
  Was noch nicht gebaut ist, meldet sich als „nicht prüfbar“ mit Grund: Datenscheibe laden (AP-3),
  Datensatz-ID für S4 und Bericht-ID für S5 aus dem Deploy (AP-2/AP-4/AP-5). Gemessen im
  Trockenlauf für OPS-001: S0 bis S3-Bereitstellung `ok`, 7 Schritte „nicht prüfbar“, Exit 2.
  Skill `docs/agent/skills/run-agentic-loop.md`. 9 Tests; Gegenprobe: Trockenlauf-Sperre bzw.
  Exit-Vorrang mutiert → je der zuständige Test rot.

### AP-10 · CI
- `visual-fabric.yml` (Meridian) um den Schleifenlauf erweitern: `workflow_dispatch`, optional
  nächtlich, nur mit gesetzten Secrets, Budget aus §5.
- Vorher `bootstrap-fabric` einmal grün, damit die 30 roten Läufe erklärt sind.
- **Fertig, wenn** ein Lauf mit echtem Runner grün ist und die PNGs als Artefakt anhängen.

### AP-11 · Lokales Modell: messen, dann routen
Anlass: Flo, 24.09.2026, schlägt ein lokales Modell (genannt: Qwen 3.8 27B, Apache 2.0, seit
August 2026, bildfähig, Tool-Calling, rund 17 GB) für Studio-Aufgaben, DAX und Berichtsarbeit
vor. Kostenersparnis für ihn, Datenresidenz und planbare Kosten für Kunden.

- **Das Fundament steht schon in Meridian** (`docs/plans/ROADMAP_Meridian_LLM_Agnostik_und_Authoring.md`):
  lokaler OpenAI-kompatibler Adapter (M1), Capability-Gate (M2), Residenz-Gate (M3),
  Agent-Runtime (M4), zitierpflichtiges Web-Authoring (M5), Profile und Eval-Gates (M6).
  Hier wird erweitert, kein zweiter Weg gebaut.
- **Lücke 1, Studio:** `studio/src/ai/` baut nur den Anthropic-Provider; jeder andere wirft
  `NotImplementedError`. Ein OpenAI-kompatibler Provider (Spiegel von
  `meridian/ais/adapters/openai_compat.py`) macht das Studio lokal lauffähig.
- **Lücke 2, Eval je Aufgabenklasse:** Unsere Tore sind die Messung. Dieselben Aufgaben laufen
  gegen beide Modelle, gezählt wird, wie oft das Ergebnis das zuständige Tor besteht:
  Bracket-Entwurf → Schema und Golden Thread; DAX-Entwurf → AP-4-Laufzeitprüfung;
  Measure-Beschreibung → `ai_description`-Regeln; Judge → Übereinstimmung aus AP-7;
  Web-Authoring → Zitat-Abdeckung und Verify-Pass aus M5. Ergebnis: eine Tabelle
  Aufgabe × Modell × Quote × Kosten × Zeit. Erst danach wird geroutet (E7).
- **Erst gehostet messen, dann Hardware kaufen.** Das Modell ist bei Hostern über eine
  OpenAI-kompatible Schnittstelle erreichbar; derselbe Adapter misst es ohne eigene GPU. Ob
  eine lokale Maschine sich rechnet, hängt an Flos heutigem API-Verbrauch, der hier nicht
  gemessen ist (**ANNAHME, ungeprüft**).
- **Denkbudget je Aufgabe festlegen.** Frühe Berichte nennen, dass das Modell ohne Vorgabe
  sehr lange nachdenkt. Das Profil bekommt je Aufgabe Modus und Tokenbudget.
- **Websuche:** Die Qualität à la Perplexity entsteht im Abruf (Suchindex, Nachladen,
  Umsortieren, Zitieren), nicht im Modell. Suchquelle ist eine Entscheidung (selbst gehostete
  Metasuche wie SearXNG oder eine Such-API). Unsere Zitierpflicht aus M5 bleibt das Tor.
  **Residenz:** eine Suchanfrage verlässt das Netz immer. Das Residenz-Gate muss deshalb
  zwischen Anfrage-Abfluss und Daten-Abfluss unterscheiden, und eine Anfrage darf keine
  Kundendaten tragen (prüfbar gegen die Kundendaten-Sperrliste).
- **Fertig, wenn** die Tabelle für mindestens drei Aufgabenklassen gemessen ist und das Studio
  mit einem lokalen Profil eine Assist-Aufgabe ohne Abfluss erledigt (Residenz-Gate grün).

- **Stand 24.09.2026, ohne Modell-Lauf umgesetzt** (Meridian D-459): Lücke 1 geschlossen.
  `studio/src/ai/OpenAICompatProvider.js` (Chat-Completions, Streaming, `response_format`),
  `bootstrap.js` verdrahtet `local` (nie mit gespeichertem Key) und `openai`. Dabei gefunden
  und behoben: das Residenz-Gate glaubte dem Wort `local`; ein `local`-Profil mit
  `https://openrouter.ai` galt als abflussfrei, in Python und JS. Jetzt prüfen beide den Host
  gegen dieselbe Fallliste (19 Fälle). Lücke 2 als Gerüst: `meridian/ais/task_eval.py` zählt
  Tor-Quoten je Aufgabenklasse und Profil. Gemessen ist damit noch nichts; die Tabelle braucht
  echte Läufe.

## 7 · Offene Entscheidungen (Flo)

| # | Frage | Optionen | Empfehlung |
|---|---|---|---|
| E1 | Welcher Tenant? | Sandbox eines Kunden · eigener Trial/Dev-Tenant | **Entschieden 24.09.2026 (Flo): eigener Tenant**, wird neu aufgesetzt. die Kunden-Sandbox wird nicht genutzt |
| E2 | Datenanbindung im Sandbox | Lakehouse + Import · Lakehouse + Direct Lake · Tabellen im Modell eingebettet | nach dem AP-3-Versuch entscheiden; Deckel 50 MB als Startwert |
| E3 | Deploy-Werkzeug | `fab` CLI (in Meridian schon genutzt) · `fabric-cicd` (Microsoft-Bibliothek) · Fabric-REST direkt | **Entschieden 24.09.2026 (Flo): `fabric-cicd`**, über das vorhandene `fabric_release.py`. Beleg: MS Learn, Items-API verlangt `byConnection`, `fabric-cicd` deployt `byPath`-PBIP |
| E4 | Heimat der Schleife | Meridian `products/pbi_visual_regression/` · ALUCA `tooling/` | **Entschieden 24.09.2026 (Flo): Klasse A nach `SHARED_SUBSTANCE.md`, eine Heimat plus Spiegel.** Sandbox-Lebenszyklus: Heimat ALUCA neben `orchestrator.py` und `fabric_release.py`. Rendern und Prüfen (`pbi_visual_regression`): Heimat Meridian. Gespiegelt wird erst ab `main` der Heimat |
| E5 | Darf der Judge blockieren? | beratend · blockierend ab gemessener Übereinstimmung | **Entschieden 24.09.2026 (Flo): beratend.** Blockierend nur als eigene spätere Entscheidung nach gemessener Übereinstimmung (AP-7) |
| E6 | Microsofts Agentic-Bundle adoptieren? | ja (Official-First) · nur MCP · nein | **Entschieden 24.09.2026 (Flo): ja, ohne Tabular Editor 3.** Ob der Modeling-MCP unter Linux einen PBIP öffnet, wird vor dem Einbinden gemessen (AP-1) |
| E8 | 20 Modellspalten ohne Gold-Quelle (AP-4-Befund) | je Lücke: Vertrag benennt um (`source_column`) · Gold-Generator ergänzt die Spalte · Spalte aus dem Modell | **Entschieden 24.09.2026 (Flo), in vier Gruppen nach gezählten Belegen:** (1) 8 Umbenennungen auf die Gold-Spalte (`Sales Units`→`Quantity`, `Purchase Amount`→`Procurement Amount`, `Actual Unit Price`→`Actual Unit Price Amount`, `Contracted Amount`→`On-Contract Amount`, `Purchase Quantity`→`Quantity`, `Inventory Value`→`Stock Value Amount`, `On-Hand Units`→`Stock Qty`, `Outcome Status`→`Action Outcome`); Spaltennamen im Modell bleiben. (2) Modell folgt der Gold-Körnung: SupplyChain bekommt `dim_category`/`dim_vendor`, `fact_procurement` hängt an `CategoryKey`/`VendorKey` statt an `ProductKey`; Experience verliert `fact_nps.QueueKey` samt Beziehung zu `dim_case_queue`. (3) Gold-Generator ergänzt `Region` (dim_customer) und `ABC_Class`/`XYZ_Class` (dim_product, aus Umsatz und Nachfrageschwankung; Schwellen werden vorgelegt). (4) Gold-Generator ergänzt die 7 ungenutzten Spalten. Umsetzung über Blueprints bzw. `generate_aurora_gold.py`, nie in `dist/` oder Gold von Hand. **Stand 24.09.2026:** Gruppen 1 und 2 umgesetzt (`tooling/codegen/model_alignment.py`, Blueprints SupplyChain/Experience), Sperrklinke 20 → 10; Gruppen 3 und 4 offen (Gold-Parquets, Größe vorher messen; ABC/XYZ-Schwellen vorlegen) |
| E7 | Welches Modell je Aufgabe? | Frontier-Modell über API · lokales Open-Weight-Modell · je Aufgabe geroutet | **Entschieden 24.09.2026 (Flo): nach gemessener Tor-Quote aus AP-11 (`task_eval.py`) routen.** Bis zur Messung bleibt alles auf dem Frontier-Modell |

## 8 · Bewusst nicht übernommen

- **JSON direkt vom Agenten editieren lassen.** Das Video nennt es langsam, teuer und
  fehleranfällig; unser Generator ersetzt es.
- **Tabular Editor 3 + Windows-VM-Tunnel.** Kommerziell, und Microsoft deckt es offiziell ab.
- **Custom Visuals** für ganze Berichte. Nicht skalierbar, oft gesperrt.
- **Kundenseitige Laufzeit.** Die Schleife ist unsere Entwicklungspipeline. Kunden bekommen
  weiter reine PBIP/TMDL-Dateien (Official-First, Kundenseite).

## 9 · Einstieg für die Cowork-Sitzung

1. `CLAUDE.md` und `AGENTS.md` beider Repos lesen, dann dieses Dokument.
2. E2 und E8 mit Flo klären, bevor ☁-Pakete beginnen (E1 und E3 bis E7 sind entschieden). AP-1, AP-3 (Datenscheibe und Parameter,
   ohne Tenant) und AP-8 (Bestandsprüfung) gehen ohne Tenant.
3. Arbeitsstand in der Statuszeile R7 von `UMSETZUNGSPLAN_REPORT_EXZELLENZ.md` abhaken, mit
   Datum und Messung, nicht hier im Fließtext.
4. Vor jedem Commit: `python scripts/check_index.py --strict`, die betroffenen Tests, und im
   Freelancing-Repo `make check` sowie die Job-Nachstellung aus dessen `CLAUDE.md`.
