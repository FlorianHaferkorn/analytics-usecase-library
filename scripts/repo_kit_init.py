#!/usr/bin/env python3
"""repo_kit_init — Detection-/Scaffold-Engine für das Claude Repo Kit.

Mechanische Schwerarbeit, deterministisch + idempotent. Wird von install.sh UND
vom /repo-kit-init-Skill genutzt; die *Urteils*-Arbeit (gute Beschreibungen,
echte Projektregeln, „lies-wenn"-Routing) macht danach der Mensch/Claude.

Subcommands (Ziel-Repo = $2 oder cwd):
  detect            JSON: {name, stacks, standards, doc_areas, code_areas}
  prefill-claude F  ersetzt die mechanischen {{Platzhalter}} in F (Repo-Name/Bereiche)
  goi-snippet       druckt den passenden §4-Stack-Block für GOI_DOKTRIN.md (zum Einsetzen)
  prefill-goi F     schreibt §4 (erkannter Stack) in F UND blankt §8-Personenkontext → Platzhalter
  scaffold-index D  schreibt D/_INDEX.md aus dem realen Ordner (Register vollständig)
  wire-gate         druckt (oder --apply) die Gate-Verdrahtung (pre-commit/CI/npm)

Kein Tool, kein Netzwerk. Überschreibt nie (→ .new bei Konflikt).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

IGNORE = {".git", "node_modules", "dist", "build", ".venv", "venv", "__pycache__",
          ".stubs", ".next", "out", "target", "templates", "archive"}

# ── Detection ────────────────────────────────────────────────────────────────

def repo_name(root: Path) -> str:
    cfg = root / ".git" / "config"
    if cfg.exists():
        m = re.search(r"url\s*=\s*.*/([^/\n]+?)(?:\.git)?\s*$", cfg.read_text(errors="replace"), re.M)
        if m:
            return m.group(1)
    return root.resolve().name


def detect_stacks(root: Path) -> tuple[list[str], str]:
    stacks: list[str] = []
    std: list[str] = []
    pkg = root / "package.json"
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text(errors="replace"))
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        except Exception:
            deps = {}
        if "next" in deps:
            stacks.append("Next.js (TypeScript)")
            std.append("- TypeScript/Next.js: App Router + React Server Components default; "
                       "Server Actions statt API-Routes wo möglich; `strict: true`, kein `any`; "
                       "Server-/Client-Component-Grenze bewusst (`'use client'` minimal).")
        elif "react" in deps:
            stacks.append("React (TypeScript)")
            std.append("- React/TypeScript: Function-Components + Hooks; `strict: true`; "
                       "abgeleiteter State statt Duplikat; Effects sparsam.")
        else:
            stacks.append("Node.js/TypeScript" if (root / "tsconfig.json").exists() else "Node.js")
            std.append("- Node.js: kleine reine Module; async/await statt Callbacks; "
                       "Fehler früh werfen, nicht schlucken.")
        if any("supabase" in d for d in deps) or (root / "supabase").is_dir():
            stacks.append("Supabase")
            std.append("- Supabase: RLS-first (jede Tabelle eine Policy); SQL-Migrations versioniert; "
                       "Service-Role-Key nie clientseitig; Auth-Rollen explizit.")
    if (root / "pyproject.toml").exists() or (root / "requirements.txt").exists() or (root / "setup.py").exists():
        blob = ""
        for f in ("pyproject.toml", "requirements.txt"):
            p = root / f
            if p.exists():
                blob += p.read_text(errors="replace").lower()
        ml = any(k in blob for k in ("torch", "tensorflow", "mps", "scikit", "numpy", "opencv", "ultralytics"))
        stacks.append("Python (ML)" if ml else "Python")
        std.append("- Python: Type-Hints überall; reine Funktionen, klare I/O-Grenzen; "
                   "PEP8; Pfade über `pathlib`. " +
                   ("ML: Determinismus/Seeds dokumentieren, Pipeline-Schritte idempotent." if ml else ""))
    for marker, name, s in [
        ("Cargo.toml", "Rust", "- Rust: `cargo clippy` clean; `Result`/`?` statt `unwrap` im Prod-Pfad."),
        ("go.mod", "Go", "- Go: `gofmt`/`go vet` clean; Fehler explizit zurückgeben, nicht panic."),
    ]:
        if (root / marker).exists():
            stacks.append(name); std.append(s)
    if not stacks:
        stacks.append("(Stack nicht erkannt — manuell eintragen)")
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
                or any(child.glob("*.py")) or any(child.glob("*.ts")) or any(child.glob("*.tsx")):
            code.append(child.name)
    return doc, code


def detect(root: Path) -> dict:
    stacks, std = detect_stacks(root)
    doc, code = detect_areas(root)
    return {"name": repo_name(root), "stacks": stacks, "standards": std,
            "doc_areas": doc, "code_areas": code}


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
            f"Restliche {{{{…}}}} = echtes Urteil (deine Projektregeln). -->")
    txt = txt.replace("## Projekt-spezifische Regeln",
                      "## Projekt-spezifische Regeln\n\n" + hint, 1)
    claude_md.write_text(txt, encoding="utf-8")
    print(f"✓ prefilled {claude_md.name}: name={d['name']} areas={a[:2]} stacks={d['stacks']}")


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
    # §8: persönlichen Kontext-Bullet auf Platzhalter setzen (kein fremder Kontext-Bleed).
    text = re.sub(r"^- Nutze bekannten Kontext.*$",
                  "- Nutze den festen Projekt-Kontext: {{Projekt-Kontext: was ist dieses Projekt, "
                  "Zielgruppe, fester Stack-Kontext}} — ohne ihn zu wiederholen.", text, flags=re.M)
    text = re.sub(r"^- .*(Fabric|Power BI|Nagarro|Freelancer|NGO e\.V\.).*$",
                  "- {{Projekt-Kontext hier eintragen}}", text, flags=re.M)
    goi.write_text(text, encoding="utf-8")
    print(f"✓ GOI: §4 = {', '.join(d['stacks'])}; §8-Personenkontext → Platzhalter.")


def scaffold_index(folder: Path, root: Path) -> None:
    out = folder / "_INDEX.md"
    if out.exists():
        out = folder / "_INDEX.md.new"
    import datetime
    try:
        today = datetime.date.today().isoformat()
    except Exception:
        today = "{{YYYY-MM-DD}}"
    rows = []
    for md in sorted(folder.rglob("*.md")):
        if md.name in ("_INDEX.md", "_INDEX.md.new") or any(p in IGNORE for p in md.parts):
            continue
        rel = md.relative_to(folder)
        rows.append(f"| `{rel}` | {{{{Zweck — 1 Zeile}}}} | {{{{lies-wenn}}}} |")
    body = (
        f"---\nlast-reviewed: {today}\nshelf-life-days: 90\n---\n"
        f"# {folder.name} — Zentraler Anlaufpunkt (_INDEX)\n\n"
        f"> Einstieg in `{folder.name}/`. Zuerst diese Datei lesen, dann gezielt zum Doc —\n"
        f"> nicht den ganzen Ordner. Offene Punkte unten im Ledger, nicht im Fließtext.\n\n"
        f"## „Lies-wenn\"-Routing (Token-Disziplin)\n\n"
        f"| Deine Aufgabe ist … | Lies | NICHT nötig |\n|---|---|---|\n"
        f"| {{{{Aufgabe}}}} | `{{{{doc}}}}` | {{{{Rest}}}} |\n\n"
        f"## Dokument-Register (vollständig — Drift-Gate erzwingt das)\n\n"
        f"| Doc | Zweck | Lies-wenn |\n|---|---|---|\n" + "\n".join(rows) + "\n\n"
        f"## Offene Punkte (Ledger — hier abhaken)\n\n"
        f"| ID | Punkt | Status | Datum |\n|---|---|---|---|\n| — | — | — | — |\n"
    )
    out.write_text(body, encoding="utf-8")
    print(f"✓ {out.relative_to(root)} ({len(rows)} Docs registriert). "
          f"Jetzt nur noch Zweck/lies-wenn füllen.")


def wire_gate(root: Path, apply: bool) -> None:
    # Commit-/CI-Gate fährt --strict → blockt ungefüllte {{…}}-Gerüste (Qualitäts-Floor).
    cmd = "python3 scripts/check_index.py --strict"
    # Pre-commit-Hook portabel: python3 ODER python (Windows/Git-Bash hat oft nur 'python').
    hook_body = (
        "# claude-repo-kit: strict Drift-/Qualitäts-Gate (blockt ungefüllte {{…}})\n"
        "if command -v python3 >/dev/null 2>&1; then PY=python3; else PY=python; fi\n"
        '"$PY" scripts/check_index.py --strict || exit 1\n'
    )
    if (root / "package.json").exists():
        print(f'npm-Script — in package.json "scripts" einfügen:\n  "check:index": "{cmd}"')
    if (root / ".github").is_dir():
        print(f"\nGitHub-Actions-Step:\n  - run: {cmd}")
    hook = root / ".git" / "hooks" / "pre-commit"
    if apply and (root / ".git").is_dir():
        existing = hook.read_text() if hook.exists() else "#!/usr/bin/env sh\n"
        if "check_index.py" not in existing:
            hook.write_text(existing.rstrip() + "\n" + hook_body)
            hook.chmod(0o755)
            print(f"\n✓ pre-commit-Hook verdrahtet ({hook.relative_to(root)}) — strict, portabel (python3/python).")
        else:
            print("\n= pre-commit-Hook ruft check_index.py bereits auf.")
    else:
        print(f"\npre-commit (mit --apply automatisch): in .git/hooks/pre-commit:\n  {cmd} || exit 1")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__); return 2
    cmd = argv[1]
    root = Path(argv[3]).resolve() if (cmd in ("prefill-claude", "scaffold-index", "prefill-goi") and len(argv) > 3) \
        else Path(argv[2]).resolve() if (cmd in ("detect", "goi-snippet", "wire-gate") and len(argv) > 2 and not argv[2].startswith("--")) \
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
    elif cmd == "wire-gate":
        wire_gate(root, "--apply" in argv)
    else:
        print(__doc__); return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
