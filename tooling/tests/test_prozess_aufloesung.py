"""Was `posix_bash()` und `programm()` zusichern -- und der Fall, in dem es brach.

Schwesterdatei im Freelancing-Repo: `core/tests/test_prozess_aufloesung.py`.
Der Fund stammt von dort, die Luecke stand hier genauso.

Die Zusage: ein ABSOLUTER Pfad. Nur der umgeht die Suchreihenfolge von
`CreateProcess`, die System32 vor den PATH stellt und dort den WSL-Starter
findet. Ein relativer Pfad taugt dafuer nicht.

Gemessen am 10.09.2026, Arbeitsverzeichnis `C:\\Windows\\System32`:

    shutil.which("bash")  ->  '.\\bash.EXE'
    posix_bash()          ->  '.\\bash.EXE'      <-- der Starter, unerkannt

`shutil.which` gibt relativ zurueck, wenn der Treffer im aktuellen Verzeichnis
liegt. Damit brachen zwei Zusagen auf einmal: die Aussortierung prueft den
Verzeichnisnamen und sah nur `''`, und der Rueckgabewert war wieder etwas, das
`CreateProcess` selbst suchen muss.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from tooling import prozess


def test_der_gefundene_pfad_ist_absolut():
    """Die Kernzusage, ohne die alles andere in dieser Datei sinnlos waere."""
    gefunden = prozess.posix_bash()
    if gefunden is None:
        pytest.skip("kein POSIX-bash auf diesem Rechner")
    assert os.path.isabs(gefunden), gefunden


def test_auch_aus_dem_verzeichnis_des_starters_heraus(tmp_path, monkeypatch):
    """Der gemessene Fall: `which` findet den Treffer im Arbeitsverzeichnis.

    Nachgestellt statt nachgefahren -- ein Test, der nach
    `C:\\Windows\\System32` wechselt, liefe nur auf einem Windows mit genau
    dieser Datei. Hier legt der Test sein eigenes Verzeichnis an, faelscht
    `which` und prueft, was `posix_bash` daraus macht.
    """
    monkeypatch.chdir(tmp_path)
    fake = tmp_path / "bash.exe"
    fake.write_bytes(b"")
    monkeypatch.setattr(prozess.shutil, "which", lambda name: "./bash.exe")
    monkeypatch.delenv(prozess.UMGEBUNGSVARIABLE, raising=False)

    gefunden = prozess.posix_bash()
    assert gefunden is not None
    assert os.path.isabs(gefunden), "ein relativer Pfad umgeht die Suchreihenfolge nicht"
    assert Path(gefunden).name.lower() == "bash.exe"


def test_der_wsl_starter_wird_auch_relativ_erkannt(tmp_path, monkeypatch):
    """Der eigentliche Schaden: unerkannt gewinnt der Starter gegen Git-Bash.

    Ein Verzeichnis namens `System32` unter einer gefaelschten Windows-Wurzel,
    darin ein `bash.exe`, und `which` meldet es relativ. Erkannt werden muss es
    trotzdem -- sonst startet der Lauf das WSL-Programm.
    """
    wurzel = tmp_path / "Windows"
    sys32 = wurzel / "System32"
    sys32.mkdir(parents=True)
    (sys32 / "bash.exe").write_bytes(b"")
    monkeypatch.chdir(sys32)
    monkeypatch.setenv("SystemRoot", str(wurzel))
    monkeypatch.setattr(prozess.shutil, "which", lambda name: "./bash.exe")
    monkeypatch.delenv(prozess.UMGEBUNGSVARIABLE, raising=False)

    assert prozess._ist_wsl_starter(prozess._absolut("./bash.exe")) is True
    # posix_bash faellt damit auf die Git-Bash-Kandidaten zurueck (oder None) --
    # in keinem Fall auf den Starter.
    assert prozess.posix_bash() != str(sys32 / "bash.exe")


def test_programm_gibt_ebenfalls_absolut_zurueck(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "irgendwas.exe").write_bytes(b"")
    monkeypatch.setattr(prozess.shutil, "which", lambda name: "./irgendwas.exe")
    gefunden = prozess.programm("irgendwas")
    assert gefunden is not None and os.path.isabs(gefunden), gefunden


def test_ein_unbekanntes_programm_bleibt_none(monkeypatch):
    """Kein Rueckfall auf den nackten Namen -- der Aufrufer soll entscheiden."""
    monkeypatch.setattr(prozess.shutil, "which", lambda name: None)
    assert prozess.programm("gibtsnicht") is None


def test_ein_bereits_absoluter_pfad_wird_nicht_verbogen(monkeypatch):
    """`Path("/usr/bin/bash").resolve()` macht auf Windows `C:\\usr\\bin\\bash`.

    Aus einem gueltigen POSIX-Pfad wird damit ein erfundener. Meine erste
    Fassung von `_absolut` tat genau das; gefunden hat es ein fremder Test im
    ALUCA-Repo, nicht meine eigenen -- die pruefen nur den relativen Fall.
    """
    assert prozess._absolut("/usr/bin/bash") == "/usr/bin/bash"
    monkeypatch.setattr(prozess.shutil, "which", lambda name: "/usr/bin/bash")
    monkeypatch.delenv(prozess.UMGEBUNGSVARIABLE, raising=False)
    assert prozess.posix_bash() == "/usr/bin/bash"
