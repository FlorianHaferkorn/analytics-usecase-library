"""Tests fuer die Bild-Evidenz des Judges (D-826): Kacheln, Seed-Katalog, echte Aufnahme.

Die Aufnahme braucht Playwright + Chromium; ohne beides wird nur die reine Logik geprueft.
"""
from __future__ import annotations

import pytest

from tooling.report_quality.judge import judge_rules, load_rubric
from tooling.report_quality.render_evidence import REQUIRED_VARIANTS, SEEDS, VIEWPORTS, tile_offsets


def test_tile_offsets_cover_the_page_without_gap():
    assert tile_offsets(2000, 900) == [0, 900, 1800]
    assert tile_offsets(900, 900) == [0]
    assert tile_offsets(0, 900) == [] and tile_offsets(500, 0) == []


def test_every_seed_targets_a_judge_rule_of_the_rubric():
    judged = {r["id"] for r in judge_rules(load_rubric())}
    assert SEEDS, "ohne Seed kein Nachweis, dass der Judge Fehler findet"
    for name, seed in SEEDS.items():
        assert seed.rule_id in judged, f"Seed {name} zielt auf {seed.rule_id}, keine Judge-Regel"


def test_required_variants_are_widths_and_modes():
    assert REQUIRED_VARIANTS == {"desktop", "mobil", "hell", "dunkel"}
    assert VIEWPORTS["mobil"][0] == 390


_PAGE = """<!doctype html><html><head><style>
body{font:14px sans-serif;margin:0} .hero{font-size:48px}
@media (prefers-color-scheme: dark){body{background:#111;color:#eee}}
</style></head><body><div class="hero" id="hero">40,4</div>
<svg width="300" height="120"><rect id="a" x="0" y="0" width="100" height="100" fill="#cccccc"/>
<rect id="b" x="150" y="0" width="100" height="100" fill="#cccccc"/></svg>
<div style="height:1500px"></div></body></html>"""


@pytest.fixture
def page_html(tmp_path):
    pytest.importorskip("playwright.sync_api")
    p = tmp_path / "page.html"
    p.write_text(_PAGE, encoding="utf-8")
    return p


def _capture_or_skip(*args, **kwargs):
    from tooling.report_quality.render_evidence import capture
    try:
        return capture(*args, **kwargs)
    except Exception as exc:  # kein Chromium in dieser Umgebung
        if "Executable doesn't exist" in str(exc) or "playwright install" in str(exc):
            pytest.skip(f"Chromium fehlt: {exc}")
        raise


def test_capture_writes_every_variant_as_tiles(page_html, tmp_path):
    from tooling.report_quality.llm_backend import dir_images
    from tooling.report_quality.judge import Evidence, missing_variants
    out = tmp_path / "ev"
    paths = _capture_or_skip(page_html, out, "UC-T", settle_ms=50)
    # 1500 px Seite: desktop (900 px) 2 Kacheln, mobil (844 px) 2 Kacheln, je hell und dunkel
    assert len(paths) == 8 and all(p.stat().st_size > 0 for p in paths)
    ev = Evidence(images=dir_images(out))
    assert missing_variants(ev, REQUIRED_VARIANTS) == frozenset()


def test_seeds_change_the_render(page_html, tmp_path):
    """Gegenprobe: ein Seed, der nichts veraendert, waere kein Fehler, den der Judge finden kann."""
    clean = _capture_or_skip(page_html, tmp_path / "clean", "UC-T", settle_ms=50)
    for name in SEEDS:
        seeded = _capture_or_skip(page_html, tmp_path / name, "UC-T", seed=name, settle_ms=50)
        first = lambda ps: next(p for p in ps if p.match("desktop/hell/1.png")).read_bytes()  # noqa: E731
        assert first(seeded) != first(clean), f"Seed {name} veraendert die Aufnahme nicht"


def test_unknown_seed_is_rejected(page_html, tmp_path):
    with pytest.raises(KeyError):
        _capture_or_skip(page_html, tmp_path, "UC-T", seed="gibt-es-nicht")
