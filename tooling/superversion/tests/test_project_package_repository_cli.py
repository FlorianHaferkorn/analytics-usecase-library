from __future__ import annotations

import json
import shutil
from pathlib import Path

import yaml

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


def _write_yaml(path: Path, value: dict) -> None:
    path.write_text(
        yaml.safe_dump(value, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
        newline="\n",
    )


def _file_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


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


def test_cli_commit_draft_derives_two_revisions_without_mutating_input(
    tmp_path: Path,
    capsys,
) -> None:
    repository = tmp_path / "repository"
    draft_v1 = _package(tmp_path / "draft-v1")
    opportunity_path = draft_v1 / "opportunity" / "opportunity.yaml"
    opportunity = yaml.safe_load(opportunity_path.read_text(encoding="utf-8"))
    opportunity["objectives"].append("Save through the repository CLI")
    _write_yaml(opportunity_path, opportunity)
    input_v1 = _file_bytes(draft_v1)

    code, first = _invoke(
        capsys,
        "--repository", str(repository),
        "--schemas", str(SCHEMAS),
        "commit-draft", "--package", str(draft_v1), "--expected-head", "none",
    )
    assert code == 0
    assert first["revision"]["revision"] == 1
    assert first["revision"]["parent_revision_hash"] is None
    assert _file_bytes(draft_v1) == input_v1

    draft_v2 = tmp_path / "draft-v2"
    shutil.copytree(draft_v1, draft_v2)
    opportunity_path = draft_v2 / "opportunity" / "opportunity.yaml"
    opportunity = yaml.safe_load(opportunity_path.read_text(encoding="utf-8"))
    opportunity["objectives"].append("Save the next revision")
    _write_yaml(opportunity_path, opportunity)
    input_v2 = _file_bytes(draft_v2)

    code, second = _invoke(
        capsys,
        "--repository", str(repository),
        "--schemas", str(SCHEMAS),
        "commit-draft", "--package", str(draft_v2),
        "--expected-head", first["revision"]["revision_hash"],
    )
    assert code == 0
    assert second["revision"]["revision"] == 2
    assert second["revision"]["parent_revision_hash"] == first["revision"]["revision_hash"]
    assert _file_bytes(draft_v2) == input_v2


def test_cli_commit_draft_rejects_invalid_domain_content(tmp_path: Path, capsys) -> None:
    draft = _package(tmp_path / "invalid-draft")
    opportunity_path = draft / "opportunity" / "opportunity.yaml"
    opportunity = yaml.safe_load(opportunity_path.read_text(encoding="utf-8"))
    opportunity["objectives"] = []
    _write_yaml(opportunity_path, opportunity)
    input_files = _file_bytes(draft)

    code, payload = _invoke(
        capsys,
        "--repository", str(tmp_path / "repository"),
        "--schemas", str(SCHEMAS),
        "commit-draft", "--package", str(draft), "--expected-head", "none",
    )

    assert code == 1
    assert payload["ok"] is False
    assert "opportunity.yaml" in payload["error"]
    assert _file_bytes(draft) == input_files


def test_cli_commit_draft_reports_stale_head_as_conflict(tmp_path: Path, capsys) -> None:
    repository = tmp_path / "repository"
    first_draft = _package(tmp_path / "draft-v1")
    code, first = _invoke(
        capsys,
        "--repository", str(repository),
        "--schemas", str(SCHEMAS),
        "commit-draft", "--package", str(first_draft), "--expected-head", "none",
    )
    assert code == 0

    stale_draft = tmp_path / "stale-draft"
    shutil.copytree(first_draft, stale_draft)
    code, conflict = _invoke(
        capsys,
        "--repository", str(repository),
        "--schemas", str(SCHEMAS),
        "commit-draft", "--package", str(stale_draft), "--expected-head", "none",
    )

    assert code == 1
    assert conflict == {
        "ok": False,
        "status": 409,
        "code": "stale_head",
        "error": (
            "stale draft: expected repository HEAD None, actual HEAD is "
            f"'{first['revision']['revision_hash']}'"
        ),
    }
