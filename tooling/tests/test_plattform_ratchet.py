"""Tests der Plattform-Sperrklinke.

Ein Waechter, der nur auf dem sauberen Repo gruen wird, ist von einem ``return 0``
nicht zu unterscheiden. Die Tests hier pruefen deshalb, dass er **ausloest** --
und zwar an Quelltext, den der Test selbst schreibt, nicht an einer Zusage
darueber, was im Repo steht.

Die Klassen stammen aus einer Messung, nicht aus einer Meinung: am 09.09.2026
waren im Freelancing-Repo auf Windows 69 + 11 + 4 Tests rot, kein einziger davon
ein Codefehler. Jede Klasse hat mindestens einen dieser Fehlschlaege verursacht.

In DIESEM Repo ist die Suite auf Windows gruen (2899 passed, 09.09.2026). Die
Funde sind also latent -- genau so sah das andere Repo aus, bevor es dort
teuer wurde. Deshalb hier eine Klinke ueber dem Bestand statt einer Sperre auf
Null: der Bestand darf sinken, nie steigen.

Der Waechter existiert bewusst zweimal, nicht als Spiegel: er kennt die
Bereichsliste seines Repos, und die unterscheidet die beiden Fassungen. Wer
hier eine Klasse ergaenzt, ergaenzt sie drueben mit -- die Mutationsprobe in
beiden Testdateien ist der Beleg.
"""
from __future__ import annotations

import ast
import collections
import importlib.util
import pathlib

import pytest

_PFAD = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "check_plattform.py"
_spec = importlib.util.spec_from_file_location("check_plattform", _PFAD)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)


def _messen(quelle: str, ist_test: bool = False) -> collections.Counter:
    """Die Klassen in einem Stueck Quelltext zaehlen -- ohne Dateisystem."""
    baum = ast.parse(quelle)
    s = mod.Sammler("<probe>", ist_test=ist_test, docstrings=mod._docstring_ids(baum))
    s.visit(baum)
    return collections.Counter(k for k, _, _ in s.funde)


# ---------------------------------------------------------------- Klasse 1
# Nackter Programmname. `CreateProcess` stellt System32 vor den PATH, dort
# liegt der WSL-Starter `bash.exe`; und `which` findet npm-Huellen, die
# `CreateProcess` nicht startet.

def test_ein_nackter_bash_aufruf_wird_gemeldet():
    assert _messen('subprocess.run(["bash", str(sh)])')["nackter_programmname"] == 1


def test_ein_aufgeloester_pfad_wird_nicht_gemeldet():
    """Der Unterschied, um den es geht: derselbe Aufruf mit absolutem Pfad."""
    assert not _messen('subprocess.run([BASH, str(sh)])')["nackter_programmname"]


def test_npx_zaehlt_mit_denn_es_ist_auf_windows_eine_cmd_huelle():
    assert _messen('subprocess.run(["npx", "--no-install", "x"])')["nackter_programmname"] == 1


def test_git_zaehlt_nicht_denn_es_hat_keinen_schatten():
    """Ein Waechter, der alles verbietet, wird abgeschaltet. `git` hat weder
    einen Namensvetter in System32 noch eine `.cmd`-Huelle."""
    assert not _messen('subprocess.run(["git", "status"])')["nackter_programmname"]


# ---------------------------------------------------------------- Klasse 2
# PATH mit hartem Doppelpunkt. Trenner ist auf Windows das Semikolon, und
# `C:\...` enthaelt selbst einen Doppelpunkt.

def test_ein_path_mit_hartem_doppelpunkt_wird_gemeldet():
    assert _messen('env = {"PATH": f"{binp}:{os.environ[chr(39)]}"}'.replace(
        "os.environ[chr(39)]", "os.environ['PATH']"))["pfad_trenner"] == 1


def test_ein_posix_ausdruck_innerhalb_einer_shell_wird_nicht_gemeldet():
    """`export PATH=/stub:"$PATH"` ist INNERHALB von bash richtig. Die Regel
    haengt deshalb an `os.environ`, nicht an jedem Doppelpunkt neben einem
    Platzhalter -- sonst faellt auch `f"{ok}/{n} ok → {out}/GOLDEN_PATH.md"`
    hinein, und ein Waechter mit Fehlalarmen wird umgangen."""
    assert not _messen('cmd = f\'export PATH={vorn}:"$PATH"; exec "$0"\'')["pfad_trenner"]
    assert not _messen('print(f"{ok}/{n} ok → {out}/GOLDEN_PATH.md")')["pfad_trenner"]


# ---------------------------------------------------------------- Klasse 3
# Kodierung nur auf einer Seite. `text=True` ohne `encoding` liest in der
# Locale; `read_text()` ohne `encoding` ebenso.

def test_text_ohne_encoding_wird_gemeldet():
    assert _messen('subprocess.run(cmd, capture_output=True, text=True)')["kodierung_einseitig"] == 1


def test_text_mit_encoding_wird_nicht_gemeldet():
    assert not _messen(
        'subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")'
    )["kodierung_einseitig"]


def test_read_text_ohne_encoding_wird_gemeldet():
    assert _messen('data = json.loads(p.read_text())')["kodierung_einseitig"] == 1


def test_ein_positionelles_encoding_wird_nicht_doppelt_gemeldet():
    """`write_text(inhalt, "utf-8")` ist gepinnt, nur eben positionell. Wer das
    meldet, provoziert genau die Doppelangabe, die einen TypeError wirft."""
    assert not _messen('p.write_text(inhalt, "utf-8")')["kodierung_einseitig"]


# ---------------------------------------------------------------- Klasse 4
# `str(pfad.relative_to(...))` -- auf Windows Rueckstriche.

def test_str_relative_to_wird_gemeldet():
    assert _messen('out[str(f.relative_to(dest))] = text')["trennzeichen_als_text"] == 1


def test_as_posix_wird_nicht_gemeldet():
    assert not _messen('out[f.relative_to(dest).as_posix()] = text')["trennzeichen_als_text"]


# ---------------------------------------------------------------- Klasse 5
# Ein Dateisystempfad, wo eine URL erwartet wird.

def test_eine_esm_importvorlage_mit_platzhalter_wird_gemeldet():
    assert _messen(
        'RUNNER = "import { f } from \'%(mod)s\';"'
    )["pfad_als_esm_url"] == 1


def test_ein_fester_import_ohne_platzhalter_wird_nicht_gemeldet():
    """Ein Modulname ist keine URL-Frage. Nur eingesetzte Pfade sind eine."""
    assert not _messen(
        'RUNNER = "import { f } from \'node:fs\';"'
    )["pfad_als_esm_url"]


def test_der_docstring_des_waechters_zaehlt_nicht_als_fund():
    """Die Erklaerung der Regel enthaelt die Vorlage als Beispiel. Ein Waechter,
    der sich selbst anzeigt, wird abgeschaltet."""
    quelle = 'def f():\n    """Beispiel: from \'%(mod)s\' ist falsch."""\n    return 1\n'
    assert not _messen(quelle)["pfad_als_esm_url"]


# ---------------------------------------------------------------- Klasse 6
# `write_text` ohne `newline` -- im Produktivcode, nicht in Tests.

def test_write_text_ohne_newline_wird_im_produktivcode_gemeldet():
    assert _messen('p.write_text(inhalt, encoding="utf-8")')["zeilenende_offen"] == 1


def test_write_text_mit_newline_wird_nicht_gemeldet():
    assert not _messen(
        'p.write_text(inhalt, encoding="utf-8", newline="\\n")'
    )["zeilenende_offen"]


def test_in_tests_zaehlt_das_zeilenende_nicht():
    """Ein Test schreibt nach tmp_path; das Ergebnis ueberlebt den Lauf nicht.
    Die Klasse dort mitzuzaehlen waere Laerm ohne Wirkung: 402 Stellen gegen
    173, und keine davon erreicht jemanden."""
    assert not _messen('p.write_text(inhalt, encoding="utf-8")',
                       ist_test=True)["zeilenende_offen"]


# ---------------------------------------------------------------- Klasse 7
# Ein Pruefer, der lautlos verschwindet.

def test_ein_spurloser_importrueckfall_wird_gemeldet():
    assert _messen(
        "try:\n    from x import p\nexcept ImportError:\n    return\n"
        .replace("return", "pass")
    )["stiller_rueckfall"] == 1


def test_ein_rueckfall_mit_meldung_wird_nicht_gemeldet():
    assert not _messen(
        "try:\n    from x import p\n"
        "except ImportError:\n    warnings.warn('kein Pruefer')\n"
    )["stiller_rueckfall"]


def test_ein_rueckfall_der_einen_schalter_setzt_wird_nicht_gemeldet():
    """`HAVE_X = False` haelt den Zustand fest und wird spaeter abgefragt --
    der uebliche und ehrliche Umgang mit einer optionalen Abhaengigkeit. Ein
    Waechter, der auch das verbietet, wird abgeschaltet."""
    assert not _messen(
        "try:\n    import jinja2\n    HAVE = True\nexcept ImportError:\n    HAVE = False\n"
    )["stiller_rueckfall"]


def test_ein_anderer_fehlertyp_geht_den_waechter_nichts_an():
    """Die Klasse handelt von verschwindenden Pruefern, nicht von Fehlerbehandlung
    ueberhaupt."""
    assert not _messen(
        "try:\n    f()\nexcept ValueError:\n    pass\n"
    )["stiller_rueckfall"]


# ---------------------------------------------------------------- Die Klinke
# Je Klasse, nie als Summe.

def test_eine_neue_stelle_in_einer_klasse_ist_ein_befund():
    gestiegen, _ = mod.vergleich(collections.Counter({"kodierung_einseitig": 101}),
                                 {"kodierung_einseitig": 100})
    assert gestiegen == ["kodierung_einseitig: 100 -> 101 (+1)"]


def test_eine_bisher_unbekannte_klasse_hat_baseline_null():
    gestiegen, _ = mod.vergleich(collections.Counter({"pfad_trenner": 1}), {})
    assert gestiegen == ["pfad_trenner: 0 -> 1 (+1)"]


def test_fortschritt_in_einer_klasse_kauft_keinen_rueckschritt_in_einer_anderen():
    """Der Grund fuer „je Klasse" statt „Summe": 30 aufgeraeumte `read_text`
    duerfen kein neues `str(relative_to)` freikaufen."""
    jetzt = collections.Counter({"kodierung_einseitig": 70, "trennzeichen_als_text": 28})
    baseline = {"kodierung_einseitig": 100, "trennzeichen_als_text": 27}
    gestiegen, gesunken = mod.vergleich(jetzt, baseline)
    assert sum(jetzt.values()) < sum(baseline.values()), "die Summe sinkt — genau darum geht es"
    assert gestiegen == ["trennzeichen_als_text: 27 -> 28 (+1)"]
    assert gesunken == ["kodierung_einseitig: 100 -> 70"]


# ---------------------------------------------------------------- Der Bestand

def test_die_harten_klassen_stehen_auf_null():
    """Klasse 1 bis 6 sind aufgeloest und bleiben es. Klasse 7 hat einen Bestand
    und laeuft als Klinke -- sie steht deshalb nicht in dieser Liste."""
    jetzt, zeilen = mod.messen()
    for klasse in mod.HARTE_KLASSEN:
        treffer = [z for z in zeilen if z.startswith(klasse)]
        assert jetzt.get(klasse, 0) == 0, "\n".join(treffer)


def test_der_waechter_liest_ueberhaupt_etwas():
    """Gegenprobe gegen einen leeren Lauf.

    Bis 10.09.2026 stand hier „findet mehr als 50 Funde" — als Beweis, dass der
    Sammler laeuft. Seit alle sechs Klassen auf Null sind, waere genau dieser
    Test der erste, der bei einem kaputten Sammler gruen bliebe: null Funde sind
    ja jetzt der Sollzustand. Gemessen wird deshalb die Reichweite, nicht die
    Ausbeute."""
    anzahl = sum(1 for _ in mod.dateien())
    assert anzahl > 300, f"nur {anzahl} Dateien im Blick — Bereichsliste kaputt?"
    jetzt, zeilen = mod.messen()
    assert len(zeilen) == sum(jetzt.values())


def test_die_klinke_haelt_gegen_die_baseline():
    """Der Lauf selbst, nicht nur seine Bestandteile.

    Die Tests darueber pruefen die Regeln (an eigenem Quelltext) und die
    Vergleichslogik (an eigenen Zahlen). Erst dieser hier faehrt den Waechter
    gegen das echte Repo und die echte Baseline -- und ist damit die Stelle,
    an der ein neuer Fund im Testlauf auffaellt statt erst in der CI.
    """
    rc = mod.main([])
    assert rc == 0, "Waechter meldet einen Anstieg — Ausgabe siehe Lauf"


@pytest.mark.parametrize("bereich", mod.BEREICHE)
def test_jeder_gemessene_bereich_existiert(bereich):
    """Ein Waechter, der ein Verzeichnis nicht mehr findet, meldet still Null."""
    assert (mod.REPO_ROOT / bereich).is_dir()
