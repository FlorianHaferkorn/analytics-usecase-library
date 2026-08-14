"""package_skill.py — export the Visual Library as a self-contained, drop-in skill bundle.

Workflow B (optimise an existing customer report, no ALUCA core) needs the library WITHOUT the
semantic model, bracket, or generator. This packages exactly the dependency-free surface —
`render.py` + `resolve.py` + the governed YAML/goldens + `tokens/layout_grid.yaml` + the SKILL.md —
into one directory a consumer drops into their repo's `.claude/skills/`.

It is GENERATED, never hand-copied (the `pbi-design` skill's 6 hand-maintained copies are the drift
risk this avoids). The bundle preserves the relative paths `render.py` resolves at runtime
(`parents[2]/core/templates/page_templates/...`), so the copied code works unchanged.

    py -3 tooling/visual_library/package_skill.py [--out dist/skills/visual-library]

Emits a `manifest.json` (file list + counts) and runs a standalone smoke check (resolve a purpose
from inside the bundle) so a broken export fails loudly.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render  # noqa: E402 — for the canonical source paths (REPO_ROOT, LIB)

REPO_ROOT = render.REPO_ROOT
LIB = render.LIB
_REL_LIB = "core/templates/page_templates/visual_library"
_REL_TOKENS = "core/templates/page_templates/tokens"


def build(out_dir: Path) -> dict:
    """Assemble the bundle at out_dir; return a manifest dict."""
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    # 1) the zero-dependency tooling, at the path render.py expects (parents[2] = bundle root)
    tool_src = Path(__file__).resolve().parent  # tooling/visual_library/ (where render.py/resolve.py live)
    tool_dst = out_dir / "tooling" / "visual_library"
    tool_dst.mkdir(parents=True)
    # render.py + resolve.py (chooser / audit / fit / why-not) + contrast.py (CVD-safe palette +
    # WCAG/CIEDE2000 checks) + a11y.py (alt-text / data-table). visreg.py is intentionally NOT
    # shipped — it is a CI regression tool needing Pillow/numpy, not a zero-dependency generation
    # feature.
    for name in ("render.py", "resolve.py", "contrast.py", "a11y.py"):
        shutil.copy2(tool_src / name, tool_dst / name)

    # 2) the governed SoT (idioms + goldens + schema + index + profiles + anti-pattern catalog)
    shutil.copytree(LIB, out_dir / _REL_LIB)

    # 3) the token files the tooling reads: the layout grid (render.grid_px) and the colour
    #    semantics (contrast.py's governed CVD-safe categorical palette lives here as SoT)
    tok_dst = out_dir / _REL_TOKENS
    tok_dst.mkdir(parents=True)
    shutil.copy2(LIB.parent / "tokens" / "layout_grid.yaml", tok_dst / "layout_grid.yaml")
    shutil.copy2(LIB.parent / "tokens" / "color_semantics.yaml", tok_dst / "color_semantics.yaml")

    # 4) the skill entry + a usage README
    skill_src = REPO_ROOT / "skills" / "visual-library" / "SKILL.md"
    if skill_src.exists():
        shutil.copy2(skill_src, out_dir / "SKILL.md")
    (out_dir / "README.md").write_text(_README, encoding="utf-8")

    files = sorted(str(p.relative_to(out_dir)).replace("\\", "/") for p in out_dir.rglob("*") if p.is_file())
    manifest = {
        "bundle": "visual-library",
        "generated_by": "tooling/visual_library/package_skill.py",
        "idiom_yaml": sum(1 for f in files if f.startswith(_REL_LIB) and f.endswith(".yaml")
                          and "/golden/" not in f and not Path(f).name.startswith("_")
                          and Path(f).name != "index.yaml"),
        "golden_files": sum(1 for f in files if "/golden/" in f),
        "file_count": len(files),
        "files": files,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def smoke(out_dir: Path) -> str:
    """Prove the bundle works standalone: run resolve (purpose + data-fit), contrast (CVD palette)
    and a11y (alt-text) from inside the bundle — so a broken export of ANY shipped tool fails loudly."""
    tools = out_dir / "tooling" / "visual_library"

    def _run(script, *args):
        return subprocess.run([sys.executable, str(tools / script), *args],
                              capture_output=True, text=True, timeout=60)

    r = _run("resolve.py", "purpose", "compare_categories")
    if r.returncode != 0 or "bar_ranking" not in r.stdout:
        raise RuntimeError(f"bundle smoke (purpose) failed (rc={r.returncode}): {r.stderr[:300] or r.stdout[:300]}")

    f = _run("resolve.py", "fit", "donut", "category=7")
    if f.returncode != 1 or "pie_or_donut_gt_4" not in f.stdout:
        raise RuntimeError(f"bundle smoke (fit) failed (rc={f.returncode}): {f.stderr[:300] or f.stdout[:300]}")

    c = _run("contrast.py", "palette", "6")
    if c.returncode != 0 or "okabe_ito" not in c.stdout:
        raise RuntimeError(f"bundle smoke (contrast) failed (rc={c.returncode}): {c.stderr[:300] or c.stdout[:300]}")

    a = _run("a11y.py", "alt", "donut")
    if a.returncode != 0 or "Donut" not in a.stdout:
        raise RuntimeError(f"bundle smoke (a11y) failed (rc={a.returncode}): {a.stderr[:300] or a.stdout[:300]}")

    return r.stdout.strip().splitlines()[0]


_README = """# Visual Library — standalone bundle

A self-contained, ALUCA-core-independent copy of the governed Visual Library, for reviewing and
upgrading an existing Power BI report. Generated by `package_skill.py` — do not hand-edit; re-export.

## Use

```bash
# which governed chart fits an analytical question?
python tooling/visual_library/resolve.py purpose <purpose_id> [--profile ibcs|print_safe]

# is an existing visual governed / denied? what should replace it?
python tooling/visual_library/resolve.py audit path/to/visual.json

# does the bound data fit the idiom? (cardinality/type vs the data_fit contract)
python tooling/visual_library/resolve.py fit donut category=7   # -> UNFIT: pie_or_donut_gt_4

# why can this idiom be the wrong choice? (governed anti-patterns + fixes)
python tooling/visual_library/resolve.py why-not <idiom_id>

# render the runnable code for an idiom x tool (reads <idiom>.yaml)
python tooling/visual_library/render.py <idiom> <tool>

# a colour-vision-deficiency-safe series palette (+ which colours need an outline on white)
python tooling/visual_library/contrast.py palette 6
python tooling/visual_library/contrast.py check "#0072B2" "#D55E00" "#009E73"   # min ΔE under CVD

# an accessible alt-text / aria description for an idiom (data-driven when a summary is supplied)
python tooling/visual_library/a11y.py alt <idiom_id>
```

Ships render.py + resolve.py + contrast.py + a11y.py (all zero-dependency, Python + PyYAML only).
The perceptual visual-regression tool (visreg.py) is NOT included — it is a CI gate needing
Pillow/numpy, not a generation feature.

Requires only Python + PyYAML. No semantic model, no bracket, no generator.
The source of truth is `core/templates/page_templates/visual_library/`.
"""


def main(argv: list[str]) -> int:
    out = Path(argv[argv.index("--out") + 1]) if "--out" in argv \
        else REPO_ROOT / "tooling" / "visual_library" / "dist" / "skills" / "visual-library"
    m = build(out)
    first = smoke(out)
    print(f"built {m['file_count']} files ({m['idiom_yaml']} idioms, {m['golden_files']} goldens) -> {out}")
    print(f"smoke: {first}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
