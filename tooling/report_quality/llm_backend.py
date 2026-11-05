"""llm_backend.py — concrete Anthropic backend for the LLM-judge seam (K6 §9).

Wires the pluggable `LLMJudge` (in `judge.py`) to a real model, so the render-only
boutique rules (BC-COLOR-01, BC-CHART-03/06, BC-NARR-05, …) can be scored over rendered
evidence instead of abstaining. Two pieces plug into `LLMJudge`:

  * `make_complete()`  -> `complete(prompt) -> str`  — an Anthropic-backed completion fn
  * `dir_render_provider(evidence_dir)` -> `render(rule_id) -> evidence`  — reads the
    rendered evidence the runbook's render step dropped on disk (per-rule file, else a
    shared report evidence file).

Design contract (honesty + opt-in, mirrors the rest of the tool infra):
  * The model id is **never hard-coded** — it is read from the `ANTHROPIC_MODEL` env var,
    so this pushed source stays model-agnostic. Set it in the shell before running.
  * Graceful-skip: with no `anthropic` SDK, no `ANTHROPIC_API_KEY`, or no `ANTHROPIC_MODEL`,
    `make_complete()` returns `None` and the `LLMJudge` abstains — it never fabricates a
    verdict. So importing/using this module without credentials changes no score.

Turnkey wiring (one call), used by the runbook:

    from tooling.report_quality.judge import CompositeJudge, SpecHeuristicJudge
    from tooling.report_quality.llm_backend import build_llm_judge
    from tooling.report_quality.boutique_scorecard import score

    judge = CompositeJudge([SpecHeuristicJudge(), build_llm_judge("build/render_evidence")])
    card = score(judge=judge)

Bild-Evidenz (D-826): `python -m tooling.report_quality.render_evidence --html … --label … --out
build/render_evidence` legt Kacheln je Breite/Modus ab; `dir_render_provider` reicht sie als Bilder
weiter, und `build_llm_judge(…, required_variants=render_evidence.REQUIRED_VARIANTS)` laesst ein
positives Urteil nur zu, wenn alle vier Varianten im Bild vorliegen.
"""
from __future__ import annotations

import base64
import os
import re
from pathlib import Path
from typing import Callable, Optional, Sequence, Union

try:  # package context (pytest / -m) …
    from tooling.report_quality.judge import (
        CompositeJudge, Evidence, ImageEvidence, LLMJudge, SpecHeuristicJudge,
    )
except ImportError:  # … or run from inside the package dir
    from judge import CompositeJudge, Evidence, ImageEvidence, LLMJudge, SpecHeuristicJudge  # type: ignore


# Filenames the render step may drop per rule, tried in order; the last few are a shared
# report-level evidence file reused for every render-only rule.
_EVIDENCE_NAMES = ("{rid}.txt", "{rid}.md", "_report.txt", "_report.md", "_report.html")
#: Bildformate, die die Messages-API als Bildblock annimmt.
_MEDIA_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


def image_blocks(images: Sequence[ImageEvidence]) -> list[dict]:
    """Bildbloecke der Messages-API, je Bild ein Textblock mit dem Label davor (Reihenfolge wie im
    Prompt). Pure — unit-getestet ohne Modell."""
    blocks: list[dict] = []
    for i, img in enumerate(images, start=1):
        media = _MEDIA_TYPES.get(img.path.suffix.lower())
        if media is None:
            raise ValueError(f"unsupported image type: {img.path.name}")
        data = base64.standard_b64encode(img.path.read_bytes()).decode("ascii")
        blocks.append({"type": "text", "text": f"[{i}] {img.label}"})
        blocks.append({"type": "image", "source": {"type": "base64", "media_type": media, "data": data}})
    return blocks


def make_complete() -> Optional[Callable[[str], str]]:
    """Build an Anthropic-backed `complete(prompt)->str`, or `None` if not wired.

    Returns `None` (→ judge abstains) when the SDK is absent, `ANTHROPIC_API_KEY` is
    unset, or `ANTHROPIC_MODEL` is unset — so callers never need a key to import this.
    """
    model = os.environ.get("ANTHROPIC_MODEL")
    if not model or not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
    except ImportError:
        return None

    client = anthropic.Anthropic()
    max_tokens = int(os.environ.get("ANTHROPIC_MAX_TOKENS", "2048"))

    def complete(prompt: str, images: Sequence[ImageEvidence] = ()) -> str:
        content: Union[str, list[dict]] = prompt
        if images:
            content = [*image_blocks(images), {"type": "text", "text": prompt}]
        msg = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            thinking={"type": "adaptive"},
            messages=[{"role": "user", "content": content}],
        )
        return "".join(
            getattr(b, "text", "") for b in msg.content
            if getattr(b, "type", None) == "text"
        )

    return complete


def dir_images(evidence_dir: str | os.PathLike) -> tuple[ImageEvidence, ...]:
    """Alle Screenshots unter `evidence_dir`, Label = relativer Pfad ohne Endung
    (`UC-FIN-002/desktop/hell/1.png` → `UC-FIN-002/desktop/hell/1`), sortiert."""
    base = Path(evidence_dir)
    found = sorted(p for p in base.rglob("*") if p.suffix.lower() in _MEDIA_TYPES and p.is_file())
    return tuple(ImageEvidence(p, p.relative_to(base).with_suffix("").as_posix()) for p in found)


def dir_render_provider(evidence_dir: str | os.PathLike) -> Callable[[str], Union[str, Evidence, None]]:
    """`render(rule_id) -> evidence` reading rendered evidence from `evidence_dir`.

    Looks for a per-rule file first (`BC-COLOR-01.txt` …), then a shared report file
    (`_report.html` …). Missing evidence → `None`, so the `LLMJudge` abstains for that
    rule rather than judging on nothing. Liegen Screenshots im Ordner (auch in Unterordnern),
    kommt `Evidence` mit Text und Bildern zurueck — ohne Bilder bleibt es beim Text.
    """
    base = Path(evidence_dir)

    def render(rule_id: str) -> Union[str, Evidence, None]:
        text = _text(rule_id)
        images = dir_images(base)
        if images:
            return Evidence(text=text or "", images=images)
        return text

    def _text(rule_id: str) -> Optional[str]:
        for pattern in _EVIDENCE_NAMES:
            p = base / pattern.format(rid=rule_id)
            if p.exists():
                text = p.read_text(encoding="utf-8").strip()
                if text:
                    return text
        # Fallback: no per-rule / _report file, so use every rendered *.html in the dir
        # as one suite-wide evidence blob. <script> is stripped (behaviour, not design
        # signal); CSS is kept (colour matters).
        htmls = sorted(base.glob("*.html"))
        if htmls:
            parts = []
            for h in htmls:
                body = re.sub(r"<script\b.*?</script>", "", h.read_text(encoding="utf-8"), flags=re.S)
                parts.append(f"<!-- {h.name} -->\n{body.strip()}")
            blob = "\n\n".join(parts).strip()
            if blob:
                return blob
        return None

    return render


def build_llm_judge(evidence_dir: str | os.PathLike, rubric: Optional[dict] = None,
                    required_variants: frozenset[str] = frozenset()) -> LLMJudge:
    """Assemble an `LLMJudge` from the env-configured model + on-disk render evidence.
    `required_variants` (z. B. `render_evidence.REQUIRED_VARIANTS`): ohne jede dieser Varianten
    im Bild kein positives Urteil (D-826)."""
    return LLMJudge(complete=make_complete(),
                    render_provider=dir_render_provider(evidence_dir),
                    rubric=rubric, required_variants=required_variants)


def build_composite_judge(evidence_dir: str | os.PathLike, rubric: Optional[dict] = None,
                          required_variants: frozenset[str] = frozenset()) -> CompositeJudge:
    """Spec-heuristic first (cheap/deterministic), LLM only for what it can't decide."""
    return CompositeJudge([SpecHeuristicJudge(), build_llm_judge(evidence_dir, rubric, required_variants)])
