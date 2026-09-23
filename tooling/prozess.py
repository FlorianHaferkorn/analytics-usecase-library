"""Wie ein Kindprozess auf Windows startet -- an einer Stelle, nicht an dreien.

Warum es diese Datei gibt
-------------------------
Dasselbe Wissen wurde in diesem Repo und im Freelancing-Repo mehrfach
unabhaengig neu erarbeitet: einmal fuer `tooling/superversion/e2e_smoke.py`,
einmal fuer die Testsuite drueben, einmal fuer einen Frische-Pruefer. Jede
Fassung kannte einen Teil. Das ist der Grund fuer die Zusammenlegung, nicht
Ordnungsliebe.

Die Schwester dieser Datei ist `core/prozess.py` im Freelancing-Repo. Sie ist
laenger: dort haengt eine Testsuite dran, die bash-Skripte gegen Stubs faehrt
und dafuer noch PATH-Hilfen braucht. Bewusst zwei Heimaten, kein Spiegel -- wer
hier etwas lernt, traegt es drueben nach.

Die drei Dinge, die Windows anders macht
----------------------------------------
1. **`CreateProcess` sucht anders als der PATH.** Reihenfolge: Verzeichnis der
   startenden EXE, aktuelles Verzeichnis, System32, Windows-Verzeichnis, dann
   erst PATH. In System32 liegt `bash.exe` -- der Starter fuer das Windows-
   Subsystem fuer Linux. Er gewinnt gegen jedes bash im PATH. Ohne installierte
   Distribution bricht er mit Exit 1 ab.
   `shutil.which` folgt dagegen der PATH-Reihenfolge. Ein Waechter, der `which`
   fragt, und ein Lauf, der den nackten Namen startet, pruefen also verschiedene
   Programme. Genau daran starben am 09.09.2026 56 Tests.
   Gegenmittel: immer den absoluten Pfad uebergeben.

2. **`.cmd`- und `.bat`-Huellen sind keine Programme.** npm legt seine CLIs als
   `foo.cmd` ab. `shutil.which("foo")` findet die Huelle ueber PATHEXT und
   meldet Erfolg; `CreateProcess` haengt nur `.exe` an und meldet WinError 2.
   Wieder gehen Waechter und Lauf auseinander.
   Gegenmittel: die Huelle ueber den Kommandoprozessor starten.

3. **Die Ausgabe des Kindes ist nicht UTF-8.** `text=True, encoding="utf-8"`
   pinnt nur die Leseseite; das Kind schreibt in seiner Locale-Kodierung, auf
   einem deutschen Windows cp1252. Ein Umlaut toetet dann den Lesethread von
   `subprocess` mit einem UnicodeDecodeError, den niemand sieht: `stdout` und
   `stderr` kommen als `None` zurueck, nicht als Fehler.
   Gegenmittel: beide Seiten pinnen.

Auf Linux und macOS aendert nichts davon etwas.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path, PurePosixPath

#: Ausdrueckliche Vorgabe, falls jemand ein bestimmtes bash erzwingen will.
UMGEBUNGSVARIABLE = "ALUCA_BASH"

_WINDOWS_SYSTEM = {"system32", "sysnative", "syswow64"}
_HUELLEN = {".cmd", ".bat"}

_GIT_BASH_KANDIDATEN = (
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files (x86)\Git\bin\bash.exe",
    r"C:\Program Files\Git\usr\bin\bash.exe",
)


def _absolut(pfad: str) -> str:
    """Einen gefundenen Programmpfad absolut machen.

    `shutil.which` gibt relativ zurueck, wenn der Treffer im aktuellen
    Verzeichnis liegt -- aus `C:\\Windows\\System32` heraus etwa `.\\bash.EXE`.
    Ein relativer Pfad taugt hier fuer nichts: die Aussortierung unten prueft
    den Verzeichnisnamen und saehe nur `''`, und der Aufrufer bekaeme wieder
    etwas, das `CreateProcess` selbst suchen muss. Gemessen am 10.09.2026.
    """
    # Schon absolut -- nicht anfassen. `Path("/usr/bin/bash").resolve()` macht
    # auf Windows `C:\\usr\\bin\\bash` daraus: aus einem gueltigen POSIX-Pfad
    # wird ein erfundener.
    #
    # Beide Konventionen pruefen, nicht nur die des laufenden Systems:
    # `os.path.isabs("/usr/bin/bash")` ist auf Windows False, weil der
    # Laufwerksbuchstabe fehlt. Diese Funktion sieht aber Pfade aus beiden
    # Welten -- einen Windows-Pfad von `shutil.which`, einen POSIX-Pfad aus
    # einer Vorgabe. Gemessen am 10.09.2026, beide Male.
    if os.path.isabs(pfad) or PurePosixPath(pfad).is_absolute():
        return pfad
    try:
        return str(Path(pfad).resolve())
    except OSError:
        return pfad


def _ist_wsl_starter(pfad: str) -> bool:
    """`C:\\Windows\\System32\\bash.exe` ist kein bash, sondern ein WSL-Starter.

    Erkannt am Verzeichnis, nicht am Dateinamen: der Name ist derselbe wie beim
    echten bash, und genau das ist ja das Problem. `Sysnative` und `SysWOW64`
    zeigen auf dieselbe Datei und muessen mitgezaehlt werden.
    """
    eltern = Path(pfad).parent
    if eltern.name.lower() not in _WINDOWS_SYSTEM:
        return False
    wurzel = os.environ.get("SystemRoot") or os.environ.get("windir")
    if not wurzel:
        return True
    try:
        return Path(wurzel).resolve() in Path(pfad).resolve().parents
    except OSError:
        return True


def posix_bash() -> str | None:
    """Absoluter Pfad zu einem echten bash -- oder None, wenn keines da ist."""
    vorgabe = os.environ.get(UMGEBUNGSVARIABLE)
    if vorgabe:
        return _absolut(vorgabe) if Path(vorgabe).is_file() else None

    gefunden = shutil.which("bash")
    if gefunden:
        gefunden = _absolut(gefunden)
        if not _ist_wsl_starter(gefunden):
            return gefunden

    for kandidat in _GIT_BASH_KANDIDATEN:
        if Path(kandidat).is_file():
            return kandidat
    return None


def programm(name: str) -> str | None:
    """Absoluter Pfad zu `name` -- oder None. Nie eine Ausnahme.

    Fuer `bash` gilt die Sonderbehandlung aus `posix_bash`. Fuer alles andere
    ist es `shutil.which`, aber das Ergebnis wird auch benutzt: wer den
    aufgeloesten Pfad wegwirft und den nackten Namen startet, hat den Waechter
    umsonst gefragt.
    """
    if Path(name).name.lower() in {"bash", "bash.exe"}:
        return posix_bash()
    gefunden = shutil.which(name)
    return _absolut(gefunden) if gefunden else None


def befehl(programm_pfad: str, *argumente: str) -> list[str]:
    """Startbare Befehlszeile fuer einen bereits aufgeloesten Pfad.

    `.cmd`/`.bat` sind Skripte fuer den Kommandoprozessor, keine Programme.
    `CreateProcess` startet sie nicht; deshalb hier ausdruecklich ueber ComSpec.
    """
    if os.name == "nt" and Path(programm_pfad).suffix.lower() in _HUELLEN:
        return [os.environ.get("ComSpec", "cmd.exe"), "/d", "/s", "/c", programm_pfad, *argumente]
    return [programm_pfad, *argumente]


def kind_umgebung(basis: dict[str, str] | None = None, **zusatz: str) -> dict[str, str]:
    """Umgebung fuer ein Kind, dessen Ausgabe als UTF-8 gelesen wird.

    Siehe Punkt 3 im Modulkopf. Gemessen am 09.09.2026: sechs rote Tests in
    `test_open_points_apply`, ausschliesslich auf Windows, ausschliesslich
    deswegen.
    """
    umgebung = dict(os.environ if basis is None else basis)
    umgebung["PYTHONIOENCODING"] = "utf-8"
    umgebung.update(zusatz)
    return umgebung


def umgebung_ohne(*namen: str, **zusatz: str) -> dict[str, str]:
    """Wie `kind_umgebung`, aber ohne die genannten Variablen.

    Fuer Tests, die beweisen wollen, dass ein Skript ohne Anmeldedaten sauber
    abbricht. Der frueher benutzte Weg -- `env={"PATH": "/usr/bin:/bin"}` --
    tut das auf Windows nicht: dort fehlen damit `SystemRoot` und die
    DLL-Suchpfade, und der Interpreter startet gar nicht erst. Ein Test, der
    aus dem falschen Grund rot wird, misst nichts.
    """
    return kind_umgebung({k: v for k, v in os.environ.items() if k not in namen}, **zusatz)


#: Was Aufrufer starten sollen. Der Rueckfall auf den nackten Namen ist bewusst:
#: er hilft dort, wo `which` nichts findet, das System aber eines hat -- und er
#: schadet nicht, weil die Waechter vorher greifen.
BASH = posix_bash() or "bash"

#: Waechter fuer Tests, die ohne bash nichts aussagen koennen.
KEIN_BASH = posix_bash() is None
KEIN_BASH_GRUND = (
    "kein POSIX-bash gefunden (der WSL-Starter in System32 zaehlt nicht). "
    f"Git-Bash installieren oder {UMGEBUNGSVARIABLE} auf ein bash setzen."
)
