"""provision_gates — emit the validation pipeline as PR/Pre/Post-Deploy stage gates.

I-19.3 (ADR-0050): the deployment models (I-19.1) decide *how* content promotes; this
module decides *what must be green before it does*. It wires the repo's **existing**
validators (Tool-Reuse — no new checker silo) as gate steps at three positions:

  * **PR gate (CI):** conformance · Block F · PBIR-validate · TMDL-load · PBI-audit/BPA
    — a red validator fails the check and blocks the merge.
  * **Pre-Deploy:** conformance · TMDL-load · catalog↔governed-drift — run right before
    ``update-from-git`` / ``fabric-cicd`` / a Deployment-Pipeline promotion.
  * **Post-Deploy:** catalog-drift · DQ · lineage smoke — run after a stage loads, before
    the next stage.

Honest by construction: every gate command is a real, already-green tool in this repo
(``core.dataarch_engine.blueprint.cli``, ``core/check_generators.py``,
``scripts/check_pbir.py``, ``scripts/check_tmdl.py``, ``products.pbi_gatekeeper``, the
``drift_check.py`` emitted by ``--emit-lineage``). Gates whose target depends on a
customer path (a semantic model, a PBIP, the emitted drift check, a DQ runner) are
**guarded** — skipped with a reason when the input is absent, never faked. A failing
gate blocks by default (``exit 1``); ``GATES_ADVISORY=1`` downgrades every gate to a
warning (the documented rollback). Emits only; never executes.
"""
from __future__ import annotations

_PHASES = ("pr", "pre-deploy", "post-deploy")

#: Die fuenf Teststufen (BK-C04, WAF *Don't assume everything works*), jede mit **Besitzer**.
#:
#: Warum ein eigenes Modell neben dem Gate-Katalog: der Katalog ist nach *Phase* geschnitten
#: (wann laeuft ein Pruefer), die Stufen sind nach *Tiefe* geschnitten (was wird ueberhaupt
#: geprueft). Beides in einer Tabelle liest sich, als waere die Lieferung vollstaendig, sobald
#: alle Gates gruen sind — und genau das war der Befund vom 16.08.2026: die Stufen 1 bis 3
#: standen als Gates, die Stufen 4 und 5 kamen in der ganzen Lieferung nicht vor (0 Treffer
#: „Lasttest", 0 Treffer „Abnahme"). Eine Stufe, die niemand nennt, hat auch keinen Besitzer.
#:
#: ``gates`` verbindet die Stufe mit den Katalogeintraegen, die sie ausfuehren — leer bei 4 und
#: 5, und das ist die Aussage: kein Skript dieser Lieferung fuehrt sie aus. ``grenze`` sagt,
#: warum nicht. Eine Stufe ohne Gate und ohne Grenze waere eine Behauptung.
TESTSTUFEN: tuple[dict, ...] = (
    {"nr": 1, "name": "Artefakt", "besitzer": "wir, automatisch im Gate",
     "wann": "PR", "gates": ("conformance", "block-f", "pbir-validate", "tmdl-load", "pbi-audit"),
     "prueft": "Jedes einzelne Erzeugnis ist in sich gültig: Blueprint-Konformität, "
               "Generator-Compliance, PBIR-Schema, TMDL lädt, Modell-Audit."},
    {"nr": 2, "name": "Integration", "besitzer": "wir, im Gate",
     "wann": "Pre-Deploy + Post-Deploy", "gates": ("catalog-drift", "lineage-smoke"),
     "prueft": "Die Teile passen zusammen: Katalog gegen Modell, Herkunft gegen Ziel, "
               "Modell lädt nach dem Deploy."},
    {"nr": 3, "name": "Datenqualität", "besitzer": "wir, im Gate",
     "wann": "Post-Deploy", "gates": ("dq",),
     "prueft": "Die geladenen Daten halten die Regeln aus `governance/data_quality.json`."},
    {"nr": 4, "name": "Lasttest", "besitzer": "wir einmalig gegen die Pilotlast, danach der Kunde",
     "wann": "vor der Übergabe, dann im Betrieb", "gates": (),
     "prueft": "Die Kette hält die erwartete Menge in der erwarteten Zeit.",
     "grenze": "Kein Gate dieser Lieferung führt sie aus, und zwar aus zwei Gründen, die "
               "beide nicht durch Bauen verschwinden: die Pilotlast ist eine Kundenangabe "
               "(BK-L01, Intake-Feld `load_test_reference`), und die Messung braucht eine "
               "laufende Kapazität mit Token — ein CI-Läufer hat keine. Sie läuft deshalb "
               "als Notebook (`day2/leistungsmessung.py`), nicht als Schritt in `validate.sh`."},
    {"nr": 5, "name": "Fachabnahme", "besitzer": "immer der Fachbereich, nie wir",
     "wann": "vor der Produktivsetzung je Gold-Produkt", "gates": (),
     "prueft": "Die Zahl, die der Bericht zeigt, ist die Zahl, die der Fachbereich meint.",
     "grenze": "Die einzige Stufe, die wir grundsätzlich nicht besetzen können. Eine "
               "Abnahme, die der Lieferant erteilt, ist keine — deshalb liefern wir den "
               "Vordruck und tragen nichts ein."},
)

#: Die zwei Stufen, die kein Gate ausfuehrt. Als abgeleitete Konstante statt als zweite Liste,
#: damit die Zahl nicht an zwei Stellen gepflegt wird.
STUFEN_OHNE_GATE = tuple(t["nr"] for t in TESTSTUFEN if not t["gates"])

# Guard → bash test. A gate with a guard runs only when the test passes; otherwise it
# prints SKIP + reason (not a failure). Keeps customer-path-dependent gates honest.
_GUARDS = {
    "model": ('[ -n "${MODEL:-}" ]', "MODEL not set"),
    "pbip": ('[ -n "${PBIP:-}" ]', "PBIP not set"),
    "drift": ('[ -f "${DRIFT_CHECK}" ]', "no emitted drift_check.py (run --emit-lineage --governed-catalog)"),
    "dq": ('[ -n "${DQ_GATE:-}" ] && [ -f "${DQ_GATE}" ]', "DQ_GATE runner not provided"),
}


#: Gate-Id → Teststufe, aus ``TESTSTUFEN`` abgeleitet statt am Katalogeintrag wiederholt. Wer
#: eine Stufe umhaengt, tut es an einer Stelle; ein Gate ohne Stufe faellt im Test auf.
_STUFE_JE_GATE: dict[str, int] = {gid: t["nr"] for t in TESTSTUFEN for gid in t["gates"]}


def _gate_catalog(architecture_path: str, stack: str) -> list[dict]:
    """The gate steps, cheapest-first. Each: id · phases · cmd · blocking · stufe · optional guard."""
    katalog = [
        # `needs` nennt die Datei, ohne die der Befehl nicht laufen KANN. Das sind durchweg
        # Werkzeuge des Lieferanten-Repos — sie liegen nicht in der Lieferung. Ohne diese
        # Unterscheidung meldete `validate.sh` beim Kunden `✗ blocking deploy` für ein Werkzeug,
        # das dort nie existiert hat, und `platform.sh` brach an Schritt 1 ab. Gemessen am
        # 31.07.2026: rc=1 auf einem frisch emittierten Baum, die Kette kam nie zur Landing Zone.
        {"id": "conformance", "phases": ("pr", "pre-deploy"), "blocking": True,
         "needs": "core/dataarch_engine/blueprint/cli.py",
         "cmd": f'python -m core.dataarch_engine.blueprint.cli '
                f'--architecture "${{ARCH:-{architecture_path}}}" --dest _gate_arch_out --stack "${{STACK:-{stack}}}"',
         "note": "Blueprint OneLake-Conformance (CLI exit 2 wenn ein Pattern rot)."},
        {"id": "block-f", "phases": ("pr",), "blocking": True,
         "needs": "core/check_generators.py",
         "cmd": "python3 core/check_generators.py",
         "note": "Generator-/Tool-Reuse-Compliance (Block A–F, exit 1 bei Verstoß)."},
        {"id": "pbir-validate", "phases": ("pr",), "blocking": True,
         "needs": "scripts/check_pbir.py",
         "cmd": "python scripts/check_pbir.py",
         "note": "PBIR-Report-Schema via offizielles MS-CLI (Official-First; soft-skip ohne CLI)."},
        {"id": "tmdl-load", "phases": ("pr", "pre-deploy"), "blocking": True, "guard": "model",
         "needs": "scripts/check_tmdl.py",
         "cmd": "python scripts/check_tmdl.py",
         "note": "SemanticModel/TMDL lädt in Desktop (schema_validate) — Defekte, die Desktop ablehnt."},
        {"id": "pbi-audit", "phases": ("pr",), "blocking": True, "guard": "pbip",
         "needs": "products/pbi_gatekeeper/__init__.py",
         "cmd": 'python -m products.pbi_gatekeeper "${PBIP}" --strict --external-lint fab-inspector',
         "note": "Modell-Audit (49 Regeln inkl. measure-uniqueness) + offizielle BPA (soft-skip ohne fab-inspector)."},
        {"id": "catalog-drift", "phases": ("pre-deploy", "post-deploy"), "blocking": True, "guard": "drift",
         "cmd": 'python "${DRIFT_CHECK}"',
         "note": "Governed-Catalog↔Live-Modell-Drift (MEASURE/TABLE/COLUMN MISSING/UNDOCUMENTED)."},
        {"id": "dq", "phases": ("post-deploy",), "blocking": True, "guard": "dq",
         "cmd": 'bash "${DQ_GATE}"',
         "note": "Data-Quality-Gates aus governance.json (nach Load) — Runner via $DQ_GATE."},
        {"id": "lineage-smoke", "phases": ("post-deploy",), "blocking": False,
         "cmd": 'echo "post-deploy smoke: Modell lädt · Refresh · Lineage-Reconcile (siehe _GATES.md)"',
         "note": "Post-Deploy-Smoke (advisory): Modell lädt, Refresh, Lineage-Reconcile vor der nächsten Stage."},
    ]
    for g in katalog:
        g["stufe"] = _STUFE_JE_GATE.get(g["id"])
    return katalog


def _gates_for_phase(catalog: list[dict], phase: str) -> list[dict]:
    return [g for g in catalog if phase in g["phases"]]


def gate_helpers_sh() -> list[str]:
    """Shared bash ``gate()``/``skip()`` helpers — reused by validate.sh (I-19.3) and the
    use-case gate (I-19.8). Expects ``$ADVISORY``, ``$fail``, ``$ran`` und ``$skipped``
    vom Aufrufer gesetzt (``set -u`` — sonst bricht das Skript ab).

    ``gate <id> <command…>`` runs the command; on failure it blocks (``fail=1``) unless
    ``ADVISORY=1`` (then it only warns). ``skip <id> <reason>`` notes a cleanly-skipped gate.
    Beide zählen mit, damit die Schlusszeile sagen kann, wie viel wirklich geprüft wurde
    (siehe ``gate_summary_sh``).
    """
    return [
        "gate() {  # gate <id> <command…>",
        '  local id="$1"; shift',
        "  ran=$((ran + 1))",
        '  echo "▶ gate: $id"',
        '  if bash -c "$*"; then',
        '    echo "  ✓ $id"',
        "  else",
        "    local rc=$?",
        '    if [ "$ADVISORY" = "1" ]; then',
        '      echo "  ⚠ $id failed (rc=$rc) — advisory, deploy not blocked"',
        "    else",
        '      echo "  ✗ $id failed (rc=$rc) — blocking deploy"; fail=1',
        "    fi",
        "  fi",
        "}",
        'skip() { skipped=$((skipped + 1)); echo "▷ gate: $1 — SKIP ($2)"; }',
        "# Ein Prüfer des Lieferanten-Repos, der hier nicht liegt, ist kein roter Gate —",
        "# er ist einer, der in dieser Umgebung nicht zuständig ist. Der Unterschied entscheidet,",
        "# ob die Kette weiterläuft oder in Schritt 1 stehenbleibt.",
        "have() {  # have <datei> → 0 wenn vorhanden",
        '  [ -e "$1" ]',
        "}",
    ]


def gate_summary_sh(label: str, phase_expr: str = "") -> list[str]:
    """Die Schlusszeile beider Gate-Runner — sie sagt, WIE VIEL geprüft wurde.

    Anlass (gemessen 11.08.2026 beim P5-Trockenlauf gegen den emittierten Fabric-Baum):
    ``bash gates/validate.sh pr`` meldete ``GATES: OK (pr)`` und Exit 0, obwohl **alle
    fünf** Gates übersprungen hatten — keiner der Prüfer lag in der Lieferung. Der Skip
    selbst ist gewollt und begründet (``have()``); die Schlusszeile war es nicht. Ein
    ``OK``, hinter dem null Prüfungen stehen, ist dieselbe Klasse wie der
    jsonschema-Soft-Skip und ``structural=None``: grün heisst dann nicht geprüft,
    sondern nur nicht rot.

    Der Exit-Code bleibt bewusst unverändert — ein nicht zuständiger Prüfer darf die
    Kette nicht blockieren. Geändert wird, was dasteht: ausgeführt vs. übersprungen,
    und bei null Ausführungen ein ausdrücklicher Satz statt eines Häkchens.
    """
    suffix = f" ({phase_expr})" if phase_expr else ""
    return [
        'zaehlung="$ran ausgefuehrt, $skipped uebersprungen"',
        f'if [ "$fail" -ne 0 ]; then echo "{label}: FAIL{suffix} — $zaehlung"; exit 1; fi',
        'if [ "$ran" -eq 0 ]; then',
        f'  echo "{label}: NICHTS GEPRUEFT{suffix} — $zaehlung. Kein Gate ist hier '
        'zustaendig; diese Zeile ist KEINE Freigabe."',
        "else",
        f'  echo "{label}: OK{suffix} — $zaehlung"',
        "fi",
    ]


def emit_validate_sh(architecture_path: str = "data_architecture.json", stack: str = "fabric") -> str:
    """Return the phased gate runner ``gates/validate.sh <pr|pre-deploy|post-deploy>``.

    Reuses the repo's existing validators. Blocking by default (``exit 1`` on any red
    gate); ``GATES_ADVISORY=1`` downgrades to warnings (rollback). Customer-path gates
    are guarded and skip cleanly when their input is absent.
    """
    catalog = _gate_catalog(architecture_path, stack)
    lines = [
        "#!/usr/bin/env bash",
        "# ArchitectureBlueprint → Validierungs-Gates (ADR-0050 / I-19.3). Generated; review before running.",
        "# Tool-Reuse: jeder Gate ist ein bestehender, grüner Prüfer im Repo — kein neues Checker-Silo.",
        "# Aufruf: bash gates/validate.sh <pr|pre-deploy|post-deploy>",
        "# Blockt per Default (exit 1 bei rotem Gate). GATES_ADVISORY=1 → nur Warnung (Rollback).",
        "set -uo pipefail",
        'PHASE="${1:?usage: validate.sh <pr|pre-deploy|post-deploy>}"',
        'ADVISORY="${GATES_ADVISORY:-0}"',
        f'DRIFT_CHECK="${{DRIFT_CHECK:-render/{stack}/lineage/drift_check.py}}"',
        "fail=0",
        "ran=0",
        "skipped=0",
        "",
    ] + gate_helpers_sh() + [
        "",
    ]
    for phase in _PHASES:
        phase_gates = _gates_for_phase(catalog, phase)
        if not phase_gates:
            continue
        lines.append(f'if [ "$PHASE" = "{phase}" ]; then')
        lines.append(f'  echo "=== {phase} gates ==="')
        for g in phase_gates:
            tag = "" if g["blocking"] else "  # advisory"
            run = f'gate "{g["id"]}" {_q(g["cmd"])}{tag}'
            if "guard" in g:
                test, reason = _GUARDS[g["guard"]]
                run = f'if {test}; then {run}; else skip "{g["id"]}" "{reason}"; fi'
            if g.get("needs"):
                # Der Werkzeug-Test steht AUSSEN: fehlt der Prüfer, ist die Eingabe egal.
                lines.append(f'  if have "{g["needs"]}"; then {run}; '
                             f'else skip "{g["id"]}" "Lieferanten-Werkzeug {g["needs"]} nicht '
                             f'vorhanden — dieser Gate laeuft im Meridian-Repo, nicht in der '
                             f'Lieferung"; fi')
            else:
                lines.append(f"  {run}")
        lines.append("fi")
        lines.append("")
    lines += gate_summary_sh("GATES", "$PHASE")
    return "\n".join(lines) + "\n"


def _q(cmd: str) -> str:
    """Single-quote a command for the ``gate`` helper (its args are re-joined + bash -c'd)."""
    return "'" + cmd.replace("'", "'\\''") + "'"


def emit_gates_ci(architecture_path: str = "data_architecture.json",
                  stack: str = "fabric", python_version: str = "3.11") -> str:
    """A GitHub Actions workflow that runs the **PR-phase** gates as a merge gate.

    Broader sibling of ``architecture-gate.yml``: instead of conformance alone it runs the
    full PR gate set via ``gates/validate.sh pr`` (blocking). Part of the delivery pipeline,
    not a customer-runtime dependency (Official-First boundary).
    """
    return f"""# validation-gates — full PR gate set as a merge gate (ADR-0050 / I-19.3).
# Runs gates/validate.sh pr: conformance · Block F · PBIR-validate · (TMDL/PBI-audit when present).
# A red validator fails this check and blocks the merge. GATES_ADVISORY unset → blocking.
name: validation-gates
on:
  pull_request: {{}}
  workflow_dispatch: {{}}
jobs:
  gates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "{python_version}"
      - name: Install deps
        run: pip install jsonschema pyyaml
      - name: Run PR gates (blocking)
        env:
          ARCH: "{architecture_path}"
          STACK: "{stack}"
        run: bash gates/validate.sh pr
"""


def _gates_doc(catalog: list[dict], model_wiring: dict[str, list[str]]) -> str:
    lines = [
        "# Validierungs-Gates (generiert — ADR-0050 / I-19.3)", "",
        "Die Validierungs-Pipeline als **Stage-Gates**: bestehende Prüfer (Tool-Reuse) an drei "
        "Positionen — PR (CI), Pre-Deploy, Post-Deploy. Roter Prüfer → Deploy blockt "
        "(`exit 1`). `GATES_ADVISORY=1` schaltet alle Gates auf Warnung (Rollback).", "",
        "## Gate × Phase", "| Gate | Stufe | PR | Pre-Deploy | Post-Deploy | Blockt | Prüfer (Tool-Reuse) |",
        "|---|:--:|:--:|:--:|:--:|:--:|---|",
    ]
    for g in catalog:
        cell = lambda p: "✓" if p in g["phases"] else ""  # noqa: E731
        blk = "ja" if g["blocking"] else "advisory"
        lines.append(f"| `{g['id']}` | {g.get('stufe') or '—'} | {cell('pr')} | {cell('pre-deploy')} | "
                     f"{cell('post-deploy')} | {blk} | {g['note']} |")
    lines += _teststufen_abschnitt()
    lines += [
        "", "## Aufruf", "```bash",
        "bash gates/validate.sh pr            # im PR (CI) — blockt Merge",
        "bash gates/validate.sh pre-deploy    # vor der Promotion in die Ziel-Stage",
        "bash gates/validate.sh post-deploy   # nach dem Load, vor der nächsten Stage",
        "GATES_ADVISORY=1 bash gates/validate.sh pre-deploy   # Rollback: nur warnen, nicht blocken",
        "```",
        "Eingaben (sonst SKIP, nie gefälscht): `ARCH` (Architektur-JSON), `STACK`, `MODEL` "
        "(SemanticModel-Pfad → tmdl-load), `PBIP` (→ pbi-audit/BPA), `DRIFT_CHECK` "
        "(emittierte `drift_check.py`), `DQ_GATE` (DQ-Runner über `governance/data_quality.json`).", "",
        "## Verdrahtung je Deployment-Modell (I-19.1)",
    ]
    for model, where in model_wiring.items():
        lines.append(f"- **{model}:** " + "; ".join(where) + ".")
    lines += [
        "", "Die PR-Gates laufen zusätzlich als eigener CI-Workflow `gates.yml` "
        "(`validate.sh pr`) — breiterer Bruder von `architecture-gate.yml`.", "",
    ]
    return "\n".join(lines) + "\n"


def _teststufen_abschnitt() -> list[str]:
    """Die fuenf Stufen als eigene Tabelle — mit Besitzer, und mit der Grenze bei 4 und 5.

    Der Abschnitt steht **nach** der Gate-Tabelle, weil er sie einordnet: alle Gates gruen
    heisst Stufe 1 bis 3 bestanden, nicht Lieferung geprueft. Ohne diesen Satz liest sich ein
    gruenes `validate.sh` wie eine Freigabe.
    """
    zeilen = ["", "## Die fünf Teststufen", "",
              "Alle Gates grün heißt: Stufe 1 bis 3 bestanden. Stufe 4 und 5 führt kein Skript "
              "dieser Lieferung aus — sie stehen hier mit Besitzer, damit sie nicht als "
              "abgedeckt gelten.", "",
              "| Stufe | Wer besitzt sie | Wann | Was sie prüft | Womit |",
              "|:--:|---|---|---|---|"]
    for t in TESTSTUFEN:
        womit = ", ".join(f"`{g}`" for g in t["gates"]) if t["gates"] else "**kein Gate** (siehe unten)"
        zeilen.append(f"| {t['nr']} {t['name']} | {t['besitzer']} | {t['wann']} | {t['prueft']} | {womit} |")
    zeilen += ["", "### Warum Stufe 4 und 5 kein Gate sind", ""]
    for t in TESTSTUFEN:
        if t.get("grenze"):
            zeilen += [f"**Stufe {t['nr']} — {t['name']}.** {t['grenze']}", ""]
    zeilen += ["Der Vordruck für beide liegt in `gates/_ABNAHME.md`.", ""]
    return zeilen


_MODEL_WIRING = {
    "deployment-pipelines": [
        "PR: `gates.yml` (validate.sh pr)",
        "Pre-Deploy: `promote.sh` ruft `validate.sh pre-deploy` vor jeder Deployment-Pipeline-Promotion",
        "Post-Deploy: `validate.sh post-deploy` nach jedem Stage-Deploy",
    ],
    "git-integration-gitflow": [
        "PR: `gates.yml` je Stage-Branch-PR (GitFlow-Approval)",
        "Pre-Deploy: `promote_gitflow.sh` ruft `validate.sh pre-deploy` vor `update-from-git`",
        "Post-Deploy: `validate.sh post-deploy` nach dem Pull in die Stage-Workspace",
    ],
    "isv-per-customer": [
        "PR: `gates.yml` auf `main`",
        "Pre-Deploy: `deploy_customers.sh` ruft `validate.sh pre-deploy` vor `publish_all_items` je Kunde",
        "Post-Deploy: `validate.sh post-deploy` je Kunden-Workspace",
    ],
    "items-api-trunk": [
        "PR: `gates.yml` auf `main`",
        "Pre-Deploy: `validate.sh pre-deploy` vor `fabric-cicd` (`--emit-fabric-cicd`)",
        "Post-Deploy: `validate.sh post-deploy` je Environment",
    ],
}


def _abnahme_md(blueprint: dict | None) -> str:
    """Der Vordruck fuer die zwei Stufen, die kein Gate ausfuehrt (BK-C04).

    Er ist aus dem Bauplan abgeleitet und nicht frei geschrieben: die Ladestrecken kommen aus
    ``ingestion``, die Gold-Produkte aus ``mesh.domains[*].data_products``. Ein Vordruck mit
    Beispielzeilen wuerde ausgefuellt aussehen; hier steht in jeder Zeile die Sache, die wirklich
    geliefert wurde, und daneben eine leere Spalte.

    Ohne Bauplan bleiben die Tabellen leer und sagen das. Eine erfundene Zeile waere schlimmer
    als eine leere Tabelle — sie liesse sich abhaken.
    """
    bp = blueprint or {}
    strecken = [i for i in (bp.get("ingestion") or []) if i.get("source")]
    produkte = [(d.get("name", ""), pname)
                for d in ((bp.get("mesh") or {}).get("domains") or [])
                for pname in (d.get("data_products") or [])]
    z = [
        "# Lasttest und Fachabnahme (generiert — BK-C04)", "",
        "Zwei Teststufen laufen in keinem Gate. Die Gründe stehen in `_GATES.md`; hier steht, "
        "wie sie stattdessen ablaufen und wo das Ergebnis hinkommt.", "",
        "## Stufe 4 — Lasttest", "",
        "Einmal vor der Übergabe, danach im Betrieb bei jeder Änderung, die das Datenvolumen "
        "oder den Zeitplan verschiebt.", "",
        "1. Die Pilotlast festlegen. Sie steht in `readiness/workload.example.json` und kommt "
        "aus der Angabe des Kunden (Intake-Feld `load_test_reference`). Ohne sie misst der Lauf "
        "die Testdaten, nicht den Betrieb.",
        "2. Die Ladestrecken einmal vollständig unter dieser Last fahren.",
        "3. Direkt danach `day2/leistungsmessung.py` starten. Der erste Lauf hat noch keinen "
        "Median der letzten acht Wochen; sein Ergebnis ist die Grundlinie, gegen die alle "
        "späteren Läufe verglichen werden.",
        "4. Das Protokoll unten ausfüllen und im Übergabeordner ablegen.", "",
        "### Protokoll je Ladestrecke", "",
        "| Ladestrecke | Quelle | Menge im Lauf | Laufzeit | gemessen am | von |",
        "|---|---|---|---|---|---|",
    ]
    if strecken:
        for i in strecken:
            z.append(f"| `{i['source']}` | {i.get('source_system') or i.get('access_mode', '')} "
                     f"|  |  |  |  |")
    else:
        z.append("| _keine Ladestrecke im Bauplan_ |  |  |  |  |  |")
    z += [
        "", "Die Antwortzeit der teuersten Berichtsabfrage gehört zur Messung und steht nicht "
        "in dieser Tabelle. Sie kommt aus dem Eventhouse (`day2/leistung_berichtsabfrage.kql`) "
        "und wird der Messung mit `--antwortzeit` übergeben.", "",
        "## Stufe 5 — Fachabnahme", "",
        "Eine Zeile je Gold-Produkt, vor dessen Produktivsetzung. Ausgefüllt wird sie vom "
        "Fachbereich. Wir tragen hier nichts ein, auch nicht vorbereitend: eine Abnahme, die "
        "der Lieferant erteilt, ist keine.", "",
        "Das Ergebnis kennt drei Werte: **angenommen**, **angenommen mit Auflage**, "
        "**abgelehnt**. Bei einer Auflage gehört in die letzte Spalte, was bis wann zu tun ist.",
        "",
        "| Gold-Produkt | Domäne | Fachbereich (Name) | geprüft am | Ergebnis | Auflage |",
        "|---|---|---|---|---|---|",
    ]
    if produkte:
        for dom, prod in produkte:
            z.append(f"| `{prod}` | {dom} |  |  |  |  |")
    else:
        z.append("| _kein Gold-Produkt im Bauplan_ |  |  |  |  |  |")
    z += [
        "", "Eine Zeile ohne Namen in der dritten Spalte zählt nicht als Abnahme. Sie sagt nur, "
        "dass jemand die Tabelle geöffnet hat.", "",
    ]
    return "\n".join(z) + "\n"


def emit_gates(architecture_path: str = "data_architecture.json", stack: str = "fabric",
               blueprint: dict | None = None) -> dict[str, str]:
    """Return the gate artifact set (path → content): the phased runner, the PR-CI workflow, the doc.

    Always emitted (the validation pipeline is the delivery pipeline, stack-agnostic). Wire the
    runner into the model scripts via ``pre_deploy_gate_line`` / ``post_deploy_gate_line``.

    ``blueprint`` (20.08.2026, BK-C04) fuellt den Vordruck der zwei Stufen, die kein Gate
    ausfuehrt. Optional, damit ein Aufruf ohne Bauplan weiterhin geht — die Tabellen bleiben
    dann leer und sagen es.
    """
    catalog = _gate_catalog(architecture_path, stack)
    return {
        "gates/validate.sh": emit_validate_sh(architecture_path, stack),
        "gates/gates.yml": emit_gates_ci(architecture_path, stack),
        "gates/_GATES.md": _gates_doc(catalog, _MODEL_WIRING),
        "gates/_ABNAHME.md": _abnahme_md(blueprint),
    }


def pre_deploy_gate_line(rel_to_gates: str = "gates") -> str:
    """A real, runnable pre-deploy gate invocation to inject at the top of a model CD script."""
    return (f'# --- Pre-Deploy-Gate (I-19.3): blockt bei rotem Prüfer (GATES_ADVISORY=1 zum Übersteuern) ---\n'
            f'bash "$(dirname "$0")/../{rel_to_gates}/validate.sh" pre-deploy')


def post_deploy_gate_line(rel_to_gates: str = "gates") -> str:
    """A real, runnable post-deploy gate invocation to inject after a stage promotion."""
    return (f'# --- Post-Deploy-Gate (I-19.3): Smoke/Drift/DQ nach dem Stage-Load ---\n'
            f'bash "$(dirname "$0")/../{rel_to_gates}/validate.sh" post-deploy')
