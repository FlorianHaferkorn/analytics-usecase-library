#!/usr/bin/env python3
"""KPI-ID-Migration D-594: semantische IDs (`sales.net_sales.amount`) -> `KPI-<KUERZEL>-<NNN>`.

Einmaliges Migrationswerkzeug. Die Zuordnung alt -> neu steht nicht hier, sondern in der von
Florian freigegebenen Tabelle aus Meridian (`research/2026-09-30_d594_kpi_mapping/
kpi_id_mapping.yaml`, Pfad per Argument). Das Werkzeug liest sie, schreibt alle Vorkommen im
Repo um und benennt die Dateien um, deren Name eine KPI-ID ist. Kein `legacy_id`, kein Alias,
kein Mapping in der Ladestrecke (D-594 Nachtrag 1).

Was es tut (`--apply`), in dieser Reihenfolge:

1. Plan-Bezuege als Katalogfeld: `plan_kpi_ref` / `plan_variance_kpi_ref` werden aus der alten
   ID-Syntax abgeleitet (`<basis>.plan.<einheit>`, `<basis>.vs_plan.<einheit>`), solange sie noch
   lesbar ist -- danach traegt die ID keine Bedeutung mehr (`comparison_measures.plan_kpi`).
2. `rolle: entfernen` (CCC-Proxy): Katalogdatei geloescht; in YAML-Listen, die das Ziel schon
   fuehren, faellt die Zeile weg; Tabellenzeilen der Katalog-Doku, die die entfernte KPI nennen,
   fallen weg; jedes andere Vorkommen wird auf die Ziel-ID umgelenkt.
3. Umschreiben mit exakter Grenze (wie die Blast-Radius-Analyse):
   `(?<![A-Za-z0-9_.])ID(?![A-Za-z0-9_])(?!\\.[a-z0-9_])`, dazu Dateipfade (`kpis/<ID>.yaml`),
   die Praefixe `Pre_`/`Post_` der Wirkungsformeln und -- nur in `UNTERSTRICH_KLASSEN` -- die
   Unterstrich-Form der OSS-Namen (`margin_gm_pct` -> `kpi_com_013`, dieselbe Form wie
   `sql_builder.kpi_to_query_name` und `generate_dbt_metrics`).
4. Dateiumbenennung (`git mv`) fuer Katalog und ROI-Presets.

`--check` meldet jedes verbliebene alte Vorkommen ausserhalb der `AUSNAHMEN` (Exit 1).
`--report <json>` schreibt die Zaehlung je Artefaktklasse (Vorkommen, Dateien).

Die Neuzugaenge der Tabelle (Aurora/Branchenpaket, `neuzugang_bibliothek: true`) legt das
Werkzeug NICHT im Katalog an: `validate_kpi_catalog.ps1` verlangt einen Use Case oder Action
Code je Katalog-KPI, und keiner referenziert sie. `--neuzugaenge <out.yaml>` schreibt sie als
vorbelegte Vorlage aus den Meridian-Quellen, Unbekanntes als Leerstelle (`NEUZUGANG_BLOCKIERT`).

    python -m tooling.migration.kpi_id_migration --mapping <kpi_id_mapping.yaml> --report out.json
    python -m tooling.migration.kpi_id_migration --mapping <kpi_id_mapping.yaml> --apply
    python -m tooling.migration.kpi_id_migration --mapping <kpi_id_mapping.yaml> --check
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
KPIS = "core/kpi_catalog/kpis"
PRESETS = "core/templates/business_case/presets"
NEUES_MUSTER = re.compile(r"^KPI-(COM|FIN|OPS|SCM|SVC|CUS|GOV|PPL|QUA|ESG)-\d{3}$")

# Historische Stellen: bleiben wie sie sind und zaehlen nicht in --check. (glob, grund)
AUSNAHMEN: tuple[tuple[str, str], ...] = (
    ("CHANGELOG.md", "Release-Historie"),
    ("docs/architecture/adr/*", "ADRs halten die Entscheidung zum Stand ihres Datums"),
    ("internal/archive/*", "Archiv"),
    ("docs/plans/*", "Umsetzungsplaene/Reviews mit Stand-Datum und zitierten Messungen"),
    ("docs/architecture/premium-acceptance-F0-F6.md", "Abnahme vom 08.07.2026"),
    ("internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md", "Fehlerlog, zitierte Meldungen sind Belege"),
    ("internal/project_mgmt/KNOWN_GAPS.md", "Audit 27.03.2026, Resolved-Teil append-only"),
    ("internal/project_mgmt/FRAMEWORK_V1_EXECUTION_PLAN.md", "Plan Stand 20.04.2026"),
    ("internal/project_mgmt/AURORA_SYNTHETIC_DATA_GAPS.md", "Datenluecken-Spezifikation, Status 19.07.2026"),
    ("internal/core_content_review_results.md", "Review 17.02.2026"),
    ("internal/metrics/runs/*", "Messlaeufe mit Datum"),
    ("tooling/generator/prompts/repo_quality_improvement_prompts.md", "Repo-Review Stand 06.04.2026"),
    ("showcases/aurora_group/proof/Aurora_Proof_Dossier.md", "Proof-Dossier Version 1.0, 01.06.2026"),
    ("products/fabric/powerbi/docs/reporting/Report_Documentation_COM-001.md",
     "generierte Report-Doku, Stand 07.02.2026"),
    ("tooling/migration/*", "das Werkzeug selbst (Quelle der Umschreibung)"),
    ("tooling/tests/test_kpi_id_migration.py", "Test des Werkzeugs (alte IDs als Fixture)"),
)

# Zaehlklassen, erster Treffer gewinnt.
KLASSEN: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("katalog", ("core/kpi_catalog/*",)),
    ("brackets", ("core/usecases/*/UseCase_Bracket.yaml",)),
    ("use_case_doku", ("core/usecases/*",)),
    ("action_codes", ("core/action_codes/*",)),
    ("presets", (PRESETS + "/*",)),
    ("semantic_models", ("core/semantic_models/*",)),
    ("core_sonstige", ("core/*",)),
    ("dist", ("products/fabric/powerbi/dist/*",)),
    ("fabric", ("products/fabric/*",)),
    ("oss", ("products/open_source_stack/*",)),
    ("studio", ("studio/*",)),
    ("superversion", ("tooling/superversion/*",)),
    ("tooling_tests", ("tooling/tests/*", "tooling/*/tests/*")),
    ("tooling", ("tooling/*",)),
    ("showcases", ("showcases/*",)),
    ("internal", ("internal/*",)),
    ("doku", ("*",)),
)
UNTERSTRICH_KLASSEN = frozenset({"oss"})
KATALOG_DOKU = ("core/kpi_catalog/*.md", "core/kpi_catalog/standards/*.md")


@dataclass
class Mapping:
    alt_neu: dict[str, str]                 # alle ALUCA-IDs (kanonisch + entfernen) -> neue ID
    entfernt: dict[str, str]                # entfernte alte ID -> alte Ziel-ID
    neuzugaenge: list[dict] = field(default_factory=list)

    @property
    def unterstrich(self) -> dict[str, str]:
        return {a.replace(".", "_"): unterstrich_name(n) for a, n in self.alt_neu.items()}


def unterstrich_name(neu: str) -> str:
    """OSS-/dbt-Name einer KPI: `KPI-COM-013` -> `kpi_com_013` (wie `kpi_to_query_name`)."""
    return re.sub(r"[^a-z0-9_]", "_", neu.lower().replace("-", "_"))


def lade_mapping(pfad: Path) -> Mapping:
    d = yaml.safe_load(pfad.read_text(encoding="utf-8"))
    alt_neu, entfernt, neu = {}, {}, []
    for z in d["zeilen"]:
        if z["quelle"] == "aluca":
            alt_neu[z["alt_id"]] = z["neu_id"]
            if z["rolle"] == "entfernen":
                entfernt[z["alt_id"]] = z["ziel_alt_id"]
        elif z.get("neuzugang_bibliothek"):
            neu.append(z)
    falsch = sorted(n for n in alt_neu.values() if not NEUES_MUSTER.match(n))
    if falsch:
        raise ValueError(f"Mapping fuehrt IDs ausserhalb des neuen Musters: {falsch}")
    for alt, ziel in entfernt.items():
        if alt_neu[alt] != alt_neu[ziel]:
            raise ValueError(f"entfernen {alt}: neu_id {alt_neu[alt]} != Ziel {alt_neu[ziel]}")
    return Mapping(alt_neu, entfernt, neu)


def _alt(ids) -> str:
    return "|".join(re.escape(i) for i in sorted(ids, key=len, reverse=True))


@dataclass
class Muster:
    punkt: re.Pattern
    pfad: re.Pattern
    praefix: re.Pattern
    unterstrich: re.Pattern

    @classmethod
    def aus(cls, m: Mapping) -> "Muster":
        a = _alt(m.alt_neu)
        return cls(
            punkt=re.compile(r"(?<![A-Za-z0-9_.])(" + a + r")(?![A-Za-z0-9_])(?!\.[a-z0-9_])"),
            pfad=re.compile(r"(?<=[/`'\"(\s])(" + a + r")(?=\.ya?ml\b)"),
            praefix=re.compile(r"(?<![A-Za-z0-9.])(Pre_|Post_)(" + a + r")(?![A-Za-z0-9_])(?!\.[a-z0-9_])"),
            unterstrich=re.compile(r"(?<![A-Za-z0-9_])(" + _alt(m.unterstrich) + r")(?![A-Za-z0-9_])"),
        )


def _passt(rel: str, muster: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatch(rel, g) for g in muster)


def ausnahme(rel: str) -> str | None:
    for g, grund in AUSNAHMEN:
        if fnmatch.fnmatch(rel, g):
            return grund
    return None


def klasse(rel: str) -> str:
    for name, muster in KLASSEN:
        if _passt(rel, muster):
            return name
    return "doku"


def git_dateien(root: Path) -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=root, check=True, capture_output=True).stdout
    return [p for p in out.decode("utf-8").split("\0") if p]


def lies(root: Path, rel: str) -> str | None:
    try:
        return (root / rel).read_text(encoding="utf-8")
    except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
        return None


# --------------------------------------------------------------------------- umschreiben

def zaehle(text: str, rel: str, mu: Muster) -> int:
    n = len(mu.punkt.findall(text)) + len(mu.pfad.findall(text)) + len(mu.praefix.findall(text))
    if klasse(rel) in UNTERSTRICH_KLASSEN:
        n += len(mu.unterstrich.findall(text))
    return n


def umschreiben(text: str, rel: str, m: Mapping, mu: Muster) -> str:
    text = mu.praefix.sub(lambda x: x.group(1) + m.alt_neu[x.group(2)], text)
    text = mu.pfad.sub(lambda x: m.alt_neu[x.group(1)], text)
    text = mu.punkt.sub(lambda x: m.alt_neu[x.group(1)], text)
    if klasse(rel) in UNTERSTRICH_KLASSEN:
        u = m.unterstrich
        text = mu.unterstrich.sub(lambda x: u[x.group(1)], text)
    return text


_LISTE = re.compile(r"^(\s*)-\s+['\"]?([A-Za-z0-9_.\-]+)['\"]?\s*$")


def entferne_zeilen(text: str, rel: str, m: Mapping) -> str:
    """`rolle: entfernen`: YAML-Listeneintrag weg, wenn dieselbe Liste das Ziel fuehrt;
    Tabellenzeilen der Katalog-Doku, die die entfernte KPI nennen, weg."""
    if not m.entfernt:
        return text
    zeilen = text.split("\n")
    raus: set[int] = set()
    if rel.endswith((".yaml", ".yml")):
        i = 0
        while i < len(zeilen):
            mt = _LISTE.match(zeilen[i])
            if not mt:
                i += 1
                continue
            einr, block = mt.group(1), []
            while i < len(zeilen) and (mt := _LISTE.match(zeilen[i])) and mt.group(1) == einr:
                block.append((i, mt.group(2)))
                i += 1
            werte = {w for _, w in block}
            for j, w in block:
                if w in m.entfernt and m.entfernt[w] in werte:
                    raus.add(j)
    if _passt(rel, KATALOG_DOKU):
        rx = re.compile(r"(?<![A-Za-z0-9_.])(" + _alt(m.entfernt) + r")(?![A-Za-z0-9_])(?!\.[a-z0-9_])")
        for j, z in enumerate(zeilen):
            if z.lstrip().startswith("|") and rx.search(z):
                raus.add(j)
    return "\n".join(z for j, z in enumerate(zeilen) if j not in raus)


# --------------------------------------------------------------------------- Plan-Bezuege

PLAN_FELDER = (("plan_kpi_ref", "plan"), ("plan_variance_kpi_ref", "vs_plan"))


def plan_bezuege(ids: set[str]) -> dict[str, dict[str, str]]:
    """Aus der alten ID-Syntax: `<basis>.<einheit>` -> `<basis>.plan|vs_plan.<einheit>`, wenn
    der Katalog die Plan-KPI fuehrt (bisher `comparison_measures.plan_kpi` per rpartition)."""
    out: dict[str, dict[str, str]] = {}
    for kid in sorted(ids):
        basis, _, einheit = kid.rpartition(".")
        for feld, art in PLAN_FELDER:
            kandidat = f"{basis}.{art}.{einheit}"
            if basis and kandidat in ids:
                out.setdefault(kid, {})[feld] = kandidat
    return out


def setze_plan_felder(text: str, felder: dict[str, str]) -> str:
    """Traegt die Felder als Top-Level-Schluessel hinter `good_is:` (sonst `calc_type:`) ein."""
    zeilen = text.split("\n")
    anker = next((i for i, z in enumerate(zeilen) if z.startswith("good_is:")), None)
    if anker is None:
        anker = next(i for i, z in enumerate(zeilen) if z.startswith("calc_type:"))
    neu = [f"{k}: {v}" for k, v in felder.items() if not any(z.startswith(f"{k}:") for z in zeilen)]
    return "\n".join(zeilen[: anker + 1] + neu + zeilen[anker + 1:])


# --------------------------------------------------------------------------- Laeufe

def bestand(root: Path, m: Mapping) -> tuple[dict, list[tuple[str, int]]]:
    mu = Muster.aus(m)
    je_klasse: dict[str, dict[str, int]] = {}
    ausgenommen: list[tuple[str, int]] = []
    for rel in git_dateien(root):
        text = lies(root, rel)
        if text is None:
            continue
        n = zaehle(text, rel, mu)
        if not n:
            continue
        if ausnahme(rel):
            ausgenommen.append((rel, n))
            continue
        k = je_klasse.setdefault(klasse(rel), {"vorkommen": 0, "dateien": 0})
        k["vorkommen"] += n
        k["dateien"] += 1
    return je_klasse, ausgenommen


def datei_umbenennungen(root: Path, m: Mapping) -> tuple[list[tuple[str, str]], list[str]]:
    mv, rm = [], []
    for ordner in (KPIS, PRESETS):
        for p in sorted((root / ordner).glob("*.yaml")):
            alt = p.stem
            if alt not in m.alt_neu:
                continue
            if alt in m.entfernt:
                rm.append(f"{ordner}/{p.name}")
            else:
                mv.append((f"{ordner}/{p.name}", f"{ordner}/{m.alt_neu[alt]}.yaml"))
    return mv, rm


def apply(root: Path, m: Mapping) -> dict:
    mu = Muster.aus(m)
    ids = {p.stem for p in (root / KPIS).glob("*.yaml") if p.stem != "_index"}
    for kid, felder in plan_bezuege(ids).items():
        p = root / KPIS / f"{kid}.yaml"
        p.write_text(setze_plan_felder(p.read_text(encoding="utf-8"), felder), encoding="utf-8")
    mv, rm = datei_umbenennungen(root, m)
    for rel in rm:
        subprocess.run(["git", "rm", "-q", rel], cwd=root, check=True)
    geaendert = 0
    for rel in git_dateien(root):
        if ausnahme(rel):
            continue
        text = lies(root, rel)
        if text is None:
            continue
        neu = umschreiben(entferne_zeilen(text, rel, m), rel, m, mu)
        if neu != text:
            (root / rel).write_text(neu, encoding="utf-8", newline="")
            geaendert += 1
    for alt, neu in mv:
        subprocess.run(["git", "mv", alt, neu], cwd=root, check=True)
    return {"geaenderte_dateien": geaendert, "umbenannt": len(mv), "entfernt": rm}


def check(root: Path, m: Mapping) -> list[tuple[str, int]]:
    mu = Muster.aus(m)
    rest = []
    for rel in git_dateien(root):
        if ausnahme(rel):
            continue
        text = lies(root, rel)
        if text and (n := zaehle(text, rel, mu)):
            rest.append((rel, n))
    for ordner in (KPIS, PRESETS):
        for p in (root / ordner).glob("*.yaml"):
            if p.stem in m.alt_neu:
                rest.append((f"{ordner}/{p.name}", 1))
    return rest


# --------------------------------------------------------------------------- Neuzugaenge

NEUZUGANG_BLOCKIERT = (
    "validate_kpi_catalog.ps1: 'use_case_ref and action_code_ref both empty' ist ein Fehler; "
    "kein ALUCA-Use-Case und kein Action Code referenziert diese KPI. Anlage im Katalog wartet "
    "auf Entscheidung (Use Case zuordnen oder Regel fuer Bibliotheks-KPIs ohne Use Case)."
)
LEER = None  # ausgewiesene Leerstelle: nicht aus der Quelle belegbar


def _quelle(pfade: dict[str, Path], z: dict) -> dict | None:
    q = z["quelle"].split(":")[-1]
    p = pfade.get(q)
    if not p:
        return None
    for k in json.loads(p.read_text(encoding="utf-8"))["kpis"]:
        if k.get("id") in (z["alt_id"], z["neu_id"]):
            return k
    return None


def neuzugang_entwurf(z: dict, q: dict | None) -> dict:
    """Vorbelegt aus Meridian; was die Quelle nicht traegt, bleibt Leerstelle (None)."""
    d = (q or {}).get("definition", {})
    meta = (q or {}).get("meta", {})
    label = (q or {}).get("label", {})
    return {
        "kpi_id": z["neu_id"],
        "kpi_key": label.get("en") or z.get("name"),
        "synonyms": [label["de"]] if label.get("de") else [],
        "kpi_type": LEER,
        "impact_dimension": LEER,
        "domain_tag": [t for t in meta.get("tags", [])] or LEER,
        "use_case_ref": [],
        "action_code_ref": [],
        "calc_type": LEER,
        "good_is": {"higher_is_better": "higher", "lower_is_better": "lower"}.get((q or {}).get("direction")),
        "business": {
            "purpose": LEER,
            "definition": d.get("formula"),
            "grain_scope": LEER,
            "unit_format": LEER,
            "interpretation": (q or {}).get("quality", {}).get("measurability_note"),
        },
        "technical": {"measure_name": label.get("en") or z.get("name"), "description": LEER,
                      "lineage": [], "depends_on_measures": []},
        "governance": {"business_owner": meta.get("owner") or z.get("owner"), "data_owner": LEER,
                       "steward": LEER},
        "_herkunft": {"quelle": z["quelle"], "meridian_id": z["alt_id"],
                      "meridian_einheit": d.get("unit"), "zaehler": d.get("numerator"),
                      "nenner": d.get("denominator"), "blockiert": NEUZUGANG_BLOCKIERT},
    }


# --------------------------------------------------------------------------- CLI

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mapping", type=Path, required=True, help="kpi_id_mapping.yaml (Meridian, freigegeben)")
    ap.add_argument("--root", type=Path, default=REPO)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--apply", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--report", type=Path, metavar="JSON")
    g.add_argument("--neuzugaenge", type=Path, metavar="YAML")
    ap.add_argument("--aurora-kpi", type=Path, help="Meridian organisations/aurora/core/kpi.json")
    ap.add_argument("--pack-kpi", type=Path, action="append", default=[],
                    help="Meridian industry-packs/<name>/core/kpi.template.json (mehrfach)")
    a = ap.parse_args(argv)
    m = lade_mapping(a.mapping)
    root = a.root.resolve()

    if a.report:
        je_klasse, ausgenommen = bestand(root, m)
        mv, rm = datei_umbenennungen(root, m)
        bericht = {
            "je_klasse": dict(sorted(je_klasse.items())),
            "summe": {"vorkommen": sum(k["vorkommen"] for k in je_klasse.values()),
                      "dateien": sum(k["dateien"] for k in je_klasse.values())},
            "ausnahmen": [{"datei": r, "vorkommen": n, "grund": ausnahme(r)} for r, n in ausgenommen],
            "umbenennungen": [{"alt": x, "neu": y} for x, y in mv],
            "entfernt": rm,
        }
        a.report.write_text(json.dumps(bericht, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{bericht['summe']['vorkommen']} Vorkommen in {bericht['summe']['dateien']} Dateien, "
              f"{len(ausgenommen)} Ausnahmedateien, {len(mv)} Umbenennungen, {len(rm)} entfernt")
        return 0
    if a.apply:
        print(json.dumps(apply(root, m), ensure_ascii=False))
        return 0
    if a.check:
        rest = check(root, m)
        for rel, n in rest:
            print(f"{rel}: {n}")
        print(f"{sum(n for _, n in rest)} alte Vorkommen in {len(rest)} Dateien ausserhalb der Ausnahmeliste")
        return 1 if rest else 0
    pfade = {"aurora": a.aurora_kpi} if a.aurora_kpi else {}
    for p in a.pack_kpi:
        pfade[p.parent.parent.name] = p
    entwuerfe = [neuzugang_entwurf(z, _quelle(pfade, z)) for z in m.neuzugaenge]
    a.neuzugaenge.write_text(
        "# Vorlage D-594: Neuzugaenge der Bibliothek, vorbelegt aus Meridian; null = Leerstelle.\n"
        f"# Erzeugt von tooling/migration/kpi_id_migration.py --neuzugaenge. {NEUZUGANG_BLOCKIERT}\n"
        + yaml.safe_dump(entwuerfe, allow_unicode=True, sort_keys=False, width=100),
        encoding="utf-8")
    print(f"{len(entwuerfe)} Neuzugaenge als Vorlage -> {a.neuzugaenge}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
