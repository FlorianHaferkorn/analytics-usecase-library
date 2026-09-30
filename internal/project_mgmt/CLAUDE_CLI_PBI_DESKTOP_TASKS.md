# Claude CLI (VS Code) — Power BI Desktop report tasks

## Why this file exists

**Any task that edits a PBIP report or semantic model and needs Power BI Desktop to validate must
run in the Claude CLI inside VS Code on a Windows dev box** — not in a cloud/Linux session. Only that
environment has all of: Power BI **Desktop** (the authoritative load/render gate), the **Fabric CLI**
(`fab`), the Windows-only **Stage-1 / Fabric quality-gate** PowerShell scripts, and the **MCP servers**
(Microsoft Learn for PBIR/TMDL/DAX docs, GitHub for the PR/CI). Linux sessions can edit and run the
Python/drift gates, but they **cannot** confirm a report still loads — that only shows up in Desktop
(the columnless / `get_Islands()` failure class in `KNOWN_ERRORS_AND_FIXES.md`).

This doc is the pickup brief for those tasks. A ready-to-paste **prompt is at the bottom**.

## Prerequisites (Windows dev box)

- Power BI **Desktop** installed and able to open the PBIP files under `products/fabric/powerbi/dist/`.
- Repo cloned; **check out the feature branch, not `main`** —
  `git fetch origin && git checkout claude/report-quality-roadmap-m997dz && git pull` (PR #390). The
  task's preconditions (canonical pointers, `check_standard_ref.py`, the SSOT dedup) live only on this
  branch; `main` does not have them, and all work commits back to this branch.
- Python env for the gates; **PowerShell** for `tooling/run_stage1_checks.ps1` and
  `tooling/quality/run_quality_gate.ps1` (Windows-only — the reason this runs here).
- **Fab CLI**: run `fab config set mode command_line` once per session before any non-interactive
  `fab` call (else it opens blocking prompts).
- **MCP servers** available in the CLI: **Microsoft Learn** (search/fetch official PBIR, TMDL, DAX,
  ISO/Fabric docs before inventing structure), **GitHub** (PR + CI). Use them instead of guessing.

## Ground rules (read before editing — repo doctrine overrides defaults)

1. Read `CLAUDE.md` + `AGENTS.md` first (router + TMDL/PBIR hardrules + Golden Thread).
2. **PostToolUse hooks are non-bypassable**: `validate_tmdl_style.sh` blocks Tab/`:=`/`description:`
   issues in `.tmdl`; `validate_pbir_structure.sh` blocks JSON syntax errors in PBIP `.json`/`.pbir`.
   If a hook blocks → **fix and retry, never bypass**.
3. TMDL hardrules: tabs (not spaces), `=` not `:=`, `/// Purpose:` comment not `description:`, set
   `summarizeBy`/`formatString`. Reference-don't-redefine: KPIs live in `core/kpi_catalog/`, never
   redefined in reports/models.
4. Commit footer (every commit):
   `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>` then
   `Claude-Session: <your session URL>`. **Never** put the model id in any pushed artifact.
5. ALUCA and Meridian are separate products — no co-branding.
6. GitHub Actions is in a known usage-limit outage (~2 s red, `runner_id:0`, HTTP 404 logs) — don't
   chase it; validate locally + in Desktop.

## Standard workflow for a PBI Desktop report/model task

1. **Understand** the target: which `.SemanticModel` and which `.Report` (a report's model is in
   `<Report>/definition.pbir` → `datasetReference.byPath.path`). Confirm measure names in the model's
   `definition/tables/_Measures.tmdl`. Note that a report's `nativeQueryRef` can be a **display alias**
   that differs from the defined measure name — reconcile in Desktop, don't assume.
2. **Edit** SSOT first (catalog/brackets/measure-defs), then the curated dist (`.tmdl` / `visual.json`).
   Dist is `no_overwrite` — it does not regenerate from the catalog; hand-edit it.
3. **Desktop-validate**: open each edited `.SemanticModel` and its report in Power BI Desktop; confirm
   it loads with no columnless/relationship errors and the visuals bind. This is the gate a Linux
   session cannot run.
4. **Gates**: `bash tooling/run_local_ci_check.sh` (drift-gate, pytest, `check_standard_ref.py --strict`,
   `check_usecase_quality.py --strict`, `validate_bindings.py`) **and** the Windows
   `tooling/run_stage1_checks.ps1` + `tooling/quality/run_quality_gate.ps1`.
5. **Regenerate** any generated artifacts touched: `tooling/codegen/kpi_catalog_files.py render`,
   ontology (`tooling/ir/build_ir.py`, `tooling/ontology/registry_builder.py`), goldens
   (`python -m tooling.superversion.from_aluca <bracket> --out tooling/superversion/tests/golden/<UC>.json`).
6. **Commit + push** to the branch; keep PR #390 updated.

---

## ✅ DONE (merged in PR #390): physical KPI de-duplication

This task is **complete** — executed via the CLI, Desktop-validated, and merged to `main` in PR #390
(catalog 127→119). Kept below as the reference example of the workflow. The **active** tasks are #2/#3
in the "Follow-up tasks" section further down; use the prompt at the very bottom of this file.

**Full technical spec (historical):** [`KPI_DEDUP_MIGRATION_RUNBOOK.md`](KPI_DEDUP_MIGRATION_RUNBOOK.md).
Summary of what was done:

- The SSOT dedup is **already done** (each twin KPI has a `canonical_kpi_id` pointer;
  `tooling/validation/check_standard_ref.py` reports the duplicate sets). This task does the **physical**
  removal the Linux session could not validate.
- **7 twins → canonical:** `ops.otif.pct`, `scm.service_level.pct`, `ops.service_level.pct` →
  `KPI-SCM-007`; `ops.inventory.value.amount` → `KPI-FIN-002`;
  `ops.production.volume` → `KPI-OPS-009`; `ops.yield.pct` → `KPI-OPS-003`;
  `svc.nps.index` → `KPI-CUS-003`.
- **Report bindings are small:** only **FIN-001** (`Supply Chain Service Level %`) and **FIN-002**
  (`Production Volume Units`, `Yield %`) bind a twin measure. Reconcile measure names per model (the
  two Finance service-level twins collapse to one `OTIF %`; Experience already has `OTIF % (XD)`).
- Do it **one twin at a time**: SSOT edits → dist rename/rebind → **open the affected model(s) +
  report in Desktop** → gates → commit. Don't batch blind.

### Definition of done
- All 7 twin KPI files deleted; every reference rewired + deduped; `check_standard_ref.py --strict`
  duplicate-set report = **0 open** sets.
- Duplicate measures renamed/removed in the domain models; FIN-001 + FIN-002 reports rebound.
- **Every edited `.SemanticModel` and the FIN-001/FIN-002 reports open cleanly in Power BI Desktop.**
- Goldens regenerated; `run_local_ci_check.sh` green; Windows Stage-1 + Fabric quality gate green.
- Committed to `claude/report-quality-roadmap-m997dz`; PR #390 updated.

---

## Prompt — paste this into the Claude CLI (VS Code, Windows)

```
You are running in the Claude CLI in VS Code on a Windows dev box with Power BI Desktop, the Fabric
CLI, and the MCP servers (Microsoft Learn, GitHub). Repo: analytics-usecase-library.

FIRST, check out the feature branch — do NOT work on main. The task's preconditions (the
canonical_kpi_id pointers, tooling/validation/check_standard_ref.py, the whole SSOT dedup) exist ONLY
on this branch, and all work commits back to it:
    git fetch origin && git checkout claude/report-quality-roadmap-m997dz && git pull
(PR #390 tracks this branch.)

Read these before touching anything: CLAUDE.md, AGENTS.md, and
internal/project_mgmt/CLAUDE_CLI_PBI_DESKTOP_TASKS.md (the handoff brief) plus
internal/project_mgmt/KPI_DEDUP_MIGRATION_RUNBOOK.md (the technical spec).

Task: execute the physical KPI de-duplication in the runbook — delete the 7 twin KPIs, rewire and
dedupe all references, rename/remove the duplicate measures in the domain semantic models, and rebind
the FIN-001 and FIN-002 reports to the canonical measures.

Do it ONE twin at a time, and for each: (1) make the SSOT + dist edits, (2) OPEN the affected
.SemanticModel and its report in Power BI Desktop and confirm it loads with no errors and the visuals
bind correctly — this Desktop check is the whole reason we're in the CLI, so do not skip it, (3) run
`bash tooling/run_local_ci_check.sh` plus the Windows `tooling/run_stage1_checks.ps1` and
`tooling/quality/run_quality_gate.ps1`, (4) regenerate goldens/ontology/catalog for the affected use
cases, (5) commit. Respect the non-bypassable TMDL/PBIR hooks (fix, never bypass), run
`fab config set mode command_line` before any non-interactive fab call, and use the Microsoft Learn
MCP for any PBIR/TMDL/DAX detail rather than guessing.

Done = all 7 twins gone, check_standard_ref --strict shows 0 open duplicate sets, every edited model +
the FIN-001/FIN-002 reports open cleanly in Desktop, all local + Windows gates green, goldens
regenerated, pushed to the branch with PR #390 updated. Commit footer:
Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com> and the Claude-Session line. Do not put the
model id in any pushed artifact; do not co-brand ALUCA with Meridian.

Start by pulling latest, reading the four docs, and printing the twin→canonical plan with the exact
files you'll touch for the first twin before editing.
```

---

## Follow-up tasks after PR #390 merge (#2 data-gap, #2b $schema lint, #3 checker)

PR #390 is merged to `main`. These are **new** work → branch fresh from `main`
(`git fetch origin main && git checkout -B claude/report-quality-roadmap-m997dz origin/main`)
and open a **new** PR. All three are Desktop/Fabric-gated (that's why they're here, not done on Linux).

### #2 — Source quality data into the Finance model (decided: "source the data")
FIN-002 (Cost Performance) shows `Quality % (FIN)` and `Quality Defect Rate %` as unit-cost drivers,
but their Finance measures reference tables the Finance model lacks — **dangling refs, broken columns**:
- `Quality % (FIN)` = `DIVIDE(SUM(fact_ops[Good Units]), SUM(fact_ops[Output Units]))` — `fact_ops` absent.
- `Quality Defect Rate %` = `DIVIDE(SUM(fact_quality[Defect Count]), SUM(fact_ops[Output Units]))` —
  `fact_quality` + `fact_ops` absent.
- (`Throughput Units (FIN)` is already correct on `fact_output` — leave it.)

Fix = give the Finance model the data (mirror how the Operations model sources it):
1. **Contract** `core/data_contracts/domains/finance.yaml`, table `fact_output` (grain
   plant_line_product_month): add `- {name: Good Units, type: decimal, agg: sum}` and
   `- {name: Defect Count, type: decimal, agg: sum}`; add `quality_rules` (Good Units ≤ Output Units;
   both ≥ 0; Defect Count ≥ 0).
2. **Semantic model** `Finance.SemanticModel`: add the two columns to `fact_output.tmdl`
   (mirror the existing `column 'Output Units'` block — `summarizeBy`, `sourceColumn`), and repoint the
   two measures in `_Measures.tmdl` off `fact_ops`/`fact_quality` onto `fact_output`:
   `Quality % (FIN)` → `DIVIDE(SUM(fact_output[Good Units]), SUM(fact_output[Output Units]))`;
   `Quality Defect Rate %` → `DIVIDE(SUM(fact_output[Defect Count]), SUM(fact_output[Output Units]))`.
   Drop the `/// NOTE: fact_ops … Finance model lacks it` comments.
3. **Seed data** — the crux: regenerate the Finance gold-layer `fact_output` (parquet + `_delta_log`)
   with the two new columns populated realistically (Good Units ≈ 0.96–0.99 × Output Units;
   Defect Count ≈ 0.01–0.04 × Output Units). Use the synthetic generator, not a hand-edit; verify with
   `scripts/check_showcase_delta.py`. Declaring the columns WITHOUT populating the parquet guarantees
   the columnless/`get_Islands` crash (KNOWN_ERRORS) — do them together.
4. **Generator** — update the Finance `fact_output` synthesizer so future regens emit the columns.
5. **Regenerate + validate**: goldens for FIN-002, catalog/ontology; `run_local_ci_check.sh`;
   **open Finance.SemanticModel + FIN-002 report in Desktop** and confirm both quality columns compute
   (non-blank) and the model loads clean.

### #2b — Pre-existing `$schema` PBIR lint (2 errors, identical on all 16 reports)
Fabric/`fab-inspector`-gated (no runnable validator on Linux). Run the report `$schema` validator
(`fab-inspector` / `powerbi-report-author validate`), read the 2 errors, fix at the source (likely a
stale/incorrect `$schema` URL or a missing required property in each `report.json`/`definition.pbir`),
and re-validate. 0-new from the dedup, so this is cleanup — batch the identical fix across all 16.

### #3 — Report measure-resolution check (close the validator gap)
`validate_bindings.py` checks projection structure only; nothing verifies a report's
`nativeQueryRef` resolves to a `measure '<name>'` in the model named by `definition.pbir →
datasetReference.byPath.path`. Build that check, BUT calibrate for PBIR `nativeQueryRef` being a
**display alias** that can differ from the defined measure name (e.g. reports bind `OTIF %` while the
Experience model defines `OTIF % (XD)`) — resolve via the actual measure entity reference in the
projection, not the alias string. Confirm it's green on the current dist in Desktop before wiring
`--strict` into `run_local_ci_check.sh`; run advisory first (BC-NARR→BC-CHART ratchet pattern).

---

## Prompt for the ACTIVE follow-up tasks (#2 + #3) — paste into the Claude CLI (VS Code, Windows)

```
You are running in the Claude CLI in VS Code on a Windows dev box with Power BI Desktop, the Fabric
CLI, and the MCP servers (Microsoft Learn, GitHub). Repo: analytics-usecase-library.

PR #390 (KPI standards program + use-case quality + KPI de-duplication) is already MERGED to main.
These are NEW tasks — branch fresh from main and open a NEW PR:
    git fetch origin main && git checkout -B claude/report-quality-roadmap-m997dz origin/main

Read first: CLAUDE.md, AGENTS.md, and internal/project_mgmt/CLAUDE_CLI_PBI_DESKTOP_TASKS.md
(the "Follow-up tasks after PR #390 merge" section has the exact per-surface steps for all three).

Do these three, each Desktop/Fabric-gated, one at a time with a Power BI Desktop load-check before commit:

#2 — Source quality data into the Finance model (decision already taken: "source the data", not remove).
  FIN-002's Quality % (FIN) and Quality Defect Rate % reference fact_ops/fact_quality, which the Finance
  model lacks → broken columns. Add Good Units + Defect Count to Finance fact_output (contract +
  fact_output.tmdl + REGENERATE the gold-layer parquet/_delta_log via the synthetic generator, populated
  realistically), repoint the two measures off fact_ops/fact_quality onto fact_output, regenerate goldens,
  and confirm in Desktop that both quality columns compute non-blank and the model loads clean. Declaring
  the columns without regenerating the seed data WILL cause the columnless/get_Islands crash — do them
  together.

#2b — Fix the pre-existing $schema PBIR lint (2 identical errors on all 16 reports) via fab-inspector /
  powerbi-report-author validate; batch the same fix across all reports; re-validate.

#3 — Build a report measure-resolution check (every report nativeQueryRef must resolve to a measure in
  the model its definition.pbir points at), calibrated for nativeQueryRef being a display alias that can
  differ from the defined name (resolve via the projection's real measure entity, not the alias). Run it
  advisory first, confirm green on current dist in Desktop, then wire --strict into run_local_ci_check.sh.

For each: run bash tooling/run_local_ci_check.sh plus the Windows tooling/run_stage1_checks.ps1 and
tooling/quality/run_quality_gate.ps1; respect the non-bypassable TMDL/PBIR hooks (fix, never bypass);
fab config set mode command_line before non-interactive fab; use the Microsoft Learn MCP for PBIR/TMDL/DAX
detail. Commit footer: Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com> + your own Claude-Session
line. No model id in pushed artifacts; no ALUCA/Meridian co-branding. Push to the branch and open a NEW
draft PR (do NOT reuse #390 — it is merged). Start by branching from main, reading the docs, and printing
your plan + exact files for #2 before editing.
```

---

# Übergabe 03.08.2026 — Report-Qualität (Konzept §17–§21)

> **Branch für diesen Block:** `claude/fabric-architecture-ai-standardization-uf4g7f`
> (nicht der oben genannte `claude/report-quality-roadmap-m997dz` — der gehört zu PR #390).
>
> **Zweck dieses Abschnitts:** alles, was in der Linux-Sitzung *gemessen* wurde, damit die
> Desktop-Sitzung eine **Prüfung** wird und keine Neuerhebung. Jede Zahl unten ist gemessen,
> nicht geschätzt; wo eine Annahme steht, ist sie als solche markiert.

## Was in der Linux-Sitzung bereits erledigt ist (nicht wiederholen)

Die Boutique-Craft-Rubrik ist von **54,4 auf 69,4 von 100** Punkten Abdeckung gestiegen —
`python3 tooling/report_quality/boutique_scorecard.py` zeigt den Stand. Verdrahtet wurden
`BC-LAYOUT-01`, `BC-LAYOUT-02`, `BC-COLOR-02`, `BC-TYPE-04`; der blinde Fleck von
`BC-CHART-04` (las nur `visual.json`, sah das Theme nicht) ist geschlossen.

Dabei entstand die Regel, die für alles Weitere gilt: **ein verdrahteter Validator muss
scheitern können.** `tooling/tests/test_rubric_integrity.py` erzwingt das maschinell —
ein advisory-Checker, der immer 0 zurückgibt, darf nicht als Prüfer eingetragen werden.
Zwei Kandidaten (`check_tabular_numerals.py`, `check_reference_lines.py`) sind genau
deshalb **nicht** verdrahtet, obwohl sie fertig aussehen.

### Nachtrag 03.08.2026 — die beiden Kandidaten sind *nicht* derselbe Fall

Beide tragen denselben Satz („await a governed emit — Windows/Fabric **or
powerbi-report-author**"). Am offiziellen Katalog gemessen (CLI 0.1.1, headless unter
Linux) trennen sie sich sofort:

| Regel | Befund am Katalog | Folge |
|---|---|---|
| **BC-TYPE-02** (Tabular Numerals, Gew. 4) | `formatting search tableEx "numeral\|figure\|tabular"` → **leer**. Der einzige Hebel ist `values.fontFamily` / `total.fontFamily` | Die CLI kann die Form **nicht** liefern, weil die Eigenschaft in Power BI nicht existiert. Kein Emit-Rückstand, sondern eine **Schriftentscheidung** |
| **BC-CHART-05** (Referenzlinie, Gew. 3) | `y1AxisReferenceLine` **existiert**, voller Satz: `show · value · displayName · lineColor · style · shadeShow · dataLabel*` | Die im Docstring genannte Entsperrbedingung ist **erfüllt** — die Form ist verifiziert |

**BC-TYPE-02 ist damit keine Desktop-Aufgabe mehr, sondern eine Doktrinfrage.**
`tokens/typography.yaml` entscheidet bereits: `numerals: tabular` ist gefordert,
`display: "DIN"` ist als Zweitschrift ausdrücklich erlaubt (BC-TYPE-01 deckt das) — aber
`display_roles: [callout]` beschränkt DIN auf die Hero-Zahl. Tabellen-Wertspalten sind
nicht abgedeckt. Zu entscheiden ist genau eine Zeile: gehört die Display-Schrift auch in
`values`/`total` von Tabelle und Matrix?

**BC-CHART-05 hat eine zweite Grenze, die der Katalog sichtbar macht:** `value` ist
`numeric`, es gibt **keine** Measure-Bindung. Der Wert muss also aus einer governten
Quelle als Zahl kommen — das ist `core/kpi_catalog/benchmarks.yaml`. Dort sind nur die
**normativen** Einträge als Ziellinie zulässig (`KPI-OPS-011` 85,0 mit Komponenten
`availability 90,0 · performance 95,0 · quality 99,0`; `KPI-SCM-007` 95,0;
`KPI-QUA-001` 98,0; `KPI-QUA-002` 1,0). Die **empirischen** sind Peer-Mediane —
die Datei sagt das selbst — und als „Ziel" gezeichnet wären sie irreführend.

### Nebenbefund, der wichtiger ist als beide: Spezifikation und Artefakt driften

`check_reference_lines.py` liest den `visual_type` aus dem **Bracket**. Alle drei
gemeldeten Exponate stehen dort als `line_chart`. Tatsächlich im dist:

| Exponat | Bracket sagt | Artefakt ist |
|---|---|---|
| OPS-001/Main_1 | `line_chart` | `lineChart` ✓ |
| OPS-001/Main_2 | `line_chart` | **`waterfallChart`** |
| SCM-001/Main_3 | `line_chart` | **`clusteredBarChart`** |

Zwei von drei driften. Und der Ausschluss, der das auffangen sollte, greift nicht:
`canonical_visual_id("waterfallChart")` → `None`, ebenso `"clustered_bar_chart"`. Das
`_INTRINSIC_DEVIATION`-Set trifft deshalb **still** nie — exakt die Fehlerklasse, vor der
der Docstring desselben Prüfers warnt („hoert beim Umbenennen STILL auf zu greifen").
Wer BC-CHART-05 verdrahtet, muss den Typ am **Artefakt** auflösen, nicht am Bracket, sonst
emittiert er eine Ziellinie in einen Wasserfall. Die Abbildung dafür existiert bereits
(`VISUAL_TYPE_MAP` in `products/fabric/powerbi/tooling/validation/check_page_template_compliance.py`)
und ist invers zu verwenden — keine zweite bauen.

### Der Struktur-Score war kein Rubrik-Problem, sondern eine Datei

Gemessen per umkehrbarem Versuch (Theme getauscht, wieder zurückgesetzt):

| Stand | Struktur-Score | rote Regeln |
|---|---|---|
| Ist bei Sitzungsbeginn | 71,7 % | 5 |
| nur Rasterfix (Commit `5bf00dc1`) | 77,5 % | 4 — **alle Theme** |
| Rasterfix + einheitliches Theme | **100,0 %** | 0 |

Alle fünf gingen auf **FIN-001** zurück: vier über sein Theme, eine über sein Layout. Die
Layout-Hälfte ist erledigt. Die Theme-Hälfte ist eine Doktrinentscheidung
(Monochromatic bleibt Hausstandard / Categorical wird es / zwei Themes bewusst) und keine
Testfrage — `BC-BRAND-02` und `BC-COLOR-02` hängen daran. **Die Abdeckung (69,4) hat sich
dabei nie bewegt**: sie zählt, wie viele Regeln verdrahtet sind, nicht wie viele bestehen.
Die beiden Zahlen werden leicht verwechselt.

## Was diese Umgebung kann und was nicht (gemessen)

| | |
|---|---|
| `powerbi-report-author` 0.1.1 (Repo-Pin) | ✅ läuft headless, auch unter Linux |
| `pwsh` → `tooling/run_stage1_checks.ps1` | ✅ 21 Checks, rc=0 |
| Python-Suite (2155 Tests) | ✅ |
| **Power BI Desktop** | ❌ — der Grund für diese Übergabe |
| `ibcs.com`, `iso.org` | ❌ Egress-Policy (Verbindung 000, nicht einmal 403) |

---

## A — Theme-Eigenschaften triagieren (der Hauptgrund, Desktop zu öffnen)

**Befund:** jeder der 17 dist-Reports meldet **24–26 Errors** des offiziellen Validators,
ausnahmslos im mitgelieferten Theme `Aurora_Group__Monochromatic__Light___2ECDE7.json`.
Frisch emittierte Reports sind sauber — der Unterschied ist das Theme, nicht der Emitter.

**Die Falle, in die ich fast gelaufen wäre:** das sind **nicht** 25 Defekte. `padding.left`
gilt für `advancedSlicerVisual` als unbekannt, obwohl **derselbe Katalog** `padding` als
shared VCO mit genau diesen vier Eigenschaften führt (`powerbi-report-author formatting
list-vcos`). Die CLI ist Public Preview und hat Katalog-Lücken. Pauschales Löschen hätte
gültige Formatierung entfernt.

Die Triage steht maschinenlesbar in `tooling/quality/known_errors.yaml`
(`pbir_theme_prop_unknown_catalog_gap` vs. `pbir_theme_prop_likely_defect`).

### Vermutlich Katalog-Lücke — in Desktop bestätigen, dann **behalten**

`padding.{top,bottom,left,right}` (advancedSlicerVisual) · `markers.{markerShape,markerSize}`
(scatterChart) · `lineStyles.{strokeLineCap,areaTransparency}` · `columnHeaders.backColor{Primary,Secondary}` ·
`rowHeaders.backColor{Primary,Secondary}`

### Vermutlich echter Defekt — in Desktop bestätigen, dann entfernen/umbenennen

| Fund | Beleg |
|---|---|
| `padding.show` | der Katalog führt für `padding` auf `*` genau vier Eigenschaften und beanstandet dort **nur** `show` |
| `outspace` | heißt im Theme-Format `outspacePane` |
| `header` auf `shape`/`actionButton`/`pageNavigator`/`bookmarkNavigator` | Buttons und Formen haben keine Kopfzeile |
| `calloutValue` auf `cardVisual` | gehört zum klassischen `card`, nicht zum neuen `cardVisual` |
| `text.text` (textbox) · `smallMultiplesLayout.*` · `legend.alignment` | noch nicht einzeln belegt |

**Prüfmethode in Desktop:** Theme laden, die Eigenschaft im Format-Bereich suchen. Greift
sie sichtbar → Katalog-Lücke, Eintrag bleibt, CLI-Pin beim nächsten Bump neu bewerten.
Greift sie nicht → entfernen. Die Doku deckt das Entfernen ausdrücklich: *„Any formatting
elements that aren't included in the JSON file revert to their default values and
settings."*

**DoD:** jede der 25 Zeilen einer der beiden Klassen zugeordnet, mit Beleg; die bestätigten
Defekte entfernt; `BASELINE_ERRORS` in `tooling/tests/test_dist_validator_ratchet.py`
gesenkt; alle 17 Themes bleiben inhaltlich identisch (`test_theme_consistency.py`).

---

## B — Varianzbrücke: `waterfallChart` bindet zu viele Measures (11 von 17 Reports)

**Befund:** `PBIR_ROLE_MAX_EXCEEDED` — 2 bis 5 Measures an Rolle `Y`, der offizielle
Katalog erlaubt **eine**. Der Superversion-Emitter kappt korrekt
(`targets/pbir.py::_PLANS["waterfall"].primary_max == 1`), der Alt-Generator, aus dem die
dist-Reports stammen, tat es nicht.

**Der naheliegende Fix ist falsch, und das ist gemessen.** Kappen auf die erste Measure
entfernt:

| Seite | behalten | entfernt |
|---|---|---|
| OPS-001 | `OEE %` | `Availability %`, `Performance %`, `Quality %` |
| COM-001LY | `Plan Sales Amount` | `Price Effect`, `Volume Effect`, `Mix Effect`, `Net Sales` |

**OEE *ist* Availability × Performance × Quality**, und COM-001LY ist eine Brücke
Plan → Preis → Menge → Mix → Ist. Die Kappung erzeugt eine Datei, die der Validator
akzeptiert und die die Zerlegung nicht mehr zeigt.

**Die eigentliche Frage (Entscheidung Flo, offen):** eine Varianzbrücke gehört bei
`waterfallChart` als **eine** Measure plus eine **Category**, die die Schritte aufzählt —
nicht als N Measures an Y. Das umzustellen berührt das Bracket-Schema, den Emitter und
vermutlich das Semantikmodell (eine Schritt-Dimension oder eine berechnete Tabelle).

**Stand:** `visual_builder.build_waterfall` kappt seit 03.08.2026 **und meldet laut**
(`logging.warning` mit den wegfallenden Measures), damit künftige Läufe gültig sind und der
Verlust nicht still passiert. Die ausgelieferten Artefakte sind **unangetastet**.

**Warum das hierher gehört:** der Emitter-Teil ginge headless, aber ob eine als Category
modellierte Brücke in Desktop *als Brücke* rendert, sagt nur Desktop. Empfehlung: erst die
Modellierung entscheiden, dann einen Report als Muster umbauen und ansehen, dann die
übrigen zehn.

---

## C — `BC-COLOR-03`: bedingte Formatierung emittieren, dann prüfen

**Befund:** die Regel („rot/grün nie allein — immer mit Icon/Gewicht") ist **nicht**
verdrahtet, weil ein Prüfer heute **leer bestünde**: keines der 188 Visuals setzt eine
semantische Farbe, und keine der 221 Measures erzeugt ein Richtungszeichen (kein ▲/▼/↑/↓,
keine `*Color`-/`*Icon`-Measure). Im Manifest steht dafür die Kategorie
`validator_blocked: vacuous_no_subject`.

**Aufgabe:** bedingte Formatierung tatsächlich emittieren (Statusfarbe auf den KPI-Karten,
gepaart mit einem Richtungsglyph), in Desktop ansehen, dann den Prüfer bauen und
verdrahten. Die Semantikfarben liegen im Theme (`good` `#519872`, `bad` `#EC4E20`,
`neutral` `#F6AE2D`) und in `tokens/color_semantics.yaml`.

---

## D — `BC-NARR-06`: Smart-Narrative-Grounding

**Befund:** alle 16 `smartNarrativeVisual` tragen **null** Konfiguration — nur
`{"visualType": "smartNarrativeVisual"}`. Der Text entsteht beim Rendern aus dem
Seitenkontext; im Artefakt gibt es keine Zahl, deren Herkunft prüfbar wäre.
`validator_blocked: render_verification`.

**Aufgabe:** in Desktop prüfen, ob die erzeugten Zahlen auf governte Measures zurückgehen
und ob die Erzählung filterlebendig ist. Falls ja, festhalten, wie sich das künftig
maschinell absichern lässt (z. B. Narrative als DAX-Measure statt als Auto-Visual — die
`Narrative Text (<SUFFIX>)`-Measures existieren bereits und werden von
`build_narrative_card` gebunden).

---

## E — Zwei Entscheidungen mit trivialer Umsetzung (brauchen kein Desktop)

1. **`Brand_Rose__Monochromatic__Lig…json`** liegt in allen 17 Reports, ist **nicht** das
   aktive Theme, führt **über 300 Farben** über den ganzen Farbkreis und widerlegt damit
   seinen eigenen Namen. Löschen? (Nicht angefasst: eine registrierte Ressource zu
   entfernen hat Folgen, die ich nicht gemessen habe.)
2. **`brand.data_colors`** in `tokens/color_semantics.yaml` ist ein Regenbogen (8 Farben
   über den ganzen Kreis) und widerspräche `BC-COLOR-02`; das emittierte Theme ist
   monochrom. Der Token hat heute **keinen Code-Konsumenten**. Welche Markenpalette gilt?

---

## Reihenfolge-Empfehlung

**A und D in einer Sitzung** — beide brauchen nur „Theme laden, hinsehen", und A ist der
teuerste Punkt, wenn er einzeln gemacht wird. **C** danach, weil es erst etwas zu sehen
gibt, wenn emittiert wurde. **B** zuletzt und nur nach der Modellierungsentscheidung.
**E** jederzeit, auch in einer Linux-Sitzung.

Wer ohnehin Desktop offen hat: **L10** (Power-BI-Decke ausreizen, Konzept §L10) liegt
ebenfalls dort und lohnt sich im selben Termin.

## Prompt — in die Claude CLI (VS Code, Windows) einfügen

```
Lies zuerst CLAUDE.md und AGENTS.md, dann internal/project_mgmt/CLAUDE_CLI_PBI_DESKTOP_TASKS.md
Abschnitt "Übergabe 03.08.2026 — Report-Qualität". Branch:
claude/fabric-architecture-ai-standardization-uf4g7f (git fetch && git checkout && git pull).

Arbeite Aufgabe A ab (Theme-Eigenschaften triagieren), danach D. Die Triage steht in
tooling/quality/known_errors.yaml — bestätige jede Zeile in Power BI Desktop, statt sie zu
übernehmen. Für jede bestätigte Katalog-Lücke: Eintrag behalten und im Ledger vermerken.
Für jeden bestätigten Defekt: entfernen bzw. umbenennen.

Harte Randbedingungen:
- Ein verdrahteter Validator MUSS scheitern können (test_rubric_integrity.py erzwingt das).
- Alle 17 Themes müssen inhaltlich identisch bleiben (test_theme_consistency.py).
- Nach jeder Verbesserung BASELINE_ERRORS in test_dist_validator_ratchet.py senken.
- KEINE Kappung von waterfallChart-Measures ohne die Modellierungsentscheidung aus B —
  sie zerstört OEE-Zerlegungen und Varianzbrücken.

Vor Commit: pwsh tooling/run_stage1_checks.ps1, python -m pytest tooling/ products/ -q,
python3 scripts/check_index.py --strict. Ergebnisse im Konzept-Ledger
(docs/plans/KONZEPT_LAYOUT_SYSTEM.md §9) abhaken.
```

---

# Nachtrag 05.08.2026 — was seit dem 03.08. erledigt ist, und was übrig bleibt

> **Gleicher Branch:** `claude/fabric-architecture-ai-standardization-uf4g7f`.
> Dieser Nachtrag ändert den Stand der Punkte **A–E** oben. Wer die Desktop-Sitzung
> aufnimmt, liest **zuerst diesen Abschnitt** — drei der fünf Punkte sind zu.

## Punkt B — erledigt (Linux, kein Desktop nötig)

`PBIR_ROLE_MAX_EXCEEDED` ist **0 über alle 18 Reports** (vorher 11). Die
Modellierungsentscheidung aus B war nur in **einem** Fall nötig:

| | Anzahl | Was es war |
|---|---|---|
| Drift | 10 | Das Bracket sagte `waterfall`, fachlich war es ein Ranking bzw. eine Zeitreihe. Umgestellt auf `clusteredBarChart` (9) bzw. `lineChart` (1) |
| echte Brücke | 1 | COM-001LY. Umgebaut nach dem Katalogmodell: **eine** Measure an `Y`, `dim_pvm_driver[Driver]` an `Category`, Endbalken über `valueAxis.totalsEnabled` |

Die Falle aus B ist bestätigt und umgangen: `Net Sales Amount` als fünfte Kategoriezeile
hätte die Brücke **verdoppelt** — jeder Balken ist ein kumulativer Delta-Schritt, der
Endbalken kommt aus `totalsEnabled`, nicht aus einer Zeile. Ergänzt wurde nur die
Startstufe `Plan Sales` in `dim_pvm_driver.tmdl` + der `PVM Bridge Value`-SWITCH.

**Nicht mehr offen.** Die Warnung in `visual_builder.build_waterfall` bleibt als Netz.

## BC-TYPE-02 — erledigt, und zwar durch Messung statt Entscheidung

Der 03.08.-Eintrag stellte es als Doktrinfrage („gehört DIN auch in `values`/`total`?").
Die Frage war falsch gestellt. Gemessen:

Microsoft dokumentiert **Selawik** als metrisch kompatibel mit Segoe UI und stellt es
quelloffen bereit. Aus den UFO-Quellen die `<advance width>` von zero..nine gelesen:

| Schnitt | Ziffernbreiten | Folge |
|---|---|---|
| Segoe UI Regular | 1 (1104) | tabular ✓ |
| Segoe UI Bold | 1 (1178) | tabular ✓ |
| **Segoe UI Light** | **4** (730/1022/1055/1087) | **proportional — auf Zahlenflächen verboten** |

Die Regel war also längst erfüllt: das Theme setzt Light nur auf Textrollen
(subTitle/legend/subheader/categoryLabels/cardVisual-label), nie auf Zahlen. DIN bleibt
auf `callout` beschränkt — kein Bedarf, es auf `values`/`total` auszudehnen.

Der Befund steht als Evidenz in `core/templates/page_templates/tokens/typography.yaml`
(`tabular_numeral_fonts` / `proportional_numeral_fonts`). `check_tabular_numerals.py` ist
von advisory zu einem echten Gate umgeschrieben (löst Schriften auf `NUMERIC_SURFACES`
gegen die deklarierten Listen auf, `--strict` → rc=1) und in
`boutique_craft_rubric.yaml` verdrahtet. Abdeckung **69,4 → 73,4**,
`test_rubric_integrity.py`-Ratchet 5 → 4.

## Punkt E — entschieden

**Monochromatic bleibt Hausstandard.** Damit ist auch die Theme-Hälfte des Struktur-Scores
zu: **100,0 % Struktur-Score, 0 rote Regeln**.

## Was in derselben Sitzung sonst noch geschlossen wurde (Kontext, nicht Desktop)

- **Das Measure-Overlay ist weg.** `products/fabric/powerbi/specs/fabric_measure_overlay.yaml`
  und sein Validator sind gelöscht. Der Katalog ist jetzt alleinige Quelle für Formel
  (`technical.calculation` → `dax_synth`), DAX-Name (`technical.measure_name`),
  `formatString` (`business.unit_format` → `format_policy`, Profil `model`) und
  DisplayFolder (`use_case_ref`). 126 Measures synthetisiert, 12 mit dokumentiertem
  Platzhalter (`blocked_by` ist Pflichtfeld: data_contract/grammar/authoring/decision).
  Drei Gates verhindern die Rückkehr, u. a. `test_measure_overlay_stays_retired` und
  `test_recurring_grammar_gap_forces_an_operation` (ab 2 Vorkommen desselben Musters rot).
- **`unit_format` normiert** von 28 Freitextwerten auf 19 Tokens. Für alle 108 KPIs mit
  dist-Gegenstück reproduziert die Ableitung den bestehenden `formatString` exakt — 0
  Änderungen. **Eine** Formattabelle in `tooling/reporting/format_policy.py` mit drei
  Profilen (`model`/`visual`/`sv`); die beiden alten Substring-Matcher rufen sie auf.
- **Konforme Dimensionen** (Freelancing): `dim_material` wird **einmal** unter
  `transforms/_conformed/` gebaut, nicht je Domäne. Zwei Tests halten das fest.

## Übrig bleibt genau ein Desktop-Punkt: **A**

Punkt **A** (Theme-Eigenschaften, 24–25 Errors je Report) ist unverändert offen und
unverändert beschrieben — Vortriage in `tooling/quality/known_errors.yaml`, Klassen
`pbir_theme_prop_unknown_catalog_gap` vs. `pbir_theme_prop_likely_defect`. **C** und **D**
bleiben offen wie beschrieben; beide sind kein Blocker.

`BASELINE_ERRORS` in `tooling/tests/test_dist_validator_ratchet.py` steht auf **25**
(von 26 gesenkt). Jede in Desktop bestätigte Entfernung senkt sie weiter.

## Eine Randbedingung, die vor dem Merge zählt

**Seit drei Tagen hat kein CI-Job einen echten Runner gesehen** — Signatur `runner_id: 0`,
~2 s, Logs 404. Alles oben ist damit **lokal** verifiziert: 2099 Python-Tests grün,
`check_index.py --strict` ohne Hard-Findings, Freelancing `make check` +
`check_generators.py` A–F grün.

Diese Sitzung hat zweimal vorgeführt, dass das nicht dasselbe ist wie CI-grün: fünf Fehler
in zwei Läufen, alle nur auf echten Runnern sichtbar, zwei davon Wiederholungen derselben
Klasse. Die Umgebungs-Ungleichheit ist über das frische venv abgedeckt (CLAUDE.md
§„lokal grün"), die Generator-Klasse (Dateisystem-Reihenfolge entscheidet das Ergebnis)
ist es nicht. **Vor dem Merge einen echten Lauf abwarten.**

## Prompt — in die Claude CLI (VS Code, Windows) einfügen

```
Lies zuerst CLAUDE.md und AGENTS.md, dann in
internal/project_mgmt/CLAUDE_CLI_PBI_DESKTOP_TASKS.md den Abschnitt
"Nachtrag 05.08.2026" und danach "A — Theme-Eigenschaften triagieren".
Branch: claude/fabric-architecture-ai-standardization-uf4g7f
(git fetch origin && git checkout claude/fabric-architecture-ai-standardization-uf4g7f && git pull).

Punkt B und BC-TYPE-02 sind erledigt, E ist entschieden (Monochromatic bleibt) — nicht
erneut anfassen. Offen und deine Aufgabe: A.

Arbeite A ab: die 24-25 Validator-Errors je Report stammen ausnahmslos aus
Aurora_Group__Monochromatic__Light___2ECDE7.json. Die Vortriage steht maschinenlesbar in
tooling/quality/known_errors.yaml, in zwei Klassen. BESTAETIGE jede Zeile in Power BI
Desktop (Theme laden, Eigenschaft im Format-Bereich suchen: greift sie sichtbar ->
Katalog-Luecke der Public-Preview-CLI, Eintrag BEHALTEN; greift sie nicht -> entfernen).
Uebernimm die Vortriage nicht ungeprueft — genau davor warnt der Abschnitt.

Harte Randbedingungen:
- Ein verdrahteter Validator MUSS scheitern koennen (test_rubric_integrity.py erzwingt das).
- Alle Themes muessen inhaltlich identisch bleiben (test_theme_consistency.py).
- Nach jeder bestaetigten Entfernung BASELINE_ERRORS in test_dist_validator_ratchet.py
  senken (steht auf 25).
- PostToolUse-Hooks sind nicht umgehbar: blockt einer, Verstoss fixen und neu versuchen.
- fab config set mode command_line vor jedem nicht-interaktiven fab-Aufruf.
- Microsoft-Learn-MCP fuer PBIR/TMDL/Theme-Details nutzen statt raten.

Vor Commit: pwsh -NoProfile -File tooling/run_stage1_checks.ps1,
python -m pytest tooling/ products/ -q, python3 scripts/check_index.py --strict,
bash tooling/run_local_ci_check.sh. Ergebnisse im Ledger abhaken
(docs/plans/KONZEPT_LAYOUT_SYSTEM.md §9 + dieser Datei).

Zur CI: seit dem 03.08. laufen alle Jobs mit runner_id 0 (Usage-Limit, ~2s, Logs 404) —
das ist keine Code-Ursache. Vor dem Abhaken eines roten Laufs einmal
python3 scripts/check_workflows.py laufen lassen; ein echter Runner mit echter Laufzeit
ist dagegen ein echter Defekt.

Beginne damit, den Branch zu ziehen, die genannten Abschnitte zu lesen und die 25 Zeilen
aus known_errors.yaml als Pruefliste auszugeben, bevor du die erste in Desktop oeffnest.
```
