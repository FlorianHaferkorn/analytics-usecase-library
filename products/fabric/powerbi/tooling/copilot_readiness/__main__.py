"""CLI: generate or check the "Prep data for AI" contents of ALUCA use cases.

    python -m products.fabric.powerbi.tooling.copilot_readiness --usecase COM-001
    python -m products.fabric.powerbi.tooling.copilot_readiness --usecase COM-001 --check

Default output: ``products/fabric/powerbi/dist/copilot_readiness/<use case folder>/``
(generated, never edited by hand). ``--check`` regenerates in memory and exits 1 when the
committed files differ (stale output), without writing.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from products.fabric.powerbi.tooling.copilot_readiness.adapter import (
    AlucaSources,
    find_bracket,
    render_all,
)


def output_dir(usecase_id: str, src: AlucaSources) -> Path:
    return src.dist / "copilot_readiness" / find_bracket(usecase_id, src).parent.name


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="copilot_readiness", description=__doc__.splitlines()[0])
    parser.add_argument("--usecase", "-u", action="append", required=True,
                        help="Use case id (repeatable), e.g. COM-001")
    parser.add_argument("--output", "-o", default=None,
                        help="Output directory (single use case only). Default: dist/copilot_readiness/<folder>/")
    parser.add_argument("--check", action="store_true",
                        help="Compare committed output with a fresh render; exit 1 on difference")
    args = parser.parse_args(argv)
    if args.output and len(args.usecase) > 1:
        parser.error("--output takes a single --usecase")

    src = AlucaSources()
    stale: list[str] = []
    for uc in args.usecase:
        out = Path(args.output) if args.output else output_dir(uc, src)
        files = render_all(uc, src)
        for name, text in files.items():
            path = out / name
            data = text.encode("utf-8")
            if args.check:
                if not path.is_file() or path.read_bytes() != data:
                    stale.append(str(path))
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            print(f"[copilot-readiness] {uc}: {path} ({len(data):,} bytes)")
    if args.check:
        if stale:
            print("[copilot-readiness] STALE — regenerate (python -m products.fabric.powerbi.tooling."
                  "copilot_readiness --usecase <id>):")
            for s in stale:
                print(f"  {s}")
            return 1
        print(f"[copilot-readiness] OK — {len(args.usecase)} use case(s) up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
