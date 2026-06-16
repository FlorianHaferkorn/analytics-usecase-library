#!/usr/bin/env python3
"""ALUCA — Analytics Library of Use Cases.

Top-level command-line entry point. Delegates to the generator core
(compile, preflight, score, telemetry, kb).

Invoke it as the installed console script::

    aluca compile --bracket <path>

or, without installation, from the repository root::

    python -m aluca compile --bracket <path>

Run from the repository root so that the default ``core/`` and ``products/``
paths resolve correctly.
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    """Run the ALUCA CLI and return its process exit code."""
    # Ensure the repository root (this file's directory) is importable so the
    # path-based ``tooling.*`` packages resolve when ALUCA is invoked as an
    # installed console script rather than via ``python -m`` from the root.
    repo_root = Path(__file__).resolve().parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from tooling.generator_core.__main__ import main as _generator_main

    return _generator_main()


if __name__ == "__main__":
    raise SystemExit(main())
