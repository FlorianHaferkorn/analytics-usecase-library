#!/usr/bin/env python3
"""Gegenprobe fuer mechanische Massenaenderungen (`Sweep`).

WOZU
====
Ein Sweep aendert dreistellig viele Dateien auf einen Schlag. Ein Diff dieser
Groesse liest niemand Zeile fuer Zeile -- und genau darin liegt das Risiko:
eine fremde Aenderung, die mitgenommen wurde, oder eine Stelle, an der das
Werkzeug etwas anderes getan hat als angekuendigt, faellt in 300 Dateien nicht
auf. Am 09.09.2026 war beides der Fall: der Sweep lief in ein Submodul hinein,
und `encoding` + `newline` in EINEM Durchgang einzufuegen verschob die zweite
Einfuegung um die Laenge der ersten.

Die Antwort darauf ist nicht sorgfaeltigeres Lesen, sondern eine Zusicherung:
**jede** geaenderte Datei muss sich aus ihrer Ausgangsfassung durch genau die
angekuendigten Regeln reproduzieren lassen. Was sich nicht reproduziert, ist
entweder Handarbeit (dann muss sie benannt werden koennen) oder ein Fehler.

Dies ist ein Werkzeug, kein Test. Ein Test waere falsch: er wuerde jede normale
Aenderung an einer .py-Datei zum Regelverstoss erklaeren. Aufgerufen wird es
einmal je Sweep, vor dem Commit.

VERWENDUNG
==========
    python scripts/pruefe_sweep.py                 # Arbeitsbaum gegen HEAD
    python scripts/pruefe_sweep.py --basis HEAD~1  # gegen einen anderen Stand
    python scripts/pruefe_sweep.py --ausnahme scripts/check_plattform.py

Der Vergleich laeuft zweistufig: erst zeichenweise, dann ueber den Syntaxbaum.
Die zweite Stufe faengt genau eine Sache ab -- nachtraegliches Ausrichten der
eingefuegten Fortsetzungszeilen, das am Baum nichts aendert.
"""
from __future__ import annotations

import argparse
import ast
import pathlib
import re
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
LAUF = {"run", "Popen", "call", "check_call", "check_output"}


def ist_test(rel: str) -> bool:
    p = pathlib.PurePosixPath(rel)
    return p.name.startswith("test_") or "tests" in p.parts or p.name == "conftest.py"


def _pos(z: list[str], lineno: int, col: int) -> int:
    """Byte-Spalte des Parsers in eine Zeichen-Position umrechnen."""
    return sum(len(x) + 1 for x in z[:lineno - 1]) + len(
        z[lineno - 1].encode("utf-8")[:col].decode("utf-8", "ignore"))


def _hat_komma(q: str, node: ast.Call) -> bool:
    """Steht zwischen letztem Argument und Klammer schon ein Komma?

    Nur dort suchen, nicht rueckwaerts ab der Klammer: ein Komma in einem
    Kommentar dazwischen hat den Einfueger einmal zu `, ,` verleitet.
    """
    letzte = list(node.args) + [k.value for k in node.keywords]
    if not letzte:
        return False
    ende = max((x.end_lineno, x.end_col_offset) for x in letzte)
    z = q.split("\n")
    a, b = _pos(z, ende[0], ende[1]), _pos(z, node.end_lineno, node.end_col_offset) - 1
    return "," in "\n".join(re.sub(r"#.*$", "", x) for x in q[a:b].split("\n"))


def kand_encoding(baum: ast.AST, _ist_test: bool) -> list[tuple[ast.Call, str]]:
    """Regel 1: `encoding` (und bei Prozessen `errors`) nachtragen."""
    tr: list[tuple[ast.Call, str]] = []
    for n in ast.walk(baum):
        if not isinstance(n, ast.Call) or any(k.arg is None for k in n.keywords):
            continue
        name = getattr(n.func, "attr", getattr(n.func, "id", ""))
        kw = {k.arg for k in n.keywords}
        if name in {"read_text", "write_text"} and "encoding" not in kw:
            if len(n.args) <= (0 if name == "read_text" else 1):
                tr.append((n, 'encoding="utf-8"'))
        elif (name in LAUF and "encoding" not in kw
              and ("text" in kw or "universal_newlines" in kw)):
            t = 'encoding="utf-8"'
            if "errors" not in kw:
                t += ', errors="replace"'
            tr.append((n, t))
    return tr


def kand_newline(baum: ast.AST, ist_test_datei: bool) -> list[tuple[ast.Call, str]]:
    """Regel 2: `newline="\\n"` beim Schreiben -- ausser in Testdateien.

    Getrennter Durchgang mit frischem Baum, nicht zusammen mit Regel 1: bei
    einem `write_text` ohne beides haetten beide Einfuegungen dieselbe
    `end_col_offset`, und nach der ersten stimmt die zweite nicht mehr.
    """
    if ist_test_datei:
        return []
    return [(n, 'newline="\\n"') for n in ast.walk(baum)
            if isinstance(n, ast.Call) and getattr(n.func, "attr", None) == "write_text"
            and not any(k.arg == "newline" for k in n.keywords)
            and not any(k.arg is None for k in n.keywords) and len(n.args) <= 1]


def einfuegen(q: str, paare: list[tuple[ast.Call, str]]) -> str:
    """Von hinten nach vorn einfuegen, damit fruehere Positionen gueltig bleiben."""
    z = q.split("\n")
    for lineno, col, node, text in sorted(
            ((n.end_lineno, n.end_col_offset, n, t) for n, t in paare), reverse=True):
        roh = z[lineno - 1].encode("utf-8")
        assert roh[col - 1:col] == b")", (lineno, col)
        leer = not node.args and not node.keywords
        zus = text if leer else ((" " + text) if _hat_komma(q, node) else (", " + text))
        z[lineno - 1] = roh[:col - 1].decode("utf-8") + zus + roh[col - 1:].decode("utf-8")
    return "\n".join(z)


def posix(q: str) -> str:
    """Regel 3: `str(x.relative_to(y))` -> `x.relative_to(y).as_posix()`.

    Achtung, die Regel sieht nur Ausdruecke: eine zweite Seite desselben
    Vergleichs, die den Pfad ueber eine Zwischenvariable fuehrt, bleibt stehen.
    Genau das hat am 10.09.2026 eine Test-Symmetrie zerbrochen.
    """
    nodes = [n for n in ast.walk(ast.parse(q))
             if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "str"
             and len(n.args) == 1 and not n.keywords
             and isinstance(n.args[0], ast.Call)
             and getattr(n.args[0].func, "attr", "") == "relative_to"]
    if not nodes:
        return q
    z = q.split("\n")
    st = sorted(((_pos(z, n.lineno, n.col_offset),
                  _pos(z, n.args[0].lineno, n.args[0].col_offset),
                  _pos(z, n.end_lineno, n.end_col_offset)) for n in nodes), reverse=True)
    for a, i, e in st:
        q = q[:a] + q[i:e - 1] + ".as_posix()" + q[e:]
    return q


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--basis", default="HEAD",
                    help="Stand, aus dem reproduziert wird (Vorgabe: HEAD)")
    ap.add_argument("--ausnahme", action="append", default=[],
                    help="Datei, die bewusst Handarbeit ist (mehrfach erlaubt)")
    args = ap.parse_args(argv)

    geaendert = subprocess.run(["git", "diff", "--name-only", args.basis],
                               cwd=REPO_ROOT, capture_output=True, text=True,
                               encoding="utf-8", errors="replace").stdout.split()
    ausnahmen = set(args.ausnahme)
    wortgleich, nur_form, abweichend, andere = 0, [], [], []

    for rel in geaendert:
        if rel in ausnahmen:
            continue
        if not rel.endswith(".py"):
            andere.append(rel)
            continue
        head = subprocess.run(["git", "show", f"{args.basis}:{rel}"], cwd=REPO_ROOT,
                              capture_output=True).stdout.decode("utf-8-sig")
        pfad = REPO_ROOT / rel
        if not pfad.is_file():
            abweichend.append(f"{rel} (geloescht)")
            continue
        jetzt = pfad.read_text(encoding="utf-8-sig")
        q = head
        try:
            for kand in (kand_encoding, kand_newline):
                paare = kand(ast.parse(q), ist_test(rel))
                if paare:
                    q = einfuegen(q, paare)
            q = posix(q)
        except Exception as e:
            abweichend.append(f"{rel}: {type(e).__name__}")
            continue
        if q.replace("\r\n", "\n") == jetzt.replace("\r\n", "\n"):
            wortgleich += 1
        elif _baum_gleich(q, jetzt):
            nur_form.append(rel)
        else:
            abweichend.append(rel)
    return _bericht(args, wortgleich, nur_form, abweichend, andere, ausnahmen)


def _baum_gleich(a: str, b: str) -> bool:
    try:
        return ast.dump(ast.parse(a)) == ast.dump(ast.parse(b))
    except SyntaxError:
        return False


def _bericht(args, wortgleich, nur_form, abweichend, andere, ausnahmen) -> int:
    gesamt = wortgleich + len(nur_form) + len(abweichend)
    # ASCII mit Absicht: dieser Bericht laeuft auch dort, wo stdout cp1252 ist.
    print(f"[pruefe-sweep] Basis {args.basis}: {gesamt} Python-Dateien geprueft")
    print(f"    wortgleich reproduziert: {wortgleich}")
    print(f"    nur Einrueckung:         {len(nur_form)}")
    print(f"    benannte Handarbeit:     {len(ausnahmen)}")
    if andere:
        print(f"    nicht geprueft (keine .py): {len(andere)}")
        for a in sorted(andere)[:10]:
            print("       ", a)
    if not abweichend:
        print("[OK] pruefe-sweep: jede geaenderte Datei reproduziert sich.")
        return 0
    print(f"[pruefe-sweep] {len(abweichend)} Datei(en) reproduzieren sich NICHT:",
          file=sys.stderr)
    for a in abweichend:
        print("   ", a, file=sys.stderr)
    print("    Entweder Handarbeit -- dann mit --ausnahme benennen -- oder ein "
          "Fehler des Werkzeugs.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
