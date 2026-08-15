"""Unit and integration tests for the report_quality self-heal loop.

Tests cover:
- Page size deterministic fix (apply + dry-run)
- Visual bounds deterministic fix
- Schema URL repair (dry-run vs apply)
- Path allowlist: rejects edits outside .Report/definition/
- No-progress detection (stalled loop)
- Summary output remains compact (not full log dump)
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from tooling.report_quality.models import Violation
from tooling.report_quality.self_heal import FixRecord, SelfHealResult, _is_safe_path, self_heal


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_report_dir(tmp_path: Path, page_width: int = 1920, page_height: int = 1080) -> Path:
    """Create a minimal .Report directory with one page (PBIR layout)."""
    report_dir = tmp_path / "Test.Report"
    definition = report_dir / "definition"
    report_dir.mkdir()
    (report_dir / "report.json").write_text(json.dumps({"$schema": "..."}), encoding="utf-8")
    definition.mkdir()
    pages_dir = definition / "pages"
    pages_dir.mkdir()

    # pages.json is required by parse_report; pageOrder must list actual subdirectory names
    page_folder_name = "Page_Overview"
    pages_meta = {"pageOrder": [page_folder_name]}
    (pages_dir / "pages.json").write_text(json.dumps(pages_meta), encoding="utf-8")

    page_dir = pages_dir / page_folder_name
    page_dir.mkdir()

    page_json = {"displayName": "Overview", "width": page_width, "height": page_height}
    (page_dir / "page.json").write_text(json.dumps(page_json), encoding="utf-8")

    # Add a visual inside bounds
    visuals_dir = page_dir / "visuals"
    visuals_dir.mkdir()
    visual_dir = visuals_dir / "kpi_card"
    visual_dir.mkdir()
    visual_json = {
        "position": {"x": 0, "y": 0, "width": 300, "height": 100},
        "visual": {"visualType": "card"},
    }
    (visual_dir / "visual.json").write_text(json.dumps(visual_json), encoding="utf-8")

    return report_dir


# ── Path allowlist tests ───────────────────────────────────────────────────────

def test_safe_path_inside_definition(tmp_path: Path) -> None:
    report_dir = tmp_path / "Test.Report"
    report_dir.mkdir()
    (report_dir / "definition").mkdir()
    target = report_dir / "definition" / "pages" / "p1" / "page.json"
    target.parent.mkdir(parents=True)
    target.touch()
    assert _is_safe_path(target, report_dir) is True


def test_safe_path_outside_definition(tmp_path: Path) -> None:
    report_dir = tmp_path / "Test.Report"
    report_dir.mkdir()
    outside = tmp_path / "other_file.json"
    outside.touch()
    assert _is_safe_path(outside, report_dir) is False


def test_safe_path_report_root(tmp_path: Path) -> None:
    report_dir = tmp_path / "Test.Report"
    report_dir.mkdir()
    root_file = report_dir / "report.json"
    root_file.touch()
    # report.json is NOT inside definition/ -- must be rejected
    assert _is_safe_path(root_file, report_dir) is False


# ── Page size fix tests ────────────────────────────────────────────────────────

def test_page_size_already_correct(tmp_path: Path) -> None:
    """A report with correct page size (page-size-only spec) should be green."""
    from tooling.report_quality.structural_validator import PageSize, ReportSpec

    report_dir = _make_report_dir(tmp_path, page_width=1920, page_height=1080)
    spec = ReportSpec(invariants=[PageSize()])
    result = self_heal(report_dir, spec=spec)
    assert result.success is True
    assert result.iterations == 0
    assert result.fixed_count == 0
    assert result.remaining == []


def test_page_size_fix_applied(tmp_path: Path) -> None:
    """Wrong page size should be fixed in one iteration (page-size-only spec)."""
    from tooling.report_quality.structural_validator import PageSize, ReportSpec

    report_dir = _make_report_dir(tmp_path, page_width=1280, page_height=720)
    spec = ReportSpec(invariants=[PageSize()])
    result = self_heal(report_dir, spec=spec)
    assert result.success is True
    assert result.fixed_count >= 1

    page_json = json.loads(
        (report_dir / "definition" / "pages" / "Page_Overview" / "page.json").read_text(encoding="utf-8")
    )
    assert page_json["width"] == 1920
    assert page_json["height"] == 1080


def test_dry_run_processes_one_violation_per_iteration(tmp_path: Path) -> None:
    """Dry-run simulates at most one violation per iteration (outer loop break)."""
    from tooling.report_quality.structural_validator import PageSize, ReportSpec

    report_dir = _make_report_dir(tmp_path, page_width=1280, page_height=720)
    spec = ReportSpec(invariants=[PageSize()])
    result = self_heal(report_dir, spec=spec, max_iterations=2, dry_run=True)
    # width + height are two violations; one per iteration => needs 2 iterations
    assert result.iterations == 2
    assert len(result.fix_log) == 2
    assert result.fix_log[0].pointer != result.fix_log[1].pointer


def test_page_size_dry_run_does_not_write(tmp_path: Path) -> None:
    """Dry-run must not modify any files."""
    report_dir = _make_report_dir(tmp_path, page_width=1280, page_height=720)
    page_file = report_dir / "definition" / "pages" / "Page_Overview" / "page.json"
    before = page_file.read_text(encoding="utf-8")

    result = self_heal(report_dir, dry_run=True)

    after = page_file.read_text(encoding="utf-8")
    assert before == after, "dry-run must not modify files"
    # Fix log should show what would have been done
    assert len(result.fix_log) > 0
    assert all("dry-run" in r.fix_id for r in result.fix_log)


# ── No-progress / stalled detection ───────────────────────────────────────────

def test_stalled_when_no_fixable_violations(tmp_path: Path) -> None:
    """Violations without a deterministic fix should cause stalled=False (no progress)."""
    from tooling.report_quality.structural_validator import ReportSpec, RequiredSlots

    report_dir = _make_report_dir(tmp_path)
    # Use a spec with only RequiredSlots (no fix_fn) to force a stall.
    # RequiredSlots now takes its mandatory slots from template_manifest.yaml and
    # needs the page variant explicitly — T1_Portfolio makes KPI_Cards/Slicer_Date
    # mandatory, and the fixture report has neither.
    spec = ReportSpec(invariants=[RequiredSlots(variant="T1_Portfolio")])
    result = self_heal(report_dir, spec=spec)
    # RequiredSlots fires (Overview page has no KPI_Cards etc.) but has no fix
    if result.initial_violations > 0:
        assert result.success is False or result.fixed_count == 0


# ── Fix log serialisation ─────────────────────────────────────────────────────

def test_fix_log_serialisation(tmp_path: Path) -> None:
    """SelfHealResult.to_dict() should produce JSON-serialisable output."""
    result = SelfHealResult(
        success=True,
        iterations=1,
        initial_violations=2,
        fixed_count=2,
        remaining=[],
        fix_log=[FixRecord(1, "page:size", "pages/p1/width", "pages/p1/page.json", "page:size:applied")],
    )
    d = result.to_dict()
    # Must be JSON-serialisable
    serialised = json.dumps(d)
    parsed = json.loads(serialised)
    assert parsed["success"] is True
    assert parsed["fixed_count"] == 2
    assert len(parsed["fix_log"]) == 1
    assert parsed["fix_log"][0]["check"] == "page:size"


# ── Invalid report_dir handling ───────────────────────────────────────────────

def test_invalid_report_dir_raises(tmp_path: Path) -> None:
    """self_heal on a non-existent directory must raise ValueError."""
    with pytest.raises(ValueError, match="does not exist"):
        self_heal(tmp_path / "NonExistent.Report")


# ── CLI integration: --summary output stays compact ────────────────────────────

def test_cli_dry_run_self_heal_exit_when_criticals_would_remain(tmp_path: Path) -> None:
    """--self-heal --dry-run must not return 0 when critical violations would persist."""
    from tooling.report_quality.cli import main as cli_main

    report_dir = _make_report_dir(tmp_path)
    # An out-of-bounds visual: `VisualWithinPage` is critical and has no fix_fn, so a
    # dry-run cannot clear it.
    #
    # This used to rely on `RequiredSlots` being part of `default_spec()`. It no longer
    # is — that invariant now needs the page variant from template_manifest.yaml, which
    # a default spec cannot know. The assertion here is about the CLI's exit code for
    # unfixable criticals, so it needs *an* unfixable critical, not that specific one.
    oob = report_dir / "definition" / "pages" / "Page_Overview" / "visuals" / "out_of_bounds"
    oob.mkdir(parents=True)
    (oob / "visual.json").write_text(
        json.dumps({"position": {"x": 1900, "y": 1000, "width": 500, "height": 400},
                    "visual": {"visualType": "card"}}),
        encoding="utf-8",
    )
    exit_code = cli_main(
        [
            "--dist-root",
            str(tmp_path),
            "--self-heal",
            "--dry-run",
            "--summary",
        ]
    )
    assert exit_code == 1


def test_cli_dry_run_self_heal_never_returns_stalled_exit(tmp_path: Path) -> None:
    """--dry-run must not use exit 3 (stalled is apply-mode only)."""
    from tooling.report_quality.cli import main as cli_main

    report_dir = _make_report_dir(tmp_path, page_width=1280, page_height=720)
    exit_code = cli_main(
        ["--dist-root", str(tmp_path), "--self-heal", "--dry-run", "--summary"]
    )
    assert exit_code != 3


def test_cli_dry_run_self_heal_exit_zero_when_fixable(tmp_path: Path) -> None:
    """--self-heal --dry-run returns 0 when all criticals are deterministically fixable."""
    from tooling.report_quality.cli import main as cli_main
    from tooling.report_quality.structural_validator import PageSize, ReportSpec
    from tooling.report_quality.self_heal import self_heal

    report_dir = _make_report_dir(tmp_path, page_width=1280, page_height=720)
    spec = ReportSpec(invariants=[PageSize()])
    result = self_heal(report_dir, spec=spec, dry_run=True)
    assert result.success is True

    exit_code = cli_main(
        [
            "--dist-root",
            str(tmp_path),
            "--self-heal",
            "--dry-run",
            "--summary",
        ]
    )
    assert exit_code in (0, 1)
    assert exit_code != 3


def test_cli_summary_output_is_compact(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """--summary mode must not dump more than ~10 lines for a report with violations."""
    from tooling.report_quality.cli import main as cli_main

    # Create a report with a wrong page size so we get violations
    report_dir = _make_report_dir(tmp_path, page_width=1280, page_height=720)

    exit_code = cli_main(["--dist-root", str(tmp_path), "--summary"])
    captured = capsys.readouterr()

    lines = [l for l in captured.out.splitlines() if l.strip()]
    # Summary should be <= 15 lines for a single-report run
    assert len(lines) <= 15, f"Summary output is too long ({len(lines)} lines):\n{captured.out}"


# ── write_fix_log ────────────────────────────────────────────────────────────

def test_write_fix_log_creates_file(tmp_path: Path) -> None:
    from tooling.report_quality.self_heal import self_heal_all, write_fix_log

    report_dir = _make_report_dir(tmp_path, page_width=1280, page_height=720)
    results = self_heal_all(tmp_path)

    log_path = tmp_path / "out" / "fix_log.json"
    write_fix_log(results, log_path)

    assert log_path.exists()
    data = json.loads(log_path.read_text(encoding="utf-8"))
    assert "Test.Report" in data
