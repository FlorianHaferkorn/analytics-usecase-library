# Agent-Entwicklerwerkzeuge: Skills for Fabric und Notebook Toolkit

> Gespiegelt aus Meridian D-603 (Entscheidung Florian 30.09.2026) und dem Meridian-Regeltext
> `docs/regeln/tool-reuse-und-official-first.md`, Abschnitt „Agent-Entwicklerwerkzeuge“.
> Official-First gilt (ADR-0002): was Microsoft abdeckt, wird adoptiert. Die Kunden-Laufzeit
> bleibt tool-frei.

Beide Werkzeuge gehören zur eigenen Entwicklungsschleife. Sie ergänzen die ALUCA-Regeln,
Skills und Generatoren, sie ersetzen sie nicht, und sie binden nie ein Kunden-Deliverable.

## Skills for Fabric

`microsoft/skills-for-fabric`, Lizenz MIT.

| Feld | Wert |
|---|---|
| Marketplace | `fabric-collection` in `.claude/settings.json` (`extraKnownMarketplaces`) |
| Quelle | `{"source": "github", "repo": "microsoft/skills-for-fabric", "ref": "v0.3.18"}` |
| `autoUpdate` | `false` |
| an | `fabric-skills@fabric-collection` |
| aus | `powerbi-authoring@fabric-collection` |
| Pin | `tooling/quality/check_upstream_sources.py`, Eintrag `ref.skills_for_fabric`, Art `github` |
| Commit hinter dem Tag | `6c11ad58c25992e5d1435ce7cd80d217d5598a31`, gemessen 30.09.2026 per `git ls-remote --tags` |
| Peer-Test | `tooling/tests/test_upstream_sources_pins.py` (Settings und Pin gleich) |

`powerbi-authoring` bleibt aus, weil das Plugin `npx -y @microsoft/powerbi-modeling-mcp@latest`
ungepinnt startet; ALUCA pinnt den MCP-Server in `.mcp.json` auf 1.0.0. Nur gepinnter Code
läuft automatisch. Einschalten, sobald das Plugin den Server auf eine Version festlegt.

Claude Code pinnt eine Marketplace-Quelle nur per `ref` (Branch oder Tag); ein Commit-`sha`
gibt es nur für Plugin-Quellen (code.claude.com/docs/en/plugins/marketplace-reference, gelesen
in Meridian am 30.09.2026). Ein Tag ist verschiebbar. Deshalb meldet der Sensor
(`python tooling/quality/check_upstream_sources.py --summary`, zweimal wöchentlich in
`.github/workflows/source-updates.yml`) drei Befunde: gepinnter Tag fehlt (`pin_missing`),
Tag zeigt nicht mehr auf den gepinnten Commit (`pin_moved`), neuerer SemVer-Tag
(`update_available`). Er meldet, er hebt nie an.

- **Laden:** erst nach Annahme des Workspace-Trust-Dialogs. Meldet Claude Code „enabled in
  project settings but isn't installed“:
  `claude plugin install fabric-skills@fabric-collection --scope project`.
  Cloud-Sitzungen (claude.ai/code) laden Plugins aus der Projekt-`settings.json` nicht.
- **Anhebung:** Tag in `.claude/settings.json` und im Pin-Eintrag (`pin`, `commit`,
  `last_checked`) im selben Commit; vorher das CHANGELOG lesen und den neuen Commit per
  `git ls-remote --tags https://github.com/microsoft/skills-for-fabric.git` messen.
- **Bekannte Eigenschaften v0.3.18** (in Meridian gemessen im Klon, Commit 6c11ad58):
  25 von 26 Skills verlangen den Header `x-ms-fabric-skill` an `api.fabric.microsoft.com`
  (Telemetrie an Microsoft); `git-integration-operations-cli` ist `maturity: experimental`;
  Anmeldung über `az login`. `fabric-skills` registriert drei entfernte MCP-Server (FabricIQ,
  gehosteter Authoring-MCP, SQL-Endpoint). Learn rät, den lokalen und den gehosteten
  Authoring-MCP nicht gleichzeitig zu registrieren (siehe
  `products/fabric/powerbi/docs/references/powerbi-modeling-mcp-setup.md`).
- **Deploys:** die Skills verweisen auf fabric-cicd; das ist unser Weg. Artefakte, die ein
  Skill baut, gehen wie jede andere Änderung über Git → PR → fabric-cicd, nie direkt in einen
  Kunden-Workspace.

## Fabric Notebook Toolkit

CLI `fntk`, PyPI `fabric-notebook-toolkit`, Pin `0.0.1a10` (Eintrag
`pkg.fabric_notebook_toolkit`, Art `pypi`, im selben Sensor). Proprietäre Pre-Release-Lizenz:
keine Weitergabe (Ziffer 2e), kein Reverse Engineering (2b), Telemetrie. Nur gegen
Dev-Workspaces der eigenen Schleife.

```bash
pip install fabric-notebook-toolkit==0.0.1a10   # eigenes venv, nie in requirements*.txt
export FNTK_TELEMETRY_RUNTIME=off               # vor dem ersten Aufruf: lokale und entfernte Senke aus
fab config set mode command_line                # ALUCA-Regel: fab non-interaktiv
fab auth login                                  # fntk nutzt die Anmeldung der Fabric CLI
fntk init --agent claude --skip-fabric-skills -y # nur den Skill fabric-notebook-workflow
```

- `--skip-fabric-skills` ist Pflicht: ohne ihn installiert `fntk init` das Plugin
  `fabric-skills` selbst, ungepinnt und neben dem gepinnten aus `settings.json`.
- `FNTK_TELEMETRY_DISABLED=1` schaltet nur die entfernte Telemetrie ab, die lokale Ablage
  bleibt (PyPI-Beschreibung 0.0.1a10, in Meridian gelesen am 30.09.2026).
- **Grenze, maschinell erzwungen:** `tooling/validation/check_fntk_boundary.py` (Stage 1,
  `tooling/run_stage1_checks.ps1`) macht jede Nennung in `products/**` (samt `dist`),
  `core/**`, `tooling/**`, `.github/**` und jeder `requirements*.txt` rot. Ausnahmen stehen
  mit Grund in `EXEMPT` der Guard-Datei (der Guard selbst, das Pin-Register). Doku und Pläne
  unter `docs/` und `internal/` bleiben erlaubt. Der Guard sieht nur getrackte Dateien und
  endet mit 2, wenn `git ls-files` scheitert (nicht geprüft ≠ nichts gefunden).
- Nachmessen am 31.10.2026 (Meridian `feature_watch: fabric-notebook-toolkit-status`):
  Lizenz, Status, Telemetrie-Schalter, Verhalten von `fntk init`.

## VFS-Modus der Fabric-Data-Engineering-Extension für VS Code

VFS bearbeitet Workspace-Items direkt als entfernte Dateien; ein Speichern synchronisiert
sofort in den Workspace (Learn `fabric/data-engineering/author-notebook-with-vs-code-vfs-mode`,
in Meridian gelesen am 30.09.2026). Deshalb nur zur Dev-Iteration in einem nicht
Git-verbundenen Dev-Workspace. Nie über VFS in einen Git-verbundenen Workspace schreiben, das
umgeht Git. Quelle bleibt Git → PR → fabric-cicd.
