from __future__ import annotations

import json
from pathlib import Path

from tooling.superversion.project_package.migrations import migrate_project_package
from tooling.superversion.project_package.repository_cli import main


REPO = Path(__file__).resolve().parents[3]
SCHEMAS = REPO / "tooling" / "generator" / "schemas"
LEGACY_FIXTURE = REPO / "tooling" / "tests" / "fixtures" / "project_package" / "v1"


def _package(root: Path) -> Path:
    migrate_project_package(LEGACY_FIXTURE, root, SCHEMAS)
    return root


def _invoke(capsys, *arguments: str) -> tuple[int, dict]:
    code = main(list(arguments))
    payload = json.loads(capsys.readouterr().out)
    return code, payload


def test_cli_commit_head_export_and_import_roundtrip(tmp_path: Path, capsys) -> None:
    repository = tmp_path / "repository"
    code, committed = _invoke(
        capsys,
        "--repository", str(repository),
        "--schemas", str(SCHEMAS),
        "commit", "--package", str(_package(tmp_path / "package")),
    )
    assert code == 0
    assert committed["revision"]["revision"] == 1

    code, head = _invoke(
        capsys,
        "--repository", str(repository),
        "--schemas", str(SCHEMAS),
        "head",
    )
    assert code == 0
    assert head["head"] == committed["revision"]

    archive = tmp_path / "history.zip"
    code, exported = _invoke(
        capsys,
        "--repository", str(repository),
        "--schemas", str(SCHEMAS),
        "export", "--output", str(archive),
    )
    assert code == 0
    assert Path(exported["output"]) == archive

    imported_root = tmp_path / "imported"
    code, imported = _invoke(
        capsys,
        "--repository", str(imported_root),
        "--schemas", str(SCHEMAS),
        "import", "--input", str(archive),
    )
    assert code == 0
    assert imported["head"] == committed["revision"]


def test_cli_returns_machine_readable_failure(tmp_path: Path, capsys) -> None:
    code, payload = _invoke(
        capsys,
        "--repository", str(tmp_path / "repository"),
        "--schemas", str(SCHEMAS),
        "commit", "--package", str(tmp_path / "missing"),
    )
    assert code == 1
    assert payload["ok"] is False
    assert "package root" in payload["error"] or "missing manifest" in payload["error"]
