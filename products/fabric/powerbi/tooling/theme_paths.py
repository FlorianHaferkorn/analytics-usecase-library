"""Where ALUCA's Power BI themes live, and how a theme name resolves to a file.

Since 2026-09-29 there is one canonical theme engine: Freelancing ``products/pbi_theme``.
ALUCA consumes its **output** — tool-free theme JSONs — as a vendored, pinned copy
(ADR-0005: vendor + PIN, no submodule). Three places, each with one owner:

``VENDORED_THEMES`` (``products/fabric/powerbi/themes/``)
    Byte-identical copy of the engine output, ``PIN.json`` with sha256 per file. Read-only
    here; re-mirrored with ``scripts/check_dataarch_mirror.py --write-themes``, guarded by the
    same sensor.
``LOCAL_THEMES`` (``products/fabric/powerbi/themes_local/``)
    ALUCA-owned output: themes generated on demand by the Freelancing engine
    (``apply_report_theme.py --run-generator``) and brand-spec derivations
    (``tooling/brand/derive_brand_artifacts.py``). Nothing is ever written into a foreign tree.
``THEME_DEFAULTS`` (``products/fabric/powerbi/tooling/theme_defaults.json``)
    Framework-wide ``defaultThemeName`` (formerly ``themes.config.json`` inside the submodule).

Theme names: the engine writes file names without ``#`` (``#`` is a fragment delimiter in the
OPC part URI a published report uses), while theme-internal names and older configs carry
``__#RRGGBB``. Lookup therefore compares stems with ``#`` removed.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable, Optional

REPO_ROOT = Path(__file__).resolve().parents[4]
POWERBI_DIR = REPO_ROOT / "products" / "fabric" / "powerbi"
VENDORED_THEMES = POWERBI_DIR / "themes"
LOCAL_THEMES = POWERBI_DIR / "themes_local"
THEME_DEFAULTS = POWERBI_DIR / "tooling" / "theme_defaults.json"

ENGINE_MODULE = "products.pbi_theme.tools.theme_generator"
_ENGINE_CLI = Path("products") / "pbi_theme" / "tools" / "theme_generator" / "cli.py"
ENGINE_A11Y_EXIT = 3


def theme_key(name: str) -> str:
    """Comparable key for a theme name or file name: stem without ``.json`` and ``#``."""
    stem = Path(name).name
    if stem.lower().endswith(".json"):
        stem = stem[:-5]
    return stem.replace("#", "")


def theme_roots() -> tuple[Path, ...]:
    """Search order: ALUCA-owned local output first, then the vendored engine output."""
    return (LOCAL_THEMES, VENDORED_THEMES)


def find_theme(name: str, roots: Optional[Iterable[Path]] = None) -> Optional[Path]:
    """Locate a theme JSON by name (with or without ``.json``, with or without ``#``)."""
    key = theme_key(name)
    for root in (roots if roots is not None else theme_roots()):
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("*.json")):
            if p.name in ("PIN.json", "manifest.json"):
                continue
            if theme_key(p.name) == key:
                return p
    return None


def freelancing_root() -> Optional[Path]:
    """The Freelancing checkout that holds the engine, or None.

    Same resolution as ``scripts/check_dataarch_mirror.py``: ``$MERIDIAN_ROOT``, else the
    sibling ``../Freelancing``.
    """
    env = os.environ.get("MERIDIAN_ROOT")
    candidates = [Path(env).expanduser()] if env else [REPO_ROOT.parent / "Freelancing"]
    for c in candidates:
        if (c / _ENGINE_CLI).is_file():
            return c
    return None


def run_engine(color: str, concept: str, mode: str, brand: str,
               secondary: Optional[str] = None, out_dir: Path = LOCAL_THEMES) -> Optional[Path]:
    """Generate a theme with the Freelancing engine into an ALUCA-owned directory.

    Returns ``out_dir`` when the engine ran, ``None`` when it did not run because no
    Freelancing checkout is reachable (soft skip — the caller then uses vendored themes).
    Raises ``RuntimeError`` when the engine ran and failed; exit 3 means the WCAG/CVD gate
    rejected the theme, which is a finding, not something to override here.
    """
    root = freelancing_root()
    if root is None:
        print("[theme-engine] NICHT GELAUFEN: kein Freelancing-Checkout ($MERIDIAN_ROOT oder "
              "../Freelancing) — es werden die vendorten Themes verwendet.", file=sys.stderr)
        return None
    out_dir = Path(out_dir).resolve()
    # Erst in ein Zwischenverzeichnis: ein Theme, das das Tor ablehnt, landet nie dort,
    # wo find_theme() es als lieferbar fände.
    with tempfile.TemporaryDirectory(prefix="aluca_theme_") as tmp:
        cmd = [sys.executable, "-m", ENGINE_MODULE, "-c", color, "-k", concept, "-m", mode,
               "-b", brand, "--out", tmp, "--theme-only"]
        if secondary:
            cmd += ["-s", secondary]
        env = {**os.environ, "PYTHONPATH": str(root)}
        proc = subprocess.run(cmd, cwd=str(root), env=env)
        if proc.returncode == ENGINE_A11Y_EXIT:
            raise RuntimeError("Theme-Engine: das WCAG/CVD-Tor hat das erzeugte Theme abgelehnt "
                               "(Exit 3). Befunde siehe Ausgabe oben; Theme nicht ausliefern.")
        if proc.returncode != 0:
            raise RuntimeError(f"Theme-Engine endete mit Exit {proc.returncode} ({root}).")
        for src in Path(tmp).rglob("*.json"):
            if src.name == "manifest.json":
                continue
            ziel = out_dir / src.relative_to(tmp)
            ziel.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, ziel)
    return out_dir
