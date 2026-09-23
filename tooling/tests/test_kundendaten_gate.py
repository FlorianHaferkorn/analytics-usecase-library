r"""Der Kundendaten-Gate: prueft die WIRKUNG, nicht die Regex.

Warum dieser Test existiert und warum er so aussieht
----------------------------------------------------
Ein frueherer Test derselben Familie las das Muster aus dem Modul und fuetterte
es sich selbst zurueck. Er war immer gruen -- die Regex findet, wonach sie sucht.
Mutationstests bewiesen das: beide Mutationen blieben gruen. Deshalb kennt dieser
Test kein Muster aus dem Modul. Er kennt nur die Sperrliste als externe Wahrheit
und fragt: findet der gebaute Regelsatz diesen Namen in dieser Schreibweise?

Der eigentliche Anlass (04.09.2026): die Grenze war `(?<![\w-])...(?![\w-])`.
Weil `_` und `-` in der Zeichenklasse standen, rutschte jede Kennung durch, die
als Namensteil zwischen Trennern steht -- `<Kennung>-Import`,
`<kennung>_ledger_package_1_0`, `<Kennung>_Auftragseingaenge`. Genau die
Schreibweise, in der solche Namen in Code und Schemata tatsaechlich vorkommen.
Der Sweep meldete 0 Treffer und lag falsch.

Die Beispiele stehen hier als Platzhalter, nicht als echte Namen. Ein Test, der
die gesuchten Kennungen ausbuchstabiert, traegt sie selbst ins Repository -- das
Gate hat genau das an diesem Modul auch prompt gemeldet.
"""

import os
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "tooling" / "validation"))

from check_kundendaten import SPERRLISTE, regeln_bauen, sperrliste_laden  # noqa: E402

# Die Sperrliste traegt echte Kundenkennungen und ist deshalb bewusst nicht eingecheckt
# (`.gitignore`). Fehlt sie, kann dieser Test nichts pruefen — und ein Test, der nichts
# prueft, meldet keinen Erfolg. Er sagt hier, dass er nicht gelaufen ist, statt zu bestehen.
#
# Der Grund fuer die Form: `sperrliste_laden` beendet den Prozess (`sys.exit`), und das ist
# fuer das Skript richtig. Der Aufruf steht hier aber in einem `parametrize`, also im
# Einsammeln — gemessen am 04.09.2026 gegen `origin/main` mit der CI-Zeile
# `python -m pytest --tb=short -q`: `INTERNALERROR ... SystemExit`, **no tests ran**. Nicht
# dieser eine Test fiel aus, sondern die gesamte Suite des Repos.
if not (_ROOT / SPERRLISTE).exists():
    pytest.skip(
        f"Sperrliste {SPERRLISTE} fehlt — dieser Test prueft ohne sie nichts und besteht "
        "deshalb nicht. Vorlage: scripts/kundendaten-sperrliste.beispiel.json",
        allow_module_level=True,
    )


def _kundennamen() -> list[str]:
    daten = sperrliste_laden(_ROOT)
    namen = [n for n in ((daten.get("begriffe") or {}).get("kunde") or []) if n]
    assert namen, "Sperrliste fuehrt keine Kundennamen - der Test haette nichts zu pruefen"
    return namen


def _trifft(text: str) -> bool:
    return any(muster.search(text) for _, muster in regeln_bauen(sperrliste_laden(_ROOT)))


@pytest.mark.parametrize("name", _kundennamen())
@pytest.mark.parametrize(
    "form",
    [
        "{n}",              # blank
        "{n}-Import",       # Bindestrich rechts
        "Import-{n}",       # Bindestrich links
        "{n}_ledger",       # Unterstrich rechts
        "check_{n}.py",     # Unterstrich links, Dateiname
        "fact_{n}_monat",   # beidseitig eingeklemmt
    ],
)
def test_eine_kundenkennung_wird_auch_als_namensteil_gefunden(name: str, form: str) -> None:
    text = form.format(n=name)
    assert _trifft(text), f"nicht gefunden: {text!r}"


@pytest.mark.parametrize("name", _kundennamen())
def test_dieselbe_kennung_mitten_im_wort_ist_kein_treffer(name: str) -> None:
    """Die Gegenprobe. Ohne sie wuerde auch ein Gate ohne jede Grenze bestehen.

    Kurze Kennungen stecken reihenweise in gewoehnlichen Woertern und in
    Bezeichnern: drei Buchstaben treffen in deutscher Prosa fast sicher, vier
    in einem camelCase-Namen. Ohne Grenze meldete das Gate hunderte Fehlalarme
    und waere nach dem zweiten Mal umgangen. Die Namen selbst stehen auch hier
    nicht; der Parametersatz zieht sie aus der Sperrliste.
    """
    assert not _trifft(f"vor{name}nach"), f"Fehlalarm mitten im Wort: vor{name}nach"


def test_ein_unverfaenglicher_text_loest_nichts_aus() -> None:
    assert not _trifft("Eine Domaene, ein Gold-Produkt und eine richtige Berechtigung.")


# ---------------------------------------------------------------------------
# Die Sperrliste gehoert nicht in die Prozessliste (D-421/D-425, gespiegelt aus
# Freelancing am 15.09.2026)
#
# Der Anlass stammt aus dem anderen Repository, die Ursache nicht: beide
# Waechter uebergaben ihre Suchbegriffe als Argumente, und Argumente eines
# Prozesses liest jeder, der `ps` aufrufen darf. Die Sperrliste liegt
# ausserhalb der Versionsverwaltung, damit die Kennungen nirgends stehen --
# und stand dann in der Befehlszeile jedes Laufs. Aufgefallen ist es drueben am
# 16.09.2026, als ein `subprocess.TimeoutExpired` sie in ein Protokoll druckte.
#
# Hier stand dieselbe Zeile noch, nur unbemerkt. Die Umstellung ist deshalb
# keine Uebernahme einer fremden Entscheidung, sondern dieselbe Luecke.
# ---------------------------------------------------------------------------

_HEIKEL = [
    "zzeinfach",
    "zz mit leerzeichen",
    "-zzfuehrender-strich",      # mit `-e` ein Muster, als Argument ein Schalter
    "zz.punkt",
    "zz[klammer]",
    "zz*stern",
    "ZzGrossKlein",
]


def _repo_mit(tmp_path, zeilen: list[str]):
    import subprocess

    repo = tmp_path / "baum_heikel"
    repo.mkdir()
    (repo / "a.txt").write_text("\n".join(zeilen) + "\n", encoding="utf-8")
    umgebung = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
    for befehl in (["init", "-q", "."], ["add", "-A"],
                   ["commit", "-qm", "x", "--no-gpg-sign"]):
        subprocess.run(["git", "-C", str(repo)] + befehl, check=True, env=umgebung,
                       capture_output=True)
    return repo


def test_die_suchbegriffe_stehen_nicht_in_der_befehlszeile() -> None:
    """Die Zusage selbst: kein Begriff und kein Muster als Argument."""
    import inspect

    import check_kundendaten as mod

    quelle = inspect.getsource(mod.pruefen)
    assert '"-e", b' not in quelle, "Begriffe stehen wieder als Argumente da"
    assert '"-e", "|".join' not in quelle, "Muster stehen wieder als Argumente da"
    assert "musterdatei(" in quelle


def test_musterdatei_und_argumente_finden_dasselbe(tmp_path) -> None:
    """Die Gegenprobe zur Sicherheitsmassnahme: findet sie auch dasselbe?

    Gemessen an Begriffen, die als Argument Aerger machen -- Leerzeichen,
    fuehrender Strich, Regex-Sonderzeichen. Mit `-F` sind sie feste
    Zeichenketten, und beide Wege muessen dieselben Zeilen liefern. Eine
    Sicherheitsmassnahme, die Treffer kostet, ist keine.
    """
    import subprocess

    import check_kundendaten as mod

    repo = _repo_mit(tmp_path, [f"Zeile mit {b} darin" for b in _HEIKEL] + ["nichts hier"])
    grund = ["git", "-C", str(repo), "grep", "-nIiF", "--no-color"]
    mit_e = list(grund)
    for b in _HEIKEL:
        mit_e += ["-e", b]
    a = subprocess.run(mit_e + ["--", "."], capture_output=True, text=True,
                       encoding="utf-8")
    with mod.musterdatei(_HEIKEL) as datei:
        b_ = subprocess.run(grund + ["-f", datei, "--", "."], capture_output=True,
                            text=True, encoding="utf-8")
    assert sorted(a.stdout.splitlines()) == sorted(b_.stdout.splitlines())
    assert len(b_.stdout.splitlines()) == len(_HEIKEL), b_.stdout


def test_ein_begriff_mit_zeilenumbruch_bricht_ab_statt_sich_zu_teilen() -> None:
    """Die Grenze, die `-f` einzieht -- benannt statt stillschweigend.

    Ein Umbruch im Begriff waere in der Datei zwei Muster, mit einer Bedeutung,
    die niemand gemeint hat. Mit `-e` war er ein Muster. Ein Waechter, der eine
    Suche leise anders meint, meldet irgendwann gruen, wo er rot meinte.
    """
    import check_kundendaten as mod

    with pytest.raises(RuntimeError, match="Zeilenumbruch"):
        with mod.musterdatei(["zzein\nzzzwei"]):
            pass


def test_die_musterdatei_liegt_geschuetzt_und_verschwindet() -> None:
    """Eine Datei mit Kundenkennungen, die liegenbleibt, ist die Sperrliste noch einmal.

    Die Rechtepruefung gilt nur auf POSIX. Windows kennt von den neun Modus-Bits genau
    eines, das schreibgeschuetzte Flag; `os.chmod(pfad, 0o600)` laesst `stat()` dort
    unveraendert `0o666` melden. Was die Datei dort schuetzt, ist ihr Ort: das Systemtemp
    liegt im Benutzerprofil und traegt dessen ACL. Die ACL selbst prueft dieser Test nicht,
    dafuer braeuchte es pywin32.
    """
    import stat
    import tempfile

    import check_kundendaten as mod

    with mod.musterdatei(["zzein", "zzzwei"]) as pfad:
        assert Path(pfad).read_text(encoding="utf-8") == "zzein\nzzzwei\n"
        if os.name == "posix":
            rechte = stat.S_IMODE(os.stat(pfad).st_mode)
            assert rechte == 0o600, oct(rechte)
        else:
            temp = Path(tempfile.gettempdir()).resolve()
            assert temp in Path(pfad).resolve().parents, \
                f"liegt nicht im Benutzer-Temp ({temp}): {pfad}"
        assert ".git" not in pfad, f"liegt im Repository: {pfad}"
    assert not Path(pfad).exists(), "die Datei blieb liegen"


def test_eine_musterdatei_verschwindet_auch_nach_einem_fehler() -> None:
    """Der Fall, der ohne `finally` liegenbleibt -- und genau dann liegt sie da."""
    import check_kundendaten as mod

    with _schlucken_und_merken() as merker:
        with mod.musterdatei(["zzdrei"]) as pfad:
            merker["pfad"] = pfad
            raise RuntimeError("abbruch")
    assert not Path(merker["pfad"]).exists()


class _schlucken_und_merken:  # noqa: N801
    """Ein winziger Helfer: Ausnahme schlucken, Pfad behalten."""

    def __enter__(self):
        self.merker: dict[str, str] = {}
        return self.merker

    def __exit__(self, *args):
        return True


# ---------------------------------------------------------------------------
# Die Deckungsprobe zur Umstellung
#
# `musterdatei()` ist eine Sicherheitsmassnahme. Dass sie dasselbe FINDET, ist
# damit noch nicht gesagt -- und eine Sicherheitsmassnahme, die Treffer kostet,
# ist keine. Die beiden Proben oben vergleichen `-e` und `-f` auf der Ebene von
# `git grep`; diese hier gehen durch `pruefen()`, also durch genau die Stellen,
# die umgestellt wurden.
#
# Gepflanzt wird mit Platzhaltern und einer eigenen Sperrliste, nie mit der
# echten: ein Test, der die gesuchten Kennungen ausbuchstabiert, traegt sie
# selbst ins Repository.
# ---------------------------------------------------------------------------


def test_der_begriffe_lauf_findet_einen_gepflanzten_namen(tmp_path) -> None:
    import check_kundendaten as mod

    repo = _repo_mit(tmp_path, ["Projekt zzeinfach-Import laeuft.", "nichts hier"])
    befunde = mod.pruefen(repo, False, {"begriffe": {"kunde": ["zzeinfach"]}})
    assert befunde, "der Lauf meldet nichts, obwohl der Begriff im Baum steht"
    assert befunde[0]["datei"] == "a.txt" and befunde[0]["zeile"] == 1, befunde


def test_der_muster_lauf_findet_ein_gepflanztes_muster(tmp_path) -> None:
    """Die zweite umgestellte Stelle -- vorher eine Alternation als Argument."""
    import check_kundendaten as mod

    repo = _repo_mit(tmp_path, ["Server unter zzhost-7 erreichbar.", "nichts hier"])
    befunde = mod.pruefen(repo, False, {"muster": {"host": ["zzhost-[0-9]+"]}})
    assert befunde, "der Muster-Lauf meldet nichts, obwohl das Muster passt"
    assert befunde[0]["treffer"].lower() == "zzhost-7", befunde


def test_ein_unverfaenglicher_baum_bleibt_still(tmp_path) -> None:
    """Gegenprobe: ein Lauf, der immer meldet, meldet nichts."""
    import check_kundendaten as mod

    repo = _repo_mit(tmp_path, ["nichts hier", "auch nichts"])
    assert mod.pruefen(repo, False, {"begriffe": {"kunde": ["zzeinfach"]}}) == []
