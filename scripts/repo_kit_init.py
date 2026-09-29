#!/usr/bin/env python3
"""repo_kit_init — Detection-/Scaffold-Engine für das Claude Repo Kit.

Mechanische Schwerarbeit, deterministisch + idempotent. Wird von install.sh UND
vom /repo-kit:repo-kit-init-Skill genutzt; die *Urteils*-Arbeit (gute Beschreibungen,
echte Projektregeln, „lies-wenn"-Routing) macht danach der Mensch/Claude.

Subcommands (Ziel-Repo = $2 oder cwd):
  detect            JSON: {name, stacks, standards, doc_areas, code_areas}
  prefill-claude F  ersetzt die mechanischen {{Platzhalter}} in F (Repo-Name/Bereiche)
  goi-snippet       druckt den passenden §4-Stack-Block für GOI_DOKTRIN.md (zum Einsetzen)
  prefill-goi F     schreibt §4 (erkannter Stack) in F UND blankt §8-Personenkontext → Platzhalter
  scaffold-index D  schreibt D/_INDEX.md aus dem realen Ordner (Register vollständig)
  scaffold-rules    Monorepo mit Stacks in ≥2 Unterordnern → pfadgebundene .claude/rules/*.md
                    (D7, ARCHITECTURE.md); Single-Stack-Repos: no-op (CLAUDE.md bleibt richtig)
  prune-stub-rules  entfernt UNBERÜHRTE Regel-Stubs, die vor v3.24 fälschlich angelegt wurden
  wire-gate         druckt (oder --apply) die Gate-Verdrahtung (pre-commit/CI/npm)

Kein Tool, kein Netzwerk. Überschreibt nie (→ .new bei Konflikt).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

IGNORE = {".git", "node_modules", "dist", "build", ".venv", "venv", "__pycache__",
          ".stubs", ".next", "out", "target", "templates", "archive"}
# Vom Installer selbst nach scripts/ kopierte Kit-Dateien — dürfen die Stack-Erkennung nicht
# beeinflussen (sonst wird jedes Repo nach dem Kopieren zum „Python (Scripts)"-Repo).
KIT_FILES = {"check_index.py", "repo_kit_init.py", "doctrine_migrations.py", "check_redaction.py"}
# Sentinel für „nichts erkannt" — Aufrufer filtern es, statt es als Stack zu zählen.
STACK_UNKNOWN = "(Stack nicht erkannt — manuell eintragen)"

# ── Detection ────────────────────────────────────────────────────────────────

def repo_name(root: Path) -> str:
    cfg = root / ".git" / "config"
    if cfg.exists():
        m = re.search(r"url\s*=\s*.*/([^/\n]+?)(?:\.git)?\s*$", cfg.read_text(encoding="utf-8", errors="replace"), re.M)
        if m:
            return m.group(1)
    return root.resolve().name


def _candidate_dirs(root: Path) -> list[Path]:
    """root + Unterordner bis Tiefe 2 (IGNORE/Dotdirs ausgelassen) — für Monorepos
    wie rallylab/ (Python) + rallylab-web/ (Next.js)."""
    dirs = [root]
    try:
        for d1 in sorted(p for p in root.iterdir() if p.is_dir()):
            if d1.name in IGNORE or d1.name.startswith("."):
                continue
            dirs.append(d1)
            for d2 in sorted(p for p in d1.iterdir() if p.is_dir()):
                if d2.name not in IGNORE and not d2.name.startswith("."):
                    dirs.append(d2)
    except OSError:
        pass
    return dirs


def detect_stacks(root: Path) -> tuple[list[str], str]:
    stacks: list[str] = []
    std: list[str] = []

    def add(name: str, standard: str) -> None:
        if name not in stacks:
            stacks.append(name)
            std.append(standard)

    for d in _candidate_dirs(root):  # Root UND Subdirs → Monorepos melden ALLE Stacks
        pkg = d / "package.json"
        if pkg.exists():
            try:
                data = json.loads(pkg.read_text(encoding="utf-8", errors="replace"))
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            except Exception:
                deps = {}
            if "next" in deps:
                add("Next.js (TypeScript)",
                    "- TypeScript/Next.js: App Router + React Server Components default; "
                    "Server Actions statt API-Routes wo möglich; `strict: true`, kein `any`; "
                    "Server-/Client-Component-Grenze bewusst (`'use client'` minimal).")
            elif "react" in deps:
                add("React (TypeScript)",
                    "- React/TypeScript: Function-Components + Hooks; `strict: true`; "
                    "abgeleiteter State statt Duplikat; Effects sparsam.")
            else:
                add("Node.js/TypeScript" if (d / "tsconfig.json").exists() else "Node.js",
                    "- Node.js: kleine reine Module; async/await statt Callbacks; "
                    "Fehler früh werfen, nicht schlucken.")
            if any("supabase" in x for x in deps) or (d / "supabase").is_dir():
                add("Supabase",
                    "- Supabase: RLS-first (jede Tabelle eine Policy); SQL-Migrations versioniert; "
                    "Service-Role-Key nie clientseitig; Auth-Rollen explizit.")
        if (d / "pyproject.toml").exists() or (d / "requirements.txt").exists() or (d / "setup.py").exists():
            blob = ""
            for f in ("pyproject.toml", "requirements.txt"):
                p = d / f
                if p.exists():
                    blob += p.read_text(encoding="utf-8", errors="replace").lower()
            ml = any(k in blob for k in ("torch", "tensorflow", "mps", "scikit", "numpy", "opencv", "ultralytics"))
            add("Python (ML)" if ml else "Python",
                "- Python: Type-Hints überall; reine Funktionen, klare I/O-Grenzen; "
                "PEP8; Pfade über `pathlib`. " +
                ("ML: Determinismus/Seeds dokumentieren, Pipeline-Schritte idempotent." if ml else ""))
        if (d / "Cargo.toml").exists():
            add("Rust", "- Rust: `cargo clippy` clean; `Result`/`?` statt `unwrap` im Prod-Pfad.")
        if (d / "go.mod").exists():
            add("Go", "- Go: `gofmt`/`go vet` clean; Fehler explizit zurückgeben, nicht panic.")

    if not stacks:  # kein Manifest irgendwo → aus Quelldatei-Endungen ableiten (Notebook-/Script-Repo)
        exts = Counter(p.suffix.lower() for p in root.rglob("*")
                       if p.is_file() and p.name not in KIT_FILES
                       and not any(part in IGNORE for part in p.parts))
        if exts[".py"] or exts[".ipynb"]:
            stacks.append("Python (Scripts/Notebooks)")
            std.append("- Python: Type-Hints; reine Funktionen, klare I/O-Grenzen; Pfade über `pathlib`. "
                       "Notebooks idempotent halten, Seeds/Determinismus dokumentieren wo relevant.")
        elif exts[".ts"] or exts[".tsx"]:
            stacks.append("TypeScript")
            std.append("- TypeScript: `strict: true`; abgeleiteter State statt Duplikat; kleine reine Module.")
        elif exts[".cs"]:
            stacks.append("C#/.NET")
            std.append("- C#: nullable enable; async/await; klare DI-Grenzen; keine stillen Catches.")
        elif exts[".sql"] or exts[".dax"]:
            stacks.append("Data/Analytics (SQL/DAX)")
            std.append("- SQL/DAX: lesbare CTEs/Measures, keine Magic-Numbers; Quelle→Modell-Trennung sauber halten.")
    if not stacks:
        stacks.append(STACK_UNKNOWN)
        std.append("- {{Code-Standards deines Stacks hier}}")
    return stacks, "\n".join(std)


def count_md(d: Path) -> int:
    return sum(1 for _ in d.rglob("*.md") if not any(p in IGNORE for p in _.parts))


def detect_areas(root: Path) -> tuple[list[str], list[str]]:
    doc, code = [], []
    for child in sorted(p for p in root.iterdir() if p.is_dir()):
        if child.name in IGNORE or child.name.startswith("."):
            continue
        if count_md(child) >= 2:
            doc.append(child.name)
        elif any((child / s).exists() for s in ("src", "app", "lib", "package.json", "pyproject.toml", "__init__.py")) \
                or any(f.name not in KIT_FILES for f in child.glob("*.py")) \
                or any(child.glob("*.ts")) or any(child.glob("*.tsx")):
            code.append(child.name)
    return doc, code


def detect_test_cmd(root: Path) -> str:
    """Projekt-Test-/Check-Kommando erkennen (für das auto-scaffold-Makefile)."""
    for d in _candidate_dirs(root):
        pkg = d / "package.json"
        if pkg.exists():
            try:
                sc = json.loads(pkg.read_text(encoding="utf-8", errors="replace")).get("scripts", {})
            except Exception:
                sc = {}
            if "check" in sc:
                return "npm run check"
            if "test" in sc:
                return "npm test"
    for d in _candidate_dirs(root):
        if (d / "tests").is_dir():
            return "pytest -q"
        pp = d / "pyproject.toml"
        if pp.exists() and "pytest" in pp.read_text(encoding="utf-8", errors="replace").lower():
            return "pytest -q"
    for base in (root, root / "scripts"):
        if base.is_dir():
            for v in sorted(base.glob("validate_*.py")):
                return f"python3 {v.relative_to(root)}"
    return ""


def rule_seeds(root: Path, stacks: list[str]) -> list[tuple[str, str]]:
    """Stack-/Domänen-Regel-SAATEN: Titel = domänenspezifischer Seed, Body bleibt {{…}}
    (du füllst). Keine aktiven Regeln — nur ein besserer Startpunkt als generische Beispiele."""
    sl = " ".join(stacks).lower()
    cdirs = _candidate_dirs(root)
    medallion = (any(any(d.glob(f"*{e}")) for d in cdirs for e in (".dax", ".tmdl"))
                 or "analytics" in sl
                 or any(re.search(r"bronze|silver|gold", p.name, re.I)
                        for d in cdirs for p in d.glob("*.md")))
    seeds: list[tuple[str, str]] = []
    if medallion:
        seeds += [("Medallion-Reihenfolge (Bronze→Silver→Gold)",
                   "{{Regel: nur abwärts Bronze→Silver→Gold schreiben, nie rückwärts; jede Schicht idempotent}}"),
                  ("Nicht-Admin-/Workspace-Grenze",
                   "{{Regel: keine Workspace-Admin-/Capacity-Operationen im Code — nur Daten-/Modell-Ebene}}")]
    if any("next" in s.lower() or "react" in s.lower() for s in stacks):
        seeds.append(("Server-/Client-Grenze",
                      "{{Regel: RSC default, `'use client'` minimal; Server Actions statt API-Routes}}"))
    if any(s.lower().startswith("python") for s in stacks):
        seeds.append(("I/O-Grenzen & Determinismus",
                      "{{Regel: reine Funktionen, klare I/O-Ränder; Seeds/Determinismus dokumentieren}}"))
    if any("supabase" in s.lower() for s in stacks):
        seeds.append(("RLS-first",
                      "{{Regel: jede Tabelle eine Policy; Service-Role-Key nie clientseitig}}"))
    if not seeds:
        seeds = [('{{Regel-Block 1, z. B. „Official-First-Prinzip"}}', "{{…}}"),
                 ('{{Regel-Block 2, z. B. „Build-Pflichtmuster"}}', "{{…}}")]
    return seeds


def scaffold_stack_rules(root: Path) -> list[str]:
    """D7 (docs/ARCHITECTURE.md): Monorepos mit Stacks in ≥2 verschiedenen direkten
    Unterordnern (z. B. `rallylab/`=Python, `rallylab-web/`=Next.js) bekommen pfadgebundene
    `.claude/rules/<dir>.md` (Anthropic-natives Lazy-Load per `paths:`-Frontmatter) statt
    aller Stack-Regel-Seeds gebündelt in der immer geladenen CLAUDE.md — jede Regel lädt nur,
    wenn tatsächlich Dateien unter ihrem Unterordner angefasst werden. Bei nur einem Stack im
    ganzen Repo bleibt CLAUDE.md die richtige Ablage (kein Lazy-Load-Gewinn ohne Trennung).
    Überschreibt nie eine bestehende Regel-Datei (User-editiert bleibt unangetastet)."""
    per_dir: dict[Path, list[str]] = {}
    try:
        for d in sorted(p for p in root.iterdir() if p.is_dir()):
            if d.name in IGNORE or d.name.startswith("."):
                continue
            stacks, _ = detect_stacks(d)
            stacks = [x for x in stacks if x != STACK_UNKNOWN]
            if stacks:
                per_dir[d] = stacks
    except OSError:
        pass
    if len(per_dir) < 2:
        return []
    rules_dir = root / ".claude" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for d, stacks in per_dir.items():
        slug = re.sub(r"[^a-z0-9]+", "-", d.name.lower()).strip("-")
        out = rules_dir / f"{slug}.md"
        if out.exists():
            continue
        out.write_text(_rule_text(d, stacks), encoding="utf-8", newline="\n")
        written.append(out.relative_to(root).as_posix())
    return written


def _rule_text(d: Path, stacks: list[str]) -> str:
    body = "\n\n".join(f"### {t}\n{h}" for t, h in rule_seeds(d, stacks))
    return (f"---\npaths: [\"{d.name}/**\"]\n---\n"
            f"# {', '.join(stacks)} — Stack-Regeln ({d.name}/, pfadgebunden — lädt nur hier)\n\n"
            f"{body}\n")


RULE_HEAD_RE = re.compile(r"^# (.+) — Stack-Regeln \((.+?)/, pfadgebunden", re.M)


def prune_stub_rules(root: Path) -> list[str]:
    """Räumt Regel-Stubs weg, die der Bug vor v3.24 für Nicht-Stack-Ordner angelegt hat
    (Sentinel „Stack nicht erkannt" bzw. die kit-eigenen scripts/ als „Python").

    Gelöscht wird NUR, wenn beides gilt: (1) die Datei ist Byte für Byte das, was die Engine
    damals erzeugt hat — also unberührt, und (2) die heutige Erkennung fände in dem Ordner keinen
    Stack mehr. Eine angefasste oder weiterhin berechtigte Regel bleibt stehen."""
    removed = []
    for f in sorted((root / ".claude" / "rules").glob("*.md")):
        text = f.read_text(encoding="utf-8", errors="replace")
        m = RULE_HEAD_RE.search(text)
        if not m or "{{" not in text:
            continue
        d = root / m.group(2)
        if text != _rule_text(d, m.group(1).split(", ")):
            continue
        now = [x for x in (detect_stacks(d)[0] if d.is_dir() else []) if x != STACK_UNKNOWN]
        if now:
            continue
        tracked = subprocess.run(["git", "-C", str(root), "ls-files", "--error-unmatch", str(f)],
                                 capture_output=True).returncode == 0
        if tracked:
            subprocess.run(["git", "-C", str(root), "rm", "-q", "--cached", str(f)], capture_output=True)
        f.unlink()
        removed.append(f.relative_to(root).as_posix())
    rules = root / ".claude" / "rules"
    if removed and rules.is_dir() and not any(rules.iterdir()):
        rules.rmdir()
    return removed


def detect(root: Path) -> dict:
    stacks, std = detect_stacks(root)
    doc, code = detect_areas(root)
    return {"name": repo_name(root), "stacks": stacks, "standards": std,
            "doc_areas": doc, "code_areas": code, "test_cmd": detect_test_cmd(root)}


# ── Actions ──────────────────────────────────────────────────────────────────

def prefill_claude(claude_md: Path, root: Path) -> None:
    d = detect(root)
    txt = claude_md.read_text(encoding="utf-8", errors="replace")
    a = d["doc_areas"] + d["code_areas"] + ["docs"]
    repl = {
        "{{REPO_NAME}}": d["name"],
        "{{AREA_1}}": a[0] if len(a) > 0 else "docs",
        "{{AREA_2}}": a[1] if len(a) > 1 else "src",
        "{{STRATEGIE/PLANUNGS}}": (a[0].capitalize() if a else "Doku") + "-",
        "{{ENTITY}}": (d["doc_areas"][0] if d["doc_areas"] else "entitäten"),
    }
    for k, v in repl.items():
        txt = txt.replace(k, v)
    # Stack-Hinweis an den Regel-Block hängen (statt blind zu raten).
    hint = (f"<!-- AUTO-DETECT: Stack = {', '.join(d['stacks'])} · "
            f"Doc-Bereiche = {', '.join(d['doc_areas']) or '—'} · "
            f"Code-Bereiche = {', '.join(d['code_areas']) or '—'}. "
            f"Restliche Platzhalter = echtes Urteil (deine Projektregeln). -->")
    txt = txt.replace("## Projekt-spezifische Regeln",
                      "## Projekt-spezifische Regeln\n\n" + hint, 1)
    # Regel-Block-SAATEN: generische `### {{Regel-Block N…}}` + {{…}} durch Stack-Saaten ersetzen
    # (Titel = domänenspezifischer Seed, Body bleibt {{…}} → du füllst). Robust per Regex.
    seed_iter = iter(rule_seeds(root, d["stacks"]))

    def _seed(m):
        try:
            t, h = next(seed_iter)
        except StopIteration:
            return m.group(0)
        return f"### {t}\n{h}"

    txt = re.sub(r"^### \{\{Regel-Block \d[^\n]*\}\}\n\{\{[^}]*\}\}", _seed, txt, flags=re.M)
    # Compliance-Befehl mit erkanntem Test/Check vorbelegen
    txt = txt.replace("{{befehl der vor jedem commit/PR grün sein muss}}",
                      d.get("test_cmd") or "make check", 1)
    claude_md.write_text(txt, encoding="utf-8", newline="\n")
    print(f"✓ prefilled {claude_md.name}: name={d['name']} stacks={d['stacks']} "
          f"test={d.get('test_cmd') or '—'}")


def goi_snippet(root: Path) -> None:
    d = detect(root)
    print("## 4. Code-Standards\n")
    print(d["standards"])
    print(f"\n(Erkannt: {', '.join(d['stacks'])}. In GOI_DOKTRIN.md §4 einsetzen; "
          "§8 Context auf dieses Projekt umschreiben.)")


def _replace_section(text: str, num: int, new_block: str) -> str:
    """Ersetzt den `## <num>. …`-Abschnitt (bis zur nächsten `## N.`-Überschrift)."""
    lines = text.splitlines(keepends=True)
    out, i, n = [], 0, len(lines)
    while i < n:
        if re.match(rf"^## {num}\.\s", lines[i]):
            out.append(new_block if new_block.endswith("\n") else new_block + "\n")
            i += 1
            while i < n and not re.match(r"^## \d", lines[i]):
                i += 1
        else:
            out.append(lines[i]); i += 1
    return "".join(out)


def prefill_goi(goi: Path, root: Path) -> None:
    d = detect(root)
    text = goi.read_text(encoding="utf-8", errors="replace")
    text = _replace_section(text, 4, "## 4. Code-Standards\n\n" + d["standards"] + "\n")
    # Defensiv: die Vorlage hat §8 bereits als Platzhalter — falls doch Personenkontext
    # drinsteht (alte GOI), hier auf Platzhalter ziehen (kein fremder Kontext-Bleed).
    text = re.sub(r"^- Nutze bekannten Kontext.*$",
                  "- Nutze den festen Projekt-Kontext: {{Projekt-Kontext: was ist dieses Projekt, "
                  "Zielgruppe, fester Stack-Kontext}} — ohne ihn zu wiederholen.", text, flags=re.M)
    text = re.sub(r"^- .*(Fabric|Power BI|Nagarro|Freelancer|NGO e\.V\.).*$",
                  "- {{Projekt-Kontext hier eintragen}}", text, flags=re.M)
    goi.write_text(text, encoding="utf-8", newline="\n")
    print(f"✓ GOI §4 gesetzt = {', '.join(d['stacks'])}. §8-Projekt-Kontext bleibt Platzhalter (von dir zu füllen).")


def _doc_purpose(p: Path) -> str:
    """Roh-Zweck aus dem Doc ziehen: erste H1, sonst erste Prosa-Zeile (Frontmatter weg)."""
    try:
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return "{{Zweck — 1 Zeile}}"
    i = 0
    if lines and lines[0].strip() == "---":
        for j in range(1, len(lines)):
            if lines[j].strip() == "---":
                i = j + 1
                break
    h1, prose = None, None
    for ln in lines[i:]:
        s = ln.strip()
        if not s:
            continue
        m = re.match(r"^#\s+(.+)", s)
        if m:
            h1 = m.group(1).strip()
            break
        if prose is None and s[0] not in "#>|`-*<":
            prose = s
    cand = re.sub(r"\s+", " ", (h1 or prose or "")).strip()[:80].rstrip(" .—-")
    return cand.replace("|", r"\|") if cand else "{{Zweck — 1 Zeile}}"


def _doc_topic(p: Path) -> str:
    """lies-wenn-Seed aus dem Dateinamen: Datum raus, -/_ → Leerzeichen (du schärfst)."""
    s = re.sub(r"\d{4}[-_.]\d{2}[-_.]\d{2}", "", p.stem)
    s = re.sub(r"[-_]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()[:40].strip().replace("|", r"\|")


def scaffold_index(folder: Path, root: Path) -> None:
    out = folder / "_INDEX.md"
    if out.exists():
        out = folder / "_INDEX.md.new"
    rows = []
    for md in sorted(folder.rglob("*.md")):
        if md.name in ("_INDEX.md", "_INDEX.md.new") or any(p in IGNORE for p in md.parts):
            continue
        rel = md.relative_to(folder)
        dated = " · datiert → ggf. `status: historical`" if re.search(r"\d{4}-\d{2}-\d{2}", md.name) else ""
        topic = _doc_topic(md)
        lieswenn = f"betrifft {topic}" if topic else "{{lies-wenn}}"
        rows.append(f"| `{rel}` | {_doc_purpose(md)}{dated} | {lieswenn} |")
    big = (f"\n     {len(rows)} Docs (>20): erwäge Sub-Bereiche, z. B. {folder.name}/<gruppe>/_INDEX.md."
           ) if len(rows) > 20 else ""
    body = (
        f"---\nlast-reviewed: {{{{YYYY-MM-DD — beim echten Review setzen, nicht Install-Datum}}}}\nshelf-life-days: 90\n---\n"
        f"# {folder.name} — Zentraler Anlaufpunkt (_INDEX)\n\n"
        f"> Einstieg in `{folder.name}/`. Zuerst diese Datei lesen, dann gezielt zum Doc —\n"
        f"> nicht den ganzen Ordner. Offene Punkte unten im Ledger, nicht im Fließtext.\n\n"
        f"## „Lies-wenn\"-Routing (Token-Disziplin)\n\n"
        f"| Deine Aufgabe ist … | Lies | NICHT nötig |\n|---|---|---|\n"
        f"| {{{{Aufgabe}}}} | `{{{{doc}}}}` | {{{{Rest}}}} |\n\n"
        f"## Dokument-Register (vollständig — Drift-Gate erzwingt das)\n\n"
        f"<!-- Code-Bereich? Frontmatter `owns: *.ts, *.sql` ergänzen → Gate erzwingt auch diese Dateien.{big} -->\n"
        f"| Doc | Zweck | Lies-wenn |\n|---|---|---|\n" + "\n".join(rows) + "\n\n"
        "## Offene Punkte (Ledger — hier abhaken)\n\n"
        "| ID | Punkt | Status | Datum |\n|---|---|---|---|\n| — | — | — | — |\n"
    )
    out.write_text(body, encoding="utf-8", newline="\n")
    print(f"✓ {out.relative_to(root)} ({len(rows)} Docs registriert). "
          f"Jetzt nur noch Zweck/lies-wenn füllen.")


def wire_gate(root: Path, apply: bool) -> None:
    # Commit-/CI-Gate fährt --strict → blockt ungefüllte {{…}}-Gerüste (Qualitäts-Floor).
    cmd = "python3 scripts/check_index.py --strict"
    hook_body = HOOK_BODY
    print("Single-Entry-Gate: Makefile-Vorlage unter .claude/repo-kit/templates/Makefile ins\n"
          "  Repo-Root übernehmen (Make-Repos) → `make check` bündelt Gate + eigene Checks für lokal/CI.\n"
          "  Der versionierte pre-commit-Hook fährt bewusst NUR das Gate — er läuft auch dort, wo\n"
          "  `make check`-Abhängigkeiten fehlen (Cloud-Container, Mitstreiter).")
    if (root / "package.json").exists():
        print('npm-Script (Single-Entry) — in package.json "scripts": '
              '"check": "python3 scripts/check_index.py --strict"  (eigene Checks mit && anhängen)')
    if (root / ".github").is_dir():
        print(f"GitHub-Actions-Step:\n  - run: {cmd}")
    # Hook-Framework? Dann KEINEN eigenen Hook schreiben (das Framework verwaltet die Hook-Datei
    # bzw. core.hooksPath selbst → Kollision). Stattdessen den passenden Eintrag ausgeben.
    # prek (Rust-Neuimplementierung von pre-commit) liest dieselbe .pre-commit-config.yaml.
    lefthook = next((f for f in ("lefthook.yml", ".lefthook.yml", "lefthook.yaml") if (root / f).exists()), "")
    if (root / ".pre-commit-config.yaml").exists():
        print("\n⚠ pre-commit/prek erkannt (.pre-commit-config.yaml) — KEIN eigener Hook geschrieben\n"
              "  (würde kollidieren). Diesen local-Hook eintragen:\n"
              "  - repo: local\n"
              "    hooks:\n"
              "      - id: check-index\n"
              "        name: claude-repo-kit drift+quality gate\n"
              f"        entry: {cmd}\n"
              "        language: system\n"
              "        pass_filenames: false\n"
              "        always_run: true")
        return
    if lefthook:
        print(f"\n⚠ Hook-Framework lefthook erkannt ({lefthook}) — KEIN eigener Hook geschrieben.\n"
              "  Eintragen:\n"
              "  pre-commit:\n"
              "    commands:\n"
              "      check-index:\n"
              f"        run: {cmd}")
        return
    if (root / ".husky").is_dir():
        print("\n⚠ Hook-Framework husky erkannt (.husky/) — KEIN eigener Hook geschrieben.\n"
              f"  In .husky/pre-commit eine Zeile ergänzen:  {cmd}")
        return
    if not apply:
        print(f"\npre-commit (mit --apply automatisch): versioniert unter .githooks/pre-commit +\n"
              f"  git config core.hooksPath .githooks   — Inhalt: {cmd} || exit 1")
        return
    if not (root / ".git").exists():
        return
    target, set_hooks_path, note = _hook_target(root)
    if target is None:
        print(note)
        return
    try:
        changed = _insert_hook_block(target, hook_body)
        if changed is None:
            print(f"\n⚠ {target} ist kein Shell-Skript (Shebang) — Kit-Block NICHT eingefügt, er würde\n"
                  f"  den Hook zerstören. Von Hand ergänzen: {cmd} (Exit-Code ≠ 0 → Commit abbrechen).")
            return
        if set_hooks_path:
            subprocess.run(["git", "-C", str(root), "config", "core.hooksPath", ".githooks"],
                           check=True, capture_output=True)
    except (OSError, subprocess.CalledProcessError) as e:
        # R2/D10: `.git` ist ein Protected Path — in einer Claude-Code-Session läuft der Write
        # über Prompt/Classifier, im `dontAsk`-Modus (CI/headless) wird er HART verweigert.
        print(f"\n⚠ pre-commit-Hook NICHT verdrahtet ({e.__class__.__name__}: {e}).\n"
              "  Häufigster Grund ist kein Defekt, sondern Absicht: `.git` ist ein Protected Path —\n"
              "  in einer Claude-Code-Session muss der Schritt bestätigt werden, headless ist er gesperrt.\n"
              "  → einmal manuell im Terminal:  git config core.hooksPath .githooks\n"
              "  Das Gate AUSFÜHREN ist davon unberührt: `python3 scripts/check_index.py --strict`.\n"
              "  Hintergrund: docs/GATE_HOOKS.md")
        return
    rel = target.relative_to(root) if target.is_relative_to(root) else target
    print(("\n✓ pre-commit-Hook verdrahtet" if changed else "\n= pre-commit-Hook ruft check_index.py bereits auf")
          + f" ({rel}) — strict, portabel (python3/python).")
    if note:
        print(note)


# Der versionierte Hook fährt NUR das Gate (zero-dependency, läuft überall). Bis v3.24 bevorzugte
# er `make check` — richtig, solange der Hook nur lokal lag. Versioniert reist er in Cloud-Container
# und zu Mitstreitern, wo `make check` an fehlenden Abhängigkeiten oder lokalen, vertraulichen
# Dateien scheitert und damit JEDEN Commit blockiert (beim Rollout in Freelancing gefunden).
# `make check` bleibt der Single-Entry für lokal und CI.
HOOK_BODY = (
    "# claude-repo-kit: strict Drift-Gate (zero-dependency; `make check` bleibt für lokal/CI).\n"
    "if command -v python3 >/dev/null 2>&1; then PY=python3; else PY=python; fi\n"
    '"$PY" scripts/check_index.py --strict || exit 1\n'
)
LEGACY_HOOK_BODY = (
    "# claude-repo-kit: strict Gate — `make check` wenn vorhanden, sonst direkt.\n"
    "if [ -f Makefile ] && grep -q '^check:' Makefile && command -v make >/dev/null 2>&1; then\n"
    "  make check || exit 1\n"
    "else\n"
    "  if command -v python3 >/dev/null 2>&1; then PY=python3; else PY=python; fi\n"
    '  "$PY" scripts/check_index.py --strict || exit 1\n'
    "fi\n"
)

SHELL_SHEBANG = re.compile(r"^#!.*\b(sh|bash|dash|zsh|ksh)\b")


def _git_out(root: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
        encoding="utf-8", errors="replace")
    return r.stdout.strip() if r.returncode == 0 else ""


def active_legacy_hooks(root: Path) -> list[str]:
    """Nicht-`.sample`-Hooks im unversionierten Hook-Ordner. Ein `core.hooksPath` würde sie ALLE
    stilllegen — git-lfs (pre-push/post-checkout), commit-msg (Gerrit), eigene Hooks (v3.24-Review)."""
    d = _git_out(root, "rev-parse", "--git-path", "hooks")
    hooks_dir = Path(d) if d else root / ".git" / "hooks"
    hooks_dir = hooks_dir if hooks_dir.is_absolute() else root / hooks_dir
    try:
        found = sorted(f for f in hooks_dir.iterdir() if f.is_file() and not f.name.endswith(".sample"))
    except OSError:
        return []
    # Ein pre-commit, der NUR den Kit-Block trägt (Install vor v3.24), zählt nicht: er ist ersetzbar.
    return [f.name for f in found if not (f.name == "pre-commit" and _kit_only(f))]


KIT_HOOK_LINES = ("if [ -f Makefile ]", "make check", "else", "fi", "if command -v python3", '"$PY"')


def _kit_only(hook: Path) -> bool:
    try:
        lines = hook.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return False
    return not [ln for ln in lines if ln.strip() and not ln.startswith("#") and "check_index.py" not in ln
                and not ln.strip().startswith(KIT_HOOK_LINES)]


def _hook_target(root: Path) -> tuple[Path | None, bool, str]:
    """Wohin der Gate-Aufruf gehört (D16). Bevorzugt ein VERSIONIERTER Hook unter `.githooks/`
    (+ `core.hooksPath`) — `.git/hooks` reist nicht mit: fehlt in jedem Clone, im Team und in
    jedem Cloud-Container. Rückgabe: (Hook-Datei oder None, core.hooksPath setzen?, Hinweis).

    Nie angefasst werden: ein GLOBALER hooksPath (gilt für jedes Repo des Rechners — der Kit-Block
    liefe dann überall) und bestehende Hooks im unversionierten Ordner (hooksPath legte sie still)."""
    local = _git_out(root, "config", "--local", "core.hooksPath")
    if local:
        d = Path(local).expanduser()
        return (d if d.is_absolute() else root / d) / "pre-commit", False, ""
    effective = _git_out(root, "config", "core.hooksPath")
    if effective:
        return None, False, (
            f"\n⚠ Globaler core.hooksPath ({effective}) — NICHT angefasst: ein Eintrag dort liefe in JEDEM\n"
            "  Repo dieses Rechners. Entweder dort von Hand einen repo-bedingten Aufruf ergänzen oder\n"
            "  in diesem Repo `git config --local core.hooksPath .githooks` setzen (dann gelten deine\n"
            "  globalen Hooks hier nicht mehr).")
    legacy_dir = _git_out(root, "rev-parse", "--git-path", "hooks") or ".git/hooks"
    legacy = (Path(legacy_dir) if Path(legacy_dir).is_absolute() else root / legacy_dir) / "pre-commit"
    others = active_legacy_hooks(root)
    if others:
        return legacy, False, (
            f"  ⚠ Bestehende, unversionierte Hooks ({', '.join(others)}) — core.hooksPath würde sie\n"
            "    stilllegen, deshalb in .git/hooks ergänzt. Der Hook fehlt so in Clones/Cloud: Hooks nach\n"
            "    .githooks/ umziehen, dann `git config core.hooksPath .githooks`.")
    return root / ".githooks" / "pre-commit", True, (
        "  Versioniert unter .githooks/ — Mitstreiter aktivieren ihn einmal mit\n"
        "  `git config core.hooksPath .githooks`; Claude-Code-Sessions erledigen das per SessionStart-Hook.")


def _insert_hook_block(hook: Path, body: str) -> bool | None:
    """Kit-Block DIREKT nach dem Shebang einfügen, nicht anhängen: ein bestehender Hook, der mit
    `exit 0` endet, würde einen angehängten Block nie erreichen. False = war schon drin,
    None = bestehender Hook ist kein Shell-Skript (Python/Node) — dann nichts anfassen."""
    existing = hook.read_text(encoding="utf-8", errors="replace") if hook.exists() else "#!/usr/bin/env sh\n"
    if LEGACY_HOOK_BODY in existing.replace("\r\n", "\n") and hook.parent.name == ".githooks":
        # Nur im VERSIONIERTEN Hook ersetzen: dort reist er in Umgebungen ohne make-Abhängigkeiten.
        # Ein lokaler .git/hooks-Hook darf `make check` behalten.
        with open(hook, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(existing.replace("\r\n", "\n").replace(LEGACY_HOOK_BODY, body))
        return True
    if "check_index.py" in existing:
        return False
    lines = existing.splitlines(keepends=True)
    if lines and lines[0].startswith("#!") and not SHELL_SHEBANG.match(lines[0]):
        return None
    head = lines[0] if lines and lines[0].startswith("#!") else "#!/usr/bin/env sh\n"
    rest = lines[1:] if lines and lines[0].startswith("#!") else lines
    hook.parent.mkdir(parents=True, exist_ok=True)
    # LF erzwingen: unter Windows schriebe write_text CRLF → `then\r` bricht den sh-Hook.
    with open(hook, "w", encoding="utf-8", newline="\n") as fh:
        fh.write((head + body + "".join(rest)).replace("\r\n", "\n"))
    try:
        hook.chmod(0o755)
    except OSError:
        pass
    return True


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__); return 2
    cmd = argv[1]
    root = Path(argv[3]).resolve() if (cmd in ("prefill-claude", "scaffold-index", "prefill-goi") and len(argv) > 3) \
        else Path(argv[2]).resolve() if (cmd in ("detect", "goi-snippet", "wire-gate", "scaffold-rules", "prune-stub-rules") and len(argv) > 2 and not argv[2].startswith("--")) \
        else Path.cwd()
    if cmd == "detect":
        print(json.dumps(detect(root), ensure_ascii=False, indent=2))
    elif cmd == "prefill-claude":
        prefill_claude(Path(argv[2]).resolve(), root)
    elif cmd == "goi-snippet":
        goi_snippet(root)
    elif cmd == "prefill-goi":
        prefill_goi(Path(argv[2]).resolve(), root)
    elif cmd == "scaffold-index":
        scaffold_index(Path(argv[2]).resolve(), root)
    elif cmd == "scaffold-rules":
        written = scaffold_stack_rules(root)
        print(f"✓ .claude/rules/: {', '.join(written)}" if written
              else "(kein Monorepo mit Stacks in ≥2 Unterordnern — CLAUDE.md bleibt richtig)")
    elif cmd == "prune-stub-rules":
        removed = prune_stub_rules(root)
        if removed:
            print(f"✓ unberührte Stub-Regeln aus dem Bug vor v3.24 entfernt: {', '.join(removed)}")
    elif cmd == "wire-gate":
        wire_gate(root, "--apply" in argv)
    else:
        print(__doc__); return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
