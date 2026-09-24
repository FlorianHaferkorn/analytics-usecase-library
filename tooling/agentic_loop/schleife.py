"""Ein Einstieg für die agentische Schleife S0 bis S7 (UMSETZUNGSPLAN_AGENTIC_LOOP.md, AP-9).

Die Schleife baut nichts selbst. Jede Stufe ruft vorhandene Werkzeuge auf, in dieser Reihenfolge:

    S0 Spezifikation   check_index --strict, check_usecase_quality <UC> --strict
    S1 Modell          die Codegen-Prüfungen (gold_source, model_alignment, comparison_measures,
                       action_trigger_dax, dax_smoke plan)
    S2 Bericht         report_quality --summary
    S3 Veröffentlichen Bereitstellung (Bericht + Modell), sandbox up, sandbox deploy;
                       Laden der Datenscheibe ist noch nicht gebaut
    S4 Laufzeit        dax_smoke run (braucht die Datensatz-ID aus dem Deploy, noch nicht erfasst)
    S5 Rendern         Export über den Service (braucht die Bericht-ID, noch nicht erfasst)
    S6 Prüfen          Meridian check-image je Seitenbild aus S5
    S7 Abräumen        sandbox down

Leitplanken (Plan §5): Trockenlauf ist Standard. Stufen gegen den Tenant laufen nur mit
``--apply`` **und** gesetzten Zugangsdaten; sonst heißen sie „nicht prüfbar“ und nennen den Grund.
Was noch nicht gebaut ist, meldet sich genauso statt grün zu erscheinen. Meridian-Werkzeuge
laufen als eigener Prozess im Meridian-Checkout (kein Import über Repo-Grenzen, E4).

Exit: 0 alles gelaufen und grün · 1 mindestens ein Befund · 2 mindestens ein Schritt nicht
prüfbar, aber kein Befund. Das Ergebnis steht als JSON unter ``<arbeit>/befunde.json``.

    python -m tooling.agentic_loop.schleife --use-case OPS-001 --run-id run-0001 [--stages S0,S1,S2] [--apply]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

REPO = Path(__file__).resolve().parents[2]
DIST = REPO / "products" / "fabric" / "powerbi" / "dist"
STUFEN = ("S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7")
ZUGANG = ("FABRIC_TENANT_ID", "FABRIC_CLIENT_ID", "FABRIC_CLIENT_SECRET")
PY = sys.executable


@dataclass
class Schritt:
    stufe: str
    name: str
    argv: list[str] | None                 # None: noch nicht gebaut, siehe `grund`
    ort: str = "aluca"                     # "aluca" | "meridian"
    tenant: bool = False
    grund: str = ""


@dataclass
class Ergebnis:
    stufe: str
    name: str
    status: str                            # ok | befund | nicht_pruefbar
    rc: int | None = None
    sekunden: float = 0.0
    grund: str = ""
    ausgabe: str = ""


@dataclass
class Lauf:
    use_case: str
    run_id: str
    apply: bool
    ergebnisse: list[Ergebnis] = field(default_factory=list)

    @property
    def exit(self) -> int:
        if any(e.status == "befund" for e in self.ergebnisse):
            return 1
        return 2 if any(e.status == "nicht_pruefbar" for e in self.ergebnisse) else 0


def meridian_root() -> Path | None:
    env = os.environ.get("MERIDIAN_ROOT")
    kandidat = Path(env).expanduser() if env else REPO.parent / "Freelancing"
    return kandidat if (kandidat / "products" / "pbi_visual_regression" / "image_checks.py").is_file() else None


def bericht_und_modell(use_case: str) -> tuple[Path, Path]:
    """Der Bericht des Use Cases und das Modell, auf das seine definition.pbir zeigt."""
    treffer = sorted(DIST.glob(f"{use_case}_*.Report"))
    if not treffer:
        raise SystemExit(f"kein Bericht für {use_case} unter {DIST}")
    bericht = treffer[0]
    pbir = json.loads((bericht / "definition.pbir").read_text(encoding="utf-8"))
    modell = (bericht / pbir["datasetReference"]["byPath"]["path"]).resolve()
    return bericht, modell


def plan(use_case: str, run_id: str, arbeit: Path) -> list[Schritt]:
    bericht, modell = bericht_und_modell(use_case)
    manifest = str(arbeit / "sandbox.json")
    bereit = arbeit / "pbip"
    codegen = ("gold_source", "model_alignment", "comparison_measures", "action_trigger_dax")
    schritte = [
        Schritt("S0", "check_index", [PY, "scripts/check_index.py", "--strict"]),
        Schritt("S0", "usecase_quality", [PY, "tooling/validation/check_usecase_quality.py", use_case, "--strict"]),
        *[Schritt("S1", m, [PY, "-m", f"tooling.codegen.{m}"]) for m in codegen],
        Schritt("S1", "dax_smoke_plan", [PY, "-m", "tooling.codegen.dax_smoke", "plan"]),
        Schritt("S2", "report_quality", [PY, "-m", "tooling.report_quality.cli", "--summary"]),
        Schritt("S3", "bereitstellen", ["bereitstellen", str(bericht), str(modell), str(bereit)]),
        Schritt("S3", "sandbox_up", [PY, "products/fabric/orchestrator/sandbox.py", "up", "--manifest", manifest,
                                     "--run-id", run_id, "--apply"], tenant=True),
        Schritt("S3", "sandbox_deploy", [PY, "products/fabric/orchestrator/sandbox.py", "deploy", "--manifest",
                                         manifest, "--pbip-dir", str(bereit), "--apply"], tenant=True),
        Schritt("S3", "datenscheibe_laden", None, tenant=True,
                grund="noch nicht gebaut: Scheibe ins Lakehouse laden und GoldSourceKind/GoldContainerUrl setzen (AP-3)"),
        Schritt("S4", "dax_smoke_run", None, tenant=True,
                grund="noch nicht gebaut: die Datensatz-ID aus dem Deploy steht nicht im Manifest (AP-2/AP-4)"),
        Schritt("S5", "rendern", None, tenant=True,
                grund="noch nicht gebaut: die Bericht-ID aus dem Deploy steht nicht im Manifest (AP-5)"),
        Schritt("S6", "check_image", ["check_image", str(arbeit / "png"), str(bericht)], ort="meridian"),
        Schritt("S7", "sandbox_down", [PY, "products/fabric/orchestrator/sandbox.py", "down", "--manifest",
                                       manifest, "--apply"], tenant=True),
    ]
    return schritte


Runner = Callable[[list[str], Path], tuple[int, str]]


def subprocess_runner(argv: list[str], cwd: Path) -> tuple[int, str]:
    r = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    return r.returncode, (r.stdout + r.stderr)[-2000:]


def _bereitstellen(bericht: Path, modell: Path, ziel: Path) -> tuple[int, str]:
    """Nur dieser Bericht und sein Modell, als Geschwister: `byPath ../<Modell>` bleibt gültig."""
    if ziel.exists():
        shutil.rmtree(ziel)
    ziel.mkdir(parents=True)
    shutil.copytree(bericht, ziel / bericht.name)
    shutil.copytree(modell, ziel / modell.name)
    return 0, f"{bericht.name} + {modell.name} nach {ziel}"


def _check_image(png_dir: Path, bericht: Path, meridian: Path, runner: Runner) -> tuple[int, str] | str:
    bilder = sorted(png_dir.glob("*.png")) if png_dir.is_dir() else []
    if not bilder:
        return "keine Seitenbilder (S5)"
    rc_max, aus = 0, []
    for png in bilder:
        seite = bericht / "definition" / "pages" / png.stem
        if not seite.is_dir():
            return f"zu {png.name} gibt es keine Seite {png.stem}"
        rc, text = runner([PY, "-m", "products.pbi_visual_regression", "check-image",
                           "--png", str(png), "--page-dir", str(seite)], meridian)
        rc_max, _ = max(rc_max, rc), aus.append(text)
    return rc_max, "\n".join(aus)[-2000:]


def ausfuehren(schritte: list[Schritt], stufen: set[str], apply: bool, lauf: Lauf,
               runner: Runner = subprocess_runner) -> Lauf:
    meridian = meridian_root()
    for s in schritte:
        if s.stufe not in stufen:
            continue
        t0 = time.monotonic()

        def notiz(status: str, rc: int | None = None, grund: str = "", ausgabe: str = "") -> None:
            lauf.ergebnisse.append(Ergebnis(s.stufe, s.name, status, rc, round(time.monotonic() - t0, 2), grund, ausgabe))

        if s.argv is None:
            notiz("nicht_pruefbar", grund=s.grund)
            continue
        if s.tenant and not apply:
            notiz("nicht_pruefbar", grund="Trockenlauf: Tenant-Schritt ohne --apply")
            continue
        if s.tenant and (fehlt := [n for n in ZUGANG if not os.environ.get(n)]):
            notiz("nicht_pruefbar", grund=f"Zugangsdaten fehlen: {', '.join(fehlt)}")
            continue
        if s.ort == "meridian" and meridian is None:
            notiz("nicht_pruefbar", grund="kein Meridian-Checkout (MERIDIAN_ROOT oder ../Freelancing)")
            continue
        if s.argv[0] == "bereitstellen":
            rc, aus = _bereitstellen(*(Path(a) for a in s.argv[1:]))
        elif s.argv[0] == "check_image":
            r = _check_image(Path(s.argv[1]), Path(s.argv[2]), meridian, runner)
            if isinstance(r, str):
                notiz("nicht_pruefbar", grund=r)
                continue
            rc, aus = r
        else:
            rc, aus = runner(s.argv, REPO if s.ort == "aluca" else meridian)
        if rc == 0:
            notiz("ok", rc, ausgabe=aus)
        elif rc == 2:
            notiz("nicht_pruefbar", rc, grund="Werkzeug meldet: nicht prüfbar", ausgabe=aus)
        else:
            notiz("befund", rc, ausgabe=aus)
    return lauf


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--use-case", required=True, help="z. B. OPS-001")
    ap.add_argument("--run-id", required=True, help="Lauf-ID, wird Teil des Sandbox-Namens")
    ap.add_argument("--stages", default=",".join(STUFEN), help="Auswahl, z. B. S0,S1,S2")
    ap.add_argument("--apply", action="store_true", help="Tenant-Stufen wirklich ausführen")
    ap.add_argument("--arbeit", default=None, help="Arbeitsordner (Vorgabe: out/agentic_loop/<run-id>)")
    a = ap.parse_args(argv)
    stufen = {x.strip().upper() for x in a.stages.split(",") if x.strip()}
    if unbekannt := stufen - set(STUFEN):
        ap.error(f"unbekannte Stufe(n): {sorted(unbekannt)}")
    arbeit = Path(a.arbeit) if a.arbeit else REPO / "out" / "agentic_loop" / a.run_id
    arbeit.mkdir(parents=True, exist_ok=True)
    lauf = ausfuehren(plan(a.use_case, a.run_id, arbeit), stufen, a.apply, Lauf(a.use_case, a.run_id, a.apply))
    ergebnis = {**{k: v for k, v in asdict(lauf).items() if k != "ergebnisse"}, "exit": lauf.exit,
                "ergebnisse": [asdict(e) for e in lauf.ergebnisse]}
    (arbeit / "befunde.json").write_text(json.dumps(ergebnis, indent=2, ensure_ascii=False) + "\n",
                                         encoding="utf-8", newline="\n")
    for e in lauf.ergebnisse:
        print(f"{e.stufe} {e.name:<20} {e.status:<15} {e.grund}")
    print(f"[schleife] exit {lauf.exit} -- {arbeit / 'befunde.json'}")
    return lauf.exit


if __name__ == "__main__":
    sys.exit(main())
