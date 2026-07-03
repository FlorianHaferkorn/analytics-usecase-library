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
import fnmatch
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

IGNORE_DIRS = {".git", "node_modules", "dist", "build", ".venv", "venv",
               "__pycache__", ".stubs", ".next", "out", "target", "golden_docs"}
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


def _frontmatter(text: str) -> dict:
    m = FRONT_RE.match(text)
    return dict(re.findall(r"^(\S+):\s*(.+)$", m.group(1), re.MULTILINE)) if m else {}


def _owns_globs(index_text: str) -> list[str]:
    """Opt-in: ein _INDEX deklariert `owns: *.sql, *.ts` → Gate erzwingt auch diese Dateien."""
    raw = _frontmatter(index_text).get("owns", "").strip().strip("[]")
    return [g.strip().strip("'\"") for g in raw.split(",") if g.strip()] if raw else []


def _non_navigated(p: Path) -> bool:
    """Nicht-navigierter Bereich → aus Completeness UND Advisory raus: `_`-präfigierter Dir
    (z. B. `_archive`) oder ein `.claude-no-index`-Marker an einem Vorfahren bis REPO_ROOT."""
    d = (p if p.is_dir() else p.parent).resolve()
    try:
        if any(part.startswith("_") for part in d.relative_to(REPO_ROOT).parts):
            return True
    except ValueError:
        pass
    while True:
        if (d / ".claude-no-index").exists():
            return True
        if d == REPO_ROOT or d.parent == d:
            return False
        d = d.parent


def check_completeness(root: Path, indexes: list[Path], errors: list[str]) -> None:
    index_dirs = {idx.parent.resolve() for idx in indexes}
    cache = {idx.parent.resolve(): idx.read_text(encoding="utf-8", errors="replace") for idx in indexes}
    for md in root.rglob("*.md"):
        if md.name == "_INDEX.md" or ignored(md) or _non_navigated(md):
            continue
        owner = next((p for p in md.resolve().parents if p in index_dirs), None)
        if owner is None:
            continue  # kein Index regiert diesen Ordner — ok
        text = cache[owner]
        rel = md.resolve().relative_to(owner)
        if not (_listed(rel.as_posix(), text) or _listed(rel.name, text)):
            idx_rel = (owner / "_INDEX.md").relative_to(REPO_ROOT)
            errors.append(f"[Vollständigkeit] {md.relative_to(REPO_ROOT)} fehlt im {idx_rel}")
    # owns: Code-/Glob-Completeness — HART, aber nur wo ein Index `owns:` deklariert (opt-in).
    for d, text in cache.items():
        globs = _owns_globs(text)
        if not globs:
            continue
        for f in d.rglob("*"):
            if not f.is_file() or f.name == "_INDEX.md" or ignored(f) or _non_navigated(f):
                continue
            if any(part in IGNORE_DIRS for part in f.parts):
                continue
            if next((p for p in f.resolve().parents if p in index_dirs), None) != d:
                continue  # gehört einem tieferen Index
            rel = f.resolve().relative_to(d)
            if any(fnmatch.fnmatch(f.name, g) or fnmatch.fnmatch(str(rel), g) for g in globs):
                if not (_listed(str(rel), text) or _listed(f.name, text)):
                    idx_rel = (d / "_INDEX.md").relative_to(REPO_ROOT)
                    errors.append(f"[Vollständigkeit/owns] {f.relative_to(REPO_ROOT)} "
                                  f"(owns: {', '.join(globs)}) fehlt im {idx_rel}")


def check_paths(index: Path, errors: list[str]) -> None:
    for raw in PATH_RE.findall(index.read_text(encoding="utf-8", errors="replace")):
        ref = raw.strip()
        if not ref or "/" not in ref or "{{" in ref or "*" in ref or ref.startswith(("http://", "https://")):
            continue
        # Prosa/Platzhalter/Verzeichnis-Referenzen NICHT als harte Datei-Pfade prüfen
        # (kein `<passende Datei>`, kein `data/`-Verzeichnis im Fließtext) — nur echte Dateien:
        if any(c in ref for c in " <>"):
            continue
        pathpart = ref.split("#", 1)[0]
        if pathpart.endswith("/") or "." not in pathpart.rsplit("/", 1)[-1]:
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


def check_routing_quality(index: Path, warnings: list[str]) -> None:
    """C/D: Routing-Qualität (advisory) — Lazy-Fill (identische lies-wenn-Zellen),
    Register-Docs ohne Task-Routing-Zeile, und zu große Flach-Register (>20)."""
    text = index.read_text(encoding="utf-8", errors="replace")
    rel = index.relative_to(REPO_ROOT)
    pathcount = Counter(p.strip() for p in PATH_RE.findall(text))
    reg_paths, liesvals = [], []
    for ln in text.splitlines():
        s = ln.strip()
        if not s.startswith("|") or re.match(r"^\|[\s:|-]+\|?$", s):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        m = re.search(r"`([^`]+)`", cells[0]) if cells else None
        if m and len(cells) >= 3:
            reg_paths.append(m.group(1).strip())
            liesvals.append(cells[-1])
    if not reg_paths:
        return
    for v, n in Counter(v for v in liesvals if v and "{{" not in v).items():
        if n >= 3:
            warnings.append(f"[Routing] {rel}: lies-wenn '{v[:40]}' {n}× identisch (Lazy-Fill? differenziert nicht)")
    only_reg = [p for p in reg_paths if pathcount[p] <= 1]
    if len(only_reg) >= 3:
        warnings.append(f"[Routing] {rel}: {len(only_reg)}/{len(reg_paths)} Register-Docs in keiner "
                        f"Task-Routing-Zeile (nur Flach-Register) — schwer erreichbar")
    if len(reg_paths) > 20:
        warnings.append(f"[Navigation] {rel}: {len(reg_paths)} Register-Zeilen (>20) — Sub-Index/Gruppen "
                        f"erwägen (ein langes Flach-Register ist selbst ein Scan)")


def check_dupes(root: Path, warnings: list[str]) -> None:
    """J: ' N'-Kopien (iCloud) sind aus der Completeness ausgenommen — hier sichtbar machen."""
    for f in root.rglob("*.md"):
        if any(p in IGNORE_DIRS for p in f.parts) or _non_navigated(f):
            continue
        if DUPE_RE.search(f.name) or DUPE_RE.search(f.stem):
            warnings.append(f"[Dupe] {f.relative_to(REPO_ROOT)}: sieht aus wie iCloud-Kopie (' N') — "
                            f"aus dem Gate ausgenommen; prüfen/löschen")


def check_staleness(index: Path, warnings: list[str]) -> None:
    rel = index.relative_to(REPO_ROOT)
    fm = _frontmatter(index.read_text(encoding="utf-8", errors="replace"))
    if not fm:
        return
    if fm.get("status", "").strip().lower() in ("historical", "superseded", "frozen"):
        return  # eingefrorenes Artefakt → staleness-frei (F)
    if "last-reviewed" not in fm:
        warnings.append(f"[Staleness] {rel}: kein last-reviewed-Feld"); return
    try:
        age = (_dt.date.today() - _dt.date.fromisoformat(fm["last-reviewed"].strip())).days
        shelf = int(fm.get("shelf-life-days", "90"))
    except ValueError:
        warnings.append(f"[Staleness] {rel}: last-reviewed/shelf-life-days unlesbar"); return
    if age > shelf:
        warnings.append(f"[Staleness] {rel}: vor {age} d reviewt (> {shelf} d) — auffrischen")


def check_unindexed_areas(root: Path, indexes: list[Path], warnings: list[str]) -> None:
    """Advisory: dateireicher Top-Level-Bereich ohne _INDEX.md irgendwo im Subtree →
    Vollständigkeits-Lücke (z. B. scripts/ mit 26 .py). Kein harter Fehler."""
    index_dirs = {idx.parent.resolve() for idx in indexes}
    for child in sorted(p for p in root.iterdir() if p.is_dir()):
        if child.name in IGNORE_DIRS or child.name.startswith(".") or _non_navigated(child):
            continue
        cr = child.resolve()
        if any(d == cr or cr in d.parents for d in index_dirs):
            continue  # Subtree hat schon irgendwo ein _INDEX.md
        n = sum(1 for f in child.rglob("*")
                if f.is_file() and not any(part in IGNORE_DIRS for part in f.parts))
        if n >= 6:
            warnings.append(f"[Navigation] {child.relative_to(REPO_ROOT)}/ hat {n} Dateien, "
                            f"aber kein _INDEX.md — navigierbarer Bereich ohne Index (erwäge einen).")


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
    check_unindexed_areas(root, indexes, warnings)
    check_dupes(root, warnings)
    for idx in indexes:
        check_paths(idx, errors)
        check_staleness(idx, warnings)
        check_routing_quality(idx, warnings)
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
