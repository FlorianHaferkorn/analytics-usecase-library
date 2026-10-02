"""Farbmathematik zweimal (D-646 in Freelancing, Brief P2.75c A2): contrast.ts rechnet wie contrast.py.

contrast_cases.json hält Eingaben und die Python-Ergebnisse; Node rechnet dieselben Eingaben mit contrast.ts.
Vergleich je Schlüssel (Brief §8.3): exakt für Hex, Zeichenketten, Bool und gerundete Werte; rohe
Gleitkommawerte (Luminanz, Lab, OKLCH, ungerundeter ΔE) relativ 1e-9 (V8 und CPython weichen an einzelnen
Stellen um 1 ulp ab); der Farbton nur bei Chroma > 1e-6.

Node fehlt oder kann kein TypeScript ohne Schalter (`process.features.typescript`, Node >= 22.18) → **rot**,
nie skip: ein Gleichstand, der nicht geprüft wurde, darf nicht grün aussehen.

Fixture neu erzeugen (nach einer Änderung an contrast.py):
    python tooling/visual_library/tests/test_contrast_ts.py --write
"""
from __future__ import annotations

import json
import math
import random
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
VL = REPO_ROOT / "tooling" / "visual_library"
sys.path.insert(0, str(VL))
import contrast as C  # noqa: E402

TS = VL / "contrast.ts"
CASES = VL / "contrast_cases.json"
SEED = 20261002
MAX_BYTES = 300_000
REL = 1e-9

#: Gründe, auf denen Meridians Theme `ensure_contrast` ruft: Weiß, dunkle Karte, IBCS-Grau 50,
#: neutral.50 von Aurora und Nimbus (Stand 02.10.2026).
THEME_GRUENDE = ["#FFFFFF", "#292929", "#F7F7F7", "#F5FBFC", "#F5FAF9"]
#: Statusfarben als reservierte Rollen (Meridian-Packs, 02.10.2026).
RESERVIERT = {"positive": "#107C10", "negative": "#D13438", "warning": "#F7630C", "neutral": "#605E5C"}
#: Rohe Gleitkommawerte, verglichen mit relativer Toleranz.
ROH = {"linear", "lum", "exakt", "lab", "roh", "L", "C", "h"}


# --------------------------------------------------------------------------- #
# Erzeuger
# --------------------------------------------------------------------------- #

def _hex(rnd: random.Random) -> str:
    return f"#{rnd.randrange(1 << 24):06X}"


def _zweig(color: str, bg: str, ratio: float) -> str:
    """Welchen Ausgang ensure_contrast nimmt — Nachbau der Schleife aus contrast.py, nur zum Zählen."""
    color = C.rgb_to_hex(C.hex_to_rgb(color))
    if C.contrast_ratio_exact(color, bg) >= ratio:
        return "direkt"
    L, c, h = C.hex_to_oklch(color)
    step = -C.ENSURE_STEP_L if C.relative_luminance(bg) > C.LIGHT_BG_LUMINANCE else C.ENSURE_STEP_L
    k = 1
    while True:
        lk = L + k * step
        if lk < 0.0 or lk > 1.0:
            break
        if C.contrast_ratio_exact(C.oklch_to_hex(lk, c, h), bg) >= ratio:
            return "schritt"
        k += 1
    end = C.oklch_to_hex(0.0 if step < 0 else 1.0, 0.0, h)
    return "endpunkt" if C.contrast_ratio_exact(end, bg) >= ratio else "fehler"


def _ensure_fall(color: str, bg: str, ratio: float) -> dict:
    fall = {"color": color, "bg": bg, "ratio": ratio, "zweig": _zweig(color, bg, ratio)}
    try:
        fall["out"] = C.ensure_contrast(color, bg, ratio)
    except ValueError:
        fall["fehler"] = True
    return fall


def _gate(pal: "list[str]", bg: str) -> dict:
    return {"palette": pal, "bg": bg, "ergebnis": C.palette_gate(pal, bg, RESERVIERT)}


def erzeuge() -> dict:
    rnd = random.Random(SEED)
    farben = [_hex(rnd) for _ in range(200)]
    ecken = ["#000000", "#FFFFFF", "#FF0000", "#00FF00", "#0000FF"]

    simulate = []
    for h in farben + ecken:
        simulate.append({"hex": h, **{k: C.simulate_cvd(h, k) for k in C.CVD_KINDS},
                         "lab": list(C._hex_to_lab(h)), "lum": C.relative_luminance(h)})

    delta_e = []
    for _ in range(400):
        a, b = _hex(rnd), _hex(rnd)
        delta_e.append({"a": a, "b": b, "roh": C.delta_e_ciede2000(C._hex_to_lab(a), C._hex_to_lab(b)),
                        "normal": C.delta_e(a, b), **{k: C.delta_e(a, b, k) for k in C.CVD_KINDS},
                        "exakt": C.contrast_ratio_exact(a, b), "gerundet": C.contrast_ratio(a, b)})

    ensure = []
    for _ in range(300):                                   # zufällige Gründe und Schwellen des Themes
        ensure.append(_ensure_fall(_hex(rnd), _hex(rnd), rnd.choice([3.0, 4.5, 4.55])))
    for bg in THEME_GRUENDE:                               # die fünf Theme-Gründe
        for _ in range(4):
            ensure.append(_ensure_fall(_hex(rnd), bg, rnd.choice([3.0, 4.5, 4.55])))
    endpunkte = 0
    while endpunkte < 24:                                  # Endpunkt-Zweig gezielt: Schwelle = Kontrast des Endpunkts
        color, bg = _hex(rnd), _hex(rnd)
        end = "#000000" if C.relative_luminance(bg) > C.LIGHT_BG_LUMINANCE else "#FFFFFF"
        ratio = min(21.0, max(1.0, C.contrast_ratio_exact(end, bg)))
        if _zweig(color, bg, ratio) == "endpunkt":
            ensure.append(_ensure_fall(color, bg, ratio))
            endpunkte += 1
    ensure.append(_ensure_fall("#777777", "#808080", 7.0))  # erzwungener ValueError
    ensure += [_ensure_fall(c, bg, r) for c, bg, r in (
        ("#2ecde7", "#ffffff", 4.5), ("#0fb2c9", "#FFFFFF", 3.0), ("#a4262c", "#292929", 4.5),
        ("#404040", "#292929", 3.0))]                      # Kleinbuchstaben-Hex
    ungueltig = [{"color": "#2ECDE7", "bg": "#FFFFFF", "ratio": r} for r in (0.5, 21.5)]

    oklch = []
    graue = ["#000000", "#808080", "#FFFFFF", "#F7F7F7", "#EEEEEE", "#D9D9D9", "#A6A6A6", "#404040",
             "#2ECDE7", "#0F766E"]
    for h in [_hex(rnd) for _ in range(200)] + graue:
        L, c, hue = C.hex_to_oklch(h)
        oklch.append({"hex": h, "L": L, "C": c, "h": hue, "zurueck": C.oklch_to_hex(L, c, hue)})
    gamut = []
    for _ in range(100):                                   # Bisektion außerhalb des Gamuts
        L, c, hue = rnd.random(), rnd.random() * 0.4, rnd.random() * 360
        gamut.append({"L": L, "C": c, "h": hue, "hex": C.oklch_to_hex(L, c, hue)})

    dunkel = []
    for _ in range(60):
        color, r = _hex(rnd), rnd.choice([None, 3.0, 4.5])
        try:
            out = {"out": C.for_dark_ground(color, "#292929", "#FFFFFF", r)}
        except ValueError:
            out = {"fehler": True}
        dunkel.append({"color": color, "dark_bg": "#292929", "light_bg": "#FFFFFF", "min_ratio": r, **out})

    werte = [0.005, 0.015, 0.285, 1.115, 2.675, 0.125, 7.125, 7.995, 8.0, 9.995, 10.0, -0.125, -0.015]
    werte += [(2 * j + 1) * 0.005 for j in range(300)]
    werte += [rnd.random() * 30 for _ in range(100)]
    mit_ulp = []
    for x in werte:
        mit_ulp += [math.nextafter(x, -math.inf), x, math.nextafter(x, math.inf)]
    rundung = {"round2": [[x, round(x, 2)] for x in mit_ulp],
               "kanal": [[[x, 0, 255.4], C.rgb_to_hex((x, 0, 255.4))]
                         for x in (126.5, 127.5, 0.5, 1.5, 254.5, -0.4, 255.6, 12.49999)]}

    paletten = []
    feste = [C.OKABE_ITO[:5], C.OKABE_ITO, C.TOL_BRIGHT,
             ["#0A8CA3", "#9A5505", "#4B46AE", "#A88822", "#942464"],     # Aurora hell
             ["#2095AD", "#AA641F", "#6868D2", "#AF8E2A", "#CA5794"],     # Aurora dunkel
             ["#0A8CA3", "#9A5505", "#4B46AE", "#A88822", "#A0306E"],     # g33: Paar 1-4 tritan
             ["#D47F5F", "#0072B2", "#7FA110"],                           # needs_label-Grenze 2,9998 / 2,9966
             ["#0A8CA3", "#D13438", "#4B46AE"]]                           # Statusfarbe als Reihe
    for pal in feste:
        paletten += [_gate(pal, "#FFFFFF"), _gate(pal, "#292929")]
    for _ in range(100):
        pal = [_hex(rnd) for _ in range(rnd.randint(3, 8))]
        paletten.append(_gate(pal, rnd.choice(["#FFFFFF", "#292929"])))
    alle_sichten = []
    for _ in range(20):
        pal = [_hex(rnd) for _ in range(4)]
        alle_sichten.append({"palette": pal, "ergebnis": C.reserved_conflicts(pal, RESERVIERT,
                                                                             visions=C.ALL_VISIONS)})
    min_paar = [{"palette": p["palette"], **{k: C.min_pairwise_delta_e(p["palette"], k) for k in C.CVD_KINDS},
                 "normal": C.min_pairwise_delta_e(p["palette"])} for p in paletten[:40]]

    return {
        "_kommentar": "Erzeugt von tooling/visual_library/tests/test_contrast_ts.py --write (Seed fest). "
                      "Nicht von Hand ändern.",
        "seed": SEED,
        "konstanten": {"ENSURE_STEP_L": C.ENSURE_STEP_L, "LIGHT_BG_LUMINANCE": C.LIGHT_BG_LUMINANCE,
                       "RESERVED_MIN_DELTA_E": C.RESERVED_MIN_DELTA_E,
                       "MACHADO": {k: [list(r) for r in v] for k, v in C._MACHADO.items()},
                       "CVD_KINDS": list(C.CVD_KINDS), "OKABE_ITO": C.OKABE_ITO, "TOL_BRIGHT": C.TOL_BRIGHT,
                       "SERIES_CAP": C.SERIES_CAP},
        "linear": [C._srgb_to_linear(i) for i in range(256)],
        "simulate": simulate,
        "delta_e": delta_e,
        "ensure": ensure,
        "ensure_ungueltig": ungueltig,
        "oklch": oklch,
        "gamut": gamut,
        "dunkel": dunkel,
        "rundung": rundung,
        "reserviert": RESERVIERT,
        "paletten": paletten,
        "alle_sichten": alle_sichten,
        "min_paar": min_paar,
    }


def dump(doc: dict) -> str:
    """Eine Zeile je Fall: diff-freundlich und unter der Größengrenze."""
    def one(v: object) -> str:
        return json.dumps(v, ensure_ascii=False, separators=(",", ":"))
    teile = []
    for k, v in doc.items():
        if isinstance(v, list):
            body = ",\n".join(one(x) for x in v)
            teile.append(f"  {json.dumps(k)}: [\n{body}\n  ]")
        elif isinstance(v, dict) and k == "rundung":
            inner = ",\n".join(f"    {json.dumps(kk)}: [\n" + ",\n".join(one(x) for x in vv) + "\n    ]"
                               for kk, vv in v.items())
            teile.append(f"  {json.dumps(k)}: {{\n{inner}\n  }}")
        else:
            teile.append(f"  {json.dumps(k)}: {one(v)}")
    return "{\n" + ",\n".join(teile) + "\n}\n"


# --------------------------------------------------------------------------- #
# Vergleich je Schlüssel (§8.3)
# --------------------------------------------------------------------------- #

def _gleich(a: object, b: object, pfad: str, roh: bool, fehler: "list[str]") -> None:
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            fehler.append(f"{pfad}: Schlüssel {sorted(set(a) ^ set(b))}")
            return
        ohne_h = "C" in a and isinstance(a["C"], float) and a["C"] <= 1e-6
        for k in a:
            if k == "h" and ohne_h:
                continue
            _gleich(a[k], b[k], f"{pfad}.{k}", roh or k in ROH, fehler)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            fehler.append(f"{pfad}: Länge {len(a)} != {len(b)}")
            return
        for i, (x, y) in enumerate(zip(a, b)):
            _gleich(x, y, f"{pfad}[{i}]", roh, fehler)
    elif isinstance(a, bool) or isinstance(b, bool) or isinstance(a, str) or a is None or b is None:
        if a != b:
            fehler.append(f"{pfad}: {a!r} != {b!r}")
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if roh:
            if abs(a - b) > REL * max(1.0, abs(a), abs(b)):
                fehler.append(f"{pfad}: {a!r} != {b!r} (relativ 1e-9)")
        elif a != b:
            fehler.append(f"{pfad}: {a!r} != {b!r}")
    elif a != b:
        fehler.append(f"{pfad}: {a!r} != {b!r}")


def vergleiche(soll: object, ist: object, roh: bool = False) -> "list[str]":
    fehler: "list[str]" = []
    _gleich(soll, ist, "$", roh, fehler)
    return fehler


# --------------------------------------------------------------------------- #
# Node
# --------------------------------------------------------------------------- #

NODE_SKRIPT = r"""
const K = await import(process.argv[1]);
const doc = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));
const wirft = (f) => { try { f(); return false; } catch (e) { return true; } };
const ens = (c) => {
  try { return { out: K.ensureContrast(c.color, c.bg, c.ratio) }; } catch (e) { return { fehler: true }; }
};
const out = {
  konstanten: { ENSURE_STEP_L: K.ENSURE_STEP_L, LIGHT_BG_LUMINANCE: K.LIGHT_BG_LUMINANCE,
    RESERVED_MIN_DELTA_E: K.RESERVED_MIN_DELTA_E, MACHADO: K.MACHADO, CVD_KINDS: K.CVD_KINDS,
    OKABE_ITO: K.OKABE_ITO, TOL_BRIGHT: K.TOL_BRIGHT, SERIES_CAP: K.SERIES_CAP },
  linear: Array.from({ length: 256 }, (_, i) => K.srgbToLinear(i)),
  simulate: doc.simulate.map((s) => ({ hex: s.hex, protan: K.simulateCvd(s.hex, 'protan'),
    deutan: K.simulateCvd(s.hex, 'deutan'), tritan: K.simulateCvd(s.hex, 'tritan'), lab: K.hexToLab(s.hex),
    lum: K.relativeLuminance(s.hex) })),
  delta_e: doc.delta_e.map((d) => ({ a: d.a, b: d.b, roh: K.deltaECiede2000(K.hexToLab(d.a), K.hexToLab(d.b)),
    normal: K.deltaE(d.a, d.b), protan: K.deltaE(d.a, d.b, 'protan'), deutan: K.deltaE(d.a, d.b, 'deutan'),
    tritan: K.deltaE(d.a, d.b, 'tritan'), exakt: K.contrastRatioExact(d.a, d.b),
    gerundet: K.contrastRatioRounded(d.a, d.b) })),
  ensure: doc.ensure.map((c) => ({ color: c.color, bg: c.bg, ratio: c.ratio, zweig: c.zweig, ...ens(c) })),
  ensure_ungueltig: doc.ensure_ungueltig.map((c) => ({ ...c,
    wirft: wirft(() => K.ensureContrast(c.color, c.bg, c.ratio)) })),
  oklch: doc.oklch.map((o) => { const [L, C, h] = K.hexToOklch(o.hex);
    return { hex: o.hex, L, C, h, zurueck: K.oklchToHex(L, C, h) }; }),
  gamut: doc.gamut.map((g) => ({ L: g.L, C: g.C, h: g.h, hex: K.oklchToHex(g.L, g.C, g.h) })),
  dunkel: doc.dunkel.map((d) => {
    let r;
    try { r = { out: K.forDarkGround(d.color, d.dark_bg, d.light_bg, d.min_ratio) }; }
    catch (e) { r = { fehler: true }; }
    return { color: d.color, dark_bg: d.dark_bg, light_bg: d.light_bg, min_ratio: d.min_ratio, ...r };
  }),
  rundung: { round2: doc.rundung.round2.map(([x]) => [x, K.round2(x)]),
    kanal: doc.rundung.kanal.map(([rgb]) => [rgb, K.rgbToHex(rgb)]) },
  paletten: doc.paletten.map((p) => ({ palette: p.palette, bg: p.bg,
    ergebnis: K.paletteGate(p.palette, p.bg, doc.reserviert) })),
  alle_sichten: doc.alle_sichten.map((p) => ({ palette: p.palette,
    ergebnis: K.reservedConflicts(p.palette, doc.reserviert, K.RESERVED_MIN_DELTA_E, K.ALL_VISIONS) })),
  min_paar: doc.min_paar.map((p) => ({ palette: p.palette, protan: K.minPairwiseDeltaE(p.palette, 'protan'),
    deutan: K.minPairwiseDeltaE(p.palette, 'deutan'), tritan: K.minPairwiseDeltaE(p.palette, 'tritan'),
    normal: K.minPairwiseDeltaE(p.palette) })),
  ungueltige_farbe: wirft(() => K.hexToRgb('#12AF')),
  unbekannte_sicht: wirft(() => K.simulateCvd('#123456', 'achromat')),
  ohne_contrastRatio: !('contrastRatio' in K),
};
process.stdout.write(JSON.stringify(out));
"""


def _node() -> str:
    node = shutil.which("node")
    if not node:
        pytest.fail("node fehlt — Gleichstand contrast.ts/contrast.py nicht geprüft (Node >= 22.18 nötig)")
    probe = subprocess.run([node, "-p", "JSON.stringify([process.version, process.features.typescript ?? null])"],
                           capture_output=True, text=True, encoding="utf-8", timeout=60)
    if probe.returncode != 0:
        pytest.fail(f"node startet nicht: {probe.stderr.strip()}")
    version, ts = json.loads(probe.stdout)
    if not ts:
        pytest.fail(f"node {version} entfernt keine TypeScript-Typen ohne Schalter "
                    "(process.features.typescript fehlt) — Node >= 22.18 nötig")
    return node


def _node_rechnet() -> dict:
    node = _node()
    run = subprocess.run([node, "--no-warnings", "--input-type=commonjs", "-e",
                          f"(async () => {{ {NODE_SKRIPT} }})().catch((e) => {{ console.error(e); process.exit(1); }})",
                          TS.as_uri(), str(CASES)],
                         capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert run.returncode == 0, run.stderr
    return json.loads(run.stdout)


@pytest.fixture(scope="module")
def doc() -> dict:
    return json.loads(CASES.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def ts() -> dict:
    return _node_rechnet()


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #

def test_node_kann_typescript_ohne_schalter():
    _node()


def test_fixture_entspricht_der_erzeugung(doc):
    """Formtest: eine Änderung an contrast.py, die eine Ausgabe an einem Fall ändert, macht hier rot, bis die
    Fixture neu erzeugt ist — und damit die Node-Parität an denselben Fällen erneut läuft."""
    fehler = vergleiche(json.loads(json.dumps(erzeuge())), doc)
    assert not fehler, "contrast_cases.json veraltet (--write): " + "; ".join(fehler[:10])


def test_fixture_bleibt_unter_300_kb():
    assert CASES.stat().st_size <= MAX_BYTES, CASES.stat().st_size


def test_fixture_deckt_die_zweige_ab(doc):
    zweige = [f["zweig"] for f in doc["ensure"]]
    assert zweige.count("endpunkt") >= 20, "Endpunkt-Zweig gezielt (zufällig nur 15 von 6 000)"
    assert zweige.count("fehler") >= 1 and zweige.count("schritt") >= 100 and zweige.count("direkt") >= 50
    assert {f["bg"] for f in doc["ensure"]} >= set(THEME_GRUENDE)
    assert any(f["color"] != f["color"].upper() for f in doc["ensure"]), "Kleinbuchstaben-Hex"
    assert any(not p["ergebnis"]["ok"] for p in doc["paletten"]) and any(p["ergebnis"]["ok"] for p in doc["paletten"])
    assert any(p["ergebnis"]["warnings"] for p in doc["paletten"]), "needs_label kommt vor"
    assert any(f["check"] == "reserved_conflict" for p in doc["paletten"] for f in p["ergebnis"]["failures"])
    assert {len(p["palette"]) for p in doc["paletten"]} >= {3, 8}
    assert any(e["ergebnis"] for e in doc["alle_sichten"])


def test_rundung_halb_zur_geraden_an_den_grenzfaellen():
    """Gegenprobe der Fixture selbst: Python rundet am Binärwert, echte Gleichstände zur geraden Zahl."""
    assert (round(0.015, 2), round(0.125, 2), round(2.675, 2), round(1.115, 2)) == (0.01, 0.12, 2.67, 1.11)
    assert C.rgb_to_hex((126.5, 127.5, 0)) == "#7E8000"


@pytest.mark.parametrize("schluessel", ["konstanten", "linear", "simulate", "delta_e", "ensure", "ensure_ungueltig",
                                        "oklch", "gamut", "dunkel", "rundung", "paletten", "alle_sichten",
                                        "min_paar"])
def test_ts_fassung_rechnet_wie_python(doc, ts, schluessel):
    soll = doc[schluessel]
    if schluessel == "ensure_ungueltig":
        soll = [{**c, "wirft": True} for c in soll]
    fehler = vergleiche(soll, ts[schluessel], roh=schluessel in ROH)
    assert not fehler, f"{len(fehler)} Abweichungen: " + "; ".join(fehler[:10])


def test_ts_fassung_wirft_wie_python_und_kennt_kein_contrastratio(ts):
    assert ts["ungueltige_farbe"] and ts["unbekannte_sicht"]
    assert ts["ohne_contrastRatio"], "kein `contrastRatio` in contrast.ts — Exact oder Rounded (QA-R2-1)"
    with pytest.raises(ValueError):
        C.simulate_cvd("#123456", "achromat")


def test_vergleich_erkennt_abweichungen():
    """Gegenprobe des Vergleichs: ein Hex, ein gerundeter Wert und ein roher Wert jenseits 1e-9 fallen auf."""
    assert vergleiche({"hex": "#000000"}, {"hex": "#000001"})
    assert vergleiche({"normal": 7.99}, {"normal": 8.0})
    assert vergleiche({"roh": 1.0}, {"roh": 1.0 + 1e-8})
    assert not vergleiche({"roh": 1.0}, {"roh": 1.0 + 1e-15})
    assert not vergleiche({"C": 1e-8, "h": 10.0}, {"C": 1e-8, "h": 200.0}), "Farbton nur bei Chroma > 1e-6"


if __name__ == "__main__":
    if sys.argv[1:] == ["--write"]:
        CASES.write_text(dump(erzeuge()), encoding="utf-8")
        print(f"{CASES.relative_to(REPO_ROOT)}: {CASES.stat().st_size} B")
    else:
        print(__doc__)
        raise SystemExit(2)
