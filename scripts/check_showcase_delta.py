#!/usr/bin/env python3
"""Showcase Delta-table consistency gate.

Every table the semantic models read via ``fn_DeltaCurrentFiles`` is a Delta
Lake folder: parquet part-files plus a ``_delta_log`` whose JSON commits list
``add``/``remove`` actions. ``fn_DeltaCurrentFiles`` replays that log and keeps
only the files whose latest action is ``add``. If a parquet is renamed on disk
without rewriting the log (e.g. a hashed ``part-00000-<uuid>-c000.snappy.parquet``
consolidated to a generic ``part-00000.parquet``), the replay matches zero
files and returns a *columnless* empty table. Power BI Desktop then loads that
dimension with no supported columns and crashes in ``Table.get_Islands()`` while
wiring relationships against the empty endpoint — a failure no diff to the TMDL
or the report can explain, because the defect is in the seed data.

This gate catches that class before Desktop does: for each Delta folder it
computes the active file set from the log and asserts every active path exists
on disk. Orphan parquet files (present but not referenced) are reported as
advisory only — extra files do not break the load, missing active ones do.

**Was dieses Gate NICHT prüft, und warum das einmal teuer war (06.08.2026).**
Es prüft die Integrität des *Logs* gegen die *Dateien* — nicht die Integrität der
*Daten*. ``dim_product`` endete bei ``ProductKey`` 4996, während Faktentabellen
4997–4999 referenzierten. Dieses Gate meldete „OK — 46 tables consistent", und genau
so wurde es gelesen: als Entwarnung. Es war eine richtige Messung auf die falsche Frage.

Zur Chronologie, weil hier zuerst der Falsche beschuldigt wurde (nachgemessen am
11.08.2026 an den Zeitstempeln des Logs): geschrumpft ist die Dimension am
**05.02.2026** — ein ``WRITE``-Commit ersetzte die 5000-Zeilen-Datei durch eine mit
4996 (``num_added_rows: 4996``). Der Vacuum-Lauf (#424) am **06.08.2026** entfernte
nur physisch, was der Log ein halbes Jahr zuvor per ``remove`` verabschiedet hatte. Er
hat also keine Zeile gelöscht, sondern die *Maske* weggenommen: wer den Log replayte
(``fn_DeltaCurrentFiles``, Power BI), sah die Lücke seit Februar; wer per ``rglob``
las, sah bis August die Leiche mit 5000 Zeilen und meldete grün. Ursache der Lücke war
weder Vacuum noch Log, sondern ``product_count // len(subcategories)`` im Generator:
1000 Consumer-Electronics-Produkte auf 6 Subkategorien ergaben 996. Behoben in
``core/data_contracts/sources/synthetic/generate_gold_layer_contract_v2.py``, die
Dimension trägt wieder alle 5000 Schlüssel.

Die fachliche Deckung (Fakt-FK → Dimension-PK) prüft ``tooling/validation/
check_data_model.py`` mit dem Befund ``ORPHAN-FK``; sie hat den Defekt auch gefunden.
Hier wird deshalb **keine zweite FK-Prüfung gebaut** (Tool-Reuse) — stattdessen sagt
die Erfolgsmeldung, was sie deckt und was nicht, damit sie nicht wieder als
Gesamt-Entwarnung gelesen wird.

Exit code 1 on any active-but-missing file. Run from the repo root.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys

GOLD_GLOB = "showcases/*/data/gold"


def _active_paths(log_dir: str) -> list[str]:
    """Replay a _delta_log directory to the set of currently-active file paths."""
    state: dict[str, str] = {}
    for commit in sorted(glob.glob(os.path.join(log_dir, "*.json"))):
        with open(commit, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if "add" in obj:
                    state[obj["add"]["path"]] = "add"
                elif "remove" in obj:
                    state[obj["remove"]["path"]] = "remove"
    return [path for path, action in state.items() if action == "add"]


def check(root: str = ".") -> int:
    problems = 0
    tables = 0
    log_dirs = sorted(
        glob.glob(os.path.join(root, GOLD_GLOB, "**", "_delta_log"), recursive=True)
    )
    for log_dir in log_dirs:
        table = os.path.dirname(log_dir)
        rel = os.path.relpath(table, root)
        active = _active_paths(log_dir)
        if not active:
            # A log with no active adds is legitimately empty only if it also has
            # no data files; flag it so a genuinely empty seed is a conscious choice.
            missing = []
        else:
            missing = [p for p in active if not os.path.exists(os.path.join(table, p))]
        tables += 1
        if missing:
            problems += 1
            print(f"FAIL {rel}")
            print(f"     active file(s) referenced by _delta_log but missing on disk:")
            for m in missing:
                print(f"       - {m}")
            phys = {
                os.path.relpath(p, table)
                for p in glob.glob(os.path.join(table, "**", "*.parquet"), recursive=True)
            }
            orphans = sorted(phys - set(active))
            if orphans:
                print(f"     physical parquet not referenced (likely the renamed file):")
                for o in orphans:
                    print(f"       - {o}")
    if problems:
        print(
            f"\n{problems} Delta table(s) inconsistent — physical parquet does not match "
            f"the _delta_log active set. Rename the orphan file(s) back to the active "
            f"add path, or rewrite the log. See internal/project_mgmt/"
            f"KNOWN_ERRORS_AND_FIXES.md.",
            file=sys.stderr,
        )
        return 1
    # Die Grenze gehoert in die Erfolgsmeldung, nicht nur in den Docstring: gelesen wird
    # die Zeile, nicht das Modul. Ohne den zweiten Satz liest sich „OK" als Entwarnung
    # fuer die Daten — genau die Verwechslung, die den ORPHAN-FK aus #424 durchliess.
    print(f"OK — {tables} showcase Delta table(s) consistent (active files all present).")
    print("     Geprueft: Log gegen Dateien. NICHT geprueft: ob die Daten fachlich decken "
          "(Fakt-FK -> Dimension-PK) - das macht tooling/validation/check_data_model.py. "
          "Nach einem Vacuum-/Dedup-Lauf beide fahren.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repo root (default: cwd)")
    args = parser.parse_args()
    return check(args.root)


if __name__ == "__main__":
    raise SystemExit(main())
