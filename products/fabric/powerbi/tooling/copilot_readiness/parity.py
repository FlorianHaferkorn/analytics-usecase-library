"""Format signature of the three "Prep data for AI" contents (parity with Meridian, D-579).

A signature is what a consumer of the files relies on, not their content: the key paths of both
JSON files and the section headings of both instruction variants. ALUCA's output must carry the
same signature as a real Meridian run; the reference lives in
``products/fabric/powerbi/tooling/tests/fixtures/copilot_readiness/meridian_format.json``.

Refresh the reference after ``check_dataarch_mirror.py --write-copilot`` (the test ties it to
the PIN's ``source_commit``)::

    # in the Freelancing checkout, at the mirrored commit
    python3 -m products.meridian_copilot_readiness --core meridian/organisations/aurora/core -o <dir>
    # in ALUCA
    python -m products.fabric.powerbi.tooling.copilot_readiness.parity <dir> --commit <sha> > <fixture>
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

JSON_FILES = ("verified_answer_candidates.json", "ai_data_schema.json")
_TXT_HEADING = re.compile(r"^[A-ZÄÖÜ][A-ZÄÖÜ ()\-—]+$")


def key_paths(value: object, prefix: str = "") -> set[str]:
    """Every key path in a JSON value; list items share ``[]`` (union over all items)."""
    out: set[str] = set()
    if isinstance(value, dict):
        for k, v in value.items():
            path = f"{prefix}.{k}" if prefix else k
            out.add(path)
            out |= key_paths(v, path)
    elif isinstance(value, list):
        for item in value:
            out |= key_paths(item, f"{prefix}[]")
    return out


def md_sections(text: str) -> list[str]:
    return [ln[3:] for ln in text.splitlines() if ln.startswith("## ")]


def txt_sections(text: str) -> list[str]:
    lines = text.splitlines()
    # Line 0 is the title, line 1 the provenance; sections follow a blank line.
    return [ln for i, ln in enumerate(lines) if i > 1 and _TXT_HEADING.match(ln) and lines[i - 1] == ""]


def signature(files: dict[str, str]) -> dict:
    return {
        "json_key_paths": {name: sorted(key_paths(json.loads(files[name]))) for name in JSON_FILES},
        "md_sections": md_sections(files["ai_instructions.md"]),
        "txt_sections": txt_sections(files["ai_instructions.txt"]),
    }


def read_dir(directory: Path) -> dict[str, str]:
    names = JSON_FILES + ("ai_instructions.md", "ai_instructions.txt")
    return {n: (directory / n).read_text(encoding="utf-8") for n in names}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print the format signature of a Meridian output dir")
    parser.add_argument("directory")
    parser.add_argument("--commit", required=True, help="Meridian commit the output was generated at")
    args = parser.parse_args(argv)
    sig = signature(read_dir(Path(args.directory)))
    doc = {"_source": "Meridian products.meridian_copilot_readiness, Aurora core, fresh CLI run",
           "source_commit": args.commit, **sig}
    sys.stdout.write(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
