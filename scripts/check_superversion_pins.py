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

Upstream-commit comparison (does our pin lag the Meridian remote?) needs the
Meridian git remote, which is not configured here — that slice soft-skips with a
clear marker, mirroring Meridian's offline behaviour.

Usage:
  python3 scripts/check_superversion_pins.py [--strict] [--json FILE]
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
VENDOR_DIR = REPO_ROOT / "tooling" / "superversion" / "vendor" / "meridian"
PIN_PATH = VENDOR_DIR / "PIN.json"
STALENESS_ADVISORY_DAYS = 60


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
                 parity_active: Optional[bool], osi_status: str) -> tuple[str, list[str]]:
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
    lines.append("  upstream-commit comparison: soft-skipped (no Meridian remote configured).")

    if has_drift(integrity):
        return "DRIFT", lines
    if (not provenance["commit_pinned"]) or provenance["stale"]:
        return "ADVISORY", lines
    return "OK", lines


# --------------------------------------------------------------------------- #
# IO (impure)                                                                  #
# --------------------------------------------------------------------------- #

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
    args = parser.parse_args(argv)

    if not PIN_PATH.exists():
        print("[superversion-pins] no vendored Meridian pin — nothing to check (soft-skip).")
        return 0

    pin = json.loads(PIN_PATH.read_text(encoding="utf-8"))
    today = _dt.date.today()
    integrity = verify_integrity(pin, VENDOR_DIR)
    provenance = pin_provenance(pin, today)
    parity = _parity_active()
    osi = _osi_status()
    level, lines = build_report(pin, integrity, provenance, parity, osi)

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
