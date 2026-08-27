"""answers_cli — apply an answered sheet back onto the inputs, with a diff and a release.

    python -m tooling.superversion.answers_cli \
        --answers answers.json --inputs inputs.json --dest out/

Without ``--release`` nothing is written except the diff (`_ANSWERS.md` under ``--dest``).
That is the point: the diff is read first, and the same text is emitted again after the
write, so before and after can be compared without re-reading both files.

With ``--release`` the inputs file is rewritten whole, sorted and indented, not patched in
place. That is deliberate — a deterministic file is diffable against the next run — but it
means hand formatting and comments in the inputs do not survive the first application.

Exit codes: 0 nothing blocked · 1 blocked answers (nothing written) · 2 the answer document
is not one.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from tooling.superversion.answers import (
    AnswerError,
    answers_markdown,
    plan_answers,
    write_decisions,
    write_inputs,
)
from tooling.superversion.architecture_blueprint import derive_blueprint
from tooling.superversion.open_questions import collect_open_questions

REPORT_PATH = "_ANSWERS.md"
DECISIONS_PATH = "decisions.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply answered open questions to the inputs")
    parser.add_argument("--answers", type=Path, required=True,
                        help="JSON: aluca/open-question-answers/v1")
    parser.add_argument("--inputs", type=Path, required=True,
                        help="JSON: derive_blueprint inputs — written only with --release")
    parser.add_argument("--dest", type=Path, required=True, help="output directory")
    parser.add_argument("--release", action="store_true",
                        help="actually write. Without it this is a dry run.")
    args = parser.parse_args(argv)

    inputs = json.loads(args.inputs.read_text(encoding="utf-8"))
    doc = json.loads(args.answers.read_text(encoding="utf-8"))
    ledger = collect_open_questions(inputs, derive_blueprint(inputs))
    try:
        plan = plan_answers(doc, ledger, inputs)
    except ValueError as exc:
        print(f"error: {exc}")
        return 2

    args.dest.mkdir(parents=True, exist_ok=True)
    (args.dest / REPORT_PATH).write_text(
        answers_markdown(plan, released=False), encoding="utf-8")

    s = plan["summary"]
    print(f"{s['answers']} answers: {s['applies']} change an input, {s['already']} already "
          f"in place, {s['records']} recorded, {s['structural']} need a new input document, "
          f"{s['blockers']} blocked")
    for b in plan["blockers"]:
        scope = f" · {b['scope']}" if b.get("scope") else ""
        print(f"  blocked: {b['id']}{scope} — {b['reason']}")
    if plan["blockers"]:
        print(f"nothing written. diff: {args.dest / REPORT_PATH}")
        return 1
    if not args.release:
        print(f"dry run. diff: {args.dest / REPORT_PATH} — re-run with --release to write")
        return 0

    try:
        written = write_inputs(args.inputs, plan, release=True)
        recorded = write_decisions(args.dest / DECISIONS_PATH, plan, release=True)
    except AnswerError as exc:  # pragma: no cover - the blockers above already returned
        print(f"error: {exc}")
        return 1
    (args.dest / REPORT_PATH).write_text(
        answers_markdown(plan, released=True), encoding="utf-8")
    for line in written:
        print(f"  written: {line}")
    if recorded:
        print(f"  recorded in {DECISIONS_PATH}: {', '.join(recorded)}")
    print(f"inputs updated: {args.inputs}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
