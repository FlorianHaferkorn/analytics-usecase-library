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
