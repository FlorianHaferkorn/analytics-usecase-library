#!/usr/bin/env python3
"""Superversion pin-drift sensor (ADR-0005 rule 6 · task I-2.4).

ALUCA-side mirror of Meridian's `scripts/check_upstream_freshness.py` (D-238)
DOCTRINE: **reports drift, never bumps** (a pin moves only via a deliberate,
reviewed commit after re-validation). Advisory (exit 0) by default; `--strict`
turns drift into an error (exit 1) for a release gate. Offline → soft-skip the
network slice.

Tracks the pins ALUCA owns for the vendored Meridian canonical-core
(`tooling/superversion/vendor/meridian/PIN.json`):

  * **local integrity** — every vendored file vs its recorded sha256 (detects
    LOCAL divergence of the vendored tree; this is netz-frei and always runs).
  * **pin provenance** — `synced_at` age (staleness) and whether an exact
    upstream commit is pinned (UNKNOWN when synced from an archive).
  * **contract parity** — whether the seam re-exports the vendored originals or
    fell back to the standalone mirror.
  * **OSI schema** — reported if vendored in ALUCA; otherwise noted as
    Meridian-owned (ALUCA adopts the OSI target later, I-3/I-7).

Upstream-commit comparison (does our pin lag Meridian?) needs a Meridian checkout
(``$MERIDIAN_ROOT`` or ``../Freelancing``); without one that slice soft-skips with a
clear marker, mirroring Meridian's offline behaviour. With one, each vendored file
is compared against the blob at ``--upstream-ref`` (default ``origin/main``) —
advisory, no network (``git fetch`` stays a deliberate act of the caller).

Re-sync (``--write``, 29.09.2026, A-19): copies ``VENDORED_FILES`` from the commit
``--ref`` (default ``HEAD``) of the Meridian checkout — ``git show <commit>:<path>``,
never the working tree — and rewrites ``PIN.json`` with the exact commit SHA, its
commit date and fresh sha256 values. Deliberately manual, never in CI. Until then
the pin carried ``commit: UNKNOWN`` (zip sync 23.06.2026) plus a hand-ported hunk.

Usage:
  python3 scripts/check_superversion_pins.py [--strict] [--json FILE]
                                             [--upstream-ref REF]
  python3 scripts/check_superversion_pins.py --write [--ref REF]
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
VENDOR_DIR = REPO_ROOT / "tooling" / "superversion" / "vendor" / "meridian"
PIN_PATH = VENDOR_DIR / "PIN.json"
STALENESS_ADVISORY_DAYS = 60

# The vendored contract surface, relative to Meridian's repo root and to VENDOR_DIR.
# The list lives HERE, not in PIN.json: otherwise a file could only be added by
# hand-editing the pin, which the integrity check (rightly) treats as divergence.
VENDORED_FILES = (
    "core/pbi_engine/model.py",
    "core/pbi_engine/parsers/tmdl_parser.py",
    "core/pbi_engine/parsers/pbir_parser.py",
)
SUBTREE_DOC = "core/pbi_engine (contract surface only: model.py + parsers/)"


# --------------------------------------------------------------------------- #
# Pure cores (netz-frei, unit-getestet)                                        #
# --------------------------------------------------------------------------- #

def verify_integrity(pin: dict, vendor_dir: Path) -> list[dict]:
    """Per-file: does the vendored file exist and match its pinned sha256?

    Returns one record per manifest entry: {path, status, detail}. `status` is
    'ok' | 'missing' | 'diverged'. Pure: only reads files, no network.
    """
    out: list[dict] = []
    for entry in pin.get("files", []):
        rel = entry.get("path", "")
        f = vendor_dir / rel
        if not f.exists():
            out.append({"path": rel, "status": "missing", "detail": "file absent"})
            continue
        got = hashlib.sha256(f.read_bytes()).hexdigest()
        want = entry.get("sha256", "")
        if got != want:
            out.append({"path": rel, "status": "diverged",
                        "detail": f"sha256 {got[:12]}… != pinned {want[:12]}…"})
        else:
            out.append({"path": rel, "status": "ok", "detail": want[:12] + "…"})
    return out


def staleness_days(synced_at: str, today: _dt.date) -> Optional[int]:
    """Whole days between `synced_at` (YYYY-MM-DD) and `today`; None if unparseable."""
    try:
        d = _dt.date.fromisoformat(synced_at)
    except (ValueError, TypeError):
        return None
    return (today - d).days


def pin_provenance(pin: dict, today: _dt.date) -> dict:
    """Provenance status: ref, commit-pinned?, staleness, advisory flag."""
    src = pin.get("source", {})
    commit = src.get("commit", "")
    commit_pinned = bool(commit) and "UNKNOWN" not in commit.upper()
    days = staleness_days(src.get("synced_at", ""), today)
    stale = days is not None and days > STALENESS_ADVISORY_DAYS
    return {
        "ref": src.get("ref", "?"),
        "commit_pinned": commit_pinned,
        "synced_at": src.get("synced_at", "?"),
        "staleness_days": days,
        "stale": stale,
    }


def has_drift(integrity: list[dict]) -> bool:
    """Hard drift = any vendored file missing or locally diverged."""
    return any(r["status"] != "ok" for r in integrity)


def build_report(pin: dict, integrity: list[dict], provenance: dict,
                 parity_active: Optional[bool], osi_status: str,
                 upstream: Optional[list[str]] = None) -> tuple[str, list[str]]:
    """(level, lines). level: 'DRIFT' (hard) | 'ADVISORY' | 'OK'."""
    lines: list[str] = []
    for r in integrity:
        mark = "OK " if r["status"] == "ok" else "!! "
        lines.append(f"  [{mark}] {r['path']} — {r['status']} ({r['detail']})")
    lines.append(f"  pin: ref={provenance['ref']} synced_at={provenance['synced_at']} "
                 f"commit_pinned={provenance['commit_pinned']} "
                 f"staleness_days={provenance['staleness_days']}")
    if not provenance["commit_pinned"]:
        lines.append("  ADVISORY: no exact upstream commit pinned — pin on next git-based sync.")
    if provenance["stale"]:
        lines.append(f"  ADVISORY: pin older than {STALENESS_ADVISORY_DAYS}d — review upstream.")
    if parity_active is None:
        lines.append("  parity: contract seam not importable (reported, not failed).")
    else:
        lines.append(f"  parity: seam re-exports {'vendored originals' if parity_active else 'standalone mirror'}.")
    lines.append(f"  osi-schema: {osi_status}")
    if upstream is None:
        lines.append("  upstream-commit comparison: soft-skipped (no Meridian checkout: "
                     "$MERIDIAN_ROOT or ../Freelancing).")
    else:
        lines.extend(upstream)

    if has_drift(integrity):
        return "DRIFT", lines
    if (not provenance["commit_pinned"]) or provenance["stale"]:
        return "ADVISORY", lines
    return "OK", lines


# --------------------------------------------------------------------------- #
# IO (impure)                                                                  #
# --------------------------------------------------------------------------- #

def _meridian_root() -> Optional[Path]:
    """Meridian checkout: ``$MERIDIAN_ROOT`` or the sibling ``../Freelancing``."""
    env = os.environ.get("MERIDIAN_ROOT")
    cand = Path(env).expanduser() if env else REPO_ROOT.parent / "Freelancing"
    return cand if (cand / VENDORED_FILES[0]).is_file() else None


def _git(root: Path, *args: str) -> Optional[str]:
    try:
        proc = subprocess.run(("git", *args), cwd=str(root), capture_output=True,
                              text=True, timeout=30, encoding="utf-8", errors="replace")
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout.strip() if proc.returncode == 0 else None


def _blob(root: Path, commit: str, rel: str) -> Optional[bytes]:
    """File content as committed (``git show``), independent of working tree and EOL."""
    try:
        proc = subprocess.run(("git", "show", f"{commit}:{rel}"), cwd=str(root),
                              capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout if proc.returncode == 0 else None


def upstream_comparison(pin: dict, meridian_root: Path, ref: str) -> list[str]:
    """Advisory: does each vendored file equal the blob at ``ref`` in Meridian?"""
    commit = _git(meridian_root, "rev-parse", "--verify", f"{ref}^{{commit}}")
    if not commit:
        return [f"  upstream-commit comparison: soft-skipped ({ref} unknown in {meridian_root})."]
    lines = [f"  upstream-commit comparison against {ref} = {commit[:8]}:"]
    for entry in pin.get("files", []):
        rel = entry.get("path", "")
        data = _blob(meridian_root, commit, rel)
        if data is None:
            lines.append(f"    [!! ] {rel} — absent upstream")
        elif hashlib.sha256(data).hexdigest() == entry.get("sha256"):
            lines.append(f"    [OK ] {rel} — equal")
        else:
            lines.append(f"    [!! ] {rel} — upstream differs (ADVISORY: re-sync with --write)")
    return lines


def write_vendor(meridian_root: Path, ref: str = "HEAD") -> dict:
    """Re-copy ``VENDORED_FILES`` from commit ``ref`` and rewrite PIN.json. Manual only."""
    commit = _git(meridian_root, "rev-parse", "--verify", f"{ref}^{{commit}}")
    if not commit:
        raise SystemExit(f"[superversion-pins] --write: {ref} ist in {meridian_root} kein Commit")
    blobs: dict[str, bytes] = {}
    for rel in VENDORED_FILES:
        data = _blob(meridian_root, commit, rel)
        if data is None:
            raise SystemExit(f"[superversion-pins] --write: {rel} nicht im Commit {commit[:8]}")
        blobs[rel] = data
    for rel, data in blobs.items():
        target = VENDOR_DIR / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    old = json.loads(PIN_PATH.read_text(encoding="utf-8")) if PIN_PATH.exists() else {}
    fresh = {
        "_doc": old.get("_doc", "Pin + integrity manifest for the vendored Meridian "
                        "canonical-core subtree (ADR-0005)."),
        "source": {
            "repo": old.get("source", {}).get("repo", "Freelancing (Meridian)"),
            "ref": ref,
            "commit": commit,
            "commit_date": _git(meridian_root, "show", "-s", "--format=%cs", commit) or "?",
            "synced_at": _dt.date.today().isoformat(),
            "subtree": SUBTREE_DOC,
        },
        "vendored": "tooling/superversion/vendor/meridian",
        "files": [{"path": rel, "sha256": hashlib.sha256(blobs[rel]).hexdigest()}
                  for rel in VENDORED_FILES],
    }
    PIN_PATH.write_text(json.dumps(fresh, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8", newline="\n")
    return fresh

def _osi_status() -> str:
    candidates = list(VENDOR_DIR.rglob("osi-schema.json"))
    if candidates:
        rel = candidates[0].relative_to(REPO_ROOT)
        return f"vendored in ALUCA at {rel} (tracked)"
    return "not vendored in ALUCA — Meridian-owned (OSI target adopted later, I-3/I-7)"


def _parity_active() -> Optional[bool]:
    try:
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))
        from tooling.superversion import canonical_contract as cc
        return bool(cc.USING_MERIDIAN_ORIGINALS)
    except Exception:
        return None


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 scripts/check_superversion_pins.py",
        description="Superversion pin-drift sensor (reports drift, never bumps).",
    )
    parser.add_argument("--strict", action="store_true",
                        help="exit 1 on hard drift (missing/diverged vendored file)")
    parser.add_argument("--json", type=Path, default=None, help="write status JSON here")
    parser.add_argument("--upstream-ref", default="origin/main",
                        help="Meridian ref for the advisory upstream comparison")
    parser.add_argument("--write", action="store_true",
                        help="re-sync the vendored files from a Meridian commit (manual, never CI)")
    parser.add_argument("--ref", default="HEAD", help="Meridian commit/ref for --write")
    args = parser.parse_args(argv)

    if args.write:
        mer = _meridian_root()
        if mer is None:
            print("[superversion-pins] --write needs a Meridian checkout "
                  "($MERIDIAN_ROOT or ../Freelancing)")
            return 1
        fresh = write_vendor(mer, args.ref)
        print(f"[superversion-pins] re-synced {len(fresh['files'])} file(s) from {mer} "
              f"at {fresh['source']['commit'][:8]} ({fresh['source']['commit_date']})")
        return 0

    if not PIN_PATH.exists():
        print("[superversion-pins] no vendored Meridian pin — nothing to check (soft-skip).")
        return 0

    pin = json.loads(PIN_PATH.read_text(encoding="utf-8"))
    today = _dt.date.today()
    integrity = verify_integrity(pin, VENDOR_DIR)
    provenance = pin_provenance(pin, today)
    parity = _parity_active()
    osi = _osi_status()
    mer = _meridian_root()
    upstream = upstream_comparison(pin, mer, args.upstream_ref) if mer is not None else None
    level, lines = build_report(pin, integrity, provenance, parity, osi, upstream)

    print(f"[superversion-pins] {level}")
    for ln in lines:
        print(ln)

    if args.json is not None:
        args.json.write_text(json.dumps({
            "level": level, "integrity": integrity, "provenance": provenance,
            "parity_active": parity, "osi": osi,
        }, indent=2) + "\n", encoding="utf-8", newline="\n")

    if args.strict and has_drift(integrity):
        print("[superversion-pins] STRICT: hard drift → exit 1")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
