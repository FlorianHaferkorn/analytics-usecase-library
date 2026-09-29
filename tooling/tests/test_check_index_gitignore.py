"""Das Index-Gate misst den versionierten Bestand, nicht das Dateisystem (29.09.2026).

Anlass: `claude-repo-kit` v3.24 (f58372c1) hat `scripts/check_index.py` durch die Kit-Fassung
ersetzt; `_git_ignored_prefixes` und `_git_submodule_prefixes` waren danach weg (Reparatur
378b5163, PR #529). `test_check_index_submodule.py` prueft nur die Funktion beim Namen: ein
Kit, das die Faehigkeit unter anderem Namen mitbringt, machte ihn rot; eines, das die Funktion
als toten Rest behielte, aber in `main()` nicht mehr aufriefe, gruen.

Die Proben hier fahren das Gate als Programm in einem Wegwerf-Repository (`tmp_path`, `git init`)
und messen nur Exit-Code und Ausgabe -- was die Datei intern tut, ist ihnen gleich. Belegt wird:
(a) gitignorierte Dateien und Ordner verlangt das Gate nicht im Register, (b) Dateien eines
Submoduls (gitlink, Modus 160000) ebenso nicht, (c) eine neue, versionierbare Datei daneben
bleibt pflichtig (Gegenprobe: sonst hiesse Exit 0 auch "Gate prueft gar nichts").
Vorbild: Freelancing `core/tests/test_check_index_gitignore.py`.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

_REGISTER = """---
last-reviewed: 2099-01-01
shelf-life-days: 90
---
# Bereich

| Datei | Zweck |
|---|---|
| `gelistet.md` | versioniert, daher gelistet |
"""


@pytest.fixture(autouse=True)
def _ohne_git_umgebung(monkeypatch: pytest.MonkeyPatch) -> None:
    """Die Proben laufen auch im pre-commit-Hook. Dort setzt Git `GIT_INDEX_FILE` (und je nach
    Aufruf `GIT_DIR`) auf das echte Repository; `git init`/`git add` im Wegwerf-Repo schrieben
    dann in dessen Index bzw. Konfiguration (gemessen 29.09.2026 in Fabric_Lineage:
    `core.bare = true` im echten Repo; Vorbild Freelancing #491). Deshalb vor jeder Probe alle
    `GIT_*` weg."""
    for name in [n for n in os.environ if n.startswith("GIT_")]:
        monkeypatch.delenv(name)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.name=probe", "-c", "user.email=probe@example.invalid",
                    "-C", str(repo), *args], check=True, capture_output=True)


def _schreibe(pfad: Path, text: str) -> None:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_text(text, encoding="utf-8", newline="\n")


@pytest.fixture()
def gate_repo(tmp_path: Path) -> Path:
    """Wegwerf-Repository mit der Gate-Fassung dieses Arbeitsbaums unter `scripts/`.

    Im Bereich liegen, alle nicht im Register: ein gitignorierter Ordner, eine gitignorierte
    Datei und ein initialisiertes Submodul mit eigener Markdown-Datei."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    (repo / "scripts").mkdir()
    shutil.copyfile(ROOT / "scripts" / "check_index.py", repo / "scripts" / "check_index.py")
    _schreibe(repo / ".gitignore", "lauf/\n*.log.md\n")
    bereich = repo / "Bereich"
    _schreibe(bereich / "_INDEX.md", _REGISTER)
    _schreibe(bereich / "gelistet.md", "# Gelistet\n")
    _schreibe(bereich / "lauf" / "protokoll_2099-01-01.md", "# Lauf\n")
    _schreibe(bereich / "heute.log.md", "# Lauf\n")
    # Submodul: eigenes Repository im Bereich, im aeusseren als gitlink (160000) erfasst.
    sub = bereich / "fremd"
    sub.mkdir()
    _git(sub, "init", "-q")
    _schreibe(sub / "submodul_notiz.md", "# Fremd versioniert\n")
    _git(sub, "add", ".")
    _git(sub, "commit", "-q", "-m", "probe")
    _git(repo, "add", ".")
    return repo


def _gate(repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(repo / "scripts" / "check_index.py"), "--strict"],
                          capture_output=True, text=True, encoding="utf-8", errors="replace",
                          cwd=repo)


def test_probe_repo_hat_gitlink(gate_repo):
    # Vorbedingung: ohne gitlink prueft die Submodul-Probe nichts.
    out = subprocess.run(["git", "-C", str(gate_repo), "ls-files", "-s", "Bereich/fremd"],
                         capture_output=True, text=True, encoding="utf-8", check=True).stdout
    assert out.startswith("160000 "), out


def test_gate_verlangt_keine_gitignorierten_dateien(gate_repo):
    r = _gate(gate_repo)
    assert "protokoll_2099-01-01.md" not in r.stdout, (
        "check_index.py verlangt gitignorierte Dateien im Register -- repo-eigene Faehigkeit "
        "(_git_ignored_prefixes) verloren, Kit-Sync? Reparaturvorlage: 378b5163\n"
        + r.stdout[-2000:])
    assert "heute.log.md" not in r.stdout, r.stdout[-2000:]


def test_gate_verlangt_keine_submodul_dateien(gate_repo):
    r = _gate(gate_repo)
    assert "submodul_notiz.md" not in r.stdout, (
        "check_index.py verlangt Dateien eines Submoduls im Register -- repo-eigene Faehigkeit "
        "(_git_submodule_prefixes) verloren, Kit-Sync? Reparaturvorlage: 378b5163\n"
        + r.stdout[-2000:])


def test_gate_ist_auf_dem_probe_bestand_gruen(gate_repo):
    r = _gate(gate_repo)
    assert r.returncode == 0, r.stdout[-2000:]


def test_gate_verlangt_weiter_versionierte_dateien(gate_repo):
    # Gegenprobe: ohne sie hiesse Exit 0 oben auch "Gate prueft gar nichts".
    _schreibe(gate_repo / "Bereich" / "unregistriert.md", "# Neu\n")
    r = _gate(gate_repo)
    assert r.returncode == 1, r.stdout[-2000:]
    assert "unregistriert.md" in r.stdout
    assert "protokoll_2099-01-01.md" not in r.stdout
    assert "submodul_notiz.md" not in r.stdout


def test_proben_laufen_ohne_git_umgebung():
    """Sperre fuer die Fixture oben: im pre-commit-Hook gesetzte `GIT_*` duerfen die Proben nicht
    erreichen, sonst schreibt `git add` im Wegwerf-Repo in den Index des echten Repositorys."""
    assert [n for n in os.environ if n.startswith("GIT_")] == []
