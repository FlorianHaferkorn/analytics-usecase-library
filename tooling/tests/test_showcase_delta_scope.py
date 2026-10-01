"""
test_showcase_delta_scope.py — die Erfolgsmeldung muss ihre Grenze nennen.

Gemessener Anlass (06.08.2026): `dim_product` endete bei `ProductKey` 4996, drei
Faktentabellen referenzierten 4997-4999. `check_showcase_delta.py` meldete
**„OK - 46 tables consistent"**, und genau so wurde es gelesen: als Entwarnung fuer die
Daten. Es war eine richtige Messung auf die falsche Frage; gefunden hat den Defekt
`check_data_model.py` (ORPHAN-FK). Der Vacuum-Lauf aus PR #424 galt zunaechst als
Ursache — nachgemessen am 11.08.2026 hat er nur physisch entfernt, was der Log seit dem
05.02.2026 per `remove` verabschiedet hatte; geschrumpft ist die Dimension damals, durch
eine Ganzzahldivision im Generator. Das aendert nichts an der Lehre unten: eine
Erfolgsmeldung, die ihre Grenze nicht nennt, wird als Gesamt-Entwarnung gelesen.

Der Fix war nicht, eine zweite FK-Pruefung zu bauen — die gibt es (Tool-Reuse) —,
sondern die Erfolgsmeldung ehrlich zu machen. Gelesen wird die Zeile, nicht der
Docstring; deshalb haelt dieser Test die Zeile fest.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "check_showcase_delta.py"


def _run(root: Path = REPO) -> subprocess.CompletedProcess:
    """Die Ausgabe wird ausdruecklich als UTF-8 gelesen, nicht mit der Locale-Vorgabe.

    Ohne `encoding` nimmt `text=True` die Locale des Elternprozesses -- auf einem
    deutschen Windows cp1252. Das Kind schreibt aber UTF-8, sobald `PYTHONIOENCODING`
    gesetzt ist (was in Agenten- und CI-Umgebungen ueblich ist). Aus dem Geviertstrich
    der Erfolgsmeldung wurde dann `â€”`, und der Test fiel um -- an einer Stelle, die
    mit seiner Aussage nichts zu tun hat. Gemessen am 06.09.2026: mit gesetzter
    Variable rot, ohne sie gruen, bei unveraendertem Repository.

    Nur beim Lesen UTF-8 zu erzwingen reicht nicht -- dann faellt der umgekehrte Fall
    um (Kind schreibt cp1252, Eltern lesen UTF-8). Gemessen, nicht vermutet: erst
    festgelegt, spaeter beides gruen. Deshalb werden BEIDE Seiten festgelegt, das Kind
    ueber `PYTHONIOENCODING` in seiner Umgebung.

    Ein Test, dessen Ergebnis von der Umgebungskodierung abhaengt, misst die Umgebung
    und nicht die Zusage.
    """
    umgebung = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    return subprocess.run([sys.executable, str(SCRIPT), "--root", str(root)], cwd=REPO,
                          env=umgebung, capture_output=True, text=True, encoding="utf-8")


def _mini_gold(root: Path) -> Path:
    """Eine Delta-Tabelle mit einem aktiven `add` -- das Gate prueft nur Log gegen Platte.

    Seit D-578 (29.09.2026) liegen die Showdaten nicht mehr in Git; der Test baut sich
    seine Daten selbst, statt vom Checkout abzuhaengen.
    """
    tab = root / "showcases" / "demo" / "data" / "gold" / "facts" / "fact_x"
    (tab / "_delta_log").mkdir(parents=True)
    (tab / "_delta_log" / "00000000000000000000.json").write_text(
        '{"add": {"path": "part-0.parquet"}}\n', encoding="utf-8")
    (tab / "part-0.parquet").write_bytes(b"PAR1")
    return root


def test_the_success_message_states_what_it_does_not_cover(tmp_path):
    r = _run(_mini_gold(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    out = r.stdout
    assert "OK —" in out or "OK -" in out
    assert "NICHT geprueft" in out, "die Grenze fehlt — 'OK' liest sich dann als Entwarnung"
    assert "check_data_model.py" in out, (
        "die Meldung muss den Pruefer nennen, der die fachliche Deckung abdeckt, "
        "sonst weiss der Lesende nicht, wohin als naechstes"
    )


def test_the_fk_coverage_check_is_not_rebuilt_here():
    """Tool-Reuse, maschinell festgehalten: die FK-Deckung gehoert in
    `check_data_model.py`. Wer sie hierher kopiert, baut das zweite Silo — und zwei
    Pruefer derselben Sache driften garantiert auseinander."""
    src = SCRIPT.read_text(encoding="utf-8")
    code = "\n".join(l for l in src.splitlines() if not l.strip().startswith("#"))
    body = code.split('"""', 2)[-1]          # ohne Modul-Docstring
    assert "ORPHAN-FK" not in body
    assert "pyarrow" not in body and "read_table" not in body, (
        "dieser Gate liest keine Parquet-Inhalte — er prueft Log gegen Dateien"
    )


def test_both_gates_run_in_the_consolidated_local_check():
    """Die Grenze zu benennen hilft nur, wenn der andere Pruefer auch laeuft."""
    sh = (REPO / "tooling" / "run_local_ci_check.sh").read_text(encoding="utf-8")
    assert "check_showcase_delta.py" in sh
    assert "check_data_model.py" in sh


def test_no_tables_is_not_run_not_ok(tmp_path):
    """Ohne Showdaten ist null Tabellen kein „OK — 0 consistent", sondern Exit 2 (D-578)."""
    r = _run(tmp_path)
    assert r.returncode == 2, r.stdout + r.stderr
    assert "NICHT GELAUFEN" in r.stderr and "showdaten.py holen" in r.stderr
    assert "OK" not in r.stdout
