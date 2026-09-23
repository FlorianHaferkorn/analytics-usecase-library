"""Was fuer die ganze Testsuite gilt, bevor der erste Test laeuft.

Hier steht heute genau eine Regel: ein leeres Parameterset ist ein Fehler, kein
Ueberspringen. Der Rumpf ist wortgleich mit `conftest.py` im Freelancing-
Repository -- die Beobachtung, die dazu gefuehrt hat, stammt von dort.
"""
from __future__ import annotations


# ------------------------------------------------------- Leere Parametersets
#: Der Wortlaut, den pytest in den Skip-Grund schreibt, wenn `parametrize`
#: nichts bekommen hat. Geteilter Koerper: dieselbe Fassung steht im anderen
#: Repository.
_LEERES_SET = "got empty parameter set"


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "darf_leer_sein(grund): dieses Parameterset darf leer bleiben -- "
        "mit benannter Begruendung",
    )


def pytest_collection_modifyitems(config, items):
    """Ein Test, den es nicht gibt, wird auch nicht rot.

    `@pytest.mark.parametrize` mit einer leeren Liste erzeugt keinen Testfall,
    sondern einen einzigen uebersprungenen Platzhalter mit dem Grund
    "got empty parameter set". Im Lauf sieht das aus wie ein bewusstes
    Ueberspringen -- eine Zeile zwischen Dutzenden anderen. Es ist aber ein
    Loch: gemessen am 14.09.2026 lief `test_real_pbip_visual_regression`
    dreieinhalb Monate ueber null Aurora-Reports, weil die Erkennung
    `pages.json` an der falschen Stelle suchte. Zehn `.Report`-Ordner lagen
    die ganze Zeit auf der Platte. Kein Fehlschlag, kein Hinweis, nur ein
    Parameterset, das leer blieb.

    Gemessen vor dem Bau: heute gibt es in beiden Repositories kein einziges
    leeres Set (525 bzw. 2949 gesammelte Tests, null Treffer). Der Waechter
    schlaegt also nicht gegen Bestehendes aus -- er haelt einen Zustand fest,
    der schon gilt.

    Wer ein leeres Set braucht, sagt es mit `@pytest.mark.darf_leer_sein` und
    einer Begruendung. Ohne diese Ausnahme bricht die Sammlung ab: lieber laut
    als leise, denn leise war genau das Problem.
    """
    import pytest

    offen = []
    for item in items:
        if any(item.iter_markers(name="darf_leer_sein")):
            continue
        for mark in item.iter_markers(name="skip"):
            grund = mark.kwargs.get("reason", "")
            if not grund and mark.args:
                grund = mark.args[0]
            if _LEERES_SET in str(grund):
                offen.append("%s\n      %s" % (item.nodeid, grund))
                break

    if offen:
        raise pytest.UsageError(
            "Leeres Parameterset -- diese Tests entstehen gar nicht:\n    "
            + "\n    ".join(offen)
            + "\n\n  Entweder die Erkennung reparieren, die die Faelle liefern "
              "soll,\n  oder den Fall mit @pytest.mark.darf_leer_sein(\"Grund\") "
              "benennen."
        )
