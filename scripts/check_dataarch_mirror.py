#!/usr/bin/env python3
"""Dataarch contract-surface mirror-drift sensor (ADR-0051 / I-20 · Tier-3 #8).

ALUCA mirrors Meridian's neutral-IR **contract surface** (concept/gov registries + ODCS) by hand —
`dataarch_engine` is NOT vendored, so unlike the pbi_engine mirror there is no vendored-file hash to
diff. This sensor closes that gap: when a Meridian checkout is reachable it compares the **public
contract** of both sides and reports drift, so a Meridian-side change can no longer silently desync
ALUCA's mirror.

DOCTRINE (same as `check_superversion_pins.py`): **reports drift, never bumps.** Advisory (exit 0) by
default; `--strict` turns drift into an error (exit 1) for a release gate. Meridian unreachable →
soft-skip (exit 0) — the sibling checkout is a dev convenience, not a CI guarantee.

Compared contract (the mirror's guarantees):
  * architecture: DEFAULT_CONCEPT + the registered concept ids;
  * governance: DEFAULT_GOVERNANCE_CONCEPT + concept ids + each id's contract_standard;
  * ODCS: ODCS_API_VERSION + the public API function names.

**Freshness of the counterpart checkout (D-341, 2026-08-27).** Two defects made this sensor
blind to the very window it guards. Measured on 2026-08-27:

* ``MERIDIAN_ROOT=/nonexistent … --strict`` exited **0** — the release gate passed although the
  cross-repo comparison never ran. Same class as ``tabular-bpa.yml`` (CLAUDE.md, 18.08.): a gate
  that cannot tell "found nothing" from "did not run" scores both as success. An unreachable
  checkout is therefore a **hard failure** under ``--strict``; without it, it stays a named skip.
* A sensor compares against a working tree, not against ``origin``. If that tree is stale, both
  sides look in sync because both are old — the ``platform.sizing`` incident (07./08.08.2026)
  happened inside that window. ``checkout_freshness()`` measures HEAD, distance behind the
  upstream ref, a dirty tree and the age of ``.git/FETCH_HEAD``; the success line now carries
  that provenance instead of claiming parity unqualified.

**The sensor never fetches on its own** — no network in ``make check``, same doctrine as "reports
drift, never bumps". ``--fetch`` makes fetching an explicit act, just as ``--write`` does mirroring.

**Theme mirror (29.09.2026).** A second vendored set under ``products/fabric/powerbi/themes/``:
the theme JSONs Freelancing's canonical engine ``products/pbi_theme`` generates, byte-identical
with their own PIN (replaces the uninitialized ``powerbi-theme`` submodule, ADR-0005). Same
three outcomes; re-mirror explicitly with ``--write-themes`` (from a commit, like ``--write``).

Meridian root resolution: ``$MERIDIAN_ROOT`` env, else the sibling ``../Freelancing`` of this repo.
Modules are loaded **by path** (concepts/governance are self-contained) or **read as source** (odcs
imports a sibling), never via ``import core`` — ALUCA owns its own ``core`` package.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_MER_REL = "core/dataarch_engine/blueprint"
_ALU_REL = "tooling/superversion"
_ODCS_PUBLIC = ("to_odcs", "emit_odcs", "to_odcs_ingestion", "emit_odcs_ingestion",
                "from_odcs", "import_sql_table", "odcs_to_catalog", "validate_odcs")
# The column-contract half (A-20/A-23, Meridian D-581, mirrored 29.09.2026): private in both
# repos, but it is the mapping `column_specs ⇄ ODCS v3.1 property`. A function added or dropped on
# one side only means the round-trip means different things here and there.
_ODCS_COLUMN_SPECS = ("_quality_rule", "_spec_to_property", "_property_to_spec",
                      "_table_properties", "_catalog_table_for")

# Zweite, stärkere Hälfte des Sensors (SHARED_SUBSTANCE.md Klasse A): die offiziell
# belegten Emitter werden nicht per Hand nachgezogen, sondern **byte-identisch**
# gespiegelt. Dafür genügt kein Vertragsflächen-Vergleich — hier wird Datei-sha256
# gediffed, gegen Meridian *und* gegen das lokale PIN.
_VENDOR_REL = "tooling/superversion/vendor/meridian_dataarch"

# **Was** gespiegelt wird, steht hier — nicht im PIN. Das PIN ist das *abgeleitete*
# Integritäts-Manifest (Hashes), diese Liste ist die Entscheidung. Andersherum wäre die
# Aufnahme eines neuen Moduls unmöglich: sie verlangte eine PIN-Änderung, und eine
# PIN-Änderung von Hand ist genau der Doktrin-Bruch, den das Integritäts-Gate abfängt.
# Form wie Meridians `MIRRORED_FILES` im Gegenstück-Sensor, um ein Paar erweitert: ein
# blosser Name ist blueprint-relativ, ein `(Quellpfad, Zielname)`-Paar nennt seinen Ort
# selbst (`mirror_quellen()`).
MIRRORED_FILES = (
    "admin_settings.py",
    "capacity_recommend.py",
    "decision_proposals.py",
    # Form eines Fabric-Item-Zeitplans + die Job-Typen als Pfadsegment (20.08.2026). Aufgenommen,
    # weil `provision_monitoring` den Zeitplan des Aktivitaetsprotokoll-Exports daraus baut: ein
    # gespiegeltes Modul, das ein nicht gespiegeltes importiert, bricht hier beim ersten Aufruf.
    "fabric_schedule.py",
    "naming.py",
    "provision_connectivity.py",
    "provision_governance.py",
    "provision_lifecycle.py",
    "provision_monitoring.py",
    "provision_operability.py",
    "provision_source_schema.py",
    "source_schema.py",
    # Fähigkeits-Wissen je Stack (SL-2607-3 Befund 2): welcher offizielle Mechanismus, welche
    # Editions-/Plan-Stufe, welche offene Entscheidung. Klasse-A-Substanz — belegt aus der
    # Herstellerdokumentation, also geteilt statt zweimal gepflegt. Bewusst abhängigkeitsarm
    # gehalten (nur typing), damit das Spiegeln nichts mitschleppt.
    "stack_capabilities.py",

    # -- Die Vollzugshälfte (26.08.2026) ------------------------------------------------
    #
    # Bis hierhin spiegelte ALUCA fünf Betriebs-Belange und emittierte im Übrigen nur die
    # Topologie. Gemessen an derselben Fixture: 39 Artefakte hier gegen die vollständige
    # Kette drüben. Der Unterschied ist nicht Geschmack, sondern genau die Substanz, die
    # SHARED_SUBSTANCE.md Klasse A nennt — `fab`-Skripte, fabric-cicd-Konfigurationen,
    # Terraform gegen den microsoft/fabric-Provider, Variable Libraries, Copy-Jobs,
    # Notebooks, Pipelines, TMDL-Kulturdateien, DAB-Bundles, MetricFlow. Jede dieser
    # Formen ist von einem Hersteller festgelegt; eine zweite Fassung davon wäre in
    # beiden Repos gleich falsch.
    #
    # Die Menge ist **gemessen, nicht gegriffen**: transitive Hülle über die Importe der
    # Kandidaten, aufgelöst gegen `core.dataarch_engine.blueprint`. Sie schließt ohne
    # einen einzigen Import außerhalb des Pakets und ohne Meridians eigenen Deriver
    # (`blueprint.py`) — den zu spiegeln hieße, ALUCA einen zweiten Deriver neben
    # `architecture_blueprint.py` zu geben, also genau das Doppel-Silo, gegen das die
    # Doktrin geschrieben ist.
    "direct_lake_guardrails.py",
    # External Data Share per REST. Am 04.09.2026 wieder entfernt, weil Meridians `main` das
    # Modul nicht fuehrte (Klasse-A-Datei ohne Heimat). Seit dem Merge von Meridian #425
    # (24.09.2026, WIP-Zweig 2026-09-03) liegt es dort, und `provision_governance.py` importiert
    # es in `emit_sharing`. Ohne diesen Eintrag braeche der gespiegelte Import beim ersten Aufruf.
    "provision_external_sharing.py",
    # Gezogen von `provision_apply` wegen `LIFECYCLE_STAGES`. Byte-identisch gespiegelt
    # statt die drei Stufen hier nachzutippen: eine Kopie, die „nur eine Konstante" teilt,
    # driftet als nächstes im Inhalt.
    "governance_strategy.py",
    "provision_apply.py",
    "provision_chargeback.py",
    "provision_cicd.py",
    "provision_databricks_cicd.py",
    "provision_dq.py",
    "provision_fabric.py",
    "provision_fabric_cicd.py",
    "provision_gates.py",
    "provision_ingestion.py",
    "provision_lineage.py",
    "provision_metricflow.py",
    "provision_notebooks.py",
    "provision_orchestration.py",
    "provision_prereq.py",
    "provision_terraform.py",
    "provision_transforms.py",
    "provision_translations.py",
    "provision_varlib.py",
    # Prüft die emittierte DDL im Zieldialekt. `sqlglot` ist hier **nicht** installiert;
    # das Modul macht ohne die Abhängigkeit einen ausgewiesenen Soft-Skip, prüft dann also
    # nur die eigenen Regeln. Mitgespiegelt, damit die Zusage identisch ist, sobald die
    # Abhängigkeit da ist — nicht, damit sie hier heute etwas beweist.
    "sql_validate.py",

    # -- Der Preis-Rechenkern (03.09.2026, ADR-0019 N-3) ---------------------------------
    #
    # **Abweichung zu ADR-0019 §2.4/§5 N-3, benannt statt geglaettet (Belegpflicht R5).**
    # Das ADR nennt `staffing.py` als den zu spiegelnden Rechenkern. Meridians Umsetzung
    # (D-2) hat den Kern woanders abgelegt, und das ist gemessen, nicht vermutet: der Weg,
    # den `write_vendor` faehrt — Datei kopieren, unter Meridians Modulnamen laden —
    # endet bei `products/sales_proposal/staffing.py` mit
    # `ImportError: cannot import name 'preis_kanon' from 'core'`, bei
    # `core/preis_kanon.py` dagegen sauber. `staffing.py` ist die Engagement-Schicht und
    # zieht `core.preis_kanon` sowie `products.governance_framework.delivery` nach; beide
    # Pakete gibt es hier nicht, und der Spiegel schreibt Importe nicht um (das waere das
    # Ende der Byte-Identitaet). Meridian sagt es in derselben Datei selbst:
    # „gespiegelt nach ALUCA wird der Kern (F-3), diese Schicht bleibt das Angebotsprodukt
    # dieses Repos."
    #
    # Die Entscheidung aus §2.4 bleibt damit unangetastet — ein Rechenkern, nicht zwei.
    # Nur die Datei heisst anders. Der Kern ist mandantenunabhaengig: `kostensatz(m, k)`,
    # `selbstkosten`, `preis_kalkuliert`, `festpreis`, `lieferzeit_band` nehmen den
    # Mandanten als Parameter, und `satzklassen` traegt hier Rolle × Standort statt einer
    # Person (ADR-0019 §2.2).
    ("core/preis_kanon.py", "preis_kanon.py"),
)


def mirror_quellen() -> tuple[tuple[str, str], ...]:
    """Je Eintrag: (Quellpfad relativ zur Meridian-Wurzel, Zielname im flachen Spiegel).

    Ein blosser Dateiname bleibt blueprint-relativ — so stand die Liste bis zum 03.09.2026
    und so bleibt sie fuer 33 der 34 Dateien lesbar. Ein Paar nennt seinen Quellpfad selbst;
    ohne das koennte der Spiegel nur aus **einem** Meridian-Verzeichnis lesen, und der
    Preis-Rechenkern liegt in `core/`.
    """
    out: list[tuple[str, str]] = []
    for eintrag in MIRRORED_FILES:
        if isinstance(eintrag, tuple):
            out.append(eintrag)
        else:
            out.append((f"{_MER_REL}/{eintrag}", eintrag))
    return tuple(out)


def _meridian_root() -> Path | None:
    env = os.environ.get("MERIDIAN_ROOT")
    if env:
        p = Path(env).expanduser()
        return p if (p / _MER_REL / "concepts.py").is_file() else None
    sibling = REPO_ROOT.parent / "Freelancing"
    return sibling if (sibling / _MER_REL / "concepts.py").is_file() else None


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sql_type_map(text: str) -> list[list[str]]:
    """The `_SQL_TYPE_TO_LOGICAL` pairs as (pattern, logical). Pure, source-text only.

    Part of the compared contract because ALUCA does not vendor a second `odcs.py`: the
    import bridge hands the mirrored `source_schema` ALUCA's own ODCS writer, so the two
    `_logical_type` tables must agree or the mirrored emitter would classify a customer's
    column types differently here than in Meridian — silently, and only for introspected
    sources. Name-level comparison would not catch that.
    """
    block = re.search(r"_SQL_TYPE_TO_LOGICAL\s*=\s*\[(.*?)\n\]", text, re.S)
    if not block:
        return []
    return [[pattern, logical] for pattern, logical
            in re.findall(r're\.compile\(r"([^"]+)"[^)]*\),\s*"([^"]+)"', block.group(1))]


def _odcs_facts(source: Path) -> dict:
    text = source.read_text(encoding="utf-8")
    version = re.search(r'ODCS_API_VERSION\s*=\s*"([^"]+)"', text)
    columns = re.search(r'ODCS_API_VERSION_SPALTEN\s*=\s*"([^"]+)"', text)
    defs = set(re.findall(r'^def (\w+)\(', text, re.M))
    return {"api_version": version.group(1) if version else None,
            "api_version_columns": columns.group(1) if columns else None,
            "public_api": sorted(d for d in defs if d in _ODCS_PUBLIC),
            "column_specs_api": sorted(d for d in defs if d in _ODCS_COLUMN_SPECS),
            "sql_type_map": sql_type_map(text)}


def _extract(concepts_py: Path, gov_py: Path, odcs_py: Path, tag: str) -> dict:
    c = _load(f"_{tag}_concepts", concepts_py)
    g = _load(f"_{tag}_gov", gov_py)
    gov_standards = {i: g.get_governance_concept(i).profile().get("contract_standard")
                     for i in g.available_governance_concepts()}
    return {
        "arch_default": c.DEFAULT_CONCEPT,
        "arch_concepts": sorted(c.available_concepts()),
        "gov_default": g.DEFAULT_GOVERNANCE_CONCEPT,
        "gov_concepts": sorted(g.available_governance_concepts()),
        "gov_standards": gov_standards,
        "odcs": _odcs_facts(odcs_py),
    }


_CONTRACT_KEYS = ("arch_default", "arch_concepts", "gov_default", "gov_concepts", "gov_standards", "odcs")


def _diff(meridian: dict, aluca: dict) -> list[str]:
    """Return one line per drifted contract field (empty = in sync). Pure, unit-testable."""
    return [f"  {k}: Meridian={meridian.get(k)!r}  vs  ALUCA={aluca.get(k)!r}"
            for k in _CONTRACT_KEYS if meridian.get(k) != aluca.get(k)]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def vendor_pin() -> dict | None:
    """The vendored subtree's PIN manifest, or None when nothing is vendored yet."""
    pin = REPO_ROOT / _VENDOR_REL / "PIN.json"
    return json.loads(pin.read_text(encoding="utf-8")) if pin.is_file() else None


def vendor_integrity(pin: dict, vendor_rel: str = _VENDOR_REL) -> list[str]:
    """Local edits inside the byte-identical mirror. Pure; runs without Meridian."""
    root = REPO_ROOT / vendor_rel
    out: list[str] = []
    for entry in pin.get("files", []):
        f = root / entry["path"]
        if not f.is_file():
            out.append(f"  {entry['path']}: missing from the mirror")
            continue
        got = _sha256(f)
        if got != entry["sha256"]:
            out.append(f"  {entry['path']}: edited locally "
                       f"(sha256 {got[:12]}… != pinned {entry['sha256'][:12]}…)")
    return out


def _quelle_bytes(meridian_root: Path, quelle: str, ref: str | None = None) -> bytes | None:
    """Inhalt einer Spiegelquelle: ohne ``ref`` aus dem Arbeitsbaum, mit ``ref`` aus dem Commit.

    Warum der Commit (25.09.2026, Meridian D-567): der Arbeitsbaum ist nicht der Stand, den
    jemand beschlossen hat. Gemessen am 24.09.2026: 24 Quellen trugen auf einem Windows-Rechner
    CRLF auf der Platte und LF im Index; ``--write`` pinnte die CRLF-Hashes, ``main`` die
    LF-Hashes — derselbe Inhalt, zwei PINs. ``git show <ref>:<pfad>`` liefert den Blob, wie er
    im Repository steht, unabhaengig von Zeilenenden und uncommitteter Arbeit.
    """
    if ref is None:
        p = meridian_root / quelle
        return p.read_bytes() if p.is_file() else None
    try:
        proc = subprocess.run(("git", "show", f"{ref}:{quelle}"), cwd=str(meridian_root),
                              capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout if proc.returncode == 0 else None


def vendor_upstream_drift(pin: dict, meridian_root: Path, ref: str | None = None) -> list[str]:
    """Meridian-side changes the mirror has not picked up yet. Pure.

    Takes the Meridian **repo root**, not the blueprint directory: since 03.09.2026 the
    mirror reads from two directories (see ``mirror_quellen``), so one fixed source dir is
    no longer enough to resolve an entry.
    """
    pinned = {e["path"]: e["sha256"] for e in pin.get("files", [])}
    ziele = [z for _, z in mirror_quellen()]
    out: list[str] = []
    for quelle, name in mirror_quellen():
        inhalt = _quelle_bytes(meridian_root, quelle, ref)
        if inhalt is None:
            if name in pinned:
                out.append(f"  {name}: removed in Meridian, still mirrored here")
            else:
                out.append(f"  {name}: declared as mirrored but absent in Meridian")
            continue
        if name not in pinned:
            out.append(f"  {name}: declared as mirrored but not mirrored yet — --write")
            continue
        if hashlib.sha256(inhalt).hexdigest() != pinned[name]:
            out.append(f"  {name}: " + pin_direction(meridian_root, quelle,
                                                     REPO_ROOT / _VENDOR_REL / name))
    for name in sorted(set(pinned) - set(ziele)):
        out.append(f"  {name}: mirrored but no longer declared in MIRRORED_FILES")
    # Meridian deklariert dieselbe Menge (`aluca_spiegelmenge.json`, Meridian D-545) und prueft
    # dort, dass jedes gespiegelte Modul nur Gespiegeltes importiert. Die Pruefung traegt nur,
    # wenn beide Listen gleich sind — sonst prueft Meridian eine Menge, die hier niemand spiegelt.
    # Merge mit main (24.09.2026): die Funktion nimmt seit main die Repo-Wurzel, und
    # MIRRORED_FILES fuehrt auch Paare (Quellpfad, Zielname) - verglichen werden die Zielnamen.
    menge = meridian_root / "core" / "dataarch_engine" / "blueprint" / "aluca_spiegelmenge.json"
    if menge.is_file():
        _m = json.loads(menge.read_text(encoding="utf-8"))
        # Meridian D-562: Paare (Dateien ausserhalb des Blueprints, etwa preis_kanon) zaehlen mit.
        deklariert = set(_m.get("dateien") or []) | set(_m.get("paare") or {})
        for name in sorted(set(ziele) - deklariert):
            out.append(f"  {name}: hier gespiegelt, in Meridians aluca_spiegelmenge.json nicht deklariert")
        for name in sorted(deklariert - set(ziele)):
            out.append(f"  {name}: in Meridians aluca_spiegelmenge.json deklariert, hier nicht gespiegelt")
    return out


NICHT_SCHREIBEN = "do NOT --write"


def _git_blob_id(path: Path) -> str:
    """The id git gives this content (``git hash-object``), computed without calling git."""
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def pin_direction(meridian_root: Path, quelle: str, vendored: Path) -> str:
    """Which side moved, measured in Meridian's history instead of assumed.

    "Meridian differs from the PIN" has two opposite causes, and the old advice fitted only one.
    Measured 24.09.2026: ALUCA mirrored ``governance_strategy.py`` with
    ``workspace_layer_labels`` on 09.09. from a Meridian working tree whose change later lived only
    on ``wip/2026-09-03-dataarch-delivery``, never on ``main``. The sensor said "Meridian moved on —
    re-mirror (--write)"; the write would have deleted the feature here. A STALE signal says the
    two sides differ, never which one is right (CLAUDE.md, 15.08.2026).

    Reads local git only (no network). The pinned blob in HEAD's history of that file means HEAD
    moved past it; only on other refs means HEAD is behind the mirror; nowhere means this
    checkout never saw it.
    """
    if not vendored.is_file():
        return "Meridian differs from the PIN; the mirrored copy is missing — --write"
    blob = _git_blob_id(vendored)
    auf_head = _git(meridian_root, "log", "HEAD", "--format=%h", f"--find-object={blob}", "--", quelle)
    if auf_head is None:
        return "Meridian differs from the PIN; direction not measurable (no git history) — --write only after reading the diff"
    if auf_head:
        return "Meridian moved on — re-mirror (--write)"
    sonst = _git(meridian_root, "log", "--all", "--reverse", "--format=%h", f"--find-object={blob}", "--", quelle)
    if sonst:
        refs = _git(meridian_root, "branch", "-a", "--format=%(refname:short)", "--contains", sonst.split()[0]) or ""
        wo = ", ".join(sorted(r for r in refs.split() if r and not r.endswith("/HEAD"))[:3]) or "an unnamed ref"
        return (f"Meridian HEAD is BEHIND the mirror — the pinned state exists only on {wo} "
                f"({NICHT_SCHREIBEN}: it would drop that change here; land it in Meridian first)")
    return (f"the pinned state is unknown to this Meridian checkout (uncommitted there, or never "
            f"fetched) — {NICHT_SCHREIBEN} before `--fetch` and a second measurement")


def write_vendor(meridian_root: Path, pin: dict | None = None, ref: str = "HEAD") -> dict:
    """Re-copy the mirrored files and rewrite PIN.json. Deliberately manual, never in CI.

    Seit Meridian D-567 aus dem Commit ``ref`` (Vorgabe HEAD), nicht aus dem Arbeitsbaum; der
    PIN nennt den Commit (``source_commit``). Uncommittete Arbeit in Meridian wird damit nicht
    mehr still gespiegelt — erst committen, dann spiegeln.

    The file list comes from ``MIRRORED_FILES``, never from the existing PIN — otherwise a
    module could only ever be *added* by hand-editing the PIN, which the integrity gate
    (rightly) treats as a doctrine breach.
    """
    root = REPO_ROOT / _VENDOR_REL
    root.mkdir(parents=True, exist_ok=True)
    pin = pin or {}
    quellen = mirror_quellen()
    commit = _git(meridian_root, "rev-parse", ref)
    if not commit:
        raise SystemExit(f"[check-dataarch-mirror] --write: {ref} ist in {meridian_root} kein Commit")
    fehlend = []
    for quelle, name in quellen:
        inhalt = _quelle_bytes(meridian_root, quelle, commit)
        if inhalt is None:
            fehlend.append(quelle)
            continue
        (root / name).write_bytes(inhalt)
    if fehlend:
        raise SystemExit("[check-dataarch-mirror] --write: nicht im Commit " + commit[:8]
                         + " (uncommittet?): " + ", ".join(fehlend))

    def _eintrag(quelle: str, name: str) -> dict:
        e = {"path": name, "sha256": _sha256(root / name)}
        # `source` steht nur dort, wo die Datei **nicht** aus `source_path` kommt. So bleibt
        # der Vorgabepfad oben eine echte Aussage und der PIN-Diff auf die Ausnahme begrenzt.
        if quelle != f"{_MER_REL}/{name}":
            e["source"] = quelle
        return e

    fresh = {
        "source_repo": pin.get("source_repo", "Freelancing"),
        "source_path": pin.get("source_path", _MER_REL),
        "source_commit": commit,
        "doctrine": pin.get("doctrine",
                            "SHARED_SUBSTANCE.md class A — home is Meridian, ALUCA mirrors."),
        "files": [_eintrag(q, n) for q, n in quellen],
    }
    (root / "PIN.json").write_text(json.dumps(fresh, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8", newline="\n")
    return fresh


# ------------------------------------------------------ Theme-Spiegel (29.09.2026)
# Zweiter vendorter Satz, gleiche Doktrin: Freelancings `products/pbi_theme` ist die eine
# kanonische Theme-Engine; ALUCA konsumiert ihre **Ausgabe** — werkzeugfreie Theme-JSONs —
# byte-identisch, mit PIN (sha256 je Datei) statt Git-Submodul (ADR-0005: vendor + PIN).
# Bis 29.09.2026 hing hier `powerbi-theme` als nie initialisiertes Submodul, in das ALUCA-Code
# zudem schrieb. Freelancing prüft seinerseits, dass seine eingecheckten Themes genau die
# Engine-Ausgabe sind (`products/pbi_theme/tests/test_regeneration.py`); dieser Sensor schließt
# die Kette bis hierher.
#
# **Die Menge ist eine Regel, kein Verzeichnis im PIN:** jede `*.json` unter
# `_THEME_SRC_REL` außer `manifest.json`. Die Doku (`*.md`) und die Manifeste bleiben drüben,
# ALUCA-Code liest nur Theme-JSONs.
_THEME_SRC_REL = "products/pbi_theme/themes"
_THEME_VENDOR_REL = "products/fabric/powerbi/themes"


def _ist_theme_json(rel: str) -> bool:
    return rel.endswith(".json") and not rel.endswith("/manifest.json") and rel != "manifest.json"


def theme_quellen(meridian_root: Path, ref: str | None = None) -> list[str] | None:
    """Die gespiegelte Theme-Menge, relativ zu ``_THEME_SRC_REL``. None = nicht messbar.

    Mit ``ref`` aus dem Commit (``git ls-tree``), sonst aus dem Arbeitsbaum — dieselbe
    Unterscheidung wie ``_quelle_bytes``.
    """
    if ref is None:
        src = meridian_root / _THEME_SRC_REL
        if not src.is_dir():
            return []
        return sorted(p.relative_to(src).as_posix() for p in src.rglob("*.json")
                      if _ist_theme_json(p.relative_to(src).as_posix()))
    out = _git(meridian_root, "ls-tree", "-r", "--name-only", ref, "--", _THEME_SRC_REL)
    if out is None:
        return None
    prefix = _THEME_SRC_REL + "/"
    return sorted(ln[len(prefix):] for ln in out.splitlines()
                  if ln.startswith(prefix) and _ist_theme_json(ln[len(prefix):]))


def theme_pin() -> dict | None:
    pin = REPO_ROOT / _THEME_VENDOR_REL / "PIN.json"
    return json.loads(pin.read_text(encoding="utf-8")) if pin.is_file() else None


def theme_upstream_drift(pin: dict, meridian_root: Path, ref: str | None = None) -> list[str]:
    """Freelancing-seitige Theme-Änderungen, die der Spiegel noch nicht hat. Pure."""
    namen = theme_quellen(meridian_root, ref)
    if namen is None:
        return [f"  themes: {ref} in {meridian_root} nicht lesbar — Theme-Spiegel NICHT verglichen"]
    if not namen:
        return [f"  themes: {_THEME_SRC_REL} fehlt in Freelancing ({ref or 'Arbeitsbaum'}) — "
                f"Engine-Ausgabe nicht vorhanden, Theme-Spiegel NICHT verglichen"]
    pinned = {e["path"]: e["sha256"] for e in pin.get("files", [])}
    out: list[str] = []
    for name in namen:
        quelle = f"{_THEME_SRC_REL}/{name}"
        inhalt = _quelle_bytes(meridian_root, quelle, ref)
        if inhalt is None:
            out.append(f"  themes/{name}: nicht lesbar in Freelancing")
        elif name not in pinned:
            out.append(f"  themes/{name}: neu in der Engine-Ausgabe, hier nicht gespiegelt — --write-themes")
        elif hashlib.sha256(inhalt).hexdigest() != pinned[name]:
            out.append(f"  themes/{name}: " + pin_direction(
                meridian_root, quelle, REPO_ROOT / _THEME_VENDOR_REL / name))
    for name in sorted(set(pinned) - set(namen)):
        out.append(f"  themes/{name}: in Freelancing entfernt, hier noch gespiegelt — --write-themes")
    return out


def write_theme_vendor(meridian_root: Path, ref: str = "HEAD") -> dict:
    """Theme-Spiegel aus dem Commit ``ref`` neu schreiben (manuell, nie in CI).

    Der Zielordner gehört ganz dem Spiegel: was nicht mehr in der Menge ist, wird entfernt.
    """
    commit = _git(meridian_root, "rev-parse", ref)
    if not commit:
        raise SystemExit(f"[check-dataarch-mirror] --write-themes: {ref} ist in {meridian_root} kein Commit")
    namen = theme_quellen(meridian_root, commit)
    if not namen:
        raise SystemExit(f"[check-dataarch-mirror] --write-themes: keine Theme-JSONs unter "
                         f"{_THEME_SRC_REL} im Commit {commit[:8]}")
    root = REPO_ROOT / _THEME_VENDOR_REL
    root.mkdir(parents=True, exist_ok=True)
    for alt in root.rglob("*.json"):
        if alt.name != "PIN.json":
            alt.unlink()
    files = []
    for name in namen:
        inhalt = _quelle_bytes(meridian_root, f"{_THEME_SRC_REL}/{name}", commit)
        if inhalt is None:
            raise SystemExit(f"[check-dataarch-mirror] --write-themes: {name} nicht im Commit {commit[:8]}")
        ziel = root / name
        ziel.parent.mkdir(parents=True, exist_ok=True)
        ziel.write_bytes(inhalt)
        files.append({"path": name, "sha256": _sha256(ziel)})
    for leer in sorted((d for d in root.rglob("*") if d.is_dir()), reverse=True):
        if not any(leer.iterdir()):
            leer.rmdir()
    fresh = {
        "source_repo": "Freelancing",
        "source_path": _THEME_SRC_REL,
        "source_commit": commit,
        "doctrine": "Freelancing products/pbi_theme ist die kanonische Theme-Engine; ALUCA "
                    "vendort ihre Theme-JSONs byte-identisch (ADR-0005: vendor + PIN, kein "
                    "Submodul). Nie hier editieren — in Freelancing erzeugen, dann --write-themes.",
        "files": files,
    }
    (root / "PIN.json").write_text(json.dumps(fresh, indent=2, ensure_ascii=False) + "\n",
                                   encoding="utf-8", newline="\n")
    return fresh


# ------------------------------------------------------ counterpart freshness (D-341)
# This sensor diffs against a WORKING TREE, not against `origin`. A stale tree makes both
# sides look identical — because both are old. Measured instead of trusted; the German
# counterpart `scripts/check_aluca_mirror.py` carries the same behaviour in its own wording
# (SHARED_SUBSTANCE.md class C: same capability, deliberately different expression).
# Exit codes are part of this sensor's contract, because a caller must be able to tell the
# two red states apart. Meridian's `check_aluca_mirror.py` delegates to this script and read
# every non-zero as DRIFT — so an unverifiable run was reported as "GEGENRICHTUNG gedriftet"
# while this script's own line said "in sync". One number for two conditions cannot be read.
EXIT_OK = 0
EXIT_DRIFT = 1
EXIT_UNVERIFIABLE = 2      # could not compare: no counterpart checkout, or uncertain freshness

FETCH_MAX_AGE_S = 3600
"""When a fetch counts as stale. A convention, not a measurement — what it costs when set too
generously is the window described above. Override with ``--max-fetch-age``."""


def _git(root: Path, *args: str) -> str | None:
    """``git`` inside the counterpart checkout. None on any failure — the sensor must never be
    the reason a gate goes red."""
    try:
        proc = subprocess.run(("git", *args), cwd=str(root), capture_output=True,
                              text=True, timeout=30, encoding="utf-8", errors="replace")
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout.strip() if proc.returncode == 0 else None


def checkout_freshness(root: Path) -> dict:
    """Provenance of the counterpart checkout. **No network** — reads only what is already local."""
    behind = _git(root, "rev-list", "--count", "HEAD..@{upstream}")
    dirty = _git(root, "status", "--porcelain")
    git_dir = _git(root, "rev-parse", "--absolute-git-dir")
    fetch_age: int | None = None
    if git_dir:
        fetch_head = Path(git_dir) / "FETCH_HEAD"
        if fetch_head.is_file():
            fetch_age = int(time.time() - fetch_head.stat().st_mtime)
    return {
        "head": _git(root, "rev-parse", "--short", "HEAD"),
        "branch": _git(root, "rev-parse", "--abbrev-ref", "HEAD"),
        "behind": int(behind) if behind and behind.isdigit() else None,
        "dirty": len([ln for ln in dirty.splitlines() if ln.strip()]) if dirty is not None else None,
        "fetch_age_s": fetch_age,
    }


def _duration(seconds: int) -> str:
    h, rest = divmod(seconds, 3600)
    return f"{h}h {rest // 60}m" if h else f"{rest // 60}m"


def freshness_findings(freshness: dict, max_age: int = FETCH_MAX_AGE_S) -> list[str]:
    """What about the counterpart checkout makes the comparison uncertain. Pure."""
    out: list[str] = []
    behind = freshness.get("behind")
    if behind:
        out.append(f"  checkout is {behind} commit(s) behind its upstream — the diff below "
                   f"measures that older state, not origin")
    dirty = freshness.get("dirty")
    if dirty:
        out.append(f"  working tree has {dirty} modified file(s) — the diff measures the working "
                   f"state, not the committed one")
    age = freshness.get("fetch_age_s")
    if age is None:
        out.append("  never fetched — a gap against origin would not be visible here (`--fetch`)")
    elif age > max_age:
        out.append(f"  last fetch {_duration(age)} ago — whatever was pushed to Meridian since is "
                   f"unknown to this diff (`--fetch`)")
    return out


def freshness_line(freshness: dict) -> str:
    """The provenance in one line, so an OK says what it rests on. Pure."""
    parts = [f"HEAD {freshness.get('head') or '?'}"]
    if freshness.get("branch"):
        parts.append(f"on {freshness['branch']}")
    behind = freshness.get("behind")
    parts.append("no upstream ref" if behind is None else f"{behind} behind upstream")
    dirty = freshness.get("dirty")
    parts.append("clean" if dirty == 0 else f"{dirty} modified file(s)")
    age = freshness.get("fetch_age_s")
    parts.append("never fetched" if age is None else f"fetched {_duration(age)} ago")
    return ", ".join(parts)


def fetch_checkout(root: Path) -> str:
    """Explicit ``git fetch`` in the counterpart checkout (only via ``--fetch``)."""
    return ("fetched origin" if _git(root, "fetch", "origin") is not None
            else "git fetch failed — the diff runs against the old ref state")


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    strict = "--strict" in argv
    write = "--write" in argv
    write_themes = "--write-themes" in argv
    fetch = "--fetch" in argv
    # `--skip-freshness` exists for exactly one caller: Meridian's `check_aluca_mirror.py`
    # delegates the reverse direction to this script. In that call the "counterpart" is
    # Meridian itself — the repo being edited. Its uncommitted working state is the SUBJECT
    # of the diff (that is the whole point of firing on the home side), not a reason to
    # doubt it. Without this, every run with uncommitted work would report the home repo as
    # of uncertain freshness. Not for human use.
    skip_freshness = "--skip-freshness" in argv
    max_age = FETCH_MAX_AGE_S
    if "--max-fetch-age" in argv:
        i = argv.index("--max-fetch-age") + 1
        if i < len(argv) and argv[i].isdigit():
            max_age = int(argv[i])

    pin = vendor_pin()
    tpin = theme_pin()
    mer = _meridian_root()

    if write_themes:
        if mer is None:
            print("[check-dataarch-mirror] --write-themes needs a Freelancing checkout "
                  "($MERIDIAN_ROOT or ../Freelancing)")
            return 1
        ref = "HEAD"
        if "--ref" in argv:
            i = argv.index("--ref") + 1
            if i < len(argv):
                ref = argv[i]
        fresh = write_theme_vendor(mer, ref)
        print(f"[check-dataarch-mirror] re-mirrored {len(fresh['files'])} theme(s) from {mer} "
              f"at {fresh['source_commit'][:8]}")
        return 0

    # --write runs *before* the integrity gate: it is the operation that re-establishes
    # integrity, so gating it on integrity would make a drifted or extended mirror
    # unrepairable — the one state in which it is actually needed.
    if write:
        if mer is None:
            print("[check-dataarch-mirror] --write needs a Meridian checkout "
                  "($MERIDIAN_ROOT or ../Freelancing)")
            return 1
        ref = "HEAD"
        if "--ref" in argv:
            i = argv.index("--ref") + 1
            if i < len(argv):
                ref = argv[i]
        fresh = write_vendor(mer, pin, ref)
        print(f"[check-dataarch-mirror] re-mirrored {len(fresh['files'])} file(s) from {mer} "
              f"at {fresh['source_commit'][:8]}")
        return 0

    # The vendored subtree's integrity does not need Meridian — check it always.
    # A local edit is not drift, it is a doctrine breach: the mirror is changed in
    # Meridian and re-mirrored, never patched here.
    if pin is not None:
        local = vendor_integrity(pin)
        if local:
            print("[check-dataarch-mirror] vendored emitters edited locally — change them in "
                  "Meridian and re-mirror instead:")
            for line in local:
                print(line)
            return 1
    if tpin is not None:
        local = vendor_integrity(tpin, _THEME_VENDOR_REL)
        if local:
            print("[check-dataarch-mirror] vendored themes edited locally — generate them in "
                  "Freelancing (products/pbi_theme) and re-mirror (--write-themes) instead:")
            for line in local:
                print(line)
            return 1

    if mer is None:
        # D-341: DID NOT RUN is not a passed comparison. Without --strict this stays a named
        # skip (the sibling checkout is a dev convenience); in the release gate it is a
        # failure, otherwise the gate passes precisely when it checked nothing.
        if pin is not None:
            print(f"[check-dataarch-mirror] vendored emitters OK ({len(pin['files'])} file(s), "
                  f"local integrity)")
        if tpin is not None:
            print(f"[check-dataarch-mirror] vendored themes OK ({len(tpin['files'])} file(s), "
                  f"local integrity)")
        print("[check-dataarch-mirror] Meridian checkout not reachable "
              "($MERIDIAN_ROOT or ../Freelancing) — the cross-repo diff DID NOT RUN")
        if strict:
            print("[check-dataarch-mirror] --strict: a comparison that did not run is not a "
                  "passed comparison")
            return EXIT_UNVERIFIABLE
        return EXIT_OK

    if fetch:
        print(f"[check-dataarch-mirror] {fetch_checkout(mer)}")

    # What everything below rests on — measured, not assumed.
    freshness = checkout_freshness(mer)
    uncertain = [] if skip_freshness else freshness_findings(freshness, max_age)
    if uncertain:
        print("[check-dataarch-mirror] counterpart checkout is of uncertain freshness; the diff "
              "below measures exactly that state:")
        for line in uncertain:
            print(line)

    meridian = _extract(mer / _MER_REL / "concepts.py",
                        mer / _MER_REL / "governance_concepts.py",
                        mer / _MER_REL / "odcs.py", "mer")
    aluca = _extract(REPO_ROOT / _ALU_REL / "architecture_concepts.py",
                     REPO_ROOT / _ALU_REL / "governance_concepts.py",
                     REPO_ROOT / _ALU_REL / "odcs.py", "alu")

    drift = _diff(meridian, aluca)
    if pin is not None:
        # Gegen den Commit, ausser Meridian selbst ruft (--skip-freshness): dort ist der
        # uncommittete Stand der Gegenstand der Pruefung (siehe oben).
        drift += vendor_upstream_drift(pin, mer, None if skip_freshness else "HEAD")
    if tpin is not None:
        drift += theme_upstream_drift(tpin, mer, None if skip_freshness else "HEAD")

    if not drift:
        vendored = len(pin["files"]) if pin else 0
        themes = len(tpin["files"]) if tpin else 0
        print(f"[check-dataarch-mirror] OK — mirror in sync with Meridian ({mer}); "
              f"contract surface + {vendored} vendored file(s) + {themes} vendored theme(s)")
        print(f"[check-dataarch-mirror] diffed against: {freshness_line(freshness)}")
        if uncertain and strict:
            print("[check-dataarch-mirror] --strict: in sync with a state of uncertain freshness "
                  "is not in sync")
            return EXIT_UNVERIFIABLE
        return EXIT_OK

    # D-442 (15.09.2026, measured in Meridian): a difference measured against a counterpart
    # checkout of uncertain freshness is not a finding about the two repositories -- it may be a
    # finding about that one checkout. On that day the sibling sensor reported "drifted" on a Mac
    # whose counterpart carried 4859 modified files, and "in sync" on a Windows box where both
    # repositories were current. Same code, same repositories, opposite verdict.
    #
    # Worse than the verdict was the advice: "re-mirror" would have copied the stale state over
    # the current one -- the sensor would have produced the drift it reports. So the headline
    # only says "re-mirror" when the comparison can carry it.
    if uncertain:
        print(f"[check-dataarch-mirror] DIFFERENCE vs Meridian ({mer}) — do NOT re-mirror yet, "
              f"the counterpart checkout is of uncertain freshness (see above); refresh it and "
              f"measure again:")
    elif any(NICHT_SCHREIBEN in line for line in drift):
        print(f"[check-dataarch-mirror] DRIFT vs Meridian ({mer}) — do NOT re-mirror blindly, "
              f"at least one side is behind the mirror (see below):")
    else:
        print(f"[check-dataarch-mirror] DRIFT vs Meridian ({mer}) — re-mirror:")
    for line in drift:
        print(line)
    if strict:
        # Mirror image of the line in the OK branch above (D-341): "in sync with a state of
        # uncertain freshness is not in sync". Red stays red -- EXIT_UNVERIFIABLE is non-zero --
        # only the reason becomes true, and with it what one does about it.
        if uncertain:
            print("[check-dataarch-mirror] --strict: a finding against a state of uncertain "
                  "freshness is not a finding about the repositories (D-442) — UNVERIFIABLE")
            return EXIT_UNVERIFIABLE
        print("[check-dataarch-mirror] --strict: drift is a hard failure")
        return EXIT_DRIFT
    print("[check-dataarch-mirror] advisory (reports drift, never bumps) — Exit 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
