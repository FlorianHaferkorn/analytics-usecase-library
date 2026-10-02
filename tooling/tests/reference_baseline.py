"""Released synthetic reference baseline for tests: built once per option set, copied per test.

Building and releasing the baseline costs about four seconds; the commercial, price-delta and
staffing tests need it in almost every test. The first call per option set builds a template in
a temporary directory, every call copies it into the caller's own directory, so tests stay
isolated (a test may write into its copy) while the build runs once per worker.
"""
from __future__ import annotations

import atexit
import shutil
import tempfile
from pathlib import Path

from tooling.superversion.project_package import alternative_impact as impact
from tooling.superversion.project_package.repository import ProjectPackageRevisionRepository

SCHEMAS = Path(__file__).resolve().parents[2] / "tooling/generator/schemas"
_TEMPLATES: dict[tuple, tuple[Path, str]] = {}


def reference_baseline(target: Path, **options) -> tuple[ProjectPackageRevisionRepository, str]:
    """Same result as ``build_reference_baseline(target, SCHEMAS, **options)`` for the reference project."""
    if {"project_ref", "repository_root"} & set(options):
        raise ValueError("Cached reference baselines use the reference project in their own directory")
    key = tuple(sorted((name, tuple(value) if isinstance(value, list) else value) for name, value in options.items()))
    if key not in _TEMPLATES:
        root = Path(tempfile.mkdtemp(prefix="aul-reference-"))
        atexit.register(shutil.rmtree, root, True)
        _repository, revision = impact.build_reference_baseline(root / "work", SCHEMAS, **options)
        _TEMPLATES[key] = (root / "work", revision)
    template, revision = _TEMPLATES[key]
    shutil.copytree(template, target)
    return ProjectPackageRevisionRepository(target / "repositories" / impact.REFERENCE_PROJECT, SCHEMAS), revision
