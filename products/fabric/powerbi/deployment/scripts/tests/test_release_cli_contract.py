"""The deploy.ps1 → fabric_release.py CLI contract, pinned.

`deploy.ps1` passed `--workspace_id`, `--domain_filter` and `--dry_run`, none of which
existed in `fabric_release.py`'s argparse — so every live deploy died with argparse exit 2
before publishing anything, and the SP credentials were handed over under `AZURE_*` names
while the Python side only read `TENANT_ID`/`CLIENT_ID`/`CLIENT_SECRET`.

These tests read both files as text and compare them, so the two sides cannot drift apart
again. They deliberately do NOT import `fabric_release` (it pulls in fabric_cicd and
azure-identity, which are deployment-only dependencies).
"""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parents[1]
_RELEASE_PY = _SCRIPTS / "fabric_release.py"
_DEPLOY_PS1 = _SCRIPTS.parents[1] / "orchestrator" / "deploy.ps1"


def _release_source() -> str:
    return _RELEASE_PY.read_text(encoding="utf-8")


def _declared_flags() -> set[str]:
    """Every `--flag` registered via parser.add_argument in fabric_release.py."""
    tree = ast.parse(_release_source())
    flags: set[str] = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_argument"):
            for arg in node.args:
                if isinstance(arg, ast.Constant) and str(arg.value).startswith("--"):
                    flags.add(arg.value)
    return flags


def _flags_passed_by_deploy_ps1() -> set[str]:
    """Every `--flag` literal that deploy.ps1 appends to its python argument list."""
    return set(re.findall(r'"(--[a-z_][a-z0-9_-]*)"', _DEPLOY_PS1.read_text(encoding="utf-8")))


# -- the contract -----------------------------------------------------------------


def test_every_flag_deploy_ps1_passes_is_declared():
    missing = sorted(_flags_passed_by_deploy_ps1() - _declared_flags())
    assert not missing, (
        f"deploy.ps1 passes flags fabric_release.py does not declare: {missing} — "
        f"argparse exits 2 and nothing is published"
    )


def test_declared_flags_cover_the_three_that_were_missing():
    flags = _declared_flags()
    for flag in ("--workspace_id", "--domain_filter", "--dry_run"):
        assert flag in flags


def test_azure_credential_env_aliases_are_accepted():
    """deploy.ps1 exports AZURE_*; the Python side must read those too."""
    src = _release_source()
    for var in ("AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET"):
        assert var in src, f"{var} (set by deploy.ps1) is never read"


def test_environment_values_deploy_ps1_can_send_are_valid_choices():
    """`--environment` is a `choices=` argument: a value deploy.ps1 can pass but argparse
    rejects would be the same class of failure as an unknown flag."""
    src = _release_source()
    choices = re.search(r'"--environment".*?choices=\[(.*?)\]', src, re.S)
    assert choices, "--environment no longer declares choices"
    allowed = {c.strip().strip('"\'') for c in choices.group(1).split(",")}
    # deploy.ps1's default; the other two are its documented usage examples.
    assert {"dev", "tst", "prd"} <= allowed


# -- domain resolution -------------------------------------------------------------


def _items_for_domain(repo_dir: Path, domain: str) -> list[str]:
    """Load just `items_for_domain` from the module source, without its heavy imports."""
    tree = ast.parse(_release_source())
    fn = next(n for n in tree.body
              if isinstance(n, ast.FunctionDef) and n.name == "items_for_domain")
    ns: dict = {"Path": Path, "json": json}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), "<items_for_domain>", "exec"), ns)
    return ns["items_for_domain"](str(repo_dir), domain)


def _make_report(root: Path, name: str, model_folder: str | None) -> None:
    d = root / f"{name}.Report"
    d.mkdir(parents=True)
    if model_folder is None:
        return
    (d / "definition.pbir").write_text(json.dumps({
        "datasetReference": {"byPath": {"path": f"../{model_folder}"}}
    }), encoding="utf-8")


@pytest.fixture()
def dist(tmp_path: Path) -> Path:
    root = tmp_path / "dist"
    (root / "Commercial.SemanticModel").mkdir(parents=True)
    (root / "Finance.SemanticModel").mkdir(parents=True)
    _make_report(root, "COM-001_Sales", "Commercial.SemanticModel")
    _make_report(root, "COM-002_Margin", "Commercial.SemanticModel")
    _make_report(root, "FIN-001_Cash", "Finance.SemanticModel")
    return root


def test_domain_resolution_follows_the_binding_not_the_name_prefix(dist: Path):
    assert _items_for_domain(dist, "Commercial") == [
        "COM-001_Sales.Report", "COM-002_Margin.Report", "Commercial.SemanticModel",
    ]


def test_a_renamed_report_still_resolves(dist: Path):
    """A prefix table would lose this report; the .pbir binding does not."""
    _make_report(dist, "Quarterly_Board_Deck", "Commercial.SemanticModel")
    assert "Quarterly_Board_Deck.Report" in _items_for_domain(dist, "Commercial")


def test_other_domains_are_excluded(dist: Path):
    assert _items_for_domain(dist, "Finance") == [
        "FIN-001_Cash.Report", "Finance.SemanticModel",
    ]


def test_unknown_domain_yields_empty_so_the_caller_can_fail(dist: Path):
    assert _items_for_domain(dist, "Marketing") == []


def test_report_without_pbir_is_skipped_not_crashed(dist: Path):
    _make_report(dist, "Broken", None)
    assert "Broken.Report" not in _items_for_domain(dist, "Commercial")


def test_malformed_pbir_is_skipped_not_crashed(dist: Path):
    d = dist / "Corrupt.Report"
    d.mkdir()
    (d / "definition.pbir").write_text("{not json", encoding="utf-8")
    assert "Corrupt.Report" not in _items_for_domain(dist, "Commercial")


def test_windows_path_separators_resolve(dist: Path):
    d = dist / "WinStyle.Report"
    d.mkdir()
    (d / "definition.pbir").write_text(
        '{"datasetReference":{"byPath":{"path":"..\\\\Commercial.SemanticModel"}}}',
        encoding="utf-8")
    assert "WinStyle.Report" in _items_for_domain(dist, "Commercial")


def test_missing_directory_yields_empty(tmp_path: Path):
    assert _items_for_domain(tmp_path / "nope", "Commercial") == []


# -- the orphan-cleanup interlock --------------------------------------------------


def test_domain_filter_disables_orphan_unpublish():
    """Orphan cleanup diffs the workspace against the staged subset — with a domain filter
    that would unpublish every other domain's items."""
    src = _release_source()
    block = src[src.index("if args.domain_filter:"):src.index("# Release to workspace")]
    assert "unpublish_orphans = False" in block
    # And the call must pass the local decision, not the raw flag.
    assert "unpublish_orphans=unpublish_orphans" in src
    assert "unpublish_orphans=args.unpublish_items" not in src
