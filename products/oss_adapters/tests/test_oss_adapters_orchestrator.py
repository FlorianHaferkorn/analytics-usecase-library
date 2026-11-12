"""The OSS adapter orchestrator runs as documented in AGENTS.md.

Until 12.11.2026 the documented call broke before doing anything
(`ModuleNotFoundError: No module named 'tooling'`), and the adapter imports pointed to a
package that does not exist (`products.oss.tooling.adapters`). Nobody noticed because no test
ran it. These tests run the documented command line and import every adapter by the path the
orchestrator and `tooling/generator_core/__main__.py` use.
"""
from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _ROOT / "products" / "oss_adapters" / "orchestrator" / "orchestrate_oss.py"
_BRACKET = _ROOT / "core" / "usecases" / "core" / "COM-001_Sales_Performance" / "UseCase_Bracket.yaml"
_ADAPTERS = {
    "metabase": ("MetabaseAdapter", "dashboard.json"),
    "grafana": ("GrafanaAdapter", "dashboard.json"),
    "superset": ("SupersetAdapter", "dashboard_export.zip"),
}


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(_SCRIPT), *args], cwd=_ROOT,
                          capture_output=True, text=True, encoding="utf-8", timeout=300)


@pytest.mark.parametrize("name", sorted(_ADAPTERS))
def test_adapter_imports_by_documented_path(name):
    cls_name, _ = _ADAPTERS[name]
    module = importlib.import_module(f"products.oss_adapters.tooling.adapters.{name}")
    assert hasattr(module, cls_name)


def test_documented_dry_run_call_works():
    res = _run("--bracket", str(_BRACKET), "--adapter", "metabase", "--dry-run")
    assert res.returncode == 0, res.stderr
    assert "[dry-run] COM-001" in res.stdout


@pytest.mark.parametrize("name", sorted(_ADAPTERS))
def test_render_writes_the_adapter_output(name, tmp_path):
    _, expected_file = _ADAPTERS[name]
    res = _run("--bracket", str(_BRACKET), "--adapter", name, "--skip-preflight",
               "--output", str(tmp_path))
    assert res.returncode == 0, res.stderr
    assert (tmp_path / expected_file).is_file(), sorted(p.name for p in tmp_path.iterdir())
