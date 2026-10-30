"""render_evidence.py — Bild-Evidenz fuer den Judge: Screenshots je Variante, optional mit gesätem Fehler.

D-826 (Freelancing-Register, 27.10.2026): kein positives Urteil ohne passende Bild-Evidenz; ein
gesäter Fehler muss gefunden werden. Dieses Modul liefert beides fuer einen gerenderten HTML-Report:

  * `capture(html, out_dir, label)` — je Breite (`desktop` 1440 px, `mobil` 390 px) und Modus
    (`hell`, `dunkel`) eine ganzseitige Aufnahme, zerlegt in Kacheln von Viewport-Hoehe
    (`<out>/<label>/<breite>/<modus>/<n>.png`). Kacheln statt einem langen Bild: das Modell
    verkleinert lange Bilder, und abgeschnittene Beschriftungen gehen genau dabei verloren.
    Seitliches Scrollen bleibt sichtbar, weil die Kachel die volle Scrollbreite aufnimmt.
  * `SEEDS` — Fehler, die vor der Aufnahme eingespielt werden, je gegen eine Rubrikregel. Die
    Aufnahme traegt dasselbe Label wie die saubere (Blindheit), sie liegt nur in eigenem `--out`. Sie
    greifen nur auf allgemeine Merkmale (SVG-Marken, Schriftgroesse), nie auf Klassen eines
    Frontends — derselbe Seed gilt fuer jeden HTML-Prüfling.

Playwright ist optional (wie das Modell im LLM-Backend): ohne es meldet `capture` den Grund.

    python -m tooling.report_quality.render_evidence --html build/UC-FIN-002.html \\
        --label UC-FIN-002 --out build/render_evidence [--seed regenbogen]
"""
from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

#: Breiten (Name → Viewport). Mobil = 390 px, die Zielbreite der Artefakt- und Cockpit-Regeln.
VIEWPORTS: dict[str, tuple[int, int]] = {"desktop": (1440, 900), "mobil": (390, 844)}
#: Modi (Name → `prefers-color-scheme`).
SCHEMES: dict[str, str] = {"hell": "light", "dunkel": "dark"}
#: Pflichtvarianten eines positiven Urteils ueber diese Evidenz (`LLMJudge(required_variants=…)`).
REQUIRED_VARIANTS = frozenset({*VIEWPORTS, *SCHEMES})


@dataclass(frozen=True)
class Seed:
    """Ein gesäter Fehler: verletzt `rule_id`, eingespielt per Skript vor der Aufnahme."""
    rule_id: str
    beschreibung: str
    script: str


SEEDS: dict[str, Seed] = {
    # BC-COLOR-01: ein neutraler Grund und genau ein Akzent. Der Seed faerbt jede Datenmarke in
    # einer eigenen Farbe — Kontext ist danach nicht mehr gedaempft, Fokus nicht mehr erkennbar.
    "regenbogen": Seed(
        "BC-COLOR-01",
        "jede SVG-Datenmarke in einer eigenen gesaettigten Farbe",
        """
        const marks = [...document.querySelectorAll('svg rect, svg path, svg circle, svg polyline, svg line')]
          .filter(el => { const b = el.getBBox ? el.getBBox() : {width: 0, height: 0};
                          return b.width * b.height > 4 || b.width > 20 || b.height > 20; });
        marks.forEach((el, i) => {
          const c = `hsl(${(i * 47) % 360} 90% 50%)`;
          el.style.setProperty('fill', el.getAttribute('fill') === 'none' ? 'none' : c, 'important');
          el.style.setProperty('stroke', c, 'important');
        });
        """,
    ),
    # BC-LAYOUT-03: eine dominante Zahl fuehrt. Der Seed setzt jede grosse Schrift (≥ 24 px) auf
    # die Groesse des Fliesstexts — die Hierarchie wird flach.
    "flach": Seed(
        "BC-LAYOUT-03",
        "jede Schrift ab 24 px auf die Fliesstextgroesse gesetzt",
        """
        const body = parseFloat(getComputedStyle(document.body).fontSize) || 14;
        for (const el of document.querySelectorAll('body *')) {
          if (parseFloat(getComputedStyle(el).fontSize) >= 24) {
            el.style.setProperty('font-size', body + 'px', 'important');
          }
        }
        """,
    ),
}


def tile_offsets(page_height: int, tile_height: int) -> list[int]:
    """Obere Kanten der Kacheln; die letzte Kachel endet am Seitenende. Pure — unit-getestet."""
    if page_height <= 0 or tile_height <= 0:
        return []
    return [i * tile_height for i in range(math.ceil(page_height / tile_height))]


def capture(html: Path, out_dir: Path, label: str, seed: Optional[str] = None,
            settle_ms: int = 800) -> list[Path]:
    """Aufnahmen aller Varianten nach `out_dir/label/<breite>/<modus>/<n>.png`; Rueckgabe: Kacheln."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # optional, wie das Modell im LLM-Backend
        raise RuntimeError("playwright fehlt: pip install playwright && playwright install chromium") from exc
    if seed is not None and seed not in SEEDS:
        raise KeyError(f"unbekannter Seed {seed!r}; bekannt: {sorted(SEEDS)}")
    written: list[Path] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            for vp, (w, h) in VIEWPORTS.items():
                for modus, scheme in SCHEMES.items():
                    page = browser.new_page(viewport={"width": w, "height": h}, color_scheme=scheme,
                                            device_scale_factor=1, reduced_motion="reduce")
                    page.goto(html.resolve().as_uri())
                    page.wait_for_timeout(settle_ms)
                    if seed is not None:
                        page.evaluate(f"() => {{ {SEEDS[seed].script} }}")
                        page.wait_for_timeout(100)
                    width, height = page.evaluate(
                        "() => [document.documentElement.scrollWidth, document.documentElement.scrollHeight]")
                    target = out_dir / label / vp / modus
                    target.mkdir(parents=True, exist_ok=True)
                    for n, top in enumerate(tile_offsets(height, h), start=1):
                        path = target / f"{n}.png"
                        page.screenshot(path=str(path), full_page=True,
                                        clip={"x": 0, "y": top, "width": max(width, w),
                                              "height": min(h, height - top)})
                        written.append(path)
                    page.close()
        finally:
            browser.close()
    return written


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="render_evidence", description=__doc__.split("\n\n")[0])
    ap.add_argument("--html", required=True, type=Path, help="gerenderter HTML-Report")
    ap.add_argument("--label", required=True, help="Prüfling, z. B. UC-FIN-002")
    ap.add_argument("--out", required=True, type=Path, help="Zielordner der Evidenz")
    ap.add_argument("--seed", choices=sorted(SEEDS),
                    help="gesäten Fehler vor der Aufnahme einspielen (eigenes --out waehlen)")
    args = ap.parse_args(argv)
    # Gleiches Label mit und ohne Seed: der Judge darf am Label nicht erkennen, wo der Fehler steckt.
    paths = capture(args.html, args.out, args.label, args.seed)
    print(f"{len(paths)} Kacheln unter {args.out / args.label}")
    return 0 if paths else 2


if __name__ == "__main__":
    sys.exit(main())
