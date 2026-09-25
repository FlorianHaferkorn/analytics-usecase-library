# GitHub-Actions-CI — Usage-Limit, rote Läufe, Umgebungsgleichheit

> Wörtlich ausgelagert aus `CLAUDE.md` am 25.09.2026, damit die immer geladene Datei unter
> 200 Zeilen bleibt. Die Kurzregeln stehen weiter dort im gleichnamigen Abschnitt; hier liegen
> Historie, Belege und Befehle.

## Bekannte Usage-Limit-Bedingung (wiederkehrend)


> **Stand 01.09.2026: das Fenster ist zu, die CI läuft wieder echt.** Alles unter dieser
> Überschrift beschreibt eine Bedingung, die gerade **nicht** herrscht. Die Anweisung weiter
> unten, rote Läufe nicht zu untersuchen, gilt ausschließlich während eines gemessenen
> Limit-Fensters. Gemessen wird sie an `runner_id`, nie am Datum dieser Zeile. Was der Stand
> heute gekostet hat, steht im Nachtrag am Ende des Abschnitts.
Das Actions-Usage-Limit ist wiederholt erschöpft — repo-weit, **auf `main` und
allen Branches gleichermaßen**. Symptom: Jobs enden nach ~2 s mit
`conclusion=failure`, **ohne Runner** (`runner_id: 0`, leerer `runner_name`),
Logs liefern HTTP 404. Das ist **keine** Code-Ursache und durch keinen Diff zu
beheben.

Historie:
- Erste Ausprägung: bis 1. Juli 2026 — hat sich am 1. Juli von selbst gelöst
  (verifiziert durch durchgehend grüne CI-Läufe mit echten `runner_id`s bis
  einschließlich PR #386).
- Zweite Ausprägung (aktuell): erneut erschöpft. **Der Mechanismus ist belegt, nicht
  vermutet** (github/docs, `billing/concepts/product-billing/github-actions.md`,
  geprüft 31.07.2026): das Repo ist **privat**, damit sind Actions-Minuten
  kontingentiert — *„If your account does not have a valid payment method on file,
  usage is blocked once you use up your quota."* Und: *„At the start of each month,
  the minutes used by the account are reset to zero."*

  Daraus folgt datiert statt geraten: das Kontingent setzt am **1. August 2026**
  zurück. Wer nicht warten will, hat genau einen Hebel — eine gültige
  Zahlungsmethode bzw. ein Spending-Limit im GitHub-Billing. Beides liegt beim
  Kontoinhaber; im Code gibt es nichts zu beheben.

  **Nachtrag 03.08.2026 — der Reset ist eine Atempause, keine Lösung.** Er kam wie
  vorhergesagt, und am 03.08. liefen um **14:14/14:15 UTC** echte Läufe (201 s bzw.
  257 s, reale Runner, reale Assertions — die 13 Testfehler daraus sind echt). Ab
  **14:25 UTC desselben Tages** trägt jeder Job wieder `runner_id: 0`. Das
  Monatskontingent war binnen eines halben Tages aufgebraucht. Die Vorhersage „am
  1. August wird es grün" war für einen halben Tag richtig — als Planungsgrundlage
  taugt sie nicht.

  Der eigentliche Ertrag dieses Tages ist deshalb die **Unterscheidung**, nicht die
  Ursache: an einem Vormittag gab es beide Sorten Rot auf demselben Branch. Genau
  dafür steht die Tabelle unten — sie ist keine Formalie, sondern der einzige
  Unterschied zwischen „erklärt" und „verstanden".

**Aber: „rot" hat mehr als eine Ursache, und sie sehen von aussen gleich aus.** Am
31.07.2026 war `.github/workflows/source-updates.yml` **kein gültiges YAML** (ein
`python -c "…"` im `run: |`-Block auf Spaltenposition 0 beendete den Blockskalar). Alle 30
Läufe seit dem 29.07. waren rot — und gingen im Limit-Fenster unter, weil jeder rote Lauf
als erklärt galt. Der Unterschied ist messbar und in Sekunden zu prüfen:

| Ursache | Jobs des Laufs | Erkennung |
|---|---|---|
| Usage-Limit | vorhanden, `runner_id: 0`, ~2 s | `list_workflow_jobs` → Jobs da, kein Runner |
| Ungültige Workflow-Datei | **`total_count: 0`** | `python3 scripts/check_workflows.py` (lokal) |

Deshalb: **vor** dem Abhaken eines roten Laufs einmal `python3 scripts/check_workflows.py`
laufen lassen (steckt in `tooling/run_local_ci_check.sh` als erster Schritt). Ein Fenster,
in dem alles erklärt ist, ist das beste Versteck für einen echten Defekt.

**Und: „lokal grün" ist nicht dasselbe wie „CI grün".** Am 01.08.2026, im ersten Lauf mit
echten Runnern nach dem Reset, waren drei Tests rot, die lokal alle grün liefen. Drei
verschiedene Gründe, jeder eine eigene Fehlerklasse:

| Symptom | Ursache |
|---|---|
| `ModuleNotFoundError: pyarrow` | die CI-`pip install`-Liste kannte die Abhängigkeit nicht — das Gate **konnte** dort nie grün werden |
| `reference_graph.md is stale` (110 vs 109) | der Generator schlüsselte Measures nach **Dateinamen**; 31 Namen kollidieren über Domänen, wer gewinnt entschied die Dateisystem-Reihenfolge. 28 Measures fielen still heraus |
| `PBIR_PLATFORM_MISSING` | die CI installiert die PBIR-CLI **ungepinnt** und bekam 0.1.4 statt des Repo-Pins 0.1.1 — die neuere Fassung prüft `.platform`, unser Emitter schrieb keine |

Der Folgelauf zeigte zwei weitere — und beide waren **Wiederholungen derselben zwei Klassen**,
nur eine Schicht tiefer:

| Symptom | Ursache |
|---|---|
| `ModuleNotFoundError: pandas` | dieselbe Lücke wie bei `pyarrow`, dahinter versteckt: erst als pyarrow da war, kam der Import überhaupt bis zur nächsten Zeile |
| `use_case_storylines.md is stale` | dieselbe Klasse wie `reference_graph`: `_action_related()` las `*_business_case.yaml` als Action-Code. Beide tragen dieselbe `id`, nur einer hat `use_case_links` — wer gewinnt, entschied `rglob`. 22 Action-Codes betroffen, ihre `Connects to`-Kanten wurden still gelöscht |

Die gemeinsame Lehre: ein Test ist nur so aussagekräftig wie die Gleichheit der beiden
Umgebungen. Wo die CI weniger installiert, prüft sie etwas anderes; wo sie ungepinnt
installiert, prüft sie etwas Unvorhersehbares; und wo ein Generator vom Dateisystem abhängt,
prüft er ein Münzwurfergebnis. Alle fünf sind behoben — die Klasse bleibt. Und: eine gefundene
Ausprägung ist kein Beweis, dass die Klasse erledigt ist — beide kamen im nächsten Lauf wieder.

Gegen die Umgebungs-Ungleichheit hilft nur Gleichheit, nicht Sorgfalt. Deshalb wird die
CI-`pip`-Liste **in einem frischen venv** nachgestellt und die CI-Kommandozeile darin gefahren,
statt sich auf die lokal ohnehin installierten Pakete zu verlassen:

```bash
python3 -m venv /tmp/civenv
/tmp/civenv/bin/pip install pyyaml jsonschema pytest typer rich referencing python-docx pyarrow pandas vl-convert-python altair pillow
/tmp/civenv/bin/python -m pytest --tb=short -q      # exakt der CI-Aufruf
```

**Und der venv-Name gehört zum Repo, nicht zur Sitzung.** Gemessen 26.08.2026: ein
`/tmp/civenv`, das im selben Arbeitstag aus Meridians `requirements.txt` gebaut worden war,
lieferte hier `ModuleNotFoundError: pyarrow` in `test_shipped_model_has_no_hard_findings` —
ein Rot, das ausschließlich die Nachstellung erzeugt hat, und zwar genau die Fehlerklasse,
gegen die sie gebaut ist. Beide Repos verlangen einen frischen venv, aber **verschiedene**
Listen (dort `requirements.txt`, hier die Liste oben). Deshalb einen eigenen Pfad wählen,
etwa `/tmp/aluca_venv`, statt einen gemeinsamen Namen zweimal zu belegen.

Daher — für die Dauer jedes solchen Fensters: diese roten CI-Läufe **nicht
untersuchen und nicht re-triggern**; stattdessen **lokal** validieren. Für die
konsolidierte lokale Prüfung: `bash tooling/run_local_ci_check.sh` (führt
Drift-Gate, Python-Testsuite, Fabric-Bindings-Validator, PBI-Quality-Tools,
Health-Scorecard sowie die Studio-Checks — tsc/vitest/Playwright — in einem
Durchlauf aus und meldet alle Ergebnisse statt beim ersten Fehler
abzubrechen). Über das weitere Vorgehen (z. B. Merge) entscheidet der/die Maintainer:in.

**Die Stage-1-PowerShell-Suite ist nicht Windows-gebunden — das war eine Annahme, kein Befund.**
Am 01.08.2026 gemessen: `pwsh` 7.4.6 unter Linux fährt `tooling/run_stage1_checks.ps1` komplett
durch (20 Checks, rc=0), Pfade inklusive. Damit ist der zuvor hier dokumentierte „Windows-only"-
Blindfleck geschlossen:

```bash
pwsh -NoProfile -File tooling/run_stage1_checks.ps1     # setzt pwsh im PATH voraus
```

Zwei Randbedingungen, gemessen statt vermutet:
- `check_schema_validation.ps1` ist ein **Node**-Validator und macht ohne Deps einen
  Soft-Skip mit rc=0 — also einmal `npm ci` in `tooling/validation/`, sonst prüft er nichts
  und meldet trotzdem Erfolg.
- `check_validate_data_contracts.ps1` wird ohne das Modul `powershell-yaml` **übersprungen**
  (das Skript sagt das selbst: „SKIPPED, not passed"). Ist die PowerShell Gallery nicht
  erreichbar, deckt sein Python-Delegat dieselbe Logik ab:
  `python3 tooling/validation/check_validate_data_contracts.py --root .`

Dabei fiel eine dritte Sache auf, und die ist keine Randbedingung, sondern ein Regelkonflikt:
`check_markdownlint.ps1` fährt `markdownlint-cli2 --fix`, und MD010 („no hard tabs") ersetzt
Tabs **auch in Code-Blöcken** — ein Tab pro Leerzeichen. Genau in den ```tmdl-Blöcken, deren
Hardrule Tabs *verlangt*. Der Check hat damit still die Doku umgeschrieben, die er schützen
sollte: `tmdl_best_practices.md` und `pbir-rename-cascade.md` lehrten bereits Leerzeichen,
`AI_Description_Standard.md` wurde beim ersten Lauf mit installierten npm-Deps erwischt. Der
Konflikt ist an der Wurzel gelöst — `MD010: { "ignore_code_languages": ["tmdl"] }` in beiden
markdownlint-Konfigurationen, MD010 bleibt also für Fließtext scharf — und die Tabs sind in
allen drei Dokumenten wiederhergestellt. Lehre für neue Auto-Fixer: ein Formatierer, der
schreiben darf, muss die Hardrules kennen, sonst gewinnt der Formatierer.

**Nachtrag 01.09.2026 — das Fenster ist zu, und es hat drei Wochen lang einen echten Defekt
gedeckt.** Das Kontingent kam zum Monatswechsel zurück. Hier lief `Stage 1` danach in **5:41**
mit echtem Runner (`runner_id 1000017482`) grün durch — derselbe Commit `8f5955af`, der am
31.08. nach zwei Sekunden ohne Runner rot war. Der ALUCA-Diff war nie die Ursache.

Der Ertrag steckt im Nachbar-Repo. Dort war der erste echte Lauf **zu Recht** rot: vier Tests
in `core/dataarch_engine/tests/test_provision_gates.py` fuhren `subprocess.run` mit einem
absoluten Pfad aus der Sitzung, in der die Datei am 09.08.2026 entstand. Lokal existiert der
Pfad, auf einem Runner nicht. Drei Wochen lang war der Job `unit` deshalb rot, und im
Limit-Fenster sah dieses Rot aus wie jedes andere.

Das verschärft die hier stehende Regel, statt sie zu widerrufen. Während eines Fensters bleibt
lokal validieren der einzige Weg — aber ein **grüner lokaler Lauf ist währenddessen kein
Nachweis**. Er setzt die Gleichheit beider Umgebungen voraus, statt sie zu messen; genau diese
Voraussetzung war hier falsch. Was in einem Fenster grün war, wird beim ersten echten Runner
erneut gemessen und nicht als erledigt geführt.
