"""Der Waechter gegen leere Parametersets -- vier Proben.

Geprueft wird der echte `conftest.py` dieses Repositories, kopiert in ein
Wegwerf-Projekt: ein Waechter, den man nur nachbaut, prueft den Nachbau.

Die vierte Probe ist die wichtigere Haelfte. Ein Waechter, der jeden `skip`
einfaengt, waere in einer Woche abgeschaltet -- diese Suite ueberspringt
absichtlich, wenn Playwright fehlt oder die Baselines von einem anderen System
stammen. Getroffen werden darf nur der eine Grund, den pytest selbst
formuliert.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

_CONFTEST = Path(__file__).resolve().parents[2] / "conftest.py"


def _projekt(tmp_path: Path, inhalt: str) -> Path:
    shutil.copy2(_CONFTEST, tmp_path / "conftest.py")
    (tmp_path / "test_probe.py").write_text(inhalt, encoding="utf-8", newline="\n")
    return tmp_path


def _lauf(pfad: Path):
    return subprocess.run(
        [sys.executable, "-m", "pytest", str(pfad), "-q", "-p", "no:cacheprovider"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(pfad),
    )


LEER = '''
import pytest

@pytest.mark.parametrize("x", [])
def test_ueber_nichts(x):
    assert False
'''

LEER_MIT_AUSNAHME = '''
import pytest

@pytest.mark.darf_leer_sein("Fixtures liegen nicht im Repository")
@pytest.mark.parametrize("x", [])
def test_ueber_nichts(x):
    assert False
'''

VOLL = '''
import pytest

@pytest.mark.parametrize("x", [1, 2])
def test_ueber_etwas(x):
    assert x > 0
'''

ECHTER_SKIP = '''
import pytest

@pytest.mark.skip(reason="Playwright ist hier nicht installiert")
def test_uebersprungen():
    assert False
'''


def test_leeres_set_bricht_die_sammlung_ab(tmp_path):
    """Der Befund, um den es geht: kein Testfall, also auch kein roter."""
    e = _lauf(_projekt(tmp_path, LEER))
    assert e.returncode != 0, e.stdout + e.stderr
    assert "Leeres Parameterset" in (e.stdout + e.stderr)
    assert "test_ueber_nichts" in (e.stdout + e.stderr)


def test_die_benannte_ausnahme_laesst_es_durch(tmp_path):
    """Ohne Ausweg wird der Waechter umgangen statt bedient."""
    e = _lauf(_projekt(tmp_path, LEER_MIT_AUSNAHME))
    assert e.returncode == 0, e.stdout + e.stderr
    assert "Leeres Parameterset" not in (e.stdout + e.stderr)


def test_ein_gefuelltes_set_bleibt_unberuehrt(tmp_path):
    """Gegenprobe: der Normalfall darf nichts merken."""
    e = _lauf(_projekt(tmp_path, VOLL))
    assert e.returncode == 0, e.stdout + e.stderr
    assert "2 passed" in e.stdout


def test_ein_echter_skip_wird_nicht_eingefangen(tmp_path):
    """Die Grenze: getroffen wird der Wortlaut von pytest, nicht jeder Skip."""
    e = _lauf(_projekt(tmp_path, ECHTER_SKIP))
    assert e.returncode == 0, e.stdout + e.stderr
    assert "Leeres Parameterset" not in (e.stdout + e.stderr)
    assert "1 skipped" in e.stdout
