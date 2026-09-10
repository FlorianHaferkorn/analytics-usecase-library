#!/usr/bin/env python3
r"""Sperrklinke gegen die Annahmen, die nur auf Linux stimmen.

Warum es diesen Waechter gibt
-----------------------------
Am 09.09.2026 waren 69 Tests auf Windows rot, kein einziger davon ein
Codefehler. Danach noch einmal 11 im Default-Lauf, danach noch einmal 4, als
`make` und `jq` installiert waren und uebersprungene Tests zu laufen anfingen.
Immer dieselben vier Annahmen, immer neu gefunden, weil nichts sie festhielt.

Die vier Klassen
----------------
1. **nackter Programmname.** `subprocess.run(["bash", ...])` laesst
   `CreateProcess` suchen, und dessen Reihenfolge stellt System32 vor den PATH.
   Dort liegt der WSL-Starter. `shutil.which` folgt dagegen dem PATH -- Waechter
   und Lauf pruefen verschiedene Programme. Dasselbe mit npm-Huellen (`.cmd`),
   die `which` findet und `CreateProcess` nicht startet.
   Gemessen: 41 Stellen, 56 rote Tests.
2. **PATH mit hartem Doppelpunkt.** Der Trenner ist auf Windows ein Semikolon,
   und `C:\\...` enthaelt selbst einen Doppelpunkt.
   Gemessen: 3 rote Tests, die "Gefunden: 0" als Befund ueber den Tenant
   meldeten.
3. **Kodierung nur auf einer Seite gepinnt.** `text=True, encoding="utf-8"`
   bestimmt das Lesen, nicht das Schreiben des Kindes. Ein Umlaut toetet dann
   den Lesethread, und `stdout` kommt als `None` zurueck -- nicht als Fehler.
   Dasselbe bei `read_text()`/`write_text()` ohne `encoding`.
   Gemessen: 9 rote Tests.
4. **`str(pfad.relative_to(...))` als Schluessel oder Zusage.** Auf Windows
   Rueckstriche, ueberall sonst Schraegstriche.
   Gemessen: 3 rote Tests.
5. **Ein Dateisystempfad, wo eine URL erwartet wird.** Der ESM-Lader von Node
   nimmt nur die Schemata file, data und node. `C:\...` sieht fuer ihn aus wie
   das Schema "c:" und wird mit ERR_UNSUPPORTED_ESM_URL_SCHEME abgewiesen. Auf
   Linux faellt es nicht auf, weil `/tmp/...` dort als relativer Pfad noch
   durchgeht. Richtig ist `Path(...).as_uri()`.
   Gemessen: 6 rote Tests.
6. **`write_text` ohne `newline` im Produktivcode.** Textmodus macht auf Windows
   aus jedem `\n` ein `\r\n`. Ein Lieferartefakt haengt damit am Betriebssystem
   dessen, der es erzeugt hat, und jeder Byte-Vergleich dagegen ist eine
   Wette auf die Maschine. In Tests ist es folgenlos (tmp_path) und wird
   deshalb nicht gezaehlt.
   Gemessen: 1 roter Test, und 372 von 437 dist-Dateien mit falschen
   Zeilenenden im Arbeitsbaum.
7. **Ein Pruefer, der lautlos verschwindet.** `try: import pruefer / except
   ImportError: return` -- der Rueckfall ist unsichtbar, und ob geprueft wird,
   haengt am `sys.path` des Aufrufers. `test_generate_aurora_uc_fin_001` war
   deshalb gruen, solange es allein lief: der Validator war dann nicht
   importierbar, und geprueft wurde nichts. Sobald mehr vom Baum gesammelt
   wurde, kam er dazu und meldete einen echten Befund.
   Erlaubt bleibt der Rueckfall -- er muss nur etwas sagen (`warnings.warn`,
   `logging`, `print`, oder eine Ausnahme).
   Gemessen: 1 Test, der aus dem falschen Grund gruen war.

Stand 10.09.2026 in diesem Repo: die Suite ist auf Windows gruen (2899 passed,
gemessen am 09.09.2026) -- die Funde unten sind also latent, nicht akut. Genau
so sah das Freelancing-Repo aus, bevor dieselben Klassen dort 84 Tests kosteten.

`pfad_trenner` und `pfad_als_esm_url` stehen auf Null und sind hart gesperrt.
Der Rest laeuft als Sperrklinke: der Bestand darf sinken, nie steigen. Je Klasse
und nicht als Summe -- 30 aufgeraeumte `read_text` duerfen kein neues
`str(relative_to)` freikaufen.

Aufruf:
    python3 scripts/check_plattform.py            # prueft gegen die Baseline
    python3 scripts/check_plattform.py --schreiben  # Baseline neu setzen
"""
from __future__ import annotations

import argparse
import ast
import collections
import json
import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
BASELINE = REPO_ROOT / "scripts" / "plattform_baseline.json"

#: Wo gemessen wird. Alles andere ist Fremdcode oder Werkzeugbau.
#:
#: Diese Liste ist der einzige echte Unterschied zur Fassung im
#: Freelancing-Repo (`scripts/check_plattform.py`) -- und der Grund, warum die
#: Datei bewusst doppelt existiert statt gespiegelt zu werden: sie hat zwei
#: Heimaten, nicht eine Heimat und einen Abzug. `MIRRORED_FILES` in
#: `scripts/check_dataarch_mirror.py` beschreibt eine Vendor-Beziehung mit vier
#: Dateien; in die gehoert ein Waechter nicht.
#:
#: Wer hier eine Klasse ergaenzt, ergaenzt sie drueben mit. Der Beleg dafuer ist
#: die Mutationsprobe in beiden Testdateien.
BEREICHE = ("core", "products", "scripts", "tooling")

AUSSCHLUSS = {".git", ".venv", "node_modules", "__pycache__", "site-packages",
              "vendor", "_archiv", "_to_delete"}

#: Die Testdatei dieses Waechters fuehrt jede Klasse als Probe im Klartext --
#: das ist ihr Zweck. Sie mitzumessen hiesse, den Nachweis als Befund zu zaehlen.
#: Wie bei einem Virenscanner, der seine eigene Testdatei nicht meldet.
EIGENE_PROBEN = ("tooling/tests/test_plattform_ratchet.py",)

#: In diesem Repo stehen nur zwei Klassen auf Null. Die anderen kamen mit
#: Bestand zur Welt -- und der wird abgetragen, nicht geraten: was eine Stelle
#: tun SOLL, weiss nur, wer ihren Zweck kennt. Bis dahin gilt die Klinke.
#: (Im Freelancing-Repo sind sechs der sieben Klassen hart; der Unterschied ist
#: der Stand der Aufraeumarbeit, nicht der Regeln.)
HARTE_KLASSEN = ("pfad_trenner", "pfad_als_esm_url")

#: `stiller_rueckfall` kam mit 14 Stellen zur Welt. Jede davon ist eine eigene
#: Entscheidung -- was der Rueckfall sagen SOLL, weiss nur, wer den Zweck der
#: Stelle kennt. Sie pauschal umzuschreiben hiesse, 14 fremde Absichten zu
#: raten. Also Klinke statt Sperre: der Bestand darf nicht wachsen.
KLINKEN_KLASSEN: tuple[str, ...] = ("nackter_programmname", "kodierung_einseitig",
                                    "trennzeichen_als_text", "zeilenende_offen",
                                    "stiller_rueckfall")

#: Programme, deren nackter Name auf Windows etwas anderes startet als gemeint.
#: `git` steht nicht dabei: es hat keinen Schatten in System32 und keine
#: `.cmd`-Huelle. Ein Waechter, der alles verbietet, wird abgeschaltet.
HEIKLE_PROGRAMME = {"bash", "sh", "npm", "npx", "make", "fab",
                    "powerbi-report-author", "pbi-tools"}


def _docstring_ids(baum) -> frozenset:
    """Die Konstanten, die als Docstring dastehen -- Prosa, keine Vorlage."""
    ids = set()
    for k in ast.walk(baum):
        if isinstance(k, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            koerper = getattr(k, "body", None)
            if (koerper and isinstance(koerper[0], ast.Expr)
                    and isinstance(koerper[0].value, ast.Constant)
                    and isinstance(koerper[0].value.value, str)):
                ids.add(id(koerper[0].value))
    return frozenset(ids)


def ist_test(pfad: pathlib.Path) -> bool:
    """Testcode schreibt in tmp_path; dort ist das Zeilenende folgenlos."""
    return (pfad.name.startswith("test_") or "tests" in pfad.parts
            or pfad.name == "conftest.py")


def dateien():
    for bereich in BEREICHE:
        wurzel = REPO_ROOT / bereich
        if not wurzel.is_dir():
            continue
        for p in sorted(wurzel.rglob("*.py")):
            if AUSSCHLUSS & set(p.parts):
                continue
            if p.relative_to(REPO_ROOT).as_posix() in EIGENE_PROBEN:
                continue
            yield p


def _erstes_wort(knoten) -> str | None:
    """Der Programmname eines subprocess-Aufrufs, falls er woertlich dasteht."""
    if isinstance(knoten, ast.List) and knoten.elts:
        knoten = knoten.elts[0]
    if isinstance(knoten, ast.Constant) and isinstance(knoten.value, str):
        teile = knoten.value.split()
        if teile:
            return teile[0]
    return None


class Sammler(ast.NodeVisitor):
    def __init__(self, rel: str, ist_test: bool = False, docstrings: frozenset = frozenset()):
        self.rel = rel
        self.ist_test = ist_test
        #: Ids der Docstring-Knoten. Ohne sie meldet dieser Waechter seine eigene
        #: Erklaerung als Fund -- die Vorlage `from '%(mod)s'` steht dort ja als
        #: Beispiel. Ein Waechter, der sich selbst anzeigt, wird abgeschaltet.
        self.docstrings = docstrings
        self.funde: list[tuple[str, int, str]] = []

    def _kw(self, knoten, name):
        return next((k for k in knoten.keywords if k.arg == name), None)

    def visit_Call(self, knoten):
        name = getattr(knoten.func, "attr", getattr(knoten.func, "id", ""))

        if name in {"run", "Popen", "call", "check_call", "check_output"}:
            wort = _erstes_wort(knoten.args[0]) if knoten.args else None
            if wort and wort in HEIKLE_PROGRAMME:
                self.funde.append(("nackter_programmname", knoten.lineno, wort))
            text = self._kw(knoten, "text") or self._kw(knoten, "universal_newlines")
            if text is not None and self._kw(knoten, "encoding") is None:
                self.funde.append(("kodierung_einseitig", knoten.lineno, "text ohne encoding"))

        if name in {"read_text", "write_text"} and self._kw(knoten, "encoding") is None:
            grenze = 0 if name == "read_text" else 1
            if len(knoten.args) <= grenze:
                self.funde.append(("kodierung_einseitig", knoten.lineno, name))

        if (name == "write_text" and not self.ist_test
                and self._kw(knoten, "newline") is None and len(knoten.args) <= 1
                and not any(k.arg is None for k in knoten.keywords)):
            self.funde.append(("zeilenende_offen", knoten.lineno, "write_text ohne newline"))

        if name == "str" and knoten.args:
            a = knoten.args[0]
            if isinstance(a, ast.Call) and getattr(a.func, "attr", "") == "relative_to":
                self.funde.append(("trennzeichen_als_text", knoten.lineno, "str(relative_to)"))

        self.generic_visit(knoten)

    def visit_Try(self, knoten):
        """Ein `except ImportError`, dessen Koerper nichts sagt.

        Geprueft wird der Koerper, nicht die Absicht: steht dort nur `pass`,
        `return`, `return None` oder eine reine Zuweisung, verschwindet der
        Pruefer ohne Spur. Ein `warnings.warn`, ein `logging`-Aufruf, ein
        `print` oder ein `raise` genuegt -- der Rueckfall ist erlaubt, das
        Schweigen nicht.
        """
        for behandler in knoten.handlers:
            typ = behandler.type
            namen = set()
            if isinstance(typ, ast.Name):
                namen = {typ.id}
            elif isinstance(typ, ast.Tuple):
                namen = {e.id for e in typ.elts if isinstance(e, ast.Name)}
            if not namen & {"ImportError", "ModuleNotFoundError"}:
                continue
            if self._sagt_etwas(behandler.body):
                continue
            self.funde.append(("stiller_rueckfall", behandler.lineno,
                               "except ImportError ohne Ansage"))
        self.generic_visit(knoten)

    @staticmethod
    def _sagt_etwas(koerper) -> bool:
        """Haelt der Rueckfall irgendetwas fest?

        Erlaubt ist viel: eine Meldung (`warn`, `log`, `print`), ein `raise`,
        ein `pytest.skip` -- und auch ein blosser Schalter (`HAVE_X = False`),
        denn der haelt den Zustand fest und wird spaeter abgefragt. Das ist der
        uebliche und ehrliche Umgang mit einer optionalen Abhaengigkeit.

        Still ist nur der Koerper, der NICHTS tut: ausschliesslich `pass`,
        `return` oder `return None`. Dann verschwindet der Pruefer spurlos, und
        ob geprueft wird, haengt am `sys.path` des Aufrufers.
        """
        for k in koerper:
            if isinstance(k, ast.Pass):
                continue
            if isinstance(k, ast.Return) and (k.value is None or (
                    isinstance(k.value, ast.Constant) and k.value.value is None)):
                continue
            return True          # irgendetwas anderes -- also nicht spurlos
        return False

    def visit_Constant(self, knoten):
        """Ein Pfad, der in eine ESM-Importzeile eingesetzt wird.

        Gesucht wird die Vorlage, nicht der Aufruf: `from '%(mod)s'` oder
        `from '{mod}'` in einem Stringliteral. Wer dort einen Pfad einsetzt,
        setzt ihn als URL ein -- und ein Windows-Pfad ist keine.
        """
        if (isinstance(knoten.value, str) and id(knoten) not in self.docstrings
                and re.search(r"from\s+['\"][%{]", knoten.value)):
            self.funde.append(("pfad_als_esm_url", knoten.lineno, "ESM-Import mit Platzhalter"))
        self.generic_visit(knoten)

    def visit_JoinedStr(self, knoten):
        """PATH-Verkettung mit hartem Doppelpunkt in einem f-String.

        Gesucht wird das Muster `{...}:` unmittelbar vor oder nach einem
        Platzhalter, in einem Ausdruck, in dem "PATH" vorkommt.
        """
        roh = ast.unparse(knoten)
        # `os.environ` als Bedingung, nicht nur "PATH": sonst faellt jede
        # Ausgabezeile mit einem Doppelpunkt hinein ("GOLDEN_PATH.md") und jeder
        # POSIX-Ausdruck, der INNERHALB einer Shell richtig ist.
        #
        # Und ausgeschrieben `os.environ`, nicht `environ`: das Teilwort steckt
        # auch in `environment`. Gemessen am 10.09.2026 beim ersten Lauf im
        # ALUCA-Repo -- fuenf Meldungen, fuenf Fehlalarme, alle aus Zeilen wie
        # `f"{relative.as_posix()}: environment does not match manifest"`.
        if "os.environ" in roh and "}:" in roh:
            self.funde.append(("pfad_trenner", knoten.lineno, "PATH mit ':' verkettet"))
        self.generic_visit(knoten)


def messen() -> tuple[collections.Counter, list[str]]:
    zaehler: collections.Counter = collections.Counter()
    zeilen: list[str] = []
    for p in dateien():
        try:
            baum = ast.parse(p.read_text(encoding="utf-8-sig"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        rel = p.relative_to(REPO_ROOT).as_posix()
        s = Sammler(rel, ist_test=ist_test(p), docstrings=_docstring_ids(baum))
        s.visit(baum)
        for klasse, zeile, detail in s.funde:
            zaehler[klasse] += 1
            zeilen.append(f"{klasse}\t{rel}:{zeile}\t{detail}")
    return zaehler, sorted(zeilen)


def vergleich(jetzt: collections.Counter, baseline: dict[str, int]):
    """Je Klasse, nie als Summe. Rein -- testbar ohne Dateisystem."""
    gestiegen, gesunken = [], []
    for klasse in sorted(set(jetzt) | set(baseline)):
        ist, soll = jetzt.get(klasse, 0), baseline.get(klasse, 0)
        if ist > soll:
            # ASCII-Pfeil mit Absicht: dieser Waechter laeuft auch dort, wo stdout
            # cp1252 ist, und ein Pruefer, der an seiner eigenen Meldung stirbt,
            # waere die Pointe der Klasse, die er pruefen soll.
            gestiegen.append(f"{klasse}: {soll} -> {ist} (+{ist - soll})")
        elif ist < soll:
            gesunken.append(f"{klasse}: {soll} -> {ist}")
    return gestiegen, gesunken


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--schreiben", action="store_true",
                    help="Baseline auf den gemessenen Stand setzen (bewusst manuell)")
    ap.add_argument("--zeigen", action="store_true", help="jede Fundstelle auflisten")
    args = ap.parse_args(argv)

    jetzt, zeilen = messen()

    if args.zeigen:
        print("\n".join(zeilen))

    if args.schreiben:
        BASELINE.write_text(json.dumps(dict(sorted(jetzt.items())), indent=2) + "\n",
                            encoding="utf-8", newline="\n")
        print(f"[check-plattform] Baseline geschrieben: {dict(sorted(jetzt.items()))}")
        return 0

    if not BASELINE.is_file():
        print(f"[check-plattform] keine Baseline unter "
              f"{BASELINE.relative_to(REPO_ROOT)} — mit --schreiben anlegen.", file=sys.stderr)
        return 1

    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))

    for klasse in HARTE_KLASSEN:
        if jetzt.get(klasse, 0) > 0:
            print(f"[check-plattform] {klasse}: {jetzt[klasse]} Stelle(n) — "
                  f"diese Klasse ist auf Null und bleibt es.", file=sys.stderr)
            for z in zeilen:
                if z.startswith(klasse):
                    print("   ", z, file=sys.stderr)
            return 1

    gestiegen, gesunken = vergleich(jetzt, baseline)
    if gestiegen:
        print("[check-plattform] Bestand gestiegen:", file=sys.stderr)
        for g in gestiegen:
            print("   ", g, file=sys.stderr)
        print("    Neue Stelle mit `--zeigen` finden, oder die Klasse dort "
              "aufloesen.", file=sys.stderr)
        return 1

    if gesunken:
        print("[check-plattform] Bestand gesunken — Baseline nachziehen "
              "(--schreiben):")
        for g in gesunken:
            print("   ", g)
    print(f"[OK] check-plattform: {dict(sorted(jetzt.items()))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
