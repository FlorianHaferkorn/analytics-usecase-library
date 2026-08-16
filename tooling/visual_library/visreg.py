"""visreg.py — perceptual visual-regression for the Visual Library (CI / maintainer gate).

The golden tests prove a realization renders and matches its frozen SOURCE byte-for-byte. They do
NOT catch a silent *pixel* drift: a layout-grid tweak, a token change, or a vl-convert / Vega-Lite
version bump can change the RENDERED image while the source (or a different source) still passes.
This adds the second, looser assertion the roadmap named — a tolerance-based image check against an
approved baseline — layered on top of the existing vl-convert rasterization, not replacing it.

Design choice: a committed baseline of raw PNGs is heavy and platform-fragile (sub-pixel anti-
aliasing differs across OS/font stacks). Instead the baseline stores a compact PERCEPTUAL SIGNATURE
per idiom — a 256-bit dHash (structure) + an 8x8 quantised colour grid (hue/token drift) — which is
robust to anti-aliasing noise yet sensitive to real layout or colour change. `visreg_baseline.json`
is small, readable, and diff-friendly; regenerate it deliberately with `visreg.py baseline`.

Not part of the zero-dep resolver runtime (does not ship in the Workflow-B bundle): this is a test
tool and may use Pillow + numpy. A pixelmatch-style exact pixel diff is provided too, for ad-hoc use.

CLI:
  visreg.py baseline [--out <path>]     # (re)generate the committed signature baseline
  visreg.py check [--json]              # re-render every idiom, compare to baseline (rc=1 on drift)
  visreg.py sig <idiom> [--profile p]   # print one idiom's signature
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library"))
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library" / "acceptance"))
import render  # noqa: E402

BASELINE = Path(__file__).resolve().parent / "visreg_baseline.json"

# Drift tolerances — generous enough to absorb cross-platform anti-aliasing, tight enough to catch a
# real layout/colour change. Calibrated so an in-environment re-render scores 0 on both axes.
DHASH_MAX_HAMMING = 12    # of 256 bits (~4.7%)
COLOR_MAX_MAE = 6.0       # mean abs error on the 0-255 colour grid


# --------------------------------------------------------------------------- #
# signature
# --------------------------------------------------------------------------- #

def _load_rgb(png: bytes, bg=(255, 255, 255)):
    """Decode a PNG to an RGB numpy array, flattening any alpha onto `bg` (charts render on
    transparent → treat as the white card surface)."""
    from PIL import Image
    import numpy as np
    im = Image.open(io.BytesIO(png)).convert("RGBA")
    arr = np.asarray(im, dtype=np.float64)
    rgb, a = arr[..., :3], arr[..., 3:4] / 255.0
    flat = rgb * a + np.array(bg, dtype=np.float64) * (1 - a)
    return flat.astype(np.uint8)


def _dhash(png: bytes, size: int = 16) -> str:
    """256-bit difference hash (structure): grayscale, resize to (size+1, size), compare adjacent
    columns. Robust to anti-aliasing; sensitive to layout/shape. Returns a 64-char hex string."""
    from PIL import Image
    import numpy as np
    rgb = _load_rgb(png)
    im = Image.fromarray(rgb).convert("L").resize((size + 1, size), Image.LANCZOS)
    g = np.asarray(im, dtype=np.int16)
    bits = (g[:, 1:] > g[:, :-1]).flatten()
    val = 0
    for b in bits:
        val = (val << 1) | int(b)
    return f"{val:0{size * size // 4}x}"


def _color_grid(png: bytes, size: int = 8) -> str:
    """8x8 RGB average grid, each channel quantised to 5 bits (>>3). Catches colour/token drift a
    structural hash misses. Returns hex of size*size*3 bytes (each 0-31)."""
    from PIL import Image
    import numpy as np
    rgb = _load_rgb(png)
    im = Image.fromarray(rgb).resize((size, size), Image.LANCZOS)
    q = (np.asarray(im, dtype=np.uint8) >> 3).flatten()  # 0..31
    return q.tobytes().hex()


def signature(png: bytes) -> dict:
    from PIL import Image
    im = Image.open(io.BytesIO(png))
    return {"dhash": _dhash(png), "color": _color_grid(png), "w": im.width, "h": im.height}


# --------------------------------------------------------------------------- #
# compare
# --------------------------------------------------------------------------- #

def _hamming_hex(a: str, b: str) -> int:
    return bin(int(a, 16) ^ int(b, 16)).count("1")


def _color_mae(a_hex: str, b_hex: str) -> float:
    a, b = bytes.fromhex(a_hex), bytes.fromhex(b_hex)
    if len(a) != len(b) or not a:
        return 255.0
    # de-quantise 5-bit back to the 0-255 scale (*8) before comparing
    return round(sum(abs(x - y) for x, y in zip(a, b)) * 8 / len(a), 2)


def compare(sig_a: dict, sig_b: dict) -> dict:
    ham = _hamming_hex(sig_a["dhash"], sig_b["dhash"])
    mae = _color_mae(sig_a["color"], sig_b["color"])
    drift = ham > DHASH_MAX_HAMMING or mae > COLOR_MAX_MAE
    return {"dhash_hamming": ham, "color_mae": mae, "drift": drift}


def pixel_diff(png_a: bytes, png_b: bytes, threshold: float = 0.1) -> dict:
    """pixelmatch-style exact diff: fraction of pixels whose normalised RGB distance exceeds
    `threshold`. Env-sensitive (not the committed gate) — for ad-hoc before/after comparison."""
    import numpy as np
    a, b = _load_rgb(png_a).astype(np.float64), _load_rgb(png_b).astype(np.float64)
    if a.shape != b.shape:
        return {"same_shape": False, "diff_fraction": 1.0}
    dist = np.sqrt(((a - b) ** 2).sum(axis=2)) / (255 * (3 ** 0.5))
    changed = int((dist > threshold).sum())
    return {"same_shape": True, "diff_fraction": round(changed / dist.size, 6),
            "changed_px": changed, "total_px": int(dist.size)}


# --------------------------------------------------------------------------- #
# baseline over the Deneb set
# --------------------------------------------------------------------------- #

def _tags_and_render():
    """Yield (tag, png) for every Deneb-capable idiom x profile — reusing the acceptance renderer."""
    import render_acceptance
    dp = render.default_profile()
    for iid in _implemented():
        for profile in render.profiles(iid):
            if "deneb_vegalite" not in render.tools(iid, profile):
                continue
            tag = iid if profile == dp else f"{iid}@{profile}"
            yield tag, render_acceptance.render_deneb_png(iid, None if profile == dp else profile)


def _implemented():
    import yaml
    idx = yaml.safe_load((render.LIB / "index.yaml").read_text(encoding="utf-8"))
    return idx.get("implemented", [])


def build_baseline() -> dict:
    sigs = {tag: signature(png) for tag, png in _tags_and_render()}
    return {"tool": "deneb_vegalite", "renderer": "vl-convert",
            "tolerances": {"dhash_max_hamming": DHASH_MAX_HAMMING, "color_max_mae": COLOR_MAX_MAE},
            "count": len(sigs), "signatures": dict(sorted(sigs.items()))}


def load_baseline() -> dict:
    return json.loads(BASELINE.read_text(encoding="utf-8"))


def check_against_baseline() -> dict:
    base = load_baseline()["signatures"]
    fresh = {tag: signature(png) for tag, png in _tags_and_render()}
    drifts, missing = [], []
    for tag, sig in fresh.items():
        if tag not in base:
            missing.append(tag)
            continue
        c = compare(base[tag], sig)
        if c["drift"]:
            drifts.append({"tag": tag, **c})
    dropped = [t for t in base if t not in fresh]
    return {"checked": len(fresh), "drifts": drifts, "new": missing, "dropped": dropped,
            "ok": not drifts and not missing and not dropped}


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv: "list[str]") -> int:
    if not argv:
        print(__doc__)
        return 2
    cmd = argv[0]
    as_json = "--json" in argv
    if cmd == "baseline":
        out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else BASELINE
        b = build_baseline()
        out.write_text(json.dumps(b, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {b['count']} signatures -> {out}")
        return 0
    if cmd == "check":
        r = check_against_baseline()
        if as_json:
            print(json.dumps(r, indent=2))
        else:
            print(f"checked {r['checked']}  drifts={len(r['drifts'])}  new={r['new']}  dropped={r['dropped']}")
            for d in r["drifts"]:
                print(f"  DRIFT {d['tag']}: dhash_hamming={d['dhash_hamming']} color_mae={d['color_mae']}")
        return 0 if r["ok"] else 1
    if cmd == "sig" and len(argv) >= 2:
        import render_acceptance
        prof = argv[argv.index("--profile") + 1] if "--profile" in argv else None
        png = render_acceptance.render_deneb_png(argv[1], prof)
        print(json.dumps(signature(png), indent=2))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
