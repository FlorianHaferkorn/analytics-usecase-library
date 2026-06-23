"""Tests for the target (stack) adapter contract + registry (task I-3.1, ADR-0006).

Exercises the contract only — there are no concrete adapters yet (I-3.2/I-3.3).
A throwaway in-test adapter stands in for a real stack.
"""
from __future__ import annotations

import pytest

from tooling.superversion import targets
from tooling.superversion.canonical_contract import (
    CanonicalModel,
    ReportModel,
    SemanticModel,
)
from tooling.superversion.targets.base import (
    REGISTRY,
    TargetAdapter,
    TargetContractError,
    TargetEmitter,
    available,
    get,
    register,
    render,
)


@pytest.fixture
def clean_registry():
    """Isolate REGISTRY mutations per test."""
    saved = dict(REGISTRY)
    REGISTRY.clear()
    try:
        yield
    finally:
        REGISTRY.clear()
        REGISTRY.update(saved)


@pytest.fixture
def model() -> CanonicalModel:
    return CanonicalModel(semantic=SemanticModel(name="X"), report=ReportModel(name="X"))


def _dummy_emit(canonical: CanonicalModel) -> dict[str, str]:
    return {
        "model.txt": f"name={canonical.semantic.name}\n",
        "report/pages.txt": f"pages={len(canonical.report.pages)}\n",
    }


def test_package_reexports_contract():
    # the package surfaces the contract directly (not only via base submodule)
    assert targets.render is render
    assert targets.TargetAdapter is TargetAdapter
    assert targets.base.render is render


def test_register_get_available(clean_registry):
    a = register(TargetAdapter(id="dummy", label="Dummy", fmt="txt", emit=_dummy_emit))
    assert get("dummy") is a
    assert available() == ["dummy"]


def test_register_rejects_empty_id(clean_registry):
    with pytest.raises(TargetContractError):
        register(TargetAdapter(id="", label="x", fmt="txt", emit=_dummy_emit))


def test_register_collision_raises_unless_replace(clean_registry):
    register(TargetAdapter(id="dup", label="A", fmt="txt", emit=_dummy_emit))
    with pytest.raises(TargetContractError):
        register(TargetAdapter(id="dup", label="B", fmt="txt", emit=_dummy_emit))
    # explicit override is allowed
    b = register(TargetAdapter(id="dup", label="B", fmt="txt", emit=_dummy_emit), replace=True)
    assert get("dup") is b


def test_get_unknown_stack_raises(clean_registry):
    with pytest.raises(KeyError):
        get("nope")


def test_render_rejects_path_escape(clean_registry, model, tmp_path):
    register(TargetAdapter(id="esc", label="Esc", fmt="txt",
                           emit=lambda c: {"../escape.txt": "x"}))
    with pytest.raises(TargetContractError):
        render("esc", model, tmp_path)
    register(TargetAdapter(id="abs", label="Abs", fmt="txt",
                           emit=lambda c: {"/etc/x.txt": "x"}), replace=True)
    with pytest.raises(TargetContractError):
        render("abs", model, tmp_path)


def test_render_writes_emitted_files(clean_registry, model, tmp_path):
    register(TargetAdapter(id="dummy", label="Dummy", fmt="txt", emit=_dummy_emit))
    written = render("dummy", model, tmp_path)
    assert {p.relative_to(tmp_path).as_posix() for p in written} == {"model.txt", "report/pages.txt"}
    assert (tmp_path / "model.txt").read_text(encoding="utf-8") == "name=X\n"
    assert (tmp_path / "report" / "pages.txt").read_text(encoding="utf-8") == "pages=0\n"


def test_render_is_deterministic(clean_registry, model, tmp_path):
    register(TargetAdapter(id="dummy", label="Dummy", fmt="txt", emit=_dummy_emit))
    a = {p.read_text(encoding="utf-8") for p in render("dummy", model, tmp_path / "a")}
    b = {p.read_text(encoding="utf-8") for p in render("dummy", model, tmp_path / "b")}
    assert a == b


def test_render_rejects_non_dict_emit(clean_registry, model, tmp_path):
    register(TargetAdapter(id="bad", label="Bad", fmt="txt", emit=lambda c: ["not", "a", "dict"]))
    with pytest.raises(TargetContractError):
        render("bad", model, tmp_path)


def test_render_rejects_non_str_content(clean_registry, model, tmp_path):
    register(TargetAdapter(id="bad", label="Bad", fmt="txt", emit=lambda c: {"f.txt": 123}))
    with pytest.raises(TargetContractError):
        render("bad", model, tmp_path)


def test_emitter_protocol_runtime_checkable():
    assert isinstance(_dummy_emit, TargetEmitter)


def test_registry_starts_empty_at_import():
    """I-3.1 ships the contract only — base.py registers NO concrete adapters at
    import (those arrive in I-3.2/I-3.3). Verified in a fresh interpreter so other
    tests' registrations can't mask a regression."""
    import subprocess
    import sys
    from pathlib import Path

    repo = Path(__file__).resolve().parents[3]
    code = (
        "from tooling.superversion.targets.base import REGISTRY;"
        "print(len(REGISTRY))"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], cwd=repo, capture_output=True, text=True,
    )
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "0", f"base.py registered adapters at import: {out.stdout!r}"
