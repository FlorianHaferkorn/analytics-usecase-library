"""Desktop guard (Skills-Abgleich R3/R4, ALUCA D-687) — peer of Meridian's build guard.

``products/fabric/powerbi/tooling/desktop_guard.py`` is a **peer pair** with Meridian
``core/pbi_engine/desktop_guard.py``: two homes, byte-identical, no PIN direction. Checked here:

  * PARITY: the file carries the pinned sha256; with a Meridian checkout ($MERIDIAN_ROOT or
    ../Freelancing) it is compared byte for byte. Meridian's ``scripts/check_aluca_mirror.py``
    (PEER_PAIRS) is the counterpart from the other side.
  * The guard tests of Meridian ``core/pbi_engine/tests/test_desktop_guard.py``, adapted only in
    the import path (path robustness, artefact matching, R3 uncommitted changes).
  * The report emitter ``generate_full_report.py`` blocks on an open Desktop session and only
    warns on uncommitted changes.

The bridge itself is mocked (no Windows/Desktop needed).
"""
from __future__ import annotations

import hashlib
import os
import subprocess
from pathlib import Path

import pytest

from products.fabric.powerbi.tooling import desktop_guard as g
from products.fabric.powerbi.tooling.page_scaffold_generator import generate_full_report as gfr

REPO = Path(__file__).resolve().parents[5]
GUARD = REPO / "products" / "fabric" / "powerbi" / "tooling" / "desktop_guard.py"
MERIDIAN_REL = "core/pbi_engine/desktop_guard.py"

#: sha256 of the peer file. Change it only together with the Meridian peer, byte-identically.
GUARD_SHA256 = "af7f861120f9a3df240286bb8a8f3000d0cf284402d83df082c2285b42cec88f"  # pragma: allowlist secret


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ─── Peer-Paar ───────────────────────────────────────────────────────────────

def test_guard_carries_the_pinned_peer_hash():
    assert _sha(GUARD) == GUARD_SHA256, (
        "desktop_guard.py changed: it is a peer pair with Meridian "
        f"{MERIDIAN_REL} — change both byte-identically, then update GUARD_SHA256")


def test_guard_byte_identical_with_meridian():
    env = os.environ.get("MERIDIAN_ROOT")
    root = Path(env).expanduser() if env else REPO.parent / "Freelancing"
    peer = root / MERIDIAN_REL
    if not peer.is_file():
        pytest.skip("no Meridian checkout with the peer guard — parity measured by the pin only")
    assert _sha(peer) == _sha(GUARD)


# ─── Meridian-Tests (Import angepasst) ───────────────────────────────────────

def _session(path: Path | str, *, pid: int = 1, unsaved: bool = True) -> g.DesktopSession:
    return g.DesktopSession(pid=pid, file_path=str(path), has_unsaved_changes=unsaved)


def _artifact(tmp_path: Path) -> tuple[Path, Path]:
    """Legt die reale Struktur nach: <dist>/<Name>.pbip neben <dist>/<Name>.Report."""
    dist = tmp_path / "dist_REFLEX-TOOLS"
    (dist / "Contoso_Modern.Report" / "definition").mkdir(parents=True)
    pbip = dist / "Contoso_Modern.pbip"
    pbip.write_text("{}", encoding="utf-8")
    return dist, pbip


def test_blocking_sessions_accepts_str_target(tmp_path, monkeypatch):
    dist, pbip = _artifact(tmp_path)
    monkeypatch.setattr(g, "sessions", lambda: [_session(pbip)])
    assert len(g.blocking_sessions(str(dist))) == 1
    assert len(g.blocking_sessions(dist)) == 1


def test_stale_sessions_accepts_str_target(tmp_path, monkeypatch):
    dist, pbip = _artifact(tmp_path)
    monkeypatch.setattr(g, "sessions", lambda: [_session(pbip)])
    monkeypatch.setattr(g, "_started_at", lambda pid: None)
    assert g.stale_sessions(str(dist)) == []
    assert g.stale_sessions(dist) == []


def test_matches_report_subdirectory(tmp_path, monkeypatch):
    dist, pbip = _artifact(tmp_path)
    monkeypatch.setattr(g, "sessions", lambda: [_session(pbip)])
    assert len(g.blocking_sessions(dist / "Contoso_Modern.Report")) == 1


def test_other_artifact_in_same_folder_does_not_block(tmp_path, monkeypatch):
    dist, _ = _artifact(tmp_path)
    repro = dist / "Contoso_Reproduktion.pbip"
    repro.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(g, "sessions", lambda: [_session(repro)])
    assert g.blocking_sessions(dist / "Contoso_Modern.Report") == []


def test_only_unsaved_filters(tmp_path, monkeypatch):
    dist, pbip = _artifact(tmp_path)
    monkeypatch.setattr(g, "sessions", lambda: [_session(pbip, unsaved=False)])
    assert len(g.blocking_sessions(dist)) == 1
    assert g.blocking_sessions(dist, only_unsaved=True) == []


def test_empty_session_path_never_matches(tmp_path, monkeypatch):
    dist, _ = _artifact(tmp_path)
    monkeypatch.setattr(g, "sessions", lambda: [_session("")])
    assert g.blocking_sessions(dist) == []


def test_no_sessions_means_no_block(tmp_path, monkeypatch):
    dist, _ = _artifact(tmp_path)
    monkeypatch.setattr(g, "sessions", lambda: [])
    assert g.blocking_sessions(dist) == []


def _git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _repo_with_report(tmp_path: Path) -> Path:
    rep = tmp_path / "X.Report"
    rep.mkdir()
    (rep / "a.json").write_text("{}", encoding="utf-8")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "-c", "user.email=t@t", "-c", "user.name=t", "add", ".")
    _git(tmp_path, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "x")
    return rep


def test_uncommitted_changes_r3(tmp_path):
    """R3 (D-687): geprüft-sauber ([]), geprüft-offen (Liste), nicht geprüft (None)."""
    assert g.uncommitted_changes(tmp_path / "fehlt.Report") is None
    rep = tmp_path / "X.Report"
    rep.mkdir()
    (rep / "a.json").write_text("{}", encoding="utf-8")
    assert g.uncommitted_changes(rep) is None  # kein Repository
    rep.joinpath("a.json").unlink()
    rep.rmdir()
    rep = _repo_with_report(tmp_path)
    assert g.uncommitted_changes(rep) == []
    (rep / "a.json").write_text('{"b": 1}', encoding="utf-8")
    offen = g.uncommitted_changes(rep)
    assert offen and offen[0].endswith("a.json")
    assert "WARNUNG R3" in g.format_uncommitted_warning(offen, rep)


# ─── Aufruf im ALUCA-Report-Emit ─────────────────────────────────────────────

def test_emitter_blocks_on_open_desktop_session(tmp_path, monkeypatch, capsys):
    dist, pbip = _artifact(tmp_path)
    monkeypatch.setattr(g, "sessions", lambda: [_session(pbip)])
    monkeypatch.setattr(g, "_started_at", lambda pid: None)
    target = dist / "Contoso_Modern.Report"
    assert gfr.desktop_guard_check(target) == 3
    assert "BUILD-GUARD" in capsys.readouterr().err
    # bewusst übergangen
    assert gfr.desktop_guard_check(target, allow_desktop_open=True) == 0


def test_emitter_only_warns_on_uncommitted_changes(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(g, "sessions", lambda: [])
    rep = _repo_with_report(tmp_path)
    (rep / "a.json").write_text('{"hand": 1}', encoding="utf-8")
    assert gfr.desktop_guard_check(rep) == 0
    assert "WARNUNG R3" in capsys.readouterr().err


def test_emitter_without_desktop_is_silent(tmp_path, monkeypatch, capsys):
    """Linux/CI: keine Sessions, kein Repository — der Guard bremst nichts."""
    monkeypatch.setattr(g, "sessions", lambda: [])
    assert gfr.desktop_guard_check(tmp_path / "Neu.Report") == 0
    assert capsys.readouterr().err == ""
