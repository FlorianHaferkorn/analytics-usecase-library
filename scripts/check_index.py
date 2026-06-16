#!/usr/bin/env python3
"""Index-Drift-Gate — hält die _INDEX.md-Navigation ehrlich UND ungefüllt-frei.

Repo-agnostisch, pure Python. Vier Prüfungen:

  1. VOLLSTÄNDIGKEIT (hart) — Subtree-Ownership: jede `*.md` gehört dem NÄCHSTEN
     Vorfahren-Ordner mit `_INDEX.md` und MUSS dort gelistet sein. Ein Index besitzt
     seinen Unterbaum bis zum nächsten Index → auch `docs/sprints/x.md` wird erfasst,
     ohne den `docs/sprints/_INDEX.md`-Bereich doppelt zu regieren.

  2. PFAD/ANKER (hart) — jeder konkrete Pfad (mit '/') im Index zeigt auf ein echtes
     Ziel; Anker (#frag) gegen die Überschriften-Slugs. Globs/{{…}}/URLs übersprungen.

  3. QUALITÄT/PLATZHALTER — `{{…}}` in einem committeten `_INDEX.md`/`CLAUDE.md`/
     `GOI_DOKTRIN.md` = ungefülltes Gerüst. Default: WARNUNG. Mit `--strict`: HART
     (du kannst kein Stub committen). Das ist der maschinell erzwingbare Qualitäts-
     Floor; die Decke (gutes Routing) liefert Mensch/Skill.

  4. STALENESS (advisory) — `last-reviewed` älter als `shelf-life-days` → WARNUNG.

Exit 1 bei harten Befunden, 0 sonst.

Aufruf:  python3 scripts/check_index.py [--strict] [TEILBAUM]
         (pre-commit/CI: --strict; lokal/nach-Scaffold: ohne)
"""
from __future__ import annotations

import datetime as _dt
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

IGNORE_DIRS = {".git", "node_modules", "dist", "build", ".venv", "venv",
               "__pycache__", ".stubs", ".next", "out", "target"}
EXEMPT_FILES = {"_INDEX.md", "README.md", "README_Template.md", "_MANIFEST.md",
                "CHANGELOG.md", "LICENSE.md", "NAVIGATION_PHILOSOPHY.md",
                "_INDEX.area.md", "_INDEX.ledger.md"}
# Platzhalter-Prüfung gilt nur für echte, gefüllte Dateien — Vorlagen sind ausgenommen.
TEMPLATE_NAMES = {"_INDEX.area.md", "_INDEX.ledger.md"}

DUPE_RE = re.compile(r" \d+(\.[A-Za-z0-9]+)?$")
PATH_RE = re.compile(r"`([^`]+)`")
FRONT_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
PLACEHOLDER_RE = re.compile(r"\{\{[^}]+\}\}")


def slugify(h: str) -> str:
    s = re.sub(r"[^\w\s-]", "", h.strip().lower(), flags=re.UNICODE)
    return re.sub(r"\s+", "-", s)


def headings_of(md: Path) -> set[str]:
    return {slugify(m.group(1)) for m in
            (re.match(r"^#{1,6}\s+(.*)", ln) for ln in md.read_text(encoding="utf-8", errors="replace").splitlines())
            if m}


def find_indexes(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("_INDEX.md")
                  if not any(part in IGNORE_DIRS for part in p.parts))


def ignored(md: Path) -> bool:
    return (any(p in IGNORE_DIRS for p in md.parts) or md.name in EXEMPT_FILES
            or DUPE_RE.search(md.name) or DUPE_RE.search(md.stem))


def _listed(token: str, text: str) -> bool:
    """Token (Pfad ODER Dateiname mit .md) als ABGEGRENZTES Vorkommen — kein
    nackter Substring (sonst matcht der Stem 'd' überall, oder 'd.md' in 'abcd.md')."""
    return re.search(r"(?<![\w/.\-])" + re.escape(token) + r"(?![\w])", text) is not None


def check_completeness(root: Path, indexes: list[Path], errors: list[str]) -> None:
    index_dirs = {idx.parent.resolve() for idx in indexes}
    cache = {idx.parent.resolve(): idx.read_text(encoding="utf-8", errors="replace") for idx in indexes}
    for md in root.rglob("*.md"):
        if md.name == "_INDEX.md" or ignored(md):
            continue
        owner = next((p for p in md.resolve().parents if p in index_dirs), None)
        if owner is None:
            continue  # kein Index regiert diesen Ordner — ok
        text = cache[owner]
        rel = md.resolve().relative_to(owner)
        if not (_listed(str(rel), text) or _listed(rel.name, text)):
            idx_rel = (owner / "_INDEX.md").relative_to(REPO_ROOT)
            errors.append(f"[Vollständigkeit] {md.relative_to(REPO_ROOT)} fehlt im {idx_rel}")


def check_paths(index: Path, errors: list[str]) -> None:
    for raw in PATH_RE.findall(index.read_text(encoding="utf-8", errors="replace")):
        ref = raw.strip()
        if not ref or "/" not in ref or "{{" in ref or "*" in ref or ref.startswith(("http://", "https://")):
            continue
        anchor = None
        if "#" in ref:
            ref, anchor = ref.split("#", 1)
        target = next((c for c in [(index.parent / ref).resolve(), (REPO_ROOT / ref).resolve()] if c.exists()), None)
        if target is None:
            errors.append(f"[Pfad] {index.relative_to(REPO_ROOT)} → '{ref}' existiert nicht")
        elif anchor and target.suffix == ".md" and slugify(anchor) not in headings_of(target):
            errors.append(f"[Anker] {index.relative_to(REPO_ROOT)} → '{ref}#{anchor}' trifft keine Überschrift")


def check_placeholders(path: Path, strict: bool, errors: list[str], warnings: list[str]) -> None:
    if not path.exists() or path.name in TEMPLATE_NAMES:
        return
    hits = PLACEHOLDER_RE.findall(path.read_text(encoding="utf-8", errors="replace"))
    if hits:
        msg = f"[Platzhalter] {path.relative_to(REPO_ROOT)}: {len(hits)} ungefüllte {{…}} (z.B. {hits[0]})"
        (errors if strict else warnings).append(msg)


def check_staleness(index: Path, warnings: list[str]) -> None:
    m = FRONT_RE.match(index.read_text(encoding="utf-8", errors="replace"))
    rel = index.relative_to(REPO_ROOT)
    if not m:
        return
    fm = dict(re.findall(r"^(\S+):\s*(.+)$", m.group(1), re.MULTILINE))
    if "last-reviewed" not in fm:
        warnings.append(f"[Staleness] {rel}: kein last-reviewed-Feld"); return
    try:
        age = (_dt.date.today() - _dt.date.fromisoformat(fm["last-reviewed"].strip())).days
        shelf = int(fm.get("shelf-life-days", "90"))
    except ValueError:
        warnings.append(f"[Staleness] {rel}: last-reviewed/shelf-life-days unlesbar"); return
    if age > shelf:
        warnings.append(f"[Staleness] {rel}: vor {age} d reviewt (> {shelf} d) — auffrischen")


def main(argv: list[str]) -> int:
    strict = "--strict" in argv
    pos = [a for a in argv[1:] if not a.startswith("--")]
    root = (REPO_ROOT / pos[0]) if pos else REPO_ROOT
    indexes = find_indexes(root)
    if not indexes:
        print(f"[check-index] keine _INDEX.md unter {root} gefunden."); return 0
    errors: list[str] = []
    warnings: list[str] = []
    check_completeness(root, indexes, errors)
    for idx in indexes:
        check_paths(idx, errors)
        check_staleness(idx, warnings)
        check_placeholders(idx, strict, errors, warnings)
    for f in ("CLAUDE.md", "GOI_DOKTRIN.md"):
        check_placeholders(REPO_ROOT / f, strict, errors, warnings)
    for w in warnings:
        print("WARN  " + w)
    for e in errors:
        print("FAIL  " + e)
    mode = "strict" if strict else "lax"
    print(f"[check-index/{mode}] {len(indexes)} Index-Dateien · "
          f"{len(errors)} harte Befunde · {len(warnings)} Warnungen.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
