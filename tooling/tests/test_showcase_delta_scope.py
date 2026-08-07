"""
test_showcase_delta_scope.py — die Erfolgsmeldung muss ihre Grenze nennen.

Gemessener Anlass (06.08.2026): der Vacuum-Lauf in PR #424 entfernte eine parquet-Datei
mit echten Dimensionszeilen und schrieb den Delta-Log konsistent nach. `dim_product`
endet seither bei `ProductKey` 4996, drei Faktentabellen referenzieren 4997-4999.
`check_showcase_delta.py` meldete danach **„OK - 46 tables consistent"**, und genau so
wurde es gelesen: als Entwarnung fuer die Daten. Es war eine richtige Messung auf die
falsche Frage; gefunden hat den Defekt `check_data_model.py` (ORPHAN-FK).

Der Fix war nicht, eine zweite FK-Pruefung zu bauen — die gibt es (Tool-Reuse) —,
sondern die Erfolgsmeldung ehrlich zu machen. Gelesen wird die Zeile, nicht der
Docstring; deshalb haelt dieser Test die Zeile fest.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "check_showcase_delta.py"


def _run() -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT)], cwd=REPO,
                          capture_output=True, text=True)


def test_the_success_message_states_what_it_does_not_cover():
    r = _run()
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
